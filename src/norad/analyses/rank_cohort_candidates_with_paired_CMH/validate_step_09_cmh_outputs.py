#!/usr/bin/env python3
"""Validate one explicit Step 09 six-output transaction without invoking R."""

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

_STEP08_MODULE_NAME = "_norad_step08_scientific_evidence_contract"
_STEP08_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
    / "contracts"
    / "scientific_evidence"
    / "step08.py"
).resolve(strict=False)
_STEP08_READY_ATTRIBUTE = "_NORAD_STEP08_CONTRACT_READY"


def _validated_step08_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 08 scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _STEP08_MODULE_PATH:
        raise ImportError(
            "cached Step 08 scientific-evidence contract resolves to "
            f"{module_path}, expected {_STEP08_MODULE_PATH}"
        )
    if getattr(module, _STEP08_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 08 scientific-evidence contract is partially initialized"
        )
    return module


def _load_step08_contract() -> object:
    cached = sys.modules.get(_STEP08_MODULE_NAME)
    if cached is not None:
        return _validated_step08_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _STEP08_MODULE_NAME, _STEP08_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 08 module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_STEP08_MODULE_NAME, module)
    if existing is not module:
        return _validated_step08_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _STEP08_READY_ATTRIBUTE, True)
        _validated_step08_contract(module)
    except BaseException:
        if sys.modules.get(_STEP08_MODULE_NAME) is module:
            del sys.modules[_STEP08_MODULE_NAME]
        raise
    return module


try:
    step08 = _load_step08_contract()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 08 scientific-evidence contract at "
        f"{_STEP08_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None

_STEP09_MODULE_NAME = "_norad_step09_scientific_evidence_contract"
_STEP09_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
    / "contracts"
    / "scientific_evidence"
    / "step09.py"
).resolve(strict=False)
_STEP09_READY_ATTRIBUTE = "_NORAD_STEP09_CONTRACT_READY"


def _validated_step09_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 09 scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _STEP09_MODULE_PATH:
        raise ImportError(
            "cached Step 09 scientific-evidence contract resolves to "
            f"{module_path}, expected {_STEP09_MODULE_PATH}"
        )
    if getattr(module, _STEP09_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 09 scientific-evidence contract is partially initialized"
        )
    return module


def _load_step09_contract() -> object:
    cached = sys.modules.get(_STEP09_MODULE_NAME)
    if cached is not None:
        return _validated_step09_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _STEP09_MODULE_NAME, _STEP09_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 09 module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_STEP09_MODULE_NAME, module)
    if existing is not module:
        return _validated_step09_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _STEP09_READY_ATTRIBUTE, True)
        _validated_step09_contract(module)
    except BaseException:
        if sys.modules.get(_STEP09_MODULE_NAME) is module:
            del sys.modules[_STEP09_MODULE_NAME]
        raise
    return module


try:
    step09 = _load_step09_contract()
    if step09.step08 is not step08:
        raise ImportError(
            "Step 09 contract and validator resolved different Step 08 objects"
        )
    if (
        step09.ContractError is not step08.ContractError
        or step09.Table is not step08.Table
    ):
        raise ImportError("Step 09 contract resolved different shared identities")
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 09 scientific-evidence contract at "
        f"{_STEP09_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


