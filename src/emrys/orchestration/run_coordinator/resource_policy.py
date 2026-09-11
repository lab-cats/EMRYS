"""Closed layered resource policy for one run-coordinator workflow attempt."""

from __future__ import annotations

import argparse
import copy
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    resolve_computational_resources,
)

SCHEMA_VERSION = "emrys.local-pilot-resources.v1"
STAGE_IDS = (
    "00a",
    "00b",
    "00c",
    "01",
    "02",
    "02b",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
)
REPEATABLE_STAGE_IDS = ("01", "02", "02b", "03", "04", "05", "06", "07")
THREAD_CAPABLE_STAGE_IDS = ("00a", "01", "02", "06", "08", "09", "10")
_SCALAR_RESOURCE_CONTROLS = ("workflow_cores", "workflow_memory_mb")
_KEYED_RESOURCE_CONTROLS = (
    ("stage_concurrency", REPEATABLE_STAGE_IDS, "STEP=COUNT"),
    ("step_threads", THREAD_CAPABLE_STAGE_IDS, "STEP=THREADS"),
    ("stage_memory_mb", STAGE_IDS, "STEP=MIB"),
)


class ResourceConfigError(ValueError):
    """One resource source or its resolved policy is not admissible."""


def is_canonical_slurm_job_id(value: object) -> bool:
    """Return whether a value is one canonical positive Slurm job ID."""

    return (
        isinstance(value, str)
        and value.isascii()
        and value.isdecimal()
        and not value.startswith("0")
    )


@dataclass(frozen=True, slots=True)
class AllocationCapacity:
    """Observed CPU and memory capacity available to the local executor."""

    cores: int
    memory_mb: int
    source: str
    slurm_job_id: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.cores, bool)
            or not isinstance(self.cores, int)
            or self.cores < 1
        ):
            raise ResourceConfigError("Allocation cores must be a positive integer")
        if (
            isinstance(self.memory_mb, bool)
            or not isinstance(self.memory_mb, int)
            or self.memory_mb < 1
        ):
            raise ResourceConfigError("Allocation memory must be a positive integer")
        if not isinstance(self.source, str) or not self.source:
            raise ResourceConfigError("Allocation source must be nonempty")
        if self.slurm_job_id is not None and not is_canonical_slurm_job_id(
            self.slurm_job_id
        ):
            raise ResourceConfigError(
                "Slurm job ID must be a positive decimal string or null"
            )


@dataclass(frozen=True, slots=True)
class ResourceOverrides:
    """Explicit highest-precedence command-line resource values."""

    workflow_cores: int | None = None
    workflow_memory_mb: int | None = None
    stage_concurrency: tuple[tuple[str, int], ...] = ()
    step_threads: tuple[tuple[str, int], ...] = ()
    stage_memory_mb: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        for field, allowed, _metavar in _KEYED_RESOURCE_CONTROLS:
            values = getattr(self, field)
            keys = [key for key, _ in values]
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            if duplicates:
                raise ResourceConfigError(
                    f"Duplicate command-line {field} override: " + ", ".join(duplicates)
                )
            unknown = sorted(set(keys).difference(allowed))
            if unknown:
                raise ResourceConfigError(
                    f"Unknown command-line {field} key: " + ", ".join(unknown)
                )
            for key, value in values:
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    raise ResourceConfigError(
                        f"Command-line {field}.{key} must be a positive integer"
                    )
        for field in _SCALAR_RESOURCE_CONTROLS:
            value = getattr(self, field)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 1
            ):
                raise ResourceConfigError(
                    f"Command-line {field} must be a positive integer"
                )

    def labels(self) -> tuple[str, ...]:
        """Return deterministic paths changed by this override set."""

        labels: list[str] = []
        for field in _SCALAR_RESOURCE_CONTROLS:
            if getattr(self, field) is not None:
                labels.append(field)
        for field, _allowed, _metavar in _KEYED_RESOURCE_CONTROLS:
            labels.extend(f"{field}.{key}" for key, _ in getattr(self, field))
        return tuple(labels)


@dataclass(frozen=True, slots=True)
class ComputationalResourceDeclaration:
    """Canonical pre-allocation computational policy for one immutable Run."""

    workflow_cores: int
    workflow_memory_mb: int | Literal["allocation"]
    stage_concurrency: tuple[tuple[str, int], ...]
    step_threads: tuple[tuple[str, int], ...]
    stage_memory_mb: tuple[tuple[str, int | Literal["workflow"]], ...]

    def identity_document(self) -> dict[str, Any]:
        """Return the Run-bound declaration without allocation or reporting policy."""

        return {
            "workflow_cores": self.workflow_cores,
            "workflow_memory_mb": self.workflow_memory_mb,
            "stage_concurrency": dict(self.stage_concurrency),
            "step_threads": dict(self.step_threads),
            "stage_memory_mb": dict(self.stage_memory_mb),
        }


