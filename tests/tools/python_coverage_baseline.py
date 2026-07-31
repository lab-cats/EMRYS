#!/usr/bin/env python3
"""Build and check deterministic NORAD Python coverage snapshots."""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys
from typing import Any, Sequence


SCHEMA_VERSION = "1.0.0"
COVERAGE_VERSION = "7.15.2"
SOURCE_ROOTS = ("scripts",)
REQUIRED_SUBPROCESS_FILES = (
    "scripts/gtf_to_bed12.py",
    "scripts/validate_manifest.py",
)
NEW_SHARED_LINE_MINIMUM = (90, 100)
NEW_SHARED_BRANCH_MINIMUM = (85, 100)
COUNT_FIELDS = (
    "covered_lines",
    "num_statements",
    "covered_branches",
    "num_branches",
)


class SnapshotError(ValueError):
    """Raised when coverage input or a snapshot violates the baseline contract."""


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


def normalized_source_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise SnapshotError("Coverage source path must be a nonempty string")
    path = value.replace("\\", "/")
    if path.startswith("/") or path != str(Path(path).as_posix()):
        raise SnapshotError(f"Coverage source path is not normalized: {value}")
    if ".." in Path(path).parts or not path.endswith(".py"):
        raise SnapshotError(f"Coverage source path is outside the Python policy: {value}")
    if not any(path.startswith(f"{root}/") for root in SOURCE_ROOTS):
        raise SnapshotError(f"Coverage source path is outside scripts/: {value}")
    return path


def counts_from_summary(summary: Any, label: str) -> dict[str, int]:
    payload = require_mapping(summary, label)
    return {
        field: require_count(payload.get(field), f"{label}.{field}")
        for field in COUNT_FIELDS
    }


def measured_file(path: str, summary: Any) -> dict[str, Any]:
    counts = counts_from_summary(summary, f"{path}.summary")
    if counts["covered_lines"] > counts["num_statements"]:
        raise SnapshotError(f"{path} covered lines exceed statements")
    if counts["covered_branches"] > counts["num_branches"]:
        raise SnapshotError(f"{path} covered branches exceed branches")
    return {
        "path": path,
        **counts,
        "line_rate": rate_text(
            counts["covered_lines"], counts["num_statements"]
        ),
        "branch_rate": rate_text(
            counts["covered_branches"], counts["num_branches"]
        ),
    }


def build_snapshot(document: Any) -> dict[str, Any]:
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
    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_path, details in raw_files.items():
        path = normalized_source_path(raw_path)
        if path in seen:
            raise SnapshotError(f"Duplicate normalized coverage path: {path}")
        seen.add(path)
        summary = require_mapping(details, f"coverage file {path}").get("summary")
        files.append(measured_file(path, summary))
    files.sort(key=lambda item: item["path"])
    if not files:
        raise SnapshotError("Coverage input contains no scripts/*.py files")

    aggregate = {field: sum(item[field] for item in files) for field in COUNT_FIELDS}
    declared_totals = counts_from_summary(
        payload.get("totals"), "coverage document.totals"
    )
    if aggregate != declared_totals:
        raise SnapshotError(
            "Coverage totals do not equal the sum of per-file counts: "
            f"declared={declared_totals}, calculated={aggregate}"
        )

    file_map = {item["path"]: item for item in files}
    for required in REQUIRED_SUBPROCESS_FILES:
        if required not in file_map or file_map[required]["covered_lines"] == 0:
            raise SnapshotError(
                "Subprocess coverage is missing for required file: " f"{required}"
            )

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
        },
        "policy": {
            "global_non_regression": ["line_rate", "branch_rate"],
            "new_shared_python_module_minimum": {
                "line_rate": rate_text(*NEW_SHARED_LINE_MINIMUM),
                "branch_rate": rate_text(*NEW_SHARED_BRANCH_MINIMUM),
            },
            "required_subprocess_coverage": list(REQUIRED_SUBPROCESS_FILES),
        },
        "totals": {
            **aggregate,
            "line_rate": rate_text(
                aggregate["covered_lines"], aggregate["num_statements"]
            ),
            "branch_rate": rate_text(
                aggregate["covered_branches"], aggregate["num_branches"]
            ),
        },
        "files": files,
    }


