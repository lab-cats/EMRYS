"""Executable contracts for the generic one-owner local task boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from norad.contracts.orchestration import api as orchestration_contracts
from norad.orchestration.local_pilot import normalization, task

from tests.orchestration.local_pilot import fixture
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture

WORKFLOW_ATTEMPT_ID = "workflow-20260812T120000Z-" + "a" * 32
TASK_ATTEMPT_ID = "task-20260812T120100Z-" + "b" * 32
MACHINE_KEY = "norad.stage.align_RNA_reads_with_STAR.v1"
SCOPE_ID = "EV_1"
TEST_DOUBLE = Path(__file__).parent / "fixtures" / "task_double.py"


@dataclass(frozen=True, slots=True)
class TaskFixture:
    run_root: Path
    dispatch_path: Path
    dispatch: dict[str, Any]
    mutable_input: Path


def _publish_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orchestration_contracts.canonical_json_bytes(value))


def _task_fixture(tmp_path: Path) -> TaskFixture:
    intake = tmp_path / "intake"
    intake.mkdir(parents=True)
    request = fixture.build(intake)
    profile = fixture.profile()
    normalized = normalization.normalize_request(request, profile=profile)

    run_root = tmp_path / "run"
    contract = run_root / "contract"
    contract.mkdir(parents=True)
    profile_path = contract / "profile.json"
    execution_path = contract / "normalized.json"
    _publish_json(profile_path, profile)
    execution_path.write_bytes(normalized.normalized_bytes)

    mutable_input = run_root / "inputs" / "owner-input.txt"
    mutable_input.parent.mkdir()
    mutable_input.write_bytes(b"stable owner input\n")
    task_root = (
        run_root / "attempts" / WORKFLOW_ATTEMPT_ID / "tasks" / MACHINE_KEY / SCOPE_ID
    )
    verified_path = run_root / "state" / "verified" / MACHINE_KEY / f"{SCOPE_ID}.json"
    task_root.mkdir(parents=True)
    verified_path.parent.mkdir(parents=True)

    first_output = run_root / "results" / "samples" / SCOPE_ID / "aligned.bam"
    second_output = run_root / "results" / "samples" / SCOPE_ID / "aligned.bam.bai"
    receipt = run_root / "results" / "receipts" / f"{SCOPE_ID}.json"
    report = run_root / "results" / "validation" / "01" / f"{SCOPE_ID}.tsv"
    producer = [
        sys.executable,
        str(TEST_DOUBLE),
        "producer",
        "--output",
        f"aligned_bam={first_output}",
        "--output",
        f"aligned_bai={second_output}",
        "--native-receipt",
        str(receipt),
    ]
    validator = [
        sys.executable,
        str(TEST_DOUBLE),
        "validator",
        "--report",
        str(report),
        "--step-id",
        "01",
        "--scope-id",
        SCOPE_ID,
    ]
    dispatch_path = task_root / "dispatch.json"
    dispatch = {
        "schema_version": task.DISPATCH_SCHEMA_VERSION,
        "run_root": str(run_root),
        "execution_path": str(execution_path),
        "profile_path": str(profile_path),
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "task_attempt_id": TASK_ATTEMPT_ID,
        "owner_run_token": "owner-run-ev-1",
        "machine_key": MACHINE_KEY,
        "scope": {"scope_type": "sample", "scope_id": SCOPE_ID},
        "producer_argv": producer,
        "validator_argv": validator,
        "inputs": [{"role": "owner_input", "path": str(mutable_input)}],
        "outputs": [
            {"role": "aligned_bam", "path": str(first_output)},
            {"role": "aligned_bai", "path": str(second_output)},
        ],
        "validation_report_path": str(report),
        "native_receipt_path": str(receipt),
        "task_attempt_path": str(task_root / "task-attempt.json"),
        "verified_task_path": str(verified_path),
        "stdout_path": str(task_root / "stdout.log"),
        "stderr_path": str(task_root / "stderr.log"),
    }
    _publish_json(dispatch_path, dispatch)
    return TaskFixture(run_root, dispatch_path, dispatch, mutable_input)


def _fixed_ops() -> task.TaskOps:
    defaults = task.default_task_ops()
    return task.TaskOps(
        run_command=defaults.run_command,
        run_semantic_all_pass=defaults.run_semantic_all_pass,
        publish_bytes=defaults.publish_bytes,
        now=lambda: datetime(2026, 8, 12, 12, 2, tzinfo=UTC),
    )


def _rewrite_dispatch(built: TaskFixture) -> None:
    built.dispatch_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(built.dispatch)
    )


def _record(path: str | Path) -> dict[str, Any]:
    return orchestration_contracts.load_json_object(path)


def test_success_publishes_schema_valid_content_bound_records(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)

    outcome = task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    attempt = _record(outcome.task_attempt_path)
    verified = _record(outcome.verified_task_path)
    orchestration_contracts.validate_record("task-attempt", attempt)
    orchestration_contracts.validate_record("verified-task", verified)
    assert attempt["status"] == "succeeded"
    assert verified["all_pass"] is True
    assert verified["stable_inputs_rechecked"] is True
    assert [item["role"] for item in verified["inputs"]] == [
        "task_dispatch",
        "execution_contract",
        "workflow_profile",
        "owner_input",
    ]
    for bound in (*verified["inputs"], *verified["outputs"]):
        content = Path(bound["path"]).read_bytes()
        assert bound["size_bytes"] == len(content)
        assert bound["sha256"] == hashlib.sha256(content).hexdigest()
    report = Path(built.dispatch["validation_report_path"])
    assert (
        verified["validation_report"]["sha256"]
        == hashlib.sha256(report.read_bytes()).hexdigest()
    )
    assert verified["native_receipt"] is not None
    assert (
        b"producer stdout complete\nvalidator stdout complete\n"
        in Path(built.dispatch["stdout_path"]).read_bytes()
    )
    assert (
        b"producer stderr complete\nvalidator stderr complete\n"
        in Path(built.dispatch["stderr_path"]).read_bytes()
    )


def test_records_exact_public_commands_and_exit_codes(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)

    task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    verified = _record(built.dispatch["verified_task_path"])
    assert verified["commands"]["producer"] == {
        "argv": built.dispatch["producer_argv"],
        "exit_code": 0,
    }
    assert verified["commands"]["validator"] == {
        "argv": built.dispatch["validator_argv"],
        "exit_code": 0,
    }
    semantic = verified["commands"]["semantic_all_pass"]
    assert semantic["exit_code"] == 0
    assert semantic["argv"] == [
        sys.executable,
        "-I",
        "-m",
        "norad",
        "validate",
        "all-pass",
        "--report",
        built.dispatch["validation_report_path"],
        "--step-id",
        "01",
        "--scope-id",
        SCOPE_ID,
    ]


def test_zero_exit_validator_fail_row_blocks_verified_publication(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    built.dispatch["validator_argv"].extend(["--status", "fail"])
    _rewrite_dispatch(built)

    with pytest.raises(task.TaskBoundaryError, match="Semantic all-pass"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    attempt = _record(built.dispatch["task_attempt_path"])
    assert attempt["status"] == "failed"
    assert attempt["validator"]["exit_code"] == 0
    assert attempt["semantic_all_pass"]["exit_code"] == 1
    assert attempt["validation_report"] is not None
    assert not Path(built.dispatch["verified_task_path"]).exists()
    assert (
        Path(built.dispatch["validation_report_path"])
        .read_text()
        .splitlines()[1]
        .split("\t")[3]
        == "fail"
    )


def test_producer_failure_preserves_partial_output_and_attempt_evidence(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    built.dispatch["producer_argv"].extend(["--fail-after", "1"])
    _rewrite_dispatch(built)

    with pytest.raises(task.TaskBoundaryError, match="Producer command exited"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    attempt = _record(built.dispatch["task_attempt_path"])
    assert attempt["producer"]["exit_code"] == 23
    assert attempt["validator"] is None
    assert attempt["semantic_all_pass"] is None
    assert Path(built.dispatch["outputs"][0]["path"]).is_file()
    assert not Path(built.dispatch["outputs"][1]["path"]).exists()
    assert not Path(built.dispatch["verified_task_path"]).exists()
    assert (
        b"producer failed after aligned_bam"
        in Path(built.dispatch["stderr_path"]).read_bytes()
    )


@pytest.mark.parametrize("destination", ["output", "report", "receipt"])
def test_preexisting_native_or_validation_residue_fails_closed(
    tmp_path: Path,
    destination: str,
) -> None:
    built = _task_fixture(tmp_path)
    paths = {
        "output": Path(built.dispatch["outputs"][0]["path"]),
        "report": Path(built.dispatch["validation_report_path"]),
        "receipt": Path(built.dispatch["native_receipt_path"]),
    }
    foreign = paths[destination]
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_bytes(b"foreign predecessor\n")

    with pytest.raises(task.TaskBoundaryError, match="pre-existing"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    assert foreign.read_bytes() == b"foreign predecessor\n"
    attempt = _record(built.dispatch["task_attempt_path"])
    assert attempt["status"] == "failed"
    assert attempt["producer"] is None
    assert not Path(built.dispatch["verified_task_path"]).exists()


def test_input_mutation_blocks_verified_publication(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    built.dispatch["producer_argv"].extend(["--mutate-input", str(built.mutable_input)])
    _rewrite_dispatch(built)

    with pytest.raises(task.TaskBoundaryError, match="stable task input changed"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    attempt = _record(built.dispatch["task_attempt_path"])
    assert attempt["stable_inputs_rechecked"] is False
    assert attempt["semantic_all_pass"]["exit_code"] == 0
    assert not Path(built.dispatch["verified_task_path"]).exists()


def test_successful_dispatch_rerun_refuses_immutable_predecessor(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())
    verified = Path(built.dispatch["verified_task_path"])
    predecessor = verified.read_bytes()

    with pytest.raises(task.TaskBoundaryError, match="task-attempt record"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    assert verified.read_bytes() == predecessor


def test_dispatch_is_closed_and_binds_exact_owner_scope(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    built.dispatch["unexpected"] = True
    _rewrite_dispatch(built)
    with pytest.raises(task.TaskBoundaryError, match="unknown unexpected"):
        task.load_dispatch(built.dispatch_path)

    built = _task_fixture(tmp_path / "second")
    built.dispatch["scope"]["scope_id"] = "not_selected"
    _rewrite_dispatch(built)
    with pytest.raises(task.TaskBoundaryError, match="not selected"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())


def test_internal_module_cli_is_isolated_and_not_a_public_lifecycle_command(
    tmp_path: Path,
) -> None:
    help_result = subprocess.run(
        [sys.executable, "-I", "-m", "norad.orchestration.local_pilot.task", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    assert "--dispatch" in help_result.stdout
    assert "not a public" in help_result.stdout
    assert "run/resume/inspect" in help_result.stdout

    built = _task_fixture(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad.orchestration.local_pilot.task",
            "--dispatch",
            str(built.dispatch_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert Path(built.dispatch["verified_task_path"]).is_file()


def test_existing_verified_or_partial_task_state_is_never_replaced(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    for field in ("verified_task_path", "stdout_path"):
        destination = Path(built.dispatch[field])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"foreign state\n")
        with pytest.raises(task.TaskBoundaryError, match="Refusing pre-existing"):
            task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())
        assert destination.read_bytes() == b"foreign state\n"
        destination.unlink()


def test_dispatch_and_output_paths_may_not_alias(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    built.dispatch["outputs"][0]["path"] = str(built.dispatch_path)
    _rewrite_dispatch(built)
    with pytest.raises(task.TaskBoundaryError, match="aliases an input"):
        task.load_dispatch(built.dispatch_path)


def test_records_are_canonical_json_bytes(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())
    for field in ("task_attempt_path", "verified_task_path"):
        path = Path(built.dispatch[field])
        record = json.loads(path.read_bytes())
        assert path.read_bytes() == orchestration_contracts.canonical_json_bytes(record)


def test_read_only_verified_admission_rechecks_every_content_binding(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())
    execution = _record(built.dispatch["execution_path"])
    profile = _record(built.dispatch["profile_path"])

    admitted = task.validate_verified_task(
        Path(built.dispatch["verified_task_path"]),
        run_root=built.run_root,
        execution=execution,
        profile=profile,
        machine_key=MACHINE_KEY,
        scope=built.dispatch["scope"],
    )
    assert admitted["all_pass"] is True

    output = Path(built.dispatch["outputs"][0]["path"])
    output.write_bytes(b"changed after verification\n")
    with pytest.raises(task.TaskBoundaryError, match="content binding"):
        task.validate_verified_task(
            Path(built.dispatch["verified_task_path"]),
            run_root=built.run_root,
            execution=execution,
            profile=profile,
            machine_key=MACHINE_KEY,
            scope=built.dispatch["scope"],
        )


@pytest.mark.parametrize(
    "field",
    [
        "verified_task_path",
        "task_attempt_path",
        "validation_report_path",
        "native_receipt_path",
    ],
)
def test_read_only_verified_admission_rejects_mutated_references(
    tmp_path: Path,
    field: str,
) -> None:
    built = _task_fixture(tmp_path)
    task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())
    referenced = Path(built.dispatch[field])
    with referenced.open("ab") as stream:
        stream.write(b"mutated-after-publication\n")

    with pytest.raises(task.TaskBoundaryError):
        task.validate_verified_task(
            Path(built.dispatch["verified_task_path"]),
            run_root=built.run_root,
            execution=_record(built.dispatch["execution_path"]),
            profile=_record(built.dispatch["profile_path"]),
            machine_key=MACHINE_KEY,
            scope=built.dispatch["scope"],
        )


def test_read_only_verified_admission_rejects_wrong_identity_and_scope(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())
    with pytest.raises(task.TaskBoundaryError, match="scope"):
        task.validate_verified_task(
            Path(built.dispatch["verified_task_path"]),
            run_root=built.run_root,
            execution=_record(built.dispatch["execution_path"]),
            profile=_record(built.dispatch["profile_path"]),
            machine_key=MACHINE_KEY,
            scope={"scope_type": "sample", "scope_id": "PUM1_1"},
        )


def test_semantic_gate_cannot_change_the_report_it_approves(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    defaults = task.default_task_ops()

    def semantic(argv: tuple[str, ...], cwd: Path) -> task.CommandResult:
        result = defaults.run_semantic_all_pass(argv, cwd)
        with Path(built.dispatch["validation_report_path"]).open("ab") as stream:
            stream.write(b"post-gate mutation\n")
        return result

    ops = task.TaskOps(
        run_command=defaults.run_command,
        run_semantic_all_pass=semantic,
        publish_bytes=defaults.publish_bytes,
        now=lambda: datetime(2026, 8, 12, 12, 2, tzinfo=UTC),
    )
    with pytest.raises(task.TaskBoundaryError, match="report changed"):
        task.execute_dispatch(built.dispatch_path, ops=ops)
    assert not Path(built.dispatch["verified_task_path"]).exists()


def test_validator_cannot_change_a_producer_output(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    defaults = task.default_task_ops()

    def command(argv: tuple[str, ...], cwd: Path) -> task.CommandResult:
        result = defaults.run_command(argv, cwd)
        if "validator" in argv:
            with Path(built.dispatch["outputs"][0]["path"]).open("ab") as stream:
                stream.write(b"validator mutation\n")
        return result

    ops = task.TaskOps(
        run_command=command,
        run_semantic_all_pass=defaults.run_semantic_all_pass,
        publish_bytes=defaults.publish_bytes,
        now=lambda: datetime(2026, 8, 12, 12, 2, tzinfo=UTC),
    )
    with pytest.raises(task.TaskBoundaryError, match="producer output changed"):
        task.execute_dispatch(built.dispatch_path, ops=ops)
    assert not Path(built.dispatch["verified_task_path"]).exists()


def test_symlinked_output_and_contract_ancestors_fail_closed(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    results = built.run_root / "results"
    results.symlink_to(outside, target_is_directory=True)
    with pytest.raises(task.TaskBoundaryError, match="symlink ancestor"):
        task.execute_dispatch(built.dispatch_path, ops=_fixed_ops())

    built = _task_fixture(tmp_path / "contract-case")
    contract = built.run_root / "contract"
    moved = built.run_root / "real-contract"
    contract.rename(moved)
    contract.symlink_to(moved, target_is_directory=True)
    with pytest.raises(task.TaskBoundaryError, match="symlink ancestor"):
        task.load_dispatch(built.dispatch_path)


def test_step00c_symlinked_stationary_reference_blocks_before_producer(
    tmp_path: Path,
) -> None:
    built = workflow_fixture.build(tmp_path / "workflow-fixture")
    machine_key = "norad.stage.construct_FASTA_sidecars.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    dispatch_path = Path(built.dispatch_paths[machine_key][scope_id])
    record = orchestration_contracts.load_json_object(dispatch_path)
    fasta = Path(str(built.execution["reference"]["fasta"]["path"]))
    original_parent = fasta.parent
    real_parent = original_parent.with_name("reference-real")
    original_parent.rename(real_parent)
    original_parent.symlink_to(real_parent, target_is_directory=True)

    fai = Path(f"{fasta}.fai")
    sequence_dict = fasta.with_name(f"{fasta.stem}.dict")
    record["outputs"] = [
        {"role": "reference_fai", "path": str(fai)},
        {"role": "reference_dict", "path": str(sequence_dict)},
    ]
    record["producer_argv"] = ["producer-must-not-run"]
    dispatch_path.write_bytes(orchestration_contracts.canonical_json_bytes(record))

    calls: list[tuple[str, ...]] = []

    def command(argv: tuple[str, ...], cwd: Path) -> task.CommandResult:
        calls.append(argv)
        return task.CommandResult(argv, 0, b"", b"")

    defaults = task.default_task_ops()
    ops = task.TaskOps(
        run_command=command,
        run_semantic_all_pass=command,
        publish_bytes=defaults.publish_bytes,
        now=lambda: datetime(2026, 8, 12, 12, 2, tzinfo=UTC),
    )
    with pytest.raises(
        task.TaskBoundaryError, match="stationary FASTA must be canonical"
    ):
        task.execute_dispatch(dispatch_path, ops=ops)

    assert calls == []
    assert not fai.exists()
    assert not sequence_dict.exists()
