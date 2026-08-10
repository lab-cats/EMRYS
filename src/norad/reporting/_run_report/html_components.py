"""Reusable escaped HTML components for static NORAD run reports."""

from __future__ import annotations

import html
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .models import (
    CSS_TEMPLATE,
    PRODUCER,
    PRODUCER_VERSION,
    QMD_TEMPLATE,
    QUARTO_VERSION,
    SAFE_STATUS_RE,
    ApprovedTable,
)


def _fallback_render_metadata() -> dict[str, str]:
    """Describe in-memory QMD generation when no execution context exists."""

    return {
        "css_template_path": str(CSS_TEMPLATE),
        "css_template_sha256": "not bound in in-memory generation",
        "qmd_template_path": str(QMD_TEMPLATE),
        "qmd_template_sha256": "not bound in in-memory generation",
        "quarto_path": "not invoked during in-memory generation",
        "quarto_sha256": "not bound in in-memory generation",
        "quarto_version": QUARTO_VERSION,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": "not bound in in-memory generation",
        "run_summary_sha256": "not bound in in-memory generation",
    }


def _escape(value: Any) -> str:
    if value is None:
        text = "Not available"
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    return html.escape(text, quote=True).replace("`", "&#96;")


def _status_class(value: Any) -> str:
    normalized = SAFE_STATUS_RE.sub("-", str(value).lower()).strip("-")
    return f"status-{normalized or 'unknown'}"


def _status(value: Any) -> str:
    return f'<span class="{_status_class(value)}">{_escape(value)}</span>'


def _empty(message: str) -> str:
    return f'<p class="empty-state">{_escape(message)}</p>'


def _section(section_id: str, title: str, body: str) -> str:
    heading_id = f"{section_id}-heading"
    return (
        f'<section id="{section_id}" class="report-section" '
        f'aria-labelledby="{heading_id}">\n'
        f'<h2 id="{heading_id}">{_escape(title)}</h2>\n'
        f"{body}\n"
        "</section>"
    )


def _category(
    category_id: str,
    title: str,
    body: str,
    *,
    open_by_default: bool = False,
) -> str:
    open_attribute = " open" if open_by_default else ""
    return (
        f'<details id="{category_id}" class="report-category" '
        f'name="norad-report-categories"{open_attribute}>\n'
        f"<summary>{_escape(title)}</summary>\n"
        f'<div class="report-category-body">\n{body}\n</div>\n'
        "</details>"
    )


def _table(
    *,
    table_id: str,
    caption: str,
    header: Sequence[str],
    rows: Iterable[Sequence[Any]],
    row_headers: bool = False,
) -> str:
    escaped_id = _escape(table_id)
    escaped_caption = _escape(caption)
    wide_class = " norad-table-wrap-wide" if len(header) > 6 else ""
    wide_attributes = (
        f' tabindex="0" role="region" aria-label="{escaped_caption}"'
        if wide_class
        else ""
    )
    head = "".join(f'<th scope="col">{_escape(column)}</th>' for column in header)
    rendered_rows = []
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            if row_headers and index == 0:
                cells.append(f'<th scope="row">{_escape(value)}</th>')
            else:
                cells.append(f"<td>{_escape(value)}</td>")
        rendered_rows.append("<tr>" + "".join(cells) + "</tr>")
    if not rendered_rows:
        rendered_rows.append(
            f'<tr><td colspan="{len(header)}">No rows are available.</td></tr>'
        )
    return (
        f'<div class="norad-table-wrap{wide_class}"{wide_attributes}>\n'
        f'<table class="norad-table" id="{escaped_id}">\n'
        f"<caption>{escaped_caption}</caption>\n"
        f"<thead><tr>{head}</tr></thead>\n"
        f"<tbody>{''.join(rendered_rows)}</tbody>\n"
        "</table>\n"
        "</div>"
    )


def _key_value_table(
    *,
    table_id: str,
    caption: str,
    rows: Iterable[tuple[str, Any]],
) -> str:
    return _table(
        table_id=table_id,
        caption=caption,
        header=("Field", "Value"),
        rows=rows,
        row_headers=True,
    )


def _render_approved_table(table: ApprovedTable) -> str:
    controlled_candidate_titles = {
        "candidate_selection": ("CMH-ranked candidates: approved selection summary"),
        "candidate_adjudication": (
            "CMH-ranked candidates: approved adjudication summary"
        ),
    }
    content = _table(
        table_id=f"approved-table-{table.table_id}",
        caption=controlled_candidate_titles.get(table.role, table.title),
        header=table.header,
        rows=table.display_rows,
    )
    if table.truncated:
        detail = (
            f"Displayed {table.displayed_row_count} of {table.row_count} rows. "
            f"Full table: {table.path}. SHA-256: {table.sha256}."
            f" Approved by {table.approved_by} under "
            f"{table.approval_policy_version} at {table.approved_at}."
        )
        content += f'<p class="notice">{_escape(detail)}</p>'
    else:
        detail = (
            f"Explicit approved table: {table.path}. SHA-256: {table.sha256}. "
            f"Rows: {table.row_count}. Approved by {table.approved_by} under "
            f"{table.approval_policy_version} at {table.approved_at}."
        )
        content += f'<p class="provenance-note">{_escape(detail)}</p>'
    return content


def _tables_for_roles(
    tables_by_role: Mapping[str, Sequence[ApprovedTable]],
    roles: Sequence[str],
    empty_message: str,
) -> str:
    selected = [table for role in roles for table in tables_by_role.get(role, ())]
    if not selected:
        return _empty(empty_message)
    return "\n".join(_render_approved_table(table) for table in selected)


def _render_json_block(title: str, value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    return (
        f"<h3>{_escape(title)}</h3>\n"
        f'<pre aria-label="{_escape(title)}">{_escape(payload)}</pre>'
    )
