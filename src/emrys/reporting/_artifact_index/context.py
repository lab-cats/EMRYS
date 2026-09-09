"""Artifact-index context assembly and stable-input rechecks."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from emrys import analyses
from emrys.contracts.artifacts import api as contracts
from emrys.libraries.source_authority import matching_clean_checkout_head_commit

from .core import (
    canonical_digest,
    canonical_json_bytes,
    load_run_contract,
    new_attempt_id,
    scope_adapter_rosters,
    sha256_bytes,
    stat_source,
    utc_now,
    validate_inventory_registry,
)
from .inspection import apply_run_contract_checks, inspect_source
from .models import (
    ARTIFACT_INDEX_HEADER,
    ARTIFACT_RECEIPT_HEADER,
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
    build_index_rows,
    build_receipt_row,
    load_existing_receipt,
    producer_evidence,
    record_manifest,
    tsv_bytes,
    validate_existing_identity,
    validate_record_in_memory,
)
from .registry import build_adapter_registry
from .validation import validate_existing_transaction

if TYPE_CHECKING:
    from emrys.libraries.source_authority import ArtifactSourceRoot, SourceCheckout


def prepare_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: SourceCheckout,
    artifact_source_root: ArtifactSourceRoot,
) -> BuildContext:
    source_identity_observer = matching_clean_checkout_head_commit
    source_root = artifact_source_root.root
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
            _snapshot_receipt(path) for path in (run_contract_path, inventory_path)
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
        analysis_module.descriptor, source_root=source_checkout.root
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
    records_dir = output_dir / "records"
    artifacts_path = output_dir / f"{arguments.run_id}.artifacts.tsv"
    receipt_path = output_dir / f"{arguments.run_id}.artifact_receipt.tsv"
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

    existing = load_existing_receipt(receipt_path, artifacts_path, records_dir)
    previous_attempt_id, attempt_history = validate_existing_identity(
        existing,
        run_contract,
    )
    if existing is not None:
        validate_existing_transaction(
            existing=existing,
            run_id=arguments.run_id,
            run_contract=run_contract,
            records_dir=records_dir,
            artifacts_path=artifacts_path,
            receipt_path=receipt_path,
            source_root=source_root,
        )

    started_at = utc_now()
    attempt_id = new_attempt_id(started_at)
    git_commit = source_identity_observer(
        source_checkout=source_checkout,
        package_root=Path(__file__).resolve().parents[2],
    )
    if git_commit is None:
        raise ArtifactIndexError(
            "Artifact-index provenance requires a stable clean source checkout"
        )
    evidence = producer_evidence(
        git_commit,
        source_root=source_checkout.root,
        analysis_module=analysis_module,
    )
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
    record_bytes: list[bytes] = []
    for inspection, inventory_row in zip(inspections, inventory_rows, strict=True):
        record = build_artifact_record(
            run_id=arguments.run_id,
            run_contract=run_contract,
            inspection=inspection,
            implementation=evidence[inventory_row["step_id"]],
            git_commit=git_commit,
            created_at=started_at,
        )
        validate_record_in_memory(
            record,
            inventory_row,
            validator,
            source_root=source_root,
        )
        records.append(record)
        record_bytes.append(canonical_json_bytes(record))

    index_rows = build_index_rows(
        records=records,
        record_bytes=record_bytes,
        records_dir=records_dir,
    )
    index_bytes = tsv_bytes(ARTIFACT_INDEX_HEADER, index_rows)
    finished_at = utc_now()
    receipt_row = build_receipt_row(
        run_id=arguments.run_id,
        run_contract=run_contract,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_row_count=len(inventory_rows),
        artifacts_path=artifacts_path,
        index_bytes=index_bytes,
        index_rows=index_rows,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
    )
    receipt_bytes = tsv_bytes(ARTIFACT_RECEIPT_HEADER, [receipt_row])
    context = BuildContext(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        run_id=arguments.run_id,
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
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
        inspections=inspections,
        records=records,
        record_bytes=record_bytes,
        index_rows=index_rows,
        index_bytes=index_bytes,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        previous_receipt=existing,
        source_identity_observer=source_identity_observer,
    )
    validate_context_in_memory(context)
    return context


def prepare_evidence_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: SourceCheckout,
    artifact_source_root: ArtifactSourceRoot,
) -> EvidenceContext:
    """Prepare summary views directly from the admitted index records."""

    from emrys.reporting._run_summary.document import build_summary
    from emrys.reporting._run_summary.models import (
        OutputPaths,
        RUN_SUMMARY_RECEIPT_HEADER,
    )
    from emrys.reporting._run_summary.transaction import _new_attempt_id
    from emrys.reporting._run_summary.validation import _build_receipt_row

    context = prepare_context(
        arguments,
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )
    paths = OutputPaths(
        output_dir=context.output_dir,
        summary_json=context.output_dir / f"{context.run_id}.run_summary.json",
        summary_tsv=context.output_dir / f"{context.run_id}.run_summary.tsv",
        qc_summary=context.output_dir / f"{context.run_id}.qc_summary.tsv",
        receipt=context.output_dir / f"{context.run_id}.run_summary_receipt.tsv",
    )
    document, summary_json, summary_tsv, qc_summary = build_summary(
        source_root=artifact_source_root.root,
        run_id=context.run_id,
        run_contract=context.run_contract,
        inventory_path=context.inventory_path,
        inventory_sha256=context.inventory_sha256,
        inventory_size_bytes=context.inventory_size_bytes,
        inventory_rows=context.inventory_rows,
        artifact_receipt_path=context.receipt_path,
        artifact_receipt_sha256=sha256_bytes(context.receipt_bytes),
        artifact_receipt_size_bytes=len(context.receipt_bytes),
        artifact_receipt=context.receipt_row,
        artifacts=context.records,
        generated_at=context.receipt_row["finished_at"],
        git_commit=context.receipt_row["git_commit"],
        analysis_policy_binding=context.analysis_policy_binding,
    )
    timestamp = utc_now()
    receipt_row = _build_receipt_row(
        run_id=context.run_id,
        run_contract=context.run_contract,
        artifact_receipt_path=context.receipt_path,
        artifact_receipt_sha256=sha256_bytes(context.receipt_bytes),
        artifact_receipt=context.receipt_row,
        inventory_path=context.inventory_path,
        inventory_sha256=context.inventory_sha256,
        inventory_row_count=len(context.inventory_rows),
        artifacts_path=context.artifacts_path,
        artifacts_sha256=sha256_bytes(context.index_bytes),
        summary_json_path=paths.summary_json,
        summary_json_bytes=summary_json,
        summary_tsv_path=paths.summary_tsv,
        summary_tsv_bytes=summary_tsv,
        summary_tsv_row_count=len(context.records),
        qc_summary_path=paths.qc_summary,
        qc_summary_bytes=qc_summary,
        qc_summary_row_count=sum(len(record["metrics"]) for record in context.records),
        document=document,
        attempt_id=_new_attempt_id(timestamp),
        previous_attempt_id=None,
        previous_attempt_history=[],
        git_commit=context.receipt_row["git_commit"],
        started_at=timestamp,
        finished_at=timestamp,
    )
    return EvidenceContext(
        index=context,
        summary_paths=paths,
        summary_document=document,
        summary_json_bytes=summary_json,
        summary_tsv_bytes=summary_tsv,
        qc_summary_bytes=qc_summary,
        summary_receipt_row=receipt_row,
        summary_receipt_bytes=tsv_bytes(RUN_SUMMARY_RECEIPT_HEADER, [receipt_row]),
    )


def validate_context_in_memory(context: BuildContext) -> None:
    if [row["artifact_id"] for row in context.index_rows] != [
        row["artifact_id"] for row in context.inventory_rows
    ]:
        raise ArtifactIndexError(
            "Generated artifact index order differs from inventory order"
        )
    if context.receipt_row["artifacts_index_sha256"] != sha256_bytes(
        context.index_bytes
    ):
        raise ArtifactIndexError("Generated artifact index hash is inconsistent")
    if context.receipt_row["record_set_sha256"] != canonical_digest(
        record_manifest(context.index_rows)
    ):
        raise ArtifactIndexError("Generated record-set hash is inconsistent")
    if context.receipt_row["transaction_state"] != "complete":
        raise ArtifactIndexError("Generated receipt is not complete")


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
    """Re-attest the exact clean producer checkout bound into the receipt."""

    observed = context.source_identity_observer(
        source_checkout=context.source_checkout,
        package_root=Path(__file__).resolve().parents[2],
    )
    if observed != context.receipt_row["git_commit"]:
        raise ArtifactIndexError(
            "Artifact-index producer checkout changed after provenance attribution"
        )
