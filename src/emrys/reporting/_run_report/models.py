"""Run-report constants and immutable model types."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from emrys.reporting import ReportProviderError
from emrys.reporting._files import FileSnapshot

if TYPE_CHECKING:
    from emrys.analyses import LoadedAnalysisModuleV1
    from emrys.libraries.source_authority import ArtifactSourceRoot, SourceCheckout

PRODUCER = "emrys.reporting.report"
PRODUCER_VERSION = "5.2.0"
HISTORICAL_RUN_SUMMARY_SCHEMA_VERSION = "2.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "3.0.0"
HISTORICAL_REPORT_RECEIPT_SCHEMA_VERSION = "4.0.0"
REPORT_RECEIPT_SCHEMA_VERSION = "5.0.0"
JINJA_VERSION = "3.1.6"
TEMPLATE_RESOURCE = "templates/run_report.html.j2"
CSS_RESOURCE = "styles/run_report.css"
COMPUTATIONAL_STATUS_FIELDS: tuple[tuple[str, str], ...] = (
    ("Implementation", "implementation_status"),
    ("Local testing", "local_test_status"),
    ("Runtime validation", "runtime_validation_status"),
    ("Cluster dry-run", "cluster_dry_run_status"),
    ("Cluster proof", "cluster_proof_status"),
)
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
EVIDENCE_REPORT_SECTION_IDS = {
    "run-identity-section",
    "status-section",
    "limitations-section",
    "scope-matrix-section",
    "analysis-sources-section",
    "qc-metrics-section",
    "attempt-lineage-section",
    "artifact-appendix-section",
    "tools-issues-section",
    "report-provenance-section",
}
RECEIPT_HEADER = (
    "schema_name",
    "schema_version",
    "run_id",
    "attempt_id",
    "generated_at",
    "interpretation_boundary",
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
    "interpretation_boundary",
    "step_id",
    "scope_type",
    "scope_id",
    "aggregate_state",
    *(field for _, field in COMPUTATIONAL_STATUS_FIELDS),
    "warning_count",
    "error_count",
)


ReportRenderError = ReportProviderError


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
    analysis_policy_path: Path | None
    analysis_policy_snapshot: FileSnapshot | None
    analysis_policy: dict[str, Any] | None
    template_snapshot: FileSnapshot
    css_snapshot: FileSnapshot
    output_root: Path
    output_dir: Path
    output_scientific_html: Path
    output_evidence_html: Path
    output_summary_tsv: Path
    output_receipt: Path
    lock_path: Path
    stable_paths: tuple[Path, ...]
    previous_snapshots: Mapping[Path, FileSnapshot]
    render_metadata: Mapping[str, str]
    scientific_html_bytes: bytes
    evidence_html_bytes: bytes
    analysis_module: LoadedAnalysisModuleV1
    scientific_renderer: Mapping[str, str]
    report_receipt_schema_version: str
    report_input_rechecks: tuple[tuple[FileSnapshot, str, bool], ...]
    interpretation_boundary: str

    @property
    def input_rechecks(self) -> tuple[tuple[FileSnapshot, str, bool], ...]:
        checks: list[tuple[FileSnapshot, str, bool]] = [
            (self.run_summary_snapshot, "run-summary document", True),
            (self.template_snapshot, "report Jinja template", True),
            (self.css_snapshot, "report CSS resource", True),
        ]
        if self.analysis_policy_snapshot is not None:
            checks.append(
                (self.analysis_policy_snapshot, "primary analysis policy", True)
            )
        checks.extend(self.report_input_rechecks)
        return tuple(checks)

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return tuple(snapshot for snapshot, _label, _rehash in self.input_rechecks)
