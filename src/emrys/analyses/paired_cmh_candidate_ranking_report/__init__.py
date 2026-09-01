"""Built-in paired-CMH scientific report provider."""

from __future__ import annotations

import base64
import binascii
import os
import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote

from emrys.reporting import (
    AnalysisReportContextV1,
    AnalysisReportInputV1,
    AnalysisScientificReportV1,
    ReportProviderError as ReportRenderError,
    admit_report_input,
    render_report_view,
    reporting_resource_path,
)

from .candidate_display import (
    CandidateMotifEvidence,
    CandidateSampleEvidence,
    SelectedCandidate,
    SelectedCandidateProjection,
    build_candidate_display,
)
from .computational import ComputationalResults, admit_computational_results
from .figures import (
    FIGURE_POLICY_VERSION,
    LOGOMAKER_VERSION,
    MATPLOTLIB_VERSION,
    PRIMARY_SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_GUIDANCE,
    SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_LABELS,
    SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    ScientificFigure,
    build_scientific_figures,
)
from .scientific_context import (
    ScientificContextResults,
    admit_scientific_context_results,
)

CANDIDATE_TERMINOLOGY = "CMH-ranked candidates"
BOUNDARY_BANNER = "COMPUTATIONAL RESULTS — BIOLOGICAL VALIDATION IS OUTSIDE EMRYS."
SCIENTIFIC_REPORT_SECTION_IDS = {
    "scientific-summary-section",
    "primary-scientific-figures-section",
    "supporting-scientific-figures-section",
    "figure-guide-section",
    "methods-data-note-section",
}
_SVG_DATA_URI_PREFIX = "data:image/svg+xml;base64,"


