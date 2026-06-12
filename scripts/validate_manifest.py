#!/usr/bin/env python3
"""Validate a tab-separated RNA-seq sample manifest."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = ("sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition")
OPTIONAL_COLUMNS = ("notes",)
ALLOWED_COLUMNS = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
VALID_STRANDEDNESS = {"forward", "reverse", "unstranded", "unknown"}


class ManifestValidationError(Exception):
    """Raised when a sample manifest fails validation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a tab-separated RNA-seq sample manifest before running "
            "the NORAD workflow."
        )
    )
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
    return parser.parse_args()


def resolve_path(path_value: str, base_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return base_dir / path


def validate_manifest(manifest: Path, base_dir: Path, check_files: bool) -> dict[str, set[str] | int]:
    if not manifest.exists():
        raise ManifestValidationError(f"Manifest does not exist: {manifest}")
    if not manifest.is_file():
        raise ManifestValidationError(f"Manifest is not a file: {manifest}")

    errors: list[str] = []
    sample_rows: dict[str, int] = {}
    conditions: set[str] = set()
    strandedness_values: set[str] = set()
    sample_count = 0

    with manifest.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ManifestValidationError(f"Manifest is empty or missing a header: {manifest}")

        fieldnames = [field.strip() for field in reader.fieldnames]
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
            raise ManifestValidationError(format_errors(errors))

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                extra_values = [value.strip() for value in row[None] if value.strip()]
                if extra_values:
                    errors.append(
                        f"Row {row_number}: too many tab-separated fields: "
                        f"{', '.join(extra_values)}"
                    )
                else:
                    errors.append(f"Row {row_number}: too many tab-separated fields")

            values = {
                column: (row.get(column) or "").strip()
                for column in ALLOWED_COLUMNS
            }

            if not any(values.values()):
                continue

            sample_count += 1
            sample_id = values["sample_id"]
            r1_fastq = values["r1_fastq"]
            r2_fastq = values["r2_fastq"]
            strandedness = values["strandedness"]
            condition = values["condition"]

            if not sample_id:
                errors.append(f"Row {row_number}: sample_id must be non-empty")
            elif sample_id in sample_rows:
                errors.append(
                    f"Row {row_number}: duplicate sample_id '{sample_id}' "
                    f"(first seen on row {sample_rows[sample_id]})"
                )
            else:
                sample_rows[sample_id] = row_number

            if not r1_fastq:
                errors.append(f"Row {row_number}: r1_fastq must be non-empty")
            if not r2_fastq:
                errors.append(f"Row {row_number}: r2_fastq must be non-empty")

            if strandedness not in VALID_STRANDEDNESS:
                errors.append(
                    f"Row {row_number}: strandedness must be one of "
                    f"{', '.join(sorted(VALID_STRANDEDNESS))}; got '{strandedness}'"
                )
            else:
                strandedness_values.add(strandedness)

            if condition:
                conditions.add(condition)

            if check_files:
                for column, fastq_path in (("r1_fastq", r1_fastq), ("r2_fastq", r2_fastq)):
                    if not fastq_path:
                        continue
                    resolved_path = resolve_path(fastq_path, base_dir)
                    if not resolved_path.exists():
                        errors.append(
                            f"Row {row_number}: {column} file does not exist: {resolved_path}"
                        )

    if sample_count == 0:
        errors.append("Manifest must contain at least one sample row")

    if errors:
        raise ManifestValidationError(format_errors(errors))

    return {
        "sample_count": sample_count,
        "conditions": conditions,
        "strandedness_values": strandedness_values,
    }


def format_errors(errors: list[str]) -> str:
    return "Manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors)


def print_summary(summary: dict[str, set[str] | int]) -> None:
    conditions = ", ".join(sorted(summary["conditions"])) or "none"
    strandedness_values = ", ".join(sorted(summary["strandedness_values"])) or "none"

    print("Manifest validation passed.")
    print(f"Samples: {summary['sample_count']}")
    print(f"Conditions: {conditions}")
    print(f"Strandedness values: {strandedness_values}")


def main() -> int:
    args = parse_args()

    try:
        summary = validate_manifest(args.manifest, args.base_dir, args.check_files)
    except ManifestValidationError as error:
        print(error, file=sys.stderr)
        return 1

    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
