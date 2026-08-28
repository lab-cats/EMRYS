"""Admit one execution profile without observing an execution attempt."""

from __future__ import annotations

import copy
import hashlib
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.local_pilot.resource_policy import (
    ResourceConfigError,
    ResourceOverrides,
    ResourcePolicy,
    admit_resource_policy,
    resume_resource_policy,
)

SCHEMA_VERSION = "emrys.execution-profile.v1"
DEFAULT_PROFILE_PATH = Path(__file__).parent / "resources/default_execution.yaml"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_POSITIVE_DECIMAL = re.compile(r"^[1-9][0-9]*$")


class ExecutionProfileError(ValueError):
    """One execution-profile source or resolved value is inadmissible."""


class _ClosedSafeLoader(yaml.SafeLoader):
    """Safe YAML loader rejecting merge and duplicate mapping keys."""

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                raise ExecutionProfileError("YAML merge keys are not allowed")
        super().flatten_mapping(node)

    def construct_mapping(
        self,
        node: yaml.MappingNode,
        deep: bool = False,
    ) -> dict[str, Any]:
        self.flatten_mapping(node)
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ExecutionProfileError("Every YAML mapping key must be a string")
            if key in result:
                raise ExecutionProfileError(f"Duplicate YAML mapping key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


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

    def attempt_placement(self, slurm_job_id: str | None = None) -> dict[str, Any]:
        """Project closed Attempt-local placement provenance."""

        if isinstance(self.placement, DirectPlacement) and slurm_job_id is not None:
            raise ExecutionProfileError("Direct placement cannot record a Slurm job ID")
        if isinstance(self.placement, SlurmPlacement) and slurm_job_id is None:
            raise ExecutionProfileError("Slurm placement requires one job ID")
        if slurm_job_id is not None and (
            not isinstance(slurm_job_id, str)
            or _POSITIVE_DECIMAL.fullmatch(slurm_job_id) is None
        ):
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


def _stable_file_state(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_uid,
        value.st_gid,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_admitted_regular_file(path: Path, label: str) -> tuple[Path, bytes]:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ExecutionProfileError(
            f"{label} cannot be admitted without symbolic-link protection"
        )
    authored = Path(os.path.abspath(path))
    try:
        resolved = authored.resolve(strict=True)
    except OSError as exc:
        raise ExecutionProfileError(f"Could not read {label}: {authored}") from exc
    if resolved != authored:
        raise ExecutionProfileError(f"{label} must be canonical and nonsymlink")

    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    chunks: list[bytes] = []
    try:
        descriptor = os.open(authored, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ExecutionProfileError(f"{label} must be one real regular file")
        bound_before = os.stat(authored, follow_symlinks=False)
        if (bound_before.st_dev, bound_before.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise ExecutionProfileError(f"{label} changed during admission")
        while block := os.read(descriptor, 1024 * 1024):
            chunks.append(block)
        after = os.fstat(descriptor)
        bound_after = os.stat(authored, follow_symlinks=False)
    except OSError as exc:
        raise ExecutionProfileError(f"Could not read {label}: {authored}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)

    data = b"".join(chunks)
    if (
        _stable_file_state(before) != _stable_file_state(after)
        or len(data) != before.st_size
        or (bound_after.st_dev, bound_after.st_ino) != (after.st_dev, after.st_ino)
    ):
        raise ExecutionProfileError(f"{label} changed while read")
    if not data:
        raise ExecutionProfileError(f"{label} must be nonempty")
    return resolved, data


def _validate_profile(document: Mapping[str, Any]) -> None:
    try:
        orchestration_contracts.validate_record("execution-profile", dict(document))
    except orchestration_contracts.ContractValidationError as exc:
        raise ExecutionProfileError(f"Invalid execution profile: {exc}") from exc


def _read_profile(path: Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    resolved, data = _read_admitted_regular_file(path, label)
    try:
        value = yaml.load(data, Loader=_ClosedSafeLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ExecutionProfileError(f"Could not parse {label}: {resolved}") from exc
    if not isinstance(value, dict):
        raise ExecutionProfileError(f"{label} must contain one YAML mapping")
    _validate_profile(value)
    return resolved, data, value


def _merge_resource_fragment(
    target: dict[str, Any], fragment: Mapping[str, Any]
) -> None:
    for key, value in fragment.items():
        if key == "schema_version":
            continue
        if isinstance(value, Mapping):
            selected = target.get(key)
            if not isinstance(selected, dict):
                selected = {}
                target[key] = selected
            selected.update(copy.deepcopy(dict(value)))
        else:
            target[key] = copy.deepcopy(value)


def _merge_profile(target: dict[str, Any], fragment: Mapping[str, Any]) -> None:
    resources = fragment.get("resources")
    if isinstance(resources, Mapping):
        _merge_resource_fragment(target["resources"], resources)
    if "placement" in fragment:
        target["placement"] = copy.deepcopy(fragment["placement"])


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
            None
            if not module_init_value
            else _absolute_nonroot_path(module_init_value)
        ),
        modules=tuple(modules["load"]),
    )


def load_execution_profile(
    request_path: Path,
    config_path: Path | None = None,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
    expected_sha256: str | None = None,
) -> ExecutionProfile:
    """Load the direct default, an explicit fragment, and resource overrides.

    Retired adjacent configuration fails closed unless one profile is selected
    explicitly, preventing an old starter from silently using new defaults.
    """

    if expected_sha256 is not None and _SHA256.fullmatch(expected_sha256) is None:
        raise ExecutionProfileError("expected_sha256 must be 64 lowercase hex")
    if config_path is None:
        request_parent = Path(os.path.abspath(request_path)).parent
        retired = tuple(
            name
            for name in (
                "emrys.resources.yaml",
                "emrys.launcher.yaml",
                "norad.resources.yaml",
                "norad.launcher.yaml",
            )
            if os.path.lexists(request_parent / name)
        )
        if retired:
            raise ExecutionProfileError(
                "Retired adjacent configuration requires migration to one explicit "
                "execution profile: " + ", ".join(retired)
            )

    default_path, default_data, default = _read_profile(
        DEFAULT_PROFILE_PATH,
        "built-in execution profile",
    )
    if set(default) != {"schema_version", "resources", "placement"}:
        raise ExecutionProfileError("Built-in execution profile is incomplete")
    document = copy.deepcopy(default)
    selected_path: Path | None = None
    selected_data: bytes | None = None
    selected_fragment: dict[str, Any] | None = None
    if config_path is not None:
        selected_path, selected_data, selected_fragment = _read_profile(
            Path(config_path),
            "execution profile",
        )
        _merge_profile(document, selected_fragment)

    _validate_profile(document)
    default_sha256 = hashlib.sha256(default_data).hexdigest()
    config_sha256 = (
        None if selected_data is None else hashlib.sha256(selected_data).hexdigest()
    )
    resources = document["resources"]
    selected_resources = (
        None if selected_fragment is None else selected_fragment.get("resources")
    )
    resource_fragment_explicit = isinstance(selected_resources, Mapping) and set(
        selected_resources
    ) != {"schema_version"}
    resource_config_path = selected_path if resource_fragment_explicit else None
    resource_config_sha256 = config_sha256 if resource_fragment_explicit else None
    try:
        policy = admit_resource_policy(
            resources,
            default_sha256=orchestration_contracts.canonical_sha256(
                default["resources"]
            ),
            config_path=resource_config_path,
            config_sha256=resource_config_sha256,
        )
        policy = resume_resource_policy(policy, overrides=resource_overrides)
    except ResourceConfigError as exc:
        raise ExecutionProfileError(str(exc)) from exc

    profile = ExecutionProfile(
        resource_policy=policy,
        placement=_admit_placement(document["placement"]),
        source_path=default_path if selected_path is None else selected_path,
        source_raw_sha256=(default_sha256 if config_sha256 is None else config_sha256),
    )
    if expected_sha256 is not None and profile.sha256 != expected_sha256:
        raise ExecutionProfileError("Execution-profile SHA-256 differs")
    return profile


__all__ = (
    "DEFAULT_PROFILE_PATH",
    "DirectPlacement",
    "ExecutionProfile",
    "ExecutionProfileError",
    "Placement",
    "SCHEMA_VERSION",
    "SlurmPlacement",
    "load_execution_profile",
)
