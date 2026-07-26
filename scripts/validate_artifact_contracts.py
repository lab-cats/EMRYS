#!/usr/bin/env python3
"""Validate NORAD artifact-schema-v1 JSON records and explicit inventories.

This command is read-only. It validates tracked JSON Schema documents, one
explicit JSON record at a time, and/or one explicit expected-artifact
inventory. It never searches for pipeline outputs or expands path globs.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "schemas" / "artifacts" / "v1"
COMMON_SCHEMA_PATH = SCHEMA_ROOT / "common.schema.json"
SCHEMA_FILES = {
    "artifact-record": SCHEMA_ROOT / "artifact_record.schema.json",
    "scientific-review-record": (
        SCHEMA_ROOT / "scientific_review_record.schema.json"
    ),
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
SCIENCE_INPUT_ROLES = {
    "sample_manifest",
    "partition_manifest",
    "step08_sites",
    "step08_inputs",
    "step08_summary",
    "step09_all_sites",
    "step09_significant_sites",
    "step09_summary",
    "step09_mutation_spectrum_tsv",
    "step09_mutation_spectrum_pdf",
    "step09_depth_delta_pdf",
    "review_plan",
    "evidence_manifest",
}
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


class ContractValidationError(RuntimeError):
    """Raised when a schema, record, or inventory contract is invalid."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate artifact-schema-v1 schemas, a named JSON record, "
            "and/or an explicit expected-artifact inventory."
        )
    )
    parser.add_argument(
        "--check-schemas",
        action="store_true",
        help="Validate all four tracked schemas against Draft 2020-12.",
    )
    parser.add_argument(
        "--schema",
        choices=tuple(SCHEMA_FILES),
        help="Schema name for --document.",
    )
    parser.add_argument(
        "--document",
        type=Path,
        help="Explicit JSON document to validate.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Explicit expected-artifact inventory TSV to validate.",
    )
    args = parser.parse_args()

    if (args.schema is None) != (args.document is None):
        parser.error("--schema and --document must be supplied together")
    if not args.check_schemas and args.document is None and args.inventory is None:
        parser.error(
            "select at least one action: --check-schemas, "
            "--schema/--document, or --inventory"
        )
    return args


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
            raise ContractValidationError(
                f"{name} schema must define a non-empty $id"
            )
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


def validate_document(name: str, document_path: Path) -> dict[str, Any]:
    schemas, registry = load_schema_registry()
    schema = schemas[name]
    document = load_json_object(document_path, f"{name} document")
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        details = "\n".join(
            f"- {format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ContractValidationError(
            f"{name} document failed validation: {document_path}\n{details}"
        )
    validate_document_semantics(name, document)
    print(f"JSON document passed {name}: {document_path}")
    return document


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ContractValidationError(f"Could not hash {path}: {exc}") from exc
    return digest.hexdigest()


def canonical_run_contract_sha256(run_contract: dict[str, Any]) -> str:
    components = {
        field: run_contract[field] for field in RUN_CONTRACT_COMPONENT_FIELDS
    }
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
        raise ContractValidationError(
            f"{label} contains an invalid control character"
        )
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
            f"{label} must be normalized without '.' or '..' components: "
            f"{value}"
        )


def validate_document_paths(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if (
                isinstance(child, str)
                and (key == "path" or key.endswith("_path"))
            ):
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
                f"{label} contains duplicate {key} {value!r} "
                f"at array index {index}"
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
                f"{label} attempt {attempt_id!r} supersedes unknown attempt "
                f"{parent!r}"
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
                    f"{label} attempt supersession contains a cycle at "
                    f"{current!r}"
                )
            visited.add(current)
            current = indexed[current]["supersedes_attempt_id"]

    for attempt_id, attempt in indexed.items():
        started_at = attempt["started_at"]
        finished_at = attempt["finished_at"]
        if started_at is not None and finished_at is not None:
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            if finished < started:
                raise ContractValidationError(
                    f"{label} attempt {attempt_id!r} finishes before it starts"
                )
        parent_id = attempt["supersedes_attempt_id"]
        if parent_id is not None:
            parent_finished_at = indexed[parent_id]["finished_at"]
            if started_at is not None and parent_finished_at is not None:
                started = datetime.fromisoformat(
                    started_at.replace("Z", "+00:00")
                )
                parent_finished = datetime.fromisoformat(
                    parent_finished_at.replace("Z", "+00:00")
                )
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
            values = [record[field] for record in evidence]
            if len(values) != len(set(values)):
                raise ContractValidationError(
                    f"{label} contains duplicate evidence {field}"
                )
        return
    keys = [
        (
            record["evidence_id"],
            record["role"],
            record["path"],
            record["sha256"],
        )
        for record in evidence
    ]
    if len(keys) != len(set(keys)):
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
    validate_evidence_references(
        local_testing["evidence"],
        f"{label} local testing",
        allow_shared_evidence_ids=allow_shared_evidence_ids,
    )
    validate_evidence_references(
        runtime_validation["evidence"],
        f"{label} runtime validation",
        allow_shared_evidence_ids=allow_shared_evidence_ids,
    )
    validate_evidence_references(
        cluster_validation["evidence"],
        f"{label} cluster validation",
        allow_shared_evidence_ids=allow_shared_evidence_ids,
    )
    require_status_evidence(
        label=f"{label} local testing",
        status=local_testing["status"],
        evidence=local_testing["evidence"],
        evidence_statuses={"passed", "failed"},
    )
    if local_testing["status"] in {"passed", "failed"}:
        require_evidence_roles(
            label=f"{label} local testing",
            evidence=local_testing["evidence"],
            required_roles={"local_test"},
        )
    require_status_evidence(
        label=f"{label} runtime validation",
        status=runtime_validation["status"],
        evidence=runtime_validation["evidence"],
        evidence_statuses={"passed", "failed"},
    )
    if runtime_validation["status"] == "passed":
        require_evidence_roles(
            label=f"{label} passed runtime validation",
            evidence=runtime_validation["evidence"],
            required_roles={"runtime_log", "runtime_output"},
        )
    elif runtime_validation["status"] == "failed":
        require_evidence_roles(
            label=f"{label} failed runtime validation",
            evidence=runtime_validation["evidence"],
            required_roles={"runtime_log"},
        )
    if (
        runtime_validation["status"] == "blocked"
        and not runtime_validation["detail"].strip()
    ):
        raise ContractValidationError(
            f"{label} blocked runtime validation requires a detail"
        )
    cluster_statuses = {
        cluster_validation["dry_run_status"],
        cluster_validation["proof_status"],
    }
    if cluster_statuses & {"passed", "failed", "proven"} and not (
        cluster_validation["evidence"]
    ):
        raise ContractValidationError(
            f"{label} passed, failed, or proven cluster validation requires "
            "at least one inspected evidence record"
        )
    if cluster_validation["dry_run_status"] in {"passed", "failed"}:
        require_evidence_roles(
            label=f"{label} cluster dry-run validation",
            evidence=cluster_validation["evidence"],
            required_roles={"cluster_dry_run"},
        )
    if cluster_validation["proof_status"] == "proven":
        if runtime_validation["status"] != "passed":
            raise ContractValidationError(
                f"{label} cluster proof requires passed runtime validation"
            )
        require_evidence_roles(
            label=f"{label} cluster proof",
            evidence=cluster_validation["evidence"],
            required_roles={
                "cluster_scheduler",
                "cluster_log",
                "cluster_output",
            },
        )
    elif cluster_validation["proof_status"] == "failed":
        require_evidence_roles(
            label=f"{label} failed cluster proof",
            evidence=cluster_validation["evidence"],
            required_roles={"cluster_log"},
        )


