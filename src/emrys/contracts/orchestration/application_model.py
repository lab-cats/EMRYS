"""Immutable successor records for Analysis, Execution Plan, and Run.

This module owns canonical values only.  It does not publish files, allocate
resources, or create Attempts.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, TypeAlias

from .api import (
    ContractValidationError,
    canonical_json_bytes,
    canonical_sha256,
    load_json_object_bytes,
    schema_errors,
    validate_record,
)

ANALYSIS_SCHEMA_VERSION = "emrys.analysis-revision.v1"
MODULE_ANALYSIS_SCHEMA_VERSION = "emrys.analysis-revision.v2"
EXECUTION_PLAN_SCHEMA_VERSION = "emrys.execution-plan.v1"
RUN_BINDING_SCHEMA_VERSION = "emrys.run-binding.v1"
LEGACY_EXECUTION_SCHEMA_VERSION = "emrys.execution.v1"

ANALYSIS_IDENTITY_DOMAIN = "emrys.analysis-revision-identity.v1"
MODULE_ANALYSIS_IDENTITY_DOMAIN = "emrys.analysis-revision-identity.v2"
EXECUTION_PLAN_IDENTITY_DOMAIN = "emrys.execution-plan-identity.v1"
RUN_IDENTITY_DOMAIN = "emrys.run-identity.v1"
IMPLEMENTATION_IDENTITY_DOMAIN = "emrys.implementation-content-identity.v1"
PROCESSING_STEP_IDS = frozenset(
    {"00a", "00b", "00c", "01", "02", "02b", "03", "04", "05", "06"}
)

_POLICY_FIELDS = (
    "control_condition",
    "treatment_condition",
    "background_condition",
    "rna_ref",
    "rna_alt",
    "min_sample_dp",
    "mean_dp_threshold",
    "fdr_threshold",
    "common_or_threshold",
    "absolute_difference_threshold",
    "background_max_fraction",
)
_SAMPLE_FIELDS = (
    "sample_id",
    "condition",
    "replicate",
    "strandedness",
    "r1_fastq_sha256",
    "r2_fastq_sha256",
)
_OWNER_FIELDS = ("machine_key", "step_id", "scope_type")
_EDGE_FIELDS = ("producer", "consumer", "artifact", "semantics")
_ARTIFACT_FIELDS = (
    "artifact_id_template",
    "step_id",
    "scope_type",
    "adapter",
    "source_path_template",
    "required",
)
_TOOL_FIELDS = ("kind", "logical_name", "content_sha256")
_IMPLEMENTATION_FIELDS = ("role", "logical_name", "content_sha256")
_PROCESSING_SOURCE_FIELDS = (
    "source_run_id",
    "workflow_attempt_id",
    "attempt_receipt_sha256",
)
_NON_RUN_TOOL_NAMES = {
    "runtime_profile",
    "storage_qualification",
    "renv_project",
    "renv_library",
}


def _closed_copy(
    value: Mapping[str, Any],
    fields: tuple[str, ...],
    label: str,
) -> dict[str, Any]:
    keys = set(value)
    expected = set(fields)
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise ContractValidationError(f"{label} must be closed ({'; '.join(details)})")
    return {field: value[field] for field in fields}


def _require_unique(values: Iterable[str], label: str) -> None:
    materialized = tuple(values)
    if len(materialized) != len(set(materialized)):
        raise ContractValidationError(f"{label} values must be unique")


def _canonical_rows(
    values: Iterable[Mapping[str, Any]],
    fields: tuple[str, ...],
    key,
    label: str,
) -> list[dict[str, Any]]:
    rows = [_closed_copy(value, fields, label) for value in values]
    rows.sort(key=key)
    return rows


def implementation_content_sha256(
    components: Iterable[Mapping[str, Any]],
) -> str:
    """Digest the closed executable implementation-content closure.

    Only executable scientific-computation and artifact-admission content may
    enter this closure.  Report renderers, templates, styles, and other
    downstream-only content are deliberately not representable.
    """

    rows = _canonical_rows(
        components,
        _IMPLEMENTATION_FIELDS,
        lambda row: (row["role"], row["logical_name"]),
        "implementation component",
    )
    if not rows:
        raise ContractValidationError("Implementation content may not be empty")
    for row in rows:
        if row["role"] not in {"scientific_computation", "artifact_admission"}:
            raise ContractValidationError(
                "Implementation role must be scientific_computation or "
                "artifact_admission"
            )
    _require_unique(
        (f"{row['role']}:{row['logical_name']}" for row in rows),
        "Implementation role/name",
    )
    return canonical_sha256(
        {
            "identity_domain": IMPLEMENTATION_IDENTITY_DOMAIN,
            "components": rows,
        }
    )


@dataclass(frozen=True, slots=True)
class _CanonicalRecord:
    """Deeply immutable record represented by its one canonical byte string."""

    _record_bytes: bytes
    schema_version: ClassVar[str]
    accepted_schema_versions: ClassVar[tuple[str, ...] | None] = None

    def __post_init__(self) -> None:
        record = load_json_object_bytes(
            self._record_bytes,
            f"canonical {self.schema_version} record",
        )
        if canonical_json_bytes(record) != self._record_bytes:
            raise ContractValidationError(
                f"{self.schema_version} record bytes must use canonical JSON"
            )
        validate_record("application-model", record)
        accepted = self.accepted_schema_versions or (self.schema_version,)
        if record.get("schema_version") not in accepted:
            raise ContractValidationError(
                f"Expected one of {', '.join(accepted)}, "
                f"got {record.get('schema_version')!r}"
            )

    @classmethod
    def from_record(cls, record: Mapping[str, Any]):
        """Construct from a JSON mapping and retain only canonical bytes."""

        return cls(canonical_json_bytes(record))

    @classmethod
    def from_bytes(cls, data: bytes):
        """Admit already-canonical bytes without creating a mutable authority."""

        return cls(bytes(data))

    @property
    def canonical_bytes(self) -> bytes:
        return self._record_bytes

    @property
    def record(self) -> dict[str, Any]:
        """Return a fresh projection; mutations cannot alter this value."""

        return load_json_object_bytes(self._record_bytes, self.schema_version)

    @property
    def record_sha256(self) -> str:
        return hashlib.sha256(self._record_bytes).hexdigest()


class AnalysisRevision(_CanonicalRecord):
    """One admitted, content-addressed scientific Analysis revision."""

    schema_version = ANALYSIS_SCHEMA_VERSION
    accepted_schema_versions = (
        ANALYSIS_SCHEMA_VERSION,
        MODULE_ANALYSIS_SCHEMA_VERSION,
    )

    @property
    def analysis_revision_id(self) -> str:
        return str(self.record["analysis_revision_id"])

    @property
    def identity_sha256(self) -> str:
        return self.analysis_revision_id.removeprefix("analysis-")

    def scope_id(
        self,
        scope_type: Literal[
            "reference", "sample", "cohort_partition", "cohort", "analysis"
        ],
        structural_id: str | None = None,
    ) -> str:
        """Derive versioned content-bound scope IDs without Project aliases.

        Sample IDs remain structural.  Cohort-partition scope binds the
        structural partition key to the content-bound cohort and exact
        partition declaration.  Reference, cohort, and analysis scopes bind
        their corresponding admitted Analysis content.
        """

        identity = self.record["identity"]
        if scope_type == "sample":
            sample_ids = {row["sample_id"] for row in identity["samples"]}
            if structural_id not in sample_ids:
                raise ContractValidationError("Unknown structural sample_id")
            assert structural_id is not None
            return structural_id
        if scope_type == "reference":
            content: Any = identity["reference"]
        elif scope_type == "cohort":
            content = {"samples": identity["samples"]}
        elif scope_type == "analysis":
            content = {"analysis_revision_sha256": self.identity_sha256}
        elif scope_type == "cohort_partition":
            partitions = {row["partition_id"]: row for row in identity["partitions"]}
            if structural_id not in partitions:
                raise ContractValidationError("Unknown structural partition_id")
            content = {
                "cohort_scope_id": self.scope_id("cohort"),
                "partition": partitions[structural_id],
            }
        else:  # pragma: no cover - Literal callers are checked statically.
            raise ContractValidationError(f"Unknown scope type: {scope_type}")
        domain = f"emrys.{scope_type}-scope-identity.v1"
        digest = canonical_sha256({"identity_domain": domain, "content": content})
        return f"scope-{scope_type.replace('_', '-')}-{digest}"


class ExecutionPlan(_CanonicalRecord):
    """One admitted effective plan, before allocation or Attempt realization."""

    schema_version = EXECUTION_PLAN_SCHEMA_VERSION

    @property
    def execution_plan_id(self) -> str:
        return str(self.record["execution_plan_id"])

    @property
    def identity_sha256(self) -> str:
        return self.execution_plan_id.removeprefix("plan-")


class RunBinding(_CanonicalRecord):
    """The sole immutable binding of an Analysis revision to an Execution Plan."""

    schema_version = RUN_BINDING_SCHEMA_VERSION

    @property
    def run_id(self) -> str:
        return str(self.record["run_id"])


@dataclass(frozen=True, slots=True)
class LegacyExecution:
    """Recognized historical execution.v1 bytes, never rewritten as a new Run."""

    source_bytes: bytes
    profile_validated: bool

    @property
    def record(self) -> dict[str, Any]:
        return load_json_object_bytes(
            self.source_bytes, LEGACY_EXECUTION_SCHEMA_VERSION
        )


ApplicationRecord: TypeAlias = AnalysisRevision | ExecutionPlan | RunBinding
ReadableApplicationRecord: TypeAlias = ApplicationRecord | LegacyExecution


def _build_analysis_revision(
    *,
    schema_version: str,
    identity_domain: str,
    samples: Iterable[Mapping[str, Any]],
    partitions: Iterable[Mapping[str, Any]],
    reference: Mapping[str, Any],
    selected_analysis: Mapping[str, Any],
) -> AnalysisRevision:
    sample_rows = _canonical_rows(
        samples,
        _SAMPLE_FIELDS,
        lambda row: row["sample_id"],
        "Analysis sample",
    )
    _require_unique((row["sample_id"] for row in sample_rows), "sample_id")

    partition_rows: list[dict[str, Any]] = []
    for partition in partitions:
        selector_type = partition.get("selector_type")
        fields = (
            ("partition_id", "selector_type", "selector_value")
            if selector_type == "region"
            else ("partition_id", "selector_type", "selector_file_sha256")
        )
        partition_rows.append(_closed_copy(partition, fields, "Analysis partition"))
    partition_rows.sort(key=lambda row: row["partition_id"])
    _require_unique(
        (row["partition_id"] for row in partition_rows),
        "partition_id",
    )
    identity = {
        "identity_domain": identity_domain,
        "samples": sample_rows,
        "partitions": partition_rows,
        "reference": _closed_copy(
            reference,
            ("fasta_sha256", "gtf_sha256"),
            "Analysis reference",
        ),
        **selected_analysis,
    }
    digest = canonical_sha256(identity)
    return AnalysisRevision.from_record(
        {
            "schema_version": schema_version,
            "identity": identity,
            "analysis_revision_id": f"analysis-{digest}",
        }
    )


def build_analysis_revision(
    *,
    samples: Iterable[Mapping[str, Any]],
    partitions: Iterable[Mapping[str, Any]],
    reference: Mapping[str, Any],
    scientific_policy: Mapping[str, Any],
) -> AnalysisRevision:
    """Build the exact historical paired-CMH scientific identity record."""

    return _build_analysis_revision(
        schema_version=ANALYSIS_SCHEMA_VERSION,
        identity_domain=ANALYSIS_IDENTITY_DOMAIN,
        samples=samples,
        partitions=partitions,
        reference=reference,
        selected_analysis={
            "scientific_policy": _closed_copy(
                scientific_policy, _POLICY_FIELDS, "Analysis scientific_policy"
            )
        },
    )


def build_module_analysis_revision(
    *,
    samples: Iterable[Mapping[str, Any]],
    partitions: Iterable[Mapping[str, Any]],
    reference: Mapping[str, Any],
    module_id: str,
    interface_version: str,
    module_version: str,
    config_schema_sha256: str,
    configuration: Mapping[str, Any],
) -> AnalysisRevision:
    """Build one path-neutral Analysis identity selected through a module."""

    return _build_analysis_revision(
        schema_version=MODULE_ANALYSIS_SCHEMA_VERSION,
        identity_domain=MODULE_ANALYSIS_IDENTITY_DOMAIN,
        samples=samples,
        partitions=partitions,
        reference=reference,
        selected_analysis={
            "analysis_module": {
                "module_id": module_id,
                "interface_version": interface_version,
                "module_version": module_version,
                "config_schema_sha256": config_schema_sha256,
                "configuration": dict(configuration),
            }
        },
    )


def analysis_revision_from_execution_fields(
    execution: Mapping[str, Any],
) -> AnalysisRevision:
    """Derive the Analysis value carried by a historical or adapter view."""

    samples = execution["samples"]["rows"]
    partitions = execution["partitions"]["rows"]
    reference = execution["reference"]
    policy = execution["analysis"]["policy"]
    common = {
        "samples": (
            {
                "sample_id": row["sample_id"],
                "condition": row["condition"],
                "replicate": row["replicate"],
                "strandedness": row["strandedness"],
                "r1_fastq_sha256": row["r1_fastq"]["sha256"],
                "r2_fastq_sha256": row["r2_fastq"]["sha256"],
            }
            for row in samples
        ),
        "partitions": (
            {
                "partition_id": row["partition_id"],
                "selector_type": row["selector_type"],
                **(
                    {"selector_value": row["selector_value"]}
                    if row["selector_type"] == "region"
                    else {"selector_file_sha256": row["selector_file"]["sha256"]}
                ),
            }
            for row in partitions
        ),
        "reference": {
            "fasta_sha256": reference["fasta"]["sha256"],
            "gtf_sha256": reference["gtf"]["sha256"],
        },
    }
    if policy.get("schema_version") == "emrys.analysis-module-policy.v1":
        module = policy["module"]
        return build_module_analysis_revision(
            **common,
            module_id=module["module_id"],
            interface_version=module["interface_version"],
            module_version=module["module_version"],
            config_schema_sha256=module["config_schema_sha256"],
            configuration=policy["configuration"],
        )
    return build_analysis_revision(
        **common,
        scientific_policy={
            key: value
            for key, value in policy.items()
            if key not in {"schema_version", "analysis_id"}
        },
    )


def _canonical_functional_specification(
    functional_specification: Mapping[str, Any],
) -> dict[str, Any]:
    owner_tasks = _canonical_rows(
        functional_specification["owner_tasks"],
        _OWNER_FIELDS,
        lambda row: row["machine_key"],
        "functional owner",
    )
    direct_edges = _canonical_rows(
        functional_specification["direct_edges"],
        _EDGE_FIELDS,
        lambda row: (
            row["producer"],
            row["consumer"],
            row["artifact"],
            row["semantics"],
        ),
        "functional edge",
    )
    artifact_templates = _canonical_rows(
        functional_specification["artifact_templates"],
        _ARTIFACT_FIELDS,
        lambda row: (
            row["step_id"],
            row["scope_type"],
            row["artifact_id_template"],
        ),
        "artifact template",
    )
    functional = _closed_copy(
        functional_specification,
        (
            "owner_tasks",
            "direct_edges",
            "required_owner_keys",
            "evidence_owner_keys",
            "artifact_templates",
        ),
        "functional specification",
    )
    functional.update(
        {
            "owner_tasks": owner_tasks,
            "direct_edges": direct_edges,
            "required_owner_keys": sorted(functional["required_owner_keys"]),
            "evidence_owner_keys": sorted(functional["evidence_owner_keys"]),
            "artifact_templates": artifact_templates,
        }
    )
    return functional


def functional_specification_from_profile(
    profile: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the canonical Run-bound functional value from a profile."""

    validate_record("profile", profile)
    return _canonical_functional_specification(
        {
            "owner_tasks": [
                {key: owner[key] for key in _OWNER_FIELDS}
                for owner in profile["owner_tasks"]
            ],
            "direct_edges": [dict(edge) for edge in profile["direct_edges"]],
            "required_owner_keys": list(profile["required_owner_keys"]),
            "evidence_owner_keys": list(profile["evidence_owner_keys"]),
            "artifact_templates": [
                {key: template[key] for key in _ARTIFACT_FIELDS}
                for template in profile["artifact_templates"]
            ],
        }
    )


