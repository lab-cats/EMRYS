"""Internal lifecycle, recovery, and derived-state contracts for B4."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import platform
import signal
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.evidence.storage_inventory import qualification as storage_qualification
from emrys.libraries.installed_package_identity import installed_package_tree_identity
from emrys.orchestration.local_pilot import (
    doctor,
    inspection,
    lifecycle,
    reporting_boundary,
)
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture

WORKFLOW_TIME = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)
FINISHED_TIME = datetime(2026, 8, 12, 14, 5, tzinfo=UTC)


def _raise_signal_on_lifecycle_thread(signum: int) -> None:
    """Keep synthetic signals away from xdist's worker-control thread."""

    signal.raise_signal(signum)


def test_successor_lifecycle_requires_symbolic_resource_policy() -> None:
    config = {"resource_policy": workflow_fixture._resource_policy()}

    assert lifecycle._resource_plan_from_workflow_config(config).workflow_cores == 1
    with pytest.raises(lifecycle.LifecycleError, match="resource policy keys"):
        lifecycle._resource_plan_from_workflow_config(
            config,
            require_symbolic=True,
        )


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
            "execution_mode": "local-science-tools",
            "workspace": str(workspace),
            "authored_paths": {"reference_fasta": str(authored_fasta)},
        },
        {"reference": {"fasta": {"path": str(normalized_fasta)}}},
        inspect_storage=inspect_storage,
    )

    assert calls == [(workspace, normalized_fasta)]
    assert binding == doctor.RuntimeBinding(
        check_id="storage_qualification",
        path=receipt,
        resolved_path=receipt.resolve(strict=True),
        sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        observed="b" * 64,
    )


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
        )


