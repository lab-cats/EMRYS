#!/usr/bin/env python3
"""Normalize one committed Step 09c package into its public science record."""

from __future__ import annotations

import csv
import importlib.util
import io
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker


_ARTIFACT_CONTRACTS_MODULE_NAME = "_norad_artifact_contracts"
_ARTIFACT_CONTRACTS_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "norad"
    / "contracts"
    / "artifacts"
    / "validate_artifact_contracts.py"
).resolve(strict=False)
_ARTIFACT_CONTRACTS_READY_ATTRIBUTE = "_NORAD_ARTIFACT_CONTRACTS_READY"


def _validated_artifact_contracts(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached artifact-contract owner has no valid file path"
        ) from exc
    if module_path != _ARTIFACT_CONTRACTS_MODULE_PATH:
        raise ImportError(
            f"cached artifact-contract owner resolves to {module_path}, "
            f"expected {_ARTIFACT_CONTRACTS_MODULE_PATH}"
        )
    if getattr(module, _ARTIFACT_CONTRACTS_READY_ATTRIBUTE, False) is not True:
        raise ImportError("cached artifact-contract owner is partially initialized")
    return module


def _load_artifact_contracts() -> object:
    cached = sys.modules.get(_ARTIFACT_CONTRACTS_MODULE_NAME)
    if cached is not None:
        return _validated_artifact_contracts(cached)
    spec = importlib.util.spec_from_file_location(
        _ARTIFACT_CONTRACTS_MODULE_NAME,
        _ARTIFACT_CONTRACTS_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file artifact-contract module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_ARTIFACT_CONTRACTS_MODULE_NAME, module)
    if existing is not module:
        return _validated_artifact_contracts(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _ARTIFACT_CONTRACTS_READY_ATTRIBUTE, True)
        _validated_artifact_contracts(module)
    except BaseException:
        if sys.modules.get(_ARTIFACT_CONTRACTS_MODULE_NAME) is module:
            del sys.modules[_ARTIFACT_CONTRACTS_MODULE_NAME]
        raise
    return module


contracts = _load_artifact_contracts()


_REVIEW_PACKAGE_MODULE_NAME = "_norad_review_package_scientific_evidence_contract"
_REVIEW_PACKAGE_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "norad"
    / "contracts"
    / "scientific_evidence"
    / "review_package.py"
).resolve(strict=False)
_REVIEW_PACKAGE_READY_ATTRIBUTE = "_NORAD_REVIEW_PACKAGE_CONTRACT_READY"


def _validated_review_package_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached review-package scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _REVIEW_PACKAGE_MODULE_PATH:
        raise ImportError(
            "cached review-package scientific-evidence contract resolves to "
            f"{module_path}, expected {_REVIEW_PACKAGE_MODULE_PATH}"
        )
    if getattr(module, _REVIEW_PACKAGE_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached review-package scientific-evidence contract is partially "
            "initialized"
        )
    return module


def _load_review_package_contract() -> object:
    cached = sys.modules.get(_REVIEW_PACKAGE_MODULE_NAME)
    if cached is not None:
        return _validated_review_package_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _REVIEW_PACKAGE_MODULE_NAME, _REVIEW_PACKAGE_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file review-package module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_REVIEW_PACKAGE_MODULE_NAME, module)
    if existing is not module:
        return _validated_review_package_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _REVIEW_PACKAGE_READY_ATTRIBUTE, True)
        _validated_review_package_contract(module)
    except BaseException:
        if sys.modules.get(_REVIEW_PACKAGE_MODULE_NAME) is module:
            del sys.modules[_REVIEW_PACKAGE_MODULE_NAME]
        raise
    return module


try:
    review_package = _load_review_package_contract()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load review-package scientific-evidence contract at "
        f"{_REVIEW_PACKAGE_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


