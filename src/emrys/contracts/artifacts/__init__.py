"""Shared artifact-inventory primitives."""

from __future__ import annotations

import glob
import re
from pathlib import Path

INVENTORY_HEADER = (
    "artifact_id",
    "step_id",
    "scope_type",
    "scope_id",
    "adapter",
    "source_path",
    "required",
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ContractValidationError(RuntimeError):
    """Raised when an artifact contract is invalid."""


def scope_key(scope: dict[str, object]) -> tuple[str, str, str]:
    """Return the canonical Step/type/ID key shared by artifact inventories."""

    return str(scope["step_id"]), str(scope["scope_type"]), str(scope["scope_id"])


def validate_resolved_path(value: str, label: str) -> None:
    """Require an explicit, normalized, non-templated artifact path."""

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
    if any(part in {".", ".."} for part in Path(value).parts):
        raise ContractValidationError(
            f"{label} must be normalized without '.' or '..' components: {value}"
        )
