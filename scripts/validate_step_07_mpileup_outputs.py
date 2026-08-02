#!/usr/bin/env python3
"""Validate one explicit Step 07 VCF/VCF/receipt transaction without bcftools."""

from __future__ import annotations

import argparse
import importlib.util
import csv
import hashlib
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



RECEIPT_HEADER = (
    "cohort_id", "partition_id", "selector_type", "selector_value",
    "orientation", "vcf_path", "sample_manifest_sha256",
    "partition_manifest_sha256", "sample_count", "vcf_record_count",
)
CHECK_IDS = {
    "receipt_structure",
    "vcf_structure",
    "selector_reconciliation",
    "manifest_identity_and_sample_order",
    "vcf_record_counts",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--partition-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--fwd-vcf", required=True, type=Path)
    parser.add_argument("--rev-vcf", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def read_sample_ids(path: Path) -> list[str]:
    header, rows = read_tsv(path)
    if "sample_id" not in header:
        raise report.ValidationError("Sample manifest lacks sample_id")
    values = [row["sample_id"] for row in rows]
    if not values or any(not value for value in values) or len(values) != len(set(values)):
        raise report.ValidationError("Sample manifest IDs must be nonempty and unique")
    return values


def read_partition(path: Path, partition_id: str) -> tuple[str, str]:
    header, rows = read_tsv(path)
    required = {"partition_id", "selector_type", "selector_value"}
    if not required.issubset(header):
        raise report.ValidationError("Partition manifest lacks required columns")
    matches = [row for row in rows if row["partition_id"] == partition_id]
    if len(matches) != 1:
        raise report.ValidationError("Expected one declared partition row")
    selector_type = matches[0]["selector_type"]
    selector_value = matches[0]["selector_value"]
    if selector_type not in {"region", "regions_file"} or not selector_value:
        raise report.ValidationError("Partition selector is invalid")
    return selector_type, selector_value


def read_fai(path: Path) -> dict[str, int]:
    contigs: dict[str, int] = {}
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 2 or not fields[1].isdigit() or int(fields[1]) < 1:
                raise report.ValidationError(f"Invalid FAI row {number}")
            if fields[0] in contigs:
                raise report.ValidationError(f"Duplicate FAI contig: {fields[0]}")
            contigs[fields[0]] = int(fields[1])
    if not contigs:
        raise report.ValidationError("FAI contains no contigs")
    return contigs


def selector_ok(
    selector_type: str, selector_value: str, partition_manifest: Path,
    contigs: dict[str, int],
) -> bool:
    if selector_type == "region":
        for region in selector_value.split(","):
            if not region:
                return False
            contig, separator, coordinates = region.partition(":")
            if contig not in contigs:
                return False
            if not separator:
                continue
            bounds = coordinates.rstrip("-").split("-", 1)
            if not all(value.isdigit() for value in bounds):
                return False
            start = int(bounds[0])
            end = int(bounds[-1]) if not coordinates.endswith("-") else contigs[contig]
            if start < 1 or end < start or end > contigs[contig]:
                return False
        return True
    selector_path = Path(selector_value)
    if not selector_path.is_absolute():
        selector_path = partition_manifest.parent / selector_path
    try:
        with selector_path.open(encoding="utf-8") as stream:
            rows = [
                line.rstrip("\n").split("\t") for line in stream
                if line.strip() and not line.startswith("#")
            ]
    except (OSError, UnicodeError):
        return False
    return bool(rows) and all(row and row[0] in contigs for row in rows)


def read_vcf(path: Path) -> tuple[list[str], int]:
    samples: list[str] | None = None
    count = 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM\t"):
                fields = line.rstrip("\n").split("\t")
                if fields[:9] != [
                    "#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER",
                    "INFO", "FORMAT",
                ]:
                    raise report.ValidationError(f"Invalid VCF header: {path}")
                samples = fields[9:]
                continue
            if line.startswith("#"):
                continue
            if samples is None:
                raise report.ValidationError(f"VCF data precedes header: {path}")
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9 + len(samples) or not fields[1].isdigit():
                raise report.ValidationError(f"Invalid VCF data row: {path}")
            count += 1
    if samples is None:
        raise report.ValidationError(f"VCF lacks #CHROM header: {path}")
    return samples, count


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": args.sample_manifest.resolve(strict=False),
        "partition_manifest": args.partition_manifest.resolve(strict=False),
        "reference_fai": args.reference_fai.resolve(strict=False),
        "fwd_vcf": args.fwd_vcf.resolve(strict=False),
        "rev_vcf": args.rev_vcf.resolve(strict=False),
        "receipt": args.receipt.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 07 {role}")
        for role, path in paths.items()
    }
    sample_ids = read_sample_ids(paths["sample_manifest"])
    selector_type, selector_value = read_partition(
        paths["partition_manifest"], args.partition_id
    )
    contigs = read_fai(paths["reference_fai"])
    fwd_samples, fwd_count = read_vcf(paths["fwd_vcf"])
    rev_samples, rev_count = read_vcf(paths["rev_vcf"])
    receipt_header, receipt_rows = read_tsv(paths["receipt"])
    receipt_structure = (
        tuple(receipt_header) == RECEIPT_HEADER
        and len(receipt_rows) == 2
        and [row["orientation"] for row in receipt_rows] == ["FWD_like", "REV_like"]
        and all(
            row["cohort_id"] == args.cohort_id
            and row["partition_id"] == args.partition_id
            for row in receipt_rows
        )
    )
    by_orientation = {row.get("orientation", ""): row for row in receipt_rows}
    vcf_structure = fwd_samples == sample_ids and rev_samples == sample_ids
    selector_reconciliation = (
        selector_ok(selector_type, selector_value, paths["partition_manifest"], contigs)
        and receipt_structure
        and all(
            row["selector_type"] == selector_type
            and row["selector_value"] == selector_value
            for row in receipt_rows
        )
    )
    manifest_identity = receipt_structure and all(
        row["sample_manifest_sha256"] == sha256(paths["sample_manifest"])
        and row["partition_manifest_sha256"] == sha256(paths["partition_manifest"])
        and row["sample_count"].isdigit()
        and int(row["sample_count"]) == len(sample_ids)
        for row in receipt_rows
    )
    counts_ok = receipt_structure and all(
        by_orientation[orientation]["vcf_path"] == str(path)
        and by_orientation[orientation]["vcf_record_count"].isdigit()
        and int(by_orientation[orientation]["vcf_record_count"]) == count
        for orientation, path, count in (
            ("FWD_like", paths["fwd_vcf"], fwd_count),
            ("REV_like", paths["rev_vcf"], rev_count),
        )
    )

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "07", f"{args.cohort_id}__{args.partition_id}", check_id,
            "pass" if passed else "fail", report.clean(observed),
            report.clean(expected), report.clean(detail),
        )

    rows = [
        item("receipt_structure", receipt_structure, f"rows={len(receipt_rows)}",
             "exact header; FWD_like then REV_like rows", "receipt transaction"),
        item("vcf_structure", vcf_structure,
             f"FWD={len(fwd_samples)} REV={len(rev_samples)} samples",
             "valid VCFs with manifest sample order", "explicit VCF structure"),
        item("selector_reconciliation", selector_reconciliation,
             f"{selector_type}={selector_value}", "declared valid selector in both rows",
             "partition selector and FAI universe"),
        item("manifest_identity_and_sample_order", manifest_identity and vcf_structure,
             f"samples={len(sample_ids)}", "manifest hashes, count, and VCF order reconcile",
             "immutable manifest identity"),
        item("vcf_record_counts", counts_ok,
             f"FWD_like={fwd_count} REV_like={rev_count}",
             "receipt paths and counts match exact VCFs", "transaction record counts"),
    ]
    data = report.render(rows)
    scope_id = f"{args.cohort_id}__{args.partition_id}"
    report.validate_report(data, scope_id, step_id="07", check_ids=CHECK_IDS)
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
        scope_id = f"{args.cohort_id}__{args.partition_id}"
        report.publish(args.output, data, scope_id, step_id="07", check_ids=CHECK_IDS)
        print(f"Published Step 07 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, csv.Error, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
