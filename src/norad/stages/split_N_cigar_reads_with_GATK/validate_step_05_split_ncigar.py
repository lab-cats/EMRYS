#!/usr/bin/env python3
"""Validate explicit Step 05 split-N-cigar outputs and reference sidecars."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
if sys.path[:1] != [src_root]:
    if src_root in sys.path:
        sys.path.remove(src_root)
    sys.path.insert(0, src_root)

from norad.libraries import validation as report
from norad.libraries.alignments import bam as bam_report
from norad.libraries.references import contigs as reference_contigs

CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_preservation",
    "reference_sidecars",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--reference-dict", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    report.add_output_arguments(parser)
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "bam": report.lexical_path(args.bam),
        "bai": report.lexical_path(args.bai),
        "fasta": report.lexical_path(args.reference_fasta),
        "fai": report.lexical_path(args.reference_fai),
        "dict": report.lexical_path(args.reference_dict),
        "samtools": report.lexical_path(args.samtools_bin),
    }
    snapshots = report.snapshots(paths, label="Step 05")
    report.require_executable(paths["samtools"], "samtools executable")
    structure, bam_magic, bai_magic = bam_report.validate_bam_bai_pair(
        paths["bam"], paths["bai"]
    )
    (
        quickcheck_ok,
        quickcheck_detail,
        coordinate,
        matching_rg,
        header_detail,
    ) = bam_report.validate_samtools_readiness(
        paths["samtools"], paths["bam"], args.scope_id
    )
    sidecar_error = ""
    try:
        fasta = reference_contigs.parse_fasta(paths["fasta"])
        fai = reference_contigs.parse_fai(paths["fai"])
        dictionary = reference_contigs.parse_dict(paths["dict"])
        sidecars_ok = fasta == fai == dictionary
        sidecar_observed = f"FASTA={len(fasta)} FAI={len(fai)} DICT={len(dictionary)}"
    except reference_contigs.ReferenceContigError as exc:
        sidecars_ok = False
        sidecar_error = report.clean(exc)
        sidecar_observed = sidecar_error

    rows = [
        report.row(
            "05",
            args.scope_id,
            "bam_bai_structure",
            structure,
            f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
            "BAM/BGZF and BAI/CSI magic",
            "split-N-cigar pair containers",
        ),
        report.row(
            "05",
            args.scope_id,
            "samtools_quickcheck",
            quickcheck_ok,
            quickcheck_detail,
            "exit=0 with empty diagnostics",
            "samtools quickcheck -v",
        ),
        report.row(
            "05",
            args.scope_id,
            "coordinate_sorting",
            coordinate,
            header_detail,
            "one @HD with SO:coordinate",
            "split BAM sort order",
        ),
        report.row(
            "05",
            args.scope_id,
            "read_group_preservation",
            matching_rg,
            header_detail,
            f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
            "canonical sample read group is preserved",
        ),
        report.row(
            "05",
            args.scope_id,
            "reference_sidecars",
            sidecars_ok,
            sidecar_observed,
            "ordered FASTA/FAI/DICT contigs and lengths agree",
            "explicit GATK reference prerequisites",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="05", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(args, build, "05", CHECK_IDS)


if __name__ == "__main__":
    raise SystemExit(main())
