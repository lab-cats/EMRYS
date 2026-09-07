#!/usr/bin/env python3
"""Plan, run, and verify deterministic shards of the behavioral Python suite."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
DEFAULT_DURATION_BASELINE = Path("tests/baselines/python_test_durations.json")
DEFAULT_IGNORES = (
    "tests/test_package_distribution.py",
    "tests/test_python_test_shards.py",
)
DEFAULT_REPORTED_DURATIONS = 50


class ShardError(RuntimeError):
    """Raised when a shard cannot be planned, run, or verified safely."""


@dataclass(frozen=True)
class DurationBaseline:
    """Reviewed duration estimates used only to balance shard assignments."""

    default_seconds: float
    durations_seconds: dict[str, float]


@dataclass(frozen=True)
class ShardPlan:
    """One deterministic complete assignment of node IDs to shards."""

    nodeids: tuple[str, ...]
    estimated_seconds: tuple[float, ...]


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def nodeids_digest(nodeids: Sequence[str]) -> str:
    """Return a stable digest for an ordered node-ID sequence."""
    payload = "".join(f"{nodeid}\n" for nodeid in nodeids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def require_shard_coordinates(index: int, count: int) -> None:
    """Require a zero-based shard index within a positive shard count."""
    if count < 1:
        raise ShardError(f"shard count must be positive; observed {count}")
    if index < 0 or index >= count:
        raise ShardError(
            f"shard index must be between 0 and {count - 1}; observed {index}"
        )


def load_duration_baseline(path: Path) -> DurationBaseline:
    """Load and validate the reviewed duration-estimate baseline."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ShardError(f"cannot read duration baseline {path}: {exc}") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ShardError(
            f"unsupported duration baseline schema in {path}: "
            f"{payload.get('schema_version')!r}"
        )
    default_seconds = payload.get("default_seconds")
    durations = payload.get("durations_seconds")
    if not isinstance(default_seconds, (int, float)) or default_seconds <= 0:
        raise ShardError("duration baseline default_seconds must be positive")
    if not isinstance(durations, dict):
        raise ShardError("duration baseline durations_seconds must be an object")
    validated: dict[str, float] = {}
    for nodeid, seconds in durations.items():
        if not isinstance(nodeid, str) or not nodeid:
            raise ShardError("duration baseline node IDs must be non-empty strings")
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            raise ShardError(f"duration estimate must be positive for {nodeid}")
        validated[nodeid] = float(seconds)
    return DurationBaseline(float(default_seconds), validated)


def collection_command() -> tuple[str, ...]:
    """Build the bounded collection command for the behavioral suite."""
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    for ignored in DEFAULT_IGNORES:
        command.append(f"--ignore={ignored}")
    return tuple(command)


