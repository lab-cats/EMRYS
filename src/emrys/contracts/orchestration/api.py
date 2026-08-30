"""Public registry and validation API for local-pilot orchestration records."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

from emrys.libraries.source_authority import controlled_python_argv

SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas" / "orchestration" / "v1"
SCHEMA_NAMES = (
    "request",
    "resource-config",
    "execution-profile",
    "profile",
    "execution",
    "application-model",
    "reference",
    "policy",
    "run-lock",
    "workflow-attempt",
    "attempt-receipt",
    "task-start",
    "task-attempt",
    "verified-task",
    "reporting-start",
    "verified-reporting",
)
SCHEMA_PATHS = {
    "common": SCHEMA_ROOT / "common.schema.json",
    **{
        name: SCHEMA_ROOT / f"{name.replace('-', '_')}.schema.json"
        for name in SCHEMA_NAMES
    },
}
SCHEMA_PATHS["profile"] = SCHEMA_ROOT.parent / "v2" / "profile.schema.json"
SCHEMA_PATHS["request"] = SCHEMA_ROOT.parent / "v3" / "request.schema.json"
SCHEMA_PATHS["resource-config"] = (
    SCHEMA_ROOT.parent / "v3" / "resource_config.schema.json"
)
SCHEMA_PATHS["execution-profile"] = (
    SCHEMA_ROOT.parent / "v3" / "execution_profile.schema.json"
)
_ATTEMPT_RECEIPT_V2_PATH = SCHEMA_ROOT.parent / "v2" / "attempt_receipt.schema.json"
_ATTEMPT_RECEIPT_V2_ID = "urn:emrys:schema:orchestration:attempt-receipt:v2"
SCHEMA_IDS = {
    name: f"urn:emrys:schema:orchestration:{name}:v1" for name in SCHEMA_PATHS
}
SCHEMA_IDS.update(
    {
        "request": "urn:emrys:schema:orchestration:request:v3",
        "resource-config": "urn:emrys:schema:orchestration:resource-config:v1",
        "execution-profile": "urn:emrys:schema:orchestration:execution-profile:v1",
        "profile": "urn:emrys:schema:orchestration:profile:v2",
    }
)


class ContractValidationError(ValueError):
    """Raised when an orchestration schema or record is invalid."""


_ATTEMPT_TIMESTAMP_RE = re.compile(
    r"^(?:workflow|task)-(?P<timestamp>[0-9]{8}T[0-9]{6}Z)-[0-9a-f]{32}$"
)


def _reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ContractValidationError(f"Duplicate JSON object key: {key}")
        value[key] = item
    return value


def _reject_nonstandard_constant(value: str) -> None:
    raise ContractValidationError(
        f"Non-standard JSON numeric constant is not allowed: {value}"
    )


def load_json_object_bytes(data: bytes, label: str = "JSON record") -> dict[str, Any]:
    """Parse admitted UTF-8 bytes without duplicate keys or numeric constants."""

    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except ContractValidationError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"Could not parse {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractValidationError(f"{label} must contain one object")
    return value


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load one strict UTF-8 JSON object without accepting duplicate keys."""

    record_path = Path(path)
    if not record_path.is_file():
        raise ContractValidationError(f"JSON record is not a file: {record_path}")
    try:
        data = record_path.read_bytes()
    except OSError as exc:
        raise ContractValidationError(
            f"Could not read JSON record {record_path}: {exc}"
        ) from exc
    return load_json_object_bytes(data, f"JSON record {record_path}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize identity content using the B0 canonical JSON encoding."""

    try:
        rendered = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(
            f"Value is not canonical-JSON serializable: {exc}"
        ) from exc
    return rendered.encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the lowercase SHA-256 of canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    """Load and validate the complete closed local orchestration registry."""

    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for name, path in SCHEMA_PATHS.items():
        schema = load_json_object(path)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ContractValidationError(
                f"{name} is not valid Draft 2020-12: {exc.message}"
            ) from exc
        expected_id = SCHEMA_IDS[name]
        if schema.get("$id") != expected_id:
            raise ContractValidationError(f"{name} schema $id must be {expected_id}")
        try:
            registry = registry.with_resource(
                expected_id,
                Resource.from_contents(schema),
            )
        except Exception as exc:
            raise ContractValidationError(
                f"Could not register local {name} schema: {exc}"
            ) from exc
        schemas[name] = schema
    return schemas, registry


@cache
def schema_validator(name: str) -> Draft202012Validator:
    """Return a validator for one public schema selector."""

    if name not in SCHEMA_NAMES:
        raise ContractValidationError(f"Unknown orchestration schema: {name}")
    schemas, registry = load_schema_registry()
    return Draft202012Validator(
        schemas[name],
        registry=registry,
        format_checker=FormatChecker(),
    )


@cache
def _attempt_receipt_v2_validator() -> Draft202012Validator:
    schema = load_json_object(_ATTEMPT_RECEIPT_V2_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ContractValidationError(
            f"attempt-receipt v2 is not valid Draft 2020-12: {exc.message}"
        ) from exc
    if schema.get("$id") != _ATTEMPT_RECEIPT_V2_ID:
        raise ContractValidationError(
            f"attempt-receipt v2 schema $id must be {_ATTEMPT_RECEIPT_V2_ID}"
        )
    _schemas, registry = load_schema_registry()
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )


def schema_errors(name: str, record: Any) -> tuple[str, ...]:
    """Return stable path-qualified schema diagnostics."""

    validator = schema_validator(name)
    if (
        name == "attempt-receipt"
        and isinstance(record, Mapping)
        and record.get("schema_version") == "emrys.attempt-receipt.v2"
    ):
        validator = _attempt_receipt_v2_validator()
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    rendered: list[str] = []
    for error in errors:
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        rendered.append(f"{path}: {error.message}")
    return tuple(rendered)


def _require_distinct_ids(record: Mapping[str, Any], *fields: str) -> None:
    values = [record[field] for field in fields if record.get(field) is not None]
    if len(values) != len(set(values)):
        raise ContractValidationError(
            f"Identity fields may not alias each other: {', '.join(fields)}"
        )


def _require_attempt_time(identifier: str, timestamp: str, label: str) -> None:
    matched = _ATTEMPT_TIMESTAMP_RE.fullmatch(identifier)
    if matched is None:
        raise ContractValidationError(f"Invalid {label} format: {identifier}")
    try:
        embedded = datetime.strptime(
            matched.group("timestamp"), "%Y%m%dT%H%M%SZ"
        ).replace(tzinfo=UTC)
        declared = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"Invalid {label} UTC context") from exc
    if declared.astimezone(UTC).replace(microsecond=0) != embedded:
        raise ContractValidationError(
            f"{label} UTC context does not match its declared timestamp"
        )


