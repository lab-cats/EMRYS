"""Paired-CMH scientific report view projection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from emrys.reporting import ReportProviderError as ReportRenderError

from .candidate_display import (
    CandidateMotifEvidence,
    CandidateSampleEvidence,
    SelectedCandidate,
    SelectedCandidateProjection,
)
from .computational import ComputationalResults
from .constants import BOUNDARY_BANNER, CANDIDATE_TERMINOLOGY
from .figure_models import (
    PRIMARY_SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_GUIDANCE,
    SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_LABELS,
    SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    ScientificFigure,
)
from .scientific_context import ScientificContextResults

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


def _document_view(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    *,
    report_view: str,
    document_title: str,
    banner: str,
    introduction: str,
    end_note: str,
    categories: tuple[dict[str, Any], ...],
    selected_candidate_ids: tuple[str, ...] = (),
    result_links: tuple[dict[str, str], ...] = (),
) -> dict[str, Any]:
    run_id = summary["run_id"]
    return {
        "report_view": report_view,
        "document_title": document_title,
        "heading": document_title,
        "run_id": run_id,
        "boundary_class": f"{report_view}-boundary",
        "banner": banner,
        "introduction": introduction,
        "end_note": end_note,
        "metadata": dict(metadata),
        "categories": categories,
        "selected_candidate_ids": selected_candidate_ids,
        "result_links": result_links,
    }


def _section(section_id: str, title: str, *blocks: dict[str, Any]) -> dict[str, Any]:
    return {"id": section_id, "title": title, "blocks": blocks}


def _category(
    category_id: str,
    title: str,
    *sections: dict[str, Any],
    open: bool | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": category_id,
        "title": title,
        "sections": sections,
    }
    if open is not None:
        result["open"] = open
    return result


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
    result_links: tuple[dict[str, str], ...] = (),
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
        banner=BOUNDARY_BANNER,
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
        result_links=result_links,
        categories=(
            _category(
                "scientific-category",
                "Scientific results",
                _section(
                    "scientific-summary-section",
                    "Scientific summary and selected candidates",
                    *_scientific_summary_blocks(
                        computational_results,
                        computational_unavailable_reason,
                        candidate_display,
                    ),
                ),
                _section(
                    "primary-scientific-figures-section",
                    "Primary findings",
                    *_primary_scientific_blocks(ordered_figures, candidate_display),
                ),
                _section(
                    "supporting-scientific-figures-section",
                    "Supporting scientific analyses appendix",
                    *_scientific_figure_blocks(
                        ordered_figures, SUPPORTING_SCIENTIFIC_FIGURE_IDS
                    ),
                ),
                _section(
                    "figure-guide-section",
                    "Scientific figure guide appendix",
                    *_figure_guide_blocks(ordered_figures),
                ),
                _section(
                    "methods-data-note-section",
                    "Methods and complete-data note",
                    *_methods_data_blocks(
                        computational_results,
                        computational_unavailable_reason,
                        scientific_context_unavailable_reason,
                    ),
                ),
            ),
        ),
    )
