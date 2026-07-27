#!/usr/bin/env python3
"""Validate an explicit Step 02 canonical BAM/BAI and read-group contract."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import validate_step_00a_star_index as report


CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_header",
    "alignment_rg_tags",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def run_tool(tool: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(tool), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


def parse_header(text: str, scope_id: str) -> tuple[bool, bool, str]:
    hd = [line for line in text.splitlines() if line.startswith("@HD\t")]
    rg = [line for line in text.splitlines() if line.startswith("@RG\t")]
    coordinate = len(hd) == 1 and "SO:coordinate" in hd[0].split("\t")
    matching = (
        len(rg) == 1
        and f"ID:{scope_id}" in rg[0].split("\t")
        and f"SM:{scope_id}" in rg[0].split("\t")
    )
    return coordinate, matching, f"HD={len(hd)} RG={len(rg)}"


def integer_stdout(result: subprocess.CompletedProcess[str], label: str) -> int:
    if result.returncode != 0:
        report.fail(f"{label} failed: {report.clean(result.stderr)}")
    try:
        value = int(result.stdout.strip())
    except ValueError:
        report.fail(f"{label} returned a noninteger count")
    if value < 0:
        report.fail(f"{label} returned a negative count")
    return value


def build(args: argparse.Namespace):
    bam = args.bam.resolve(strict=False)
    bai = args.bai.resolve(strict=False)
    tool = args.samtools_bin.resolve(strict=False)
    snapshots = {
        path: report.regular_snapshot(path, label)
        for path, label in (
            (bam, "Step 02 BAM"),
            (bai, "Step 02 BAI"),
            (tool, "samtools executable"),
        )
    }
    if not tool.stat().st_mode & 0o111:
        report.fail(f"samtools executable is not executable: {tool}")
    bam_magic = bam.read_bytes()[:4]
    bai_magic = bai.read_bytes()[:4]
    structure = (
        bam_magic in {b"BAM\x01", b"\x1f\x8b\x08\x04"}
        and bai_magic in {b"BAI\x01", b"CSI\x01"}
    )
    quickcheck = run_tool(tool, "quickcheck", "-v", str(bam))
    header = run_tool(tool, "view", "-H", str(bam))
    if header.returncode != 0:
        report.fail(f"samtools view -H failed: {report.clean(header.stderr)}")
    coordinate, matching_rg, header_detail = parse_header(header.stdout, args.scope_id)
    total = integer_stdout(run_tool(tool, "view", "-c", str(bam)), "alignment count")
    tagged = integer_stdout(
        run_tool(tool, "view", "-c", "-d", f"RG:{args.scope_id}", str(bam)),
        "read-group alignment count",
    )

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "02", args.scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("bam_bai_structure", structure,
             f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
             "BAM/BGZF and BAI/CSI magic", "canonical pair containers"),
        item("samtools_quickcheck", quickcheck.returncode == 0,
             report.clean(quickcheck.stderr) or f"exit={quickcheck.returncode}",
             "exit=0 with empty diagnostics", "samtools quickcheck -v"),
        item("coordinate_sorting", coordinate, header_detail,
             "one @HD with SO:coordinate", "canonical BAM sort order"),
        item("read_group_header", matching_rg, header_detail,
             f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
             "sample read-group header"),
        item("alignment_rg_tags", tagged == total, f"tagged={tagged} total={total}",
             "tagged equals total", "all alignments carry the sample RG tag"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="02", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        print(data.decode(), end="")
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        for path, expected in snapshots.items():
            if report.regular_snapshot(path, f"Input {path.name}") != expected:
                report.fail(f"Input changed after validation: {path}")
        report.publish(args.output, data, args.scope_id, step_id="02", check_ids=CHECK_IDS)
        print(f"Published Step 02 validation report: {args.output}")
        return 0
    except (OSError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