def _validate_direct_edges(edges: list[Mapping[str, Any]], owners: set[str]) -> None:
    pairs: list[tuple[str, str]] = []
    adjacency = {owner: set() for owner in owners}
    for edge in edges:
        producer = str(edge["producer"])
        consumer = str(edge["consumer"])
        if producer not in owners or consumer not in owners:
            raise ContractValidationError(
                "Profile edges must reference semantic_owner_keys"
            )
        pair = producer, consumer
        if pair in pairs:
            raise ContractValidationError(
                "Profile direct_edges must not repeat a producer/consumer pair: "
                f"{producer} -> {consumer}"
            )
        pairs.append(pair)
        adjacency[producer].add(consumer)

    complete: set[str] = set()
    active: list[str] = []

    def visit(owner: str) -> None:
        if owner in active:
            cycle_start = active.index(owner)
            cycle = (*active[cycle_start:], owner)
            raise ContractValidationError(
                "Profile direct_edges must be acyclic: " + " -> ".join(cycle)
            )
        if owner in complete:
            return
        active.append(owner)
        for consumer in sorted(adjacency[owner]):
            visit(consumer)
        active.pop()
        complete.add(owner)

    for owner in sorted(owners):
        visit(owner)


def _validate_artifact_template_groups(
    templates: list[Mapping[str, Any]],
    scope_selectors: Mapping[str, str],
) -> None:
    closed: set[tuple[str, str, str]] = set()
    active: tuple[str, str, str] | None = None
    for template in templates:
        scope_type = str(template["scope_type"])
        scope_selector = str(template["scope_selector"])
        expected_selector = scope_selectors[scope_type]
        if scope_selector != expected_selector:
            raise ContractValidationError(
                "Profile artifact scope_selector must match its scope_type"
            )
        group = str(template["step_id"]), scope_type, scope_selector
        if group == active:
            continue
        if group in closed:
            raise ContractValidationError(
                "Profile artifact template logical scope group reopens: "
                f"{group[0]}/{group[1]}/{group[2]}"
            )
        if active is not None:
            closed.add(active)
        active = group


