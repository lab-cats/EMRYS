"""Explicit artifact-inventory validation and reconciliation."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .definitions import (
    BOOLEAN_VALUES,
    INVENTORY_HEADER,
    REPO_ROOT,
    SAFE_ID_RE,
    SCOPE_TYPES,
    ContractValidationError,
)
from .identity import (
    resolve_contract_path,
    validate_resolved_path,
)
from .run_summary_status import scope_key
from .schema import sha256_file

SAFE_ID_COLUMNS = INVENTORY_HEADER[:-2]
RECONCILE_FIELDS = ("artifact_id", "scope", "adapter", "expectation")


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


def validate_inventory(
    path: Path,
    *,
    source_root: Path = REPO_ROOT,
) -> list[dict[str, str]]:
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
        _reject_duplicate_inventory_value(
            row_number, "artifact_id", artifact_id, seen_artifact_ids
        )

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
        _reject_duplicate_inventory_value(
            row_number, "source_path", source_path, seen_source_paths
        )
        canonical_source_path = resolve_contract_path(
            source_path,
            source_root=source_root,
        )
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
    *,
    source_root: Path = REPO_ROOT,
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
    if (
        resolve_contract_path(
            inventory_record["path"],
            source_root=source_root,
        )
        != inventory_path.resolve()
    ):
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
        (scope_key(scope["scope"]), scope["artifact_ids"])
        for scope in document["expected_scopes"]
    ]
    if observed_scope_contract != expected_scope_contract:
        raise ContractValidationError(
            "run summary expected scopes do not exactly group the supplied "
            "inventory in stable first-seen order"
        )
