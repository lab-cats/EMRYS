"""Scientific-review-record semantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import (
    SCIENCE_INPUT_ROLES,
    SCIENCE_UPSTREAM_ROLE_CONTRACTS,
    ContractValidationError,
    require_unique_key,
    validate_computational_statuses,
    validate_document_paths,
    validate_run_contract,
)


def validate_scientific_review_semantics(document: dict[str, Any]) -> None:
    validate_run_contract(
        document["run_contract"],
        f"scientific review {document['review_id']!r}",
    )
    validate_document_paths(document)
    computational_status = document["computational_status"]
    validate_computational_statuses(
        label=f"scientific review {document['review_id']!r}",
        local_testing={
            "status": computational_status["local_test_status"],
            "evidence": computational_status["evidence"],
        },
        runtime_validation={
            "status": computational_status["runtime_validation_status"],
            "detail": (
                "Scientific runtime validation is blocked."
                if computational_status["runtime_validation_status"] == "blocked"
                else None
            ),
            "evidence": computational_status["evidence"],
        },
        cluster_validation={
            "dry_run_status": computational_status["cluster_dry_run_status"],
            "proof_status": computational_status["cluster_proof_status"],
            "evidence": computational_status["evidence"],
        },
        allow_shared_evidence_ids=True,
    )

    primary_analysis_id = document["primary_analysis_id"]
    superseded_analysis_ids = set(document["superseded_analysis_ids"])
    sensitivity_analysis_ids = set(document["sensitivity_analysis_ids"])
    if primary_analysis_id in superseded_analysis_ids | sensitivity_analysis_ids:
        raise ContractValidationError(
            "scientific review primary analysis cannot also be superseded "
            "or sensitivity analysis"
        )
    overlapping_alternates = superseded_analysis_ids & sensitivity_analysis_ids
    if overlapping_alternates:
        raise ContractValidationError(
            "scientific review superseded and sensitivity analysis IDs "
            "overlap: " + ", ".join(sorted(overlapping_alternates))
        )
    allowed_analysis_ids = {
        primary_analysis_id,
        *superseded_analysis_ids,
        *sensitivity_analysis_ids,
    }

    evidence_index = require_unique_key(
        document["evidence_records"],
        "evidence_id",
        "scientific evidence records",
    )
    evidence_ids = set(evidence_index)
    for evidence_id, record in evidence_index.items():
        if record["analysis_id"] not in allowed_analysis_ids:
            raise ContractValidationError(
                f"scientific evidence {evidence_id!r} names undeclared "
                f"analysis {record['analysis_id']!r}"
            )

    computational_evidence_ids = {
        reference["evidence_id"] for reference in computational_status["evidence"]
    }
    unknown_computational = sorted(computational_evidence_ids - evidence_ids)
    if unknown_computational:
        raise ContractValidationError(
            "scientific computational status references unknown evidence IDs: "
            + ", ".join(unknown_computational)
        )
    computational_reference_keys: set[tuple[str, str]] = set()
    for reference in computational_status["evidence"]:
        reference_key = (reference["evidence_id"], reference["role"])
        if reference_key in computational_reference_keys:
            raise ContractValidationError(
                "scientific computational evidence repeats evidence_id/role: "
                + "/".join(reference_key)
            )
        computational_reference_keys.add(reference_key)
        record = evidence_index[reference["evidence_id"]]
        if (
            record["category"] != "computational_validation"
            or record["status"] != "complete"
            or record["source"] is None
        ):
            raise ContractValidationError(
                f"scientific computational evidence "
                f"{reference['evidence_id']!r} must resolve to one complete "
                "computational_validation record"
            )

    # Every computational_validation record is owned by the independent
    # computational-status panel. Only complete records that directly support
    # a declared status are promoted into its typed evidence references; any
    # incomplete, missing, or not-applicable declarations remain explicit in
    # evidence_records without becoming proof.
    referenced_evidence_ids = {
        evidence_id
        for evidence_id, record in evidence_index.items()
        if record["category"] == "computational_validation"
    }
    for category_name, category in document["evidence_categories"].items():
        referenced_ids = category["evidence_ids"]
        unknown = sorted(set(referenced_ids) - evidence_ids)
        if unknown:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} references "
                "unknown evidence IDs: " + ", ".join(unknown)
            )
        records = [evidence_index[evidence_id] for evidence_id in referenced_ids]
        mismatched_categories = [
            record["evidence_id"]
            for record in records
            if record["category"] != category_name
        ]
        if mismatched_categories:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} references "
                "records assigned to another category: "
                + ", ".join(mismatched_categories)
            )
        if category_name in {"sensitivity_matrix", "leave_one_pair_out"}:
            allowed_category_analysis_ids = {
                primary_analysis_id,
                *sensitivity_analysis_ids,
            }
        else:
            allowed_category_analysis_ids = {primary_analysis_id}
        wrong_category_analyses = [
            record["evidence_id"]
            for record in records
            if record["analysis_id"] not in allowed_category_analysis_ids
        ]
        if wrong_category_analyses:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} references "
                "evidence for an analysis not allowed by that category: "
                + ", ".join(wrong_category_analyses)
            )
        referenced_evidence_ids.update(referenced_ids)
        status = category["status"]
        if status in {"complete", "incomplete"} and not records:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} status "
                f"{status!r} requires at least one evidence record"
            )
        if status == "complete" and (
            any(
                record["status"] not in {"complete", "not_applicable"}
                for record in records
            )
            or not any(record["status"] == "complete" for record in records)
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is complete "
                "without at least one complete record or contains missing/"
                "incomplete evidence"
            )
        if status == "incomplete" and not any(
            record["status"] in {"missing", "incomplete"} for record in records
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is incomplete "
                "without missing or incomplete evidence"
            )
        if status == "not_applicable" and any(
            record["status"] != "not_applicable" for record in records
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is "
                "not_applicable but references applicable evidence"
            )
        if status == "missing" and any(
            record["status"] != "missing" for record in records
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is missing "
                "but references non-missing evidence"
            )
    for decision_name, decision in document["decisions"].items():
        unknown = sorted(set(decision["evidence_ids"]) - evidence_ids)
        if unknown:
            raise ContractValidationError(
                f"scientific decision {decision_name!r} references unknown "
                "evidence IDs: " + ", ".join(unknown)
            )
        referenced_evidence_ids.update(decision["evidence_ids"])
        if decision["status"] == "recorded" and not decision["evidence_ids"]:
            raise ContractValidationError(
                f"scientific decision {decision_name!r} is recorded without "
                "supporting evidence"
            )
        if decision["status"] == "recorded" and any(
            evidence_index[evidence_id]["status"] not in {"complete", "not_applicable"}
            for evidence_id in decision["evidence_ids"]
        ):
            raise ContractValidationError(
                f"scientific decision {decision_name!r} cites missing or "
                "incomplete evidence"
            )
    orientation_decision = document["decisions"]["orientation"]
    if (
        orientation_decision["status"] == "recorded"
        and orientation_decision["value"]
        != document["scientific_state"]["orientation_status"]
    ):
        raise ContractValidationError(
            "recorded orientation decision value must match "
            "scientific_state.orientation_status"
        )

    input_index = require_unique_key(
        document["input_artifacts"],
        "role",
        "scientific review input artifacts",
    )
    observed_roles = set(input_index)
    if observed_roles != SCIENCE_INPUT_ROLES:
        missing = sorted(SCIENCE_INPUT_ROLES - observed_roles)
        extra = sorted(observed_roles - SCIENCE_INPUT_ROLES)
        details: list[str] = []
        if missing:
            details.append("missing roles: " + ", ".join(missing))
        if extra:
            details.append("unknown roles: " + ", ".join(extra))
        raise ContractValidationError(
            "scientific review input artifact roles must match the complete "
            "Step 09c provenance set; " + "; ".join(details)
        )
    require_unique_key(
        document["input_artifacts"],
        "artifact_id",
        "scientific review input artifacts",
    )
    require_unique_key(
        document["limitations"],
        "limitation_id",
        "scientific review limitations",
    )
    for limitation in document["limitations"]:
        referenced_evidence_ids.update(limitation["evidence_ids"])
    orphan_evidence = sorted(evidence_ids - referenced_evidence_ids)
    if orphan_evidence:
        raise ContractValidationError(
            "scientific evidence records must be referenced by computational "
            "status, a category, a decision, or a limitation: "
            + ", ".join(orphan_evidence)
        )
    if (
        document["primary_analysis_id"]
        != document["run_contract"]["primary_analysis_id"]
    ):
        raise ContractValidationError(
            "scientific review primary_analysis_id does not match its "
            "immutable run contract"
        )
    input_paths = [record["path"] for record in document["input_artifacts"]]
    if len(input_paths) != len(set(input_paths)):
        raise ContractValidationError(
            "scientific review input artifact paths must be unique"
        )
    pdf_input_roles = {
        "step09_mutation_spectrum_pdf",
        "step09_depth_delta_pdf",
    }
    for role, record in input_index.items():
        suffix = Path(record["path"]).suffix.lower()
        expected = ".pdf" if role in pdf_input_roles else ".tsv"
        expected_is_na = role in pdf_input_roles
        if suffix != expected or (record["row_count"] is None) != expected_is_na:
            raise ContractValidationError(
                f"scientific review tabular input role {role!r} must use a "
                f"{expected} path and {'NA' if expected_is_na else 'non-null'} row_count"
            )
        role_contract = SCIENCE_UPSTREAM_ROLE_CONTRACTS.get(role)
        if role_contract is not None and not Path(record["path"]).name.endswith(
            role_contract[3]
        ):
            raise ContractValidationError(
                f"scientific review input role {role!r} path must end with "
                f"{role_contract[3]!r}"
            )
    if (
        input_index["sample_manifest"]["sha256"]
        != document["run_contract"]["sample_manifest_sha256"]
    ):
        raise ContractValidationError(
            "sample_manifest input hash does not match the run contract"
        )
    if (
        input_index["partition_manifest"]["sha256"]
        != document["run_contract"]["partition_manifest_sha256"]
    ):
        raise ContractValidationError(
            "partition_manifest input hash does not match the run contract"
        )
