"""Shared parsers for evidence-style validation artifacts."""

from __future__ import annotations

import math
import re

FLAGSTAT_RE = re.compile(r"^([0-9]+) \+ ([0-9]+) (.+)$")


def parse_flagstat(text: str) -> tuple[dict[str, tuple[int, int]], list[str]]:
    values: dict[str, tuple[int, int]] = {}
    errors: list[str] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw:
            continue
        match = FLAGSTAT_RE.match(raw)
        if match is None:
            errors.append(f"line {number} malformed")
            continue
        passed, failed, label = int(match.group(1)), int(match.group(2)), match.group(3)
        key = (
            "total"
            if label.startswith("in total ")
            else "mapped"
            if label.startswith("mapped ")
            else ""
        )
        if key:
            if key in values:
                errors.append(f"duplicate {key} row")
            values[key] = (passed, failed)
    return values, errors


def parse_fraction_report(
    text: str, labels: tuple[str, ...]
) -> tuple[dict[str, float], list[str]]:
    values: dict[str, float] = {}
    errors: list[str] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if ":" not in raw:
            continue
        label, lexeme = (part.strip() for part in raw.rsplit(":", 1))
        if label not in labels:
            continue
        if label in values:
            errors.append(f"duplicate label at line {number}")
            continue
        try:
            value = float(lexeme)
        except ValueError:
            errors.append(f"invalid fraction at line {number}")
            continue
        if not math.isfinite(value):
            errors.append(f"nonfinite fraction at line {number}")
            continue
        values[label] = value
    missing = [label for label in labels if label not in values]
    if missing:
        errors.append(f"missing {len(missing)} required labels")
    return values, errors
