#!/usr/bin/env python3
"""Validate explicit Step 00c FASTA, FAI, and DICT contig contracts."""

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


CHECK_IDS = {
    "fasta_structure", "fai_structure", "dict_structure",
    "fai_contig_agreement", "dict_contig_agreement",
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
        "fasta": args.reference_fasta.resolve(strict=False),
        "fai": args.reference_fai.resolve(strict=False),
        "dict": args.reference_dict.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Reference {role.upper()}")
        for role, path in paths.items()
    }
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
    def item(check_id, passed, observed, expected, detail):
        return ("00c", args.scope_id, check_id, "pass" if passed else "fail",
                report.clean(observed), report.clean(expected), report.clean(detail))
    rows = []
    for role in ("fasta", "fai", "dict"):
        rows.append(item(
            f"{role}_structure", role in parsed,
            len(parsed.get(role, [])) if role in parsed else errors.get(role, "invalid"),
            "nonempty unique contigs", f"{role.upper()} contig structure",
        ))
    for role in ("fai", "dict"):
        matches = "fasta" in parsed and role in parsed and parsed[role] == parsed["fasta"]
        rows.append(item(
            f"{role}_contig_agreement", matches,
            len(parsed.get(role, [])) if role in parsed else "invalid",
            len(parsed.get("fasta", [])) if "fasta" in parsed else "invalid",
            f"ordered {role.upper()} names and lengths equal FASTA",
        ))
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="00c", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id='00c',
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label='Step 00c',
            ),
            data,
            snapshots,
        )
    except (report.ValidationError, reference_contigs.ReferenceContigError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
