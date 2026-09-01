"""Small, installed-module boundary for downstream scientific analyses."""

from __future__ import annotations

import importlib.metadata
import importlib.resources
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, NamedTuple, TypeAlias

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from emrys.contracts import orchestration as orchestration_contracts
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_python_package_identity,
)
from emrys.libraries.validation import HEADER as VALIDATION_REPORT_HEADER

ANALYSIS_MODULE_ENTRY_POINT_GROUP = "emrys.analysis_modules"
ANALYSIS_MODULE_INTERFACE_V1 = "emrys.analysis-module.v1"
BUILTIN_PAIRED_CMH_MODULE_ID = "emrys.paired-cmh"
ANALYSIS_MEDIA_TYPE_BY_KIND = {
    "pdf": "application/pdf",
    "sample_blocks_tsv": "text/tab-separated-values",
    "tsv": "text/tab-separated-values",
    "validation_report": "text/tab-separated-values",
}

JsonObject: TypeAlias = Mapping[str, object]


class AnalysisModuleLoadError(RuntimeError):
    pass


class AnalysisTaskPlanningError(ValueError):
    pass


def effective_configuration(policy: JsonObject) -> JsonObject:
    """Return the module configuration without its public policy envelope."""

    schema = policy.get("schema_version")
    if schema == "emrys.analysis-module-policy.v1":
        configuration = policy.get("configuration")
        if not isinstance(configuration, Mapping):
            raise ValueError("Analysis module policy has no configuration object")
        return dict(configuration)
    if schema == "emrys.analysis-policy.v1":
        return {
            key: value
            for key, value in policy.items()
            if key not in {"schema_version", "analysis_id"}
        }
    if schema is None:
        return dict(policy)
    raise ValueError(f"Unsupported Analysis policy schema: {schema!r}")


class AnalysisInputV1(NamedTuple):
    producer: str
    artifact: str
    semantics: str
    adapters: tuple[str, ...]


class AnalysisArtifactV1(NamedTuple):
    artifact_name: str
    adapter: str
    source_path_template: str
    kind: str
    expected_header: tuple[str, ...] | None = None
    exact_data_rows: int | None = None
    allow_header_only: bool = True


class AnalysisReportArtifactV1(NamedTuple):
    adapter: str
    artifact_id: str
    path: Path
    sha256: str
    media_type: str


class AnalysisReportContextV1(NamedTuple):
    run_id: str
    analysis_id: str
    module_id: str
    output_dir: Path
    artifact_source_root: Path
    run_summary: JsonObject
    artifacts: tuple[AnalysisReportArtifactV1, ...]


class AnalysisScientificReportV1(NamedTuple):
    interpretation_boundary: str
    html_bytes: bytes


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
ScientificReporterV1: TypeAlias = Callable[
    [AnalysisReportContextV1], AnalysisScientificReportV1
]


class AnalysisTaskV1(NamedTuple):
    owner_key: str
    rule_name: str
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
    render_scientific_report: ScientificReporterV1
    implementation_package: str
    required_runtime_checks: tuple[str, ...]


