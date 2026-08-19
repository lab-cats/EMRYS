"""Deterministic scientific-figure projection from admitted Step 09 records."""

from __future__ import annotations

import base64
import csv
import hashlib
import importlib
import importlib.metadata
import math
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from .inputs import _assert_snapshot
from .models import (
    FIGURE_POLICY_VERSION,
    LOGOMAKER_VERSION,
    MATPLOTLIB_VERSION,
    ComputationalResults,
    ComputationalTable,
    ReportRenderError,
    ScientificContextResults,
    ScientificFigure,
)

_SVG_DATA_URI_PREFIX = "data:image/svg+xml;base64,"
_MATPLOTLIB_CONFIG_PREFIX = "norad-matplotlib-"
_MAX_SVG_BYTES = 4_000_000
_LANDSCAPE_X_BINS = 48
_LANDSCAPE_Y_BINS = 36
_CONCORDANCE_BINS = 40
_PROFILE_DISPLAY_LIMIT = 8
_LOCATION_FIELDS = (
    ("is_five_prime_utr", "5′ UTR"),
    ("is_cds", "CDS"),
    ("is_three_prime_utr", "3′ UTR"),
    ("is_exon", "Exon"),
    ("is_intron", "Intron"),
)
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
_STATUS_ORDER = ("other", "significant_down", "significant_up")
_STATUS_STYLE = {
    "other": ("Other tested candidates", "#6b7280", "o"),
    "significant_down": ("Significant down", "#2563eb", "v"),
    "significant_up": ("Significant up", "#dc2626", "^"),
}
_MPL_API: tuple[Any, Any, Any] | None = None
_LOGOMAKER_API: tuple[Any, Any] | None = None


def _fail(message: str) -> None:
    raise ReportRenderError(message)


def _matplotlib_api() -> tuple[Any, Any, Any]:
    """Import the fixed SVG renderer through one cleaned temporary cache."""

    global _LOGOMAKER_API, _MPL_API
    if _MPL_API is not None:
        return _MPL_API
    preloaded = tuple(
        name
        for name in (
            "matplotlib",
            "matplotlib.font_manager",
            "matplotlib.figure",
            "matplotlib.backends.backend_svg",
            "logomaker",
        )
        if name in sys.modules
    )
    if preloaded:
        _fail(
            "Matplotlib was imported before NORAD established its controlled "
            "temporary renderer cache: " + ", ".join(preloaded)
        )

    environment_keys = (
        "MPLBACKEND",
        "MPLCONFIGDIR",
        "MPL_IGNORE_SYSTEM_FONTS",
    )
    previous = {key: os.environ.get(key) for key in environment_keys}
    config_path: Path | None = None
    renderer_api: tuple[Any, Any, Any] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix=_MATPLOTLIB_CONFIG_PREFIX) as config:
            config_path = Path(config)
            os.environ.update(
                {
                    "MPLBACKEND": "svg",
                    "MPLCONFIGDIR": config,
                    "MPL_IGNORE_SYSTEM_FONTS": "1",
                }
            )
            matplotlib = importlib.import_module("matplotlib")
            if matplotlib.__version__ != MATPLOTLIB_VERSION:
                _fail(
                    "Matplotlib renderer version mismatch: observed "
                    f"{matplotlib.__version__}; expected {MATPLOTLIB_VERSION}"
                )
            matplotlib.use("svg", force=True)
            importlib.import_module("matplotlib.font_manager")
            figure_type = importlib.import_module("matplotlib.figure").Figure
            canvas_type = importlib.import_module(
                "matplotlib.backends.backend_svg"
            ).FigureCanvasSVG
            if importlib.metadata.version("logomaker") != LOGOMAKER_VERSION:
                _fail(
                    "Logomaker renderer version mismatch: observed "
                    f"{importlib.metadata.version('logomaker')}; expected "
                    f"{LOGOMAKER_VERSION}"
                )
            logomaker = importlib.import_module("logomaker")
            pandas = importlib.import_module("pandas")
            _LOGOMAKER_API = (logomaker, pandas)
            renderer_api = (matplotlib, figure_type, canvas_type)
    except ReportRenderError:
        raise
    except Exception as exc:  # pragma: no cover - library import boundary
        _fail(f"Could not initialize the fixed Matplotlib SVG renderer: {exc}")
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    if config_path is None or config_path.exists() or renderer_api is None:
        _fail("Matplotlib temporary renderer cache was not removed")
    _MPL_API = renderer_api
    return _MPL_API


