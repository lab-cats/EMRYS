"""Internal lifecycle, recovery, and derived-state contracts for B4."""

from __future__ import annotations

import copy
import argparse
import fcntl
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from emrys.libraries.source_authority import PACKAGE_ROOT, admit_installed_package
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.evidence.runtime_availability.inspector import (
    RuntimeBinding,
    RuntimeCheck,
    RuntimeInspection,
    RuntimeObservation,
)
from emrys.evidence.storage_inventory import qualification as storage_qualification
from emrys.libraries.installed_package_identity import installed_package_tree_identity
from emrys.libraries.validation import inputs as validation_inputs
from emrys.orchestration.run_coordinator import (
    _inspection_attempts,
    control,
    doctor,
    inspection,
    lifecycle,
    task,
)
from emrys.orchestration.run_coordinator.execution_profile import (
    project_default_profile_bytes,
)
from tests.orchestration.run_coordinator.fixtures import workflow as workflow_fixture

WORKFLOW_TIME = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)
FINISHED_TIME = datetime(2026, 8, 12, 14, 5, tzinfo=UTC)


def _raise_signal_on_lifecycle_thread(signum: int) -> None:
    """Keep synthetic signals away from xdist's worker-control thread."""

    signal.raise_signal(signum)


def _attempt_record(request: lifecycle.LifecycleRequest) -> dict[str, Any]:
    return json.loads(request.attempt_record_bytes)


def _run_attempt(
    request: lifecycle.LifecycleRequest,
    *,
    ops: lifecycle.LifecycleOps,
) -> lifecycle.LifecycleOutcome:
    return lifecycle.run_materialized_attempt(request, lambda: None, ops=ops)


def test_successor_lifecycle_requires_symbolic_resource_policy() -> None:
    config = {"resource_policy": workflow_fixture._resource_policy()}

    assert lifecycle._resource_plan_from_workflow(config).workflow_cores == 1
    del config["resource_policy"]["symbolic"]
    del config["resource_policy"]["symbolic_sha256"]
    with pytest.raises(lifecycle.LifecycleError, match="resource policy keys"):
        lifecycle._resource_plan_from_workflow(
            config,
        )


@pytest.mark.parametrize(
    ("boundary", "change"),
    (
        ("locked", None),
        ("outer", "omit"),
        ("outer", "repoint"),
        ("locked", "omit"),
        ("locked", "repoint"),
        ("locked", "history"),
    ),
)
def test_resume_preflights_recheck_exact_pending_retry_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str, change: str | None
) -> None:
    from contextlib import nullcontext
    from types import SimpleNamespace

    reference = {
        "path": "attempts/previous/tasks/owner/retry/task-attempt.json",
        "sha256": "a" * 64,
    }
    previous = {
        "workflow_attempt_id": "previous",
        "run_id": "run-fixture",
        "execution_contract_sha256": "b" * 64,
        "profile_sha256": "c" * 64,
        "execution_mode": "local-science-tools",
        "executor": "snakemake",
    }
    attempt = {
        **previous,
        "workflow_attempt_id": "next",
        "supersedes_workflow_attempt_id": "previous",
        "tasks": {
            "owner": {
                "retry": {"retry_task_attempt_record": dict(reference)},
                "unentered": {"retry_task_attempt_record": None},
                "verified": {
                    "workflow_attempt_record": {
                        "path": "attempts/previous/attempt.json",
                        "sha256": "d" * 64,
                    }
                },
            }
        },
    }

    def scope(name, state, retry=None):
        return SimpleNamespace(
            expected=SimpleNamespace(machine_key="owner", scope_id=name),
            state=state,
            retry_task_attempt_record=retry,
        )

    observed = SimpleNamespace(
        recovery_available=True,
        latest_attempt=previous,
        latest_receipt={"status": "interrupted"},
        tasks=(
            scope("retry", "pending", reference),
            scope("unentered", "pending"),
            scope("verified", "verified"),
        ),
    )
    locks, observations = [], []

    def inspect_run(root, *, ops, allowed_next_attempt=None):
        assert root == tmp_path
        observations.append(allowed_next_attempt)
        return observed

    monkeypatch.setattr(inspection, "state_tree_blockers", lambda _root: ())
    monkeypatch.setattr(
        inspection,
        "lock_tree_blockers",
        lambda _root, *, expected_run_lock: locks.append(expected_run_lock) or (),
    )
    monkeypatch.setattr(
        inspection,
        "inspect_attempt_tree",
        lambda _root: ((tmp_path / "attempts/previous",), ()),
    )
    monkeypatch.setattr(inspection, "inspect_run", inspect_run)
    ops = SimpleNamespace(
        host_name=lambda: "fixture",
        process_is_alive=lambda _pid: False,
        validate_reporting_receipt=lambda *_a, **_k: None,
    )

    def mutate():
        changed = {**reference, "sha256": "e" * 64}
        if change == "history":
            observed.tasks[0].retry_task_attempt_record = changed
        else:
            attempt["tasks"]["owner"]["retry"]["retry_task_attempt_record"] = (
                None if change == "omit" else changed
            )

    if boundary == "outer":
        mutate()
    failure = lambda: pytest.raises(
        lifecycle.LifecycleError, match="exact admitted history"
    )
    with failure() if boundary == "outer" else nullcontext():
        lifecycle._operation_preflight("resume", tmp_path, attempt, ops)
    if boundary == "outer":
        assert locks == [False] and observations == [None]
        return
    if change is not None:
        mutate()
    with failure() if change is not None else nullcontext():
        lifecycle._under_lock_attempt_preflight(
            SimpleNamespace(operation="resume"), tmp_path, attempt, ops
        )
    assert locks == [False, True]
    assert observations[0] is None and observations[1] is attempt
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize(
    ("run_suffix", "source_suffix", "allowed"),
    [
        ("same", "same", False),
        ("source/run", "source", False),
        ("run", "run/source", False),
        ("run", "source", True),
    ],
)
def test_run_root_and_source_checkout_must_be_disjoint(
    tmp_path: Path,
    run_suffix: str,
    source_suffix: str,
    allowed: bool,
) -> None:
    run_root = tmp_path / run_suffix
    source_checkout = tmp_path / source_suffix
    if allowed:
        lifecycle._require_disjoint_roots(run_root, source_checkout)
        return
    with pytest.raises(lifecycle.LifecycleError, match="must be disjoint"):
        lifecycle._require_disjoint_roots(run_root, source_checkout)


def test_storage_readmission_uses_normalized_reference_identity(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    authored_fasta = tmp_path / "authored.fa"
    normalized_fasta = tmp_path / "normalized.fa"
    receipt = tmp_path / "storage.qualified.json"
    receipt_bytes = b"qualified storage\n"
    receipt.write_bytes(receipt_bytes)
    calls: list[tuple[Path, Path]] = []

    def inspect_storage(
        observed_workspace: Path,
        observed_reference: Path,
    ) -> storage_qualification.QualifiedStorage:
        calls.append((observed_workspace, observed_reference))
        return storage_qualification.QualifiedStorage(
            receipt_path=receipt,
            receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
            qualification_id="b" * 64,
        )

    binding = lifecycle._readmit_storage_runtime_binding(
        {
            "workspace": str(workspace),
            "authored_paths": {"reference_fasta": str(authored_fasta)},
        },
        {"reference": {"fasta": {"path": str(normalized_fasta)}}},
        inspect_storage=inspect_storage,
        inspect_direct_storage=inspect_storage,
    )

    assert calls == [(workspace, normalized_fasta)]
    assert binding == RuntimeBinding(
        check_id="storage_qualification",
        path=receipt,
        resolved_path=receipt.resolve(strict=True),
        sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        observed="b" * 64,
    )


@pytest.mark.parametrize(
    "receipt_name",
    ("storage.direct-qualified.json", "storage.direct-qualified.1.json"),
)
def test_direct_storage_readmission_uses_the_bound_receipt_class(
    tmp_path: Path,
    receipt_name: str,
) -> None:
    workspace = tmp_path / "workspace"
    reference = tmp_path / "reference.fa"
    receipt = tmp_path / receipt_name
    receipt_bytes = b"direct storage\n"
    receipt.write_bytes(receipt_bytes)
    calls: list[str] = []

    def reject_site(
        _workspace: Path,
        _reference: Path,
    ) -> storage_qualification.QualifiedStorage:
        calls.append("site")
        raise storage_qualification.StorageQualificationError("wrong receipt class")

    def admit_direct(
        observed_workspace: Path,
        observed_reference: Path,
    ) -> storage_qualification.QualifiedStorage:
        assert (observed_workspace, observed_reference) == (workspace, reference)
        calls.append("direct")
        return storage_qualification.QualifiedStorage(
            receipt_path=receipt,
            receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
            qualification_id="d" * 64,
        )

    binding = lifecycle._readmit_storage_runtime_binding(
        {
            "execution_mode": "local-science-tools",
            "workspace": str(workspace),
            "placement": {"kind": "direct"},
            "required_tools": (
                {"name": "storage_qualification", "path": str(receipt)},
            ),
        },
        {"reference": {"fasta": {"path": str(reference)}}},
        inspect_storage=reject_site,
        inspect_direct_storage=admit_direct,
    )

    assert calls == ["direct"]
    assert binding is not None and binding.path == receipt


def test_slurm_storage_readmission_never_accepts_direct_evidence(
    tmp_path: Path,
) -> None:
    direct_receipt = tmp_path / "storage.direct-qualified.json"

    def reject_site(
        _workspace: Path,
        _reference: Path,
    ) -> storage_qualification.QualifiedStorage:
        raise storage_qualification.StorageQualificationError(
            "site evidence is required"
        )

    with pytest.raises(lifecycle.LifecycleError, match="site evidence is required"):
        lifecycle._readmit_storage_runtime_binding(
            {
                "execution_mode": "local-science-tools",
                "workspace": str(tmp_path / "workspace"),
                "placement": {"kind": "slurm"},
                "required_tools": (
                    {
                        "name": "storage_qualification",
                        "path": str(direct_receipt),
                    },
                ),
            },
            {"reference": {"fasta": {"path": str(tmp_path / "reference.fa")}}},
            inspect_storage=reject_site,
            inspect_direct_storage=lambda *_args: pytest.fail(
                "Slurm admitted direct-only storage evidence"
            ),
        )


@pytest.mark.parametrize("relative_reference", (False, True))
def test_successor_storage_readmission_resolves_authored_reference_from_request(
    tmp_path: Path,
    relative_reference: bool,
) -> None:
    workspace = tmp_path / "workspace"
    request = tmp_path / "intake" / "request.yaml"
    reference = request.parent / "reference" / "genome.fa"
    calls: list[tuple[Path, Path]] = []

    def inspect_storage(
        observed_workspace: Path,
        observed_reference: Path,
    ) -> storage_qualification.QualifiedStorage:
        calls.append((observed_workspace, observed_reference))
        raise storage_qualification.StorageQualificationError("stop after capture")

    with pytest.raises(lifecycle.LifecycleError, match="stop after capture"):
        lifecycle._readmit_storage_runtime_binding(
            {
                "execution_mode": "local-science-tools",
                "workspace": str(workspace),
                "authored_paths": {
                    "request": str(request),
                    "reference_fasta": (
                        "reference/genome.fa" if relative_reference else str(reference)
                    ),
                },
            },
            {"schema_version": "emrys.run-binding.v1"},
            inspect_storage=inspect_storage,
            inspect_direct_storage=inspect_storage,
        )

    assert calls == [(workspace, reference)]


def test_storage_readmission_failure_is_a_lifecycle_error(tmp_path: Path) -> None:
    def reject_storage(
        _workspace: Path,
        _reference: Path,
    ) -> storage_qualification.QualifiedStorage:
        raise storage_qualification.StorageQualificationError("fixture drift")

    with pytest.raises(
        lifecycle.LifecycleError,
        match="Could not re-admit storage qualification: fixture drift",
    ):
        lifecycle._readmit_storage_runtime_binding(
            {
                "execution_mode": "local-science-tools",
                "workspace": str(tmp_path / "workspace"),
            },
            {"reference": {"fasta": {"path": str(tmp_path / "reference.fa")}}},
            inspect_storage=reject_storage,
            inspect_direct_storage=reject_storage,
        )


def test_default_lifecycle_ops_bind_semantic_storage_admission() -> None:
    admission = lifecycle.default_lifecycle_ops().admit_storage_context

    assert isinstance(admission, partial)
    assert admission.func is lifecycle._readmit_storage_runtime_binding
    assert (
        admission.keywords["inspect_storage"]
        is storage_qualification.admit_final_qualification
    )
    assert (
        admission.keywords["inspect_direct_storage"]
        is storage_qualification.admit_direct_qualification
    )


@dataclass(slots=True)
class ValidatedFixtureReceipt:
    receipt_path: Path
    receipt_sha256: str

    @property
    def verified_report_locations(self) -> tuple[tuple[str, Path], ...]:
        if not self.receipt_path.name.endswith(".report_outputs.tsv"):
            return ()
        run_id = self.receipt_path.parent.name
        return (
            (
                "scientific-report-html",
                self.receipt_path.with_name(f"{run_id}.scientific_report.html"),
            ),
            (
                "evidence-report-html",
                self.receipt_path.with_name(f"{run_id}.evidence_report.html"),
            ),
        )


@dataclass(slots=True)
class Harness:
    built: workflow_fixture.WorkflowFixture
    request: lifecycle.LifecycleRequest
    events: list[str]
    result: lifecycle.WorkflowResult
    materialize_complete: bool = False
    mutate_verified: bool = False
    storage_admissions: int = 0
    fail_first_storage_admission: bool = False
    fail_second_storage_admission: bool = False
    runtime_admissions: int = 0
    fail_second_runtime_admission: bool = False
    mutate_request_on_first_admission: bool = False
    inject_attempt_entry_after_lock: bool = False
    materialize_start_only: bool = False
    materialize_preentry_failure: bool = False
    preentry_stdout: bytes = b"fixture preentry stdout\n"
    preentry_stderr: bytes = b"fixture preentry stderr\n"
    inspect_live_transient: bool = False
    inject_state_entry_after_child: bool = False
    inject_lock_entry_on_release: bool = False
    fail_attempt_directory_sync: bool = False
    live_observation: inspection.RunInspection | None = None
    publications: int = 0

    def ops(self) -> lifecycle.LifecycleOps:
        return lifecycle.LifecycleOps(
            run_workflow=self.run_workflow,
            publish_bytes=self.publish,
            release_lock=self.release,
            promote_receipt=self.promote_receipt,
            now=lambda: FINISHED_TIME,
            host_name=lambda: "fixture-host",
            process_id=lambda: 4242,
            process_is_alive=lambda _pid: True,
            validate_reporting_receipt=self.validate_reporting,
            admit_storage_context=self.admit_storage,
            admit_runtime_context=self.admit_runtime,
            sync_directory=self.sync_directory,
        )

    def inspection_ops(
        self, *, host="fixture-host", process_is_alive=lambda _pid: True
    ):
        return inspection.InspectionOps(
            lambda: host, process_is_alive, self.validate_reporting
        )

    def inspect(self, **observations):
        return inspection.inspect_run(
            self.built.run_root, ops=self.inspection_ops(**observations)
        )

    def sync_directory(self, path: Path, label: str) -> None:
        self.events.append(f"sync:{path.relative_to(self.built.run_root)}")
        if (
            self.fail_attempt_directory_sync
            and label == "new workflow-attempt directory"
        ):
            raise lifecycle.LifecycleError("fixture attempt-directory sync failure")
        lifecycle._sync_real_directory(path, label)

    def admit_storage(
        self,
        _attempt: dict[str, Any],
        _execution: dict[str, Any],
    ) -> None:
        self.storage_admissions += 1
        self.events.append("storage-admitted")
        if self.fail_first_storage_admission and self.storage_admissions == 1:
            raise lifecycle.LifecycleError(
                "Could not re-admit storage qualification: initial fixture drift"
            )
        if self.fail_second_storage_admission and self.storage_admissions == 2:
            raise lifecycle.LifecycleError(
                "Could not re-admit storage qualification: post-child fixture drift"
            )
        return None

    def admit_runtime(
        self,
        _attempt: dict[str, Any],
        _request: lifecycle.LifecycleRequest,
        _storage_binding: RuntimeBinding | None,
        _initial_inspection: RuntimeInspection | None,
    ) -> None:
        self.runtime_admissions += 1
        self.events.append("runtime-admitted")
        if self.mutate_request_on_first_admission and self.runtime_admissions == 1:
            self.request.request_source_path.write_text(
                "mutated after initial admission\n", encoding="utf-8"
            )
        if self.fail_second_runtime_admission and self.runtime_admissions == 2:
            raise lifecycle.LifecycleError("runtime context mutated after child")

    def publish(self, path: Path, data: bytes) -> None:
        self.events.append(f"publish:{path.relative_to(self.built.run_root)}")
        self.publications += 1
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        descriptor = os.open(path, flags, 0o600)
        try:
            os.write(descriptor, data)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if self.inject_attempt_entry_after_lock and path == (
            self.built.run_root / "locks" / "run.lock"
        ):
            (self.built.run_root / "attempts" / "foreign").mkdir()

    def release(
        self,
        path: Path,
        evidence_path: Path,
        expected: bytes,
        inode: tuple[int, int],
        retain_source: bool = False,
    ) -> None:
        self.events.append("release")
        lifecycle._release_owned_lock(
            path, evidence_path, expected, inode, retain_source
        )
        if self.inject_lock_entry_on_release:
            (path.parent / "foreign.lock").write_bytes(b"late foreign lock\n")

    def promote_receipt(
        self,
        prepared_path: Path,
        receipt_path: Path,
        expected: bytes,
        inode: tuple[int, int],
        retain_source: bool = False,
    ) -> None:
        self.events.append("promote-receipt")
        lifecycle._promote_prepared_receipt(
            prepared_path,
            receipt_path,
            expected,
            inode,
            retain_source,
        )

    def validate_reporting(
        self,
        name: str,
        path: Path,
        _identity: Any,
        **_keywords: Any,
    ) -> ValidatedFixtureReceipt:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record != {"kind": name, "run_id": self.built.execution["run_id"]}:
            raise ValueError("reporting receipt has wrong semantic identity")
        return ValidatedFixtureReceipt(
            receipt_path=path,
            receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    def run_workflow(
        self, argv: tuple[str, ...], _cwd: Path
    ) -> lifecycle.WorkflowResult:
        self.events.append("workflow")
        attempt = _attempt_record(self.request)
        assert list(argv) == attempt["snakemake_argv"]
        attempt_path = (
            self.built.run_root
            / "attempts"
            / str(attempt["workflow_attempt_id"])
            / "attempt.json"
        )
        if self.materialize_preentry_failure:
            _materialize_preentry_failure(
                self.built,
                attempt_path,
                stdout_data=self.preentry_stdout,
                stderr_data=self.preentry_stderr,
            )
        if self.materialize_start_only or self.inspect_live_transient:
            _materialize_start_only(self.built, attempt_path)
        if self.inspect_live_transient:
            self.live_observation = self.inspect()
        if self.materialize_complete:
            _materialize_verified(
                self.built,
                attempt_path,
            )
        if self.mutate_verified:
            marker = next(self.built.verified_root.glob("*/*.json"))
            marker_record = orchestration_contracts.load_record(marker, "verified-task")
            record = orchestration_contracts.load_record(
                self.built.run_root / marker_record["task_attempt_record"]["path"],
                "task-attempt",
            )
            Path(record["outputs"][0]["path"]).write_bytes(b"foreign mutation\n")
        if self.inject_state_entry_after_child:
            (self.built.run_root / "state" / "foreign").mkdir()
        return self.result


def _record_reference(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def test_transaction_signal_controller_forwards_only_first_signal_once() -> None:
    sent: list[tuple[int, int]] = []
    controller: lifecycle.TransactionSignalController

    def send(process_group_id: int, signum: int) -> None:
        sent.append((process_group_id, signum))
        controller.record(signal.SIGTERM)

    process_ops = lifecycle.ProcessGroupOps(signal_group=send)
    controller = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        process_ops,
    )

    controller.register_process_group(9001)
    controller.record(signal.SIGINT)

    assert controller.first_signal == signal.SIGINT
    assert sent == [(9001, signal.SIGINT)]


def test_process_group_ambiguity_escalates_and_fails_closed() -> None:
    class Process:
        pid = 9002

    ticks = iter((0.0, 0.0, 1.0, 1.0, 2.0, 2.0))
    sent: list[int] = []
    controller = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        lifecycle.DEFAULT_PROCESS_GROUP_OPS,
    )
    ops = lifecycle.ProcessGroupOps(
        spawn=lambda _argv, _cwd, _env: Process(),
        poll=lambda _process: 0,
        group_exists=lambda _pgid: True,
        signal_group=lambda _pgid, signum: sent.append(signum),
        monotonic=lambda: next(ticks),
        sleep=lambda _seconds: None,
        terminate_grace_seconds=0.0,
        kill_grace_seconds=0.0,
    )

    with pytest.raises(lifecycle.ProcessGroupAmbiguity, match="proved quiescent"):
        lifecycle._run_process_group(("fixture",), Path("/"), controller, ops=ops)

    assert sent == [signal.SIGTERM, signal.SIGKILL]


@pytest.mark.parametrize("stopped_by", (signal.SIGTERM, signal.SIGKILL))
def test_process_group_poll_failure_still_forces_quiescence(stopped_by: int) -> None:
    class Process:
        pid = 9003

    alive = True
    poll_calls = 0
    sent: list[int] = []

    def poll(_process: Process) -> int:
        nonlocal poll_calls
        poll_calls += 1
        if poll_calls == 1:
            raise OSError("poll failed")
        return 0

    def send(_pgid: int, signum: int) -> None:
        nonlocal alive
        sent.append(signum)
        if signum == stopped_by:
            alive = False

    controller = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        lifecycle.DEFAULT_PROCESS_GROUP_OPS,
    )
    ops = lifecycle.ProcessGroupOps(
        spawn=lambda _argv, _cwd, _env: Process(),
        poll=poll,
        group_exists=lambda _pgid: alive,
        signal_group=send,
        monotonic=lambda: 0.0,
        sleep=lambda _seconds: None,
        terminate_grace_seconds=0.0,
    )

    failure = (
        OSError if stopped_by == signal.SIGTERM else lifecycle.ProcessGroupAmbiguity
    )
    message = "poll failed" if stopped_by == signal.SIGTERM else "quiescent"
    with pytest.raises(failure, match=message):
        lifecycle._run_process_group(("fixture",), Path("/"), controller, ops=ops)

    assert sent == (
        [signal.SIGTERM]
        if stopped_by == signal.SIGTERM
        else [signal.SIGTERM, signal.SIGKILL]
    )