def _validate_profile(record: Mapping[str, Any]) -> None:
    owners = set(record["semantic_owner_keys"])
    task_keys = [task["machine_key"] for task in record["owner_tasks"]]
    if len(task_keys) != len(set(task_keys)) or set(task_keys) != owners:
        raise ContractValidationError(
            "Profile must define exactly one owner_task per semantic_owner_key"
        )
    required = set(record["required_owner_keys"])
    evidence = set(record["evidence_owner_keys"])
    if not required <= owners or not evidence <= owners:
        raise ContractValidationError(
            "Profile owner classifications must reference semantic_owner_keys"
        )
    if not evidence <= required:
        raise ContractValidationError(
            "Every evidence owner must also be required for profile completion"
        )
    if required != owners:
        raise ContractValidationError(
            "Every semantic owner must be required for profile completion"
        )
    rule_names = [task["rule_name"] for task in record["owner_tasks"]]
    if len(rule_names) != len(set(rule_names)):
        raise ContractValidationError(
            "Profile owner_task rule_name values must be unique"
        )
    _validate_direct_edges(record["direct_edges"], owners)
    templates = [item["artifact_id_template"] for item in record["artifact_templates"]]
    if len(templates) != len(set(templates)):
        raise ContractValidationError(
            "Profile artifact_id_template values must be unique"
        )
    scope_selectors = {
        "reference": "reference",
        "sample": "samples",
        "cohort_partition": "partitions",
        "cohort": "cohort",
        "analysis": "analysis",
    }
    for task in record["owner_tasks"]:
        expected_selector = scope_selectors[task["scope_type"]]
        if task["scope_selector"] != expected_selector:
            raise ContractValidationError(
                "Profile owner_task scope_selector must match its scope_type"
            )
    _validate_artifact_template_groups(record["artifact_templates"], scope_selectors)


def _validate_policy(record: Mapping[str, Any]) -> None:
    if record["control_condition"] == record["treatment_condition"]:
        raise ContractValidationError(
            "Analysis control_condition and treatment_condition must differ"
        )
    background = record.get("background_condition")
    if background in {record["control_condition"], record["treatment_condition"]}:
        raise ContractValidationError(
            "Analysis background_condition must differ from primary conditions"
        )
    if record["rna_ref"] == record["rna_alt"]:
        raise ContractValidationError("Analysis rna_ref and rna_alt must differ")


def _validate_request(record: Mapping[str, Any]) -> None:
    _validate_policy(record["analysis"])


def _validate_execution(record: Mapping[str, Any]) -> None:
    sample_ids = [row["sample_id"] for row in record["samples"]["rows"]]
    if len(sample_ids) != len(set(sample_ids)):
        raise ContractValidationError("Execution sample_id values must be unique")
    partition_ids = [row["partition_id"] for row in record["partitions"]["rows"]]
    if len(partition_ids) != len(set(partition_ids)):
        raise ContractValidationError("Execution partition_id values must be unique")

    analysis = record["analysis"]
    policy = analysis["policy"]
    _validate_policy(policy)
    if analysis["primary_analysis_id"] != policy["analysis_id"]:
        raise ContractValidationError(
            "Execution primary_analysis_id must equal policy.analysis_id"
        )
    if analysis["policy_sha256"] != canonical_sha256(policy):
        raise ContractValidationError(
            "Execution policy_sha256 does not match canonical policy content"
        )
    controls: dict[str, int] = {}
    treatments: dict[str, int] = {}
    for sample in record["samples"]["rows"]:
        replicate = sample["replicate"]
        if sample["condition"] == policy["control_condition"]:
            controls[replicate] = controls.get(replicate, 0) + 1
        if sample["condition"] == policy["treatment_condition"]:
            treatments[replicate] = treatments.get(replicate, 0) + 1
    if (
        set(controls) != set(treatments)
        or len(controls) < 2
        or any(count != 1 for count in (*controls.values(), *treatments.values()))
    ):
        raise ContractValidationError(
            "Execution samples must define exactly one control and treatment "
            "for each of at least two complete replicate strata"
        )

    envelope = record["identity_envelope"]
    expected_envelope = {
        "schema_version": "emrys.identity-envelope.v1",
        "profile": record["profile"],
        "samples": record["samples"],
        "partitions": record["partitions"],
        "reference": record["reference"],
        "analysis": record["analysis"],
    }
    if envelope != expected_envelope:
        raise ContractValidationError(
            "Execution identity_envelope must exactly match normalized identity fields"
        )
    digest = canonical_sha256(envelope)
    if record["identity_envelope_sha256"] != digest:
        raise ContractValidationError(
            "Execution identity_envelope_sha256 does not match canonical content"
        )
    if record["run_id"] != f"run-{digest}":
        raise ContractValidationError(
            "Execution run_id must be run- plus identity_envelope_sha256"
        )
    projection = record["reporting_projection"]
    if projection["reference_contract"]["sha256"] != canonical_sha256(
        record["reference"]
    ):
        raise ContractValidationError(
            "Execution reference_contract hash does not match normalized reference"
        )
    if projection["primary_analysis_policy"]["sha256"] != analysis["policy_sha256"]:
        raise ContractValidationError(
            "Execution primary_analysis_policy hash does not match normalized policy"
        )


