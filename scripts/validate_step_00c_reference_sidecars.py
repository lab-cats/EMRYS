#!/usr/bin/env python3
"""Validate explicit Step 00c FASTA, FAI, and DICT contig contracts."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Sequence


# Temporary exact-file bridge; the final owner is src/norad/libraries/validation_report.py.
_REPORT_MODULE_NAME = "_norad_validation_report"
_REPORT_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "norad"
    / "libraries"
    / "validation_report.py"
).resolve(strict=False)
_REPORT_READY_ATTRIBUTE = "_NORAD_VALIDATION_REPORT_READY"


def _validated_validation_report(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError("cached validation-report owner has no valid file path") from exc
    if module_path != _REPORT_MODULE_PATH:
        raise ImportError(
            f"cached validation-report owner resolves to {module_path}, "
            f"expected {_REPORT_MODULE_PATH}"
        )
    if getattr(module, _REPORT_READY_ATTRIBUTE, False) is not True:
        raise ImportError("cached validation-report owner is partially initialized")
    return module


def _load_validation_report() -> object:
    cached = sys.modules.get(_REPORT_MODULE_NAME)
    if cached is not None:
        return _validated_validation_report(cached)
    spec = importlib.util.spec_from_file_location(
        _REPORT_MODULE_NAME, _REPORT_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError("unable to create an exact-file module specification")
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_REPORT_MODULE_NAME, module)
    if existing is not module:
        return _validated_validation_report(existing)
    try:
        spec.loader.exec_module(module)
        _validated_validation_report(module)
    except BaseException:
        if sys.modules.get(_REPORT_MODULE_NAME) is module:
            del sys.modules[_REPORT_MODULE_NAME]
        raise
    return module


try:
    report = _load_validation_report()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load NORAD validation-report owner at "
        f"{_REPORT_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None

import reference_provenance


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
        "fasta": reference_provenance.parse_fasta,
        "fai": reference_provenance.parse_fai,
        "dict": reference_provenance.parse_dict,
    }
    for role, parser in parsers.items():
        try:
            parsed[role] = parser(paths[role])
        except reference_provenance.ProvenanceError as exc:
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
        print(data.decode(), end="")
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        for path, expected in snapshots.items():
            if report.regular_snapshot(path, f"Input {path.name}") != expected:
                report.fail(f"Input changed after validation: {path}")
        report.publish(
            args.output, data, args.scope_id, step_id="00c", check_ids=CHECK_IDS
        )
        print(f"Published Step 00c validation report: {args.output}")
        return 0
    except (report.ValidationError, reference_provenance.ProvenanceError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
