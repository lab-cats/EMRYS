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
from io import BytesIO
from pathlib import Path
from typing import Any

from emrys.reporting import (
    ReportProviderError as ReportRenderError,
    recheck_report_input as _assert_snapshot,
)

from .candidate_display import SelectedCandidateProjection
from .computational import ComputationalResults, ComputationalTable
from .figure_models import (
    FIGURE_POLICY_VERSION,
    LOGOMAKER_VERSION,
    MATPLOTLIB_VERSION,
    ScientificFigure,
)
from .scientific_context import ScientificContextResults

_SVG_DATA_URI_PREFIX = "data:image/svg+xml;base64,"
_MATPLOTLIB_CONFIG_PREFIX = "emrys-matplotlib-"
_MAX_SVG_BYTES = 4_000_000
_LANDSCAPE_X_BINS = 48
_LANDSCAPE_Y_BINS = 36
_CONCORDANCE_BINS = 40
_PROFILE_DISPLAY_LIMIT = 8
_PAIR_LEGEND_LIMIT = 4
_PROFILE_MAX_HEIGHT_INCHES = 7.2
_PROFILE_ROW_HEIGHT_INCHES = 1.6
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
    preloaded = sys.modules.get("matplotlib")
    if preloaded is not None:
        controlled = getattr(preloaded, "_emrys_controlled_svg_runtime", None)
        if controlled is not None:
            _MPL_API, _LOGOMAKER_API = controlled
            return _MPL_API
        _fail(
            "Matplotlib was imported before EMRYS established its controlled "
            "temporary renderer cache"
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
    setattr(matplotlib, "_emrys_controlled_svg_runtime", (_MPL_API, _LOGOMAKER_API))
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
        "svg.hashsalt": f"emrys-{FIGURE_POLICY_VERSION}",
    }
    with matplotlib.rc_context(settings):
        figure = figure_type(figsize=figsize, dpi=100)
        canvas = canvas_type(figure)
        draw(figure)
        buffer = BytesIO()
        canvas.print_svg(
            buffer,
            metadata={"Creator": "EMRYS deterministic scientific report", "Date": None},
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


def _combined_occupancy(
    grid: Mapping[str, Mapping[tuple[int, int], int]],
) -> dict[tuple[int, int], int]:
    """Return one complete tested-population background occupancy."""

    combined: dict[tuple[int, int], int] = {}
    for status in _STATUS_ORDER:
        for cell, count in grid[status].items():
            combined[cell] = combined.get(cell, 0) + count
    return combined


def _exact_significant_points(
    table: ComputationalTable,
    *,
    x_field: str,
    y_field: str,
    x_positive: bool = False,
    unit_interval: bool = False,
) -> dict[str, tuple[tuple[float, float], ...]]:
    """Read exact admitted coordinates for both significant call directions."""

    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    points: dict[str, list[tuple[float, float]]] = {
        "significant_down": [],
        "significant_up": [],
    }
    for row in _candidate_rows(table):
        status = row["call_status"]
        if row["test_status"] != "tested" or status not in points:
            continue
        try:
            x_value = float(row[x_field])
            y_value = float(row[y_field])
        except ValueError as exc:
            _fail(f"Admitted significant-candidate figure value is not numeric: {exc}")
        if x_positive and x_value <= 0:
            _fail(f"Admitted significant-candidate {x_field!r} must be positive")
        if unit_interval and not (0 <= x_value <= 1 and 0 <= y_value <= 1):
            _fail("Admitted significant-candidate condition mean is outside [0, 1]")
        points[status].append((x_value, y_value))
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    return {status: tuple(values) for status, values in points.items()}


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
    significant_points = _exact_significant_points(
        results.all_sites,
        x_field="mean_analysis_dp",
        y_field="treatment_control_difference",
        x_positive=True,
    )
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
    if (
        len(significant_points["significant_up"]) != significant_up_count
        or len(significant_points["significant_down"]) != significant_down_count
    ):
        _fail("Exact significant landscape points do not match the Step 09 summary")
    other_count = expected_count - significant_up_count - significant_down_count
    control = summary["control_condition"]
    treatment = summary["treatment_condition"]
    background_grid = _combined_occupancy(grid)
    plot_x_limits = grid_x_limits
    if depth_threshold > 0:
        plot_x_limits = (
            min(grid_x_limits[0], depth_threshold / 1.25),
            max(grid_x_limits[1], depth_threshold * 1.25),
        )
    depth_gate_note = (
        f"mean depth > {depth_threshold:g}"
        if depth_threshold > 0
        else "mean-depth threshold = 0 (outside the log axis; no vertical line)"
    )
    depth_caption = (
        "the declared mean-depth and absolute-difference gates are drawn"
        if depth_threshold > 0
        else (
            "the absolute-difference gates are drawn; the declared zero mean-depth "
            "threshold cannot be represented on the logarithmic axis"
        )
    )

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        if population_count:
            log_min = math.log10(grid_x_limits[0])
            log_max = math.log10(grid_x_limits[1])
            cells = sorted(background_grid)
            axis.scatter(
                [
                    10
                    ** (log_min + ((x + 0.5) / _LANDSCAPE_X_BINS) * (log_max - log_min))
                    for x, _y in cells
                ],
                [
                    100.0 * (-1.0 + ((y + 0.5) / _LANDSCAPE_Y_BINS) * 2.0)
                    for _x, y in cells
                ],
                s=[
                    15.0 + min(72.0, 12.0 * math.log2(background_grid[cell] + 1))
                    for cell in cells
                ],
                c="#9ca3af",
                marker="o",
                alpha=0.52,
                edgecolors="white",
                linewidths=0.3,
                label="All tested candidates (binned)",
                zorder=2,
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
            axis.scatter(
                [], [], c="#9ca3af", marker="o", label="All tested candidates (binned)"
            )
        for status in ("significant_down", "significant_up"):
            _label, color, marker = _STATUS_STYLE[status]
            points = significant_points[status]
            condition_label = (
                f"Significant: {treatment} < {control}"
                if status == "significant_down"
                else f"Significant: {treatment} > {control}"
            )
            axis.scatter(
                [point[0] for point in points],
                [100.0 * point[1] for point in points],
                s=35.0,
                c=color,
                marker=marker,
                alpha=0.95,
                edgecolors="#111827",
                linewidths=0.45,
                label=condition_label,
                zorder=4,
            )
        axis.set_xscale("log")
        axis.set_xlim(*plot_x_limits)
        axis.set_ylim(-100.0, 100.0)
        axis.axhline(0.0, color="#111827", linewidth=0.7)
        if depth_threshold > 0:
            axis.axvline(
                depth_threshold,
                color="#7c3aed",
                linestyle="--",
                linewidth=0.9,
                label="Declared mean-depth threshold",
                zorder=3,
            )
        axis.axhline(
            100.0 * effect_threshold,
            color="#d97706",
            linestyle=":",
            linewidth=0.9,
            label="Declared ±effect threshold",
            zorder=3,
        )
        axis.axhline(
            -100.0 * effect_threshold,
            color="#d97706",
            linestyle=":",
            linewidth=0.9,
            zorder=3,
        )
        axis.text(
            0.01,
            0.98,
            f"Declared gates: {depth_gate_note}; "
            f"|{treatment} − {control}| > {100.0 * effect_threshold:g} pp",
            ha="left",
            va="top",
            transform=axis.transAxes,
            fontsize=7.5,
        )
        axis.set_title("Candidate editing landscape")
        axis.set_xlabel("Mean analysis depth (log scale)")
        axis.set_ylabel(
            f"{treatment} − {control} mean editing-rate difference (percentage points)"
        )
        axis.grid(True, which="both", color="#d1d5db", linewidth=0.45, alpha=0.6)
        axis.legend(loc="lower right", frameon=True, fontsize=7.0)
        figure.subplots_adjust(left=0.13, right=0.98, bottom=0.17, top=0.90)

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
            f"Candidate landscape of mean analysis depth versus {treatment}-minus-"
            f"{control} editing-rate difference in percentage points. A complete "
            "binned tested-candidate background is overlaid with exact significant "
            f"candidate coordinates; {depth_caption}. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "The gray occupancy grid includes every successfully tested candidate; "
            "triangles mark exact threshold-passing coordinates. "
            f"{depth_caption.capitalize()}. These geometric guides are not the "
            "complete calling rule: Step 09 also applies the "
            f"declared BH FDR ({summary['fdr_threshold']}), common-odds-ratio "
            f"({summary['common_or_threshold']}), and background policy before a "
            "candidate is called significant."
        ),
        input_roles=("all_sites", "summary"),
        mapping=(
            "background x=mean_analysis_dp log-grid center; background "
            "y=100*treatment_control_difference grid center; background marker "
            "area=cell count; exact overlays=(mean_analysis_dp, "
            "100*treatment_control_difference) for significant_up/down; lines="
            + (
                "declared mean_dp_threshold and ±absolute_difference_threshold"
                if depth_threshold > 0
                else (
                    "±absolute_difference_threshold only; zero mean_dp_threshold "
                    "is outside the log axis"
                )
            )
        ),
        population=(
            f"{population_count} successfully tested target candidates; fixed "
            f"{_LANDSCAPE_X_BINS}x{_LANDSCAPE_Y_BINS} complete-population occupancy "
            f"grid plus {significant_up_count + significant_down_count} exact significant "
            f"{'overlay' if significant_up_count + significant_down_count == 1 else 'overlays'}; "
            "no sampling"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _mutation_figure(results: ComputationalResults) -> ScientificFigure:
    summary = _table_row(results.summary)
    table = results.mutation_spectrum
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    rows = [dict(zip(table.header, row, strict=True)) for row in table.display_rows]
    mutations = tuple(row["mutation_type"] for row in rows)
    counts = tuple(int(row["candidate_count"]) for row in rows)
    target_change = summary["target_rna_change"]
    if mutations.count(target_change) != 1:
        _fail(
            "Admitted mutation spectrum does not contain the declared target RNA "
            f"change exactly once: {target_change!r}"
        )
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        colors = tuple(
            "#dc2626" if mutation == target_change else "#94a3b8"
            for mutation in mutations
        )
        bars = axis.bar(mutations, counts, color=colors, width=0.72)
        for bar, count in zip(bars, counts, strict=True):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(count),
                ha="center",
                va="bottom",
                fontsize=7.5,
            )
        for tick, mutation in zip(axis.get_xticklabels(), mutations, strict=True):
            if mutation == target_change:
                tick.set_color("#b91c1c")
                tick.set_fontweight("bold")
        axis.bar([], [], color="#dc2626", label=f"Declared target: {target_change}")
        axis.bar([], [], color="#94a3b8", label="Other RNA changes")
        axis.set_title("Candidate mutation spectrum")
        axis.set_xlabel("RNA reference > alternate")
        axis.set_ylabel("Candidate count")
        axis.grid(True, axis="y", color="#d1d5db", linewidth=0.45, alpha=0.7)
        axis.set_axisbelow(True)
        axis.legend(loc="upper right", frameon=True)
        figure.subplots_adjust(left=0.10, right=0.98, bottom=0.16, top=0.90)

    svg, digest, size = _render_svg("mutation-spectrum-figure", draw)
    total = sum(counts)
    nonzero = sum(count > 0 for count in counts)
    class_clause = "class has" if nonzero == 1 else "classes have"
    summary_text = (
        f"{total} candidates across 12 canonical single-nucleotide changes; "
        f"{nonzero} mutation {class_clause} nonzero counts. The declared target "
        f"RNA change is {target_change}."
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
            "candidate table or consume the existing PDF diagnostic. The declared "
            "target RNA change is highlighted. This is candidate-class composition; "
            "it does not establish PUM specificity or biological editing validity."
        ),
        input_roles=("mutation_spectrum", "summary"),
        mapping=(
            "x=mutation_type (canonical order); y=candidate_count; "
            "red=summary target_rna_change; grey=other RNA changes"
        ),
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
    significant_points = _exact_significant_points(
        results.all_sites,
        x_field="mean_control_af",
        y_field="mean_treatment_af",
        unit_interval=True,
    )
    expected_count = int(summary["successfully_tested_count"])
    if population_count != expected_count:
        _fail(
            "Condition-concordance population does not match the admitted Step 09 "
            f"summary: observed {population_count}; expected {expected_count}"
        )
    significant_up_count = int(summary["significant_up_count"])
    significant_down_count = int(summary["significant_down_count"])
    if (
        len(significant_points["significant_up"]) != significant_up_count
        or len(significant_points["significant_down"]) != significant_down_count
    ):
        _fail("Exact significant concordance points do not match the Step 09 summary")
    background_grid = _combined_occupancy(grid)
    control = summary["control_condition"]
    treatment = summary["treatment_condition"]

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        axis.plot(
            (0.0, 100.0),
            (0.0, 100.0),
            color="#111827",
            linestyle="--",
            linewidth=0.8,
            label=f"Equal {control} and {treatment} means",
        )
        cells = sorted(background_grid)
        axis.scatter(
            [100.0 * (x + 0.5) / _CONCORDANCE_BINS for x, _y in cells],
            [100.0 * (y + 0.5) / _CONCORDANCE_BINS for _x, y in cells],
            s=[
                15.0 + min(72.0, 12.0 * math.log2(background_grid[cell] + 1))
                for cell in cells
            ],
            c="#9ca3af",
            marker="o",
            alpha=0.52,
            edgecolors="white",
            linewidths=0.3,
            label="All tested candidates (binned)",
            zorder=2,
        )
        for status in ("significant_down", "significant_up"):
            _label, color, marker = _STATUS_STYLE[status]
            points = significant_points[status]
            condition_label = (
                f"Significant: {treatment} < {control}"
                if status == "significant_down"
                else f"Significant: {treatment} > {control}"
            )
            axis.scatter(
                [100.0 * point[0] for point in points],
                [100.0 * point[1] for point in points],
                s=35.0,
                c=color,
                marker=marker,
                alpha=0.95,
                edgecolors="#111827",
                linewidths=0.45,
                label=condition_label,
                zorder=4,
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
        axis.set_xlim(0.0, 100.0)
        axis.set_ylim(0.0, 100.0)
        axis.set_aspect("equal", adjustable="box")
        axis.set_title("Condition editing-rate concordance")
        axis.set_xlabel(f"{control} mean editing rate (%)")
        axis.set_ylabel(f"{treatment} mean editing rate (%)")
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
            f"Scatter plot of Step 09 mean {control} editing rate versus mean "
            f"{treatment} editing rate in percent, with an equality diagonal, a "
            "complete binned tested-candidate background, and exact significant "
            "candidate overlays. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "Every successfully tested target candidate is included through a "
            f"fixed {_CONCORDANCE_BINS} × {_CONCORDANCE_BINS} occupancy grid. "
            "The axes use Step 09's unweighted means across manifest-defined "
            "replicates; reporting does not pool allele and depth counts. Cell "
            "centers approximate coordinates and capped log-scaled symbol area "
            "reflects candidates per occupied cell. Significant candidates are "
            "overlaid at their exact admitted condition means; points above the "
            f"equality diagonal have higher mean editing in {treatment}, and points "
            f"below it have higher mean editing in {control}."
        ),
        input_roles=("all_sites", "summary"),
        mapping=(
            "background x=100*mean_control_af grid center; background "
            "y=100*mean_treatment_af grid center; background marker area=cell "
            "count; exact overlays=(100*mean_control_af, 100*mean_treatment_af) "
            "for significant_up/down; diagonal=equal condition means"
        ),
        population=(
            f"{population_count} successfully tested target candidates; fixed "
            f"{_CONCORDANCE_BINS}x{_CONCORDANCE_BINS} complete-population occupancy "
            f"grid plus {significant_up_count + significant_down_count} exact significant "
            f"{'overlay' if significant_up_count + significant_down_count == 1 else 'overlays'}; "
            "no sampling"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _short_candidate_id(value: str, *, limit: int = 34) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _paired_sample_profile_figure(
    candidate_display: SelectedCandidateProjection,
) -> ScientificFigure:
    profiles = candidate_display.candidates
    if len(profiles) > _PROFILE_DISPLAY_LIMIT:
        _fail("Shared candidate display exceeds the paired-profile display limit")
    pair_count = len(profiles[0].pairs) if profiles else 0
    if any(len(candidate.pairs) != pair_count for candidate in profiles):
        _fail("Shared candidate display changes its manifest pair roster")

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
        for profile_index, candidate in enumerate(profiles, start=1):
            axis = figure.add_subplot(row_count, columns, profile_index)
            complete_pair_count = 0
            for pair_index, pair in enumerate(candidate.pairs):
                control_af = pair.control.allele_fraction
                treatment_af = pair.treatment.allele_fraction
                if control_af is None or treatment_af is None:
                    continue
                complete_pair_count += 1
                axis.plot(
                    (0.0, 1.0),
                    (100.0 * float(control_af), 100.0 * float(treatment_af)),
                    marker="o",
                    markersize=3.2,
                    linewidth=0.9,
                    alpha=0.72,
                    color=_PAIR_COLORS[pair_index % len(_PAIR_COLORS)],
                    label=pair.replicate,
                )
            if (
                candidate.mean_control_af is not None
                and candidate.mean_treatment_af is not None
            ):
                axis.plot(
                    (0.0, 1.0),
                    (
                        100.0 * float(candidate.mean_control_af),
                        100.0 * float(candidate.mean_treatment_af),
                    ),
                    marker="D",
                    markersize=4.0,
                    linewidth=1.8,
                    color="#111827",
                    label="Step 09 mean",
                )
            axis.set_xlim(-0.12, 1.12)
            axis.set_ylim(0.0, 100.0)
            axis.set_xticks((0.0, 1.0))
            axis.set_xticklabels(
                (
                    _short_candidate_id(
                        candidate_display.control_condition,
                        limit=18,
                    ),
                    _short_candidate_id(
                        candidate_display.treatment_condition,
                        limit=18,
                    ),
                ),
                fontsize=7,
            )
            axis.set_title(
                f"{candidate.display_rank}. "
                f"{_short_candidate_id(candidate.candidate_id)}",
                fontsize=8.5,
                loc="left",
            )
            axis.grid(True, axis="y", color="#d1d5db", linewidth=0.4, alpha=0.6)
            if (profile_index - 1) % columns == 0:
                axis.set_ylabel("Editing rate (%)", fontsize=7.5)
            if profile_index == 1:
                if complete_pair_count <= _PAIR_LEGEND_LIMIT:
                    axis.legend(loc="best", fontsize=5.5, frameon=True)
                else:
                    axis.text(
                        0.02,
                        0.98,
                        f"{complete_pair_count} manifest pairs; exact values in "
                        "candidate records",
                        ha="left",
                        va="top",
                        transform=axis.transAxes,
                        fontsize=5.8,
                    )
        figure.suptitle(
            "Selected significant-candidate paired sample profiles",
            fontsize=11,
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.98,
            bottom=0.07,
            top=0.93,
            hspace=0.62,
            wspace=0.26,
        )

    row_count = max(1, math.ceil(len(profiles) / 2))
    svg, digest, size = _render_svg(
        "paired-sample-profile-figure",
        draw,
        figsize=(
            8.0,
            min(
                _PROFILE_MAX_HEIGHT_INCHES,
                max(4.8, _PROFILE_ROW_HEIGHT_INCHES * row_count + 0.8),
            ),
        ),
    )
    selected_ids = tuple(candidate.candidate_id for candidate in profiles)
    pair_mapping = "; ".join(
        f"{pair.replicate}: {pair.control.sample_id} → {pair.treatment.sample_id}"
        for pair in (profiles[0].pairs if profiles else ())
    )
    selection_description = (
        "the admitted Step 10 display order"
        if candidate_display.selection_source == "step10_display_rank"
        else "the fixed Step 09 presentation rule"
    )
    summary_text = (
        f"{len(profiles)} of {candidate_display.significant_candidate_count} "
        f"significant {'candidate is' if len(profiles) == 1 else 'candidates are'} "
        f"displayed across {pair_count} manifest-defined replicate pairs."
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
            f"The shared display-only roster uses at most {_PROFILE_DISPLAY_LIMIT} "
            f"candidates selected by {selection_description}; this figure performs "
            "no selection or reranking. Colored lines join the exact manifest-defined "
            f"sample pairs ({pair_mapping}); black diamonds join Step 09's "
            "unweighted condition means. Selected IDs: "
            + (", ".join(selected_ids) if selected_ids else "none")
            + "."
        ),
        input_roles=(
            (
                "significant_sites",
                "summary",
                "sample_manifest",
                "candidate_context",
                "receipt",
            )
            if candidate_display.selection_source == "step10_display_rank"
            else ("significant_sites", "summary", "sample_manifest")
        ),
        mapping=(
            "x={control_condition,treatment_condition}; y=100*AF__sample; "
            "line=manifest replicate pair; black diamonds=Step 09 condition means; "
            f"candidate order={candidate_display.selection_source}"
        ),
        population=(
            f"Shared ordered roster of {len(profiles)} of "
            f"{candidate_display.significant_candidate_count} significant candidates "
            f"from {selection_description}; all manifest-defined pairs"
        ),
        svg_sha256=digest,
        svg_size_bytes=size,
        unavailable_reason=None,
    )


def _location_memberships(
    table: ComputationalTable,
) -> tuple[tuple[int, ...], int]:
    _assert_snapshot(table.snapshot, f"scientific figure input {table.artifact_id!r}")
    counts = [0] * (len(_LOCATION_FIELDS) + 1)
    population_count = 0
    for row in _candidate_rows(table):
        population_count += 1
        recorded_overlap = False
        for index, (field, _label) in enumerate(_LOCATION_FIELDS):
            if row[field] == "TRUE":
                counts[index] += 1
                recorded_overlap = True
        if not recorded_overlap:
            counts[-1] += 1
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
    labels = (
        *tuple(label for _field, label in _LOCATION_FIELDS),
        "No recorded overlap",
    )

    def draw(figure: Any) -> None:
        axis = figure.add_subplot(1, 1, 1)
        positions = tuple(range(len(labels)))
        colors = (*("#2563eb" for _ in _LOCATION_FIELDS), "#64748b")
        bars = axis.barh(positions, percentages, color=colors, height=0.66)
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
                f"{count}/{population_count} ({percentage:.1f}%)"
                if population_count
                else "0/0 (0.0%)",
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
        axis.set_xlabel(
            "Percentage of significant candidates (shared denominator; memberships nonexclusive)"
        )
        axis.grid(True, axis="x", color="#d1d5db", linewidth=0.45, alpha=0.7)
        axis.set_axisbelow(True)
        figure.subplots_adjust(left=0.18, right=0.96, bottom=0.16, top=0.90)

    svg, digest, size = _render_svg("location-membership-figure", draw)
    summary_text = (
        f"Among {population_count} significant candidates, the independently "
        "recorded memberships are "
        + ", ".join(
            f"{label}={count} ({percentage:.1f}%)"
            for label, count, percentage in zip(
                labels, counts, percentages, strict=True
            )
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
            "UTR, exon, and intron overlap memberships plus an explicit no-"
            "recorded-overlap category. Each label gives count, common denominator, "
            "and percentage. " + summary_text
        ),
        text_summary=summary_text,
        caption=(
            "The complete significant-sites population is counted against each "
            "producer-recorded Step 08 GTF-overlap flag. Memberships are "
            "independent and nonexclusive: CDS and UTR memberships can also be "
            "exonic, and transcript isoforms can give one candidate several "
            "memberships. Counts and percentages therefore need not sum to the "
            "candidate population or 100%. ‘No recorded overlap’ means all five "
            "admitted flags are false; it is not renamed or inferred as intergenic. "
            "Reporting does not reannotate or infer an exclusive region."
        ),
        input_roles=("significant_sites", "summary"),
        mapping=(
            "y={is_five_prime_utr,is_cds,is_three_prime_utr,is_exon,is_intron}; "
            "additional y=no recorded overlap when all five flags are FALSE; "
            "x=count / all significant candidates * 100 for each displayed category"
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
            "background x=mean_analysis_dp log-grid center; background "
            "y=100*treatment_control_difference grid center; background marker "
            "area=cell count; exact significant_up/down overlays; lines=declared "
            "mean_dp_threshold and ±absolute_difference_threshold",
        ),
        (
            "mutation-spectrum-figure",
            "Candidate mutation spectrum",
            ("mutation_spectrum", "summary"),
            "x=mutation_type (canonical order); y=candidate_count; "
            "color=declared target_rna_change versus other RNA changes",
        ),
        (
            "condition-concordance-figure",
            "Condition editing-rate concordance",
            ("all_sites", "summary"),
            "background x=100*mean_control_af grid center; background "
            "y=100*mean_treatment_af grid center; background marker area=cell "
            "count; exact significant_up/down overlays; diagonal=equal means",
        ),
        (
            "paired-sample-profile-figure",
            "Selected candidate per-sample profiles",
            ("significant_sites", "summary", "sample_manifest"),
            "x={control_condition,treatment_condition}; y=100*AF__sample; "
            "line=manifest replicate pair; black diamonds=Step 09 condition means",
        ),
        (
            "location-membership-figure",
            "Candidate location memberships",
            ("significant_sites", "summary"),
            "y={is_five_prime_utr,is_cds,is_three_prime_utr,is_exon,is_intron}; "
            "additional y=no recorded overlap when all five flags are FALSE; "
            "x=count/all significant candidates*100 per category",
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
    candidate_display: SelectedCandidateProjection | None = None,
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
        if candidate_display is None:
            _fail(
                "Admitted computational results require the shared selected-"
                "candidate projection for the paired-profile and selected-context "
                "figures"
            )
        try:
            current_figures = (
                _candidate_figure(results),
                _mutation_figure(results),
                _condition_concordance_figure(results),
                _paired_sample_profile_figure(candidate_display),
                _location_membership_figure(results),
            )
        except ReportRenderError:
            raise
        except (OSError, UnicodeError, csv.Error, ValueError, OverflowError) as exc:
            _fail(f"Could not render admitted Step 09 scientific figures: {exc}")
    context_figures = build_scientific_context_figures(
        scientific_context_results,
        scientific_context_unavailable_reason,
        candidate_display,
        unavailable_reason,
    )
    return (*current_figures, *context_figures)