def toolchain_from_required_tools(
    required_tools: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project canonical Run-bound tool content from Attempt observations."""

    tools: list[dict[str, Any]] = []
    for item in required_tools:
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise ContractValidationError("Required tool name must be nonempty")
        if name in _NON_RUN_TOOL_NAMES:
            continue
        content_sha256 = item.get("sha256")
        if not isinstance(content_sha256, str):
            raise ContractValidationError(
                f"Run-bound tool has no content identity: {name}"
            )
        tools.append(
            {
                "kind": "environment" if name.startswith("r_") else "tool",
                "logical_name": name,
                "content_sha256": content_sha256,
            }
        )
    canonical = _canonical_rows(
        tools,
        _TOOL_FIELDS,
        lambda row: (row["kind"], row["logical_name"]),
        "tool/environment identity",
    )
    _require_unique(
        (f"{row['kind']}:{row['logical_name']}" for row in canonical),
        "tool/environment kind/name",
    )
    return canonical


def build_execution_plan(
    *,
    functional_specification: Mapping[str, Any],
    scientific_stopping_owner_keys: Iterable[str],
    implementation_content_sha256: str,
    toolchain: Iterable[Mapping[str, Any]],
    backend: str,
    engine: str,
    backend_semantics_sha256: str,
    star_index: Mapping[str, Any],
    computational_resources: Mapping[str, Any],
    processing_source: Mapping[str, Any] | None = None,
) -> ExecutionPlan:
    """Build the exact pre-allocation, reporting-neutral Execution Plan."""

    functional = _canonical_functional_specification(functional_specification)
    tools = _canonical_rows(
        toolchain,
        _TOOL_FIELDS,
        lambda row: (row["kind"], row["logical_name"]),
        "tool/environment identity",
    )
    resources = _closed_copy(
        computational_resources,
        (
            "workflow_cores",
            "workflow_memory_mb",
            "stage_concurrency",
            "step_threads",
            "stage_memory_mb",
        ),
        "computational resource declaration",
    )
    resources.update(
        {
            name: dict(sorted(resources[name].items()))
            for name in ("stage_concurrency", "step_threads", "stage_memory_mb")
        }
    )
    identity = {
        "identity_domain": EXECUTION_PLAN_IDENTITY_DOMAIN,
        "functional_specification": functional,
        "scientific_stopping_owner_keys": sorted(scientific_stopping_owner_keys),
        "implementation_content_sha256": implementation_content_sha256,
        "toolchain": tools,
        "backend": {
            "backend": backend,
            "engine": engine,
            "semantics_sha256": backend_semantics_sha256,
        },
        "star_index": _closed_copy(
            star_index,
            ("sjdb_overhang", "genome_sa_index_nbases"),
            "STAR-index policy",
        ),
        "computational_resources": resources,
    }
    if processing_source is not None:
        identity["processing_source"] = _closed_copy(
            processing_source,
            _PROCESSING_SOURCE_FIELDS,
            "processing source",
        )
    digest = canonical_sha256(identity)
    return ExecutionPlan.from_record(
        {
            "schema_version": EXECUTION_PLAN_SCHEMA_VERSION,
            "identity": identity,
            "execution_plan_id": f"plan-{digest}",
        }
    )


def bind_run(analysis: AnalysisRevision, plan: ExecutionPlan) -> RunBinding:
    """Bind already-admitted identities; no allocation or Attempt fact is accepted."""

    binding = {
        "identity_domain": RUN_IDENTITY_DOMAIN,
        "analysis_revision_sha256": analysis.identity_sha256,
        "execution_plan_sha256": plan.identity_sha256,
    }
    return RunBinding.from_record(
        {
            "schema_version": RUN_BINDING_SCHEMA_VERSION,
            "binding": binding,
            "run_id": f"run-{canonical_sha256(binding)}",
        }
    )


def processing_stopping_owner_keys(functional: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the fixed evidence-complete processing owner roster."""

    required = set(map(str, functional["required_owner_keys"]))
    return tuple(
        sorted(
            str(owner["machine_key"])
            for owner in functional["owner_tasks"]
            if str(owner["step_id"]) in PROCESSING_STEP_IDS
            and str(owner["machine_key"]) in required
        )
    )


def execution_plan_boundary(
    plan: ExecutionPlan,
) -> Literal["analysis", "processing", "partial"]:
    """Classify the immutable scientific stopping roster."""

    identity = plan.record["identity"]
    selected = tuple(identity["scientific_stopping_owner_keys"])
    functional = identity["functional_specification"]
    if selected == tuple(functional["required_owner_keys"]):
        return "analysis"
    return (
        "processing"
        if selected == processing_stopping_owner_keys(functional)
        else "partial"
    )


def execution_owner_keys(plan: ExecutionPlan) -> tuple[str, ...]:
    """Return owners executed inside this Run rather than admitted from a source Run."""

    identity = plan.record["identity"]
    selected = set(identity["scientific_stopping_owner_keys"])
    if "processing_source" in identity:
        selected -= set(
            processing_stopping_owner_keys(identity["functional_specification"])
        )
    return tuple(sorted(selected))


def read_application_record(
    data: bytes,
    *,
    legacy_profile: Mapping[str, Any] | None = None,
) -> ReadableApplicationRecord:
    """Read a successor record or recognize historical execution.v1 unchanged.

    Historical bytes are preserved exactly.  Supplying the exact historical
    profile upgrades recognition to full legacy semantic validation; without
    it, the closed legacy schema is checked but no successor record is made.
    """

    record = load_json_object_bytes(data, "application record")
    version = record.get("schema_version")
    record_types: dict[str, type[_CanonicalRecord]] = {
        ANALYSIS_SCHEMA_VERSION: AnalysisRevision,
        MODULE_ANALYSIS_SCHEMA_VERSION: AnalysisRevision,
        EXECUTION_PLAN_SCHEMA_VERSION: ExecutionPlan,
        RUN_BINDING_SCHEMA_VERSION: RunBinding,
    }
    if not isinstance(version, str):
        raise ContractValidationError(
            f"Application record schema_version must be a string: {version!r}"
        )
    if version in record_types:
        return record_types[version].from_bytes(data)
    if version == LEGACY_EXECUTION_SCHEMA_VERSION:
        errors = schema_errors("execution", record)
        if errors:
            raise ContractValidationError(
                "Invalid historical execution record:\n" + "\n".join(errors)
            )
        if legacy_profile is not None:
            validate_record("execution", record, profile=legacy_profile)
        return LegacyExecution(bytes(data), legacy_profile is not None)
    raise ContractValidationError(f"Unsupported application record: {version!r}")


def validate_execution_view(
    record: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
) -> None:
    """Validate an exact historical execution.v1 view."""

    version = record.get("schema_version")
    if version != LEGACY_EXECUTION_SCHEMA_VERSION:
        raise ContractValidationError(f"Unsupported execution view: {version!r}")
    validate_record("execution", record, profile=profile)


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContractValidationError(f"{label} must be a positive integer")
    return value


def _validate_resource_resolution(
    plan: ExecutionPlan,
    resource_policy: Mapping[str, Any],
) -> None:
    expected_policy_fields = {
        "symbolic",
        "symbolic_sha256",
        "effective",
        "effective_sha256",
        "allocation",
        "sources",
    }
    if set(resource_policy) != expected_policy_fields:
        raise ContractValidationError("Workflow resource policy fields must be closed")
    symbolic = resource_policy.get("symbolic")
    effective = resource_policy.get("effective")
    allocation = resource_policy.get("allocation")
    sources = resource_policy.get("sources")
    if (
        not isinstance(symbolic, Mapping)
        or not isinstance(effective, Mapping)
        or not isinstance(allocation, Mapping)
        or not isinstance(sources, Mapping)
    ):
        raise ContractValidationError(
            "Workflow resource policy requires symbolic, effective, allocation, "
            "and sources mappings"
        )
    if canonical_sha256(symbolic) != resource_policy.get("symbolic_sha256"):
        raise ContractValidationError("Workflow symbolic resource digest differs")
    if canonical_sha256(effective) != resource_policy.get("effective_sha256"):
        raise ContractValidationError("Workflow resource policy digest differs")
    validate_record("resource-config", symbolic)
    validate_record("resource-config", effective)
    computational_fields = {
        "workflow_cores",
        "workflow_memory_mb",
        "stage_concurrency",
        "step_threads",
        "stage_memory_mb",
    }
    if not computational_fields <= set(effective):
        missing = sorted(computational_fields - set(effective))
        raise ContractValidationError(
            "Workflow resource resolution is incomplete: " + ", ".join(missing)
        )
    if not computational_fields <= set(symbolic):
        missing = sorted(computational_fields - set(symbolic))
        raise ContractValidationError(
            "Workflow symbolic resource policy is incomplete: " + ", ".join(missing)
        )
    if frozenset(allocation) not in {
        frozenset({"cores", "memory_mb", "source"}),
        frozenset({"cores", "memory_mb", "source", "slurm_job_id"}),
    }:
        raise ContractValidationError("Workflow allocation fields must be closed")
    if set(sources) != {
        "default_sha256",
        "config_path",
        "config_sha256",
        "cli_overrides",
    }:
        raise ContractValidationError("Workflow resource source fields must be closed")
    for field in ("default_sha256", "config_sha256"):
        value = sources[field]
        if field == "config_sha256" and value is None:
            continue
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ContractValidationError(
                f"Workflow resource source {field} must be a SHA-256 digest"
            )
    if sources["config_path"] is not None and not isinstance(
        sources["config_path"], str
    ):
        raise ContractValidationError(
            "Workflow resource source config_path must be a string or null"
        )
    if not isinstance(sources["cli_overrides"], list) or not all(
        isinstance(value, str) for value in sources["cli_overrides"]
    ):
        raise ContractValidationError(
            "Workflow resource source cli_overrides must be a string list"
        )
    allocation_cores = _positive_integer(allocation["cores"], "Allocation cores")
    allocation_memory = _positive_integer(allocation["memory_mb"], "Allocation memory")
    if not isinstance(allocation["source"], str) or not allocation["source"]:
        raise ContractValidationError("Allocation source must be nonempty")
    slurm_job_id = allocation.get("slurm_job_id")
    if slurm_job_id is not None and (
        not isinstance(slurm_job_id, str)
        or not slurm_job_id.isascii()
        or not slurm_job_id.isdecimal()
        or not slurm_job_id.strip("0")
    ):
        raise ContractValidationError(
            "Allocation Slurm job ID must be a positive decimal string or null"
        )

    declaration = plan.record["identity"]["computational_resources"]
    if {field: symbolic[field] for field in computational_fields} != declaration:
        raise ContractValidationError(
            "Symbolic computational resources differ from the Execution Plan"
        )
    workflow_cores = _positive_integer(
        effective["workflow_cores"], "Resolved workflow cores"
    )
    workflow_memory = _positive_integer(
        effective["workflow_memory_mb"], "Resolved workflow memory"
    )
    if workflow_cores != declaration["workflow_cores"]:
        raise ContractValidationError(
            "Resolved workflow cores differ from the Execution Plan"
        )
    declared_memory = declaration["workflow_memory_mb"]
    expected_memory = (
        allocation_memory if declared_memory == "allocation" else declared_memory
    )
    if workflow_memory != expected_memory:
        raise ContractValidationError(
            "Resolved workflow memory differs from the Execution Plan"
        )
    if workflow_cores > allocation_cores or workflow_memory > allocation_memory:
        raise ContractValidationError(
            "Resolved workflow resources exceed the observed allocation"
        )

    for field in ("stage_concurrency", "step_threads"):
        if effective[field] != declaration[field]:
            raise ContractValidationError(
                f"Resolved {field} differs from the Execution Plan"
            )
    expected_stage_memory = {
        step_id: workflow_memory if value == "workflow" else value
        for step_id, value in declaration["stage_memory_mb"].items()
    }
    if effective["stage_memory_mb"] != expected_stage_memory:
        raise ContractValidationError(
            "Resolved stage_memory_mb differs from the Execution Plan"
        )
    for step_id, memory in expected_stage_memory.items():
        concurrency = effective["stage_concurrency"].get(step_id, 1)
        threads = effective["step_threads"].get(step_id, 1)
        if concurrency * threads > workflow_cores:
            raise ContractValidationError(
                f"Resolved stage {step_id} CPU demand exceeds workflow cores"
            )
        if concurrency * memory > workflow_memory:
            raise ContractValidationError(
                f"Resolved stage {step_id} memory demand exceeds workflow memory"
            )
    reporting_memory = effective.get("reporting_memory_mb", {})
    if not isinstance(reporting_memory, Mapping):
        raise ContractValidationError("Resolved reporting_memory_mb must be a mapping")
    for kind, value in reporting_memory.items():
        memory = _positive_integer(value, f"Resolved reporting memory {kind}")
        if memory > workflow_memory:
            raise ContractValidationError(
                f"Resolved reporting memory {kind} exceeds workflow memory"
            )


def validate_successor_run(
    *,
    analysis: AnalysisRevision,
    plan: ExecutionPlan,
    run: RunBinding,
    profile: Mapping[str, Any],
    attempt: Mapping[str, Any] | None = None,
    resource_policy: Mapping[str, Any] | None = None,
    observed_implementation_content_sha256: str | None = None,
    observed_backend_semantics_sha256: str | None = None,
) -> None:
    """Prove that a successor Run and optional Attempt agree with authority."""

    if run.canonical_bytes != bind_run(analysis, plan).canonical_bytes:
        raise ContractValidationError(
            "Run binding differs from the admitted Analysis and Execution Plan"
        )

    plan_identity = plan.record["identity"]
    if (
        functional_specification_from_profile(profile)
        != plan_identity["functional_specification"]
    ):
        raise ContractValidationError(
            "Profile functional specification differs from the Execution Plan"
        )

    if attempt is not None:
        validate_record("workflow-attempt", attempt)
        if attempt["run_id"] != run.run_id:
            raise ContractValidationError("Attempt Run ID differs")
        if attempt["execution_contract_sha256"] != run.record_sha256:
            raise ContractValidationError("Attempt Run binding digest differs")
        if attempt["profile_sha256"] != canonical_sha256(profile):
            raise ContractValidationError("Attempt profile digest differs")
        if (
            toolchain_from_required_tools(attempt["required_tools"])
            != plan_identity["toolchain"]
        ):
            raise ContractValidationError(
                "Attempt tool content differs from the Execution Plan"
            )
        backend = plan_identity["backend"]
        if (
            attempt["executor"] != backend["backend"]
            or backend["engine"] != "snakemake"
        ):
            raise ContractValidationError(
                "Attempt executor differs from the Execution Plan backend"
            )

    if resource_policy is not None:
        _validate_resource_resolution(plan, resource_policy)
        if (
            attempt is not None
            and attempt["cores"] != resource_policy["effective"]["workflow_cores"]
        ):
            raise ContractValidationError(
                "Attempt cores differ from the resolved workflow resource policy"
            )
    if (
        observed_implementation_content_sha256 is not None
        and observed_implementation_content_sha256
        != plan_identity["implementation_content_sha256"]
    ):
        raise ContractValidationError(
            "Observed implementation content differs from the Execution Plan"
        )
    if (
        observed_backend_semantics_sha256 is not None
        and observed_backend_semantics_sha256
        != plan_identity["backend"]["semantics_sha256"]
    ):
        raise ContractValidationError(
            "Observed backend semantics differ from the Execution Plan"
        )


def _validate_analysis_semantics(record: Mapping[str, Any]) -> None:
    identity = record["identity"]
    if canonical_sha256(identity) != record["analysis_revision_id"].removeprefix(
        "analysis-"
    ):
        raise ContractValidationError("Analysis revision ID does not match identity")
    samples = identity["samples"]
    partitions = identity["partitions"]
    if samples != sorted(samples, key=lambda row: row["sample_id"]):
        raise ContractValidationError("Analysis samples must be sorted by sample_id")
    if partitions != sorted(partitions, key=lambda row: row["partition_id"]):
        raise ContractValidationError(
            "Analysis partitions must be sorted by partition_id"
        )
    _require_unique((row["sample_id"] for row in samples), "sample_id")
    _require_unique((row["partition_id"] for row in partitions), "partition_id")
    if record["schema_version"] == MODULE_ANALYSIS_SCHEMA_VERSION:
        return
    policy = identity["scientific_policy"]
    if policy["control_condition"] == policy["treatment_condition"]:
        raise ContractValidationError("Analysis conditions must differ")
    if policy["background_condition"] in {
        policy["control_condition"],
        policy["treatment_condition"],
    }:
        raise ContractValidationError("Analysis background condition must differ")
    if policy["rna_ref"] == policy["rna_alt"]:
        raise ContractValidationError(
            "Analysis reference and alternate bases must differ"
        )
    conditions = {row["condition"] for row in samples}
    required_conditions = {
        policy["control_condition"],
        policy["treatment_condition"],
    }
    if policy["background_condition"] is not None:
        required_conditions.add(policy["background_condition"])
    if not required_conditions <= conditions:
        raise ContractValidationError(
            "Analysis policy conditions must exist in the admitted samples"
        )
    controls: dict[str, int] = {}
    treatments: dict[str, int] = {}
    for sample in samples:
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
            "Analysis samples must define exactly one control and treatment "
            "for each of at least two complete replicate strata"
        )


