"""Shared artifact-contract schema, identity, path, and evidence rules."""

from __future__ import annotations

import glob
import hashlib
import json
import re
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

from norad.contracts.scientific_evidence import review_package

_MODULE_PATH = Path(__file__).resolve()

if (src_root := str(_MODULE_PATH.parents[3])) not in sys.path:
    sys.path.insert(0, src_root)
from norad.libraries import validation as report

REPO_ROOT = _MODULE_PATH.parents[5]
SCHEMA_ROOT = _MODULE_PATH.parents[2] / "schemas" / "artifacts" / "v1"
COMMON_SCHEMA_PATH = SCHEMA_ROOT / "common.schema.json"
SCHEMA_FILES = {
    "artifact-record": SCHEMA_ROOT / "artifact_record.schema.json",
    "scientific-review-record": (SCHEMA_ROOT / "scientific_review_record.schema.json"),
    "run-summary": SCHEMA_ROOT / "run_summary.schema.json",
    "report-receipt": SCHEMA_ROOT / "report_receipt.schema.json",
}
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
BOOLEAN_VALUES = {"true", "false"}
SCOPE_TYPES = {
    "reference",
    "sample",
    "cohort_partition",
    "cohort",
    "analysis",
    "scientific_review",
}
SCIENCE_INPUT_ROLES = set(review_package.INPUT_ARTIFACT_ROLES.values())
SCIENCE_UPSTREAM_ROLE_CONTRACTS = {
    "step08_sites": ("08", "cohort", "step08_sites_v1", ".step08_sites.tsv"),
    "step08_inputs": ("08", "cohort", "step08_inputs_v1", ".step08_inputs.tsv"),
    "step08_summary": (
        "08",
        "cohort",
        "step08_summary_v1",
        ".step08_summary.tsv",
    ),
    "step09_all_sites": (
        "09",
        "analysis",
        "step09_cmh_all_sites_v1",
        ".cmh_all_sites.tsv",
    ),
    "step09_significant_sites": (
        "09",
        "analysis",
        "step09_cmh_significant_sites_v1",
        ".cmh_significant_sites.tsv",
    ),
    "step09_summary": (
        "09",
        "analysis",
        "step09_cmh_summary_v1",
        ".cmh_summary.tsv",
    ),
    "step09_mutation_spectrum_tsv": (
        "09",
        "analysis",
        "step09_mutation_spectrum_tsv_v1",
        ".mutation_spectrum.tsv",
    ),
    "step09_mutation_spectrum_pdf": (
        "09",
        "analysis",
        "step09_mutation_spectrum_pdf_v1",
        ".mutation_spectrum.pdf",
    ),
    "step09_depth_delta_pdf": (
        "09",
        "analysis",
        "step09_depth_delta_pdf_v1",
        ".depth_delta.pdf",
    ),
}
RUN_CONTRACT_COMPONENT_FIELDS = (
    "sample_manifest_sha256",
    "reference_contract_sha256",
    "partition_manifest_sha256",
    "primary_analysis_id",
    "primary_analysis_policy_sha256",
)
_COMPUTATIONAL_STATUS_ROLE_REQUIREMENTS = {
    "local testing": {
        "passed": {"local_test"},
        "failed": {"local_test"},
    },
    "runtime validation": {
        "passed": {"runtime_log", "runtime_output"},
        "failed": {"runtime_log"},
    },
}
_CLUSTER_VALIDATION_REQUIREMENTS = (
    ("cluster dry-run validation", "dry_run_status", {"passed", "failed"}, {"cluster_dry_run"}),
    ("cluster proof", "proof_status", {"proven"}, {"cluster_scheduler", "cluster_log", "cluster_output"}),
    ("failed cluster proof", "proof_status", {"failed"}, {"cluster_log"}),
)
_CLUSTER_VALIDATION_TRIGGER_STATUSES = {"passed", "failed", "proven"}


class ContractValidationError(RuntimeError):
    """Raised when a schema, record, or inventory contract is invalid."""


