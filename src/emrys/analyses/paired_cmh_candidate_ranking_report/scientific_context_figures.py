"""Presentation-only figures from admitted Step 10 scientific-context tables."""

from __future__ import annotations

import csv
import math
import textwrap
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from emrys.contracts.scientific_evidence import scientific_context as owner_context

from .candidate_display import (
    CandidateSampleEvidence,
    SelectedCandidate,
    SelectedCandidateProjection,
)
from .figures import (
    _assert_snapshot,
    _data_uri,
    _fail,
    _logomaker_api,
    _render_svg,
    _short_candidate_id,
)
from emrys.reporting import ReportProviderError as ReportRenderError

from .computational import ComputationalTable
from .figures import (
    SCIENTIFIC_FIGURE_LABELS,
    ScientificFigure,
    ScientificFigurePanel,
)
from .scientific_context import ScientificContextResults

_BASES = ("A", "C", "G", "T")
_BASE_COLORS = {
    "A": "#2f855a",
    "C": "#2563eb",
    "G": "#d97706",
    "T": "#dc2626",
}
_POPULATION_STYLE = {
    "significant_up": ("Significant up", "#dc2626", "o"),
    "background": ("FDR/effect not met", "#6b7280", "s"),
    "significant_down": ("Significant down", "#2563eb", "^"),
}
_PAIR_COLORS = (
    "#2563eb",
    "#dc2626",
    "#059669",
    "#7c3aed",
    "#d97706",
    "#0891b2",
    "#db2777",
    "#4b5563",
)
_MOTIF_PANEL_LINE_WIDTH = 56
_PANEL_CONDITION_LABEL_LIMIT = 18
_PAIR_LEGEND_LIMIT = 4
_TRACK_RADIUS = 25


def _table_rows(table: ComputationalTable) -> tuple[dict[str, str], ...]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    rows = tuple(
        dict(zip(table.header, values, strict=True)) for values in table.display_rows
    )
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    return rows


def _logo_matrices(
    table: ComputationalTable,
) -> dict[str, tuple[str, int, dict[int, dict[str, float]]]]:
    matrices: dict[str, tuple[str, int, dict[int, dict[str, float]]]] = {}
    by_population: dict[str, list[dict[str, str]]] = {}
    for row in _table_rows(table):
        by_population.setdefault(row["population"], []).append(row)
    for population in ("significant_up", "background", "significant_down"):
        rows = by_population.get(population, [])
        if not rows:
            _fail(f"Admitted sequence-logo matrix omits population {population!r}")
        status = rows[0]["availability_status"]
        candidate_count = int(rows[0]["candidate_count"])
        matrix: dict[int, dict[str, float]] = {
            position: {} for position in range(-10, 11)
        }
        for row in rows:
            if (
                row["availability_status"] != status
                or int(row["candidate_count"]) != candidate_count
            ):
                _fail("Admitted sequence-logo population metadata is inconsistent")
            position = int(row["relative_position"])
            base = row["base"]
            value = row["base_fraction"]
            matrix[position][base] = math.nan if value == "NA" else float(value)
        if any(tuple(values) != _BASES for values in matrix.values()):
            _fail("Admitted sequence-logo matrix has the wrong fixed base roster")
        matrices[population] = (status, candidate_count, matrix)
    return matrices


def _logo_frame(matrix: Mapping[int, Mapping[str, float]]) -> Any:
    _logomaker, pandas = _logomaker_api()
    return pandas.DataFrame.from_dict(matrix, orient="index", columns=_BASES)


def _draw_frequency_logo(
    axis: Any,
    matrix: Mapping[int, Mapping[str, float]],
    *,
    title: str,
    mark_edit: bool = True,
    ylabel: str = "Observed base fraction",
) -> None:
    logomaker, _pandas = _logomaker_api()
    missing_positions = tuple(
        position
        for position, values in matrix.items()
        if all(math.isnan(value) for value in values.values())
    )
    display_matrix = {
        position: {
            base: 0.0 if math.isnan(value) else value for base, value in values.items()
        }
        for position, values in matrix.items()
    }
    logomaker.Logo(
        _logo_frame(display_matrix),
        ax=axis,
        color_scheme=_BASE_COLORS,
        stack_order="small_on_top",
        vpad=0.04,
    )
    if mark_edit:
        axis.axvline(0, color="#111827", linewidth=0.7, linestyle="--")
    for position in missing_positions:
        axis.axvspan(
            position - 0.48,
            position + 0.48,
            color="#d1d5db",
            alpha=0.7,
            linewidth=0,
        )
    axis.set_ylim(0.0, 1.0)
    axis.set_title(title, fontsize=9)
    axis.set_xlabel("Position relative to edited base")
    axis.set_ylabel(ylabel)
    axis.grid(True, axis="y", color="#d1d5db", linewidth=0.35, alpha=0.6)


