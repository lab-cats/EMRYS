"""Value objects and stable vocabulary for run-summary science projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from norad.contracts.scientific_evidence.computational_validation import (
    HEADER as COMPUTATIONAL_VALIDATION_HEADER,
)
from norad.contracts.scientific_evidence.computational_validation import (
    SCOPE_PLAN_FIELDS as COMPUTATIONAL_SCOPE_PLAN_FIELDS,
)
from norad.contracts.scientific_evidence.computational_validation import (
    SCOPE_ROLES as COMPUTATIONAL_SCOPE_ROLES,
)
from norad.contracts.scientific_evidence.review_package import (
    INPUT_ARTIFACT_ROLES as INPUT_ROLE_BY_STEP09C_KEY,
)
from norad.contracts.scientific_evidence.review_package import OUTPUT_SUFFIXES

NA_VALUE = "NA"
SCIENCE_SCHEMA_VERSION = "1.1.0"
PRODUCER = "build_run_summary"
PRODUCER_VERSION = "1.0.0"
PUBLISHED_ADAPTERS = {key: f"step09c_{key}_v1" for key, _ in OUTPUT_SUFFIXES}


@dataclass(frozen=True)
class ReviewInput:
    """One source descriptor committed into the public review summary."""

    path: Path
    sha256: str
    row_count: str


@dataclass
class ReviewPackageContext:
    """The public package projection required by run-summary reporting."""

    plan: dict[str, str]
    category_rows: dict[str, list[dict[str, str]]]
    evidence_index_rows: list[dict[str, str]]
    artifacts: dict[str, ReviewInput]
    input_hashes: dict[Path, str]


class RunSummaryScienceError(RuntimeError):
    """Raised when Step 09c cannot be faithfully normalized."""


def _fail(message: str) -> None:
    raise RunSummaryScienceError(message)


def _artifact_scope(artifact: Mapping[str, Any]) -> tuple[str, str, str]:
    scope = artifact.get("scope")
    if not isinstance(scope, Mapping):
        _fail("Artifact record has no valid scope object.")
    values = (
        scope.get("step_id"),
        scope.get("scope_type"),
        scope.get("scope_id"),
    )
    if not all(isinstance(value, str) for value in values):
        _fail("Artifact record has an invalid scope identity.")
    return values  # type: ignore[return-value]


def _artifact_source(
    artifact: Mapping[str, Any],
    *,
    label: str,
) -> Mapping[str, Any]:
    source = artifact.get("source")
    if not isinstance(source, Mapping):
        _fail(f"{label} has no indexed source descriptor.")
    return source


def _parse_row_count(label: str, value: str) -> int | None:
    if value == NA_VALUE:
        return None
    if not value.isdigit():
        _fail(f"{label} is not a non-negative integer or NA: {value!r}")
    return int(value)


def _split_ids(value: str) -> list[str]:
    if value == NA_VALUE:
        return []
    return value.split(",")


def _nullable(value: str) -> str | None:
    return None if value == NA_VALUE else value
