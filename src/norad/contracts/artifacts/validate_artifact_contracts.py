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

from norad.contracts.artifacts import api
from norad.contracts.artifacts._artifact_contracts.definitions import SCHEMA_FILES
from norad.contracts.artifacts._artifact_contracts.schema import validate_all_schemas


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
    document = api.load_json_object(document_path, f"{name} document")
    errors = api.schema_errors(name, document)
    if errors:
        details = "\n".join(
            f"- {api.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise api.ContractValidationError(
            f"{name} document failed validation: {document_path}\n{details}"
        )
    api.validate_document_semantics(name, document)
    print(f"JSON document passed {name}: {document_path}")
    return document


def main() -> int:
    args = parse_args()
    try:
        if args.check_schemas:
            validate_all_schemas()
        document = (
            validate_document(args.schema, args.document) if args.document else None
        )
        inventory_rows = (
            api.validate_inventory(args.inventory) if args.inventory else None
        )
        if document is not None and inventory_rows is not None:
            api.reconcile_document_inventory(
                args.schema,
                document,
                inventory_rows,
                args.inventory,
            )
            print(f"Document/inventory reconciliation passed: {args.document}")
    except api.ContractValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
