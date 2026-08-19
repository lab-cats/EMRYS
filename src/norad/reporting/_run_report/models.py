"""Run-report constants and immutable model types."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from norad.reporting._files import FileSnapshot

if TYPE_CHECKING:
    from norad.libraries.source_authority import ArtifactSourceRoot, SourceCheckout

PRODUCER = "norad.reporting.report"
PRODUCER_VERSION = "4.3.0"
RUN_SUMMARY_SCHEMA_VERSION = "2.0.0"
REPORT_RECEIPT_SCHEMA_VERSION = "4.0.0"
JINJA_VERSION = "3.1.6"
MATPLOTLIB_VERSION = "3.11.1"
LOGOMAKER_VERSION = "0.8.7"
FIGURE_POLICY_VERSION = "3.0.0"
FIGURE_FORMAT = "SVG data URI"
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
INTERPRETATION_BOUNDARY = (
    "computational_candidates_only_biological_validation_outside_norad"
)
BOUNDARY_BANNER = "COMPUTATIONAL RESULTS — BIOLOGICAL VALIDATION IS OUTSIDE NORAD."
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
SCIENTIFIC_REPORT_SECTION_IDS = {
    "computational-results-section",
    "scientific-figures-section",
    "key-qc-section",
}
EVIDENCE_REPORT_SECTION_IDS = {
    "run-identity-section",
    "status-section",
    "limitations-section",
    "scope-matrix-section",
    "step09-sources-section",
    "qc-metrics-section",
    "attempt-lineage-section",
    "artifact-appendix-section",
    "tools-issues-section",
    "report-provenance-section",
}
REPORT_SECTION_IDS_BY_VIEW = {
    "scientific": SCIENTIFIC_REPORT_SECTION_IDS,
    "evidence": EVIDENCE_REPORT_SECTION_IDS,
}
SCIENTIFIC_FIGURE_IDS = (
    "candidate-landscape-figure",
    "mutation-spectrum-figure",
    "condition-concordance-figure",
    "paired-sample-profile-figure",
    "location-membership-figure",
    "sequence-context-logo-figure",
    "motif-context-enrichment-figure",
    "selected-context-track-figure",
)
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


class ReportRenderError(RuntimeError):
    """Raised when a run report cannot be validated or safely published."""


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
class SamplePair:
    replicate: str
    control_sample_id: str
    treatment_sample_id: str


@dataclass(frozen=True)
class ComputationalSampleManifest:
    role: str
    path: Path
    sha256: str
    size_bytes: int
    sample_ids: tuple[str, ...]
    control_condition: str
    treatment_condition: str
    pairs: tuple[SamplePair, ...]
    snapshot: FileSnapshot


@dataclass(frozen=True)
class ScientificFigure:
    figure_id: str
    title: str
    status: str
    data_uri: str | None
    alt_text: str
    text_summary: str
    caption: str
    input_roles: tuple[str, ...]
    mapping: str
    population: str
    svg_sha256: str | None
    svg_size_bytes: int | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class ComputationalResults:
    analysis_id: str
    sample_ids: tuple[str, ...]
    validation: ComputationalTable
    all_sites: ComputationalTable
    significant_sites: ComputationalTable
    summary: ComputationalTable
    mutation_spectrum: ComputationalTable
    sample_manifest: ComputationalSampleManifest

    @property
    def tables(self) -> tuple[ComputationalTable, ...]:
        return (
            self.validation,
            self.all_sites,
            self.significant_sites,
            self.summary,
            self.mutation_spectrum,
        )

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return (
            *(table.snapshot for table in self.tables),
            self.sample_manifest.snapshot,
        )


@dataclass(frozen=True)
class ScientificContextSource:
    role: str
    artifact_id: str
    path: Path
    sha256: str
    size_bytes: int
    row_count: int | None
    snapshot: FileSnapshot


@dataclass(frozen=True)
class ScientificContextResults:
    analysis_id: str
    validation: ComputationalTable
    candidate_context: ComputationalTable
    motif_hits: ComputationalTable
    sequence_logo: ComputationalTable
    motif_statistics: ComputationalTable
    receipt: ComputationalTable
    bound_inputs: tuple[ScientificContextSource, ...]
    receipt_metadata: Mapping[str, str]

    @property
    def tables(self) -> tuple[ComputationalTable, ...]:
        return (
            self.validation,
            self.candidate_context,
            self.motif_hits,
            self.sequence_logo,
            self.motif_statistics,
            self.receipt,
        )

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return (
            *(table.snapshot for table in self.tables),
            *(source.snapshot for source in self.bound_inputs),
        )


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
    computational_results: ComputationalResults | None
    computational_unavailable_reason: str | None
    scientific_context_results: ScientificContextResults | None
    scientific_context_unavailable_reason: str | None
    scientific_figures: tuple[ScientificFigure, ...]
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
    execute: bool

    @property
    def input_rechecks(self) -> tuple[tuple[FileSnapshot, str, bool], ...]:
        checks: list[tuple[FileSnapshot, str, bool]] = [
            (self.run_summary_snapshot, "run-summary document", True),
            (self.template_snapshot, "report Jinja template", True),
            (self.css_snapshot, "report CSS resource", True),
        ]
        computational_snapshots: tuple[FileSnapshot, ...] = ()
        if self.computational_results is not None:
            computational = self.computational_results
            computational_snapshots = computational.input_snapshots
            checks.extend(
                (
                    table.snapshot,
                    f"computational result {table.artifact_id!r}",
                    True,
                )
                for table in computational.tables
            )
            checks.append(
                (
                    computational.sample_manifest.snapshot,
                    "Step 09 sample manifest",
                    True,
                )
            )
        if self.scientific_context_results is not None:
            scientific_context = self.scientific_context_results
            checks.extend(
                (
                    table.snapshot,
                    f"scientific-context result {table.artifact_id!r}",
                    True,
                )
                for table in scientific_context.tables
                if table.snapshot not in computational_snapshots
            )
            checks.extend(
                (
                    source.snapshot,
                    f"scientific-context receipt-bound input {source.role!r}",
                    source.role != "reference_fasta",
                )
                for source in scientific_context.bound_inputs
                if source.snapshot not in computational_snapshots
            )
        return tuple(checks)

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return tuple(snapshot for snapshot, _label, _rehash in self.input_rechecks)

    @property
    def input_snapshot_labels(self) -> tuple[str, ...]:
        return tuple(label for _snapshot, label, _rehash in self.input_rechecks)
