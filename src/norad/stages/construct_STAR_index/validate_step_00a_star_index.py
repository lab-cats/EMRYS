#!/usr/bin/env python3
"""Validate one explicit Step 00a STAR index without modifying it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from norad.libraries import validation as report
from norad.libraries.references import contigs as reference_contigs


REQUIRED_MEMBERS = (
    "genomeParameters.txt", "Genome", "SA", "SAindex", "chrLength.txt",
    "chrName.txt", "chrNameLength.txt", "chrStart.txt", "exonGeTrInfo.tab",
    "exonInfo.tab", "geneInfo.tab", "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab", "sjdbList.out.tab", "transcriptInfo.tab",
)
CHECK_IDS = {
    "index_members",
    "fasta_identity",
    "gtf_identity",
    "contig_names_lengths",
    "sjdb_overhang",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--index-dir", required=True, type=Path)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-gtf", required=True, type=Path)
    parser.add_argument(
        "--parameter-path-base",
        required=True,
        type=Path,
        help="Explicit base for relative paths recorded in genomeParameters.txt.",
    )
    parser.add_argument("--expected-sjdb-overhang", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def parse_parameters(path: Path) -> tuple[dict[str, list[str]], report.Snapshot]:
    text, snapshot = report.stable_text(path, "STAR genomeParameters")
    parsed: dict[str, list[str]] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) < 2:
            report.fail(f"STAR genomeParameters line {number} has no value")
        if fields[0] in parsed:
            report.fail(f"STAR genomeParameters repeats {fields[0]!r}")
        parsed[fields[0]] = fields[1:]
    return parsed, snapshot


def fasta_contigs(path: Path) -> tuple[list[tuple[str, int]], report.Snapshot]:
    text, snapshot = report.stable_text(path, "Reference FASTA")
    try:
        contigs = reference_contigs.parse_fasta_lines(text.splitlines())
    except reference_contigs.ReferenceContigError as exc:
        report.fail(str(exc))
    return contigs, snapshot


def index_contigs(
    index_dir: Path,
) -> tuple[list[tuple[str, int]], tuple[report.Snapshot, report.Snapshot]]:
    names_text, names_snapshot = report.stable_text(
        index_dir / "chrName.txt", "STAR chrName"
    )
    lengths_text, lengths_snapshot = report.stable_text(
        index_dir / "chrLength.txt", "STAR chrLength"
    )
    names = names_text.splitlines()
    lengths = lengths_text.splitlines()
    if not names or len(names) != len(lengths) or len(names) != len(set(names)):
        report.fail("STAR chrName/chrLength rows are empty, duplicate, or misaligned")
    try:
        parsed = [(name, int(length)) for name, length in zip(names, lengths, strict=True)]
    except ValueError as exc:
        report.fail(f"STAR chrLength contains a non-integer: {exc}")
    if any(not name or length <= 0 for name, length in parsed):
        report.fail("STAR contig names and lengths must be nonempty and positive")
    return parsed, (names_snapshot, lengths_snapshot)


def build_report(args: argparse.Namespace) -> tuple[bytes, dict[Path, report.Snapshot]]:
    if not args.scope_id or any(char.isspace() for char in args.scope_id):
        report.fail("scope-id must be nonempty and contain no whitespace")
    if args.expected_sjdb_overhang < 0:
        report.fail("expected-sjdb-overhang must be nonnegative")
    index_dir = report.lexical_path(args.index_dir)
    if not index_dir.is_dir() or index_dir.is_symlink():
        report.fail(
            f"STAR index directory must be an existing real directory: {index_dir}"
        )
    path_base = report.lexical_path(args.parameter_path_base)
    if not path_base.is_dir() or path_base.is_symlink():
        report.fail(
            f"Parameter path base must be an existing real directory: {path_base}"
        )
    snapshots: dict[Path, report.Snapshot] = {}
    missing: list[str] = []
    for name in REQUIRED_MEMBERS:
        path = index_dir / name
        try:
            snapshots[path] = report.regular_snapshot(
                path, f"STAR index member {name}"
            )
        except report.ValidationError:
            missing.append(name)
    members_pass = not missing
    parameters, parameter_snapshot = parse_parameters(index_dir / "genomeParameters.txt")
    snapshots[index_dir / "genomeParameters.txt"] = parameter_snapshot
    fasta = report.lexical_path(args.reference_fasta)
    gtf = report.lexical_path(args.reference_gtf)
    fasta_records, fasta_snapshot = fasta_contigs(fasta)
    snapshots[fasta] = fasta_snapshot
    _, gtf_snapshot = report.stable_text(gtf, "Reference GTF")
    snapshots[gtf] = gtf_snapshot
    star_records, star_snapshots = index_contigs(index_dir)
    snapshots[index_dir / "chrName.txt"] = star_snapshots[0]
    snapshots[index_dir / "chrLength.txt"] = star_snapshots[1]
    fasta_values = parameters.get("genomeFastaFiles", [])
    gtf_values = parameters.get("sjdbGTFfile", [])
    overhang_values = parameters.get("sjdbOverhang", [])
    fasta_match = len(fasta_values) == 1 and report.resolve_from_base(
        path_base, fasta_values[0]
    ) == fasta
    gtf_match = len(gtf_values) == 1 and report.resolve_from_base(
        path_base, gtf_values[0]
    ) == gtf
    try:
        observed_overhang = int(overhang_values[0]) if len(overhang_values) == 1 else None
    except ValueError:
        observed_overhang = None
    rows = (
        report.row(
            "00a", args.scope_id, "index_members", members_pass,
            len(REQUIRED_MEMBERS) - len(missing), len(REQUIRED_MEMBERS),
            "all required members present" if members_pass else "missing: " + ",".join(missing),
        ),
        report.row(
            "00a", args.scope_id, "fasta_identity", fasta_match,
            fasta_values[0] if len(fasta_values) == 1 else "invalid", str(fasta),
            "genomeFastaFiles resolves to the explicit FASTA",
        ),
        report.row(
            "00a", args.scope_id, "gtf_identity", gtf_match,
            gtf_values[0] if len(gtf_values) == 1 else "invalid", str(gtf),
            "sjdbGTFfile resolves to the explicit GTF",
        ),
        report.row(
            "00a", args.scope_id, "contig_names_lengths", star_records == fasta_records,
            f"{len(star_records)} STAR contigs", f"{len(fasta_records)} FASTA contigs",
            "ordered contig names and lengths agree" if star_records == fasta_records else "ordered contig names or lengths differ",
        ),
        report.row(
            "00a", args.scope_id, "sjdb_overhang", observed_overhang == args.expected_sjdb_overhang,
            observed_overhang if observed_overhang is not None else "invalid",
            args.expected_sjdb_overhang, "configured STAR splice-junction overhang",
        ),
    )
    data = report.render(rows)
    report.validate_report(
        data, args.scope_id, step_id="00a", check_ids=CHECK_IDS
    )
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build_report(args)
        return report.finish(
            report.Runtime(
                step_id="00a",
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label="Step 00a",
            ),
            data,
            snapshots,
            before_report=lambda: (
                print(f"Step: 00a"),
                print(f"Scope: {args.scope_id}"),
                print(f"STAR index: {args.index_dir}"),
                print(f"Parameter path base: {args.parameter_path_base}"),
                print(f"Output: {args.output}"),
            ),
        )
    except report.ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