@dataclass(frozen=True, slots=True)
class ResourcePolicy:
    """One admitted symbolic computational policy plus source context."""

    declaration: ComputationalResourceDeclaration
    default_sha256: str
    config_path: Path | None
    config_sha256: str | None
    override_labels: tuple[str, ...]

    def document(self) -> dict[str, Any]:
        """Return the complete symbolic policy for persistence and re-admission."""

        return {
            "schema_version": SCHEMA_VERSION,
            **self.declaration.identity_document(),
        }


@dataclass(frozen=True, slots=True)
class AttemptResourceResolution:
    """Allocation observation and numeric computational resolution for one Attempt."""

    allocation: AllocationCapacity
    workflow_memory_mb: int
    stage_memory_mb: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ResourcePlan:
    """Compatibility view over one declaration and its Attempt resolution."""

    policy: ResourcePolicy
    resolution: AttemptResourceResolution

    @property
    def declaration(self) -> ComputationalResourceDeclaration:
        return self.policy.declaration

    @property
    def workflow_cores(self) -> int:
        return self.declaration.workflow_cores

    @property
    def workflow_memory_mb(self) -> int:
        return self.resolution.workflow_memory_mb

    @property
    def stage_concurrency(self) -> tuple[tuple[str, int], ...]:
        return self.declaration.stage_concurrency

    @property
    def step_threads(self) -> tuple[tuple[str, int], ...]:
        return self.declaration.step_threads

    @property
    def stage_memory_mb(self) -> tuple[tuple[str, int], ...]:
        return self.resolution.stage_memory_mb

    @property
    def allocation(self) -> AllocationCapacity:
        return self.resolution.allocation

    def threads_for(self, step_id: str) -> int:
        """Return explicit threads or the fixed one-thread rule default."""

        return dict(self.step_threads).get(step_id, 1)

    def effective_document(self) -> dict[str, Any]:
        """Return the canonical JSON-ready effective policy."""

        return {
            "schema_version": SCHEMA_VERSION,
            "workflow_cores": self.workflow_cores,
            "workflow_memory_mb": self.workflow_memory_mb,
            "stage_concurrency": dict(self.stage_concurrency),
            "step_threads": dict(self.step_threads),
            "stage_memory_mb": dict(self.stage_memory_mb),
        }

    def policy_record(self) -> dict[str, Any]:
        """Return the immutable effective policy and its admitted provenance."""

        symbolic = self.policy.document()
        effective = self.effective_document()
        return {
            "symbolic": symbolic,
            "symbolic_sha256": orchestration_contracts.canonical_sha256(symbolic),
            "effective": effective,
            "effective_sha256": orchestration_contracts.canonical_sha256(effective),
            "allocation": {
                "cores": self.allocation.cores,
                "memory_mb": self.allocation.memory_mb,
                "source": self.allocation.source,
                "slurm_job_id": self.allocation.slurm_job_id,
            },
            "sources": {
                "default_sha256": self.policy.default_sha256,
                "config_path": (
                    None
                    if self.policy.config_path is None
                    else str(self.policy.config_path)
                ),
                "config_sha256": self.policy.config_sha256,
                "cli_overrides": list(self.policy.override_labels),
            },
        }

    def scheduler_limits(self) -> tuple[tuple[str, int], ...]:
        """Return deterministic Snakemake global resource limits."""

        limits = {"mem_mb": self.workflow_memory_mb}
        limits.update(
            {
                stage_slot_name(step_id): concurrency
                for step_id, concurrency in self.stage_concurrency
            }
        )
        return tuple(sorted(limits.items()))


def stage_slot_name(step_id: str) -> str:
    """Return the fixed Snakemake global resource name for one stage."""

    if step_id not in REPEATABLE_STAGE_IDS:
        raise ResourceConfigError(f"Stage is not repeatable: {step_id}")
    return f"stage_{step_id}_slots"


def _apply_overrides(target: dict[str, Any], overrides: ResourceOverrides) -> None:
    for field in _SCALAR_RESOURCE_CONTROLS:
        value = getattr(overrides, field)
        if value is not None:
            target[field] = value
    for field, _allowed, _metavar in _KEYED_RESOURCE_CONTROLS:
        selected = target[field]
        assert isinstance(selected, dict)
        selected.update(dict(getattr(overrides, field)))


def _closed_map(
    document: Mapping[str, Any],
    field: str,
    required: tuple[str, ...],
) -> dict[str, Any]:
    value = document.get(field)
    if not isinstance(value, dict) or set(value) != set(required):
        raise ResourceConfigError(
            f"Resolved {field} keys must be exactly: {', '.join(required)}"
        )
    return value


