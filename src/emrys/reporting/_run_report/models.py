"""Run-report constants and immutable model types."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from emrys.reporting._files import FileSnapshot

if TYPE_CHECKING:
    from emrys.libraries.source_authority import ArtifactSourceRoot, SourceCheckout

    from .candidate_display import SelectedCandidateProjection

PRODUCER = "emrys.reporting.report"
PRODUCER_VERSION = "5.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "2.0.0"
REPORT_RECEIPT_SCHEMA_VERSION = "4.0.0"
JINJA_VERSION = "3.1.6"
MATPLOTLIB_VERSION = "3.11.1"
LOGOMAKER_VERSION = "0.8.7"
FIGURE_POLICY_VERSION = "4.0.0"
FIGURE_FORMAT = "SVG data URI"
TEMPLATE_RESOURCE = "templates/run_report.html.j2"
CSS_RESOURCE = "styles/run_report.css"
CANDIDATE_TERMINOLOGY = "CMH-ranked candidates"
# Native candidate TSVs are admitted and streamed where needed, but no prefix is
# materialized for a human-facing wide table in the scientific HTML.
COMPUTATIONAL_ALL_SITES_DISPLAY_LIMIT = 0
COMPUTATIONAL_SIGNIFICANT_DISPLAY_LIMIT = 0
COMPUTATIONAL_STATUS_FIELDS: tuple[tuple[str, str], ...] = (
    ("Implementation", "implementation_status"),
    ("Local testing", "local_test_status"),
    ("Runtime validation", "runtime_validation_status"),
    ("Cluster dry-run", "cluster_dry_run_status"),
    ("Cluster proof", "cluster_proof_status"),
)
INTERPRETATION_BOUNDARY = (
    "computational_candidates_only_biological_validation_outside_emrys"
)
BOUNDARY_BANNER = "COMPUTATIONAL RESULTS — BIOLOGICAL VALIDATION IS OUTSIDE EMRYS."
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
    "scientific-summary-section",
    "primary-scientific-figures-section",
    "supporting-scientific-figures-section",
    "figure-guide-section",
    "methods-data-note-section",
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
PRIMARY_SCIENTIFIC_FIGURE_IDS = (
    "candidate-landscape-figure",
    "selected-context-track-figure",
    "location-membership-figure",
    "motif-context-enrichment-figure",
)
SUPPORTING_SCIENTIFIC_FIGURE_IDS = (
    "mutation-spectrum-figure",
    "condition-concordance-figure",
    "paired-sample-profile-figure",
    "sequence-context-logo-figure",
)
SCIENTIFIC_FIGURE_LABELS: Mapping[str, str] = {
    **{
        figure_id: f"Figure {index}"
        for index, figure_id in enumerate(PRIMARY_SCIENTIFIC_FIGURE_IDS, start=1)
    },
    **{
        figure_id: f"Figure S{index}"
        for index, figure_id in enumerate(SUPPORTING_SCIENTIFIC_FIGURE_IDS, start=1)
    },
}
SCIENTIFIC_FIGURE_GUIDANCE: Mapping[str, Mapping[str, str]] = {
    "candidate-landscape-figure": {
        "question": (
            "How do editing-rate differences and read depth relate across the "
            "complete tested candidate population?"
        ),
        "how_to_read": (
            "Read depth increases from left to right and the treatment-minus-control "
            "editing-rate difference increases from bottom to top. Triangles mark "
            "exact threshold-passing candidates; the pale grid summarizes all tested "
            "candidates."
        ),
        "limitations": (
            "The geometric depth and effect thresholds do not encode the separate "
            "FDR, common-odds-ratio, or background filters. Passing candidates "
            "remain computational results rather than biologically validated sites."
        ),
    },
    "mutation-spectrum-figure": {
        "question": "Which RNA-change classes make up the admitted candidate set?",
        "how_to_read": (
            "Bar height is the number of candidates in each RNA-change class. The "
            "declared target change is highlighted separately from the other classes."
        ),
        "limitations": (
            "This is candidate-class composition. It does not establish PUM "
            "specificity or biological editing validity."
        ),
    },
    "condition-concordance-figure": {
        "question": (
            "How do mean editing rates compare between the declared control and "
            "treatment conditions across tested candidates?"
        ),
        "how_to_read": (
            "Each point compares the mean control editing rate on the horizontal axis "
            "with the mean treatment rate on the vertical axis. Points above the "
            "diagonal are higher in treatment; triangles are exact threshold-passing "
            "candidates."
        ),
        "limitations": (
            "Condition means summarize admitted samples and do not replace the "
            "paired replicate evidence or adjudicate biological effect."
        ),
    },
    "paired-sample-profile-figure": {
        "question": (
            "Are the upstream-selected candidates' paired replicate editing-rate "
            "patterns consistent across conditions?"
        ),
        "how_to_read": (
            "Within each candidate panel, each colored line joins one declared "
            "control/treatment replicate pair. Black diamonds connect the admitted "
            "condition means."
        ),
        "limitations": (
            "At most eight candidates are shown under a deterministic display rule; "
            "the figure is not a new scientific ranking."
        ),
    },
    "location-membership-figure": {
        "question": (
            "Which recorded transcript-region annotations overlap the significant "
            "candidate population?"
        ),
        "how_to_read": (
            "Each bar reports the count and percentage of significant candidates with "
            "that recorded annotation overlap. A candidate can contribute to more "
            "than one bar."
        ),
        "limitations": (
            "Memberships are nonexclusive and can reflect multiple isoforms. An "
            "all-false record means no recorded overlap, not an inferred intergenic site."
        ),
    },
    "sequence-context-logo-figure": {
        "question": (
            "What admitted base composition surrounds edited positions, and what "
            "fixed PUM consensus was registered for comparison?"
        ),
        "how_to_read": (
            "The observed panels show admitted base frequencies around edited bases. "
            "The separate reference panel shows the fixed registered PUM consensus "
            "used by the workflow."
        ),
        "limitations": (
            "The observed composition panels are not de novo motif discovery, and "
            "the fixed consensus panel is not evidence that a candidate is bound by PUM."
        ),
    },
    "motif-context-enrichment-figure": {
        "question": (
            "Where is the nearest exact registered PUM motif relative to the edited "
            "base, and how does motif incidence compare across admitted populations?"
        ),
        "how_to_read": (
            "The position panel shows the percentage of analyzable candidates whose "
            "nearest exact registered motif falls in each signed distance bin. The "
            "adjacent comparison reports the admitted odds ratio, confidence interval, "
            "and p-value."
        ),
        "limitations": (
            "The figure preserves the producer-admitted exact-match window and Fisher "
            "test. Association does not establish binding or mechanism."
        ),
    },
    "selected-context-track-figure": {
        "question": (
            "For each upstream-selected candidate, what are the editing rates, exact "
            "location annotations, read support, and nearby registered motif hits?"
        ),
        "how_to_read": (
            "Each panel belongs to one selected candidate. The sequence is centered "
            "on the edited base, yellow marks admitted exact motif spans within the "
            "displayed window, and paired lines compare control and treatment editing "
            "rates. Exact values and annotations appear in the following record."
        ),
        "limitations": (
            "This is a candidate-centered, mechanically oriented genomic-context "
            "view. It is not a continuous transcript locus, an isoform selection, or "
            "a report-inferred biological-strand interpretation."
        ),
    },
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
class ScientificFigurePanel:
    panel_id: str
    data_uri: str
    alt_text: str
    svg_sha256: str
    svg_size_bytes: int


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
    panels: tuple[ScientificFigurePanel, ...] = ()

    @staticmethod
    def _validate_asset(asset: ScientificFigurePanel, label: str) -> None:
        if not asset.panel_id or not asset.alt_text:
            raise ReportRenderError(f"{label} requires a panel ID and alt text")
        prefix = "data:image/svg+xml;base64,"
        if not asset.data_uri.startswith(prefix):
            raise ReportRenderError(f"{label} is not an embedded SVG data URI")
        try:
            payload = base64.b64decode(
                asset.data_uri[len(prefix) :],
                validate=True,
            )
        except (binascii.Error, ValueError) as exc:
            raise ReportRenderError(f"{label} has invalid base64 SVG bytes") from exc
        if b"<svg" not in payload[:4096]:
            raise ReportRenderError(f"{label} does not contain an SVG root")
        if len(payload) != asset.svg_size_bytes:
            raise ReportRenderError(f"{label} SVG byte size does not match provenance")
        if hashlib.sha256(payload).hexdigest() != asset.svg_sha256:
            raise ReportRenderError(f"{label} SVG SHA-256 does not match provenance")

    def validate(self) -> None:
        """Reject inconsistent availability and single/multi-panel provenance."""

        legacy_values = (self.data_uri, self.svg_sha256, self.svg_size_bytes)
        legacy_present = any(value is not None for value in legacy_values)
        legacy_complete = all(value is not None for value in legacy_values)
        if legacy_present and not legacy_complete:
            raise ReportRenderError(
                f"Scientific figure {self.figure_id!r} has partial legacy SVG provenance"
            )
        if self.panels and legacy_present:
            raise ReportRenderError(
                f"Scientific figure {self.figure_id!r} mixes legacy and panel SVGs"
            )
        if self.status == "available":
            if self.unavailable_reason is not None:
                raise ReportRenderError(
                    f"Available scientific figure {self.figure_id!r} has an "
                    "unavailable reason"
                )
            if not self.panels and not legacy_complete:
                raise ReportRenderError(
                    f"Available scientific figure {self.figure_id!r} has no SVG asset"
                )
        elif self.status == "unavailable":
            if self.panels or legacy_present:
                raise ReportRenderError(
                    f"Unavailable scientific figure {self.figure_id!r} has SVG assets"
                )
            if not self.unavailable_reason:
                raise ReportRenderError(
                    f"Unavailable scientific figure {self.figure_id!r} lacks a reason"
                )
        else:
            raise ReportRenderError(
                f"Scientific figure {self.figure_id!r} has unknown status {self.status!r}"
            )

        assets = self.panels
        if legacy_complete:
            assert self.data_uri is not None
            assert self.svg_sha256 is not None
            assert self.svg_size_bytes is not None
            assets = (
                ScientificFigurePanel(
                    panel_id=f"{self.figure_id}-panel",
                    data_uri=self.data_uri,
                    alt_text=self.alt_text,
                    svg_sha256=self.svg_sha256,
                    svg_size_bytes=self.svg_size_bytes,
                ),
            )
        panel_ids = tuple(asset.panel_id for asset in assets)
        if len(panel_ids) != len(set(panel_ids)):
            raise ReportRenderError(
                f"Scientific figure {self.figure_id!r} repeats a panel ID"
            )
        for asset in assets:
            self._validate_asset(asset, f"Scientific figure panel {asset.panel_id!r}")

    @property
    def assets(self) -> tuple[ScientificFigurePanel, ...]:
        """Return one normalized ordered asset roster for single or panel figures."""

        self.validate()
        if self.panels:
            return self.panels
        if (
            self.data_uri is None
            or self.svg_sha256 is None
            or self.svg_size_bytes is None
        ):
            return ()
        return (
            ScientificFigurePanel(
                panel_id=f"{self.figure_id}-panel",
                data_uri=self.data_uri,
                alt_text=self.alt_text,
                svg_sha256=self.svg_sha256,
                svg_size_bytes=self.svg_size_bytes,
            ),
        )


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
    candidate_display: SelectedCandidateProjection | None
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