def test_default_lifecycle_ops_bind_semantic_storage_admission() -> None:
    admission = lifecycle.default_lifecycle_ops().admit_storage_context

    assert isinstance(admission, partial)
    assert admission.func is lifecycle._readmit_storage_runtime_binding
    assert (
        admission.keywords["inspect_storage"]
        is storage_qualification.admit_final_qualification
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
    reporting_error: str | None = None
    reporting_identity_lie: bool = False
    storage_admissions: int = 0
    fail_first_storage_admission: bool = False
    fail_second_storage_admission: bool = False
    runtime_admissions: int = 0
    fail_second_runtime_admission: bool = False
    mutate_request_on_first_admission: bool = False
    inject_attempt_entry_after_lock: bool = False
    materialize_start_only: bool = False
    materialize_reporting_start_only: bool = False
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
            now=lambda: FINISHED_TIME,
            host_name=lambda: "fixture-host",
            process_id=lambda: 4242,
            process_is_alive=lambda _pid: True,
            validate_reporting_receipt=self.validate_reporting,
            admit_storage_context=self.admit_storage,
            admit_runtime_context=self.admit_runtime,
            sync_directory=self.sync_directory,
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
        _storage_binding: doctor.RuntimeBinding | None,
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
    ) -> None:
        self.events.append("release")
        state = path.stat(follow_symlinks=False)
        assert (state.st_dev, state.st_ino) == inode
        assert path.read_bytes() == expected
        path.rename(evidence_path)
        assert evidence_path.read_bytes() == expected
        if self.inject_lock_entry_on_release:
            (path.parent / "foreign.lock").write_bytes(b"late foreign lock\n")

    def validate_reporting(
        self,
        name: str,
        path: Path,
        _root: Path,
        _execution: dict[str, Any],
        _profile: dict[str, Any],
        _attempt: dict[str, Any],
        _config: dict[str, Any],
    ) -> ValidatedFixtureReceipt:
        if self.reporting_error is not None:
            raise ValueError(self.reporting_error)
        record = json.loads(path.read_text(encoding="utf-8"))
        if record != {"kind": name, "run_id": self.built.execution["run_id"]}:
            raise ValueError("reporting receipt has wrong semantic identity")
        return ValidatedFixtureReceipt(
            receipt_path=path.with_name("foreign")
            if self.reporting_identity_lie
            else path,
            receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    def run_workflow(
        self, argv: tuple[str, ...], _cwd: Path
    ) -> lifecycle.WorkflowResult:
        self.events.append("workflow")
        assert list(argv) == self.request.attempt_record["snakemake_argv"]
        attempt_path = (
            self.built.run_root
            / "attempts"
            / str(self.request.attempt_record["workflow_attempt_id"])
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
        if self.materialize_reporting_start_only:
            _materialize_reporting_start_only(self.request, "artifact_index")
        if self.inspect_live_transient:
            self.live_observation = inspection.inspect_run(
                self.built.run_root,
                ops=inspection.InspectionOps(
                    lambda: "fixture-host",
                    lambda _pid: True,
                    self.validate_reporting,
                ),
            )
        if self.materialize_complete:
            _materialize_verified(
                self.built,
                attempt_path,
            )
            _materialize_reporting(self.request, self.built.execution["run_id"])
        if self.mutate_verified:
            marker = next(self.built.verified_root.glob("*/*.json"))
            record = orchestration_contracts.load_record(marker, "verified-task")
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


def test_process_group_poll_failure_still_forces_quiescence() -> None:
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
        if signum == signal.SIGTERM:
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
    )

    with pytest.raises(OSError, match="poll failed"):
        lifecycle._run_process_group(("fixture",), Path("/"), controller, ops=ops)

    assert sent == [signal.SIGTERM]


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
    identifier = str(built.request.attempt_record["workflow_attempt_id"])

    with pytest.raises(lifecycle.ProcessGroupAmbiguity):
        lifecycle.run_attempt(
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
        lifecycle.run_attempt(
            built.request,
            ops=replace(built.ops(), observe_phase=interrupt),
        )

    identifier = str(built.request.attempt_record["workflow_attempt_id"])
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

    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    with pytest.raises(lifecycle.LifecycleError, match="after run-lock"):
        lifecycle.run_attempt(
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

    outcome = lifecycle.run_attempt(
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
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    receipt_path = (
        built.built.run_root / "attempts" / identifier / "attempt-receipt.json"
    )
    prior = signal.getsignal(signal.SIGTERM)

    def ambient(_signum: int, _frame: object) -> None:
        ambient_observations.append(receipt_path.is_file())

    def publish(path: Path, data: bytes) -> None:
        if path == receipt_path:
            _raise_signal_on_lifecycle_thread(signal.SIGTERM)
        defaults.publish_bytes(path, data)

    signal.signal(signal.SIGTERM, ambient)
    try:
        outcome = lifecycle.run_attempt(
            built.request,
            ops=replace(defaults, publish_bytes=publish),
        )
    finally:
        signal.signal(signal.SIGTERM, prior)

    assert outcome.receipt["status"] == "failed"
    assert ambient_observations == [True]
    assert receipt_path.is_file()


@pytest.mark.parametrize("mutex_phase", ["before_release", "after_release"])
def test_signal_during_mutex_cleanup_is_delivered_after_unlock(
    tmp_path: Path,
    mutex_phase: str,
) -> None:
    built = _build_harness(tmp_path)
    defaults = built.ops()
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
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
        outcome = lifecycle.run_attempt(
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
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    receipt_path = (
        built.built.run_root / "attempts" / identifier / "attempt-receipt.json"
    )
    prior_handlers = {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    }
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())

    def publish(path: Path, data: bytes) -> None:
        if path == receipt_path:
            os.kill(os.getpid(), signal.SIGINT)
            raise OSError("fixture receipt publication failure")
        defaults.publish_bytes(path, data)

    with pytest.raises(OSError, match="receipt publication failure"):
        lifecycle.run_attempt(
            built.request,
            ops=replace(defaults, publish_bytes=publish),
        )

    assert not receipt_path.exists()
    assert (
        built.built.run_root / "attempts" / identifier / "released-run-lock.json"
    ).is_file()
    assert {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    } == prior_handlers
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == prior_mask


def test_preblocked_ordinary_signal_is_refused_without_run_evidence(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    try:
        with pytest.raises(lifecycle.LifecycleError, match="ambient mask"):
            lifecycle.run_attempt(built.request, ops=built.ops())
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
) -> tuple[inspection.ExpectedTask, dict[str, Any], Path, dict[str, Any]]:
    expected = inspection.expected_tasks(built.execution, built.profile)[0]
    attempt = orchestration_contracts.load_record(attempt_path, "workflow-attempt")
    config = orchestration_contracts.load_json_object(
        built.run_root / str(attempt["workflow_config"]["path"])
    )
    dispatch_path = Path(
        config["dispatch_paths"][expected.machine_key][expected.scope_id]["path"]
    )
    dispatch = orchestration_contracts.load_json_object(dispatch_path)
    return expected, attempt, dispatch_path, dispatch


def _materialize_start_only(
    built: workflow_fixture.WorkflowFixture,
    attempt_path: Path,
) -> Path:
    expected, attempt, dispatch_path, dispatch = _first_task_context(
        built, attempt_path
    )
    start_path = Path(dispatch["task_start_path"])
    start_path.parent.mkdir(parents=True, exist_ok=True)
    task_root = Path(dispatch["task_attempt_path"]).parent
    task_root.mkdir(parents=True, exist_ok=True)
    start = {
        "schema_version": "emrys.task-start.v1",
        "run_id": built.execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(
            (built.run_root / "contract" / "normalized.json").read_bytes()
        ).hexdigest(),
        "profile_sha256": hashlib.sha256(
            (built.run_root / "contract" / "profile.json").read_bytes()
        ).hexdigest(),
        "workflow_attempt_id": attempt["workflow_attempt_id"],
        "task_attempt_id": dispatch["task_attempt_id"],
        "machine_key": expected.machine_key,
        "scope": expected.scope,
        "owner_run_token": dispatch["owner_run_token"],
        "workflow_attempt_record": _record_reference(attempt_path, built.run_root),
        "workflow_config": attempt["workflow_config"],
        "run_lock": inspection.admit_attempt_run_lock(
            built.run_root, attempt, require_active=True
        ),
        "task_dispatch_record": _record_reference(dispatch_path, built.run_root),
        "created_at": "2026-08-12T12:01:00Z",
    }
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
    expected, attempt, _dispatch_path, dispatch = _first_task_context(
        built, attempt_path
    )
    task_attempt_path = Path(dispatch["task_attempt_path"])
    task_attempt_path.parent.mkdir(parents=True, exist_ok=True)
    stdout = Path(dispatch["stdout_path"])
    stderr = Path(dispatch["stderr_path"])
    stdout.write_bytes(stdout_data)
    stderr.write_bytes(stderr_data)
    record = {
        "schema_version": "emrys.task-attempt.v1",
        "run_id": built.execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(
            (built.run_root / "contract" / "normalized.json").read_bytes()
        ).hexdigest(),
        "profile_sha256": hashlib.sha256(
            (built.run_root / "contract" / "profile.json").read_bytes()
        ).hexdigest(),
        "workflow_attempt_id": attempt["workflow_attempt_id"],
        "task_attempt_id": dispatch["task_attempt_id"],
        "machine_key": expected.machine_key,
        "scope": expected.scope,
        "owner_run_token": dispatch["owner_run_token"],
        "task_start_record": None,
        "status": "failed",
        "started_at": "2026-08-12T12:01:00Z",
        "finished_at": "2026-08-12T12:01:01Z",
        "producer": None,
        "validator": None,
        "semantic_all_pass": None,
        "stable_inputs_rechecked": False,
        "validation_report": None,
        "stdout_log": _record_reference(stdout, built.run_root),
        "stderr_log": _record_reference(stderr, built.run_root),
        "failure_message": "fixture preentry admission failure",
    }
    orchestration_contracts.validate_record("task-attempt", record)
    task_attempt_path.write_bytes(orchestration_contracts.canonical_json_bytes(record))
    return task_attempt_path


def _materialize_verified(
    built: workflow_fixture.WorkflowFixture, attempt_path: Path
) -> None:
    execution_hash = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(built.execution)
    ).hexdigest()
    profile_hash = orchestration_contracts.canonical_sha256(built.profile)
    owners = {str(item["machine_key"]): item for item in built.profile["owner_tasks"]}
    command = {"argv": ["fixture-owner", "--execute"], "exit_code": 0}
    workflow_id = str(
        orchestration_contracts.load_record(attempt_path, "workflow-attempt")[
            "workflow_attempt_id"
        ]
    )
    workflow_attempt = orchestration_contracts.load_record(
        attempt_path, "workflow-attempt"
    )
    workflow_config = workflow_attempt["workflow_config"]
    config_document = orchestration_contracts.load_json_object(
        built.run_root / str(workflow_config["path"])
    )
    for index, expected in enumerate(
        inspection.expected_tasks(built.execution, built.profile), start=1
    ):
        machine = expected.machine_key
        scope_id = expected.scope_id
        marker = built.verified_root / machine / f"{scope_id}.json"
        if marker.is_file() and not marker.is_symlink():
            continue
        owner = owners[machine]
        dispatch_path = Path(
            config_document["dispatch_paths"][machine][scope_id]["path"]
        )
        dispatch = orchestration_contracts.load_json_object(dispatch_path)
        task_id = str(dispatch["task_attempt_id"])
        owner_token = str(dispatch["owner_run_token"])
        task_root = Path(dispatch["task_attempt_path"]).parent
        task_root.mkdir(parents=True, exist_ok=True)
        artifact_root = (
            built.run_root / "products" / "lifecycle-task-double" / machine / scope_id
        )
        artifact_root.mkdir(parents=True, exist_ok=True)
        input_path = artifact_root / "input.txt"
        output_path = artifact_root / "output.txt"
        report_path = artifact_root / "validation.tsv"
        input_path.write_text(f"input {machine} {scope_id}\n", encoding="utf-8")
        output_path.write_text(f"output {machine} {scope_id}\n", encoding="utf-8")
        report_path.write_text(
            "step_id\tscope_id\tcheck_id\tstatus\tobserved\texpected\tdetail\n"
            f"{owner['step_id']}\t{scope_id}\tlifecycle_fixture\tpass\tpass\tpass\tfixture\n",
            encoding="utf-8",
        )
        task_start_path = (
            built.run_root / "state" / "task-starts" / machine / f"{scope_id}.json"
        )
        task_start_path.parent.mkdir(parents=True, exist_ok=True)
        start = {
            "schema_version": "emrys.task-start.v1",
            "run_id": built.execution["run_id"],
            "execution_contract_sha256": execution_hash,
            "profile_sha256": profile_hash,
            "workflow_attempt_id": workflow_id,
            "task_attempt_id": task_id,
            "machine_key": machine,
            "scope": expected.scope,
            "owner_run_token": owner_token,
            "workflow_attempt_record": _record_reference(attempt_path, built.run_root),
            "workflow_config": workflow_config,
            "run_lock": inspection.admit_attempt_run_lock(
                built.run_root, workflow_attempt, require_active=True
            ),
            "task_dispatch_record": _record_reference(dispatch_path, built.run_root),
            "created_at": "2026-08-12T12:01:00Z",
        }
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
        task_attempt = {
            "schema_version": "emrys.task-attempt.v1",
            "run_id": built.execution["run_id"],
            "execution_contract_sha256": execution_hash,
            "profile_sha256": profile_hash,
            "workflow_attempt_id": workflow_id,
            "task_attempt_id": task_id,
            "machine_key": machine,
            "scope": expected.scope,
            "owner_run_token": owner_token,
            "task_start_record": task_start_reference,
            "status": "succeeded",
            "started_at": "2026-08-12T12:01:00Z",
            "finished_at": "2026-08-12T12:02:00Z",
            "producer": command,
            "validator": command,
            "semantic_all_pass": command,
            "stable_inputs_rechecked": True,
            "validation_report": report_reference,
            "stdout_log": _record_reference(task_root / "stdout.log", built.run_root),
            "stderr_log": _record_reference(task_root / "stderr.log", built.run_root),
            "failure_message": None,
        }
        orchestration_contracts.validate_record("task-attempt", task_attempt)
        task_attempt_path.write_bytes(
            orchestration_contracts.canonical_json_bytes(task_attempt)
        )
        verified = {
            "schema_version": "emrys.verified-task.v1",
            "run_id": built.execution["run_id"],
            "execution_contract_sha256": execution_hash,
            "profile_sha256": profile_hash,
            "workflow_attempt_id": workflow_id,
            "task_attempt_id": task_id,
            "task_attempt_record": _record_reference(task_attempt_path, built.run_root),
            "task_start_record": task_start_reference,
            "machine_key": machine,
            "scope": expected.scope,
            "owner_run_token": owner_token,
            "commands": {
                "producer": command,
                "validator": command,
                "semantic_all_pass": command,
            },
            "inputs": [_bound("fixture_input", input_path)],
            "outputs": [_bound("fixture_output", output_path)],
            "native_receipt": None,
            "validation_report": {**report_reference, "all_pass": True},
            "stable_inputs_rechecked": True,
            "all_pass": True,
            "created_at": "2026-08-12T12:02:00Z",
        }
        orchestration_contracts.validate_record("verified-task", verified)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(orchestration_contracts.canonical_json_bytes(verified))


def _materialize_reporting(
    request: lifecycle.LifecycleRequest,
    run_id: str,
) -> None:
    semantic_paths = {
        "artifact_index": (
            request.run_root
            / "products"
            / "artifact-summary"
            / run_id
            / f"{run_id}.artifact_receipt.tsv"
        ),
        "run_summary": (
            request.run_root
            / "products"
            / "artifact-summary"
            / run_id
            / f"{run_id}.run_summary_receipt.tsv"
        ),
        "html_report": (
            request.run_root
            / "products"
            / "report"
            / run_id
            / f"{run_id}.report_outputs.tsv"
        ),
    }
    for name in ("artifact_index", "run_summary", "html_report"):
        ledger = reporting_boundary.ledger_paths(request.run_root, name)
        if ledger.verified.is_file() and not ledger.verified.is_symlink():
            continue
        path = semantic_paths[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            orchestration_contracts.canonical_json_bytes(
                {"kind": name, "run_id": run_id}
            )
        )
        reporting_boundary.publish_start(
            kind=name,
            run_root=request.run_root,
            execution_path=request.execution_path,
            profile_path=request.profile_path,
            workflow_attempt_path=(
                request.run_root
                / "attempts"
                / str(request.attempt_record["workflow_attempt_id"])
                / "attempt.json"
            ),
            workflow_config_path=request.workflow_config_path,
            ops=reporting_boundary.ReportingBoundaryOps(
                publish_bytes=_publish_fixture_bytes,
                now=lambda: FINISHED_TIME,
                validate_semantic_receipt=lambda *args: ValidatedFixtureReceipt(
                    receipt_path=args[1],
                    receipt_sha256=hashlib.sha256(args[1].read_bytes()).hexdigest(),
                ),
                attest_source_checkout=lambda **_kwargs: None,
            ),
        )
        reporting_boundary.publish_verified(
            kind=name,
            receipt_path=path,
            run_root=request.run_root,
            execution_path=request.execution_path,
            profile_path=request.profile_path,
            workflow_attempt_path=(
                request.run_root
                / "attempts"
                / str(request.attempt_record["workflow_attempt_id"])
                / "attempt.json"
            ),
            workflow_config_path=request.workflow_config_path,
            ops=reporting_boundary.ReportingBoundaryOps(
                publish_bytes=_publish_fixture_bytes,
                now=lambda: FINISHED_TIME,
                validate_semantic_receipt=lambda *args: ValidatedFixtureReceipt(
                    receipt_path=args[1],
                    receipt_sha256=hashlib.sha256(args[1].read_bytes()).hexdigest(),
                ),
                attest_source_checkout=lambda **_kwargs: None,
            ),
        )


def _materialize_reporting_start_only(
    request: lifecycle.LifecycleRequest,
    kind: str,
) -> None:
    reporting_boundary.publish_start(
        kind=kind,
        run_root=request.run_root,
        execution_path=request.execution_path,
        profile_path=request.profile_path,
        workflow_attempt_path=(
            request.run_root
            / "attempts"
            / str(request.attempt_record["workflow_attempt_id"])
            / "attempt.json"
        ),
        workflow_config_path=request.workflow_config_path,
        ops=reporting_boundary.ReportingBoundaryOps(
            publish_bytes=_publish_fixture_bytes,
            now=lambda: FINISHED_TIME,
            validate_semantic_receipt=lambda *args: ValidatedFixtureReceipt(
                receipt_path=args[1],
                receipt_sha256=hashlib.sha256(args[1].read_bytes()).hexdigest(),
            ),
            attest_source_checkout=lambda **_kwargs: None,
        ),
    )


def _publish_fixture_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _materialize_workflow_config(
    built: workflow_fixture.WorkflowFixture,
    identifier: str,
) -> Path:
    config = orchestration_contracts.load_json_object(built.config_path)
    config["workflow_attempt_id"] = identifier
    config["python_executable"] = sys.executable
    dispatches: dict[str, dict[str, dict[str, str]]] = {}
    for machine_key, by_scope in config["dispatch_paths"].items():
        dispatches[machine_key] = {}
        for scope_id, reference in by_scope.items():
            verified = built.verified_root / machine_key / f"{scope_id}.json"
            if verified.is_file() and not verified.is_symlink():
                dispatches[machine_key][scope_id] = reference
                continue
            old_path = Path(reference["path"])
            dispatch = orchestration_contracts.load_json_object(old_path)
            task_root = (
                built.run_root
                / "attempts"
                / identifier
                / "tasks"
                / machine_key
                / scope_id
            )
            dispatch.update(
                workflow_attempt_id=identifier,
                task_attempt_path=str(task_root / "task-attempt.json"),
                stdout_path=str(task_root / "stdout.log"),
                stderr_path=str(task_root / "stderr.log"),
            )
            new_path = (
                built.run_root
                / "contract"
                / "dispatch"
                / identifier
                / machine_key
                / f"{scope_id}.json"
            )
            new_path.parent.mkdir(parents=True, exist_ok=True)
            data = orchestration_contracts.canonical_json_bytes(dispatch)
            new_path.write_bytes(data)
            dispatches[machine_key][scope_id] = {
                "path": str(new_path),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
    config["dispatch_paths"] = dispatches
    path = built.run_root / "contract" / "workflow-configs" / f"{identifier}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orchestration_contracts.canonical_json_bytes(config))
    return path


def _attempt(
    built: workflow_fixture.WorkflowFixture,
    *,
    operation: lifecycle.Operation,
    identifier: str,
    supersedes: str | None,
    argv: tuple[str, ...],
) -> dict[str, Any]:
    execution_bytes = (built.run_root / "contract" / "normalized.json").read_bytes()
    profile_bytes = (built.run_root / "contract" / "profile.json").read_bytes()
    created = identifier.split("-")[1]
    created_at = datetime.strptime(created, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    return {
        "schema_version": "emrys.workflow-attempt.v1",
        "run_id": built.execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(execution_bytes).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "workflow_attempt_id": identifier,
        "supersedes_workflow_attempt_id": supersedes,
        "operation": operation,
        "created_at": created_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "request": {
            "path": str(built.run_root / "attempts" / identifier / "request.yaml"),
            "size_bytes": (built.root / "intake" / "request.yaml").stat().st_size,
            "sha256": hashlib.sha256(
                (built.root / "intake" / "request.yaml").read_bytes()
            ).hexdigest(),
        },
        "request_label": "fixture lifecycle",
        "authored_paths": {
            "request": str((built.root / "intake" / "request.yaml").resolve()),
            "sample_manifest": "samples.tsv",
            "partition_manifest": "partitions.tsv",
            "reference_fasta": "reference/genome.fa",
            "reference_gtf": "reference/genome.gtf",
            "analysis_policy": None,
        },
        "normalizer": {
            "name": "emrys",
            "version": "0.1.0",
            "path": sys.executable,
            "resolved_path": str(Path(sys.executable).resolve(strict=True)),
            "sha256": hashlib.sha256(
                Path(sys.executable).resolve(strict=True).read_bytes()
            ).hexdigest(),
        },
        "workspace": str(built.run_root.parent.parent),
        "scratch": None,
        "source_checkout": {
            "path": str(workflow_fixture.REPO_ROOT),
            "commit": workflow_fixture.source_checkout_commit(),
            "clean": True,
        },
        "executor": "local",
        "execution_mode": "test-double",
        "snakemake_argv": list(argv),
        "workflow_config": _record_reference(
            built.run_root / "contract" / "workflow-configs" / f"{identifier}.json",
            built.run_root,
        ),
        "host": "fixture-host",
        "process_id": 4242,
        "owner_token": f"owner-{identifier[-8:]}",
        "cores": 1,
        "required_tools": [
            {
                "name": "python",
                "version": platform.python_version(),
                "path": sys.executable,
                "resolved_path": str(Path(sys.executable).resolve(strict=True)),
                "sha256": hashlib.sha256(
                    Path(sys.executable).resolve(strict=True).read_bytes()
                ).hexdigest(),
            },
            {
                "name": "snakemake",
                "version": "9.25.1",
                "path": sys.executable,
                "resolved_path": str(Path(sys.executable).resolve(strict=True)),
                "sha256": hashlib.sha256(
                    Path(sys.executable).resolve(strict=True).read_bytes()
                ).hexdigest(),
            },
        ],
    }


def _build_harness(
    tmp_path: Path,
    *,
    operation: lifecycle.Operation = "execute",
    supersedes: str | None = None,
    identifier: str | None = None,
    result: lifecycle.WorkflowResult | None = None,
) -> Harness:
    built = workflow_fixture.build(tmp_path / "workspace" / "fixture")
    # The workflow fixture's static B3 attempt binds task dispatches; lifecycle
    # tests replace it with the attempt under test before any EMRYS mutation.
    shutil.rmtree(built.workflow_attempt_path.parent)
    workflow_test_state = built.run_root / "attempts" / "workflow-test"
    if workflow_test_state.exists():
        workflow_test_state.rename(
            built.run_root / "attempts" / "task-fixture-dispatch"
        )
    (built.run_root / "attempts").mkdir(exist_ok=True)
    (built.run_root / "locks").mkdir(exist_ok=True)
    workflow_id = identifier or "workflow-20260812T140000Z-" + "d" * 32
    config = _materialize_workflow_config(built, workflow_id)
    argv = lifecycle.build_snakemake_argv(
        python_executable=Path(sys.executable),
        snakefile=workflow_fixture.SNAKEFILE.resolve(),
        workflow_profile=(
            workflow_fixture.REPO_ROOT / "workflow/profiles/local/profile.v9+.yaml"
        ).resolve(),
        configfile=config,
        run_root=built.run_root,
        target="local_pipeline_slice",
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
        execution_path=built.run_root / "contract" / "normalized.json",
        profile_path=built.run_root / "contract" / "profile.json",
        workflow_config_path=config,
        snakefile=workflow_fixture.SNAKEFILE.resolve(),
        python_executable=Path(sys.executable),
        workflow_profile=(
            workflow_fixture.REPO_ROOT / "workflow/profiles/local/profile.v9+.yaml"
        ).resolve(),
        target="local_pipeline_slice",
        operation=operation,
        attempt_record=attempt,
        request_source_path=(built.root / "intake" / "request.yaml").resolve(),
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
    config = _materialize_workflow_config(harness.built, identifier)
    argv = lifecycle.build_snakemake_argv(
        python_executable=harness.request.python_executable,
        snakefile=harness.request.snakefile,
        workflow_profile=harness.request.workflow_profile,
        configfile=config,
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
            workflow_config_path=config,
            operation="resume",
            attempt_record=attempt,
        ),
        attempt,
    )


def test_success_publishes_receipt_last_and_inspection_ignores_engine_metadata(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())

    assert outcome.receipt["status"] == "succeeded"
    expected_task_count = len(
        inspection.expected_tasks(built.built.execution, built.built.profile)
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
    assert built.events[-2:] == [
        "release",
        f"publish:{outcome.receipt_path.relative_to(built.built.run_root)}",
    ]
    runtime_admissions = [
        index
        for index, event in enumerate(built.events)
        if event == "runtime-admitted"
    ]
    assert len(runtime_admissions) == 2
    storage_admissions = [
        index
        for index, event in enumerate(built.events)
        if event == "storage-admitted"
    ]
    assert len(storage_admissions) == 2
    workflow_index = built.events.index("workflow")
    assert runtime_admissions[0] < workflow_index < runtime_admissions[1]
    assert storage_admissions[0] < workflow_index < storage_admissions[1]
    (built.built.run_root / ".snakemake").mkdir()
    (built.built.run_root / ".snakemake" / "foreign").write_text("junk\n")
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "valid", observed.blockers
    assert observed.attempt_outcome == "succeeded"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "complete"


def test_workflow_argv_binds_reviewed_absolute_source_files(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    argv = list(built.request.attempt_record["snakemake_argv"])
    assert argv[:6] == [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "snakemake",
    ]
    assert argv[argv.index("--snakefile") + 1] == str(
        workflow_fixture.REPO_ROOT / "workflow" / "Snakefile"
    )
    assert argv[argv.index("--workflow-profile") + 1] == str(
        workflow_fixture.REPO_ROOT
        / "workflow"
        / "profiles"
        / "local"
        / "profile.v9+.yaml"
    )

    injected = built.built.run_root / "profiles" / "local" / "profile.v9+.yaml"
    injected.parent.mkdir(parents=True)
    injected.write_text("forceall: true\n", encoding="utf-8")
    assert str(injected) not in argv


def test_foreign_python_runtime_is_rejected_before_mutation(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    attempt = copy.deepcopy(built.request.attempt_record)
    foreign = Path("/usr/bin/python3")
    attempt["normalizer"]["path"] = str(foreign)
    for tool in attempt["required_tools"]:
        if tool["name"] in {"python", "snakemake"}:
            tool["path"] = str(foreign)
    request = lifecycle.LifecycleRequest(
        run_root=built.request.run_root,
        execution_path=built.request.execution_path,
        profile_path=built.request.profile_path,
        workflow_config_path=built.request.workflow_config_path,
        snakefile=built.request.snakefile,
        python_executable=foreign,
        workflow_profile=built.request.workflow_profile,
        target=built.request.target,
        operation=built.request.operation,
        attempt_record=attempt,
        request_source_path=built.request.request_source_path,
    )
    with pytest.raises(lifecycle.LifecycleError, match="lexical sys.executable"):
        lifecycle.run_attempt(request, ops=built.ops())
    assert built.events == []


def test_required_tool_same_path_and_version_rejects_byte_mutation(
    tmp_path: Path,
) -> None:
    tool = tmp_path / "tool"
    tool.write_bytes(b"first executable bytes\n")
    tool.chmod(0o755)
    identity = {
        "name": "star",
        "version": "2.7.11b",
        "path": str(tool),
        "resolved_path": str(tool),
        "sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
    }

    lifecycle._admit_required_tool_identity(identity)
    tool.write_bytes(b"different executable bytes\n")

    with pytest.raises(lifecycle.LifecycleError, match="byte digest differs"):
        lifecycle._admit_required_tool_identity(identity)


def test_initial_and_post_child_runtime_environments_select_bound_java(
    tmp_path: Path,
) -> None:
    selected_home = tmp_path / "selected-java"
    selected_java = selected_home / "bin" / "java"
    selected_java.parent.mkdir(parents=True)
    poison_home = tmp_path / "poison-java"
    poison_java = poison_home / "bin" / "java"
    poison_java.parent.mkdir(parents=True)
    selected_marker = tmp_path / "selected.marker"
    poison_marker = tmp_path / "poison.marker"
    gatk = tmp_path / "gatk"
    renv_library = tmp_path / "renv-library"
    renv_library.mkdir()

    selected_java.write_text(
        "#!/bin/sh\nprintf 'selected\\n' >> \"$SELECTED_MARKER\"\n",
        encoding="utf-8",
    )
    poison_java.write_text(
        "#!/bin/sh\nprintf 'poison\\n' >> \"$POISON_MARKER\"\n",
        encoding="utf-8",
    )
    gatk.write_text(
        '#!/bin/sh\nprintf \'%s|%s\\n\' "$JAVA_HOME" "$(command -v java)"\n'
        "java -version\n",
        encoding="utf-8",
    )
    for executable in (selected_java, poison_java, gatk):
        executable.chmod(0o755)
    hostile = {
        "PATH": f"{poison_java.parent}{os.pathsep}{os.environ['PATH']}",
        "JAVA_HOME": str(poison_home),
        "SELECTED_MARKER": str(selected_marker),
        "POISON_MARKER": str(poison_marker),
        "BASH_ENV": str(tmp_path / "hostile-bash-startup"),
        "CLASSPATH": "/ambient/classes",
        "GATK_JAR": "/ambient/gatk.jar",
        "GATK_LOCAL_JAR": "/ambient/local-gatk.jar",
        "JAVA_OPTS": "-Dambient.java.opts=true",
        "JAVA_TOOL_OPTIONS": "-Dambient.java.tool.options=true",
        "JDK_JAVA_OPTIONS": "-Dambient.jdk.java.options=true",
        "_JAVA_OPTIONS": "-Dambient.underscore.java.options=true",
    }

    observations = []
    for _phase in ("initial", "post-child"):
        environment = lifecycle._local_runtime_environment(
            workflow_fixture.REPO_ROOT,
            renv_library,
            selected_java.resolve(),
            base_environment=hostile,
        )
        completed = subprocess.run(
            (str(gatk),),
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        observations.append(completed.stdout.strip())
        assert "BASH_ENV" not in environment
        assert not {
            "CLASSPATH",
            "GATK_JAR",
            "GATK_LOCAL_JAR",
            "JAVA_OPTS",
            "JAVA_TOOL_OPTIONS",
            "JDK_JAVA_OPTIONS",
            "_JAVA_OPTIONS",
        }.intersection(environment)

    expected = f"{selected_home.resolve()}|{selected_java.resolve()}"
    assert observations == [expected, expected]
    assert selected_marker.read_text(encoding="utf-8").splitlines() == [
        "selected",
        "selected",
    ]
    assert not poison_marker.exists()


def test_r_package_byte_mutation_before_workflow_retains_ambiguous_lock(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    package = tmp_path / "renv-library" / "VariantAnnotation"
    database = package / "R" / "VariantAnnotation.rdb"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"package-db-v1\n")
    (package / "DESCRIPTION").write_text(
        "Package: VariantAnnotation\nVersion: 1.0.0\n",
        encoding="utf-8",
    )
    package_identity = installed_package_tree_identity(package)
    built.request.attempt_record["required_tools"].insert(
        1,
        {
            "name": "r_variant_annotation",
            "version": "1.0.0",
            "path": str(package),
            "resolved_path": str(package),
            "sha256": package_identity.sha256,
        },
    )

    def mutate(phase: str) -> None:
        if phase == "before_workflow":
            database.write_bytes(b"package-db-v2\n")

    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    with pytest.raises(
        lifecycle.LifecycleError,
        match="runner failed without a terminal child observation",
    ) as observed:
        lifecycle.run_attempt(
            built.request,
            ops=replace(built.ops(), observe_phase=mutate),
        )

    assert isinstance(observed.value.__cause__, lifecycle.LifecycleError)
    assert "R package tree digest differs" in str(observed.value.__cause__)
    attempt_root = built.built.run_root / "attempts" / identifier
    assert "workflow" not in built.events
    assert (built.built.run_root / "locks/run.lock").is_file()
    assert (attempt_root / "attempt.json").is_file()
    assert not (attempt_root / "released-run-lock.json").exists()
    assert not (attempt_root / "attempt-receipt.json").exists()


def test_alternate_checkout_snakefile_is_rejected_before_mutation(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    alternate = workflow_fixture.REPO_ROOT / "workflow" / "README.md"
    argv = lifecycle.build_snakemake_argv(
        python_executable=built.request.python_executable,
        snakefile=alternate,
        workflow_profile=built.request.workflow_profile,
        configfile=built.request.workflow_config_path,
        run_root=built.request.run_root,
        target=built.request.target,
        operation=built.request.operation,
        cores=1,
        resource_limits=workflow_fixture._resource_limits(),
    )
    attempt = copy.deepcopy(built.request.attempt_record)
    attempt["snakemake_argv"] = list(argv)
    request = lifecycle.LifecycleRequest(
        run_root=built.request.run_root,
        execution_path=built.request.execution_path,
        profile_path=built.request.profile_path,
        workflow_config_path=built.request.workflow_config_path,
        snakefile=alternate,
        python_executable=built.request.python_executable,
        workflow_profile=built.request.workflow_profile,
        target=built.request.target,
        operation=built.request.operation,
        attempt_record=attempt,
        request_source_path=built.request.request_source_path,
    )
    with pytest.raises(lifecycle.LifecycleError, match="reviewed workflow/Snakefile"):
        lifecycle.run_attempt(request, ops=built.ops())
    assert built.events == []


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
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == expected
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.attempt_outcome == expected
    assert observed.results_status == "incomplete"
    assert observed.reporting_status == "incomplete"
    assert observed.recovery_available


def test_complete_results_and_reports_survive_legacy_failed_receipt(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "late failure")
    )
    built.materialize_complete = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )

    assert outcome.receipt["status"] == "failed"
    assert len(outcome.verified_report_locations) == 2
    assert observed.attempt_outcome == "succeeded"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "complete"
    assert not observed.recovery_available
    assert len(observed.verified_report_locations) == 2


def test_resume_creates_attempt_with_content_bound_rerun_policy(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "preentry failure")
    )
    built.materialize_preentry_failure = True
    first_outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    first_id = str(built.request.attempt_record["workflow_attempt_id"])

    built.request, second_attempt = _resume_request(
        built,
        identifier="workflow-20260812T140500Z-" + "e" * 32,
        supersedes=first_id,
    )
    built.events = []
    built.result = lifecycle.WorkflowResult(0, None)
    built.materialize_preentry_failure = False
    built.materialize_complete = True
    second_outcome = lifecycle.run_attempt(built.request, ops=built.ops())

    assert first_outcome.receipt["status"] == "failed"
    assert second_outcome.receipt["status"] == "succeeded"
    position = second_attempt["snakemake_argv"].index("--rerun-triggers")
    assert second_attempt["snakemake_argv"][position + 1] == "input"
    assert second_attempt["snakemake_argv"].count("--ignore-incomplete") == 1


def test_verified_mutation_blocks(tmp_path: Path) -> None:
    mutation = _build_harness(tmp_path / "mutation")
    mutation.materialize_complete = True
    mutation.mutate_verified = True
    outcome = lifecycle.run_attempt(mutation.request, ops=mutation.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any("content binding" in item for item in outcome.receipt["blockers"])


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
            built.built.execution, built.built.profile
        )[0]
        residue = verified_root / expected.machine_key / f"{expected.scope_id}.json"
        residue.parent.mkdir(parents=True, exist_ok=True)
        residue.symlink_to(built.request.request_source_path)

    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "verified task" in value.lower() for value in outcome.receipt["blockers"]
    )
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.results_status == "blocked"
    assert any("verified task" in value.lower() for value in observed.blockers)


def test_semantically_invalid_reporting_receipt_prevents_completion(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    built.reporting_error = "semantic reporting validation failed"
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any("semantic reporting" in item for item in outcome.receipt["blockers"])
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "valid"
    assert observed.attempt_outcome == "succeeded"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "blocked"
    assert not observed.recovery_available


def test_reporting_validator_cannot_validate_a_different_receipt(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    built.reporting_identity_lie = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "semantic receipt identity no longer matches" in item
        for item in outcome.receipt["blockers"]
    )


def test_post_child_runtime_identity_change_blocks(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    built.fail_second_runtime_admission = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "Runtime identity changed" in item for item in outcome.receipt["blockers"]
    )
    assert built.runtime_admissions == 2
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
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
        lifecycle.run_attempt(built.request, ops=built.ops())

    assert built.storage_admissions == 1
    assert "workflow" not in built.events
    assert not (built.built.run_root / "locks" / "run.lock").exists()
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    assert not (built.built.run_root / "attempts" / identifier).exists()


def test_post_child_storage_qualification_change_blocks(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    built.fail_second_storage_admission = True

    outcome = lifecycle.run_attempt(built.request, ops=built.ops())

    assert built.storage_admissions == 2
    assert "workflow" in built.events
    assert outcome.receipt["status"] == "blocked"
    assert any(
        "post-child fixture drift" in item
        for item in outcome.receipt["blockers"]
    )
    assert not outcome.lock_path.exists()
    assert outcome.receipt_path.is_file()


def test_authored_request_change_before_publication_fails_cleanly(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.mutate_request_on_first_admission = True
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    with pytest.raises(lifecycle.LifecycleError, match="Authored request changed"):
        lifecycle.run_attempt(built.request, ops=built.ops())
    assert not (built.built.run_root / "attempts" / identifier).exists()
    assert not (built.built.run_root / "locks" / "run.lock").exists()
    assert built.events[-1] == "release"


def test_attempt_directory_sync_failure_precedes_child_record_publication(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.fail_attempt_directory_sync = True
    identifier = str(built.request.attempt_record["workflow_attempt_id"])

    with pytest.raises(
        lifecycle.LifecycleError, match="attempt-directory sync failure"
    ):
        lifecycle.run_attempt(built.request, ops=built.ops())

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
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
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
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    built.inject_attempt_entry_after_lock = True
    with pytest.raises(lifecycle.LifecycleError, match="establish immutable"):
        lifecycle.run_attempt(built.request, ops=built.ops())
    assert "publish:locks/run.lock" in built.events
    assert built.events[-1] == "release"
    assert not (built.built.run_root / "locks" / "run.lock").exists()
    released = built.built.run_root / "locks" / f"released-{identifier}-run-lock.json"
    assert released.is_file()
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "blocked"
    assert any("retained aggregate lock" in value for value in observed.blockers)


def test_existing_lock_serializes_attempt_creation(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    lock = built.built.run_root / "locks" / "run.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    with pytest.raises(lifecycle.LifecycleError, match="Unexpected aggregate run lock"):
        lifecycle.run_attempt(built.request, ops=built.ops())
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
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
    retained = (
        built.built.run_root
        / "locks"
        / f"released-{identifier}-run-lock.json"
    )
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
        lifecycle.run_attempt(built.request, ops=built.ops())

    assert not (built.built.run_root / "locks" / "run.lock").exists()


def test_late_state_and_lock_namespace_drift_are_receipt_bound_blockers(
    tmp_path: Path,
) -> None:
    state_case = _build_harness(
        tmp_path / "state", result=lifecycle.WorkflowResult(7, None)
    )
    state_case.inject_state_entry_after_child = True
    state_outcome = lifecycle.run_attempt(state_case.request, ops=state_case.ops())
    assert state_outcome.receipt["status"] == "blocked"
    assert any(
        "Unexpected aggregate state path" in item
        for item in state_outcome.receipt["blockers"]
    )

    lock_case = _build_harness(
        tmp_path / "lock", result=lifecycle.WorkflowResult(7, None)
    )
    lock_case.inject_lock_entry_on_release = True
    lock_outcome = lifecycle.run_attempt(lock_case.request, ops=lock_case.ops())
    assert lock_outcome.receipt["status"] == "blocked"
    assert any(
        "Unexpected retained aggregate lock state" in item
        for item in lock_outcome.receipt["blockers"]
    )
    assert lock_outcome.receipt_path.is_file()


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
    ) -> None:
        evidence_path.write_bytes(expected)
        path.unlink()

    ops = lifecycle.LifecycleOps(
        run_workflow=defaults.run_workflow,
        publish_bytes=defaults.publish_bytes,
        release_lock=copied_release,
        now=defaults.now,
        host_name=defaults.host_name,
        process_id=defaults.process_id,
        process_is_alive=defaults.process_is_alive,
        validate_reporting_receipt=defaults.validate_reporting_receipt,
        admit_storage_context=defaults.admit_storage_context,
        admit_runtime_context=defaults.admit_runtime_context,
        sync_directory=defaults.sync_directory,
    )
    with pytest.raises(lifecycle.LifecycleError, match="descriptor identity"):
        lifecycle.run_attempt(built.request, ops=ops)
    identifier = str(built.request.attempt_record["workflow_attempt_id"])
    assert not (
        built.built.run_root / "attempts" / identifier / "attempt-receipt.json"
    ).exists()


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


def test_initial_and_resume_argv_never_contain_recovery_bypasses(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    initial = list(built.request.attempt_record["snakemake_argv"])
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

    record = copy.deepcopy(built.request.attempt_record)
    record["snakemake_argv"].insert(-2, "--unlock")
    with pytest.raises(
        orchestration_contracts.ContractValidationError, match="forbidden"
    ):
        orchestration_contracts.validate_record("workflow-attempt", record)


def test_inspection_parses_only_already_admitted_attempt_bytes() -> None:
    valid = orchestration_contracts.canonical_json_bytes(
        {
            "not": "a full record",
        }
    )
    with pytest.raises(inspection.InspectionError, match="Invalid workflow-attempt"):
        inspection._parse_attempt_path_bytes(valid, Path("/changed/attempt.json"))


def test_inspection_blocks_empty_or_foreign_attempt_state(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    empty = (
        built.built.run_root / "attempts" / ("workflow-20260812T170000Z-" + "a" * 32)
    )
    empty.mkdir()
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "blocked"
    assert any("no immutable attempt" in item for item in observed.blockers)


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

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "blocked"
    assert any("attempts root" in item for item in observed.blockers)

    with pytest.raises(lifecycle.LifecycleError, match="Aggregate attempt state"):
        lifecycle.run_attempt(built.request, ops=built.ops())
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

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "blocked"
    assert any(
        "Unexpected aggregate attempt state" in item for item in observed.blockers
    )
    assert any(
        "Unexpected workflow-attempt state" in item for item in observed.blockers
    )

    with pytest.raises(lifecycle.LifecycleError, match="Aggregate attempt state"):
        lifecycle.run_attempt(built.request, ops=built.ops())
    assert not any(event == "publish:locks/run.lock" for event in built.events)


def test_lying_runtime_authority_fails_before_mutation(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)

    def reject(
        _attempt: dict[str, Any],
        _request: lifecycle.LifecycleRequest,
        _storage_binding: doctor.RuntimeBinding | None,
    ) -> None:
        raise lifecycle.LifecycleError("declared checkout differs from observed")

    ops = built.ops()
    lying = lifecycle.LifecycleOps(
        run_workflow=ops.run_workflow,
        publish_bytes=ops.publish_bytes,
        release_lock=ops.release_lock,
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
        lifecycle.run_attempt(built.request, ops=lying)
    assert built.events == ["storage-admitted"]


def test_success_receipt_with_verified_subset_is_blocked_on_inspection(
    tmp_path: Path,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    receipt = orchestration_contracts.load_record(
        outcome.receipt_path, "attempt-receipt"
    )
    receipt["verified_tasks"] = receipt["verified_tasks"][:1]
    receipt.update(
        status="blocked",
        blockers=["fixture forged subset"],
        message="fixture forged subset",
        local_pipeline_complete=False,
    )
    outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(receipt)
    )
    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.results_status == "blocked"
    assert any("exact verified task" in item for item in observed.blockers)


def test_completed_run_refuses_rerun_and_resume(tmp_path: Path) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    lifecycle.run_attempt(built.request, ops=built.ops())
    with pytest.raises(lifecycle.LifecycleError, match="prior attempts"):
        lifecycle.run_attempt(built.request, ops=built.ops())

    first_id = str(built.request.attempt_record["workflow_attempt_id"])
    resume_id = "workflow-20260812T160000Z-" + "f" * 32
    config = _materialize_workflow_config(built.built, resume_id)
    argv = lifecycle.build_snakemake_argv(
        python_executable=built.request.python_executable,
        snakefile=built.request.snakefile,
        workflow_profile=built.request.workflow_profile,
        configfile=config,
        run_root=built.built.run_root,
        target="local_pipeline_slice",
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
    resumed = lifecycle.LifecycleRequest(
        run_root=built.request.run_root,
        execution_path=built.request.execution_path,
        profile_path=built.request.profile_path,
        workflow_config_path=config,
        snakefile=built.request.snakefile,
        python_executable=built.request.python_executable,
        workflow_profile=built.request.workflow_profile,
        target="local_pipeline_slice",
        operation="resume",
        attempt_record=attempt,
        request_source_path=built.request.request_source_path,
    )
    with pytest.raises(lifecycle.LifecycleError, match="Results are complete"):
        lifecycle.run_attempt(resumed, ops=built.ops())


def test_live_owned_incomplete_start_is_running_then_terminally_blocked(
    tmp_path: Path,
) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(9, None, "fixture stop")
    )
    built.inspect_live_transient = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())

    assert built.live_observation is not None
    assert built.live_observation.attempt_outcome == "running"
    assert not built.live_observation.recovery_available
    assert outcome.receipt["status"] == "blocked"
    assert len(outcome.receipt["task_start_records"]) == 1

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "blocked"


def test_task_start_crash_and_deletion_remain_blocked(tmp_path: Path) -> None:
    built = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(17, None, "fixture crash")
    )
    built.materialize_start_only = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "blocked"
    start = (
        built.built.run_root
        / outcome.receipt["task_start_records"][0]["record"]["path"]
    )
    start.unlink()

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.results_status == "blocked"
    assert any("task-start" in blocker for blocker in observed.blockers)


def test_reporting_start_without_completion_and_deleted_completion_block(
    tmp_path: Path,
) -> None:
    entered = _build_harness(
        tmp_path / "entered",
        result=lifecycle.WorkflowResult(19, None, "reporting crash"),
    )
    entered.materialize_reporting_start_only = True
    entered_outcome = lifecycle.run_attempt(entered.request, ops=entered.ops())
    assert entered_outcome.receipt["status"] == "blocked"
    assert (
        entered_outcome.receipt["reporting_completion_records"]["artifact_index"][
            "start"
        ]
        is not None
    )

    complete = _build_harness(tmp_path / "complete")
    complete.materialize_complete = True
    lifecycle.run_attempt(complete.request, ops=complete.ops())
    reporting_boundary.ledger_paths(
        complete.built.run_root, "html_report"
    ).verified.unlink()
    observed = inspection.inspect_run(
        complete.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            complete.validate_reporting,
        ),
    )
    assert observed.integrity == "valid"
    assert observed.attempt_outcome == "succeeded"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "blocked"
    assert not observed.recovery_available
    assert any("reporting ledger" in blocker for blocker in observed.blockers)


@pytest.mark.parametrize("tamper", ["extra", "deep", "symlink"])
def test_historical_task_tree_is_recursively_closed(
    tmp_path: Path,
    tamper: str,
) -> None:
    built = _build_harness(tmp_path)
    built.materialize_complete = True
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
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

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.integrity == "blocked"
    assert any("task" in blocker.lower() for blocker in observed.blockers)


def test_stable_file_reference_rejects_same_byte_replacement_during_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "stdout.log"
    payload = b"x" * (2 * 1024 * 1024 + 17)
    path.write_bytes(payload)
    original_state = path.stat(follow_symlinks=False)
    original_read = inspection.os.read
    replaced = False

    def replace_after_first_chunk(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        data = original_read(descriptor, size)
        state = os.fstat(descriptor)
        if (
            not replaced
            and data
            and (state.st_dev, state.st_ino)
            == (original_state.st_dev, original_state.st_ino)
        ):
            replaced = True
            path.rename(tmp_path / "original.log")
            path.write_bytes(payload)
        return data

    monkeypatch.setattr(inspection.os, "read", replace_after_first_chunk)

    with pytest.raises(inspection.InspectionError, match="changed while it was read"):
        inspection._stable_file_reference(path, tmp_path, "stdout log")
    assert replaced


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
    first_outcome = lifecycle.run_attempt(first.request, ops=first.ops())
    assert first_outcome.receipt["status"] == "failed"
    task_attempt = next(
        first_outcome.attempt_path.parent.glob("tasks/*/*/task-attempt.json")
    )
    stdout_path = task_attempt.with_name("stdout.log")
    stderr_path = task_attempt.with_name("stderr.log")
    log_paths = {stdout_path, stderr_path}
    chunk_lengths: dict[Path, list[int]] = {path: [] for path in log_paths}
    stable_calls: list[Path] = []
    original_consume = inspection._consume_stable_file
    original_read_bytes = inspection._read_bytes
    original_stable_reference = inspection._stable_file_reference

    def track_consume(
        path: Path,
        root: Path,
        label: str,
        consume: Callable[[bytes], object],
    ) -> None:
        def consume_chunk(chunk: bytes) -> object:
            if path in log_paths:
                chunk_lengths[path].append(len(chunk))
            return consume(chunk)

        original_consume(path, root, label, consume_chunk)

    def reject_full_log_read(path: Path, root: Path, label: str) -> bytes:
        if path in log_paths:
            raise AssertionError(f"task log was fully read: {label}")
        return original_read_bytes(path, root, label)

    def track_stable_reference(path: Path, root: Path, label: str) -> dict[str, str]:
        stable_calls.append(path)
        return original_stable_reference(path, root, label)

    monkeypatch.setattr(inspection, "_consume_stable_file", track_consume)
    monkeypatch.setattr(inspection, "_read_bytes", reject_full_log_read)
    monkeypatch.setattr(inspection, "_stable_file_reference", track_stable_reference)
    inspect_ops = inspection.InspectionOps(
        lambda: "fixture-host",
        lambda _pid: True,
        first.validate_reporting,
    )

    observed = inspection.inspect_run(first.built.run_root, ops=inspect_ops)
    assert observed.recovery_available
    assert stable_calls == [stdout_path, stderr_path]
    for path, expected_size in (
        (stdout_path, len(stdout_data)),
        (stderr_path, len(stderr_data)),
    ):
        assert sum(chunk_lengths[path]) == expected_size
        assert len(chunk_lengths[path]) > 2
        assert max(chunk_lengths[path]) <= 1024 * 1024

    stable_calls.clear()
    original_inspect_run = inspection.inspect_run
    resume_inspections: list[tuple[str, tuple[Path, ...]]] = []

    def track_inspect_run(
        run_root: Path,
        *,
        ops: inspection.InspectionOps | None = None,
        allowed_next_attempt: Mapping[str, Any] | None = None,
    ) -> inspection.RunInspection:
        before = len(stable_calls)
        result = original_inspect_run(
            run_root,
            ops=ops,
            allowed_next_attempt=allowed_next_attempt,
        )
        resume_inspections.append(
            (
                "under-lock" if allowed_next_attempt is not None else "outer",
                tuple(stable_calls[before:]),
            )
        )
        return result

    monkeypatch.setattr(inspection, "inspect_run", track_inspect_run)
    first_id = str(first.request.attempt_record["workflow_attempt_id"])
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

    second_outcome = lifecycle.run_attempt(first.request, ops=first.ops())
    assert second_outcome.receipt["status"] == "succeeded"
    expected_log_pass = (stdout_path, stderr_path)
    assert resume_inspections == [
        ("outer", expected_log_pass),
        ("under-lock", expected_log_pass),
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
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    task_root = outcome.attempt_path.parent / "tasks"
    log_path = next(task_root.glob(f"*/*/{file_name}"))
    if tamper == "append":
        with log_path.open("ab") as stream:
            stream.write(b"foreign log bytes\n")
    else:
        log_path.write_bytes(b"")

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.results_status == "blocked"
    assert any(
        "binds different" in blocker and file_name.split(".")[0] in blocker
        for blocker in observed.blockers
    )


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
    outcome = lifecycle.run_attempt(built.request, ops=built.ops())
    assert outcome.receipt["status"] == "failed"
    log_path = next(outcome.attempt_path.parent.glob(f"tasks/*/*/{file_name}"))
    if tamper == "append":
        with log_path.open("ab") as stream:
            stream.write(b"foreign log bytes\n")
    else:
        log_path.write_bytes(b"")

    observed = inspection.inspect_run(
        built.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            built.validate_reporting,
        ),
    )
    assert observed.results_status == "blocked"
    assert observed.recovery_available is False
    assert any(
        "binds different" in blocker and file_name.split(".")[0] in blocker
        for blocker in observed.blockers
    )


def test_preentry_failure_can_resume_into_later_verified_start(tmp_path: Path) -> None:
    first = _build_harness(
        tmp_path, result=lifecycle.WorkflowResult(23, None, "preentry failure")
    )
    first.materialize_preentry_failure = True
    first_outcome = lifecycle.run_attempt(first.request, ops=first.ops())
    assert first_outcome.receipt["status"] == "failed"
    assert len(first_outcome.receipt["preentry_task_attempt_records"]) == 1
    assert (
        inspection.inspect_run(
            first.built.run_root,
            ops=inspection.InspectionOps(
                lambda: "fixture-host",
                lambda _pid: True,
                first.validate_reporting,
            ),
        ).recovery_available
    )

    first_id = str(first.request.attempt_record["workflow_attempt_id"])
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
    second_outcome = lifecycle.run_attempt(first.request, ops=first.ops())
    assert second_outcome.receipt["status"] == "succeeded"
    assert len(second_outcome.receipt["preentry_task_attempt_records"]) == 1
    complete_observation = inspection.inspect_run(
        first.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            first.validate_reporting,
        ),
    )
    assert (
        complete_observation.integrity,
        complete_observation.attempt_outcome,
        complete_observation.results_status,
        complete_observation.reporting_status,
        complete_observation.recovery_available,
    ) == ("valid", "succeeded", "complete", "complete", False), (
        complete_observation.blockers
    )

    original_first_receipt = orchestration_contracts.load_record(
        first_outcome.receipt_path, "attempt-receipt"
    )
    omitted = copy.deepcopy(original_first_receipt)
    omitted["preentry_task_attempt_records"] = []
    first_outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(omitted)
    )
    omitted_observation = inspection.inspect_run(
        first.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            first.validate_reporting,
        ),
    )
    assert omitted_observation.results_status == "blocked"
    assert any(
        "cumulative preentry evidence" in blocker
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
        local_pipeline_complete=False,
        task_start_records=[second_outcome.receipt["task_start_records"][0]],
    )
    first_outcome.receipt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(forged)
    )
    forged_observation = inspection.inspect_run(
        first.built.run_root,
        ops=inspection.InspectionOps(
            lambda: "fixture-host",
            lambda _pid: True,
            first.validate_reporting,
        ),
    )
    assert forged_observation.integrity == "blocked"
    assert forged_observation.results_status == "blocked"
    assert any(
        "pre-binds future task-start" in blocker
        for blocker in forged_observation.blockers
    )
    assert any(
        "Superseded workflow attempt is not resumable" in blocker
        for blocker in forged_observation.blockers
    )