def _logomaker_api() -> tuple[Any, Any]:
    """Return Logomaker imported inside the controlled Matplotlib cache."""

    _matplotlib_api()
    if _LOGOMAKER_API is None:  # pragma: no cover - guarded import boundary
        _fail("Logomaker was not initialized with the controlled SVG renderer")
    return _LOGOMAKER_API


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1].lower()


def _validated_svg(raw: bytes, figure_id: str) -> bytes:
    start = raw.find(b"<svg")
    end = raw.rfind(b"</svg>")
    if start < 0 or end < start:
        _fail(f"Scientific figure {figure_id!r} did not render an SVG document")
    svg = raw[start : end + len(b"</svg>")]
    svg = re.sub(rb"\s*<metadata>.*?</metadata>", b"", svg, flags=re.DOTALL)
    svg += b"\n"
    if len(svg) > _MAX_SVG_BYTES:
        _fail(
            f"Scientific figure {figure_id!r} exceeds the fixed SVG size limit: "
            f"{len(svg)} bytes"
        )
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        _fail(f"Scientific figure {figure_id!r} rendered invalid SVG: {exc}")
    if _local_name(root.tag) != "svg":
        _fail(f"Scientific figure {figure_id!r} has a non-SVG root element")
    for element in root.iter():
        tag = _local_name(element.tag)
        if tag in {"script", "foreignobject", "image"}:
            _fail(f"Scientific figure {figure_id!r} contains forbidden {tag!r}")
        if tag == "style":
            style_text = "".join(element.itertext())
            references = re.findall(r"url\(([^)]+)\)", style_text, re.IGNORECASE)
            if re.search(r"@import", style_text, re.IGNORECASE) or any(
                not reference.strip(" '\"").startswith("#") for reference in references
            ):
                _fail(f"Scientific figure {figure_id!r} contains external CSS content")
        for raw_name, value in element.attrib.items():
            name = _local_name(raw_name)
            if name == "base":
                _fail(f"Scientific figure {figure_id!r} contains an XML base URI")
            if name.startswith("on"):
                _fail(f"Scientific figure {figure_id!r} contains an event attribute")
            if name == "href" and not value.startswith("#"):
                _fail(f"Scientific figure {figure_id!r} contains an external reference")
            for reference in re.findall(r"url\(([^)]+)\)", value):
                if not reference.strip(" '\"").startswith("#"):
                    _fail(f"Scientific figure {figure_id!r} contains an external URL")
    return svg


def _render_svg(
    figure_id: str,
    draw: Any,
    *,
    figsize: tuple[float, float] = (8.0, 4.8),
) -> tuple[bytes, str, int]:
    matplotlib, figure_type, canvas_type = _matplotlib_api()
    settings = {
        "font.family": "DejaVu Sans",
        "font.size": 9.0,
        "axes.titlesize": 11.0,
        "axes.labelsize": 9.5,
        "legend.fontsize": 8.0,
        "svg.fonttype": "path",
        "svg.hashsalt": f"norad-{FIGURE_POLICY_VERSION}",
    }
    with matplotlib.rc_context(settings):
        figure = figure_type(figsize=figsize, dpi=100)
        canvas = canvas_type(figure)
        draw(figure)
        buffer = BytesIO()
        canvas.print_svg(
            buffer,
            metadata={"Creator": "NORAD deterministic scientific report", "Date": None},
        )
        figure.clear()
    svg = _validated_svg(buffer.getvalue(), figure_id)
    return svg, hashlib.sha256(svg).hexdigest(), len(svg)


def _data_uri(svg: bytes) -> str:
    return _SVG_DATA_URI_PREFIX + base64.b64encode(svg).decode("ascii")


def _table_row(table: ComputationalTable) -> dict[str, str]:
    if len(table.display_rows) != 1:
        _fail(f"Scientific figure input {table.artifact_id!r} must have one row")
    return dict(zip(table.header, table.display_rows[0], strict=True))


def _candidate_rows(table: ComputationalTable) -> Iterator[Mapping[str, str]]:
    with table.path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != table.header:
            _fail(
                f"Scientific figure input {table.artifact_id!r} header changed "
                "after canonical admission"
            )
        yield from reader


