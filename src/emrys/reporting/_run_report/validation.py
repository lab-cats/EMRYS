"""Jinja environment construction and static HTML contract validation."""

from __future__ import annotations

import re
from collections.abc import Mapping
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
    CSS_RESOURCE_RE,
    EVIDENCE_REPORT_SECTION_IDS,
    REMOTE_URI_RE,
    ReportRenderError,
)

SCIENTIFIC_PRESENTATION_SECTION_IDS = {
    "scientific-summary-section",
    "primary-scientific-figures-section",
    "supporting-scientific-figures-section",
    "figure-guide-section",
    "methods-data-note-section",
}


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
        self.scientific_presentations = 0

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
        if classes & {
            "scientific-figure",
            "candidate-index-block",
            "candidate-index-record",
            "candidate-evidence-record",
        }:
            self.scientific_presentations += 1
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
) -> None:
    """Validate every provider's safe shell and the fixed evidence view."""

    report_view = expected_identity.get("data-report-view")
    if report_view not in {"scientific", "evidence"}:
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
            "Rendered report must contain exactly one main landmark; "
            f"found {inspector.main_count}"
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
    if inspector.table_errors:
        _fail(
            "Rendered report table accessibility failed: "
            + "; ".join(inspector.table_errors)
        )
    if report_view == "evidence":
        if inspector.emrys_tables == 0:
            _fail("Rendered evidence report contains no EMRYS tables")
        if inspector.accessible_svgs < 1:
            _fail("Rendered evidence report lacks an accessible embedded figure")
        missing = EVIDENCE_REPORT_SECTION_IDS - inspector.ids
        if missing:
            _fail(
                "Rendered evidence report lacks required sections: "
                + ", ".join(sorted(missing))
            )
        unexpected = SCIENTIFIC_PRESENTATION_SECTION_IDS & inspector.ids
        if unexpected or inspector.scientific_presentations:
            _fail(
                "Rendered evidence report contains scientific or selected-candidate "
                "presentation content"
            )
    else:
        unexpected = EVIDENCE_REPORT_SECTION_IDS & inspector.ids
        if unexpected:
            _fail(
                "Rendered scientific report contains core evidence sections: "
                + ", ".join(sorted(unexpected))
            )
    observed_banner = " ".join("".join(inspector.banner_text).split())
    if inspector.banner_count != 1 or observed_banner != " ".join(
        expected_banner.split()
    ):
        _fail(
            f"Rendered report does not contain the required state banner: {expected_banner}"
        )
    main_attributes = inspector.main_attributes[0]
    if report_view == "scientific":
        forbidden = {
            "data-css-sha256",
            "data-jinja-version",
            "data-renderer-version",
            "data-run-summary-sha256",
            "data-template-sha256",
        }
        observed = forbidden & main_attributes.keys()
        if observed:
            _fail(
                "Rendered scientific report exposes core renderer provenance: "
                + ", ".join(sorted(observed))
            )
    for attribute, expected in expected_identity.items():
        if main_attributes.get(attribute) != expected:
            _fail(f"Rendered report provenance differs for {attribute}")
    _assert_snapshot(snapshot, "rendered HTML report")
