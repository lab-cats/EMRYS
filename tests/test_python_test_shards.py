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

    first = TOOL.plan_shards(nodeids, 3, durations, 2)
    second = TOOL.plan_shards(tuple(reversed(nodeids)), 3, durations, 2)

    assert first == second
    assert sorted(nodeid for plan in first for nodeid in plan.nodeids) == sorted(
        nodeids
    )
    assert sum(slow in plan.nodeids for plan in first) == 1
    assert len({nodeid for plan in first for nodeid in plan.nodeids}) == len(nodeids)
    assert {plan.worker_count for plan in first} == {2}


def test_worker_aware_plan_uses_capacity_for_shard_membership() -> None:
    six = "tests/test_example.py::test_six"
    four_a = "tests/test_example.py::test_four_a"
    four_b = "tests/test_example.py::test_four_b"
    three_a = "tests/test_example.py::test_three_a"
    three_b = "tests/test_example.py::test_three_b"
    durations = {
        six: 6.0,
        four_a: 4.0,
        four_b: 4.0,
        three_a: 3.0,
        three_b: 3.0,
    }
    nodeids = tuple(durations)

    worker_aware = TOOL.plan_shards(nodeids, 2, baseline(durations=durations), 2)
    serial = TOOL.plan_shards(nodeids, 2, baseline(durations=durations), 1)

    assert tuple(plan.nodeids for plan in worker_aware) == (
        (four_b, six),
        (four_a, three_a, three_b),
    )
    assert tuple(plan.nodeids for plan in serial) == (
        (six, three_a),
        (four_a, four_b, three_b),
    )


def test_plan_rejects_stale_duration_nodeid() -> None:
    with pytest.raises(TOOL.ShardError, match="absent from collection"):
        TOOL.plan_shards(
            ("tests/test_example.py::test_live",),
            2,
            baseline(durations={"tests/test_example.py::test_retired": 3.0}),
            2,
        )


@pytest.mark.parametrize("write_timing_report", (True, False))
def test_run_writes_receipt_before_selected_pytest_execution(
    tmp_path: Path, write_timing_report: bool
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    duration_path = repo_root / "durations.json"
    duration_path.write_text(
        json.dumps(
            {
                "schema_version": TOOL.DURATION_SCHEMA_VERSION,
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
    timing_report = receipt.with_suffix(".xml")
    if not write_timing_report:
        timing_report.write_text("<stale-testsuites />\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        observed.append(command)
        if "--collect-only" in command:
            return subprocess.CompletedProcess(command, 0, "\n".join(collected), "")
        assert receipt.is_file()
        report_argument = next(
            item for item in command if item.startswith("--junitxml=")
        )
        if write_timing_report:
            Path(report_argument.removeprefix("--junitxml=")).write_text(
                "<testsuites />\n", encoding="utf-8"
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    arguments = {
        "repo_root": repo_root,
        "shard_index": 1,
        "shard_count": 2,
        "workers": 2,
        "duration_baseline": duration_path,
        "receipt": receipt,
        "command_runner": command_runner,
    }
    if not write_timing_report:
        with pytest.raises(TOOL.ShardError, match="did not write timing report"):
            TOOL.run_shard(**arguments)
        assert receipt.is_file()
        assert not timing_report.exists()
        return
    status = TOOL.run_shard(**arguments)

    payload = json.loads(receipt.read_text(encoding="utf-8"))
    expected = TOOL.plan_shards(collected, 2, baseline(), 2)[1].nodeids
    assert status == 0
    assert tuple(payload["nodeids"]) == expected
    assert payload["collected_count"] == 3
    assert payload["worker_count"] == 2
    assert payload["schema_version"] == TOOL.RECEIPT_SCHEMA_VERSION
    assert "estimated_seconds" not in payload
    assert "--dist=worksteal" in observed[1]
    assert "junit_duration_report=total" in observed[1]
    assert "junit_family=xunit1" in observed[1]
    assert f"--junitxml={timing_report}" in observed[1]
    assert timing_report.is_file()
    assert observed[1][-len(expected) :] == expected


def test_load_receipt_rejects_pre_worker_schema(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps({"schema_version": TOOL.DURATION_SCHEMA_VERSION}),
        encoding="utf-8",
    )

    with pytest.raises(TOOL.ShardError, match="unsupported shard receipt"):
        TOOL.load_receipt(receipt)


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
    plans = TOOL.plan_shards(nodeids, 2, durations, 2)
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


def test_receipt_verification_rejects_worker_count_mismatch(tmp_path: Path) -> None:
    nodeids = tuple(f"tests/test_example.py::test_{index}" for index in range(8))
    durations = baseline()
    plans = TOOL.plan_shards(nodeids, 2, durations, 2)
    receipts = [
        (
            tmp_path / f"python-test-shard-{index}-of-2.json",
            TOOL.receipt_payload(
                all_nodeids=nodeids,
                plan=plan,
                shard_index=index,
                shard_count=2,
            ),
        )
        for index, plan in enumerate(plans)
    ]
    receipts[1][1]["worker_count"] = 3

    with pytest.raises(TOOL.ShardError, match="disagree on worker_count"):
        TOOL.verify_receipts(
            receipts=receipts,
            all_nodeids=nodeids,
            baseline=durations,
        )


@pytest.mark.parametrize("worker_count", [None, 0, -1, True])
def test_receipt_verification_rejects_invalid_worker_count(
    tmp_path: Path, worker_count: object
) -> None:
    nodeids = ("tests/test_example.py::test_one",)
    plan = TOOL.plan_shards(nodeids, 1, baseline(), 1)[0]
    payload = TOOL.receipt_payload(
        all_nodeids=nodeids,
        plan=plan,
        shard_index=0,
        shard_count=1,
    )
    if worker_count is None:
        payload.pop("worker_count")
    else:
        payload["worker_count"] = worker_count

    with pytest.raises(TOOL.ShardError, match="positive integer"):
        TOOL.verify_receipts(
            receipts=[(tmp_path / "python-test-shard-0-of-1.json", payload)],
            all_nodeids=nodeids,
            baseline=baseline(),
        )


@pytest.mark.parametrize(
    ("index", "count", "message"),
    [(-1, 4, "between 0 and 3"), (4, 4, "between 0 and 3"), (0, 0, "positive")],
)
def test_shard_coordinate_bounds(index: int, count: int, message: str) -> None:
    with pytest.raises(TOOL.ShardError, match=message):
        TOOL.require_shard_coordinates(index, count)
