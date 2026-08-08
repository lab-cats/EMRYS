"""Validation row construction, rendering, and schema checks."""

from __future__ import annotations

import csv
from collections.abc import Sequence

from norad.libraries.validation.errors import fail

HEADER = (
    "step_id",
    "scope_id",
    "check_id",
    "status",
    "observed",
    "expected",
    "detail",
)


def clean(value: object) -> str:
    return " ".join(str(value).replace("\x00", "").split())


def row(
    step_id: str,
    scope_id: str,
    check_id: str,
    passed: bool,
    observed: object,
    expected: object,
    detail: object,
) -> tuple[str, ...]:
    """Build one normalized seven-field validation row."""

    return (
        step_id,
        scope_id,
        check_id,
        "pass" if passed else "fail",
        clean(observed),
        clean(expected),
        clean(detail),
    )


def render(rows: Sequence[Sequence[str]]) -> bytes:
    lines = ["\t".join(HEADER)]
    lines.extend("\t".join(clean(value) for value in values) for values in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_report(
    data: bytes,
    scope_id: str,
    *,
    step_id: str = "00a",
    check_ids: set[str] | None = None,
) -> None:
    try:
        reader = csv.DictReader(data.decode("utf-8").splitlines(), delimiter="\t")
    except UnicodeError as exc:
        fail(f"Validation report is not UTF-8: {exc}")
    if tuple(reader.fieldnames or ()) != HEADER:
        fail("Validation report header is invalid")
    expected_ids = check_ids or {
        "index_members",
        "fasta_identity",
        "gtf_identity",
        "contig_names_lengths",
        "sjdb_overhang",
    }
    rows = list(reader)
    if len(rows) != len(expected_ids):
        fail(
            f"Step {step_id} validation report must contain exactly "
            f"{len(expected_ids)} checks"
        )
    if any(
        None in item or any(value is None for value in item.values()) for item in rows
    ):
        fail("Validation report contains an invalid row")
    if {item["check_id"] for item in rows} != expected_ids:
        fail("Validation report check IDs are invalid")
    if any(item["step_id"] != step_id or item["scope_id"] != scope_id for item in rows):
        fail("Validation report scope identity is invalid")
    if any(item["status"] not in {"pass", "fail"} for item in rows):
        fail("Validation report status is invalid")
