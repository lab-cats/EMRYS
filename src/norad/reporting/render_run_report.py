#!/usr/bin/env python3
"""Render one canonical NORAD run summary as a static report bundle.

The command is explicit-input-only and dry-run-first. It validates one
``norad.run_summary`` v1.1 document and may read only the TSVs explicitly
authorized by that document's ``approved_report_tables`` records. It never
discovers pipeline outputs, executes analysis code, installs software, or
promotes computational or scientific status.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import html
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, NoReturn

import yaml
_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[2])
if sys.path[:1] != [src_root]:
    if src_root in sys.path:
        sys.path.remove(src_root)
    sys.path.insert(0, src_root)

from norad.contracts.artifacts import validate_artifact_contracts as contracts
from norad.reporting import _files

PRODUCER = "render_run_report"
PRODUCER_VERSION = "1.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "1.1.0"
QUARTO_VERSION = "1.9.38"
QMD_TEMPLATE = _MODULE_PATH.parent / "templates" / "run_report.qmd"
CSS_TEMPLATE = _MODULE_PATH.parent / "styles" / "run_report.css"
BODY_MARKER = "{{NORAD_REPORT_BODY}}"
CSS_MARKER = "{{NORAD_REPORT_CSS}}"
CANDIDATE_TERMINOLOGY = "CMH-ranked candidates"
COMPUTATIONAL_STATUS_FIELDS: tuple[tuple[str, str], ...] = (
    ("Implementation", "implementation_status"),
    ("Local testing", "local_test_status"),
    ("Runtime validation", "runtime_validation_status"),
    ("Cluster dry-run", "cluster_dry_run_status"),
    ("Cluster proof", "cluster_proof_status"),
)
SCIENCE_BANNERS = {
    "evidence_incomplete": (
        "SCIENTIFIC REVIEW INCOMPLETE — NO BIOLOGICAL INTERPRETATION."
    ),
    "science_review_complete_exploratory": (
        "EXPLORATORY / PROVISIONAL — NOT BIOLOGICALLY VALIDATED."
    ),
}
KNOWN_REPORT_ROLES = {
    "orientation_locus_audit",
    "annotation_audit",
    "qc_funnel",
    "replicate_effects",
    "sensitivity_matrix",
    "leave_one_pair_out",
    "candidate_selection",
    "candidate_adjudication",
    "decisions",
    "evidence_index",
    "limitations",
}
ACTIVE_RESOURCE_ATTRIBUTES = {
    ("script", "src"),
    ("link", "href"),
    ("img", "src"),
    ("img", "srcset"),
    ("iframe", "src"),
    ("object", "data"),
    ("embed", "src"),
    ("source", "src"),
    ("source", "srcset"),
    ("video", "src"),
    ("video", "poster"),
    ("audio", "src"),
    ("input", "src"),
    ("track", "src"),
    ("image", "href"),
    ("image", "xlink:href"),
    ("use", "href"),
    ("use", "xlink:href"),
}
REMOTE_URI_RE = re.compile(r"^\s*(?:https?:)?//", re.IGNORECASE)
CSS_RESOURCE_RE = re.compile(
    r"url\s*\(\s*(['\"]?)(.*?)\1\s*\)"
    r"|@import\s+(?:url\s*\(\s*)?(['\"])(.*?)\3",
    re.IGNORECASE,
)
EXECUTABLE_QMD_RE = re.compile(r"^\s*```\s*\{", re.MULTILINE)
SAFE_STATUS_RE = re.compile(r"[^a-z0-9]+")
REPORT_SECTION_IDS = {
    "run-identity-section",
    "status-section",
    "limitations-section",
    "scope-matrix-section",
    "qc-orientation-section",
    "replicate-sensitivity-section",
    "candidate-section",
    "decisions-section",
    "rerun-section",
    "evidence-methods-section",
}
EXPECTED_QMD_FRONTMATTER = {
    "execute": {"enabled": False},
    "format": {
        "html": {
            "anchor-sections": False,
            "embed-resources": True,
            "html-math-method": "plain",
            "minimal": True,
            "theme": "none",
        }
    },
    "lang": "en",
    "pagetitle": "NORAD consolidated run report",
}
EXPECTED_QMD_BODY = (
    "\n\n<!-- This tracked view is static by contract. It contains no executable "
    "cells. -->\n"
    f"{CSS_MARKER}\n"
    f"{BODY_MARKER}\n"
)
SAFE_RENDER_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"


class ReportRenderError(RuntimeError):
    """Raised when a run report cannot be validated or safely published."""


FileSnapshot = _files.FileSnapshot


@dataclass(frozen=True)
class ApprovedTable:
    table_id: str
    artifact_id: str
    role: str
    title: str
    path: Path
    sha256: str
    row_count: int
    display_row_limit: int | None
    approval_policy_version: str
    approved_by: str
    approved_at: str
    header: tuple[str, ...]
    display_rows: tuple[tuple[str, ...], ...]
    snapshot: FileSnapshot

    @property
    def displayed_row_count(self) -> int:
        return len(self.display_rows)

    @property
    def truncated(self) -> bool:
        return self.displayed_row_count < self.row_count


@dataclass(frozen=True)
class LockOwnership:
    path: Path
    token: str
    device: int
    inode: int


@dataclass(frozen=True)
class RenderContext:
    run_summary_path: Path
    run_summary_snapshot: FileSnapshot
    summary: dict[str, Any]
    tables: tuple[ApprovedTable, ...]
    template_snapshot: FileSnapshot
    css_snapshot: FileSnapshot
    quarto_path: Path
    quarto_snapshot: FileSnapshot
    output_root: Path
    output_dir: Path
    output_html: Path
    lock_path: Path
    previous_output_snapshot: FileSnapshot | None
    render_metadata: Mapping[str, str]
    qmd_bytes: bytes
    execute: bool

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return (
            self.run_summary_snapshot,
            self.template_snapshot,
            self.css_snapshot,
            self.quarto_snapshot,
            *(table.snapshot for table in self.tables),
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


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render one validated NORAD run-summary JSON as a static, "
            "self-contained HTML report. Dry-run is the default."
        )
    )
    parser.add_argument(
        "--run-summary",
        required=True,
        type=Path,
        help="Explicit canonical <run-id>.run_summary.json input.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    parser.add_argument(
        "--quarto-bin",
        required=True,
        type=Path,
        help=f"Explicit Quarto {QUARTO_VERSION} executable.",
    )
    parser.add_argument(
        "--formats",
        choices=("html", "pdf", "all"),
        default="all",
        help=(
            "Presentation format. The default all publishes HTML and PDF; "
            "every mode also publishes a deterministic summary TSV and "
            "receipt."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the validated HTML report. Omit for dry-run.",
    )
    return parser.parse_args(argv)


def _fail(message: str) -> None:
    raise ReportRenderError(message)


def _explicit_path(path: Path, label: str) -> Path:
    try:
        contracts.validate_resolved_path(str(path), label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    return path.absolute()


def _reject_symlink_components(path: Path, label: str) -> None:
    _files.reject_symlink_components(path, label, _fail)


def _snapshot_regular(
    path: Path,
    label: str,
    *,
    executable: bool = False,
) -> FileSnapshot:
    path = _explicit_path(path, label)
    _reject_symlink_components(path, label)
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                _fail(f"{label} must be a regular non-symlink file: {path}")
            if executable and not before.st_mode & stat.S_IXUSR:
                _fail(f"{label} is not executable: {path}")
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except ReportRenderError:
        raise
    except OSError as exc:
        _fail(f"Could not inspect and hash {label} {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    before_identity = _files.stat_identity(before)
    after_identity = _files.stat_identity(after)
    current_identity = _files.stat_identity(current)
    if (
        before_identity != after_identity
        or before_identity != current_identity
        or stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
    ):
        _fail(f"{label} changed while its snapshot was captured: {path}")
    return FileSnapshot(
        path=path,
        sha256=digest.hexdigest(),
        device=before.st_dev,
        inode=before.st_ino,
        size_bytes=before.st_size,
        mtime_ns=before.st_mtime_ns,
        ctime_ns=before.st_ctime_ns,
    )


def _assert_snapshot(snapshot: FileSnapshot, label: str) -> None:
    current = _snapshot_regular(
        snapshot.path,
        label,
        executable=(label == "Quarto executable"),
    )
    if current != snapshot:
        _fail(f"{label} changed during report rendering: {snapshot.path}")


def _load_run_summary(path: Path) -> dict[str, Any]:
    try:
        document = contracts.load_json_object(path, "run-summary document")
        errors = contracts.schema_errors("run-summary", document)
        if errors:
            detail = "\n".join(
                f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
                for error in errors
            )
            _fail(f"run-summary document failed validation: {path}\n{detail}")
        contracts.validate_run_summary_semantics(document)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    if document["schema_version"] != RUN_SUMMARY_SCHEMA_VERSION:
        _fail(f"Unsupported run-summary schema version: {document['schema_version']!r}")
    if document["candidate_terminology"] != CANDIDATE_TERMINOLOGY:
        _fail(
            "Run summary does not use the required candidate terminology: "
            f"{CANDIDATE_TERMINOLOGY}"
        )
    if document["science_status"] not in SCIENCE_BANNERS:
        _fail(
            "Run summary uses an unauthorized scientific state: "
            f"{document['science_status']!r}"
        )
    return document


def _resolve_contract_file(value: str, label: str) -> Path:
    try:
        contracts.validate_resolved_path(value, label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    declared = Path(value)
    lexical = (
        declared if declared.is_absolute() else contracts.REPO_ROOT / declared
    ).absolute()
    _reject_symlink_components(lexical, label)
    resolved = contracts.resolve_contract_path(value)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved


def _read_approved_table(record: Mapping[str, Any]) -> ApprovedTable:
    table_id = record["table_id"]
    path = _resolve_contract_file(
        record["path"],
        f"approved report table {table_id!r}",
    )
    snapshot = _snapshot_regular(
        path,
        f"approved report table {table_id!r}",
    )
    if snapshot.sha256 != record["sha256"]:
        _fail(
            f"Approved report table {table_id!r} SHA-256 mismatch: observed "
            f"{snapshot.sha256}; expected {record['sha256']}"
        )

    display_limit = record["display_row_limit"]
    header: tuple[str, ...] | None = None
    displayed: list[tuple[str, ...]] = []
    row_count = 0
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            try:
                raw_header = next(reader)
            except StopIteration:
                _fail(f"Approved report table {table_id!r} is empty: {path}")
            if not raw_header or any(not column for column in raw_header):
                _fail(f"Approved report table {table_id!r} has a blank header column")
            if len(raw_header) != len(set(raw_header)):
                _fail(
                    f"Approved report table {table_id!r} has duplicate header columns"
                )
            header = tuple(raw_header)
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    _fail(
                        f"Approved report table {table_id!r} row {row_number} "
                        f"has {len(row)} fields; expected {len(header)}"
                    )
                row_count += 1
                if display_limit is None or len(displayed) < display_limit:
                    displayed.append(tuple(row))
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not parse approved report table {table_id!r}: {exc}")

    if row_count != record["row_count"]:
        _fail(
            f"Approved report table {table_id!r} row-count mismatch: observed "
            f"{row_count}; expected {record['row_count']}"
        )
    _assert_snapshot(snapshot, f"approved report table {table_id!r}")
    assert header is not None
    return ApprovedTable(
        table_id=table_id,
        artifact_id=record["artifact_id"],
        role=record["role"],
        title=record["title"],
        path=path,
        sha256=snapshot.sha256,
        row_count=row_count,
        display_row_limit=display_limit,
        approval_policy_version=record["approval"]["policy_version"],
        approved_by=record["approval"]["approved_by"],
        approved_at=record["approval"]["approved_at"],
        header=header,
        display_rows=tuple(displayed),
        snapshot=snapshot,
    )


def _sanitized_tool_environment() -> dict[str, str]:
    """Return the small ambient environment allowed for pinned report tools."""

    return {
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "PATH": SAFE_RENDER_PATH,
        "TMPDIR": "/tmp",
        "TZ": "UTC",
    }


def _quarto_version(path: Path) -> str:
    try:
        result = subprocess.run(
            [str(path), "--version"],
            env=_sanitized_tool_environment(),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _fail(f"Could not execute {path} --version: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        _fail(f"Quarto version check failed: {detail}")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if lines != [QUARTO_VERSION]:
        _fail(
            f"Quarto reported {result.stdout.strip()!r}; expected exactly "
            f"{QUARTO_VERSION!r}"
        )
    return lines[0]


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


def _artifact_overview(summary: Mapping[str, Any]) -> str:
    rollup = summary["computational_rollup"]
    categories = (
        ("complete", rollup["complete_artifact_count"], "#287a5d"),
        ("missing", rollup["missing_artifact_count"], "#64748b"),
        ("incomplete", rollup["incomplete_artifact_count"], "#b7791f"),
        ("failed", rollup["failed_artifact_count"], "#b42318"),
        (
            "externally unavailable",
            rollup["externally_unavailable_artifact_count"],
            "#6b5ca5",
        ),
    )
    total = rollup["expected_artifact_count"]
    width = 720
    height = 82
    cursor = 0.0
    rectangles: list[str] = []
    for name, count, color in categories:
        segment = width * count / total if total else 0
        if count:
            rectangles.append(
                f'<rect x="{cursor:.3f}" y="18" width="{segment:.3f}" '
                f'height="30" fill="{color}"><title>'
                f"{_escape(name)}: {_escape(count)}</title></rect>"
            )
        cursor += segment
    accessible = ", ".join(f"{name}: {count}" for name, count, _ in categories)
    legend = "".join(
        f'<li class="legend-{_escape(name.replace(" ", "-"))}">'
        f"{_escape(name.title())}: {_escape(count)}</li>"
        for name, count, _ in categories
    )
    return (
        '<figure class="artifact-overview">\n'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="artifact-overview-title '
        'artifact-overview-description">\n'
        '<title id="artifact-overview-title">Expected artifact state overview'
        "</title>\n"
        '<desc id="artifact-overview-description">'
        f"{_escape(accessible)}</desc>\n"
        + "".join(rectangles)
        + f'<text x="0" y="70" font-size="14" fill="#17202a">'
        f"Expected artifacts: {_escape(total)}</text>\n"
        "</svg>\n"
        "<figcaption>Artifact availability is copied from the canonical run "
        "summary. This visualization is not validation evidence.</figcaption>\n"
        "</figure>\n"
        f'<ul class="artifact-legend" aria-label="Artifact state legend">'
        f"{legend}</ul>"
    )


def _failed_scope_summary(summary: Mapping[str, Any]) -> str:
    failed = [
        (
            scope_record["scope"]["step_id"],
            scope_record["scope"]["scope_type"],
            scope_record["scope"]["scope_id"],
        )
        for scope_record in summary["expected_scopes"]
        if scope_record["aggregate_state"] == "failed"
    ]
    if not failed:
        return '<p class="provenance-note">Failed expected scopes: none.</p>'
    items = "".join(
        f"<li>{_escape(step_id)} {_escape(scope_type)} {_escape(scope_id)} failed</li>"
        for step_id, scope_type, scope_id in failed
    )
    return (
        '<div class="notice"><p><strong>Failed expected scopes</strong></p>'
        f"<ul>{items}</ul></div>"
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


def _render_run_identity(summary: Mapping[str, Any]) -> str:
    contract = summary["run_contract"]
    rows = (
        ("Run ID", summary["run_id"]),
        ("Run-summary schema", summary["schema_version"]),
        ("Summary state", summary["summary_state"]),
        ("Generated at", summary["generated_at"]),
        ("Run-contract SHA-256", contract["run_contract_sha256"]),
        ("Sample-manifest SHA-256", contract["sample_manifest_sha256"]),
        ("Reference-contract SHA-256", contract["reference_contract_sha256"]),
        ("Partition-manifest SHA-256", contract["partition_manifest_sha256"]),
        ("Primary analysis ID", contract["primary_analysis_id"]),
        (
            "Primary-analysis-policy SHA-256",
            contract["primary_analysis_policy_sha256"],
        ),
        ("Inventory path", summary["inventory"]["path"]),
        ("Inventory SHA-256", summary["inventory"]["sha256"]),
        ("Artifact receipt path", summary["artifact_receipt"]["path"]),
        ("Artifact receipt SHA-256", summary["artifact_receipt"]["sha256"]),
    )
    return _key_value_table(
        table_id="run-identity",
        caption="Immutable run identity and explicit source records",
        rows=rows,
    )


def _render_report_provenance(metadata: Mapping[str, str]) -> str:
    rows = (
        ("Run-summary input", metadata["run_summary_path"]),
        ("Run-summary input SHA-256", metadata["run_summary_sha256"]),
        (
            "Renderer",
            f"{metadata['renderer']} {metadata['renderer_version']}",
        ),
        ("Quarto executable", metadata["quarto_path"]),
        ("Quarto version", metadata["quarto_version"]),
        ("Quarto executable SHA-256", metadata["quarto_sha256"]),
        ("QMD template", metadata["qmd_template_path"]),
        ("QMD template SHA-256", metadata["qmd_template_sha256"]),
        ("CSS template", metadata["css_template_path"]),
        ("CSS template SHA-256", metadata["css_template_sha256"]),
    )
    return _key_value_table(
        table_id="report-renderer-provenance",
        caption="Static report renderer provenance",
        rows=rows,
    )


def _render_status_panels(summary: Mapping[str, Any]) -> str:
    rollup = summary["computational_rollup"]
    computational_rows = tuple(
        (label, rollup[field]) for label, field in COMPUTATIONAL_STATUS_FIELDS
    )
    review = summary["scientific_review"]
    scientific_rows: list[tuple[str, Any]] = [
        ("Overall science status", summary["science_status"]),
        ("Review record state", review["record_state"]),
    ]
    record = review["record"]
    if record is not None:
        state = record["scientific_state"]
        scientific_rows.extend(
            (
                ("Orientation status", state["orientation_status"]),
                ("Orientation policy", state["orientation_policy"]),
                (
                    "Orientation policy version",
                    state["orientation_policy_version"],
                ),
            )
        )
    else:
        scientific_rows.extend(
            (
                ("Orientation status", "not available"),
                ("Orientation policy", "not available"),
            )
        )
    computational = _key_value_table(
        table_id="computational-status",
        caption="Computational status dimensions",
        rows=computational_rows,
    )
    scientific = _key_value_table(
        table_id="scientific-status",
        caption="Scientific review status dimensions",
        rows=scientific_rows,
    )
    return (
        '<div class="panel-grid">\n'
        '<div class="status-panel"><h3>Computational status</h3>'
        f"{computational}</div>\n"
        '<div class="status-panel"><h3>Scientific status</h3>'
        f"{scientific}</div>\n"
        "</div>\n" + _artifact_overview(summary) + _failed_scope_summary(summary)
    )


def _render_scope_matrix(summary: Mapping[str, Any]) -> str:
    rows = []
    for scope_record in summary["expected_scopes"]:
        scope = scope_record["scope"]
        rows.append(
            (
                scope["step_id"],
                scope["scope_type"],
                scope["scope_id"],
                scope_record["aggregate_state"],
                *(scope_record[field] for _, field in COMPUTATIONAL_STATUS_FIELDS),
                ", ".join(scope_record["artifact_ids"]),
            )
        )
    return _table(
        table_id="expected-scope-matrix",
        caption=(
            "Every expected pipeline and review scope, including explicit "
            "missing, incomplete, failed, or externally unavailable evidence"
        ),
        header=(
            "Step",
            "Scope type",
            "Scope ID",
            "Evidence state",
            "Implementation",
            "Local test",
            "Runtime",
            "Cluster dry-run",
            "Cluster proof",
            "Artifact IDs",
        ),
        rows=rows,
    )


def _render_qc_metrics(summary: Mapping[str, Any]) -> str:
    promoted_ids = {metric["metric_id"] for metric in summary["qc_metrics"]}
    rows = [
        (
            artifact["artifact_id"],
            metric["metric_id"],
            metric["name"],
            metric["value"],
            metric["unit"],
            metric["status"],
            metric["metric_id"] in promoted_ids,
        )
        for artifact in summary["artifacts"]
        for metric in artifact["metrics"]
    ]
    if not rows:
        return _empty(
            "No artifact-level QC metrics are present in the canonical run summary."
        )
    return _table(
        table_id="qc-metrics",
        caption=(
            "Canonical artifact-level QC metrics in stable artifact order; "
            "globally promoted indicates a unique top-level metric ID"
        ),
        header=(
            "Artifact",
            "Metric ID",
            "Name",
            "Value",
            "Unit",
            "Status",
            "Globally promoted",
        ),
        rows=rows,
    )


def _scientific_record(summary: Mapping[str, Any]) -> Mapping[str, Any] | None:
    record = summary["scientific_review"]["record"]
    return record if isinstance(record, Mapping) else None


def _render_evidence_categories(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "No normalized scientific-review record is present. Orientation, "
            "annotation, funnel, replicate, sensitivity, and adjudication "
            "evidence remain unavailable."
        )
    rows = []
    for category, value in record["evidence_categories"].items():
        rows.append(
            (
                category,
                value["status"],
                ", ".join(value["evidence_ids"]) or "None declared",
                value["not_applicable_reason"],
            )
        )
    return _table(
        table_id="science-evidence-categories",
        caption="Scientific evidence-category completeness",
        header=("Category", "Status", "Evidence IDs", "Not-applicable reason"),
        rows=rows,
    )


def _render_limitations(summary: Mapping[str, Any]) -> str:
    limitations = summary["limitations"]
    if not limitations:
        return _empty("No limitations are recorded in the canonical run summary.")
    return _table(
        table_id="limitations",
        caption="Recorded limitations and their interpretation impact",
        header=(
            "Limitation",
            "Status",
            "Category",
            "Severity",
            "Description",
            "Impact",
            "Mitigation",
            "Owner",
            "Review date",
            "Evidence IDs",
        ),
        rows=(
            (
                item["limitation_id"],
                item["status"],
                item.get("category"),
                item.get("severity"),
                item["description"],
                item["impact"],
                item.get("mitigation"),
                item.get("owner"),
                item.get("review_date"),
                ", ".join(item["evidence_ids"]) or "None declared",
            )
            for item in limitations
        ),
    )


def _render_decisions(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "Background, matched-DNA, orthogonal-evidence, annotation, "
            "threshold, and adjudication decisions are unavailable because "
            "no scientific-review record is present."
        )
    rows = []
    for dimension, decision in record["decisions"].items():
        rows.append(
            (
                dimension,
                decision["status"],
                decision["value"],
                decision["detail"],
                decision["reviewer"],
                decision["decision_date"],
                ", ".join(decision["evidence_ids"]) or "None declared",
                decision.get("rerun_required"),
                decision["rerun_scope"],
            )
        )
    return _table(
        table_id="science-decisions",
        caption="Explicit scientific-review decision dimensions",
        header=(
            "Dimension",
            "Status",
            "Value",
            "Detail",
            "Reviewer",
            "Decision date",
            "Evidence IDs",
            "Rerun required",
            "Rerun scope",
        ),
        rows=rows,
    )


def _render_rerun_implications(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "No review decisions are available from which to report explicit "
            "rerun implications. This report does not infer them."
        )
    rows = [
        (
            dimension,
            decision["status"],
            decision.get("rerun_required"),
            decision["rerun_scope"],
            decision["detail"],
        )
        for dimension, decision in record["decisions"].items()
    ]
    return _table(
        table_id="rerun-implications",
        caption=(
            "Recorded rerun scopes copied from review decisions; no rerun is "
            "scheduled or executed by this report"
        ),
        header=(
            "Decision dimension",
            "Status",
            "Rerun required",
            "Rerun scope",
            "Detail",
        ),
        rows=rows,
    )


def _render_evidence_index(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None or not record["evidence_records"]:
        return _empty(
            "No scientific evidence index is present in the canonical run summary."
        )
    return _table(
        table_id="science-evidence-index",
        caption="Explicit scientific evidence records",
        header=(
            "Evidence ID",
            "Category",
            "Analysis ID",
            "Status",
            "Path",
            "SHA-256",
            "Reviewer",
            "Owner",
            "Evidence date",
            "Policy version",
        ),
        rows=(
            (
                evidence["evidence_id"],
                evidence["category"],
                evidence["analysis_id"],
                evidence["status"],
                (
                    evidence["source"]["path"]
                    if evidence["source"] is not None
                    else "Not available"
                ),
                (
                    evidence["source"]["sha256"]
                    if evidence["source"] is not None
                    else "Not available"
                ),
                evidence["reviewer"],
                evidence["owner"],
                evidence["evidence_date"],
                evidence["policy_version"],
            )
            for evidence in record["evidence_records"]
        ),
    )


def _render_input_artifacts(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty("No scientific-review input-artifact list is present.")
    return _table(
        table_id="science-input-artifacts",
        caption="Scientific-review input artifacts",
        header=("Role", "Artifact ID", "Path", "SHA-256", "Rows"),
        rows=(
            (
                item["role"],
                item["artifact_id"],
                item["path"],
                item["sha256"],
                item["row_count"],
            )
            for item in record["input_artifacts"]
        ),
    )


def _render_science_methods(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "Scientific-review metadata, policies, selection rules, and "
            "computational evidence are unavailable because no normalized "
            "review record is present."
        )
    metadata = _key_value_table(
        table_id="science-review-metadata",
        caption="Scientific-review metadata",
        rows=record["review_metadata"].items(),
    )
    policies = _key_value_table(
        table_id="science-policy-versions",
        caption="Scientific-review policy versions",
        rows=record["policy_versions"].items(),
    )
    rules = _key_value_table(
        table_id="science-selection-rules",
        caption="Preregistered selection and sensitivity rules",
        rows=record["selection_rules"].items(),
    )
    computational = record["computational_status"]
    status_rows = tuple(
        (label, computational[field])
        for label, field in COMPUTATIONAL_STATUS_FIELDS
    )
    status_table = _key_value_table(
        table_id="science-computational-status",
        caption="Computational status declared by the scientific review",
        rows=status_rows,
    )
    evidence = computational["evidence"]
    evidence_table = (
        _table(
            table_id="science-computational-evidence",
            caption="Computational evidence references declared by the review",
            header=("Evidence ID", "Role", "Path", "SHA-256"),
            rows=(
                (
                    item["evidence_id"],
                    item["role"],
                    item["path"],
                    item["sha256"],
                )
                for item in evidence
            ),
        )
        if evidence
        else _empty(
            "The scientific-review record declares no computational evidence "
            "references."
        )
    )
    return "\n".join((metadata, policies, rules, status_table, evidence_table))


def _render_attempt_lineage(summary: Mapping[str, Any]) -> str:
    attempts = summary["attempts"]
    if not attempts:
        attempt_table = _empty(
            "No execution-attempt lineage is recorded for this synthetic or "
            "not-attempted run."
        )
    else:
        attempt_table = _table(
            table_id="run-attempt-lineage",
            caption="Immutable run execution-attempt lineage",
            header=(
                "Attempt ID",
                "State",
                "Started",
                "Finished",
                "Exit code",
                "Supersedes",
                "Evidence count",
                "Warnings",
                "Errors",
            ),
            rows=(
                (
                    attempt["attempt_id"],
                    attempt["state"],
                    attempt["started_at"],
                    attempt["finished_at"],
                    attempt["exit_code"],
                    attempt["supersedes_attempt_id"],
                    len(attempt["evidence"]),
                    len(attempt["warnings"]),
                    len(attempt["errors"]),
                )
                for attempt in attempts
            ),
        )
    selections = _table(
        table_id="artifact-attempt-selections",
        caption="Selected and superseded attempt references by artifact",
        header=(
            "Artifact ID",
            "Selected attempt",
            "Attempt provenance",
            "Artifact attempt IDs",
        ),
        rows=(
            (
                artifact["artifact_id"],
                artifact["selected_attempt_id"],
                artifact["attempt_provenance_status"],
                ", ".join(attempt["attempt_id"] for attempt in artifact["attempts"])
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )
    superseded = ", ".join(summary["superseded_attempt_ids"]) or "None"
    return (
        attempt_table
        + "\n"
        + selections
        + f'<p class="provenance-note">Superseded run attempt IDs: '
        f"{_escape(superseded)}.</p>"
    )


def _render_artifact_appendix(summary: Mapping[str, Any]) -> str:
    return _table(
        table_id="artifact-evidence-index",
        caption="Expected artifact evidence and selected source records",
        header=(
            "Artifact ID",
            "Step",
            "Scope type",
            "Scope ID",
            "Required",
            "Availability",
            "Completion",
            "State reason",
            "Source path",
            "Source SHA-256",
            "Warning detail",
            "Error detail",
        ),
        rows=(
            (
                artifact["artifact_id"],
                artifact["scope"]["step_id"],
                artifact["scope"]["scope_type"],
                artifact["scope"]["scope_id"],
                artifact["expectation"]["required"],
                artifact["availability_status"],
                artifact["completion_status"],
                artifact["state_reason"],
                (
                    artifact["source"]["path"]
                    if artifact["source"] is not None
                    else "Not available"
                ),
                (
                    artifact["source"]["sha256"]
                    if artifact["source"] is not None
                    else "Not available"
                ),
                "; ".join(
                    f"{issue['code']}: {issue['message']}"
                    for issue in artifact["warnings"]
                )
                or "None",
                "; ".join(
                    f"{issue['code']}: {issue['message']}"
                    for issue in artifact["errors"]
                )
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )


def _render_tools(summary: Mapping[str, Any]) -> str:
    if not summary["tools"]:
        return _empty("No aggregate software records are declared.")
    return _table(
        table_id="software-provenance",
        caption="Aggregate software provenance",
        header=("Tool", "Version", "Role", "Path", "SHA-256"),
        rows=(
            (
                tool["name"],
                tool["version"],
                tool["role"],
                tool["path"],
                tool["sha256"],
            )
            for tool in summary["tools"]
        ),
    )


def _render_issues(summary: Mapping[str, Any]) -> str:
    rows = [
        (
            level[:-1],
            issue["code"],
            issue["message"],
            ", ".join(issue["related_artifact_ids"]) or "None declared",
            ", ".join(
                reference["evidence_id"] for reference in issue["evidence"]
            )
            or "None declared",
        )
        for level in ("warnings", "errors")
        for issue in summary[level]
    ]
    if not rows:
        return _empty("No aggregate run-summary warnings or errors are recorded.")
    return _table(
        table_id="run-summary-issues",
        caption="Aggregate warnings and errors",
        header=("Level", "Code", "Message", "Artifact IDs", "Evidence IDs"),
        rows=rows,
    )


def _render_table_inventory(tables: Sequence[ApprovedTable]) -> str:
    if not tables:
        return _empty(
            "No full report tables were explicitly approved. The renderer did "
            "not discover or open any native pipeline output."
        )
    return _table(
        table_id="approved-table-inventory",
        caption="Explicit report-table approvals and display policy",
        header=(
            "Table ID",
            "Role",
            "Artifact ID",
            "Path",
            "SHA-256",
            "Full rows",
            "Displayed rows",
            "Truncated",
            "Approval policy",
            "Approved by",
            "Approved at",
        ),
        rows=(
            (
                table.table_id,
                table.role,
                table.artifact_id,
                table.path,
                table.sha256,
                table.row_count,
                table.displayed_row_count,
                table.truncated,
                table.approval_policy_version,
                table.approved_by,
                table.approved_at,
            )
            for table in tables
        ),
    )


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


def build_report_body(
    summary: Mapping[str, Any],
    tables: Sequence[ApprovedTable],
    render_metadata: Mapping[str, str] | None = None,
) -> str:
    """Build deterministic escaped raw HTML for the static QMD view."""

    metadata = (
        dict(render_metadata)
        if render_metadata is not None
        else _fallback_render_metadata()
    )
    science_status = summary["science_status"]
    banner = SCIENCE_BANNERS[science_status]
    tables_by_role: dict[str, list[ApprovedTable]] = defaultdict(list)
    for table in tables:
        tables_by_role[table.role].append(table)

    overview = "\n".join(
        (
            _section(
                "status-section",
                "Computational and scientific status",
                _render_status_panels(summary),
            ),
            _section(
                "candidate-section",
                f"{CANDIDATE_TERMINOLOGY} and adjudication summaries",
                _tables_for_roles(
                    tables_by_role,
                    ("candidate_selection", "candidate_adjudication"),
                    (
                        "No candidate-selection or adjudication table was "
                        "explicitly approved. No candidate row is displayed "
                        "or inferred."
                    ),
                ),
            ),
            _section(
                "limitations-section",
                "Limitations and interpretation boundary",
                _render_limitations(summary)
                + "\n"
                + _tables_for_roles(
                    tables_by_role,
                    ("limitations",),
                    "No separate limitations table was explicitly approved.",
                ),
            ),
        )
    )
    qc_and_orientation = _section(
        "qc-orientation-section",
        "QC, orientation, annotation, and Step 07 to Step 09 funnel",
        _render_qc_metrics(summary)
        + "\n"
        + _render_evidence_categories(summary)
        + "\n"
        + _tables_for_roles(
            tables_by_role,
            (
                "orientation_locus_audit",
                "annotation_audit",
                "qc_funnel",
            ),
            (
                "No orientation-locus, annotation-audit, or QC-funnel table "
                "was explicitly approved. Statuses remain visible above; row "
                "content was not discovered."
            ),
        ),
    )
    replicates_and_sensitivity = _section(
        "replicate-sensitivity-section",
        "Replicate, sensitivity, and leave-one-pair-out summaries",
        _tables_for_roles(
            tables_by_role,
            (
                "replicate_effects",
                "sensitivity_matrix",
                "leave_one_pair_out",
            ),
            (
                "No replicate-effect, sensitivity, or leave-one-pair-out table "
                "was explicitly approved."
            ),
        ),
    )
    review_decisions = "\n".join(
        (
            _section(
                "decisions-section",
                ("Background, matched-DNA, orthogonal-evidence, and review decisions"),
                _render_decisions(summary)
                + "\n"
                + _tables_for_roles(
                    tables_by_role,
                    ("decisions",),
                    "No separate decision table was explicitly approved.",
                ),
            ),
            _section(
                "rerun-section",
                "Rerun implications",
                _render_rerun_implications(summary),
            ),
        )
    )
    evidence_and_provenance = "\n".join(
        (
            _section(
                "run-identity-section",
                "Run identity, inputs, hashes, and provenance",
                _render_run_identity(summary),
            ),
            _section(
                "scope-matrix-section",
                "Expected-step and missing-evidence matrix",
                _render_scope_matrix(summary),
            ),
            _section(
                "evidence-methods-section",
                "Evidence index and methods appendix",
                _render_evidence_index(summary)
                + "\n"
                + _tables_for_roles(
                    tables_by_role,
                    ("evidence_index",),
                    "No separate evidence-index table was explicitly approved.",
                )
                + "\n"
                + _render_input_artifacts(summary)
                + "\n"
                + _render_science_methods(summary)
                + "\n"
                + _render_attempt_lineage(summary)
                + "\n"
                + _render_artifact_appendix(summary)
                + "\n"
                + _render_table_inventory(tables)
                + "\n"
                + _render_tools(summary)
                + "\n"
                + _render_issues(summary)
                + "\n"
                + _render_json_block("Run-summary parameters", summary["parameters"])
                + "\n"
                + _render_json_block("Run-summary provenance", summary["provenance"])
                + "\n"
                + _render_report_provenance(metadata),
            ),
        )
    )
    unknown_tables = [table for table in tables if table.role not in KNOWN_REPORT_ROLES]
    if unknown_tables:
        evidence_and_provenance += "\n" + _section(
            "other-approved-tables-section",
            "Other explicitly approved report tables",
            "\n".join(_render_approved_table(table) for table in unknown_tables),
        )

    parts = [
        (
            '<main id="norad-report" tabindex="-1" '
            f'data-run-id="{_escape(summary["run_id"])}" '
            f'data-run-summary-sha256="{_escape(metadata["run_summary_sha256"])}" '
            f'data-renderer-version="{_escape(metadata["renderer_version"])}" '
            f'data-quarto-version="{_escape(metadata["quarto_version"])}" '
            f'data-qmd-sha256="{_escape(metadata["qmd_template_sha256"])}" '
            f'data-css-sha256="{_escape(metadata["css_template_sha256"])}">\n'
            f'<h1 id="norad-report-title">NORAD consolidated run report: '
            f"{_escape(summary['run_id'])}</h1>"
        ),
        (
            f'<div class="state-banner state-{_escape(science_status.replace("_", "-"))}" '
            'role="status" aria-live="polite">'
            f"{_escape(banner)}</div>"
        ),
        (
            '<p class="report-disclaimer">This report is a read-only view of '
            "declared evidence. Report generation is not evidence of local, "
            "runtime, cluster, scientific, or biological validation. Candidate "
            f"rows are described only as {_escape(CANDIDATE_TERMINOLOGY)}.</p>"
        ),
        (
            '<div class="report-category-tabs" role="group" '
            'aria-label="Report categories">'
        ),
        _category(
            "overview-category",
            "Overview",
            overview,
            open_by_default=True,
        ),
        _category(
            "qc-category",
            "QC and orientation",
            qc_and_orientation,
        ),
        _category(
            "replicate-category",
            "Replicates and sensitivity",
            replicates_and_sensitivity,
        ),
        _category(
            "review-category",
            "Review decisions",
            review_decisions,
        ),
        _category(
            "evidence-category",
            "Evidence and provenance",
            evidence_and_provenance,
        ),
        "</div>",
        (
            '<p class="report-disclaimer">End of report. '
            f"{_escape(banner)} Report generation did not change any recorded "
            "status.</p>\n</main>"
        ),
    ]
    return "\n\n".join(parts) + "\n"


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


def _expected_html_identity(context: RenderContext) -> dict[str, str]:
    metadata = context.render_metadata
    return {
        "data-css-sha256": metadata["css_template_sha256"],
        "data-qmd-sha256": metadata["qmd_template_sha256"],
        "data-quarto-version": metadata["quarto_version"],
        "data-renderer-version": metadata["renderer_version"],
        "data-run-id": context.summary["run_id"],
        "data-run-summary-sha256": metadata["run_summary_sha256"],
    }


def prepare_context(arguments: argparse.Namespace) -> RenderContext:
    run_summary_path = _explicit_path(
        arguments.run_summary,
        "run-summary path",
    )
    run_summary_snapshot = _snapshot_regular(
        run_summary_path,
        "run-summary document",
    )
    summary = _load_run_summary(run_summary_path)
    _assert_snapshot(run_summary_snapshot, "run-summary document")
    run_id = summary["run_id"]
    expected_name = f"{run_id}.run_summary.json"
    if run_summary_path.name != expected_name or run_summary_path.parent.name != run_id:
        _fail(
            "Canonical run-summary input must use "
            f"<run-id>/{expected_name}; observed {run_summary_path}"
        )

    tables = tuple(
        _read_approved_table(record) for record in summary["approved_report_tables"]
    )
    template_snapshot = _snapshot_regular(
        QMD_TEMPLATE,
        "report QMD template",
    )
    css_snapshot = _snapshot_regular(
        CSS_TEMPLATE,
        "report CSS template",
    )
    quarto_path = _explicit_path(arguments.quarto_bin, "Quarto executable")
    quarto_snapshot = _snapshot_regular(
        quarto_path,
        "Quarto executable",
        executable=True,
    )
    _quarto_version(quarto_path)
    _assert_snapshot(quarto_snapshot, "Quarto executable")

    output_root = _explicit_path(arguments.output_root, "report output root")
    _reject_symlink_components(output_root, "report output root")
    output_dir = output_root / run_id
    output_html = output_dir / f"{run_id}.run_report.html"
    lock_path = output_dir / f".{run_id}.report-html.lock"
    for path, label in (
        (output_dir, "report output directory"),
        (output_html, "report HTML output"),
        (lock_path, "report lock"),
    ):
        _reject_symlink_components(path, label)

    if os.path.lexists(output_root):
        metadata = output_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output root must be a non-symlink directory when it "
                f"exists: {output_root}"
            )
    if os.path.lexists(output_dir):
        metadata = output_dir.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output directory must be a non-symlink directory when "
                f"it exists: {output_dir}"
            )
    previous_output_snapshot: FileSnapshot | None = None
    if os.path.lexists(output_html):
        metadata = output_html.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail(
                "Existing report output must be a regular non-symlink file: "
                f"{output_html}"
            )
        previous_output_snapshot = _snapshot_regular(
            output_html,
            "existing report output",
        )
        validate_rendered_html(
            output_html,
            expected_banner=None,
        )
        _assert_snapshot(
            previous_output_snapshot,
            "existing report output",
        )
    if os.path.lexists(lock_path):
        _fail(f"Report render lock already exists: {lock_path}")

    template_bytes = template_snapshot.path.read_bytes()
    css_bytes = css_snapshot.path.read_bytes()
    try:
        css_text = css_bytes.decode("utf-8")
    except UnicodeError as exc:
        _fail(f"Report CSS template is not UTF-8: {exc}")
    _validate_css_resources(css_text, "Report CSS template")
    render_metadata = {
        "css_template_path": str(css_snapshot.path),
        "css_template_sha256": css_snapshot.sha256,
        "qmd_template_path": str(template_snapshot.path),
        "qmd_template_sha256": template_snapshot.sha256,
        "quarto_path": str(quarto_snapshot.path),
        "quarto_sha256": quarto_snapshot.sha256,
        "quarto_version": QUARTO_VERSION,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
    }
    qmd_bytes = build_qmd_bytes(
        summary,
        tables,
        template_bytes=template_bytes,
        css_bytes=css_bytes,
        render_metadata=render_metadata,
    )
    for snapshot, label in (
        (run_summary_snapshot, "run-summary document"),
        (template_snapshot, "report QMD template"),
        (css_snapshot, "report CSS template"),
        (quarto_snapshot, "Quarto executable"),
    ):
        _assert_snapshot(snapshot, label)
    return RenderContext(
        run_summary_path=run_summary_path,
        run_summary_snapshot=run_summary_snapshot,
        summary=summary,
        tables=tables,
        template_snapshot=template_snapshot,
        css_snapshot=css_snapshot,
        quarto_path=quarto_path,
        quarto_snapshot=quarto_snapshot,
        output_root=output_root,
        output_dir=output_dir,
        output_html=output_html,
        lock_path=lock_path,
        previous_output_snapshot=previous_output_snapshot,
        render_metadata=render_metadata,
        qmd_bytes=qmd_bytes,
        execute=arguments.execute,
    )


def _create_directories(path: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while not os.path.lexists(current):
        missing.append(current)
        if current == current.parent:
            break
        current = current.parent
    if os.path.lexists(current):
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(f"Report output ancestor is not a non-symlink directory: {current}")
    created: list[Path] = []
    try:
        for directory in reversed(missing):
            os.mkdir(directory, 0o755)
            created.append(directory)
    except OSError as exc:
        for directory in reversed(created):
            with contextlib.suppress(OSError):
                directory.rmdir()
        _fail(f"Could not create report output directory {path}: {exc}")
    _reject_symlink_components(path, "report output directory")
    return created


def _remove_empty_created_directories(created: Sequence[Path]) -> None:
    for directory in reversed(created):
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            break


def _lock_payload(context: RenderContext, token: str) -> str:
    return (
        "owner\tNORAD_REPORT_HTML\n"
        f"pid\t{os.getpid()}\n"
        f"token\t{token}\n"
        f"run_id\t{context.summary['run_id']}\n"
        f"run_summary_sha256\t{context.run_summary_snapshot.sha256}\n"
    )


def _acquire_lock(context: RenderContext, token: str) -> LockOwnership:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(context.lock_path, flags, 0o600)
    except FileExistsError:
        _fail(f"Report render lock already exists: {context.lock_path}")
    except OSError as exc:
        _fail(f"Could not create report render lock {context.lock_path}: {exc}")
    metadata: os.stat_result | None = None
    try:
        metadata = os.fstat(descriptor)
        payload = _lock_payload(context, token).encode("utf-8")
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    except BaseException as original_exc:
        if metadata is None:
            try:
                metadata = os.fstat(descriptor)
            except OSError:
                metadata = None
        os.close(descriptor)
        try:
            if metadata is None:
                raise ReportRenderError("Could not capture owned report-lock identity")
            current = context.lock_path.lstat()
            if current.st_dev != metadata.st_dev or current.st_ino != metadata.st_ino:
                raise ReportRenderError(
                    "Report lock changed identity during interrupted "
                    f"acquisition: {context.lock_path}"
                )
            context.lock_path.unlink()
        except (OSError, ReportRenderError) as cleanup_exc:
            raise ReportRenderError(
                "Report lock acquisition was interrupted and owned cleanup "
                f"could not be proved: {cleanup_exc}"
            ) from original_exc
        raise
    os.close(descriptor)
    assert metadata is not None
    return LockOwnership(
        path=context.lock_path,
        token=token,
        device=metadata.st_dev,
        inode=metadata.st_ino,
    )


def _release_lock(ownership: LockOwnership) -> None:
    snapshot = _snapshot_regular(ownership.path, "owned report render lock")
    try:
        payload = ownership.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read owned report render lock: {exc}")
    if (
        snapshot.device != ownership.device
        or snapshot.inode != ownership.inode
        or f"token\t{ownership.token}\n" not in payload
    ):
        _fail(
            "Report render lock identity or ownership changed; refusing "
            f"cleanup: {ownership.path}"
        )
    ownership.path.unlink()


def _install_publication_signal_handlers() -> dict[int, Any]:
    previous: dict[int, Any] = {}

    def interrupt(signum: int, _frame: Any) -> None:
        try:
            name = signal.Signals(signum).name
        except ValueError:
            name = str(signum)
        raise ReportRenderError(f"Report publication interrupted by signal {name}")

    try:
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, interrupt)
    except BaseException as exc:
        try:
            _restore_signal_handlers(previous)
        except BaseException as restore_exc:
            raise ReportRenderError(
                "Could not restore partially installed report publication "
                f"signal handlers: {restore_exc}"
            ) from exc
        raise
    return previous


def _restore_signal_handlers(previous: Mapping[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)


def _snapshot_at(snapshot: FileSnapshot, path: Path) -> FileSnapshot:
    return FileSnapshot(
        path=path,
        sha256=snapshot.sha256,
        device=snapshot.device,
        inode=snapshot.inode,
        size_bytes=snapshot.size_bytes,
        mtime_ns=snapshot.mtime_ns,
        ctime_ns=snapshot.ctime_ns,
    )


def _capture_moved_snapshot(
    path: Path,
    expected: FileSnapshot,
    label: str,
) -> FileSnapshot:
    current = _snapshot_regular(path, label)
    stable_identity = (
        current.device,
        current.inode,
        current.size_bytes,
        current.mtime_ns,
        current.sha256,
    )
    expected_identity = (
        expected.device,
        expected.inode,
        expected.size_bytes,
        expected.mtime_ns,
        expected.sha256,
    )
    if stable_identity != expected_identity:
        _fail(f"{label} changed identity or content during publication: {path}")
    return current


def _assert_predecessor(context: RenderContext) -> None:
    previous = context.previous_output_snapshot
    if previous is None:
        if os.path.lexists(context.output_html):
            _fail(
                "Report output appeared after initial validation; prepare a "
                f"fresh render context: {context.output_html}"
            )
        return
    _assert_snapshot(previous, "existing report output")
    validate_rendered_html(
        context.output_html,
        expected_banner=None,
    )
    _assert_snapshot(previous, "existing report output")


def _write_recovery_marker(path: Path, message: str) -> None:
    with contextlib.suppress(OSError, ReportRenderError):
        _write_owned_file(path, message.encode("utf-8"))


def _write_owned_file(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_owned_stage(
    path: Path,
    token: str,
    identity: tuple[int, int] | None,
) -> None:
    if not os.path.lexists(path):
        return
    metadata = path.lstat()
    if (
        token not in path.name
        or identity is None
        or (metadata.st_dev, metadata.st_ino) != identity
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail(f"Refusing to remove unverified report staging path: {path}")
    shutil.rmtree(path)


def _recheck_inputs(context: RenderContext) -> None:
    labels = (
        "run-summary document",
        "report QMD template",
        "report CSS template",
        "Quarto executable",
        *(f"approved report table {table.table_id!r}" for table in context.tables),
    )
    for snapshot, label in zip(context.input_snapshots, labels):
        _assert_snapshot(snapshot, label)


def _source_date_epoch(summary: Mapping[str, Any]) -> str:
    value = summary["generated_at"]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # schema validation should make this unreachable
        _fail(f"Could not derive fixed report time from generated_at: {exc}")
    return str(int(parsed.timestamp()))


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Stop the complete Quarto process group and reap its direct process."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        if process.poll() is None:
            process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def _run_quarto_process(
    command: Sequence[str],
    stage: Path,
    environment: Mapping[str, str],
    fail: Callable[[str], NoReturn],
) -> tuple[int, str, str]:
    """Own the shared timeout and process-group lifecycle for Quarto renders."""
    print("Quarto render command:")
    print(f"  {shlex.join(command)}")
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=stage,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_group(process)
            fail(f"Quarto render exceeded the 300-second timeout: {exc}")
    except OSError as exc:
        if process is not None:
            _terminate_process_group(process)
        fail(f"Could not execute Quarto render: {exc}")
    except BaseException:
        if process is not None:
            _terminate_process_group(process)
        raise
    assert process is not None and process.returncode is not None
    if stdout.strip():
        print(stdout.rstrip())
    return process.returncode, stdout, stderr


def _render_with_quarto(
    context: RenderContext,
    stage: Path,
) -> Path:
    run_id = context.summary["run_id"]
    qmd_path = stage / f"{run_id}.run_report.qmd"
    output_name = f"{run_id}.run_report.html"
    output_path = stage / output_name
    project_path = stage / "_quarto.yml"
    _write_owned_file(qmd_path, context.qmd_bytes)
    project_bytes = (
        f"project:\n  type: default\n  render:\n    - {qmd_path.name}\n"
    ).encode()
    _write_owned_file(project_path, project_bytes)
    command = [
        str(context.quarto_path),
        "render",
        qmd_path.name,
        "--to",
        "html",
        "--output",
        output_name,
        "--no-execute",
    ]
    environment = _sanitized_tool_environment()
    environment["SOURCE_DATE_EPOCH"] = _source_date_epoch(context.summary)
    environment["DENO_DIR"] = str(stage / ".deno")
    runtime_tmp = stage / ".runtime-tmp"
    runtime_tmp.mkdir(mode=0o700)
    environment["TMPDIR"] = str(runtime_tmp)
    returncode, standard_output, standard_error = _run_quarto_process(
        command, stage, environment, _fail
    )
    if returncode != 0:
        detail = standard_error.strip() or standard_output.strip()
        _fail(f"Quarto render failed with exit {returncode}: {detail}")
    if standard_error.strip():
        print(standard_error.rstrip(), file=sys.stderr)
    for child in stage.iterdir():
        if child.is_dir() and child.name.endswith("_files"):
            _fail(
                "Quarto created a sidecar resource directory despite the "
                f"self-contained contract: {child}"
            )
    validate_rendered_html(
        output_path,
        expected_banner=SCIENCE_BANNERS[context.summary["science_status"]],
        expected_identity=_expected_html_identity(context),
    )
    return output_path


def publish_report(context: RenderContext) -> None:
    created = _create_directories(context.output_dir)
    output_dir_metadata = context.output_dir.lstat()
    output_dir_identity = (
        output_dir_metadata.st_dev,
        output_dir_metadata.st_ino,
    )
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    stage = context.output_dir / f".run-report.{token}.tmp"
    backup = context.output_dir / f".{context.output_html.name}.{token}.previous"
    recovery = (
        context.output_dir
        / f".{context.summary['run_id']}.report-html.{token}.RECOVERY.txt"
    )
    ownership: LockOwnership | None = None
    previous_signal_handlers: dict[int, Any] | None = None
    backed_up = False
    published = False
    committed = False
    recovery_required = False
    output_identity_lost = False
    stage_identity: tuple[int, int] | None = None
    rendered_snapshot: FileSnapshot | None = None
    backup_snapshot: FileSnapshot | None = None
    published_snapshot: FileSnapshot | None = None

    def assert_output_dir_identity() -> None:
        if not os.path.lexists(context.output_dir):
            _fail(
                "Report output directory disappeared during publication: "
                f"{context.output_dir}"
            )
        metadata = context.output_dir.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != output_dir_identity
        ):
            _fail(
                "Report output directory changed identity during publication: "
                f"{context.output_dir}"
            )

    try:
        previous_signal_handlers = _install_publication_signal_handlers()
        ownership = _acquire_lock(context, token)
        assert_output_dir_identity()
        _assert_predecessor(context)
        os.mkdir(stage, 0o700)
        stage_metadata = stage.lstat()
        stage_identity = (stage_metadata.st_dev, stage_metadata.st_ino)
        _recheck_inputs(context)
        rendered = _render_with_quarto(context, stage)
        rendered_snapshot = _snapshot_regular(
            rendered,
            "validated staged HTML report",
        )
        _fsync_file(rendered)
        _recheck_inputs(context)
        assert_output_dir_identity()
        _assert_predecessor(context)
        if os.path.lexists(backup):
            _fail(f"Report backup path unexpectedly exists: {backup}")
        if context.previous_output_snapshot is not None:
            backed_up = True
            os.link(
                context.output_html,
                backup,
                follow_symlinks=False,
            )
            backup_snapshot = _capture_moved_snapshot(
                backup,
                context.previous_output_snapshot,
                "backed-up prior HTML report",
            )
            _fsync_directory(context.output_dir)
            _capture_moved_snapshot(
                context.output_html,
                context.previous_output_snapshot,
                "existing report output",
            )
            context.output_html.unlink()
            _fsync_directory(context.output_dir)
        published = True
        os.link(
            rendered,
            context.output_html,
            follow_symlinks=False,
        )
        published_snapshot = _capture_moved_snapshot(
            context.output_html,
            rendered_snapshot,
            "newly published HTML report",
        )
        _fsync_file(context.output_html)
        _fsync_directory(context.output_dir)
        validate_rendered_html(
            context.output_html,
            expected_banner=SCIENCE_BANNERS[context.summary["science_status"]],
            expected_identity=_expected_html_identity(context),
        )
        _recheck_inputs(context)
        assert_output_dir_identity()
        committed = True
    except BaseException as original_exc:
        if committed:
            if isinstance(original_exc, ReportRenderError):
                raise
            if isinstance(original_exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise ReportRenderError(str(original_exc)) from original_exc
        rollback_errors: list[str] = []

        try:
            assert_output_dir_identity()
        except ReportRenderError as identity_exc:
            output_identity_lost = True
            recovery_required = True
            raise ReportRenderError(
                f"{original_exc}\nReport output directory identity changed "
                "during publication; path-based rollback was skipped to avoid "
                "modifying a replacement directory. Preserve the owned lock "
                f"and recovery state: {identity_exc}"
            ) from original_exc

        def rollback(label: str, operation: Any) -> None:
            nonlocal output_identity_lost
            try:
                assert_output_dir_identity()
            except ReportRenderError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")
                return
            try:
                operation()
                assert_output_dir_identity()
            except BaseException as rollback_exc:
                rollback_errors.append(f"{label}: {rollback_exc}")

        def remove_new_report() -> None:
            if not os.path.lexists(context.output_html):
                return
            if published_snapshot is None:
                if rendered_snapshot is None:
                    _fail(
                        "A final report exists but no owned staged report "
                        "snapshot was captured"
                    )
                _capture_moved_snapshot(
                    context.output_html,
                    rendered_snapshot,
                    "owned newly published HTML report",
                )
            else:
                _assert_snapshot(
                    published_snapshot,
                    "owned newly published HTML report",
                )
            context.output_html.unlink()

        def restore_prior_report() -> None:
            previous = context.previous_output_snapshot
            if previous is None:
                _fail("No prior report was declared for rollback")
            if os.path.lexists(backup):
                if backup_snapshot is None:
                    backup_snapshot_local = _capture_moved_snapshot(
                        backup,
                        previous,
                        "owned prior-report backup",
                    )
                else:
                    _assert_snapshot(
                        backup_snapshot,
                        "owned prior-report backup",
                    )
                    backup_snapshot_local = backup_snapshot
                if os.path.lexists(context.output_html):
                    _capture_moved_snapshot(
                        context.output_html,
                        previous,
                        "prior HTML report that remained during backup",
                    )
                    backup.unlink()
                    return
                os.link(
                    backup,
                    context.output_html,
                    follow_symlinks=False,
                )
                _capture_moved_snapshot(
                    context.output_html,
                    backup_snapshot_local,
                    "restored prior HTML report",
                )
                backup.unlink()
                return
            if os.path.lexists(context.output_html):
                _capture_moved_snapshot(
                    context.output_html,
                    previous,
                    "prior HTML report that remained in place",
                )
                return
            _fail(
                "Neither the validated prior report nor its owned backup "
                f"remains: {context.output_html}"
            )

        if published:
            rollback("remove owned new report", remove_new_report)
        if context.previous_output_snapshot is not None and backed_up:
            if not rollback_errors:
                rollback("restore validated prior report", restore_prior_report)
        elif context.previous_output_snapshot is not None:
            rollback(
                "verify prior report remained in place",
                restore_prior_report,
            )
        elif os.path.lexists(context.output_html):
            rollback(
                "remove unexpected first-publication output",
                remove_new_report,
            )
        if not rollback_errors:
            rollback(
                "durability-sync report rollback",
                lambda: _fsync_directory(context.output_dir),
            )
        if rollback_errors:
            recovery_required = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery,
                    "Report HTML rollback was incomplete.\n"
                    f"Original error: {original_exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Backup: {backup}\n"
                    f"Lock: {context.lock_path}\n",
                )
            raise ReportRenderError(
                "Report publication failed and rollback was incomplete. "
                "Preserve the owned lock and recovery state under "
                f"{context.output_dir}. Rollback errors: " + "; ".join(rollback_errors)
            ) from original_exc
        backed_up = False
        published = False
        if isinstance(original_exc, ReportRenderError):
            raise
        if isinstance(original_exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise ReportRenderError(str(original_exc)) from original_exc
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required and not output_identity_lost:
            try:
                assert_output_dir_identity()
                _remove_owned_stage(stage, token, stage_identity)
            except Exception as exc:
                cleanup_errors.append(f"owned stage cleanup failed: {exc}")
            if not cleanup_errors and os.path.lexists(backup):
                try:
                    if not committed or backup_snapshot is None:
                        _fail("Unexpected report backup remains after rollback")
                    _assert_snapshot(
                        backup_snapshot,
                        "owned committed report backup",
                    )
                    backup.unlink()
                    _fsync_directory(context.output_dir)
                except Exception as exc:
                    cleanup_errors.append(f"owned backup cleanup failed: {exc}")
        if (
            ownership is not None
            and not recovery_required
            and not output_identity_lost
            and not cleanup_errors
        ):
            try:
                _release_lock(ownership)
            except Exception as exc:
                cleanup_errors.append(f"owned lock cleanup failed: {exc}")
        if previous_signal_handlers is not None:
            try:
                _restore_signal_handlers(previous_signal_handlers)
            except BaseException as exc:
                cleanup_errors.append(f"signal-handler restoration failed: {exc}")
        if cleanup_errors:
            recovery_required = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery,
                    "Report HTML publication cleanup was incomplete.\n"
                    f"Active error: {active}\n"
                    f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Backup: {backup}\n"
                    f"Lock: {context.lock_path}\n",
                )
            raise ReportRenderError(
                "Report publication cleanup failed; preserve the owned lock "
                f"and recovery state under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active
        if (
            active is not None
            and not recovery_required
            and not os.path.lexists(context.output_html)
        ):
            _remove_empty_created_directories(created)


def print_plan(context: RenderContext) -> None:
    mode = "execute" if context.execute else "dry-run"
    print("NORAD static run-report plan:")
    print(f"  Mode: {mode}")
    print(f"  Run ID: {context.summary['run_id']}")
    print(f"  Run summary: {context.run_summary_path}")
    print(f"  Run-summary SHA-256: {context.run_summary_snapshot.sha256}")
    print(f"  Science status: {context.summary['science_status']}")
    print(f"  State banner: {SCIENCE_BANNERS[context.summary['science_status']]}")
    print(f"  Approved report tables: {len(context.tables)}")
    for table in context.tables:
        print(
            f"    {table.table_id}: {table.path} "
            f"(rows={table.row_count}, display={table.displayed_row_count}, "
            f"sha256={table.sha256})"
        )
    print(f"  Quarto: {context.quarto_path}")
    print(f"  Quarto version: {QUARTO_VERSION}")
    print(f"  QMD template: {context.template_snapshot.path}")
    print(f"  CSS template: {context.css_snapshot.path}")
    print(f"  HTML output: {context.output_html}")
    print(
        "  Report meaning: rendering does not establish computational or "
        "scientific validation."
    )


def html_core_main(argv: Sequence[str] | None = None) -> int:
    """Run the established HTML core used by the bundle coordinator."""

    try:
        arguments = parse_arguments(argv)
        if arguments.formats != "html":
            _fail("The internal HTML core accepts only --formats html")
        context = prepare_context(arguments)
        print_plan(context)
        if context.execute:
            publish_report(context)
            print(f"Published self-contained HTML report: {context.output_html}")
        else:
            print(
                "Dry-run only. Add --execute to publish the HTML report; no "
                "output, lock, or scratch path was created."
            )
        return 0
    except ReportRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the public report-bundle interface."""

    from norad.reporting import render_run_report_bundle

    return render_run_report_bundle.main(list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
