"""Validate explicit Step 06 mechanical-orientation outputs and counts."""

from __future__ import annotations

import argparse
from pathlib import Path

from emrys.libraries.alignments.bam import validate_bam_bai_pair
from emrys.libraries.alignments.orientation import (
    ORIENTATIONS,
    mechanical_like_count_detail,
    read_orientation_counts,
)
from emrys.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    lexical_path,
    run_from_args,
    snapshots,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "output_containers",
    "counts_structure",
    "fwd_count_arithmetic",
    "rev_count_arithmetic",
    "assigned_count_arithmetic",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add mechanical-orientation validator arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--fwd-bam", required=True, type=Path)
    parser.add_argument("--fwd-bai", required=True, type=Path)
    parser.add_argument("--rev-bam", required=True, type=Path)
    parser.add_argument("--rev-bai", required=True, type=Path)
    parser.add_argument("--counts", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 06 report from partitions and native counts."""
    input_paths = {
        "fwd_bam": lexical_path(arguments.fwd_bam),
        "fwd_bai": lexical_path(arguments.fwd_bai),
        "rev_bam": lexical_path(arguments.rev_bam),
        "rev_bai": lexical_path(arguments.rev_bai),
        "counts": lexical_path(arguments.counts),
    }
    input_snapshots = snapshots(input_paths, label="Step 06")

    container_magic = {}
    containers_valid = True
    for bam_key, bai_key in (
        ("fwd_bam", "fwd_bai"),
        ("rev_bam", "rev_bai"),
    ):
        pair_valid, bam_magic, bai_magic = validate_bam_bai_pair(
            input_paths[bam_key], input_paths[bai_key]
        )
        containers_valid = containers_valid and pair_valid
        container_magic[bam_key] = bam_magic
        container_magic[bai_key] = bai_magic

    count_values, counts_structure_detail = read_orientation_counts(
        input_paths["counts"], arguments.scope_id
    )
    counts_structure_valid = bool(count_values)
    checks = {
        "output_containers": (
            containers_valid,
            " ".join(f"{key}={value.hex()}" for key, value in container_magic.items()),
            "two BAM/BGZF and two BAI/CSI signatures",
            "orientation output containers",
        ),
        "counts_structure": (
            counts_structure_valid,
            counts_structure_detail,
            "one exact typed sample row",
            "orientation counts table",
        ),
    }
    for check_id, orientation_name in zip(
        ("fwd_count_arithmetic", "rev_count_arithmetic"),
        ORIENTATIONS,
        strict=True,
    ):
        counts_valid, counts_detail = mechanical_like_count_detail(
            count_values, orientation_name
        )
        checks[check_id] = (
            counts_structure_valid and counts_valid,
            counts_detail,
            f"mechanical {orientation_name} counts",
            f"mechanical {orientation_name} counts",
        )

    assigned_counts_valid = counts_structure_valid and (
        count_values["fwd_like_records"] + count_values["rev_like_records"]
        == count_values["assigned_records"]
        and count_values["assigned_records"] + count_values["unassigned_records"]
        == count_values["input_records"]
        and count_values["input_records"] > 0
        and abs(
            count_values["assigned_fraction"]
            - count_values["assigned_records"] / count_values["input_records"]
        )
        <= 0.0000005
    )
    checks["assigned_count_arithmetic"] = (
        assigned_counts_valid,
        f"input={count_values.get('input_records')} "
        f"assigned={count_values.get('assigned_records')} "
        f"unassigned={count_values.get('unassigned_records')} "
        f"fraction={count_values.get('assigned_fraction')}",
        "groups sum; assigned + unassigned = input; fraction reconciles",
        "complete orientation count arithmetic",
    )
    return build_report(
        "06",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        checks,
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 06 partition request."""
    return run_from_args(arguments, build_validation_report, "06", CHECK_IDS)