def admit_resource_policy(
    document: Mapping[str, Any],
    *,
    default_sha256: str,
    config_path: Path | None = None,
    config_sha256: str | None = None,
    override_labels: tuple[str, ...] = (),
) -> ResourcePolicy:
    """Admit one complete symbolic policy without observing an allocation."""

    value = copy.deepcopy(dict(document))
    try:
        orchestration_contracts.validate_record("resource-config", value)
    except orchestration_contracts.ContractValidationError as exc:
        raise ResourceConfigError(str(exc)) from exc
    stage_concurrency = _closed_map(value, "stage_concurrency", REPEATABLE_STAGE_IDS)
    step_threads = _closed_map(value, "step_threads", THREAD_CAPABLE_STAGE_IDS)
    stage_memory = _closed_map(value, "stage_memory_mb", STAGE_IDS)
    try:
        workflow_cores = int(value["workflow_cores"])
        configured_workflow_memory = value["workflow_memory_mb"]
    except KeyError as exc:
        raise ResourceConfigError(
            f"Resolved resource policy is missing {exc.args[0]}"
        ) from exc
    declared_workflow_memory: int | Literal["allocation"] = (
        "allocation"
        if configured_workflow_memory == "allocation"
        else int(configured_workflow_memory)
    )
    declared_stage_memory: dict[str, int | Literal["workflow"]] = {
        step_id: "workflow" if value == "workflow" else int(value)
        for step_id, value in stage_memory.items()
    }
    declaration = ComputationalResourceDeclaration(
        workflow_cores=workflow_cores,
        workflow_memory_mb=declared_workflow_memory,
        stage_concurrency=tuple(
            (key, int(stage_concurrency[key])) for key in REPEATABLE_STAGE_IDS
        ),
        step_threads=tuple(
            (key, int(step_threads[key])) for key in THREAD_CAPABLE_STAGE_IDS
        ),
        stage_memory_mb=tuple((key, declared_stage_memory[key]) for key in STAGE_IDS),
    )
    return ResourcePolicy(
        declaration=declaration,
        default_sha256=default_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        override_labels=override_labels,
    )


def resolve_resource_policy(
    policy: ResourcePolicy,
    allocation: AllocationCapacity,
) -> ResourcePlan:
    """Resolve one exact admitted policy against one Attempt allocation."""

    declaration = policy.declaration
    try:
        effective = resolve_computational_resources(
            declaration.identity_document(), allocation.cores, allocation.memory_mb
        )
    except orchestration_contracts.ContractValidationError as exc:
        raise ResourceConfigError(str(exc)) from exc
    resolution = AttemptResourceResolution(
        allocation=allocation,
        workflow_memory_mb=effective["workflow_memory_mb"],
        stage_memory_mb=tuple(
            (key, effective["stage_memory_mb"][key]) for key in STAGE_IDS
        ),
    )
    return ResourcePlan(
        policy=policy,
        resolution=resolution,
    )


def _admit_policy_sources(
    sources: Any,
    *,
    label: str,
) -> tuple[str, Path | None, str | None, tuple[str, ...]]:
    if not isinstance(sources, dict) or set(sources) != {
        "default_sha256",
        "config_path",
        "config_sha256",
        "cli_overrides",
    }:
        raise ResourceConfigError(f"{label} resource sources are malformed")
    default_sha256 = sources["default_sha256"]
    config_path_value = sources["config_path"]
    config_sha256 = sources["config_sha256"]
    override_values = sources["cli_overrides"]
    if not isinstance(default_sha256, str):
        raise ResourceConfigError(f"{label} resource default digest is malformed")
    if config_path_value is not None and not isinstance(config_path_value, str):
        raise ResourceConfigError(f"{label} resource config path is malformed")
    if config_sha256 is not None and not isinstance(config_sha256, str):
        raise ResourceConfigError(f"{label} resource config digest is malformed")
    if not isinstance(override_values, list) or not all(
        isinstance(value, str) for value in override_values
    ):
        raise ResourceConfigError(f"{label} resource overrides are malformed")
    return (
        default_sha256,
        None if config_path_value is None else Path(config_path_value),
        config_sha256,
        tuple(override_values),
    )


def resume_resource_policy(
    predecessor_policy: ResourcePolicy,
    *,
    overrides: ResourceOverrides = ResourceOverrides(),
) -> ResourcePolicy:
    """Re-admit a predecessor policy and explicit overrides without allocation."""

    document = predecessor_policy.document()
    default_sha256 = predecessor_policy.default_sha256
    config_path = predecessor_policy.config_path
    config_sha256 = predecessor_policy.config_sha256
    prior_labels = predecessor_policy.override_labels
    _apply_overrides(document, overrides)
    combined_labels = tuple(dict.fromkeys((*prior_labels, *overrides.labels())))
    return admit_resource_policy(
        document,
        default_sha256=default_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        override_labels=combined_labels,
    )


