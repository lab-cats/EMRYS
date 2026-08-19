"""Presentation-only figures from admitted Step 10 scientific-context tables."""

from __future__ import annotations

import csv
import math
from collections.abc import Mapping, Sequence
from typing import Any

from norad.contracts.scientific_evidence import scientific_context as owner_context

from .figures import (
    _assert_snapshot,
    _candidate_rows,
    _data_uri,
    _fail,
    _logomaker_api,
    _render_svg,
    _short_candidate_id,
)
from .models import (
    ComputationalResults,
    ComputationalTable,
    ReportRenderError,
    ScientificContextResults,
    ScientificFigure,
)

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
    axis.set_ylabel("Observed base fraction")
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
                    title=f"{label} observed context (n={count})",
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
                axis.set_title(f"{label} observed context", fontsize=9)
                axis.set_axis_off()
        motif_axis = figure.add_subplot(2, 2, 4)
        _draw_frequency_logo(
            motif_axis,
            _registered_motif_matrix(owner_context.MOTIF_DNA_CONSENSUS),
            title=(
                f"Registered PUM motif: RNA {owner_context.MOTIF_RNA_CONSENSUS} / "
                f"DNA {owner_context.MOTIF_DNA_CONSENSUS}"
            ),
            mark_edit=False,
        )
        motif_axis.set_xlabel("Registered motif position")
        figure.suptitle("Edit-centered observed context and registered PUM motif")
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
            f"{owner_context.MOTIF_DNA_CONSENSUS})."
        ),
        caption=(
            "Observed panels consume the complete Step 10 frequency matrix for "
            "positions −10 through +10; reporting does not reopen the reference, "
            "count bases, or infer a motif. T is retained because the admitted "
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
            analyzable = rows[0]["analyzable_candidate_count"]
            if status != "available":
                profile_axis.plot(
                    [],
                    [],
                    color=color,
                    marker=marker,
                    label=f"{label}: unavailable ({status.replace('_', ' ')})",
                )
                continue
            midpoints = [
                (int(row["bin_start"]) + int(row["bin_end"])) / 2 for row in rows
            ]
            candidate_counts = [int(row["candidate_with_motif_count"]) for row in rows]
            profile_axis.plot(
                midpoints,
                candidate_counts,
                color=color,
                marker=marker,
                markersize=3.5,
                linewidth=1.1,
                label=f"{label} (analyzable n={analyzable})",
            )
        profile_axis.axvline(0, color="#111827", linestyle="--", linewidth=0.8)
        profile_axis.set_xlim(-100, 100)
        profile_axis.set_ylabel("Candidates with nearest hit")
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
                0.18,
                f"OR={enrichment['odds_ratio']}  95% CI "
                f"[{enrichment['odds_ratio_ci95_lower']}, "
                f"{enrichment['odds_ratio_ci95_upper']}]  "
                f"two-sided Fisher p={enrichment['fisher_p_value_two_sided']}",
                ha="center",
                transform=enrichment_axis.transAxes,
                fontsize=8,
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
        "The fixed 10-nt position bins show producer-admitted nearest-hit candidate "
        "counts without smoothing. The whole-window significant-up versus "
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
            "and a whole-window Fisher enrichment panel. " + summary
        ),
        text_summary=summary,
        caption=(
            "Position-bin counts, availability, odds ratio, confidence interval, "
            "and two-sided Fisher p-value are read directly from the validated Step "
            "10 motif-statistics table. Reporting performs no motif scan, nearest-hit "
            "selection, population construction, significance test, multiple-testing "
            "adjustment, or smoothing. The sole registered-motif policy records BH as "
            "not applicable. Negative offsets are upstream and positive offsets are "
            "downstream in the provisional RNA-change-oriented genomic context."
        ),
        input_roles=("motif_statistics", "receipt"),
        mapping=(
            "x=signed fixed 10-nt position-bin midpoint; y=admitted nearest-hit "
            "candidate count; enrichment=admitted two-sided Fisher odds ratio, "
            "95% CI, and p"
        ),
        population=(
            "Producer-defined significant_up, fdr_not_met/effect_not_met background, "
            "and separate significant_down populations; fixed minima retained"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _selected_context_rows(
    table: ComputationalTable,
) -> tuple[dict[str, str], ...]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    selected: list[dict[str, str]] = []
    for row in _candidate_rows(table):
        if row["display_rank"] == "NA":
            continue
        selected.append(dict(row))
        if len(selected) > 8:
            _fail("Admitted context transaction selected more than eight display rows")
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    selected.sort(key=lambda row: int(row["display_rank"]))
    return tuple(selected)


def _selected_hits(
    table: ComputationalTable,
    candidate_ids: set[str],
) -> dict[str, tuple[dict[str, str], ...]]:
    hits: dict[str, list[dict[str, str]]] = {
        candidate_id: [] for candidate_id in candidate_ids
    }
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    with table.path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t", strict=True)
        if tuple(reader.fieldnames or ()) != table.header:
            _fail("Admitted motif-hit header changed after canonical admission")
        for row in reader:
            if row["candidate_id"] in hits:
                hits[row["candidate_id"]].append(dict(row))
                if len(hits[row["candidate_id"]]) > 201:
                    _fail("Selected context track exceeds the bounded motif-hit roster")
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    return {candidate_id: tuple(rows) for candidate_id, rows in hits.items()}


def _selected_step09_rows(
    table: ComputationalTable,
    candidate_ids: set[str],
) -> dict[str, dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    for row in _candidate_rows(table):
        candidate_id = row["candidate_id"]
        if candidate_id in candidate_ids:
            if candidate_id in selected:
                _fail(f"Step 09 significant table repeats candidate {candidate_id!r}")
            selected[candidate_id] = dict(row)
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    if set(selected) != candidate_ids:
        _fail("Step 10 selected context roster differs from Step 09 significant rows")
    return selected


def _numeric_af(row: Mapping[str, str], field: str) -> float | None:
    value = row[field]
    if value == "NA":
        return None
    parsed = float(value)
    if not 0 <= parsed <= 1:
        _fail(f"Admitted Step 09 editing rate {field!r} is outside [0, 1]")
    return parsed


def _selected_context_track_figure(
    context_results: ScientificContextResults,
    computational_results: ComputationalResults,
) -> ScientificFigure:
    selected = _selected_context_rows(context_results.candidate_context)
    candidate_ids = {row["candidate_id"] for row in selected}
    hits = _selected_hits(context_results.motif_hits, candidate_ids)
    step09_rows = _selected_step09_rows(
        computational_results.significant_sites, candidate_ids
    )
    design = computational_results.sample_manifest

    def draw(figure: Any) -> None:
        if not selected:
            axis = figure.add_subplot(1, 1, 1)
            axis.text(
                0.5,
                0.5,
                "No upstream-selected significant candidates",
                ha="center",
                va="center",
                transform=axis.transAxes,
            )
            axis.set_axis_off()
            return
        grid = figure.add_gridspec(
            len(selected),
            2,
            width_ratios=(3.2, 1.0),
            hspace=0.78,
            wspace=0.20,
        )
        for index, context_row in enumerate(selected):
            candidate_id = context_row["candidate_id"]
            sequence_axis = figure.add_subplot(grid[index, 0])
            sequence = context_row["oriented_sequence"]
            center = int(context_row["edit_offset_0based"])
            left = max(-_TRACK_RADIUS, -center)
            right = min(_TRACK_RADIUS, len(sequence) - center - 1)
            for hit in hits[candidate_id]:
                start = max(left, int(hit["start_offset"]))
                end = min(right, int(hit["end_offset"]))
                if start <= end:
                    sequence_axis.axvspan(
                        start - 0.48,
                        end + 0.48,
                        color="#fbbf24",
                        alpha=0.34,
                        linewidth=0,
                    )
            for relative in range(left, right + 1):
                base = sequence[center + relative]
                sequence_axis.text(
                    relative,
                    0.0,
                    base,
                    color=_BASE_COLORS.get(base, "#111827"),
                    ha="center",
                    va="center",
                    fontsize=6.4,
                    fontweight="bold" if relative == 0 else "normal",
                )
            sequence_axis.axvline(0, color="#111827", linewidth=1.0)
            sequence_axis.set_xlim(-_TRACK_RADIUS - 0.6, _TRACK_RADIUS + 0.6)
            sequence_axis.set_ylim(-0.5, 0.5)
            sequence_axis.set_yticks(())
            sequence_axis.set_xticks((-25, -10, 0, 10, 25))
            sequence_axis.set_title(
                f"{context_row['display_rank']}. "
                f"{_short_candidate_id(candidate_id, limit=42)} — "
                f"{context_row['chromosome']}:{context_row['position']} "
                f"({context_row['population']}; {context_row['context_status']})",
                fontsize=8,
                loc="left",
            )
            if index == len(selected) - 1:
                sequence_axis.set_xlabel(
                    "Oriented genomic offset from edited base (nt)"
                )

            af_axis = figure.add_subplot(grid[index, 1])
            step09 = step09_rows[candidate_id]
            for pair_index, pair in enumerate(design.pairs):
                control = _numeric_af(step09, f"AF__{pair.control_sample_id}")
                treatment = _numeric_af(step09, f"AF__{pair.treatment_sample_id}")
                if control is None or treatment is None:
                    continue
                af_axis.plot(
                    (0.0, 1.0),
                    (control, treatment),
                    marker="o",
                    markersize=2.8,
                    linewidth=0.8,
                    alpha=0.72,
                    label=pair.replicate,
                )
            af_axis.set_xlim(-0.15, 1.15)
            af_axis.set_ylim(0.0, 1.0)
            af_axis.set_xticks((0.0, 1.0))
            af_axis.set_xticklabels(
                (design.control_condition, design.treatment_condition), fontsize=6
            )
            af_axis.set_ylabel("Editing rate", fontsize=6.5)
            af_axis.grid(True, axis="y", color="#d1d5db", linewidth=0.35, alpha=0.6)
            if index == 0 and design.pairs:
                af_axis.legend(loc="best", fontsize=5, frameon=True)
        figure.suptitle(
            "Upstream-selected candidate context, registered motif hits, and samples",
            fontsize=11,
        )
        figure.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.94)

    svg, digest, size = _render_svg(
        "selected-context-track-figure",
        draw,
        figsize=(10.5, max(4.2, 1.55 * len(selected) + 1.0)),
    )
    selected_ids = tuple(row["candidate_id"] for row in selected)
    return ScientificFigure(
        figure_id="selected-context-track-figure",
        title="Selected candidate sequence and sample context",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Sparse tracks for the upstream-selected significant candidates, with "
            "the edited base at zero, admitted registered-motif hits highlighted, "
            f"and manifest-paired sample editing rates. {len(selected)} candidates."
        ),
        text_summary=(
            f"{len(selected)} upstream-ranked candidate contexts are displayed at "
            "±25 nt with their admitted motif-hit spans and manifest-paired sample "
            "editing rates."
        ),
        caption=(
            "Step 10 supplies the display_rank and the complete provisional "
            "RNA-change-oriented genomic window; reporting neither ranks candidates "
            "nor reopens the reference. Only the ±25-nt presentation slice is drawn. "
            "A boundary-truncated admitted context shows only its available bases "
            "and is never padded. "
            "Yellow spans are admitted exact registered PUM hits, and the vertical "
            "line is the edited base. Sample values are the admitted Step 09 AF "
            "columns paired by the hash-bound manifest; missing values are omitted, "
            "never replaced with zero. Selected IDs in upstream order: "
            + (", ".join(selected_ids) if selected_ids else "none")
            + "."
        ),
        input_roles=(
            "candidate_context",
            "motif_hits",
            "significant_sites",
            "sample_manifest",
            "receipt",
        ),
        mapping=(
            "left x=admitted oriented_sequence offsets -25..25 with edit=0 and "
            "admitted motif spans; right x=manifest conditions, y=AF__sample, "
            "line=manifest replicate pair"
        ),
        population=(
            f"Exactly {len(selected)} candidates with upstream Step 10 display_rank; "
            "maximum eight; no report-side selection or reranking"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
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
            "x=signed fixed 10-nt position bin; y=admitted nearest-hit candidate "
            "count; enrichment=admitted two-sided Fisher odds ratio, 95% CI, and p",
            reason,
        ),
        _unavailable_context_figure(
            "selected-context-track-figure",
            "Selected candidate sequence and sample context",
            (
                "candidate_context",
                "motif_hits",
                "significant_sites",
                "sample_manifest",
                "receipt",
            ),
            "left x=admitted oriented_sequence offsets -25..25 with edit=0 and "
            "admitted motif spans; right x=manifest conditions, y=AF__sample",
            reason,
        ),
    )


