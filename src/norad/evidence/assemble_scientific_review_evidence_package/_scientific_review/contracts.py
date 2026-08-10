"""Exact neutral contract owners and retained Step 09c constants."""

from __future__ import annotations

from norad.contracts.scientific_evidence import (
    computational_validation,
    step08,
    step09,
)

if step09.step08 is not step08:
    raise ImportError("Step 09c and Step 09 resolved different Step 08 objects")
if step09.ContractError is not step08.ContractError or step09.Table is not step08.Table:
    raise ImportError("Step 09 contract resolved different shared identities")


ContractError = step08.ContractError
NA_VALUE = step08.NA_VALUE
Table = step08.Table
values_close = step08.values_close
sha256_file = step08.sha256_file
read_tsv = step08.read_tsv
COMPUTATIONAL_SCOPE_ROLES = computational_validation.SCOPE_ROLES
COMPUTATIONAL_SCOPE_PLAN_FIELDS = computational_validation.SCOPE_PLAN_FIELDS

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

COMPUTATIONAL_VALIDATION_HEADER = computational_validation.HEADER

COMPUTATIONAL_VALIDATION_STATUSES = (
    "not_run",
    "blocked",
    "passed",
    "failed",
    "proven",
)


resolve_recorded_path = step09.resolve_recorded_path
