"""Executable contracts for the generic one-owner local task boundary."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import (
    PACKAGE_ROOT,
    admit_installed_package,
    controlled_python_argv,
)
from emrys.orchestration.run_coordinator import lifecycle, reporting_boundary, task

from tests.orchestration.run_coordinator import fixture
from tests.orchestration.run_coordinator.fixtures import workflow as workflow_fixture

WORKFLOW_ATTEMPT_ID = "workflow-20260812T120000Z-" + "a" * 32
TASK_ATTEMPT_ID = "task-20260812T120100Z-" + "b" * 32
MACHINE_KEY = "emrys.stage.align_RNA_reads_with_STAR.v1"
SCOPE_ID = "EV_1"
TEST_DOUBLE = Path(__file__).parent / "fixtures" / "task_double.py"
REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class TaskFixture:
    run_root: Path
    manifest_path: Path
    definition: dict[str, Any]
    mutable_input: Path
    plan: task.TaskPlan


def _publish_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orchestration_contracts.canonical_json_bytes(value))


def _materialize_active_lock(run_root: Path, attempt_path: Path) -> Path:
    attempt = orchestration_contracts.load_record(attempt_path, "workflow-attempt")
    lock = orchestration_contracts.run_lock_record(attempt)
    orchestration_contracts.validate_record("run-lock", lock)
    lock_path = run_root / "locks" / "run.lock"
    lock_path.parent.mkdir()
    _publish_json(lock_path, lock)
    return lock_path


def _task_fixture(tmp_path: Path, *, prepublication: bool = False) -> TaskFixture:
    intake = tmp_path / "intake"
    intake.mkdir(parents=True)
    profile = fixture.profile()
    storage_receipt = tmp_path / "storage.qualified.json"
    storage_receipt.write_bytes(b"bounded task-fixture storage qualification\n")
    normalizer, required_tools = workflow_fixture._attempt_runtime_identities(tmp_path)
    _request, candidate = fixture.build_run(
        intake, profile, required_tools=required_tools
    )
    machine_key = (
        "emrys.stage.preprocess_and_annotate_cohort_candidates.v1"
        if prepublication
        else MACHINE_KEY
    )
    scope_id = (
        candidate.analysis.revision.scope_id("cohort") if prepublication else SCOPE_ID
    )
    step_id = "08" if prepublication else "01"
    execution = candidate.run_binding.record
    execution_bytes = candidate.run_binding.canonical_bytes
    profile = candidate.analysis.profile
    run_root = tmp_path / "runs" / candidate.run_id
    fixture.publish_run(candidate, run_root)
    contract = run_root / "contract"
    profile_path = contract / "profile.json"

    files, reporting_config, _ = reporting_boundary._attempt_reporting_materialization(
        {**candidate.analysis.workflow_inputs, "run_id": candidate.run_id},
        profile,
        run_root,
        analysis=candidate.analysis.revision,
        attempt_id=WORKFLOW_ATTEMPT_ID,
    )
    for path, data in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    mutable_input = run_root / "inputs" / "owner-input.txt"
    mutable_input.parent.mkdir()
    mutable_input.write_bytes(b"stable owner input\n")
    verified_path = run_root / "state" / "verified" / machine_key / f"{scope_id}.json"
    (run_root / "attempts" / WORKFLOW_ATTEMPT_ID).mkdir(parents=True)
    task_start = run_root / "state" / "task-starts" / machine_key / f"{scope_id}.json"
    task_start.parent.mkdir(parents=True)
    verified_path.parent.mkdir(parents=True)

    first_output = run_root / "results" / "samples" / scope_id / "aligned.bam"
    second_output = run_root / "results" / "samples" / scope_id / "aligned.bam.bai"
    receipt = run_root / "results" / "receipts" / f"{scope_id}.json"
    report = run_root / "results" / "validation" / step_id / f"{scope_id}.tsv"
    producer = list(
        controlled_python_argv(
            sys.executable,
            str(TEST_DOUBLE),
            "producer",
            "--output",
            f"aligned_bam={first_output}",
            "--output",
            f"aligned_bai={second_output}",
            "--native-receipt",
            str(receipt),
        )
    )
    validator = list(
        controlled_python_argv(
            sys.executable,
            str(TEST_DOUBLE),
            "validator",
            "--report",
            str(report),
            "--step-id",
            step_id,
            "--scope-id",
            scope_id,
        )
    )
    if prepublication:
        validator.extend(["--input", str(first_output)])
    definition = {
        "task_attempt_id": TASK_ATTEMPT_ID,
        "owner_run_token": "owner-run-ev-1",
        "scope_type": "cohort" if prepublication else "sample",
        "producer_argv": producer,
        "validator_argv": validator,
        "inputs": [{"role": "owner_input", "path": str(mutable_input)}],
        "outputs": [
            {"role": "aligned_bam", "path": str(first_output)},
            {"role": "aligned_bai", "path": str(second_output)},
            {"role": "native_receipt", "path": str(receipt)},
        ],
        "publication": {
            "locks": [str(first_output.parent / ".owner.lock")],
            "forbidden_paths": [str(first_output.parent / ".owner.*")],
            "output_directory": None,
            "input_directories": [],
        },
        "validation_report_path": str(report),
        "native_receipt_path": str(receipt),
    }
    for output in definition["outputs"]:
        final = Path(output["path"])
        final.parent.mkdir(parents=True, exist_ok=True)
        working = final.parent / ".emrys-owner-run-ev-1.work" / final.name
        output["working_path"] = str(working)
        definition["producer_argv"] = [
            argument.replace(str(final), str(working))
            for argument in definition["producer_argv"]
        ]
    attempt_path = run_root / "attempts" / WORKFLOW_ATTEMPT_ID / "attempt.json"
    request_snapshot = attempt_path.parent / "request.yaml"
    request_bytes = b"task-fixture: true\n"
    request_snapshot.write_bytes(request_bytes)
    attempt = {
        "schema_version": "emrys.workflow-attempt.v2",
        "run_id": execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(execution_bytes).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "supersedes_workflow_attempt_id": None,
        "operation": "execute",
        "created_at": "2026-08-12T12:00:00Z",
        "request": {
            "path": str(request_snapshot),
            "size_bytes": len(request_bytes),
            "sha256": hashlib.sha256(request_bytes).hexdigest(),
        },
        "request_label": "generic task fixture",
        "authored_paths": {
            "request": str(request_snapshot),
            "sample_manifest": "samples.tsv",
            "partition_manifest": "partitions.tsv",
            "reference_fasta": "reference.fa",
            "reference_gtf": "reference.gtf",
            "analysis_policy": None,
        },
        "normalizer": normalizer,
        "workspace": str(tmp_path.resolve()),
        "scratch": None,
        "installed_package": admit_installed_package().record,
        "executor": "local",
        "execution_mode": "local-science-tools",
        "snakemake_argv": list(
            controlled_python_argv(
                sys.executable,
                "-m",
                "snakemake",
                "--",
                "cohort_slice",
            )
        ),
        "workflow": {
            **reporting_config,
            "resource_policy": workflow_fixture._resource_policy(),
        },
        "tasks": {machine_key: {scope_id: definition}},
        "host": "task-fixture",
        "process_id": 1,
        "owner_token": "task-fixture-owner",
        "cores": 1,
        "required_tools": required_tools,
    }
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    _publish_json(attempt_path, attempt)
    _materialize_active_lock(run_root, attempt_path)
    plan = task.load_task(
        attempt_path,
        expected_sha256=_manifest_sha256(attempt_path),
        machine_key=machine_key,
        scope_id=scope_id,
    )
    return TaskFixture(run_root, attempt_path, definition, mutable_input, plan)


def _fixed_ops() -> task.TaskOps:
    defaults = task.default_task_ops()

    return task.TaskOps(
        run_command=defaults.run_command,
        run_semantic_all_pass=defaults.run_semantic_all_pass,
        publish_bytes=defaults.publish_bytes,
        now=lambda: datetime(2026, 8, 12, 12, 2, tzinfo=UTC),
    )


def _run_default_command(
    argv: tuple[str, ...],
    cwd: Path,
    environment: Mapping[str, str],
) -> tuple[task.CommandResult, bytes, bytes]:
    runner = task.default_task_ops().run_command
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        result = runner(
            argv,
            cwd,
            environment,
            stdout.fileno(),
            stderr.fileno(),
        )
        stdout.seek(0)
        stderr.seek(0)
        return result, stdout.read(), stderr.read()


def test_default_command_runner_blocks_hostile_bash_startup(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "bash-env-marker"
    startup = tmp_path / "hostile-bash-env"
    startup.write_text(f"touch {marker}\n", encoding="utf-8")
    result, _stdout, _stderr = _run_default_command(
        ("/bin/bash", "-c", "true"),
        tmp_path,
        {
            **os.environ,
            "BASH_ENV": str(startup),
            "ENV": str(startup),
            "CDPATH": str(tmp_path),
            "GLOBIGNORE": "*",
            "BASH_FUNC_hostile%%": "() { touch hostile-function-marker; }",
        },
    )

    assert result.exit_code == 0
    assert not marker.exists()
    assert not (tmp_path / "hostile-function-marker").exists()


@pytest.mark.parametrize(
    ("error", "expected_exit"),
    [
        (FileNotFoundError(errno.ENOENT, "fixture missing", "missing-tool"), 127),
        (PermissionError(errno.EACCES, "fixture denied", "denied-tool"), 126),
    ],
)
def test_default_command_runner_streams_exact_spawn_error_and_exit_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: OSError,
    expected_exit: int,
) -> None:
    argv = ("fixture-tool", "--argument")

    def fail_spawn(*_args: object, **_kwargs: object) -> subprocess.Popen[bytes]:
        raise error

    monkeypatch.setattr(task.subprocess, "Popen", fail_spawn)
    result, stdout, stderr = _run_default_command(argv, tmp_path, {})

    assert result.record == {"argv": list(argv), "exit_code": expected_exit}
    assert stdout == b""
    assert stderr == f"Could not execute {argv[0]}: {error}\n".encode(
        "utf-8", errors="backslashreplace"
    )


@pytest.mark.parametrize(
    ("shell_command", "expected_exit"),
    [
        ("exit 0", 0),
        ("exit 23", 23),
        ("exit 255", 255),
        ("kill -9 $$", 128),
    ],
)
def test_default_command_runner_preserves_exit_code_normalization(
    tmp_path: Path,
    shell_command: str,
    expected_exit: int,
) -> None:
    result, stdout, stderr = _run_default_command(
        ("/bin/sh", "-c", shell_command), tmp_path, {}
    )

    assert result.exit_code == expected_exit
    assert stdout == b""
    assert stderr == b""


def test_default_command_runner_drains_inherited_streams_through_eof(
    tmp_path: Path,
) -> None:
    result, stdout, stderr = _run_default_command(
        (
            "/bin/sh",
            "-c",
            "(sleep 0.05; printf 'late\\n') & printf 'early\\n'",
        ),
        tmp_path,
        {},
    )

    assert result.exit_code == 0
    assert stdout == b"early\nlate\n"
    assert stderr == b""


def test_failed_command_quiesces_descendants_before_draining_inherited_streams(
    tmp_path: Path,
) -> None:
    script = """
