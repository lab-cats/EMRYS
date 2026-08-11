"""Explicit scientific-review reconciliation for Step 09c outputs."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

from .contracts import contracts, review_package, step08
from .models import (
    SHA256_RE,
    STEP09C_CATEGORY_ADAPTERS,
    ArtifactIndexError,
    Inspection,
)
from .reconcile_native import NativeSourceIndex, native_int, require_referenced_source


def split_native_safe_ids(value: str, field_name: str) -> list[str]:
    if value == step08.NA_VALUE:
        return []
    values = value.split(",")
    if (
        any(not item or item.strip() != item for item in values)
        or len(values) != len(set(values))
        or any(not contracts.SAFE_ID_RE.fullmatch(item) for item in values)
    ):
        raise ArtifactIndexError(
            f"Step 09c {field_name} is not a unique comma-separated safe-ID list"
        )
    return values


def _allowed_analysis_ids(plan_row: Mapping[str, str]) -> set[str]:
    return {
        plan_row["primary_analysis_id"],
        *split_native_safe_ids(
            plan_row["superseded_analysis_ids"], "superseded_analysis_ids"
        ),
        *split_native_safe_ids(
            plan_row["sensitivity_analysis_ids"], "sensitivity_analysis_ids"
        ),
    }


def _require_review_identity(
    row: Mapping[str, str],
    summary_row: Mapping[str, str],
    allowed_analysis_ids: set[str],
) -> None:
    if (
        row.get("review_id") != summary_row["review_id"]
        or row.get("analysis_id") not in allowed_analysis_ids
    ):
        raise ArtifactIndexError(
            "Step 09c review identity is outside the declared review"
        )


def validate_step09c_evidence_index(
    evidence_rows: Sequence[Mapping[str, str]],
    plan_row: Mapping[str, str],
    summary_row: Mapping[str, str],
) -> dict[str, str]:
    if not evidence_rows:
        raise ArtifactIndexError("Step 09c evidence index is empty")
    allowed_analysis_ids = _allowed_analysis_ids(plan_row)
    seen_evidence_ids: set[str] = set()
    category_order = {
        category: index
        for index, category in enumerate(review_package.ALLOWED_EVIDENCE_CATEGORIES)
    }
    observed_order: list[tuple[int, str]] = []
    for row in evidence_rows:
        evidence_id = row["evidence_id"]
        category = row["evidence_category"]
        status = row["evidence_status"]
        if (
            not contracts.SAFE_ID_RE.fullmatch(evidence_id)
            or evidence_id in seen_evidence_ids
        ):
            raise ArtifactIndexError("Step 09c evidence IDs must be unique safe IDs")
        seen_evidence_ids.add(evidence_id)
        if category not in review_package.ALLOWED_EVIDENCE_CATEGORIES:
            raise ArtifactIndexError(
                f"Step 09c evidence category is invalid: {category!r}"
            )
        if status not in review_package.EVIDENCE_STATUSES:
            raise ArtifactIndexError(f"Step 09c evidence status is invalid: {status!r}")
        _require_review_identity(row, summary_row, allowed_analysis_ids)
        observed_order.append((category_order[category], evidence_id))
        if status in {"missing", "not_applicable"}:
            if any(
                row[field_name] != step08.NA_VALUE
                for field_name in (
                    "source_path",
                    "declared_sha256",
                    "observed_sha256",
                    "declared_row_count",
                    "observed_row_count",
                )
            ):
                raise ArtifactIndexError(
                    "Step 09c missing/not-applicable evidence must use NA "
                    "for source path, hashes, and row counts"
                )
            if (
                status == "missing" and row["not_applicable_reason"] != step08.NA_VALUE
            ) or (
                status == "not_applicable"
                and row["not_applicable_reason"] in {"", step08.NA_VALUE}
            ):
                raise ArtifactIndexError(
                    "Step 09c evidence not-applicable reason is inconsistent"
                )
        else:
            if (
                row["source_path"] == step08.NA_VALUE
                or row["not_applicable_reason"] != step08.NA_VALUE
                or not SHA256_RE.fullmatch(row["declared_sha256"])
                or row["declared_sha256"] != row["observed_sha256"]
                or native_int(row, "declared_row_count")
                != native_int(row, "observed_row_count")
            ):
                raise ArtifactIndexError(
                    "Step 09c complete/incomplete evidence source metadata "
                    "does not reconcile"
                )
            if status == "complete" and native_int(row, "observed_row_count") == 0:
                raise ArtifactIndexError(
                    "Step 09c complete evidence must contain at least one row; "
                    "use not_applicable for a justified empty category"
                )
    if observed_order != sorted(observed_order):
        raise ArtifactIndexError(
            "Step 09c evidence index is not in canonical category/ID order"
        )
    missing_categories = [
        category
        for category in review_package.CATEGORY_ORDER
        if not any(row["evidence_category"] == category for row in evidence_rows)
    ]
    if missing_categories:
        raise ArtifactIndexError(
            "Step 09c evidence index omits required explicit categories: "
            + ", ".join(missing_categories)
        )
    for category in review_package.CATEGORY_ORDER:
        status = review_package.aggregate_evidence_status(evidence_rows, category)
        if summary_row[f"{category}_status"] != status:
            raise ArtifactIndexError(
                f"Step 09c summary {category}_status disagrees with evidence"
            )
    expected_source_count = sum(
        row["evidence_status"] in {"complete", "incomplete"} for row in evidence_rows
    )
    if native_int(summary_row, "evidence_source_count") != expected_source_count:
        raise ArtifactIndexError(
            "Step 09c summary evidence_source_count disagrees with evidence"
        )
    return {
        category: review_package.aggregate_evidence_status(evidence_rows, category)
        for category in review_package.ALLOWED_EVIDENCE_CATEGORIES
    }


def validate_step09c_payloads(
    *,
    by_adapter: Mapping[str, Inspection],
    evidence_rows: Sequence[Mapping[str, str]],
    plan_row: Mapping[str, str],
    summary_row: Mapping[str, str],
) -> None:
    allowed_analysis_ids = _allowed_analysis_ids(plan_row)
    evidence_by_category: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_category[row["evidence_category"]].append(row)
    for category, adapter_id in STEP09C_CATEGORY_ADAPTERS.items():
        member = by_adapter[adapter_id]
        payload_rows = member.native.get("rows", [])
        indexed_rows = evidence_by_category[category]
        indexed_by_id = {row["evidence_id"]: row for row in indexed_rows}
        expected_counts = {
            row["evidence_id"]: (
                native_int(row, "observed_row_count")
                if row["evidence_status"] in {"complete", "incomplete"}
                else 0
            )
            for row in indexed_rows
        }
        payload_counts = Counter(row["evidence_id"] for row in payload_rows)
        if payload_counts != Counter(expected_counts):
            raise ArtifactIndexError(
                f"Step 09c {category} payload row counts disagree with "
                "the evidence index"
            )
        expected_total = sum(expected_counts.values())
        observed_total = member.source["row_count"] if member.source else None
        if observed_total != expected_total:
            raise ArtifactIndexError(
                f"Step 09c {category} published row count disagrees with "
                "the evidence index"
            )
        for row in payload_rows:
            evidence = indexed_by_id.get(row["evidence_id"])
            if evidence is None:
                raise ArtifactIndexError(
                    f"Step 09c {category} payload identity is not declared "
                    "by the review/evidence index"
                )
            _require_review_identity(row, summary_row, allowed_analysis_ids)
            if (
                "primary_analysis_id" in row
                and row["primary_analysis_id"] != plan_row["primary_analysis_id"]
            ):
                raise ArtifactIndexError(
                    f"Step 09c {category} payload primary analysis is invalid"
                )


def validate_step09c_decisions(
    decision_rows: Sequence[Mapping[str, str]],
    summary_row: Mapping[str, str],
    *,
    require_complete: bool,
) -> dict[str, str]:
    seen: set[str] = set()
    decisions: dict[str, str] = {}
    for row in decision_rows:
        dimension = row["decision_dimension"]
        if (
            row["review_id"] != summary_row["review_id"]
            or dimension not in review_package.DECISION_DIMENSIONS
            or dimension in seen
            or row["evidence_status"] not in review_package.EVIDENCE_STATUSES
            or row["decision_status"] not in review_package.DECISION_STATUSES
        ):
            raise ArtifactIndexError(
                "Step 09c decision identity/status contract is invalid"
            )
        seen.add(dimension)
        if row["decision_status"] == "recorded":
            if row["decision_value"] in {"", step08.NA_VALUE} or row[
                "decision_date"
            ] in {"", step08.NA_VALUE}:
                raise ArtifactIndexError(
                    "Step 09c recorded decision lacks a value or date"
                )
            decisions[dimension] = row["decision_value"]
        else:
            if (
                row["decision_value"] != step08.NA_VALUE
                or row["decision_date"] != step08.NA_VALUE
            ):
                raise ArtifactIndexError(
                    "Step 09c pending decision must use NA value/date"
                )
            decisions[dimension] = "pending"
    if require_complete and (
        seen != set(review_package.DECISION_DIMENSIONS)
        or any(value == "pending" for value in decisions.values())
    ):
        raise ArtifactIndexError(
            "Step 09c completed science state lacks complete decisions"
        )
    summary_fields = {
        "background": "background_decision",
        "matched_dna": "matched_dna_decision",
        "orthogonal_evidence": "orthogonal_evidence_decision",
        "annotation": "annotation_decision",
        "thresholds": "thresholds_decision",
        "adjudication": "adjudication_decision",
        "orientation": "orientation_decision",
    }
    for dimension, field_name in summary_fields.items():
        if summary_row[field_name] != decisions.get(dimension, "pending"):
            raise ArtifactIndexError(
                f"Step 09c summary {field_name} disagrees with decisions"
            )
    return decisions


def step09c_candidate_keys(
    rows: Sequence[Mapping[str, str]],
    label: str,
) -> set[tuple[str, str]]:
    keys = {(row["analysis_id"], row["candidate_id"]) for row in rows}
    if len(keys) != len(rows):
        raise ArtifactIndexError(
            f"Step 09c {label} contains duplicate candidate identities"
        )
    return keys


def reconcile_step09c(
    members: Sequence[Inspection],
    sources: NativeSourceIndex,
) -> None:
    by_adapter = {member.row["adapter"]: member for member in members}
    plan = by_adapter["step09c_review_plan_v1"]
    summary = by_adapter["step09c_review_summary_v1"]
    plan_row = plan.first_row or {}
    summary_row = summary.first_row or {}
    for field_name in review_package.REVIEW_PLAN_HEADER:
        if summary_row.get(field_name) != plan_row.get(field_name):
            raise ArtifactIndexError(
                f"Step 09c summary disagrees with review plan: {field_name}"
            )
    if native_int(summary_row, "published_output_count") != len(
        review_package.OUTPUT_SUFFIXES
    ):
        raise ArtifactIndexError("Step 09c published_output_count is inconsistent")
    if summary_row.get("transaction_state") != "complete":
        raise ArtifactIndexError("Step 09c summary transaction_state is not complete")
    status_contracts = {
        "implementation_status": review_package.IMPLEMENTATION_STATUSES,
        "local_test_status": review_package.LOCAL_TEST_STATUSES,
        "runtime_validation_status": review_package.RUNTIME_VALIDATION_STATUSES,
        "cluster_dry_run_status": review_package.CLUSTER_DRY_RUN_STATUSES,
        "cluster_proof_status": review_package.CLUSTER_PROOF_STATUSES,
        "orientation_status": review_package.ORIENTATION_STATUSES,
    }
    for field_name, allowed in status_contracts.items():
        if summary_row.get(field_name) not in allowed:
            raise ArtifactIndexError(f"Step 09c summary {field_name} is invalid")
    for category in review_package.CATEGORY_ORDER:
        field_name = f"{category}_status"
        if summary_row.get(field_name) not in review_package.EVIDENCE_STATUSES:
            raise ArtifactIndexError(f"Step 09c summary {field_name} is invalid")
    for prefix in (
        "sample_manifest",
        "partition_manifest",
        "evidence_manifest",
    ):
        if not summary_row.get(f"{prefix}_path"):
            raise ArtifactIndexError(f"Step 09c summary {prefix}_path is empty")
        if not SHA256_RE.fullmatch(summary_row.get(f"{prefix}_sha256", "")):
            raise ArtifactIndexError(f"Step 09c summary {prefix}_sha256 is invalid")
        native_int(summary_row, f"{prefix}_row_count")
    if native_int(summary_row, "evidence_source_count") > native_int(
        summary_row, "evidence_record_count"
    ):
        raise ArtifactIndexError(
            "Step 09c evidence source count exceeds evidence record count"
        )
    count_bindings = (
        (
            "step09c_evidence_index_v1",
            "evidence_record_count",
        ),
        (
            "step09c_candidate_selection_v1",
            "selected_candidate_count",
        ),
        (
            "step09c_candidate_adjudication_v1",
            "adjudicated_candidate_count",
        ),
        (
            "step09c_limitations_v1",
            "limitation_count",
        ),
    )
    for adapter_id, field_name in count_bindings:
        member = by_adapter[adapter_id]
        if native_int(summary_row, field_name) != (
            member.source["row_count"] if member.source else None
        ):
            raise ArtifactIndexError(f"Step 09c summary {field_name} is inconsistent")
    evidence_rows = by_adapter["step09c_evidence_index_v1"].native.get(
        "rows",
        [],
    )
    if native_int(summary_row, "evidence_manifest_row_count") != len(evidence_rows):
        raise ArtifactIndexError(
            "Step 09c evidence manifest and evidence index row counts disagree"
        )
    category_statuses = validate_step09c_evidence_index(
        evidence_rows,
        plan_row,
        summary_row,
    )
    validate_step09c_payloads(
        by_adapter=by_adapter,
        evidence_rows=evidence_rows,
        plan_row=plan_row,
        summary_row=summary_row,
    )
    overall_status = summary_row.get("overall_science_status", "")
    exploratory_complete = overall_status == "science_review_complete_exploratory"
    decisions = validate_step09c_decisions(
        by_adapter["step09c_decisions_v1"].native.get("rows", []),
        summary_row,
        require_complete=exploratory_complete,
    )
    selected = step09c_candidate_keys(
        by_adapter["step09c_candidate_selection_v1"].native.get("rows", []),
        "candidate selection",
    )
    adjudicated = step09c_candidate_keys(
        by_adapter["step09c_candidate_adjudication_v1"].native.get("rows", []),
        "candidate adjudication",
    )
    if exploratory_complete:
        incomplete_categories = {
            category: category_statuses[category]
            for category in review_package.CATEGORY_ORDER
            if category_statuses[category] not in {"complete", "not_applicable"}
        }
        if incomplete_categories:
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state has incomplete evidence "
                f"categories: {incomplete_categories}"
            )
        if category_statuses["decisions"] != "complete":
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state lacks completed decisions"
            )
        if selected != adjudicated:
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state lacks complete "
                "candidate adjudication coverage"
            )
        if summary_row.get("review_completed_date") == step08.NA_VALUE:
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state lacks a completion date"
            )
    elif summary_row.get("review_completed_date") != step08.NA_VALUE:
        raise ArtifactIndexError(
            "Step 09c evidence-incomplete state must not claim a completion date"
        )
    orientation_status = summary_row.get("orientation_status")
    if orientation_status != "provisional" and (
        category_statuses["orientation_locus_audit"] != "complete"
        or category_statuses["decisions"] != "complete"
        or decisions.get("orientation") != orientation_status
    ):
        raise ArtifactIndexError(
            "Step 09c non-provisional orientation status lacks complete "
            "orientation evidence and a matching recorded decision"
        )
    if (
        summary_row.get("cluster_proof_status") == "proven"
        and category_statuses["computational_validation"] != "complete"
    ):
        raise ArtifactIndexError(
            "Step 09c cluster proof lacks complete computational evidence"
        )
    input_bindings = (
        ("step08_sites", "step08_sites_v1"),
        ("step08_inputs", "step08_inputs_v1"),
        ("step08_summary", "step08_summary_v1"),
        ("step09_all_sites", "step09_cmh_all_sites_v1"),
        (
            "step09_significant_sites",
            "step09_cmh_significant_sites_v1",
        ),
        ("step09_summary", "step09_cmh_summary_v1"),
        (
            "step09_mutation_spectrum",
            "step09_mutation_spectrum_tsv_v1",
        ),
        (
            "step09_mutation_spectrum_pdf",
            "step09_mutation_spectrum_pdf_v1",
        ),
        ("step09_depth_delta_pdf", "step09_depth_delta_pdf_v1"),
        ("review_plan", "step09c_review_plan_v1"),
    )
    for prefix, adapter_id in input_bindings:
        target = require_referenced_source(
            row=summary_row,
            path_field=f"{prefix}_path",
            hash_field=f"{prefix}_sha256",
            row_count_field=f"{prefix}_row_count",
            sources=sources,
        )
        if target.row["adapter"] != adapter_id:
            raise ArtifactIndexError(
                f"Step 09c {prefix}_path points to the wrong adapter"
            )
