"""Stable Run manifest value projections."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


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
