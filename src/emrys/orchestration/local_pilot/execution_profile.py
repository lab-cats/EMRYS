"""Admit one execution profile without observing an execution attempt."""

from __future__ import annotations

import copy
import hashlib
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Literal

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.local_pilot.resource_policy import (
    ResourceConfigError,
    ResourceOverrides,
    ResourcePolicy,
    admit_resource_policy,
    resume_resource_policy,
)

SCHEMA_VERSION = "emrys.execution-profile.v1"
SCHEMA_ID = "urn:emrys:schema:orchestration:execution-profile:v1"
DEFAULT_PROFILE_PATH = Path(__file__).parent / "resources/default_execution.yaml"
PROFILE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts/schemas/orchestration/v3/execution_profile.schema.json"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


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

    @property
    def request_memory(self) -> bool:
        """Return whether submission should request an explicit memory limit."""

        return self.memory_mb is not None

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
    default_sha256: str
    config_path: Path | None
    config_sha256: str | None

    @property
    def resources(self) -> ResourcePolicy:
        """Return the retained Run-bound resource-policy projection."""

        return self.resource_policy

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
    except ExecutionProfileError:
        raise
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


@cache
def _profile_validator() -> Draft202012Validator:
    _path, data = _read_admitted_regular_file(
        PROFILE_SCHEMA_PATH,
        "execution-profile schema",
    )
    try:
        schema = orchestration_contracts.load_json_object_bytes(
            data,
            "execution-profile schema",
        )
        Draft202012Validator.check_schema(schema)
        _schemas, registry = orchestration_contracts.load_schema_registry()
    except (orchestration_contracts.ContractValidationError, SchemaError) as exc:
        raise ExecutionProfileError(
            "Execution-profile schema is not an admissible local contract"
        ) from exc
    if schema.get("$id") != SCHEMA_ID:
        raise ExecutionProfileError(f"Execution-profile schema $id must be {SCHEMA_ID}")
    return Draft202012Validator(schema, registry=registry)


def _validate_profile(document: Mapping[str, Any]) -> None:
    errors = sorted(
        _profile_validator().iter_errors(dict(document)),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if not errors:
        return
    error = errors[0]
    location = ".".join(str(part) for part in error.absolute_path)
    prefix = "execution profile" if not location else f"execution profile {location}"
    raise ExecutionProfileError(f"{prefix}: {error.message}")


def _read_profile(path: Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    resolved, data = _read_admitted_regular_file(path, label)
    try:
        value = yaml.load(data, Loader=_ClosedSafeLoader)
    except ExecutionProfileError:
        raise
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
        target_resources = target.get("resources")
        if not isinstance(target_resources, dict):
            raise ExecutionProfileError("Built-in execution resources are malformed")
        _merge_resource_fragment(target_resources, resources)
    if "placement" in fragment:
        target["placement"] = copy.deepcopy(fragment["placement"])


def _absolute_nonroot_path(value: Any, label: str) -> Path:
    if not isinstance(value, str):
        raise ExecutionProfileError(f"{label} must be an absolute path")
    path = Path(value)
    if not path.is_absolute() or path == Path("/"):
        raise ExecutionProfileError(f"{label} must be an absolute non-root path")
    return Path(os.path.abspath(path))


def _admit_placement(document: Any) -> Placement:
    if not isinstance(document, Mapping):
        raise ExecutionProfileError("Resolved placement must be one mapping")
    if document.get("kind") == "direct":
        return DirectPlacement()

    modules = document.get("modules")
    if not isinstance(modules, Mapping):
        raise ExecutionProfileError("Resolved Slurm modules must be one mapping")
    mode = modules.get("mode")
    if mode not in {"none", "exact"}:
        raise ExecutionProfileError("Resolved Slurm module mode is invalid")
    module_init_value = modules.get("init")
    if not isinstance(module_init_value, str):
        raise ExecutionProfileError("Resolved Slurm module init is invalid")
    load = modules.get("load")
    if not isinstance(load, list) or not all(isinstance(item, str) for item in load):
        raise ExecutionProfileError("Resolved Slurm module roster is invalid")
    return SlurmPlacement(
        account=(None if document.get("account") is None else str(document["account"])),
        partition=(
            None if document.get("partition") is None else str(document["partition"])
        ),
        qos=None if document.get("qos") is None else str(document["qos"]),
        cpus_per_task=int(document["cpus_per_task"]),
        memory_mb=(
            None if document.get("memory_mb") is None else int(document["memory_mb"])
        ),
        time=str(document["time"]),
        exclusive=bool(document["exclusive"]),
        nodelist=(
            None if document.get("nodelist") is None else str(document["nodelist"])
        ),
        scratch_parent=_absolute_nonroot_path(
            document["scratch_parent"],
            "placement.scratch_parent",
        ),
        module_mode=mode,
        module_init=(
            None
            if not module_init_value
            else _absolute_nonroot_path(
                module_init_value,
                "placement.modules.init",
            )
        ),
        modules=tuple(load),
    )


def load_execution_profile(
    request_path: Path,
    config_path: Path | None = None,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
    expected_sha256: str | None = None,
) -> ExecutionProfile:
    """Load the direct default, an explicit fragment, and resource overrides.

    ``request_path`` is accepted at the grouped-Run boundary but is deliberately
    not used for adjacent profile discovery.
    """

    del request_path
    if expected_sha256 is not None and _SHA256.fullmatch(expected_sha256) is None:
        raise ExecutionProfileError("expected_sha256 must be 64 lowercase hex")

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
    if set(document) != {"schema_version", "resources", "placement"}:
        raise ExecutionProfileError("Resolved execution profile is incomplete")

    default_sha256 = hashlib.sha256(default_data).hexdigest()
    config_sha256 = (
        None if selected_data is None else hashlib.sha256(selected_data).hexdigest()
    )
    resources = document.get("resources")
    if not isinstance(resources, Mapping):
        raise ExecutionProfileError("Resolved execution resources are malformed")
    selected_resources = (
        None if selected_fragment is None else selected_fragment.get("resources")
    )
    resource_config_path = (
        selected_path if isinstance(selected_resources, Mapping) else None
    )
    resource_config_sha256 = (
        orchestration_contracts.canonical_sha256(dict(selected_resources))
        if isinstance(selected_resources, Mapping)
        else None
    )
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
        default_sha256=default_sha256,
        config_path=selected_path,
        config_sha256=config_sha256,
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
    "PROFILE_SCHEMA_PATH",
    "SCHEMA_VERSION",
    "SlurmPlacement",
    "load_execution_profile",
)