def validate_artifact_semantics(document: dict[str, Any]) -> None:
    validate_run_contract(
        document["run_contract"],
        f"artifact {document['artifact_id']!r}",
    )
    validate_document_paths(document)
    attempts = document["attempts"]
    attempt_index = validate_attempt_graph(
        attempts,
        selected_attempt_id=document["selected_attempt_id"],
        label=f"artifact {document['artifact_id']!r}",
    )
    selected_attempt_id = document["selected_attempt_id"]
    if selected_attempt_id is not None:
        selected = attempt_index[selected_attempt_id]
        superseded_ids = {
            attempt["supersedes_attempt_id"]
            for attempt in attempts
            if attempt["supersedes_attempt_id"] is not None
        }
        if selected_attempt_id in superseded_ids:
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} selected attempt "
                "has been superseded"
            )
        completion = document["completion_status"]
        if completion == "complete" and selected["state"] != "succeeded":
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} complete state "
                "must select a succeeded attempt"
            )
        if completion == "failed" and selected["state"] != "failed":
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} failed state "
                "must select a failed attempt"
            )
        if completion == "in_progress" and selected["state"] != "running":
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} in-progress state "
                "must select a running attempt"
            )
        if completion == "incomplete" and selected["state"] not in {
            "failed",
            "cancelled",
            "blocked",
        }:
            raise ContractValidationError(
                f"artifact {document['artifact_id']!r} incomplete state "
                "must select a failed, cancelled, or blocked attempt"
            )

    validate_computational_statuses(
        label=f"artifact {document['artifact_id']!r}",
        local_testing=document["local_testing"],
        runtime_validation=document["runtime_validation"],
        cluster_validation=document["cluster_validation"],
    )

    members = document["members"]
    require_unique_key(members, "member_id", "artifact members")
    member_paths = [member["path"] for member in members]
    canonical_member_paths = [
        resolve_contract_path(path) for path in member_paths
    ]
    if len(canonical_member_paths) != len(set(canonical_member_paths)):
        raise ContractValidationError("artifact members contain duplicate paths")
    if document["source"] is not None and (
        document["source"]["path"] != document["expectation"]["source_path"]
    ):
        raise ContractValidationError(
            "artifact source path does not match its explicit inventory "
            "expectation"
        )
    if (
        document["source"] is None
        and resolve_contract_path(document["expectation"]["source_path"])
        in canonical_member_paths
    ):
        raise ContractValidationError(
            "artifact member cannot claim the absent expected source path"
        )
    if document["source"] is not None:
        matching_members = [
            member
            for member in members
            if resolve_contract_path(member["path"])
            == resolve_contract_path(document["source"]["path"])
        ]
        if matching_members:
            member = matching_members[0]
            for field in ("sha256", "size_bytes", "row_count", "media_type"):
                if document["source"].get(field) != member.get(field):
                    raise ContractValidationError(
                        "artifact source and same-path member disagree on "
                        f"{field}"
                    )

    completion = document["completion_status"]
    if completion != "complete" and not document["state_reason"].strip():
        raise ContractValidationError(
            "non-complete artifact state_reason must contain non-whitespace text"
        )
    if completion == "failed" and not document["errors"]:
        raise ContractValidationError(
            "failed artifact must record at least one error"
        )
    if completion == "incomplete" and not (
        document["warnings"] or document["errors"]
    ):
        raise ContractValidationError(
            "incomplete artifact must record at least one warning or error"
        )


