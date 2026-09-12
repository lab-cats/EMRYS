"""Artifact records, deterministic indexes, identities, and receipts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from emrys.contracts.artifacts import api as contracts
from emrys.libraries.validation.tsv import tsv_bytes as render_tsv_bytes

from .core import safe_tsv
from .models import (
    ArtifactIndexError,
    Inspection,
)


def build_artifact_record(
    *,
    inspection: Inspection,
) -> dict[str, Any]:
    return {
        "artifact_id": inspection.row["artifact_id"],
        "scope": {
            "step_id": inspection.row["step_id"],
            "scope_type": inspection.row["scope_type"],
            "scope_id": inspection.row["scope_id"],
        },
        "adapter": inspection.row["adapter"],
        "expectation": {
            "required": inspection.row["required"] == "true",
            "source_path": inspection.row["source_path"],
        },
        "availability_status": inspection.availability_status,
        "completion_status": inspection.completion_status,
        "state_reason": inspection.state_reason,
        "attempt_provenance_status": inspection.attempt_provenance_status,
        "attempts": [],
        "selected_attempt_id": None,
        "local_testing": {"status": "not_run", "evidence": []},
        "runtime_validation": {
            "status": "not_run",
            "detail": None,
            "evidence": [],
        },
        "cluster_validation": {
            "dry_run_status": "not_run",
            "proof_status": "not_run",
            "evidence": [],
        },
        "source": inspection.source,
        "members": [],
        "tools": [],
        "parameters": inspection.parameters,
        "metrics": inspection.metrics,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
    }


def validate_record_in_memory(
    record: dict[str, Any],
    inventory_row: dict[str, str],
    validator: Draft202012Validator,
    *,
    source_root: Path,
) -> None:
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed schema:\n{detail}"
        )
    try:
        contracts.validate_artifact_semantics(record, source_root=source_root)
        contracts.reconcile_artifact_inventory_row(record, inventory_row)
    except contracts.ContractValidationError as exc:
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed semantic "
            f"validation: {exc}"
        ) from exc


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    return render_tsv_bytes(
        header,
        ({field: safe_tsv(row[field]) for field in header} for row in rows),
    )
