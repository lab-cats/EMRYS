"""Run the fixed reporting projection after one successful scientific Attempt."""

from __future__ import annotations

import argparse
import stat
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal, NamedTuple

from emrys.contracts.artifacts.api import ContractValidationError
from emrys.contracts.orchestration.artifact_inventory import report_output_root
from emrys.contracts.orchestration.application_model import PROCESSING_STEP_IDS
from emrys.libraries.source_authority import (
    ArtifactSourceRootError,
    SourceCheckoutError,
    admit_artifact_source_root,
    admit_source_checkout,
)
from emrys.orchestration.run_coordinator import inspection, reporting_boundary
from emrys.reporting._artifact_index.models import ArtifactIndexError
from emrys.reporting._run_report.models import ReportRenderError
from emrys.reporting._run_summary.models import RunSummaryError

_PRODUCER_ERRORS = (
    ArtifactIndexError,
    RunSummaryError,
    ReportRenderError,
    ArtifactSourceRootError,
    SourceCheckoutError,
    ContractValidationError,
    OSError,
    ValueError,
)


class ReportingOperationError(RuntimeError):
    """One Run cannot safely plan, generate, or reuse its reports."""


class ReportingOperationOutcome(NamedTuple):
    """The result of one read-only plan, generation, or validated reuse."""

    status: Literal["planned", "generated", "reused"]
    verified_report_locations: tuple[tuple[str, Path], ...]


def _require_empty_output(path: Path, *, run_root: Path) -> None:
    cursor = run_root
    for part in path.relative_to(run_root).parts:
        cursor /= part
        try:
            state = cursor.lstat()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ReportingOperationError(
                f"Could not inspect reporting output location: {cursor}: {exc}"
            ) from exc
        if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
            raise ReportingOperationError(
                "Reporting output location must be absent or use only real "
                f"directories: {cursor}"
            )
    try:
        if any(path.iterdir()):
            raise ReportingOperationError(
                f"Refusing to adopt existing reporting output state: {path}"
            )
    except OSError as exc:
        raise ReportingOperationError(
            f"Could not inspect reporting output location: {path}: {exc}"
        ) from exc


def _arguments(identity: Any, kind: str) -> argparse.Namespace:
    root = identity.root
    run_id = str(identity.execution["run_id"])
    artifact_root = root / "products" / "artifact-summary"
    artifact_run_root = artifact_root / run_id
    source_checkout = Path(str(identity.attempt["source_checkout"]["path"]))
    authority = {"source_checkout": source_checkout, "artifact_source_root": root}
    run_contract = root / str(identity.config["reporting_run_contract_path"]["path"])
    policy_reference = identity.config.get("primary_analysis_policy_path")
    analysis_policy = (
        None
        if policy_reference is None
        else root / str(policy_reference["path"])
    )
    inventory = root / str(identity.config["artifact_inventory_path"]["path"])
    values = {
        "artifact_index": {
            "run_id": run_id,
            "run_contract": run_contract,
            "analysis_policy": analysis_policy,
            "profile": identity.profile,
            "inventory": inventory,
            "output_root": artifact_root,
        },
        "run_summary": {
            "run_id": run_id,
            "artifact_receipt": artifact_run_root / f"{run_id}.artifact_receipt.tsv",
            "analysis_policy": analysis_policy,
            "output_root": artifact_root,
            "expected_run_contract_path": run_contract,
            "expected_inventory_path": inventory,
        },
        "html_report": {
            "run_summary": artifact_run_root / f"{run_id}.run_summary.json",
            "analysis_policy": analysis_policy,
            "output_root": report_output_root(root, identity.profile),
        },
    }
    return argparse.Namespace(**authority, **values[kind])


def _producer_error(kind: str, phase: str, error: Exception) -> ReportingOperationError:
    rendered = str(error).strip()
    detail = rendered.splitlines()[-1][-500:] if rendered else ""
    return ReportingOperationError(f"{kind} {phase}{': ' + detail if detail else ''}")


