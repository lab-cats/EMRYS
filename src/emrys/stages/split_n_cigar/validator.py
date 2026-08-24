"""Validate explicit Step 05 split-N-cigar outputs and reference sidecars."""

from __future__ import annotations

import argparse
from pathlib import Path

from emrys.libraries.alignments.bam import (
    validate_bam_bai_pair,
    validate_samtools_readiness,
)
from emrys.libraries.references.contigs import (
    ReferenceContigError,
    parse_dict,
    parse_fai,
    parse_fasta,
)
from emrys.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    clean,
    lexical_path,
    require_executable,
    run_from_args,
    snapshots,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_preservation",
    "reference_sidecars",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add split-N-cigar validator arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--reference-dict", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    add_output_arguments(parser)


def _inspect_reference_sidecars(
    fasta_path: Path,
    fai_path: Path,
    dictionary_path: Path,
) -> tuple[bool, str]:
    try:
        fasta_contigs = parse_fasta(fasta_path)
        fai_contigs = parse_fai(fai_path)
        dictionary_contigs = parse_dict(dictionary_path)
    except ReferenceContigError as error:
        return False, clean(error)

    sidecars_valid = fasta_contigs == fai_contigs == dictionary_contigs
    observed = (
        f"FASTA={len(fasta_contigs)} FAI={len(fai_contigs)} "
        f"DICT={len(dictionary_contigs)}"
    )
    return sidecars_valid, observed


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 05 report from output and reference evidence."""
    input_paths = {
        "bam": lexical_path(arguments.bam),
        "bai": lexical_path(arguments.bai),
        "fasta": lexical_path(arguments.reference_fasta),
        "fai": lexical_path(arguments.reference_fai),
        "dict": lexical_path(arguments.reference_dict),
        "samtools": lexical_path(arguments.samtools_bin),
    }
    input_snapshots = snapshots(input_paths, label="Step 05")
    require_executable(input_paths["samtools"], "samtools executable")
    bam_bai_valid, bam_magic, bai_magic = validate_bam_bai_pair(
        input_paths["bam"], input_paths["bai"]
    )
    (
        quickcheck_valid,
        quickcheck_detail,
        coordinate_sorting_valid,
        read_group_valid,
        header_detail,
    ) = validate_samtools_readiness(
        input_paths["samtools"], input_paths["bam"], arguments.scope_id
    )
    reference_sidecars_valid, sidecar_observed = _inspect_reference_sidecars(
        input_paths["fasta"],
        input_paths["fai"],
        input_paths["dict"],
    )

    return build_report(
        "05",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        {
            "bam_bai_structure": (
                bam_bai_valid,
                f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
                "BAM/BGZF and BAI/CSI magic",
                "split-N-cigar pair containers",
            ),
            "samtools_quickcheck": (
                quickcheck_valid,
                quickcheck_detail,
                "exit=0 with empty diagnostics",
                "samtools quickcheck -v",
            ),
            "coordinate_sorting": (
                coordinate_sorting_valid,
                header_detail,
                "one @HD with SO:coordinate",
                "split BAM sort order",
            ),
            "read_group_preservation": (
                read_group_valid,
                header_detail,
                f"one @RG with ID:{arguments.scope_id} and SM:{arguments.scope_id}",
                "canonical sample read group is preserved",
            ),
            "reference_sidecars": (
                reference_sidecars_valid,
                sidecar_observed,
                "ordered FASTA/FAI/DICT contigs and lengths agree",
                "explicit GATK reference prerequisites",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 05 split-N-cigar request."""
    return run_from_args(arguments, build_validation_report, "05", CHECK_IDS)
