"""Validate explicit EMRYS artifact contracts through the grouped CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

from emrys.contracts.artifacts._artifact_contracts.definitions import (
    SCHEMA_FILES,
    ContractValidationError,
)

DESCRIPTION = (
    "Validate the registered artifact-contract schemas, a named JSON record, "
    "and/or an explicit expected-artifact inventory."
)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the artifact-contract validation arguments."""

    parser.add_argument(
        "--check-schemas",
        action="store_true",
        help="Validate every registered schema resource against Draft 2020-12.",
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
    parser.set_defaults(_command_parser=parser)


def _validate_document(name: str, document_path: Path) -> dict[str, Any]:
    # Keep JSON Schema dependencies lazy so unrelated installed commands work.
    from emrys.contracts.artifacts import api  # ruff: ignore[import-outside-top-level]

    document = api.load_json_object(document_path, f"{name} document")
    errors = api.schema_errors(name, document)
    if errors:
        details = "\n".join(
            f"- {api.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ContractValidationError(
            f"{name} document failed validation: {document_path}\n{details}"
        )
    api.validate_document_semantics(name, document)
    print(f"JSON document passed {name}: {document_path}")
    return document


def _validate_selected(arguments: argparse.Namespace) -> None:
    # These imports intentionally happen only after this command is selected.
    from emrys.contracts.artifacts import api  # ruff: ignore[import-outside-top-level]
    from emrys.contracts.artifacts._artifact_contracts.schema import (  # ruff: ignore[import-outside-top-level]
        validate_all_schemas,
    )

    if arguments.check_schemas:
        validate_all_schemas()
    document = (
        _validate_document(arguments.schema, arguments.document)
        if arguments.document
        else None
    )
    inventory_rows = (
        api.validate_inventory(arguments.inventory) if arguments.inventory else None
    )
    if document is not None and inventory_rows is not None:
        api.reconcile_document_inventory(
            arguments.schema,
            document,
            inventory_rows,
            arguments.inventory,
        )
        print(f"Document/inventory reconciliation passed: {arguments.document}")


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate the selected artifact-contract inputs."""

    parser = cast(argparse.ArgumentParser, arguments._command_parser)
    if (arguments.schema is None) != (arguments.document is None):
        parser.error("--schema and --document must be supplied together")
    if (
        not arguments.check_schemas
        and arguments.document is None
        and arguments.inventory is None
    ):
        parser.error(
            "select at least one action: --check-schemas, "
            "--schema/--document, or --inventory"
        )

    try:
        _validate_selected(arguments)
    except ContractValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0