def _validate_identity_record(name: str, record: Mapping[str, Any]) -> None:
    if name == "run-lock":
        _require_distinct_ids(record, "run_id", "workflow_attempt_id", "owner_token")
        _require_attempt_time(
            record["workflow_attempt_id"],
            record["created_at"],
            "workflow_attempt_id",
        )
    elif name == "workflow-attempt":
        _require_distinct_ids(record, "run_id", "workflow_attempt_id", "owner_token")
        if (
            record.get("supersedes_workflow_attempt_id")
            == record["workflow_attempt_id"]
        ):
            raise ContractValidationError("A workflow attempt may not supersede itself")
        _require_attempt_time(
            record["workflow_attempt_id"],
            record["created_at"],
            "workflow_attempt_id",
        )
        tool_names = [tool["name"] for tool in record["required_tools"]]
        if len(tool_names) != len(set(tool_names)):
            raise ContractValidationError("Workflow required tool names must be unique")
        if tool_names != sorted(tool_names):
            raise ContractValidationError(
                "Workflow required tool identities must use normalized name order"
            )
        tools = {tool["name"]: tool for tool in record["required_tools"]}
        if set(("python", "snakemake")) - tools.keys():
            raise ContractValidationError(
                "Workflow required tools must include python and snakemake"
            )
        runtime_path = record["normalizer"]["path"]
        if (
            tools["python"]["path"] != runtime_path
            or tools["snakemake"]["path"] != runtime_path
        ):
            raise ContractValidationError(
                "Workflow Python, Snakemake, and normalizer paths must be identical"
            )
        if (
            record["normalizer"]["resolved_path"] != tools["python"]["resolved_path"]
            or record["normalizer"]["sha256"] != tools["python"]["sha256"]
        ):
            raise ContractValidationError(
                "Workflow normalizer must bind the exact Python executable bytes"
            )
        if (
            tools["python"]["resolved_path"] != tools["snakemake"]["resolved_path"]
            or tools["python"]["sha256"] != tools["snakemake"]["sha256"]
            or tools["python"]["sha256"] is None
        ):
            raise ContractValidationError(
                "Workflow Python and Snakemake must bind the same executable bytes"
            )
        sha256_python = tools.get("sha256_python")
        if record["execution_mode"] == "local-science-tools" and sha256_python is None:
            raise ContractValidationError(
                "Local science workflow must bind controlled Python SHA-256"
            )
        if (
            record["execution_mode"] == "local-science-tools"
            and "storage_qualification" not in tools
        ):
            raise ContractValidationError(
                "Local science workflow must bind one storage qualification"
            )
        if sha256_python is not None and any(
            sha256_python[field] != tools["python"][field]
            for field in ("path", "resolved_path", "sha256")
        ):
            raise ContractValidationError(
                "Workflow SHA-256 Python must bind the exact Python executable bytes"
            )
        directory_tools = {"renv_project", "renv_library"}
        for tool in record["required_tools"]:
            if (tool["name"] in directory_tools) != (tool["sha256"] is None):
                raise ContractValidationError(
                    "Only required runtime directory identities may omit a byte digest"
                )
        runtime_profile = tools.get("runtime_profile")
        if runtime_profile is not None and (
            runtime_profile["sha256"] is None
            or runtime_profile["version"] != f"sha256:{runtime_profile['sha256']}"
        ):
            raise ContractValidationError(
                "Workflow runtime profile version must bind its exact byte digest"
            )
        argv = list(record["snakemake_argv"])
        expected_python_prefix = list(
            controlled_python_argv(runtime_path, "-m", "snakemake")
        )
        if argv[: len(expected_python_prefix)] != expected_python_prefix:
            raise ContractValidationError(
                "Workflow Snakemake argv must launch the bound controlled Python module"
            )
        forbidden = {
            "--unlock",
            "--cleanup-metadata",
            "--forceall",
            "--rerun-incomplete",
            "--force",
        }
        observed_forbidden = sorted(forbidden.intersection(argv))
        if observed_forbidden:
            raise ContractValidationError(
                "Workflow Snakemake argv contains forbidden recovery controls: "
                + ", ".join(observed_forbidden)
            )
        rerun_positions = [
            index for index, value in enumerate(argv) if value == "--rerun-triggers"
        ]
        ignore_incomplete_positions = [
            index for index, value in enumerate(argv) if value == "--ignore-incomplete"
        ]
        if record["operation"] == "execute":
            if rerun_positions or ignore_incomplete_positions:
                raise ContractValidationError(
                    "Initial execution must use Snakemake's default incomplete-state "
                    "and rerun behavior"
                )
        elif (
            len(rerun_positions) != 1
            or rerun_positions[0] + 1 >= len(argv)
            or argv[rerun_positions[0] + 1] != "input"
            or len(ignore_incomplete_positions) != 1
            or ignore_incomplete_positions[0] != rerun_positions[0] + 2
        ):
            raise ContractValidationError(
                "Resume must use exactly --rerun-triggers input and --ignore-incomplete"
            )
    elif name == "attempt-receipt":
        _require_distinct_ids(record, "run_id", "workflow_attempt_id")
        status = record["status"]
        exit_code = record["snakemake_exit_code"]
        signal_number = record["termination_signal"]
        blockers = list(record["blockers"])
        message = record["message"]
        task_identities = [
            (
                item["machine_key"],
                item["scope"]["scope_type"],
                item["scope"]["scope_id"],
            )
            for item in record["verified_tasks"]
        ]
        start_identities = [
            (
                item["machine_key"],
                item["scope"]["scope_type"],
                item["scope"]["scope_id"],
            )
            for item in record["task_start_records"]
        ]
        preentry_identities = [
            (
                item["workflow_attempt_id"],
                item["machine_key"],
                item["scope"]["scope_type"],
                item["scope"]["scope_id"],
            )
            for item in record["preentry_task_attempt_records"]
        ]
        if preentry_identities != sorted(preentry_identities):
            raise ContractValidationError(
                "Attempt receipt preentry_task_attempt_records must use normalized "
                "attempt-owner-scope order"
            )
        if len(preentry_identities) != len(set(preentry_identities)):
            raise ContractValidationError(
                "Attempt receipt preentry_task_attempt_records must be unique"
            )
        if start_identities != sorted(start_identities):
            raise ContractValidationError(
                "Attempt receipt task_start_records must use normalized owner-scope "
                "order"
            )
        if len(start_identities) != len(set(start_identities)):
            raise ContractValidationError(
                "Attempt receipt task_start_records must have unique owner scopes"
            )
        if len(task_identities) != len(set(task_identities)):
            raise ContractValidationError(
                "Attempt receipt verified_tasks must have unique owner scopes"
            )
        if not set(task_identities).issubset(start_identities):
            raise ContractValidationError(
                "Attempt receipt verified_tasks must have corresponding task starts"
            )
        if status != "blocked" and set(task_identities) != set(start_identities):
            raise ContractValidationError(
                "Non-blocked attempt receipts require every task start to be verified"
            )
        if record["schema_version"] == "emrys.attempt-receipt.v1":
            for kind, reporting_state in record["reporting_completion_records"].items():
                if (
                    reporting_state["verified"] is not None
                    and reporting_state["start"] is None
                ):
                    raise ContractValidationError(
                        f"Attempt receipt {kind} verified reporting requires a start"
                    )
                if status != "blocked" and (
                    (reporting_state["start"] is None)
                    != (reporting_state["verified"] is None)
                ):
                    raise ContractValidationError(
                        f"Non-blocked attempt receipt has incomplete {kind} reporting"
                    )
        if status == "succeeded" and (exit_code != 0 or signal_number is not None):
            raise ContractValidationError(
                "Successful attempt receipt requires exit 0 and no signal"
            )
        if status == "failed" and (exit_code is None or signal_number is not None):
            raise ContractValidationError(
                "Failed attempt receipt requires an observed exit and no signal"
            )
        if status == "interrupted" and (exit_code is not None or signal_number is None):
            raise ContractValidationError(
                "Interrupted attempt receipt requires a signal and no exit code"
            )
        if status == "blocked":
            if not blockers:
                raise ContractValidationError(
                    "Blocked attempt receipt requires at least one blocker"
                )
            if exit_code is not None and signal_number is not None:
                raise ContractValidationError(
                    "Blocked attempt receipt may bind at most one exit or signal"
                )
        elif blockers:
            raise ContractValidationError(
                "Only blocked attempt receipts may retain blockers"
            )
        if status != "succeeded" and message is None:
            raise ContractValidationError(
                "Every non-success attempt receipt requires a message"
            )
    elif name in {"task-start", "task-attempt", "verified-task"}:
        _require_distinct_ids(
            record,
            "run_id",
            "workflow_attempt_id",
            "task_attempt_id",
            "owner_run_token",
        )
        if name == "task-attempt":
            _require_attempt_time(
                record["task_attempt_id"],
                record["started_at"],
                "task_attempt_id",
            )
    elif name in {"reporting-start", "verified-reporting"}:
        _require_distinct_ids(record, "run_id", "origin_workflow_attempt_id")


