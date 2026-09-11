"""Fixed immutable ledger contracts for reporting producer boundaries."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.run_coordinator import inspection, reporting_boundary
from emrys.orchestration.run_coordinator._inspection_evidence import (
    _inspect_reporting_ledger_with_locations,
)
from emrys.reporting import transaction_validation
from tests.orchestration.run_coordinator.fixtures import workflow as workflow_fixture

FIXED_TIME = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _SemanticResult:
    receipt_path: Path
    receipt_sha256: str


@dataclass(frozen=True, slots=True)
class _ReportSemanticResult:
    receipt_path: Path
    receipt_sha256: str
    verified_report_locations: tuple[tuple[str, Path], ...]


def _semantic_result(path: Path) -> _SemanticResult:
    return _SemanticResult(
        receipt_path=path,
        receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def test_default_inspection_reuses_only_current_reporting_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[Any] = []
    expected = _ReportSemanticResult(Path("/receipt.tsv"), "a" * 64, ())

    def validate(
        *_arguments: Any,
        validated_predecessor: Any = None,
        prepared_context: Any = None,
    ) -> Any:
        assert prepared_context is None
        observed.append(validated_predecessor)
        return expected

    monkeypatch.setattr(transaction_validation, "validate_receipt", validate)
    for _session in range(2):
        validator = inspection.default_inspection_ops().validate_reporting_receipt
        for kind in ("run_summary", "html_report"):
            assert (
                validator(kind, Path("/run/receipt.tsv"), tmp_path, {}, {}, {}, {})
                == expected
            )
    assert observed == [None, expected, None, expected]


def _reference(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _build(
    root: Path,
    *,
    terminal: bool = True,
) -> workflow_fixture.WorkflowFixture:
    built = workflow_fixture.build(root)
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path,
        "workflow-attempt",
    )
    run_lock = orchestration_contracts.run_lock_record(attempt)
    orchestration_contracts.validate_record("run-lock", run_lock)
    lock_path = built.run_root / "locks" / "run.lock"
    lock_path.parent.mkdir(exist_ok=True)
    lock_path.write_bytes(orchestration_contracts.canonical_json_bytes(run_lock))
    if terminal:
        _terminalize_attempt(built.run_root, built.workflow_attempt_path)
    return replace(
        built,
        execution=orchestration_contracts.load_json_object(
            built.run_root / "contract" / "run.json"
        ),
    )


def _terminalize_attempt(run_root: Path, attempt_path: Path) -> None:
    attempt = orchestration_contracts.load_record(
        attempt_path,
        "workflow-attempt",
    )
    lock_path = run_root / "locks" / "run.lock"
    lock_bytes = lock_path.read_bytes()
    released_path = attempt_path.with_name("released-run-lock.json")
    released_path.write_bytes(lock_bytes)
    lock_path.unlink()
    task_evidence = {
        "machine_key": "fixture-owner",
        "scope": {"scope_type": "analysis", "scope_id": "fixture"},
        "record": _reference(attempt_path, run_root),
    }
    terminal = {
        "schema_version": "emrys.attempt-receipt.v2",
        "run_id": attempt["run_id"],
        "execution_contract_sha256": attempt["execution_contract_sha256"],
        "profile_sha256": attempt["profile_sha256"],
        "workflow_attempt_id": attempt["workflow_attempt_id"],
        "attempt_record": _reference(attempt_path, run_root),
        "released_run_lock": _reference(released_path, run_root),
        "status": "succeeded",
        "finished_at": "2026-08-12T15:00:00Z",
        "snakemake_exit_code": 0,
        "termination_signal": None,
        "preentry_task_attempt_records": [],
        "task_start_records": [task_evidence],
        "verified_tasks": [task_evidence],
        "blockers": [],
        "message": None,
    }
    orchestration_contracts.validate_record("attempt-receipt", terminal)
    attempt_path.with_name("attempt-receipt.json").write_bytes(
        orchestration_contracts.canonical_json_bytes(terminal)
    )


def _identity_paths(
    built: workflow_fixture.WorkflowFixture,
) -> dict[str, Path]:
    return {
        "workflow_attempt_path": built.workflow_attempt_path,
    }


def _ops(validator: Any) -> reporting_boundary.ReportingBoundaryOps:
    return replace(
        reporting_boundary.DEFAULT_REPORTING_BOUNDARY_OPS,
        now=lambda: FIXED_TIME,
        validate_semantic_receipt=validator,
    )


def _publish_complete_summary_ledger(
    built: workflow_fixture.WorkflowFixture,
    *,
    validator: Any,
) -> reporting_boundary.ReportingBoundaryOps:
    ops = _ops(validator)
    reporting_boundary.publish_start(
        kind="run_summary",
        **_identity_paths(built),
        ops=ops,
    )
    built.run_summary.parent.mkdir(parents=True, exist_ok=True)
    built.run_summary.write_bytes(b"semantic artifact receipt\n")
    reporting_boundary.publish_verified(
        kind="run_summary",
        receipt_path=built.run_summary,
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
            kind="run_summary",
            **_identity_paths(built),
            ops=_ops(lambda *_arguments: _semantic_result(built.run_summary)),
        )


def test_bound_read_preserves_empty_and_canonical_file_semantics(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    empty = root / "empty"
    empty.write_bytes(b"")

    assert reporting_boundary._read_bound(empty, root, "empty input") == b""
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="Could not admit directory input",
    ):
        reporting_boundary._read_bound(root, root, "directory input")

    alias = root / "alias"
    alias.symlink_to(empty)
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="must be a canonical regular file",
    ):
        reporting_boundary._read_bound(alias, root, "alias input")


def test_start_and_completion_publish_fixed_closed_records(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    config_document = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )["workflow"]
    assert all(
        set(config_document[f"{name}_path"]) == {"path", "sha256"}
        for name in reporting_boundary.CONTRACT_PATHS
    )

    def validate(
        kind: str,
        receipt_path: Path,
        run_root: Path,
        execution: dict[str, Any],
        profile: dict[str, Any],
        attempt: dict[str, Any],
        config: dict[str, Any],
    ) -> _SemanticResult:
        assert kind == "run_summary"
        assert run_root == built.run_root
        assert execution == built.execution
        assert profile == built.profile
        assert attempt["workflow_attempt_id"] in str(built.workflow_attempt_path)
        assert config == config_document
        return _semantic_result(receipt_path)

    ops = _publish_complete_summary_ledger(built, validator=validate)
    paths = reporting_boundary.ledger_paths(built.run_root, "run_summary")
    assert paths.start == (
        built.run_root / "state" / "reporting" / "run_summary" / "start.json"
    )
    assert paths.verified == paths.start.with_name("verified.json")
    start = orchestration_contracts.load_record(paths.start, "reporting-start")
    verified = orchestration_contracts.load_record(
        paths.verified,
        "verified-reporting",
    )
    assert start["kind"] == verified["kind"] == "run_summary"
    assert _inspect_reporting_ledger_with_locations(
        built.run_root, built.execution, built.profile, validate
    )[1] == ["html_report reporting is absent after a verified transaction prefix"]
    assert (
        _inspect_reporting_ledger_with_locations(
            built.run_root,
            built.execution,
            built.profile,
            validate,
            allow_incomplete_origin=str(start["origin_workflow_attempt_id"]),
        )[1]
        == []
    )
    assert start["run_lock"] == {
        "path": (
            built.workflow_attempt_path.with_name("released-run-lock.json")
            .relative_to(built.run_root)
            .as_posix()
        ),
        "sha256": hashlib.sha256(
            built.workflow_attempt_path.with_name("released-run-lock.json").read_bytes()
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

    admitted = reporting_boundary.validate_verified(
        "run_summary",
        built.run_root,
        built.execution,
        built.profile,
        semantic_validator=ops.validate_semantic_receipt,
    )
    assert isinstance(admitted, reporting_boundary.ReportingLedgerAdmission)
    assert admitted == reporting_boundary.ReportingLedgerAdmission(
        origin_workflow_attempt_id=str(start["origin_workflow_attempt_id"]),
        start_reference=_reference(paths.start, built.run_root),
        verified_reference=_reference(paths.verified, built.run_root),
    )

    def mutate_start(*_arguments: Any) -> _SemanticResult:
        changed = orchestration_contracts.load_record(
            paths.start,
            "reporting-start",
        )
        changed["created_at"] = "2026-08-12T14:00:01Z"
        paths.start.write_bytes(orchestration_contracts.canonical_json_bytes(changed))
        return _semantic_result(built.run_summary)

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="changed during semantic validation",
    ):
        reporting_boundary.validate_verified(
            "run_summary",
            built.run_root,
            built.execution,
            built.profile,
            semantic_validator=mutate_start,
        )


def test_historical_reporting_state_is_rejected_without_mutation(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "artifact_index")
    ops = _publish_complete_summary_ledger(
        built, validator=lambda _kind, path, *_args: _semantic_result(path)
    )
    summary = reporting_boundary.ledger_paths(built.run_root, "run_summary")
    (built.reporting_root / "artifact_index").mkdir()
    retained = summary.start.read_bytes(), summary.verified.read_bytes()
    blockers = _inspect_reporting_ledger_with_locations(
        built.run_root,
        built.execution,
        built.profile,
        ops.validate_semantic_receipt,
    )[1]
    assert blockers
    assert retained == (summary.start.read_bytes(), summary.verified.read_bytes())


def test_current_boundary_uses_run_authority_and_exact_attempt_reference(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "current")
    identity = _identity_paths(built)
    config = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )["workflow"]
    assert all(
        set(config[f"{name}_path"]) == {"path", "sha256"}
        for name in reporting_boundary.CONTRACT_PATHS
    )

    reporting_boundary.publish_start(
        kind="run_summary",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(Path("/unused"))),
    )
    start = orchestration_contracts.load_record(
        reporting_boundary.ledger_paths(built.run_root, "run_summary").start,
        "reporting-start",
    )
    assert (
        start["execution_contract_sha256"]
        == hashlib.sha256(
            (built.run_root / "contract/run.json").read_bytes()
        ).hexdigest()
    )
    assert start["workflow_attempt"] == _reference(
        built.workflow_attempt_path, built.run_root
    )
    admitted = reporting_boundary.validate_start(
        "run_summary",
        built.run_root,
        orchestration_contracts.load_json_object(
            (built.run_root / "contract/run.json")
        ),
        orchestration_contracts.load_json_object(
            (built.run_root / "contract/profile.json")
        ),
    )
    assert admitted.origin_workflow_attempt_id == start["origin_workflow_attempt_id"]


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("path", "does not use its fixed path"),
        ("bytes", "bytes differ from workflow Attempt identity"),
    ),
)
def test_current_boundary_rejects_reporting_reference_tamper(
    tmp_path: Path,
    case: str,
    message: str,
) -> None:
    built = _build(tmp_path / case)
    identity = _identity_paths(built)
    config = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )["workflow"]
    if case == "path":
        config["reference_contract_path"]["path"] = "contract/other.json"
        attempt = orchestration_contracts.load_record(
            identity["workflow_attempt_path"],
            "workflow-attempt",
        )
        attempt["workflow"] = config
        identity["workflow_attempt_path"].write_bytes(
            orchestration_contracts.canonical_json_bytes(attempt)
        )
    else:
        inventory = built.run_root / config["artifact_inventory_path"]["path"]
        inventory.write_bytes(inventory.read_bytes() + b"tampered\n")

    with pytest.raises(reporting_boundary.ReportingBoundaryError, match=message):
        reporting_boundary.publish_start(
            kind="run_summary",
            **identity,
            ops=_ops(lambda *_arguments: _semantic_result(Path("/unused"))),
        )


def test_verified_boundary_carries_admitted_report_locations_unchanged(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    run_id = str(built.execution["run_id"])
    locations = (
        (
            "scientific-report-html",
            built.report_receipt.with_name(f"{run_id}.scientific_report.html"),
        ),
        (
            "evidence-report-html",
            built.report_receipt.with_name(f"{run_id}.evidence_report.html"),
        ),
    )

    def validate(*_arguments: Any) -> _ReportSemanticResult:
        return _ReportSemanticResult(
            receipt_path=built.report_receipt,
            receipt_sha256=hashlib.sha256(
                built.report_receipt.read_bytes()
            ).hexdigest(),
            verified_report_locations=locations,
        )

    ops = _ops(validate)
    reporting_boundary.publish_start(
        kind="html_report",
        **_identity_paths(built),
        ops=ops,
    )
    built.report_receipt.parent.mkdir(parents=True, exist_ok=True)
    built.report_receipt.write_bytes(b"semantic report receipt\n")
    reporting_boundary.publish_verified(
        kind="html_report",
        receipt_path=built.report_receipt,
        **_identity_paths(built),
        ops=ops,
    )
    admitted = reporting_boundary.validate_verified(
        "html_report",
        built.run_root,
        built.execution,
        built.profile,
        semantic_validator=validate,
    )
    assert isinstance(admitted, reporting_boundary.ReportingLedgerAdmission)
    assert admitted.verified_report_locations == locations


def test_only_html_semantic_results_require_verified_locations() -> None:
    summary = _SemanticResult(Path("/receipt.tsv"), "a" * 64)
    assert reporting_boundary._semantic_report_locations("run_summary", summary) == ()
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="lacks both exact verified result locations",
    ):
        reporting_boundary._semantic_report_locations("html_report", summary)


def test_boundary_rejects_wrong_attempt_identity(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
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
            kind="run_summary",
            **identity,
            ops=_ops(lambda *_arguments: _semantic_result(built.run_summary)),
        )


def test_boundary_attests_attempt_commit_and_projection_bytes(tmp_path: Path) -> None:
    wrong_commit = _build(tmp_path / "wrong-commit")
    wrong_attempt = orchestration_contracts.load_record(
        wrong_commit.workflow_attempt_path,
        "workflow-attempt",
    )
    wrong_attempt["installed_package"]["git_commit"] = "f" * 40
    wrong_commit.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(wrong_attempt)
    )
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="Installed package differs from the workflow attempt",
    ):
        reporting_boundary.publish_start(
            kind="run_summary",
            **_identity_paths(wrong_commit),
        )

    changed_projection = _build(tmp_path / "changed-projection")
    projection_path = (
        changed_projection.run_root
        / orchestration_contracts.load_record(
            changed_projection.workflow_attempt_path, "workflow-attempt"
        )["workflow"]["artifact_inventory_path"]["path"]
    )
    projection_path.write_bytes(projection_path.read_bytes() + b"mutated\n")
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="projection artifact_inventory bytes differ",
    ):
        reporting_boundary.publish_start(
            kind="run_summary",
            **_identity_paths(changed_projection),
            ops=_ops(
                lambda *_arguments: _semantic_result(changed_projection.run_summary)
            ),
        )


def test_completion_rechecks_projection_after_semantic_validation(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    reporting_boundary.publish_start(
        kind="run_summary",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(built.run_summary)),
    )
    built.run_summary.parent.mkdir(parents=True, exist_ok=True)
    built.run_summary.write_bytes(b"semantic artifact receipt\n")
    projection_path = (
        built.run_root
        / orchestration_contracts.load_record(
            built.workflow_attempt_path, "workflow-attempt"
        )["workflow"]["artifact_inventory_path"]["path"]
    )

    def mutate_projection(*_arguments: Any) -> _SemanticResult:
        result = _semantic_result(built.run_summary)
        projection_path.write_bytes(projection_path.read_bytes() + b"mutated\n")
        return result

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="projection artifact_inventory bytes differ",
    ):
        reporting_boundary.publish_verified(
            kind="run_summary",
            receipt_path=built.run_summary,
            **identity,
            ops=_ops(mutate_projection),
        )


def test_completion_guard_runs_after_validation_before_verified_publication(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    observed: list[str] = []

    def validate(*_arguments: Any) -> _SemanticResult:
        observed.append("semantic-validation")
        return _semantic_result(built.run_summary)

    ops = _ops(validate)
    reporting_boundary.publish_start(kind="run_summary", **identity, ops=ops)
    built.run_summary.parent.mkdir(parents=True, exist_ok=True)
    built.run_summary.write_bytes(b"semantic artifact receipt\n")
    verified = reporting_boundary.ledger_paths(built.run_root, "run_summary").verified

    def reject() -> None:
        observed.append("final-guard")
        assert not verified.exists()
        raise RuntimeError("source changed")

    with pytest.raises(RuntimeError, match="source changed"):
        reporting_boundary.publish_verified(
            kind="run_summary",
            receipt_path=built.run_summary,
            **identity,
            ops=ops,
            before_publication=reject,
        )

    assert observed == ["semantic-validation", "final-guard"]
    assert not verified.exists()


def test_new_reporting_ledger_directories_are_durably_linked(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    synchronized: list[Path] = []
    ops = replace(
        _ops(lambda *_arguments: _semantic_result(built.run_summary)),
        sync_directory=synchronized.append,
    )

    reporting_boundary.publish_start(
        kind="run_summary",
        **_identity_paths(built),
        ops=ops,
    )

    state = built.run_root / "state"
    reporting = state / "reporting"
    ledger = reporting / "run_summary"
    assert state.is_dir()
    assert synchronized == [
        state,
        built.run_root,
        reporting,
        state,
        ledger,
        reporting,
    ]


def test_start_rechecks_released_run_lock_immediately_before_publication(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    lock_path = built.workflow_attempt_path.with_name("released-run-lock.json")

    def mutate_lock() -> datetime:
        lock = orchestration_contracts.load_record(lock_path, "run-lock")
        lock["owner_token"] = "different-lock-owner"
        lock_path.write_bytes(orchestration_contracts.canonical_json_bytes(lock))
        return FIXED_TIME

    ops = replace(
        _ops(lambda *_arguments: _semantic_result(built.run_summary)),
        now=mutate_lock,
    )
    paths = reporting_boundary.ledger_paths(built.run_root, "run_summary")
    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="released run-lock evidence",
    ):
        reporting_boundary.publish_start(
            kind="run_summary",
            **_identity_paths(built),
            ops=ops,
        )
    assert not paths.start.exists()


def test_start_timestamp_cannot_predate_origin_attempt(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    paths = reporting_boundary.ledger_paths(built.run_root, "run_summary")
    ops = replace(
        _ops(lambda *_arguments: _semantic_result(built.run_summary)),
        now=lambda: datetime(2026, 8, 12, 11, 59, tzinfo=UTC),
    )

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="start timestamp precedes its workflow attempt",
    ):
        reporting_boundary.publish_start(
            kind="run_summary",
            **_identity_paths(built),
            ops=ops,
        )
    assert not paths.start.exists()


def test_completion_rejects_start_and_receipt_mutation(tmp_path: Path) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    reporting_boundary.publish_start(
        kind="run_summary",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(built.run_summary)),
    )
    built.run_summary.parent.mkdir(parents=True, exist_ok=True)
    built.run_summary.write_bytes(b"semantic artifact receipt\n")
    start_path = reporting_boundary.ledger_paths(
        built.run_root,
        "run_summary",
    ).start

    def mutate_start(*_arguments: Any) -> _SemanticResult:
        start = orchestration_contracts.load_record(start_path, "reporting-start")
        start["created_at"] = "2026-08-12T14:00:01Z"
        start_path.write_bytes(orchestration_contracts.canonical_json_bytes(start))
        return _semantic_result(built.run_summary)

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="start marker changed",
    ):
        reporting_boundary.publish_verified(
            kind="run_summary",
            receipt_path=built.run_summary,
            **identity,
            ops=_ops(mutate_start),
        )

    fresh = _build(tmp_path / "receipt-fixture")
    fresh_identity = _identity_paths(fresh)
    reporting_boundary.publish_start(
        kind="run_summary",
        **fresh_identity,
        ops=_ops(lambda *_arguments: _semantic_result(fresh.run_summary)),
    )
    fresh.run_summary.parent.mkdir(parents=True, exist_ok=True)
    fresh.run_summary.write_bytes(b"semantic artifact receipt\n")

    def mutate_receipt(*_arguments: Any) -> _SemanticResult:
        before = _semantic_result(fresh.run_summary)
        fresh.run_summary.write_bytes(b"mutated receipt\n")
        return before

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="different reporting receipt identity",
    ):
        reporting_boundary.publish_verified(
            kind="run_summary",
            receipt_path=fresh.run_summary,
            **fresh_identity,
            ops=_ops(mutate_receipt),
        )


def test_incomplete_start_and_concurrent_publication_fail_closed(
    tmp_path: Path,
) -> None:
    built = _build(tmp_path / "fixture")
    identity = _identity_paths(built)
    reporting_boundary.publish_start(
        kind="run_summary",
        **identity,
        ops=_ops(lambda *_arguments: _semantic_result(built.run_summary)),
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

    with pytest.raises(
        reporting_boundary.ReportingBoundaryError,
        match="start marker already exists",
    ):
        reporting_boundary.publish_start(
            kind="run_summary",
            **identity,
            ops=_ops(lambda *_arguments: _semantic_result(built.run_summary)),
        )


def test_private_reporting_boundary_cli_is_retired() -> None:
    assert not hasattr(reporting_boundary, "configure_parser")
    assert not hasattr(reporting_boundary, "main")
