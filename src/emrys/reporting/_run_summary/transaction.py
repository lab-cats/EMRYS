"""Stable run-summary value and receipt utilities."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts

from .inputs import _fail


def _path_hash(
    path: Path,
    *,
    sha256: str,
    size_bytes: int,
    row_count: int | None,
    media_type: str,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256,
        "size_bytes": size_bytes,
        "row_count": row_count,
        "media_type": media_type,
    }


def _canonical_key(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _stable_unique(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    observed: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        key = _canonical_key(record)
        if key in observed:
            continue
        observed.add(key)
        result.append(record)
    return result


def _parse_history(
    receipt: Mapping[str, str],
    *,
    id_field: str,
    supersedes_field: str,
    history_field: str,
) -> tuple[str, list[str]]:
    attempt_id = receipt[id_field]
    history = [value for value in receipt[history_field].split(",") if value]
    if (
        not contracts.SAFE_ID_RE.fullmatch(attempt_id)
        or not history
        or history[-1] != attempt_id
        or len(history) != len(set(history))
        or any(not contracts.SAFE_ID_RE.fullmatch(value) for value in history)
    ):
        _fail(f"Receipt has an invalid {history_field}")
    expected_previous = history[-2] if len(history) > 1 else ""
    if receipt[supersedes_field] != expected_previous:
        _fail(f"Receipt has an invalid {supersedes_field}")
    return attempt_id, history


def _receipt_int(
    receipt: Mapping[str, str],
    field: str,
) -> int:
    value = receipt[field]
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        _fail(f"Receipt field {field} is not a non-negative integer")
    return int(value)


def _new_attempt_id(timestamp: str) -> str:
    compact = re.sub(r"[^0-9]", "", timestamp)[:14]
    return f"run-summary-{compact}-{uuid.uuid4().hex[:12]}"