def _validate_graph(edges: list[Mapping[str, Any]], owners: set[str]) -> None:
    identities: set[tuple[str, str, str]] = set()
    adjacency = {owner: set() for owner in owners}
    for edge in edges:
        pair = str(edge["producer"]), str(edge["consumer"])
        if not set(pair) <= owners:
            raise ContractValidationError(
                "Execution Plan edge references unknown owner"
            )
        identity = (*pair, str(edge["artifact"]))
        if identity in identities:
            raise ContractValidationError("Execution Plan repeats a direct owner edge")
        identities.add(identity)
        adjacency[pair[0]].add(pair[1])
    complete: set[str] = set()
    active: set[str] = set()

    def visit(owner: str) -> None:
        if owner in active:
            raise ContractValidationError("Execution Plan owner graph must be acyclic")
        if owner in complete:
            return
        active.add(owner)
        for consumer in sorted(adjacency[owner]):
            visit(consumer)
        active.remove(owner)
        complete.add(owner)

    for owner in sorted(owners):
        visit(owner)


def _validate_plan_semantics(record: Mapping[str, Any]) -> None:
    identity = record["identity"]
    if canonical_sha256(identity) != record["execution_plan_id"].removeprefix("plan-"):
        raise ContractValidationError("Execution Plan ID does not match identity")
    functional = identity["functional_specification"]
    owners_list = functional["owner_tasks"]
    if owners_list != sorted(owners_list, key=lambda row: row["machine_key"]):
        raise ContractValidationError(
            "Execution Plan owner_tasks must use canonical machine-key order"
        )
    edges = functional["direct_edges"]
    if edges != sorted(
        edges,
        key=lambda row: (
            row["producer"],
            row["consumer"],
            row["artifact"],
            row["semantics"],
        ),
    ):
        raise ContractValidationError(
            "Execution Plan direct_edges must use canonical content order"
        )
    artifacts = functional["artifact_templates"]
    if artifacts != sorted(
        artifacts,
        key=lambda row: (
            row["step_id"],
            row["scope_type"],
            row["artifact_id_template"],
        ),
    ):
        raise ContractValidationError(
            "Execution Plan artifact_templates must use canonical content order"
        )
    owner_keys = [row["machine_key"] for row in owners_list]
    _require_unique(owner_keys, "functional owner machine_key")
    owners = set(owner_keys)
    for field in (
        "required_owner_keys",
        "evidence_owner_keys",
        "scientific_stopping_owner_keys",
    ):
        values = (
            identity[field]
            if field == "scientific_stopping_owner_keys"
            else functional[field]
        )
        if values != sorted(values) or len(values) != len(set(values)):
            raise ContractValidationError(f"{field} must be a sorted set")
        if not set(values) <= owners:
            raise ContractValidationError(f"{field} references an unknown owner")
    if not set(functional["evidence_owner_keys"]) <= set(
        functional["required_owner_keys"]
    ):
        raise ContractValidationError("Evidence owners must also be required")
    _validate_graph(edges, owners)
    stopping = set(identity["scientific_stopping_owner_keys"])
    if not stopping <= set(functional["required_owner_keys"]):
        raise ContractValidationError(
            "scientific_stopping_owner_keys must reference required owners"
        )
    missing_predecessors = sorted(
        str(edge["producer"])
        for edge in edges
        if str(edge["consumer"]) in stopping and str(edge["producer"]) not in stopping
    )
    if missing_predecessors:
        raise ContractValidationError(
            "scientific_stopping_owner_keys must be predecessor-closed; missing "
            + ", ".join(missing_predecessors)
        )
    if "processing_source" in identity and stopping != set(
        functional["required_owner_keys"]
    ):
        raise ContractValidationError(
            "A processing source is valid only for a complete downstream Analysis plan"
        )
    _require_unique(
        (row["artifact_id_template"] for row in artifacts),
        "artifact_id_template",
    )
    tools = identity["toolchain"]
    _require_unique(
        (f"{row['kind']}:{row['logical_name']}" for row in tools),
        "tool/environment kind/name",
    )
    if tools != sorted(tools, key=lambda row: (row["kind"], row["logical_name"])):
        raise ContractValidationError("Toolchain identities must be canonicalized")


