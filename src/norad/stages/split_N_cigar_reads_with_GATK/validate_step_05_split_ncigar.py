#!/usr/bin/env python3
"""Validate explicit Step 05 split-N-cigar outputs and reference sidecars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

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
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "bam": args.bam.resolve(strict=False),
        "bai": args.bai.resolve(strict=False),
        "fasta": args.reference_fasta.resolve(strict=False),
        "fai": args.reference_fai.resolve(strict=False),
        "dict": args.reference_dict.resolve(strict=False),
        "samtools": args.samtools_bin.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 05 {role}")
        for role, path in paths.items()
    }
    if not paths["samtools"].stat().st_mode & 0o111:
        report.fail(f"samtools executable is not executable: {paths['samtools']}")
    bam_magic = paths["bam"].read_bytes()[:4]
    bai_magic = paths["bai"].read_bytes()[:4]
    structure = (
        bam_magic in {b"BAM\x01", b"\x1f\x8b\x08\x04"}
        and bai_magic in {b"BAI\x01", b"CSI\x01"}
    )
    quick = bam_report.run_tool(
        paths["samtools"], "quickcheck", "-v", str(paths["bam"])
    )
    header = bam_report.run_tool(
        paths["samtools"], "view", "-H", str(paths["bam"])
    )
    if header.returncode != 0:
        report.fail(f"samtools view -H failed: {report.clean(header.stderr)}")
    coordinate, matching_rg, header_detail = bam_report.parse_header(
        header.stdout, args.scope_id
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
            "05", args.scope_id, "bam_bai_structure", structure,
            f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
            "BAM/BGZF and BAI/CSI magic", "split-N-cigar pair containers",
        ),
        report.row(
            "05", args.scope_id, "samtools_quickcheck", quick.returncode == 0,
            report.clean(quick.stderr) or f"exit={quick.returncode}",
            "exit=0 with empty diagnostics", "samtools quickcheck -v",
        ),
        report.row(
            "05", args.scope_id, "coordinate_sorting", coordinate,
            header_detail, "one @HD with SO:coordinate", "split BAM sort order",
        ),
        report.row(
            "05", args.scope_id, "read_group_preservation", matching_rg,
            header_detail, f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
            "canonical sample read group is preserved",
        ),
        report.row(
            "05", args.scope_id, "reference_sidecars", sidecars_ok,
            sidecar_observed, "ordered FASTA/FAI/DICT contigs and lengths agree",
            "explicit GATK reference prerequisites",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="05", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id='05',
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label='Step 05',
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
