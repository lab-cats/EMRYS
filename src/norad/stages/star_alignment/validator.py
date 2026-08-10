"""Validate explicit Step 01 STAR alignment outputs and mapping summary."""

from __future__ import annotations

import argparse
from pathlib import Path

from norad.libraries.alignments.bam import validate_bam_signature
from norad.libraries.alignments.star import (
    parse_final_log,
    valid_mapping_summary,
    valid_splice_junction_table,
)
from norad.libraries.validation import (
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
    "output_files",
    "bam_structure",
    "final_log_structure",
    "mapping_summary",
    "splice_junction_structure",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the STAR-alignment validator owner's arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--log-final", required=True, type=Path)
    parser.add_argument("--log-out", required=True, type=Path)
    parser.add_argument("--log-progress", required=True, type=Path)
    parser.add_argument("--sj-out", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 01 report from explicit STAR outputs."""
    artifact_paths = {
        "bam": lexical_path(arguments.bam),
        "log_final": lexical_path(arguments.log_final),
        "log_out": lexical_path(arguments.log_out),
        "log_progress": lexical_path(arguments.log_progress),
        "sj_out": lexical_path(arguments.sj_out),
    }
    input_snapshots = snapshots(artifact_paths, label="Step 01")
    all_outputs_nonempty = all(
        snapshot.size > 0 for snapshot in input_snapshots.values()
    )
    bam_structure_valid, bam_prefix = validate_bam_signature(artifact_paths["bam"])
    final_log_values: dict[str, str] = {}
    final_log_error = ""
    final_log_text = stable_text(
        artifact_paths["log_final"],
        "STAR final log",
    )[0]
    try:
        final_log_values = parse_final_log(final_log_text)
    except ValueError as exc:
        final_log_error = str(exc)
    mapping_summary_valid, mapping_summary_observed = valid_mapping_summary(
        final_log_values
    )
    splice_junctions_valid, splice_junctions_observed = valid_splice_junction_table(
        stable_text(
            artifact_paths["sj_out"],
            "STAR splice-junction table",
        )[0]
    )

    return build_report(
        "01",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        {
            "output_files": (
                all_outputs_nonempty,
                len(artifact_paths),
                "5 nonempty explicit outputs",
                "BAM, final/general/progress logs, and SJ table",
            ),
            "bam_structure": (
                bam_structure_valid,
                bam_prefix.hex(),
                "BAM or BGZF magic",
                "alignment output container",
            ),
            "final_log_structure": (
                bool(final_log_values),
                len(final_log_values) if final_log_values else final_log_error,
                "nonempty unique key/value rows",
                "STAR Log.final.out structure",
            ),
            "mapping_summary": (
                mapping_summary_valid,
                mapping_summary_observed,
                "three required percentages in 0..100",
                "STAR mapping summary",
            ),
            "splice_junction_structure": (
                splice_junctions_valid,
                splice_junctions_observed,
                "zero or more valid 9-column rows",
                "STAR SJ.out.tab structure",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 01 STAR-alignment request."""
    return run_from_args(arguments, build_validation_report, "01", CHECK_IDS)
