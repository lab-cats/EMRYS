"""Jinja environment construction and static HTML contract validation."""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Mapping, Sequence
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    PackageLoader,
    StrictUndefined,
    TemplateError,
    nodes,
    select_autoescape,
)

from .inputs import _assert_snapshot, _fail, _snapshot_regular
from .models import (
    ACTIVE_RESOURCE_ATTRIBUTES,
    CANDIDATE_TERMINOLOGY,
    CSS_RESOURCE_RE,
    PRIMARY_SCIENTIFIC_FIGURE_IDS,
    REMOTE_URI_RE,
    REPORT_SECTION_IDS_BY_VIEW,
    SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    ReportRenderError,
)

_SVG_DATA_URI_PREFIX = "data:image/svg+xml;base64,"


def build_environment() -> Environment:
    """Return the closed deterministic environment used by installed reports."""

    return Environment(
        loader=PackageLoader("emrys.reporting", "templates"),
        autoescape=select_autoescape(enabled_extensions=("html", "j2"), default=True),
        undefined=StrictUndefined,
        auto_reload=False,
        cache_size=0,
        keep_trailing_newline=True,
        newline_sequence="\n",
    )


def validate_template_source(source: str) -> None:
    try:
        syntax = Environment().parse(source)
    except TemplateError as exc:
        _fail(f"Report template is not valid Jinja: {exc}")
    safe_filters = [
        node for node in syntax.find_all(nodes.Filter) if node.name == "safe"
    ]
    if (
        source.count("{{ css | safe }}") != 1
        or len(safe_filters) != 1
        or not isinstance(safe_filters[0].node, nodes.Name)
        or safe_filters[0].node.name != "css"
    ):
        _fail("Report template may use |safe exactly once for the tracked CSS resource")
    if re.search(r"<script\b|\{[%{]\s*(?:include|import|from|extends)\b", source, re.I):
        _fail("Report template contains a script or external template dependency")
    if re.search(r"(?:https?:)?//", source, re.I):
        _fail("Report template contains a remote resource reference")


def _validate_css_resources(css: str, label: str) -> None:
    for match in CSS_RESOURCE_RE.finditer(css):
        resource = (match.group(2) or match.group(4) or "").strip()
        if resource.startswith(("data:", "#")):
            continue
        _fail(f"{label} contains a non-embedded CSS resource: {resource!r}")
    if re.search(r"</?style\b|<script\b", css, re.IGNORECASE):
        _fail(f"{label} contains an unsafe raw HTML boundary")


def render_html(view: Mapping[str, Any], css: str) -> bytes:
    environment = build_environment()
    source, _, _ = environment.loader.get_source(environment, "run_report.html.j2")
    validate_template_source(source)
    _validate_css_resources(css, "Report CSS resource")
    rendered = environment.get_template("run_report.html.j2").render(
        view=view,
        css=css,
    )
    return rendered.encode("utf-8")


def _scientific_svg_data_uri_error(source: str, figure_id: str) -> str | None:
    if not source.startswith(_SVG_DATA_URI_PREFIX):
        return (
            f"scientific figure {figure_id!r} must use an exact embedded SVG data URI"
        )
    payload = source[len(_SVG_DATA_URI_PREFIX) :]
    try:
        decoded = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return f"scientific figure {figure_id!r} has invalid base64 SVG data"
    if not decoded or re.search(rb"<svg(?:\s|>)", decoded, re.IGNORECASE) is None:
        return f"scientific figure {figure_id!r} data URI is not an SVG document"
    return None


