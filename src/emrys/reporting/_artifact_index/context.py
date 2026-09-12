"""Artifact-index context assembly and stable-input rechecks."""

from __future__ import annotations

import argparse
import copy
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from emrys import analyses
from emrys.contracts.artifacts import api as contracts
from emrys.contracts.orchestration.api import canonical_sha256
from emrys.libraries.source_authority import admit_installed_package

from .core import (
    load_run_contract,
    new_attempt_id,
    scope_adapter_rosters,
    stat_source,
    utc_now,
    validate_inventory_registry,
)
from .inspection import apply_run_contract_checks, inspect_source
from .models import (
    ArtifactIndexError,
    BuildContext,
    EvidenceContext,
)
from .reconciliation import (
    reconcile_native_transactions,
    reconcile_scope_transactions,
)
from .records import (
    build_artifact_record,
    validate_record_in_memory,
)
from .registry import build_adapter_registry

if TYPE_CHECKING:
    from emrys.libraries.source_authority import ArtifactSourceRoot, InstalledPackage


def prepare_context(
    arguments: argparse.Namespace,
    *,
    installed_package: InstalledPackage,
    artifact_source_root: ArtifactSourceRoot,
) -> BuildContext:
    source_identity_observer = admit_installed_package
    source_root = artifact_source_root.root
    scientific_origin = copy.deepcopy(arguments.scientific_origin)
    if not contracts.SAFE_ID_RE.fullmatch(arguments.run_id):
        raise ArtifactIndexError("run_id must match [A-Za-z0-9][A-Za-z0-9._-]*")
    run_contract_path = arguments.run_contract.expanduser().resolve()
    inventory_path = arguments.inventory.expanduser().resolve()
    output_root = arguments.output_root.expanduser().resolve()
    from emrys.reporting.transaction_validation import (
        ReportingTransactionError,
        _snapshot_receipt,
    )

    try:
        contract_inputs = tuple(
            _snapshot_receipt(path)
            for path in (
                run_contract_path,
                inventory_path,
                *(Path(reference["path"]) for reference in scientific_origin.values()),
            )
        )
        if any(
            snapshot.sha256 != reference["sha256"]
            for snapshot, reference in zip(
                contract_inputs[2:], scientific_origin.values(), strict=True
            )
        ):
            raise ArtifactIndexError(
                "Original scientific records differ from their bound hashes"
            )
    except ReportingTransactionError as exc:
        raise ArtifactIndexError(str(exc)) from exc

    def recheck_contract_inputs() -> None:
        try:
            if any(_snapshot_receipt(item.path) != item for item in contract_inputs):
                raise ArtifactIndexError(
                    "Run contract or inventory changed after admission"
                )
        except ReportingTransactionError as exc:
            raise ArtifactIndexError(str(exc)) from exc

    run_contract, run_contract_file_sha256 = load_run_contract(run_contract_path)
    from emrys.reporting._run_summary.document import admit_analysis_policy

    analysis_policy_path = getattr(arguments, "analysis_policy", None)
    analysis_policy, analysis_policy_binding, recheck_analysis_policy = (
        admit_analysis_policy(analysis_policy_path, run_contract)
    )
    try:
        analysis_module = analyses.readmit_analysis_module(analysis_policy)
    except analyses.AnalysisModuleLoadError as exc:
        raise ArtifactIndexError(str(exc)) from exc
    adapter_registry = build_adapter_registry(
        analysis_module.descriptor, source_root=installed_package.root
    )
    profile = getattr(arguments, "profile", None)
    if profile is None:
        raise ArtifactIndexError(
            "Artifact indexing requires the Run's immutable workflow profile"
        )
    scope_rosters = scope_adapter_rosters(profile["artifact_templates"])
    module_steps = {task.step_id for task in analysis_module.descriptor.tasks}
    source_path_templates = {
        str(template["adapter"]): str(template["source_path_template"])
        for template in profile["artifact_templates"]
        if template["step_id"] in module_steps
        and template.get("source_path_template") is not None
    }
    inventory_rows = contracts.validate_inventory(
        inventory_path,
        source_root=source_root,
    )
    validate_inventory_registry(
        inventory_rows,
        source_root=source_root,
        adapter_registry=adapter_registry,
        scope_rosters=scope_rosters,
        source_path_templates=source_path_templates,
    )
    inventory_sha256 = contract_inputs[1].sha256
    recheck_contract_inputs()
    output_dir = output_root / arguments.run_id
    lock_path = output_dir / f".{arguments.run_id}.artifact-index.lock"
    if output_dir.is_symlink():
        raise ArtifactIndexError(
            f"Artifact-index output directory must not be a symlink: {output_dir}"
        )
    if lock_path.exists() or lock_path.is_symlink():
        raise ArtifactIndexError(
            f"Artifact-index output is locked; inspect owner metadata: {lock_path}"
        )
    contract_input_paths = [
        ("run contract", run_contract_path),
        ("inventory", inventory_path),
    ]
    if analysis_policy_path is not None:
        contract_input_paths.append(("analysis policy", analysis_policy_path))
    for label, path in contract_input_paths:
        if path == output_dir or output_dir in path.parents:
            raise ArtifactIndexError(
                f"The {label} must not live inside its generated run directory"
            )
    for row in inventory_rows:
        source = contracts.resolve_contract_path(
            row["source_path"],
            source_root=source_root,
        )
        if source == output_dir or output_dir in source.parents:
            raise ArtifactIndexError(
                "Inventory source paths must not point inside the generated "
                f"run directory: {row['source_path']}"
            )

    started_at = utc_now()
    attempt_id = new_attempt_id(started_at)
    observed = source_identity_observer(root=installed_package.root)
    if observed.record != installed_package.record:
        raise ArtifactIndexError(
            "Installed package changed before provenance attribution"
        )
    git_commit = installed_package.git_commit or "unavailable"
    inspections = [
        inspect_source(
            row,
            adapter_registry[row["adapter"]],
            source_root=source_root,
        )
        for row in inventory_rows
    ]
    apply_run_contract_checks(inspections, run_contract)
    reconcile_native_transactions(
        inspections,
        source_root=source_root,
    )
    reconcile_scope_transactions(inspections)

    validator = contracts.schema_validator("artifact-record")
    records: list[dict[str, Any]] = []
    for inspection, inventory_row in zip(inspections, inventory_rows, strict=True):
        record = build_artifact_record(inspection=inspection)
        validate_record_in_memory(
            record,
            inventory_row,
            validator,
        )
        records.append(record)

    finished_at = utc_now()
    context = BuildContext(
        installed_package=installed_package,
        artifact_source_root=artifact_source_root,
        scientific_origin=scientific_origin,
        run_id=arguments.run_id,
        profile_sha256=canonical_sha256(profile),
        run_contract_path=run_contract_path,
        run_contract=run_contract,
        run_contract_file_sha256=run_contract_file_sha256,
        analysis_policy_path=analysis_policy_path,
        analysis_policy_binding=analysis_policy_binding,
        recheck_analysis_policy=recheck_analysis_policy,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_size_bytes=contract_inputs[1].size_bytes,
        recheck_contract_inputs=recheck_contract_inputs,
        inventory_rows=inventory_rows,
        output_dir=output_dir,
        lock_path=lock_path,
        inspections=inspections,
        records=records,
        attempt_id=attempt_id,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
        source_identity_observer=source_identity_observer,
    )
    return context


