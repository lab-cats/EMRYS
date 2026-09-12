"""Run-contract, explicit-path, and uniqueness rules."""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path
from typing import Any

from .definitions import (
    PACKAGE_ROOT,
    RUN_CONTRACT_COMPONENT_FIELDS,
    ContractValidationError,
)


def scope_key(scope: dict[str, Any]) -> tuple[str, str, str]:
    return scope["step_id"], scope["scope_type"], scope["scope_id"]


def canonical_run_contract_sha256(run_contract: dict[str, Any]) -> str:
    components = {field: run_contract[field] for field in RUN_CONTRACT_COMPONENT_FIELDS}
    payload = json.dumps(
        components,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_run_contract(run_contract: dict[str, Any], label: str) -> None:
    expected = canonical_run_contract_sha256(run_contract)
    observed = run_contract["run_contract_sha256"]
    if observed != expected:
        raise ContractValidationError(
            f"{label} run_contract_sha256 does not match the canonical "
            f"component contract; observed {observed}, expected {expected}"
        )


def validate_resolved_path(value: str, label: str) -> None:
    if not value or value.strip() != value:
        raise ContractValidationError(
            f"{label} must be non-empty and have no surrounding whitespace"
        )
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ContractValidationError(f"{label} contains an invalid control character")
    if glob.has_magic(value):
        raise ContractValidationError(
            f"{label} must be explicit and must not contain glob syntax: {value}"
        )
    if any(token in value for token in ("${", "{{", "}}")):
        raise ContractValidationError(
            f"{label} must be resolved, not templated: {value}"
        )
    if "//" in value:
        raise ContractValidationError(
            f"{label} must not contain redundant path separators: {value}"
        )
    path = Path(value)
    if any(part in {".", ".."} for part in path.parts):
        raise ContractValidationError(
            f"{label} must be normalized without '.' or '..' components: {value}"
        )


def validate_document_paths(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if isinstance(child, str) and (key == "path" or key.endswith("_path")):
                validate_resolved_path(child, child_location)
            validate_document_paths(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_document_paths(child, f"{location}[{index}]")


def require_unique_key(
    records: list[dict[str, Any]],
    key: str,
    label: str,
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        value = record[key]
        if value in indexed:
            raise ContractValidationError(
                f"{label} contains duplicate {key} {value!r} at array index {index}"
            )
        indexed[value] = record
    return indexed


def resolve_contract_path(
    value: str,
    *,
    source_root: Path = PACKAGE_ROOT,
) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = source_root / path
    return path.resolve()
