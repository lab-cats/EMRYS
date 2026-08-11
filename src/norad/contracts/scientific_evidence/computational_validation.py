"""Shared computational-validation evidence contract."""

from __future__ import annotations

SCOPE_ROLES = {
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
SCOPE_PLAN_FIELDS = {
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
HEADER = (
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