import os, signal, sys, time
reader, writer = os.pipe()
if os.fork() == 0:
    os.close(reader)
    def terminate(*_args):
        os.write(1, b"descendant stopped\\n")
        sys.exit(0)
    signal.signal(signal.SIGTERM, terminate)
    os.write(writer, b"ready")
    os.close(writer)
    time.sleep(2)
    os.write(1, b"descendant completed without cancellation\\n")
    sys.exit(0)
os.close(writer)
os.read(reader, 5)
os.close(reader)
sys.exit(23)
"""
    result, stdout, stderr = _run_default_command(
        (sys.executable, "-c", script), tmp_path, {}
    )

    assert result.exit_code == 23
    assert stdout == b"descendant stopped\n"
    assert stderr == b""


@pytest.mark.parametrize("fault", ["selector-construction", "second-registration"])
def test_default_command_runner_cleans_up_child_when_selector_setup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    process = Mock(pid=12345, stdout=Mock(), stderr=Mock())
    quiesce = Mock()
    selector = Mock()
    selector.register.side_effect = [
        None,
        RuntimeError("injected selector registration failure"),
    ]

    def selector_factory() -> Mock:
        if fault == "selector-construction":
            raise RuntimeError("injected selector construction failure")
        return selector

    monkeypatch.setattr(task.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(lifecycle, "quiesce_process_group", quiesce)
    monkeypatch.setattr(task.selectors, "DefaultSelector", selector_factory)
    with pytest.raises(RuntimeError, match="injected selector"):
        _run_default_command(("fixture-tool",), tmp_path, {})

    quiesce.assert_called_once_with(
        process.pid, process, lifecycle.DEFAULT_PROCESS_GROUP_OPS
    )
    process.stdout.close.assert_called_once_with()
    process.stderr.close.assert_called_once_with()
    if fault == "second-registration":
        selector.close.assert_called_once_with()
    else:
        selector.close.assert_not_called()


def _rewrite_task(built: TaskFixture) -> None:
    attempt = orchestration_contracts.load_json_object(built.manifest_path)
    attempt["tasks"][built.plan.machine_key][built.plan.scope["scope_id"]] = (
        built.definition
    )
    _publish_json(built.manifest_path, attempt)
    _publish_json(
        built.run_root / "locks/run.lock",
        orchestration_contracts.run_lock_record(attempt),
    )


def _manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _execute_task(plan: task.TaskPlan, *, ops: task.TaskOps) -> task.TaskOutcome:
    return task.execute_task(
        plan.path,
        expected_sha256=_manifest_sha256(plan.path),
        machine_key=plan.machine_key,
        scope_id=plan.scope["scope_id"],
        ops=ops,
    )


def _load_task(
    path: Path, *, machine_key: str = MACHINE_KEY, scope_id: str = SCOPE_ID
) -> task.TaskPlan:
    return task.load_task(
        path,
        expected_sha256=_manifest_sha256(path),
        machine_key=machine_key,
        scope_id=scope_id,
    )


def _record(path: str | Path) -> dict[str, Any]:
    return orchestration_contracts.load_json_object(path)


def _validate_verified(
    built: TaskFixture,
    **overrides: Any,
) -> dict[str, Any]:
    arguments = {
        "run_root": built.run_root,
        "execution": _record(built.plan.execution_path),
        "profile": _record(built.plan.profile_path),
        "machine_key": built.plan.machine_key,
        "scope": built.plan.scope,
        **overrides,
    }
    return task.validate_verified_task(Path(built.plan.verified_task_path), **arguments)


def _step00c_with_existing_sidecars(
    tmp_path: Path,
) -> tuple[
    workflow_fixture.WorkflowFixture,
    task.TaskPlan,
    dict[str, Any],
    tuple[Path, Path],
]:
    built = workflow_fixture.build(tmp_path)
    workflow_fixture.materialize_active_run_lock(built)
    machine_key = "emrys.stage.construct_FASTA_sidecars.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    manifest = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    record = manifest["tasks"][machine_key][scope_id]
    plan = _load_task(
        built.workflow_attempt_path, machine_key=machine_key, scope_id=scope_id
    )
    outputs = tuple(Path(item["path"]) for item in record["outputs"])
    assert len(outputs) == 2
    publication = task._NativePublication(plan)
    work = publication.prepare(reused=False)
    try:
        producer, _stdout, stderr = _run_default_command(
            tuple(record["producer_argv"]),
            built.run_root,
            {"EMRYS_TASK_WORK_DIR": str(work), "TMPDIR": str(work)},
        )
        assert producer.exit_code == 0, stderr.decode(errors="replace")
        publication.publish()
        publication.committed = True
    finally:
        publication.close()
    return built, plan, record, (outputs[0], outputs[1])


def test_success_publishes_schema_valid_content_bound_records(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    task_scope = Path(built.plan.task_attempt_path).parent
    assert not task_scope.exists()

    outcome = _execute_task(built.plan, ops=_fixed_ops())

    attempt = _record(outcome.task_attempt_path)
    verified = _record(outcome.verified_task_path)
    start = _record(built.plan.task_start_path)
    orchestration_contracts.validate_record("task-start", start)
    orchestration_contracts.validate_record("task-attempt", attempt)
    orchestration_contracts.validate_record("verified-task", verified)
    assert attempt["status"] == "succeeded"
    assert task_scope.is_dir()
    assert verified == {
        "schema_version": "emrys.verified-task.v2",
        "task_attempt_record": {
            "path": outcome.task_attempt_path.relative_to(built.run_root).as_posix(),
            "sha256": hashlib.sha256(
                outcome.task_attempt_path.read_bytes()
            ).hexdigest(),
        },
    }
    verified = _validate_verified(built)
    assert verified == attempt
    assert attempt["task_start_record"]["path"] == (
        Path(built.plan.task_start_path).relative_to(built.run_root).as_posix()
    )
    assert start["workflow_attempt_record"]["sha256"] == _manifest_sha256(
        built.manifest_path
    )
    lock_path = built.run_root / "locks" / "run.lock"
    assert start["run_lock"] == {
        "path": (f"attempts/{WORKFLOW_ATTEMPT_ID}/released-run-lock.json"),
        "sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
    }
    assert verified["status"] == "succeeded"
    assert verified["stable_inputs_rechecked"] is True
    assert [item["role"] for item in verified["inputs"]] == [
        "workflow_attempt",
        "execution_contract",
        "workflow_profile",
        "owner_input",
    ]
    for bound in (*verified["inputs"], *verified["outputs"]):
        content = Path(bound["path"]).read_bytes()
        assert bound["size_bytes"] == len(content)
        assert bound["sha256"] == hashlib.sha256(content).hexdigest()
    report = Path(built.definition["validation_report_path"])
    assert (
        verified["validation_report"]["sha256"]
        == hashlib.sha256(report.read_bytes()).hexdigest()
    )
    assert verified["native_receipt"] is not None
    assert (
        b"producer stdout complete\nvalidator stdout complete\n"
        in Path(built.plan.stdout_path).read_bytes()
    )
    assert (
        b"producer stderr complete\nvalidator stderr complete\n"
        in Path(built.plan.stderr_path).read_bytes()
    )
    assert attempt["stdout_log"] == {
        "path": Path(built.plan.stdout_path).relative_to(built.run_root).as_posix(),
        "sha256": hashlib.sha256(Path(built.plan.stdout_path).read_bytes()).hexdigest(),
    }
    assert attempt["stderr_log"] == {
        "path": Path(built.plan.stderr_path).relative_to(built.run_root).as_posix(),
        "sha256": hashlib.sha256(Path(built.plan.stderr_path).read_bytes()).hexdigest(),
    }


def test_stream_capture_preserves_exact_opaque_bytes_and_per_stream_order(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        label = b"producer" if "producer" in argv else b"validator"
        os.write(stdout_descriptor, b"\x00\xff" + label + b":before\n")
        os.write(stderr_descriptor, b"\xfe\x00" + label + b":before\n")
        result = defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )
        os.write(stdout_descriptor, b"\x80" + label + b":after\n")
        os.write(stderr_descriptor, b"\x81" + label + b":after\n")
        return result

    def semantic(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        os.write(stdout_descriptor, b"\x00\xffsemantic:before\n")
        os.write(stderr_descriptor, b"\xfe\x00semantic:before\n")
        result = defaults.run_semantic_all_pass(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )
        os.write(stdout_descriptor, b"\x80semantic:after\n")
        os.write(stderr_descriptor, b"\x81semantic:after\n")
        return result

    _execute_task(
        built.plan,
        ops=replace(
            defaults,
            run_command=command,
            run_semantic_all_pass=semantic,
        ),
    )

    report_path = Path(built.definition["validation_report_path"])
    report_sha256 = hashlib.sha256(report_path.read_bytes()).hexdigest()
    expected_stdout = b"".join(
        (
            b"\x00\xffproducer:before\n",
            b"producer stdout complete\n",
            b"\x80producer:after\n",
            b"\x00\xffvalidator:before\n",
            b"validator stdout complete\n",
            b"\x80validator:after\n",
            b"\x00\xffsemantic:before\n",
            b"Validation report semantic all-pass: PASS\n",
            f"  Report: {report_path}\n".encode(),
            f"  SHA-256: {report_sha256}\n".encode(),
            b"  Check rows: 1\n",
            b"  Check IDs: test_double_contract\n",
            b"\x80semantic:after\n",
        )
    )
    expected_stderr = b"".join(
        (
            b"\xfe\x00producer:before\n",
            b"producer stderr complete\n",
            b"\x81producer:after\n",
            b"\xfe\x00validator:before\n",
            b"validator stderr complete\n",
            b"\x81validator:after\n",
            b"\xfe\x00semantic:before\n",
            b"\x81semantic:after\n",
        )
    )
    assert Path(built.plan.stdout_path).read_bytes() == expected_stdout
    assert Path(built.plan.stderr_path).read_bytes() == expected_stderr


def test_records_exact_public_commands_and_exit_codes(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)

    _execute_task(built.plan, ops=_fixed_ops())

    verified = _validate_verified(built)
    assert verified["producer"] == {
        "argv": built.definition["producer_argv"],
        "exit_code": 0,
    }
    assert verified["validator"] == {
        "argv": built.definition["validator_argv"],
        "exit_code": 0,
    }
    semantic = verified["semantic_all_pass"]
    assert semantic["exit_code"] == 0
    assert semantic["argv"] == list(
        controlled_python_argv(
            sys.executable,
            "-m",
            "emrys",
            "validate",
            "all-pass",
            "--report",
            built.definition["validation_report_path"],
            "--step-id",
            "01",
            "--scope-id",
            SCOPE_ID,
        )
    )


def test_zero_exit_validator_fail_row_blocks_verified_publication(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    built.definition["validator_argv"].extend(["--status", "fail"])
    _rewrite_task(built)

    with pytest.raises(task.TaskBoundaryError, match="Semantic all-pass"):
        _execute_task(built.plan, ops=_fixed_ops())

    attempt = _record(built.plan.task_attempt_path)
    assert attempt["status"] == "failed"
    assert attempt["task_start_record"] is not None
    assert Path(built.plan.task_start_path).is_file()
    assert attempt["validator"]["exit_code"] == 0
    assert attempt["semantic_all_pass"]["exit_code"] == 1
    assert attempt["validation_report"] is not None
    assert not Path(built.plan.verified_task_path).exists()
    assert (
        Path(built.definition["validation_report_path"])
        .read_text()
        .splitlines()[1]
        .split("\t")[3]
        == "fail"
    )


def test_producer_failure_removes_working_output_and_preserves_attempt_evidence(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    built.definition["producer_argv"].extend(["--fail-after", "1"])
    _rewrite_task(built)

    with pytest.raises(task.TaskBoundaryError, match="Producer command exited"):
        _execute_task(built.plan, ops=_fixed_ops())

    attempt = _record(built.plan.task_attempt_path)
    assert attempt["producer"]["exit_code"] == 23
    assert attempt["validator"] is None
    assert attempt["semantic_all_pass"] is None
    assert not Path(built.definition["outputs"][0]["path"]).exists()
    assert not Path(built.definition["outputs"][0]["working_path"]).parent.exists()
    assert not Path(built.definition["outputs"][1]["path"]).exists()
    assert not Path(built.plan.verified_task_path).exists()
    assert (
        b"producer failed after aligned_bam"
        in Path(built.plan.stderr_path).read_bytes()
    )


@pytest.mark.parametrize(
    "fault", ("after_link", "foreign_final", "owner_loss", "residue", "input_drift")
)
def test_native_publication_preserves_unowned_state_and_rolls_back_owned_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    built = _task_fixture(tmp_path)
    first, second = (Path(item["path"]) for item in built.definition["outputs"][:2])
    working = Path(built.definition["outputs"][0]["working_path"]).parent
    lock = Path(built.definition["publication"]["locks"][0])
    original_link = task.os.link
    defaults = _fixed_ops()

    def link(source: Any, destination: Any, **kwargs: Any) -> None:
        if Path(destination) == first:
            original_link(source, destination, **kwargs)
            if fault == "after_link":
                raise OSError("interrupted after the native link succeeded")
            if fault == "input_drift":
                built.mutable_input.write_bytes(b"input changed during publication\n")
        elif Path(destination) == second and fault == "foreign_final":
            second.write_bytes(b"foreign final\n")
            original_link(source, destination, **kwargs)
        else:
            original_link(source, destination, **kwargs)

    def command(*arguments: Any) -> task.CommandResult:
        result = defaults.run_command(*arguments)
        if fault == "owner_loss":
            (lock / "owner").write_bytes(b"foreign owner\n")
        return result

    if fault == "residue":
        (first.parent / ".owner.recovery").write_bytes(b"retained recovery\n")
    monkeypatch.setattr(task.os, "link", link)
    with pytest.raises(task.TaskBoundaryError):
        _execute_task(built.plan, ops=replace(defaults, run_command=command))
    assert not first.exists()
    assert not Path(built.plan.verified_task_path).exists()
    if fault == "input_drift":
        assert all(
            not Path(item["path"]).exists() for item in built.definition["outputs"]
        )
        assert not Path(built.definition["validation_report_path"]).exists()
    if fault == "foreign_final":
        assert second.read_bytes() == b"foreign final\n"
    if fault in {"foreign_final", "owner_loss"}:
        assert working.is_dir() and lock.is_dir()
    else:
        assert not working.exists() and not lock.exists()


@pytest.mark.parametrize(
    "mutation", ("none", "replace_input", "add_input", "empty_input")
)
def test_star_publication_and_input_directory_roster_are_content_bound(
    tmp_path: Path, mutation: str
) -> None:
    built = _task_fixture(tmp_path)
    inputs = built.run_root / "inputs" / "index"
    inputs.mkdir()
    member = inputs / "Genome"
    member.write_bytes(b"reference genome\n")
    final_directory = built.run_root / "results" / "index"
    working = final_directory.parent / ".index.owner.work"
    built.definition["native_receipt_path"] = None
    built.definition["outputs"] = [
        {
            "role": "genome",
            "path": str(final_directory / "Genome"),
            "working_path": str(working / "Genome"),
        }
    ]
    built.definition["publication"]["input_directories"] = [str(inputs)]
    built.definition["publication"]["output_directory"] = str(final_directory)
    built.definition["producer_argv"] = list(
        controlled_python_argv(
            sys.executable,
            str(TEST_DOUBLE),
            "producer",
            "--output",
            f"genome={working / 'Genome'}",
            "--output",
            f"star_log={working / 'Log.out'}",
        )
    )
    _rewrite_task(built)
    defaults = _fixed_ops()

    def command(*arguments: Any) -> task.CommandResult:
        result = defaults.run_command(*arguments)
        if mutation == "replace_input":
            replacement = inputs / "replacement"
            replacement.write_bytes(member.read_bytes())
            replacement.replace(member)
        elif mutation == "add_input":
            (inputs / "new-member").write_bytes(b"changed roster\n")
        elif mutation == "empty_input":
            member.write_bytes(b"")
        elif arguments[0] == tuple(built.definition["producer_argv"]):
            (working / "Log.progress.out").touch()
        return result

    if mutation != "none":
        with pytest.raises(task.TaskBoundaryError, match="input directory"):
            _execute_task(built.plan, ops=replace(defaults, run_command=command))
        assert not final_directory.exists()
        return
    outcome = _execute_task(built.plan, ops=replace(defaults, run_command=command))
    assert {path.name for path in final_directory.iterdir()} == {
        "Genome",
        "Log.out",
        "Log.progress.out",
    }
    verified = _validate_verified(built)
    assert {Path(item["path"]).name for item in verified["outputs"]} == {
        "Genome",
        "Log.out",
        "Log.progress.out",
    }
    assert any(item["path"] == str(member) for item in verified["inputs"])
    assert not working.exists()
    assert _validate_verified(built)["status"] == "succeeded"


def test_catchable_task_termination_kills_worker_group_and_preserves_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    built = _task_fixture(tmp_path)
    built.definition["producer_argv"] = list(
        controlled_python_argv(
            sys.executable,
            "-c",
            "import os,signal,subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); os.kill(os.getppid(),signal.SIGTERM); time.sleep(60)",
        )
    )
    _rewrite_task(built)
    original = task.os.killpg
    killed: list[int] = []

    def kill_group(identifier: int, signum: int) -> None:
        killed.append(identifier)
        original(identifier, signum)

    monkeypatch.setattr(task.os, "killpg", kill_group)
    with pytest.raises(task.TaskBoundaryError, match="interrupted by signal"):
        _execute_task(built.plan, ops=_fixed_ops())
    assert killed and all(identifier != os.getpgrp() for identifier in killed)
    assert _record(built.plan.task_attempt_path)["status"] == "failed"
    assert not Path(built.definition["outputs"][0]["working_path"]).parent.exists()


def test_historical_attempt_is_rejected_before_task_mutation(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    attempt = _record(built.manifest_path)
    attempt["schema_version"] = "emrys.workflow-attempt.v1"
    _publish_json(built.manifest_path, attempt)
    with pytest.raises(task.TaskBoundaryError, match="schema_version"):
        _execute_task(built.plan, ops=_fixed_ops())
    assert not Path(built.plan.task_start_path).exists()


def test_uncertain_worker_group_preserves_workspace_and_owner_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    built = _task_fixture(tmp_path)

    def uncertain(*_arguments: Any) -> None:
        raise lifecycle.ProcessGroupAmbiguity("Could not prove worker group absent")

    monkeypatch.setattr(lifecycle, "quiesce_process_group", uncertain)
    with pytest.raises(
        task.TaskBoundaryError, match="Could not prove worker group absent"
    ):
        _execute_task(built.plan, ops=_fixed_ops())
    assert Path(built.definition["outputs"][0]["working_path"]).is_file()
    assert Path(built.definition["publication"]["locks"][0]).is_dir()
    assert not Path(built.definition["outputs"][0]["path"]).exists()
    assert not Path(built.plan.verified_task_path).exists()


def test_unexpected_interruption_preserves_and_closes_partial_task_logs(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    observed_descriptors: list[int] = []

    def interrupt(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        del argv, cwd, environment
        observed_descriptors.extend((stdout_descriptor, stderr_descriptor))
        os.write(stdout_descriptor, b"partial stdout\x00\xff\n")
        os.write(stderr_descriptor, b"partial stderr\xfe\x00\n")
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _execute_task(
            built.plan,
            ops=replace(defaults, run_command=interrupt),
        )

    assert Path(built.plan.task_start_path).is_file()
    assert Path(built.plan.stdout_path).read_bytes() == (b"partial stdout\x00\xff\n")
    assert Path(built.plan.stderr_path).read_bytes() == (b"partial stderr\xfe\x00\n")
    assert not Path(built.plan.task_attempt_path).exists()
    assert not Path(built.plan.verified_task_path).exists()
    for descriptor in observed_descriptors:
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(descriptor)


@pytest.mark.parametrize("destination", ["output", "report", "receipt"])
def test_preexisting_native_or_validation_residue_fails_closed(
    tmp_path: Path,
    destination: str,
) -> None:
    built = _task_fixture(tmp_path)
    paths = {
        "output": Path(built.definition["outputs"][0]["path"]),
        "report": Path(built.definition["validation_report_path"]),
        "receipt": Path(built.definition["native_receipt_path"]),
    }
    foreign = paths[destination]
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_bytes(b"foreign predecessor\n")

    with pytest.raises(task.TaskBoundaryError, match="pre-existing"):
        _execute_task(built.plan, ops=_fixed_ops())

    assert foreign.read_bytes() == b"foreign predecessor\n"
    attempt = _record(built.plan.task_attempt_path)
    assert attempt["status"] == "failed"
    assert attempt["task_start_record"] is None
    assert not Path(built.plan.task_start_path).exists()
    assert Path(built.plan.task_attempt_path).parent.is_dir()
    assert attempt["producer"] is None
    assert not Path(built.plan.verified_task_path).exists()


def test_input_mutation_blocks_verified_publication(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    built.definition["producer_argv"].extend(
        ["--mutate-input", str(built.mutable_input)]
    )
    _rewrite_task(built)

    with pytest.raises(task.TaskBoundaryError, match="stable task input changed"):
        _execute_task(built.plan, ops=_fixed_ops())

    attempt = _record(built.plan.task_attempt_path)
    assert attempt["stable_inputs_rechecked"] is False
    assert attempt["validator"] is None
    assert attempt["semantic_all_pass"] is None
    assert not Path(built.plan.verified_task_path).exists()


def test_processing_source_input_must_match_its_admitted_snapshot(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    original = built.mutable_input.read_bytes()
    built.definition["inputs"][0].update(
        {
            "size_bytes": len(original),
            "sha256": hashlib.sha256(original).hexdigest(),
        }
    )
    built.mutable_input.write_bytes(b"changed after source admission\n")
    _rewrite_task(built)

    with pytest.raises(
        task.TaskBoundaryError,
        match="differs from its immutable binding",
    ):
        _execute_task(built.plan, ops=_fixed_ops())

    attempt = _record(built.plan.task_attempt_path)
    assert attempt["status"] == "failed"
    assert attempt["producer"] is None
    assert attempt["task_start_record"] is None
    assert not Path(built.plan.task_start_path).exists()
    assert not Path(built.plan.verified_task_path).exists()


@pytest.mark.parametrize(
    ("collection", "field", "value", "message"),
    (
        ("inputs", "size_bytes", None, "size_bytes must be a nonnegative integer"),
        ("inputs", "sha256", None, "sha256 must be 64 lowercase hex"),
        (
            "outputs",
            "size_bytes",
            0,
            r"outputs\[0\] is not closed: unknown sha256, size_bytes",
        ),
    ),
)
def test_processing_source_binding_is_closed_and_input_only(
    tmp_path: Path,
    collection: str,
    field: str,
    value: object,
    message: str,
) -> None:
    built = _task_fixture(tmp_path)
    original = built.mutable_input.read_bytes()
    declaration = built.definition[collection][0]
    declaration.update(
        {"size_bytes": len(original), "sha256": hashlib.sha256(original).hexdigest()}
    )
    declaration[field] = value
    _rewrite_task(built)

    with pytest.raises(task.TaskBoundaryError, match=message):
        _execute_task(built.plan, ops=_fixed_ops())
    assert not Path(built.plan.task_attempt_path).exists()
    assert not Path(built.plan.task_start_path).exists()


def test_successful_dispatch_rerun_refuses_immutable_predecessor(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    _execute_task(built.plan, ops=_fixed_ops())
    verified = Path(built.plan.verified_task_path)
    predecessor = verified.read_bytes()

    with pytest.raises(task.TaskBoundaryError, match="task-start record"):
        _execute_task(built.plan, ops=_fixed_ops())

    assert verified.read_bytes() == predecessor


def test_dispatch_is_closed_and_binds_exact_owner_scope(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    built.definition["unexpected"] = True
    _rewrite_task(built)
    with pytest.raises(
        task.TaskBoundaryError, match="unexpected|Additional properties"
    ):
        _load_task(built.manifest_path)

    built = _task_fixture(tmp_path / "second")
    attempt = _record(built.manifest_path)
    attempt["tasks"][MACHINE_KEY] = {"not_selected": built.definition}
    _publish_json(built.manifest_path, attempt)
    plan = _load_task(built.manifest_path, scope_id="not_selected")
    with pytest.raises(task.TaskBoundaryError, match="not selected"):
        _execute_task(plan, ops=_fixed_ops())


def test_dispatch_hash_is_bound_before_parsing_or_producer_execution(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path / "hash-mismatch")
    wrong = "0" * 64
    with pytest.raises(task.TaskBoundaryError, match="SHA-256 differs"):
        task.execute_task(
            built.manifest_path,
            expected_sha256=wrong,
            machine_key=MACHINE_KEY,
            scope_id=SCOPE_ID,
            ops=_fixed_ops(),
        )
    assert not Path(built.plan.task_attempt_path).exists()

    changed = _task_fixture(tmp_path / "changed-after-load")
    expected = _manifest_sha256(changed.manifest_path)
    admitted = task.load_task(
        changed.manifest_path,
        expected_sha256=expected,
        machine_key=MACHINE_KEY,
        scope_id=SCOPE_ID,
    )
    modified_attempt = _record(changed.manifest_path)
    modified_attempt["tasks"][MACHINE_KEY][SCOPE_ID]["producer_argv"].append(
        "--foreign-change"
    )
    _publish_json(changed.manifest_path, modified_attempt)
    calls: list[tuple[str, ...]] = []

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        _environment: Mapping[str, str],
        _stdout_descriptor: int,
        _stderr_descriptor: int,
    ) -> task.CommandResult:
        calls.append(argv)
        return task.CommandResult(argv, 0)

    defaults = _fixed_ops()
    ops = task.TaskOps(
        run_command=command,
        run_semantic_all_pass=command,
        publish_bytes=defaults.publish_bytes,
        now=lambda: datetime(2026, 8, 12, 12, 2, tzinfo=UTC),
    )
    with pytest.raises(task.TaskBoundaryError, match="Workflow attempt changed"):
        task.run_task(admitted, backend=admitted.backend, ops=ops)
    # Even a caller forwarding the modified file's matching hash cannot replace
    # the original plan admitted by the already-published outer Run lock.
    with pytest.raises(task.TaskBoundaryError, match="attempt_record_sha256"):
        _execute_task(changed.plan, ops=ops)
    assert calls == []


def test_task_start_publication_failure_after_link_never_enters_producer(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    calls: list[tuple[str, ...]] = []
    injected = False

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        _environment: Mapping[str, str],
        _stdout_descriptor: int,
        _stderr_descriptor: int,
    ) -> task.CommandResult:
        calls.append(argv)
        return task.CommandResult(argv, 0)

    def publish(path: Path, data: bytes) -> None:
        nonlocal injected
        defaults.publish_bytes(path, data)
        if path == Path(built.plan.task_start_path) and not injected:
            injected = True
            raise task.TaskBoundaryError("injected after task-start link")

    ops = replace(
        defaults,
        run_command=command,
        run_semantic_all_pass=command,
        publish_bytes=publish,
    )
    with pytest.raises(task.TaskBoundaryError, match="injected after task-start"):
        _execute_task(built.plan, ops=ops)

    assert calls == []
    start_path = Path(built.plan.task_start_path)
    assert start_path.is_file()
    orchestration_contracts.validate_record(
        "task-start", orchestration_contracts.load_json_object(start_path)
    )
    attempt = orchestration_contracts.load_record(
        built.plan.task_attempt_path, "task-attempt"
    )
    assert attempt["task_start_record"] is None
    assert attempt["producer"] is None


def test_task_streams_are_fsynced_and_closed_before_attempt_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    events: list[str] = []
    original_fsync = task.os.fsync
    original_close = task.os.close
    log_paths = {
        "stdout": Path(built.plan.stdout_path),
        "stderr": Path(built.plan.stderr_path),
    }

    def descriptor_log_label(descriptor: int) -> str | None:
        try:
            descriptor_state = os.fstat(descriptor)
        except OSError:
            return None
        for label, path in log_paths.items():
            try:
                path_state = path.stat(follow_symlinks=False)
            except OSError:
                continue
            if os.path.samestat(descriptor_state, path_state):
                return label
        return None

    def tracked_fsync(descriptor: int) -> None:
        label = descriptor_log_label(descriptor)
        if label is not None:
            events.append(f"fsync-{label}")
        original_fsync(descriptor)

    def tracked_close(descriptor: int) -> None:
        label = descriptor_log_label(descriptor)
        if label is not None:
            events.append(f"close-{label}")
        original_close(descriptor)

    def publish(path: Path, data: bytes) -> None:
        if path == Path(built.plan.task_attempt_path):
            events.append("publish-attempt")
        defaults.publish_bytes(path, data)

    monkeypatch.setattr(task.os, "fsync", tracked_fsync)
    monkeypatch.setattr(task.os, "close", tracked_close)
    _execute_task(
        built.plan,
        ops=replace(defaults, publish_bytes=publish),
    )

    attempt_index = events.index("publish-attempt")
    for label in log_paths:
        assert events.index(f"fsync-{label}") < events.index(f"close-{label}")
        assert events.index(f"close-{label}") < attempt_index


@pytest.mark.parametrize("label", ["stdout", "stderr"])
def test_same_byte_log_replacement_while_descriptor_open_is_not_admitted(
    tmp_path: Path,
    label: str,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    field = f"{label}_path"
    replacement_bytes = b""

    def semantic(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        nonlocal replacement_bytes
        result = defaults.run_semantic_all_pass(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )
        descriptor = stdout_descriptor if label == "stdout" else stderr_descriptor
        target = Path(getattr(built.plan, field))
        original_state = os.fstat(descriptor)
        replacement_bytes = target.read_bytes()
        replacement = target.with_name(f".{target.name}.foreign-replacement")
        replacement.write_bytes(replacement_bytes)
        replacement.replace(target)
        current_state = target.stat(follow_symlinks=False)
        still_open_state = os.fstat(descriptor)
        assert os.path.samestat(still_open_state, original_state)
        assert not os.path.samestat(current_state, still_open_state)
        return result

    with pytest.raises(
        task.TaskBoundaryError,
        match=rf"task {label} log path no longer matches its synchronized descriptor",
    ):
        _execute_task(
            built.plan,
            ops=replace(defaults, run_semantic_all_pass=semantic),
        )

    assert Path(getattr(built.plan, field)).read_bytes() == replacement_bytes
    assert not Path(built.plan.task_attempt_path).exists()
    assert not Path(built.plan.verified_task_path).exists()


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("stdout_path", "Task stdout changed"),
        ("stderr_path", "Task stderr changed"),
        ("task_attempt_path", "Terminal task result changed"),
        ("validation_report_path", "Validation report changed"),
        ("outputs", "producer output changed"),
    ],
)
def test_evidence_change_during_terminal_publication_blocks_verified_marker(
    tmp_path: Path,
    field: str,
    message: str,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    target = Path(
        built.definition[field][0]["path"]
        if field == "outputs"
        else getattr(built.plan, field)
    )

    def publish(path: Path, data: bytes) -> None:
        defaults.publish_bytes(path, data)
        if path == Path(built.plan.task_attempt_path):
            with target.open("ab") as stream:
                stream.write(b"foreign evidence bytes\n")

    with pytest.raises(task.TaskBoundaryError, match=message):
        _execute_task(
            built.plan,
            ops=replace(defaults, publish_bytes=publish),
        )

    assert Path(built.plan.task_attempt_path).is_file()
    assert not Path(built.plan.verified_task_path).exists()


def test_internal_module_cli_is_isolated_and_not_a_public_lifecycle_command(
    tmp_path: Path,
) -> None:
    help_result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys.orchestration.run_coordinator.task",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    assert "--attempt" in help_result.stdout
    assert "--attempt-sha256" in help_result.stdout
    assert "not a public" in help_result.stdout
    assert "run/resume/inspect" in help_result.stdout

    built = _task_fixture(tmp_path)
    result = subprocess.run(
        [
            *controlled_python_argv(
                sys.executable,
                "-m",
                "emrys.orchestration.run_coordinator.task",
            ),
            "--attempt",
            str(built.manifest_path),
            "--attempt-sha256",
            _manifest_sha256(built.manifest_path),
            "--owner",
            built.plan.machine_key,
            "--scope",
            built.plan.scope["scope_id"],
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert Path(built.plan.verified_task_path).is_file()


def test_existing_verified_or_partial_task_state_is_never_replaced(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    for field in ("verified_task_path", "stdout_path"):
        destination = Path(getattr(built.plan, field))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"foreign state\n")
        with pytest.raises(task.TaskBoundaryError, match="Refusing pre-existing"):
            _execute_task(built.plan, ops=_fixed_ops())
        assert destination.read_bytes() == b"foreign state\n"
        destination.unlink()


def test_task_log_symlink_injected_at_stream_open_is_never_followed(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"foreign bytes\n")
    calls: list[tuple[str, ...]] = []

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        del cwd, environment, stdout_descriptor, stderr_descriptor
        calls.append(argv)
        return task.CommandResult(argv, 0)

    def publish(path: Path, data: bytes) -> None:
        defaults.publish_bytes(path, data)
        if path == Path(built.plan.task_start_path):
            Path(built.plan.stdout_path).symlink_to(outside)

    with pytest.raises(task.TaskBoundaryError, match="canonical|replace existing"):
        _execute_task(
            built.plan,
            ops=replace(
                defaults,
                run_command=command,
                run_semantic_all_pass=command,
                publish_bytes=publish,
            ),
        )

    assert calls == []
    stdout_path = Path(built.plan.stdout_path)
    assert stdout_path.is_symlink()
    assert outside.read_bytes() == b"foreign bytes\n"
    assert not Path(built.plan.stderr_path).exists()
    assert not Path(built.plan.task_attempt_path).exists()
    assert not Path(built.plan.verified_task_path).exists()


def test_dispatch_and_output_paths_may_not_alias(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    built.definition["outputs"][0]["path"] = str(built.manifest_path)
    _rewrite_task(built)
    with pytest.raises(task.TaskBoundaryError, match="aliases an input"):
        _load_task(built.manifest_path)


def test_read_only_verified_admission_rechecks_every_content_binding(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    _execute_task(built.plan, ops=_fixed_ops())
    execution = _record(built.plan.execution_path)
    profile = _record(built.plan.profile_path)

    admitted = _validate_verified(
        built,
        execution=execution,
        profile=profile,
    )
    assert admitted["status"] == "succeeded"

    output = Path(built.definition["outputs"][0]["path"])
    output.write_bytes(b"changed after verification\n")
    with pytest.raises(task.TaskBoundaryError, match="content binding"):
        _validate_verified(
            built,
            execution=execution,
            profile=profile,
        )


def test_task_log_hashing_uses_shared_streaming_hasher_without_full_log_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()
    log_paths = {
        Path(built.plan.stdout_path),
        Path(built.plan.stderr_path),
    }
    hashed_paths: list[Path] = []
    original_hash = task.sha256_with_identity
    original_read = task._read_bound_file

    def tracked_hash(
        path: Path,
        label: str,
        *,
        nonempty: bool = True,
    ) -> tuple[str, os.stat_result]:
        if path in log_paths:
            hashed_paths.append(path)
        return original_hash(path, label, nonempty=nonempty)

    def reject_full_log_read(path: Path, label: str) -> tuple[bytes, os.stat_result]:
        if path in log_paths:
            raise AssertionError(f"task log was fully read: {label}")
        return original_read(path, label)

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        if "producer" in argv:
            large_chunk = b"x" * (1024 * 1024)
            assert os.write(stdout_descriptor, large_chunk) == len(large_chunk)
            assert os.write(stdout_descriptor, large_chunk) == len(large_chunk)
            assert os.write(stdout_descriptor, b"tail") == 4
        return defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )

    monkeypatch.setattr(task, "sha256_with_identity", tracked_hash)
    monkeypatch.setattr(task, "_read_bound_file", reject_full_log_read)
    _execute_task(
        built.plan,
        ops=replace(defaults, run_command=command),
    )
    _validate_verified(built)

    assert set(hashed_paths) == log_paths
    with Path(built.plan.stdout_path).open("ab") as stream:
        stream.write(b"mutation")
    with pytest.raises(task.TaskBoundaryError, match="SHA-256 no longer matches"):
        _validate_verified(built)


def test_read_only_task_start_admission_rechecks_every_origin(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    _execute_task(built.plan, ops=_fixed_ops())
    execution = _record(built.plan.execution_path)
    profile = _record(built.plan.profile_path)
    start_path = Path(built.plan.task_start_path)

    admitted = task.validate_task_start(
        start_path,
        run_root=built.run_root,
        execution=execution,
        profile=profile,
        machine_key=MACHINE_KEY,
        scope=built.plan.scope,
    )
    assert admitted["workflow_attempt_record"]["sha256"] == _manifest_sha256(
        built.manifest_path
    )

    with built.manifest_path.open("ab") as stream:
        stream.write(b"changed after task entry\n")
    with pytest.raises(task.TaskBoundaryError, match="SHA-256"):
        task.validate_task_start(
            start_path,
            run_root=built.run_root,
            execution=execution,
            profile=profile,
            machine_key=MACHINE_KEY,
            scope=built.plan.scope,
        )


def test_terminal_workflow_attempt_cannot_start_a_task(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    terminal = (
        built.run_root / "attempts" / WORKFLOW_ATTEMPT_ID / "attempt-receipt.json"
    )
    terminal.write_bytes(b"terminal-origin\n")

    with pytest.raises(task.TaskBoundaryError, match="terminal workflow attempt"):
        _execute_task(built.plan, ops=_fixed_ops())

    assert not Path(built.plan.task_start_path).exists()


def test_foreign_lock_namespace_blocks_task_entry(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    (built.run_root / "locks" / "foreign.lock").write_bytes(b"foreign\n")

    with pytest.raises(
        task.TaskBoundaryError, match="Unexpected retained aggregate lock state"
    ):
        _execute_task(built.plan, ops=_fixed_ops())

    assert not Path(built.plan.task_start_path).exists()


def test_changed_installed_package_blocks_before_task_start(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    calls: list[str] = []

    def reject_transient_head(**_kwargs: Any) -> None:
        calls.append("attest")
        raise task.InstalledPackageError(
            "Installed package differs from the workflow attempt"
        )

    defaults = _fixed_ops()
    ops = replace(defaults, admit_installed_package=reject_transient_head)
    with pytest.raises(task.TaskBoundaryError, match="Could not admit task child"):
        _execute_task(built.plan, ops=ops)

    assert calls == ["attest"]
    assert not Path(built.plan.task_start_path).exists()


def test_task_child_rechecks_source_identity_at_irreversible_entry(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    calls = 0
    production_attester = _fixed_ops().admit_installed_package

    def transient_move(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise task.InstalledPackageError("changed package identity")
        return production_attester(**kwargs)

    defaults = _fixed_ops()
    ops = replace(defaults, admit_installed_package=transient_move)
    with pytest.raises(task.TaskBoundaryError, match="changed package identity"):
        _execute_task(built.plan, ops=ops)

    assert calls == 2
    assert not Path(built.plan.task_start_path).exists()


@pytest.mark.parametrize(
    "field",
    [
        "verified_task_path",
        "task_attempt_path",
        "validation_report_path",
        "native_receipt_path",
        "task_start_path",
    ],
)
def test_read_only_verified_admission_rejects_mutated_references(
    tmp_path: Path,
    field: str,
) -> None:
    built = _task_fixture(tmp_path)
    _execute_task(built.plan, ops=_fixed_ops())
    referenced = Path(getattr(built.plan, field))
    with referenced.open("ab") as stream:
        stream.write(b"mutated-after-publication\n")

    with pytest.raises(task.TaskBoundaryError):
        _validate_verified(built)


def test_read_only_verified_admission_rejects_wrong_identity_and_scope(
    tmp_path: Path,
) -> None:
    built = _task_fixture(tmp_path)
    _execute_task(built.plan, ops=_fixed_ops())
    with pytest.raises(task.TaskBoundaryError, match="scope"):
        _validate_verified(
            built,
            scope={"scope_type": "sample", "scope_id": "PUM1_1"},
        )


def test_semantic_gate_cannot_change_the_report_it_approves(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()

    def semantic(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        result = defaults.run_semantic_all_pass(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )
        with Path(built.definition["validation_report_path"]).open("ab") as stream:
            stream.write(b"post-gate mutation\n")
        return result

    ops = replace(defaults, run_semantic_all_pass=semantic)
    with pytest.raises(task.TaskBoundaryError, match="report changed"):
        _execute_task(built.plan, ops=ops)
    assert not Path(built.plan.verified_task_path).exists()


def test_validator_cannot_change_a_producer_output(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    defaults = _fixed_ops()

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        result = defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )
        if "validator" in argv:
            with Path(built.definition["outputs"][0]["path"]).open("ab") as stream:
                stream.write(b"validator mutation\n")
        return result

    ops = replace(defaults, run_command=command)
    with pytest.raises(task.TaskBoundaryError, match="producer output changed"):
        _execute_task(built.plan, ops=ops)
    assert not Path(built.plan.verified_task_path).exists()


def test_symlinked_output_and_contract_ancestors_fail_closed(tmp_path: Path) -> None:
    built = _task_fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    results = built.run_root / "results"
    shutil.rmtree(results)
    results.symlink_to(outside, target_is_directory=True)
    with pytest.raises(task.TaskBoundaryError, match="symlink ancestor"):
        _execute_task(built.plan, ops=_fixed_ops())

    built = _task_fixture(tmp_path / "contract-case")
    contract = built.run_root / "contract"
    moved = built.run_root / "real-contract"
    contract.rename(moved)
    contract.symlink_to(moved, target_is_directory=True)
    with pytest.raises(task.TaskBoundaryError, match="canonical|symlink ancestor"):
        _load_task(built.manifest_path)


def test_step00c_symlinked_stationary_reference_blocks_before_producer(
    tmp_path: Path,
) -> None:
    built = workflow_fixture.build(tmp_path / "workflow-fixture")
    workflow_fixture.materialize_active_run_lock(built)
    machine_key = "emrys.stage.construct_FASTA_sidecars.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    manifest = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    record = manifest["tasks"][machine_key][scope_id]
    plan = _load_task(
        built.workflow_attempt_path, machine_key=machine_key, scope_id=scope_id
    )
    fasta = Path(str(built.execution["reference"]["fasta"]["path"]))
    original_parent = fasta.parent
    real_parent = original_parent.with_name("reference-real")
    original_parent.rename(real_parent)
    original_parent.symlink_to(real_parent, target_is_directory=True)

    fai = Path(f"{fasta}.fai")
    sequence_dict = fasta.with_name(f"{fasta.stem}.dict")
    record["producer_argv"] = ["producer-must-not-run"]
    _publish_json(built.workflow_attempt_path, manifest)

    calls: list[tuple[str, ...]] = []

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        _environment: Mapping[str, str],
        _stdout_descriptor: int,
        _stderr_descriptor: int,
    ) -> task.CommandResult:
        calls.append(argv)
        return task.CommandResult(argv, 0)

    defaults = _fixed_ops()
    ops = replace(
        defaults,
        run_command=command,
        run_semantic_all_pass=command,
    )
    with pytest.raises(
        task.TaskBoundaryError, match="stationary FASTA must be canonical"
    ):
        _execute_task(plan, ops=ops)

    assert calls == []
    assert not fai.exists()
    assert not sequence_dict.exists()


def test_step00c_parent_permission_drift_blocks_before_task_start(
    tmp_path: Path,
) -> None:
    built = workflow_fixture.build(tmp_path / "workflow-fixture")
    workflow_fixture.materialize_active_run_lock(built)
    machine_key = "emrys.stage.construct_FASTA_sidecars.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    manifest = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    record = manifest["tasks"][machine_key][scope_id]
    plan = _load_task(
        built.workflow_attempt_path, machine_key=machine_key, scope_id=scope_id
    )
    parent = Path(str(built.execution["reference"]["fasta"]["path"])).parent
    calls: list[tuple[str, ...]] = []

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        _environment: Mapping[str, str],
        _stdout_descriptor: int,
        _stderr_descriptor: int,
    ) -> task.CommandResult:
        calls.append(argv)
        return task.CommandResult(argv, 0)

    defaults = _fixed_ops()
    parent_checks = 0

    def permission_drift(path: Path, mode: int) -> bool:
        nonlocal parent_checks
        if path != parent:
            return os.access(path, mode)
        assert mode == os.R_OK | os.W_OK | os.X_OK
        parent_checks += 1
        return parent_checks == 1

    with pytest.raises(task.TaskBoundaryError, match="not readable, writable"):
        _execute_task(
            plan,
            ops=replace(
                defaults,
                run_command=command,
                run_semantic_all_pass=command,
                path_access=permission_drift,
            ),
        )

    assert parent_checks == 2
    assert calls == []
    assert not Path(plan.task_start_path).exists()
    attempt_path = Path(plan.task_attempt_path)
    attempt = orchestration_contracts.load_record(attempt_path, "task-attempt")
    assert attempt["status"] == "failed"
    assert attempt["task_start_record"] is None
    assert attempt["producer"] is None
    for field, path_field in (
        ("stdout_log", "stdout_path"),
        ("stderr_log", "stderr_path"),
    ):
        log_path = Path(getattr(plan, path_field))
        assert attempt[field] == {
            "path": log_path.relative_to(built.run_root).as_posix(),
            "sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
        }
    fasta = Path(str(built.execution["reference"]["fasta"]["path"]))
    assert not Path(f"{fasta}.fai").exists()
    assert not fasta.with_name(f"{fasta.stem}.dict").exists()
    assert not list(parent.glob(".*step00c*"))
    assert not list(parent.glob("*.emrys-stage"))


def test_complete_step00c_sidecar_pair_is_reused_and_content_bound(
    tmp_path: Path,
) -> None:
    built, plan, record, outputs = _step00c_with_existing_sidecars(
        tmp_path / "workflow-fixture"
    )
    before = {
        path: (path.read_bytes(), path.stat().st_dev, path.stat().st_ino)
        for path in outputs
    }
    producer_argv = tuple(record["producer_argv"])
    defaults = _fixed_ops()
    calls: list[tuple[str, ...]] = []

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        calls.append(argv)
        if argv == producer_argv:
            os.write(stdout_descriptor, b"reused existing sidecars\n")
            return task.CommandResult(argv, 0)
        return defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )

    outcome = _execute_task(
        plan,
        ops=replace(defaults, run_command=command),
    )

    assert calls == [tuple(record["validator_argv"])]
    assert b"producer command skipped" in Path(plan.stdout_path).read_bytes()
    verified = _record(outcome.task_attempt_path)
    assert verified["outputs"] == [
        {
            "role": declaration["role"],
            "path": str(path),
            "size_bytes": len(before[path][0]),
            "sha256": hashlib.sha256(before[path][0]).hexdigest(),
        }
        for declaration, path in zip(record["outputs"], outputs, strict=True)
    ]
    for path in outputs:
        assert (path.read_bytes(), path.stat().st_dev, path.stat().st_ino) == before[
            path
        ]


def test_partial_step00c_sidecar_pair_blocks_before_producer(tmp_path: Path) -> None:
    built, plan, record, outputs = _step00c_with_existing_sidecars(
        tmp_path / "workflow-fixture"
    )
    outputs[1].unlink()
    survivor = outputs[0].read_bytes()
    calls: list[tuple[str, ...]] = []
    defaults = _fixed_ops()

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        calls.append(argv)
        return defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )

    with pytest.raises(task.TaskBoundaryError, match="partial pre-existing Step 00c"):
        _execute_task(
            plan,
            ops=replace(defaults, run_command=command),
        )

    assert calls == []
    assert outputs[0].read_bytes() == survivor
    assert not outputs[1].exists()
    attempt = _record(plan.task_attempt_path)
    assert attempt["task_start_record"] is None
    assert attempt["producer"] is None


def test_reused_step00c_sidecar_mutation_during_validation_fails_closed(
    tmp_path: Path,
) -> None:
    built, plan, record, outputs = _step00c_with_existing_sidecars(
        tmp_path / "workflow-fixture"
    )
    producer_argv = tuple(record["producer_argv"])
    defaults = _fixed_ops()

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        if argv == producer_argv:
            return task.CommandResult(argv, 0)
        result = defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )
        with outputs[1].open("ab") as stream:
            stream.write(b"foreign mutation\n")
        return result

    with pytest.raises(task.TaskBoundaryError, match="during validation"):
        _execute_task(
            plan,
            ops=replace(defaults, run_command=command),
        )
    assert not Path(plan.verified_task_path).exists()


def test_reused_step00c_sidecar_rechecked_before_verified_publication(
    tmp_path: Path,
) -> None:
    built, plan, record, outputs = _step00c_with_existing_sidecars(
        tmp_path / "workflow-fixture"
    )
    producer_argv = tuple(record["producer_argv"])
    original = outputs[0].read_bytes()
    defaults = _fixed_ops()

    def command(
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
        stdout_descriptor: int,
        stderr_descriptor: int,
    ) -> task.CommandResult:
        if argv == producer_argv:
            return task.CommandResult(argv, 0)
        return defaults.run_command(
            argv,
            cwd,
            environment,
            stdout_descriptor,
            stderr_descriptor,
        )

    def publish(path: Path, data: bytes) -> None:
        defaults.publish_bytes(path, data)
        if path == Path(plan.task_attempt_path):
            replacement = outputs[0].with_name(f".{outputs[0].name}.late-replacement")
            replacement.write_bytes(original)
            replacement.replace(outputs[0])

    with pytest.raises(task.TaskBoundaryError, match="before verified publication"):
        _execute_task(
            plan,
            ops=replace(
                defaults,
                run_command=command,
                publish_bytes=publish,
            ),
        )
    assert _record(plan.task_attempt_path)["status"] == "succeeded"
    assert not Path(plan.verified_task_path).exists()


@pytest.mark.parametrize("outcome", ("pass", "fail", "changed-output"))
def test_scientific_validation_precedes_native_publication(
    tmp_path: Path, outcome: str
) -> None:
    built = _task_fixture(tmp_path, prepublication=True)
    if outcome == "fail":
        built.definition["validator_argv"].extend(["--status", "fail"])
        _rewrite_task(built)
    defaults = _fixed_ops()
    finals = [Path(item["path"]) for item in built.definition["outputs"]]
    working = Path(built.definition["outputs"][0]["working_path"])

    def command(argv, *arguments):
        if "validator" in argv:
            assert not any(path.exists() for path in finals)
            assert str(working) in argv
            assert str(finals[0]) not in argv
        result = defaults.run_command(argv, *arguments)
        if "validator" in argv and outcome == "changed-output":
            working.write_bytes(b"changed after scientific validation\n")
        return result

    ops = replace(defaults, run_command=command)
    if outcome == "pass":
        _execute_task(built.plan, ops=ops)
        verified = _validate_verified(built)
        assert str(working) in verified["validator"]["argv"]
        assert all(path.is_file() for path in finals)
    else:
        with pytest.raises(task.TaskBoundaryError):
            _execute_task(built.plan, ops=ops)
        assert not any(path.exists() for path in finals)
        assert not Path(built.plan.verified_task_path).exists()
        assert Path(built.definition["validation_report_path"]).is_file()
