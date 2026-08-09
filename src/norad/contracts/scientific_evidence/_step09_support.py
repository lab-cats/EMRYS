"""Step 09 scalar, path, file, and sample-pair helpers."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path

from norad.contracts.scientific_evidence import step08


def parse_nonnegative_or_infinite(label: str, value: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        step08.fail(f"{label} must be numeric; got: {value}")
    if math.isnan(parsed) or parsed < 0:
        step08.fail(f"{label} must be non-negative and not NaN; got: {value}")
    return parsed


def resolve_recorded_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def validate_pdf(label: str, path: Path) -> None:
    path = step08.require_file(label, path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        step08.fail(f"Could not read {label}: {exc}")
    if not data.startswith(b"%PDF-"):
        step08.fail(f"{label} lacks a %PDF- signature: {path}")
    if b"%%EOF" not in data[-2048:]:
        step08.fail(f"{label} lacks a trailing %%EOF marker: {path}")


def count_status(rows: Sequence[Mapping[str, str]], column: str, value: str) -> int:
    return sum(row[column] == value for row in rows)


def paired_samples(
    sample_rows: Sequence[Mapping[str, str]],
    control: str,
    treatment: str,
) -> tuple[list[str], dict[str, tuple[str, str]]]:
    if control == treatment:
        step08.fail("Step 09 control and treatment conditions must differ.")
    analysis_rows = [
        row for row in sample_rows if row["condition"] in (control, treatment)
    ]
    replicates: list[str] = []
    for row in analysis_rows:
        if row["replicate"] not in replicates:
            replicates.append(row["replicate"])
    pairs: dict[str, tuple[str, str]] = {}
    for replicate in replicates:
        controls = [
            row["sample_id"]
            for row in sample_rows
            if row["condition"] == control and row["replicate"] == replicate
        ]
        treatments = [
            row["sample_id"]
            for row in sample_rows
            if row["condition"] == treatment and row["replicate"] == replicate
        ]
        if len(controls) != 1 or len(treatments) != 1:
            step08.fail(
                "Sample manifest must define exactly one control and one "
                f"treatment for replicate {replicate}."
            )
        pairs[replicate] = (controls[0], treatments[0])
    control_replicates = {
        row["replicate"] for row in sample_rows if row["condition"] == control
    }
    treatment_replicates = {
        row["replicate"] for row in sample_rows if row["condition"] == treatment
    }
    if control_replicates != treatment_replicates or len(replicates) < 2:
        step08.fail(
            "Sample manifest must define identical control/treatment replicate "
            "sets with at least two strata."
        )
    return replicates, pairs