CHECK_IDS = {
    "output_transaction",
    "upstream_identity_and_candidate_order",
    "status_semantics",
    "significant_subset",
    "summary_count_reconciliation",
    "mutation_spectrum_reconciliation",
    "pdf_structure",
}
T = TypeVar("T")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--step08-sites", required=True, type=Path)
    parser.add_argument("--step08-inputs", required=True, type=Path)
    parser.add_argument("--all-sites", required=True, type=Path)
    parser.add_argument("--significant-sites", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--mutation-spectrum", required=True, type=Path)
    parser.add_argument("--mutation-spectrum-pdf", required=True, type=Path)
    parser.add_argument("--depth-delta-pdf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def attempt(function: Callable[[], T]) -> tuple[T | None, str]:
    try:
        return function(), "validated"
    except (OSError, UnicodeError, csv.Error, step08.ContractError) as exc:
        return None, report.clean(exc)


def header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(next(csv.reader(stream, delimiter="\t")))


def absolute(path: Path) -> Path:
    """Return an absolute lexical path without following a final symlink."""
    return path.expanduser().absolute()


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": absolute(args.sample_manifest),
        "partition_manifest": absolute(args.partition_manifest),
        "step08_sites": absolute(args.step08_sites),
        "step08_inputs": absolute(args.step08_inputs),
        "all_sites": absolute(args.all_sites),
        "significant_sites": absolute(args.significant_sites),
        "summary": absolute(args.summary),
        "mutation_spectrum": absolute(args.mutation_spectrum),
        "mutation_spectrum_pdf": absolute(args.mutation_spectrum_pdf),
        "depth_delta_pdf": absolute(args.depth_delta_pdf),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 09 {role}")
        for role, path in paths.items()
    }
    suffixes = {
        "all_sites": ".cmh_all_sites.tsv",
        "significant_sites": ".cmh_significant_sites.tsv",
        "summary": ".cmh_summary.tsv",
        "mutation_spectrum": ".mutation_spectrum.tsv",
        "mutation_spectrum_pdf": ".mutation_spectrum.pdf",
        "depth_delta_pdf": ".depth_delta.pdf",
    }
    native_paths = [paths[key] for key in suffixes]
    native_snapshots = [snapshots[path] for path in native_paths]
    transaction_ok = (
        all(
            paths[key].name == f"{args.analysis_id}{suffix}"
            for key, suffix in suffixes.items()
        )
        and len({path.parent for path in native_paths}) == 1
        and len(
            {(snapshot.device, snapshot.inode) for snapshot in native_snapshots}
        ) == len(native_paths)
    )

    _, id_detail = attempt(
        lambda: (
            step08.validate_safe_id("analysis_id", args.analysis_id),
            step08.validate_safe_id("cohort_id", args.cohort_id),
        )
    )
    sample_result, sample_detail = attempt(
        lambda: step08.validate_sample_manifest(paths["sample_manifest"])
    )
    partition_table, partition_detail = attempt(
        lambda: step08.validate_partition_manifest(paths["partition_manifest"])
    )
    step08_inputs = None
    step08_input_detail = "manifest prerequisite failed"
    if sample_result is not None and partition_table is not None:
        step08_inputs, step08_input_detail = attempt(
            lambda: step08.validate_step08_inputs(
                paths["step08_inputs"],
                sample_result[1],
                partition_table.rows,
                step08.sha256_file(paths["sample_manifest"]),
                step08.sha256_file(paths["partition_manifest"]),
            )
        )
    cohort_policy_ok = (
        step08_inputs is not None
        and all(
            row["cohort_id"] == args.cohort_id
            and row["orientation_policy"] == "legacy_provisional_v1"
            for row in step08_inputs.rows
        )
    )
    if step08_inputs is not None and not cohort_policy_ok:
        step08_input_detail = (
            "explicit cohort identity or legacy_provisional_v1 policy mismatch"
        )
    step08_sites = None
    step08_sites_detail = "Step 08 input prerequisite failed"
    if (
        sample_result is not None
        and partition_table is not None
        and step08_inputs is not None
    ):
        step08_sites, step08_sites_detail = attempt(
            lambda: step08.validate_step08_sites(
                paths["step08_sites"],
                sample_result[1],
                partition_table.rows,
                step08_inputs.rows,
            )
        )

    expected_result_header = None
    if sample_result is not None:
        expected_result_header = (
            step09.STEP09_RESULT_HEADER
            + tuple(f"DP__{sample}" for sample in sample_result[1])
            + tuple(f"AD__{sample}" for sample in sample_result[1])
            + tuple(f"AF__{sample}" for sample in sample_result[1])
        )
    observed_headers, header_detail = attempt(
        lambda: (
            header(paths["all_sites"]),
            header(paths["significant_sites"]),
            header(paths["summary"]),
            header(paths["mutation_spectrum"]),
        )
    )
    transaction_ok = (
        transaction_ok
        and expected_result_header is not None
        and observed_headers
        == (
            expected_result_header,
            expected_result_header,
            step09.STEP09_SUMMARY_HEADER,
            step09.STEP09_MUTATION_HEADER,
        )
    )

    all_sites = None
    significant_sites = None
    result_detail = "Step 08 prerequisite failed"
    if sample_result is not None and step08_sites is not None:
        all_sites, all_detail = attempt(
            lambda: step09.validate_step09_results(
                "Step 09 all-sites",
                paths["all_sites"],
                sample_result[1],
                args.analysis_id,
                step08_sites.rows,
            )
        )
        significant_sites, significant_detail = attempt(
            lambda: step09.validate_step09_results(
                "Step 09 significant-sites",
                paths["significant_sites"],
                sample_result[1],
                args.analysis_id,
                step08_sites.rows,
            )
        )
        result_detail = f"all={all_detail}; significant={significant_detail}"
    candidate_order_ok = (
        all_sites is not None
        and step08_sites is not None
        and [row["candidate_id"] for row in all_sites.rows]
        == [row["candidate_id"] for row in step08_sites.rows]
    )
    if all_sites is not None and not candidate_order_ok:
        result_detail = (
            "all-sites candidate order/universe differs from Step 08"
        )

    summary = None
    summary_detail = "result or upstream prerequisite failed"
    if (
        sample_result is not None
        and step08_inputs is not None
        and all_sites is not None
    ):
        summary, summary_detail = attempt(
            lambda: step09.validate_step09_summary(
                paths["summary"],
                args.analysis_id,
                args.cohort_id,
                sample_result[1],
                sample_result[2],
                all_sites.rows,
                paths["sample_manifest"],
                paths["partition_manifest"],
                paths["step08_sites"],
                paths["step08_inputs"],
                step08.sha256_file(paths["sample_manifest"]),
                step08.sha256_file(paths["partition_manifest"]),
                step08.sha256_file(paths["step08_sites"]),
                step08.sha256_file(paths["step08_inputs"]),
                step08_inputs.rows[0]["orientation_policy"],
            )
        )
    semantic_ok = False
    semantic_detail = "result or summary prerequisite failed"
    if summary is not None and all_sites is not None and sample_result is not None:
        _, semantic_detail = attempt(
            lambda: step09.validate_step09_result_semantics(
                all_sites.rows, summary.rows[0], sample_result[2]
            )
        )
        semantic_ok = semantic_detail == "validated"

    subset_ok = False
    subset_detail = "result prerequisite failed"
    if all_sites is not None and significant_sites is not None:
        subset_result, subset_detail = attempt(
            lambda: step09.validate_significant_subset(
                all_sites.rows, significant_sites.rows
            )
        )
        subset_ok = subset_detail == "validated"

    mutation = None
    mutation_detail = "all-sites prerequisite failed"
    if all_sites is not None:
        mutation, mutation_detail = attempt(
            lambda: step09.validate_mutation_spectrum(
                paths["mutation_spectrum"], args.analysis_id, all_sites.rows
            )
        )

    _, mutation_pdf_detail = attempt(
        lambda: step09.validate_pdf(
            "Step 09 mutation-spectrum PDF", paths["mutation_spectrum_pdf"]
        )
    )
    _, depth_pdf_detail = attempt(
        lambda: step09.validate_pdf(
            "Step 09 depth-delta PDF", paths["depth_delta_pdf"]
        )
    )
    pdf_ok = mutation_pdf_detail == depth_pdf_detail == "validated"
    scope_id = args.analysis_id

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "09", scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item(
            "output_transaction",
            transaction_ok,
            f"headers={header_detail}; six regular snapshots",
            "four exact TSV headers; analysis-bound basenames; one parent; "
            "six distinct physical files",
            "native Step 09 output transaction",
        ),
        item(
            "upstream_identity_and_candidate_order",
            (
                id_detail == "validated"
                and cohort_policy_ok
                and candidate_order_ok
                and significant_sites is not None
            ),
            result_detail,
            "safe analysis/cohort; provisional policy; complete ordered "
            "Step 08 candidate universe",
            f"ids={id_detail}; sample={sample_detail}; "
            f"partition={partition_detail}; inputs={step08_input_detail}; "
            f"sites={step08_sites_detail}",
        ),
        item(
            "status_semantics",
            semantic_ok,
            semantic_detail,
            "recomputed target/test/call, depth, AF, background, CMH, and BH",
            "native Step 09 statistical-state contract",
        ),
        item("significant_subset", subset_ok, subset_detail,
             "exact ordered significant subset", "all-sites versus significant-sites"),
        item(
            "summary_count_reconciliation",
            summary is not None,
            summary_detail,
            "one analysis/cohort-bound summary with exact counts and provenance",
            "paths, hashes, pairings, context, policy, and thresholds",
        ),
        item("mutation_spectrum_reconciliation", mutation is not None, mutation_detail,
             "canonical 12-SNV spectrum matching all-sites",
             "mutation counts, fractions, and significant directions"),
        item("pdf_structure", pdf_ok,
             f"mutation={mutation_pdf_detail}; depth={depth_pdf_detail}",
             "two structurally valid PDFs", "plot output containers"),
    ]
    data = report.render(rows)
    report.validate_report(data, scope_id, step_id="09", check_ids=CHECK_IDS)
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
        report.publish(args.output, data, args.analysis_id, step_id="09", check_ids=CHECK_IDS)
        print(f"Published Step 09 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, csv.Error, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