class ReportHTMLInspector(HTMLParser):
    """Collect structural, accessibility, and active-resource facts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang: str | None = None
        self.title_count = 0
        self.title_depth = 0
        self.title_text: list[str] = []
        self.main_count = 0
        self.main_depth = 0
        self.main_attributes: list[dict[str, str | None]] = []
        self.heading_levels: list[int] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.active_resource_errors: list[str] = []
        self.emrys_table_depth = 0
        self.emrys_tables = 0
        self.current_table_has_caption = False
        self.current_table_bad_headers = 0
        self.table_errors: list[str] = []
        self.svg_depth = 0
        self.svg_count = 0
        self.accessible_svgs = 0
        self.banner_depth = 0
        self.banner_count = 0
        self.banner_text: list[str] = []
        self.base_count = 0
        self.style_depth = 0
        self.style_text: list[str] = []
        self.meta_refreshes: list[str] = []
        self.image_errors: list[str] = []
        self.details_count = 0
        self.wide_table_wraps = 0
        self.section_stack: list[str] = []
        self.scientific_figures: list[dict[str, Any]] = []
        self.current_scientific_figure: dict[str, Any] | None = None
        self.figure_guides: list[dict[str, Any]] = []
        self.current_figure_guide: dict[str, Any] | None = None
        self.candidate_index_count = 0
        self.candidate_index_ids: list[str] = []
        self.candidate_records: list[dict[str, Any]] = []
        self.current_candidate_record: dict[str, Any] | None = None
        self.scientific_figure_errors: list[str] = []

    @staticmethod
    def _classes(attributes: Mapping[str, str | None]) -> set[str]:
        return set((attributes.get("class") or "").split())

    @staticmethod
    def _resource_values(name: str, value: str) -> list[str]:
        if name != "srcset":
            return [value]
        stripped = value.strip()
        if stripped.startswith("data:"):
            if re.fullmatch(r"data:[^\s]+(?:\s+\d+(?:\.\d+)?[wx])?", stripped):
                return [stripped.split()[0]]
            return ["invalid-or-multiple-data-srcset"]
        return [item.strip().split()[0] for item in value.split(",") if item.strip()]

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if tag == "html":
            self.html_lang = attributes.get("lang")
        if tag == "title" and not self.svg_depth:
            self.title_count += 1
            self.title_depth = 1
        elif self.title_depth:
            self.title_depth += 1
        if tag == "base":
            self.base_count += 1
        if tag == "details":
            self.details_count += 1
        if tag == "script":
            self.active_resource_errors.append("<script> is not permitted")
        if tag in {"iframe", "object", "embed"}:
            self.active_resource_errors.append(f"<{tag}> is not permitted")
        if tag == "img" and not (
            attributes.get("alt")
            or (
                attributes.get("role") == "presentation" and attributes.get("alt") == ""
            )
        ):
            self.image_errors.append("<img> lacks alternative text")
        if tag == "meta" and (attributes.get("http-equiv") or "").lower() == "refresh":
            self.meta_refreshes.append(attributes.get("content") or "")
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "main":
            self.main_count += 1
            self.main_depth += 1
            self.main_attributes.append(attributes)
        elif self.main_depth and re.fullmatch(r"h[1-6]", tag):
            self.heading_levels.append(int(tag[1]))

        classes = self._classes(attributes)
        if "emrys-table-wrap-wide" in classes:
            self.wide_table_wraps += 1
        if "candidate-index-block" in classes:
            self.candidate_index_count += 1
        if "candidate-index-record" in classes and attributes.get(
            "data-candidate-id"
        ):
            self.candidate_index_ids.append(str(attributes["data-candidate-id"]))
        if tag == "article" and "candidate-evidence-record" in classes:
            record = {
                "id": attributes.get("id"),
                "candidate_id": attributes.get("data-candidate-id"),
                "rank": attributes.get("data-candidate-rank"),
                "groups": set(),
            }
            self.candidate_records.append(record)
            self.current_candidate_record = record
        if (
            self.current_candidate_record is not None
            and "candidate-evidence-group" in classes
            and attributes.get("data-evidence-group")
        ):
            self.current_candidate_record["groups"].add(
                str(attributes["data-evidence-group"])
            )
        if tag == "section":
            self.section_stack.append(element_id or "")
        if tag == "article" and "figure-guide-entry" in classes:
            record = {
                "id": attributes.get("id"),
                "figure_id": attributes.get("data-figure-id"),
                "question": 0,
                "reading": 0,
                "inputs": 0,
                "population": 0,
                "limitations": 0,
            }
            self.figure_guides.append(record)
            self.current_figure_guide = record
        if self.current_figure_guide is not None:
            for class_name, field in (
                ("figure-guide-question", "question"),
                ("figure-guide-reading", "reading"),
                ("figure-guide-inputs", "inputs"),
                ("figure-guide-population", "population"),
                ("figure-guide-limitations", "limitations"),
            ):
                if class_name in classes:
                    self.current_figure_guide[field] += 1
        if tag == "figure":
            if self.current_scientific_figure is not None:
                self.scientific_figure_errors.append(
                    "scientific figures may not contain nested figures"
                )
            if "scientific-figure" in classes:
                record = {
                    "id": attributes.get("id"),
                    "status": attributes.get("data-figure-status"),
                    "section_id": (
                        self.section_stack[-1] if self.section_stack else None
                    ),
                    "images": [],
                    "captions": 0,
                    "summaries": 0,
                    "unavailable_messages": 0,
                }
                self.scientific_figures.append(record)
                self.current_scientific_figure = record
        if self.current_scientific_figure is not None:
            if tag == "img":
                self.current_scientific_figure["images"].append(attributes)
            if tag == "figcaption":
                self.current_scientific_figure["captions"] += 1
            if "figure-summary" in classes:
                self.current_scientific_figure["summaries"] += 1
            if "figure-unavailable" in classes:
                self.current_scientific_figure["unavailable_messages"] += 1
        if tag == "table" and "emrys-table" in classes:
            self.emrys_table_depth = 1
            self.emrys_tables += 1
            self.current_table_has_caption = False
            self.current_table_bad_headers = 0
        elif self.emrys_table_depth:
            self.emrys_table_depth += 1
            if tag == "caption":
                self.current_table_has_caption = True
            if tag == "th" and attributes.get("scope") not in {"col", "row"}:
                self.current_table_bad_headers += 1

        if tag == "svg":
            self.svg_depth += 1
            self.svg_count += 1
            if attributes.get("role") == "img" and (
                attributes.get("aria-label") or attributes.get("aria-labelledby")
            ):
                self.accessible_svgs += 1
        elif self.svg_depth:
            self.svg_depth += 1
        if "state-banner" in classes:
            self.banner_count += 1
            self.banner_depth = 1
        elif self.banner_depth:
            self.banner_depth += 1
        if tag == "style":
            self.style_depth = 1
        elif self.style_depth:
            self.style_depth += 1
        inline_style = attributes.get("style")
        if inline_style:
            try:
                _validate_css_resources(inline_style, f"<{tag}> style")
            except ReportRenderError as exc:
                self.active_resource_errors.append(str(exc))
        for name, value in attrs:
            if value is None or (tag, name) not in ACTIVE_RESOURCE_ATTRIBUTES:
                continue
            for resource in self._resource_values(name, value):
                if REMOTE_URI_RE.match(resource):
                    self.active_resource_errors.append(
                        f"<{tag}> {name} uses remote resource {resource!r}"
                    )
                elif not (resource.startswith(("data:", "#")) or resource == ""):
                    self.active_resource_errors.append(
                        f"<{tag}> {name} is not embedded: {resource!r}"
                    )

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "figure" and self.current_scientific_figure is not None:
            self.current_scientific_figure = None
        if tag == "article" and self.current_figure_guide is not None:
            self.current_figure_guide = None
        if tag == "article" and self.current_candidate_record is not None:
            self.current_candidate_record = None
        if tag == "section" and self.section_stack:
            self.section_stack.pop()
        if tag == "main" and self.main_depth:
            self.main_depth -= 1
        if self.emrys_table_depth:
            self.emrys_table_depth -= 1
            if tag == "table" and self.emrys_table_depth == 0:
                if not self.current_table_has_caption:
                    self.table_errors.append("EMRYS table lacks a caption")
                if self.current_table_bad_headers:
                    self.table_errors.append("EMRYS table has headers without scope")
        if self.svg_depth:
            self.svg_depth -= 1
        if self.banner_depth:
            self.banner_depth -= 1
        if self.style_depth:
            self.style_depth -= 1
            if tag == "style" and self.style_depth == 0:
                try:
                    _validate_css_resources(
                        "".join(self.style_text), "rendered <style>"
                    )
                except ReportRenderError as exc:
                    self.active_resource_errors.append(str(exc))
                self.style_text = []
        if self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.banner_depth:
            self.banner_text.append(data)
        if self.style_depth:
            self.style_text.append(data)
        if self.title_depth:
            self.title_text.append(data)


def validate_rendered_html(
    path: Path,
    *,
    expected_banner: str,
    expected_identity: Mapping[str, str],
    expected_candidate_ids: Sequence[str] = (),
) -> None:
    report_view = expected_identity.get("data-report-view")
    if report_view not in REPORT_SECTION_IDS_BY_VIEW:
        _fail(f"Rendered report has an unknown expected view: {report_view!r}")
    snapshot = _snapshot_regular(path, "rendered HTML report")
    if snapshot.size_bytes == 0:
        _fail(f"Rendered HTML report is empty: {path}")
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read rendered HTML report {path}: {exc}")
    if not re.match(r"\s*<!doctype\s+html", content, re.IGNORECASE):
        _fail("Rendered report does not begin with an HTML doctype")
    inspector = ReportHTMLInspector()
    try:
        inspector.feed(content)
        inspector.close()
    except Exception as exc:
        _fail(f"Could not parse rendered HTML report: {exc}")
    if inspector.html_lang != "en":
        _fail("Rendered report must declare html lang='en'")
    observed_title = " ".join("".join(inspector.title_text).split())
    if inspector.title_count != 1 or not observed_title:
        _fail("Rendered report must contain exactly one non-empty document title")
    if inspector.main_count != 1:
        _fail(
            f"Rendered report must contain exactly one main landmark; found {inspector.main_count}"
        )
    if not inspector.heading_levels or inspector.heading_levels[0] != 1:
        _fail("Rendered report must begin its main heading sequence with h1")
    for previous, current in zip(
        inspector.heading_levels, inspector.heading_levels[1:]
    ):
        if current > previous + 1:
            _fail(f"Rendered report heading order jumps from h{previous} to h{current}")
    if inspector.duplicate_ids:
        _fail(
            "Rendered report contains duplicate IDs: "
            + ", ".join(sorted(inspector.duplicate_ids))
        )
    if inspector.base_count or inspector.meta_refreshes:
        _fail("Rendered report contains navigation-capable HTML")
    if inspector.active_resource_errors:
        _fail(
            "Rendered report contains active resources:\n- "
            + "\n- ".join(inspector.active_resource_errors)
        )
    if inspector.image_errors:
        _fail(
            "Rendered report image accessibility failed: "
            + "; ".join(inspector.image_errors)
        )
    if inspector.current_scientific_figure is not None:
        inspector.scientific_figure_errors.append(
            "scientific figure lacks a closing figure element"
        )
    if report_view == "scientific":
        expected_figure_ids = (
            *PRIMARY_SCIENTIFIC_FIGURE_IDS,
            *SUPPORTING_SCIENTIFIC_FIGURE_IDS,
        )
        observed_figure_ids = tuple(
            str(figure["id"] or "") for figure in inspector.scientific_figures
        )
        if observed_figure_ids != expected_figure_ids:
            inspector.scientific_figure_errors.append(
                "scientific figure roster must be exactly "
                + ", ".join(expected_figure_ids)
            )
        observed_primary = tuple(
            str(figure["id"] or "")
            for figure in inspector.scientific_figures
            if figure["section_id"] == "primary-scientific-figures-section"
        )
        observed_supporting = tuple(
            str(figure["id"] or "")
            for figure in inspector.scientific_figures
            if figure["section_id"] == "supporting-scientific-figures-section"
        )
        if observed_primary != PRIMARY_SCIENTIFIC_FIGURE_IDS:
            inspector.scientific_figure_errors.append(
                "primary scientific figure grouping must be exactly "
                + ", ".join(PRIMARY_SCIENTIFIC_FIGURE_IDS)
            )
        if observed_supporting != SUPPORTING_SCIENTIFIC_FIGURE_IDS:
            inspector.scientific_figure_errors.append(
                "supporting scientific figure grouping must be exactly "
                + ", ".join(SUPPORTING_SCIENTIFIC_FIGURE_IDS)
            )
        misplaced = [
            str(figure["id"] or "<missing>")
            for figure in inspector.scientific_figures
            if figure["section_id"]
            not in {
                "primary-scientific-figures-section",
                "supporting-scientific-figures-section",
            }
        ]
        if misplaced:
            inspector.scientific_figure_errors.append(
                "scientific figures are outside their owned sections: "
                + ", ".join(misplaced)
            )
        for figure in inspector.scientific_figures:
            figure_id = str(figure["id"] or "<missing>")
            status = figure["status"]
            images = figure["images"]
            if figure["captions"] != 1 or figure["summaries"] != 1:
                inspector.scientific_figure_errors.append(
                    f"scientific figure {figure_id!r} must have one caption and "
                    "one visible text summary"
                )
            if status == "available":
                if not images:
                    inspector.scientific_figure_errors.append(
                        f"scientific figure {figure_id!r} with status {status!r} "
                        "must have at least one image"
                    )
                else:
                    for index, image in enumerate(images, start=1):
                        if image.get("id") != f"{figure_id}-image-{index}":
                            inspector.scientific_figure_errors.append(
                                f"scientific figure {figure_id!r} image {index} "
                                "has the wrong ID"
                            )
                        source = image.get("src") or ""
                        if error := _scientific_svg_data_uri_error(
                            source, f"{figure_id} panel {index}"
                        ):
                            inspector.scientific_figure_errors.append(error)
                if figure["unavailable_messages"]:
                    inspector.scientific_figure_errors.append(
                        f"scientific figure {figure_id!r} has an unavailable message "
                        f"with status {status!r}"
                    )
            elif status == "unavailable":
                if images:
                    inspector.scientific_figure_errors.append(
                        f"unavailable scientific figure {figure_id!r} must not "
                        "contain an image"
                    )
                if figure["unavailable_messages"] != 1:
                    inspector.scientific_figure_errors.append(
                        f"unavailable scientific figure {figure_id!r} must have "
                        "one unavailable message"
                    )
            else:
                inspector.scientific_figure_errors.append(
                    f"scientific figure {figure_id!r} has unknown status {status!r}"
                )
        if inspector.svg_count:
            inspector.scientific_figure_errors.append(
                "scientific report must not contain raw SVG markup"
            )
        if inspector.details_count:
            inspector.scientific_figure_errors.append(
                "scientific report must not contain collapsible details content"
            )
        if inspector.wide_table_wraps:
            inspector.scientific_figure_errors.append(
                "scientific report must not contain horizontally scrollable tables"
            )
        observed_guides = tuple(
            str(guide["figure_id"] or "") for guide in inspector.figure_guides
        )
        if observed_guides != expected_figure_ids:
            inspector.scientific_figure_errors.append(
                "scientific figure guide roster must be exactly "
                + ", ".join(expected_figure_ids)
            )
        for guide in inspector.figure_guides:
            figure_id = str(guide["figure_id"] or "<missing>")
            if any(
                guide[field] != 1
                for field in (
                    "question",
                    "reading",
                    "inputs",
                    "population",
                    "limitations",
                )
            ):
                inspector.scientific_figure_errors.append(
                    f"scientific figure guide {figure_id!r} must show one question, "
                    "reading guide, input roster, population, and limitations statement"
                )
        expected_candidates = tuple(expected_candidate_ids)
        observed_record_ids = tuple(
            str(record["candidate_id"] or "") for record in inspector.candidate_records
        )
        observed_ranks = tuple(
            str(record["rank"] or "") for record in inspector.candidate_records
        )
        if expected_candidates:
            if inspector.candidate_index_count != 1:
                inspector.scientific_figure_errors.append(
                    "scientific report must contain one selected-candidate index"
                )
            if tuple(inspector.candidate_index_ids) != expected_candidates:
                inspector.scientific_figure_errors.append(
                    "selected-candidate index differs from the expected roster"
                )
            if observed_record_ids != expected_candidates:
                inspector.scientific_figure_errors.append(
                    "candidate evidence records differ from the expected roster"
                )
            if observed_ranks != tuple(
                str(index) for index in range(1, len(expected_candidates) + 1)
            ):
                inspector.scientific_figure_errors.append(
                    "candidate evidence record ranks are not contiguous from one"
                )
            required_groups = {"editing-rate", "location", "nearby-motifs"}
            for record in inspector.candidate_records:
                if not required_groups <= record["groups"]:
                    inspector.scientific_figure_errors.append(
                        "candidate evidence record lacks Editing rate, Location, or "
                        "Nearby motifs"
                    )
        elif (
            inspector.candidate_index_count
            or inspector.candidate_index_ids
            or inspector.candidate_records
        ):
            inspector.scientific_figure_errors.append(
                "scientific report contains unexpected selected-candidate content"
            )
    else:
        if inspector.scientific_figures:
            inspector.scientific_figure_errors.append(
                "evidence report must not contain scientific figure images"
            )
        if (
            inspector.candidate_index_count
            or inspector.candidate_index_ids
            or inspector.candidate_records
        ):
            inspector.scientific_figure_errors.append(
                "evidence report must not contain selected-candidate presentation "
                "content"
            )
    if inspector.scientific_figure_errors:
        _fail(
            "Rendered report scientific-figure validation failed: "
            + "; ".join(inspector.scientific_figure_errors)
        )
    if inspector.table_errors or (
        report_view == "evidence" and inspector.emrys_tables == 0
    ):
        _fail(
            "Rendered report table accessibility failed: "
            + "; ".join(inspector.table_errors or ["no EMRYS tables found"])
        )
    if report_view == "evidence" and inspector.accessible_svgs < 1:
        _fail("Rendered report lacks an accessible embedded figure")
    observed_banner = " ".join("".join(inspector.banner_text).split())
    if inspector.banner_count != 1 or observed_banner != " ".join(
        expected_banner.split()
    ):
        _fail(
            f"Rendered report does not contain the required state banner: {expected_banner}"
        )
    required_sections = REPORT_SECTION_IDS_BY_VIEW[report_view]
    missing_sections = required_sections - inspector.ids
    if missing_sections:
        _fail(
            "Rendered report lacks required sections: "
            + ", ".join(sorted(missing_sections))
        )
    other_sections = set().union(
        *(
            section_ids
            for view_name, section_ids in REPORT_SECTION_IDS_BY_VIEW.items()
            if view_name != report_view
        )
    )
    unexpected_sections = other_sections & inspector.ids
    if unexpected_sections:
        _fail(
            f"Rendered {report_view} report contains sections owned by another "
            "view: " + ", ".join(sorted(unexpected_sections))
        )
    if report_view == "scientific" and CANDIDATE_TERMINOLOGY not in content:
        _fail(f"Rendered report lacks fixed terminology: {CANDIDATE_TERMINOLOGY}")
    main_attributes = inspector.main_attributes[0]
    scientific_forbidden_attributes = {
        "data-css-sha256",
        "data-jinja-version",
        "data-renderer-version",
        "data-run-summary-sha256",
        "data-template-sha256",
    }
    if report_view == "scientific":
        observed_forbidden = scientific_forbidden_attributes & main_attributes.keys()
        if observed_forbidden:
            _fail(
                "Rendered scientific report exposes renderer provenance: "
                + ", ".join(sorted(observed_forbidden))
            )
    for attribute, expected in expected_identity.items():
        if main_attributes.get(attribute) != expected:
            _fail(f"Rendered report provenance differs for {attribute}")
    _assert_snapshot(snapshot, "rendered HTML report")
