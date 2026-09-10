"""Scientific display formatting and direct rendering of admitted report values."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from emrys.reporting import ReportProviderError as ReportRenderError
from emrys.reporting._run_report.validation import render_html

from .candidate_display import CandidateMotifEvidence, SelectedCandidateProjection
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


def render_scientific_html(
    summary: Mapping[str, Any],
    css: str,
    *,
    scientific_figures: Sequence[ScientificFigure],
    computational_results: ComputationalResults | None = None,
    computational_unavailable_reason: str | None = None,
    scientific_context_results: ScientificContextResults | None = None,
    scientific_context_unavailable_reason: str | None = None,
    candidate_display: SelectedCandidateProjection | None = None,
    result_links: tuple[dict[str, str], ...] = (),
) -> bytes:
    """Render the existing scientific values without a second presentation tree."""

    return render_html(
        summary,
        css,
        report_view="scientific",
        banner=BOUNDARY_BANNER,
        result_links=result_links,
        figures={
            figure.figure_id: figure
            for figure in _ordered_scientific_figures(scientific_figures)
        },
        figure_labels=SCIENTIFIC_FIGURE_LABELS,
        figure_guidance=SCIENTIFIC_FIGURE_GUIDANCE,
        primary_figure_ids=PRIMARY_SCIENTIFIC_FIGURE_IDS,
        supporting_figure_ids=SUPPORTING_SCIENTIFIC_FIGURE_IDS,
        input_labels=_SCIENTIFIC_INPUT_LABELS,
        candidate_terminology=CANDIDATE_TERMINOLOGY,
        computational_results=computational_results,
        computational_unavailable_reason=computational_unavailable_reason,
        scientific_context_unavailable_reason=(
            None
            if scientific_context_results is not None
            else scientific_context_unavailable_reason
        ),
        candidate_display=candidate_display,
        decimal_text=_decimal_text,
        rate_text=_rate_text,
        difference_text=_difference_text,
        motif_index_text=_motif_index_text,
        signed_offset=lambda value: format(value, "+"),
    )