def reject_duplicate_json_keys(
    pairs: Iterable[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractValidationError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def reject_nonstandard_json_constant(value: str) -> None:
    raise ContractValidationError(
        f"Non-standard JSON numeric constant is not allowed: {value}"
    )


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ContractValidationError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise ContractValidationError(f"{label} is not a file: {path}")
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(
                stream,
                object_pairs_hook=reject_duplicate_json_keys,
                parse_constant=reject_nonstandard_json_constant,
            )
    except ContractValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"Could not parse {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractValidationError(f"{label} must contain a JSON object: {path}")
    return value


def load_schema(name: str) -> dict[str, Any]:
    schemas, _ = load_schema_registry()
    return schemas[name]


def load_schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schema_paths = {"common": COMMON_SCHEMA_PATH, **SCHEMA_FILES}
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for name, schema_path in schema_paths.items():
        schema = load_json_object(schema_path, f"{name} schema")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ContractValidationError(
                f"{name} schema is not valid Draft 2020-12: {exc.message}"
            ) from exc
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ContractValidationError(f"{name} schema must define a non-empty $id")
        try:
            registry = registry.with_resource(
                schema_id,
                Resource.from_contents(schema),
            )
        except Exception as exc:
            raise ContractValidationError(
                f"Could not register local {name} schema: {exc}"
            ) from exc
        schemas[name] = schema
    return schemas, registry


def schema_validator(name: str) -> Draft202012Validator:
    """Build a validator from the closed local registry for one named schema."""
    schemas, registry = load_schema_registry()
    return Draft202012Validator(
        schemas[name],
        registry=registry,
        format_checker=FormatChecker(),
    )


def schema_errors(name: str, document: Any) -> list[Any]:
    """Order errors deterministically while callers retain message ownership."""
    return sorted(
        schema_validator(name).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )


def validate_all_schemas() -> None:
    schemas, _ = load_schema_registry()
    for name in schemas:
        print(f"Schema passed Draft 2020-12 validation: {name}")


def format_json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def sha256_file(path: Path) -> str:
    try:
        return report.sha256_file(path)
    except OSError as exc:
        raise ContractValidationError(f"Could not hash {path}: {exc}") from exc


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


def validate_resolved_path(value: str, label: str) -> None:
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
    path = Path(value)
    if any(part in {".", ".."} for part in path.parts):
        raise ContractValidationError(
            f"{label} must be normalized without '.' or '..' components: {value}"
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


def require_status_evidence(
    *,
    label: str,
    status: str,
    evidence: list[dict[str, Any]],
    evidence_statuses: set[str],
) -> None:
    if status in evidence_statuses and not evidence:
        raise ContractValidationError(
            f"{label} status {status!r} requires at least one evidence record"
        )


def require_evidence_roles(
    *,
    label: str,
    evidence: list[dict[str, Any]],
    required_roles: set[str],
) -> None:
    observed_roles = {record["role"] for record in evidence}
    missing_roles = sorted(required_roles - observed_roles)
    if missing_roles:
        raise ContractValidationError(
            f"{label} requires evidence roles: " + ", ".join(missing_roles)
        )


def validate_evidence_references(
    evidence: list[dict[str, Any]],
    label: str,
    *,
    allow_shared_evidence_ids: bool,
) -> None:
    if not allow_shared_evidence_ids:
        for field in ("evidence_id", "role", "path"):
            if len({record[field] for record in evidence}) != len(evidence):
                raise ContractValidationError(
                    f"{label} contains duplicate evidence {field}"
                )
        return
    if len({
        (
            record["evidence_id"],
            record["role"],
            record["path"],
            record["sha256"],
        )
        for record in evidence
    }) != len(evidence):
        raise ContractValidationError(
            f"{label} contains a duplicate evidence reference"
        )


def validate_computational_statuses(
    *,
    label: str,
    local_testing: dict[str, Any],
    runtime_validation: dict[str, Any],
    cluster_validation: dict[str, Any],
    allow_shared_evidence_ids: bool = False,
) -> None:
    status_scopes = (
        ("local testing", local_testing),
        ("runtime validation", runtime_validation),
        ("cluster validation", cluster_validation),
    )
    for scope_name, scope in status_scopes:
        validate_evidence_references(
            scope["evidence"],
            f"{label} {scope_name}",
            allow_shared_evidence_ids=allow_shared_evidence_ids,
        )
    for scope_name, scope in status_scopes[:2]:
        scope_status = scope["status"]
        scope_evidence = scope["evidence"]
        scope_label = f"{label} {scope_name}"
        require_status_evidence(
            label=scope_label,
            status=scope_status,
            evidence=scope_evidence,
            evidence_statuses={"passed", "failed"},
        )
        if required_roles := _COMPUTATIONAL_STATUS_ROLE_REQUIREMENTS[scope_name].get(scope_status):
            require_evidence_roles(
                label=scope_label,
                evidence=scope_evidence,
                required_roles=required_roles,
            )
    if runtime_validation["status"] == "blocked" and not runtime_validation["detail"].strip():
        raise ContractValidationError(
            f"{label} blocked runtime validation requires a detail"
        )
    cluster_statuses = {
        cluster_validation["dry_run_status"],
        cluster_validation["proof_status"],
    }
    if _CLUSTER_VALIDATION_TRIGGER_STATUSES & cluster_statuses and not (
        cluster_validation["evidence"]
    ):
        raise ContractValidationError(
            f"{label} passed, failed, or proven cluster validation requires "
            "at least one inspected evidence record"
        )
    for scope_name, scope_field, triggering_statuses, required_roles in _CLUSTER_VALIDATION_REQUIREMENTS:
        if cluster_validation[scope_field] in triggering_statuses:
            require_evidence_roles(
                label=f"{label} {scope_name}",
                evidence=cluster_validation["evidence"],
                required_roles=required_roles,
            )
    if cluster_validation["proof_status"] == "proven" and runtime_validation["status"] != "passed":
        raise ContractValidationError(
            f"{label} cluster proof requires passed runtime validation"
        )


def resolve_contract_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()
