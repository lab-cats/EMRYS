"""Focused tests for the terminal reporting operation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from emrys.orchestration.local_pilot import reporting_operation


def _state(
    root: Path,
    *,
    receipt_version: str = "emrys.attempt-receipt.v2",
    reporting_status: str = "incomplete",
    records: dict[str, dict[str, object | None]] | None = None,
) -> SimpleNamespace:
    attempt = {
        "workflow_attempt_id": "workflow-20260812T120000Z-" + "a" * 32,
        "workflow_config": {
            "path": "contract/workflow-configs/attempt.json",
            "sha256": "a" * 64,
        },
    }
    return SimpleNamespace(
        run_root=root,
        authority=object(),
        integrity="valid",
        attempt_outcome="succeeded",
        results_status="complete",
        latest_attempt=attempt,
        latest_receipt={"schema_version": receipt_version, "status": "succeeded"},
        reporting_status=reporting_status,
        reporting_completion_records=records
        or {
            kind: {"start": None, "verified": None}
            for kind in ("artifact_index", "run_summary", "html_report")
        },
        verified_report_locations=(),
        processing_source=None,
    )


def _identity(root: Path, state: SimpleNamespace) -> SimpleNamespace:
    identifier = state.latest_attempt["workflow_attempt_id"]
    return SimpleNamespace(
        root=root,
        execution={"run_id": root.name},
        profile={
            "artifact_templates": [
                {"source_path_template": "products/native/reference/output"}
            ]
        },
        attempt={
            **state.latest_attempt,
            "source_checkout": {"path": str(root.parent), "commit": "b" * 40},
        },
        config={
            "reporting_run_contract_path": {
                "path": f"contract/reporting-inputs/{identifier}/run.json",
                "sha256": "c" * 64,
            },
            "artifact_inventory_path": {
                "path": f"contract/reporting-inputs/{identifier}/inventory.tsv",
                "sha256": "d" * 64,
            },
        },
    )


def _install_admission(
    monkeypatch: pytest.MonkeyPatch,
    state: SimpleNamespace,
    identity: SimpleNamespace,
) -> None:
    monkeypatch.setattr(
        reporting_operation.inspection, "inspect_run", lambda _root: state
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "_admit_identity",
        lambda **_kwargs: identity,
    )


def _processing_source(
    tmp_path: Path,
    *,
    relocate_reference: bool = False,
    validation_sha256: str = "b" * 64,
) -> tuple[SimpleNamespace, SimpleNamespace]:
    source_root = (tmp_path / "source").resolve()
    output = source_root / "output.bam"
    validation = source_root / "validation.tsv"
    reference = (tmp_path / "source-reference.fa").resolve()
    prepared_reference = (
        (tmp_path / "relocated-reference.fa").resolve()
        if relocate_reference
        else reference
    )
    source = SimpleNamespace(
        root=source_root,
        binding={"source_run_id": "source-run"},
        state=SimpleNamespace(
            tasks=(
                SimpleNamespace(
                    record={
                        "inputs": [
                            {
                                "path": str(reference),
                                "size_bytes": 11,
                                "sha256": "c" * 64,
                            }
                        ],
                        "outputs": [
                            {
                                "path": str(output),
                                "size_bytes": 17,
                                "sha256": "a" * 64,
                            }
                        ],
                        "validation_report": {
                            "path": "validation.tsv",
                            "sha256": "b" * 64,
                        },
                        "native_receipt": None,
                    }
                ),
            )
        ),
        artifact_snapshots=(
            {"path": str(output), "size_bytes": 17, "sha256": "a" * 64},
        ),
    )
    context = SimpleNamespace(
        analysis_module=object(),
        inspections=tuple(
            SimpleNamespace(
                row={"step_id": "00c"},
                resolved_path=path,
                snapshot=SimpleNamespace(
                    status="present", size_bytes=size, sha256=sha256
                ),
            )
            for path, size, sha256 in (
                (output, 17, "a" * 64),
                (validation, 23, validation_sha256),
                (prepared_reference, 11, "c" * 64),
            )
        )
    )
    return source, context


def test_fixed_arguments_carry_the_admitted_analysis_policy(tmp_path: Path) -> None:
    root = (tmp_path / "run").resolve()
    state = _state(root)
    identity = _identity(root, state)
    relative = "contract/reporting-inputs/attempt/primary-analysis-policy.json"
    identity.config["primary_analysis_policy_path"] = {
        "path": relative,
        "sha256": "e" * 64,
    }

    artifact = reporting_operation._arguments(identity, "artifact_index")
    summary = reporting_operation._arguments(identity, "run_summary")

    assert artifact.analysis_policy == root / relative
    assert artifact.profile is identity.profile
    assert summary.analysis_policy == root / relative


def test_complete_historical_reporting_is_reused_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run").resolve()
    root.mkdir()
    locations = (("scientific-report-html", root / "scientific.html"),)
    state = _state(
        root,
        receipt_version="emrys.attempt-receipt.v1",
        reporting_status="complete",
    )
    state.verified_report_locations = locations
    monkeypatch.setattr(
        reporting_operation.inspection, "inspect_run", lambda _root: state
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "_admit_identity",
        lambda **_kwargs: pytest.fail("validated reuse must not enter publication"),
    )

    outcome = reporting_operation.run_reporting(root, execute=True)

    assert outcome.status == "reused"
    assert outcome.verified_report_locations == locations


@pytest.mark.parametrize("execute", (False, True))
def test_processing_only_run_refuses_reporting_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    execute: bool,
) -> None:
    root = (tmp_path / "run-processing-only").resolve()
    root.mkdir()
    state = _state(root, reporting_status="not applicable")
    monkeypatch.setattr(
        reporting_operation.inspection,
        "inspect_run",
        lambda _root: state,
    )
    monkeypatch.setattr(
        reporting_operation,
        "_prepare_transaction",
        lambda *_args: pytest.fail("processing-only Run entered a report producer"),
    )
    before = tuple(root.rglob("*"))

    with pytest.raises(
        reporting_operation.ReportingOperationError,
        match="not applicable to this partial scientific Run",
    ):
        reporting_operation.run_reporting(root, execute=execute)

    assert tuple(root.rglob("*")) == before


def test_dry_run_validates_first_producer_without_publishing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = (tmp_path / "run-dry").resolve()
    root.mkdir()
    state = _state(root)
    identity = _identity(root, state)
    _install_admission(monkeypatch, state, identity)
    observed: list[str] = []

    def prepare(kind: str, _arguments: Any) -> object:
        observed.append(kind)
        return object()

    monkeypatch.setattr(reporting_operation, "_prepare_transaction", prepare)
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_start",
        lambda **_kwargs: pytest.fail("dry-run must not publish"),
    )

    outcome = reporting_operation.run_reporting(root, execute=False)

    assert outcome.status == "planned"
    assert outcome.verified_report_locations == ()
    assert observed == ["artifact_index"]
    assert capsys.readouterr() == ("", "")


def test_processing_source_mismatch_fails_before_reporting_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run-source-mismatch").resolve()
    root.mkdir()
    source, context = _processing_source(tmp_path, validation_sha256="d" * 64)
    state = _state(root)
    state.processing_source = source
    identity = _identity(root, state)
    _install_admission(monkeypatch, state, identity)
    monkeypatch.setattr(
        reporting_operation,
        "_prepare_transaction",
        lambda *_args, **_kwargs: context,
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_start",
        lambda **_kwargs: pytest.fail("mismatched source published a start"),
    )

    with pytest.raises(
        reporting_operation.ReportingOperationError,
        match="Prepared artifact index differs from processing source",
    ):
        reporting_operation.run_reporting(root, execute=True)


def test_execute_prepares_and_publishes_each_fixed_transaction_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run-execute").resolve()
    root.mkdir()
    initial = _state(root)
    source, context = _processing_source(tmp_path, relocate_reference=True)
    initial.processing_source = source
    locations = (
        ("scientific-report-html", root / "results" / "scientific.html"),
        ("evidence-report-html", root / "results" / "evidence.html"),
    )
    monkeypatch.setattr(
        reporting_operation.inspection,
        "inspect_run",
        lambda _root: initial,
    )
    identity = _identity(root, initial)
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "_admit_identity",
        lambda **_kwargs: identity,
    )
    observed: list[str] = []
    preparations: dict[str, int] = {}

    def prepare(
        kind: str,
        _arguments: Any,
        *,
        analysis_module: object | None,
    ) -> object:
        assert analysis_module is (
            None if kind == "artifact_index" else context.analysis_module
        )
        preparations[kind] = preparations.get(kind, 0) + 1
        observed.append(f"prepare:{kind}:{preparations[kind]}")
        return context if kind == "artifact_index" else object()

    def publish(kind: str, _context: object) -> Path:
        observed.append(f"publish:{kind}")
        return root / f"{kind}.receipt"

    def start(*, kind: str, **_kwargs: Any) -> None:
        observed.append(f"start:{kind}")

    def verified(
        *, kind: str, before_publication: Any = None, **_kwargs: Any
    ) -> tuple[tuple[str, Path], ...]:
        if before_publication is not None:
            before_publication()
        observed.append(f"verified:{kind}")
        return locations if kind == "html_report" else ()

    def admit_source(*_args: Any) -> SimpleNamespace:
        observed.append("recheck:artifact_index")
        return source

    monkeypatch.setattr(reporting_operation, "_prepare_transaction", prepare)
    monkeypatch.setattr(reporting_operation, "_publish_prepared", publish)
    monkeypatch.setattr(reporting_operation.reporting_boundary, "publish_start", start)
    monkeypatch.setattr(
        reporting_operation.inspection,
        "admit_bound_processing_source",
        admit_source,
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_verified",
        verified,
    )

    outcome = reporting_operation.run_reporting(root, execute=True)

    assert outcome.status == "generated"
    assert outcome.verified_report_locations == locations
    assert observed == [
        "prepare:artifact_index:1",
        "start:artifact_index",
        "publish:artifact_index",
        "recheck:artifact_index",
        "verified:artifact_index",
        "prepare:run_summary:1",
        "start:run_summary",
        "publish:run_summary",
        "verified:run_summary",
        "prepare:html_report:1",
        "start:html_report",
        "publish:html_report",
        "verified:html_report",
    ]


def test_generation_observer_runs_only_after_first_published_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run-observed").resolve()
    root.mkdir()
    initial = _state(root)
    monkeypatch.setattr(
        reporting_operation.inspection,
        "inspect_run",
        lambda _root: initial,
    )
    identity = _identity(root, initial)
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "_admit_identity",
        lambda **_kwargs: identity,
    )
    observed: list[str] = []
    preparations: dict[str, int] = {}
    module = object()

    def prepare(
        kind: str,
        _arguments: Any,
        *,
        analysis_module: object | None,
    ) -> object:
        assert analysis_module is (None if kind == "artifact_index" else module)
        preparations[kind] = preparations.get(kind, 0) + 1
        observed.append(f"prepare:{kind}:{preparations[kind]}")
        return (
            SimpleNamespace(analysis_module=module)
            if kind == "artifact_index"
            else object()
        )

    def publish(kind: str, _context: object) -> Path:
        observed.append(f"publish:{kind}")
        return root / f"{kind}.receipt"

    monkeypatch.setattr(reporting_operation, "_prepare_transaction", prepare)
    monkeypatch.setattr(reporting_operation, "_publish_prepared", publish)
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_start",
        lambda *, kind, **_kwargs: observed.append(f"start:{kind}"),
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_verified",
        lambda **_kwargs: (),
    )

    outcome = reporting_operation.run_reporting(
        root,
        execute=True,
        observe_generation_start=lambda: observed.append("observed"),
    )

    assert outcome.status == "generated"
    assert observed.count("observed") == 1
    assert observed.index("start:artifact_index") < observed.index("observed")
    assert observed.index("observed") < observed.index("publish:artifact_index")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("integrity", "blocked", "Run integrity is blocked"),
        ("attempt_outcome", "blocked", "requires a successful Attempt"),
        ("results_status", "blocked", "requires a successful Attempt"),
    ),
)
def test_generation_rejects_blocked_scientific_state_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    message: str,
) -> None:
    root = (tmp_path / field).resolve()
    root.mkdir()
    initial = _state(root)
    setattr(initial, field, value)
    monkeypatch.setattr(
        reporting_operation.inspection,
        "inspect_run",
        lambda _root: initial,
    )

    with pytest.raises(reporting_operation.ReportingOperationError, match=message):
        reporting_operation.run_reporting(root, execute=True)


@pytest.mark.parametrize(
    ("version", "records", "message"),
    (
        (
            "emrys.attempt-receipt.v1",
            None,
            "supported only for v2 Attempt receipts",
        ),
        (
            "emrys.attempt-receipt.v2",
            {
                "artifact_index": {"start": {"path": "start"}, "verified": None},
                "run_summary": {"start": None, "verified": None},
                "html_report": {"start": None, "verified": None},
            },
            "Reporting state is blocked",
        ),
    ),
)
def test_generation_rejects_historical_or_partial_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: str,
    records: dict[str, dict[str, object | None]] | None,
    message: str,
) -> None:
    root = (tmp_path / version).resolve()
    root.mkdir()
    state = _state(root, receipt_version=version, records=records)
    if records is not None:
        state.reporting_status = "blocked"
    monkeypatch.setattr(
        reporting_operation.inspection, "inspect_run", lambda _root: state
    )
    if version == "emrys.attempt-receipt.v1":
        monkeypatch.setattr(
            reporting_operation.reporting_boundary,
            "_admit_identity",
            lambda **_kwargs: (_ for _ in ()).throw(
                reporting_operation.reporting_boundary.ReportingBoundaryError(
                    "New reporting generation is supported only for v2 Attempt receipts"
                )
            ),
        )

    with pytest.raises(reporting_operation.ReportingOperationError, match=message):
        reporting_operation.run_reporting(root, execute=False)


def test_generation_rejects_nonempty_or_symlink_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run-output").resolve()
    root.mkdir()
    state = _state(root)
    identity = _identity(root, state)
    _install_admission(monkeypatch, state, identity)
    output = root / "products" / "artifact-summary" / root.name
    output.parent.mkdir(parents=True)
    target = tmp_path / "foreign"
    target.mkdir()
    output.symlink_to(target, target_is_directory=True)

    with pytest.raises(
        reporting_operation.ReportingOperationError,
        match="absent or use only real directories",
    ):
        reporting_operation.run_reporting(root, execute=False)


@pytest.mark.parametrize("output_kind", ("artifact", "report"))
def test_generation_rejects_symlinked_output_ancestor_before_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output_kind: str,
) -> None:
    root = (tmp_path / f"run-{output_kind}").resolve()
    root.mkdir()
    state = _state(root)
    identity = _identity(root, state)
    _install_admission(monkeypatch, state, identity)
    ancestor = (
        root / "products" / "artifact-summary"
        if output_kind == "artifact"
        else reporting_operation.report_output_root(root, identity.profile)
    )
    ancestor.parent.mkdir(parents=True)
    foreign = tmp_path / f"foreign-{output_kind}"
    foreign.mkdir()
    ancestor.symlink_to(foreign, target_is_directory=True)
    monkeypatch.setattr(
        reporting_operation,
        "_prepare_transaction",
        lambda *_args: pytest.fail("unsafe output reached a reporting producer"),
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_start",
        lambda **_kwargs: pytest.fail("unsafe output published a reporting start"),
    )

    with pytest.raises(
        reporting_operation.ReportingOperationError,
        match="absent or use only real directories",
    ):
        reporting_operation.run_reporting(root, execute=True)
    assert list(foreign.iterdir()) == []


def test_producer_failure_stops_after_immutable_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run-failure").resolve()
    root.mkdir()
    state = _state(root)
    identity = _identity(root, state)
    _install_admission(monkeypatch, state, identity)
    observed: list[str] = []
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_start",
        lambda *, kind, **_kwargs: observed.append(f"start:{kind}"),
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_verified",
        lambda **_kwargs: pytest.fail("failed producer cannot publish completion"),
    )

    from emrys.reporting._artifact_index.models import ArtifactIndexError

    monkeypatch.setattr(
        reporting_operation,
        "_prepare_transaction",
        lambda _kind, _arguments, **_kwargs: SimpleNamespace(analysis_module=object()),
    )
    monkeypatch.setattr(
        reporting_operation,
        "_publish_prepared",
        lambda _kind, _context: (_ for _ in ()).throw(
            ArtifactIndexError("bounded private failure")
        ),
    )

    with pytest.raises(
        reporting_operation.ReportingOperationError,
        match="producer failed after ledger entry: bounded private failure",
    ):
        reporting_operation.run_reporting(root, execute=True)
    assert observed == ["start:artifact_index"]


def test_preflight_failure_publishes_no_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = (tmp_path / "run-preflight-failure").resolve()
    root.mkdir()
    state = _state(root)
    identity = _identity(root, state)
    _install_admission(monkeypatch, state, identity)
    from emrys.reporting._artifact_index.models import ArtifactIndexError

    monkeypatch.setattr(
        reporting_operation,
        "_prepare_transaction",
        lambda _kind, _arguments, **_kwargs: (_ for _ in ()).throw(
            ArtifactIndexError("bounded preflight failure")
        ),
    )
    monkeypatch.setattr(
        reporting_operation.reporting_boundary,
        "publish_start",
        lambda **_kwargs: pytest.fail("failed preflight cannot publish a start"),
    )

    with pytest.raises(
        reporting_operation.ReportingOperationError,
        match="preflight failed before ledger entry",
    ):
        reporting_operation.run_reporting(root, execute=True)