def admit_resource_policy_record(record: Mapping[str, Any]) -> ResourcePlan:
    """Re-admit one closed current symbolic policy and its allocation resolution."""

    expected = {
        "effective",
        "effective_sha256",
        "allocation",
        "sources",
        "symbolic",
        "symbolic_sha256",
    }
    if set(record) != expected:
        raise ResourceConfigError(
            "Persisted resource policy keys are malformed; expected "
            + ", ".join(sorted(expected))
        )

    allocation = record.get("allocation")
    if not isinstance(allocation, dict) or frozenset(allocation) not in {
        frozenset({"cores", "memory_mb", "source"}),
        frozenset({"cores", "memory_mb", "source", "slurm_job_id"}),
    }:
        raise ResourceConfigError("Persisted resource allocation is malformed")
    capacity = AllocationCapacity(
        cores=allocation["cores"],
        memory_mb=allocation["memory_mb"],
        source=allocation["source"],
        slurm_job_id=allocation.get("slurm_job_id"),
    )

    effective = record.get("effective")
    symbolic = record.get("symbolic")
    sources = record.get("sources")
    if (
        not isinstance(symbolic, dict)
        or not isinstance(effective, dict)
        or not isinstance(sources, dict)
    ):
        raise ResourceConfigError("Persisted resource policy is malformed")
    if orchestration_contracts.canonical_sha256(symbolic) != record.get(
        "symbolic_sha256"
    ):
        raise ResourceConfigError("Persisted symbolic resource digest differs")
    if orchestration_contracts.canonical_sha256(effective) != record.get(
        "effective_sha256"
    ):
        raise ResourceConfigError("Persisted effective resource digest differs")

    default_sha256, config_path, config_sha256, override_labels = _admit_policy_sources(
        sources, label="Persisted"
    )

    policy = admit_resource_policy(
        symbolic,
        default_sha256=default_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        override_labels=override_labels,
    )
    resolved = resolve_resource_policy(policy, capacity)
    projected = resolved.effective_document()
    if projected != effective:
        raise ResourceConfigError(
            "Persisted symbolic resource policy does not reproduce its resolution"
        )
    return resolved


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _assignment(value: str) -> tuple[str, int]:
    key, separator, raw = value.partition("=")
    if not separator or not key:
        raise argparse.ArgumentTypeError("must use KEY=POSITIVE_INTEGER")
    return key, _positive_integer(raw)


def add_resource_override_arguments(parser: argparse.ArgumentParser) -> None:
    """Add optional highest-precedence computational-resource controls."""

    for field in _SCALAR_RESOURCE_CONTROLS:
        parser.add_argument(
            "--" + field.replace("_", "-"),
            type=_positive_integer,
            help=f"Override {field} from YAML and packaged defaults.",
        )
    for field, _allowed, metavar in _KEYED_RESOURCE_CONTROLS:
        parser.add_argument(
            "--" + field.replace("_", "-"),
            action="append",
            default=[],
            metavar=metavar,
            type=_assignment,
            help=f"Repeatable {field.replace('_', ' ')} override.",
        )


def resource_override_argv(overrides: ResourceOverrides) -> tuple[str, ...]:
    """Render admitted overrides for one exact grouped-command delegate."""

    arguments: list[str] = []
    for field in _SCALAR_RESOURCE_CONTROLS:
        value = getattr(overrides, field)
        if value is not None:
            arguments.extend(("--" + field.replace("_", "-"), str(value)))
    for field, _allowed, _metavar in _KEYED_RESOURCE_CONTROLS:
        for key, value in getattr(overrides, field):
            arguments.extend(("--" + field.replace("_", "-"), f"{key}={value}"))
    return tuple(arguments)


def overrides_from_args(arguments: argparse.Namespace) -> ResourceOverrides:
    """Project only explicitly supplied command-line resource values."""

    return ResourceOverrides(
        workflow_cores=getattr(arguments, "workflow_cores", None),
        workflow_memory_mb=getattr(arguments, "workflow_memory_mb", None),
        **{
            field: tuple(getattr(arguments, field, ()))
            for field, _allowed, _metavar in _KEYED_RESOURCE_CONTROLS
        },
    )


__all__ = (
    "AllocationCapacity",
    "AttemptResourceResolution",
    "ComputationalResourceDeclaration",
    "REPEATABLE_STAGE_IDS",
    "ResourceConfigError",
    "ResourceOverrides",
    "ResourcePolicy",
    "ResourcePlan",
    "STAGE_IDS",
    "THREAD_CAPABLE_STAGE_IDS",
    "add_resource_override_arguments",
    "admit_resource_policy",
    "admit_resource_policy_record",
    "overrides_from_args",
    "resource_override_argv",
    "resolve_resource_policy",
    "resume_resource_policy",
    "stage_slot_name",
)