def _is_strict_json_value(value: Any) -> bool:
    """Return whether canonical bytes preserve the value's Python JSON types."""

    if value is None or type(value) in {str, int, float, bool}:
        return True
    if type(value) is list:
        return all(_is_strict_json_value(item) for item in value)
    if type(value) is dict:
        return all(
            type(key) is str and _is_strict_json_value(item)
            for key, item in value.items()
        )
    return False


def _validate_record_uncached(
    name: str,
    record: Any,
    *,
    profile: Mapping[str, Any] | None = None,
) -> None:
    errors = schema_errors(name, record)
    if errors:
        raise ContractValidationError(f"Invalid {name} record:\n" + "\n".join(errors))
    assert isinstance(record, Mapping)
    if name == "profile":
        _validate_profile(record)
    elif name == "request":
        _validate_request(record)
    elif name == "policy":
        _validate_policy(record)
    elif name == "execution":
        _validate_execution(record)
        if profile is None:
            raise ContractValidationError(
                "Execution validation requires its exact profile record"
            )
        validate_record("profile", profile)
        from emrys.contracts.orchestration.projection import (  # noqa: PLC0415
            validate_reporting_projection,
        )

        validate_reporting_projection(record, profile)
    elif name == "application-model":
        from emrys.contracts.orchestration.application_model import (  # noqa: PLC0415
            _validate_application_model_semantics,
        )

        _validate_application_model_semantics(record)
    _validate_identity_record(name, record)


