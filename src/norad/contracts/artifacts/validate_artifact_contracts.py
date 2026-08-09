#!/usr/bin/env python3
"""Validate NORAD artifact-schema-v1 JSON records and explicit inventories.

This command is read-only. It validates tracked JSON Schema documents, one
explicit JSON record at a time, and/or one explicit expected-artifact
inventory. It never searches for pipeline outputs or expands path globs.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

src_root = str(Path(__file__).resolve().parents[3])
if sys.path[:1] != [src_root]:
    if src_root in sys.path:
        sys.path.remove(src_root)
    sys.path.insert(0, src_root)

from norad.contracts.artifacts._artifact_contracts import artifact as _artifact_owner
from norad.contracts.artifacts._artifact_contracts import core as _core_owner
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
SAFE_ID_COLUMNS = INVENTORY_HEADER[:-2]
RECONCILE_FIELDS = ("artifact_id", "scope", "adapter", "expectation")
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
validate_scientific_review_semantics = _scientific_review_owner.validate_scientific_review_semantics
artifact_rollup_state = _run_summary_owner.artifact_rollup_state
aggregate_artifact_state = _run_summary_owner.aggregate_artifact_state
artifact_status_dimensions = _run_summary_owner.artifact_status_dimensions
validate_run_summary_semantics = _run_summary_owner.validate_run_summary_semantics
aggregate_equal_or_mixed = _run_summary_owner.aggregate_equal_or_mixed
RUN_SUMMARY_STATUS_FIELDS = _run_summary_owner.RUN_SUMMARY_STATUS_FIELDS
scope_key = _run_summary_owner.scope_key


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


def validate_report_receipt_semantics(document: dict[str, Any]) -> None:
    validate_document_paths(document)
    outputs = document["outputs"]
    require_unique_key(outputs, "output_id", "report outputs")
    output_kinds = {output["kind"] for output in outputs}
    output_paths = {output["path"] for output in outputs}
    if len(output_kinds) != len(outputs):
        raise ContractValidationError("report outputs contain duplicate kinds")
    if len(output_paths) != len(outputs):
        raise ContractValidationError("report outputs contain duplicate paths")
    expected_kinds = set(document["requested_formats"]) | {"run_summary_tsv"}
    if output_kinds != expected_kinds:
        raise ContractValidationError(
            "report output kinds must exactly match requested formats plus "
            "run_summary_tsv"
        )
    expected_basenames = {
        "html": f"{document['run_id']}.run_report.html",
        "pdf": f"{document['run_id']}.run_report.pdf",
        "run_summary_tsv": f"{document['run_id']}.run_summary.tsv",
    }
    output_parents: set[Path] = set()
    for output in outputs:
        path = Path(output["path"])
        if path.name != expected_basenames[output["kind"]]:
            raise ContractValidationError(
                f"report {output['kind']} output basename must be "
                f"{expected_basenames[output['kind']]!r}"
            )
        output_parents.add(path.parent)
    if len(output_parents) != 1:
        raise ContractValidationError(
            "all report outputs must share one publication directory"
        )
    output_parent = next(iter(output_parents))
    if output_parent.name != document["run_id"]:
        raise ContractValidationError(
            "report publication directory name must equal run_id"
        )
    if (
        input_run_summary_path := Path(document["input_run_summary"]["path"])
    ).name != (f"{document['run_id']}.run_summary.json"):
        raise ContractValidationError(
            "report receipt input run-summary basename does not match run_id"
        )
    if input_run_summary_path.parent.name != document["run_id"]:
        raise ContractValidationError(
            "report receipt input run-summary directory name must equal run_id"
        )
    require_unique_key(document["truncations"], "table_id", "report truncations")
    for truncation in document["truncations"]:
        if truncation["displayed_row_count"] >= truncation["full_row_count"]:
            raise ContractValidationError(
                f"truncation {truncation['table_id']!r} must display fewer "
                "rows than the full table"
            )


def validate_document_semantics(name: str, document: dict[str, Any]) -> None:
    validators = {
        "artifact-record": validate_artifact_semantics,
        "scientific-review-record": validate_scientific_review_semantics,
        "run-summary": validate_run_summary_semantics,
        "report-receipt": validate_report_receipt_semantics,
    }
    if (validator := validators.get(name)) is not None:
        validator(document)


def validate_safe_id(label: str, value: str, row_number: int) -> None:
    if not SAFE_ID_RE.fullmatch(value):
        raise ContractValidationError(
            f"Inventory row {row_number}: {label} must match "
            f"[A-Za-z0-9][A-Za-z0-9._-]*; got {value!r}"
        )


def validate_explicit_source_path(value: str, row_number: int) -> None:
    validate_resolved_path(
        value,
        f"Inventory row {row_number}: source_path",
    )


def _reject_duplicate_inventory_value(
    row_number: int,
    field_name: str,
    value: str,
    seen: dict[str, int],
) -> None:
    if value in seen:
        raise ContractValidationError(
            f"Inventory row {row_number}: duplicate {field_name} "
            f"{value!r}; first seen on row {seen[value]}"
        )
    seen[value] = row_number


def validate_inventory(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ContractValidationError(f"Inventory does not exist: {path}")
    if not path.is_file():
        raise ContractValidationError(f"Inventory is not a file: {path}")

    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames is None:
                raise ContractValidationError(
                    f"Inventory is empty or missing a header: {path}"
                )
            if tuple(reader.fieldnames) != INVENTORY_HEADER:
                raise ContractValidationError(
                    "Inventory header must exactly equal: "
                    + "\t".join(INVENTORY_HEADER)
                )
            rows = list(reader)
    except ContractValidationError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ContractValidationError(
            f"Could not parse inventory {path}: {exc}"
        ) from exc

    if not rows:
        raise ContractValidationError(
            f"Inventory must contain at least one artifact row: {path}"
        )

    seen_artifact_ids: dict[str, int] = {}
    seen_source_paths: dict[str, int] = {}
    seen_canonical_source_paths: dict[Path, int] = {}
    closed_scopes: set[tuple[str, str, str]] = set()
    active_scope: tuple[str, str, str] | None = None
    for row_number, row in enumerate(rows, start=2):
        if any(column is None for column in row):
            raise ContractValidationError(
                f"Inventory row {row_number}: too many tab-separated fields"
            )
        if any(value is None for value in row.values()):
            raise ContractValidationError(
                f"Inventory row {row_number}: too few tab-separated fields"
            )
        if empty_column := next(
            (column for column, value in row.items() if value == ""),
            None,
        ):
            raise ContractValidationError(
                f"Inventory row {row_number}: {empty_column} must be non-empty"
            )

        for column in SAFE_ID_COLUMNS:
            validate_safe_id(column, row[column], row_number)

        artifact_id = row["artifact_id"]
        _reject_duplicate_inventory_value(row_number, "artifact_id", artifact_id, seen_artifact_ids)

        if row["scope_type"] not in SCOPE_TYPES:
            raise ContractValidationError(
                f"Inventory row {row_number}: scope_type must be one of "
                f"{', '.join(sorted(SCOPE_TYPES))}; got {row['scope_type']!r}"
            )
        scope_key_ = scope_key(row)
        if active_scope is None:
            active_scope = scope_key_
        elif scope_key_ != active_scope:
            closed_scopes.add(active_scope)
            if scope_key_ in closed_scopes:
                raise ContractValidationError(
                    f"Inventory row {row_number}: artifacts for logical scope "
                    f"{scope_key_} must be contiguous"
                )
            active_scope = scope_key_

        source_path = row["source_path"]
        validate_explicit_source_path(source_path, row_number)
        _reject_duplicate_inventory_value(row_number, "source_path", source_path, seen_source_paths)
        canonical_source_path = resolve_contract_path(source_path)
        if canonical_source_path in seen_canonical_source_paths:
            raise ContractValidationError(
                f"Inventory row {row_number}: source_path resolves to the "
                "same physical path as row "
                f"{seen_canonical_source_paths[canonical_source_path]}: "
                f"{source_path!r}"
            )
        seen_canonical_source_paths[canonical_source_path] = row_number
        if row["required"] not in BOOLEAN_VALUES:
            raise ContractValidationError(
                f"Inventory row {row_number}: required must be exactly "
                f"'true' or 'false'; got {row['required']!r}"
            )

    print(f"Inventory validation passed: {path}")
    print(f"Artifacts: {len(rows)}")
    return rows


def expected_artifact_from_inventory_row(
    row: dict[str, str],
) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "scope": {
            "step_id": row["step_id"],
            "scope_type": row["scope_type"],
            "scope_id": row["scope_id"],
        },
        "adapter": row["adapter"],
        "expectation": {
            "source_path": row["source_path"],
            "required": row["required"] == "true",
        },
    }


def reconcile_artifact_inventory_row(
    artifact: dict[str, Any],
    row: dict[str, str],
) -> None:
    expected = expected_artifact_from_inventory_row(row)
    for field in RECONCILE_FIELDS:
        if artifact[field] != expected[field]:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} {field} does not "
                "match its explicit inventory row"
            )


def reconcile_document_inventory(
    name: str,
    document: dict[str, Any],
    rows: list[dict[str, str]],
    inventory_path: Path,
) -> None:
    row_index = {row["artifact_id"]: row for row in rows}
    if name == "artifact-record":
        if document["artifact_id"] not in row_index:
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} is not declared by the inventory"
            )
        reconcile_artifact_inventory_row(document, row_index[document["artifact_id"]])
        return
    if name != "run-summary":
        raise ContractValidationError(
            f"inventory reconciliation is unsupported for schema {name!r}"
        )

    inventory_record = document["inventory"]
    if resolve_contract_path(inventory_record["path"]) != inventory_path.resolve():
        raise ContractValidationError(
            "run summary inventory path does not match the supplied inventory"
        )
    observed_hash = sha256_file(inventory_path)
    if inventory_record["sha256"] != observed_hash:
        raise ContractValidationError(
            "run summary inventory hash does not match the supplied inventory"
        )
    if inventory_record["row_count"] != len(rows):
        raise ContractValidationError(
            "run summary inventory row_count does not match the supplied inventory"
        )

    artifacts = document["artifacts"]
    if len(artifacts) != len(rows) or any(
        artifact["artifact_id"] != row["artifact_id"]
        for artifact, row in zip(artifacts, rows)
    ):
        raise ContractValidationError(
            "run summary artifacts do not exactly match inventory row order"
        )
    for artifact, row in zip(artifacts, rows):
        reconcile_artifact_inventory_row(artifact, row)

    scope_groups: dict[tuple[str, str, str], list[str]] = {}
    for row in rows:
        scope_key_ = scope_key(row)
        scope_groups.setdefault(scope_key_, []).append(row["artifact_id"])
    expected_scope_contract = list(scope_groups.items())
    observed_scope_contract = [
        (scope_key(scope["scope"]), scope["artifact_ids"]) for scope in document["expected_scopes"]
    ]
    if observed_scope_contract != expected_scope_contract:
        raise ContractValidationError(
            "run summary expected scopes do not exactly group the supplied "
            "inventory in stable first-seen order"
        )


def main() -> int:
    args = parse_args()
    try:
        if args.check_schemas:
            validate_all_schemas()
        document = validate_document(args.schema, args.document) if args.document else None
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
