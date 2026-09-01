"""Small, installed-module boundary for downstream scientific analyses."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NamedTuple, TypeAlias

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from emrys.contracts import orchestration as orchestration_contracts
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    InstalledProviderV1,
    admit_installed_provider,
)
from emrys.libraries.validation import HEADER as VALIDATION_REPORT_HEADER

ANALYSIS_MODULE_ENTRY_POINT_GROUP = "emrys.analysis_modules"
ANALYSIS_MODULE_INTERFACE_V1 = "emrys.analysis-module.v1"
BUILTIN_PAIRED_CMH_MODULE_ID = "emrys.paired-cmh"
_SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_LOWER_ID_RE = re.compile(r"[a-z][a-z0-9_]*")
ANALYSIS_ARTIFACT_KINDS = frozenset(
    {"pdf", "sample_blocks_tsv", "tsv", "validation_report"}
)

JsonObject: TypeAlias = Mapping[str, object]


class AnalysisModuleLoadError(RuntimeError):
    pass


class AnalysisTaskPlanningError(ValueError):
    pass


class AnalysisInputV1(NamedTuple):
    """One predecessor and the exact admitted adapters consumed from it."""

    producer: str
    adapters: tuple[str, ...]
    semantics: str = "required artifact"


class AnalysisArtifactV1(NamedTuple):
    artifact_name: str
    adapter: str
    source_path_template: str
    kind: str
    expected_header: tuple[str, ...] | None = None
    exact_data_rows: int | None = None
    allow_header_only: bool = True


class AnalysisInputContextV1(NamedTuple):
    samples: tuple[JsonObject, ...]
    partitions: tuple[JsonObject, ...]
    reference: JsonObject


class TaskCommandPlanV1(NamedTuple):
    producer_argv: tuple[str, ...]
    validator_argv: tuple[str, ...]
    input_paths: tuple[Path, ...]


class TaskPlanningContextV1(NamedTuple):
    reference_id: str
    cohort_id: str
    analysis_id: str
    sample_manifest: Path
    partition_manifest: Path
    reference_fasta: Path
    reference_gtf: Path
    source_commit: str
    configuration: JsonObject
    output_path: Callable[[str], Path]
    artifact_path: Callable[[str, str, str], Path]
    runtime_path: Callable[[str], str]
    python_command: Callable[[tuple[str, ...]], tuple[str, ...]]
    r_owner_command: Callable[[tuple[str, ...]], tuple[str, ...]]
    validator_command: Callable[[tuple[str, ...]], tuple[str, ...]]


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


@dataclass(frozen=True, slots=True)
class AnalysisModuleDescriptorV1:
    module_id: str
    module_version: str
    config_schema: JsonObject
    normalize_config: ConfigNormalizerV1
    tasks: tuple[AnalysisTaskV1, ...]
    required_runtime_checks: tuple[str, ...]


def module_profile_record(descriptor: AnalysisModuleDescriptorV1) -> dict[str, object]:
    """Project the selected analysis tasks into the immutable Run profile."""

    owners = [task.owner_key for task in descriptor.tasks]
    return {
        "semantic_owner_keys": owners,
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
                "producer": item.producer,
                "consumer": task.owner_key,
                "artifact": adapter,
                "semantics": item.semantics,
            }
            for task in descriptor.tasks
            for item in task.inputs
            for adapter in item.adapters
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


def admit_configuration(
    descriptor: AnalysisModuleDescriptorV1,
    configuration: JsonObject,
    context: AnalysisInputContextV1,
) -> dict[str, object]:
    """Validate declared syntax before invoking module-owned semantics."""

    validator = Draft202012Validator(descriptor.config_schema)

    def validate(value: Mapping[str, object]) -> None:
        errors = sorted(validator.iter_errors(value), key=lambda item: item.json_path)
        if errors:
            raise ValueError(
                f"Invalid {descriptor.module_id} configuration: {errors[0].message}"
            )

    validate(configuration)
    normalized = descriptor.normalize_config(dict(configuration), context)
    if not isinstance(normalized, Mapping):
        raise ValueError(
            "Analysis module normalizer must return a configuration object"
        )
    normalized = dict(normalized)
    validate(normalized)
    return normalized


def compose_profile(
    base: Mapping[str, Any],
    descriptor: AnalysisModuleDescriptorV1,
) -> dict[str, object]:
    """Compose one selected analysis tail onto the fixed processing profile."""

    fragment = module_profile_record(descriptor)
    composed: dict[str, object] = {
        key: base[key] for key in ("schema_version", "profile_id", "profile_version")
    }
    composed.update({key: [*base[key], *values] for key, values in fragment.items()})
    try:
        orchestration_contracts.validate_record("profile", composed)
    except orchestration_contracts.ContractValidationError as exc:
        raise AnalysisModuleLoadError(str(exc)) from exc
    return composed


@dataclass(frozen=True, slots=True)
class LoadedAnalysisModuleV1:
    descriptor: AnalysisModuleDescriptorV1
    provider: InstalledProviderV1


def module_identity_record(module: LoadedAnalysisModuleV1) -> dict[str, object]:
    """Project the installed provider facts persisted with a modular Run."""

    descriptor = module.descriptor
    return {
        "module_id": descriptor.module_id,
        "interface_version": ANALYSIS_MODULE_INTERFACE_V1,
        "module_version": descriptor.module_version,
        "distribution_name": module.provider.distribution_name,
        "distribution_version": module.provider.distribution_version,
        "entry_point": module.provider.entry_point_value,
        "config_schema_sha256": orchestration_contracts.canonical_sha256(
            descriptor.config_schema
        ),
        "required_runtime_checks": list(descriptor.required_runtime_checks),
    }


def _safe_id(value: object, pattern: re.Pattern[str] = _SAFE_ID_RE) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _safe_output(output: AnalysisArtifactV1) -> bool:
    path, header, rows = (
        output.source_path_template,
        output.expected_header,
        output.exact_data_rows,
    )
    return (
        _safe_id(output.artifact_name, _LOWER_ID_RE)
        and _safe_id(output.adapter)
        and output.kind in ANALYSIS_ARTIFACT_KINDS
        and isinstance(path, str)
        and "{analysis_id}" in path
        and not any(token in path.replace("{analysis_id}", "") for token in "{}\\")
        and path.startswith(("results/", "products/native/"))
        and not any(part in {"", ".", ".."} for part in path.split("/"))
        and (
            header is None
            or isinstance(header, tuple)
            and all(isinstance(value, str) and value for value in header)
        )
        and (rows is None or type(rows) is int and rows >= 0)
        and isinstance(output.allow_header_only, bool)
        and (
            output.kind != "validation_report"
            or header in (None, VALIDATION_REPORT_HEADER)
        )
    )


def _validate_v1_shape(descriptor: AnalysisModuleDescriptorV1) -> None:
    tasks, checks = descriptor.tasks, descriptor.required_runtime_checks
    if not isinstance(tasks, tuple) or not all(
        isinstance(task, AnalysisTaskV1)
        and _safe_id(task.owner_key)
        and task.step_id in {"09", "10"}
        and (
            task.stage_memory_mb == "workflow"
            or type(task.stage_memory_mb) is int
            and task.stage_memory_mb > 0
        )
        and callable(task.plan)
        and isinstance(task.inputs, tuple)
        and all(
            isinstance(item, AnalysisInputV1)
            and _safe_id(item.producer)
            and isinstance(item.adapters, tuple)
            and item.adapters
            and all(_safe_id(adapter) for adapter in item.adapters)
            and len(item.adapters) == len(set(item.adapters))
            and isinstance(item.semantics, str)
            and bool(item.semantics)
            for item in task.inputs
        )
        and isinstance(task.outputs, tuple)
        and all(
            isinstance(output, AnalysisArtifactV1) and _safe_output(output)
            for output in task.outputs
        )
        and sum(output.kind == "validation_report" for output in task.outputs) == 1
        for task in tasks
    ):
        raise AnalysisModuleLoadError("Invalid analysis module v1 task declaration")
    outputs = tuple(output for task in tasks for output in task.outputs)
    if (
        not 1 <= len(tasks) <= 2
        or len({task.owner_key for task in tasks}) != len(tasks)
        or len({task.step_id for task in tasks}) != len(tasks)
        or len({output.adapter for output in outputs}) != len(outputs)
        or len({output.artifact_name for output in outputs}) != len(outputs)
        or not isinstance(checks, tuple)
        or not checks
        or not all(_safe_id(check, _LOWER_ID_RE) for check in checks)
        or len(checks) != len(set(checks))
        or not _safe_id(descriptor.module_id)
        or not _safe_id(descriptor.module_version)
        or not callable(descriptor.normalize_config)
    ):
        raise AnalysisModuleLoadError(
            "Analysis module v1 must fill the exact Step 09/10 analysis slots"
        )


def load_analysis_module(module_id: str) -> LoadedAnalysisModuleV1:
    """Load only the one exact installed module selected by ``module_id``."""

    try:
        installed = admit_installed_provider(
            ANALYSIS_MODULE_ENTRY_POINT_GROUP,
            module_id,
            label="Analysis module",
        )
    except InstalledPackageIdentityError as exc:
        raise AnalysisModuleLoadError(str(exc)) from exc
    try:
        descriptor = installed.provider()
    except Exception as exc:
        raise AnalysisModuleLoadError(
            f"Provider could not be loaded: {module_id!r}"
        ) from exc
    if not isinstance(descriptor, AnalysisModuleDescriptorV1):
        raise AnalysisModuleLoadError(
            f"Provider returned wrong descriptor type: {module_id!r}"
        )
    if descriptor.module_id != module_id:
        raise AnalysisModuleLoadError(
            f"Analysis module descriptor ID does not match entry point: {descriptor.module_id!r}"
        )
    try:
        Draft202012Validator.check_schema(descriptor.config_schema)
    except SchemaError as exc:
        raise AnalysisModuleLoadError(
            "Analysis module configuration schema is invalid"
        ) from exc
    _validate_v1_shape(descriptor)
    try:
        installed.require_callables(
            descriptor.normalize_config,
            *(task.plan for task in descriptor.tasks),
            label="Analysis module",
        )
    except InstalledPackageIdentityError as exc:
        raise AnalysisModuleLoadError(str(exc)) from exc
    return LoadedAnalysisModuleV1(descriptor, installed)


def module_admission_record(module: LoadedAnalysisModuleV1) -> dict[str, object]:
    """Return the exact module facts that must survive operation boundaries."""

    return {
        "module": module_identity_record(module),
        "implementation_sha256": module.provider.package.sha256,
    }


def readmit_analysis_module(
    policy: JsonObject,
    *,
    admitted: LoadedAnalysisModuleV1 | None = None,
) -> LoadedAnalysisModuleV1:
    """Reload the exact module selected by persisted policy and optional admission."""

    persisted = policy.get("module")
    module_id = persisted.get("module_id") if isinstance(persisted, Mapping) else None
    if not isinstance(module_id, str) and (
        policy.get("schema_version") == "emrys.analysis-policy.v1"
        and admitted is not None
    ):
        module_id = admitted.descriptor.module_id
    if not isinstance(module_id, str):
        raise AnalysisModuleLoadError("Persisted analysis policy has no module")
    loaded = load_analysis_module(module_id)
    if persisted is not None and persisted != module_identity_record(loaded):
        raise AnalysisModuleLoadError(
            "Installed analysis module differs from persisted Run policy"
        )
    if admitted is not None and (
        module_admission_record(loaded) != module_admission_record(admitted)
    ):
        raise AnalysisModuleLoadError(
            "Installed analysis module differs from Project admission"
        )
    return loaded
