"""Constants owned by the Step 09c scientific-review package."""

from __future__ import annotations

__all__ = ("EVIDENCE_MANIFEST_HEADER", "COMPUTATIONAL_VALIDATION_STATUSES")

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

COMPUTATIONAL_VALIDATION_STATUSES = (
    "not_run",
    "blocked",
    "passed",
    "failed",
    "proven",
)
