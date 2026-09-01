"""Artifact-contract locations, vocabularies, and error identity."""

from __future__ import annotations

from pathlib import Path

from emrys.contracts.artifacts import (
    INVENTORY_HEADER,
    SAFE_ID_RE,
    ContractValidationError,
    scope_key,
)

_MODULE_PATH = Path(__file__).resolve()

REPO_ROOT = _MODULE_PATH.parents[5]
SCHEMA_ROOT = _MODULE_PATH.parents[2] / "schemas" / "artifacts"
COMMON_SCHEMA_PATH = SCHEMA_ROOT / "v1" / "common.schema.json"
SCHEMA_FILES = {
    "artifact-record": SCHEMA_ROOT / "v2" / "artifact_record.schema.json",
    "run-summary": SCHEMA_ROOT / "v2" / "run_summary.schema.json",
    "report-receipt": SCHEMA_ROOT / "v4" / "report_receipt.schema.json",
}
VERSIONED_SCHEMA_FILES = {
    ("run-summary", "3.0.0"): SCHEMA_ROOT / "v3" / "run_summary.schema.json",
    ("report-receipt", "5.0.0"): SCHEMA_ROOT / "v5" / "report_receipt.schema.json",
}
CROSS_SCHEMA_FILES = {
    "orchestration-common": (
        SCHEMA_ROOT.parent / "orchestration" / "v1" / "common.schema.json"
    ),
    "analysis-policy": (
        SCHEMA_ROOT.parent / "orchestration" / "v1" / "policy.schema.json"
    ),
}
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
