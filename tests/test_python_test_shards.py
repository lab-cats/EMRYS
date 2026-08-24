"""Contract tests for deterministic behavioral-suite sharding."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from tests.tools import python_test_shards as TOOL


def baseline(*, durations: dict[str, float] | None = None) -> TOOL.DurationBaseline:
    return TOOL.DurationBaseline(1.0, durations or {})


def test_plan_is_deterministic_complete_disjoint_and_duration_aware() -> None:
    nodeids = tuple(f"tests/test_example.py::test_{index}" for index in range(12))
    slow = nodeids[7]
    durations = baseline(durations={slow: 20.0})

    first = TOOL.plan_shards(nodeids, 3, durations)
    second = TOOL.plan_shards(tuple(reversed(nodeids)), 3, durations)

    assert first == second
    assert sorted(nodeid for plan in first for nodeid in plan.nodeids) == sorted(nodeids)
    assert sum(slow in plan.nodeids for plan in first) == 1
    assert len({nodeid for plan in first for nodeid in plan.nodeids}) == len(nodeids)
    non_slow_loads = [
        plan.estimated_seconds for plan in first if slow not in plan.nodeids
    ]
    assert max(non_slow_loads) - min(non_slow_loads) <= durations.default_seconds


def test_plan_rejects_stale_duration_nodeid() -> None:
    with pytest.raises(TOOL.ShardError, match="absent from collection"):
        TOOL.plan_shards(
            ("tests/test_example.py::test_live",),
            2,
            baseline(durations={"tests/test_example.py::test_retired": 3.0}),
        )


def test_run_writes_receipt_before_selected_pytest_execution(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    duration_path = repo_root / "durations.json"
    duration_path.write_text(
        json.dumps(
            {
                "schema_version": TOOL.SCHEMA_VERSION,
                "default_seconds": 1.0,
                "durations_seconds": {},
            }
        ),
        encoding="utf-8",
    )
    receipt = tmp_path / "receipt.json"
    collected = (
        "tests/test_example.py::test_a",
        "tests/test_example.py::test_b",
        "tests/test_example.py::test_c",
    )
    observed: list[tuple[str, ...]] = []

    def command_runner(
        command: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        observed.append(command)
        if "--collect-only" in command:
            return subprocess.CompletedProcess(command, 0, "\n".join(collected), "")
        assert receipt.is_file()
        return subprocess.CompletedProcess(command, 0, "", "")

    status = TOOL.run_shard(
        repo_root=repo_root,
        shard_index=1,
        shard_count=2,
        workers=2,
        duration_baseline=duration_path,
        receipt=receipt,
        command_runner=command_runner,
    )

    payload = json.loads(receipt.read_text(encoding="utf-8"))
    expected = TOOL.plan_shards(collected, 2, baseline())[1].nodeids
    assert status == 0
    assert tuple(payload["nodeids"]) == expected
    assert payload["collected_count"] == 3
    assert "--dist=worksteal" in observed[1]
    assert set(expected).issubset(observed[1])


def test_in_process_pytest_adds_and_restores_repository_import_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    previous_cwd = Path.cwd()
    observed: dict[str, object] = {}

    def fake_main(arguments: list[str]) -> int:
        observed["arguments"] = arguments
        observed["cwd"] = Path.cwd()
        observed["path"] = tuple(sys.path)
        return 7

    monkeypatch.setattr(pytest, "main", fake_main)
    status = TOOL.run_pytest_in_process(
        (sys.executable, "-m", "pytest", "-q", "tests/test_example.py::test_one"),
        repo_root,
    )

    assert status == 7
    assert observed["arguments"] == ["-q", "tests/test_example.py::test_one"]
    assert observed["cwd"] == repo_root
    assert str(repo_root) in observed["path"]
    assert Path.cwd() == previous_cwd
    assert str(repo_root) not in sys.path


def test_receipt_verification_rejects_missing_duplicate_and_stale_plans(
    tmp_path: Path,
) -> None:
    nodeids = tuple(f"tests/test_example.py::test_{index}" for index in range(8))
    durations = baseline()
    plans = TOOL.plan_shards(nodeids, 2, durations)
    receipts = []
    for index, plan in enumerate(plans):
        path = tmp_path / f"python-test-shard-{index}-of-2.json"
        payload = TOOL.receipt_payload(
            all_nodeids=nodeids,
            plan=plan,
            shard_index=index,
            shard_count=2,
        )
        receipts.append((path, payload))

    TOOL.verify_receipts(
        receipts=receipts,
        all_nodeids=nodeids,
        baseline=durations,
    )
    with pytest.raises(TOOL.ShardError, match="expected 2 shard receipts"):
        TOOL.verify_receipts(
            receipts=receipts[:1],
            all_nodeids=nodeids,
            baseline=durations,
        )
    duplicate_index = [receipts[0], (receipts[1][0], dict(receipts[0][1]))]
    with pytest.raises(TOOL.ShardError, match="duplicate shard index"):
        TOOL.verify_receipts(
            receipts=duplicate_index,
            all_nodeids=nodeids,
            baseline=durations,
        )
    stale = dict(receipts[1][1])
    stale["nodeids"] = list(reversed(stale["nodeids"]))
    with pytest.raises(TOOL.ShardError, match="deterministic plan"):
        TOOL.verify_receipts(
            receipts=[receipts[0], (receipts[1][0], stale)],
            all_nodeids=nodeids,
            baseline=durations,
        )


@pytest.mark.parametrize(
    ("index", "count", "message"),
    [(-1, 4, "between 0 and 3"), (4, 4, "between 0 and 3"), (0, 0, "positive")],
)
def test_shard_coordinate_bounds(index: int, count: int, message: str) -> None:
    with pytest.raises(TOOL.ShardError, match=message):
        TOOL.require_shard_coordinates(index, count)
