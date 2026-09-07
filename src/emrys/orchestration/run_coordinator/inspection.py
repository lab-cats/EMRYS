"""Read-only derivation of Project Run and Results state.

This facade aggregates immutable Attempt, task, reporting, and lock evidence.
Snakemake metadata remains intentionally outside the inspection authority.
"""

from __future__ import annotations

import hashlib
import re
import socket
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from coolname_hash import pseudohash

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
    ExecutionPlan,
    execution_plan_boundary,
    validate_successor_run,
)
from emrys.libraries.process_environment import process_is_alive
from emrys.orchestration.run_coordinator._inspection_admission import (
    ExpectedTask,
    InspectionError,
    SuccessorRunAuthority,
    _canonical_root,
    _state_tree_blockers_by_domain,
    _successor_expected_tasks,
    admit_attempt_run_lock,
    admit_canonical_record,
    admit_execution_path,
    admit_successor_run,
    expected_tasks,
    lock_tree_blockers,
    state_tree_blockers,
    task_start_tree_blockers,
    verified_tree_blockers,
)
from emrys.orchestration.run_coordinator._inspection_attempts import (
    attempt_fields,
    inspect_attempt_chain,
    inspect_attempt_task_trees,
    inspect_attempt_tree,
)
from emrys.orchestration.run_coordinator._inspection_evidence import (
    ReportingReceiptValidator,
    TaskInspection,
    ValidatedReportingReceipt,
    _receipt_binds_reporting,
    inspect_evidence,
)

AttemptOutcome = Literal[
    "not_started",
    "running",
    "succeeded",
    "failed",
    "interrupted",
    "blocked",
]
RunIntegrity = Literal["valid", "blocked"]
ResultsStatus = Literal["incomplete", "complete", "blocked"]
ReportingStatus = Literal["not applicable", "incomplete", "complete", "blocked"]
_RUN_ID_PATTERN = re.compile(r"run-[0-9a-f]{64}\Z")
_RUN_ID_PREFIX_PATTERN = re.compile(r"run-[0-9a-f]{1,64}\Z")


def human_run_name(run_id: str) -> str:
    """Derive one stable two-word presentation name from an immutable Run ID."""

    if _RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise InspectionError(f"Invalid Run ID: {run_id}")
    return "-".join(pseudohash(run_id, 2))


def project_run_roots(project_root: Path) -> tuple[Path, ...]:
    """List canonical Run paths without admitting their evidence trees."""

    runs_root = project_root / "runs"
    if not runs_root.exists() and not runs_root.is_symlink():
        return ()
    if runs_root.is_symlink() or not runs_root.is_dir():
        raise InspectionError(f"Project runs path must be a real directory: {runs_root}")
    try:
        entries = tuple(runs_root.iterdir())
    except OSError as exc:
        raise InspectionError(f"Could not list Project Runs: {runs_root}: {exc}") from exc
    return tuple(
        entry
        for entry in sorted(entries, key=lambda item: item.name)
        if _RUN_ID_PATTERN.fullmatch(entry.name) is not None
        and not entry.is_symlink()
        and entry.is_dir()
    )


def resolve_run_root(run_roots: Sequence[Path], selector: str) -> Path:
    """Resolve an exact name or ID, or an unambiguous Run-ID prefix."""

    matches = tuple(
        root
        for root in run_roots
        if selector == human_run_name(root.name) or selector == root.name
    )
    if not matches and _RUN_ID_PREFIX_PATTERN.fullmatch(selector) is not None:
        matches = tuple(root for root in run_roots if root.name.startswith(selector))
    if len(matches) == 1:
        return matches[0]
    outcome = "No Project Run matches" if not matches else "Ambiguous Project Run"
    raise InspectionError(f"{outcome} selector: {selector}")


@dataclass(frozen=True, slots=True)
class InspectionOps:
    """Explicit host/process observations used by read-only inspection."""

    host_name: Callable[[], str]
    process_is_alive: Callable[[int], bool]
    validate_reporting_receipt: ReportingReceiptValidator