def validate_scientific_review_semantics(document: dict[str, Any]) -> None:
    validate_run_contract(
        document["run_contract"],
        f"scientific review {document['review_id']!r}",
    )
    validate_document_paths(document)
    computational_status = document["computational_status"]
    validate_computational_statuses(
        label=f"scientific review {document['review_id']!r}",
        local_testing={
            "status": computational_status["local_test_status"],
            "evidence": computational_status["evidence"],
        },
        runtime_validation={
            "status": computational_status["runtime_validation_status"],
            "detail": (
                "Scientific runtime validation is blocked."
                if computational_status["runtime_validation_status"] == "blocked"
                else None
            ),
            "evidence": computational_status["evidence"],
        },
        cluster_validation={
            "dry_run_status": computational_status["cluster_dry_run_status"],
            "proof_status": computational_status["cluster_proof_status"],
            "evidence": computational_status["evidence"],
        },
        allow_shared_evidence_ids=True,
    )

    primary_analysis_id = document["primary_analysis_id"]
    superseded_analysis_ids = set(document["superseded_analysis_ids"])
    sensitivity_analysis_ids = set(document["sensitivity_analysis_ids"])
    if primary_analysis_id in superseded_analysis_ids | sensitivity_analysis_ids:
        raise ContractValidationError(
            "scientific review primary analysis cannot also be superseded "
            "or sensitivity analysis"
        )
    overlapping_alternates = (
        superseded_analysis_ids & sensitivity_analysis_ids
    )
    if overlapping_alternates:
        raise ContractValidationError(
            "scientific review superseded and sensitivity analysis IDs "
            "overlap: "
            + ", ".join(sorted(overlapping_alternates))
        )
    allowed_analysis_ids = {
        primary_analysis_id,
        *superseded_analysis_ids,
        *sensitivity_analysis_ids,
    }

    evidence_index = require_unique_key(
        document["evidence_records"],
        "evidence_id",
        "scientific evidence records",
    )
    evidence_ids = set(evidence_index)
    for evidence_id, record in evidence_index.items():
        if record["analysis_id"] not in allowed_analysis_ids:
            raise ContractValidationError(
                f"scientific evidence {evidence_id!r} names undeclared "
                f"analysis {record['analysis_id']!r}"
            )

    computational_evidence_ids = {
        reference["evidence_id"]
        for reference in computational_status["evidence"]
    }
    unknown_computational = sorted(
        computational_evidence_ids - evidence_ids
    )
    if unknown_computational:
        raise ContractValidationError(
            "scientific computational status references unknown evidence IDs: "
            + ", ".join(unknown_computational)
        )
    computational_reference_keys: set[tuple[str, str]] = set()
    for reference in computational_status["evidence"]:
        reference_key = (reference["evidence_id"], reference["role"])
        if reference_key in computational_reference_keys:
            raise ContractValidationError(
                "scientific computational evidence repeats evidence_id/role: "
                + "/".join(reference_key)
            )
        computational_reference_keys.add(reference_key)
        record = evidence_index[reference["evidence_id"]]
        if (
            record["category"] != "computational_validation"
            or record["status"] != "complete"
            or record["source"] is None
        ):
            raise ContractValidationError(
                f"scientific computational evidence "
                f"{reference['evidence_id']!r} must resolve to one complete "
                "computational_validation record"
            )

    # Every computational_validation record is owned by the independent
    # computational-status panel. Only complete records that directly support
    # a declared status are promoted into its typed evidence references; any
    # incomplete, missing, or not-applicable declarations remain explicit in
    # evidence_records without becoming proof.
    referenced_evidence_ids = {
        evidence_id
        for evidence_id, record in evidence_index.items()
        if record["category"] == "computational_validation"
    }
    for category_name, category in document["evidence_categories"].items():
        referenced_ids = category["evidence_ids"]
        unknown = sorted(set(referenced_ids) - evidence_ids)
        if unknown:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} references "
                "unknown evidence IDs: "
                + ", ".join(unknown)
            )
        records = [evidence_index[evidence_id] for evidence_id in referenced_ids]
        mismatched_categories = [
            record["evidence_id"]
            for record in records
            if record["category"] != category_name
        ]
        if mismatched_categories:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} references "
                "records assigned to another category: "
                + ", ".join(mismatched_categories)
            )
        if category_name in {"sensitivity_matrix", "leave_one_pair_out"}:
            allowed_category_analysis_ids = {
                primary_analysis_id,
                *sensitivity_analysis_ids,
            }
        else:
            allowed_category_analysis_ids = {primary_analysis_id}
        wrong_category_analyses = [
            record["evidence_id"]
            for record in records
            if record["analysis_id"] not in allowed_category_analysis_ids
        ]
        if wrong_category_analyses:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} references "
                "evidence for an analysis not allowed by that category: "
                + ", ".join(wrong_category_analyses)
            )
        referenced_evidence_ids.update(referenced_ids)
        status = category["status"]
        if status in {"complete", "incomplete"} and not records:
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} status "
                f"{status!r} requires at least one evidence record"
            )
        if status == "complete" and (
            any(
                record["status"] not in {"complete", "not_applicable"}
                for record in records
            )
            or not any(record["status"] == "complete" for record in records)
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is complete "
                "without at least one complete record or contains missing/"
                "incomplete evidence"
            )
        if status == "incomplete" and not any(
            record["status"] in {"missing", "incomplete"} for record in records
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is incomplete "
                "without missing or incomplete evidence"
            )
        if status == "not_applicable" and any(
            record["status"] != "not_applicable" for record in records
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is "
                "not_applicable but references applicable evidence"
            )
        if status == "missing" and any(
            record["status"] != "missing" for record in records
        ):
            raise ContractValidationError(
                f"scientific evidence category {category_name!r} is missing "
                "but references non-missing evidence"
            )
    for decision_name, decision in document["decisions"].items():
        unknown = sorted(set(decision["evidence_ids"]) - evidence_ids)
        if unknown:
            raise ContractValidationError(
                f"scientific decision {decision_name!r} references unknown "
                "evidence IDs: "
                + ", ".join(unknown)
            )
        referenced_evidence_ids.update(decision["evidence_ids"])
        if decision["status"] == "recorded" and not decision["evidence_ids"]:
            raise ContractValidationError(
                f"scientific decision {decision_name!r} is recorded without "
                "supporting evidence"
            )
        if decision["status"] == "recorded" and any(
            evidence_index[evidence_id]["status"]
            not in {"complete", "not_applicable"}
            for evidence_id in decision["evidence_ids"]
        ):
            raise ContractValidationError(
                f"scientific decision {decision_name!r} cites missing or "
                "incomplete evidence"
            )
    orientation_decision = document["decisions"]["orientation"]
    if (
        orientation_decision["status"] == "recorded"
        and orientation_decision["value"]
        != document["scientific_state"]["orientation_status"]
    ):
        raise ContractValidationError(
            "recorded orientation decision value must match "
            "scientific_state.orientation_status"
        )

    input_index = require_unique_key(
        document["input_artifacts"],
        "role",
        "scientific review input artifacts",
    )
    observed_roles = set(input_index)
    if observed_roles != SCIENCE_INPUT_ROLES:
        missing = sorted(SCIENCE_INPUT_ROLES - observed_roles)
        extra = sorted(observed_roles - SCIENCE_INPUT_ROLES)
        details: list[str] = []
        if missing:
            details.append("missing roles: " + ", ".join(missing))
        if extra:
            details.append("unknown roles: " + ", ".join(extra))
        raise ContractValidationError(
            "scientific review input artifact roles must match the complete "
            "Step 09c provenance set; "
            + "; ".join(details)
        )
    require_unique_key(
        document["input_artifacts"],
        "artifact_id",
        "scientific review input artifacts",
    )
    require_unique_key(
        document["limitations"],
        "limitation_id",
        "scientific review limitations",
    )
    for limitation in document["limitations"]:
        referenced_evidence_ids.update(limitation["evidence_ids"])
    orphan_evidence = sorted(evidence_ids - referenced_evidence_ids)
    if orphan_evidence:
        raise ContractValidationError(
            "scientific evidence records must be referenced by computational "
            "status, a category, a decision, or a limitation: "
            + ", ".join(orphan_evidence)
        )
    if document["primary_analysis_id"] != document["run_contract"][
        "primary_analysis_id"
    ]:
        raise ContractValidationError(
            "scientific review primary_analysis_id does not match its "
            "immutable run contract"
        )
    input_paths = [record["path"] for record in document["input_artifacts"]]
    if len(input_paths) != len(set(input_paths)):
        raise ContractValidationError(
            "scientific review input artifact paths must be unique"
        )
    pdf_input_roles = {
        "step09_mutation_spectrum_pdf",
        "step09_depth_delta_pdf",
    }
    for role, record in input_index.items():
        suffix = Path(record["path"]).suffix.lower()
        if role in pdf_input_roles:
            if suffix != ".pdf" or record["row_count"] is not None:
                raise ContractValidationError(
                    f"scientific review PDF input role {role!r} must use a "
                    ".pdf path and null row_count"
                )
        elif suffix != ".tsv" or record["row_count"] is None:
            raise ContractValidationError(
                f"scientific review tabular input role {role!r} must use a "
                ".tsv path and a non-null row_count"
            )
        role_contract = SCIENCE_UPSTREAM_ROLE_CONTRACTS.get(role)
        if (
            role_contract is not None
            and not Path(record["path"]).name.endswith(role_contract[3])
        ):
            raise ContractValidationError(
                f"scientific review input role {role!r} path must end with "
                f"{role_contract[3]!r}"
            )
    if (
        input_index["sample_manifest"]["sha256"]
        != document["run_contract"]["sample_manifest_sha256"]
    ):
        raise ContractValidationError(
            "sample_manifest input hash does not match the run contract"
        )
    if (
        input_index["partition_manifest"]["sha256"]
        != document["run_contract"]["partition_manifest_sha256"]
    ):
        raise ContractValidationError(
            "partition_manifest input hash does not match the run contract"
        )


