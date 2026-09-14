"""Artifact records, deterministic indexes, identities, and receipts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from emrys.libraries.validation.tsv import tsv_bytes as render_tsv_bytes

from .core import safe_tsv
from .models import Inspection


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
        "source": inspection.source,
        "parameters": inspection.parameters,
        "metrics": inspection.metrics,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
    }


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    return render_tsv_bytes(
        header,
        ({field: safe_tsv(row[field]) for field in header} for row in rows),
    )
