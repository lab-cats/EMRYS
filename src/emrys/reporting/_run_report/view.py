"""Scientific and operational-evidence projections for static HTML reports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any

from .candidate_display import (
    CandidateMotifEvidence,
    CandidateSampleEvidence,
    SelectedCandidate,
    SelectedCandidateProjection,
)
from .models import (
    BOUNDARY_BANNER,
    CANDIDATE_TERMINOLOGY,
    COMPUTATIONAL_STATUS_FIELDS,
    PRIMARY_SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_GUIDANCE,
    SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_LABELS,
    SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    ComputationalResults,
    ReportRenderError,
    ScientificContextResults,
    ScientificFigure,
)

_SCIENTIFIC_INPUT_LABELS = {
    "all_sites": "tested candidate results",
    "summary": "analysis summary",
    "mutation_spectrum": "mutation spectrum",
    "significant_sites": "threshold-passing candidate results",
    "sample_manifest": "sample manifest and replicate pairs",
    "sequence_logo": "observed sequence-context frequencies",
    "motif_catalog": "registered motif catalog",
    "motif_statistics": "motif position and enrichment statistics",
    "candidate_context": "selected candidate contexts",
    "motif_hits": "exact registered motif hits",
    "receipt": "Step 10 scientific-context receipt",
}


def _display(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _table(
    table_id: str,
    caption: str,
    header: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    row_headers: bool = False,
) -> dict[str, Any]:
    materialized = [tuple(_display(value) for value in row) for row in rows]
    return {
        "kind": "table",
        "id": table_id,
        "caption": caption,
        "header": tuple(header),
        "rows": materialized,
        "row_headers": row_headers,
        "wide": len(header) > 6,
    }


def _key_value_table(
    table_id: str,
    caption: str,
    rows: Iterable[tuple[str, Any]],
) -> dict[str, Any]:
    return _table(
        table_id,
        caption,
        ("Field", "Value"),
        rows,
        row_headers=True,
    )


def _empty(message: str) -> dict[str, Any]:
    return {"kind": "empty", "message": message}


def _note(message: str, *, notice: bool = False) -> dict[str, Any]:
    return {"kind": "note", "message": message, "notice": notice}


def _ordered_scientific_figures(
    figures: Sequence[ScientificFigure],
) -> tuple[ScientificFigure, ...]:
    ordered = tuple(figures)
    observed_ids = tuple(figure.figure_id for figure in ordered)
    if observed_ids != SCIENTIFIC_FIGURE_IDS:
        raise ReportRenderError(
            "Scientific figures must use the fixed ordered roster: "
            + ", ".join(SCIENTIFIC_FIGURE_IDS)
        )
    panel_ids: list[str] = []
    for figure in ordered:
        figure.validate()
        panel_ids.extend(asset.panel_id for asset in figure.assets)
    if len(panel_ids) != len(set(panel_ids)):
        raise ReportRenderError("Scientific figure panel IDs must be globally unique")
    return ordered


def _scientific_figure_blocks(
    figures: Sequence[ScientificFigure],
    figure_ids: Sequence[str],
) -> tuple[dict[str, Any], ...]:
    by_id = {figure.figure_id: figure for figure in figures}
    blocks: list[dict[str, Any]] = []
    for figure_id in figure_ids:
        figure = by_id[figure_id]
        guidance = SCIENTIFIC_FIGURE_GUIDANCE[figure_id]
        blocks.append(
            {
                "kind": "scientific_figure",
                "id": figure.figure_id,
                "label": SCIENTIFIC_FIGURE_LABELS[figure_id],
                "title": figure.title,
                "status": figure.status,
                "assets": tuple(
                    {
                        "panel_id": asset.panel_id,
                        "data_uri": asset.data_uri,
                        "alt_text": asset.alt_text,
                    }
                    for asset in figure.assets
                ),
                "takeaway": figure.text_summary,
                "caption": figure.caption,
                "question": guidance["question"],
                "how_to_read": guidance["how_to_read"],
                "population": figure.population,
                "limitations": guidance["limitations"],
                "unavailable_reason": figure.unavailable_reason,
            }
        )
    return tuple(blocks)


def _figure_guide_blocks(
    figures: Sequence[ScientificFigure],
) -> tuple[dict[str, Any], ...]:
    by_id = {figure.figure_id: figure for figure in figures}
    return tuple(
        {
            "kind": "figure_guide",
            "id": f"{figure_id}-guide",
            "figure_id": figure_id,
            "label": SCIENTIFIC_FIGURE_LABELS[figure_id],
            "title": by_id[figure_id].title,
            "question": SCIENTIFIC_FIGURE_GUIDANCE[figure_id]["question"],
            "how_to_read": SCIENTIFIC_FIGURE_GUIDANCE[figure_id]["how_to_read"],
            "input_roles": ", ".join(
                _SCIENTIFIC_INPUT_LABELS.get(role, role.replace("_", " "))
                for role in by_id[figure_id].input_roles
            ),
            "population": by_id[figure_id].population,
            "limitations": SCIENTIFIC_FIGURE_GUIDANCE[figure_id]["limitations"],
        }
        for figure_id in (
            *PRIMARY_SCIENTIFIC_FIGURE_IDS,
            *SUPPORTING_SCIENTIFIC_FIGURE_IDS,
        )
    )


def _summary_row(results: ComputationalResults) -> dict[str, str]:
    return dict(
        zip(results.summary.header, results.summary.display_rows[0], strict=True)
    )


def _scientific_summary_blocks(
    results: ComputationalResults | None,
    unavailable_reason: str | None,
    candidate_display: SelectedCandidateProjection | None,
) -> tuple[dict[str, Any], ...]:
    boundary = _note(
        "COMPUTATIONAL RESULTS — NOT SCIENTIFICALLY ADJUDICATED. "
        f"Threshold-passing rows are {CANDIDATE_TERMINOLOGY}, not validated "
        "RNA-editing sites or biological conclusions.",
        notice=True,
    )
    if results is None:
        return (
            boundary,
            _empty(
                unavailable_reason
                or (
                    "The exact complete primary-analysis Step 09 source bundle is "
                    "not available. No computational candidate row was inferred."
                )
            ),
        )
    summary = _summary_row(results)
    blocks: list[dict[str, Any]] = [
        boundary,
        {
            "kind": "metric_grid",
            "id": "scientific-kpis",
            "metrics": (
                {"label": "Samples", "value": len(results.sample_ids)},
                {"label": "Replicate pairs", "value": summary["replicate_count"]},
                {
                    "label": "Successfully tested",
                    "value": summary["successfully_tested_count"],
                },
                {"label": "Significant up", "value": summary["significant_up_count"]},
                {
                    "label": "Significant down",
                    "value": summary["significant_down_count"],
                },
            ),
        },
        {
            "kind": "fact_grid",
            "id": "scientific-method-summary",
            "title": "Analysis and declared decision rules",
            "facts": (
                ("Analysis", summary["analysis_id"]),
                ("Cohort", summary["cohort_id"]),
                (
                    "Comparison",
                    f"{summary['control_condition']} → {summary['treatment_condition']}",
                ),
                ("Target RNA change", summary["target_rna_change"]),
                ("Minimum sample depth", summary["min_sample_dp"]),
                ("Mean depth threshold", summary["mean_dp_threshold"]),
                ("BH FDR threshold", summary["fdr_threshold"]),
                ("Common odds-ratio threshold", summary["common_or_threshold"]),
                (
                    "Absolute editing-rate difference threshold",
                    summary["absolute_difference_threshold"],
                ),
                ("Background maximum fraction", summary["background_max_fraction"]),
            ),
        },
    ]
    blocks.extend(_candidate_index_blocks(candidate_display))
    return tuple(blocks)


def _decimal_text(value: Decimal | None) -> str:
    if value is None:
        return "Not available"
    return format(value, ".4g")


def _rate_text(value: Decimal | None) -> str:
    if value is None:
        return "Not available"
    return f"{format(value * 100, '.4g')}% (AF {value})"


def _difference_text(value: Decimal | None) -> str:
    if value is None:
        return "Not available"
    return f"{format(value * 100, '+.4g')} percentage points (ΔAF {value})"


def _sample_record(sample: CandidateSampleEvidence) -> dict[str, str]:
    read_support = (
        "Not available"
        if sample.alternate_depth is None or sample.total_depth is None
        else f"AD {sample.alternate_depth} / DP {sample.total_depth}"
    )
    return {
        "sample_id": sample.sample_id,
        "editing_rate": _rate_text(sample.allele_fraction),
        "read_support": read_support,
    }


def _motif_index_text(motif: CandidateMotifEvidence) -> str:
    if motif.state == "present":
        count = len(motif.hits)
        nearest = min(
            motif.hits,
            key=lambda hit: (
                abs(hit.midpoint_offset),
                hit.midpoint_offset,
                hit.start_offset,
                hit.matched_sequence,
            ),
        )
        return (
            f"{count} exact registered {motif.motif_id} "
            f"hit{'s' if count != 1 else ''}; nearest midpoint "
            f"{nearest.midpoint_offset:+} nt"
        )
    if motif.state == "no_registered_hit":
        return f"No exact registered {motif.motif_id} hit in the admitted context"
    if motif.state == "boundary_unavailable":
        return "Unavailable: admitted context crosses a contig boundary"
    return "Unavailable: Step 10 scientific context was not admitted"


def _candidate_index_record(
    candidate: SelectedCandidate,
    projection: SelectedCandidateProjection,
) -> dict[str, str | int]:
    location = candidate.location
    memberships = ", ".join(location.region_memberships) or "No recorded overlap"
    return {
        "rank": candidate.display_rank,
        "candidate_id": candidate.candidate_id,
        "gene_ids": ", ".join(location.gene_ids) or "No recorded gene",
        "call_status": candidate.call_status,
        "editing_rate": (
            f"{projection.control_condition}: {_rate_text(candidate.mean_control_af)}; "
            f"{projection.treatment_condition}: "
            f"{_rate_text(candidate.mean_treatment_af)}; "
            f"Δ {_difference_text(candidate.treatment_control_difference)}"
        ),
        "location": (
            f"{location.chromosome}:{location.position_1based}; "
            f"RNA {location.rna_ref}>{location.rna_alt}; {memberships}"
        ),
        "motif": _motif_index_text(candidate.motif),
    }


def _candidate_record(
    candidate: SelectedCandidate,
    projection: SelectedCandidateProjection,
) -> dict[str, Any]:
    location = candidate.location
    motif = candidate.motif
    region_memberships = ", ".join(location.region_memberships) or (
        "No recorded transcript-region overlap"
    )
    context_window = (
        "Not available"
        if motif.window_start_1based is None or motif.window_end_1based is None
        else (
            f"{location.chromosome}:{motif.window_start_1based}-"
            f"{motif.window_end_1based}; registered radius ±{motif.context_radius} nt"
        )
    )
    exact_hit_count = (
        str(len(motif.hits))
        if motif.state in {"present", "no_registered_hit"}
        else "Not available under the admitted context policy"
    )
    motif_definition = (
        "Not admitted because the Step 10 scientific-context transaction is unavailable"
        if motif.state == "step10_unavailable"
        else f"{motif.motif_id}; RNA {motif.rna_consensus}; DNA {motif.dna_consensus}"
    )
    motif_facts = (
        ("Registered motif", motif_definition),
        ("Match policy", motif.match_policy or "Not admitted"),
        ("Admitted context window", context_window),
        ("Context state", motif.context_status or motif.state),
        ("Context orientation action", motif.orientation_action or "Not available"),
        ("Exact admitted hit count", exact_hit_count),
        ("Result", _motif_index_text(motif)),
        (
            "Display relationship",
            "All admitted hits across the registered context are listed below. "
            f"{SCIENTIFIC_FIGURE_LABELS['selected-context-track-figure']} highlights "
            "only spans intersecting its ±25-nt sequence "
            "panel; hits outside that panel remain listed here.",
        ),
    )
    motif_hits = tuple(
        (
            f"{hit.motif_id} {hit.matched_sequence}: offsets "
            f"{hit.start_offset:+d} to {hit.end_offset:+d}; midpoint "
            f"{hit.midpoint_offset:+} nt"
        )
        for hit in motif.hits
    )
    return {
        "id": f"candidate-evidence-{candidate.display_rank}",
        "rank": candidate.display_rank,
        "candidate_id": candidate.candidate_id,
        "call_status": candidate.call_status,
        "groups": (
            {
                "title": "Editing rate",
                "facts": (
                    (
                        f"{projection.control_condition} mean",
                        _rate_text(candidate.mean_control_af),
                    ),
                    (
                        f"{projection.treatment_condition} mean",
                        _rate_text(candidate.mean_treatment_af),
                    ),
                    (
                        "Treatment − control",
                        _difference_text(candidate.treatment_control_difference),
                    ),
                    ("Mean analysis depth", _decimal_text(candidate.mean_analysis_dp)),
                ),
            },
            {
                "title": "Location",
                "facts": (
                    (
                        "Coordinate (1-based)",
                        f"{location.chromosome}:{location.position_1based}",
                    ),
                    (
                        "Change",
                        f"genomic {location.genomic_ref}>{location.genomic_alt}; "
                        f"RNA {location.rna_ref}>{location.rna_alt}",
                    ),
                    ("Workflow orientation", location.workflow_orientation),
                    ("Admitted orientation policy", location.orientation_policy),
                    ("Annotation strand (carried)", location.annotation_strand),
                    ("Genes", ", ".join(location.gene_ids) or "Not available"),
                    (
                        "Recorded transcripts (no isoform selected)",
                        ", ".join(location.transcript_ids) or "Not available",
                    ),
                    ("Region memberships", region_memberships),
                ),
            },
            {
                "title": "Statistical evidence",
                "facts": (
                    ("Call status", candidate.call_status),
                    ("BH FDR", _decimal_text(candidate.cmh_fdr_bh)),
                    ("Common odds ratio", _decimal_text(candidate.common_odds_ratio)),
                ),
            },
            {
                "title": "Nearby motifs",
                "facts": motif_facts,
            },
        ),
        "pairs": tuple(
            {
                "replicate": pair.replicate,
                "control_label": projection.control_condition,
                "control": _sample_record(pair.control),
                "treatment_label": projection.treatment_condition,
                "treatment": _sample_record(pair.treatment),
            }
            for pair in candidate.pairs
        ),
        "motif_hits": motif_hits,
        "motif_unavailable_reason": motif.unavailable_reason,
    }


def _candidate_index_blocks(
    candidate_display: SelectedCandidateProjection | None,
) -> tuple[dict[str, Any], ...]:
    """Build the narrow summary index without ranking or joining."""

    if candidate_display is None:
        return (
            _empty(
                "Selected candidate evidence is unavailable because no shared "
                "candidate-display projection was supplied."
            ),
        )
    if not candidate_display.candidates:
        return (
            _empty(
                "No threshold-passing candidates are available for the bounded "
                "selected-candidate display."
            ),
        )
    index_records = tuple(
        _candidate_index_record(candidate, candidate_display)
        for candidate in candidate_display.candidates
    )
    selection_label = (
        "the admitted Step 10 display order"
        if candidate_display.selection_source == "step10_display_rank"
        else "the fixed Step 09 fallback display rule"
    )
    return (
        {
            "kind": "candidate_index",
            "id": "selected-candidate-index",
            "caption": (
                "Selected candidate index: editing rate, location, and nearby "
                "registered motifs"
            ),
            "selection_note": (
                f"Showing {len(candidate_display.candidates)} of "
                f"{candidate_display.significant_candidate_count} threshold-passing "
                f"candidates using {selection_label}."
            ),
            "records": index_records,
        },
    )


def _candidate_record_blocks(
    candidate_display: SelectedCandidateProjection | None,
) -> tuple[dict[str, Any], ...]:
    """Build primary vertical evidence records from the shared projection."""

    if candidate_display is None:
        return ()
    return tuple(
        {
            "kind": "candidate_record",
            "record": _candidate_record(candidate, candidate_display),
        }
        for candidate in candidate_display.candidates
    )


def _methods_data_blocks(
    results: ComputationalResults | None,
    unavailable_reason: str | None,
    scientific_context_unavailable_reason: str | None,
) -> tuple[dict[str, Any], ...]:
    if results is None:
        source_note = unavailable_reason or "Step 09 computational results unavailable."
    else:
        all_sites_rows = results.all_sites.row_count
        significant_rows = results.significant_sites.row_count
        source_note = (
            f"The complete admitted Step 09 all-sites ({all_sites_rows} "
            f"{'row' if all_sites_rows == 1 else 'rows'}) and threshold-passing "
            f"({significant_rows} {'row' if significant_rows == 1 else 'rows'}) "
            "TSVs remain canonical data artifacts. They are not reproduced as wide "
            "HTML tables; exact paths and hashes are recorded in the operational "
            "evidence report."
        )
    context_note = scientific_context_unavailable_reason or (
        "Step 10 candidate context and exact registered-motif hits were admitted "
        "for the selected-candidate display projection."
    )
    return (
        _note(source_note),
        _note(context_note),
        _note(
            "The selected index and vertical evidence records are a bounded display "
            "projection. They do not replace the complete admitted TSVs and do not "
            "constitute a new biological ranking."
        ),
    )


def _step09_sources(
    results: ComputationalResults | None,
    unavailable_reason: str | None,
) -> dict[str, Any]:
    if results is None:
        return _empty(
            unavailable_reason
            or "The exact complete primary-analysis Step 09 source set is unavailable."
        )
    return _table(
        "step09-source-records",
        "Exact completed Step 09 sources and its hash-bound sample manifest "
        "admitted for report generation",
        ("Role", "Artifact ID", "Source path", "SHA-256", "Bytes", "Rows"),
        (
            *(
                (
                    table.role,
                    table.artifact_id,
                    table.path,
                    table.sha256,
                    table.size_bytes,
                    table.row_count,
                )
                for table in results.tables
            ),
            (
                results.sample_manifest.role,
                "Step 09 summary-bound input",
                results.sample_manifest.path,
                results.sample_manifest.sha256,
                results.sample_manifest.size_bytes,
                len(results.sample_manifest.sample_ids),
            ),
        ),
    )


def _scientific_context_sources(
    results: ScientificContextResults | None,
    unavailable_reason: str | None,
) -> dict[str, Any]:
    if results is None:
        return _empty(
            unavailable_reason
            or "The complete primary-analysis Step 10 source set is unavailable."
        )
    return _table(
        "step10-source-records",
        "Exact completed Step 10 records and every receipt-bound input admitted "
        "for report generation",
        ("Role", "Artifact ID", "Source path", "SHA-256", "Bytes", "Rows"),
        (
            *(
                (
                    table.role,
                    table.artifact_id,
                    table.path,
                    table.sha256,
                    table.size_bytes,
                    table.row_count,
                )
                for table in results.tables
            ),
            *(
                (
                    source.role,
                    source.artifact_id,
                    source.path,
                    source.sha256,
                    source.size_bytes,
                    source.row_count,
                )
                for source in results.bound_inputs
            ),
        ),
    )


def _scientific_context_policy(
    results: ScientificContextResults | None,
    unavailable_reason: str | None,
) -> dict[str, Any]:
    if results is None:
        return _empty(
            unavailable_reason
            or "No Step 10 receipt policy is available for this report."
        )
    receipt = results.receipt_metadata
    fields = (
        ("Scientific-context schema", "scientific_context_schema_version"),
        ("Orientation policy", "context_orientation_policy"),
        ("Context radius", "context_radius"),
        ("Logo radius", "logo_radius"),
        ("Display limit", "display_limit"),
        ("Motif match policy", "motif_match_policy"),
        ("Motif distance policy", "motif_distance_policy"),
        ("Motif distance-bin width", "motif_distance_bin_width"),
        ("Foreground", "foreground_population"),
        ("Comparison background", "background_population"),
        ("Separate population", "separate_population"),
        ("Foreground minimum", "foreground_minimum_count"),
        ("Background minimum", "background_minimum_count"),
        ("Separate-population minimum", "separate_minimum_count"),
        ("Enrichment test", "enrichment_test"),
        ("Enrichment alternative", "enrichment_alternative"),
        ("Multiple-testing method", "multiple_testing_method"),
        ("Producer", "producer"),
        ("Producer version", "producer_version"),
        ("R version", "r_version"),
        ("Biostrings version", "biostrings_version"),
        ("Rsamtools version", "rsamtools_version"),
        ("Producer Git commit", "git_commit"),
    )
    return _key_value_table(
        "step10-policy-record",
        "Receipt-bound scientific-context policies and software",
        ((label, receipt[field]) for label, field in fields),
    )


def _artifact_overview(summary: Mapping[str, Any]) -> dict[str, Any]:
    rollup = summary["computational_rollup"]
    categories = (
        ("complete", rollup["complete_artifact_count"], "#287a5d"),
        ("missing", rollup["missing_artifact_count"], "#64748b"),
        ("incomplete", rollup["incomplete_artifact_count"], "#b7791f"),
        ("failed", rollup["failed_artifact_count"], "#b42318"),
        (
            "externally unavailable",
            rollup["externally_unavailable_artifact_count"],
            "#6b5ca5",
        ),
    )
    total = rollup["expected_artifact_count"]
    width = 720
    cursor = 0.0
    segments = []
    legend = []
    for name, count, color in categories:
        segment_width = width * count / total if total else 0
        if count:
            segments.append(
                {
                    "x": f"{cursor:.3f}",
                    "width": f"{segment_width:.3f}",
                    "color": color,
                    "name": name,
                    "count": count,
                }
            )
        legend.append({"name": name, "count": count})
        cursor += segment_width
    return {
        "kind": "artifact_overview",
        "width": width,
        "height": 82,
        "total": total,
        "segments": segments,
        "legend": legend,
        "description": ", ".join(f"{name}: {count}" for name, count, _ in categories),
    }


def _status_blocks(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    rollup = summary["computational_rollup"]
    failed = [
        item["scope"]
        for item in summary["expected_scopes"]
        if item["aggregate_state"] == "failed"
    ]
    failed_block = (
        {
            "kind": "notice_list",
            "title": "Failed expected scopes",
            "items": [
                f"{scope['step_id']} {scope['scope_type']} {scope['scope_id']} failed"
                for scope in failed
            ],
        }
        if failed
        else _note("Failed expected scopes: none.")
    )
    return [
        {
            "kind": "panel_grid",
            "panels": (
                {
                    "title": "Computational status",
                    "block": _key_value_table(
                        "computational-status",
                        "Computational status dimensions",
                        (
                            (label, rollup[field])
                            for label, field in COMPUTATIONAL_STATUS_FIELDS
                        ),
                    ),
                },
                {
                    "title": "Interpretation boundary",
                    "block": _key_value_table(
                        "interpretation-boundary",
                        "Fixed EMRYS output boundary",
                        (
                            ("Boundary", summary["interpretation_boundary"]),
                            ("Candidate terminology", summary["candidate_terminology"]),
                            ("Biological validation", "outside EMRYS"),
                        ),
                    ),
                },
            ),
        },
        _artifact_overview(summary),
        failed_block,
    ]


def _run_identity(summary: Mapping[str, Any]) -> dict[str, Any]:
    contract = summary["run_contract"]
    return _key_value_table(
        "run-identity",
        "Immutable run identity and explicit source records",
        (
            ("Run ID", summary["run_id"]),
            ("Run-summary schema", summary["schema_version"]),
            ("Summary state", summary["summary_state"]),
            ("Generated at", summary["generated_at"]),
            ("Run-contract SHA-256", contract["run_contract_sha256"]),
            ("Sample-manifest SHA-256", contract["sample_manifest_sha256"]),
            ("Reference-contract SHA-256", contract["reference_contract_sha256"]),
            ("Partition-manifest SHA-256", contract["partition_manifest_sha256"]),
            ("Primary analysis ID", contract["primary_analysis_id"]),
            (
                "Primary-analysis-policy SHA-256",
                contract["primary_analysis_policy_sha256"],
            ),
            ("Inventory path", summary["inventory"]["path"]),
            ("Inventory SHA-256", summary["inventory"]["sha256"]),
            ("Artifact receipt path", summary["artifact_receipt"]["path"]),
            ("Artifact receipt SHA-256", summary["artifact_receipt"]["sha256"]),
        ),
    )


def _scope_matrix(summary: Mapping[str, Any]) -> dict[str, Any]:
    return _table(
        "expected-scope-matrix",
        "Every expected computational scope, including explicit incomplete states",
        (
            "Step",
            "Scope type",
            "Scope ID",
            "Evidence state",
            "Implementation",
            "Local test",
            "Runtime",
            "Cluster dry-run",
            "Cluster proof",
            "Artifact IDs",
        ),
        (
            (
                item["scope"]["step_id"],
                item["scope"]["scope_type"],
                item["scope"]["scope_id"],
                item["aggregate_state"],
                *(item[field] for _, field in COMPUTATIONAL_STATUS_FIELDS),
                ", ".join(item["artifact_ids"]),
            )
            for item in summary["expected_scopes"]
        ),
    )


def _qc_metrics(summary: Mapping[str, Any]) -> dict[str, Any]:
    promoted = {metric["metric_id"] for metric in summary["qc_metrics"]}
    rows = [
        (
            artifact["artifact_id"],
            metric["metric_id"],
            metric["name"],
            metric["value"],
            metric["unit"],
            metric["status"],
            metric["metric_id"] in promoted,
        )
        for artifact in summary["artifacts"]
        for metric in artifact["metrics"]
    ]
    if not rows:
        return _empty("No artifact-level QC metrics are present.")
    return _table(
        "qc-metrics",
        "Canonical artifact-level QC metrics in stable artifact order",
        (
            "Artifact",
            "Metric ID",
            "Name",
            "Value",
            "Unit",
            "Status",
            "Globally promoted",
        ),
        rows,
    )


def _limitations(summary: Mapping[str, Any]) -> dict[str, Any]:
    limitations = summary["limitations"]
    if not limitations:
        return _empty("No computational limitations are recorded in the run summary.")
    return _table(
        "limitations",
        "Recorded computational limitations and their impact",
        ("Limitation", "Status", "Description", "Impact", "Evidence IDs"),
        (
            (
                item["limitation_id"],
                item["status"],
                item["description"],
                item["impact"],
                ", ".join(item["evidence_ids"]) or "None declared",
            )
            for item in limitations
        ),
    )


def _attempt_lineage(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    attempts = summary["attempts"]
    attempt_block = (
        _table(
            "run-attempt-lineage",
            "Immutable run execution-attempt lineage",
            (
                "Attempt ID",
                "State",
                "Started",
                "Finished",
                "Exit code",
                "Supersedes",
                "Evidence count",
                "Warnings",
                "Errors",
            ),
            (
                (
                    item["attempt_id"],
                    item["state"],
                    item["started_at"],
                    item["finished_at"],
                    item["exit_code"],
                    item["supersedes_attempt_id"],
                    len(item["evidence"]),
                    len(item["warnings"]),
                    len(item["errors"]),
                )
                for item in attempts
            ),
        )
        if attempts
        else _empty("No execution-attempt lineage is recorded.")
    )
    selections = _table(
        "artifact-attempt-selections",
        "Selected and superseded attempt references by artifact",
        (
            "Artifact ID",
            "Selected attempt",
            "Attempt provenance",
            "Artifact attempt IDs",
        ),
        (
            (
                artifact["artifact_id"],
                artifact["selected_attempt_id"],
                artifact["attempt_provenance_status"],
                ", ".join(item["attempt_id"] for item in artifact["attempts"])
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )
    return [
        attempt_block,
        selections,
        _note(
            "Superseded run attempt IDs: "
            + (", ".join(summary["superseded_attempt_ids"]) or "None")
            + "."
        ),
    ]


def _artifact_appendix(summary: Mapping[str, Any]) -> dict[str, Any]:
    return _table(
        "artifact-evidence-index",
        "Expected artifact evidence and selected source records",
        (
            "Artifact ID",
            "Step",
            "Scope type",
            "Scope ID",
            "Required",
            "Availability",
            "Completion",
            "State reason",
            "Source path",
            "Source SHA-256",
            "Warning detail",
            "Error detail",
        ),
        (
            (
                artifact["artifact_id"],
                artifact["scope"]["step_id"],
                artifact["scope"]["scope_type"],
                artifact["scope"]["scope_id"],
                artifact["expectation"]["required"],
                artifact["availability_status"],
                artifact["completion_status"],
                artifact["state_reason"],
                artifact["source"]["path"] if artifact["source"] else None,
                artifact["source"]["sha256"] if artifact["source"] else None,
                "; ".join(
                    f"{issue['code']}: {issue['message']}"
                    for issue in artifact["warnings"]
                )
                or "None",
                "; ".join(
                    f"{issue['code']}: {issue['message']}"
                    for issue in artifact["errors"]
                )
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )


def _tools_and_issues(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    tools = (
        _table(
            "software-provenance",
            "Aggregate software provenance",
            ("Tool", "Version", "Role", "Path", "SHA-256"),
            (
                (
                    tool["name"],
                    tool["version"],
                    tool["role"],
                    tool["path"],
                    tool["sha256"],
                )
                for tool in summary["tools"]
            ),
        )
        if summary["tools"]
        else _empty("No aggregate software records are declared.")
    )
    issue_rows = [
        (
            level[:-1],
            issue["code"],
            issue["message"],
            ", ".join(issue["related_artifact_ids"]) or "None declared",
            ", ".join(item["evidence_id"] for item in issue["evidence"])
            or "None declared",
        )
        for level in ("warnings", "errors")
        for issue in summary[level]
    ]
    issues = (
        _table(
            "run-summary-issues",
            "Aggregate warnings and errors",
            ("Level", "Code", "Message", "Artifact IDs", "Evidence IDs"),
            issue_rows,
        )
        if issue_rows
        else _empty("No aggregate run-summary warnings or errors are recorded.")
    )
    return [tools, issues]


def _report_provenance(metadata: Mapping[str, str]) -> dict[str, Any]:
    return _key_value_table(
        "report-renderer-provenance",
        "Static report renderer provenance",
        (
            ("Run-summary input", metadata["run_summary_path"]),
            ("Run-summary input SHA-256", metadata["run_summary_sha256"]),
            ("Renderer", f"{metadata['renderer']} {metadata['renderer_version']}"),
            ("Jinja2 version", metadata["jinja_version"]),
            (
                "Figure renderer",
                f"{metadata['figure_renderer']} {metadata['figure_renderer_version']}",
            ),
            (
                "Logo renderer",
                f"{metadata['logo_renderer']} {metadata['logo_renderer_version']}",
            ),
            ("Figure format", metadata["figure_format"]),
            ("Figure policy version", metadata["figure_policy_version"]),
            ("HTML template", metadata["template_path"]),
            ("HTML template SHA-256", metadata["template_sha256"]),
            ("CSS resource", metadata["css_path"]),
            ("CSS resource SHA-256", metadata["css_sha256"]),
        ),
    )


def _scientific_figure_provenance(
    figures: Sequence[ScientificFigure],
) -> dict[str, Any]:
    ordered = _ordered_scientific_figures(figures)
    rows = tuple(
        (
            figure.figure_id,
            figure.status,
            ", ".join(figure.input_roles),
            figure.mapping,
            figure.population,
            "; ".join(f"{asset.panel_id}={asset.svg_sha256}" for asset in figure.assets)
            or "Not applicable",
            "; ".join(
                f"{asset.panel_id}={asset.svg_size_bytes}" for asset in figure.assets
            )
            or "Not applicable",
            figure.unavailable_reason or "None",
        )
        for figure in ordered
    )
    return _table(
        "scientific-figure-provenance",
        "Fixed scientific-figure inputs, mappings, outputs, and availability",
        (
            "Figure ID",
            "Status",
            "Input roles",
            "Mapping",
            "Population",
            "SVG asset SHA-256",
            "SVG asset bytes",
            "Unavailable reason",
        ),
        rows,
    )


def _document_view(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    *,
    report_view: str,
    document_title: str,
    heading: str,
    banner: str,
    boundary_class: str,
    introduction: str,
    end_note: str,
    categories: tuple[dict[str, Any], ...],
    selected_candidate_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "report_view": report_view,
        "document_title": document_title,
        "heading": heading,
        "run_id": summary["run_id"],
        "boundary_class": boundary_class,
        "banner": banner,
        "introduction": introduction,
        "end_note": end_note,
        "metadata": dict(metadata),
        "categories": categories,
        "selected_candidate_ids": selected_candidate_ids,
    }


def _primary_scientific_blocks(
    figures: Sequence[ScientificFigure],
    candidate_display: SelectedCandidateProjection | None,
) -> tuple[dict[str, Any], ...]:
    """Keep the print-first summary-to-landscape-to-candidate narrative order."""

    return (
        *_scientific_figure_blocks(figures, ("candidate-landscape-figure",)),
        *_scientific_figure_blocks(figures, ("selected-context-track-figure",)),
        *_candidate_record_blocks(candidate_display),
        *_scientific_figure_blocks(
            figures,
            (
                "location-membership-figure",
                "motif-context-enrichment-figure",
            ),
        ),
    )


def build_scientific_view(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    *,
    scientific_figures: Sequence[ScientificFigure],
    computational_results: ComputationalResults | None = None,
    computational_unavailable_reason: str | None = None,
    scientific_context_results: ScientificContextResults | None = None,
    scientific_context_unavailable_reason: str | None = None,
    candidate_display: SelectedCandidateProjection | None = None,
) -> dict[str, Any]:
    """Build the scientific interpretation view without operational provenance."""

    ordered_figures = _ordered_scientific_figures(scientific_figures)
    if scientific_context_results is not None:
        scientific_context_unavailable_reason = None
    return _document_view(
        summary,
        metadata,
        report_view="scientific",
        document_title=f"EMRYS scientific report: {summary['run_id']}",
        heading=f"EMRYS scientific report: {summary['run_id']}",
        banner=BOUNDARY_BANNER,
        boundary_class="scientific-boundary",
        introduction=(
            "This read-only scientific view reports the completed Step 09 "
            f"analysis as {CANDIDATE_TERMINOLOGY}. It does not claim biological "
            "validation or validated RNA-editing sites."
        ),
        end_note=(
            "End of scientific report. Biological validation remains outside EMRYS."
        ),
        selected_candidate_ids=(
            tuple(candidate.candidate_id for candidate in candidate_display.candidates)
            if candidate_display is not None
            else ()
        ),
        categories=(
            {
                "id": "scientific-category",
                "title": "Scientific results",
                "open": True,
                "sections": (
                    {
                        "id": "scientific-summary-section",
                        "title": "Scientific summary and selected candidates",
                        "blocks": _scientific_summary_blocks(
                            computational_results,
                            computational_unavailable_reason,
                            candidate_display,
                        ),
                    },
                    {
                        "id": "primary-scientific-figures-section",
                        "title": "Primary findings",
                        "blocks": _primary_scientific_blocks(
                            ordered_figures,
                            candidate_display,
                        ),
                    },
                    {
                        "id": "supporting-scientific-figures-section",
                        "title": "Supporting scientific analyses appendix",
                        "blocks": _scientific_figure_blocks(
                            ordered_figures,
                            SUPPORTING_SCIENTIFIC_FIGURE_IDS,
                        ),
                    },
                    {
                        "id": "figure-guide-section",
                        "title": "Scientific figure guide appendix",
                        "blocks": _figure_guide_blocks(ordered_figures),
                    },
                    {
                        "id": "methods-data-note-section",
                        "title": "Methods and complete-data note",
                        "blocks": _methods_data_blocks(
                            computational_results,
                            computational_unavailable_reason,
                            scientific_context_unavailable_reason,
                        ),
                    },
                ),
            },
        ),
    )


def build_evidence_view(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    *,
    scientific_figures: Sequence[ScientificFigure],
    computational_results: ComputationalResults | None = None,
    computational_unavailable_reason: str | None = None,
    scientific_context_results: ScientificContextResults | None = None,
    scientific_context_unavailable_reason: str | None = None,
) -> dict[str, Any]:
    """Build the operational evidence and provenance view without candidate rows."""

    return _document_view(
        summary,
        metadata,
        report_view="evidence",
        document_title=f"EMRYS operational evidence report: {summary['run_id']}",
        heading=f"EMRYS operational evidence report: {summary['run_id']}",
        banner=BOUNDARY_BANNER,
        boundary_class="evidence-boundary",
        introduction=(
            "This read-only view records operational status, evidence, and "
            "provenance. It does not display Step 09 candidate rows and does not "
            "provide scientific or biological interpretation."
        ),
        end_note=(
            "End of operational evidence report. Report generation did not change "
            "any computational status."
        ),
        categories=(
            {
                "id": "overview-category",
                "title": "Run overview",
                "open": True,
                "sections": (
                    {
                        "id": "run-identity-section",
                        "title": "Run identity",
                        "blocks": (_run_identity(summary),),
                    },
                    {
                        "id": "status-section",
                        "title": "Computational status",
                        "blocks": tuple(_status_blocks(summary)),
                    },
                    {
                        "id": "limitations-section",
                        "title": "Computational limitations",
                        "blocks": (_limitations(summary),),
                    },
                    {
                        "id": "scope-matrix-section",
                        "title": "Expected computational scopes",
                        "blocks": (_scope_matrix(summary),),
                    },
                ),
            },
            {
                "id": "evidence-category",
                "title": "QC and evidence",
                "open": False,
                "sections": (
                    {
                        "id": "step09-sources-section",
                        "title": "Scientific report sources",
                        "blocks": (
                            _step09_sources(
                                computational_results,
                                computational_unavailable_reason,
                            ),
                            _scientific_context_sources(
                                scientific_context_results,
                                scientific_context_unavailable_reason,
                            ),
                            _scientific_context_policy(
                                scientific_context_results,
                                scientific_context_unavailable_reason,
                            ),
                        ),
                    },
                    {
                        "id": "qc-metrics-section",
                        "title": "QC metrics",
                        "blocks": (_qc_metrics(summary),),
                    },
                    {
                        "id": "attempt-lineage-section",
                        "title": "Attempt lineage",
                        "blocks": tuple(_attempt_lineage(summary)),
                    },
                    {
                        "id": "artifact-appendix-section",
                        "title": "Artifact appendix",
                        "blocks": (_artifact_appendix(summary),),
                    },
                ),
            },
            {
                "id": "provenance-category",
                "title": "Provenance",
                "open": False,
                "sections": (
                    {
                        "id": "tools-issues-section",
                        "title": "Tools and issues",
                        "blocks": tuple(_tools_and_issues(summary)),
                    },
                    {
                        "id": "report-provenance-section",
                        "title": "Report provenance",
                        "blocks": (
                            _report_provenance(metadata),
                            _scientific_figure_provenance(scientific_figures),
                        ),
                    },
                ),
            },
        ),
    )