def _prepare_transaction(kind: str, arguments: argparse.Namespace) -> Any:
    if kind == "html_report":
        from emrys.reporting import report  # noqa: PLC0415

        return report.prepare_report(arguments)

    source_checkout = admit_source_checkout(
        root=arguments.source_checkout,
        package_root=Path(__file__).resolve().parents[2],
    )
    artifact_source_root = admit_artifact_source_root(
        root=arguments.artifact_source_root,
    )
    if kind == "artifact_index":
        from emrys.reporting._artifact_index.context import prepare_context  # noqa: PLC0415

        return prepare_context(
            arguments,
            source_checkout=source_checkout,
            artifact_source_root=artifact_source_root,
        )
    from emrys.reporting._run_summary.builder import prepare_context  # noqa: PLC0415

    return prepare_context(
        arguments,
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )


def _publish_prepared(kind: str, context: Any) -> Path:
    if kind == "artifact_index":
        from emrys.reporting._artifact_index.publication import publish_context  # noqa: PLC0415

        publish_context(context)
        return context.receipt_path
    if kind == "run_summary":
        from emrys.reporting._run_summary.publication import (  # noqa: PLC0415
            publish_context,
        )

        publish_context(context)
        return context.paths.receipt
    from emrys.reporting import report  # noqa: PLC0415
    from emrys.reporting._run_report.publication import publish_report  # noqa: PLC0415

    publish_report(context, report.default_publication_ops())
    return context.output_receipt


def _require_successful_results(state: inspection.RunInspection) -> None:
    if state.integrity != "valid":
        raise ReportingOperationError("Run integrity is blocked")
    if state.attempt_outcome != "succeeded" or state.results_status != "complete":
        raise ReportingOperationError(
            "Reporting requires a successful Attempt with complete Results"
        )
    assert state.latest_attempt is not None and state.latest_receipt is not None
    if state.latest_receipt.get("status") != "succeeded":
        raise ReportingOperationError("Reporting requires a successful Attempt receipt")


def _admit_generation(state: inspection.RunInspection) -> Any:
    if state.authority is None:
        raise ReportingOperationError(
            "New reporting generation requires a successor Run authority"
        )
    assert state.latest_attempt is not None
    if state.reporting_status == "blocked":
        raise ReportingOperationError("Reporting state is blocked")

    identifier = str(state.latest_attempt["workflow_attempt_id"])
    attempt_path = state.run_root / "attempts" / identifier / "attempt.json"
    return reporting_boundary._admit_identity(  # noqa: SLF001
        run_root=state.run_root,
        execution_path=state.run_root / "contract" / "run.json",
        profile_path=state.run_root / "contract" / "profile.json",
        workflow_attempt_path=attempt_path,
        workflow_config_path=state.run_root
        / str(state.latest_attempt["workflow_config"]["path"]),
        require_publishable_attempt=True,
    )


def _require_prepared_processing_source(
    state: inspection.RunInspection,
    context: Any,
) -> None:
    """Bind the prepared artifact index to the already-admitted source bytes."""

    source = state.processing_source
    if source is None:
        return
    expected: dict[Path, tuple[int | None, str]] = {}
    for task in source.state.tasks:
        if task.record is None:
            raise ReportingOperationError("Processing source task evidence is incomplete")
        references = [*task.record["inputs"], *task.record["outputs"]]
        references.append(task.record["validation_report"])
        if task.record["native_receipt"] is not None:
            references.append(task.record["native_receipt"])
        for reference in references:
            path = Path(str(reference["path"]))
            if not path.is_absolute():
                path = source.root / path
            binding = (reference.get("size_bytes"), str(reference["sha256"]))
            if path in expected and expected[path] != binding:
                raise ReportingOperationError(
                    f"Processing source evidence disagrees for artifact: {path}"
                )
            expected[path] = binding
    external = tuple(
        binding for path, binding in expected.items() if not path.is_relative_to(source.root)
    )

    def matches(
        required: tuple[int | None, str] | None,
        observed: tuple[int | None, str] | None,
    ) -> bool:
        return bool(
            required
            and observed
            and required[1] == observed[1]
            and (required[0] is None or required[0] == observed[0])
        )

    for item in context.inspections:
        if str(item.row["step_id"]) not in PROCESSING_STEP_IDS:
            continue
        path = Path(item.resolved_path)
        snapshot = item.snapshot
        binding = (snapshot.size_bytes, snapshot.sha256) if snapshot is not None else None
        required = expected.get(path)
        if (
            snapshot is None
            or snapshot.status != "present"
            or (
                not matches(required, binding)
                and (
                    path.is_relative_to(source.root)
                    or not any(matches(item, binding) for item in external)
                )
            )
        ):
            raise ReportingOperationError(
                f"Prepared artifact index differs from processing source: {path}"
            )


