"""Paired-CMH presentation invariants not owned by core HTML validation."""

from __future__ import annotations

from collections.abc import Mapping
from html.parser import HTMLParser
from typing import Any

from emrys.reporting import ReportProviderError

from .constants import CANDIDATE_TERMINOLOGY, SCIENTIFIC_REPORT_SECTION_IDS
from .figure_models import (
    PRIMARY_SCIENTIFIC_FIGURE_IDS,
    SUPPORTING_SCIENTIFIC_FIGURE_IDS,
)


class _Inspector(HTMLParser):
    """Collect only semantics specific to the paired-CMH presentation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.section_stack: list[str] = []
        self.figures: list[dict[str, Any]] = []
        self.current_figure: dict[str, Any] | None = None
        self.guides: list[dict[str, Any]] = []
        self.current_guide: dict[str, Any] | None = None
        self.candidate_index_count = 0
        self.candidate_index_ids: list[str] = []
        self.candidates: list[dict[str, Any]] = []
        self.current_candidate: dict[str, Any] | None = None
        self.selected_candidate_counts: list[str | None] = []
        self.raw_svg_count = 0
        self.details_count = 0
        self.wide_table_count = 0

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
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
        if tag == "main":
            self.selected_candidate_counts.append(
                attributes.get("data-selected-candidate-count")
            )
        if tag == "svg":
            self.raw_svg_count += 1
        if tag == "details":
            self.details_count += 1
        if "emrys-table-wrap-wide" in classes:
            self.wide_table_count += 1
        if "candidate-index-block" in classes:
            self.candidate_index_count += 1
        if "candidate-index-record" in classes:
            candidate_id = attributes.get("data-candidate-id")
            if candidate_id:
                self.candidate_index_ids.append(candidate_id)
        if tag == "article" and "candidate-evidence-record" in classes:
            candidate = {
                "id": attributes.get("data-candidate-id"),
                "rank": attributes.get("data-candidate-rank"),
                "groups": set(),
            }
            self.candidates.append(candidate)
            self.current_candidate = candidate
        if (
            self.current_candidate is not None
            and "candidate-evidence-group" in classes
        ):
            group = attributes.get("data-evidence-group")
            if group:
                self.current_candidate["groups"].add(group)
        if tag == "section":
            self.section_stack.append(attributes.get("id") or "")
        if tag == "article" and "figure-guide-entry" in classes:
            guide = {
                "id": attributes.get("data-figure-id"),
                "fields": set(),
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
                    self.current_guide["fields"].add(field)
        if tag == "figure" and "scientific-figure" in classes:
            if self.current_figure is not None:
                raise ReportProviderError("Scientific figures may not be nested")
            figure = {
                "id": attributes.get("id"),
                "section": self.section_stack[-1] if self.section_stack else None,
                "status": attributes.get("data-figure-status"),
                "images": 0,
                "captions": 0,
                "summaries": 0,
                "unavailable": 0,
            }
            self.figures.append(figure)
            self.current_figure = figure
        if self.current_figure is not None:
            if tag == "img":
                self.current_figure["images"] += 1
            if tag == "figcaption":
                self.current_figure["captions"] += 1
            if "figure-summary" in classes:
                self.current_figure["summaries"] += 1
            if "figure-unavailable" in classes:
                self.current_figure["unavailable"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "figure":
            self.current_figure = None
        if tag == "article":
            self.current_guide = None
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


def validate_scientific_html(
    html_bytes: bytes,
    expected_candidate_ids: tuple[str, ...],
) -> None:
    """Validate paired-CMH semantics; core later validates safety and structure."""

    try:
        content = html_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ReportProviderError("Scientific report is not UTF-8") from exc
    inspector = _Inspector()
    try:
        inspector.feed(content)
        inspector.close()
    except ReportProviderError:
        raise
    except Exception as exc:
        raise ReportProviderError(
            f"Could not inspect paired-CMH scientific report: {exc}"
        ) from exc

    errors: list[str] = []
    expected_figures = (
        *PRIMARY_SCIENTIFIC_FIGURE_IDS,
        *SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    )
    observed_figures = tuple(str(item["id"] or "") for item in inspector.figures)
    if observed_figures != expected_figures:
        errors.append("scientific figure roster or order differs")
    for section_id, expected in (
        ("primary-scientific-figures-section", PRIMARY_SCIENTIFIC_FIGURE_IDS),
        ("supporting-scientific-figures-section", SUPPORTING_SCIENTIFIC_FIGURE_IDS),
    ):
        observed = tuple(
            str(item["id"] or "")
            for item in inspector.figures
            if item["section"] == section_id
        )
        if observed != expected:
            errors.append(f"{section_id} figure grouping differs")
    for figure in inspector.figures:
        figure_id = str(figure["id"] or "<missing>")
        if figure["captions"] != 1 or figure["summaries"] != 1:
            errors.append(f"figure {figure_id!r} lacks its caption or summary")
        if figure["status"] == "available":
            if not figure["images"] or figure["unavailable"]:
                errors.append(f"available figure {figure_id!r} is incomplete")
        elif figure["status"] == "unavailable":
            if figure["images"] or figure["unavailable"] != 1:
                errors.append(f"unavailable figure {figure_id!r} is inconsistent")
        else:
            errors.append(f"figure {figure_id!r} has an unknown status")

    observed_guides = tuple(str(item["id"] or "") for item in inspector.guides)
    if observed_guides != expected_figures:
        errors.append("figure-guide roster differs from the figure roster")
    required_guide_fields = {
        "question",
        "reading",
        "inputs",
        "population",
        "limitations",
    }
    if any(item["fields"] != required_guide_fields for item in inspector.guides):
        errors.append("a figure guide is incomplete")

    observed_candidates = tuple(str(item["id"] or "") for item in inspector.candidates)
    if inspector.selected_candidate_counts != [str(len(expected_candidate_ids))]:
        errors.append("selected-candidate count differs")
    if expected_candidate_ids:
        if inspector.candidate_index_count != 1:
            errors.append("selected-candidate index count differs")
        if tuple(inspector.candidate_index_ids) != expected_candidate_ids:
            errors.append("selected-candidate index roster differs")
        if observed_candidates != expected_candidate_ids:
            errors.append("candidate-evidence roster differs")
        if tuple(str(item["rank"] or "") for item in inspector.candidates) != tuple(
            str(index) for index in range(1, len(expected_candidate_ids) + 1)
        ):
            errors.append("candidate-evidence ranks are not contiguous")
        required_groups = {"editing-rate", "location", "nearby-motifs"}
        if any(not required_groups <= item["groups"] for item in inspector.candidates):
            errors.append("candidate evidence lacks a required group")
    elif (
        inspector.candidate_index_count
        or inspector.candidate_index_ids
        or inspector.candidates
    ):
        errors.append("unexpected selected-candidate content is present")

    if not SCIENTIFIC_REPORT_SECTION_IDS <= inspector.ids:
        errors.append("required paired-CMH sections are missing")
    if CANDIDATE_TERMINOLOGY not in content:
        errors.append("fixed paired-CMH terminology is missing")
    if inspector.raw_svg_count:
        errors.append("raw SVG markup is not allowed in the scientific view")
    if inspector.details_count:
        errors.append("collapsible content is not allowed in the scientific view")
    if inspector.wide_table_count:
        errors.append("wide scrolling tables are not allowed in the scientific view")
    if errors:
        raise ReportProviderError(
            "Paired-CMH scientific report validation failed: " + "; ".join(errors)
        )