def _validate_run_semantics(record: Mapping[str, Any]) -> None:
    if record["run_id"] != f"run-{canonical_sha256(record['binding'])}":
        raise ContractValidationError("Run ID does not match its binding")


def _validate_application_model_semantics(record: Mapping[str, Any]) -> None:
    """Validate content identities after the shared closed schema succeeds."""

    version = record["schema_version"]
    if version in {ANALYSIS_SCHEMA_VERSION, MODULE_ANALYSIS_SCHEMA_VERSION}:
        _validate_analysis_semantics(record)
    elif version == EXECUTION_PLAN_SCHEMA_VERSION:
        _validate_plan_semantics(record)
    elif version == RUN_BINDING_SCHEMA_VERSION:
        _validate_run_semantics(record)
    else:
        raise ContractValidationError(f"Unsupported application record: {version!r}")


__all__ = (
    "ANALYSIS_SCHEMA_VERSION",
    "MODULE_ANALYSIS_SCHEMA_VERSION",
    "EXECUTION_PLAN_SCHEMA_VERSION",
    "RUN_BINDING_SCHEMA_VERSION",
    "LEGACY_EXECUTION_SCHEMA_VERSION",
    "AnalysisRevision",
    "ExecutionPlan",
    "RunBinding",
    "LegacyExecution",
    "ApplicationRecord",
    "ReadableApplicationRecord",
    "bind_run",
    "analysis_revision_from_execution_fields",
    "build_analysis_revision",
    "build_module_analysis_revision",
    "build_execution_plan",
    "functional_specification_from_profile",
    "implementation_content_sha256",
    "execution_plan_boundary",
    "execution_owner_keys",
    "processing_stopping_owner_keys",
    "read_application_record",
    "toolchain_from_required_tools",
    "validate_execution_view",
    "validate_successor_run",
)