def _recheck_processing_source(state: inspection.RunInspection) -> None:
    """Re-admit one source immediately before artifact-index verification."""

    if state.processing_source is None:
        return
    assert state.authority is not None
    try:
        confirmed = inspection.admit_bound_processing_source(
            state.run_root,
            state.authority,
        )
    except (OSError, inspection.InspectionError) as exc:
        raise ReportingOperationError(
            f"Processing source changed during artifact-index publication: {exc}"
        ) from exc
    if confirmed is None:
        raise ReportingOperationError(
            "Processing source changed during artifact-index publication"
        )


def run_reporting(
    run_root: Path,
    *,
    execute: bool,
    observe_generation_start: Callable[[], None] | None = None,
) -> ReportingOperationOutcome:
    """Plan, generate, or validate reuse of one Run's reporting projection."""

    try:
        state = inspection.inspect_run(run_root)
        _require_successful_results(state)
        if state.reporting_status == "not applicable":
            raise ReportingOperationError(
                "Reporting is not applicable to this partial scientific Run"
            )
        if state.reporting_status == "complete":
            return ReportingOperationOutcome(
                status="reused",
                verified_report_locations=state.verified_report_locations,
            )
        identity = _admit_generation(state)
        run_id = str(identity.execution["run_id"])
        for output in (
            identity.root / "products" / "artifact-summary" / run_id,
            report_output_root(identity.root, identity.profile) / run_id,
        ):
            _require_empty_output(output, run_root=identity.root)

        if not execute:
            try:
                context = _prepare_transaction(
                    "artifact_index", _arguments(identity, "artifact_index")
                )
                _require_prepared_processing_source(state, context)
            except _PRODUCER_ERRORS as exc:
                raise _producer_error("artifact_index", "dry-run failed", exc) from exc
            return ReportingOperationOutcome(
                status="planned",
                verified_report_locations=(),
            )

        publish_ops = replace(
            reporting_boundary.DEFAULT_REPORTING_BOUNDARY_OPS,
            validate_semantic_receipt=reporting_boundary.semantic_validator_session(
                read=False
            ),
        )
        identifier = str(identity.attempt["workflow_attempt_id"])
        identity_paths = {
            "run_root": identity.root,
            "execution_path": identity.root / "contract" / "run.json",
            "profile_path": identity.root / "contract" / "profile.json",
            "workflow_attempt_path": (
                identity.root / "attempts" / identifier / "attempt.json"
            ),
            "workflow_config_path": identity.root
            / str(identity.attempt["workflow_config"]["path"]),
        }
        locations: tuple[tuple[str, Path], ...] = ()
        for kind in reporting_boundary.REPORTING_KINDS:
            try:
                context = _prepare_transaction(kind, _arguments(identity, kind))
                if kind == "artifact_index":
                    _require_prepared_processing_source(state, context)
            except _PRODUCER_ERRORS as exc:
                raise _producer_error(
                    kind, "preflight failed before ledger entry", exc
                ) from exc
            reporting_boundary.publish_start(
                kind=kind,
                **identity_paths,
                ops=publish_ops,
            )
            if kind == reporting_boundary.REPORTING_KINDS[0] and observe_generation_start:
                try:
                    observe_generation_start()
                except Exception:
                    pass
            try:
                receipt_path = _publish_prepared(kind, context)
            except _PRODUCER_ERRORS as exc:
                raise _producer_error(
                    kind, "producer failed after ledger entry", exc
                ) from exc
            locations = reporting_boundary.publish_verified(
                kind=kind,
                receipt_path=receipt_path,
                **identity_paths,
                ops=publish_ops,
                before_publication=(
                    (lambda: _recheck_processing_source(state))
                    if kind == "artifact_index" and state.processing_source is not None
                    else None
                ),
            )
        return ReportingOperationOutcome(
            status="generated",
            verified_report_locations=locations,
        )
    except (
        inspection.InspectionError,
        reporting_boundary.ReportingBoundaryError,
    ) as exc:
        raise ReportingOperationError(str(exc)) from exc
