"""Validate a tab-separated RNA-seq sample manifest.

The manifest is the workflow contract between sample metadata and pipeline
steps. The validator checks schema, sample IDs, strandedness values, and
optional FASTQ path existence before cluster jobs depend on the file.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

from norad.libraries.validation import ValidationError, lexical_path, resolve_from_base

REQUIRED_COLUMNS = ("sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition")
OPTIONAL_COLUMNS = ("notes", "replicate")
ALLOWED_COLUMNS = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
VALID_STRANDEDNESS = {"forward", "reverse", "unstranded", "unknown"}
DESCRIPTION = (
    "Validate a tab-separated RNA-seq sample manifest before running "
    "the NORAD workflow."
)


@dataclass(frozen=True)
class ManifestSummary:
    """Validated manifest counts and observed categorical values."""

    sample_count: int
    conditions: frozenset[str]
    strandedness_values: frozenset[str]


@dataclass
class _ManifestState:
    errors: list[str] = field(default_factory=list)
    sample_rows: dict[str, int] = field(default_factory=dict)
    conditions: set[str] = field(default_factory=set)
    strandedness_values: set[str] = field(default_factory=set)
    sample_count: int = 0

    def summary(self) -> ManifestSummary:
        return ManifestSummary(
            sample_count=self.sample_count,
            conditions=frozenset(self.conditions),
            strandedness_values=frozenset(self.strandedness_values),
        )


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the manifest owner's arguments to a parser."""
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to the tab-separated sample manifest to validate.",
    )
    parser.add_argument(
        "--base-dir",
        default=Path("."),
        type=Path,
        help=(
            "Base directory for resolving relative FASTQ paths when "
            "--check-files is set. Defaults to the current directory."
        ),
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help=(
            "Verify that r1_fastq and r2_fastq paths exist. Relative paths "
            "are resolved against --base-dir; absolute paths are checked as-is."
        ),
    )


def _validate_header(reader: csv.DictReader, manifest: Path) -> None:
    if reader.fieldnames is None:
        raise ValidationError(f"Manifest is empty or missing a header: {manifest}")

    fieldnames = [column.strip() for column in reader.fieldnames]
    reader.fieldnames = fieldnames
    errors: list[str] = []

    duplicate_columns = sorted(
        column for column in set(fieldnames) if fieldnames.count(column) > 1
    )
    if duplicate_columns:
        errors.append(f"Duplicate column name(s): {', '.join(duplicate_columns)}")
    if "" in fieldnames:
        errors.append("Header contains an empty column name")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        errors.append(f"Missing required column(s): {', '.join(missing_columns)}")

    unexpected_columns = sorted(
        column for column in fieldnames if column not in ALLOWED_COLUMNS
    )
    if unexpected_columns:
        errors.append(f"Unexpected column(s): {', '.join(unexpected_columns)}")
    if errors:
        raise ValidationError(format_errors(errors))


def _record_extra_fields(
    row_number: int,
    row: dict[str | None, str | list[str] | None],
    state: _ManifestState,
) -> None:
    raw_extra_values = row.get(None)
    if not isinstance(raw_extra_values, list):
        return

    extra_values = [value.strip() for value in raw_extra_values if value.strip()]
    message = f"Row {row_number}: too many tab-separated fields"
    if extra_values:
        message = f"{message}: {', '.join(extra_values)}"
    state.errors.append(message)


def _normalized_values(
    row: dict[str | None, str | list[str] | None],
) -> dict[str, str]:
    return {
        column: value.strip() if isinstance(value := row.get(column), str) else ""
        for column in ALLOWED_COLUMNS
    }


def _record_sample_id(
    row_number: int,
    sample_id: str,
    state: _ManifestState,
) -> None:
    if not sample_id:
        state.errors.append(f"Row {row_number}: sample_id must be non-empty")
    elif sample_id in state.sample_rows:
        state.errors.append(
            f"Row {row_number}: duplicate sample_id '{sample_id}' "
            f"(first seen on row {state.sample_rows[sample_id]})"
        )
    else:
        state.sample_rows[sample_id] = row_number


def _record_required_fastq_paths(
    row_number: int,
    values: dict[str, str],
    state: _ManifestState,
) -> None:
    for column in ("r1_fastq", "r2_fastq"):
        if not values[column]:
            state.errors.append(f"Row {row_number}: {column} must be non-empty")


def _record_strandedness(
    row_number: int,
    strandedness: str,
    state: _ManifestState,
) -> None:
    if strandedness not in VALID_STRANDEDNESS:
        state.errors.append(
            f"Row {row_number}: strandedness must be one of "
            f"{', '.join(sorted(VALID_STRANDEDNESS))}; got '{strandedness}'"
        )
    else:
        state.strandedness_values.add(strandedness)


def _record_missing_fastq_files(
    row_number: int,
    values: dict[str, str],
    base_dir: Path,
    state: _ManifestState,
) -> None:
    for column in ("r1_fastq", "r2_fastq"):
        fastq_path = values[column]
        if not fastq_path:
            continue
        resolved_path = resolve_from_base(base_dir, fastq_path)
        if not resolved_path.exists():
            state.errors.append(
                f"Row {row_number}: {column} file does not exist: {resolved_path}"
            )


def _validate_row(
    row_number: int,
    row: dict[str | None, str | list[str] | None],
    base_dir: Path,
    check_files: bool,
    state: _ManifestState,
) -> None:
    _record_extra_fields(row_number, row, state)
    values = _normalized_values(row)
    if not any(values.values()):
        return

    state.sample_count += 1
    _record_sample_id(row_number, values["sample_id"], state)
    _record_required_fastq_paths(row_number, values, state)
    _record_strandedness(row_number, values["strandedness"], state)
    if values["condition"]:
        state.conditions.add(values["condition"])
    if check_files:
        _record_missing_fastq_files(row_number, values, base_dir, state)


def validate_manifest(
    manifest: Path, base_dir: Path, check_files: bool
) -> ManifestSummary:
    if not manifest.exists():
        raise ValidationError(f"Manifest does not exist: {manifest}")
    if not manifest.is_file():
        raise ValidationError(f"Manifest is not a file: {manifest}")

    state = _ManifestState()
    with manifest.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        _validate_header(reader, manifest)
        for row_number, row in enumerate(reader, start=2):
            _validate_row(row_number, row, base_dir, check_files, state)

    if state.sample_count == 0:
        state.errors.append("Manifest must contain at least one sample row")
    if state.errors:
        raise ValidationError(format_errors(state.errors))
    return state.summary()


def format_errors(errors: list[str]) -> str:
    return "Manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors)


def print_summary(summary: ManifestSummary) -> None:
    conditions = ", ".join(sorted(summary.conditions)) or "none"
    strandedness_values = ", ".join(sorted(summary.strandedness_values)) or "none"

    print("Manifest validation passed.")
    print(f"Samples: {summary.sample_count}")
    print(f"Conditions: {conditions}")
    print(f"Strandedness values: {strandedness_values}")


def validate_from_args(args: argparse.Namespace) -> int:
    """Validate and report one parsed manifest request."""
    manifest = lexical_path(args.manifest)
    base_dir = lexical_path(args.base_dir)

    try:
        summary = validate_manifest(manifest, base_dir, args.check_files)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1

    print_summary(summary)
    return 0
