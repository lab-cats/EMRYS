"""Artifact-contract locations, vocabularies, and error identity."""

from __future__ import annotations

import re
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve()

REPO_ROOT = _MODULE_PATH.parents[5]
SCHEMA_ROOT = _MODULE_PATH.parents[2] / "schemas" / "artifacts"
COMMON_SCHEMA_PATH = SCHEMA_ROOT / "v1" / "common.schema.json"
SCHEMA_FILES = {
    "artifact-record": SCHEMA_ROOT / "v2" / "artifact_record.schema.json",
    "run-summary": SCHEMA_ROOT / "v2" / "run_summary.schema.json",
    "report-receipt": SCHEMA_ROOT / "v3" / "report_receipt.schema.json",
}
INVENTORY_HEADER = (
    "artifact_id",
    "step_id",
    "scope_type",
    "scope_id",
    "adapter",
    "source_path",
    "required",
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BOOLEAN_VALUES = {"true", "false"}
SCOPE_TYPES = {
    "reference",
    "sample",
    "cohort_partition",
    "cohort",
    "analysis",
}
RUN_CONTRACT_COMPONENT_FIELDS = (
    "sample_manifest_sha256",
    "reference_contract_sha256",
    "partition_manifest_sha256",
    "primary_analysis_id",
    "primary_analysis_policy_sha256",
)
COMPUTATIONAL_STATUS_ROLE_REQUIREMENTS = {
    "local testing": {
        "passed": {"local_test"},
        "failed": {"local_test"},
    },
    "runtime validation": {
        "passed": {"runtime_log", "runtime_output"},
        "failed": {"runtime_log"},
    },
}
CLUSTER_VALIDATION_REQUIREMENTS = (
    (
        "cluster dry-run validation",
        "dry_run_status",
        {"passed", "failed"},
        {"cluster_dry_run"},
    ),
    (
        "cluster proof",
        "proof_status",
        {"proven"},
        {"cluster_scheduler", "cluster_log", "cluster_output"},
    ),
    ("failed cluster proof", "proof_status", {"failed"}, {"cluster_log"}),
)
CLUSTER_VALIDATION_TRIGGER_STATUSES = {"passed", "failed", "proven"}


class ContractValidationError(RuntimeError):
    """Raised when a schema, record, or inventory contract is invalid."""
