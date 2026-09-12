"""Artifact source and completion semantics."""

from __future__ import annotations

from typing import Any

from .definitions import ContractValidationError
from .identity import validate_document_paths


def validate_artifact_semantics(document: dict[str, Any]) -> None:
    validate_document_paths(document)
    source = document["source"]
    if source is not None and (
        source["path"] != document["expectation"]["source_path"]
    ):
        raise ContractValidationError(
            "artifact source path does not match its explicit inventory expectation"
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
