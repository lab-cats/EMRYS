"""Artifact-record semantic validation."""

from __future__ import annotations

from typing import Any

from .core import (
    ContractValidationError,
    require_unique_key,
    resolve_contract_path,
    validate_attempt_graph,
    validate_computational_statuses,
    validate_document_paths,
    validate_run_contract,
)

_SELECTED_ATTEMPT_STATE_BY_COMPLETION = {
    "complete": "succeeded",
    "failed": "failed",
    "in_progress": "running",
}
_INCOMPLETE_SELECTED_ATTEMPT_STATES = {"failed", "cancelled", "blocked"}


def validate_artifact_semantics(document: dict[str, Any]) -> None:
    artifact_label = f"artifact {document['artifact_id']!r}"
    validate_run_contract(
        document["run_contract"],
        artifact_label,
    )
    validate_document_paths(document)
    attempts = document["attempts"]
    attempt_index = validate_attempt_graph(
        attempts,
        selected_attempt_id=document["selected_attempt_id"],
        label=artifact_label,
    )
    selected_attempt_id = document["selected_attempt_id"]
    if selected_attempt_id is not None:
        selected = attempt_index[selected_attempt_id]
        superseded_ids = {
            attempt["supersedes_attempt_id"]
            for attempt in attempts
            if attempt["supersedes_attempt_id"] is not None
        }
        if selected_attempt_id in superseded_ids:
            raise ContractValidationError(
                f"{artifact_label} selected attempt has been superseded"
            )
        completion = document["completion_status"]
        if (
            completion == "incomplete"
            and selected["state"] not in _INCOMPLETE_SELECTED_ATTEMPT_STATES
        ):
            raise ContractValidationError(
                f"{artifact_label} incomplete state "
                "must select a failed, cancelled, or blocked attempt"
            )
        if (
            expected_state := _SELECTED_ATTEMPT_STATE_BY_COMPLETION.get(completion)
        ) is not None and selected["state"] != expected_state:
            raise ContractValidationError(
                f"{artifact_label} {completion.replace('_', '-')} state "
                f"must select a {expected_state} attempt"
            )

    validate_computational_statuses(
        label=artifact_label,
        local_testing=document["local_testing"],
        runtime_validation=document["runtime_validation"],
        cluster_validation=document["cluster_validation"],
    )

    members = document["members"]
    require_unique_key(members, "member_id", "artifact members")
    expected_source_path = resolve_contract_path(document["expectation"]["source_path"])
    canonical_member_paths = {
        resolve_contract_path(member["path"]) for member in members
    }
    if len(canonical_member_paths) != len(members):
        raise ContractValidationError("artifact members contain duplicate paths")
    source = document["source"]
    if source is not None and (
        source["path"] != document["expectation"]["source_path"]
    ):
        raise ContractValidationError(
            "artifact source path does not match its explicit inventory expectation"
        )
    if source is None and expected_source_path in canonical_member_paths:
        raise ContractValidationError(
            "artifact member cannot claim the absent expected source path"
        )
    if source is not None:
        source_path = resolve_contract_path(source["path"])
        source_member = next(
            (
                member
                for member in members
                if resolve_contract_path(member["path"]) == source_path
            ),
            None,
        )
        if source_member is not None:
            for field in ("sha256", "size_bytes", "row_count", "media_type"):
                if source.get(field) != source_member.get(field):
                    raise ContractValidationError(
                        f"artifact source and same-path member disagree on {field}"
                    )

    completion = document["completion_status"]
    if completion != "complete" and not document["state_reason"].strip():
        raise ContractValidationError(
            "non-complete artifact state_reason must contain non-whitespace text"
        )
    if completion == "failed" and not document["errors"]:
        raise ContractValidationError("failed artifact must record at least one error")
    if completion == "incomplete" and not (document["warnings"] or document["errors"]):
        raise ContractValidationError(
            "incomplete artifact must record at least one warning or error"
        )