def build_scientific_context_figures(
    context_results: ScientificContextResults | None,
    context_unavailable_reason: str | None,
    computational_results: ComputationalResults | None,
    computational_unavailable_reason: str | None,
) -> tuple[ScientificFigure, ...]:
    """Return the fixed ordered figures 6-8 without upstream recalculation."""

    if context_results is None:
        return unavailable_scientific_context_figures(
            context_unavailable_reason
            or "The complete primary Step 10 scientific-context bundle is unavailable."
        )
    if context_unavailable_reason is not None:
        _fail("Scientific-context results and an unavailable reason cannot coexist")
    try:
        logo = _sequence_context_logo_figure(context_results)
        motif = _motif_context_enrichment_figure(context_results)
        if computational_results is None:
            tracks = _unavailable_context_figure(
                "selected-context-track-figure",
                "Selected candidate sequence and sample context",
                (
                    "candidate_context",
                    "motif_hits",
                    "significant_sites",
                    "sample_manifest",
                    "receipt",
                ),
                "left x=admitted oriented_sequence offsets -25..25 with edit=0 and "
                "admitted motif spans; right x=manifest conditions, y=AF__sample",
                computational_unavailable_reason
                or "The admitted Step 09 sample values are unavailable.",
            )
        else:
            tracks = _selected_context_track_figure(
                context_results, computational_results
            )
        return logo, motif, tracks
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error, ValueError, OverflowError) as exc:
        _fail(f"Could not render admitted Step 10 scientific figures: {exc}")


__all__: Sequence[str] = (
    "build_scientific_context_figures",
    "unavailable_scientific_context_figures",
)
