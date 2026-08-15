"""Run-report constants and immutable model types."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from norad.contracts.scientific_evidence import review_package
from norad.reporting._files import FileSnapshot

if TYPE_CHECKING:
    from norad.libraries.source_authority import ArtifactSourceRoot, SourceCheckout

PRODUCER = "norad.reporting.report"
PRODUCER_VERSION = "2.1.0"
RUN_SUMMARY_SCHEMA_VERSION = "1.1.0"
REPORT_RECEIPT_SCHEMA_VERSION = "2.0.0"
JINJA_VERSION = "3.1.6"
TEMPLATE_RESOURCE = "templates/run_report.html.j2"
CSS_RESOURCE = "styles/run_report.css"
CANDIDATE_TERMINOLOGY = "CMH-ranked candidates"
COMPUTATIONAL_ALL_SITES_DISPLAY_LIMIT = 250
COMPUTATIONAL_SIGNIFICANT_DISPLAY_LIMIT = 250
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
REPORT_SECTION_IDS = {
    "computational-results-section",
    "key-qc-section",
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
RECEIPT_HEADER = (
    "schema_name",
    "schema_version",
    "run_id",
    "attempt_id",
    "generated_at",
    "science_status",
    "output_id",
    "kind",
    "path",
    "sha256",
    "size_bytes",
    "media_type",
    "self_contained",
    "report_receipt_json",
)
SUMMARY_HEADER = (
    "run_id",
    "science_status",
    "step_id",
    "scope_type",
    "scope_id",
    "aggregate_state",
    *(field for _, field in COMPUTATIONAL_STATUS_FIELDS),
    "warning_count",
    "error_count",
)


class ReportRenderError(RuntimeError):
    """Raised when a run report cannot be validated or safely published."""


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
class ComputationalTable:
    role: str
    table_id: str
    artifact_id: str
    title: str
    path: Path
    sha256: str
    size_bytes: int
    row_count: int
    display_row_limit: int
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
class ComputationalResults:
    analysis_id: str
    sample_ids: tuple[str, ...]
    validation: ComputationalTable
    all_sites: ComputationalTable
    significant_sites: ComputationalTable
    summary: ComputationalTable

    @property
    def tables(self) -> tuple[ComputationalTable, ...]:
        return (self.validation, self.all_sites, self.significant_sites, self.summary)


@dataclass(frozen=True)
class LockOwnership:
    path: Path
    token: str
    device: int
    inode: int


@dataclass(frozen=True)
class ReportContext:
    source_checkout: SourceCheckout
    artifact_source_root: ArtifactSourceRoot
    producer_git_commit: str
    run_summary_path: Path
    run_summary_snapshot: FileSnapshot
    summary: dict[str, Any]
    tables: tuple[ApprovedTable, ...]
    computational_results: ComputationalResults | None
    computational_unavailable_reason: str | None
    template_snapshot: FileSnapshot
    css_snapshot: FileSnapshot
    output_root: Path
    output_dir: Path
    output_html: Path
    output_summary_tsv: Path
    output_receipt: Path
    lock_path: Path
    stable_paths: tuple[Path, ...]
    previous_snapshots: Mapping[Path, FileSnapshot]
    render_metadata: Mapping[str, str]
    html_bytes: bytes
    execute: bool

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        computational = (
            self.computational_results.tables
            if self.computational_results is not None
            else ()
        )
        return (
            self.run_summary_snapshot,
            self.template_snapshot,
            self.css_snapshot,
            *(table.snapshot for table in computational),
            *(table.snapshot for table in self.tables),
        )

    @property
    def input_snapshot_labels(self) -> tuple[str, ...]:
        computational = (
            self.computational_results.tables
            if self.computational_results is not None
            else ()
        )
        return (
            "run-summary document",
            "report Jinja template",
            "report CSS resource",
            *(f"computational result {table.artifact_id!r}" for table in computational),
            *(f"approved report table {table.table_id!r}" for table in self.tables),
        )