def _registered_motif_matrix(consensus: str) -> dict[int, dict[str, float]]:
    matrix: dict[int, dict[str, float]] = {}
    for position, symbol in enumerate(consensus, start=1):
        matrix[position] = {
            base: (0.25 if symbol == "N" else float(base == symbol)) for base in _BASES
        }
    return matrix


def _sequence_context_logo_figure(
    results: ScientificContextResults,
) -> ScientificFigure:
    matrices = _logo_matrices(results.sequence_logo)

    def draw(figure: Any) -> None:
        for index, population in enumerate(
            ("significant_up", "background", "significant_down"), start=1
        ):
            axis = figure.add_subplot(2, 2, index)
            status, count, matrix = matrices[population]
            label = _POPULATION_STYLE[population][0]
            if status == "available":
                _draw_frequency_logo(
                    axis,
                    matrix,
                    title=f"Observed composition — {label} (n={count})",
                )
            else:
                axis.text(
                    0.5,
                    0.52,
                    f"Unavailable: {status.replace('_', ' ')}\n(n={count})",
                    ha="center",
                    va="center",
                    transform=axis.transAxes,
                )
                axis.set_title(f"Observed composition — {label}", fontsize=9)
                axis.set_axis_off()
        motif_axis = figure.add_subplot(2, 2, 4)
        _draw_frequency_logo(
            motif_axis,
            _registered_motif_matrix(owner_context.MOTIF_DNA_CONSENSUS),
            title=(
                f"Fixed registered reference — RNA "
                f"{owner_context.MOTIF_RNA_CONSENSUS} / DNA "
                f"{owner_context.MOTIF_DNA_CONSENSUS}"
            ),
            mark_edit=False,
            ylabel="Registered symbol weight",
        )
        motif_axis.set_xlabel("Registered motif position")
        figure.suptitle(
            "Observed edit-centered composition (not motif discovery) and fixed PUM reference"
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.98,
            bottom=0.10,
            top=0.90,
            hspace=0.55,
            wspace=0.28,
        )

    svg, digest, size = _render_svg(
        "sequence-context-logo-figure", draw, figsize=(9.0, 7.0)
    )
    availability = ", ".join(
        f"{_POPULATION_STYLE[population][0]}={status} (n={count})"
        for population, (status, count, _matrix) in matrices.items()
    )
    return ScientificFigure(
        figure_id="sequence-context-logo-figure",
        title="Edit-centered sequence context and registered PUM motif",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Observed base-frequency logos centered on the edited nucleotide for "
            "each admitted Step 10 population, alongside the registered PUM "
            f"motif {owner_context.MOTIF_RNA_CONSENSUS}. {availability}."
        ),
        text_summary=(
            "Step 10 population-specific observed sequence frequencies are shown "
            "when their registered minimum population is met; the fixed registered "
            f"PUM motif is RNA {owner_context.MOTIF_RNA_CONSENSUS} (DNA "
            f"{owner_context.MOTIF_DNA_CONSENSUS}). The observed panels are not de "
            "novo motif discovery."
        ),
        caption=(
            "Observed panels consume the complete Step 10 frequency matrix for "
            "positions −10 through +10; reporting does not reopen the reference, "
            "count bases, discover, recover, or infer a motif. The visually separate "
            "fixed-reference panel is a registered comparison, not a result inferred "
            "from the observed panels. T is retained because the admitted "
            "oriented context uses the DNA alphabet. The known PUM model is the "
            "receipt-bound registered catalog entry; its N position is displayed "
            "as equal support for A, C, G, and T. Panels below the producer's fixed "
            "population minimum remain explicitly unavailable; a grey observed "
            "position marks an admitted NA frequency because no canonical base was "
            "observed there, rather than treating missing evidence as zero."
        ),
        input_roles=("sequence_logo", "motif_catalog", "receipt"),
        mapping=(
            "observed glyph height=admitted base_fraction by population and "
            "relative_position; registered glyph height=literal catalog consensus"
        ),
        population=availability,
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _motif_statistics(
    table: ComputationalTable,
) -> tuple[dict[str, str], dict[str, tuple[dict[str, str], ...]]]:
    rows = _table_rows(table)
    enrichment = tuple(row for row in rows if row["statistic_type"] == "enrichment")
    if len(enrichment) != 1:
        _fail("Admitted motif-statistics table lacks its sole enrichment row")
    bins = {
        population: tuple(
            row
            for row in rows
            if row["statistic_type"] == "position_bin"
            and row["population"] == population
        )
        for population in _POPULATION_STYLE
    }
    if any(len(population_rows) != 20 for population_rows in bins.values()):
        _fail("Admitted motif-statistics table lacks its fixed position-bin roster")
    return enrichment[0], bins