def artifact_rollup_state(artifact: dict[str, Any]) -> str:
    if artifact["completion_status"] == "complete":
        return "complete"
    if artifact["completion_status"] == "failed":
        return "failed"
    if artifact["availability_status"] == "missing":
        return "missing"
    if artifact["availability_status"] == "externally_unavailable":
        return "externally_unavailable"
    return "incomplete"


def aggregate_equal_or_mixed(values: Iterable[str]) -> str:
    observed = list(values)
    if not observed:
        raise ContractValidationError("cannot aggregate an empty status set")
    return observed[0] if len(set(observed)) == 1 else "mixed"


def aggregate_artifact_state(artifacts: list[dict[str, Any]]) -> str:
    required_artifacts = [
        artifact
        for artifact in artifacts
        if artifact["expectation"]["required"]
    ]
    considered = required_artifacts or artifacts
    states = [artifact_rollup_state(artifact) for artifact in considered]
    for state in (
        "failed",
        "incomplete",
        "missing",
        "externally_unavailable",
    ):
        if state in states:
            return state
    return "complete"


def artifact_status_dimensions(artifact: dict[str, Any]) -> dict[str, str]:
    return {
        "implementation_status": artifact["implementation"]["status"],
        "local_test_status": artifact["local_testing"]["status"],
        "runtime_validation_status": artifact["runtime_validation"]["status"],
        "cluster_dry_run_status": artifact["cluster_validation"][
            "dry_run_status"
        ],
        "cluster_proof_status": artifact["cluster_validation"]["proof_status"],
    }