NA_VALUE = "NA"
COMPUTATIONAL_SCOPE_ROLES = {
    "local_fixture_tests": "local_test",
    "local_test": "local_test",
    "runtime_validation": "runtime_output",
    "runtime_log": "runtime_log",
    "runtime_output": "runtime_output",
    "cluster_dry_run": "cluster_dry_run",
    "cluster_proof": "cluster_output",
    "cluster_scheduler": "cluster_scheduler",
    "cluster_log": "cluster_log",
    "cluster_output": "cluster_output",
}
COMPUTATIONAL_SCOPE_PLAN_FIELDS = {
    "local_fixture_tests": "local_test_status",
    "local_test": "local_test_status",
    "runtime_validation": "runtime_validation_status",
    "runtime_log": "runtime_validation_status",
    "runtime_output": "runtime_validation_status",
    "cluster_dry_run": "cluster_dry_run_status",
    "cluster_proof": "cluster_proof_status",
    "cluster_scheduler": "cluster_proof_status",
    "cluster_log": "cluster_proof_status",
    "cluster_output": "cluster_proof_status",
}
COMPUTATIONAL_VALIDATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "validation_scope",
    "validation_status",
    "evidence_path",
    "evidence_sha256",
    "scheduler_state",
    "exit_code",
    "reviewer",
    "evidence_date",
    "notes",
)


@dataclass(frozen=True)
class ReviewInput:
    """One source descriptor committed into the public review summary."""

    path: Path
    sha256: str
    row_count: str


@dataclass(frozen=True)
class TableData:
    """One strict UTF-8 TSV read by the reporting-local package reader."""

    header: tuple[str, ...]
    rows: list[dict[str, str]]
    path: Path


@dataclass
class ReviewPackageContext:
    """The public package projection required by run-summary reporting."""

    plan: dict[str, str]
    evidence_rows: list[dict[str, str]]
    category_rows: dict[str, list[dict[str, str]]]
    evidence_index_rows: list[dict[str, str]]
    artifacts: dict[str, ReviewInput]
    input_hashes: dict[Path, str]
    output_paths: dict[str, Path]


SCIENCE_SCHEMA_VERSION = "1.1.0"
PRODUCER = "build_run_summary"
PRODUCER_VERSION = "1.0.0"

PUBLISHED_ADAPTERS = {
    key: f"step09c_{key}_v1" for key, _ in review_package.OUTPUT_SUFFIXES
}
INPUT_ROLE_BY_STEP09C_KEY = {
    "sample_manifest": "sample_manifest",
    "partition_manifest": "partition_manifest",
    "step08_sites": "step08_sites",
    "step08_inputs": "step08_inputs",
    "step08_summary": "step08_summary",
    "step09_all_sites": "step09_all_sites",
    "step09_significant_sites": "step09_significant_sites",
    "step09_summary": "step09_summary",
    "step09_mutation_spectrum": "step09_mutation_spectrum_tsv",
    "step09_mutation_spectrum_pdf": "step09_mutation_spectrum_pdf",
    "step09_depth_delta_pdf": "step09_depth_delta_pdf",
    "review_plan": "review_plan",
    "evidence_manifest": "evidence_manifest",
}
class RunSummaryScienceError(RuntimeError):
    """Raised when Step 09c cannot be faithfully normalized."""


def _fail(message: str) -> None:
    raise RunSummaryScienceError(message)


def _absolute_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(Path(value).expanduser())))


def _require_regular_file(label: str, value: str | Path) -> Path:
    path = _absolute_path(value)
    try:
        metadata = path.lstat()
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(metadata.st_mode):
        _fail(f"{label} must not be a symbolic link: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        _fail(f"{label} is not a regular file: {path}")
    if metadata.st_size == 0:
        _fail(f"{label} is empty: {path}")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} cannot be resolved: {path}: {exc}")


def _require_contract_file(label: str, value: str) -> Path:
    return _require_regular_file(label, contracts.resolve_contract_path(value))


def _sha256_file(path: Path) -> str:
    return contracts.sha256_file(path)


