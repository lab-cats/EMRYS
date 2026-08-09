"""Closed-registry JSON Schema loading and deterministic diagnostics."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

from norad.libraries import validation as report

from .definitions import (
    COMMON_SCHEMA_PATH,
    SCHEMA_FILES,
    ContractValidationError,
)


def reject_duplicate_json_keys(
    pairs: Iterable[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractValidationError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def reject_nonstandard_json_constant(value: str) -> None:
    raise ContractValidationError(
        f"Non-standard JSON numeric constant is not allowed: {value}"
    )


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ContractValidationError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise ContractValidationError(f"{label} is not a file: {path}")
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(
                stream,
                object_pairs_hook=reject_duplicate_json_keys,
                parse_constant=reject_nonstandard_json_constant,
            )
    except ContractValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"Could not parse {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractValidationError(f"{label} must contain a JSON object: {path}")
    return value


def load_schema(name: str) -> dict[str, Any]:
    schemas, _ = load_schema_registry()
    return schemas[name]


def load_schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schema_paths = {"common": COMMON_SCHEMA_PATH, **SCHEMA_FILES}
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for name, schema_path in schema_paths.items():
        schema = load_json_object(schema_path, f"{name} schema")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ContractValidationError(
                f"{name} schema is not valid Draft 2020-12: {exc.message}"
            ) from exc
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ContractValidationError(f"{name} schema must define a non-empty $id")
        try:
            registry = registry.with_resource(
                schema_id,
                Resource.from_contents(schema),
            )
        except Exception as exc:
            raise ContractValidationError(
                f"Could not register local {name} schema: {exc}"
            ) from exc
        schemas[name] = schema
    return schemas, registry


def schema_validator(name: str) -> Draft202012Validator:
    """Build a validator from the closed local registry for one named schema."""

    schemas, registry = load_schema_registry()
    return Draft202012Validator(
        schemas[name],
        registry=registry,
        format_checker=FormatChecker(),
    )


def schema_errors(name: str, document: Any) -> list[Any]:
    """Order errors deterministically while callers retain message ownership."""

    return sorted(
        schema_validator(name).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )


def validate_all_schemas() -> None:
    schemas, _ = load_schema_registry()
    for name in schemas:
        print(f"Schema passed Draft 2020-12 validation: {name}")


def format_json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def sha256_file(path: Path) -> str:
    try:
        return report.sha256_file(path)
    except OSError as exc:
        raise ContractValidationError(f"Could not hash {path}: {exc}") from exc
