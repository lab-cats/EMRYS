"""Current Run manifest schema, inventory and semantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts

from .models import RunSummaryError


def _validate_document(
    document: dict[str, Any],
    inventory_rows: list[dict[str, str]],
    inventory_path: Path,
    *,
    source_root: Path,
) -> None:
    errors = sorted(
        contracts.schema_validator("run-summary").iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        details = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise RunSummaryError(
            f"Run summary failed Draft 2020-12 validation:\n{details}"
        )
    try:
        contracts.validate_run_summary_semantics(
            document,
            source_root=source_root,
        )
        contracts.reconcile_document_inventory(
            "run-summary",
            document,
            inventory_rows,
            inventory_path,
            source_root=source_root,
        )
    except contracts.ContractValidationError as exc:
        raise RunSummaryError(f"Run summary failed semantic validation: {exc}")