def validate_snapshot(document: Any, label: str) -> dict[str, Any]:
    payload = require_mapping(document, label)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise SnapshotError(f"{label} has an unsupported schema_version")
    expected_tool = {"name": "coverage.py", "version": COVERAGE_VERSION}
    if payload.get("tool") != expected_tool:
        raise SnapshotError(f"{label} has an unexpected coverage tool identity")
    expected_measurement = {
        "branch": True,
        "source": list(SOURCE_ROOTS),
        "subprocess": True,
        "test_command": [".venv/bin/python", "-m", "pytest"],
    }
    if payload.get("measurement") != expected_measurement:
        raise SnapshotError(f"{label} has an unexpected measurement policy")
    expected_policy = {
        "global_non_regression": ["line_rate", "branch_rate"],
        "new_shared_python_module_minimum": {
            "line_rate": rate_text(*NEW_SHARED_LINE_MINIMUM),
            "branch_rate": rate_text(*NEW_SHARED_BRANCH_MINIMUM),
        },
        "required_subprocess_coverage": list(REQUIRED_SUBPROCESS_FILES),
    }
    if payload.get("policy") != expected_policy:
        raise SnapshotError(f"{label} has an unexpected coverage policy")

    raw_files = payload.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise SnapshotError(f"{label}.files must be a nonempty array")
    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_files):
        entry = require_mapping(item, f"{label}.files[{index}]")
        path = normalized_source_path(entry.get("path"))
        if path in seen:
            raise SnapshotError(f"{label} repeats coverage file {path}")
        seen.add(path)
        counts = {
            field: require_count(
                entry.get(field), f"{label}.files[{index}].{field}"
            )
            for field in COUNT_FIELDS
        }
        expected = measured_file(path, counts)
        if entry != expected:
            raise SnapshotError(f"{label}.files[{index}] is not canonical")
        files.append(entry)
    if [item["path"] for item in files] != sorted(item["path"] for item in files):
        raise SnapshotError(f"{label}.files must be sorted by path")

    aggregate = {field: sum(item[field] for item in files) for field in COUNT_FIELDS}
    expected_totals = {
        **aggregate,
        "line_rate": rate_text(
            aggregate["covered_lines"], aggregate["num_statements"]
        ),
        "branch_rate": rate_text(
            aggregate["covered_branches"], aggregate["num_branches"]
        ),
    }
    if payload.get("totals") != expected_totals:
        raise SnapshotError(f"{label}.totals do not reconcile with files")
    return payload


def ratio_is_at_least(
    covered: int, total: int, minimum_covered: int, minimum_total: int
) -> bool:
    if total == 0:
        return True
    return covered * minimum_total >= minimum_covered * total


def compare_snapshots(
    baseline_document: Any,
    current_document: Any,
    new_shared_modules: Sequence[str] = (),
) -> str:
    baseline = validate_snapshot(baseline_document, "baseline")
    current = validate_snapshot(current_document, "current")
    baseline_files = {item["path"]: item for item in baseline["files"]}
    current_files = {item["path"]: item for item in current["files"]}

    removed = sorted(set(baseline_files) - set(current_files))
    if removed:
        raise SnapshotError(
            "Measured Python source disappeared from the baseline: "
            + ", ".join(removed)
        )

    baseline_totals = baseline["totals"]
    current_totals = current["totals"]
    for label, covered_field, total_field in (
        ("line", "covered_lines", "num_statements"),
        ("branch", "covered_branches", "num_branches"),
    ):
        if not ratio_is_at_least(
            current_totals[covered_field],
            current_totals[total_field],
            baseline_totals[covered_field],
            baseline_totals[total_field],
        ):
            raise SnapshotError(
                f"Global Python {label} coverage regressed: "
                f"{current_totals[label + '_rate']} < "
                f"{baseline_totals[label + '_rate']}"
            )

    for raw_path in new_shared_modules:
        path = normalized_source_path(raw_path)
        if path in baseline_files:
            raise SnapshotError(
                f"New shared module was already present in the baseline: {path}"
            )
        if path not in current_files:
            raise SnapshotError(f"New shared module is not measured: {path}")
        entry = current_files[path]
        if not ratio_is_at_least(
            entry["covered_lines"],
            entry["num_statements"],
            *NEW_SHARED_LINE_MINIMUM,
        ):
            raise SnapshotError(
                f"New shared module line coverage is below 90%: {path}"
            )
        if not ratio_is_at_least(
            entry["covered_branches"],
            entry["num_branches"],
            *NEW_SHARED_BRANCH_MINIMUM,
        ):
            raise SnapshotError(
                f"New shared module branch coverage is below 85%: {path}"
            )

    return (
        "Python coverage check passed: "
        f"line={current_totals['line_rate']} "
        f"branch={current_totals['branch_rate']} "
        f"files={len(current_files)}"
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
        "build", help="Build a deterministic snapshot from coverage JSON."
    )
    build.add_argument("--coverage-json", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)

    check = subparsers.add_parser(
        "check", help="Check current coverage against the tracked baseline."
    )
    check.add_argument("--baseline", required=True, type=Path)
    check.add_argument("--current", required=True, type=Path)
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
            snapshot = build_snapshot(load_json(args.coverage_json))
            write_snapshot(args.output, snapshot)
            totals = snapshot["totals"]
            print(
                "Python coverage snapshot built: "
                f"line={totals['line_rate']} "
                f"branch={totals['branch_rate']} "
                f"files={len(snapshot['files'])}"
            )
        else:
            print(
                compare_snapshots(
                    load_json(args.baseline),
                    load_json(args.current),
                    args.new_shared_module,
                )
            )
    except SnapshotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
