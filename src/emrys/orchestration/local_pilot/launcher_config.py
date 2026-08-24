"""Resolve and submit one generated single-allocation launcher configuration."""

from __future__ import annotations

import argparse
import copy
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from emrys.contracts.orchestration import api as orchestration_contracts

SCHEMA_VERSION = "emrys.local-pilot-launcher.v1"
ADJACENT_CONFIG_NAME = "emrys.launcher.yaml"
LEGACY_ADJACENT_CONFIG_NAME = "norad.launcher.yaml"
DOTENV_NAME = ".env"
BATCH_MARKER = "emrys-local-pilot-batch-v1"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "resources/default_launcher.yaml"

_SLURM_FIELDS = (
    "account",
    "partition",
    "qos",
    "cpus_per_task",
    "memory",
    "time",
    "exclusive",
    "nodelist",
)
_PATH_FIELDS = (
    "log_dir",
    "request",
    "workspace",
    "runtime_profile",
    "scratch_parent",
)
_MODULE_FIELDS = ("mode", "init", "load")
_TOP_LEVEL_FIELDS = ("schema_version", "slurm", "paths", "modules")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SAFE_SLURM_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_NODELIST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._,\[\]-]*$")
_SAFE_MODULE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+/-]*$")
_SLURM_SIZE = re.compile(r"^[1-9][0-9]*[KMGTP]?$")
_SLURM_TIME = re.compile(
    r"^(?:[0-9]+-[0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?|"
    r"[0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?|[1-9][0-9]*)$"
)

_FIELD_ENV_NAMES = {
    ("slurm", "account"): "EMRYS_SLURM_ACCOUNT",
    ("slurm", "partition"): "EMRYS_SLURM_PARTITION",
    ("slurm", "qos"): "EMRYS_SLURM_QOS",
    ("slurm", "cpus_per_task"): "EMRYS_SLURM_CPUS",
    ("slurm", "memory"): "EMRYS_SLURM_MEMORY",
    ("slurm", "time"): "EMRYS_SLURM_TIME",
    ("slurm", "exclusive"): "EMRYS_SLURM_EXCLUSIVE",
    ("slurm", "nodelist"): "EMRYS_SLURM_NODELIST",
    ("paths", "log_dir"): "EMRYS_LOG_DIR",
    ("paths", "request"): "EMRYS_REQUEST",
    ("paths", "workspace"): "EMRYS_WORKSPACE",
    ("paths", "runtime_profile"): "EMRYS_RUNTIME_PROFILE",
    ("paths", "scratch_parent"): "EMRYS_SCRATCH_PARENT",
    ("modules", "mode"): "EMRYS_MODULE_MODE",
    ("modules", "init"): "EMRYS_MODULE_INIT",
    ("modules", "load"): "EMRYS_MODULES",
}
_ALLOWED_DOTENV_NAMES = frozenset(_FIELD_ENV_NAMES.values())


class LauncherConfigError(ValueError):
    """One launcher source or its resolved submission policy is inadmissible."""


