"""Shared run-summary constants, errors, and transaction models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts
from norad.contracts.scientific_evidence import review_package
from norad.libraries.source_authority import ArtifactSourceRoot, SourceCheckout
from norad.reporting._artifact_index.api import RUN_CONTRACT_FIELDS
from norad.reporting._files import FileSnapshot

PRODUCER = "build_run_summary"
PRODUCER_VERSION = "1.1.0"
LEGACY_PRODUCER_VERSION = "1.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "1.1.0"
RUN_SUMMARY_TSV_SCHEMA_VERSION = "1.0.0"
QC_SUMMARY_TSV_SCHEMA_VERSION = "1.0.0"
RUN_SUMMARY_RECEIPT_SCHEMA_VERSION = "1.0.0"
REPORT_TABLE_APPROVALS_HEADER = (
    "run_id",
    "run_contract_sha256",
    "table_id",
    "artifact_id",
    "role",
    "title",
    "path",
    "sha256",
    "row_count",
    "display_row_limit",
    "approval_status",
    "approval_policy_version",
    "approved_by",
    "approved_at",
)

REPORT_ROLE_ADAPTERS = {
    role: f"step09c_{role}_v1" for role in review_package.REPORT_TABLE_ROLES
}

RUN_SUMMARY_HEADER = (
    "run_id",
    "run_contract_sha256",
    "summary_state",
    "science_status",
    "artifact_order",
    "scope_order",
    "step_id",
    "scope_type",
    "scope_id",
    "artifact_id",
    "adapter",
    "required",
    "availability_status",
    "completion_status",
    "rollup_state",
    *contracts.RUN_SUMMARY_STATUS_FIELDS,
    "source_path",
    "source_sha256",
    "source_row_count",
    "selected_attempt_id",
    "warning_count",
    "error_count",
)

QC_SUMMARY_HEADER = (
    "run_id",
    "artifact_order",
    "metric_order",
    "step_id",
    "scope_type",
    "scope_id",
    "artifact_id",
    "metric_id",
    "name",
    "value",
    "value_type",
    "unit",
    "status",
    "source_artifact_id",
)

RUN_SUMMARY_RECEIPT_HEADER = (
    "run_id",
    *RUN_CONTRACT_FIELDS,
    "artifact_receipt_path",
    "artifact_receipt_sha256",
    "artifact_adapter_attempt_id",
    "inventory_path",
    "inventory_sha256",
    "inventory_row_count",
    "artifacts_index_path",
    "artifacts_index_sha256",
    "artifact_record_count",
    "record_set_sha256",
    "run_summary_schema_version",
    "run_summary_tsv_schema_version",
    "qc_summary_tsv_schema_version",
    "run_summary_receipt_schema_version",
    "run_summary_json_path",
    "run_summary_json_sha256",
    "run_summary_json_size_bytes",
    "run_summary_tsv_path",
    "run_summary_tsv_sha256",
    "run_summary_tsv_row_count",
    "qc_summary_tsv_path",
    "qc_summary_tsv_sha256",
    "qc_summary_tsv_row_count",
    "science_review_summary_path",
    "science_review_summary_sha256",
    "summary_state",
    "science_status",
    "published_output_count",
    "run_summary_attempt_id",
    "supersedes_run_summary_attempt_id",
    "run_summary_attempt_history",
    "producer",
    "producer_version",
    "git_commit",
    "started_at",
    "finished_at",
    "transaction_state",
)


class RunSummaryError(RuntimeError):
    """Raised when a run summary cannot be built or safely published."""


@dataclass(frozen=True)
class OutputPaths:
    output_dir: Path
    output_dir_device: int
    output_dir_inode: int
    summary_json: Path
    summary_tsv: Path
    qc_summary: Path
    receipt: Path
    lock: Path

    @property
    def ordered_outputs(self) -> tuple[Path, ...]:
        return (
            self.summary_json,
            self.summary_tsv,
            self.qc_summary,
            self.receipt,
        )


@dataclass
class BuildContext:
    run_id: str
    execute: bool
    artifact_receipt_path: Path
    artifact_receipt: dict[str, str]
    run_contract_path: Path
    run_contract_file_sha256: str
    run_contract: dict[str, Any]
    inventory_path: Path
    inventory_sha256: str
    inventory_rows: list[dict[str, str]]
    artifacts_path: Path
    records_dir: Path
    input_snapshots: tuple[FileSnapshot, ...]
    artifacts: list[dict[str, Any]]
    science_review_summary_path: Path | None
    science_review_summary_sha256: str | None
    report_table_approvals_path: Path | None
    report_table_approvals_sha256: str | None
    report_table_snapshots: tuple[FileSnapshot, ...]
    document: dict[str, Any]
    summary_json_bytes: bytes
    summary_rows: list[dict[str, Any]]
    summary_tsv_bytes: bytes
    qc_summary_bytes: bytes
    paths: OutputPaths
    previous_receipt: dict[str, str] | None
    previous_receipt_sha256: str | None
    previous_attempt_id: str | None
    attempt_id: str
    git_commit: str
    receipt_row: dict[str, Any]
    receipt_bytes: bytes
    source_checkout: SourceCheckout = field(
        kw_only=True,
        compare=False,
        repr=False,
    )
    artifact_source_root: ArtifactSourceRoot = field(
        kw_only=True,
        compare=False,
        repr=False,
    )