def _position_profile_percentages(
    rows: Sequence[Mapping[str, str]],
) -> tuple[tuple[float, ...], tuple[float, ...], int, int]:
    """Project admitted nearest-hit counts onto their population denominator."""

    if not rows:
        _fail("Admitted motif position profile is empty")
    analyzable = int(rows[0]["analyzable_candidate_count"])
    if any(int(row["analyzable_candidate_count"]) != analyzable for row in rows):
        _fail("Admitted motif position profile changes its analyzable denominator")
    midpoints = tuple((int(row["bin_start"]) + int(row["bin_end"])) / 2 for row in rows)
    counts = tuple(int(row["candidate_with_motif_count"]) for row in rows)
    if any(count < 0 or count > analyzable for count in counts):
        _fail("Admitted motif position-bin count exceeds its analyzable population")
    candidate_with_hit_count = sum(counts)
    if candidate_with_hit_count > analyzable:
        _fail("Admitted nearest-hit bins exceed their analyzable candidate population")
    percentages = tuple(
        (100.0 * count / analyzable) if analyzable else 0.0 for count in counts
    )
    return midpoints, percentages, analyzable, candidate_with_hit_count


def _motif_context_enrichment_figure(
    results: ScientificContextResults,
) -> ScientificFigure:
    enrichment, bins = _motif_statistics(results.motif_statistics)
    available_profiles = tuple(
        population
        for population, rows in bins.items()
        if rows[0]["availability_status"] == "available"
    )
    enrichment_available = enrichment["availability_status"] == "available"
    if not available_profiles and not enrichment_available:
        status = enrichment["availability_status"].replace("_", " ")
        return _unavailable_context_figure(
            "motif-context-enrichment-figure",
            "Registered PUM motif position and enrichment",
            ("motif_statistics", "receipt"),
            "x=signed fixed 10-nt position bin; y=admitted nearest-hit candidate "
            "count; enrichment=admitted two-sided Fisher odds ratio, 95% CI, and p",
            (
                "The admitted Step 10 position and enrichment populations do not "
                f"meet their registered availability rules ({status}); no inferential "
                "graphic was generated."
            ),
        )

    def draw(figure: Any) -> None:
        profile_axis = figure.add_subplot(2, 1, 1)
        for population, rows in bins.items():
            label, color, marker = _POPULATION_STYLE[population]
            status = rows[0]["availability_status"]
            if status != "available":
                profile_axis.plot(
                    [],
                    [],
                    color=color,
                    marker=marker,
                    label=f"{label}: unavailable ({status.replace('_', ' ')})",
                )
                continue
            midpoints, percentages, analyzable, with_hit = (
                _position_profile_percentages(rows)
            )
            profile_axis.plot(
                midpoints,
                percentages,
                color=color,
                marker=marker,
                markersize=3.5,
                linewidth=1.1,
                label=(
                    f"{label}: {with_hit}/{analyzable} with a registered hit "
                    f"({(100.0 * with_hit / analyzable) if analyzable else 0.0:.1f}%)"
                ),
            )
        profile_axis.axvline(0, color="#111827", linestyle="--", linewidth=0.8)
        profile_axis.set_xlim(-100, 100)
        profile_axis.set_ylim(bottom=0.0)
        profile_axis.set_ylabel("Analyzable candidates in nearest-hit bin (%)")
        profile_axis.set_xlabel("Signed motif-center offset from edit (nt)")
        profile_axis.set_title("Nearest registered-motif position profile")
        profile_axis.grid(True, color="#d1d5db", linewidth=0.4, alpha=0.65)
        profile_axis.legend(loc="best", frameon=True)

        enrichment_axis = figure.add_subplot(2, 1, 2)
        enrichment_axis.set_title(
            "Significant-up versus comparison-background enrichment"
        )
        if enrichment_available:
            odds = float(enrichment["odds_ratio"])
            lower = float(enrichment["odds_ratio_ci95_lower"])
            upper = float(enrichment["odds_ratio_ci95_upper"])
            finite_positive = all(
                math.isfinite(value) and value > 0 for value in (odds, lower, upper)
            )
            if finite_positive:
                enrichment_axis.errorbar(
                    [odds],
                    [0],
                    xerr=[[odds - lower], [upper - odds]],
                    fmt="o",
                    color="#7c3aed",
                    capsize=4,
                )
                enrichment_axis.axvline(
                    1.0, color="#111827", linestyle="--", linewidth=0.8
                )
                enrichment_axis.set_xscale("log")
                enrichment_axis.set_yticks(())
                enrichment_axis.set_xlabel("Fisher odds ratio (log scale; 95% CI)")
            else:
                enrichment_axis.text(
                    0.5,
                    0.62,
                    "Finite graphical odds-ratio interval unavailable",
                    ha="center",
                    transform=enrichment_axis.transAxes,
                )
                enrichment_axis.set_axis_off()
            enrichment_axis.text(
                0.5,
                0.12,
                f"OR={enrichment['odds_ratio']}  95% CI "
                f"[{enrichment['odds_ratio_ci95_lower']}, "
                f"{enrichment['odds_ratio_ci95_upper']}]  "
                f"two-sided Fisher p={enrichment['fisher_p_value_two_sided']}",
                ha="center",
                transform=enrichment_axis.transAxes,
                fontsize=8,
            )
            foreground_count = int(enrichment["candidate_with_motif_count"])
            foreground_total = int(enrichment["analyzable_candidate_count"])
            background_count = int(enrichment["background_with_motif_count"])
            background_total = int(enrichment["background_candidate_count"])
            enrichment_axis.text(
                0.5,
                0.28,
                "Registered hit in ±100-nt analyzable context: foreground "
                f"{foreground_count}/{foreground_total} "
                f"({(100.0 * foreground_count / foreground_total) if foreground_total else 0.0:.1f}%); "
                f"background {background_count}/{background_total} "
                f"({(100.0 * background_count / background_total) if background_total else 0.0:.1f}%)",
                ha="center",
                transform=enrichment_axis.transAxes,
                fontsize=7.5,
            )
        else:
            enrichment_axis.text(
                0.5,
                0.55,
                "Enrichment unavailable: "
                + enrichment["availability_status"].replace("_", " "),
                ha="center",
                va="center",
                transform=enrichment_axis.transAxes,
            )
            enrichment_axis.text(
                0.5,
                0.30,
                "Foreground "
                f"{enrichment['candidate_with_motif_count']}/"
                f"{enrichment['analyzable_candidate_count']}; background "
                f"{enrichment['background_with_motif_count']}/"
                f"{enrichment['background_candidate_count']}",
                ha="center",
                transform=enrichment_axis.transAxes,
                fontsize=8,
            )
            enrichment_axis.set_axis_off()
        figure.subplots_adjust(
            left=0.10, right=0.97, bottom=0.10, top=0.93, hspace=0.55
        )

    svg, digest, size = _render_svg(
        "motif-context-enrichment-figure", draw, figsize=(8.5, 7.0)
    )
    summary = (
        "The fixed 10-nt position bins show the percentage of each producer-admitted "
        "analyzable population assigned to its nearest registered hit, without "
        "smoothing. The whole-window significant-up versus "
        "comparison-background Fisher result is "
        f"{enrichment['availability_status']}."
    )
    return ScientificFigure(
        figure_id="motif-context-enrichment-figure",
        title="Registered PUM motif position and enrichment",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Position profile of nearest registered PUM motif hits around the edit "
            "as a percentage of each analyzable population, with population-specific "
            "denominators, and a whole-window Fisher enrichment panel. " + summary
        ),
        text_summary=summary,
        caption=(
            "Position-bin counts and per-population analyzable denominators are read "
            "directly from the validated Step 10 motif-statistics table; reporting "
            "only expresses each admitted count as a percentage of its own admitted "
            "denominator. Availability, odds ratio, confidence interval, and two-sided "
            "Fisher p-value are retained unchanged. Reporting performs no motif scan, nearest-hit "
            "selection, population construction, significance test, multiple-testing "
            "adjustment, or smoothing. The sole registered-motif policy records BH as "
            "not applicable. Negative offsets are upstream and positive offsets are "
            "downstream in the provisional RNA-change-oriented genomic context. The "
            f"registered exact-match motif is RNA {owner_context.MOTIF_RNA_CONSENSUS} "
            f"(DNA {owner_context.MOTIF_DNA_CONSENSUS}) within the admitted ±"
            f"{owner_context.CONTEXT_RADIUS}-nt window."
        ),
        input_roles=("motif_statistics", "receipt"),
        mapping=(
            "x=signed fixed 10-nt position-bin midpoint; y=100*admitted nearest-hit "
            "candidate count/admitted analyzable_candidate_count for that population; "
            "enrichment=unchanged admitted two-sided Fisher odds ratio, 95% CI, and p"
        ),
        population=(
            "Producer-defined significant_up, fdr_not_met/effect_not_met background, "
            "and separate significant_down populations; fixed minima retained"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _decimal_text(value: Decimal | None) -> str:
    return "unavailable" if value is None else str(value)


def _percentage_text(value: Decimal | None) -> str:
    if value is None:
        return "unavailable"
    return f"{float(value * 100):.2f}% (AF {value})"


def _signed_percentage_point_text(value: Decimal | None) -> str:
    if value is None:
        return "unavailable"
    return f"{float(value * 100):+.2f} pp (ΔAF {value})"


def _sample_support_text(sample: CandidateSampleEvidence) -> str:
    support = (
        f"AD/DP {sample.alternate_depth}/{sample.total_depth}"
        if sample.alternate_depth is not None and sample.total_depth is not None
        else "AD/DP unavailable"
    )
    return f"{sample.sample_id}: {_percentage_text(sample.allele_fraction)}, {support}"


def _wrap_motif_panel_lines(lines: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        wrapped
        for line in lines
        for wrapped in textwrap.wrap(
            line,
            width=_MOTIF_PANEL_LINE_WIDTH,
            break_long_words=True,
            break_on_hyphens=False,
        )
    )


def _motif_panel_lines(candidate: SelectedCandidate) -> tuple[str, ...]:
    """Return bounded visual context; exhaustive facts stay in the HTML record."""

    motif = candidate.motif
    if motif.state == "step10_unavailable":
        return _wrap_motif_panel_lines(
            (
                "Registered motif: not admitted (Step 10 unavailable)",
                "Sequence and exact motif-hit evidence are unavailable.",
                "Exact rates, read support, and location facts follow below.",
            )
        )
    motif_id = _short_candidate_id(motif.motif_id or "unavailable", limit=28)
    rna_consensus = _short_candidate_id(motif.rna_consensus or "unavailable", limit=18)
    dna_consensus = _short_candidate_id(motif.dna_consensus or "unavailable", limit=18)
    context_status = _short_candidate_id(
        motif.context_status or "unavailable", limit=24
    )
    orientation_action = _short_candidate_id(
        motif.orientation_action or "unavailable", limit=24
    )
    lines = [
        f"Registered {motif_id}: RNA {rna_consensus}; DNA {dna_consensus}",
        f"Context: {context_status}; orientation action {orientation_action}",
    ]
    if motif.state == "present":
        visible_count = sum(
            hit.end_offset >= -_TRACK_RADIUS and hit.start_offset <= _TRACK_RADIUS
            for hit in motif.hits
        )
        nearest = min(motif.hits, key=lambda hit: abs(hit.midpoint_offset))
        lines.append(
            f"Exact hits in admitted ±{motif.context_radius}-nt context: "
            f"{len(motif.hits)}; intersecting this ±{_TRACK_RADIUS}-nt panel: "
            f"{visible_count}"
        )
        lines.append(f"Nearest hit midpoint: {nearest.midpoint_offset:+} nt")
    elif motif.state == "no_registered_hit":
        lines.append(
            f"No exact registered hit in the analyzable ±{motif.context_radius}-nt "
            "context."
        )
    elif motif.state == "boundary_unavailable":
        lines.append(
            "Motif analysis unavailable because the admitted context crosses a "
            "contig boundary."
        )
    else:  # pragma: no cover - closed Literal boundary
        _fail(f"Unsupported candidate motif state: {motif.state!r}")
    lines.append("Exact AF, AD/DP, annotations, and all motif offsets follow below.")
    return _wrap_motif_panel_lines(lines)


def _panel_condition_label(value: str) -> str:
    """Bound condition labels inside a fixed-width SVG panel."""

    return _short_candidate_id(value, limit=_PANEL_CONDITION_LABEL_LIMIT)


def _draw_candidate_sequence(axis: Any, candidate: SelectedCandidate) -> None:
    motif = candidate.motif
    sequence = motif.oriented_sequence
    center = motif.edit_offset_0based
    axis.set_xlim(-_TRACK_RADIUS - 0.6, _TRACK_RADIUS + 0.6)
    axis.set_ylim(-0.5, 0.5)
    axis.set_yticks(())
    axis.set_xticks((-25, -10, 0, 10, 25))
    axis.set_xlabel("Site-centered oriented genomic offset from edited base (nt)")
    if sequence is None or center is None:
        axis.text(
            0.5,
            0.5,
            "Step 10 sequence context unavailable",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
        axis.set_title("±25-nt site-centered sequence display unavailable", loc="left")
        return
    left = max(-_TRACK_RADIUS, -center)
    right = min(_TRACK_RADIUS, len(sequence) - center - 1)
    if left > -_TRACK_RADIUS:
        axis.axvspan(-_TRACK_RADIUS - 0.5, left - 0.5, color="#e5e7eb", alpha=0.8)
    if right < _TRACK_RADIUS:
        axis.axvspan(right + 0.5, _TRACK_RADIUS + 0.5, color="#e5e7eb", alpha=0.8)
    for hit in motif.hits:
        start = max(left, hit.start_offset)
        end = min(right, hit.end_offset)
        if start <= end:
            axis.axvspan(
                start - 0.48,
                end + 0.48,
                color="#fbbf24",
                alpha=0.38,
                linewidth=0,
            )
    for relative in range(left, right + 1):
        base = sequence[center + relative]
        axis.text(
            relative,
            0.0,
            base,
            color=_BASE_COLORS.get(base, "#111827"),
            ha="center",
            va="center",
            fontsize=6.7,
            fontweight="bold" if relative == 0 else "normal",
        )
    axis.axvline(0, color="#111827", linewidth=1.1)
    status = motif.context_status or "unavailable"
    axis.set_title(
        "Site-centered ±25-nt sequence (edit=0; yellow=admitted exact hit; "
        f"context={status})",
        loc="left",
        fontsize=8.5,
    )


def _candidate_panel(
    candidate: SelectedCandidate,
    projection: SelectedCandidateProjection,
) -> ScientificFigurePanel:
    panel_id = (
        f"selected-context-track-figure-candidate-{candidate.display_rank:02d}-panel"
    )
    location = candidate.location
    membership_text = (
        ", ".join(location.region_memberships)
        if location.region_memberships
        else "No recorded overlap (not inferred intergenic)"
    )
    motif_lines = _motif_panel_lines(candidate)

    def draw(figure: Any) -> None:
        grid = figure.add_gridspec(
            2,
            2,
            height_ratios=(1.0, 1.28),
            width_ratios=(1.0, 1.25),
            hspace=0.62,
            wspace=0.28,
        )
        sequence_axis = figure.add_subplot(grid[0, :])
        _draw_candidate_sequence(sequence_axis, candidate)

        rate_axis = figure.add_subplot(grid[1, 0])
        plotted_pairs = 0
        for pair_index, pair in enumerate(candidate.pairs):
            if (
                pair.control.allele_fraction is None
                or pair.treatment.allele_fraction is None
            ):
                continue
            plotted_pairs += 1
            rate_axis.plot(
                (0.0, 1.0),
                (
                    100.0 * float(pair.control.allele_fraction),
                    100.0 * float(pair.treatment.allele_fraction),
                ),
                marker="o",
                markersize=3.4,
                linewidth=1.0,
                color=_PAIR_COLORS[pair_index % len(_PAIR_COLORS)],
                alpha=max(0.45, 0.92 - pair_index * 0.08),
                label=pair.replicate,
            )
        rate_axis.set_xlim(-0.13, 1.13)
        rate_axis.set_ylim(0.0, 100.0)
        rate_axis.set_xticks((0.0, 1.0))
        rate_axis.set_xticklabels(
            (
                _panel_condition_label(projection.control_condition),
                _panel_condition_label(projection.treatment_condition),
            ),
            fontsize=7,
        )
        rate_axis.set_ylabel("Editing rate (%)")
        rate_axis.set_title("Manifest-paired editing rates", loc="left")
        rate_axis.grid(True, axis="y", color="#d1d5db", linewidth=0.4, alpha=0.65)
        if 0 < plotted_pairs <= _PAIR_LEGEND_LIMIT:
            rate_axis.legend(loc="best", fontsize=6, frameon=True)
        elif plotted_pairs:
            rate_axis.text(
                0.02,
                0.98,
                f"{plotted_pairs} manifest pairs; exact values below",
                ha="left",
                va="top",
                transform=rate_axis.transAxes,
                fontsize=6.2,
            )
        else:
            rate_axis.text(
                0.5,
                0.5,
                "No complete paired AF values",
                ha="center",
                va="center",
                transform=rate_axis.transAxes,
            )

        motif_axis = figure.add_subplot(grid[1, 1])
        motif_axis.set_axis_off()
        motif_axis.set_title("Candidate summary and nearby motif state", loc="left")
        motif_axis.text(
            0.0,
            0.90,
            "\n".join(motif_lines),
            ha="left",
            va="top",
            transform=motif_axis.transAxes,
            fontsize=7.4,
            linespacing=1.30,
        )
        figure.suptitle(
            f"{candidate.display_rank}. "
            f"{_short_candidate_id(candidate.candidate_id, limit=30)} — "
            "candidate-centered evidence (not a transcript locus)",
            x=0.055,
            y=0.985,
            ha="left",
            fontsize=11,
        )
        figure.text(
            0.07,
            0.91,
            f"Editing rate: {_percentage_text(candidate.mean_control_af)} → "
            f"{_percentage_text(candidate.mean_treatment_af)}; Δ "
            f"{_signed_percentage_point_text(candidate.treatment_control_difference)}",
            ha="left",
            va="top",
            fontsize=8.0,
        )
        figure.text(
            0.07,
            0.865,
            "Location (1-based; exact annotations below): "
            f"{_short_candidate_id(location.chromosome, limit=24)}:"
            f"{location.position_1based}; RNA {location.rna_ref}>{location.rna_alt}; "
            "genes "
            f"{_short_candidate_id(', '.join(location.gene_ids) or 'none recorded', limit=46)}",
            ha="left",
            va="top",
            fontsize=7.5,
        )
        figure.subplots_adjust(left=0.07, right=0.98, bottom=0.08, top=0.77)

    svg, digest, size = _render_svg(
        panel_id,
        draw,
        figsize=(8.4, 5.2),
    )
    alt_hits = "; ".join(
        f"{hit.matched_sequence} {hit.start_offset:+d}..{hit.end_offset:+d}"
        for hit in candidate.motif.hits
    )
    alt_pairs = (
        "; ".join(
            f"{pair.replicate}: {_sample_support_text(pair.control)} to "
            f"{_sample_support_text(pair.treatment)}"
            for pair in candidate.pairs
        )
        or "no manifest-defined pairs"
    )
    alt_text = (
        f"Candidate {candidate.display_rank}, {candidate.candidate_id}. "
        f"{projection.control_condition} mean {_percentage_text(candidate.mean_control_af)}; "
        f"{projection.treatment_condition} mean {_percentage_text(candidate.mean_treatment_af)}; "
        f"difference {_signed_percentage_point_text(candidate.treatment_control_difference)}. "
        f"Location (1-based) {location.chromosome}:{location.position_1based}; RNA "
        f"{location.rna_ref}>{location.rna_alt}; workflow orientation "
        f"{location.workflow_orientation}; orientation policy "
        f"{location.orientation_policy}; annotation strand "
        f"{location.annotation_strand}; genes {', '.join(location.gene_ids) or 'none recorded'}; "
        f"transcripts {', '.join(location.transcript_ids) or 'none recorded'}; "
        f"recorded regions {membership_text}. Per-pair evidence: {alt_pairs}. "
        + (
            "Registered motif evidence was not admitted; state step10_unavailable."
            if candidate.motif.state == "step10_unavailable"
            else (
                f"Registered motif {candidate.motif.rna_consensus}, state "
                f"{candidate.motif.state}"
                + (f"; hits {alt_hits}." if alt_hits else ".")
            )
        )
    )
    return ScientificFigurePanel(
        panel_id=panel_id,
        data_uri=_data_uri(svg),
        alt_text=alt_text,
        svg_sha256=digest,
        svg_size_bytes=size,
    )


def _empty_candidate_panel() -> ScientificFigurePanel:
    panel_id = "selected-context-track-figure-empty-panel"

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        axis.text(
            0.5,
            0.55,
            "No significant candidates were selected for candidate-centered display.",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
        axis.text(
            0.5,
            0.40,
            "No editing-rate, location, or nearby-motif values were inferred.",
            ha="center",
            va="center",
            transform=axis.transAxes,
            fontsize=8,
        )
        axis.set_axis_off()

    svg, digest, size = _render_svg(panel_id, draw, figsize=(8.4, 3.2))
    return ScientificFigurePanel(
        panel_id=panel_id,
        data_uri=_data_uri(svg),
        alt_text="No significant candidates were selected for display.",
        svg_sha256=digest,
        svg_size_bytes=size,
    )


def _selected_context_track_figure(
    candidate_display: SelectedCandidateProjection,
) -> ScientificFigure:
    panels = tuple(
        _candidate_panel(candidate, candidate_display)
        for candidate in candidate_display.candidates
    ) or (_empty_candidate_panel(),)
    selected_ids = tuple(
        candidate.candidate_id for candidate in candidate_display.candidates
    )
    selection_description = (
        "the admitted Step 10 display order"
        if candidate_display.selection_source == "step10_display_rank"
        else "the fixed Step 09 presentation rule"
    )
    context_admitted = candidate_display.selection_source == "step10_display_rank"
    motif_states = (
        ", ".join(
            f"{candidate.candidate_id}={candidate.motif.state}"
            for candidate in candidate_display.candidates
        )
        or "no selected candidates"
    )
    return ScientificFigure(
        figure_id="selected-context-track-figure",
        title="Selected candidate editing rate, location, and nearby motifs",
        status="available",
        data_uri=None,
        alt_text=(
            f"{len(candidate_display.candidates)} ordered candidate-centered evidence "
            "panels covering editing rate, location, read support, and nearby "
            f"registered motifs. Motif states: {motif_states}."
        ),
        text_summary=(
            f"{len(candidate_display.candidates)} of "
            f"{candidate_display.significant_candidate_count} significant "
            f"{'candidate is' if len(candidate_display.candidates) == 1 else 'candidates are'} "
            "shown as bounded evidence panels that directly report editing "
            "rate, carried location annotations, and nearby registered motif state."
        ),
        caption=(
            f"The shared display roster is supplied by {selection_description}; "
            f"{SCIENTIFIC_FIGURE_LABELS['selected-context-track-figure']} performs "
            "no selection or reranking. Each bounded panel shows "
            "named-condition rates, paired trends, location, and admitted sequence/"
            "motif state when available. Exact AF/AD/DP, annotations, and all motif "
            "offsets remain in the following candidate record. This mechanically "
            "oriented view is not a continuous transcript locus, isoform selection, "
            "or biological-strand interpretation. Selected IDs: "
            + (", ".join(selected_ids) if selected_ids else "none")
            + "."
        ),
        input_roles=(
            (
                "candidate_context",
                "motif_hits",
                "significant_sites",
                "sample_manifest",
                "receipt",
            )
            if context_admitted
            else ("significant_sites", "sample_manifest")
        ),
        mapping=(
            "one bounded SVG panel per shared selected candidate; pair traces="
            "admitted Step 09 AF; location=carried Step 08/09 fields; "
            + (
                "sequence x=admitted oriented offsets -25..25 with edit=0; yellow "
                "spans=admitted exact registered hits intersecting the slice"
                if context_admitted
                else "sequence and registered-motif context unavailable because "
                "Step 10 was not admitted"
            )
        ),
        population=(
            f"Shared ordered roster of {len(candidate_display.candidates)} of "
            f"{candidate_display.significant_candidate_count} significant candidates "
            f"from {selection_description}; maximum eight; no figure-side "
            "selection or reranking"
        ),
        svg_sha256=None,
        svg_size_bytes=None,
        unavailable_reason=None,
        panels=panels,
    )


def _unavailable_context_figure(
    figure_id: str,
    title: str,
    input_roles: tuple[str, ...],
    mapping: str,
    reason: str,
) -> ScientificFigure:
    return ScientificFigure(
        figure_id=figure_id,
        title=title,
        status="unavailable",
        data_uri=None,
        alt_text="",
        text_summary="No context figure was rendered from an unavailable admitted population.",
        caption=(
            "The required validated Step 10 inputs or registered availability state "
            "were unavailable; no values were inferred and no image was generated."
        ),
        input_roles=input_roles,
        mapping=mapping,
        population="Unavailable under the fixed Step 10 population policy",
        svg_sha256=None,
        svg_size_bytes=None,
        unavailable_reason=reason,
    )


def unavailable_scientific_context_figures(
    reason: str,
) -> tuple[ScientificFigure, ...]:
    return (
        _unavailable_context_figure(
            "sequence-context-logo-figure",
            "Edit-centered sequence context and registered PUM motif",
            ("sequence_logo", "motif_catalog", "receipt"),
            "observed glyph height=admitted base_fraction; registered glyph "
            "height=literal catalog consensus",
            reason,
        ),
        _unavailable_context_figure(
            "motif-context-enrichment-figure",
            "Registered PUM motif position and enrichment",
            ("motif_statistics", "receipt"),
            "x=signed fixed 10-nt position bin; y=100*admitted nearest-hit "
            "candidate count/admitted analyzable population; enrichment=unchanged "
            "admitted two-sided Fisher odds ratio, 95% CI, and p",
            reason,
        ),
        _unavailable_context_figure(
            "selected-context-track-figure",
            "Selected candidate editing rate, location, and nearby motifs",
            (
                "candidate_context",
                "motif_hits",
                "significant_sites",
                "sample_manifest",
                "receipt",
            ),
            "one ordered panel per shared selected candidate; editing=admitted "
            "Step 09 AF/AD/DP; location=carried Step 08/09 fields; sequence="
            "admitted oriented offsets -25..25; motif text=all admitted ±100-nt hits",
            reason,
        ),
    )


def build_scientific_context_figures(
    context_results: ScientificContextResults | None,
    context_unavailable_reason: str | None,
    candidate_display: SelectedCandidateProjection | None,
    candidate_unavailable_reason: str | None,
) -> tuple[ScientificFigure, ...]:
    """Return the fixed ordered Step 10 figures without upstream recalculation."""

    try:
        if context_results is None:
            unavailable = unavailable_scientific_context_figures(
                context_unavailable_reason
                or "The complete primary Step 10 scientific-context bundle is unavailable."
            )
            logo, motif = unavailable[:2]
        else:
            if context_unavailable_reason is not None:
                _fail(
                    "Scientific-context results and an unavailable reason cannot coexist"
                )
            logo = _sequence_context_logo_figure(context_results)
            motif = _motif_context_enrichment_figure(context_results)
        if candidate_display is None:
            tracks = _unavailable_context_figure(
                "selected-context-track-figure",
                "Selected candidate editing rate, location, and nearby motifs",
                (
                    "candidate_context",
                    "motif_hits",
                    "significant_sites",
                    "sample_manifest",
                    "receipt",
                ),
                "one ordered panel per shared selected candidate; editing=admitted "
                "Step 09 AF/AD/DP; location=carried Step 08/09 fields; sequence="
                "admitted oriented offsets -25..25; motif text=all admitted ±100-nt hits",
                candidate_unavailable_reason
                or "The admitted selected-candidate projection is unavailable.",
            )
        else:
            tracks = _selected_context_track_figure(candidate_display)
        return logo, motif, tracks
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error, ValueError, OverflowError) as exc:
        _fail(f"Could not render admitted Step 10 scientific figures: {exc}")


__all__: Sequence[str] = (
    "build_scientific_context_figures",
    "unavailable_scientific_context_figures",
)
