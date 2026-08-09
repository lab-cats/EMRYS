#!/usr/bin/env python3
"""Validate explicit Step 00c FASTA, FAI, and DICT contig contracts."""

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
from norad.libraries.references import contigs as reference_contigs

CHECK_IDS = {
    "fasta_structure",
    "fai_structure",
    "dict_structure",
    "fai_contig_agreement",
    "dict_contig_agreement",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--reference-dict", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "fasta": report.lexical_path(args.reference_fasta),
        "fai": report.lexical_path(args.reference_fai),
        "dict": report.lexical_path(args.reference_dict),
    }
    snapshots = report.snapshots(paths, label="Reference")
    parsed = {}
    errors = {}
    parsers = {
        "fasta": reference_contigs.parse_fasta,
        "fai": reference_contigs.parse_fai,
        "dict": reference_contigs.parse_dict,
    }
    for role, parser in parsers.items():
        try:
            parsed[role] = parser(paths[role])
        except reference_contigs.ReferenceContigError as exc:
            errors[role] = report.clean(exc)
    rows = []
    for role in ("fasta", "fai", "dict"):
        rows.append(
            report.row(
                "00c",
                args.scope_id,
                f"{role}_structure",
                role in parsed,
                len(parsed.get(role, []))
                if role in parsed
                else errors.get(role, "invalid"),
                "nonempty unique contigs",
                f"{role.upper()} contig structure",
            )
        )
    for role in ("fai", "dict"):
        matches = (
            "fasta" in parsed and role in parsed and parsed[role] == parsed["fasta"]
        )
        rows.append(
            report.row(
                "00c",
                args.scope_id,
                f"{role}_contig_agreement",
                matches,
                len(parsed.get(role, [])) if role in parsed else "invalid",
                len(parsed.get("fasta", [])) if "fasta" in parsed else "invalid",
                f"ordered {role.upper()} names and lengths equal FASTA",
            )
        )
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="00c", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(
        args,
        build,
        "00c",
        CHECK_IDS,
        caught_errors=(report.ValidationError, reference_contigs.ReferenceContigError),
    )


if __name__ == "__main__":
    raise SystemExit(main())
