"""Normalize indexed inputs and evidence from a committed review package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts
from norad.contracts.scientific_evidence import review_package
from norad.reporting._run_summary.transaction import _path_hash

from .science_io import _require_regular_file
from .science_models import (
    INPUT_ROLE_BY_STEP09C_KEY,
    ReviewInput,
    ReviewPackageContext,
    _artifact_scope,
    _artifact_source,
    _fail,
    _nullable,
    _parse_row_count,
)


def _match_upstream_artifact(
    *,
    role: str,
    step09c_artifact: ReviewInput,
    artifacts: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    step_id, scope_type, adapter, suffix = contracts.SCIENCE_UPSTREAM_ROLE_CONTRACTS[
        role
    ]
    expected_row_count = _parse_row_count(
        f"Step 09c {role} row count", step09c_artifact.row_count
    )
    matches: list[Mapping[str, Any]] = []
    for artifact in artifacts:
        scope = _artifact_scope(artifact)
        if (
            scope[0] != step_id
            or scope[1] != scope_type
            or artifact.get("adapter") != adapter
            or artifact.get("completion_status") != "complete"
        ):
            continue
        source = artifact.get("source")
        if not isinstance(source, Mapping):
            continue
        source_value = source.get("path")
        if not isinstance(source_value, str):
            continue
        if not Path(source_value).name.endswith(suffix):
            continue
        indexed_path = contracts.resolve_contract_path(source_value)
        if indexed_path != step09c_artifact.path:
            continue
        if (
            source.get("sha256") != step09c_artifact.sha256
            or source.get("row_count") != expected_row_count
        ):
            continue
        matches.append(artifact)
    if len(matches) != 1:
        _fail(
            f"Scientific input role {role} must match exactly one complete "
            f"indexed Step {step_id} artifact; observed {len(matches)}."
        )
    return matches[0]


def _normalize_input_artifacts(
    *,
    context: ReviewPackageContext,
    artifacts: Sequence[Mapping[str, Any]],
    review_id: str,
    run_contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key in review_package.INPUT_ARTIFACT_KEYS:
        source_artifact = context.artifacts[key]
        role = INPUT_ROLE_BY_STEP09C_KEY[key]
        row_count = _parse_row_count(
            f"Step 09c input {role} row count", source_artifact.row_count
        )
        if role in contracts.SCIENCE_UPSTREAM_ROLE_CONTRACTS:
            indexed = _match_upstream_artifact(
                role=role,
                step09c_artifact=source_artifact,
                artifacts=artifacts,
            )
            artifact_id = indexed.get("artifact_id")
            if not isinstance(artifact_id, str):
                _fail(f"Indexed scientific input {role} has no artifact_id.")
            source = _artifact_source(indexed, label=f"Indexed scientific input {role}")
            normalized_path = source.get("path")
            if not isinstance(normalized_path, str):
                _fail(f"Indexed scientific input {role} has no source path.")
        else:
            artifact_id = f"input.{review_id}.{role}"
            normalized_path = str(source_artifact.path)
        result.append(
            {
                "role": role,
                "artifact_id": artifact_id,
                "path": normalized_path,
                "sha256": source_artifact.sha256,
                "row_count": row_count,
            }
        )
    input_index = {record["role"]: record for record in result}
    if input_index["sample_manifest"]["sha256"] != run_contract.get(
        "sample_manifest_sha256"
    ):
        _fail("Step 09c sample-manifest hash differs from the run contract.")
    if input_index["partition_manifest"]["sha256"] != run_contract.get(
        "partition_manifest_sha256"
    ):
        _fail("Step 09c partition-manifest hash differs from the run contract.")
    return result


def _normalize_evidence(
    context: ReviewPackageContext,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    represented_ids: set[str] = set()
    for row in context.evidence_index_rows:
        status = row["evidence_status"]
        evidence_date = _nullable(row["evidence_date"])
        if evidence_date is None and status in ("complete", "incomplete"):
            _fail(
                f"Evidence {row['evidence_id']} has no evidence_date and "
                f"cannot represent {status} evidence."
            )
        if status in ("complete", "incomplete"):
            path = _require_regular_file(
                f"Scientific evidence {row['evidence_id']}",
                row["source_path"],
            )
            row_count = _parse_row_count(
                f"Scientific evidence {row['evidence_id']} row count",
                row["observed_row_count"],
            )
            if row_count is None:
                _fail(f"Scientific evidence {row['evidence_id']} lacks a row count.")
            source = _path_hash(
                path,
                sha256=row["observed_sha256"],
                size_bytes=path.stat().st_size,
                row_count=row_count,
                media_type="text/tab-separated-values",
            )
        else:
            source = None
        records.append(
            {
                "evidence_id": row["evidence_id"],
                "category": row["evidence_category"],
                "analysis_id": row["analysis_id"],
                "status": status,
                "source": source,
                "reviewer": row["reviewer"],
                "owner": row["owner"],
                "evidence_date": evidence_date,
                "policy_version": row["policy_version"],
                "not_applicable_reason": (
                    row["not_applicable_reason"] if status == "not_applicable" else None
                ),
            }
        )
        represented_ids.add(row["evidence_id"])

    categories: dict[str, dict[str, Any]] = {}
    for category in review_package.CATEGORY_ORDER:
        rows = [
            row
            for row in context.evidence_index_rows
            if row["evidence_category"] == category
        ]
        status = review_package.aggregate_evidence_status(
            context.evidence_rows, category
        )
        reasons: list[str] = []
        if status == "not_applicable":
            for row in rows:
                reason = row["not_applicable_reason"]
                if reason not in reasons:
                    reasons.append(reason)
        categories[category] = {
            "status": status,
            "evidence_ids": [
                row["evidence_id"]
                for row in rows
                if row["evidence_id"] in represented_ids
            ],
            "not_applicable_reason": (
                "; ".join(reasons) if status == "not_applicable" else None
            ),
        }
    return categories, records
