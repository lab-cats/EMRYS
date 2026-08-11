"""Run-report constants and immutable model types."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from norad.contracts.scientific_evidence import review_package
from norad.reporting import _files

_MODULE_PATH = Path(__file__).resolve()

PRODUCER = "render_run_report"
PRODUCER_VERSION = "1.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "1.1.0"
QUARTO_VERSION = "1.9.38"
QMD_TEMPLATE = _MODULE_PATH.parent.parent / "templates" / "run_report.qmd"
CSS_TEMPLATE = _MODULE_PATH.parent.parent / "styles" / "run_report.css"
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
KNOWN_REPORT_ROLES = set(review_package.REPORT_TABLE_ROLES)
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