class _PairedScientificInspector(HTMLParser):
    """Collect the paired provider's scientific-view invariants."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.svg_count = 0
        self.details_count = 0
        self.wide_table_wraps = 0
        self.section_stack: list[str] = []
        self.figures: list[dict[str, Any]] = []
        self.current_figure: dict[str, Any] | None = None
        self.guides: list[dict[str, Any]] = []
        self.current_guide: dict[str, Any] | None = None
        self.candidate_index_count = 0
        self.candidate_index_ids: list[str] = []
        self.candidate_records: list[dict[str, Any]] = []
        self.current_candidate: dict[str, Any] | None = None
        self.selected_candidate_counts: list[str | None] = []

    @staticmethod
    def _classes(attributes: Mapping[str, str | None]) -> set[str]:
        return set((attributes.get("class") or "").split())

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        classes = self._classes(attributes)
        if tag == "main":
            self.selected_candidate_counts.append(
                attributes.get("data-selected-candidate-count")
            )
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
        if tag == "svg":
            self.svg_count += 1
        if tag == "details":
            self.details_count += 1
        if "emrys-table-wrap-wide" in classes:
            self.wide_table_wraps += 1
        if "candidate-index-block" in classes:
            self.candidate_index_count += 1
        if "candidate-index-record" in classes and attributes.get("data-candidate-id"):
            self.candidate_index_ids.append(str(attributes["data-candidate-id"]))
        if tag == "article" and "candidate-evidence-record" in classes:
            record = {
                "candidate_id": attributes.get("data-candidate-id"),
                "rank": attributes.get("data-candidate-rank"),
                "groups": set(),
            }
            self.candidate_records.append(record)
            self.current_candidate = record
        if (
            self.current_candidate is not None
            and "candidate-evidence-group" in classes
            and attributes.get("data-evidence-group")
        ):
            self.current_candidate["groups"].add(str(attributes["data-evidence-group"]))
        if tag == "section":
            self.section_stack.append(attributes.get("id") or "")
        if tag == "article" and "figure-guide-entry" in classes:
            guide = {
                "figure_id": attributes.get("data-figure-id"),
                "question": 0,
                "reading": 0,
                "inputs": 0,
                "population": 0,
                "limitations": 0,
            }
            self.guides.append(guide)
            self.current_guide = guide
        if self.current_guide is not None:
            for class_name, field in (
                ("figure-guide-question", "question"),
                ("figure-guide-reading", "reading"),
                ("figure-guide-inputs", "inputs"),
                ("figure-guide-population", "population"),
                ("figure-guide-limitations", "limitations"),
            ):
                if class_name in classes:
                    self.current_guide[field] += 1
        if tag == "figure":
            if self.current_figure is not None:
                raise ReportRenderError("Scientific figures may not be nested")
            if "scientific-figure" in classes:
                figure = {
                    "id": attributes.get("id"),
                    "status": attributes.get("data-figure-status"),
                    "section_id": self.section_stack[-1]
                    if self.section_stack
                    else None,
                    "images": [],
                    "captions": 0,
                    "summaries": 0,
                    "unavailable_messages": 0,
                }
                self.figures.append(figure)
                self.current_figure = figure
        if self.current_figure is not None:
            if tag == "img":
                self.current_figure["images"].append(attributes)
            if tag == "figcaption":
                self.current_figure["captions"] += 1
            if "figure-summary" in classes:
                self.current_figure["summaries"] += 1
            if "figure-unavailable" in classes:
                self.current_figure["unavailable_messages"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "figure" and self.current_figure is not None:
            self.current_figure = None
        if tag == "article" and self.current_guide is not None:
            self.current_guide = None
        if tag == "article" and self.current_candidate is not None:
            self.current_candidate = None
        if tag == "section" and self.section_stack:
            self.section_stack.pop()

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)


def _embedded_svg_error(source: str, label: str) -> str | None:
    if not source.startswith(_SVG_DATA_URI_PREFIX):
        return f"{label} must use an exact embedded SVG data URI"
    try:
        payload = base64.b64decode(
            source[len(_SVG_DATA_URI_PREFIX) :],
            validate=True,
        )
    except (binascii.Error, ValueError):
        return f"{label} has invalid base64 SVG data"
    if not payload or re.search(rb"<svg(?:\s|>)", payload, re.IGNORECASE) is None:
        return f"{label} data URI is not an SVG document"
    return None


def _validate_scientific_html(
    html_bytes: bytes,
    expected_candidate_ids: tuple[str, ...],
) -> None:
    """Retain paired figure and candidate checks at their scientific owner."""

    try:
        content = html_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ReportRenderError("Scientific report is not UTF-8") from exc
    inspector = _PairedScientificInspector()
    try:
        inspector.feed(content)
        inspector.close()
    except ReportRenderError:
        raise
    except Exception as exc:
        raise ReportRenderError(f"Could not inspect scientific report: {exc}") from exc
    errors: list[str] = []
    if inspector.current_figure is not None:
        errors.append("scientific figure lacks a closing figure element")
    expected_figures = (
        *PRIMARY_SCIENTIFIC_FIGURE_IDS,
        *SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    )
    observed_figures = tuple(str(item["id"] or "") for item in inspector.figures)
    if observed_figures != expected_figures:
        errors.append(
            "scientific figure roster must be exactly " + ", ".join(expected_figures)
        )
    for section_id, expected in (
        ("primary-scientific-figures-section", PRIMARY_SCIENTIFIC_FIGURE_IDS),
        ("supporting-scientific-figures-section", SUPPORTING_SCIENTIFIC_FIGURE_IDS),
    ):
        observed = tuple(
            str(item["id"] or "")
            for item in inspector.figures
            if item["section_id"] == section_id
        )
        if observed != expected:
            errors.append(
                f"{section_id} figure grouping must be exactly " + ", ".join(expected)
            )
    for figure in inspector.figures:
        figure_id = str(figure["id"] or "<missing>")
        images = figure["images"]
        if figure["captions"] != 1 or figure["summaries"] != 1:
            errors.append(
                f"scientific figure {figure_id!r} must have one caption and summary"
            )
        if figure["status"] == "available":
            if not images or figure["unavailable_messages"]:
                errors.append(
                    f"available scientific figure {figure_id!r} is incomplete"
                )
            for index, image in enumerate(images, start=1):
                if image.get("id") != f"{figure_id}-image-{index}":
                    errors.append(
                        f"scientific figure {figure_id!r} image {index} has the wrong ID"
                    )
                if error := _embedded_svg_error(
                    image.get("src") or "",
                    f"scientific figure {figure_id!r} panel {index}",
                ):
                    errors.append(error)
        elif figure["status"] == "unavailable":
            if images or figure["unavailable_messages"] != 1:
                errors.append(
                    f"unavailable scientific figure {figure_id!r} is inconsistent"
                )
        else:
            errors.append(f"scientific figure {figure_id!r} has an unknown status")
    observed_guides = tuple(str(item["figure_id"] or "") for item in inspector.guides)
    if observed_guides != expected_figures:
        errors.append("scientific figure guide roster must match the figure roster")
    for guide in inspector.guides:
        if any(
            guide[field] != 1
            for field in ("question", "reading", "inputs", "population", "limitations")
        ):
            errors.append(
                f"scientific figure guide {guide['figure_id']!r} is incomplete"
            )
    observed_candidates = tuple(
        str(record["candidate_id"] or "") for record in inspector.candidate_records
    )
    if inspector.selected_candidate_counts != [str(len(expected_candidate_ids))]:
        errors.append("scientific report selected-candidate count is inconsistent")
    if expected_candidate_ids:
        if inspector.candidate_index_count != 1:
            errors.append("scientific report must contain one selected-candidate index")
        if tuple(inspector.candidate_index_ids) != expected_candidate_ids:
            errors.append("selected-candidate index differs from the expected roster")
        if observed_candidates != expected_candidate_ids:
            errors.append("candidate evidence records differ from the expected roster")
        expected_ranks = tuple(
            str(index) for index in range(1, len(expected_candidate_ids) + 1)
        )
        if (
            tuple(str(record["rank"] or "") for record in inspector.candidate_records)
            != expected_ranks
        ):
            errors.append("candidate evidence record ranks are not contiguous from one")
        required_groups = {"editing-rate", "location", "nearby-motifs"}
        if any(
            not required_groups <= record["groups"]
            for record in inspector.candidate_records
        ):
            errors.append("candidate evidence record lacks a required evidence group")
    elif (
        inspector.candidate_index_count
        or inspector.candidate_index_ids
        or observed_candidates
    ):
        errors.append(
            "scientific report contains unexpected selected-candidate content"
        )
    if inspector.svg_count:
        errors.append("scientific report must not contain raw SVG markup")
    if inspector.details_count:
        errors.append("scientific report must not contain collapsible details content")
    if inspector.wide_table_wraps:
        errors.append(
            "scientific report must not contain horizontally scrollable tables"
        )
    if not SCIENTIFIC_REPORT_SECTION_IDS <= inspector.ids:
        errors.append("scientific report lacks required paired-CMH sections")
    if CANDIDATE_TERMINOLOGY not in content:
        errors.append(
            f"scientific report lacks fixed terminology: {CANDIDATE_TERMINOLOGY}"
        )
    if errors:
        raise ReportRenderError(
            "Paired-CMH scientific report validation failed: " + "; ".join(errors)
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


def render_scientific_report(
    context: AnalysisReportContextV1,
) -> AnalysisScientificReportV1:
    """Render the established paired-CMH scientific view from admitted artifacts."""

    summary = dict(context.run_summary)
    artifacts = {artifact.adapter: artifact for artifact in context.artifacts}
    computational, computational_reason = admit_computational_results(
        summary,
        artifacts,
        source_root=context.artifact_source_root,
    )
    scientific_context, scientific_context_reason = admit_scientific_context_results(
        summary,
        artifacts,
        computational_results=computational,
    )
    candidate_display = build_candidate_display(
        computational,
        scientific_context,
        scientific_context_reason,
    )
    figures = build_scientific_figures(
        computational,
        computational_reason,
        scientific_context,
        scientific_context_reason,
        candidate_display,
    )
    css_path = reporting_resource_path("styles/run_report.css")
    css = admit_report_input(css_path, "report CSS resource").path.read_text(
        encoding="utf-8"
    )
    link_copy = {
        "step09_cmh_significant_sites_v1": (
            "Threshold-passing candidates",
            "Ranked Step 09 result table",
        ),
        "step09_cmh_all_sites_v1": (
            "Complete candidate table",
            "All tested Step 09 candidates",
        ),
        "step10_candidate_context_v1": (
            "Candidate context",
            "Step 10 scientific context",
        ),
    }
    links = tuple(
        {
            "label": link_copy[artifact.adapter][0],
            "description": link_copy[artifact.adapter][1],
            "href": quote(
                Path(
                    os.path.relpath(artifact.path, start=context.output_dir)
                ).as_posix(),
                safe="/._-",
            ),
        }
        for artifact in context.artifacts
        if artifact.adapter in link_copy
    )
    view = build_scientific_view(
        summary,
        {},
        computational_results=computational,
        computational_unavailable_reason=computational_reason,
        scientific_context_results=scientific_context,
        scientific_context_unavailable_reason=scientific_context_reason,
        candidate_display=candidate_display,
        scientific_figures=figures,
        result_links=links,
    )
    html_bytes = render_report_view(view, css)
    _validate_scientific_html(
        html_bytes,
        (
            tuple(item.candidate_id for item in candidate_display.candidates)
            if candidate_display is not None
            else ()
        ),
    )
    input_snapshots = {
        snapshot.path: snapshot
        for results in (computational, scientific_context)
        if results is not None
        for snapshot in results.input_snapshots
    }
    identity_only = {
        source.path
        for source in (
            scientific_context.bound_inputs if scientific_context is not None else ()
        )
        if source.role == "reference_fasta"
    }
    receipt_authorities = {
        source.path: scientific_context.receipt.sha256
        for source in (
            scientific_context.bound_inputs if scientific_context is not None else ()
        )
    }
    return AnalysisScientificReportV1(
        BOUNDARY_BANNER,
        html_bytes,
        tuple(
            AnalysisReportInputV1(
                f"paired-CMH scientific input {path.name!r}",
                path,
                snapshot.sha256,
                path not in identity_only,
                receipt_authorities.get(path),
            )
            for path, snapshot in sorted(
                input_snapshots.items(), key=lambda item: str(item[0])
            )
        ),
        (
            ("Figure renderer", f"Matplotlib {MATPLOTLIB_VERSION}"),
            ("Logo renderer", f"Logomaker {LOGOMAKER_VERSION}"),
            ("Figure format", "inline SVG"),
            ("Figure policy version", FIGURE_POLICY_VERSION),
        ),
        tuple(
            (
                figure.figure_id,
                figure.status,
                ", ".join(figure.input_roles),
                figure.mapping,
                figure.population,
                "; ".join(
                    f"{asset.panel_id}={asset.svg_sha256}" for asset in figure.assets
                )
                or "Not applicable",
                "; ".join(
                    f"{asset.panel_id}={asset.svg_size_bytes}"
                    for asset in figure.assets
                )
                or "Not applicable",
                figure.unavailable_reason or "None",
            )
            for figure in figures
        ),
    )