@pytest.mark.parametrize(
    "failure_point",
    ["poll", "probe", "signal", "sleep", "base_exception"],
)
def test_process_group_quiescence_effect_failure_is_typed_ambiguity(
    failure_point: str,
) -> None:
    class Process:
        pid = 9005

    controller = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        lifecycle.DEFAULT_PROCESS_GROUP_OPS,
    )

    def fail(label: str) -> None:
        if failure_point == "base_exception" and label == "probe":
            raise KeyboardInterrupt("fixture group probe interruption")
        if failure_point == label:
            raise OSError(f"fixture group {label} failure")

    def group_exists(_pgid: int) -> bool:
        fail("probe")
        return True

    def poll(_process: Process) -> int:
        fail("poll")
        return 0

    def send(_pgid: int, _signum: int) -> None:
        fail("signal")

    def sleep(_seconds: float) -> None:
        fail("sleep")

    ops = lifecycle.ProcessGroupOps(
        spawn=lambda _argv, _cwd, _env: Process(),
        poll=poll,
        group_exists=group_exists,
        signal_group=send,
        monotonic=lambda: 0.0,
        sleep=sleep,
    )

    with pytest.raises(
        lifecycle.ProcessGroupAmbiguity,
        match="quiesc",
    ) as observed:
        lifecycle._run_process_group(("fixture",), Path("/"), controller, ops=ops)
    if failure_point == "base_exception":
        assert isinstance(observed.value.__cause__, KeyboardInterrupt)


def test_post_spawn_poll_failure_reaps_real_leader_before_propagating(
    tmp_path: Path,
) -> None:
    processes: list[subprocess.Popen[bytes]] = []
    poll_calls = 0

    def spawn(
        argv: tuple[str, ...], cwd: Path, environment: dict[str, str]
    ) -> subprocess.Popen[bytes]:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=environment,
            start_new_session=True,
        )
        processes.append(process)
        return process

    def poll(process: subprocess.Popen[bytes]) -> int | None:
        nonlocal poll_calls
        poll_calls += 1
        if poll_calls == 1:
            raise OSError("fixture post-spawn poll failure")
        return process.poll()

    controller = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        lifecycle.DEFAULT_PROCESS_GROUP_OPS,
    )
    ops = lifecycle.ProcessGroupOps(
        spawn=spawn,
        poll=poll,
        terminate_grace_seconds=0.5,
        kill_grace_seconds=0.5,
    )

    with pytest.raises(OSError, match="post-spawn poll failure"):
        try:
            lifecycle._run_process_group(
                (sys.executable, "-c", "import time; time.sleep(60)"),
                tmp_path,
                controller,
                ops=ops,
            )
        finally:
            for process in processes:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=1)

    assert len(processes) == 1
    process = processes[0]
    assert process.returncode is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(process.pid, 0)


def test_process_group_ambiguity_retains_public_lock_without_receipt(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)

    class Process:
        pid = 9006

    process_ops = lifecycle.ProcessGroupOps(
        spawn=lambda _argv, _cwd, _env: Process(),
        poll=lambda _process: 0,
        group_exists=lambda _pgid: True,
        signal_group=lambda _pgid, _signum: (_ for _ in ()).throw(
            OSError("fixture group signal failure")
        ),
    )
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])

    with pytest.raises(lifecycle.ProcessGroupAmbiguity):
        _run_attempt(
            built.request,
            ops=replace(
                built.ops(),
                run_workflow=None,
                process_group_ops=process_ops,
            ),
        )

    attempt_root = built.built.run_root / "attempts" / identifier
    assert (built.built.run_root / "locks/run.lock").is_file()
    assert (attempt_root / "attempt.json").is_file()
    assert not (attempt_root / "released-run-lock.json").exists()
    assert not (attempt_root / "attempt-receipt.json").exists()


def _nested_native_cancellation_child(root: Path, grace: str) -> None:
    """Exercise lifecycle -> Task wrapper -> separate native session, without Snakemake."""
    built = _build_harness(root / "lifecycle")
    native_root = root / "task"
    native_record = native_root / "native.json"
    process: subprocess.Popen[bytes] | None = None
    interrupted = False
    deadline = time.monotonic() + 20
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
    prior_handlers = {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    }

    def spawn(
        _argv: tuple[str, ...], _cwd: Path, environment: Mapping[str, str]
    ) -> subprocess.Popen[bytes]:
        nonlocal process
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; import sys; "
                "from tests.orchestration.run_coordinator.test_task import "
                "_task_native_signal_child; "
                "_task_native_signal_child(Path(sys.argv[1]), 'nested')",
                str(native_root),
            ],
            cwd=Path(__file__).resolve().parents[3],
            env=environment,
            start_new_session=True,
        )
        return process

    def poll(child: subprocess.Popen[bytes]) -> int | None:
        nonlocal interrupted
        assert time.monotonic() < deadline, "native fixture did not terminate in time"
        if not interrupted and native_record.exists():
            interrupted = True
            if grace == "external-kill":
                os.killpg(child.pid, signal.SIGKILL)
            else:
                os.kill(os.getpid(), signal.SIGTERM)
        return child.poll()

    process_ops = replace(lifecycle.WORKFLOW_PROCESS_GROUP_OPS, spawn=spawn, poll=poll)
    if grace == "forced":
        process_ops = replace(process_ops, terminate_grace_seconds=0.05)
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    attempt_root = built.built.run_root / "attempts" / identifier
    try:
        if grace != "default":
            with pytest.raises(
                lifecycle.ProcessGroupAmbiguity, match="separately owned native groups"
            ):
                _run_attempt(
                    built.request,
                    ops=replace(
                        built.ops(), run_workflow=None, process_group_ops=process_ops
                    ),
                )
            assert (built.built.run_root / "locks/run.lock").is_file()
            assert (attempt_root / "attempt.json").is_file()
            assert not (attempt_root / "attempt-receipt.json").exists()
            assert not (attempt_root / "released-run-lock.json").exists()
            assert not (native_root / "native-cleanup.json").exists()
            os.kill(int(json.loads(native_record.read_text())["pid"]), 0)
        else:
            outcome = _run_attempt(
                built.request,
                ops=replace(
                    built.ops(), run_workflow=None, process_group_ops=process_ops
                ),
            )
            assert outcome.receipt["status"] == "interrupted"
            assert outcome.receipt["termination_signal"] == signal.SIGTERM
            assert (
                outcome.receipt_path.is_file() and outcome.released_lock_path.is_file()
            )
            assert not outcome.lock_path.exists()
            assert (native_root / "native-cleanup.json").is_file()
        assert process is not None and process.returncode == (
            -signal.SIGKILL if grace != "default" else 0
        )
        with pytest.raises(ProcessLookupError):
            os.killpg(process.pid, 0)
        assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == prior_mask
        assert {
            signum: signal.getsignal(signum) for signum in prior_handlers
        } == prior_handlers
    finally:
        if process is not None and process.poll() is None:
            lifecycle._signal_process_group(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        if native_record.is_file():
            lifecycle._signal_process_group(
                int(json.loads(native_record.read_text())["pid"]), signal.SIGKILL
            )


@pytest.mark.parametrize("grace", ("default", "forced", "external-kill"))
def test_nested_native_cancellation_requires_wrapper_cleanup_proof(
    tmp_path: Path, grace: str
) -> None:
    try:
        completed = workflow_fixture.run_child(
            _nested_native_cancellation_child, tmp_path, grace, timeout=40
        )
        assert completed.returncode == 0, (completed.stdout, completed.stderr)
    finally:
        native_record = tmp_path / "task/native.json"
        if native_record.is_file():
            lifecycle._signal_process_group(
                int(json.loads(native_record.read_text())["pid"]), signal.SIGKILL
            )


def test_signal_forwarding_failure_is_nonraising_then_fails_closed() -> None:
    controller: lifecycle.TransactionSignalController
    sent: list[int] = []

    def fail(_pgid: int, signum: int) -> None:
        sent.append(signum)
        raise PermissionError("fixture forwarding denial")

    controller = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        lifecycle.ProcessGroupOps(signal_group=fail),
    )
    controller.register_process_group(9004)

    controller.record(signal.SIGTERM)

    assert sent == [signal.SIGTERM]
    with pytest.raises(lifecycle.ProcessGroupAmbiguity, match="Could not forward"):
        controller.raise_forwarding_error()


@pytest.mark.parametrize("phase", ["before_mutex", "after_mutex", "before_run_lock"])
def test_signal_before_run_lock_aborts_without_attempt_evidence(
    tmp_path: Path,
    phase: str,
) -> None:
    built = _build_harness(tmp_path)
    previous = {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    }

    def interrupt(observed: str) -> None:
        if observed == phase:
            os.kill(os.getpid(), signal.SIGTERM)

    with pytest.raises(lifecycle.LifecycleError, match="interrupted"):
        _run_attempt(
            built.request,
            ops=replace(built.ops(), observe_phase=interrupt),
        )

    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    assert not (built.built.run_root / "locks/run.lock").exists()
    assert not (built.built.run_root / "attempts" / identifier).exists()
    assert not list((built.built.run_root / "locks").glob("released-*.json"))
    assert {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    } == previous


def test_signal_after_run_lock_retains_aggregate_recovery_evidence(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)

    def interrupt(phase: str) -> None:
        if phase == "after_run_lock":
            os.kill(os.getpid(), signal.SIGINT)

    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    with pytest.raises(lifecycle.LifecycleError, match="after run-lock"):
        _run_attempt(
            built.request,
            ops=replace(built.ops(), observe_phase=interrupt),
        )

    assert not (built.built.run_root / "locks/run.lock").exists()
    assert (
        built.built.run_root / "locks" / f"released-{identifier}-run-lock.json"
    ).is_file()
    assert not (built.built.run_root / "attempts" / identifier).exists()


