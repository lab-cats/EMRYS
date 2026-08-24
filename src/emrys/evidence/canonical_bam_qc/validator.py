"""Validate explicit Step 02b quickcheck and flagstat evidence files."""

from __future__ import annotations

import argparse
from pathlib import Path

from emrys.libraries.evidence.qc import parse_flagstat
from emrys.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    lexical_path,
    run_from_args,
    snapshots,
    stable_text,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "quickcheck_structure",
    "flagstat_structure",
    "total_records",
    "mapped_records",
    "count_consistency",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the canonical-BAM QC validator arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--quickcheck", required=True, type=Path)
    parser.add_argument("--flagstat", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 02b report from explicit QC evidence."""
    quickcheck_path = lexical_path(arguments.quickcheck)
    flagstat_path = lexical_path(arguments.flagstat)
    input_snapshots = snapshots(
        {"quickcheck": quickcheck_path, "flagstat": flagstat_path},
        label="Step 02b",
    )
    quickcheck_text = stable_text(
        quickcheck_path,
        "Quickcheck output",
    )[0].strip()
    quickcheck_valid = (
        quickcheck_text == "PASS: samtools quickcheck completed with no errors."
    )
    flagstat_values, flagstat_errors = parse_flagstat(
        stable_text(flagstat_path, "Flagstat output")[0]
    )
    total_records = sum(flagstat_values.get("total", (-1, -1)))
    mapped_records = sum(flagstat_values.get("mapped", (-1, -1)))
    flagstat_structure_valid = (
        not flagstat_errors and {"total", "mapped"} <= flagstat_values.keys()
    )
    total_records_valid = flagstat_structure_valid and total_records >= 0
    mapped_records_valid = flagstat_structure_valid and mapped_records >= 0
    counts_consistent = (
        total_records_valid and mapped_records_valid and mapped_records <= total_records
    )

    return build_report(
        "02b",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        {
            "quickcheck_structure": (
                quickcheck_valid,
                quickcheck_text or "empty",
                "exact PASS marker",
                "captured samtools quickcheck result",
            ),
            "flagstat_structure": (
                flagstat_structure_valid,
                (
                    "; ".join(flagstat_errors)
                    if flagstat_errors
                    else ",".join(sorted(flagstat_values))
                ),
                "unique total and mapped rows",
                "flagstat report structure",
            ),
            "total_records": (
                total_records_valid,
                total_records if total_records_valid else "invalid",
                "nonnegative integer",
                "QC-passed plus QC-failed total",
            ),
            "mapped_records": (
                mapped_records_valid,
                mapped_records if mapped_records_valid else "invalid",
                "nonnegative integer",
                "QC-passed plus QC-failed mapped",
            ),
            "count_consistency": (
                counts_consistent,
                f"mapped={mapped_records} total={total_records}",
                "mapped <= total",
                "flagstat count reconciliation",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 02b canonical-BAM QC request."""
    return run_from_args(arguments, build_validation_report, "02b", CHECK_IDS)
