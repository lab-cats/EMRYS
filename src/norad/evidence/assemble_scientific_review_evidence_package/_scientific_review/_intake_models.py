"""Data models assembled during scientific-review intake."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Artifact:
    label: str
    path: Path
    sha256: str
    row_count: str


@dataclass
class ReviewContext:
    review_id: str
    plan: dict[str, str]
    evidence_rows: list[dict[str, str]]
    category_rows: dict[str, list[dict[str, str]]]
    evidence_index_rows: list[dict[str, str]]
    artifacts: dict[str, Artifact]
    input_hashes: dict[Path, str]
    sample_ids: list[str]
    sample_rows: list[dict[str, str]]
    partition_rows: list[dict[str, str]]
    step08_input_rows: list[dict[str, str]]
    step08_site_rows: list[dict[str, str]]
    step09_all_rows: list[dict[str, str]]
    step09_significant_rows: list[dict[str, str]]
    step09_summary: dict[str, str]
    output_paths: dict[str, Path]