def module_profile_record(descriptor: AnalysisModuleDescriptorV1) -> dict[str, object]:
    """Project the selected analysis tasks into the immutable Run profile."""

    owners = [task.owner_key for task in descriptor.tasks]
    return {
        "semantic_owner_keys": owners,
        "owner_tasks": [
            {
                "machine_key": task.owner_key,
                "rule_name": task.rule_name,
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
                "artifact": item.artifact,
                "semantics": item.semantics,
            }
            for task in descriptor.tasks
            for item in task.inputs
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

    errors = sorted(
        Draft202012Validator(descriptor.config_schema).iter_errors(configuration),
        key=lambda item: item.json_path,
    )
    if errors:
        raise ValueError(
            f"Invalid {descriptor.module_id} configuration: {errors[0].message}"
        )
    normalized = descriptor.normalize_config(dict(configuration), context)
    if not isinstance(normalized, Mapping):
        raise ValueError(
            "Analysis module normalizer must return a configuration object"
        )
    return dict(normalized)


def compose_profile(
    base: Mapping[str, Any],
    descriptor: AnalysisModuleDescriptorV1,
) -> dict[str, object]:
    """Compose one selected analysis tail onto the fixed processing profile."""

    fragment = module_profile_record(descriptor)
    collisions = {template["adapter"] for template in base["artifact_templates"]} & {
        artifact.adapter for task in descriptor.tasks for artifact in task.outputs
    }
    if collisions:
        raise AnalysisModuleLoadError(
            "Analysis module adapters collide with the processing profile: "
            + ", ".join(sorted(collisions))
        )
    return {
        "schema_version": base["schema_version"],
        "profile_id": base["profile_id"],
        "profile_version": base["profile_version"],
        "semantic_owner_keys": [
            *base["semantic_owner_keys"],
            *fragment["semantic_owner_keys"],
        ],
        "owner_tasks": [
            *(dict(owner) for owner in base["owner_tasks"]),
            *fragment["owner_tasks"],
        ],
        "direct_edges": [
            *(dict(edge) for edge in base["direct_edges"]),
            *fragment["direct_edges"],
        ],
        "required_owner_keys": [
            *base["required_owner_keys"],
            *fragment["required_owner_keys"],
        ],
        "evidence_owner_keys": list(base["evidence_owner_keys"]),
        "artifact_templates": [
            *(dict(item) for item in base["artifact_templates"]),
            *fragment["artifact_templates"],
        ],
    }


@dataclass(frozen=True, slots=True)
class LoadedAnalysisModuleV1:
    descriptor: AnalysisModuleDescriptorV1
    trust: Literal["built-in", "external"]
    distribution_name: str
    distribution_version: str
    entry_point_value: str
    implementation_root: Path
    implementation_sha256: str


_BUILTIN_PROVIDER = "emrys.analyses.paired_cmh_candidate_ranking:analysis_module_v1"


def module_identity_record(module: LoadedAnalysisModuleV1) -> dict[str, object]:
    """Project the installed provider facts persisted with a modular Run."""

    descriptor = module.descriptor
    return {
        "module_id": descriptor.module_id,
        "interface_version": ANALYSIS_MODULE_INTERFACE_V1,
        "module_version": descriptor.module_version,
        "trust": module.trust,
        "distribution_name": module.distribution_name,
        "distribution_version": module.distribution_version,
        "entry_point": module.entry_point_value,
        "config_schema_sha256": orchestration_contracts.canonical_sha256(
            descriptor.config_schema
        ),
        "required_runtime_checks": list(descriptor.required_runtime_checks),
    }


def _validate_v1_shape(descriptor: AnalysisModuleDescriptorV1) -> None:
    tasks = descriptor.tasks
    owner_keys = tuple(task.owner_key for task in tasks)
    owner_steps = tuple(task.step_id for task in tasks)
    outputs = tuple((task, output) for task in tasks for output in task.outputs)
    adapters = tuple(output.adapter for _, output in outputs)
    runtime_checks = descriptor.required_runtime_checks
    outputs_by_owner = {
        task.owner_key: {output.adapter for output in task.outputs} for task in tasks
    }
    if (
        not 1 <= len(tasks) <= 2
        or len(set(owner_keys)) != len(tasks)
        or len(set(owner_steps)) != len(tasks)
        or not set(owner_steps) <= {"09", "10"}
        or any(
            task.stage_memory_mb != "workflow"
            and (
                isinstance(task.stage_memory_mb, bool)
                or not isinstance(task.stage_memory_mb, int)
                or task.stage_memory_mb < 1
            )
            for task in tasks
        )
        or any(not callable(task.plan) for task in tasks)
        or len(adapters) != len(set(adapters))
        or len({item.artifact_name for _, item in outputs}) != len(outputs)
        or any(
            not re.fullmatch(r"[a-z][a-z0-9_]*", output.artifact_name)
            for _, output in outputs
        )
        or any(output.kind not in ANALYSIS_MEDIA_TYPE_BY_KIND for _, output in outputs)
        or any(
            output.kind == "validation_report"
            and output.expected_header not in (None, VALIDATION_REPORT_HEADER)
            for _, output in outputs
        )
        or any(
            "{analysis_id}" not in output.source_path_template
            or any(
                token in output.source_path_template.replace("{analysis_id}", "")
                for token in "{}"
            )
            or not output.source_path_template.startswith(
                ("results/", "products/native/")
            )
            or "\\" in output.source_path_template
            or any(
                part in {"", ".", ".."}
                for part in output.source_path_template.split("/")
            )
            or PurePosixPath(output.source_path_template).is_absolute()
            for _, output in outputs
        )
        or any(
            not item.adapters
            or len(item.adapters) != len(set(item.adapters))
            or any(
                not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", adapter)
                for adapter in item.adapters
            )
            for task in tasks
            for item in task.inputs
        )
        or any(
            adapter not in outputs_by_owner[item.producer]
            for task in tasks
            for item in task.inputs
            if item.producer in outputs_by_owner
            for adapter in item.adapters
        )
        or any(
            sum(output.kind == "validation_report" for output in task.outputs) != 1
            for task in tasks
        )
        or not runtime_checks
        or len(runtime_checks) != len(set(runtime_checks))
        or any(not re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in runtime_checks)
    ):
        raise AnalysisModuleLoadError(
            "Analysis module v1 must fill the exact Step 09/10 analysis slots"
        )


def load_analysis_module(
    module_id: str, *, source_root: Path | None = None
) -> LoadedAnalysisModuleV1:
    """Load only the one exact installed module selected by ``module_id``."""

    if not isinstance(module_id, str) or not module_id:
        raise AnalysisModuleLoadError("Analysis module ID must be nonempty")
    matches = tuple(
        entry_point
        for entry_point in importlib.metadata.entry_points(
            group=ANALYSIS_MODULE_ENTRY_POINT_GROUP
        )
        if entry_point.name == module_id
    )
    if len(matches) != 1:
        detail = "not installed" if not matches else "selection is ambiguous"
        raise AnalysisModuleLoadError(f"Analysis module {detail}: {module_id!r}")

    entry_point = matches[0]
    try:
        provider = entry_point.load()
        if not callable(provider):
            raise TypeError("entry point does not expose a callable provider")
        descriptor = provider()
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
    distribution = getattr(entry_point, "dist", None)
    distribution_name = getattr(distribution, "name", None)
    if distribution is not None and distribution_name is None:
        distribution_name = distribution.metadata.get("Name")
    distribution_version = getattr(distribution, "version", None)
    if distribution_name is None or distribution_version is None:
        raise AnalysisModuleLoadError(
            "Analysis module entry point has no distribution provenance"
        )
    distribution_name = str(distribution_name)
    distribution_version = str(distribution_version)
    normalized_name = re.sub(r"[-_.]+", "-", distribution_name).lower()
    trust: Literal["built-in", "external"] = (
        "built-in"
        if (
            module_id == BUILTIN_PAIRED_CMH_MODULE_ID
            and normalized_name == "emrys-rna-workflow"
            and entry_point.value == _BUILTIN_PROVIDER
        )
        else "external"
    )
    if not callable(descriptor.render_scientific_report):
        raise AnalysisModuleLoadError(
            "Analysis modules must provide one scientific report renderer"
        )
    implementation_package = descriptor.implementation_package
    provider_module = entry_point.value.partition(":")[0]
    if not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*",
        implementation_package,
    ) or not (
        provider_module == implementation_package
        or provider_module.startswith(f"{implementation_package}.")
    ):
        raise AnalysisModuleLoadError(
            "Analysis module implementation package must contain its provider"
        )
    try:
        implementation_root = (
            Path(os.path.abspath(source_root / "src"))
            / Path(*implementation_package.split("."))
            if trust == "built-in" and source_root is not None
            else Path(
                os.path.abspath(
                    os.fspath(importlib.resources.files(implementation_package))
                )
            )
        )
        implementation = installed_python_package_identity(implementation_root)
    except (InstalledPackageIdentityError, OSError, TypeError) as exc:
        raise AnalysisModuleLoadError(
            "Analysis module implementation package is unavailable"
        ) from exc
    return LoadedAnalysisModuleV1(
        descriptor=descriptor,
        trust=trust,
        distribution_name=distribution_name,
        distribution_version=distribution_version,
        entry_point_value=entry_point.value,
        implementation_root=implementation.root,
        implementation_sha256=implementation.sha256,
    )


def module_admission_record(module: LoadedAnalysisModuleV1) -> dict[str, object]:
    """Return the exact module facts that must survive operation boundaries."""

    return {
        "module": module_identity_record(module),
        "profile": module_profile_record(module.descriptor),
        "implementation_sha256": module.implementation_sha256,
    }


def readmit_analysis_module(
    admitted: LoadedAnalysisModuleV1,
    policy: JsonObject,
    *,
    source_root: Path | None = None,
) -> LoadedAnalysisModuleV1:
    """Reload one module and compare it with admission and persisted policy."""

    loaded = load_analysis_module(
        admitted.descriptor.module_id, source_root=source_root
    )
    if module_admission_record(loaded) != module_admission_record(admitted):
        raise AnalysisModuleLoadError(
            "Installed analysis module differs from Project admission"
        )
    if policy.get("schema_version") == "emrys.analysis-module-policy.v1" and (
        policy.get("module") != module_identity_record(loaded)
    ):
        raise AnalysisModuleLoadError(
            "Installed analysis module differs from persisted Run policy"
        )
    return loaded
