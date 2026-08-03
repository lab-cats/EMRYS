#!/usr/bin/env python3
"""Validate one explicit Step 08 three-TSV transaction without invoking R."""

from __future__ import annotations

import argparse
import importlib.util
import csv
import sys
from pathlib import Path
from typing import Callable, Sequence, TypeVar


# Temporary exact-file bridge; the final owner is src/norad/libraries/validation_report.py.
_REPORT_MODULE_NAME = "_norad_validation_report"
_REPORT_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
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

_CONTRACTS_MODULE_NAME = "_norad_step_09c_scientific_validation_contracts"
_CONTRACTS_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "scripts"
    / "step_09c_scientific_validation.py"
).resolve(strict=False)
_CONTRACTS_READY_ATTRIBUTE = "_NORAD_STEP09C_CONTRACTS_READY"


def _validated_step09c_contracts(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 09c contract owner has no valid file path"
        ) from exc
    if module_path != _CONTRACTS_MODULE_PATH:
        raise ImportError(
            f"cached Step 09c contract owner resolves to {module_path}, "
            f"expected {_CONTRACTS_MODULE_PATH}"
        )
    if getattr(module, _CONTRACTS_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 09c contract owner is partially initialized"
        )
    return module


def _load_step09c_contracts() -> object:
    cached = sys.modules.get(_CONTRACTS_MODULE_NAME)
    if cached is not None:
        return _validated_step09c_contracts(cached)
    spec = importlib.util.spec_from_file_location(
        _CONTRACTS_MODULE_NAME, _CONTRACTS_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 09c module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_CONTRACTS_MODULE_NAME, module)
    if existing is not module:
        return _validated_step09c_contracts(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _CONTRACTS_READY_ATTRIBUTE, True)
        _validated_step09c_contracts(module)
    except BaseException:
        if sys.modules.get(_CONTRACTS_MODULE_NAME) is module:
            del sys.modules[_CONTRACTS_MODULE_NAME]
        raise
    return module


try:
    contracts = _load_step09c_contracts()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 09c contract owner at "
        f"{_CONTRACTS_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


CHECK_IDS = {
    "output_transaction",
    "manifest_annotation_identity",
    "input_receipt_reconciliation",
    "sites_order_uniqueness",
    "summary_count_reconciliation",
}
T = TypeVar("T")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--annotation-gtf", required=True, type=Path)
    parser.add_argument("--sites", required=True, type=Path)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def attempt(function: Callable[[], T]) -> tuple[T | None, str]:
    try:
        return function(), "validated"
    except (OSError, UnicodeError, csv.Error, contracts.ContractError) as exc:
        return None, report.clean(exc)


def header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(next(csv.reader(stream, delimiter="\t")))


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": args.sample_manifest.resolve(strict=False),
        "partition_manifest": args.partition_manifest.resolve(strict=False),
        "annotation_gtf": args.annotation_gtf.resolve(strict=False),
        "sites": args.sites.resolve(strict=False),
        "inputs": args.inputs.resolve(strict=False),
        "summary": args.summary.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 08 {role}")
        for role, path in paths.items()
    }
    sample_result, sample_detail = attempt(
        lambda: contracts.validate_sample_manifest(paths["sample_manifest"])
    )
    partition_table, partition_detail = attempt(
        lambda: contracts.validate_partition_manifest(paths["partition_manifest"])
    )
    sample_hash = contracts.sha256_file(paths["sample_manifest"])
    partition_hash = contracts.sha256_file(paths["partition_manifest"])
    annotation_hash = contracts.sha256_file(paths["annotation_gtf"])

    expected_sites_header = None
    if sample_result is not None:
        expected_sites_header = (
            contracts.STEP08_METADATA_HEADER
            + tuple(f"DP__{sample}" for sample in sample_result[1])
            + tuple(f"AD__{sample}" for sample in sample_result[1])
            + tuple(f"AF__{sample}" for sample in sample_result[1])
        )
    observed_headers, header_detail = attempt(
        lambda: (
            header(paths["sites"]),
            header(paths["inputs"]),
            header(paths["summary"]),
        )
    )
    transaction_ok = (
        observed_headers is not None
        and expected_sites_header is not None
        and observed_headers
        == (
            expected_sites_header,
            contracts.STEP08_INPUTS_HEADER,
            contracts.STEP08_SUMMARY_HEADER,
        )
    )

    inputs_table = None
    inputs_detail = "prerequisite manifest validation failed"
    if sample_result is not None and partition_table is not None:
        inputs_table, inputs_detail = attempt(
            lambda: contracts.validate_step08_inputs(
                paths["inputs"],
                sample_result[1],
                partition_table.rows,
                sample_hash,
                partition_hash,
            )
        )
    identity_ok = False
    if inputs_table is not None:
        identity_ok = all(
            row["cohort_id"] == args.cohort_id
            and row["annotation_gtf"] == str(paths["annotation_gtf"])
            and row["annotation_gtf_sha256"] == annotation_hash
            and row["orientation_policy"] == "legacy_provisional_v1"
            for row in inputs_table.rows
        )
        if not identity_ok:
            inputs_detail = "cohort, annotation identity, or policy mismatch"

    sites_table = None
    sites_detail = "prerequisite input receipt validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
    ):
        sites_table, sites_detail = attempt(
            lambda: contracts.validate_step08_sites(
                paths["sites"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
            )
        )

    summary_table = None
    summary_detail = "prerequisite sites validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
        and sites_table is not None
    ):
        summary_table, summary_detail = attempt(
            lambda: contracts.validate_step08_summary(
                paths["summary"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
                sites_table.rows,
                sample_hash,
                partition_hash,
            )
        )
        if summary_table is not None:
            row = summary_table.rows[0]
            if (
                row["cohort_id"] != args.cohort_id
                or row["annotation_gtf"] != str(paths["annotation_gtf"])
                or row["annotation_gtf_sha256"] != annotation_hash
                or row["orientation_policy"] != "legacy_provisional_v1"
            ):
                summary_table = None
                summary_detail = "summary cohort, annotation identity, or policy mismatch"

    scope_id = args.cohort_id

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "08", scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("output_transaction", transaction_ok, header_detail,
             "three exact Step 08 TSV headers", "sites, inputs, and summary"),
        item("manifest_annotation_identity", identity_ok,
             f"sample={sample_detail}; partition={partition_detail}",
             "cohort, manifest hashes, annotation path/hash, provisional policy",
             inputs_detail),
        item("input_receipt_reconciliation", inputs_table is not None,
             inputs_detail, "complete partition x orientation receipt",
             "ordered inputs, types, hashes, and per-row arithmetic"),
        item("sites_order_uniqueness", sites_table is not None,
             sites_detail, "typed unique candidates and per-scope counts",
             "sites schema, sample columns, order, uniqueness, and AF arithmetic"),
        item("summary_count_reconciliation", summary_table is not None,
             summary_detail, "one exact aggregate row matching inputs and sites",
             "three-output transaction count reconciliation"),
    ]
    data = report.render(rows)
    report.validate_report(data, scope_id, step_id="08", check_ids=CHECK_IDS)
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
        report.publish(args.output, data, args.cohort_id, step_id="08", check_ids=CHECK_IDS)
        print(f"Published Step 08 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, csv.Error, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