def validate_run_summary_semantics(document: dict[str, Any]) -> None:
    validate_run_contract(document["run_contract"], "run summary")
    validate_document_paths(document)

    attempts = validate_attempt_graph(
        document["attempts"],
        label="run summary",
        require_single_chain=False,
    )
    superseded = document["superseded_attempt_ids"]
    unknown_superseded = sorted(set(superseded) - set(attempts))
    if unknown_superseded:
        raise ContractValidationError(
            "run summary superseded_attempt_ids contain unknown attempts: "
            + ", ".join(unknown_superseded)
        )
    actual_superseded = {
        attempt["supersedes_attempt_id"]
        for attempt in document["attempts"]
        if attempt["supersedes_attempt_id"] is not None
    }
    if set(superseded) != actual_superseded:
        raise ContractValidationError(
            "run summary superseded_attempt_ids must exactly name attempts "
            "superseded by another recorded attempt"
        )

    artifacts = document["artifacts"]
    artifact_index = require_unique_key(artifacts, "artifact_id", "run artifacts")
    artifact_attempts: dict[str, dict[str, Any]] = {}
    expected_source_artifacts: dict[Path, dict[str, Any]] = {}
    physical_path_records: dict[Path, tuple[Any, ...]] = {}
    for artifact in artifacts:
        validate_artifact_semantics(artifact)
        if artifact["run_id"] != document["run_id"]:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} has a different run_id"
            )
        if artifact["run_contract"] != document["run_contract"]:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} has a different "
                "immutable run contract"
            )
        for attempt in artifact["attempts"]:
            attempt_id = attempt["attempt_id"]
            if (
                attempt_id in artifact_attempts
                and artifact_attempts[attempt_id] != attempt
            ):
                raise ContractValidationError(
                    f"artifact attempt {attempt_id!r} has conflicting "
                    "definitions across artifact records"
                )
            artifact_attempts[attempt_id] = attempt
            if attempt_id not in attempts or attempts[attempt_id] != attempt:
                raise ContractValidationError(
                    f"artifact attempt {attempt_id!r} is not represented "
                    "identically in the run attempt history"
                )
        if artifact["selected_attempt_id"] in superseded:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} selects a superseded "
                "run attempt"
            )
        expected_path = resolve_contract_path(
            artifact["expectation"]["source_path"]
        )
        if expected_path in expected_source_artifacts:
            raise ContractValidationError(
                f"run artifacts contain duplicate expected source path "
                f"{expected_path!r}"
            )
        expected_source_artifacts[expected_path] = artifact
        physical_records = (
            ([artifact["source"]] if artifact["source"] is not None else [])
            + artifact["members"]
        )
        for record in physical_records:
            fingerprint = (
                record["sha256"],
                record.get("size_bytes"),
                record.get("row_count"),
                record.get("media_type"),
            )
            physical_path = resolve_contract_path(record["path"])
            prior = physical_path_records.get(physical_path)
            if prior is not None and prior != fingerprint:
                raise ContractValidationError(
                    f"run artifacts disagree on physical path "
                    f"{str(physical_path)!r}"
                )
            physical_path_records[physical_path] = fingerprint

    for expected_path, expected_artifact in expected_source_artifacts.items():
        if expected_path not in physical_path_records:
            continue
        source = expected_artifact["source"]
        if source is None:
            raise ContractValidationError(
                f"run member records claim missing expected source "
                f"{str(expected_path)!r}"
            )
        expected_fingerprint = (
            source["sha256"],
            source.get("size_bytes"),
            source.get("row_count"),
            source.get("media_type"),
        )
        if physical_path_records[expected_path] != expected_fingerprint:
            raise ContractValidationError(
                f"run member/source metadata disagree for expected path "
                f"{str(expected_path)!r}"
            )

    scope_keys: set[tuple[str, str, str]] = set()
    ordered_expected_artifact_ids: list[str] = []
    for scope_record in document["expected_scopes"]:
        scope = scope_record["scope"]
        scope_key = (
            scope["step_id"],
            scope["scope_type"],
            scope["scope_id"],
        )
        if scope_key in scope_keys:
            raise ContractValidationError(
                f"run summary contains duplicate expected scope {scope_key}"
            )
        scope_keys.add(scope_key)
        scope_artifacts: list[dict[str, Any]] = []
        for artifact_id in scope_record["artifact_ids"]:
            if artifact_id not in artifact_index:
                raise ContractValidationError(
                    f"expected scope {scope_key} references unknown artifact "
                    f"{artifact_id!r}"
                )
            artifact = artifact_index[artifact_id]
            artifact_scope = artifact["scope"]
            if (
                artifact_scope["step_id"],
                artifact_scope["scope_type"],
                artifact_scope["scope_id"],
            ) != scope_key:
                raise ContractValidationError(
                    f"expected scope {scope_key} does not match artifact "
                    f"{artifact_id!r}"
                )
            scope_artifacts.append(artifact)
        expected_aggregate = aggregate_artifact_state(scope_artifacts)
        if scope_record["aggregate_state"] != expected_aggregate:
            raise ContractValidationError(
                f"expected scope {scope_key} aggregate_state is "
                f"{scope_record['aggregate_state']!r}, expected "
                f"{expected_aggregate!r}"
            )
        for status_field in (
            "implementation_status",
            "local_test_status",
            "runtime_validation_status",
            "cluster_dry_run_status",
            "cluster_proof_status",
        ):
            expected_status = aggregate_equal_or_mixed(
                artifact_status_dimensions(artifact)[status_field]
                for artifact in scope_artifacts
            )
            if scope_record[status_field] != expected_status:
                raise ContractValidationError(
                    f"expected scope {scope_key} {status_field} is "
                    f"{scope_record[status_field]!r}, expected "
                    f"{expected_status!r}"
                )
        ordered_expected_artifact_ids.extend(scope_record["artifact_ids"])

    if len(ordered_expected_artifact_ids) != len(
        set(ordered_expected_artifact_ids)
    ):
        raise ContractValidationError(
            "an artifact_id appears in more than one expected scope"
        )
    if ordered_expected_artifact_ids != list(artifact_index):
        raise ContractValidationError(
            "artifacts must appear exactly once in expected-scope/inventory order"
        )
    inventory_row_count = document["inventory"]["row_count"]
    if (
        inventory_row_count is not None
        and inventory_row_count != len(artifacts)
    ):
        raise ContractValidationError(
            "inventory row_count does not match the expected artifact count"
        )

    rollup = document["computational_rollup"]
    observed_counts = {
        "complete_artifact_count": 0,
        "missing_artifact_count": 0,
        "incomplete_artifact_count": 0,
        "failed_artifact_count": 0,
        "externally_unavailable_artifact_count": 0,
    }
    for artifact in artifacts:
        state = artifact_rollup_state(artifact)
        observed_counts[f"{state}_artifact_count"] += 1
    if rollup["expected_artifact_count"] != len(artifacts):
        raise ContractValidationError(
            "computational_rollup expected_artifact_count does not match "
            "the artifact array"
        )
    for field, observed in observed_counts.items():
        if rollup[field] != observed:
            raise ContractValidationError(
                f"computational_rollup {field} is {rollup[field]}, "
                f"expected {observed}"
            )
    for status_field in (
        "implementation_status",
        "local_test_status",
        "runtime_validation_status",
        "cluster_dry_run_status",
        "cluster_proof_status",
    ):
        expected_status = aggregate_equal_or_mixed(
            artifact_status_dimensions(artifact)[status_field]
            for artifact in artifacts
        )
        if rollup[status_field] != expected_status:
            raise ContractValidationError(
                f"computational_rollup {status_field} is "
                f"{rollup[status_field]!r}, expected {expected_status!r}"
            )

    review = document["scientific_review"]
    if review["overall_status"] != document["science_status"]:
        raise ContractValidationError(
            "run summary science_status does not match scientific_review"
        )
    if review["record"] is not None:
        record = review["record"]
        validate_scientific_review_semantics(record)
        if record["run_id"] != document["run_id"]:
            raise ContractValidationError(
                "scientific review record has a different run_id"
            )
        if record["run_contract"] != document["run_contract"]:
            raise ContractValidationError(
                "scientific review record has a different immutable run contract"
            )
        if record["scientific_state"]["overall_status"] != document["science_status"]:
            raise ContractValidationError(
                "scientific review record has a different overall science status"
            )
        if (
            review["source"]["path"] != record["review_summary"]["path"]
            or review["source"]["sha256"] != record["review_summary"]["sha256"]
        ):
            raise ContractValidationError(
                "scientific review source path/hash does not match the "
                "embedded review record"
            )
        matching_review_artifacts = [
            artifact
            for artifact in artifacts
            if artifact["scope"]["step_id"] == "09c"
            if artifact["scope"]["scope_type"] == "scientific_review"
            and artifact["scope"]["scope_id"] == record["review_id"]
                and artifact["completion_status"] == "complete"
                and artifact["source"] is not None
                and resolve_contract_path(artifact["source"]["path"])
                == resolve_contract_path(record["review_summary"]["path"])
                and artifact["source"]["sha256"]
                == record["review_summary"]["sha256"]
        ]
        if len(matching_review_artifacts) != 1:
            raise ContractValidationError(
                "embedded scientific review must match exactly one complete "
                "scientific-review artifact source"
            )
        for input_artifact in record["input_artifacts"]:
            role_contract = SCIENCE_UPSTREAM_ROLE_CONTRACTS.get(
                input_artifact["role"]
            )
            if role_contract is None:
                continue
            artifact_id = input_artifact["artifact_id"]
            if artifact_id not in artifact_index:
                raise ContractValidationError(
                    f"scientific review input role "
                    f"{input_artifact['role']!r} references artifact "
                    f"{artifact_id!r} absent from the run summary"
                )
            upstream = artifact_index[artifact_id]
            source = upstream["source"]
            expected_step, expected_scope_type, expected_adapter, _ = (
                role_contract
            )
            if (
                upstream["completion_status"] != "complete"
                or source is None
                or upstream["scope"]["step_id"] != expected_step
                or upstream["scope"]["scope_type"] != expected_scope_type
                or upstream["adapter"] != expected_adapter
                or source["path"] != input_artifact["path"]
                or source["sha256"] != input_artifact["sha256"]
                or source.get("row_count") != input_artifact["row_count"]
            ):
                raise ContractValidationError(
                    f"scientific review input role "
                    f"{input_artifact['role']!r} does not match one complete "
                    "run artifact source"
                )

    report_tables = require_unique_key(
        document["approved_report_tables"],
        "table_id",
        "approved report tables",
    )
    for table in report_tables.values():
        artifact_id = table["artifact_id"]
        if artifact_id not in artifact_index:
            raise ContractValidationError(
                f"report table {table['table_id']!r} references unknown "
                f"artifact {artifact_id!r}"
            )
        artifact = artifact_index[artifact_id]
        if artifact["completion_status"] != "complete":
            raise ContractValidationError(
                f"report table {table['table_id']!r} references a non-complete "
                "artifact"
            )
        report_sources = {
            (
                artifact["source"]["path"],
                artifact["source"]["sha256"],
            ): artifact["source"]
        }
        report_sources.update(
            {
                (member["path"], member["sha256"]): member
                for member in artifact["members"]
            }
        )
        source_record = report_sources.get((table["path"], table["sha256"]))
        if source_record is None:
            raise ContractValidationError(
                f"report table {table['table_id']!r} path/hash does not match "
                "its artifact source or members"
            )
        if source_record.get("row_count") != table["row_count"]:
            raise ContractValidationError(
                f"report table {table['table_id']!r} row_count does not match "
                "its source artifact"
            )
        if source_record.get("media_type") != "text/tab-separated-values":
            raise ContractValidationError(
                f"report table {table['table_id']!r} must reference a TSV "
                "artifact"
            )

    qc_metrics = require_unique_key(
        document["qc_metrics"],
        "metric_id",
        "QC metrics",
    )
    for metric in qc_metrics.values():
        source_artifact_id = metric["source_artifact_id"]
        if source_artifact_id is None:
            raise ContractValidationError(
                f"QC metric {metric['metric_id']!r} requires an explicit "
                "source_artifact_id"
            )
        if source_artifact_id not in artifact_index:
            raise ContractValidationError(
                f"QC metric {metric['metric_id']!r} references unknown "
                f"artifact {source_artifact_id!r}"
            )
        source_metrics = {
            source_metric["metric_id"]: source_metric
            for source_metric in artifact_index[source_artifact_id]["metrics"]
        }
        if source_metrics.get(metric["metric_id"]) != metric:
            raise ContractValidationError(
                f"QC metric {metric['metric_id']!r} does not exactly match "
                f"the metric recorded by artifact {source_artifact_id!r}"
            )
    require_unique_key(
        document["limitations"],
        "limitation_id",
        "run summary limitations",
    )


