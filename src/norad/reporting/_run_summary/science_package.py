"""Reconstruct and validate one committed public Step 09c package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts
from norad.contracts.scientific_evidence import review_package
from norad.libraries.validation.tsv import tsv_bytes as _tsv_bytes

from .science_io import (
    _read_tsv,
    _require_contract_file,
    _require_regular_file,
    _resolve_recorded_path,
)
from .science_models import (
    COMPUTATIONAL_VALIDATION_HEADER,
    NA_VALUE,
    PUBLISHED_ADAPTERS,
    ReviewInput,
    ReviewPackageContext,
    RunSummaryScienceError,
    _artifact_scope,
    _artifact_source,
    _fail,
    _parse_row_count,
)


def _validate_summary_artifact(
    *,
    summary_path: Path,
    artifacts: Sequence[Mapping[str, Any]],
    summary_row: Mapping[str, str],
    summary_sha256: str,
) -> Mapping[str, Any]:
    matches: list[Mapping[str, Any]] = []
    for artifact in artifacts:
        if artifact.get("adapter") != "step09c_review_summary_v1":
            continue
        source = artifact.get("source")
        if not isinstance(source, Mapping):
            continue
        source_value = source.get("path")
        if not isinstance(source_value, str):
            continue
        try:
            source_path = _require_contract_file(
                "Indexed Step 09c review summary", source_value
            )
        except RunSummaryScienceError:
            continue
        if source_path == summary_path:
            matches.append(artifact)
    if len(matches) != 1:
        _fail(
            "The explicit Step 09c review summary must match exactly one "
            "indexed step09c_review_summary_v1 artifact; observed "
            f"{len(matches)} matches."
        )
    artifact = matches[0]
    if artifact.get("completion_status") != "complete":
        _fail("The indexed Step 09c review-summary artifact is not complete.")
    source = _artifact_source(artifact, label="Step 09c review summary")
    if source.get("sha256") != summary_sha256:
        _fail("The indexed Step 09c review-summary hash differs from the file.")
    if source.get("row_count") != 1:
        _fail("The indexed Step 09c review summary must have row_count=1.")
    if source.get("size_bytes") != summary_path.stat().st_size:
        _fail("The indexed Step 09c review-summary byte size differs.")
    if source.get("media_type") != "text/tab-separated-values":
        _fail("The indexed Step 09c review summary has the wrong media type.")
    expected_scope = (
        "09c",
        "scientific_review",
        summary_row["review_id"],
    )
    if _artifact_scope(artifact) != expected_scope:
        _fail("The indexed Step 09c review summary has the wrong review scope.")
    return artifact


def _validate_published_artifacts(
    *,
    summary_path: Path,
    summary_row: Mapping[str, str],
    artifacts: Sequence[Mapping[str, Any]],
    summary_artifact: Mapping[str, Any],
    output_tables: Mapping[str, tuple[tuple[str, ...], list[dict[str, str]]]],
) -> None:
    review_id = summary_row["review_id"]
    scoped = [
        artifact
        for artifact in artifacts
        if _artifact_scope(artifact) == ("09c", "scientific_review", review_id)
    ]
    expected_adapters = set(PUBLISHED_ADAPTERS.values())
    observed_adapters = [artifact.get("adapter") for artifact in scoped]
    if (
        len(scoped) != len(expected_adapters)
        or set(observed_adapters) != expected_adapters
        or len(observed_adapters) != len(set(observed_adapters))
    ):
        _fail(
            "The Step 09c review scope must contain exactly the 13 fixed "
            "published adapters."
        )
    indexed = {artifact["adapter"]: artifact for artifact in scoped}
    expected_science = {
        "overall_status": summary_row["overall_science_status"],
        "orientation_status": summary_row["orientation_status"],
        "orientation_policy": summary_row["orientation_policy"],
        "review_id": review_id,
    }
    if summary_artifact.get("scientific_state") != expected_science:
        _fail(
            "The indexed Step 09c review summary does not carry the exact "
            "science state declared by its source row."
        )

    for key, suffix in review_package.OUTPUT_SUFFIXES:
        adapter = PUBLISHED_ADAPTERS[key]
        artifact = indexed[adapter]
        if artifact.get("completion_status") != "complete":
            _fail(f"Indexed Step 09c artifact {adapter} is not complete.")
        if artifact.get("scientific_state") != expected_science:
            _fail(
                f"Indexed Step 09c artifact {adapter} has a mismatched "
                "propagated science state."
            )
        expected_path = summary_path.parent / f"{review_id}.{suffix}"
        source = _artifact_source(artifact, label=adapter)
        source_value = source.get("path")
        if not isinstance(source_value, str):
            _fail(f"Indexed Step 09c artifact {adapter} has no source path.")
        actual_path = _require_contract_file(
            f"Indexed Step 09c artifact {adapter}", source_value
        )
        if actual_path != expected_path:
            _fail(
                f"Indexed Step 09c artifact {adapter} is not at its exact "
                f"published path: expected {expected_path}; observed "
                f"{source_value}."
            )
        expectation = artifact.get("expectation")
        if not isinstance(expectation, Mapping):
            _fail(f"Indexed Step 09c artifact {adapter} has no expectation.")
        expected_source_value = expectation.get("source_path")
        if (
            not isinstance(expected_source_value, str)
            or expected_source_value != source_value
        ):
            _fail(
                f"Indexed Step 09c artifact {adapter} expectation does not "
                "match its indexed source path."
            )
        header, rows = output_tables[key]
        observed_table = _read_tsv(f"Published Step 09c {key}", actual_path, header)
        if observed_table.rows != rows:
            _fail(f"Published Step 09c {key} rows differ from reconstruction.")
        expected_bytes = _tsv_bytes(header, rows)
        try:
            observed_bytes = actual_path.read_bytes()
        except OSError as exc:
            _fail(f"Could not read published Step 09c {key}: {exc}")
        if observed_bytes != expected_bytes:
            _fail(f"Published Step 09c {key} bytes differ from reconstruction.")
        observed_hash = contracts.sha256_file(actual_path)
        if source.get("sha256") != observed_hash:
            _fail(f"Published Step 09c {key} rows differ from reconstruction.")
        if source.get("size_bytes") != len(observed_bytes):
            _fail(f"Indexed Step 09c artifact {adapter} byte size differs.")
        if source.get("row_count") != len(rows):
            _fail(f"Indexed Step 09c artifact {adapter} row count differs.")
        if source.get("media_type") != "text/tab-separated-values":
            _fail(f"Indexed Step 09c artifact {adapter} media type differs.")


def _read_committed_review_package(
    *,
    summary_path: Path,
    summary_row: Mapping[str, str],
) -> tuple[
    ReviewPackageContext,
    dict[str, tuple[tuple[str, ...], list[dict[str, str]]]],
]:
    review_id = summary_row["review_id"]
    output_paths = {
        key: summary_path.parent / f"{review_id}.{suffix}"
        for key, suffix in review_package.OUTPUT_SUFFIXES
    }
    if output_paths["review_summary"] != summary_path:
        _fail(
            "The summary-declared Step 09c identity names a different "
            "review-summary path."
        )

    output_tables: dict[str, tuple[tuple[str, ...], list[dict[str, str]]]] = {}
    input_hashes: dict[Path, str] = {}

    def remember_input(path: Path, observed_hash: str) -> None:
        previous = input_hashes.get(path)
        if previous is not None and previous != observed_hash:
            _fail(f"Reporting input has conflicting committed hashes: {path}")
        input_hashes[path] = observed_hash

    for key, _suffix in review_package.OUTPUT_SUFFIXES:
        if key == "review_plan":
            header = review_package.REVIEW_PLAN_HEADER
        elif key == "evidence_index":
            header = review_package.EVIDENCE_INDEX_HEADER
        elif key == "review_summary":
            header = review_package.REVIEW_SUMMARY_HEADER
        else:
            header = review_package.CATEGORY_HEADERS[key]
        table = _read_tsv(
            f"Committed Step 09c {key}",
            output_paths[key],
            header,
        )
        output_tables[key] = (header, table.rows)
        remember_input(table.path, contracts.sha256_file(table.path))

    plan_rows = output_tables["review_plan"][1]
    if len(plan_rows) != 1:
        _fail("The committed Step 09c review plan must contain one row.")
    committed_summary_rows = output_tables["review_summary"][1]
    if committed_summary_rows != [dict(summary_row)]:
        _fail("The committed Step 09c review summary changed while loading.")

    input_artifacts: dict[str, ReviewInput] = {}
    for key in review_package.INPUT_ARTIFACT_KEYS:
        input_artifacts[key] = ReviewInput(
            path=contracts.resolve_contract_path(summary_row[f"{key}_path"]),
            sha256=summary_row[f"{key}_sha256"],
            row_count=summary_row[f"{key}_row_count"],
        )

    evidence_index_rows = output_tables["evidence_index"][1]
    category_rows = {
        category: output_tables[category][1]
        for category in review_package.CATEGORY_ORDER
    }
    category_rows["computational_validation"] = []
    for row in evidence_index_rows:
        if row["evidence_status"] not in ("complete", "incomplete"):
            continue
        evidence_id = row["evidence_id"]
        source_path = _require_regular_file(
            f"Scientific evidence {evidence_id}", row["source_path"]
        )
        observed_hash = contracts.sha256_file(source_path)
        if observed_hash != row["observed_sha256"]:
            _fail(f"Scientific evidence {evidence_id} hash differs.")
        expected_header = (
            COMPUTATIONAL_VALIDATION_HEADER
            if row["evidence_category"] == "computational_validation"
            else review_package.CATEGORY_HEADERS[row["evidence_category"]]
        )
        source_table = _read_tsv(
            f"Scientific evidence {evidence_id}",
            source_path,
            expected_header,
        )
        expected_row_count = _parse_row_count(
            f"Scientific evidence {evidence_id} row count",
            row["observed_row_count"],
        )
        if expected_row_count != len(source_table.rows):
            _fail(f"Scientific evidence {evidence_id} row count differs.")
        remember_input(source_path, observed_hash)
        if row["evidence_category"] != "computational_validation":
            continue
        for payload in source_table.rows:
            if (
                payload["review_id"] != review_id
                or payload["evidence_id"] != evidence_id
                or payload["analysis_id"] != row["analysis_id"]
            ):
                _fail(
                    f"Computational evidence {evidence_id} identity differs "
                    "from its committed evidence-index record."
                )
            if payload["evidence_path"] != NA_VALUE:
                payload_path = _require_regular_file(
                    f"Computational payload {evidence_id} "
                    f"{payload['validation_scope']}",
                    _resolve_recorded_path(payload["evidence_path"]),
                )
                payload_hash = contracts.sha256_file(payload_path)
                if payload_hash != payload["evidence_sha256"]:
                    _fail(
                        f"Computational payload {evidence_id} "
                        f"{payload['validation_scope']} hash differs."
                    )
                remember_input(payload_path, payload_hash)
        category_rows["computational_validation"].extend(source_table.rows)

    context = ReviewPackageContext(
        plan=dict(plan_rows[0]),
        evidence_rows=[dict(row) for row in evidence_index_rows],
        category_rows=category_rows,
        evidence_index_rows=evidence_index_rows,
        artifacts=input_artifacts,
        input_hashes=input_hashes,
        output_paths=output_paths,
    )
    return context, output_tables
