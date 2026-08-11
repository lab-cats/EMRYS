"""Scientific-review intake models and shared helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from norad.libraries.validation.tsv import write_rows

from .contracts import NA_VALUE, Table, review_package, sha256_file, step08


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
    artifacts: dict[str, Artifact]
    input_hashes: dict[Path, str]
    sample_ids: list[str]
    sample_rows: list[dict[str, str]]
    partition_rows: list[dict[str, str]]
    step08_input_rows: list[dict[str, str]]
    step09_all_rows: list[dict[str, str]]
    step09_summary: dict[str, str]
    output_paths: dict[str, Path]


def validate_iso_date(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        step08.fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")
    if parsed.isoformat() != value:
        step08.fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")


def complement_base(value: str) -> str:
    complements = {"A": "T", "C": "G", "G": "C", "T": "A"}
    if value not in complements:
        step08.fail(f"Expected a canonical DNA base; got: {value}")
    return complements[value]


def split_ids(label: str, value: str) -> list[str]:
    if value == NA_VALUE:
        return []
    parts = value.split(",")
    if any(not part or part.strip() != part for part in parts):
        step08.fail(f"{label} must be comma-separated safe IDs or NA; got: {value}")
    for part in parts:
        step08.validate_safe_id(label, part)
    if len(parts) != len(set(parts)):
        step08.fail(f"{label} contains duplicate IDs: {value}")
    return parts


def require_directory(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_dir():
        step08.fail(f"{label} does not exist or is not a directory: {path}")
    return path.resolve()


def write_tsv(
    path: Path, header: Sequence[str], rows: Iterable[Mapping[str, str]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        write_rows(stream, header, rows)


def artifact_from_table(label: str, table: Table) -> Artifact:
    return Artifact(
        label=label,
        path=table.path,
        sha256=sha256_file(table.path),
        row_count=str(len(table.rows)),
    )


def artifact_from_binary(label: str, path: Path) -> Artifact:
    return Artifact(
        label=label,
        path=path,
        sha256=sha256_file(path),
        row_count=NA_VALUE,
    )


def resolve_declared_path(value: str, source_file: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = source_file.parent / path
    return path.resolve()


def register_artifact(
    artifacts: dict[str, Artifact],
    input_hashes: dict[Path, str],
    key: str,
    artifact: Artifact,
) -> None:
    if key in artifacts:
        step08.fail(f"Internal artifact key was registered twice: {key}")
    artifacts[key] = artifact
    input_hashes[artifact.path] = artifact.sha256


def step09_paths(analysis_dir: Path, analysis_id: str) -> dict[str, Path]:
    return {
        "step09_all_sites": analysis_dir / f"{analysis_id}.cmh_all_sites.tsv",
        "step09_significant_sites": (
            analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        "step09_summary": analysis_dir / f"{analysis_id}.cmh_summary.tsv",
        "step09_mutation_spectrum": (
            analysis_dir / f"{analysis_id}.mutation_spectrum.tsv"
        ),
        "step09_mutation_spectrum_pdf": (
            analysis_dir / f"{analysis_id}.mutation_spectrum.pdf"
        ),
        "step09_depth_delta_pdf": (analysis_dir / f"{analysis_id}.depth_delta.pdf"),
    }


def validate_supporting_ids(label: str, value: str, evidence_ids: set[str]) -> None:
    for evidence_id in split_ids(label, value):
        if evidence_id not in evidence_ids:
            step08.fail(f"{label} references unknown evidence_id {evidence_id}.")


def category_is_complete(
    evidence_rows: Sequence[Mapping[str, str]], category: str
) -> bool:
    return (
        review_package.aggregate_evidence_status(evidence_rows, category) == "complete"
    )


def validate_candidate_reference(
    label: str, candidate_id: str, candidates: Mapping[str, Mapping[str, str]]
) -> Mapping[str, str]:
    result = candidates.get(candidate_id)
    if result is None:
        step08.fail(f"{label} references unknown candidate_id {candidate_id}.")
    return result