class _ClosedSafeLoader(yaml.SafeLoader):
    """Safe YAML loader rejecting merge and duplicate mapping keys."""

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                raise LauncherConfigError("YAML merge keys are not allowed")
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
                raise LauncherConfigError("Every YAML mapping key must be a string")
            if key in result:
                raise LauncherConfigError(f"Duplicate YAML mapping key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


@dataclass(frozen=True, slots=True)
class LauncherOverrides:
    """Explicit highest-precedence launcher values."""

    account: str | None = None
    partition: str | None = None
    qos: str | None = None
    cpus_per_task: int | None = None
    memory: str | None = None
    time: str | None = None
    log_dir: str | Path | None = None
    request: str | Path | None = None
    workspace: str | Path | None = None
    runtime_profile: str | Path | None = None
    module_mode: str | None = None
    module_init: str | Path | None = None
    modules: str | Sequence[str] | None = None
    scratch_parent: str | Path | None = None
    exclusive: bool | None = None
    nodelist: str | None = None


@dataclass(frozen=True, slots=True)
class LauncherPlan:
    """Fully resolved values for one outer single-node Slurm allocation."""

    account: str
    partition: str
    qos: str
    cpus_per_task: int
    memory: str
    time: str
    log_dir: Path
    request: Path
    workspace: Path
    runtime_profile: Path
    module_mode: str
    module_init: str
    modules: tuple[str, ...]
    scratch_parent: Path
    exclusive: bool
    nodelist: str | None
    config_path: Path | None
    dotenv_path: Path | None
    override_labels: tuple[str, ...]


def _read_yaml_mapping(data: bytes, path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(data, Loader=_ClosedSafeLoader)
    except LauncherConfigError:
        raise
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise LauncherConfigError(
            f"Could not parse launcher configuration YAML: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise LauncherConfigError("Launcher configuration must be a YAML mapping")
    return value


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


def _read_admitted_regular_file(
    path: Path,
    label: str,
    *,
    allow_empty: bool,
    private: bool = False,
) -> tuple[Path, bytes]:
    if not hasattr(os, "O_NOFOLLOW"):
        raise LauncherConfigError(
            f"{label} cannot be admitted without symbolic-link protection"
        )
    authored = Path(os.path.abspath(path))
    try:
        resolved = authored.resolve(strict=True)
    except OSError as exc:
        raise LauncherConfigError(f"Could not read {label}: {authored}") from exc
    if resolved != authored:
        raise LauncherConfigError(f"{label} must be canonical and nonsymlink")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    chunks: list[bytes] = []
    try:
        descriptor = os.open(authored, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise LauncherConfigError(f"{label} must be one real regular file")
        if private:
            if before.st_uid != os.getuid():
                raise LauncherConfigError(f"{label} owner is invalid")
            if stat.S_IMODE(before.st_mode) & ~0o600:
                raise LauncherConfigError(
                    f"{label} permissions must be mode 0600 or stricter"
                )
        bound_before = os.stat(authored, follow_symlinks=False)
        if (bound_before.st_dev, bound_before.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise LauncherConfigError(f"{label} changed during admission")
        while block := os.read(descriptor, 1024 * 1024):
            chunks.append(block)
        after = os.fstat(descriptor)
        bound_after = os.stat(authored, follow_symlinks=False)
    except LauncherConfigError:
        raise
    except OSError as exc:
        raise LauncherConfigError(f"Could not read {label}: {authored}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    data = b"".join(chunks)
    if (
        _stable_file_state(before) != _stable_file_state(after)
        or len(data) != before.st_size
        or (bound_after.st_dev, bound_after.st_ino)
        != (after.st_dev, after.st_ino)
    ):
        raise LauncherConfigError(f"{label} changed while read")
    if not allow_empty and not data:
        raise LauncherConfigError(f"{label} must be nonempty")
    return resolved, data


def _read_real_file(path: Path, label: str) -> tuple[Path, bytes]:
    return _read_admitted_regular_file(path, label, allow_empty=False)


def _require_source_checkout(path: Path) -> Path:
    authored = Path(os.path.abspath(path))
    try:
        state = authored.lstat()
        resolved = authored.resolve(strict=True)
    except OSError as exc:
        raise LauncherConfigError("Source checkout is unavailable") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
        raise LauncherConfigError("Source checkout must be one real directory")
    if resolved != authored:
        raise LauncherConfigError("Source checkout must be canonical")
    return resolved


def _validate_fragment(document: Mapping[str, Any]) -> None:
    unknown = sorted(set(document).difference(_TOP_LEVEL_FIELDS))
    if unknown:
        raise LauncherConfigError(
            "unknown launcher configuration key: " + ", ".join(unknown)
        )
    if document.get("schema_version") != SCHEMA_VERSION:
        raise LauncherConfigError(
            f"schema_version must be exactly {SCHEMA_VERSION}"
        )
    for section, allowed in (
        ("slurm", _SLURM_FIELDS),
        ("paths", _PATH_FIELDS),
        ("modules", _MODULE_FIELDS),
    ):
        value = document.get(section)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise LauncherConfigError(f"{section} must be a mapping")
        extras = sorted(set(value).difference(allowed))
        if extras:
            raise LauncherConfigError(
                f"unknown launcher configuration key in {section}: "
                + ", ".join(extras)
            )
        for field, selected in value.items():
            if isinstance(selected, dict):
                if set(selected) != {"env"}:
                    raise LauncherConfigError(
                        f"{section}.{field} environment reference must contain "
                        "exactly env"
                    )
                name = selected.get("env")
                if not isinstance(name, str) or not _ENV_NAME.fullmatch(name):
                    raise LauncherConfigError(
                        f"{section}.{field} environment variable name is invalid"
                    )
                expected = _FIELD_ENV_NAMES[(section, field)]
                if name != expected:
                    raise LauncherConfigError(
                        f"{section}.{field} environment reference must name {expected}"
                    )
    try:
        orchestration_contracts.validate_record("launcher-config", document)
    except orchestration_contracts.ContractValidationError as exc:
        raise LauncherConfigError(
            "Launcher configuration does not satisfy the closed schema"
        ) from exc


def _require_complete_defaults(document: Mapping[str, Any]) -> None:
    for section, fields in (
        ("slurm", _SLURM_FIELDS),
        ("paths", _PATH_FIELDS),
        ("modules", _MODULE_FIELDS),
    ):
        selected = document.get(section)
        if not isinstance(selected, Mapping) or set(selected) != set(fields):
            raise LauncherConfigError(
                f"Packaged launcher defaults have incomplete {section} keys"
            )


def _merge_fragment(target: dict[str, Any], fragment: Mapping[str, Any]) -> None:
    for section in ("slurm", "paths", "modules"):
        selected = fragment.get(section)
        if selected is not None:
            assert isinstance(selected, dict)
            target_section = target[section]
            assert isinstance(target_section, dict)
            target_section.update(copy.deepcopy(selected))


def _override_pairs(overrides: LauncherOverrides) -> tuple[tuple[str, str, Any], ...]:
    return (
        ("slurm", "account", overrides.account),
        ("slurm", "partition", overrides.partition),
        ("slurm", "qos", overrides.qos),
        ("slurm", "cpus_per_task", overrides.cpus_per_task),
        ("slurm", "memory", overrides.memory),
        ("slurm", "time", overrides.time),
        ("paths", "log_dir", overrides.log_dir),
        ("paths", "request", overrides.request),
        ("paths", "workspace", overrides.workspace),
        ("paths", "runtime_profile", overrides.runtime_profile),
        ("modules", "mode", overrides.module_mode),
        ("modules", "init", overrides.module_init),
        ("modules", "load", overrides.modules),
        ("paths", "scratch_parent", overrides.scratch_parent),
        ("slurm", "exclusive", overrides.exclusive),
        ("slurm", "nodelist", overrides.nodelist),
    )


def _apply_overrides(
    target: dict[str, Any], overrides: LauncherOverrides
) -> tuple[str, ...]:
    labels: list[str] = []
    for section, field, selected in _override_pairs(overrides):
        if selected is None:
            continue
        if isinstance(selected, Path):
            selected = str(selected)
        elif section == "modules" and field == "load" and not isinstance(
            selected, str
        ):
            selected = list(selected)
        target_section = target[section]
        assert isinstance(target_section, dict)
        target_section[field] = selected
        labels.append(f"{section}.{field}")
    return tuple(labels)


def _read_dotenv(source_checkout: Path) -> tuple[Path | None, dict[str, str]]:
    path = source_checkout / DOTENV_NAME
    if not os.path.lexists(path):
        return None, {}
    resolved, data = _read_admitted_regular_file(
        path,
        "Source-checkout .env",
        allow_empty=True,
        private=True,
    )
    if b"\r" in data:
        raise LauncherConfigError("Source-checkout .env contains a carriage return")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LauncherConfigError("Source-checkout .env is not UTF-8") from exc
    result: dict[str, str] = {}
    for line_number, line in enumerate(text.split("\n"), start=1):
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator or not _ENV_NAME.fullmatch(name):
            raise LauncherConfigError(
                f"Source-checkout .env line {line_number} must be NAME=VALUE"
            )
        if name not in _ALLOWED_DOTENV_NAMES:
            raise LauncherConfigError(
                f"Source-checkout .env names unsupported variable {name}"
            )
        if name in result:
            raise LauncherConfigError(
                f"Source-checkout .env has duplicate variable {name}"
            )
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise LauncherConfigError(
                f"Source-checkout .env variable {name} contains a control character"
            )
        result[name] = value
    return resolved, result


def _resolve_value(
    section: str,
    field: str,
    selected: Any,
    process_environment: Mapping[str, str],
    dotenv: Mapping[str, str],
) -> Any:
    if not isinstance(selected, dict):
        return selected
    if set(selected) != {"env"}:
        raise LauncherConfigError(
            f"{section}.{field} environment reference is malformed"
        )
    name = selected.get("env")
    expected = _FIELD_ENV_NAMES[(section, field)]
    if name != expected:
        raise LauncherConfigError(
            f"{section}.{field} environment reference must name {expected}"
        )
    if name in process_environment:
        return process_environment[name]
    if name in dotenv:
        return dotenv[name]
    raise LauncherConfigError(f"Missing referenced environment variable {name}")


def _string(
    value: Any,
    label: str,
    *,
    allow_empty: bool = False,
    allow_comma: bool = False,
) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        raise LauncherConfigError(f"{label} must be a string")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise LauncherConfigError(f"{label} contains an unsafe character")
    if not allow_comma and "," in value:
        raise LauncherConfigError(f"{label} contains an unsafe character")
    return value


def _slurm_name(value: Any, label: str) -> str:
    selected = _string(value, label)
    if not _SAFE_SLURM_NAME.fullmatch(selected):
        raise LauncherConfigError(f"{label} is invalid")
    return selected


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise LauncherConfigError(f"{label} must be a positive integer")
    if isinstance(value, str):
        if not value.isdigit():
            raise LauncherConfigError(f"{label} must be a positive integer")
        value = int(value)
    if not isinstance(value, int) or value < 1:
        raise LauncherConfigError(f"{label} must be a positive integer")
    return value


def _memory(value: Any) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    selected = _string(value, "slurm.memory")
    if selected != "site-default" and not _SLURM_SIZE.fullmatch(selected):
        raise LauncherConfigError(
            "slurm.memory must be site-default or one positive Slurm size"
        )
    return selected


def _time(value: Any) -> str:
    selected = _string(value, "slurm.time")
    if not _SLURM_TIME.fullmatch(selected):
        raise LauncherConfigError("slurm.time is invalid")
    return selected


def _boolean(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.lower()
        if normalized in {"1", "true"}:
            return True
        if normalized in {"0", "false"}:
            return False
    raise LauncherConfigError(f"{label} must be true/false or 1/0")


def _nodelist(value: Any) -> str | None:
    if value is None or value == "":
        return None
    selected = _string(value, "slurm.nodelist", allow_comma=True)
    if not _SAFE_NODELIST.fullmatch(selected):
        raise LauncherConfigError("slurm.nodelist is invalid")
    return selected


def _path(
    value: Any,
    label: str,
    *,
    relative_base: Path | None = None,
) -> Path:
    selected = _string(value, label)
    path = Path(selected)
    if not path.is_absolute():
        if relative_base is None:
            raise LauncherConfigError(f"{label} must be absolute")
        if any(part in {".", ".."} for part in path.parts):
            raise LauncherConfigError(f"{label} contains an unsafe relative component")
        path = relative_base / path
    if path == Path("/"):
        raise LauncherConfigError(f"{label} must be a non-root path")
    return Path(os.path.abspath(path))


def _module_load(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        selected: Sequence[Any] = () if not value else value.split(":")
    elif isinstance(value, list):
        selected = value
    else:
        raise LauncherConfigError("modules.load must be a string list")
    modules: list[str] = []
    for item in selected:
        if not isinstance(item, str) or not _SAFE_MODULE.fullmatch(item):
            raise LauncherConfigError("modules.load contains an invalid module")
        if item in modules:
            raise LauncherConfigError("modules.load must not contain duplicates")
        modules.append(item)
    return tuple(modules)


def _resolve_plan(
    document: Mapping[str, Any],
    process_environment: Mapping[str, str],
    dotenv: Mapping[str, str],
    *,
    config_path: Path | None,
    dotenv_path: Path | None,
    override_labels: tuple[str, ...],
    relative_path_bases: Mapping[str, Path | None],
) -> LauncherPlan:
    resolved: dict[str, dict[str, Any]] = {}
    for section, fields in (
        ("slurm", _SLURM_FIELDS),
        ("paths", _PATH_FIELDS),
        ("modules", _MODULE_FIELDS),
    ):
        source = document.get(section)
        if not isinstance(source, Mapping) or set(source) != set(fields):
            raise LauncherConfigError(f"Resolved {section} keys are incomplete")
        resolved[section] = {
            field: _resolve_value(
                section,
                field,
                source[field],
                process_environment,
                dotenv,
            )
            for field in fields
        }

    slurm = resolved["slurm"]
    paths = resolved["paths"]
    modules = resolved["modules"]
    log_dir = _path(paths["log_dir"], "paths.log_dir")
    if "%" in str(log_dir):
        raise LauncherConfigError(
            "paths.log_dir must not contain a Slurm percent expansion"
        )
    try:
        log_state = log_dir.lstat()
    except OSError as exc:
        raise LauncherConfigError("paths.log_dir must already exist") from exc
    if stat.S_ISLNK(log_state.st_mode) or not stat.S_ISDIR(log_state.st_mode):
        raise LauncherConfigError("paths.log_dir must be one real directory")
    mode = _string(modules["mode"], "modules.mode")
    if mode not in {"exact", "none"}:
        raise LauncherConfigError("modules.mode must be exact or none")
    module_init = _string(modules["init"], "modules.init", allow_empty=True)
    module_load = _module_load(modules["load"])
    if mode == "none" and (module_init or module_load):
        raise LauncherConfigError(
            "modules.init and modules.load must be empty when modules.mode=none"
        )
    if mode == "exact" and (not module_init or not module_load):
        raise LauncherConfigError(
            "modules.init and modules.load are required when modules.mode=exact"
        )
    if mode == "exact":
        init_path = Path(module_init)
        if not init_path.is_absolute() or init_path == Path("/"):
            raise LauncherConfigError(
                "modules.init must be an absolute non-root path in exact mode"
            )
    return LauncherPlan(
        account=_slurm_name(slurm["account"], "slurm.account"),
        partition=_slurm_name(slurm["partition"], "slurm.partition"),
        qos=_slurm_name(slurm["qos"], "slurm.qos"),
        cpus_per_task=_positive_integer(
            slurm["cpus_per_task"], "slurm.cpus_per_task"
        ),
        memory=_memory(slurm["memory"]),
        time=_time(slurm["time"]),
        log_dir=log_dir,
        request=_path(
            paths["request"],
            "paths.request",
            relative_base=relative_path_bases["request"],
        ),
        workspace=_path(paths["workspace"], "paths.workspace"),
        runtime_profile=_path(
            paths["runtime_profile"],
            "paths.runtime_profile",
            relative_base=relative_path_bases["runtime_profile"],
        ),
        module_mode=mode,
        module_init=module_init,
        modules=module_load,
        scratch_parent=_path(paths["scratch_parent"], "paths.scratch_parent"),
        exclusive=_boolean(slurm["exclusive"], "slurm.exclusive"),
        nodelist=_nodelist(slurm["nodelist"]),
        config_path=config_path,
        dotenv_path=dotenv_path,
        override_labels=override_labels,
    )


def load_launcher_plan(
    *,
    launcher_root: Path,
    source_checkout: Path,
    environment: Mapping[str, str] | None = None,
    overrides: LauncherOverrides = LauncherOverrides(),
    config_path: Path | None = None,
) -> LauncherPlan:
    """Resolve packaged defaults, launcher YAML, environment, and overrides."""

    root = Path(os.path.abspath(launcher_root))
    try:
        root_state = root.lstat()
    except OSError as exc:
        raise LauncherConfigError("Launcher root is unavailable") from exc
    if stat.S_ISLNK(root_state.st_mode) or not stat.S_ISDIR(root_state.st_mode):
        raise LauncherConfigError("Launcher root must be one real directory")
    checkout = _require_source_checkout(source_checkout)
    selected_environment = os.environ if environment is None else environment
    dotenv_path, dotenv = _read_dotenv(checkout)
    default_path, default_data = _read_real_file(
        DEFAULT_CONFIG_PATH, "packaged launcher defaults"
    )
    defaults = _read_yaml_mapping(default_data, default_path)
    _validate_fragment(defaults)
    _require_complete_defaults(defaults)
    document = copy.deepcopy(defaults)
    relative_path_bases: dict[str, Path | None] = {
        field: (
            root
            if isinstance(document["paths"][field], str)
            and not Path(document["paths"][field]).is_absolute()
            else None
        )
        for field in ("request", "runtime_profile")
    }
    selected_path: Path | None = None
    candidate = (
        Path(config_path)
        if config_path is not None
        else root / ADJACENT_CONFIG_NAME
    )
    if config_path is None:
        legacy_candidate = root / LEGACY_ADJACENT_CONFIG_NAME
        if os.path.lexists(legacy_candidate):
            if os.path.lexists(candidate):
                raise LauncherConfigError(
                    "Conflicting adjacent launcher configurations: "
                    f"{ADJACENT_CONFIG_NAME} and {LEGACY_ADJACENT_CONFIG_NAME}"
                )
            raise LauncherConfigError(
                f"Legacy adjacent launcher configuration {LEGACY_ADJACENT_CONFIG_NAME} "
                f"is not accepted; rename it to {ADJACENT_CONFIG_NAME}"
            )
    if config_path is not None or os.path.lexists(candidate):
        selected_path, data = _read_real_file(candidate, "launcher configuration")
        fragment = _read_yaml_mapping(data, selected_path)
        _validate_fragment(fragment)
        _merge_fragment(document, fragment)
        fragment_paths = fragment.get("paths")
        if isinstance(fragment_paths, Mapping):
            for field in ("request", "runtime_profile"):
                if field not in fragment_paths:
                    continue
                selected = fragment_paths[field]
                relative_path_bases[field] = (
                    selected_path.parent
                    if isinstance(selected, str)
                    and not Path(selected).is_absolute()
                    else None
                )
    labels = _apply_overrides(document, overrides)
    if overrides.request is not None:
        relative_path_bases["request"] = None
    if overrides.runtime_profile is not None:
        relative_path_bases["runtime_profile"] = None
    return _resolve_plan(
        document,
        selected_environment,
        dotenv,
        config_path=selected_path,
        dotenv_path=dotenv_path,
        override_labels=labels,
        relative_path_bases=relative_path_bases,
    )


def _positive_cli(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the generated wrapper's submit-mode argument surface."""

    parser.add_argument("wrapper_path", type=Path)
    parser.add_argument("--launcher-config", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--account")
    parser.add_argument("--partition")
    parser.add_argument("--qos")
    parser.add_argument("--cpus-per-task", type=_positive_cli)
    parser.add_argument("--memory")
    parser.add_argument("--time")
    parser.add_argument("--log-dir", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--runtime-profile", type=Path)
    parser.add_argument("--module-mode")
    parser.add_argument("--module-init")
    parser.add_argument("--modules")
    parser.add_argument("--scratch-parent", type=Path)
    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument("--exclusive", dest="exclusive", action="store_true")
    exclusive.add_argument(
        "--no-exclusive", dest="exclusive", action="store_false"
    )
    parser.set_defaults(exclusive=None)
    parser.add_argument("--nodelist")


def _overrides_from_args(arguments: argparse.Namespace) -> LauncherOverrides:
    return LauncherOverrides(
        account=arguments.account,
        partition=arguments.partition,
        qos=arguments.qos,
        cpus_per_task=arguments.cpus_per_task,
        memory=arguments.memory,
        time=arguments.time,
        log_dir=arguments.log_dir,
        request=arguments.request,
        workspace=arguments.workspace,
        runtime_profile=arguments.runtime_profile,
        module_mode=arguments.module_mode,
        module_init=arguments.module_init,
        modules=arguments.modules,
        scratch_parent=arguments.scratch_parent,
        exclusive=arguments.exclusive,
        nodelist=arguments.nodelist,
    )


def _generation_path(
    environment: Mapping[str, str], name: str, *, directory: bool
) -> Path:
    value = environment.get(name)
    if not value or "\n" in value or "\r" in value or "," in value:
        raise LauncherConfigError(f"{name} must be generation-bound")
    path = Path(value)
    if not path.is_absolute() or path == Path("/"):
        raise LauncherConfigError(f"{name} must be an absolute non-root path")
    authored = Path(os.path.abspath(path))
    if directory:
        try:
            state = authored.lstat()
            resolved = authored.resolve(strict=True)
        except OSError as exc:
            raise LauncherConfigError(f"{name} is unavailable") from exc
        if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
            raise LauncherConfigError(f"{name} must be one real directory")
        if resolved != authored:
            raise LauncherConfigError(f"{name} must be canonical")
        return resolved

    if authored.parent == Path("/"):
        raise LauncherConfigError(f"{name} parent must not be the filesystem root")
    if ":" in str(authored.parent):
        raise LauncherConfigError(f"{name} parent is unsafe for the sealed PATH")
    try:
        parent_state = authored.parent.lstat()
        parent_resolved = authored.parent.resolve(strict=True)
        before = authored.lstat()
        link_before = os.readlink(authored) if stat.S_ISLNK(before.st_mode) else ""
        target = authored.resolve(strict=True)
        target_before = target.stat(follow_symlinks=False)
        after = authored.lstat()
        link_after = os.readlink(authored) if stat.S_ISLNK(after.st_mode) else ""
        confirmed_target = authored.resolve(strict=True)
        target_after = confirmed_target.stat(follow_symlinks=False)
    except OSError as exc:
        raise LauncherConfigError(f"{name} is unavailable") from exc
    if (
        stat.S_ISLNK(parent_state.st_mode)
        or not stat.S_ISDIR(parent_state.st_mode)
        or parent_resolved != authored.parent
        or (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns)
        or link_before != link_after
        or confirmed_target != target
        or (target_before.st_dev, target_before.st_ino, target_before.st_mode)
        != (target_after.st_dev, target_after.st_ino, target_after.st_mode)
        or not stat.S_ISREG(target_after.st_mode)
        or not os.access(authored, os.X_OK)
    ):
        raise LauncherConfigError(f"{name} launcher identity is invalid or changed")
    return authored


def _wrapper_path(path: Path) -> Path:
    authored = Path(os.path.abspath(path))
    try:
        state = authored.lstat()
        resolved = authored.resolve(strict=True)
    except OSError as exc:
        raise LauncherConfigError("Generated wrapper is unavailable") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode):
        raise LauncherConfigError("Generated wrapper must be one real file")
    if resolved != authored:
        raise LauncherConfigError("Generated wrapper must be canonical")
    return resolved


def _export_value(name: str, value: str) -> str:
    if "\n" in value or "\r" in value or "," in value:
        raise LauncherConfigError(f"{name} is unsafe for Slurm export")
    return f"{name}={value}"


def _submission_command(
    plan: LauncherPlan,
    *,
    wrapper: Path,
    source_checkout: Path,
    workflow_python: Path,
    execute: bool,
    live_uid: int,
    live_user: str,
    sbatch: str,
) -> list[str]:
    python_directory = workflow_python.parent
    fields = (
        _export_value("PATH", f"{python_directory}:/usr/bin:/bin"),
        _export_value("EMRYS_SUBMIT_UID", str(live_uid)),
        _export_value("EMRYS_SUBMIT_USER", live_user),
        _export_value("USER", live_user),
        _export_value("LOGNAME", live_user),
        _export_value("EMRYS_SLURM_CPUS", str(plan.cpus_per_task)),
        _export_value("EMRYS_SOURCE_CHECKOUT", str(source_checkout)),
        _export_value("EMRYS_PYTHON", str(workflow_python)),
        _export_value("EMRYS_REQUEST", str(plan.request)),
        _export_value("EMRYS_WORKSPACE", str(plan.workspace)),
        _export_value("EMRYS_RUNTIME_PROFILE", str(plan.runtime_profile)),
        _export_value("EMRYS_MODULE_MODE", plan.module_mode),
        _export_value("EMRYS_MODULE_INIT", plan.module_init),
        _export_value("EMRYS_MODULES", ":".join(plan.modules)),
        _export_value("EMRYS_SCRATCH_PARENT", str(plan.scratch_parent)),
        _export_value("EMRYS_EXECUTE", "1" if execute else "0"),
    )
    command = [
        sbatch,
        "--parsable",
        f"--account={plan.account}",
        f"--partition={plan.partition}",
        f"--qos={plan.qos}",
        "--nodes=1",
        "--ntasks=1",
        f"--cpus-per-task={plan.cpus_per_task}",
    ]
    if plan.memory != "site-default":
        command.append(f"--mem={plan.memory}")
    if plan.exclusive:
        command.append("--exclusive")
    if plan.nodelist is not None:
        command.append(f"--nodelist={plan.nodelist}")
    command.extend(
        (
            f"--time={plan.time}",
            "--job-name=emrys-local-pilot",
            f"--output={plan.log_dir}/emrys-local-pilot-%j.out",
            f"--error={plan.log_dir}/emrys-local-pilot-%j.err",
            "--export=" + ",".join(fields),
            str(wrapper),
            BATCH_MARKER,
        )
    )
    return command


def _live_submitter_identity() -> tuple[int, str]:
    observed: list[str] = []
    for option in ("-u", "-un"):
        try:
            output = subprocess.check_output(
                ("/usr/bin/id", option),
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise LauncherConfigError(
                "Could not resolve the live submitter identity"
            ) from exc
        lines = output.splitlines()
        if len(lines) != 1:
            raise LauncherConfigError("Live submitter identity output is invalid")
        observed.append(lines[0])
    uid_text, live_user = observed
    if not uid_text.isdigit():
        raise LauncherConfigError("Live submitter numeric UID is invalid")
    if not _SAFE_SLURM_NAME.fullmatch(live_user):
        raise LauncherConfigError("Live user name is unsafe for Slurm export")
    return int(uid_text), live_user


def submit_from_args(
    arguments: argparse.Namespace,
    *,
    environment: Mapping[str, str] | None = None,
) -> int:
    """Resolve one submit-mode invocation and call ``sbatch`` exactly once."""

    selected_environment = os.environ if environment is None else environment
    wrapper = _wrapper_path(arguments.wrapper_path)
    source_checkout = _generation_path(
        selected_environment,
        "EMRYS_LAUNCHER_SOURCE_CHECKOUT",
        directory=True,
    )
    workflow_python = _generation_path(
        selected_environment,
        "EMRYS_LAUNCHER_PYTHON",
        directory=False,
    )
    plan = load_launcher_plan(
        launcher_root=wrapper.parent,
        source_checkout=source_checkout,
        environment=selected_environment,
        overrides=_overrides_from_args(arguments),
        config_path=arguments.launcher_config,
    )
    live_uid, live_user = _live_submitter_identity()
    if selected_environment.get("USER") != live_user or selected_environment.get(
        "LOGNAME"
    ) != live_user:
        raise LauncherConfigError("Submission USER/LOGNAME must match the live user")
    sbatch = shutil.which("sbatch", path=selected_environment.get("PATH", ""))
    if sbatch is None:
        raise LauncherConfigError("sbatch is unavailable on this host")
    command = _submission_command(
        plan,
        wrapper=wrapper,
        source_checkout=source_checkout,
        workflow_python=workflow_python,
        execute=bool(arguments.execute),
        live_uid=live_uid,
        live_user=live_user,
        sbatch=sbatch,
    )
    submission_environment = {
        name: value
        for name, value in selected_environment.items()
        if not name.startswith("SBATCH_") and name != "EMRYS_EXECUTE"
    }
    try:
        result = subprocess.run(
            command,
            env=submission_environment,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise LauncherConfigError("Could not execute sbatch") from exc
    if result.returncode != 0:
        raise LauncherConfigError(f"sbatch failed with exit {result.returncode}")
    output_lines = result.stdout.splitlines()
    if len(output_lines) != 1:
        raise LauncherConfigError("sbatch did not return one parsable job ID")
    job_id = output_lines[0].split(";", 1)[0]
    if not job_id.isdigit():
        raise LauncherConfigError("sbatch returned an invalid job ID")
    stdout_path = plan.log_dir / f"emrys-local-pilot-{job_id}.out"
    stderr_path = plan.log_dir / f"emrys-local-pilot-{job_id}.err"
    print(f"JOB_ID={job_id}")
    print(f"OUT={stdout_path}")
    print(f"ERR={stderr_path}")
    print("Wait for both files, then tail them with:")
    print(
        "while [[ ! -e "
        f"{shlex.quote(str(stdout_path))} || ! -e {shlex.quote(str(stderr_path))} "
        f"]]; do squeue -j {shlex.quote(job_id)}; sleep 2; done"
    )
    print(
        "tail -n +1 -F "
        f"{shlex.quote(str(stdout_path))} {shlex.quote(str(stderr_path))}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Submit one generated EMRYS local-pilot allocation."
    )
    configure_parser(parser)
    arguments = parser.parse_args(argv)
    try:
        return submit_from_args(arguments)
    except LauncherConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = (
    "ADJACENT_CONFIG_NAME",
    "BATCH_MARKER",
    "DEFAULT_CONFIG_PATH",
    "DOTENV_NAME",
    "LauncherConfigError",
    "LauncherOverrides",
    "LauncherPlan",
    "configure_parser",
    "load_launcher_plan",
    "main",
    "submit_from_args",
)
