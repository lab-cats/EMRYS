#!/usr/bin/env python3
"""Build and check compact NORAD Python coverage policies."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "2.0.0"
COVERAGE_VERSION = "7.15.2"
SOURCE_ROOTS = ("scripts", "src/norad")
NEW_SHARED_LINE_MINIMUM = (90, 100)
NEW_SHARED_BRANCH_MINIMUM = (85, 100)
COUNT_FIELDS = (
    "covered_lines",
    "num_statements",
    "covered_branches",
    "num_branches",
)
CRITICAL_OWNER_GROUPS: Mapping[str, tuple[str, ...]] = {
    "norad.contracts.scientific_evidence": (
        "src/norad/contracts/scientific_evidence/",
    ),
    "norad.libraries.validation": ("src/norad/libraries/validation/",),
    "shared_scientific_validation_primitives": (
        "src/norad/libraries/alignments/",
        "src/norad/libraries/evidence/",
        "src/norad/libraries/quality/",
        "src/norad/libraries/references/",
    ),
    "report_publication_and_receipt_validation": (
        "src/norad/contracts/artifacts/",
        "src/norad/reporting/",
    ),
    "scientific_review_publication": ("src/norad/evidence/scientific_review_package/",),
    "paired_cmh_analysis_contracts": (
        "src/norad/analyses/paired_cmh_candidate_ranking/",
    ),
}
REQUIRED_SUBPROCESS_ROUTES: Mapping[str, tuple[str, ...]] = {
    "norad.convert.gtf_to_bed12": ("src/norad/stages/gtf_to_bed12/converter.py",),
    "norad.validate.sample_manifest": (
        "src/norad/ingestion/sample_manifest_admission/validator.py",
    ),
}
SUBPROCESS_TEST_COMMAND = (
    ".venv/bin/python",
    "-m",
    "pytest",
    "-q",
    "tests/stages/gtf_to_bed12/test_gtf_to_bed12.py",
    "tests/ingestion/sample_manifest_admission/test_validate_manifest.py",
)


class SnapshotError(ValueError):
    """Raised when coverage input or a snapshot violates the policy."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    if not path.is_file() or path.is_symlink():
        raise SnapshotError(f"Expected a regular non-symlink JSON file: {path}")
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                SnapshotError(f"Non-standard JSON numeric constant: {value}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Could not read strict JSON from {path}: {exc}") from exc


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotError(f"{label} must be a JSON object")
    return value


def require_count(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SnapshotError(f"{label} must be a nonnegative integer")
    return value


def rate_text(covered: int, total: int) -> str:
    if total == 0:
        return "1.000000"
    value = Decimal(covered) / Decimal(total)
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def policy_groups(groups: Mapping[str, tuple[str, ...]]) -> dict[str, list[str]]:
    return {name: list(prefixes) for name, prefixes in groups.items()}


def snapshot_contract() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": {
            "name": "coverage.py",
            "version": COVERAGE_VERSION,
        },
        "measurement": {
            "branch": True,
            "source": list(SOURCE_ROOTS),
            "subprocess": True,
            "test_command": [".venv/bin/python", "-m", "pytest"],
            "subprocess_test_command": list(SUBPROCESS_TEST_COMMAND),
        },
        "policy": {
            "global_non_regression": ["line_rate", "branch_rate"],
            "critical_owner_non_regression": policy_groups(CRITICAL_OWNER_GROUPS),
            "new_shared_python_module_minimum": {
                "line_rate": rate_text(*NEW_SHARED_LINE_MINIMUM),
                "branch_rate": rate_text(*NEW_SHARED_BRANCH_MINIMUM),
            },
            "required_subprocess_coverage": policy_groups(REQUIRED_SUBPROCESS_ROUTES),
        },
    }


def normalized_source_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise SnapshotError("Coverage source path must be a nonempty string")
    path = value.replace("\\", "/")
    if path.startswith("/") or path != str(Path(path).as_posix()):
        raise SnapshotError(f"Coverage source path is not normalized: {value}")
    if ".." in Path(path).parts or not path.endswith(".py"):
        raise SnapshotError(
            f"Coverage source path is outside the Python policy: {value}"
        )
    if not any(path.startswith(f"{root}/") for root in SOURCE_ROOTS):
        raise SnapshotError(
            f"Coverage source path is outside configured roots: {value}"
        )
    return path


