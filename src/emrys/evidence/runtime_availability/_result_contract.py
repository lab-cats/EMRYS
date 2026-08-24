"""Deterministic TSV rendering and validation for runtime-preflight evidence."""

from __future__ import annotations

import csv
from collections.abc import Sequence

from ._runtime_model import (
    RESULT_HEADER,
    RESULT_STATUSES,
    Check,
    Result,
    _fail,
    _single_line,
)


def result_bytes(
    profile_sha256: str,
    runtime_context: str,
    results: Sequence[Result],
) -> bytes:
    rows = ["\t".join(RESULT_HEADER)]
    for result in results:
        values = (
            profile_sha256,
            runtime_context,
            result.check.check_id,
            result.check.check_type,
            result.check.target,
            "true" if result.check.required else "false",
            result.status,
            result.observed,
            result.check.expected,
            result.detail,
        )
        rows.append("\t".join(_single_line(value) for value in values))
    return ("\n".join(rows) + "\n").encode("utf-8")


def validate_result_bytes(
    data: bytes,
    profile_sha256: str,
    runtime_context: str,
    checks: Sequence[Check],
) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(f"Runtime preflight output is not UTF-8: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != RESULT_HEADER:
        _fail("Runtime preflight output has an invalid header")
    rows = list(reader)
    if len(rows) != len(checks):
        _fail("Runtime preflight output row count does not match the profile")
    seen: set[str] = set()
    for row, check in zip(rows, checks, strict=True):
        if None in row or any(value is None for value in row.values()):
            _fail("Runtime preflight output has an invalid row shape")
        if row["profile_sha256"] != profile_sha256:
            _fail("Runtime preflight output profile hash does not match")
        if row["runtime_context"] != runtime_context:
            _fail("Runtime preflight output context does not match")
        if row["status"] not in RESULT_STATUSES:
            _fail("Runtime preflight output has an invalid status")
        if row["check_id"] in seen:
            _fail("Runtime preflight output has duplicate check IDs")
        seen.add(row["check_id"])
        expected_fields = {
            "check_id": check.check_id,
            "check_type": check.check_type,
            "target": check.target,
            "required": "true" if check.required else "false",
            "expected": check.expected,
        }
        for field, expected_value in expected_fields.items():
            if row[field] != expected_value:
                _fail(
                    f"Runtime preflight output {field} does not match the "
                    f"profile for check {check.check_id}"
                )