def validate_report_receipt_semantics(document: dict[str, Any]) -> None:
    validate_document_paths(document)
    outputs = document["outputs"]
    require_unique_key(outputs, "output_id", "report outputs")
    kinds = [output["kind"] for output in outputs]
    if len(kinds) != len(set(kinds)):
        raise ContractValidationError("report outputs contain duplicate kinds")
    paths = [output["path"] for output in outputs]
    if len(paths) != len(set(paths)):
        raise ContractValidationError("report outputs contain duplicate paths")
    expected_kinds = set(document["requested_formats"]) | {"run_summary_tsv"}
    if set(kinds) != expected_kinds:
        raise ContractValidationError(
            "report output kinds must exactly match requested formats plus "
            "run_summary_tsv"
        )
    expected_basenames = {
        "html": f"{document['run_id']}.run_report.html",
        "pdf": f"{document['run_id']}.run_report.pdf",
        "run_summary_tsv": f"{document['run_id']}.run_summary.tsv",
    }
    output_parents: set[Path] = set()
    for output in outputs:
        path = Path(output["path"])
        if path.name != expected_basenames[output["kind"]]:
            raise ContractValidationError(
                f"report {output['kind']} output basename must be "
                f"{expected_basenames[output['kind']]!r}"
            )
        output_parents.add(path.parent)
    if len(output_parents) != 1:
        raise ContractValidationError(
            "all report outputs must share one publication directory"
        )
    output_parent = next(iter(output_parents))
    if output_parent.name != document["run_id"]:
        raise ContractValidationError(
            "report publication directory name must equal run_id"
        )
    if Path(document["input_run_summary"]["path"]).name != (
        f"{document['run_id']}.run_summary.json"
    ):
        raise ContractValidationError(
            "report receipt input run-summary basename does not match run_id"
        )
    if Path(document["input_run_summary"]["path"]).parent.name != document["run_id"]:
        raise ContractValidationError(
            "report receipt input run-summary directory name must equal run_id"
        )
    require_unique_key(document["truncations"], "table_id", "report truncations")
    for truncation in document["truncations"]:
        if truncation["displayed_row_count"] >= truncation["full_row_count"]:
            raise ContractValidationError(
                f"truncation {truncation['table_id']!r} must display fewer "
                "rows than the full table"
            )


