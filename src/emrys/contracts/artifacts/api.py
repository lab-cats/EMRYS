"""Curated artifact-contract API shared by reporting owners."""

from __future__ import annotations

from typing import Any

from ._artifact_contracts.artifact import validate_artifact_semantics
from ._artifact_contracts.definitions import (
    INVENTORY_HEADER,
    REPO_ROOT,
    RUN_CONTRACT_COMPONENT_FIELDS,
    SAFE_ID_RE,
    ContractValidationError,
)
from ._artifact_contracts.identity import (
    resolve_contract_path,
    validate_resolved_path,
    validate_run_contract,
)
from ._artifact_contracts.inventory import (
    reconcile_artifact_inventory_row,
    reconcile_document_inventory,
    validate_inventory,
)
from ._artifact_contracts.report_receipt import (
    validate_report_receipt_semantics,
)
from ._artifact_contracts.run_summary_status import (
    RUN_SUMMARY_STATUS_FIELDS,
    aggregate_artifact_state,
    aggregate_equal_or_mixed,
    artifact_rollup_state,
    artifact_status_dimensions,
    scope_key,
)
from ._artifact_contracts.run_summary_validation import (
    validate_run_summary_semantics,
)
from ._artifact_contracts.schema import (
    format_json_path,
    load_json_object,
    load_schema_registry,
    reject_duplicate_json_keys,
    reject_nonstandard_json_constant,
    schema_errors,
    schema_validator,
    sha256_file,
)

__all__ = (
    "INVENTORY_HEADER",
    "REPO_ROOT",
    "RUN_CONTRACT_COMPONENT_FIELDS",
    "RUN_SUMMARY_STATUS_FIELDS",
    "SAFE_ID_RE",
    "ContractValidationError",
    "aggregate_artifact_state",
    "aggregate_equal_or_mixed",
    "artifact_rollup_state",
    "artifact_status_dimensions",
    "format_json_path",
    "load_json_object",
    "load_schema_registry",
    "reconcile_artifact_inventory_row",
    "reconcile_document_inventory",
    "reject_duplicate_json_keys",
    "reject_nonstandard_json_constant",
    "resolve_contract_path",
    "schema_errors",
    "schema_validator",
    "scope_key",
    "sha256_file",
    "validate_artifact_semantics",
    "validate_document_semantics",
    "validate_inventory",
    "validate_report_receipt_semantics",
    "validate_resolved_path",
    "validate_run_contract",
    "validate_run_summary_semantics",
)


def validate_document_semantics(name: str, document: dict[str, Any]) -> None:
    """Validate the semantic contract for one named schema document."""

    validators = {
        "artifact-record": validate_artifact_semantics,
        "run-summary": validate_run_summary_semantics,
        "report-receipt": validate_report_receipt_semantics,
    }
    if (validator := validators.get(name)) is not None:
        validator(document)