def _tested_candidate(row: Mapping[str, str]) -> tuple[float, float, str] | None:
    if row["test_status"] != "tested":
        return None
    try:
        depth = float(row["mean_analysis_dp"])
        effect = float(row["treatment_control_difference"])
    except ValueError as exc:
        _fail(f"Admitted Step 09 figure value is not numeric: {exc}")
    if depth <= 0:
        _fail("Candidate depth must be positive for the logarithmic figure axis")
    status = row["call_status"]
    group = status if status in {"significant_up", "significant_down"} else "other"
    return depth, effect, group


@dataclass(frozen=True)
class _SelectedProfile:
    rank_key: tuple[float, float, str]
    row: Mapping[str, str]


def _candidate_grid(
    table: ComputationalTable,
) -> tuple[
    dict[str, dict[tuple[int, int], int]],
    int,
    tuple[float, float],
]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    observed_count = 0
    minimum_depth = math.inf
    maximum_depth = 0.0
    for row in _candidate_rows(table):
        candidate = _tested_candidate(row)
        if candidate is None:
            continue
        depth, _effect, _status = candidate
        observed_count += 1
        minimum_depth = min(minimum_depth, depth)
        maximum_depth = max(maximum_depth, depth)
    if observed_count == 0:
        _assert_snapshot(
            table.snapshot, f"scientific figure input {table.artifact_id!r}"
        )
        return (
            {status: {} for status in _STATUS_ORDER},
            0,
            (1.0, 10.0),
        )
    log_min = math.log10(minimum_depth)
    log_max = math.log10(maximum_depth)
    if math.isclose(log_min, log_max):
        log_min -= 0.25
        log_max += 0.25
    grid = {status: {} for status in _STATUS_ORDER}
    second_count = 0
    for row in _candidate_rows(table):
        candidate = _tested_candidate(row)
        if candidate is None:
            continue
        depth, effect, status = candidate
        x_fraction = (math.log10(depth) - log_min) / (log_max - log_min)
        y_fraction = (effect + 1.0) / 2.0
        x_bin = min(_LANDSCAPE_X_BINS - 1, max(0, int(x_fraction * _LANDSCAPE_X_BINS)))
        y_bin = min(_LANDSCAPE_Y_BINS - 1, max(0, int(y_fraction * _LANDSCAPE_Y_BINS)))
        cell = (x_bin, y_bin)
        grid[status][cell] = grid[status].get(cell, 0) + 1
        second_count += 1
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    if second_count != observed_count:
        _fail("Candidate landscape population changed during bounded projection")
    return grid, observed_count, (10**log_min, 10**log_max)


