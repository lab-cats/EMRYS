"""Fixed immutable ledger contracts for reporting producer boundaries."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.local_pilot import reporting_boundary
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture

FIXED_TIME = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _SemanticResult:
    receipt_path: Path
    receipt_sha256: str


def _semantic_result(path: Path) -> _SemanticResult:
    return _SemanticResult(
        receipt_path=path,
        receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _reference(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _build(root: Path) -> workflow_fixture.WorkflowFixture:
    built = workflow_fixture.build(root)
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path,
        "workflow-attempt",
    )
    identifier = str(attempt["workflow_attempt_id"])
    run_lock = {
        "schema_version": "emrys.run-lock.v1",
        "run_id": attempt["run_id"],
        "workflow_attempt_id": identifier,
        "attempt_record_path": f"attempts/{identifier}/attempt.json",
        "owner_token": attempt["owner_token"],
        "process_id": attempt["process_id"],
        "host": attempt["host"],
        "created_at": attempt["created_at"],
    }
    orchestration_contracts.validate_record("run-lock", run_lock)
    lock_path = built.run_root / "locks" / "run.lock"
    lock_path.parent.mkdir(exist_ok=True)
    lock_path.write_bytes(orchestration_contracts.canonical_json_bytes(run_lock))
    return built


def _terminalize_run_lock(built: workflow_fixture.WorkflowFixture) -> None:
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path,
        "workflow-attempt",
    )
    lock_path = built.run_root / "locks" / "run.lock"
    lock_bytes = lock_path.read_bytes()
    released_path = built.workflow_attempt_path.with_name("released-run-lock.json")
    released_path.write_bytes(lock_bytes)
    lock_path.unlink()
    reporting: dict[str, dict[str, dict[str, str] | None]] = {}
    for kind in reporting_boundary.REPORTING_KINDS:
        paths = reporting_boundary.ledger_paths(built.run_root, kind)
        reporting[kind] = {
            "start": _reference(paths.start, built.run_root)
            if paths.start.is_file()
            else None,
            "verified": _reference(paths.verified, built.run_root)
            if paths.verified.is_file()
            else None,
        }
    terminal = {
        "schema_version": "emrys.attempt-receipt.v1",
        "run_id": attempt["run_id"],
        "execution_contract_sha256": attempt["execution_contract_sha256"],
        "profile_sha256": attempt["profile_sha256"],
        "workflow_attempt_id": attempt["workflow_attempt_id"],
        "attempt_record": _reference(built.workflow_attempt_path, built.run_root),
        "released_run_lock": _reference(released_path, built.run_root),
        "status": "blocked",
        "finished_at": "2026-08-12T15:00:00Z",
        "snakemake_exit_code": None,
        "termination_signal": None,
        "preentry_task_attempt_records": [],
        "task_start_records": [],
        "verified_tasks": [],
        "reporting_completion_records": reporting,
        "blockers": ["fixture terminalization"],
        "message": "fixture terminalization",
        "local_pipeline_complete": False,
    }
    orchestration_contracts.validate_record("attempt-receipt", terminal)
    built.workflow_attempt_path.with_name("attempt-receipt.json").write_bytes(
        orchestration_contracts.canonical_json_bytes(terminal)
    )


def _identity_paths(
    built: workflow_fixture.WorkflowFixture,
) -> dict[str, Path]:
    return {
        "run_root": built.run_root,
        "execution_path": built.run_root / "contract" / "normalized.json",
        "profile_path": built.run_root / "contract" / "profile.json",
        "workflow_attempt_path": built.workflow_attempt_path,
        "workflow_config_path": built.config_path,
    }


def _attest_fixture_source_checkout(**kwargs: Any) -> tuple[Path, str]:
    return Path(kwargs["root"]), str(kwargs["expected_commit"])


def _ops(validator: Any) -> reporting_boundary.ReportingBoundaryOps:
    return replace(
        reporting_boundary.DEFAULT_REPORTING_BOUNDARY_OPS,
        now=lambda: FIXED_TIME,
        validate_semantic_receipt=validator,
        attest_source_checkout=_attest_fixture_source_checkout,
    )


def _publish_complete_artifact_ledger(
    built: workflow_fixture.WorkflowFixture,
    *,
    validator: Any,
) -> reporting_boundary.ReportingBoundaryOps:
    ops = _ops(validator)
    reporting_boundary.publish_start(
        kind="artifact_index",
        **_identity_paths(built),
        ops=ops,
    )
    built.artifact_receipt.parent.mkdir(parents=True, exist_ok=True)
    built.artifact_receipt.write_bytes(b"semantic artifact receipt\n")
    reporting_boundary.publish_verified(
        kind="artifact_index",
        receipt_path=built.artifact_receipt,
        **_identity_paths(built),
        ops=ops,
    )
    return ops


def test_shared_record_admission_preserves_reporting_error_boundary(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    profile_path = built.run_root / "contract" / "profile.json"
    profile_path.write_bytes(b" " + profile_path.read_bytes())

    with pytest.raises(reporting_boundary.ReportingBoundaryError):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **_identity_paths(built),
            ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        )


def test_start_and_completion_publish_fixed_closed_records(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")

    def validate(
        kind: str,
        receipt_path: Path,
        run_root: Path,
        execution: dict[str, Any],
        profile: dict[str, Any],
        attempt: dict[str, Any],
    ) -> _SemanticResult:
        assert kind == "artifact_index"
        assert run_root == built.run_root
        assert execution == built.execution
        assert profile == built.profile
        assert attempt["workflow_attempt_id"] in str(built.workflow_attempt_path)
        return _semantic_result(receipt_path)

    ops = _publish_complete_artifact_ledger(built, validator=validate)
    paths = reporting_boundary.ledger_paths(built.run_root, "artifact_index")
    assert paths.start == (
        built.run_root / "state" / "reporting" / "artifact_index" / "start.json"
    )
    assert paths.verified == paths.start.with_name("verified.json")
    start = orchestration_contracts.load_record(paths.start, "reporting-start")
    verified = orchestration_contracts.load_record(
        paths.verified,
        "verified-reporting",
    )
    assert start["kind"] == verified["kind"] == "artifact_index"
    assert start["run_lock"] == {
        "path": (
            built.workflow_attempt_path.with_name("released-run-lock.json")
            .relative_to(built.run_root)
            .as_posix()
        ),
        "sha256": hashlib.sha256(
            (built.run_root / "locks" / "run.lock").read_bytes()
        ).hexdigest(),
    }
    assert verified["reporting_start"] == {
        "path": paths.start.relative_to(built.run_root).as_posix(),
        "sha256": hashlib.sha256(paths.start.read_bytes()).hexdigest(),
    }
    assert paths.start.read_bytes() == orchestration_contracts.canonical_json_bytes(
        start
    )
    assert paths.verified.read_bytes() == (
        orchestration_contracts.canonical_json_bytes(verified)
    )

    _terminalize_run_lock(built)
    observed = reporting_boundary.validate_verified(
        "artifact_index",
        built.run_root,
        built.execution,
        built.profile,
        semantic_validator=ops.validate_semantic_receipt,
    )
    assert observed.semantic_receipt_path == built.artifact_receipt

    def mutate_start(*_arguments: Any) -> _SemanticResult:
        changed = orchestration_contracts.load_record(
            paths.start,
            "reporting-start",
        )
        changed["created_at"] = "2026-08-12T14:00:01Z"
        paths.start.write_bytes(orchestration_contracts.canonical_json_bytes(changed))
        return _semantic_result(built.artifact_receipt)

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="changed during semantic validation",
    ):
        reporting_boundary.validate_verified(
            "artifact_index",
            built.run_root,
            built.execution,
            built.profile,
            semantic_validator=mutate_start,
        )


def test_boundary_rejects_wrong_identity_and_nonfixed_paths(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    wrong_execution = built.run_root / "contract" / "execution-copy.json"
    wrong_execution.write_bytes(
        (built.run_root / "contract" / "normalized.json").read_bytes()
    )
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="fixed execution/profile",
    ):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **{**identity, "execution_path": wrong_execution},
            ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        )

    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path,
        "workflow-attempt",
    )
    attempt["run_id"] = "run-" + "f" * 64
    built.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(attempt)
    )
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="does not bind reporting run_id",
    ):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **identity,
            ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        )


def test_boundary_attests_attempt_commit_and_projection_bytes(tmp_path: Path) -> None:
    wrong_commit = _build(tmp_path / "wrong-commit")
    wrong_attempt = orchestration_contracts.load_record(
        wrong_commit.workflow_attempt_path,
        "workflow-attempt",
    )
    wrong_attempt["source_checkout"]["commit"] = "f" * 40
    wrong_commit.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(wrong_attempt)
    )
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="Source checkout HEAD differs from the workflow attempt commit",
    ):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **_identity_paths(wrong_commit),
        )

    changed_projection = _build(tmp_path / "changed-projection")
    projection_path = (
        changed_projection.run_root / "contract" / "artifact_inventory.tsv"
    )
    projection_path.write_bytes(projection_path.read_bytes() + b"mutated\n")
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="projection artifact_inventory bytes differ",
    ):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **_identity_paths(changed_projection),
            ops=_ops(
                lambda *_arguments: _semantic_result(
                    changed_projection.artifact_receipt
                )
            ),
        )


def test_completion_rechecks_projection_after_semantic_validation(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    reporting_boundary.publish_start(
        kind="artifact_index",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
    )
    built.artifact_receipt.parent.mkdir(parents=True, exist_ok=True)
    built.artifact_receipt.write_bytes(b"semantic artifact receipt\n")
    projection_path = built.run_root / "contract" / "artifact_inventory.tsv"

    def mutate_projection(*_arguments: Any) -> _SemanticResult:
        result = _semantic_result(built.artifact_receipt)
        projection_path.write_bytes(projection_path.read_bytes() + b"mutated\n")
        return result

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="projection artifact_inventory bytes differ",
    ):
        reporting_boundary.publish_verified(
            kind="artifact_index",
            receipt_path=built.artifact_receipt,
            **identity,
            ops=_ops(mutate_projection),
        )


def test_new_reporting_ledger_directories_are_durably_linked(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    synchronized: list[Path] = []
    ops = replace(
        _ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        sync_directory=synchronized.append,
    )

    reporting_boundary.publish_start(
        kind="artifact_index",
        **_identity_paths(built),
        ops=ops,
    )

    state = built.run_root / "state"
    reporting = state / "reporting"
    ledger = reporting / "artifact_index"
    assert state.is_dir()
    assert synchronized == [
        state,
        built.run_root,
        reporting,
        state,
        ledger,
        reporting,
    ]


def test_start_rechecks_active_run_lock_immediately_before_publication(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    lock_path = built.run_root / "locks" / "run.lock"

    def mutate_lock() -> datetime:
        lock = orchestration_contracts.load_record(lock_path, "run-lock")
        lock["owner_token"] = "different-lock-owner"
        lock_path.write_bytes(orchestration_contracts.canonical_json_bytes(lock))
        return FIXED_TIME

    ops = replace(
        _ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        now=mutate_lock,
    )
    paths = reporting_boundary.ledger_paths(built.run_root, "artifact_index")
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="Run-lock evidence disagrees.*owner_token",
    ):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **_identity_paths(built),
            ops=ops,
        )
    assert not paths.start.exists()


def test_start_timestamp_cannot_predate_origin_attempt(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    paths = reporting_boundary.ledger_paths(built.run_root, "artifact_index")
    ops = replace(
        _ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        now=lambda: datetime(2026, 8, 12, 11, 59, tzinfo=UTC),
    )

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="start timestamp precedes its workflow attempt",
    ):
        reporting_boundary.publish_start(
            kind="artifact_index",
            **_identity_paths(built),
            ops=ops,
        )
    assert not paths.start.exists()


def test_completion_rejects_start_and_receipt_mutation(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    reporting_boundary.publish_start(
        kind="artifact_index",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
    )
    built.artifact_receipt.parent.mkdir(parents=True, exist_ok=True)
    built.artifact_receipt.write_bytes(b"semantic artifact receipt\n")
    start_path = reporting_boundary.ledger_paths(
        built.run_root,
        "artifact_index",
    ).start

    def mutate_start(*_arguments: Any) -> _SemanticResult:
        start = orchestration_contracts.load_record(start_path, "reporting-start")
        start["created_at"] = "2026-08-12T14:00:01Z"
        start_path.write_bytes(orchestration_contracts.canonical_json_bytes(start))
        return _semantic_result(built.artifact_receipt)

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="start marker changed",
    ):
        reporting_boundary.publish_verified(
            kind="artifact_index",
            receipt_path=built.artifact_receipt,
            **identity,
            ops=_ops(mutate_start),
        )

    fresh = _build(tmp_path / "receipt-fixture")
    fresh_identity = _identity_paths(fresh)
    reporting_boundary.publish_start(
        kind="artifact_index",
        **fresh_identity,
        ops=_ops(lambda *_arguments: _semantic_result(fresh.artifact_receipt)),
    )
    fresh.artifact_receipt.parent.mkdir(parents=True, exist_ok=True)
    fresh.artifact_receipt.write_bytes(b"semantic artifact receipt\n")

    def mutate_receipt(*_arguments: Any) -> _SemanticResult:
        before = _semantic_result(fresh.artifact_receipt)
        fresh.artifact_receipt.write_bytes(b"mutated receipt\n")
        return before

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="different reporting receipt identity",
    ):
        reporting_boundary.publish_verified(
            kind="artifact_index",
            receipt_path=fresh.artifact_receipt,
            **fresh_identity,
            ops=_ops(mutate_receipt),
        )


def test_incomplete_start_and_terminal_origin_fail_closed(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    reporting_boundary.publish_start(
        kind="run_summary",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
    )
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="verified.json",
    ):
        reporting_boundary.validate_verified(
            "run_summary",
            built.run_root,
            built.execution,
            built.profile,
        )

    unexpected = (
        reporting_boundary.ledger_paths(
            built.run_root,
            "run_summary",
        ).root
        / ".foreign-stage"
    )
    unexpected.write_text("foreign\n", encoding="utf-8")
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="unexpected state",
    ):
        reporting_boundary.validate_start(
            "run_summary",
            built.run_root,
            built.execution,
            built.profile,
        )
    unexpected.unlink()

    _terminalize_run_lock(built)
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="terminal workflow attempt",
    ):
        reporting_boundary.publish_start(
            kind="html_report",
            **identity,
            ops=_ops(lambda *_arguments: _semantic_result(built.artifact_receipt)),
        )


def test_cli_contract_requires_fixed_identity_and_receipt(capsys: Any) -> None:
    with pytest.raises(SystemExit) as exc:
        reporting_boundary.main(["complete", "--kind", "artifact_index"])
    assert exc.value.code == 2
    assert "--receipt" in capsys.readouterr().err
