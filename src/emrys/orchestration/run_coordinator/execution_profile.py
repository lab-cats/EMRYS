"""Admit one execution profile without observing an execution attempt."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    resolve_computational_resources,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes
from emrys.orchestration.run_coordinator.resource_policy import (
    ResourceConfigError,
    ResourceOverrides,
    ResourcePolicy,
    admit_resource_policy,
    is_canonical_slurm_job_id,
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


def add_site_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--site",
        choices=("viking",),
        help="Use Viking's built-in Slurm placement for this Project.",
    )


def project_default_profile_bytes(site: str | None = None) -> bytes:
    """Select initial placement without changing scientific resource defaults."""

    if site is None:
        return PROJECT_DEFAULT_PROFILE_BYTES
    if site != "viking":
        raise ExecutionProfileError(f"Unsupported Project site: {site!r}")
    return f"""schema_version: {SCHEMA_VERSION}
placement:
  kind: slurm
  account: viking-users
  partition: long
  qos: normal
  cpus_per_task: 4
  memory_mb: null
  time: "08:00:00"
  exclusive: false
  nodelist: null
  scratch_parent: /tmp
  modules:
    mode: none
    init: ""
    load: []
""".encode()


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

    def validate_reservation(self) -> None:
        """Reject known reservation conflicts without changing symbolic policy."""
        if isinstance(self.placement, SlurmPlacement):
            try:
                resolve_computational_resources(
                    self.resource_policy.declaration.identity_document(),
                    self.placement.cpus_per_task,
                    self.placement.memory_mb,
                    limit_source="Slurm reservation",
                )
            except orchestration_contracts.ContractValidationError as exc:
                raise ExecutionProfileError(str(exc)) from exc

    def submission_summary(self) -> tuple[str, ...]:
        """Describe admitted requests and limits without observing an allocation."""

        placement, resources = self.placement, self.resource_policy.declaration
        lines = [f"Execution placement: {placement.kind.capitalize()}"]
        if isinstance(placement, SlurmPlacement):
            lines.extend(
                (
                    f"Node request: 1; requested host(s): {placement.nodelist or 'scheduler-selected; exact host unknown'}",
                    "Exclusive allocation: "
                    + (
                        "requested"
                        if placement.exclusive
                        else "not requested; site policy applies"
                    ),
                    f"Allocation request: {placement.cpus_per_task} CPUs, {placement.time}; memory: "
                    + (
                        "site default (unknown)"
                        if placement.memory_mb is None
                        else f"{placement.memory_mb} MiB"
                    ),
                    f"Account: {placement.account or 'site default'}; "
                    f"partition: {placement.partition or 'site default'}; "
                    f"QoS: {placement.qos or 'site default'}",
                    f"Scratch parent: {str(placement.scratch_parent)!r}; modules: {placement.module_mode}; "
                    f"initialization: {str(placement.module_init) if placement.module_init else 'none'!r}; "
                    f"load in order: {', '.join(placement.modules) or 'none'}",
                )
            )
        lines.extend(
            (
                f"Workflow CPU ceiling: {resources.workflow_cores}; memory ceiling: "
                + (
                    "allocation capacity (unknown until execution)"
                    if resources.workflow_memory_mb == "allocation"
                    else f"{resources.workflow_memory_mb} MiB"
                ),
                "Stage thread caps: "
                + ", ".join(f"{step}={count}" for step, count in resources.step_threads)
                + "; other stages=1",
                "Repeated-stage concurrency caps: "
                + ", ".join(
                    f"{step}={count}" for step, count in resources.stage_concurrency
                ),
                "Stage memory: workflow ceiling; explicit MiB caps: "
                + (
                    ", ".join(
                        f"{step}={memory}"
                        for step, memory in resources.stage_memory_mb
                        if memory != "workflow"
                    )
                    or "none"
                ),
                "Actual allocation capacity is unknown until execution; reservations and limits do not guarantee utilization.",
            )
        )
        return tuple(lines)

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

        return hashlib.sha256(
            f"{self.sha256}\0{self.source_raw_sha256}".encode()
        ).hexdigest()

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


def _parse_profile(data: bytes, path: Path, label: str) -> dict[str, Any]:
    try:
        value = orchestration_contracts.load_yaml_object_bytes(data, label)
    except orchestration_contracts.ContractValidationError as exc:
        raise ExecutionProfileError(f"Could not parse {label} {path}: {exc}") from exc
    _validate_profile(value)
    return value


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


def admit_execution_profile_bytes(
    default_data: bytes,
    source_path: Path | None = None,
    source_data: bytes | None = None,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
) -> ExecutionProfile:
    """Admit supplied default and selected bytes without reading files or capacity."""

    if (source_path is None) != (source_data is None):
        raise ExecutionProfileError(
            "Selected profile path and bytes must be supplied together"
        )
    default = _parse_profile(
        default_data, DEFAULT_PROFILE_PATH, "built-in execution profile"
    )
    default_resource_sha256 = orchestration_contracts.canonical_sha256(
        default["resources"]
    )
    document = default
    selected_fragment: dict[str, Any] = {}
    if source_data is not None and source_path is not None:
        selected_fragment = _parse_profile(
            source_data, source_path, "execution profile"
        )
        _merge_profile(document, selected_fragment)
    else:
        source_path, source_data = DEFAULT_PROFILE_PATH, default_data

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
            overrides=resource_overrides,
        )
    except ResourceConfigError as exc:
        raise ExecutionProfileError(str(exc)) from exc

    return ExecutionProfile(
        resource_policy=policy,
        placement=_admit_placement(document["placement"]),
        source_path=source_path,
        source_raw_sha256=source_sha256,
        computational_resources_explicit=bool(explicit_resource_fields),
    )


def load_execution_profile(
    config_path: Path | None = None,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
    expected_binding_sha256: str | None = None,
) -> ExecutionProfile:
    """Load packaged defaults, one selected profile fragment, and resource overrides."""

    if (
        expected_binding_sha256 is not None
        and _SHA256.fullmatch(expected_binding_sha256) is None
    ):
        raise ExecutionProfileError("expected_binding_sha256 must be 64 lowercase hex")
    _, default_data = _read_admitted_regular_file(
        DEFAULT_PROFILE_PATH, "built-in execution profile"
    )
    source_path, source_data = (
        (None, None)
        if config_path is None
        else _read_admitted_regular_file(Path(config_path), "execution profile")
    )
    profile = admit_execution_profile_bytes(
        default_data, source_path, source_data, resource_overrides
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
    "add_site_argument",
    "admit_execution_profile_bytes",
    "load_execution_profile",
    "project_default_profile_bytes",
    "project_execution_profile_path",
)