@pytest.mark.parametrize(
    "phase",
    [
        "after_attempt_publication",
        "after_workflow",
        "before_lock_release",
        "before_receipt_publication",
    ],
)
def test_signal_after_attempt_terminalizes_interrupted_receipt(
    tmp_path: Path,
    phase: str,
) -> None:
    built = _build_harness(tmp_path)

    def interrupt(observed: str) -> None:
        if observed == phase:
            os.kill(os.getpid(), signal.SIGTERM)

    outcome = _run_attempt(
        built.request,
        ops=replace(built.ops(), observe_phase=interrupt),
    )

    assert outcome.receipt["status"] == "interrupted"
    assert outcome.receipt["termination_signal"] == signal.SIGTERM
    assert outcome.receipt_path.is_file()
    assert outcome.released_lock_path.is_file()
    assert not outcome.lock_path.exists()


def test_signal_during_receipt_commit_reaches_ambient_handler_after_commit(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()
    ambient_observations: list[bool] = []
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    receipt_path = (
        built.built.run_root / "attempts" / identifier / "attempt-receipt.json"
    )
    prepared_path = receipt_path.with_name("prepared-attempt-receipt.json")
    prior = signal.getsignal(signal.SIGTERM)

    def ambient(_signum: int, _frame: object) -> None:
        ambient_observations.append(receipt_path.is_file())

    def publish(path: Path, data: bytes) -> None:
        if path == prepared_path:
            _raise_signal_on_lifecycle_thread(signal.SIGTERM)
        defaults.publish_bytes(path, data)

    signal.signal(signal.SIGTERM, ambient)
    try:
        outcome = _run_attempt(
            built.request,
            ops=replace(defaults, publish_bytes=publish),
        )
    finally:
        signal.signal(signal.SIGTERM, prior)

    assert outcome.receipt["status"] == "failed"
    assert ambient_observations == [True]
    assert receipt_path.is_file()
    assert not prepared_path.exists()


@pytest.mark.parametrize("mutex_phase", ["before_release", "after_release"])
def test_signal_during_mutex_cleanup_is_delivered_after_unlock(
    tmp_path: Path,
    mutex_phase: str,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    receipt_path = (
        built.built.run_root / "attempts" / identifier / "attempt-receipt.json"
    )
    mutex_path = built.built.run_root / "locks/acquire.mutex"
    observations: list[tuple[bool, bool]] = []
    prior_handler = signal.getsignal(signal.SIGTERM)
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())

    def ambient(_signum: int, _frame: object) -> None:
        descriptor = os.open(mutex_path, os.O_RDWR | os.O_NOFOLLOW)
        lock_available = False
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_available = True
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
        observations.append((receipt_path.is_file(), lock_available))

    def observe(event: str, _path: Path) -> None:
        if event == mutex_phase:
            _raise_signal_on_lifecycle_thread(signal.SIGTERM)

    signal.signal(signal.SIGTERM, ambient)
    try:
        outcome = _run_attempt(
            built.request,
            ops=replace(defaults, observe_mutex=observe),
        )
    finally:
        signal.signal(signal.SIGTERM, prior_handler)

    assert outcome.receipt_path.is_file()
    assert observations == [(True, True)]
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == prior_mask


def test_signal_and_failure_during_receipt_commit_restore_controller_state(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    receipt_path = (
        built.built.run_root / "attempts" / identifier / "attempt-receipt.json"
    )
    prepared_path = receipt_path.with_name("prepared-attempt-receipt.json")
    prior_handlers = {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    }
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())

    def fail_promotion(
        _prepared: Path,
        _receipt: Path,
        _expected: bytes,
        _inode: tuple[int, int],
        _retain_source: bool,
    ) -> None:
        os.kill(os.getpid(), signal.SIGINT)
        raise OSError("fixture receipt promotion failure")

    with pytest.raises(
        lifecycle.LifecycleError,
        match="Could not materialize immutable workflow attempt",
    ) as observed:
        _run_attempt(
            built.request,
            ops=replace(defaults, promote_receipt=fail_promotion),
        )

    assert isinstance(observed.value.__cause__, OSError)
    assert "receipt promotion failure" in str(observed.value.__cause__)
    assert not receipt_path.exists()
    assert prepared_path.is_file()
    assert (
        built.built.run_root / "attempts" / identifier / "released-run-lock.json"
    ).is_file()
    assert {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    } == prior_handlers
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == prior_mask


def test_prepared_receipt_publication_failure_retains_active_lock(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    attempt_root = built.built.run_root / "attempts" / identifier
    prepared_path = attempt_root / "prepared-attempt-receipt.json"

    def fail_preparation(path: Path, data: bytes) -> None:
        if path == prepared_path:
            raise OSError("fixture prepared receipt publication failure")
        defaults.publish_bytes(path, data)

    with pytest.raises(
        lifecycle.LifecycleError,
        match="Could not materialize immutable workflow attempt",
    ):
        _run_attempt(
            built.request,
            ops=replace(defaults, publish_bytes=fail_preparation),
        )

    assert (built.built.run_root / "locks/run.lock").is_file()
    assert not prepared_path.exists()
    assert not (attempt_root / "released-run-lock.json").exists()
    assert not (attempt_root / "attempt-receipt.json").exists()


def test_lock_release_failure_retains_prepared_receipt_and_active_lock(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    attempt_root = built.built.run_root / "attempts" / identifier

    def fail_release(
        _path: Path,
        _evidence_path: Path,
        _expected: bytes,
        _inode: tuple[int, int],
        _retain_source: bool,
    ) -> None:
        raise lifecycle.LifecycleError("fixture lock release failure")

    with pytest.raises(lifecycle.LifecycleError, match="lock release failure"):
        _run_attempt(
            built.request,
            ops=replace(defaults, release_lock=fail_release),
        )

    assert (built.built.run_root / "locks/run.lock").is_file()
    assert (attempt_root / "prepared-attempt-receipt.json").is_file()
    assert not (attempt_root / "released-run-lock.json").exists()
    assert not (attempt_root / "attempt-receipt.json").exists()


def test_preblocked_ordinary_signal_is_refused_without_run_evidence(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    try:
        with pytest.raises(lifecycle.LifecycleError, match="ambient mask"):
            _run_attempt(built.request, ops=built.ops())
        assert not (built.built.run_root / "locks/run.lock").exists()
        assert not list((built.built.run_root / "attempts").iterdir())
        assert signal.SIGTERM in signal.pthread_sigmask(signal.SIG_BLOCK, set())
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)


def test_process_group_leader_exit_still_quiesces_grandchild(tmp_path: Path) -> None:
    pid_file = tmp_path / "grandchild.pid"
    launcher = tmp_path / "launcher.py"
    launcher.write_text(
        "import os, pathlib, subprocess, sys\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "pathlib.Path(sys.argv[1]).write_text(f'{os.getpgrp()} {child.pid}')\n",
        encoding="utf-8",
    )
    signals = lifecycle.TransactionSignalController(
        lifecycle.DEFAULT_SIGNAL_OPS,
        lifecycle.DEFAULT_PROCESS_GROUP_OPS,
    )

    result = lifecycle._run_process_group(
        (sys.executable, str(launcher), str(pid_file)),
        tmp_path,
        signals,
        ops=lifecycle.ProcessGroupOps(
            terminate_grace_seconds=0.2,
            kill_grace_seconds=0.5,
        ),
    )

    assert result == lifecycle.WorkflowResult(0, None, None)
    process_group_id, grandchild_pid = (
        int(value) for value in pid_file.read_text(encoding="utf-8").split()
    )
    try:
        with pytest.raises(ProcessLookupError):
            os.killpg(process_group_id, 0)
    finally:
        try:
            os.kill(grandchild_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _bound(role: str, path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "role": role,
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _first_task_context(
    built: workflow_fixture.WorkflowFixture,
    attempt_path: Path,
) -> tuple[inspection.ExpectedTask, task.TaskPlan]:
    expected = inspection.expected_tasks(
        inspection.admit_successor_run(built.run_root), built.profile
    )[0]
    plan = task.load_task(
        attempt_path,
        expected_sha256=hashlib.sha256(attempt_path.read_bytes()).hexdigest(),
        machine_key=expected.machine_key,
        scope_id=expected.scope_id,
    )
    return expected, plan


def _task_identity(built, expected, plan) -> dict[str, Any]:
    return {
        "run_id": built.execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(
            (built.run_root / "contract" / "run.json").read_bytes()
        ).hexdigest(),
        "profile_sha256": hashlib.sha256(
            (built.run_root / "contract" / "profile.json").read_bytes()
        ).hexdigest(),
        "workflow_attempt_id": plan.attempt_record["workflow_attempt_id"],
        "task_attempt_id": plan.task_attempt_id,
        "machine_key": expected.machine_key,
        "scope": expected.scope,
        "owner_run_token": plan.owner_run_token,
    }


def _task_start_record(built, plan, identity) -> dict[str, Any]:
    return {
        "schema_version": "emrys.task-start.v3",
        **identity,
        "workflow_attempt_record": _record_reference(plan.path, built.run_root),
        "run_lock": inspection.admit_attempt_run_lock(
            built.run_root, plan.attempt_record, require_active=True
        ),
        "created_at": "2026-08-12T12:01:00Z",
        "inputs": [
            _bound("workflow_attempt", plan.path),
            _bound("execution_contract", plan.execution_path),
            _bound("workflow_profile", plan.profile_path),
            *(_bound(item.role, item.path) for item in plan.inputs),
        ],
    }


def _task_terminal_record(built, plan, identity, **changes) -> dict[str, Any]:
    return {
        "schema_version": "emrys.task-attempt.v4",
        "abort_closure": None,
        **identity,
        "task_start_record": None,
        "status": "failed",
        "started_at": "2026-08-12T12:01:00Z",
        "finished_at": "2026-08-12T12:01:01Z",
        "producer": None,
        "validator": None,
        "semantic_all_pass": None,
        "stable_inputs_rechecked": False,
        "validation_report": None,
        "stdout_log": _record_reference(plan.stdout_path, built.run_root),
        "stderr_log": _record_reference(plan.stderr_path, built.run_root),
        "failure_message": "fixture preentry admission failure",
        "inputs": [],
        "outputs": [],
        **changes,
    }


def _materialize_start_only(
    built: workflow_fixture.WorkflowFixture,
    attempt_path: Path,
) -> Path:
    expected, plan = _first_task_context(built, attempt_path)
    start_path = plan.task_start_path
    start_path.parent.mkdir(parents=True, exist_ok=True)
    task_root = plan.task_attempt_path.parent
    task_root.mkdir(parents=True, exist_ok=True)
    start = _task_start_record(built, plan, _task_identity(built, expected, plan))
    orchestration_contracts.validate_record("task-start", start)
    start_path.write_bytes(orchestration_contracts.canonical_json_bytes(start))
    return start_path


def _materialize_preentry_failure(
    built: workflow_fixture.WorkflowFixture,
    attempt_path: Path,
    *,
    stdout_data: bytes,
    stderr_data: bytes,
) -> Path:
    expected, plan = _first_task_context(built, attempt_path)
    task_attempt_path = plan.task_attempt_path
    task_attempt_path.parent.mkdir(parents=True, exist_ok=True)
    stdout = plan.stdout_path
    stderr = plan.stderr_path
    stdout.write_bytes(stdout_data)
    stderr.write_bytes(stderr_data)
    record = _task_terminal_record(built, plan, _task_identity(built, expected, plan))
    orchestration_contracts.validate_record("task-attempt", record)
    task_attempt_path.write_bytes(orchestration_contracts.canonical_json_bytes(record))
    return task_attempt_path


def _materialize_verified(
    built: workflow_fixture.WorkflowFixture,
    attempt_path: Path,
    *,
    skip: tuple[str, str] | None = None,
) -> None:
    execution_hash = hashlib.sha256(
        (built.run_root / "contract" / "run.json").read_bytes()
    ).hexdigest()
    profile_hash = orchestration_contracts.canonical_sha256(built.profile)
    owners = {str(item["machine_key"]): item for item in built.profile["owner_tasks"]}
    workflow_attempt = orchestration_contracts.load_record(
        attempt_path, "workflow-attempt"
    )
    attempt_reference = _record_reference(attempt_path, built.run_root)
    for expected in inspection.expected_tasks(
        inspection.admit_successor_run(built.run_root), built.profile
    ):
        machine = expected.machine_key
        scope_id = expected.scope_id
        if (machine, scope_id) == skip:
            continue
        marker = built.verified_root / machine / f"{scope_id}.json"
        if marker.is_file() and not marker.is_symlink():
            continue
        owner = owners[machine]
        plan = task.task_from_attempt(
            attempt_path,
            workflow_attempt,
            expected_sha256=attempt_reference["sha256"],
            machine_key=machine,
            scope_id=scope_id,
        )
        identity = _task_identity(built, expected, plan)
        identity.update(
            execution_contract_sha256=execution_hash, profile_sha256=profile_hash
        )
        task_root = plan.task_attempt_path.parent
        task_root.mkdir(parents=True, exist_ok=True)
        artifact_root = (
            built.run_root / "products" / "lifecycle-task-double" / machine / scope_id
        )
        artifact_root.mkdir(parents=True, exist_ok=True)
        input_path = artifact_root / "input.txt"
        report_path = plan.validation_report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(f"input {machine} {scope_id}\n", encoding="utf-8")
        for output in plan.outputs:
            output_path = output.path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(f"output {machine} {scope_id}\n", encoding="utf-8")
        report_path.write_text(
            "step_id\tscope_id\tcheck_id\tstatus\tobserved\texpected\tdetail\n"
            f"{owner['step_id']}\t{scope_id}\tlifecycle_fixture\tpass\tpass\tpass\tfixture\n",
            encoding="utf-8",
        )
        task_start_path = plan.task_start_path
        task_start_path.parent.mkdir(parents=True, exist_ok=True)
        start = _task_start_record(built, plan, identity)
        orchestration_contracts.validate_record("task-start", start)
        start_bytes = orchestration_contracts.canonical_json_bytes(start)
        if task_start_path.exists() or task_start_path.is_symlink():
            assert task_start_path.read_bytes() == start_bytes
        else:
            task_start_path.write_bytes(start_bytes)
        task_start_reference = _record_reference(task_start_path, built.run_root)
        task_attempt_path = task_root / "task-attempt.json"
        (task_root / "stdout.log").write_bytes(b"fixture owner stdout\n")
        (task_root / "stderr.log").write_bytes(b"fixture owner stderr\n")
        report_reference = _record_reference(report_path, built.run_root)
        task_attempt = _task_terminal_record(
            built,
            plan,
            identity,
            task_start_record=task_start_reference,
            status="succeeded",
            finished_at="2026-08-12T12:02:00Z",
            producer={"argv": list(plan.backend.producer_argv), "exit_code": 0},
            validator={"argv": list(plan.backend.validator_argv), "exit_code": 0},
            semantic_all_pass={
                "argv": list(task._semantic_argv(plan, str(owner["step_id"]))),
                "exit_code": 0,
            },
            stable_inputs_rechecked=True,
            validation_report=report_reference,
            failure_message=None,
            inputs=start["inputs"],
            outputs=[_bound(output.role, output.path) for output in plan.outputs],
        )
        orchestration_contracts.validate_record("task-attempt", task_attempt)
        task_attempt_path.write_bytes(
            orchestration_contracts.canonical_json_bytes(task_attempt)
        )
        verified = {
            "schema_version": "emrys.verified-task.v2",
            "task_attempt_record": _record_reference(task_attempt_path, built.run_root),
        }
        orchestration_contracts.validate_record("verified-task", verified)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(orchestration_contracts.canonical_json_bytes(verified))


def _attempt_tasks(
    built: workflow_fixture.WorkflowFixture,
) -> dict[str, dict[str, Any]]:
    tasks = json.loads(built.attempt_record_bytes)["tasks"]
    for machine, by_scope in tasks.items():
        for scope_id in by_scope:
            verified = built.verified_root / machine / f"{scope_id}.json"
            if verified.is_file() and not verified.is_symlink():
                marker = orchestration_contracts.load_record(verified, "verified-task")
                terminal = orchestration_contracts.load_record(
                    built.run_root / marker["task_attempt_record"]["path"],
                    "task-attempt",
                )
                start = orchestration_contracts.load_record(
                    built.run_root / terminal["task_start_record"]["path"],
                    "task-start",
                )
                by_scope[scope_id] = {
                    "workflow_attempt_record": start["workflow_attempt_record"]
                }
    return tasks


def _attempt(
    built: workflow_fixture.WorkflowFixture,
    *,
    operation: lifecycle.Operation,
    identifier: str,
    supersedes: str | None,
    argv: tuple[str, ...],
) -> dict[str, Any]:
    return workflow_fixture.attempt_record(
        built.run_root,
        identifier,
        (built.root / "intake/project.yaml").resolve(),
        operation=operation,
        supersedes_workflow_attempt_id=supersedes,
        snakemake_argv=list(argv),
        request_label="fixture lifecycle",
        workflow=json.loads(built.attempt_record_bytes)["workflow"],
        tasks=_attempt_tasks(built),
        host="fixture-host",
        process_id=4242,
        owner_token=f"owner-{identifier[-8:]}",
    )


def _build_harness(
    tmp_path: Path,
    *,
    operation: lifecycle.Operation = "execute",
    supersedes: str | None = None,
    identifier: str | None = None,
    result: lifecycle.WorkflowResult | None = None,
) -> Harness:
    built = workflow_fixture.build(
        tmp_path / "workspace" / "fixture", materialize_attempt=False
    )
    (built.run_root / "attempts").mkdir(exist_ok=True)
    (built.run_root / "locks").mkdir(exist_ok=True)
    workflow_id = identifier or "workflow-20260812T140000Z-" + "d" * 32
    manifest = built.run_root / "attempts" / workflow_id / "attempt.json"
    argv = lifecycle.build_snakemake_argv(
        python_executable=Path(sys.executable),
        snakefile=workflow_fixture.SNAKEFILE.resolve(),
        workflow_profile=workflow_fixture.WORKFLOW_PROFILE.resolve(),
        configfile=manifest,
        run_root=built.run_root,
        target="cohort_slice",
        operation=operation,
        cores=1,
        resource_limits=workflow_fixture._resource_limits(),
    )
    attempt = _attempt(
        built,
        operation=operation,
        identifier=workflow_id,
        supersedes=supersedes,
        argv=argv,
    )
    request = lifecycle.LifecycleRequest(
        run_root=built.run_root,
        execution_path=built.run_root / "contract" / "run.json",
        profile_path=built.run_root / "contract" / "profile.json",
        snakefile=workflow_fixture.SNAKEFILE.resolve(),
        python_executable=Path(sys.executable),
        workflow_profile=workflow_fixture.WORKFLOW_PROFILE.resolve(),
        target="cohort_slice",
        operation=operation,
        attempt_record_bytes=orchestration_contracts.canonical_json_bytes(attempt),
        request_source_path=(built.root / "intake" / "project.yaml").resolve(),
    )
    return Harness(
        built=built,
        request=request,
        events=[],
        result=result or lifecycle.WorkflowResult(0, None),
    )


def _resume_request(
    harness: Harness,
    *,
    identifier: str,
    supersedes: str,
) -> tuple[lifecycle.LifecycleRequest, dict[str, Any]]:
    manifest = harness.built.run_root / "attempts" / identifier / "attempt.json"
    argv = lifecycle.build_snakemake_argv(
        python_executable=harness.request.python_executable,
        snakefile=harness.request.snakefile,
        workflow_profile=harness.request.workflow_profile,
        configfile=manifest,
        run_root=harness.built.run_root,
        target=harness.request.target,
        operation="resume",
        cores=1,
        resource_limits=workflow_fixture._resource_limits(),
    )
    attempt = _attempt(
        harness.built,
        operation="resume",
        identifier=identifier,
        supersedes=supersedes,
        argv=argv,
    )
    return (
        replace(
            harness.request,
            operation="resume",
            attempt_record_bytes=orchestration_contracts.canonical_json_bytes(attempt),
        ),
        attempt,
    )


def test_success_publishes_receipt_last_and_inspection_ignores_engine_metadata(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = _run_attempt(built.request, ops=built.ops())

    assert outcome.receipt["status"] == "succeeded"
    assert outcome.receipt["schema_version"] == "emrys.attempt-receipt.v3"
    assert "reporting_completion_records" not in outcome.receipt
    assert "local_pipeline_complete" not in outcome.receipt
    expected_task_count = len(
        inspection.expected_tasks(
            inspection.admit_successor_run(built.built.run_root), built.built.profile
        )
    )
    assert len(outcome.receipt["verified_tasks"]) == expected_task_count
    assert not outcome.lock_path.exists()
    assert outcome.attempt_path.with_name("released-run-lock.json").is_file()
    snapshot = outcome.attempt_path.with_name("request.yaml")
    assert snapshot.read_bytes() == built.request.request_source_path.read_bytes()
    assert built.events.index(
        f"publish:{snapshot.relative_to(built.built.run_root)}"
    ) < built.events.index(
        f"publish:{outcome.attempt_path.relative_to(built.built.run_root)}"
    )
    prepared_path = outcome.attempt_path.with_name("prepared-attempt-receipt.json")
    assert not prepared_path.exists()
    assert (
        outcome.receipt_path.read_bytes()
        == orchestration_contracts.canonical_json_bytes(outcome.receipt)
    )
    assert built.events[-4:] == [
        f"publish:{prepared_path.relative_to(built.built.run_root)}",
        f"sync:{prepared_path.parent.relative_to(built.built.run_root)}",
        "release",
        "promote-receipt",
    ]
    runtime_admissions = [
        index for index, event in enumerate(built.events) if event == "runtime-admitted"
    ]
    assert len(runtime_admissions) == 2
    storage_admissions = [
        index for index, event in enumerate(built.events) if event == "storage-admitted"
    ]
    assert len(storage_admissions) == 2
    workflow_index = built.events.index("workflow")
    assert runtime_admissions[0] < workflow_index < runtime_admissions[1]
    assert storage_admissions[0] < workflow_index < storage_admissions[1]
    (built.built.run_root / ".snakemake").mkdir()
    (built.built.run_root / ".snakemake" / "foreign").write_text("junk\n")
    observed = built.inspect()
    assert observed.integrity == "valid", observed.blockers
    assert observed.attempt_outcome == "succeeded"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "incomplete"
    assert {
        control._inspection_presentation.task_observation(item)
        for item in observed.tasks
    } == {"Verified complete"}


def test_application_event_observer_exceptions_cannot_alter_receipt(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    observed_events = []

    def reject_event(event_name: str) -> None:
        observed_events.append(event_name)
        raise RuntimeError("injected diagnostic observer failure")

    outcome = _run_attempt(
        built.request,
        ops=replace(built.ops(), observe_application_event=reject_event),
    )

    assert observed_events == ["analysis_started", "publication_ready"]
    assert outcome.receipt["status"] == "succeeded"
    assert outcome.receipt_path.is_file()
    assert json.loads(outcome.receipt_path.read_bytes()) == outcome.receipt
    prepared_path = outcome.attempt_path.with_name("prepared-attempt-receipt.json")
    assert built.events[-4:] == [
        f"publish:{prepared_path.relative_to(built.built.run_root)}",
        f"sync:{prepared_path.parent.relative_to(built.built.run_root)}",
        "release",
        "promote-receipt",
    ]


def _prepared_finalization_case(tmp_path: Path) -> tuple[Harness, Path, Path, Path]:
    built = _build_harness(tmp_path)
    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "failed"
    prepared = outcome.receipt_path.with_name("prepared-attempt-receipt.json")
    released = outcome.receipt_path.with_name("released-run-lock.json")
    return built, outcome.receipt_path, prepared, released


@pytest.mark.parametrize(
    ("shape", "lock_shape", "receipt_shape"),
    (
        ("active", "active", "prepared"),
        ("active-released", "active-released-alias", "prepared"),
        ("fully-staged", "active-released-alias", "prepared-final-alias"),
        ("final-alias", "released", "prepared-final-alias"),
    ),
)
def test_prepared_finalization_completes_supported_inode_transitions(
    tmp_path: Path,
    shape: str,
    lock_shape: str,
    receipt_shape: str,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    active = built.built.run_root / "locks/run.lock"
    if shape in {"fully-staged", "final-alias"}:
        os.link(receipt, prepared)
        if shape == "fully-staged":
            os.link(released, active)
    else:
        receipt.rename(prepared)
        if shape == "active":
            released.rename(active)
        else:
            os.link(released, active)

    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in built.built.run_root.rglob("*")
        if path.is_file()
    }
    preview = inspection.inspect_prepared_finalization(built.built.run_root)
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in built.built.run_root.rglob("*")
        if path.is_file()
    } == before
    assert preview.candidate.lock_shape == lock_shape
    assert preview.candidate.receipt_shape == receipt_shape
    assert preview.prospective_state.recovery_available
    if shape == "active":
        active_state = built.inspect()
        assert active_state.lock_observation == "local live owner"
        assert active_state.attempt_outcome != "running"

    finalized = lifecycle.finalize_prepared_attempt(
        built.built.run_root, preview.candidate, ops=built.ops()
    )
    assert finalized.recovery_available
    assert finalized.latest_receipt == preview.candidate.record
    assert receipt.is_file() and released.is_file()
    assert not prepared.exists() and not active.exists()


@pytest.mark.parametrize("collision", ("lock-copy", "receipt-copy"))
def test_prepared_finalization_rejects_copied_equal_bytes(
    tmp_path: Path,
    collision: str,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    if collision == "lock-copy":
        receipt.rename(prepared)
        shutil.copyfile(released, built.built.run_root / "locks/run.lock")
    else:
        shutil.copyfile(receipt, prepared)

    observed = inspection.inspect_run(built.built.run_root)
    assert observed.prepared_finalization is None
    with pytest.raises(inspection.InspectionError, match="no admissible prepared"):
        inspection.inspect_prepared_finalization(built.built.run_root)


@pytest.mark.parametrize("replaced_name", ("receipt", "lock"))
def test_prepared_finalization_rejects_distinct_inode_equal_bytes_after_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replaced_name: str,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    receipt.rename(prepared)
    active = built.built.run_root / "locks/run.lock"
    released.rename(active)
    target = prepared if replaced_name == "receipt" else active
    read = validation_inputs.read_bytes_with_identity
    replaced = []

    def replace_after_read(path, label, **kwargs):
        data, identity = read(path, label, **kwargs)
        if path == target and not replaced:
            replacement = path.with_name(f"{path.name}.replacement")
            replacement.write_bytes(data)
            replacement.replace(path)
            replacement_state = target.stat()
            assert (replacement_state.st_dev, replacement_state.st_ino) != (
                identity.st_dev,
                identity.st_ino,
            )
            replaced.append(path)
        return data, identity

    monkeypatch.setattr(
        validation_inputs, "read_bytes_with_identity", replace_after_read
    )
    with pytest.raises(inspection.InspectionError, match="changed during preview"):
        inspection.inspect_prepared_finalization(built.built.run_root)
    assert replaced == [target]


def test_released_lock_without_prepared_receipt_remains_ineligible(
    tmp_path: Path,
) -> None:
    built, receipt, _prepared, _released = _prepared_finalization_case(tmp_path)
    receipt.unlink()
    observed = inspection.inspect_run(built.built.run_root)
    assert observed.prepared_finalization is None
    assert not observed.recovery_available
    assert any(
        "without a prepared or final terminal receipt" in blocker
        for blocker in observed.blockers
    )


def test_prepared_finalization_accepts_exact_concurrent_completion(
    tmp_path: Path,
) -> None:
    built, receipt, prepared, _released = _prepared_finalization_case(tmp_path)
    os.link(receipt, prepared)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)
    lifecycle._promote_prepared_receipt(
        prepared,
        receipt,
        receipt_bytes := orchestration_contracts.canonical_json_bytes(
            preview.candidate.record
        ),
        preview.candidate.prepared_inode,
    )
    assert receipt.read_bytes() == receipt_bytes

    finalized = lifecycle.finalize_prepared_attempt(
        built.built.run_root, preview.candidate, ops=built.ops()
    )
    assert finalized.latest_receipt == preview.candidate.record
    assert finalized.recovery_available


def test_prepared_finalization_concurrent_completion_does_not_consume_signal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built, receipt, prepared, _released = _prepared_finalization_case(tmp_path)
    os.link(receipt, prepared)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)
    lifecycle._promote_prepared_receipt(
        prepared,
        receipt,
        orchestration_contracts.canonical_json_bytes(preview.candidate.record),
        preview.candidate.prepared_inode,
    )
    inspect_prepared = inspection.inspect_prepared_finalization

    def interrupt_then_inspect(*args, **kwargs):
        _raise_signal_on_lifecycle_thread(signal.SIGTERM)
        return inspect_prepared(*args, **kwargs)

    monkeypatch.setattr(
        inspection, "inspect_prepared_finalization", interrupt_then_inspect
    )
    ambient = []
    prior_handler = signal.getsignal(signal.SIGTERM)
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
    signal.signal(signal.SIGTERM, lambda signum, _frame: ambient.append(signum))
    try:
        with pytest.raises(lifecycle.LifecycleError, match="interrupted before commit"):
            lifecycle.finalize_prepared_attempt(
                built.built.run_root, preview.candidate, ops=built.ops()
            )
    finally:
        signal.signal(signal.SIGTERM, prior_handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)

    assert ambient == []
    assert inspection.inspect_run(built.built.run_root).recovery_available


def test_prepared_finalization_refuses_signal_recorded_during_reinspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    active = built.built.run_root / "locks/run.lock"
    receipt.rename(prepared)
    released.rename(active)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in built.built.run_root.rglob("*")
        if path.is_file()
    }
    ambient = []
    prior_handler = signal.getsignal(signal.SIGTERM)
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
    inspect_prepared = inspection.inspect_prepared_finalization

    def inspect_then_interrupt(*args, **kwargs):
        admitted = inspect_prepared(*args, **kwargs)
        _raise_signal_on_lifecycle_thread(signal.SIGTERM)
        return admitted

    monkeypatch.setattr(
        inspection, "inspect_prepared_finalization", inspect_then_interrupt
    )
    signal.signal(signal.SIGTERM, lambda signum, _frame: ambient.append(signum))
    try:
        with pytest.raises(lifecycle.LifecycleError, match="interrupted before commit"):
            lifecycle.finalize_prepared_attempt(
                built.built.run_root, preview.candidate, ops=built.ops()
            )
        assert signal.getsignal(signal.SIGTERM) is not prior_handler
        assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == prior_mask
    finally:
        signal.signal(signal.SIGTERM, prior_handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)

    assert ambient == []
    assert prepared.is_file() and active.is_file()
    assert not receipt.exists() and not released.exists()
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in built.built.run_root.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    "mutation", ("unexpected-child", "deleted-task", "changed-task")
)
def test_prepared_finalization_refuses_retained_evidence_drift_after_preview(
    tmp_path: Path,
    mutation: str,
) -> None:
    built = _build_harness(tmp_path, result=lifecycle.WorkflowResult(7, None))
    built.materialize_preentry_failure = True
    outcome = _run_attempt(built.request, ops=built.ops())
    attempt_root = outcome.receipt_path.parent
    prepared = attempt_root / "prepared-attempt-receipt.json"
    active = built.built.run_root / "locks/run.lock"
    outcome.receipt_path.rename(prepared)
    outcome.released_lock_path.rename(active)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)

    if mutation == "unexpected-child":
        (attempt_root / "unexpected").write_bytes(b"late child\n")
    else:
        reference = preview.candidate.record["task_attempt_records"][0]["record"]
        retained = built.built.run_root / reference["path"]
        if mutation == "deleted-task":
            retained.unlink()
        else:
            retained.write_bytes(b"{}\n")

    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.finalize_prepared_attempt(
            built.built.run_root, preview.candidate, ops=built.ops()
        )
    assert prepared.is_file() and active.is_file()
    assert not outcome.receipt_path.exists()
    assert not outcome.released_lock_path.exists()


def test_prepared_finalization_failure_retains_retryable_staged_aliases(
    tmp_path: Path,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    active = built.built.run_root / "locks/run.lock"
    receipt.rename(prepared)
    released.rename(active)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)
    defaults = built.ops()
    failures = []

    def fail_once(*args, **kwargs):
        failures.append((args, kwargs))
        raise OSError("fixture prepared finalization failure")

    with pytest.raises(OSError, match="prepared finalization failure"):
        lifecycle.finalize_prepared_attempt(
            built.built.run_root,
            preview.candidate,
            ops=replace(defaults, promote_receipt=fail_once),
        )
    assert len(failures) == 1
    assert prepared.is_file() and active.is_file() and released.is_file()
    assert not receipt.exists()
    assert len(tuple((built.built.run_root / "attempts").iterdir())) == 1

    finalized = lifecycle.finalize_prepared_attempt(
        built.built.run_root, preview.candidate, ops=defaults
    )
    assert finalized.recovery_available
    assert receipt.is_file() and released.is_file()
    assert not prepared.exists() and not active.exists()


def test_prepared_finalization_revalidates_evidence_after_alias_staging(
    tmp_path: Path,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    active = built.built.run_root / "locks/run.lock"
    receipt.rename(prepared)
    released.rename(active)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)
    unexpected = prepared.parent / "unexpected"

    def inject_drift(phase: str) -> None:
        if phase == "before_receipt_promotion":
            unexpected.write_bytes(b"late child\n")

    with pytest.raises(inspection.InspectionError, match="changed during preview"):
        lifecycle.finalize_prepared_attempt(
            built.built.run_root,
            preview.candidate,
            ops=replace(built.ops(), observe_phase=inject_drift),
        )
    assert prepared.is_file() and receipt.is_file()
    assert active.is_file() and released.is_file()
    assert prepared.stat().st_ino == receipt.stat().st_ino
    assert active.stat().st_ino == released.stat().st_ino

    unexpected.unlink()
    finalized = lifecycle.finalize_prepared_attempt(
        built.built.run_root, preview.candidate, ops=built.ops()
    )
    assert finalized.recovery_available
    assert receipt.is_file() and released.is_file()
    assert not prepared.exists() and not active.exists()


def test_prepared_finalization_rejects_receipt_promoter_inode_substitution(
    tmp_path: Path,
) -> None:
    built, receipt, prepared, released = _prepared_finalization_case(tmp_path)
    active = built.built.run_root / "locks/run.lock"
    receipt.rename(prepared)
    released.rename(active)
    preview = inspection.inspect_prepared_finalization(built.built.run_root)

    def substitute_receipt(
        source: Path,
        destination: Path,
        expected: bytes,
        _inode: tuple[int, int],
        _retain_source: bool,
    ) -> None:
        destination.write_bytes(expected)
        source.unlink()

    with pytest.raises(inspection.InspectionError):
        lifecycle.finalize_prepared_attempt(
            built.built.run_root,
            preview.candidate,
            ops=replace(built.ops(), promote_receipt=substitute_receipt),
        )
    assert receipt.is_file() and active.is_file() and released.is_file()
    assert not prepared.exists()
    observed = inspection.inspect_run(built.built.run_root)
    assert not observed.recovery_available
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.finalize_prepared_attempt(
            built.built.run_root, preview.candidate, ops=built.ops()
        )


@pytest.mark.parametrize("execute", (False, True), ids=("preview", "execute"))
@pytest.mark.parametrize("outcome", ("succeeded", "blocked"))
def test_public_resume_finalization_only_outcomes_create_no_attempt(
    tmp_path: Path,
    capsys,
    execute: bool,
    outcome: str,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = outcome == "succeeded"
    built.inject_state_entry_after_child = outcome == "blocked"
    attempt_root = (
        built.built.run_root
        / "attempts"
        / str(_attempt_record(built.request)["workflow_attempt_id"])
    )
    receipt = attempt_root / "attempt-receipt.json"
    prepared = attempt_root / "prepared-attempt-receipt.json"
    if outcome == "blocked":
        with pytest.raises(
            lifecycle.LifecycleError, match="prepared receipt was retained"
        ):
            _run_attempt(built.request, ops=built.ops())
    else:
        terminal = _run_attempt(built.request, ops=built.ops())
        terminal.receipt_path.rename(prepared)
        terminal.released_lock_path.rename(built.built.run_root / "locks/run.lock")
    record = json.loads(prepared.read_bytes())
    assert record["status"] == outcome
    receipt_before = receipt.exists()
    attempt_count = len(tuple((built.built.run_root / "attempts").iterdir()))
    project = built.built.root / "project.yaml"
    shutil.copy2(built.built.root / "intake/project.yaml", project)
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in built.built.root.rglob("*")
        if path.is_file()
    }

    result = control.resume_from_args(
        argparse.Namespace(
            project=project,
            run=built.built.run_root.name,
            profile=str(tmp_path / "must-not-be-read.yaml"),
            execute=execute,
        )
    )
    assert result == (2 if execute and outcome == "blocked" else 0)
    rendered = capsys.readouterr().err
    assert inspection.human_run_name(built.built.run_root.name) in rendered
    assert str(built.built.run_root) in rendered
    assert record["workflow_attempt_id"] in rendered
    assert len(tuple((built.built.run_root / "attempts").iterdir())) == attempt_count
    if execute:
        assert receipt.is_file() and not prepared.exists()
        if outcome == "blocked":
            assert "continuation remains unavailable" in rendered
    else:
        assert "Dry-run complete; no resume state was written." in rendered
        assert prepared.is_file() and receipt.exists() is receipt_before
        assert {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in built.built.root.rglob("*")
            if path.is_file()
        } == before


@pytest.mark.parametrize("delegate_context", ("none", "mismatched", "incomplete"))
def test_public_slurm_profile_finalization_only_logs_without_submission_or_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    delegate_context: str,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    terminal = _run_attempt(built.request, ops=built.ops())
    prepared = terminal.receipt_path.with_name("prepared-attempt-receipt.json")
    original_receipt = terminal.receipt_path.read_bytes()
    terminal.receipt_path.rename(prepared)
    terminal.released_lock_path.rename(built.built.run_root / "locks/run.lock")
    project = built.built.root / "project.yaml"
    shutil.copy2(built.built.root / "intake/project.yaml", project)
    profile = tmp_path / "slurm.yaml"
    profile.write_bytes(project_default_profile_bytes("viking"))
    log_root = tmp_path / "application-logs"
    attempts_before = tuple((built.built.run_root / "attempts").iterdir())
    real_finalize = control.lifecycle.finalize_prepared_attempt
    finalizations = []

    def finalize_with_open_log(*args, **kwargs):
        (log_path,) = log_root.rglob("*.jsonl")
        assert [
            json.loads(line)["event"] for line in log_path.read_text().splitlines()
        ] == ["attempt_opened"]
        finalizations.append(True)
        return real_finalize(*args, **kwargs)

    monkeypatch.setattr(
        control.lifecycle, "finalize_prepared_attempt", finalize_with_open_log
    )
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda *_args, **_kwargs: pytest.fail("finalization submitted a job"),
    )
    scheduler = control.slurm_submission
    for name in (
        scheduler.DELEGATE_MARKER_ENV,
        scheduler.PROFILE_SHA256_ENV,
        scheduler.SUBMIT_UID_ENV,
        scheduler.REQUEST_TOKEN_ENV,
        "SLURM_JOB_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    if delegate_context != "none":
        monkeypatch.setenv(scheduler.DELEGATE_MARKER_ENV, scheduler.DELEGATE_MARKER)
        if delegate_context == "mismatched":
            monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, "f" * 64)
            monkeypatch.setenv(scheduler.SUBMIT_UID_ENV, str(os.getuid()))
            monkeypatch.setenv("SLURM_JOB_ID", "812345")

    result = control.resume_from_args(
        argparse.Namespace(
            project=project,
            run=built.built.run_root.name,
            profile=str(profile),
            execute=True,
            log_root=log_root,
        )
    )
    assert result == (0 if delegate_context == "none" else 2)
    assert tuple((built.built.run_root / "attempts").iterdir()) == attempts_before
    assert not (built.built.root / "logs").exists()
    if delegate_context != "none":
        assert prepared.read_bytes() == original_receipt
        assert not terminal.receipt_path.exists()
        assert finalizations == []
        if delegate_context == "incomplete":
            assert not log_root.exists()
        else:
            (log_path,) = log_root.rglob("*.jsonl")
            assert [
                json.loads(line)["event"] for line in log_path.read_text().splitlines()
            ] == [
                "attempt_opened",
                "attempt_failed",
            ]
        return
    assert terminal.receipt_path.read_bytes() == original_receipt
    assert not prepared.exists()
    assert finalizations == [True]
    (log_path,) = log_root.rglob("*.jsonl")
    assert [
        json.loads(line)["event"] for line in log_path.read_text().splitlines()
    ] == [
        "attempt_opened",
        "resume_finalization_completed",
    ]


def test_workflow_argv_binds_reviewed_absolute_source_files(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    argv = list(_attempt_record(built.request)["snakemake_argv"])
    assert argv[:6] == [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "snakemake",
    ]
    assert argv[argv.index("--snakefile") + 1] == str(workflow_fixture.SNAKEFILE)
    assert argv[argv.index("--workflow-profile") + 1] == str(
        workflow_fixture.WORKFLOW_PROFILE
    )

    injected = built.built.run_root / "profiles" / "local" / "profile.v9+.yaml"
    injected.parent.mkdir(parents=True)
    injected.write_text("forceall: true\n", encoding="utf-8")
    assert str(injected) not in argv


def test_foreign_python_runtime_is_rejected_before_attempt_publication(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    foreign = Path("/usr/bin/python3")
    request = replace(built.request, python_executable=foreign)
    with pytest.raises(lifecycle.LifecycleError, match="lexical sys.executable"):
        _run_attempt(request, ops=built.ops())
    assert built.events == ["publish:locks/run.lock", "release"]
    assert not list((built.built.run_root / "attempts").iterdir())


def test_required_tool_same_path_and_version_rejects_byte_mutation(
    tmp_path: Path,
) -> None:
    tool = tmp_path / "tool"
    tool.write_bytes(b"first executable bytes\n")
    tool.chmod(0o755)
    identity = {
        "name": "r_collaborator_tool",
        "version": "2.7.11b",
        "path": str(tool),
        "resolved_path": str(tool),
        "sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
        "identity_kind": "file",
    }

    lifecycle._admit_required_tool_identity(identity)
    tool.write_bytes(b"different executable bytes\n")

    with pytest.raises(lifecycle.LifecycleError, match="byte digest differs"):
        lifecycle._admit_required_tool_identity(identity)


def test_cached_runtime_probe_rechecks_executable_permission(tmp_path: Path) -> None:
    tool = tmp_path / "STAR"
    tool.write_bytes(b"tool bytes\n")
    tool.chmod(0o755)
    check = RuntimeCheck(
        check_id="star",
        check_type="tool_version",
        target=str(tool),
        probe_args=("--version",),
        expected=".*",
    )
    cached = RuntimeInspection(
        profile_path=tmp_path / "runtime.tsv",
        profile_sha256="a" * 64,
        profile_bytes=b"runtime\n",
        observations=(
            RuntimeObservation(
                check=check,
                status="pass",
                observed="1.0",
                detail="qualified",
                resolved_path=tool,
            ),
        ),
    )
    lifecycle._admit_runtime_executable_permissions(cached)
    tool.chmod(0o644)

    with pytest.raises(lifecycle.LifecycleError, match="no longer executable"):
        lifecycle._admit_runtime_executable_permissions(cached)


def test_explicit_package_tree_mutation_before_workflow_retains_ambiguous_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "renv-library" / "VariantAnnotation"
    database = package / "R" / "VariantAnnotation.rdb"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"package-db-v1\n")
    (package / "DESCRIPTION").write_text(
        "Package: VariantAnnotation\nVersion: 1.0.0\n",
        encoding="utf-8",
    )
    package_identity = installed_package_tree_identity(package)
    runtime_identities = workflow_fixture._attempt_runtime_identities

    def bound_identities(root: Path):
        normalizer, tools = runtime_identities(root)
        tools.append(
            {
                "name": "collaborator_assets",
                "version": "1.0.0",
                "path": str(package),
                "resolved_path": str(package),
                "sha256": package_identity.sha256,
                "identity_kind": "package_tree",
            }
        )
        return normalizer, sorted(tools, key=lambda item: item["name"])

    monkeypatch.setattr(
        workflow_fixture, "_attempt_runtime_identities", bound_identities
    )
    built = _build_harness(tmp_path)

    def mutate(phase: str) -> None:
        if phase == "before_workflow":
            database.write_bytes(b"package-db-v2\n")

    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    with pytest.raises(
        lifecycle.LifecycleError,
        match="runner failed without a terminal child observation",
    ) as observed:
        _run_attempt(
            built.request,
            ops=replace(built.ops(), observe_phase=mutate),
        )

    assert isinstance(observed.value.__cause__, lifecycle.LifecycleError)
    assert "package tree digest differs" in str(observed.value.__cause__)
    attempt_root = built.built.run_root / "attempts" / identifier
    assert "workflow" not in built.events
    assert (built.built.run_root / "locks/run.lock").is_file()
    assert (attempt_root / "attempt.json").is_file()
    assert not (attempt_root / "released-run-lock.json").exists()
    assert not (attempt_root / "attempt-receipt.json").exists()


def test_alternate_checkout_snakefile_is_rejected_before_attempt_publication(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    alternate = PACKAGE_ROOT / "workflow" / "README.md"
    request = replace(built.request, snakefile=alternate)
    with pytest.raises(lifecycle.LifecycleError, match="reviewed workflow/Snakefile"):
        _run_attempt(request, ops=built.ops())
    assert built.events == ["publish:locks/run.lock", "release"]
    assert not list((built.built.run_root / "attempts").iterdir())


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (lifecycle.WorkflowResult(23, None), "failed"),
        (lifecycle.WorkflowResult(None, 15), "interrupted"),
    ],
)
def test_clean_failure_and_interruption_are_resume_available(
    tmp_path: Path,
    result: lifecycle.WorkflowResult,
    expected: str,
) -> None:
    built = _build_harness(tmp_path, result=result)
    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == expected
    observed = built.inspect()
    assert observed.attempt_outcome == expected
    assert observed.lock_observation == "no lock"
    assert observed.results_status == "incomplete"
    assert observed.reporting_status == "incomplete"
    assert observed.recovery_available

    outcome.lock_path.write_bytes(
        outcome.attempt_path.with_name("released-run-lock.json").read_bytes()
    )
    retained = built.inspect()
    assert retained.lock_observation == "invalid or ambiguous lock"
    assert retained.integrity == "blocked"
    assert "Terminal workflow attempt retained its run lock" in retained.blockers
    assert not retained.recovery_available


def test_complete_results_do_not_replace_latest_scientific_attempt_outcome() -> None:
    assert (
        inspection._attempt_outcome(
            latest={"workflow_attempt_id": "latest"},
            receipt={"schema_version": "emrys.attempt-receipt.v3", "status": "failed"},
            running=False,
            integrity_blockers=(),
            results_status="complete",
        )
        == "failed"
    )


def test_rederived_results_blocker_does_not_block_run_integrity_by_wording(
    tmp_path: Path,
) -> None:
    built = workflow_fixture.build(tmp_path)
    state = inspection.RunInspection(
        authority=inspection.admit_successor_run(built.run_root),
        run_root=Path("/run"),
        run_id=f"run-{'a' * 64}",
        attempt_outcome="blocked",
        latest_attempt={"workflow_attempt_id": "latest"},
        latest_receipt={
            "schema_version": "emrys.attempt-receipt.v3",
            "status": "blocked",
            "blockers": ["Could not admit task-start record"],
        },
        tasks=(),
        reporting_completion_records={},
        integrity_blockers=(),
        results_blockers=("Could not close task-start",),
        reporting_blockers=(),
    )

    assert state.integrity == "valid"
    assert state.results_status == "blocked"
    assert state.receipt_blockers == ("Could not admit task-start record",)


def test_reporting_residue_does_not_gate_failed_science_recovery(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path,
        result=lifecycle.WorkflowResult(23, None, "scientific failure"),
    )
    residue = built.built.run_root / "state" / "reporting" / "foreign"
    residue.mkdir(parents=True)

    outcome = _run_attempt(built.request, ops=built.ops())
    observed = built.inspect()

    assert outcome.receipt["status"] == "failed"
    assert outcome.receipt["blockers"] == []
    assert observed.reporting_status == "blocked"
    assert observed.recovery_available


def test_complete_results_survive_failed_scientific_receipt(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "late failure")
    )
    built.materialize_complete = True
    outcome = _run_attempt(built.request, ops=built.ops())
    observed = built.inspect()

    assert outcome.receipt["status"] == "failed"
    assert observed.attempt_outcome == "failed"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "incomplete"
    assert not observed.recovery_available
    assert observed.verified_report_locations == ()