def counts_from_summary(summary: Any, label: str) -> dict[str, int]:
    payload = require_mapping(summary, label)
    counts = {
        field: require_count(payload.get(field), f"{label}.{field}")
        for field in COUNT_FIELDS
    }
    if counts["covered_lines"] > counts["num_statements"]:
        raise SnapshotError(f"{label} covered lines exceed statements")
    if counts["covered_branches"] > counts["num_branches"]:
        raise SnapshotError(f"{label} covered branches exceed branches")
    return counts


def measurement(counts: Mapping[str, int]) -> dict[str, Any]:
    return {
        **counts,
        "line_rate": rate_text(counts["covered_lines"], counts["num_statements"]),
        "branch_rate": rate_text(counts["covered_branches"], counts["num_branches"]),
    }


def measured_files(document: Any) -> dict[str, dict[str, int]]:
    payload = require_mapping(document, "coverage document")
    meta = require_mapping(payload.get("meta"), "coverage document.meta")
    if meta.get("version") != COVERAGE_VERSION:
        raise SnapshotError(
            "Coverage version mismatch: "
            f"expected {COVERAGE_VERSION}, observed {meta.get('version')!r}"
        )
    if meta.get("branch_coverage") is not True:
        raise SnapshotError("Coverage input must include branch coverage")

    raw_files = require_mapping(payload.get("files"), "coverage document.files")
    files: dict[str, dict[str, int]] = {}
    for raw_path, details in raw_files.items():
        path = normalized_source_path(raw_path)
        if path in files:
            raise SnapshotError(f"Duplicate normalized coverage path: {path}")
        summary = require_mapping(details, f"coverage file {path}").get("summary")
        files[path] = counts_from_summary(summary, f"{path}.summary")
    if not files:
        raise SnapshotError("Coverage input contains no configured Python source files")

    aggregate = aggregate_counts(files.values())
    declared_totals = counts_from_summary(
        payload.get("totals"), "coverage document.totals"
    )
    if aggregate != declared_totals:
        raise SnapshotError(
            "Coverage totals do not equal the sum of per-file counts: "
            f"declared={declared_totals}, calculated={aggregate}"
        )
    return files


def aggregate_counts(entries: Iterable[Mapping[str, int]]) -> dict[str, int]:
    return {field: sum(entry[field] for entry in entries) for field in COUNT_FIELDS}


def files_for_prefixes(
    files: Mapping[str, Mapping[str, int]], prefixes: Sequence[str]
) -> list[Mapping[str, int]]:
    return [
        counts
        for path, counts in files.items()
        if any(path.startswith(prefix) for prefix in prefixes)
    ]


def group_measurement(
    name: str,
    prefixes: Sequence[str],
    files: Mapping[str, Mapping[str, int]],
) -> dict[str, Any]:
    members = files_for_prefixes(files, prefixes)
    if not members:
        raise SnapshotError(f"Critical coverage owner has no measured files: {name}")
    counts = aggregate_counts(members)
    if counts["num_statements"] == 0:
        raise SnapshotError(f"Critical coverage owner has no statements: {name}")
    return {"name": name, "prefixes": list(prefixes), **measurement(counts)}


def subprocess_measurement(
    name: str,
    paths: Sequence[str],
    files: Mapping[str, Mapping[str, int]],
) -> dict[str, Any]:
    missing = [
        path for path in paths if path not in files or files[path]["covered_lines"] == 0
    ]
    if missing:
        raise SnapshotError(
            f"Subprocess coverage is missing for route {name}: {', '.join(missing)}"
        )
    return {
        "name": name,
        "paths": list(paths),
        "covered_lines": sum(files[path]["covered_lines"] for path in paths),
    }


