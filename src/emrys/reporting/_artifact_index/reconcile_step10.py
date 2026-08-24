"""Step 10 context transaction plus artifact-source graph reconciliation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from emrys.contracts.scientific_evidence import scientific_context

from .models import ArtifactIndexError, Inspection
from .reconcile_native import NativeSourceIndex, require_referenced_source


def _member_by_adapter(
    members: Sequence[Inspection], adapter: str
) -> Inspection:
    matches = [member for member in members if member.row["adapter"] == adapter]
    if len(matches) != 1:
        raise ArtifactIndexError(
            f"Step 10 expected one {adapter} artifact; observed {len(matches)}"
        )
    return matches[0]


def _reconcile_output(
    *,
    row: Mapping[str, str],
    prefix: str,
    table: scientific_context.ContextTable,
    member: Inspection,
) -> None:
    if table.path != member.resolved_path or row[f"{prefix}_path"] != str(
        member.resolved_path
    ):
        raise ArtifactIndexError(
            f"Step 10 receipt {prefix}_path disagrees with the inventory"
        )
    source_row_count = member.source["row_count"] if member.source else None
    if source_row_count != table.row_count:
        raise ArtifactIndexError(
            f"Step 10 receipt {prefix}_row_count disagrees with the inventory"
        )
    if member.snapshot is None or member.snapshot.sha256 != table.sha256:
        raise ArtifactIndexError(
            f"Step 10 receipt {prefix}_sha256 disagrees with the inventory"
        )


def reconcile_step10(
    members: Sequence[Inspection],
    sources: NativeSourceIndex,
) -> None:
    """Re-admit Step 10 and bind its receipt to declared upstream artifacts."""

    receipt = _member_by_adapter(members, "step10_context_receipt_v1")
    try:
        transaction = scientific_context.validate_scientific_context_transaction(
            receipt.resolved_path
        )
    except scientific_context.ContractError as exc:
        raise ArtifactIndexError(str(exc)) from exc

    row = transaction.receipt.rows[0]
    if row["analysis_id"] != receipt.row["scope_id"]:
        raise ArtifactIndexError(
            "Step 10 receipt analysis_id disagrees with inventory scope"
        )

    for prefix, adapter in (
        ("step09_all_sites", "step09_cmh_all_sites_v1"),
        ("step09_significant_sites", "step09_cmh_significant_sites_v1"),
        ("step09_summary", "step09_cmh_summary_v1"),
        ("reference_fasta", "step00c_reference_fasta_v1"),
        ("reference_fai", "step00c_reference_fai_v1"),
    ):
        source = require_referenced_source(
            row=row,
            path_field=f"{prefix}_path",
            hash_field=f"{prefix}_sha256",
            row_count_field=None,
            sources=sources,
        )
        if source.row["adapter"] != adapter:
            raise ArtifactIndexError(
                f"Step 10 {prefix}_path points to the wrong adapter"
            )

    outputs = transaction.outputs
    for prefix, adapter, table in (
        (
            "candidate_context",
            "step10_candidate_context_v1",
            outputs.candidate_context,
        ),
        ("motif_hits", "step10_motif_hits_v1", outputs.motif_hits),
        ("sequence_logo", "step10_sequence_logo_v1", outputs.sequence_logo),
        (
            "motif_statistics",
            "step10_motif_statistics_v1",
            outputs.motif_statistics,
        ),
    ):
        _reconcile_output(
            row=row,
            prefix=prefix,
            table=table,
            member=_member_by_adapter(members, adapter),
        )
