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
    from emrys.libraries.source_authority import ArtifactSourceRoot, InstalledPackage
    from emrys.reporting._run_summary.models import OutputPaths

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RUN_CONTRACT_FIELDS = ("run_contract_sha256", *contracts.RUN_CONTRACT_COMPONENT_FIELDS)
ANCHOR_HASH_FIELDS = ("sample_manifest_sha256", "partition_manifest_sha256")


class ArtifactIndexError(RuntimeError):
    """Raised when the explicit adapter/index contract cannot be honored."""


@dataclass(frozen=True)
class AdapterSpec:
    adapter_id: str
    step_id: str
    scope_type: str
    kind: str
    media_type: str
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


@dataclass
class Inspection:
    row: dict[str, str]
    spec: AdapterSpec
    resolved_path: Path
    availability_status: str
    completion_status: str
    state_reason: str | None
    source: dict[str, Any] | None
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    native: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    first_row: dict[str, str] | None = None
    snapshot: SourceSnapshot | None = None
    projection: object | None = None


@dataclass
class BuildContext:
    installed_package: InstalledPackage
    artifact_source_root: ArtifactSourceRoot
    scientific_origin: dict[str, Any]
    run_id: str
    profile_sha256: str
    run_contract_path: Path
    run_contract: dict[str, Any]
    run_contract_file_sha256: str
    analysis_policy_path: Path
    analysis_policy_binding: dict[str, Any]
    recheck_analysis_policy: Callable[[], None]
    inventory_path: Path
    inventory_sha256: str
    inventory_size_bytes: int
    recheck_contract_inputs: Callable[[], None]
    inventory_rows: list[dict[str, str]]
    output_dir: Path
    lock_path: Path
    inspections: list[Inspection]
    records: list[dict[str, Any]]
    attempt_id: str
    git_commit: str
    started_at: str
    finished_at: str
    source_identity_observer: Callable[..., InstalledPackage]


@dataclass(frozen=True)
class EvidenceContext:
    """One prepared index and its summary projections for exclusive publication."""

    index: BuildContext
    summary_paths: OutputPaths
    summary_document: dict[str, Any]
    summary_json_bytes: bytes
    summary_tsv_bytes: bytes
    qc_summary_bytes: bytes
