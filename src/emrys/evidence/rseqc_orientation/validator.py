"""Validate an explicit Step 03 RSeQC infer_experiment report."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from emrys.libraries.evidence.qc import parse_fraction_report
from emrys.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    fail,
    lexical_path,
    run_from_args,
    snapshots,
    stable_text,
)

DESCRIPTION = __doc__
FAILED_FRACTION_LABEL = "Fraction of reads failed to determine"
ORIENTATION_A_LABEL = 'Fraction of reads explained by "1++,1--,2+-,2-+"'
ORIENTATION_B_LABEL = 'Fraction of reads explained by "1+-,1-+,2++,2--"'
FRACTION_LABELS = (
    FAILED_FRACTION_LABEL,
    ORIENTATION_A_LABEL,
    ORIENTATION_B_LABEL,
)
CHECK_IDS = {
    "report_structure",
    "failed_fraction",
    "paired_orientation_fraction_a",
    "paired_orientation_fraction_b",
    "fraction_sum",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the RSeQC-orientation validator arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--infer-report", required=True, type=Path)
    parser.add_argument("--sum-tolerance", type=float, default=0.001)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 03 report from explicit RSeQC evidence."""
    if (
        not math.isfinite(arguments.sum_tolerance)
        or not 0 <= arguments.sum_tolerance <= 0.1
    ):
        fail("--sum-tolerance must be finite and between 0 and 0.1")

    source_path = lexical_path(arguments.infer_report)
    input_snapshots = snapshots({"report": source_path}, label="Step 03 RSeQC")
    fraction_values, parse_errors = parse_fraction_report(
        stable_text(source_path, "RSeQC inference report")[0],
        FRACTION_LABELS,
    )
    fractions = tuple(fraction_values.get(label) for label in FRACTION_LABELS)
    failed_fraction, orientation_a_fraction, orientation_b_fraction = fractions
    fraction_validity = tuple(
        fraction is not None and 0 <= fraction <= 1 for fraction in fractions
    )
    (
        failed_fraction_valid,
        orientation_a_fraction_valid,
        orientation_b_fraction_valid,
    ) = fraction_validity
    observed_sum = sum(fraction for fraction in fractions if fraction is not None)
    fraction_sum_valid = (
        all(fraction_validity) and abs(observed_sum - 1.0) <= arguments.sum_tolerance
    )

    return build_report(
        "03",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        {
            "report_structure": (
                not parse_errors,
                (
                    "; ".join(parse_errors)
                    if parse_errors
                    else "3 unique required labels"
                ),
                "exactly one value per required label",
                "RSeQC report structure",
            ),
            "failed_fraction": (
                failed_fraction_valid,
                failed_fraction,
                "finite 0..1",
                "reads not assigned to an orientation",
            ),
            "paired_orientation_fraction_a": (
                orientation_a_fraction_valid,
                orientation_a_fraction,
                "finite 0..1",
                ORIENTATION_A_LABEL,
            ),
            "paired_orientation_fraction_b": (
                orientation_b_fraction_valid,
                orientation_b_fraction,
                "finite 0..1",
                ORIENTATION_B_LABEL,
            ),
            "fraction_sum": (
                fraction_sum_valid,
                f"{observed_sum:.12g}",
                f"1 within {arguments.sum_tolerance:.12g}",
                "three fractions reconcile",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 03 RSeQC-orientation request."""
    return run_from_args(arguments, build_validation_report, "03", CHECK_IDS)
