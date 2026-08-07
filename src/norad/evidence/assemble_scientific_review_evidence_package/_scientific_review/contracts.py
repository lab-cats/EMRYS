"""Exact neutral contract owners and retained Step 09c constants."""

from __future__ import annotations

from norad.contracts.scientific_evidence import review_package, step08, step09


if step09.step08 is not step08:
    raise ImportError("Step 09c and Step 09 resolved different Step 08 objects")
if step09.ContractError is not step08.ContractError or step09.Table is not step08.Table:
    raise ImportError("Step 09 contract resolved different shared identities")


ContractError = step08.ContractError
NA_VALUE = step08.NA_VALUE
COMPUTATIONAL_SCOPE_ROLES = {
    "local_fixture_tests": "local_test",
    "local_test": "local_test",
    "runtime_validation": "runtime_output",
    "runtime_log": "runtime_log",
    "runtime_output": "runtime_output",
    "cluster_dry_run": "cluster_dry_run",
    "cluster_proof": "cluster_output",
    "cluster_scheduler": "cluster_scheduler",
    "cluster_log": "cluster_log",
    "cluster_output": "cluster_output",
}
COMPUTATIONAL_SCOPE_PLAN_FIELDS = {
    "local_fixture_tests": "local_test_status",
    "local_test": "local_test_status",
    "runtime_validation": "runtime_validation_status",
    "runtime_log": "runtime_validation_status",
    "runtime_output": "runtime_validation_status",
    "cluster_dry_run": "cluster_dry_run_status",
    "cluster_proof": "cluster_proof_status",
    "cluster_scheduler": "cluster_proof_status",
    "cluster_log": "cluster_proof_status",
    "cluster_output": "cluster_proof_status",
}

EVIDENCE_MANIFEST_HEADER = (
    "evidence_id",
    "evidence_category",
    "analysis_id",
    "source_path",
    "source_sha256",
    "source_row_count",
    "evidence_status",
    "not_applicable_reason",
    "reviewer",
    "owner",
    "evidence_date",
    "policy_version",
)

COMPUTATIONAL_VALIDATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "validation_scope",
    "validation_status",
    "evidence_path",
    "evidence_sha256",
    "scheduler_state",
    "exit_code",
    "reviewer",
    "evidence_date",
    "notes",
)

COMPUTATIONAL_VALIDATION_STATUSES = (
    "not_run",
    "blocked",
    "passed",
    "failed",
    "proven",
)


Table = step08.Table
values_close = step08.values_close
sha256_file = step08.sha256_file
read_tsv = step08.read_tsv
resolve_recorded_path = step09.resolve_recorded_path