@lru_cache(maxsize=2048)
def _validate_canonical_record(
    name: str,
    record_data: bytes,
    profile_data: bytes | None,
) -> None:
    """Cache only successful validation of exact canonical JSON content."""

    record = load_json_object_bytes(record_data, f"canonical {name} record")
    profile = (
        None
        if profile_data is None
        else load_json_object_bytes(profile_data, "canonical profile record")
    )
    _validate_record_uncached(name, record, profile=profile)


def validate_record(
    name: str,
    record: Any,
    *,
    profile: Mapping[str, Any] | None = None,
) -> None:
    """Validate one record against its closed schema and B0 record semantics.

    Runtime records are strict JSON values. Their canonical bytes form a safe,
    bounded memoization key for this pure validation step; filesystem and
    source-authority admission remains uncached in the owning boundaries.
    Non-JSON-native Python values retain the original direct validation path.
    """

    if _is_strict_json_value(record) and (
        profile is None or _is_strict_json_value(profile)
    ):
        _validate_canonical_record(
            name,
            canonical_json_bytes(record),
            None if profile is None else canonical_json_bytes(profile),
        )
        return
    _validate_record_uncached(name, record, profile=profile)


def load_record(
    path: str | Path,
    name: str,
    *,
    profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and validate one named orchestration record."""

    record = load_json_object(path)
    validate_record(name, record, profile=profile)
    return record


__all__ = (
    "SCHEMA_IDS",
    "SCHEMA_NAMES",
    "SCHEMA_PATHS",
    "ContractValidationError",
    "canonical_json_bytes",
    "canonical_sha256",
    "load_json_object",
    "load_json_object_bytes",
    "load_record",
    "load_schema_registry",
    "schema_errors",
    "schema_validator",
    "validate_record",
)
