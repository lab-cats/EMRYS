"""Static QMD construction and rendered-HTML contract validation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml

from .html_projection import build_report_body
from .inputs import _assert_snapshot, _fail, _snapshot_regular
from .models import (
    ACTIVE_RESOURCE_ATTRIBUTES,
    BODY_MARKER,
    CANDIDATE_TERMINOLOGY,
    CSS_MARKER,
    CSS_RESOURCE_RE,
    CSS_TEMPLATE,
    EXECUTABLE_QMD_RE,
    EXPECTED_QMD_BODY,
    EXPECTED_QMD_FRONTMATTER,
    QMD_TEMPLATE,
    REMOTE_URI_RE,
    REPORT_SECTION_IDS,
    SCIENCE_BANNERS,
    ApprovedTable,
    ReportRenderError,
)


def build_qmd_bytes(
    summary: Mapping[str, Any],
    tables: Sequence[ApprovedTable],
    *,
    template_bytes: bytes | None = None,
    css_bytes: bytes | None = None,
    render_metadata: Mapping[str, str] | None = None,
) -> bytes:
    if template_bytes is None:
        try:
            template_bytes = QMD_TEMPLATE.read_bytes()
        except OSError as exc:
            _fail(f"Could not read report QMD template {QMD_TEMPLATE}: {exc}")
    try:
        template = template_bytes.decode("utf-8")
    except UnicodeError as exc:
        _fail(f"Report QMD template is not UTF-8: {exc}")
    if css_bytes is None:
        try:
            css_bytes = CSS_TEMPLATE.read_bytes()
        except OSError as exc:
            _fail(f"Could not read report CSS template {CSS_TEMPLATE}: {exc}")
    try:
        css = css_bytes.decode("utf-8")
    except UnicodeError as exc:
        _fail(f"Report CSS template is not UTF-8: {exc}")
    _validate_css_resources(css, "Report CSS template")
    if re.search(r"</?style\b|<script\b", css, re.IGNORECASE):
        _fail("Report CSS template contains an unsafe raw HTML boundary")
    validate_qmd_template(template)
    qmd = template.replace(
        CSS_MARKER,
        '<style id="norad-report-styles">\n' + css + "\n</style>",
    ).replace(
        BODY_MARKER,
        build_report_body(summary, tables, render_metadata),
    )
    if EXECUTABLE_QMD_RE.search(qmd):
        _fail("Generated QMD contains an executable fenced cell")
    return qmd.encode("utf-8")
def validate_qmd_template(template: str) -> None:
    if template.count(BODY_MARKER) != 1:
        _fail(f"Report QMD template must contain exactly one {BODY_MARKER!r} marker")
    if template.count(CSS_MARKER) != 1:
        _fail(f"Report QMD template must contain exactly one {CSS_MARKER!r} marker")
    if EXECUTABLE_QMD_RE.search(template):
        _fail("Report QMD template contains an executable fenced cell")
    match = re.fullmatch(r"---\n(.*?)\n---(\n.*)", template, re.DOTALL)
    if match is None:
        _fail("Report QMD template must contain one closed YAML frontmatter block")

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_unique_mapping(
        loader: yaml.SafeLoader,
        node: yaml.nodes.MappingNode,
        deep: bool = False,
    ) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.YAMLError(f"duplicate YAML key: {key!r}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_unique_mapping,
    )
    try:
        frontmatter = yaml.load(match.group(1), Loader=UniqueKeyLoader)
    except (TypeError, yaml.YAMLError) as exc:
        _fail(f"Report QMD frontmatter is invalid: {exc}")
    if frontmatter != EXPECTED_QMD_FRONTMATTER:
        _fail("Report QMD frontmatter differs from the closed static HTML allowlist")
    if match.group(2) != EXPECTED_QMD_BODY:
        _fail(
            "Report QMD body must contain only the tracked static-contract "
            "comment and the report-body marker"
        )
def _validate_css_resources(css: str, label: str) -> None:
    for match in CSS_RESOURCE_RE.finditer(css):
        resource = (match.group(2) or match.group(4) or "").strip()
        if resource.startswith(("data:", "#")):
            continue
        _fail(f"{label} contains a non-embedded CSS resource: {resource!r}")
class ReportHTMLInspector(HTMLParser):
    """Collect local structural and active-resource facts from rendered HTML."""

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
        self.norad_table_depth = 0
        self.norad_tables = 0
        self.current_table_has_caption = False
        self.current_table_bad_headers = 0
        self.table_errors: list[str] = []
        self.svg_depth = 0
        self.accessible_svgs = 0
        self.banner_depth = 0
        self.banner_count = 0
        self.banner_text: list[str] = []
        self.base_count = 0
        self.style_depth = 0
        self.style_text: list[str] = []
        self.meta_refreshes: list[str] = []
        self.image_errors: list[str] = []

    @staticmethod
    def _classes(attributes: Mapping[str, str | None]) -> set[str]:
        return set((attributes.get("class") or "").split())

    @staticmethod
    def _resource_values(name: str, value: str) -> list[str]:
        if name != "srcset":
            return [value]
        stripped_value = value.strip()
        if stripped_value.startswith("data:"):
            if re.fullmatch(
                r"data:[^\s]+(?:\s+\d+(?:\.\d+)?[wx])?",
                stripped_value,
            ):
                return [stripped_value.split()[0]]
            return ["invalid-or-multiple-data-srcset"]
        values = []
        for candidate in value.split(","):
            stripped = candidate.strip()
            if stripped:
                values.append(stripped.split()[0])
        return values

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
            self.active_resource_errors.append(
                "<script> is not permitted in a static NORAD report"
            )
        if tag in {"iframe", "object", "embed"}:
            self.active_resource_errors.append(
                f"<{tag}> is not permitted in a static NORAD report"
            )
        if tag == "img" and not (
            attributes.get("alt")
            or (
                attributes.get("role") == "presentation" and attributes.get("alt") == ""
            )
        ):
            self.image_errors.append("<img> lacks non-empty alternative text")
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
        if tag == "table" and "norad-table" in classes:
            self.norad_table_depth = 1
            self.norad_tables += 1
            self.current_table_has_caption = False
            self.current_table_bad_headers = 0
        elif self.norad_table_depth:
            self.norad_table_depth += 1
            if tag == "caption":
                self.current_table_has_caption = True
            if tag == "th" and attributes.get("scope") not in {"col", "row"}:
                self.current_table_bad_headers += 1

        if tag == "svg":
            self.svg_depth += 1
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
                elif not (
                    resource.startswith(("data:", "#"))
                    or resource == ""
                ):
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
        if self.norad_table_depth:
            self.norad_table_depth -= 1
            if tag == "table" and self.norad_table_depth == 0:
                if not self.current_table_has_caption:
                    self.table_errors.append("NORAD table lacks a caption")
                if self.current_table_bad_headers:
                    self.table_errors.append(
                        "NORAD table has header cells without scope"
                    )
        if self.svg_depth:
            self.svg_depth -= 1
        if self.banner_depth:
            self.banner_depth -= 1
        if self.style_depth:
            self.style_depth -= 1
            if tag == "style" and self.style_depth == 0:
                try:
                    _validate_css_resources(
                        "".join(self.style_text),
                        "rendered <style>",
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
    expected_banner: str | None,
    expected_identity: Mapping[str, str] | None = None,
) -> None:
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
            f"Rendered report must contain exactly one main landmark; found "
            f"{inspector.main_count}"
        )
    if not inspector.heading_levels or inspector.heading_levels[0] != 1:
        _fail("Rendered report must begin its main heading sequence with h1")
    for previous, current in zip(
        inspector.heading_levels,
        inspector.heading_levels[1:],
    ):
        if current > previous + 1:
            _fail(f"Rendered report heading order jumps from h{previous} to h{current}")
    if inspector.duplicate_ids:
        _fail(
            "Rendered report contains duplicate element IDs: "
            + ", ".join(sorted(inspector.duplicate_ids))
        )
    if inspector.base_count:
        _fail("Rendered report must not contain a <base> element")
    if inspector.meta_refreshes:
        _fail("Rendered report must not contain meta refresh navigation")
    if inspector.active_resource_errors:
        _fail(
            "Rendered report contains non-embedded active resources:\n- "
            + "\n- ".join(inspector.active_resource_errors)
        )
    if inspector.image_errors:
        _fail(
            "Rendered report image accessibility validation failed: "
            + "; ".join(inspector.image_errors)
        )
    if inspector.norad_tables == 0 or inspector.table_errors:
        _fail(
            "Rendered report table accessibility validation failed: "
            + "; ".join(inspector.table_errors or ["no NORAD tables found"])
        )
    if inspector.accessible_svgs < 1:
        _fail("Rendered report lacks an accessible embedded figure")
    observed_banner = " ".join("".join(inspector.banner_text).split())
    if inspector.banner_count != 1:
        _fail("Rendered report must contain exactly one scientific-state banner")
    if expected_banner is None:
        allowed_banners = {
            " ".join(value.split()) for value in SCIENCE_BANNERS.values()
        }
        if observed_banner not in allowed_banners:
            _fail(
                "Existing report does not contain exactly one recognized "
                "scientific-state banner"
            )
    elif observed_banner != " ".join(expected_banner.split()):
        _fail(
            f"Rendered report does not contain the required state banner: "
            f"{expected_banner}"
        )
    if expected_identity is not None:
        missing_sections = REPORT_SECTION_IDS - inspector.ids
        if missing_sections:
            _fail(
                "Rendered report lacks required report sections: "
                + ", ".join(sorted(missing_sections))
            )
        if CANDIDATE_TERMINOLOGY not in content:
            _fail(
                "Rendered report lacks the fixed candidate terminology: "
                f"{CANDIDATE_TERMINOLOGY}"
            )
        main_attributes = inspector.main_attributes[0]
        for attribute, expected in expected_identity.items():
            if main_attributes.get(attribute) != expected:
                _fail(
                    "Rendered report provenance binding differs from the "
                    f"prepared context for {attribute}: observed "
                    f"{main_attributes.get(attribute)!r}; expected {expected!r}"
                )
    _assert_snapshot(snapshot, "rendered HTML report")