def build_snapshot(document: Any, subprocess_document: Any) -> dict[str, Any]:
    files = measured_files(document)
    subprocess_files = measured_files(subprocess_document)
    totals = measurement(aggregate_counts(files.values()))
    return {
        **snapshot_contract(),
        "totals": totals,
        "critical_owners": [
            group_measurement(name, prefixes, files)
            for name, prefixes in CRITICAL_OWNER_GROUPS.items()
        ],
        "subprocess_routes": [
            subprocess_measurement(name, paths, subprocess_files)
            for name, paths in REQUIRED_SUBPROCESS_ROUTES.items()
        ],
    }


def validate_measurement(value: Any, label: str) -> dict[str, Any]:
    payload = require_mapping(value, label)
    counts = counts_from_summary(payload, label)
    expected = measurement(counts)
    if payload != expected:
        raise SnapshotError(f"{label} is not canonical")
    return payload


def validate_group_measurements(
    value: Any,
    label: str,
    groups: Mapping[str, tuple[str, ...]],
    totals: Mapping[str, int],
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(groups):
        raise SnapshotError(f"{label} has an unexpected owner roster")
    result: list[dict[str, Any]] = []
    for index, (name, prefixes) in enumerate(groups.items()):
        entry = require_mapping(value[index], f"{label}[{index}]")
        identity = {"name": name, "prefixes": list(prefixes)}
        if {key: entry.get(key) for key in identity} != identity:
            raise SnapshotError(f"{label}[{index}] has an unexpected owner identity")
        counts = validate_measurement(
            {
                key: entry.get(key)
                for key in (*COUNT_FIELDS, "line_rate", "branch_rate")
            },
            f"{label}[{index}]",
        )
        if entry != {**identity, **counts}:
            raise SnapshotError(f"{label}[{index}] is not canonical")
        if counts["num_statements"] == 0:
            raise SnapshotError(f"{label}[{index}] has no statements")
        if any(counts[field] > totals[field] for field in COUNT_FIELDS):
            raise SnapshotError(f"{label}[{index}] exceeds repository totals")
        result.append(entry)
    return result


def validate_subprocess_measurements(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(REQUIRED_SUBPROCESS_ROUTES):
        raise SnapshotError(f"{label} has an unexpected owner roster")
    result: list[dict[str, Any]] = []
    for index, (name, paths) in enumerate(REQUIRED_SUBPROCESS_ROUTES.items()):
        entry = require_mapping(value[index], f"{label}[{index}]")
        expected = {
            "name": name,
            "paths": list(paths),
            "covered_lines": require_count(
                entry.get("covered_lines"), f"{label}[{index}].covered_lines"
            ),
        }
        if entry != expected:
            raise SnapshotError(f"{label}[{index}] is not canonical")
        if entry["covered_lines"] == 0:
            raise SnapshotError(f"{label}[{index}] has no covered lines")
        result.append(entry)
    return result


def validate_snapshot(document: Any, label: str) -> dict[str, Any]:
    payload = require_mapping(document, label)
    expected_contract = snapshot_contract()
    expected_keys = {
        *expected_contract,
        "totals",
        "critical_owners",
        "subprocess_routes",
    }
    if set(payload) != expected_keys:
        raise SnapshotError(f"{label} has unexpected top-level fields")
    for field, problem in (
        ("schema_version", "unsupported schema_version"),
        ("tool", "unexpected coverage tool identity"),
        ("measurement", "unexpected measurement policy"),
        ("policy", "unexpected coverage policy"),
    ):
        if payload.get(field) != expected_contract[field]:
            raise SnapshotError(f"{label} has an {problem}")

    totals = validate_measurement(payload.get("totals"), f"{label}.totals")
    validate_group_measurements(
        payload.get("critical_owners"),
        f"{label}.critical_owners",
        CRITICAL_OWNER_GROUPS,
        totals,
    )
    subprocess_routes = validate_subprocess_measurements(
        payload.get("subprocess_routes"), f"{label}.subprocess_routes"
    )
    if any(
        item["covered_lines"] > totals["covered_lines"] for item in subprocess_routes
    ):
        raise SnapshotError(f"{label}.subprocess_routes exceeds repository totals")
    return payload


def ratio_is_at_least(
    covered: int, total: int, minimum_covered: int, minimum_total: int
) -> bool:
    if total == 0:
        return True
    return covered * minimum_total >= minimum_covered * total


def require_non_regression(
    label: str,
    baseline: Mapping[str, int],
    current: Mapping[str, int],
) -> None:
    for rate_name, covered_field, total_field in (
        ("line", "covered_lines", "num_statements"),
        ("branch", "covered_branches", "num_branches"),
    ):
        if not ratio_is_at_least(
            current[covered_field],
            current[total_field],
            baseline[covered_field],
            baseline[total_field],
        ):
            raise SnapshotError(
                f"{label} {rate_name} coverage regressed: "
                f"{current[rate_name + '_rate']} < {baseline[rate_name + '_rate']}"
            )


def compare_snapshots(baseline_document: Any, current_document: Any) -> str:
    baseline = validate_snapshot(baseline_document, "baseline")
    current = validate_snapshot(current_document, "current")
    require_non_regression("Global Python", baseline["totals"], current["totals"])

    for baseline_group, current_group in zip(
        baseline["critical_owners"], current["critical_owners"], strict=True
    ):
        require_non_regression(
            f"Critical owner {baseline_group['name']}",
            baseline_group,
            current_group,
        )

    return (
        "Python coverage check passed: "
        f"line={current['totals']['line_rate']} "
        f"branch={current['totals']['branch_rate']} "
        f"critical_owners={len(current['critical_owners'])}"
    )


def validate_new_shared_modules(document: Any, raw_paths: Sequence[str]) -> None:
    if not raw_paths:
        return
    files = measured_files(document)
    for raw_path in raw_paths:
        path = normalized_source_path(raw_path)
        if path not in files:
            raise SnapshotError(f"New shared module is not measured: {path}")
        counts = files[path]
        if not ratio_is_at_least(
            counts["covered_lines"],
            counts["num_statements"],
            *NEW_SHARED_LINE_MINIMUM,
        ):
            raise SnapshotError(f"New shared module line coverage is below 90%: {path}")
        if not ratio_is_at_least(
            counts["covered_branches"],
            counts["num_branches"],
            *NEW_SHARED_BRANCH_MINIMUM,
        ):
            raise SnapshotError(
                f"New shared module branch coverage is below 85%: {path}"
            )


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise SnapshotError(f"Output parent must be a real directory: {path.parent}")
    if path.exists() and (not path.is_file() or path.is_symlink()):
        raise SnapshotError(f"Refusing unsafe snapshot output: {path}")
    payload = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser(
        "build", help="Build a deterministic compact policy from coverage JSON."
    )
    build.add_argument("--coverage-json", required=True, type=Path)
    build.add_argument("--subprocess-coverage-json", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)

    check = subparsers.add_parser(
        "check", help="Check current coverage against the tracked policy."
    )
    check.add_argument("--baseline", required=True, type=Path)
    check.add_argument("--current", required=True, type=Path)
    check.add_argument("--coverage-json", type=Path)
    check.add_argument(
        "--new-shared-module",
        action="append",
        default=[],
        help="Require 90%% line and 85%% branch coverage for a new shared module.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            snapshot = build_snapshot(
                load_json(args.coverage_json),
                load_json(args.subprocess_coverage_json),
            )
            write_snapshot(args.output, snapshot)
            print(
                "Python coverage policy built: "
                f"line={snapshot['totals']['line_rate']} "
                f"branch={snapshot['totals']['branch_rate']} "
                f"critical_owners={len(snapshot['critical_owners'])}"
            )
        else:
            if args.new_shared_module and args.coverage_json is None:
                raise SnapshotError(
                    "--coverage-json is required with --new-shared-module"
                )
            message = compare_snapshots(
                load_json(args.baseline),
                load_json(args.current),
            )
            if args.coverage_json is not None:
                validate_new_shared_modules(
                    load_json(args.coverage_json), args.new_shared_module
                )
            print(message)
    except SnapshotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