def test_resume_creates_attempt_with_content_bound_rerun_policy(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "preentry failure")
    )
    built.materialize_preentry_failure = True
    first_outcome = _run_attempt(built.request, ops=built.ops())
    first_id = str(_attempt_record(built.request)["workflow_attempt_id"])

    built.request, second_attempt = _resume_request(
        built,
        identifier="workflow-20260812T140500Z-" + "e" * 32,
        supersedes=first_id,
    )
    built.events = []
    built.result = lifecycle.WorkflowResult(0, None)
    built.materialize_preentry_failure = False
    built.materialize_complete = True
    second_outcome = _run_attempt(built.request, ops=built.ops())

    assert first_outcome.receipt["status"] == "failed"
    assert second_outcome.receipt["status"] == "succeeded"
    position = second_attempt["snakemake_argv"].index("--rerun-triggers")
    assert second_attempt["snakemake_argv"][position + 1] == "input"
    assert second_attempt["snakemake_argv"].count("--ignore-incomplete") == 1


def test_verified_mutation_blocks(tmp_path: Path) -> None:
    mutation = _build_harness(tmp_path / "mutation")
    mutation.materialize_complete = True
    mutation.mutate_verified = True
    outcome = _run_attempt(mutation.request, ops=mutation.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any("content binding" in item for item in outcome.receipt["blockers"])
    observed = mutation.inspect()
    assert "Verification not admitted" in {
        control._inspection_presentation.task_observation(item)
        for item in observed.tasks
    }
    assert observed.results_status == "blocked" and not observed.recovery_available


@pytest.mark.parametrize("recorded_status", ("failed", "succeeded"))
@pytest.mark.parametrize("malformed_start", (False, True))
def test_terminal_task_observation_does_not_admit_unverified_results(
    tmp_path: Path,
    recorded_status: str,
    malformed_start: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    built = _build_harness(tmp_path, result=lifecycle.WorkflowResult(9, None))
    built.materialize_complete = True
    plans = []

    def without_verification(
        argv: tuple[str, ...], cwd: Path
    ) -> lifecycle.WorkflowResult:
        result = built.run_workflow(argv, cwd)
        attempt_id = str(_attempt_record(built.request)["workflow_attempt_id"])
        attempt_path = built.built.run_root / "attempts" / attempt_id / "attempt.json"
        _expected, plan = _first_task_context(built.built, attempt_path)
        plans.append(plan)
        record = orchestration_contracts.load_record(
            plan.task_attempt_path, "task-attempt"
        )
        record["status"] = recorded_status
        record["failure_message"] = (
            "fixture postentry failure\x1b[31m" if recorded_status == "failed" else None
        )
        orchestration_contracts.validate_record("task-attempt", record)
        plan.task_attempt_path.write_bytes(
            orchestration_contracts.canonical_json_bytes(record)
        )
        plan.verified_task_path.unlink()
        return result

    outcome = _run_attempt(
        built.request, ops=replace(built.ops(), run_workflow=without_verification)
    )
    plan = plans[0]
    if malformed_start:
        record = orchestration_contracts.load_record(
            plan.task_attempt_path, "task-attempt"
        )
        start_path = plan.run_root / record["task_start_record"]["path"]
        start_path.write_bytes(b'{"malformed":true}')
        record["task_start_record"] = _record_reference(start_path, plan.run_root)
        orchestration_contracts.validate_record("task-attempt", record)
        plan.task_attempt_path.write_bytes(
            orchestration_contracts.canonical_json_bytes(record)
        )
    before = {
        path: path.read_bytes()
        for path in built.built.run_root.rglob("*")
        if path.is_file()
    }
    observed = built.inspect()
    inspected = next(
        item
        for item in observed.tasks
        if (item.expected.machine_key, item.expected.scope_id)
        == (plan.machine_key, plan.scope["scope_id"])
    )
    assert inspected.state == ("pending" if malformed_start else "blocked")
    assert inspected.record is None
    assert inspected.record_reference is None
    terminal_reference = _record_reference(plan.task_attempt_path, plan.run_root)
    if malformed_start:
        assert inspected.start_reference is None
        assert inspected.terminal_attempts == ()
        assert any(
            "Could not close attempt task state" in item for item in observed.blockers
        )
    else:
        assert inspected.start_reference is not None
        assert len(inspected.terminal_attempts) == 1
        terminal = inspected.terminal_attempts[0]
        assert terminal.record["status"] == recorded_status
        assert terminal.record_reference == terminal_reference
        assert terminal.record["stdout_log"] == _record_reference(
            plan.stdout_path, plan.run_root
        )
        assert terminal.record["stderr_log"] == _record_reference(
            plan.stderr_path, plan.run_root
        )
    assert observed.results_status == "blocked" and not observed.recovery_available
    assert outcome.receipt["status"] == "blocked"
    assert not any(
        item["record"] == terminal_reference
        for item in outcome.receipt["verified_tasks"]
    )
    snapshots = []

    def snapshot(root):
        snapshots.append(root)
        return observed

    monkeypatch.setattr(control.inspection, "inspect_run", snapshot)
    monkeypatch.setattr(
        control,
        "_resolve_run_argument",
        lambda _args: (built.request.request_source_path, plan.run_root),
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    capsys.readouterr()
    for detail in ("normal", "verbose"):
        assert (
            control.inspect_from_args(
                parser.parse_args(
                    [
                        plan.run_root.name,
                        *(["--verbose"] if detail == "verbose" else []),
                    ]
                )
            )
            == 0
        )
        output = capsys.readouterr().out
        assert "Scientific Results: blocked" in output
        assert ("Recovery available: no" in output) is (detail == "verbose")
        assert "Recorded Task attempts:" not in output
        assert ("Recorded Task outcomes and logs:" in output) is (
            detail == "verbose"
            and any(task.terminal_attempts for task in observed.tasks)
        )
        if detail == "verbose" and malformed_start:
            assert f"    record: {plan.task_attempt_path}" not in output
        elif detail == "verbose":
            assert (
                f"recorded {recorded_status}; Attempt {terminal.record['workflow_attempt_id']}"
                in output
            )
            assert f"    record: {plan.task_attempt_path}" in output
            assert (
                "Task diagnostic streams (paths do not establish existence or liveness):"
                in output
            )
            stream_label = (
                f"  Task {plan.machine_key}/{plan.scope['scope_id']} "
                f"({terminal.record['workflow_attempt_id']}; recorded {recorded_status})"
            )
            assert f"{stream_label} stdout: {plan.stdout_path}" in output
            assert f"{stream_label} stderr: {plan.stderr_path}" in output
            if recorded_status == "failed":
                assert "fixture postentry failure\\x1b[31m" in output
        assert "\x1b" not in output
    assert snapshots == [plan.run_root] * 2
    assert {
        path: path.read_bytes()
        for path in built.built.run_root.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize("shape", ["unexpected_owner", "deep_path", "symlink_marker"])
def test_verified_tree_residue_blocks_lifecycle_and_inspection(
    tmp_path: Path,
    shape: str,
) -> None:
    built = _build_harness(tmp_path)
    verified_root = built.built.verified_root
    if shape == "unexpected_owner":
        residue = verified_root / "foreign-owner" / "scope.json"
        residue.parent.mkdir(parents=True)
        residue.write_text("foreign\n", encoding="utf-8")
    elif shape == "deep_path":
        owner = str(built.built.profile["required_owner_keys"][0])
        residue = verified_root / owner / "nested" / "scope.json"
        residue.parent.mkdir(parents=True)
        residue.write_text("foreign\n", encoding="utf-8")
    else:
        expected = inspection.expected_tasks(
            inspection.admit_successor_run(built.built.run_root), built.built.profile
        )[0]
        residue = verified_root / expected.machine_key / f"{expected.scope_id}.json"
        residue.parent.mkdir(parents=True, exist_ok=True)
        residue.symlink_to(built.request.request_source_path)

    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "verified task" in value.lower() for value in outcome.receipt["blockers"]
    )
    observed = built.inspect()
    assert observed.results_status == "blocked"
    assert any("verified task" in value.lower() for value in observed.blockers)


def test_post_child_runtime_identity_change_blocks(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    built.fail_second_runtime_admission = True
    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "Runtime identity changed" in item for item in outcome.receipt["blockers"]
    )
    assert built.runtime_admissions == 2
    observed = built.inspect()
    assert observed.integrity == "blocked"
    assert any("Runtime identity changed" in item for item in observed.receipt_blockers)
    assert not observed.recovery_available


def test_initial_storage_qualification_failure_prevents_workflow(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.fail_first_storage_admission = True

    with pytest.raises(
        lifecycle.LifecycleError,
        match="initial fixture drift",
    ):
        _run_attempt(built.request, ops=built.ops())

    assert built.storage_admissions == 1
    assert "workflow" not in built.events
    assert not (built.built.run_root / "locks" / "run.lock").exists()
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    assert not (built.built.run_root / "attempts" / identifier).exists()


def test_post_child_storage_qualification_change_blocks(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    built.fail_second_storage_admission = True

    outcome = _run_attempt(built.request, ops=built.ops())

    assert built.storage_admissions == 2
    assert "workflow" in built.events
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "post-child fixture drift" in item for item in outcome.receipt["blockers"]
    )
    assert not outcome.lock_path.exists()
    assert outcome.receipt_path.is_file()


def test_authored_request_change_before_publication_fails_cleanly(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.mutate_request_on_first_admission = True
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    with pytest.raises(lifecycle.LifecycleError, match="Authored source changed"):
        _run_attempt(built.request, ops=built.ops())
    assert not (built.built.run_root / "attempts" / identifier).exists()
    assert not (built.built.run_root / "locks" / "run.lock").exists()
    assert built.events[-1] == "release"


def test_attempt_directory_sync_failure_precedes_child_record_publication(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.fail_attempt_directory_sync = True
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])

    with pytest.raises(
        lifecycle.LifecycleError, match="attempt-directory sync failure"
    ):
        _run_attempt(built.request, ops=built.ops())

    attempt_root = built.built.run_root / "attempts" / identifier
    assert attempt_root.is_dir()
    assert not (attempt_root / "request.yaml").exists()
    assert not (attempt_root / "attempt.json").exists()
    assert not (attempt_root / "released-run-lock.json").exists()
    assert (
        built.built.run_root / "locks" / f"released-{identifier}-run-lock.json"
    ).is_file()
    assert not (attempt_root / "attempt-receipt.json").exists()
    assert built.events.index(f"sync:attempts/{identifier}") < built.events.index(
        "release"
    )


def test_malformed_workflow_observation_terminalizes_as_blocked(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path,
        result=lifecycle.WorkflowResult(9, 15, "contradictory fixture result"),
    )
    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert outcome.receipt["snakemake_exit_code"] is None
    assert outcome.receipt["termination_signal"] is None
    assert any(
        "invalid terminal observation" in value for value in outcome.receipt["blockers"]
    )
    assert not outcome.lock_path.exists()


def test_foreign_attempt_directory_race_is_refused_after_lock_acquisition(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    built.inject_attempt_entry_after_lock = True
    with pytest.raises(lifecycle.LifecycleError, match="establish immutable"):
        _run_attempt(built.request, ops=built.ops())
    assert "publish:locks/run.lock" in built.events
    assert built.events[-1] == "release"
    assert not (built.built.run_root / "locks" / "run.lock").exists()
    released = built.built.run_root / "locks" / f"released-{identifier}-run-lock.json"
    assert released.is_file()
    observed = built.inspect()
    assert observed.integrity == "blocked"
    assert any("retained aggregate lock" in value for value in observed.blockers)


def test_existing_lock_serializes_attempt_creation(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    lock = built.built.run_root / "locks" / "run.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    with pytest.raises(lifecycle.LifecycleError, match="Unexpected aggregate run lock"):
        _run_attempt(built.request, ops=built.ops())
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    assert not (built.built.run_root / "attempts" / identifier).exists()


def test_persistent_zero_byte_mutex_is_benign_but_other_shapes_block(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    mutex = built.built.run_root / "locks" / "acquire.mutex"
    mutex.write_bytes(b"")

    assert (
        inspection.lock_tree_blockers(
            built.built.run_root,
            expected_run_lock=False,
        )
        == ()
    )

    mutex.write_bytes(b"foreign\n")
    blockers = inspection.lock_tree_blockers(
        built.built.run_root,
        expected_run_lock=False,
    )
    assert any("must be zero bytes" in item for item in blockers)


def test_retained_pre_attempt_release_evidence_requires_reconciliation(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    identifier = "workflow-20260812T170000Z-" + "a" * 32
    retained = built.built.run_root / "locks" / f"released-{identifier}-run-lock.json"
    retained.write_bytes(b"retained pre-attempt evidence\n")

    blockers = inspection.lock_tree_blockers(
        built.built.run_root,
        expected_run_lock=False,
    )

    assert blockers == (f"Unexpected retained aggregate lock state: {retained}",)


def test_advisory_mutex_unavailability_fails_before_mutex_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built = _build_harness(tmp_path)
    mutex = built.built.run_root / "locks" / "acquire.mutex"
    monkeypatch.setattr(lifecycle, "_fcntl", None)

    with pytest.raises(lifecycle.LifecycleError, match="advisory file locking"):
        with lifecycle._acquire_attempt_mutex(built.built.run_root):
            raise AssertionError("unsupported mutex unexpectedly acquired")

    assert not mutex.exists()


def test_foreign_aggregate_state_blocks_before_lock_acquisition(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    (built.built.run_root / "state" / "foreign").mkdir()

    with pytest.raises(lifecycle.LifecycleError, match="Unexpected aggregate state"):
        _run_attempt(built.request, ops=built.ops())

    assert not (built.built.run_root / "locks" / "run.lock").exists()


def test_late_state_and_lock_namespace_drift_are_receipt_bound_blockers(
    tmp_path: Path,
) -> None:
    state_case = _build_harness(
        tmp_path / "state", result=lifecycle.WorkflowResult(7, None)
    )
    state_case.inject_state_entry_after_child = True
    with pytest.raises(
        lifecycle.LifecycleError,
        match="lock release left ambiguous aggregate state",
    ):
        _run_attempt(state_case.request, ops=state_case.ops())
    identifier = str(_attempt_record(state_case.request)["workflow_attempt_id"])
    state_attempt = state_case.built.run_root / "attempts" / identifier
    receipt = json.loads((state_attempt / "prepared-attempt-receipt.json").read_bytes())
    assert receipt["status"] == "blocked"
    assert any(
        "Unexpected aggregate state path" in item for item in receipt["blockers"]
    )
    assert (state_attempt / "attempt-receipt.json").is_file()

    lock_case = _build_harness(
        tmp_path / "lock", result=lifecycle.WorkflowResult(7, None)
    )
    lock_case.inject_lock_entry_on_release = True
    with pytest.raises(
        lifecycle.LifecycleError,
        match="Unexpected retained aggregate lock state",
    ):
        _run_attempt(lock_case.request, ops=lock_case.ops())
    identifier = str(_attempt_record(lock_case.request)["workflow_attempt_id"])
    attempt_root = lock_case.built.run_root / "attempts" / identifier
    assert (attempt_root / "prepared-attempt-receipt.json").is_file()
    assert (attempt_root / "released-run-lock.json").is_file()
    assert not (attempt_root / "attempt-receipt.json").exists()
    assert (lock_case.built.run_root / "locks/foreign.lock").is_file()


def test_release_hook_cannot_substitute_equal_bytes_on_a_new_inode(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()

    def copied_release(
        path: Path,
        evidence_path: Path,
        expected: bytes,
        _inode: tuple[int, int],
        _retain_source: bool,
    ) -> None:
        evidence_path.write_bytes(expected)
        path.unlink()

    ops = lifecycle.LifecycleOps(
        run_workflow=defaults.run_workflow,
        publish_bytes=defaults.publish_bytes,
        release_lock=copied_release,
        promote_receipt=defaults.promote_receipt,
        now=defaults.now,
        host_name=defaults.host_name,
        process_id=defaults.process_id,
        process_is_alive=defaults.process_is_alive,
        validate_reporting_receipt=defaults.validate_reporting_receipt,
        admit_storage_context=defaults.admit_storage_context,
        admit_runtime_context=defaults.admit_runtime_context,
        sync_directory=defaults.sync_directory,
    )
    with pytest.raises(
        (lifecycle.LifecycleError, inspection.InspectionError),
        match="staged terminal receipt alias",
    ):
        _run_attempt(built.request, ops=ops)
    identifier = str(_attempt_record(built.request)["workflow_attempt_id"])
    attempt_root = built.built.run_root / "attempts" / identifier
    assert (attempt_root / "prepared-attempt-receipt.json").is_file()
    assert (attempt_root / "released-run-lock.json").is_file()
    assert not (attempt_root / "attempt-receipt.json").exists()
    assert inspection.inspect_run(built.built.run_root).prepared_finalization is None
    with pytest.raises(inspection.InspectionError, match="no admissible prepared"):
        inspection.inspect_prepared_finalization(built.built.run_root)


def test_owned_lock_release_retains_owned_inode_and_removes_public_name(
    tmp_path: Path,
) -> None:
    lock = tmp_path / "run.lock"
    expected = b"owned lock\n"
    lock.write_bytes(expected)
    state = lock.stat(follow_symlinks=False)

    evidence = tmp_path / "released-run-lock.json"
    lifecycle._release_owned_lock(
        lock,
        evidence,
        expected,
        (state.st_dev, state.st_ino),
    )
    evidence_state = evidence.stat(follow_symlinks=False)
    assert not lock.exists()
    assert (evidence_state.st_dev, evidence_state.st_ino) == (
        state.st_dev,
        state.st_ino,
    )
    assert evidence.read_bytes() == expected


def test_owned_lock_release_collision_preserves_source_and_foreign_evidence(
    tmp_path: Path,
) -> None:
    lock = tmp_path / "run.lock"
    expected = b"owned lock\n"
    foreign = b"foreign replacement\n"
    lock.write_bytes(expected)
    state = lock.stat(follow_symlinks=False)

    evidence = tmp_path / "released-run-lock.json"
    evidence.write_bytes(foreign)
    foreign_state = evidence.stat(follow_symlinks=False)

    with pytest.raises(lifecycle.LifecycleError, match="Refusing to replace"):
        lifecycle._release_owned_lock(
            lock,
            evidence,
            expected,
            (state.st_dev, state.st_ino),
        )
    assert lock.read_bytes() == expected
    assert evidence.read_bytes() == foreign
    evidence_after = evidence.stat(follow_symlinks=False)
    assert (evidence_after.st_dev, evidence_after.st_ino) == (
        foreign_state.st_dev,
        foreign_state.st_ino,
    )


def test_owned_lock_injected_destination_race_preserves_both_names(
    tmp_path: Path,
) -> None:
    lock = tmp_path / "run.lock"
    expected = b"owned lock\n"
    foreign = b"foreign replacement\n"
    lock.write_bytes(expected)
    state = lock.stat(follow_symlinks=False)
    evidence = tmp_path / "released-run-lock.json"

    def collide(_source: Path, destination: Path) -> None:
        destination.write_bytes(foreign)
        raise FileExistsError(destination)

    with pytest.raises(lifecycle.LifecycleError, match="Refusing to replace"):
        lifecycle._release_owned_lock(
            lock,
            evidence,
            expected,
            (state.st_dev, state.st_ino),
            publish_evidence=collide,
        )

    assert lock.read_bytes() == expected
    assert evidence.read_bytes() == foreign


def test_prepared_receipt_promotion_retains_inode_and_exact_bytes(
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared-attempt-receipt.json"
    receipt = tmp_path / "attempt-receipt.json"
    expected = b'{"schema_version":"emrys.attempt-receipt.v3"}\n'
    prepared.write_bytes(expected)
    prepared_state = prepared.stat(follow_symlinks=False)

    lifecycle._promote_prepared_receipt(
        prepared,
        receipt,
        expected,
        (prepared_state.st_dev, prepared_state.st_ino),
    )

    receipt_state = receipt.stat(follow_symlinks=False)
    assert not prepared.exists()
    assert receipt.read_bytes() == expected
    assert (receipt_state.st_dev, receipt_state.st_ino) == (
        prepared_state.st_dev,
        prepared_state.st_ino,
    )


def test_prepared_receipt_cleanup_failure_preserves_both_inode_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = tmp_path / "prepared-attempt-receipt.json"
    receipt = tmp_path / "attempt-receipt.json"
    expected = b'{"schema_version":"emrys.attempt-receipt.v3"}\n'
    prepared.write_bytes(expected)
    prepared_state = prepared.stat(follow_symlinks=False)
    real_unlink = Path.unlink

    def fail_prepared_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == prepared:
            raise OSError("fixture prepared-alias cleanup failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_prepared_unlink)

    with pytest.raises(
        lifecycle.LifecycleError,
        match="prepared-alias cleanup failure",
    ):
        lifecycle._promote_prepared_receipt(
            prepared,
            receipt,
            expected,
            (prepared_state.st_dev, prepared_state.st_ino),
        )

    receipt_state = receipt.stat(follow_symlinks=False)
    assert prepared.read_bytes() == receipt.read_bytes() == expected
    assert (receipt_state.st_dev, receipt_state.st_ino) == (
        prepared_state.st_dev,
        prepared_state.st_ino,
    )


def test_initial_and_resume_argv_never_contain_recovery_bypasses(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    initial = list(_attempt_record(built.request)["snakemake_argv"])
    assert "--rerun-triggers" not in initial
    assert "--ignore-incomplete" not in initial
    forbidden = {
        "--unlock",
        "--cleanup-metadata",
        "--forceall",
        "--rerun-incomplete",
        "--force",
    }
    assert forbidden.isdisjoint(initial)

    record = copy.deepcopy(_attempt_record(built.request))
    record["snakemake_argv"].insert(-2, "--unlock")
    with pytest.raises(
        orchestration_contracts.ContractValidationError, match="forbidden"
    ):
        orchestration_contracts.validate_record("workflow-attempt", record)


def test_inspection_blocks_empty_or_foreign_attempt_state(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    empty = (
        built.built.run_root / "attempts" / ("workflow-20260812T170000Z-" + "a" * 32)
    )
    empty.mkdir()
    observed = built.inspect()
    assert observed.integrity == "blocked"
    assert any(str(empty / "attempt.json") in item for item in observed.blockers)


@pytest.mark.parametrize("root_state", ("missing", "symlink"))
def test_attempts_root_must_be_pre_materialized_and_real(
    tmp_path: Path,
    root_state: str,
) -> None:
    built = _build_harness(tmp_path)
    attempts_root = built.built.run_root / "attempts"
    if root_state == "missing":
        attempts_root.rmdir()
    else:
        real_root = attempts_root.with_name("attempts-real")
        attempts_root.rename(real_root)
        attempts_root.symlink_to(real_root, target_is_directory=True)

    observed = built.inspect()
    assert observed.integrity == "blocked"
    assert any("attempts root" in item for item in observed.blockers)

    with pytest.raises(
        lifecycle.LifecycleError,
        match="Lifecycle parent must be pre-materialized and real",
    ):
        _run_attempt(built.request, ops=built.ops())
    assert not any(event == "publish:locks/run.lock" for event in built.events)


def test_nonattempt_entry_and_unexpected_attempt_child_block_before_lock(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    attempts_root = built.built.run_root / "attempts"
    (attempts_root / "foreign").mkdir()
    identifier = "workflow-20260812T170000Z-" + "b" * 32
    attempt_root = attempts_root / identifier
    attempt_root.mkdir()
    (attempt_root / "foreign.txt").write_text("foreign\n", encoding="utf-8")

    observed = built.inspect()
    assert observed.integrity == "blocked"
    assert any(
        "Unexpected aggregate attempt state" in item for item in observed.blockers
    )
    assert any(
        "Unexpected workflow-attempt state" in item for item in observed.blockers
    )

    with pytest.raises(lifecycle.LifecycleError, match="Aggregate attempt state"):
        _run_attempt(built.request, ops=built.ops())
    assert not any(event == "publish:locks/run.lock" for event in built.events)


def test_lying_runtime_authority_fails_before_attempt_publication(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)

    def reject(
        _attempt: dict[str, Any],
        _request: lifecycle.LifecycleRequest,
        _storage_binding: RuntimeBinding | None,
        _initial_inspection: RuntimeInspection | None,
    ) -> None:
        raise lifecycle.LifecycleError("declared checkout differs from observed")

    ops = built.ops()
    lying = lifecycle.LifecycleOps(
        run_workflow=ops.run_workflow,
        publish_bytes=ops.publish_bytes,
        release_lock=ops.release_lock,
        promote_receipt=ops.promote_receipt,
        now=ops.now,
        host_name=ops.host_name,
        process_id=ops.process_id,
        process_is_alive=ops.process_is_alive,
        validate_reporting_receipt=ops.validate_reporting_receipt,
        admit_storage_context=ops.admit_storage_context,
        admit_runtime_context=reject,
        sync_directory=ops.sync_directory,
    )
    with pytest.raises(lifecycle.LifecycleError, match="checkout differs"):
        _run_attempt(built.request, ops=lying)
    assert built.events == [
        "publish:locks/run.lock",
        "storage-admitted",
        "release",
    ]
    assert not list((built.built.run_root / "attempts").iterdir())


def test_success_receipt_with_verified_subset_is_blocked_on_inspection(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = _run_attempt(built.request, ops=built.ops())
    receipt = orchestration_contracts.load_record(
        outcome.receipt_path, "attempt-receipt"
    )
    receipt["verified_tasks"] = receipt["verified_tasks"][:1]
    receipt.update(
        status="blocked",
        blockers=["fixture forged subset"],
        message="fixture forged subset",
    )
    outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(receipt)
    )
    observed = built.inspect()
    assert observed.results_status == "blocked"
    assert any("cumulative verified tasks" in item for item in observed.blockers)


def test_completed_run_refuses_rerun_and_resume(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    _run_attempt(built.request, ops=built.ops())
    with pytest.raises(lifecycle.LifecycleError, match="prior attempts"):
        _run_attempt(built.request, ops=built.ops())

    first_id = str(_attempt_record(built.request)["workflow_attempt_id"])
    resume_id = "workflow-20260812T160000Z-" + "f" * 32
    manifest = built.built.run_root / "attempts" / resume_id / "attempt.json"
    argv = lifecycle.build_snakemake_argv(
        python_executable=built.request.python_executable,
        snakefile=built.request.snakefile,
        workflow_profile=built.request.workflow_profile,
        configfile=manifest,
        run_root=built.built.run_root,
        target="cohort_slice",
        operation="resume",
        cores=1,
        resource_limits=workflow_fixture._resource_limits(),
    )
    attempt = _attempt(
        built.built,
        operation="resume",
        identifier=resume_id,
        supersedes=first_id,
        argv=argv,
    )
    resumed = replace(
        built.request,
        operation="resume",
        attempt_record_bytes=orchestration_contracts.canonical_json_bytes(attempt),
    )
    with pytest.raises(lifecycle.LifecycleError, match="Results are complete"):
        _run_attempt(resumed, ops=built.ops())


def test_live_owned_incomplete_start_is_running_then_terminally_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(9, None, "fixture stop")
    )
    built.inspect_live_transient = True
    root = built.built.run_root
    remote_states: list[inspection.RunInspection] = []

    def display(state: inspection.RunInspection) -> None:
        before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
        calls = []
        started = next(item for item in state.tasks if item.start_reference is not None)
        expected_root = (
            root
            / "attempts"
            / started.start_origin
            / "tasks"
            / started.expected.machine_key
            / started.expected.scope_id
        )
        expected_paths = (expected_root / "stderr.log", expected_root / "stdout.log")
        streams = control._inspection_presentation.task_stream_sources(state)
        assert tuple(source.path for source in streams) == expected_paths
        assert all(
            "expected diagnostic from admitted start" in source.label
            for source in streams
        )

        def snapshot(selected: Path) -> inspection.RunInspection:
            assert selected == root
            calls.append(selected)
            return state

        with monkeypatch.context() as public:
            public.setattr(inspection, "inspect_run", snapshot)
            public.setattr(
                control,
                "_resolve_run_argument",
                lambda _args: (built.request.request_source_path, root),
            )
            for verbose in (False, True):
                capsys.readouterr()
                assert (
                    control.inspect_from_args(
                        argparse.Namespace(run=root.name, verbose=verbose)
                    )
                    == 0
                )
                output = capsys.readouterr().out
                assert ("Scientific task observations:" in output) is verbose
                observation = (
                    "Started; completion unverified"
                    if state.attempt_outcome == "running"
                    else "Verification not admitted"
                )
                assert (f"  {observation}: 1" in output) is verbose
                assert f"Scientific Results: {state.results_status}" in output
                assert (f"Run lock: {state.lock_observation}" in output) is (
                    verbose or state.lock_observation != "no lock"
                )
                assert ("Recovery available: no" in output) is verbose
                for path in expected_paths:
                    assert (str(path) in output) is verbose
                if verbose:
                    assert "paths do not establish existence or liveness" in output
                    assert f"; start={root / started.start_reference['path']}" in output
                if state.attempt_outcome == "blocked":
                    assert "Do not resume." in output
                    assert "RESULTS BLOCKER:" in output
        assert calls == [root] * 2
        assert {
            path: path.read_bytes() for path in root.rglob("*") if path.is_file()
        } == before

    def run_workflow(argv: tuple[str, ...], cwd: Path) -> lifecycle.WorkflowResult:
        result = built.run_workflow(argv, cwd)
        assert built.live_observation is not None
        display(built.live_observation)
        remote = built.inspect(
            host="head-node",
            process_is_alive=lambda _pid: pytest.fail("remote PID was probed"),
        )
        remote_states.append(remote)
        display(remote)
        return result

    outcome = _run_attempt(
        built.request, ops=replace(built.ops(), run_workflow=run_workflow)
    )

    assert built.live_observation is not None
    assert built.live_observation.attempt_outcome == "running"
    assert built.live_observation.lock_observation == "local live owner"
    assert not built.live_observation.recovery_available
    assert all(not item.terminal_attempts for item in built.live_observation.tasks)
    assert outcome.receipt["status"] == "blocked"
    assert len(outcome.receipt["task_start_records"]) == 1

    observed = built.inspect()
    assert observed.integrity == "valid"
    assert observed.attempt_outcome == "blocked"
    assert observed.results_status == "blocked"
    display(observed)
    remote = remote_states[0]
    assert remote.lock_observation == "remote ownership unverified"
    assert remote.integrity == remote.results_status == "blocked"
    assert (
        [item.start_reference for item in observed.tasks]
        == [item.start_reference for item in remote.tasks]
        == [item.start_reference for item in built.live_observation.tasks]
    )


@pytest.mark.parametrize(
    ("condition", "expected", "process_checks"),
    (
        ("local", "local live owner", 1),
        ("remote", "remote ownership unverified", 0),
        ("dead", "local process not live", 1),
        ("malformed", "invalid or ambiguous lock", 0),
        ("mismatched", "invalid or ambiguous lock", 0),
        ("namespace", "invalid or ambiguous lock", 0),
    ),
)
def test_live_lock_observation_preserves_admission_and_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    condition: str,
    expected: str,
    process_checks: int,
) -> None:
    built = _build_harness(tmp_path, result=lifecycle.WorkflowResult(9, None))
    root = built.built.run_root
    lock = root / "locks/run.lock"
    foreign = root / "locks/foreign.lock"
    observed_states = []
    checked_processes = []
    lock_reads = []
    read_counts = []
    displays = []
    original_admit = inspection.admit_canonical_record

    def admit_record(path, *args, **kwargs):
        if path == lock:
            lock_reads.append(path)
        return original_admit(path, *args, **kwargs)

    monkeypatch.setattr(inspection, "admit_canonical_record", admit_record)

    def inspect_during_workflow(argv, cwd):
        original_bytes = lock.read_bytes()
        if condition == "malformed":
            lock.write_bytes(b"malformed fixture lock\n")
        elif condition == "mismatched":
            record = json.loads(original_bytes)
            record["process_id"] = 9999
            lock.write_bytes(orchestration_contracts.canonical_json_bytes(record))
        elif condition == "namespace":
            foreign.write_bytes(b"ambiguous fixture lock\n")
        before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
        inspect_ops = built.inspection_ops(
            host="head-node" if condition == "remote" else "fixture-host",
            process_is_alive=lambda pid: (
                checked_processes.append(pid) is None and condition != "dead"
            ),
        )
        previous_reads = len(lock_reads)
        observed_states.append(inspection.inspect_run(root, ops=inspect_ops))
        read_counts.append(len(lock_reads) - previous_reads)
        with monkeypatch.context() as public:
            public.setattr(inspection, "default_inspection_ops", lambda: inspect_ops)
            public.setattr(
                control,
                "_resolve_run_argument",
                lambda _arguments: (built.request.request_source_path, root),
            )
            for verbose in (False, True):
                capsys.readouterr()
                previous_reads = len(lock_reads)
                assert (
                    control.inspect_from_args(
                        argparse.Namespace(
                            project=built.request.request_source_path,
                            run=root.name,
                            verbose=verbose,
                        )
                    )
                    == 0
                )
                displays.append(capsys.readouterr().out)
                read_counts.append(len(lock_reads) - previous_reads)
        assert {
            path: path.read_bytes() for path in root.rglob("*") if path.is_file()
        } == before
        if condition in {"malformed", "mismatched"}:
            lock.write_bytes(original_bytes)
        elif condition == "namespace":
            foreign.unlink()
        return built.run_workflow(argv, cwd)

    _run_attempt(
        built.request, ops=replace(built.ops(), run_workflow=inspect_during_workflow)
    )
    observed = observed_states[0]
    assert observed.lock_observation == expected
    assert observed.attempt_outcome == (
        "running" if condition == "local" else "blocked"
    )
    assert observed.integrity == ("valid" if condition == "local" else "blocked")
    assert not observed.recovery_available
    assert len(checked_processes) == process_checks * 3
    assert read_counts == [0 if condition == "namespace" else 1] * 3
    for index, display in enumerate(displays):
        assert f"Run lock: {expected}" in display
        assert f"Run admission: {observed.integrity}" in display
        assert f"Attempt outcome: {observed.attempt_outcome}" in display
        assert ("Recovery available: no" in display) is bool(index % 2)
        if condition in {"local", "remote", "dead"}:
            assert "Recorded lock host: fixture-host; scheduler job: none" in display
        else:
            assert "Recorded lock host:" not in display
        if condition != "local":
            assert "Do not resume." in display
    if condition == "remote":
        assert (
            "Run lock host is not this host; live ownership is unproved"
            in observed.blockers
        )


@pytest.mark.parametrize("damage", ("missing", "malformed"))
def test_task_start_crash_and_damage_remain_blocked(
    tmp_path: Path, damage: str
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(17, None, "fixture crash")
    )
    built.materialize_start_only = True
    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    start = (
        built.built.run_root
        / outcome.receipt["task_start_records"][0]["record"]["path"]
    )
    if damage == "missing":
        start.unlink()
    else:
        start.write_bytes(b"malformed task-start fixture\n")

    observed = built.inspect()
    assert observed.results_status == "blocked"
    assert any(
        "Could not close attempt task state" in blocker for blocker in observed.blockers
    )
    assert {
        control._inspection_presentation.task_observation(item)
        for item in observed.tasks
    } == {"No admitted start"}
    assert control._inspection_presentation.task_stream_sources(observed) == ()


@pytest.mark.parametrize("tamper", ["extra", "deep", "symlink"])
def test_historical_task_tree_is_recursively_closed(
    tmp_path: Path,
    tamper: str,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = _run_attempt(built.request, ops=built.ops())
    task_root = outcome.attempt_path.parent / "tasks"
    scope_root = next(path for path in task_root.glob("*/*") if path.is_dir())
    if tamper == "extra":
        (scope_root / "foreign.txt").write_text("foreign\n", encoding="utf-8")
    elif tamper == "deep":
        nested = scope_root / "nested"
        nested.mkdir()
        (nested / "foreign.txt").write_text("foreign\n", encoding="utf-8")
    else:
        stdout = scope_root / "stdout.log"
        stdout.unlink()
        stdout.symlink_to(scope_root / "stderr.log")

    observed = built.inspect()
    assert observed.integrity == "valid"
    assert observed.results_status == "blocked"
    assert not observed.recovery_available
    assert any("task" in blocker.lower() for blocker in observed.blockers)
    affected = next(
        item
        for item in observed.tasks
        if (item.expected.machine_key, item.expected.scope_id)
        == (scope_root.parent.name, scope_root.name)
    )
    assert affected.terminal_attempts == ()
    assert any(
        item.terminal_attempts for item in observed.tasks if item is not affected
    )


def test_attempt_logs_are_chunk_hashed_for_inspect_and_resume_preflights(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "preentry failure")
    )
    stdout_data = b"o" * (3 * 1024 * 1024 + 17)
    stderr_data = b"e" * (2 * 1024 * 1024 + 29)
    first.materialize_preentry_failure = True
    first.preentry_stdout = stdout_data
    first.preentry_stderr = stderr_data
    first_outcome = _run_attempt(first.request, ops=first.ops())
    assert first_outcome.receipt["status"] == "failed"
    task_attempt = next(
        first_outcome.attempt_path.parent.glob("tasks/*/*/task-attempt.json")
    )
    stdout_path = task_attempt.with_name("stdout.log")
    stderr_path = task_attempt.with_name("stderr.log")
    log_paths = {stdout_path, stderr_path}
    chunk_lengths: dict[Path, list[int]] = {path: [] for path in log_paths}
    log_identities: dict[Path, tuple[int, int]] = {}
    for path in log_paths:
        state = path.stat(follow_symlinks=False)
        log_identities[path] = (state.st_dev, state.st_ino)
    original_os_read = validation_inputs.os.read
    original_read_bytes = _inspection_attempts._read_bytes

    def track_os_read(descriptor: int, size: int) -> bytes:
        data = original_os_read(descriptor, size)
        state = os.fstat(descriptor)
        identity = (state.st_dev, state.st_ino)
        for path, expected in log_identities.items():
            if identity == expected and data:
                chunk_lengths[path].append(len(data))
        return data

    def reject_full_log_read(path: Path, root: Path, label: str) -> bytes:
        if path in log_paths:
            raise AssertionError(f"task log was fully read: {label}")
        return original_read_bytes(path, root, label)

    monkeypatch.setattr(validation_inputs.os, "read", track_os_read)
    monkeypatch.setattr(_inspection_attempts, "_read_bytes", reject_full_log_read)
    inspect_ops = first.inspection_ops()

    observed = inspection.inspect_run(first.built.run_root, ops=inspect_ops)
    assert observed.recovery_available
    terminals = [
        terminal for item in observed.tasks for terminal in item.terminal_attempts
    ]
    assert len(terminals) == 1
    terminal = terminals[0]
    assert (
        terminal.record["status"] == "failed"
        and terminal.record["task_start_record"] is None
    )
    assert terminal.record_reference == _record_reference(
        task_attempt, first.built.run_root
    )
    assert terminal.record["stdout_log"] == {
        "path": stdout_path.relative_to(first.built.run_root).as_posix(),
        "sha256": hashlib.sha256(stdout_data).hexdigest(),
    }
    assert terminal.record["stderr_log"] == {
        "path": stderr_path.relative_to(first.built.run_root).as_posix(),
        "sha256": hashlib.sha256(stderr_data).hexdigest(),
    }
    for path, expected_size in (
        (stdout_path, len(stdout_data)),
        (stderr_path, len(stderr_data)),
    ):
        assert sum(chunk_lengths[path]) == expected_size
        assert len(chunk_lengths[path]) > 2
        assert max(chunk_lengths[path]) <= 1024 * 1024

    original_inspect_run = inspection.inspect_run
    resume_inspections: list[tuple[str, tuple[Path, ...]]] = []

    def track_inspect_run(
        run_root: Path,
        *,
        ops: inspection.InspectionOps | None = None,
        allowed_next_attempt: Mapping[str, Any] | None = None,
        prospective_receipt: inspection.PreparedFinalizationCandidate | None = None,
    ) -> inspection.RunInspection:
        before = {path: len(chunks) for path, chunks in chunk_lengths.items()}
        result = original_inspect_run(
            run_root,
            ops=ops,
            allowed_next_attempt=allowed_next_attempt,
            prospective_receipt=prospective_receipt,
        )
        resume_inspections.append(
            (
                (
                    "under-lock"
                    if allowed_next_attempt is not None
                    else "prospective"
                    if prospective_receipt is not None
                    else "outer"
                ),
                tuple(
                    path
                    for path in (stdout_path, stderr_path)
                    if len(chunk_lengths[path]) > before[path]
                ),
            )
        )
        return result

    monkeypatch.setattr(inspection, "inspect_run", track_inspect_run)
    first_id = str(_attempt_record(first.request)["workflow_attempt_id"])
    second_id = "workflow-20260812T140500Z-" + "e" * 32
    first.request, _ = _resume_request(
        first,
        identifier=second_id,
        supersedes=first_id,
    )
    first.events = []
    first.result = lifecycle.WorkflowResult(0, None)
    first.materialize_preentry_failure = False
    first.materialize_complete = True

    second_outcome = _run_attempt(first.request, ops=first.ops())
    assert second_outcome.receipt["status"] == "succeeded"
    expected_log_pass = (stdout_path, stderr_path)
    # Outer planning, under-lock admission, staged and terminal re-admission.
    assert resume_inspections == [
        ("outer", expected_log_pass),
        ("under-lock", expected_log_pass),
        ("prospective", expected_log_pass),
        ("outer", expected_log_pass),
    ]


@pytest.mark.parametrize("file_name", ["stdout.log", "stderr.log"])
@pytest.mark.parametrize("tamper", ["append", "truncate"])
def test_task_log_mutation_blocks_completed_run_inspection(
    tmp_path: Path,
    file_name: str,
    tamper: str,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = _run_attempt(built.request, ops=built.ops())
    task_root = outcome.attempt_path.parent / "tasks"
    log_path = next(task_root.glob(f"*/*/{file_name}"))
    if tamper == "append":
        with log_path.open("ab") as stream:
            stream.write(b"foreign log bytes\n")
    else:
        log_path.write_bytes(b"")

    observed = built.inspect()
    assert observed.results_status == "blocked"
    assert any(
        "SHA-256 no longer matches" in blocker and file_name.split(".")[0] in blocker
        for blocker in observed.blockers
    )
    affected = next(
        item
        for item in observed.tasks
        if (item.expected.machine_key, item.expected.scope_id)
        == (log_path.parent.parent.name, log_path.parent.name)
    )
    assert affected.terminal_attempts == ()


@pytest.mark.parametrize("file_name", ["stdout.log", "stderr.log"])
@pytest.mark.parametrize("tamper", ["append", "truncate"])
def test_preentry_task_log_mutation_blocks_resume(
    tmp_path: Path,
    file_name: str,
    tamper: str,
) -> None:
    built = _build_harness(
        tmp_path,
        result=lifecycle.WorkflowResult(23, None, "preentry failure"),
    )
    built.materialize_preentry_failure = True
    outcome = _run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "failed"
    log_path = next(outcome.attempt_path.parent.glob(f"tasks/*/*/{file_name}"))
    if tamper == "append":
        with log_path.open("ab") as stream:
            stream.write(b"foreign log bytes\n")
    else:
        log_path.write_bytes(b"")

    observed = built.inspect()
    assert observed.results_status == "blocked"
    assert observed.recovery_available is False
    assert all(not item.terminal_attempts for item in observed.tasks)
    assert any(
        "SHA-256 no longer matches" in blocker and file_name.split(".")[0] in blocker
        for blocker in observed.blockers
    )


def test_preentry_failure_can_resume_into_later_verified_start(tmp_path: Path) -> None:
    first = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "preentry failure")
    )
    first.materialize_preentry_failure = True

    def partial_workflow(argv: tuple[str, ...], cwd: Path) -> lifecycle.WorkflowResult:
        result = first.run_workflow(argv, cwd)
        attempt_id = str(_attempt_record(first.request)["workflow_attempt_id"])
        attempt_path = first.built.run_root / "attempts" / attempt_id / "attempt.json"
        expected, _plan = _first_task_context(first.built, attempt_path)
        _materialize_verified(
            first.built, attempt_path, skip=(expected.machine_key, expected.scope_id)
        )
        return result

    first_outcome = _run_attempt(
        first.request, ops=replace(first.ops(), run_workflow=partial_workflow)
    )
    assert first_outcome.receipt["status"] == "failed"
    task_count = sum(
        len(scopes) for scopes in _attempt_record(first.request)["tasks"].values()
    )
    assert len(first_outcome.receipt["task_attempt_records"]) == task_count
    assert first.inspect().recovery_available

    first_id = str(_attempt_record(first.request)["workflow_attempt_id"])
    second_id = "workflow-20260812T140500Z-" + "a" * 32
    first.request, _ = _resume_request(
        first,
        identifier=second_id,
        supersedes=first_id,
    )
    first.events = []
    first.result = lifecycle.WorkflowResult(0, None)
    first.materialize_preentry_failure = False
    first.materialize_complete = True
    second_outcome = _run_attempt(first.request, ops=first.ops())
    assert second_outcome.receipt["status"] == "succeeded"
    assert len(second_outcome.receipt["task_attempt_records"]) == task_count + 1
    complete_observation = first.inspect()
    assert (
        complete_observation.integrity,
        complete_observation.attempt_outcome,
        complete_observation.results_status,
        complete_observation.reporting_status,
        complete_observation.recovery_available,
    ) == ("valid", "succeeded", "complete", "incomplete", False), (
        complete_observation.blockers
    )
    retried = next(
        item for item in complete_observation.tasks if len(item.terminal_attempts) == 2
    )
    assert [
        item.record["workflow_attempt_id"] for item in retried.terminal_attempts
    ] == [first_id, second_id]
    assert [item.record["status"] for item in retried.terminal_attempts] == [
        "failed",
        "succeeded",
    ]
    reused = [item for item in complete_observation.tasks if item is not retried]
    assert reused and all(len(item.terminal_attempts) == 1 for item in reused)
    assert all(
        item.terminal_attempts[0].record["workflow_attempt_id"] == first_id
        for item in reused
    )
    for item in complete_observation.tasks:
        for terminal in item.terminal_attempts:
            assert terminal.record_reference == _record_reference(
                first.built.run_root / terminal.record_reference["path"],
                first.built.run_root,
            )

    historical = retried.terminal_attempts[0]
    historical_path = first.built.run_root / historical.record_reference["path"]
    historical_bytes = historical_path.read_bytes()
    wrong_start = copy.deepcopy(historical.record)
    wrong_start["task_start_record"] = retried.start_reference
    orchestration_contracts.validate_record("task-attempt", wrong_start)
    historical_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(wrong_start)
    )
    wrong_origin = first.inspect()
    affected = next(
        item for item in wrong_origin.tasks if item.expected == retried.expected
    )
    assert affected.start_origin == second_id
    assert affected.start_reference == retried.start_reference
    assert [
        item.record["workflow_attempt_id"] for item in affected.terminal_attempts
    ] == [second_id]
    assert wrong_origin.results_status == "blocked"
    assert wrong_origin.blockers and not wrong_origin.recovery_available
    historical_path.write_bytes(historical_bytes)

    original_first_receipt = orchestration_contracts.load_record(
        first_outcome.receipt_path, "attempt-receipt"
    )
    omitted = copy.deepcopy(original_first_receipt)
    omitted["task_attempt_records"] = []
    first_outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(omitted)
    )
    omitted_observation = first.inspect()
    assert omitted_observation.results_status == "blocked"
    assert any(
        "cumulative Task attempts" in blocker
        for blocker in omitted_observation.blockers
    )
    first_outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(original_first_receipt)
    )

    forged = orchestration_contracts.load_record(
        first_outcome.receipt_path, "attempt-receipt"
    )
    forged.update(
        status="blocked",
        blockers=["forged future binding"],
        message="forged future binding",
        task_start_records=second_outcome.receipt["task_start_records"],
    )
    orchestration_contracts.validate_record("attempt-receipt", forged)
    first_outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(forged)
    )
    forged_observation = first.inspect()
    assert forged_observation.integrity == "blocked"
    assert forged_observation.results_status == "blocked"
    assert any(
        "cumulative task starts" in blocker for blocker in forged_observation.blockers
    )
    assert any(
        "Superseded workflow attempt is not resumable" in blocker
        for blocker in forged_observation.blockers
    )