def _candidate_figure(results: ComputationalResults) -> ScientificFigure:
    summary = _table_row(results.summary)
    grid, population_count, grid_x_limits = _candidate_grid(results.all_sites)
    expected_count = int(summary["successfully_tested_count"])
    if population_count != expected_count:
        _fail(
            "Candidate landscape population does not match the admitted Step 09 "
            f"summary: observed {population_count}; expected {expected_count}"
        )
    depth_threshold = float(summary["mean_dp_threshold"])
    effect_threshold = float(summary["absolute_difference_threshold"])
    significant_up_count = int(summary["significant_up_count"])
    significant_down_count = int(summary["significant_down_count"])
    other_count = expected_count - significant_up_count - significant_down_count

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        if population_count:
            log_min = math.log10(grid_x_limits[0])
            log_max = math.log10(grid_x_limits[1])
            for status in _STATUS_ORDER:
                label, color, marker = _STATUS_STYLE[status]
                cells = sorted(grid[status])
                x_values = [
                    10
                    ** (log_min + ((x + 0.5) / _LANDSCAPE_X_BINS) * (log_max - log_min))
                    for x, _y in cells
                ]
                y_values = [
                    -1.0 + ((y + 0.5) / _LANDSCAPE_Y_BINS) * 2.0 for _x, y in cells
                ]
                sizes = [
                    18.0 + min(82.0, 14.0 * math.log2(grid[status][cell] + 1))
                    for cell in cells
                ]
                axis.scatter(
                    x_values,
                    y_values,
                    s=sizes,
                    c=color,
                    marker=marker,
                    alpha=0.78,
                    edgecolors="white",
                    linewidths=0.35,
                    label=label,
                )
        else:
            axis.text(
                0.5,
                0.5,
                "No successfully tested target candidates",
                ha="center",
                va="center",
                transform=axis.transAxes,
            )
            for status in _STATUS_ORDER:
                label, color, marker = _STATUS_STYLE[status]
                axis.scatter([], [], c=color, marker=marker, label=label)
        axis.set_xscale("log")
        axis.set_xlim(*grid_x_limits)
        axis.set_ylim(-1.0, 1.0)
        axis.axhline(0.0, color="#111827", linewidth=0.7)
        axis.text(
            0.01,
            0.98,
            f"Declared thresholds: mean depth {depth_threshold:g}; "
            f"absolute difference {effect_threshold:g}",
            ha="left",
            va="top",
            transform=axis.transAxes,
            fontsize=7.5,
        )
        axis.set_title("Candidate editing landscape")
        axis.set_xlabel("Mean analysis depth (log scale)")
        axis.set_ylabel("Treatment − control mean editing rate")
        axis.grid(True, which="both", color="#d1d5db", linewidth=0.45, alpha=0.6)
        axis.legend(loc="lower right", frameon=True)
        figure.subplots_adjust(left=0.11, right=0.98, bottom=0.16, top=0.90)

    svg, digest, size = _render_svg("candidate-landscape-figure", draw)
    summary_text = (
        f"{population_count} successfully tested target candidates: "
        f"{significant_up_count} significant up, "
        f"{significant_down_count} significant down, and "
        f"{other_count} other tested calls."
    )
    return ScientificFigure(
        figure_id="candidate-landscape-figure",
        title="Candidate editing landscape",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Candidate landscape of mean analysis depth versus treatment-minus-"
            "control editing-rate difference, grouped as significant up, "
            "significant down, or other tested status. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "All successfully tested target candidates are included through a "
            f"fixed {_LANDSCAPE_X_BINS} × {_LANDSCAPE_Y_BINS} occupancy grid; "
            "capped log-scaled symbol area reflects candidates per occupied cell. "
            "No random sampling or 250-row table-display limit is applied. Cell "
            "centers approximate coordinates, so exact threshold lines are not "
            "overlaid; the declared mean-depth and absolute-difference thresholds "
            f"({depth_threshold:g} and {effect_threshold:g}) are shown in the plot."
        ),
        input_roles=("all_sites", "summary"),
        mapping=(
            "x=mean_analysis_dp log-grid center; "
            "y=treatment_control_difference grid center; series={significant_up, "
            "significant_down, other tested statuses}; marker area=cell count"
        ),
        population=(
            f"{population_count} successfully tested target candidates; fixed "
            f"{_LANDSCAPE_X_BINS}x{_LANDSCAPE_Y_BINS} occupancy grid; no sampling"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _mutation_figure(results: ComputationalResults) -> ScientificFigure:
    table = results.mutation_spectrum
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    rows = [dict(zip(table.header, row, strict=True)) for row in table.display_rows]
    mutations = tuple(row["mutation_type"] for row in rows)
    counts = tuple(int(row["candidate_count"]) for row in rows)
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        bars = axis.bar(mutations, counts, color="#2563eb", width=0.72)
        for bar, count in zip(bars, counts, strict=True):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(count),
                ha="center",
                va="bottom",
                fontsize=7.5,
            )
        axis.set_title("Candidate mutation spectrum")
        axis.set_xlabel("RNA reference > alternate")
        axis.set_ylabel("Candidate count")
        axis.grid(True, axis="y", color="#d1d5db", linewidth=0.45, alpha=0.7)
        axis.set_axisbelow(True)
        figure.subplots_adjust(left=0.10, right=0.98, bottom=0.16, top=0.90)

    svg, digest, size = _render_svg("mutation-spectrum-figure", draw)
    total = sum(counts)
    nonzero = sum(count > 0 for count in counts)
    class_clause = "class has" if nonzero == 1 else "classes have"
    summary_text = (
        f"{total} candidates across 12 canonical single-nucleotide changes; "
        f"{nonzero} mutation {class_clause} nonzero counts."
    )
    return ScientificFigure(
        figure_id="mutation-spectrum-figure",
        title="Candidate mutation spectrum",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Bar chart of candidate counts in canonical mutation-type order. "
            + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "Counts are read directly from the admitted Step 09 mutation-spectrum "
            "TSV in canonical order; reporting does not recompute them from the "
            "candidate table or consume the existing PDF diagnostic."
        ),
        input_roles=("mutation_spectrum",),
        mapping="x=mutation_type (canonical order); y=candidate_count",
        population=f"All {len(rows)} canonical mutation classes; {total} candidates",
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _condition_grid(
    table: ComputationalTable,
) -> tuple[dict[str, dict[tuple[int, int], int]], int]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    grid = {status: {} for status in _STATUS_ORDER}
    observed_count = 0
    for row in _candidate_rows(table):
        if row["test_status"] != "tested":
            continue
        try:
            control = float(row["mean_control_af"])
            treatment = float(row["mean_treatment_af"])
        except ValueError as exc:
            _fail(f"Admitted Step 09 condition mean is not numeric: {exc}")
        if not 0 <= control <= 1 or not 0 <= treatment <= 1:
            _fail("Admitted Step 09 condition mean is outside [0, 1]")
        status = row["call_status"]
        group = status if status in {"significant_up", "significant_down"} else "other"
        cell = (
            min(_CONCORDANCE_BINS - 1, int(control * _CONCORDANCE_BINS)),
            min(_CONCORDANCE_BINS - 1, int(treatment * _CONCORDANCE_BINS)),
        )
        grid[group][cell] = grid[group].get(cell, 0) + 1
        observed_count += 1
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    return grid, observed_count


