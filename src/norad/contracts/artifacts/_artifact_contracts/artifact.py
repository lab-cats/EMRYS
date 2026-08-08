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


def validate_artifact_semantics(document: dict[str, Any]) -> None:
    validate_run_contract(
        document["run_contract"],
        f"artifact {document['artifact_id']!r}",
    )
    validate_document_paths(document)
    attempts = document["attempts"]
    attempt_index = validate_attempt_graph(
        attempts,
        selected_attempt_id=document["selected_attempt_id"],
        label=f"artifact {document['artifact_id']!r}",
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
                f"artifact {document['artifact_id']!r} selected attempt "
                "has been superseded"
            )
        completion = document["completion_status"]
        if completion == "complete" and selected["state"] != "succeeded":
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} complete state "
                "must select a succeeded attempt"
            )
        if completion == "failed" and selected["state"] != "failed":
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} failed state "
                "must select a failed attempt"
            )
        if completion == "in_progress" and selected["state"] != "running":
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} in-progress state "
                "must select a running attempt"
            )
        if completion == "incomplete" and selected["state"] not in {
            "failed",
            "cancelled",
            "blocked",
        }:
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} incomplete state "
                "must select a failed, cancelled, or blocked attempt"
            )

    validate_computational_statuses(
        label=f"artifact {document['artifact_id']!r}",
        local_testing=document["local_testing"],
        runtime_validation=document["runtime_validation"],
        cluster_validation=document["cluster_validation"],
    )

    members = document["members"]
    require_unique_key(members, "member_id", "artifact members")
    member_paths = [member["path"] for member in members]
    canonical_member_paths = [resolve_contract_path(path) for path in member_paths]
    if len(canonical_member_paths) != len(set(canonical_member_paths)):
        raise ContractValidationError("artifact members contain duplicate paths")
    if document["source"] is not None and (
        document["source"]["path"] != document["expectation"]["source_path"]
    ):
        raise ContractValidationError(
            "artifact source path does not match its explicit inventory expectation"
        )
    if (
        document["source"] is None
        and resolve_contract_path(document["expectation"]["source_path"])
        in canonical_member_paths
    ):
        raise ContractValidationError(
            "artifact member cannot claim the absent expected source path"
        )
    if document["source"] is not None:
        matching_members = [
            member
            for member in members
            if resolve_contract_path(member["path"])
            == resolve_contract_path(document["source"]["path"])
        ]
        if matching_members:
            member = matching_members[0]
            for field in ("sha256", "size_bytes", "row_count", "media_type"):
                if document["source"].get(field) != member.get(field):
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
