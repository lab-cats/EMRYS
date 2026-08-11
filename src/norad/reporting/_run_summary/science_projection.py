"""Normalize one committed Step 09c package into its public science record."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts
from norad.contracts.scientific_evidence import review_package
from norad.reporting._run_summary.science_evidence import (
    _normalize_evidence,
    _normalize_input_artifacts,
)
from norad.reporting._run_summary.science_io import (
    _confirm_inputs_unchanged,
    _read_tsv,
    _require_regular_file,
    _resolve_recorded_path,
)
from norad.reporting._run_summary.science_models import (
    COMPUTATIONAL_SCOPE_PLAN_FIELDS,
    COMPUTATIONAL_SCOPE_ROLES,
    NA_VALUE,
    PRODUCER,
    PRODUCER_VERSION,
    SCIENCE_SCHEMA_VERSION,
    ReviewPackageContext,
    RunSummaryScienceError,
    _artifact_source,
    _fail,
    _nullable,
    _split_ids,
)
from norad.reporting._run_summary.science_package import (
    _read_committed_review_package,
    _validate_published_artifacts,
    _validate_summary_artifact,
)


def _validate_computational_payload_status(
    *,
    evidence_id: str,
    validation_scope: str,
    validation_status: str,
    plan: Mapping[str, str],
) -> None:
    plan_field = COMPUTATIONAL_SCOPE_PLAN_FIELDS[validation_scope]
    expected = plan[plan_field]
    if validation_status != expected:
        _fail(
            f"Computational evidence {evidence_id} scope "
            f"{validation_scope} status "
            f"{validation_status!r} does not exactly support the declared "
            f"{plan_field} {expected!r}."
        )


def _normalize_computational_evidence(
    *,
    context: ReviewPackageContext,
    evidence_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    record_index = {record["evidence_id"]: record for record in evidence_records}
    rows_by_evidence: dict[str, list[dict[str, str]]] = {}
    for row in context.category_rows["computational_validation"]:
        rows_by_evidence.setdefault(row["evidence_id"], []).append(row)

    references: list[dict[str, str]] = []
    computational_rows = [
        row
        for row in context.evidence_index_rows
        if row["evidence_category"] == "computational_validation"
    ]
    for index_row in computational_rows:
        evidence_id = index_row["evidence_id"]
        if index_row["evidence_status"] != "complete":
            continue
        payload_rows = rows_by_evidence.get(evidence_id, [])
        if not payload_rows:
            _fail(
                f"Computational evidence {evidence_id} must contain at least "
                "one validation_scope row."
            )
        record = record_index[evidence_id]
        wrapper_source = record["source"]
        if not isinstance(wrapper_source, Mapping):
            _fail(f"Computational evidence {evidence_id} has no source descriptor.")
        for payload in payload_rows:
            validation_scope = payload["validation_scope"]
            role = COMPUTATIONAL_SCOPE_ROLES[validation_scope]
            _validate_computational_payload_status(
                evidence_id=evidence_id,
                validation_scope=validation_scope,
                validation_status=payload["validation_status"],
                plan=context.plan,
            )
            if payload["evidence_path"] == NA_VALUE:
                evidence_path = wrapper_source["path"]
                evidence_sha256 = wrapper_source["sha256"]
            else:
                evidence_path_object = _require_regular_file(
                    f"Computational payload {evidence_id} {validation_scope}",
                    _resolve_recorded_path(payload["evidence_path"]),
                )
                evidence_path = str(evidence_path_object)
                evidence_sha256 = payload["evidence_sha256"]
                if contracts.sha256_file(evidence_path_object) != evidence_sha256:
                    _fail(
                        f"Computational payload {evidence_id} "
                        f"{validation_scope} hash changed during "
                        "normalization."
                    )
            references.append(
                {
                    "evidence_id": evidence_id,
                    "role": role,
                    "path": evidence_path,
                    "sha256": evidence_sha256,
                }
            )
    return references


def _normalize_decisions(
    context: ReviewPackageContext,
) -> dict[str, dict[str, Any]]:
    by_dimension = {
        row["decision_dimension"]: row for row in context.category_rows["decisions"]
    }
    decisions: dict[str, dict[str, Any]] = {}
    for dimension in review_package.DECISION_DIMENSIONS:
        row = by_dimension.get(dimension)
        if row is None or row["decision_status"] == "pending":
            if row is not None and row["supporting_evidence_ids"] != NA_VALUE:
                _fail(
                    f"Pending decision {dimension} cannot carry supporting "
                    "evidence IDs in scientific-review-record v1."
                )
            decisions[dimension] = {
                "status": "pending",
                "value": None,
                "detail": None if row is None else row["rationale"],
                "reviewer": (None if row is None else row["decision_owner"]),
                "decision_date": None,
                "evidence_ids": [],
                "rerun_scope": "none" if row is None else row["rerun_scope"],
                "decision_id": (None if row is None else row["decision_id"]),
                "source_evidence_id": (None if row is None else row["evidence_id"]),
                "evidence_status": (None if row is None else row["evidence_status"]),
                "policy_version": (None if row is None else row["policy_version"]),
                "rerun_required": (
                    None if row is None else row["rerun_required"] == "TRUE"
                ),
            }
            continue
        decisions[dimension] = {
            "status": "recorded",
            "value": row["decision_value"],
            "detail": row["rationale"],
            "reviewer": row["decision_owner"],
            "decision_date": row["decision_date"],
            "evidence_ids": _split_ids(row["supporting_evidence_ids"]),
            "rerun_scope": row["rerun_scope"],
            "decision_id": row["decision_id"],
            "source_evidence_id": row["evidence_id"],
            "evidence_status": row["evidence_status"],
            "policy_version": row["policy_version"],
            "rerun_required": row["rerun_required"] == "TRUE",
        }
    return decisions


def _normalize_limitations(
    context: ReviewPackageContext,
) -> list[dict[str, Any]]:
    statuses = {
        "active": "open",
        "open": "open",
        "accepted": "accepted",
        "resolved": "resolved",
    }
    limitations: list[dict[str, Any]] = []
    for row in context.category_rows["limitations"]:
        status = statuses.get(row["limitation_status"])
        if status is None:
            _fail(
                f"Limitation {row['limitation_id']} has unsupported status "
                f"{row['limitation_status']!r}."
            )
        limitations.append(
            {
                "limitation_id": row["limitation_id"],
                "status": status,
                "description": row["description"],
                "impact": row["impact"],
                "category": row["limitation_category"],
                "severity": row["severity"],
                "mitigation": row["mitigation"],
                "owner": row["owner"],
                "review_date": row["review_date"],
                "evidence_ids": _split_ids(row["related_evidence_ids"]),
            }
        )
    return limitations


def _validate_normalized_record(document: dict[str, Any]) -> None:
    try:
        errors = contracts.schema_errors("scientific-review-record", document)
        if errors:
            details = "\n".join(
                f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
                for error in errors
            )
            _fail(
                "Normalized Step 09c scientific review failed its Draft "
                f"2020-12 schema:\n{details}"
            )
        contracts.validate_scientific_review_semantics(document)
    except contracts.ContractValidationError as exc:
        _fail(
            f"Normalized Step 09c scientific review failed semantic validation: {exc}"
        )


def normalize_scientific_review(
    *,
    summary_path: Path,
    artifacts: list[dict[str, Any]],
    run_id: str,
    run_contract: Mapping[str, Any],
    generated_at: str,
    git_commit: str,
) -> dict[str, Any]:
    """Revalidate and normalize one explicit committed Step 09c transaction."""

    try:
        normalized_summary_path = _require_regular_file(
            "Explicit Step 09c review summary", summary_path
        )
        summary_table = _read_tsv(
            "Explicit Step 09c review summary",
            normalized_summary_path,
            review_package.REVIEW_SUMMARY_HEADER,
        )
        if len(summary_table.rows) != 1:
            _fail("The explicit Step 09c review summary must contain one row.")
        summary_row = summary_table.rows[0]
        if summary_row["transaction_state"] != "complete":
            _fail("The explicit Step 09c review summary is not committed.")
        if summary_row["published_output_count"] != str(
            len(review_package.OUTPUT_SUFFIXES)
        ):
            _fail("The Step 09c review summary does not declare 13 outputs.")
        if summary_row["overall_science_status"] == "biological_interpretation_ready":
            _fail(
                "biological_interpretation_ready is reserved and cannot be "
                "normalized by scientific-review-record v1."
            )
        if summary_row["overall_science_status"] not in {
            "evidence_incomplete",
            "science_review_complete_exploratory",
        }:
            _fail(
                "The Step 09c review summary declares an unsupported science "
                f"state: {summary_row['overall_science_status']!r}."
            )
        if summary_row["primary_analysis_id"] != run_contract.get(
            "primary_analysis_id"
        ):
            _fail(
                "The Step 09c primary analysis differs from the immutable run contract."
            )
        summary_sha256 = contracts.sha256_file(normalized_summary_path)
        summary_artifact = _validate_summary_artifact(
            summary_path=normalized_summary_path,
            artifacts=artifacts,
            summary_row=summary_row,
            summary_sha256=summary_sha256,
        )

        context, output_tables = _read_committed_review_package(
            summary_path=normalized_summary_path,
            summary_row=summary_row,
        )
        _validate_published_artifacts(
            summary_path=normalized_summary_path,
            summary_row=summary_row,
            artifacts=artifacts,
            summary_artifact=summary_artifact,
            output_tables=output_tables,
        )
        input_artifacts = _normalize_input_artifacts(
            context=context,
            artifacts=artifacts,
            review_id=summary_row["review_id"],
            run_contract=run_contract,
        )
        evidence_categories, evidence_records = _normalize_evidence(context)
        computational_evidence = _normalize_computational_evidence(
            context=context,
            evidence_records=evidence_records,
        )
        summary_source = _artifact_source(
            summary_artifact, label="Step 09c review summary"
        )
        document: dict[str, Any] = {
            "schema_name": "norad.scientific_review_record",
            "schema_version": SCIENCE_SCHEMA_VERSION,
            "record_type": "scientific_review_record",
            "run_id": run_id,
            "run_contract": dict(run_contract),
            "review_id": summary_row["review_id"],
            "primary_analysis_id": summary_row["primary_analysis_id"],
            "superseded_analysis_ids": _split_ids(
                summary_row["superseded_analysis_ids"]
            ),
            "sensitivity_analysis_ids": _split_ids(
                summary_row["sensitivity_analysis_ids"]
            ),
            "review_metadata": {
                "plan_version": summary_row["plan_version"],
                "plan_date": summary_row["plan_date"],
                "reviewer": summary_row["reviewer"],
                "decision_owner": summary_row["decision_owner"],
                "git_commit": summary_row["git_commit"],
                "review_completed_date": _nullable(
                    summary_row["review_completed_date"]
                ),
            },
            "computational_status": {
                "implementation_status": summary_row["implementation_status"],
                "local_test_status": summary_row["local_test_status"],
                "runtime_validation_status": summary_row["runtime_validation_status"],
                "cluster_dry_run_status": summary_row["cluster_dry_run_status"],
                "cluster_proof_status": summary_row["cluster_proof_status"],
                "evidence": computational_evidence,
            },
            "scientific_state": {
                "overall_status": summary_row["overall_science_status"],
                "orientation_status": summary_row["orientation_status"],
                "orientation_policy": summary_row["orientation_policy"],
                "orientation_policy_version": summary_row["orientation_policy_version"],
            },
            "readiness_authorization": None,
            "policy_versions": {
                "locus_selection": summary_row["locus_selection_policy_version"],
                "candidate_selection": summary_row[
                    "candidate_selection_policy_version"
                ],
                "sensitivity": summary_row["sensitivity_policy_version"],
                "background": summary_row["background_policy_version"],
                "annotation": summary_row["annotation_policy_version"],
                "adjudication": summary_row["adjudication_policy_version"],
            },
            "selection_rules": {
                "locus_selection": summary_row["locus_selection_rule"],
                "candidate_selection": summary_row["candidate_selection_rule"],
                "sensitivity": summary_row["sensitivity_rule"],
                "leave_one_pair_out": summary_row["leave_one_pair_out_rule"],
            },
            "evidence_categories": evidence_categories,
            "evidence_records": evidence_records,
            "decisions": _normalize_decisions(context),
            "input_artifacts": input_artifacts,
            "review_summary": {
                "path": summary_source["path"],
                "sha256": summary_sha256,
                "size_bytes": summary_source["size_bytes"],
                "row_count": 1,
                "media_type": "text/tab-separated-values",
            },
            "limitations": _normalize_limitations(context),
            "warnings": [],
            "errors": [],
            "provenance": {
                "producer": PRODUCER,
                "producer_version": PRODUCER_VERSION,
                "git_commit": git_commit,
                "created_at": generated_at,
            },
        }
        _confirm_inputs_unchanged(context.input_hashes)
        _validate_normalized_record(document)
        return document
    except RunSummaryScienceError:
        raise
    except contracts.ContractValidationError as exc:
        raise RunSummaryScienceError(
            f"Artifact-contract validation failed during normalization: {exc}"
        ) from exc
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RunSummaryScienceError(
            f"Could not normalize the Step 09c scientific review: {exc}"
        ) from exc