def _condition_concordance_figure(results: ComputationalResults) -> ScientificFigure:
    summary = _table_row(results.summary)
    grid, population_count = _condition_grid(results.all_sites)
    expected_count = int(summary["successfully_tested_count"])
    if population_count != expected_count:
        _fail(
            "Condition-concordance population does not match the admitted Step 09 "
            f"summary: observed {population_count}; expected {expected_count}"
        )

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        axis.plot(
            (0.0, 1.0),
            (0.0, 1.0),
            color="#111827",
            linestyle="--",
            linewidth=0.8,
            label="Equal condition means",
        )
        for status in _STATUS_ORDER:
            label, color, marker = _STATUS_STYLE[status]
            cells = sorted(grid[status])
            x_values = [(x + 0.5) / _CONCORDANCE_BINS for x, _y in cells]
            y_values = [(y + 0.5) / _CONCORDANCE_BINS for _x, y in cells]
            sizes = [
                18.0 + min(82.0, 14.0 * math.log2(grid[status][cell] + 1))
                for cell in cells
            ]
            axis.scatter(
                x_values,
                y_values,
                s=sizes,
                c=color,
                marker=marker,
                alpha=0.78,
                edgecolors="white",
                linewidths=0.35,
                label=label,
            )
        if not population_count:
            axis.text(
                0.5,
                0.5,
                "No successfully tested target candidates",
                ha="center",
                va="center",
                transform=axis.transAxes,
            )
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)
        axis.set_aspect("equal", adjustable="box")
        axis.set_title("Condition editing-rate concordance")
        axis.set_xlabel(f"{summary['control_condition']} mean editing rate")
        axis.set_ylabel(f"{summary['treatment_condition']} mean editing rate")
        axis.grid(True, color="#d1d5db", linewidth=0.45, alpha=0.6)
        axis.legend(loc="lower right", frameon=True)
        figure.subplots_adjust(left=0.19, right=0.93, bottom=0.15, top=0.90)

    svg, digest, size = _render_svg("condition-concordance-figure", draw)
    summary_text = (
        f"{population_count} successfully tested target candidates compare the "
        f"unweighted {summary['control_condition']} and "
        f"{summary['treatment_condition']} replicate means produced by Step 09."
    )
    return ScientificFigure(
        figure_id="condition-concordance-figure",
        title="Condition editing-rate concordance",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Scatter plot of Step 09 mean control editing rate versus mean "
            "treatment editing rate with an equality diagonal. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "Every successfully tested target candidate is included through a "
            f"fixed {_CONCORDANCE_BINS} × {_CONCORDANCE_BINS} occupancy grid. "
            "The axes use Step 09's unweighted means across manifest-defined "
            "replicates; reporting does not pool allele and depth counts. Cell "
            "centers approximate coordinates and capped log-scaled symbol area "
            "reflects candidates per occupied cell."
        ),
        input_roles=("all_sites", "summary"),
        mapping=(
            "x=mean_control_af grid center; y=mean_treatment_af grid center; "
            "series={significant_up, significant_down, other tested statuses}; "
            "marker area=cell count"
        ),
        population=(
            f"{population_count} successfully tested target candidates; fixed "
            f"{_CONCORDANCE_BINS}x{_CONCORDANCE_BINS} occupancy grid; no sampling"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _selected_profiles(table: ComputationalTable) -> tuple[_SelectedProfile, ...]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    selected: list[_SelectedProfile] = []
    for row in _candidate_rows(table):
        try:
            fdr = float(row["cmh_fdr_bh"])
            effect = float(row["treatment_control_difference"])
        except ValueError as exc:
            _fail(f"Admitted significant-candidate ranking value is not numeric: {exc}")
        profile = _SelectedProfile(
            rank_key=(fdr, -abs(effect), row["candidate_id"]),
            row=dict(row),
        )
        selected.append(profile)
        selected.sort(key=lambda value: value.rank_key)
        del selected[_PROFILE_DISPLAY_LIMIT:]
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    return tuple(selected)


def _short_candidate_id(value: str, *, limit: int = 34) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _paired_sample_profile_figure(results: ComputationalResults) -> ScientificFigure:
    profiles = _selected_profiles(results.significant_sites)
    design = results.sample_manifest
    pair_count = len(design.pairs)

    def sample_af(row: Mapping[str, str], sample_id: str) -> float:
        value = row[f"AF__{sample_id}"]
        try:
            parsed = float(value)
        except ValueError:
            _fail(
                "Admitted significant candidate lacks a numeric editing rate for "
                f"paired sample {sample_id!r}"
            )
        if not 0 <= parsed <= 1:
            _fail(
                f"Admitted significant-candidate AF for {sample_id!r} is outside [0, 1]"
            )
        return parsed

    def draw(figure: Any) -> None:
        if not profiles:
            axis = figure.add_subplot(1, 1, 1)
            axis.text(
                0.5,
                0.5,
                "No significant candidates",
                ha="center",
                va="center",
                transform=axis.transAxes,
            )
            axis.set_axis_off()
            return
        columns = 1 if len(profiles) == 1 else 2
        row_count = math.ceil(len(profiles) / columns)
        for profile_index, profile in enumerate(profiles, start=1):
            axis = figure.add_subplot(row_count, columns, profile_index)
            row = profile.row
            for pair_index, pair in enumerate(design.pairs):
                control_af = sample_af(row, pair.control_sample_id)
                treatment_af = sample_af(row, pair.treatment_sample_id)
                axis.plot(
                    (0.0, 1.0),
                    (control_af, treatment_af),
                    marker="o",
                    markersize=3.2,
                    linewidth=0.9,
                    alpha=0.72,
                    color=_PAIR_COLORS[pair_index % len(_PAIR_COLORS)],
                    label=pair.replicate,
                )
            axis.plot(
                (0.0, 1.0),
                (
                    float(row["mean_control_af"]),
                    float(row["mean_treatment_af"]),
                ),
                marker="D",
                markersize=4.0,
                linewidth=1.8,
                color="#111827",
                label="Step 09 mean",
            )
            axis.set_xlim(-0.12, 1.12)
            axis.set_ylim(0.0, 1.0)
            axis.set_xticks((0.0, 1.0))
            axis.set_xticklabels(
                (design.control_condition, design.treatment_condition),
                fontsize=7,
            )
            axis.set_title(
                f"{profile_index}. {_short_candidate_id(row['candidate_id'])}",
                fontsize=8.5,
                loc="left",
            )
            axis.grid(True, axis="y", color="#d1d5db", linewidth=0.4, alpha=0.6)
            if (profile_index - 1) % columns == 0:
                axis.set_ylabel("Editing rate", fontsize=7.5)
            if profile_index == 1:
                axis.legend(loc="best", fontsize=5.5, frameon=True)
        figure.suptitle(
            "Selected significant-candidate paired sample profiles",
            fontsize=11,
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.98,
            bottom=0.07,
            top=0.93,
            hspace=0.72,
            wspace=0.26,
        )

    row_count = max(1, math.ceil(len(profiles) / 2))
    svg, digest, size = _render_svg(
        "paired-sample-profile-figure",
        draw,
        figsize=(8.0, max(4.8, 2.15 * row_count + 0.8)),
    )
    selected_ids = tuple(profile.row["candidate_id"] for profile in profiles)
    pair_mapping = "; ".join(
        f"{pair.replicate}: {pair.control_sample_id} → {pair.treatment_sample_id}"
        for pair in design.pairs
    )
    summary_text = (
        f"{len(profiles)} of {results.significant_sites.row_count} significant "
        f"candidates are displayed across {pair_count} manifest-defined replicate "
        "pairs."
    )
    return ScientificFigure(
        figure_id="paired-sample-profile-figure",
        title="Selected candidate per-sample profiles",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Small-multiple paired-line profiles of sample editing rates for "
            "selected significant candidates. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            f"Display-only selection uses at most {_PROFILE_DISPLAY_LIMIT} candidates "
            "ordered by CMH BH FDR ascending, absolute treatment-minus-control "
            "difference descending, then candidate ID. It does not create a new "
            "scientific ranking. Colored lines join the exact manifest-defined "
            f"sample pairs ({pair_mapping}); black diamonds join Step 09's "
            "unweighted condition means. Selected IDs: "
            + (", ".join(selected_ids) if selected_ids else "none")
            + "."
        ),
        input_roles=("significant_sites", "summary", "sample_manifest"),
        mapping=(
            "x={control_condition,treatment_condition}; y=AF__sample; "
            "line=manifest replicate pair; black diamonds=Step 09 condition means"
        ),
        population=(
            f"Top {len(profiles)} of {results.significant_sites.row_count} significant "
            "candidates by the fixed display rule; all manifest-defined analysis pairs"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _location_memberships(
    table: ComputationalTable,
) -> tuple[tuple[int, ...], int]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    counts = [0] * len(_LOCATION_FIELDS)
    population_count = 0
    for row in _candidate_rows(table):
        population_count += 1
        for index, (field, _label) in enumerate(_LOCATION_FIELDS):
            if row[field] == "TRUE":
                counts[index] += 1
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    return tuple(counts), population_count


def _location_membership_figure(results: ComputationalResults) -> ScientificFigure:
    summary = _table_row(results.summary)
    counts, population_count = _location_memberships(results.significant_sites)
    expected_count = int(summary["significant_up_count"]) + int(
        summary["significant_down_count"]
    )
    if population_count != expected_count:
        _fail(
            "Location-membership population does not match the admitted Step 09 "
            f"summary: observed {population_count}; expected {expected_count}"
        )
    percentages = tuple(
        (100.0 * count / population_count) if population_count else 0.0
        for count in counts
    )
    labels = tuple(label for _field, label in _LOCATION_FIELDS)

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        positions = tuple(range(len(labels)))
        bars = axis.barh(positions, percentages, color="#2563eb", height=0.66)
        axis.set_yticks(positions)
        axis.set_yticklabels(labels)
        axis.invert_yaxis()
        axis.set_xlim(0.0, 100.0 if population_count else 1.0)
        for bar, count, percentage in zip(
            bars,
            counts,
            percentages,
            strict=True,
        ):
            axis.text(
                min(bar.get_width() + 1.2, 97.0) if population_count else 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{count} ({percentage:.1f}%)",
                ha="left" if percentage < 91 else "right",
                va="center",
                fontsize=8,
            )
        if not population_count:
            axis.text(
                0.5,
                0.5,
                "No significant candidates",
                ha="center",
                va="center",
                transform=axis.transAxes,
            )
        axis.set_title("Recorded annotation-overlap memberships")
        axis.set_xlabel("Percentage of significant candidates")
        axis.grid(True, axis="x", color="#d1d5db", linewidth=0.45, alpha=0.7)
        axis.set_axisbelow(True)
        figure.subplots_adjust(left=0.18, right=0.96, bottom=0.16, top=0.90)

    svg, digest, size = _render_svg("location-membership-figure", draw)
    summary_text = (
        f"{population_count} significant candidates contribute independently to "
        + ", ".join(
            f"{label}={count}" for label, count in zip(labels, counts, strict=True)
        )
        + "."
    )
    return ScientificFigure(
        figure_id="location-membership-figure",
        title="Candidate location memberships",
        status="available",
        data_uri=_data_uri(svg),
        alt_text=(
            "Horizontal bars of the recorded five-prime UTR, CDS, three-prime "
            "UTR, exon, and intron overlap memberships. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "The complete significant-sites population is counted against each "
            "producer-recorded Step 08 GTF-overlap flag. Memberships are "
            "independent and nonexclusive: CDS and UTR memberships can also be "
            "exonic, and transcript isoforms can give one candidate several "
            "memberships. Counts and percentages therefore need not sum to the "
            "candidate population or 100%. Reporting does not reannotate, infer "
            "an exclusive region, or rename an all-false record as intergenic."
        ),
        input_roles=("significant_sites", "summary"),
        mapping=(
            "y={is_five_prime_utr,is_cds,is_three_prime_utr,is_exon,is_intron}; "
            "x=independent membership percentage among significant candidates"
        ),
        population=f"All {population_count} significant Step 09 candidates; no sampling",
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _unavailable_figures(reason: str) -> tuple[ScientificFigure, ...]:
    specifications: Sequence[tuple[str, str, tuple[str, ...], str]] = (
        (
            "candidate-landscape-figure",
            "Candidate editing landscape",
            ("all_sites", "summary"),
            "x=mean_analysis_dp log-grid center; "
            "y=treatment_control_difference grid center; series={significant_up, "
            "significant_down, other tested statuses}; marker area=cell count",
        ),
        (
            "mutation-spectrum-figure",
            "Candidate mutation spectrum",
            ("mutation_spectrum",),
            "x=mutation_type (canonical order); y=candidate_count",
        ),
        (
            "condition-concordance-figure",
            "Condition editing-rate concordance",
            ("all_sites", "summary"),
            "x=mean_control_af grid center; y=mean_treatment_af grid center; "
            "series={significant_up, significant_down, other tested statuses}; "
            "marker area=cell count",
        ),
        (
            "paired-sample-profile-figure",
            "Selected candidate per-sample profiles",
            ("significant_sites", "summary", "sample_manifest"),
            "x={control_condition,treatment_condition}; y=AF__sample; "
            "line=manifest replicate pair; black diamonds=Step 09 condition means",
        ),
        (
            "location-membership-figure",
            "Candidate location memberships",
            ("significant_sites", "summary"),
            "y={is_five_prime_utr,is_cds,is_three_prime_utr,is_exon,is_intron}; "
            "x=independent membership percentage among significant candidates",
        ),
    )
    return tuple(
        ScientificFigure(
            figure_id=figure_id,
            title=title,
            status="unavailable",
            data_uri=None,
            alt_text="",
            text_summary="No scientific figure was rendered from an incomplete source bundle.",
            caption=(
                "The required admitted Step 09 inputs were unavailable; no values "
                "were inferred and no image was generated."
            ),
            input_roles=input_roles,
            mapping=mapping,
            population="Unavailable because the complete admitted source bundle is absent",
            svg_sha256=None,
            svg_size_bytes=None,
            unavailable_reason=reason,
        )
        for figure_id, title, input_roles, mapping in specifications
    )


def build_scientific_figures(
    results: ComputationalResults | None,
    unavailable_reason: str | None,
    scientific_context_results: ScientificContextResults | None = None,
    scientific_context_unavailable_reason: str | None = None,
) -> tuple[ScientificFigure, ...]:
    """Return the fixed ordered eight-figure scientific roster."""

    from .scientific_context_figures import build_scientific_context_figures

    if results is None:
        current_figures = _unavailable_figures(
            unavailable_reason
            or "The complete primary Step 09 source bundle is unavailable."
        )
    else:
        if unavailable_reason is not None:
            _fail("Computational results and an unavailable reason cannot coexist")
        try:
            current_figures = (
                _candidate_figure(results),
                _mutation_figure(results),
                _condition_concordance_figure(results),
                _paired_sample_profile_figure(results),
                _location_membership_figure(results),
            )
        except ReportRenderError:
            raise
        except (OSError, UnicodeError, csv.Error, ValueError, OverflowError) as exc:
            _fail(f"Could not render admitted Step 09 scientific figures: {exc}")
    context_figures = build_scientific_context_figures(
        scientific_context_results,
        scientific_context_unavailable_reason,
        results,
        unavailable_reason,
    )
    return (*current_figures, *context_figures)
