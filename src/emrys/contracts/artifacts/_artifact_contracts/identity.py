"""Run-contract, explicit-path, uniqueness, and attempt-graph rules."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import validate_resolved_path

from .definitions import (
    REPO_ROOT,
    RUN_CONTRACT_COMPONENT_FIELDS,
    ContractValidationError,
)


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


def validate_attempt_graph(
    attempts: list[dict[str, Any]],
    *,
    selected_attempt_id: str | None = None,
    label: str,
    require_single_chain: bool = True,
) -> dict[str, dict[str, Any]]:
    def parse_utc_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    indexed = require_unique_key(attempts, "attempt_id", label)
    if selected_attempt_id is not None and selected_attempt_id not in indexed:
        raise ContractValidationError(
            f"{label} selected_attempt_id does not name a recorded attempt: "
            f"{selected_attempt_id}"
        )

    for attempt_id, attempt in indexed.items():
        parent = attempt["supersedes_attempt_id"]
        if parent is None:
            continue
        if parent == attempt_id:
            raise ContractValidationError(
                f"{label} attempt {attempt_id!r} cannot supersede itself"
            )
        if parent not in indexed:
            raise ContractValidationError(
                f"{label} attempt {attempt_id!r} supersedes unknown attempt {parent!r}"
            )

    roots = [
        attempt_id
        for attempt_id, attempt in indexed.items()
        if attempt["supersedes_attempt_id"] is None
    ]
    if require_single_chain and indexed and len(roots) != 1:
        raise ContractValidationError(
            f"{label} attempt history must be one connected retry chain; "
            f"found {len(roots)} roots"
        )
    child_counts: dict[str, int] = defaultdict(int)
    for attempt in indexed.values():
        parent = attempt["supersedes_attempt_id"]
        if parent is not None:
            child_counts[parent] += 1
    branched = sorted(
        attempt_id
        for attempt_id, child_count in child_counts.items()
        if child_count > 1
    )
    if branched:
        raise ContractValidationError(
            f"{label} attempt history branches at: " + ", ".join(branched)
        )

    for start in indexed:
        visited: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in visited:
                raise ContractValidationError(
                    f"{label} attempt supersession contains a cycle at {current!r}"
                )
            visited.add(current)
            current = indexed[current]["supersedes_attempt_id"]

    for attempt_id, attempt in indexed.items():
        started_at = attempt["started_at"]
        finished_at = attempt["finished_at"]
        if started_at is not None and finished_at is not None:
            started = parse_utc_timestamp(started_at)
            finished = parse_utc_timestamp(finished_at)
            if finished < started:
                raise ContractValidationError(
                    f"{label} attempt {attempt_id!r} finishes before it starts"
                )
        parent_id = attempt["supersedes_attempt_id"]
        if parent_id is not None:
            parent_finished_at = indexed[parent_id]["finished_at"]
            if started_at is not None and parent_finished_at is not None:
                started = parse_utc_timestamp(started_at)
                parent_finished = parse_utc_timestamp(parent_finished_at)
                if started < parent_finished:
                    raise ContractValidationError(
                        f"{label} attempt {attempt_id!r} starts before "
                        f"superseded attempt {parent_id!r} finishes"
                    )
    return indexed


def resolve_contract_path(
    value: str,
    *,
    source_root: Path = REPO_ROOT,
) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = source_root / path
    return path.resolve()
