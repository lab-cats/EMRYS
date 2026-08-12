"""Artifact-contract locations, vocabularies, and error identity."""

from __future__ import annotations

import re
from pathlib import Path

from norad.contracts.scientific_evidence import review_package

_MODULE_PATH = Path(__file__).resolve()

REPO_ROOT = _MODULE_PATH.parents[5]
SCHEMA_ROOT = _MODULE_PATH.parents[2] / "schemas" / "artifacts" / "v1"
REPORT_RECEIPT_SCHEMA_PATH = (
    _MODULE_PATH.parents[2]
    / "schemas"
    / "artifacts"
    / "v2"
    / "report_receipt.schema.json"
)
COMMON_SCHEMA_PATH = SCHEMA_ROOT / "common.schema.json"
SCHEMA_FILES = {
    "artifact-record": SCHEMA_ROOT / "artifact_record.schema.json",
    "scientific-review-record": SCHEMA_ROOT / "scientific_review_record.schema.json",
    "run-summary": SCHEMA_ROOT / "run_summary.schema.json",
    "report-receipt": REPORT_RECEIPT_SCHEMA_PATH,
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
    "scientific_review",
}
SCIENCE_INPUT_ROLES = set(review_package.INPUT_ARTIFACT_ROLES.values())
SCIENCE_UPSTREAM_ROLE_CONTRACTS = {
    "step08_sites": ("08", "cohort", "step08_sites_v1", ".step08_sites.tsv"),
    "step08_inputs": ("08", "cohort", "step08_inputs_v1", ".step08_inputs.tsv"),
    "step08_summary": (
        "08",
        "cohort",
        "step08_summary_v1",
        ".step08_summary.tsv",
    ),
    "step09_all_sites": (
        "09",
        "analysis",
        "step09_cmh_all_sites_v1",
        ".cmh_all_sites.tsv",
    ),
    "step09_significant_sites": (
        "09",
        "analysis",
        "step09_cmh_significant_sites_v1",
        ".cmh_significant_sites.tsv",
    ),
    "step09_summary": (
        "09",
        "analysis",
        "step09_cmh_summary_v1",
        ".cmh_summary.tsv",
    ),
    "step09_mutation_spectrum_tsv": (
        "09",
        "analysis",
        "step09_mutation_spectrum_tsv_v1",
        ".mutation_spectrum.tsv",
    ),
    "step09_mutation_spectrum_pdf": (
        "09",
        "analysis",
        "step09_mutation_spectrum_pdf_v1",
        ".mutation_spectrum.pdf",
    ),
    "step09_depth_delta_pdf": (
        "09",
        "analysis",
        "step09_depth_delta_pdf_v1",
        ".depth_delta.pdf",
    ),
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