def validate_document_semantics(name: str, document: dict[str, Any]) -> None:
    if name == "artifact-record":
        validate_artifact_semantics(document)
    elif name == "scientific-review-record":
        validate_scientific_review_semantics(document)
    elif name == "run-summary":
        validate_run_summary_semantics(document)
    elif name == "report-receipt":
        validate_report_receipt_semantics(document)


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


def validate_inventory(path: Path) -> list[dict[str, str]]:
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
        raise ContractValidationError(f"Could not parse inventory {path}: {exc}") from exc

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
        if None in row:
            raise ContractValidationError(
                f"Inventory row {row_number}: too many tab-separated fields"
            )
        if any(value is None for value in row.values()):
            raise ContractValidationError(
                f"Inventory row {row_number}: too few tab-separated fields"
            )
        for column in INVENTORY_HEADER:
            value = row[column]
            if value == "":
                raise ContractValidationError(
                    f"Inventory row {row_number}: {column} must be non-empty"
                )

        for column in (
            "artifact_id",
            "step_id",
            "scope_type",
            "scope_id",
            "adapter",
        ):
            validate_safe_id(column, row[column], row_number)

        artifact_id = row["artifact_id"]
        if artifact_id in seen_artifact_ids:
            raise ContractValidationError(
                f"Inventory row {row_number}: duplicate artifact_id "
                f"{artifact_id!r}; first seen on row "
                f"{seen_artifact_ids[artifact_id]}"
            )
        seen_artifact_ids[artifact_id] = row_number

        if row["scope_type"] not in SCOPE_TYPES:
            raise ContractValidationError(
                f"Inventory row {row_number}: scope_type must be one of "
                f"{', '.join(sorted(SCOPE_TYPES))}; got {row['scope_type']!r}"
            )
        scope_key = (row["step_id"], row["scope_type"], row["scope_id"])
        if active_scope is None:
            active_scope = scope_key
        elif scope_key != active_scope:
            closed_scopes.add(active_scope)
            if scope_key in closed_scopes:
                raise ContractValidationError(
                    f"Inventory row {row_number}: artifacts for logical scope "
                    f"{scope_key} must be contiguous"
                )
            active_scope = scope_key

        validate_explicit_source_path(row["source_path"], row_number)
        source_path = row["source_path"]
        if source_path in seen_source_paths:
            raise ContractValidationError(
                f"Inventory row {row_number}: duplicate source_path "
                f"{source_path!r}; first seen on row "
                f"{seen_source_paths[source_path]}"
            )
        seen_source_paths[source_path] = row_number
        canonical_source_path = resolve_contract_path(source_path)
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
    for field in ("artifact_id", "scope", "adapter", "expectation"):
        if artifact[field] != expected[field]:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} {field} does not "
                "match its explicit inventory row"
            )


