"""Shared run-summary constants, errors, and transaction models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts
from emrys.libraries.source_authority import ArtifactSourceRoot, SourceCheckout
from emrys.reporting._artifact_index.api import RUN_CONTRACT_FIELDS
from emrys.reporting._files import FileSnapshot

PRODUCER = "build_run_summary"
PRODUCER_VERSION = "2.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "2.0.0"
MODULE_PRODUCER_VERSION = "3.0.0"
MODULE_RUN_SUMMARY_SCHEMA_VERSION = "3.0.0"
RUN_SUMMARY_TSV_SCHEMA_VERSION = "2.0.0"
QC_SUMMARY_TSV_SCHEMA_VERSION = "1.0.0"
RUN_SUMMARY_RECEIPT_SCHEMA_VERSION = "2.0.0"
INTERPRETATION_BOUNDARY = (
    "computational_candidates_only_biological_validation_outside_emrys"
)

RUN_SUMMARY_HEADER = (
    "run_id",
    "run_contract_sha256",
    "summary_state",
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
    "summary_state",
    "interpretation_boundary",
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
    analysis_policy_path: Path | None
    analysis_policy: dict[str, Any] | None
    input_snapshots: tuple[FileSnapshot, ...]
    artifacts: list[dict[str, Any]]
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