def recheck_inputs(context: BuildContext) -> None:
    context.recheck_contract_inputs()
    if context.recheck_analysis_policy is not None:
        context.recheck_analysis_policy()
    for inspection in context.inspections:
        observed = stat_source(
            inspection.resolved_path,
            hash_content=(
                inspection.snapshot is not None
                and inspection.snapshot.file_type == "hash_read_error"
            ),
        )
        expected_snapshot = inspection.snapshot
        # Rechecks may skip hashing, but every filesystem identity field must match.
        if expected_snapshot is None or not (
            expected_snapshot == replace(observed, sha256=expected_snapshot.sha256)
        ):
            raise ArtifactIndexError(
                "Declared source changed after initial inspection: "
                f"{inspection.row['source_path']}"
            )


def recheck_source_identity(context: BuildContext) -> None:
    """Re-observe the exact installed producer bound into the manifest."""

    observed = context.source_identity_observer(root=context.installed_package.root)
    if observed.record != context.installed_package.record:
        raise ArtifactIndexError(
            "Artifact-index installed producer changed after provenance attribution"
        )


def prepare_evidence_context(
    arguments: argparse.Namespace,
    *,
    installed_package: InstalledPackage,
    artifact_source_root: ArtifactSourceRoot,
) -> EvidenceContext:
    """Prepare the single Run result manifest and its human table projections."""
    from emrys.reporting._run_summary.document import build_summary
    from emrys.reporting._run_summary.models import OutputPaths

    context = prepare_context(
        arguments,
        installed_package=installed_package,
        artifact_source_root=artifact_source_root,
    )
    paths = OutputPaths(
        output_dir=context.output_dir,
        summary_json=context.output_dir / f"{context.run_id}.run_summary.json",
        summary_tsv=context.output_dir / f"{context.run_id}.run_summary.tsv",
        qc_summary=context.output_dir / f"{context.run_id}.qc_summary.tsv",
    )
    document, summary_json, summary_tsv, qc_summary = build_summary(
        source_root=artifact_source_root.root,
        output_dir=context.output_dir,
        run_id=context.run_id,
        run_contract=context.run_contract,
        run_contract_path=context.run_contract_path,
        run_contract_file_sha256=context.run_contract_file_sha256,
        inventory_path=context.inventory_path,
        inventory_sha256=context.inventory_sha256,
        inventory_size_bytes=context.inventory_size_bytes,
        inventory_rows=context.inventory_rows,
        artifacts=context.records,
        generated_at=context.finished_at,
        git_commit=context.git_commit,
        installed_package=context.installed_package.record,
        scientific_origin=context.scientific_origin,
        analysis_policy_binding=context.analysis_policy_binding,
        publication={
            "attempt_id": context.attempt_id,
            "started_at": context.started_at,
            "finished_at": context.finished_at,
            "transaction_state": "complete",
        },
    )
    return EvidenceContext(
        context, paths, document, summary_json, summary_tsv, qc_summary
    )
