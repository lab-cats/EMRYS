#!/usr/bin/env python3
"""Validate NORAD artifact-schema-v1 JSON records and explicit inventories.

This command is read-only. It validates tracked JSON Schema documents, one
explicit JSON record at a time, and/or one explicit expected-artifact
inventory. It never searches for pipeline outputs or expands path globs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

src_root = str(Path(__file__).resolve().parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.contracts.artifacts._artifact_contracts import artifact as _artifact_owner
from norad.contracts.artifacts._artifact_contracts import core as _core_owner
from norad.contracts.artifacts._artifact_contracts import inventory as _inventory_owner
from norad.contracts.artifacts._artifact_contracts import (
    report_receipt as _report_receipt_owner,
)
from norad.contracts.artifacts._artifact_contracts import (
    run_summary as _run_summary_owner,
)
from norad.contracts.artifacts._artifact_contracts import (
    scientific_review as _scientific_review_owner,
)

REPO_ROOT = _core_owner.REPO_ROOT
SCHEMA_FILES = _core_owner.SCHEMA_FILES
SCHEMA_ROOT = _core_owner.SCHEMA_ROOT
COMMON_SCHEMA_PATH = _core_owner.COMMON_SCHEMA_PATH
INVENTORY_HEADER = _core_owner.INVENTORY_HEADER
SAFE_ID_RE = _core_owner.SAFE_ID_RE
BOOLEAN_VALUES = _core_owner.BOOLEAN_VALUES
SCOPE_TYPES = _core_owner.SCOPE_TYPES
SCIENCE_INPUT_ROLES = _core_owner.SCIENCE_INPUT_ROLES
SCIENCE_UPSTREAM_ROLE_CONTRACTS = _core_owner.SCIENCE_UPSTREAM_ROLE_CONTRACTS
RUN_CONTRACT_COMPONENT_FIELDS = _core_owner.RUN_CONTRACT_COMPONENT_FIELDS
ContractValidationError = _core_owner.ContractValidationError
reject_duplicate_json_keys = _core_owner.reject_duplicate_json_keys
reject_nonstandard_json_constant = _core_owner.reject_nonstandard_json_constant
load_json_object = _core_owner.load_json_object
load_schema_registry = _core_owner.load_schema_registry
schema_errors = _core_owner.schema_errors
schema_validator = _core_owner.schema_validator
validate_all_schemas = _core_owner.validate_all_schemas
sha256_file = _core_owner.sha256_file
format_json_path = _core_owner.format_json_path
validate_run_contract = _core_owner.validate_run_contract
canonical_run_contract_sha256 = _core_owner.canonical_run_contract_sha256
validate_resolved_path = _core_owner.validate_resolved_path
validate_document_paths = _core_owner.validate_document_paths
require_unique_key = _core_owner.require_unique_key
validate_attempt_graph = _core_owner.validate_attempt_graph
require_status_evidence = _core_owner.require_status_evidence
require_evidence_roles = _core_owner.require_evidence_roles
validate_evidence_references = _core_owner.validate_evidence_references
validate_computational_statuses = _core_owner.validate_computational_statuses
resolve_contract_path = _core_owner.resolve_contract_path
validate_artifact_semantics = _artifact_owner.validate_artifact_semantics
validate_scientific_review_semantics = (
    _scientific_review_owner.validate_scientific_review_semantics
)
artifact_rollup_state = _run_summary_owner.artifact_rollup_state
aggregate_artifact_state = _run_summary_owner.aggregate_artifact_state
artifact_status_dimensions = _run_summary_owner.artifact_status_dimensions
validate_run_summary_semantics = _run_summary_owner.validate_run_summary_semantics
aggregate_equal_or_mixed = _run_summary_owner.aggregate_equal_or_mixed
RUN_SUMMARY_STATUS_FIELDS = _run_summary_owner.RUN_SUMMARY_STATUS_FIELDS
scope_key = _run_summary_owner.scope_key
SAFE_ID_COLUMNS = _inventory_owner.SAFE_ID_COLUMNS
RECONCILE_FIELDS = _inventory_owner.RECONCILE_FIELDS
validate_safe_id = _inventory_owner.validate_safe_id
validate_explicit_source_path = _inventory_owner.validate_explicit_source_path
_reject_duplicate_inventory_value = _inventory_owner._reject_duplicate_inventory_value
validate_inventory = _inventory_owner.validate_inventory
expected_artifact_from_inventory_row = (
    _inventory_owner.expected_artifact_from_inventory_row
)
reconcile_artifact_inventory_row = _inventory_owner.reconcile_artifact_inventory_row
reconcile_document_inventory = _inventory_owner.reconcile_document_inventory
validate_report_receipt_semantics = (
    _report_receipt_owner.validate_report_receipt_semantics
)


if not (
    _artifact_owner.ContractValidationError is ContractValidationError
    and _scientific_review_owner.ContractValidationError is ContractValidationError
    and _run_summary_owner.ContractValidationError is ContractValidationError
):
    raise ImportError(
        "artifact-contract private modules did not resolve one error owner"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate artifact-schema-v1 schemas, a named JSON record, "
            "and/or an explicit expected-artifact inventory."
        )
    )
    parser.add_argument(
        "--check-schemas",
        action="store_true",
        help="Validate all four tracked schemas against Draft 2020-12.",
    )
    parser.add_argument(
        "--schema",
        choices=tuple(SCHEMA_FILES),
        help="Schema name for --document.",
    )
    parser.add_argument(
        "--document",
        type=Path,
        help="Explicit JSON document to validate.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Explicit expected-artifact inventory TSV to validate.",
    )
    args = parser.parse_args()

    if (args.schema is None) != (args.document is None):
        parser.error("--schema and --document must be supplied together")
    if not args.check_schemas and args.document is None and args.inventory is None:
        parser.error(
            "select at least one action: --check-schemas, "
            "--schema/--document, or --inventory"
        )
    return args


def validate_document(name: str, document_path: Path) -> dict[str, Any]:
    document = load_json_object(document_path, f"{name} document")
    errors = schema_errors(name, document)
    if errors:
        details = "\n".join(
            f"- {format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ContractValidationError(
            f"{name} document failed validation: {document_path}\n{details}"
        )
    validate_document_semantics(name, document)
    print(f"JSON document passed {name}: {document_path}")
    return document


def validate_document_semantics(name: str, document: dict[str, Any]) -> None:
    validators = {
        "artifact-record": validate_artifact_semantics,
        "scientific-review-record": validate_scientific_review_semantics,
        "run-summary": validate_run_summary_semantics,
        "report-receipt": validate_report_receipt_semantics,
    }
    if (validator := validators.get(name)) is not None:
        validator(document)


def main() -> int:
    args = parse_args()
    try:
        if args.check_schemas:
            validate_all_schemas()
        document = (
            validate_document(args.schema, args.document) if args.document else None
        )
        inventory_rows = validate_inventory(args.inventory) if args.inventory else None
        if document is not None and inventory_rows is not None:
            reconcile_document_inventory(
                args.schema,
                document,
                inventory_rows,
                args.inventory,
            )
            print(f"Document/inventory reconciliation passed: {args.document}")
    except ContractValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
