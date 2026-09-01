"""Artifact-index constants and immutable build models."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from emrys.contracts.artifacts import api as contracts
from emrys.libraries.alignments.orientation import COUNTS_HEADER as STEP06_COUNTS_HEADER
from emrys.libraries.alignments.star import REQUIRED_INDEX_MEMBERS as STEP00A_BASENAMES
from emrys.libraries.validation.mpileup import RECEIPT_HEADER as STEP07_RECEIPT_HEADER
from emrys.libraries.validation.report import HEADER as VALIDATION_REPORT_HEADER

if TYPE_CHECKING:
    from emrys.libraries.source_authority import ArtifactSourceRoot, SourceCheckout

PRODUCER = "build_artifact_index"
PRODUCER_VERSION = "2.0.0"
ARTIFACT_SCHEMA_VERSION = "2.0.0"
ARTIFACT_INDEX_SCHEMA_VERSION = "2.0.0"
ARTIFACT_RECEIPT_SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RUN_CONTRACT_FIELDS = ("run_contract_sha256", *contracts.RUN_CONTRACT_COMPONENT_FIELDS)
ANCHOR_HASH_FIELDS = (
    "sample_manifest_sha256",
    "partition_manifest_sha256",
)
ARTIFACT_INDEX_HEADER = (
    "run_id",
    "run_contract_sha256",
    *contracts.INVENTORY_HEADER,
    "availability_status",
    "completion_status",
    "attempt_provenance_status",
    "selected_attempt_id",
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
    "source_sha256",
    "source_size_bytes",
    "source_row_count",
    "source_media_type",
    "warning_count",
    "error_count",
    "record_path",
    "record_sha256",
    "record_schema_version",
)

ARTIFACT_RECEIPT_HEADER = (
    "run_id",
    "run_contract_sha256",
    "run_contract_path",
    "run_contract_file_sha256",
    *contracts.RUN_CONTRACT_COMPONENT_FIELDS,
    "inventory_path",
    "inventory_sha256",
    "inventory_row_count",
    "artifact_schema_version",
    "artifact_index_schema_version",
    "artifact_receipt_schema_version",
    "artifacts_index_path",
    "artifacts_index_sha256",
    "artifact_record_count",
    "record_set_sha256",
    "required_artifact_count",
    "required_missing_artifact_count",
    "present_artifact_count",
    "missing_artifact_count",
    "externally_unavailable_artifact_count",
    "unknown_artifact_count",
    "complete_artifact_count",
    "not_attempted_artifact_count",
    "in_progress_artifact_count",
    "incomplete_artifact_count",
    "failed_artifact_count",
    "warning_count",
    "error_count",
    "published_output_count",
    "adapter_attempt_id",
    "supersedes_adapter_attempt_id",
    "adapter_attempt_history",
    "producer",
    "producer_version",
    "git_commit",
    "started_at",
    "finished_at",
    "transaction_state",
)


class ArtifactIndexError(RuntimeError):
    """Raised when the explicit adapter/index contract cannot be honored."""


@dataclass(frozen=True)
class AdapterSpec:
    adapter_id: str
    step_id: str
    scope_type: str
    kind: str
    media_type: str
    source_path_template: str | None = None
    suffixes: tuple[str, ...] = ()
    basenames: tuple[str, ...] = ()
    expected_header: tuple[str, ...] | None = None
    exact_data_rows: int | None = None
    allow_header_only: bool = True


@dataclass(frozen=True)
class SourceSnapshot:
    status: str
    sha256: str | None
    size_bytes: int | None
    file_type: str
    link_target: str | None = None
    device: int | None = None
    inode: int | None = None
    mtime_ns: int | None = None
    ctime_ns: int | None = None


@dataclass(frozen=True)
class LockOwnership:
    device: int
    inode: int
    run_token: str


@dataclass
class Inspection:
    row: dict[str, str]
    spec: AdapterSpec
    resolved_path: Path
    availability_status: str
    completion_status: str
    state_reason: str | None
    attempt_provenance_status: str
    source: dict[str, Any] | None
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    native: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    first_row: dict[str, str] | None = None
    snapshot: SourceSnapshot | None = None


@dataclass
class BuildContext:
    source_checkout: SourceCheckout
    artifact_source_root: ArtifactSourceRoot
    run_id: str
    run_contract_path: Path
    run_contract: dict[str, Any]
    run_contract_file_sha256: str
    analysis_policy_path: Path | None
    analysis_policy_sha256: str | None
    inventory_path: Path
    inventory_sha256: str
    inventory_rows: list[dict[str, str]]
    output_dir: Path
    records_dir: Path
    artifacts_path: Path
    receipt_path: Path
    lock_path: Path
    inspections: list[Inspection]
    records: list[dict[str, Any]]
    record_bytes: list[bytes]
    index_rows: list[dict[str, str]]
    index_bytes: bytes
    receipt_row: dict[str, str]
    receipt_bytes: bytes
    attempt_id: str
    previous_attempt_id: str | None
    attempt_history: list[str]
    previous_receipt: dict[str, str] | None
    source_identity_observer: Callable[..., str | None]
