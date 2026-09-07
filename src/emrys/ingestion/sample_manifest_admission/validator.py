"""Validate a tab-separated RNA-seq sample manifest.

The manifest is the workflow contract between sample metadata and pipeline
steps. The validator checks schema, sample IDs, strandedness values, and
optional FASTQ path existence before cluster jobs depend on the file.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries.validation import ValidationError, lexical_path, resolve_from_base

REQUIRED_COLUMNS = ("sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition")
OPTIONAL_COLUMNS = ("notes", "replicate")
ALLOWED_COLUMNS = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
VALID_STRANDEDNESS = {"forward", "reverse", "unstranded", "unknown"}
DESCRIPTION = (
    "Validate a tab-separated RNA-seq sample manifest before running "
    "the EMRYS workflow."
)


@dataclass(frozen=True)
class ManifestSummary:
    """Validated manifest counts and observed categorical values."""

    sample_count: int
    conditions: frozenset[str]
    strandedness_values: frozenset[str]


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


def validate_manifest(
    manifest: Path, base_dir: Path, check_files: bool
) -> ManifestSummary:
    if not manifest.exists():
        raise ValidationError(f"Manifest does not exist: {manifest}")
    if not manifest.is_file():
        raise ValidationError(f"Manifest is not a file: {manifest}")

    errors: list[str] = []
    sample_rows: dict[str, int] = {}
    conditions: set[str] = set()
    strandedness_values: set[str] = set()
    sample_count = 0
    with manifest.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValidationError(f"Manifest is empty or missing a header: {manifest}")
        fieldnames = [column.strip() for column in reader.fieldnames]
        reader.fieldnames = fieldnames
        duplicate_columns = sorted(
            column for column in set(fieldnames) if fieldnames.count(column) > 1
        )
        if duplicate_columns:
            errors.append(f"Duplicate column name(s): {', '.join(duplicate_columns)}")
        if "" in fieldnames:
            errors.append("Header contains an empty column name")
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            errors.append(f"Missing required column(s): {', '.join(missing_columns)}")
        unexpected_columns = sorted(column for column in fieldnames if column not in ALLOWED_COLUMNS)
        if unexpected_columns:
            errors.append(f"Unexpected column(s): {', '.join(unexpected_columns)}")
        if errors:
            raise ValidationError(format_errors(errors))
        for row_number, row in enumerate(reader, start=2):
            raw_extra_values = row.get(None)
            if isinstance(raw_extra_values, list):
                extra_values = [value.strip() for value in raw_extra_values if value.strip()]
                message = f"Row {row_number}: too many tab-separated fields"
                if extra_values:
                    message = f"{message}: {', '.join(extra_values)}"
                errors.append(message)
            values = {
                column: value.strip() if isinstance(value := row.get(column), str) else ""
                for column in ALLOWED_COLUMNS
            }
            if not any(values.values()):
                continue
            sample_count += 1
            sample_id = values["sample_id"]
            if not sample_id:
                errors.append(f"Row {row_number}: sample_id must be non-empty")
            elif sample_id in sample_rows:
                errors.append(
                    f"Row {row_number}: duplicate sample_id '{sample_id}' "
                    f"(first seen on row {sample_rows[sample_id]})"
                )
            else:
                sample_rows[sample_id] = row_number
            for column in ("r1_fastq", "r2_fastq"):
                fastq_path = values[column]
                if not fastq_path:
                    errors.append(f"Row {row_number}: {column} must be non-empty")
                elif check_files and not (
                    resolved_path := resolve_from_base(base_dir, fastq_path)
                ).exists():
                    errors.append(
                        f"Row {row_number}: {column} file does not exist: {resolved_path}"
                    )
            strandedness = values["strandedness"]
            if strandedness not in VALID_STRANDEDNESS:
                errors.append(
                    f"Row {row_number}: strandedness must be one of "
                    f"{', '.join(sorted(VALID_STRANDEDNESS))}; got '{strandedness}'"
                )
            else:
                strandedness_values.add(strandedness)
            if values["condition"]:
                conditions.add(values["condition"])

    if sample_count == 0:
        errors.append("Manifest must contain at least one sample row")
    if errors:
        raise ValidationError(format_errors(errors))
    return ManifestSummary(sample_count, frozenset(conditions), frozenset(strandedness_values))


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
