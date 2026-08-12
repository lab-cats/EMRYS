"""Require semantic success from one persisted owner-validation report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from norad.libraries import validation

DESCRIPTION = (
    "Require every row in one explicit NORAD owner-validation report to pass. "
    "The check is read-only and publishes no receipt."
)


@dataclass(frozen=True, slots=True)
class AllPassEvidence:
    """Content identity and semantic result for one all-pass report."""

    report_path: Path
    report_sha256: str
    row_count: int
    check_ids: tuple[str, ...]
    step_id: str
    scope_id: str


def _report_rows(data: bytes, path: Path) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
        raw_rows = list(csv.reader(StringIO(text, newline=""), delimiter="\t", strict=True))
    except (UnicodeError, csv.Error) as exc:
        validation.fail(f"Validation report is not strict UTF-8 TSV: {path}: {exc}")

    if not raw_rows:
        validation.fail(f"Validation report is empty: {path}")
    header = tuple(raw_rows[0])
    if header != validation.HEADER:
        validation.fail(
            "Validation report header is invalid; expected exactly: "
            + " | ".join(validation.HEADER)
        )

    rows: list[dict[str, str]] = []
    for row_number, values in enumerate(raw_rows[1:], start=2):
        if len(values) != len(validation.HEADER):
            validation.fail(
                f"Validation report row {row_number} has {len(values)} fields; "
                f"expected {len(validation.HEADER)}: {path}"
            )
        rows.append(dict(zip(validation.HEADER, values, strict=True)))
    if not rows:
        validation.fail(f"Validation report contains no check rows: {path}")
    return rows


def require_all_pass(
    report_path: Path,
    *,
    step_id: str,
    scope_id: str,
) -> AllPassEvidence:
    """Parse one complete report and fail unless every declared check passes."""

    if not step_id:
        validation.fail("Expected step ID must be nonempty")
    if not scope_id:
        validation.fail("Expected scope ID must be nonempty")

    path = validation.lexical_path(report_path)
    data = validation.read_bytes(path, "Validation report")
    rows = _report_rows(data, path)
    check_ids: list[str] = []
    seen: set[str] = set()
    nonpassing: list[str] = []

    for row_number, row in enumerate(rows, start=2):
        if row["step_id"] != step_id or row["scope_id"] != scope_id:
            validation.fail(
                f"Validation report row {row_number} has the wrong step/scope; "
                f"expected {step_id}/{scope_id}, observed "
                f"{row['step_id']}/{row['scope_id']}"
            )
        check_id = row["check_id"]
        if not check_id:
            validation.fail(
                f"Validation report row {row_number} has an empty check_id"
            )
        if check_id in seen:
            validation.fail(f"Validation report repeats check_id: {check_id}")
        seen.add(check_id)
        check_ids.append(check_id)
        if row["status"] != "pass":
            nonpassing.append(f"{check_id}={row['status'] or '<empty>'}")

    if nonpassing:
        validation.fail(
            "Validation report is not all-pass: " + ", ".join(nonpassing)
        )

    return AllPassEvidence(
        report_path=path,
        report_sha256=hashlib.sha256(data).hexdigest(),
        row_count=len(rows),
        check_ids=tuple(check_ids),
        step_id=step_id,
        scope_id=scope_id,
    )


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the semantic all-pass arguments to the grouped validator CLI."""

    parser.add_argument(
        "--report",
        required=True,
        type=Path,
        help="Exact persisted seven-column owner-validation report.",
    )
    parser.add_argument(
        "--step-id",
        required=True,
        help="Expected historical step identity recorded in every report row.",
    )
    parser.add_argument(
        "--scope-id",
        required=True,
        help="Expected owner scope identity recorded in every report row.",
    )
    parser.set_defaults(_command_parser=parser)


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Run and report one read-only semantic all-pass check."""

    try:
        evidence = require_all_pass(
            arguments.report,
            step_id=arguments.step_id,
            scope_id=arguments.scope_id,
        )
    except (OSError, validation.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Validation report semantic all-pass: PASS")
    print(f"  Report: {evidence.report_path}")
    print(f"  SHA-256: {evidence.report_sha256}")
    print(f"  Check rows: {evidence.row_count}")
    print(f"  Check IDs: {','.join(evidence.check_ids)}")
    return 0