@dataclass(frozen=True, slots=True)
class RunInspection:
    """Complete derived state without a mutable status cache."""

    run_root: Path
    run_id: str
    attempt_outcome: AttemptOutcome
    latest_attempt: dict[str, Any] | None
    latest_receipt: dict[str, Any] | None
    tasks: tuple[TaskInspection, ...]
    reporting_completion_records: dict[str, dict[str, dict[str, str] | None]]
    integrity_blockers: tuple[str, ...]
    results_blockers: tuple[str, ...]
    reporting_blockers: tuple[str, ...]
    verified_report_locations: tuple[tuple[str, Path], ...] = ()
    authority: SuccessorRunAuthority | None = None
    processing_source: ProcessingSourceAdmission | None = None

    @property
    def processing_source_run_id(self) -> str | None:
        """Return the source ID derived from immutable Execution-Plan authority."""

        if self.authority is None:
            return None
        source = self.authority.execution_plan.record["identity"].get(
            "processing_source"
        )
        return None if source is None else str(source["source_run_id"])

    @property
    def integrity(self) -> RunIntegrity:
        """Return whether Run and Attempt authority remain admissible."""

        blocked_receipt_has_no_derived_domain = (
            self.latest_receipt is not None
            and self.latest_receipt["status"] == "blocked"
            and not self.results_blockers
            and not (
                _receipt_binds_reporting(self.latest_receipt)
                and self.reporting_blockers
            )
        )
        return (
            "blocked"
            if self.integrity_blockers or blocked_receipt_has_no_derived_domain
            else "valid"
        )

    @property
    def results_status(self) -> ResultsStatus:
        """Return scientific Results completeness without reporting state."""

        return _results_status(self.tasks, self.results_blockers)

    @property
    def reporting_status(self) -> ReportingStatus:
        """Return downstream reporting status without changing Results."""

        if self.reporting_blockers:
            return "blocked"
        if (
            self.authority is not None
            and execution_plan_boundary(self.authority.execution_plan) != "analysis"
        ):
            return "not applicable"
        if self.reporting_completion_records and all(
            records["start"] is not None and records["verified"] is not None
            for records in self.reporting_completion_records.values()
        ):
            return "complete"
        return "incomplete"

    @property
    def receipt_blockers(self) -> tuple[str, ...]:
        """Return Attempt blockers retained by the terminal receipt."""

        if self.latest_receipt is None or self.latest_receipt["status"] != "blocked":
            return ()
        return tuple(str(value) for value in self.latest_receipt["blockers"])

    @property
    def blockers(self) -> tuple[str, ...]:
        """Return all blockers while preserving their owned domain fields."""

        return tuple(
            dict.fromkeys(
                (
                    *self.integrity_blockers,
                    *self.results_blockers,
                    *self.reporting_blockers,
                    *self.receipt_blockers,
                )
            )
        )

    @property
    def recovery_available(self) -> bool:
        """Return whether incomplete scientific work has a safe resume boundary."""

        return (
            self.integrity == "valid"
            and self.results_status == "incomplete"
            and self.attempt_outcome in {"failed", "interrupted"}
        )


@dataclass(frozen=True, slots=True)
class ProcessingSourceAdmission:
    """One successful processing Run admitted as immutable downstream input."""

    root: Path
    state: RunInspection
    binding: dict[str, str]
    artifact_snapshots: tuple[dict[str, Any], ...]


def _attempt_outcome(
    *,
    latest: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
    running: bool,
    integrity_blockers: Sequence[str],
    results_status: ResultsStatus,
) -> AttemptOutcome:
    """Derive scientific Attempt outcome independently of reporting."""

    if latest is None:
        return "not_started"
    if running:
        return "running"
    if receipt is None or results_status == "blocked" or integrity_blockers:
        return "blocked"
    if _receipt_binds_reporting(receipt) and results_status == "complete":
        return "succeeded"
    return cast(AttemptOutcome, receipt["status"])


def _results_status(
    tasks: Sequence[TaskInspection], blockers: Sequence[str]
) -> ResultsStatus:
    if blockers:
        return "blocked"
    if tasks and all(item.state == "verified" for item in tasks):
        return "complete"
    return "incomplete"


def default_inspection_ops() -> InspectionOps:
    """Construct production-only process observations."""

    from emrys.orchestration.run_coordinator import reporting_boundary  # noqa: PLC0415

    return InspectionOps(
        host_name=socket.gethostname,
        process_is_alive=process_is_alive,
        validate_reporting_receipt=reporting_boundary.semantic_validator_session(
            read=True
        ),
    )