def resolve_contract_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def reconcile_document_inventory(
    name: str,
    document: dict[str, Any],
    rows: list[dict[str, str]],
    inventory_path: Path,
) -> None:
    row_index = {row["artifact_id"]: row for row in rows}
    if name == "artifact-record":
        artifact_id = document["artifact_id"]
        if artifact_id not in row_index:
            raise ContractValidationError(
                f"artifact {artifact_id!r} is not declared by the inventory"
            )
        reconcile_artifact_inventory_row(document, row_index[artifact_id])
        return
    if name != "run-summary":
        raise ContractValidationError(
            f"inventory reconciliation is unsupported for schema {name!r}"
        )

    inventory_record = document["inventory"]
    if resolve_contract_path(inventory_record["path"]) != inventory_path.resolve():
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
            "run summary inventory row_count does not match the supplied "
            "inventory"
        )

    artifacts = document["artifacts"]
    observed_artifact_ids = [artifact["artifact_id"] for artifact in artifacts]
    expected_artifact_ids = [row["artifact_id"] for row in rows]
    if observed_artifact_ids != expected_artifact_ids:
        raise ContractValidationError(
            "run summary artifacts do not exactly match inventory row order"
        )
    for artifact, row in zip(artifacts, rows, strict=True):
        reconcile_artifact_inventory_row(artifact, row)

    scope_groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    scope_order: list[tuple[str, str, str]] = []
    for row in rows:
        scope_key = (row["step_id"], row["scope_type"], row["scope_id"])
        if scope_key not in scope_groups:
            scope_order.append(scope_key)
        scope_groups[scope_key].append(row["artifact_id"])
    expected_scope_contract = [
        (scope_key, scope_groups[scope_key]) for scope_key in scope_order
    ]
    observed_scope_contract = [
        (
            (
                scope["scope"]["step_id"],
                scope["scope"]["scope_type"],
                scope["scope"]["scope_id"],
            ),
            scope["artifact_ids"],
        )
        for scope in document["expected_scopes"]
    ]
    if observed_scope_contract != expected_scope_contract:
        raise ContractValidationError(
            "run summary expected scopes do not exactly group the supplied "
            "inventory in stable first-seen order"
        )


def main() -> int:
    args = parse_args()
    try:
        if args.check_schemas:
            validate_all_schemas()
        document: dict[str, Any] | None = None
        inventory_rows: list[dict[str, str]] | None = None
        if args.document is not None:
            document = validate_document(args.schema, args.document)
        if args.inventory is not None:
            inventory_rows = validate_inventory(args.inventory)
        if document is not None and inventory_rows is not None:
            reconcile_document_inventory(
                args.schema,
                document,
                inventory_rows,
                args.inventory,
            )
            print(
                f"Document/inventory reconciliation passed: {args.document}"
            )
    except ContractValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
