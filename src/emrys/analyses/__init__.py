"""Installed computation-provider boundary for scientific analyses."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, NamedTuple, TypeAlias

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    InstalledProviderV1,
    admit_installed_provider,
)
from emrys.libraries.validation import HEADER as VALIDATION_REPORT_HEADER

ANALYSIS_MODULE_ENTRY_POINT_GROUP = "emrys.analysis_modules"
ANALYSIS_MODULE_INTERFACE_V1 = "emrys.analysis-module.v1"
BUILTIN_PAIRED_CMH_MODULE_ID = "emrys.paired-cmh"
ANALYSIS_ARTIFACT_MEDIA_TYPES = MappingProxyType(
    {
        "pdf": "application/pdf",
        "sample_blocks_tsv": "text/tab-separated-values",
        "tsv": "text/tab-separated-values",
        "validation_report": "text/tab-separated-values",
    }
)
ANALYSIS_ARTIFACT_KINDS = frozenset(ANALYSIS_ARTIFACT_MEDIA_TYPES)

_SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_ARTIFACT_NAME_RE = re.compile(r"[a-z][a-z0-9_]*")
_RESERVED_DEPENDENCY_IDS = frozenset({"runtime_profile", "storage_qualification"})

JsonObject: TypeAlias = Mapping[str, object]


class AnalysisModuleLoadError(RuntimeError):
    """An installed analysis module could not be admitted."""


class AnalysisTaskPlanningError(ValueError):
    """An admitted module could not produce one closed task plan."""


class AnalysisInputV1(NamedTuple):
    """One semantic predecessor and its consumed artifact adapters."""

    producer: str
    adapters: tuple[str, ...]
    semantics: str = "required artifact"


class AnalysisArtifactV1(NamedTuple):
    """One module-owned output admitted by the core."""

    artifact_name: str
    adapter: str
    source_path_template: str
    kind: str
    expected_header: tuple[str, ...] | None = None
    exact_data_rows: int | None = None
    allow_header_only: bool = True


class AnalysisInputContextV1(NamedTuple):
    """Path-neutral Project content available during configuration admission."""

    samples: tuple[JsonObject, ...]
    partitions: tuple[JsonObject, ...]
    reference: JsonObject


class TaskInputV1(NamedTuple):
    """One stable provenance role and its exact task input path."""

    role: str
    path: Path


class TaskCommandPlanV1(NamedTuple):
    """Producer, validator, and complete provenance inputs for one task."""

    producer_argv: tuple[str, ...]
    validator_argv: tuple[str, ...]
    inputs: tuple[TaskInputV1, ...]


class TaskPlanningContextV1(NamedTuple):
    """Closed core projection; modules do not receive workflow layout internals."""

    reference_id: str
    cohort_id: str
    analysis_id: str
    sample_manifest: Path
    partition_manifest: Path
    reference_fasta: Path
    reference_gtf: Path
    source_commit: str
    configuration: JsonObject
    inputs: Mapping[str, tuple[Path, ...]]
    outputs: Mapping[str, Path]
    runtime_paths: Mapping[str, str]
    python_command: Callable[[tuple[str, ...]], tuple[str, ...]]
    r_owner_command: Callable[[tuple[str, ...]], tuple[str, ...]]
    validator_command: Callable[[tuple[str, ...]], tuple[str, ...]]
    threads: int = 1


ConfigNormalizerV1: TypeAlias = Callable[
    [JsonObject, AnalysisInputContextV1], JsonObject
]
TaskPlannerV1: TypeAlias = Callable[[TaskPlanningContextV1], TaskCommandPlanV1]


class AnalysisTaskV1(NamedTuple):
    owner_key: str
    step_id: str
    stage_memory_mb: int | Literal["workflow"]
    inputs: tuple[AnalysisInputV1, ...]
    outputs: tuple[AnalysisArtifactV1, ...]
    plan: TaskPlannerV1
    minimum_threads: int = 1


class AnalysisDependencyV1(NamedTuple):
    """One selected-module runtime dependency absent from the fixed profile."""

    dependency_id: str
    kind: Literal["executable", "r_namespace", "file", "package_tree"]
    target: str
    expected: str = ""
    probe_args: tuple[str, ...] = ()
    description: str = "analysis module dependency"


@dataclass(frozen=True, slots=True)
class AnalysisModuleDescriptorV1:
    module_id: str
    module_version: str
    config_schema: JsonObject
    normalize_config: ConfigNormalizerV1
    tasks: tuple[AnalysisTaskV1, ...]
    dependencies: tuple[str | AnalysisDependencyV1, ...]


@dataclass(frozen=True, slots=True)
class LoadedAnalysisModuleV1:
    descriptor: AnalysisModuleDescriptorV1
    provider: InstalledProviderV1


def module_profile_record(
    descriptor: AnalysisModuleDescriptorV1,
) -> dict[str, list[object]]:
    """Project one selected downstream module into the workflow profile."""

    owners = [task.owner_key for task in descriptor.tasks]
    return {
        "semantic_owner_keys": list(owners),
        "owner_tasks": [
            {
                "machine_key": task.owner_key,
                "rule_name": f"analysis_owner_{task.step_id}",
                "step_id": task.step_id,
                "scope_type": "analysis",
                "scope_selector": "analysis",
            }
            for task in descriptor.tasks
        ],
        "direct_edges": [
            {
                "producer": declared.producer,
                "consumer": task.owner_key,
                "artifact": ", ".join(declared.adapters),
                "semantics": declared.semantics,
            }
            for task in descriptor.tasks
            for declared in task.inputs
        ],
        "required_owner_keys": list(owners),
        "evidence_owner_keys": [],
        "artifact_templates": [
            {
                "artifact_id_template": (
                    f"analysis.{{analysis_id}}.{artifact.artifact_name}"
                ),
                "step_id": task.step_id,
                "scope_type": "analysis",
                "scope_selector": "analysis",
                "adapter": artifact.adapter,
                "source_path_template": artifact.source_path_template,
                "required": True,
            }
            for task in descriptor.tasks
            for artifact in task.outputs
        ],
    }


def compose_profile(
    base: Mapping[str, Any],
    descriptor: AnalysisModuleDescriptorV1,
) -> dict[str, object]:
    """Compose exactly one selected module tail onto a processing profile."""

    if any(str(task.get("step_id")) in {"09", "10"} for task in base["owner_tasks"]):
        raise AnalysisModuleLoadError(
            "Analysis module must be composed onto the processing profile exactly once"
        )
    fragment = module_profile_record(descriptor)
    base_adapters = {
        str(template["adapter"]) for template in base["artifact_templates"]
    }
    selected_adapters = {
        str(template["adapter"]) for template in fragment["artifact_templates"]
    }
    if collisions := sorted(base_adapters & selected_adapters):
        raise AnalysisModuleLoadError(
            "Analysis module adapter collides with processing profile: "
            + ", ".join(collisions)
        )
    composed: dict[str, object] = {
        key: base[key] for key in ("schema_version", "profile_id", "profile_version")
    }
    composed.update(
        {key: [*base[key], *values] for key, values in fragment.items()}
    )
    try:
        orchestration_contracts.validate_record("profile", composed)
    except orchestration_contracts.ContractValidationError as exc:
        raise AnalysisModuleLoadError(str(exc)) from exc
    return composed


def _safe_id(value: object, pattern: re.Pattern[str] = _SAFE_ID_RE) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _safe_artifact(output: AnalysisArtifactV1) -> bool:
    path = output.source_path_template
    return (
        _safe_id(output.artifact_name, _ARTIFACT_NAME_RE)
        and _safe_id(output.adapter)
        and output.kind in ANALYSIS_ARTIFACT_KINDS
        and "{analysis_id}" in path
        and "{" not in path.replace("{analysis_id}", "")
        and "}" not in path.replace("{analysis_id}", "")
        and "\\" not in path
        and path.startswith(
            "products/native/"
            if output.kind == "validation_report"
            else ("results/", "products/native/")
        )
        and all(part not in {"", ".", ".."} for part in path.split("/"))
        and (
            output.expected_header is None
            or bool(output.expected_header)
            and all(output.expected_header)
        )
        and (
            output.exact_data_rows is None
            or type(output.exact_data_rows) is int
            and output.exact_data_rows >= 0
        )
        and isinstance(output.allow_header_only, bool)
        and (
            output.kind != "validation_report"
            or output.expected_header == VALIDATION_REPORT_HEADER
        )
    )


def _dependency_record(
    dependency: str | AnalysisDependencyV1,
) -> dict[str, object]:
    if isinstance(dependency, str):
        return {"dependency_id": dependency, "kind": "existing_check"}
    record: dict[str, object] = {
        "dependency_id": dependency.dependency_id,
        "kind": dependency.kind,
    }
    if dependency.kind == "r_namespace":
        record["target"] = dependency.target
    if dependency.kind in {"executable", "r_namespace"}:
        record["expected"] = dependency.expected
    if dependency.kind == "executable":
        record["probe_args"] = list(dependency.probe_args)
    return record


def dependency_records(
    descriptor: AnalysisModuleDescriptorV1,
) -> tuple[dict[str, object], ...]:
    """Return the canonical, order-neutral dependency declarations."""

    return tuple(
        sorted(
            (_dependency_record(item) for item in descriptor.dependencies),
            key=lambda item: str(item["dependency_id"]),
        )
    )


def dependency_ids(
    descriptor: AnalysisModuleDescriptorV1,
) -> tuple[str, ...]:
    """Return dependency IDs in their canonical order."""

    return tuple(str(item["dependency_id"]) for item in dependency_records(descriptor))


def _validate_descriptor(descriptor: AnalysisModuleDescriptorV1) -> None:
    if not _safe_id(descriptor.module_id) or not _safe_id(descriptor.module_version):
        raise AnalysisModuleLoadError("Analysis module ID and version must be safe IDs")
    if not callable(descriptor.normalize_config):
        raise AnalysisModuleLoadError("Analysis module normalizer must be callable")
    try:
        Draft202012Validator.check_schema(descriptor.config_schema)
    except SchemaError as exc:
        raise AnalysisModuleLoadError(
            "Analysis module configuration schema is invalid"
        ) from exc
    tasks = descriptor.tasks
    if tuple(task.step_id for task in tasks) not in {("09",), ("09", "10")}:
        raise AnalysisModuleLoadError(
            "Analysis module tasks must occupy Step 09, optionally followed by Step 10"
        )
    if len({task.owner_key for task in tasks}) != len(tasks):
        raise AnalysisModuleLoadError("Analysis module owner keys must be unique")
    outputs: list[AnalysisArtifactV1] = []
    for task in tasks:
        if (
            not _safe_id(task.owner_key)
            or not callable(task.plan)
            or not (
                task.stage_memory_mb == "workflow"
                or type(task.stage_memory_mb) is int
                and task.stage_memory_mb > 0
            )
            or type(task.minimum_threads) is not int
            or task.minimum_threads < 1
            or any(
                not _safe_id(item.producer)
                or not item.adapters
                or len(item.adapters) != len(set(item.adapters))
                or not all(_safe_id(adapter) for adapter in item.adapters)
                or not item.semantics
                for item in task.inputs
            )
            or len({item.producer for item in task.inputs}) != len(task.inputs)
            or any(not _safe_artifact(output) for output in task.outputs)
            or sum(output.kind == "validation_report" for output in task.outputs) != 1
        ):
            raise AnalysisModuleLoadError("Invalid analysis module task declaration")
        outputs.extend(task.outputs)
    if len({output.adapter for output in outputs}) != len(outputs) or len(
        {output.artifact_name for output in outputs}
    ) != len(outputs):
        raise AnalysisModuleLoadError("Analysis module outputs must be unique")
    dependencies = descriptor.dependencies
    records = dependency_records(descriptor)
    dependency_ids = [str(item["dependency_id"]) for item in records]
    if len(dependency_ids) != len(set(dependency_ids)):
        raise AnalysisModuleLoadError("Analysis module dependencies must be unique")
    if _RESERVED_DEPENDENCY_IDS.intersection(dependency_ids):
        raise AnalysisModuleLoadError("Analysis module dependency ID is reserved")
    for dependency in dependencies:
        if isinstance(dependency, str):
            if not _safe_id(dependency):
                raise AnalysisModuleLoadError(
                    "Analysis module runtime checks must be safe IDs"
                )
            continue
        if not isinstance(dependency, AnalysisDependencyV1) or not _safe_id(
            dependency.dependency_id
        ):
            raise AnalysisModuleLoadError(
                "Analysis module dependency IDs must be safe IDs"
            )
        if (
            dependency.kind not in {"executable", "r_namespace", "file", "package_tree"}
            or not dependency.description
            or "\x00" in dependency.target
            or (
                dependency.kind != "r_namespace"
                and not Path(dependency.target).is_absolute()
            )
        ):
            raise AnalysisModuleLoadError("Invalid analysis module dependency")
        if dependency.kind == "executable":
            if not dependency.expected or not dependency.probe_args:
                raise AnalysisModuleLoadError(
                    "Executable dependencies require probe arguments and a version pattern"
                )
        elif dependency.kind == "r_namespace":
            if (
                re.fullmatch(r"[A-Za-z][A-Za-z0-9.]*", dependency.target) is None
                or not dependency.expected
                or dependency.probe_args
            ):
                raise AnalysisModuleLoadError("Invalid R namespace dependency")
        elif dependency.expected or dependency.probe_args:
            raise AnalysisModuleLoadError(
                "File and package-tree dependencies do not accept probes"
            )
        if dependency.expected:
            try:
                re.compile(dependency.expected)
            except re.error as exc:
                raise AnalysisModuleLoadError(
                    "Analysis module dependency version pattern is invalid"
                ) from exc


def load_analysis_module(module_id: str) -> LoadedAnalysisModuleV1:
    """Load one exact installed module selected by Project configuration."""

    try:
        provider = admit_installed_provider(
            ANALYSIS_MODULE_ENTRY_POINT_GROUP,
            module_id,
            label="Analysis module",
        )
    except InstalledPackageIdentityError as exc:
        raise AnalysisModuleLoadError(str(exc)) from exc
    try:
        descriptor = provider.provider()
    except Exception as exc:
        raise AnalysisModuleLoadError(
            f"Analysis module provider failed: {module_id!r}"
        ) from exc
    if not isinstance(descriptor, AnalysisModuleDescriptorV1):
        raise AnalysisModuleLoadError(
            f"Provider returned the wrong descriptor type: {module_id!r}"
        )
    if descriptor.module_id != module_id:
        raise AnalysisModuleLoadError(
            f"Descriptor ID differs from entry point: {descriptor.module_id!r}"
        )
    _validate_descriptor(descriptor)
    try:
        provider.require_callables(
            descriptor.normalize_config,
            *(task.plan for task in descriptor.tasks),
            label="Analysis module",
        )
    except InstalledPackageIdentityError as exc:
        raise AnalysisModuleLoadError(str(exc)) from exc
    return LoadedAnalysisModuleV1(descriptor=descriptor, provider=provider)


def admit_configuration(
    descriptor: AnalysisModuleDescriptorV1,
    configuration: JsonObject,
    context: AnalysisInputContextV1,
) -> dict[str, object]:
    """Validate syntax, normalize semantics once, and freeze canonical JSON."""

    validator = Draft202012Validator(descriptor.config_schema)

    def validate(value: Mapping[str, object]) -> None:
        errors = sorted(validator.iter_errors(value), key=lambda item: item.json_path)
        if errors:
            raise ValueError(
                f"Invalid {descriptor.module_id} configuration: {errors[0].message}"
            )

    validate(configuration)
    configuration_copy = orchestration_contracts.load_json_object_bytes(
        orchestration_contracts.canonical_json_bytes(configuration),
        "analysis-module configuration",
    )
    normalized = descriptor.normalize_config(configuration_copy, context)
    if not isinstance(normalized, Mapping):
        raise ValueError("Analysis module normalizer must return an object")
    validate(normalized)
    data = orchestration_contracts.canonical_json_bytes(normalized)
    return orchestration_contracts.load_json_object_bytes(
        data, "normalized analysis-module configuration"
    )


def module_identity_record(module: LoadedAnalysisModuleV1) -> dict[str, object]:
    """Return persisted provider facts that are not scientific identity."""

    descriptor = module.descriptor
    provider = module.provider
    return {
        "module_id": descriptor.module_id,
        "interface_version": ANALYSIS_MODULE_INTERFACE_V1,
        "module_version": descriptor.module_version,
        "distribution_name": provider.distribution_name,
        "distribution_version": provider.distribution_version,
        "entry_point": provider.entry_point_value,
        "config_schema_sha256": orchestration_contracts.canonical_sha256(
            descriptor.config_schema
        ),
        "dependencies": list(dependency_records(descriptor)),
    }


def module_admission_record(module: LoadedAnalysisModuleV1) -> dict[str, object]:
    """Return provider metadata plus the exact installed implementation digest."""

    return {
        "module": module_identity_record(module),
        "implementation_sha256": module.provider.package.sha256,
    }


def readmit_analysis_module(
    policy: JsonObject,
) -> LoadedAnalysisModuleV1:
    """Reload the provider bound by persisted policy without renormalizing config."""

    persisted = policy.get("module")
    if policy.get("schema_version") == "emrys.analysis-policy.v1":
        module_id = BUILTIN_PAIRED_CMH_MODULE_ID
    elif isinstance(persisted, Mapping) and isinstance(persisted.get("module_id"), str):
        module_id = str(persisted["module_id"])
    else:
        raise AnalysisModuleLoadError("Persisted analysis policy has no module")
    loaded = load_analysis_module(module_id)
    if persisted is not None and persisted != module_identity_record(loaded):
        raise AnalysisModuleLoadError(
            "Installed analysis module differs from persisted Run policy"
        )
    persisted_implementation = policy.get("implementation_sha256")
    if (
        policy.get("schema_version") == "emrys.analysis-module-policy.v1"
        and persisted_implementation != loaded.provider.package.sha256
    ):
        raise AnalysisModuleLoadError(
            "Installed analysis module implementation differs from persisted Run policy"
        )
    return loaded


__all__ = (
    "ANALYSIS_ARTIFACT_KINDS",
    "ANALYSIS_ARTIFACT_MEDIA_TYPES",
    "ANALYSIS_MODULE_ENTRY_POINT_GROUP",
    "ANALYSIS_MODULE_INTERFACE_V1",
    "BUILTIN_PAIRED_CMH_MODULE_ID",
    "VALIDATION_REPORT_HEADER",
    "AnalysisArtifactV1",
    "AnalysisDependencyV1",
    "AnalysisInputContextV1",
    "AnalysisInputV1",
    "AnalysisModuleDescriptorV1",
    "AnalysisModuleLoadError",
    "AnalysisTaskPlanningError",
    "AnalysisTaskV1",
    "LoadedAnalysisModuleV1",
    "TaskCommandPlanV1",
    "TaskInputV1",
    "TaskPlanningContextV1",
    "admit_configuration",
    "compose_profile",
    "dependency_records",
    "dependency_ids",
    "load_analysis_module",
    "module_admission_record",
    "module_identity_record",
    "module_profile_record",
    "readmit_analysis_module",
)
