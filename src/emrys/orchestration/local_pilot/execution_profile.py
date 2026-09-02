"""Admit one execution profile without observing an execution attempt."""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes
from emrys.orchestration.local_pilot.resource_policy import (
    ResourceConfigError,
    ResourceOverrides,
    ResourcePolicy,
    admit_resource_policy,
    is_canonical_slurm_job_id,
    resume_resource_policy,
)

SCHEMA_VERSION = "emrys.execution-profile.v1"
DEFAULT_PROFILE_PATH = Path(__file__).parent / "resources/default_execution.yaml"
PROJECT_PROFILE_DIRECTORY = Path("runtime/profiles")
PROJECT_DEFAULT_PROFILE_BYTES = (
    f"schema_version: {SCHEMA_VERSION}\nplacement:\n  kind: direct\n".encode()
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PROFILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_RETIRED_ADJACENT_FILES = (
    "emrys.resources.yaml",
    "emrys.launcher.yaml",
    "norad.resources.yaml",
    "norad.launcher.yaml",
)


class ExecutionProfileError(ValueError):
    """One execution-profile source or resolved value is inadmissible."""


def project_execution_profile_path(
    project_path: Path,
    selection: str | Path | None,
) -> Path:
    """Resolve one default, named, or absolute execution-profile source."""

    project_root = Path(os.path.abspath(project_path)).parent
    if selection is None:
        retired = tuple(
            name
            for name in _RETIRED_ADJACENT_FILES
            if os.path.lexists(project_root / name)
        )
        if retired:
            raise ExecutionProfileError(
                "Retired adjacent configuration requires migration: "
                + ", ".join(retired)
            )
        return project_root / PROJECT_PROFILE_DIRECTORY / "default.yaml"
    value = str(selection)
    path = Path(value)
    if path.is_absolute():
        return path
    if _PROFILE_NAME.fullmatch(value) is None or value.endswith(".yaml"):
        raise ExecutionProfileError(
            "--profile must be a safe Project profile name without '.yaml' "
            "or an absolute path"
        )
    return project_root / PROJECT_PROFILE_DIRECTORY / f"{value}.yaml"


@dataclass(frozen=True, slots=True)
class DirectPlacement:
    """Execute the admitted Run directly in the current allocation."""

    kind: Literal["direct"] = field(default="direct", init=False)

    def document(self) -> dict[str, str]:
        """Return the closed placement document."""

        return {"kind": self.kind}


@dataclass(frozen=True, slots=True)
class SlurmPlacement:
    """Attempt-local request for one outer Slurm allocation."""

    account: str | None
    partition: str | None
    qos: str | None
    cpus_per_task: int
    memory_mb: int | None
    time: str
    exclusive: bool
    nodelist: str | None
    scratch_parent: Path
    module_mode: Literal["none", "exact"]
    module_init: Path | None
    modules: tuple[str, ...]
    kind: Literal["slurm"] = field(default="slurm", init=False)

    def document(self) -> dict[str, Any]:
        """Return the closed Attempt-local placement document."""

        return {
            "kind": self.kind,
            "account": self.account,
            "partition": self.partition,
            "qos": self.qos,
            "cpus_per_task": self.cpus_per_task,
            "memory_mb": self.memory_mb,
            "time": self.time,
            "exclusive": self.exclusive,
            "nodelist": self.nodelist,
            "scratch_parent": str(self.scratch_parent),
            "modules": {
                "mode": self.module_mode,
                "init": "" if self.module_init is None else str(self.module_init),
                "load": list(self.modules),
            },
        }


Placement = DirectPlacement | SlurmPlacement


@dataclass(frozen=True, slots=True)
class ExecutionProfile:
    """One admitted resource-policy projection plus Attempt placement."""

    resource_policy: ResourcePolicy
    placement: Placement
    source_path: Path
    source_raw_sha256: str
    computational_resources_explicit: bool
    selected_reporting_memory: tuple[tuple[str, int | Literal["workflow"]], ...]

    def document(self) -> dict[str, Any]:
        """Return the complete effective profile without source locators."""

        return {
            "schema_version": SCHEMA_VERSION,
            "resources": self.resource_policy.document(),
            "placement": self.placement.document(),
        }

    @property
    def sha256(self) -> str:
        """Digest the canonical effective profile."""

        return orchestration_contracts.canonical_sha256(self.document())

    @property
    def binding_sha256(self) -> str:
        """Bind effective semantics to the exact selected source bytes."""

        return hashlib.sha256(f"{self.sha256}\0{self.source_raw_sha256}".encode()).hexdigest()

    def attempt_placement(self, slurm_job_id: str | None = None) -> dict[str, Any]:
        """Project closed Attempt-local placement provenance."""

        if isinstance(self.placement, DirectPlacement) and slurm_job_id is not None:
            raise ExecutionProfileError("Direct placement cannot record a Slurm job ID")
        if isinstance(self.placement, SlurmPlacement) and slurm_job_id is None:
            raise ExecutionProfileError("Slurm placement requires one job ID")
        if slurm_job_id is not None and not is_canonical_slurm_job_id(slurm_job_id):
            raise ExecutionProfileError(
                "Slurm job ID must be one canonical positive decimal string or null"
            )
        return {
            "kind": self.placement.kind,
            "source": {
                "path": str(self.source_path),
                "sha256": self.source_raw_sha256,
            },
            "effective_sha256": self.sha256,
            "request": self.placement.document(),
            "scheduler_job_id": slurm_job_id,
        }


def _read_admitted_regular_file(path: Path, label: str) -> tuple[Path, bytes]:
    authored = Path(os.path.abspath(path))
    try:
        resolved = authored.resolve(strict=True)
        if resolved != authored:
            raise ExecutionProfileError(f"{label} must be canonical and nonsymlink")
        return resolved, read_bytes(authored, label)
    except (OSError, ValidationError) as exc:
        raise ExecutionProfileError(
            f"Could not read {label}: {authored}: {exc}"
        ) from exc


def _validate_profile(document: Mapping[str, Any]) -> None:
    try:
        orchestration_contracts.validate_record("execution-profile", dict(document))
    except orchestration_contracts.ContractValidationError as exc:
        raise ExecutionProfileError(f"Invalid execution profile: {exc}") from exc


def _read_profile(path: Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    resolved, data = _read_admitted_regular_file(path, label)
    try:
        value = orchestration_contracts.load_yaml_object_bytes(data, label)
    except orchestration_contracts.ContractValidationError as exc:
        raise ExecutionProfileError(
            f"Could not parse {label} {resolved}: {exc}"
        ) from exc
    _validate_profile(value)
    return resolved, data, value


def _merge_profile(target: dict[str, Any], fragment: Mapping[str, Any]) -> None:
    resources = fragment.get("resources")
    if isinstance(resources, Mapping):
        for key, value in resources.items():
            if key == "schema_version":
                continue
            if isinstance(value, Mapping):
                target["resources"][key].update(dict(value))
            else:
                target["resources"][key] = value
    if "placement" in fragment:
        target["placement"] = fragment["placement"]


def _absolute_nonroot_path(value: str) -> Path:
    return Path(os.path.abspath(value))


def _admit_placement(document: Any) -> Placement:
    if document.get("kind") == "direct":
        return DirectPlacement()

    modules = document["modules"]
    module_init_value = modules["init"]
    return SlurmPlacement(
        account=document["account"],
        partition=document["partition"],
        qos=document["qos"],
        cpus_per_task=document["cpus_per_task"],
        memory_mb=document["memory_mb"],
        time=document["time"],
        exclusive=document["exclusive"],
        nodelist=document["nodelist"],
        scratch_parent=_absolute_nonroot_path(document["scratch_parent"]),
        module_mode=modules["mode"],
        module_init=(
            None if not module_init_value else _absolute_nonroot_path(module_init_value)
        ),
        modules=tuple(modules["load"]),
    )


def load_execution_profile(
    config_path: Path | None = None,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
    expected_binding_sha256: str | None = None,
) -> ExecutionProfile:
    """Load packaged defaults, one selected profile fragment, and resource overrides."""

    if expected_binding_sha256 is not None and _SHA256.fullmatch(
        expected_binding_sha256
    ) is None:
        raise ExecutionProfileError("expected_binding_sha256 must be 64 lowercase hex")
    source_path, source_data, default = _read_profile(
        DEFAULT_PROFILE_PATH,
        "built-in execution profile",
    )
    default_resource_sha256 = orchestration_contracts.canonical_sha256(
        default["resources"]
    )
    document = default
    selected_fragment: dict[str, Any] = {}
    if config_path is not None:
        source_path, source_data, selected_fragment = _read_profile(
            Path(config_path),
            "execution profile",
        )
        _merge_profile(document, selected_fragment)

    _validate_profile(document)
    source_sha256 = hashlib.sha256(source_data).hexdigest()
    resources = document["resources"]
    selected_resources = selected_fragment.get("resources", {})
    explicit_resource_fields = {
        key
        for key, value in selected_resources.items()
        if key != "schema_version" and value
    }
    resource_fragment_explicit = bool(explicit_resource_fields)
    resource_config_path = source_path if resource_fragment_explicit else None
    resource_config_sha256 = source_sha256 if resource_fragment_explicit else None
    try:
        policy = admit_resource_policy(
            resources,
            default_sha256=default_resource_sha256,
            config_path=resource_config_path,
            config_sha256=resource_config_sha256,
        )
        policy = resume_resource_policy(policy, overrides=resource_overrides)
    except ResourceConfigError as exc:
        raise ExecutionProfileError(str(exc)) from exc

    profile = ExecutionProfile(
        resource_policy=policy,
        placement=_admit_placement(document["placement"]),
        source_path=source_path,
        source_raw_sha256=source_sha256,
        computational_resources_explicit=bool(
            explicit_resource_fields - {"reporting_memory_mb"}
        ),
        selected_reporting_memory=tuple(
            selected_resources.get("reporting_memory_mb", {}).items()
        ),
    )
    if (
        expected_binding_sha256 is not None
        and profile.binding_sha256 != expected_binding_sha256
    ):
        raise ExecutionProfileError("Execution-profile binding SHA-256 differs")
    return profile


__all__ = (
    "DEFAULT_PROFILE_PATH",
    "DirectPlacement",
    "ExecutionProfile",
    "ExecutionProfileError",
    "PROJECT_DEFAULT_PROFILE_BYTES",
    "PROJECT_PROFILE_DIRECTORY",
    "Placement",
    "SCHEMA_VERSION",
    "SlurmPlacement",
    "load_execution_profile",
    "project_execution_profile_path",
)