def _inspect_lock(
    root: Path,
    *,
    latest: Mapping[str, Any] | None,
    latest_terminal: bool,
    ops: InspectionOps,
    allowed_next_attempt: Mapping[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    locks_root = root / "locks"
    blockers = list(lock_tree_blockers(root))
    if any("aggregate locks root" in item.lower() for item in blockers):
        return False, blockers
    path = locks_root / "run.lock"
    if not path.exists() and not path.is_symlink():
        return False, blockers
    try:
        record, _ = admit_canonical_record(path, root, "run-lock")
    except InspectionError as exc:
        return False, [str(exc)]
    if latest is None:
        blockers.append("Run lock exists without a workflow attempt")
    else:
        identifier = str(latest["workflow_attempt_id"])
        expected_lock_attempt = latest
        if (
            allowed_next_attempt is not None
            and allowed_next_attempt.get("supersedes_workflow_attempt_id") == identifier
            and record["workflow_attempt_id"]
            == allowed_next_attempt.get("workflow_attempt_id")
        ):
            expected_lock_attempt = allowed_next_attempt
        elif record["workflow_attempt_id"] != identifier:
            blockers.append("Run lock does not bind the latest workflow attempt")
        for field, expected in orchestration_contracts.run_lock_record(
            expected_lock_attempt
        ).items():
            if record[field] != expected:
                blockers.append(f"Run lock does not bind its Attempt {field}")
        if latest_terminal and expected_lock_attempt is latest:
            blockers.append("Terminal workflow attempt retained its run lock")
        if record["host"] != ops.host_name():
            blockers.append(
                "Run lock host is not this host; live ownership is unproved"
            )
        elif not ops.process_is_alive(int(record["process_id"])):
            blockers.append(
                "Run lock process is not live; automatic recovery is forbidden"
            )
    return (
        not blockers
        and latest is not None
        and (not latest_terminal or expected_lock_attempt is not latest),
        blockers,
    )


def inspect_run(
    run_root: Path,
    *,
    ops: InspectionOps | None = None,
    allowed_next_attempt: Mapping[str, Any] | None = None,
) -> RunInspection:
    """Derive one run state without reading or repairing ``.snakemake``."""

    root = _canonical_root(run_root)
    active_ops = default_inspection_ops() if ops is None else ops
    authority = admit_successor_run(root)
    profile_path = root / "contract" / "profile.json"
    profile_present = profile_path.exists() or profile_path.is_symlink()
    legacy_execution_path = root / "contract" / "normalized.json"
    legacy_execution_present = (
        legacy_execution_path.exists() or legacy_execution_path.is_symlink()
    )
    state_integrity, state_results, state_reporting = _state_tree_blockers_by_domain(
        root
    )
    integrity_blockers = list(state_integrity)
    results_blockers = list(state_results)
    reporting_blockers = list(state_reporting)
    processing_source = None
    if authority is not None:
        execution = authority.run_binding.record
        execution_data = authority.run_binding.canonical_bytes
        if legacy_execution_present:
            integrity_blockers.append(
                "Successor Run retains a retired execution projection"
            )
        if profile_present:
            profile, profile_data = admit_canonical_record(
                profile_path, root, "profile"
            )
            try:
                validate_successor_run(
                    analysis=authority.analysis_revision,
                    plan=authority.execution_plan,
                    run=authority.run_binding,
                    profile=profile,
                )
            except orchestration_contracts.ContractValidationError as exc:
                integrity_blockers.append(f"Profile differs from immutable Run: {exc}")
            try:
                processing_source = admit_bound_processing_source(root, authority)
            except (OSError, InspectionError) as exc:
                results_blockers.append(f"Processing source is not admissible: {exc}")
        else:
            profile = None
            profile_data = None
    else:
        if profile_present != legacy_execution_present:
            raise InspectionError(
                "Run has an incomplete profile/execution contract pair"
            )
        profile, profile_data = admit_canonical_record(profile_path, root, "profile")
        execution, execution_data = admit_canonical_record(
            legacy_execution_path,
            root,
            "execution",
            profile=profile,
        )
        if (
            execution["profile"]["profile_sha256"]
            != hashlib.sha256(profile_data).hexdigest()
        ):
            integrity_blockers.append(
                "Execution contract no longer binds profile snapshot bytes"
            )

    attempts, receipts, attempt_blockers = inspect_attempt_chain(
        root,
        authority=authority,
        profile=profile if authority is not None else None,
    )
    integrity_blockers.extend(attempt_blockers)
    latest = attempts[-1] if attempts else None
    latest_id = None if latest is None else str(latest["workflow_attempt_id"])
    latest_receipt = None if latest_id is None else receipts.get(latest_id)
    if latest is not None and profile_data is not None:
        expected_bindings = {
            "run_id": execution["run_id"],
            "execution_contract_sha256": hashlib.sha256(execution_data).hexdigest(),
            "profile_sha256": hashlib.sha256(profile_data).hexdigest(),
        }
        for field, expected in expected_bindings.items():
            if latest[field] != expected:
                integrity_blockers.append(
                    f"Latest attempt does not bind admitted {field}"
                )
    running, lock_blockers = _inspect_lock(
        root,
        latest=latest,
        latest_terminal=latest_receipt is not None,
        ops=active_ops,
        allowed_next_attempt=allowed_next_attempt,
    )
    integrity_blockers.extend(lock_blockers)
    if authority is not None and not profile_present:
        if latest is not None:
            integrity_blockers.append(
                "Successor Attempt exists without its backend adapters"
            )
            results_blockers.append(
                "Scientific Results cannot be admitted without backend adapters"
            )
            if any(_receipt_binds_reporting(receipt) for receipt in receipts.values()):
                reporting_blockers.append(
                    "Reporting evidence cannot be admitted without backend adapters"
                )
        expected = _successor_expected_tasks(authority)
        tasks = tuple(TaskInspection(item, "pending", None, None) for item in expected)
        outcome = _attempt_outcome(
            latest=latest,
            receipt=latest_receipt,
            running=running,
            integrity_blockers=integrity_blockers,
            results_status=_results_status(tasks, results_blockers),
        )
        return RunInspection(
            run_root=root,
            run_id=authority.run_binding.run_id,
            attempt_outcome=outcome,
            latest_attempt=latest,
            latest_receipt=latest_receipt,
            tasks=tasks,
            reporting_completion_records={
                kind: {"start": None, "verified": None}
                for kind in ("artifact_index", "run_summary", "html_report")
            },
            integrity_blockers=tuple(dict.fromkeys(integrity_blockers)),
            results_blockers=tuple(dict.fromkeys(results_blockers)),
            reporting_blockers=tuple(dict.fromkeys(reporting_blockers)),
            authority=authority,
        )
    live_origin = (
        latest_id
        if running and latest_receipt is None and allowed_next_attempt is None
        else None
    )
    evidence = inspect_evidence(
        root,
        execution,
        profile,
        attempts,
        receipts,
        active_ops.validate_reporting_receipt,
        authority=authority,
        allow_incomplete_origin=live_origin,
    )
    integrity_blockers.extend(evidence.integrity_blockers)
    results_blockers.extend(evidence.results_blockers)
    reporting_blockers.extend(evidence.reporting_blockers)
    tasks = evidence.tasks
    reporting = evidence.reporting_completion_records
    if latest_receipt is not None:
        if latest_receipt["status"] == "succeeded":
            if any(item.state != "verified" for item in tasks):
                results_blockers.append(
                    "Successful attempt receipt is missing required verified tasks"
                )
            if _receipt_binds_reporting(latest_receipt) and any(
                state["start"] is None or state["verified"] is None
                for state in reporting.values()
            ):
                reporting_blockers.append(
                    "Successful attempt receipt is missing reporting transactions"
                )
    if (
        latest is not None
        and latest_receipt is None
        and not (running and allowed_next_attempt is None)
    ):
        integrity_blockers.append(
            "Latest workflow attempt is nonterminal without a live owned lock"
        )
    outcome = _attempt_outcome(
        latest=latest,
        receipt=latest_receipt,
        running=running and allowed_next_attempt is None,
        integrity_blockers=integrity_blockers,
        results_status=_results_status(tasks, results_blockers),
    )
    return RunInspection(
        run_root=root,
        run_id=(
            authority.run_binding.run_id
            if authority is not None
            else str(execution["run_id"])
        ),
        attempt_outcome=outcome,
        latest_attempt=latest,
        latest_receipt=latest_receipt,
        tasks=tasks,
        reporting_completion_records=reporting,
        integrity_blockers=tuple(dict.fromkeys(integrity_blockers)),
        results_blockers=tuple(dict.fromkeys(results_blockers)),
        reporting_blockers=tuple(dict.fromkeys(reporting_blockers)),
        verified_report_locations=evidence.verified_report_locations,
        authority=authority,
        processing_source=processing_source,
    )


def admit_processing_source(run_root: Path) -> ProcessingSourceAdmission:
    """Admit one exact, successful processing-only Run without mutating it."""

    state = inspect_run(run_root)
    authority = state.authority
    receipt = state.latest_receipt
    attempt = state.latest_attempt
    if authority is None:
        raise InspectionError("A processing source must use successor Run authority")
    if execution_plan_boundary(authority.execution_plan) != "processing":
        raise InspectionError(
            "A processing source must stop at the exact Step 06 boundary"
        )
    if (
        state.integrity != "valid"
        or state.attempt_outcome != "succeeded"
        or state.results_status != "complete"
        or state.reporting_status != "not applicable"
        or receipt is None
        or attempt is None
        or receipt.get("schema_version") != "emrys.attempt-receipt.v2"
        or receipt.get("status") != "succeeded"
    ):
        raise InspectionError(
            "A processing source requires valid, complete, successful Step 00-06 evidence"
        )
    return ProcessingSourceAdmission(
        root=state.run_root,
        state=state,
        binding={
            "source_run_id": state.run_id,
            "workflow_attempt_id": str(attempt["workflow_attempt_id"]),
            "attempt_receipt_sha256": orchestration_contracts.canonical_sha256(receipt),
        },
        artifact_snapshots=tuple(
            {
                "step_id": task_state.expected.step_id,
                "scope_id": task_state.expected.scope_id,
                "role": (
                    (
                        "step00c_reference_fai_v1",
                        "step00c_reference_dict_v1",
                    )[output_index]
                    if task_state.expected.step_id == "00c"
                    else str(output["role"])
                ),
                "path": str(output["path"]),
                "size_bytes": int(output["size_bytes"]),
                "sha256": str(output["sha256"]),
            }
            for task_state in state.tasks
            if task_state.record is not None
            for output_index, output in enumerate(task_state.record["outputs"])
        ),
    )


def validate_processing_source(
    source: ProcessingSourceAdmission,
    *,
    target_analysis: AnalysisRevision,
    target_plan: ExecutionPlan,
) -> None:
    """Require exact subset-compatible processing for one target Analysis Run."""

    authority = source.state.authority
    assert authority is not None
    source_analysis = authority.analysis_revision.record["identity"]
    target_identity = target_analysis.record["identity"]
    if source_analysis["reference"] != target_identity["reference"]:
        raise InspectionError(
            "Processing source and target reference identities differ"
        )
    source_samples = {
        str(row["sample_id"]): row for row in source_analysis["samples"]
    }
    if any(
        source_samples.get(str(row["sample_id"])) != row
        for row in target_identity["samples"]
    ):
        raise InspectionError(
            "Target samples are not an exact subset of the processing source"
        )

    source_plan = authority.execution_plan.record["identity"]
    target_plan_identity = target_plan.record["identity"]
    if target_plan_identity.get("processing_source") != source.binding:
        raise InspectionError(
            "Target Execution Plan binds a different processing source"
        )
    source_compatibility = source_plan.get("processing_compatibility_sha256")
    target_compatibility = target_plan_identity.get(
        "processing_compatibility_sha256"
    )
    if source_compatibility is not None and target_compatibility is not None:
        if source_compatibility != target_compatibility:
            raise InspectionError(
                "Processing source and target execution semantics differ"
            )
        return

    # Historical execution-plan.v1 records predate the processing projection.
    # They remain reusable only when the former whole-plan comparison proves
    # exact compatibility; no missing digest is synthesized or trusted.
    ignored = {
        "scientific_stopping_owner_keys",
        "processing_source",
        "processing_compatibility_sha256",
    }
    if {
        key: value for key, value in source_plan.items() if key not in ignored
    } != {
        key: value
        for key, value in target_plan_identity.items()
        if key not in ignored
    }:
        raise InspectionError("Processing source and target execution semantics differ")


def admit_bound_processing_source(
    run_root: Path,
    authority: SuccessorRunAuthority,
) -> ProcessingSourceAdmission | None:
    """Resolve and admit the immutable same-Project processing relationship."""

    binding = authority.execution_plan.record["identity"].get("processing_source")
    if binding is None:
        return None
    source = admit_processing_source(run_root.parent / str(binding["source_run_id"]))
    validate_processing_source(
        source,
        target_analysis=authority.analysis_revision,
        target_plan=authority.execution_plan,
    )
    return source


__all__ = (
    "ExpectedTask",
    "InspectionError",
    "InspectionOps",
    "ProcessingSourceAdmission",
    "RunInspection",
    "ReportingReceiptValidator",
    "SuccessorRunAuthority",
    "TaskInspection",
    "ValidatedReportingReceipt",
    "admit_canonical_record",
    "admit_execution_path",
    "admit_successor_run",
    "admit_attempt_run_lock",
    "admit_bound_processing_source",
    "admit_processing_source",
    "attempt_fields",
    "default_inspection_ops",
    "expected_tasks",
    "inspect_attempt_tree",
    "inspect_attempt_chain",
    "inspect_attempt_task_trees",
    "inspect_run",
    "lock_tree_blockers",
    "state_tree_blockers",
    "task_start_tree_blockers",
    "verified_tree_blockers",
    "validate_processing_source",
)