def _read_tsv(
    label: str,
    value: str | Path,
    expected_header: Sequence[str],
) -> TableData:
    path = _require_regular_file(label, value)
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            raw_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")
    if not raw_rows:
        _fail(f"{label} is empty: {path}")
    header = tuple(raw_rows[0])
    if any(not column for column in header):
        _fail(f"{label} contains an empty header field: {path}")
    if len(header) != len(set(header)):
        _fail(f"{label} contains duplicate header fields: {path}")
    if header != tuple(expected_header):
        _fail(
            f"{label} header is invalid: {path}\n"
            f"Expected: {' | '.join(expected_header)}\n"
            f"Observed: {' | '.join(header)}"
        )
    rows: list[dict[str, str]] = []
    for index, values in enumerate(raw_rows[1:], start=2):
        if len(values) != len(header):
            _fail(
                f"{label} row {index} has {len(values)} fields; "
                f"expected {len(header)}: {path}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    return TableData(header=header, rows=rows, path=path)


def _resolve_recorded_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _confirm_inputs_unchanged(input_hashes: Mapping[Path, str]) -> None:
    for path, expected_hash in input_hashes.items():
        if not path.is_file():
            _fail(f"A reporting input disappeared during normalization: {path}")
        if _sha256_file(path) != expected_hash:
            _fail(f"A reporting input changed during normalization: {path}")


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


def _tsv_bytes(
    header: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(header),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _source_path_hash(
    *,
    path: Path,
    sha256: str,
    row_count: int | None,
    media_type: str,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256,
        "size_bytes": path.stat().st_size,
        "row_count": row_count,
        "media_type": media_type,
    }


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
    output_tables: Mapping[
        str, tuple[tuple[str, ...], list[dict[str, str]]]
    ],
) -> dict[str, Mapping[str, Any]]:
    review_id = summary_row["review_id"]
    expected_scope = ("09c", "scientific_review", review_id)
    scoped = [
        artifact
        for artifact in artifacts
        if _artifact_scope(artifact) == expected_scope
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

    by_key: dict[str, Mapping[str, Any]] = {}
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
        observed_table = _read_tsv(
            f"Published Step 09c {key}", actual_path, header
        )
        if observed_table.rows != rows:
            _fail(f"Published Step 09c {key} rows differ from reconstruction.")
        expected_bytes = _tsv_bytes(header, rows)
        try:
            observed_bytes = actual_path.read_bytes()
        except OSError as exc:
            _fail(f"Could not read published Step 09c {key}: {exc}")
        if observed_bytes != expected_bytes:
            _fail(
                f"Published Step 09c {key} bytes differ from reconstruction."
            )
        observed_hash = contracts.sha256_file(actual_path)
        if source.get("sha256") != observed_hash:
            _fail(
                f"Published Step 09c {key} rows differ from reconstruction."
            )
        if source.get("size_bytes") != len(observed_bytes):
            _fail(f"Indexed Step 09c artifact {adapter} byte size differs.")
        if source.get("row_count") != len(rows):
            _fail(f"Indexed Step 09c artifact {adapter} row count differs.")
        if source.get("media_type") != "text/tab-separated-values":
            _fail(f"Indexed Step 09c artifact {adapter} media type differs.")
        by_key[key] = artifact
    return by_key


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

    output_tables: dict[
        str, tuple[tuple[str, ...], list[dict[str, str]]]
    ] = {}
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
        remember_input(table.path, _sha256_file(table.path))

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
        observed_hash = _sha256_file(source_path)
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
                payload_hash = _sha256_file(payload_path)
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


def _match_upstream_artifact(
    *,
    role: str,
    step09c_artifact: ReviewInput,
    artifacts: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    step_id, scope_type, adapter, suffix = (
        contracts.SCIENCE_UPSTREAM_ROLE_CONTRACTS[role]
    )
    expected_row_count = _parse_row_count(
        f"Step 09c {role} row count", step09c_artifact.row_count
    )
    matches: list[Mapping[str, Any]] = []
    for artifact in artifacts:
        scope = _artifact_scope(artifact)
        if (
            scope[0] != step_id
            or scope[1] != scope_type
            or artifact.get("adapter") != adapter
            or artifact.get("completion_status") != "complete"
        ):
            continue
        source = artifact.get("source")
        if not isinstance(source, Mapping):
            continue
        source_value = source.get("path")
        if not isinstance(source_value, str):
            continue
        if not Path(source_value).name.endswith(suffix):
            continue
        indexed_path = contracts.resolve_contract_path(source_value)
        if indexed_path != step09c_artifact.path:
            continue
        if (
            source.get("sha256") != step09c_artifact.sha256
            or source.get("row_count") != expected_row_count
        ):
            continue
        matches.append(artifact)
    if len(matches) != 1:
        _fail(
            f"Scientific input role {role} must match exactly one complete "
            f"indexed Step {step_id} artifact; observed {len(matches)}."
        )
    return matches[0]


def _normalize_input_artifacts(
    *,
    context: ReviewPackageContext,
    artifacts: Sequence[Mapping[str, Any]],
    review_id: str,
    run_contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key in review_package.INPUT_ARTIFACT_KEYS:
        source_artifact = context.artifacts[key]
        role = INPUT_ROLE_BY_STEP09C_KEY[key]
        row_count = _parse_row_count(
            f"Step 09c input {role} row count", source_artifact.row_count
        )
        if role in contracts.SCIENCE_UPSTREAM_ROLE_CONTRACTS:
            indexed = _match_upstream_artifact(
                role=role,
                step09c_artifact=source_artifact,
                artifacts=artifacts,
            )
            artifact_id = indexed.get("artifact_id")
            if not isinstance(artifact_id, str):
                _fail(f"Indexed scientific input {role} has no artifact_id.")
            source = _artifact_source(
                indexed, label=f"Indexed scientific input {role}"
            )
            normalized_path = source.get("path")
            if not isinstance(normalized_path, str):
                _fail(f"Indexed scientific input {role} has no source path.")
        else:
            artifact_id = f"input.{review_id}.{role}"
            normalized_path = str(source_artifact.path)
        result.append(
            {
                "role": role,
                "artifact_id": artifact_id,
                "path": normalized_path,
                "sha256": source_artifact.sha256,
                "row_count": row_count,
            }
        )
    input_index = {record["role"]: record for record in result}
    if (
        input_index["sample_manifest"]["sha256"]
        != run_contract.get("sample_manifest_sha256")
    ):
        _fail("Step 09c sample-manifest hash differs from the run contract.")
    if (
        input_index["partition_manifest"]["sha256"]
        != run_contract.get("partition_manifest_sha256")
    ):
        _fail("Step 09c partition-manifest hash differs from the run contract.")
    return result


def _normalize_evidence(
    context: ReviewPackageContext,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    represented_ids: set[str] = set()
    for row in context.evidence_index_rows:
        status = row["evidence_status"]
        evidence_date = _nullable(row["evidence_date"])
        if (
            evidence_date is None
            and status in ("complete", "incomplete")
        ):
            _fail(
                f"Evidence {row['evidence_id']} has no evidence_date and "
                f"cannot represent {status} evidence."
            )
        if status in ("complete", "incomplete"):
            path = _require_regular_file(
                f"Scientific evidence {row['evidence_id']}",
                row["source_path"],
            )
            row_count = _parse_row_count(
                f"Scientific evidence {row['evidence_id']} row count",
                row["observed_row_count"],
            )
            if row_count is None:
                _fail(
                    f"Scientific evidence {row['evidence_id']} lacks a row "
                    "count."
                )
            source = _source_path_hash(
                path=path,
                sha256=row["observed_sha256"],
                row_count=row_count,
                media_type="text/tab-separated-values",
            )
        else:
            source = None
        records.append(
            {
                "evidence_id": row["evidence_id"],
                "category": row["evidence_category"],
                "analysis_id": row["analysis_id"],
                "status": status,
                "source": source,
                "reviewer": row["reviewer"],
                "owner": row["owner"],
                "evidence_date": evidence_date,
                "policy_version": row["policy_version"],
                "not_applicable_reason": (
                    row["not_applicable_reason"]
                    if status == "not_applicable"
                    else None
                ),
            }
        )
        represented_ids.add(row["evidence_id"])

    categories: dict[str, dict[str, Any]] = {}
    for category in review_package.CATEGORY_ORDER:
        rows = [
            row
            for row in context.evidence_index_rows
            if row["evidence_category"] == category
        ]
        status = review_package.aggregate_evidence_status(
            context.evidence_rows, category
        )
        reasons: list[str] = []
        if status == "not_applicable":
            for row in rows:
                reason = row["not_applicable_reason"]
                if reason not in reasons:
                    reasons.append(reason)
        categories[category] = {
            "status": status,
            "evidence_ids": [
                row["evidence_id"]
                for row in rows
                if row["evidence_id"] in represented_ids
            ],
            "not_applicable_reason": (
                "; ".join(reasons) if status == "not_applicable" else None
            ),
        }
    return categories, records


def _validate_computational_payload_status(
    *,
    evidence_id: str,
    validation_scope: str,
    validation_status: str,
    plan: Mapping[str, str],
) -> None:
    plan_field = COMPUTATIONAL_SCOPE_PLAN_FIELDS[validation_scope]
    expected = plan[plan_field]
    if validation_status != expected:
        _fail(
            f"Computational evidence {evidence_id} scope "
            f"{validation_scope} status "
            f"{validation_status!r} does not exactly support the declared "
            f"{plan_field} {expected!r}."
        )


def _normalize_computational_evidence(
    *,
    context: ReviewPackageContext,
    evidence_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    record_index = {
        record["evidence_id"]: record for record in evidence_records
    }
    rows_by_evidence: dict[str, list[dict[str, str]]] = {}
    for row in context.category_rows["computational_validation"]:
        rows_by_evidence.setdefault(row["evidence_id"], []).append(row)

    references: list[dict[str, str]] = []
    computational_rows = [
        row
        for row in context.evidence_index_rows
        if row["evidence_category"] == "computational_validation"
    ]
    for index_row in computational_rows:
        evidence_id = index_row["evidence_id"]
        if index_row["evidence_status"] != "complete":
            continue
        payload_rows = rows_by_evidence.get(evidence_id, [])
        if not payload_rows:
            _fail(
                f"Computational evidence {evidence_id} must contain at least "
                "one validation_scope row."
            )
        record = record_index[evidence_id]
        wrapper_source = record["source"]
        if not isinstance(wrapper_source, Mapping):
            _fail(
                f"Computational evidence {evidence_id} has no source "
                "descriptor."
            )
        for payload in payload_rows:
            validation_scope = payload["validation_scope"]
            role = COMPUTATIONAL_SCOPE_ROLES[validation_scope]
            _validate_computational_payload_status(
                evidence_id=evidence_id,
                validation_scope=validation_scope,
                validation_status=payload["validation_status"],
                plan=context.plan,
            )
            if payload["evidence_path"] == NA_VALUE:
                evidence_path = wrapper_source["path"]
                evidence_sha256 = wrapper_source["sha256"]
            else:
                evidence_path_object = _require_regular_file(
                    f"Computational payload {evidence_id} "
                    f"{validation_scope}",
                    _resolve_recorded_path(payload["evidence_path"]),
                )
                evidence_path = str(evidence_path_object)
                evidence_sha256 = payload["evidence_sha256"]
                if (
                    _sha256_file(evidence_path_object) != evidence_sha256
                ):
                    _fail(
                        f"Computational payload {evidence_id} "
                        f"{validation_scope} hash changed during "
                        "normalization."
                    )
            references.append(
                {
                    "evidence_id": evidence_id,
                    "role": role,
                    "path": evidence_path,
                    "sha256": evidence_sha256,
                }
            )
    return references


def _normalize_decisions(
    context: ReviewPackageContext,
) -> dict[str, dict[str, Any]]:
    by_dimension = {
        row["decision_dimension"]: row
        for row in context.category_rows["decisions"]
    }
    decisions: dict[str, dict[str, Any]] = {}
    for dimension in review_package.DECISION_DIMENSIONS:
        row = by_dimension.get(dimension)
        if row is None or row["decision_status"] == "pending":
            if (
                row is not None
                and row["supporting_evidence_ids"] != NA_VALUE
            ):
                _fail(
                    f"Pending decision {dimension} cannot carry supporting "
                    "evidence IDs in scientific-review-record v1."
                )
            decisions[dimension] = {
                "status": "pending",
                "value": None,
                "detail": None if row is None else row["rationale"],
                "reviewer": (
                    None if row is None else row["decision_owner"]
                ),
                "decision_date": None,
                "evidence_ids": [],
                "rerun_scope": "none" if row is None else row["rerun_scope"],
                "decision_id": (
                    None if row is None else row["decision_id"]
                ),
                "source_evidence_id": (
                    None if row is None else row["evidence_id"]
                ),
                "evidence_status": (
                    None if row is None else row["evidence_status"]
                ),
                "policy_version": (
                    None if row is None else row["policy_version"]
                ),
                "rerun_required": (
                    None
                    if row is None
                    else row["rerun_required"] == "TRUE"
                ),
            }
            continue
        decisions[dimension] = {
            "status": "recorded",
            "value": row["decision_value"],
            "detail": row["rationale"],
            "reviewer": row["decision_owner"],
            "decision_date": row["decision_date"],
            "evidence_ids": _split_ids(row["supporting_evidence_ids"]),
            "rerun_scope": row["rerun_scope"],
            "decision_id": row["decision_id"],
            "source_evidence_id": row["evidence_id"],
            "evidence_status": row["evidence_status"],
            "policy_version": row["policy_version"],
            "rerun_required": row["rerun_required"] == "TRUE",
        }
    return decisions


def _normalize_limitations(
    context: ReviewPackageContext,
) -> list[dict[str, Any]]:
    statuses = {
        "active": "open",
        "open": "open",
        "accepted": "accepted",
        "resolved": "resolved",
    }
    limitations: list[dict[str, Any]] = []
    for row in context.category_rows["limitations"]:
        status = statuses.get(row["limitation_status"])
        if status is None:
            _fail(
                f"Limitation {row['limitation_id']} has unsupported status "
                f"{row['limitation_status']!r}."
            )
        limitations.append(
            {
                "limitation_id": row["limitation_id"],
                "status": status,
                "description": row["description"],
                "impact": row["impact"],
                "category": row["limitation_category"],
                "severity": row["severity"],
                "mitigation": row["mitigation"],
                "owner": row["owner"],
                "review_date": row["review_date"],
                "evidence_ids": _split_ids(row["related_evidence_ids"]),
            }
        )
    return limitations


def _validate_normalized_record(document: dict[str, Any]) -> None:
    try:
        schemas, registry = contracts.load_schema_registry()
        validator = Draft202012Validator(
            schemas["scientific-review-record"],
            registry=registry,
            format_checker=FormatChecker(),
        )
        errors = sorted(
            validator.iter_errors(document),
            key=lambda error: tuple(
                str(part) for part in error.absolute_path
            ),
        )
        if errors:
            details = "\n".join(
                f"- {contracts.format_json_path(error.absolute_path)}: "
                f"{error.message}"
                for error in errors
            )
            _fail(
                "Normalized Step 09c scientific review failed its Draft "
                f"2020-12 schema:\n{details}"
            )
        contracts.validate_scientific_review_semantics(document)
    except contracts.ContractValidationError as exc:
        _fail(
            "Normalized Step 09c scientific review failed semantic "
            f"validation: {exc}"
        )


def normalize_scientific_review(
    *,
    summary_path: Path,
    artifacts: list[dict[str, Any]],
    run_id: str,
    run_contract: Mapping[str, Any],
    generated_at: str,
    git_commit: str,
) -> dict[str, Any]:
    """Revalidate and normalize one explicit committed Step 09c transaction."""

    try:
        normalized_summary_path = _require_regular_file(
            "Explicit Step 09c review summary", summary_path
        )
        summary_table = _read_tsv(
            "Explicit Step 09c review summary",
            normalized_summary_path,
            review_package.REVIEW_SUMMARY_HEADER,
        )
        if len(summary_table.rows) != 1:
            _fail("The explicit Step 09c review summary must contain one row.")
        summary_row = summary_table.rows[0]
        if summary_row["transaction_state"] != "complete":
            _fail("The explicit Step 09c review summary is not committed.")
        if summary_row["published_output_count"] != str(
            len(review_package.OUTPUT_SUFFIXES)
        ):
            _fail("The Step 09c review summary does not declare 13 outputs.")
        if (
            summary_row["overall_science_status"]
            == "biological_interpretation_ready"
        ):
            _fail(
                "biological_interpretation_ready is reserved and cannot be "
                "normalized by scientific-review-record v1."
            )
        if summary_row["overall_science_status"] not in {
            "evidence_incomplete",
            "science_review_complete_exploratory",
        }:
            _fail(
                "The Step 09c review summary declares an unsupported science "
                f"state: {summary_row['overall_science_status']!r}."
            )
        if summary_row["primary_analysis_id"] != run_contract.get(
            "primary_analysis_id"
        ):
            _fail(
                "The Step 09c primary analysis differs from the immutable "
                "run contract."
            )
        summary_sha256 = contracts.sha256_file(normalized_summary_path)
        summary_artifact = _validate_summary_artifact(
            summary_path=normalized_summary_path,
            artifacts=artifacts,
            summary_row=summary_row,
            summary_sha256=summary_sha256,
        )

        context, output_tables = _read_committed_review_package(
            summary_path=normalized_summary_path,
            summary_row=summary_row,
        )
        _validate_published_artifacts(
            summary_path=normalized_summary_path,
            summary_row=summary_row,
            artifacts=artifacts,
            summary_artifact=summary_artifact,
            output_tables=output_tables,
        )
        input_artifacts = _normalize_input_artifacts(
            context=context,
            artifacts=artifacts,
            review_id=summary_row["review_id"],
            run_contract=run_contract,
        )
        evidence_categories, evidence_records = _normalize_evidence(context)
        computational_evidence = _normalize_computational_evidence(
            context=context,
            evidence_records=evidence_records,
        )
        summary_source = _artifact_source(
            summary_artifact, label="Step 09c review summary"
        )
        document: dict[str, Any] = {
            "schema_name": "norad.scientific_review_record",
            "schema_version": SCIENCE_SCHEMA_VERSION,
            "record_type": "scientific_review_record",
            "run_id": run_id,
            "run_contract": dict(run_contract),
            "review_id": summary_row["review_id"],
            "primary_analysis_id": summary_row["primary_analysis_id"],
            "superseded_analysis_ids": _split_ids(
                summary_row["superseded_analysis_ids"]
            ),
            "sensitivity_analysis_ids": _split_ids(
                summary_row["sensitivity_analysis_ids"]
            ),
            "review_metadata": {
                "plan_version": summary_row["plan_version"],
                "plan_date": summary_row["plan_date"],
                "reviewer": summary_row["reviewer"],
                "decision_owner": summary_row["decision_owner"],
                "git_commit": summary_row["git_commit"],
                "review_completed_date": _nullable(
                    summary_row["review_completed_date"]
                ),
            },
            "computational_status": {
                "implementation_status": summary_row[
                    "implementation_status"
                ],
                "local_test_status": summary_row["local_test_status"],
                "runtime_validation_status": summary_row[
                    "runtime_validation_status"
                ],
                "cluster_dry_run_status": summary_row[
                    "cluster_dry_run_status"
                ],
                "cluster_proof_status": summary_row[
                    "cluster_proof_status"
                ],
                "evidence": computational_evidence,
            },
            "scientific_state": {
                "overall_status": summary_row["overall_science_status"],
                "orientation_status": summary_row["orientation_status"],
                "orientation_policy": summary_row["orientation_policy"],
                "orientation_policy_version": summary_row[
                    "orientation_policy_version"
                ],
            },
            "readiness_authorization": None,
            "policy_versions": {
                "locus_selection": summary_row[
                    "locus_selection_policy_version"
                ],
                "candidate_selection": summary_row[
                    "candidate_selection_policy_version"
                ],
                "sensitivity": summary_row[
                    "sensitivity_policy_version"
                ],
                "background": summary_row[
                    "background_policy_version"
                ],
                "annotation": summary_row[
                    "annotation_policy_version"
                ],
                "adjudication": summary_row[
                    "adjudication_policy_version"
                ],
            },
            "selection_rules": {
                "locus_selection": summary_row["locus_selection_rule"],
                "candidate_selection": summary_row[
                    "candidate_selection_rule"
                ],
                "sensitivity": summary_row["sensitivity_rule"],
                "leave_one_pair_out": summary_row[
                    "leave_one_pair_out_rule"
                ],
            },
            "evidence_categories": evidence_categories,
            "evidence_records": evidence_records,
            "decisions": _normalize_decisions(context),
            "input_artifacts": input_artifacts,
            "review_summary": {
                "path": summary_source["path"],
                "sha256": summary_sha256,
                "size_bytes": summary_source["size_bytes"],
                "row_count": 1,
                "media_type": "text/tab-separated-values",
            },
            "limitations": _normalize_limitations(context),
            "warnings": [],
            "errors": [],
            "provenance": {
                "producer": PRODUCER,
                "producer_version": PRODUCER_VERSION,
                "git_commit": git_commit,
                "created_at": generated_at,
            },
        }
        _confirm_inputs_unchanged(context.input_hashes)
        _validate_normalized_record(document)
        return document
    except RunSummaryScienceError:
        raise
    except contracts.ContractValidationError as exc:
        raise RunSummaryScienceError(
            f"Artifact-contract validation failed during normalization: {exc}"
        ) from exc
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RunSummaryScienceError(
            f"Could not normalize the Step 09c scientific review: {exc}"
        ) from exc
