"""Step 09 contract projection plus artifact-source graph reconciliation."""

from __future__ import annotations

from collections.abc import Sequence

from norad.contracts.scientific_evidence import step09

from .models import ArtifactIndexError, Inspection
from .reconcile_native import NativeSourceIndex, require_referenced_source


def reconcile_step09(
    members: Sequence[Inspection],
    sources: NativeSourceIndex,
) -> None:
    all_sites = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_all_sites_v1"
    )
    significant = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_significant_sites_v1"
    )
    summary = next(
        member for member in members if member.row["adapter"] == "step09_cmh_summary_v1"
    )
    mutation = next(
        member
        for member in members
        if member.row["adapter"] == "step09_mutation_spectrum_tsv_v1"
    )
    analysis_id = all_sites.row["scope_id"]
    try:
        _all_table, _significant_table, summary_table, sample_ids = (
            step09.validate_step09_projection(
                all_sites.resolved_path,
                significant.resolved_path,
                summary.resolved_path,
                analysis_id,
                mutation_spectrum=mutation.resolved_path,
            )
        )
    except step09.ContractError as exc:
        raise ArtifactIndexError(str(exc)) from exc

    summary_row = summary_table.rows[0]
    all_samples = list(sample_ids)
    for path_field, hash_field, adapter_id in (
        ("step08_sites_path", "step08_sites_sha256", "step08_sites_v1"),
        ("step08_inputs_path", "step08_inputs_sha256", "step08_inputs_v1"),
    ):
        target = require_referenced_source(
            row=summary_row,
            path_field=path_field,
            hash_field=hash_field,
            row_count_field=None,
            sources=sources,
        )
        if target.row["adapter"] != adapter_id:
            raise ArtifactIndexError(
                f"Step 09 {path_field} points to the wrong adapter"
            )
        if (
            adapter_id == "step08_sites_v1"
            and target.native.get("samples") != all_samples
        ):
            raise ArtifactIndexError(
                "Step 09 result sample order disagrees with Step 08 sites"
            )