def collect_nodeids(
    repo_root: Path,
    *,
    command_runner: CommandRunner = subprocess.run,
) -> tuple[str, ...]:
    """Collect the complete behavioral-suite node-ID inventory."""
    environment = os.environ.copy()
    environment["PYTEST_ADDOPTS"] = ""
    result = command_runner(
        collection_command(),
        cwd=repo_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ShardError(
            "behavioral test collection failed"
            + (f"\n{detail}" if detail else "")
        )
    nodeids = tuple(line for line in result.stdout.splitlines() if "::" in line)
    if not nodeids:
        raise ShardError("behavioral test collection returned no node IDs")
    if len(nodeids) != len(set(nodeids)):
        raise ShardError("behavioral test collection returned duplicate node IDs")
    return tuple(sorted(nodeids))


def plan_shards(
    nodeids: Sequence[str],
    shard_count: int,
    baseline: DurationBaseline,
) -> tuple[ShardPlan, ...]:
    """Balance tests with deterministic longest-processing-time assignment."""
    require_shard_coordinates(0, shard_count)
    if len(nodeids) != len(set(nodeids)):
        raise ShardError("cannot plan duplicate node IDs")
    unknown = set(baseline.durations_seconds) - set(nodeids)
    if unknown:
        examples = ", ".join(sorted(unknown)[:3])
        raise ShardError(
            "duration baseline contains node IDs absent from collection: " + examples
        )

    assignments: list[list[str]] = [[] for _ in range(shard_count)]
    estimated = [0.0] * shard_count
    queue = [(0.0, 0, index) for index in range(shard_count)]
    heapq.heapify(queue)
    weighted = sorted(
        (
            (baseline.durations_seconds.get(nodeid, baseline.default_seconds), nodeid)
            for nodeid in nodeids
        ),
        key=lambda item: (-item[0], item[1]),
    )
    for seconds, nodeid in weighted:
        load, item_count, shard_index = heapq.heappop(queue)
        assignments[shard_index].append(nodeid)
        estimated[shard_index] = load + seconds
        heapq.heappush(queue, (load + seconds, item_count + 1, shard_index))

    return tuple(
        ShardPlan(tuple(sorted(selected)), estimated[index])
        for index, selected in enumerate(assignments)
    )


def receipt_payload(
    *,
    all_nodeids: Sequence[str],
    plan: ShardPlan,
    shard_index: int,
    shard_count: int,
) -> dict[str, Any]:
    """Build one auditable shard-selection receipt."""
    return {
        "schema_version": SCHEMA_VERSION,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "collected_count": len(all_nodeids),
        "collected_sha256": nodeids_digest(all_nodeids),
        "selected_count": len(plan.nodeids),
        "selected_sha256": nodeids_digest(plan.nodeids),
        "estimated_seconds": round(plan.estimated_seconds, 3),
        "nodeids": list(plan.nodeids),
    }


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    """Write a stable selection receipt before executing its tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def pytest_command(nodeids: Sequence[str], workers: int) -> tuple[str, ...]:
    """Build the live-output pytest command for one exact selection."""
    if workers < 1:
        raise ShardError(f"worker count must be positive; observed {workers}")
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--tb=short",
        f"--durations={DEFAULT_REPORTED_DURATIONS}",
    ]
    if workers > 1:
        command.extend(("-n", str(workers), "--dist=worksteal"))
    command.extend(nodeids)
    return tuple(command)


def run_pytest_in_process(command: Sequence[str], repo_root: Path) -> int:
    """Run pytest under an active coverage controller with repository imports."""
    previous_cwd = Path.cwd()
    repo_root_text = str(repo_root)
    inserted_path = repo_root_text not in sys.path
    previous_addopts = os.environ.get("PYTEST_ADDOPTS")
    os.environ["PYTEST_ADDOPTS"] = ""
    try:
        os.chdir(repo_root)
        if inserted_path:
            sys.path.insert(0, repo_root_text)
        import pytest

        return int(pytest.main(list(command[3:])))
    finally:
        os.chdir(previous_cwd)
        if inserted_path:
            sys.path.remove(repo_root_text)
        if previous_addopts is None:
            os.environ.pop("PYTEST_ADDOPTS", None)
        else:
            os.environ["PYTEST_ADDOPTS"] = previous_addopts


def run_shard(
    *,
    repo_root: Path,
    shard_index: int,
    shard_count: int,
    workers: int,
    duration_baseline: Path,
    receipt: Path,
    command_runner: CommandRunner | None = None,
) -> int:
    """Plan one shard, record its selection, and execute every selected test."""
    require_shard_coordinates(shard_index, shard_count)
    collector = command_runner or subprocess.run
    all_nodeids = collect_nodeids(repo_root, command_runner=collector)
    baseline = load_duration_baseline(duration_baseline)
    plans = plan_shards(all_nodeids, shard_count, baseline)
    selected = plans[shard_index]
    write_receipt(
        receipt,
        receipt_payload(
            all_nodeids=all_nodeids,
            plan=selected,
            shard_index=shard_index,
            shard_count=shard_count,
        ),
    )
    print(
        f"SHARD {shard_index + 1}/{shard_count}: "
        f"{len(selected.nodeids)}/{len(all_nodeids)} tests, "
        f"estimated {selected.estimated_seconds:.1f}s",
        flush=True,
    )
    environment = os.environ.copy()
    environment["PYTEST_ADDOPTS"] = ""
    command = pytest_command(selected.nodeids, workers)
    if command_runner is not None:
        result = command_runner(
            command,
            cwd=repo_root,
            env=environment,
            text=True,
            check=False,
        )
        return result.returncode
    return run_pytest_in_process(command, repo_root)


def load_receipt(path: Path) -> dict[str, Any]:
    """Load one shard receipt with bounded structural validation."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ShardError(f"cannot read shard receipt {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ShardError(f"unsupported shard receipt: {path}")
    return payload


def verify_receipts(
    *,
    receipts: Sequence[tuple[Path, dict[str, Any]]],
    all_nodeids: Sequence[str],
    baseline: DurationBaseline,
) -> None:
    """Require receipts to prove one complete, disjoint deterministic plan."""
    if not receipts:
        raise ShardError("no shard receipts were found")
    shard_counts = {payload.get("shard_count") for _, payload in receipts}
    if len(shard_counts) != 1:
        raise ShardError("shard receipts disagree on shard_count")
    shard_count = next(iter(shard_counts))
    if not isinstance(shard_count, int) or shard_count < 1:
        raise ShardError("shard receipt count must be a positive integer")
    if len(receipts) != shard_count:
        raise ShardError(
            f"expected {shard_count} shard receipts; observed {len(receipts)}"
        )
    expected_digest = nodeids_digest(all_nodeids)
    expected_plans = plan_shards(all_nodeids, shard_count, baseline)
    seen_indices: set[int] = set()
    seen_nodeids: set[str] = set()
    for path, payload in receipts:
        index = payload.get("shard_index")
        if not isinstance(index, int):
            raise ShardError(f"shard receipt has invalid index: {path}")
        require_shard_coordinates(index, shard_count)
        if index in seen_indices:
            raise ShardError(f"duplicate shard index {index}")
        seen_indices.add(index)
        nodeids = payload.get("nodeids")
        if not isinstance(nodeids, list) or not all(
            isinstance(nodeid, str) for nodeid in nodeids
        ):
            raise ShardError(f"shard receipt has invalid node IDs: {path}")
        selected = tuple(nodeids)
        expected = expected_plans[index].nodeids
        if selected != expected:
            raise ShardError(f"shard {index} selection differs from deterministic plan")
        if payload.get("collected_count") != len(all_nodeids):
            raise ShardError(f"shard {index} collected count is stale")
        if payload.get("collected_sha256") != expected_digest:
            raise ShardError(f"shard {index} collection digest is stale")
        if payload.get("selected_count") != len(selected):
            raise ShardError(f"shard {index} selected count is inconsistent")
        if payload.get("selected_sha256") != nodeids_digest(selected):
            raise ShardError(f"shard {index} selection digest is inconsistent")
        duplicates = seen_nodeids.intersection(selected)
        if duplicates:
            raise ShardError(f"duplicate test selection: {sorted(duplicates)[0]}")
        seen_nodeids.update(selected)
    if seen_nodeids != set(all_nodeids):
        missing = sorted(set(all_nodeids) - seen_nodeids)
        extra = sorted(seen_nodeids - set(all_nodeids))
        raise ShardError(
            "shard receipts do not cover the current suite exactly"
            f"; missing={missing[:3]!r}; extra={extra[:3]!r}"
        )


def verify_receipt_directory(
    *,
    repo_root: Path,
    receipt_dir: Path,
    duration_baseline: Path,
) -> None:
    """Verify every receipt below a downloaded artifact directory."""
    paths = sorted(receipt_dir.rglob("python-test-shard-*.json"))
    receipts = tuple((path, load_receipt(path)) for path in paths)
    all_nodeids = collect_nodeids(repo_root)
    baseline = load_duration_baseline(duration_baseline)
    verify_receipts(receipts=receipts, all_nodeids=all_nodeids, baseline=baseline)
    print(
        f"VERIFIED {len(receipts)} shards cover {len(all_nodeids)} tests exactly",
        flush=True,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the test-only sharding interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run one deterministic shard")
    run_parser.add_argument("--repo-root", type=Path, required=True)
    run_parser.add_argument("--shard-index", type=int, required=True)
    run_parser.add_argument("--shard-count", type=int, required=True)
    run_parser.add_argument("--workers", type=int, default=2)
    run_parser.add_argument(
        "--duration-baseline",
        type=Path,
        default=DEFAULT_DURATION_BASELINE,
    )
    run_parser.add_argument("--receipt", type=Path, required=True)
    verify_parser = subparsers.add_parser(
        "verify", help="verify downloaded shard receipts"
    )
    verify_parser.add_argument("--repo-root", type=Path, required=True)
    verify_parser.add_argument("--receipt-dir", type=Path, required=True)
    verify_parser.add_argument(
        "--duration-baseline",
        type=Path,
        default=DEFAULT_DURATION_BASELINE,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested test-only sharding operation."""
    args = parse_args(argv)
    try:
        repo_root = args.repo_root.resolve(strict=True)
        duration_baseline = args.duration_baseline
        if not duration_baseline.is_absolute():
            duration_baseline = repo_root / duration_baseline
        if args.command == "run":
            return run_shard(
                repo_root=repo_root,
                shard_index=args.shard_index,
                shard_count=args.shard_count,
                workers=args.workers,
                duration_baseline=duration_baseline,
                receipt=args.receipt,
            )
        verify_receipt_directory(
            repo_root=repo_root,
            receipt_dir=args.receipt_dir,
            duration_baseline=duration_baseline,
        )
    except (OSError, ShardError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
