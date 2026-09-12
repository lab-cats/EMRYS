"""Shared run-summary constants, errors, and transaction models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from emrys.reporting._artifact_index.models import RUN_CONTRACT_FIELDS

PRODUCER = "build_run_summary"
PRODUCER_VERSION = "7.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "7.0.0"

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
    "source_path",
    "source_sha256",
    "source_row_count",
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


class RunSummaryError(RuntimeError):
    """Raised when a run summary cannot be built or safely published."""


@dataclass(frozen=True)
class OutputPaths:
    output_dir: Path
    summary_json: Path
    summary_tsv: Path
    qc_summary: Path

    @property
    def ordered_outputs(self) -> tuple[Path, ...]:
        return (
            self.summary_tsv,
            self.qc_summary,
            self.summary_json,
        )
