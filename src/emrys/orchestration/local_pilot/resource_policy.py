"""Closed layered resource policy for one local-pilot workflow attempt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from emrys.contracts.orchestration import api as orchestration_contracts

SCHEMA_VERSION = "emrys.local-pilot-resources.v1"
ADJACENT_CONFIG_NAME = "emrys.resources.yaml"
LEGACY_ADJACENT_CONFIG_NAME = "norad.resources.yaml"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "resources/default_resources.yaml"
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
THREAD_CAPABLE_STAGE_IDS = ("00a", "01", "02", "06", "08")
REPORTING_KINDS = ("artifact_index", "run_summary", "html_report")


class ResourceConfigError(ValueError):
    """One resource source or its resolved policy is not admissible."""


class _ClosedSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects merge and duplicate mapping keys."""

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                raise ResourceConfigError("YAML merge keys are not allowed")
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
                raise ResourceConfigError("Every YAML mapping key must be a string")
            if key in result:
                raise ResourceConfigError(f"Duplicate YAML mapping key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


@dataclass(frozen=True, slots=True)
class AllocationCapacity:
    """Observed CPU and memory capacity available to the local executor."""

    cores: int
    memory_mb: int
    source: str

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


@dataclass(frozen=True, slots=True)
class ResourceOverrides:
    """Explicit highest-precedence command-line resource values."""

    workflow_cores: int | None = None
    workflow_memory_mb: int | None = None
    stage_concurrency: tuple[tuple[str, int], ...] = ()
    step_threads: tuple[tuple[str, int], ...] = ()
    stage_memory_mb: tuple[tuple[str, int], ...] = ()
    reporting_memory_mb: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        for field, allowed in (
            ("stage_concurrency", REPEATABLE_STAGE_IDS),
            ("step_threads", THREAD_CAPABLE_STAGE_IDS),
            ("stage_memory_mb", STAGE_IDS),
            ("reporting_memory_mb", REPORTING_KINDS),
        ):
            values = getattr(self, field)
            keys = [key for key, _ in values]
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            if duplicates:
                raise ResourceConfigError(
                    f"Duplicate command-line {field} override: "
                    + ", ".join(duplicates)
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
        for field in ("workflow_cores", "workflow_memory_mb"):
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
        if self.workflow_cores is not None:
            labels.append("workflow_cores")
        if self.workflow_memory_mb is not None:
            labels.append("workflow_memory_mb")
        for field in (
            "stage_concurrency",
            "step_threads",
            "stage_memory_mb",
            "reporting_memory_mb",
        ):
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
    """One admitted symbolic policy plus non-Run reporting and source context."""

    declaration: ComputationalResourceDeclaration
    reporting_memory_mb: tuple[
        tuple[str, int | Literal["workflow"]], ...
    ]
    default_sha256: str
    config_path: Path | None
    config_sha256: str | None
    override_labels: tuple[str, ...]

    def document(self) -> dict[str, Any]:
        """Return the complete symbolic policy for persistence and re-admission."""

        return {
            "schema_version": SCHEMA_VERSION,
            **self.declaration.identity_document(),
            "reporting_memory_mb": dict(self.reporting_memory_mb),
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
    reporting_memory_mb: tuple[tuple[str, int], ...]

    @property
    def declaration(self) -> ComputationalResourceDeclaration:
        return self.policy.declaration

    @property
    def default_sha256(self) -> str:
        return self.policy.default_sha256

    @property
    def config_path(self) -> Path | None:
        return self.policy.config_path

    @property
    def config_sha256(self) -> str | None:
        return self.policy.config_sha256

    @property
    def override_labels(self) -> tuple[str, ...]:
        return self.policy.override_labels

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

    def thread_map(self) -> dict[str, int]:
        """Return the closed thread-capable stage mapping."""

        return dict(self.step_threads)

    def concurrency_map(self) -> dict[str, int]:
        """Return the closed repeatable-stage concurrency mapping."""

        return dict(self.stage_concurrency)

    def stage_memory_map(self) -> dict[str, int]:
        """Return total memory reserved by each computational owner job."""

        return dict(self.stage_memory_mb)

    def reporting_memory_map(self) -> dict[str, int]:
        """Return total memory reserved by each reporting job."""

        return dict(self.reporting_memory_mb)

    def concurrency_for(self, step_id: str) -> int:
        """Return the configured repeatable-stage cap or singleton cap."""

        return dict(self.stage_concurrency).get(step_id, 1)

    def memory_for(self, step_id: str) -> int:
        """Return total MiB reserved by one computational owner job."""

        try:
            return dict(self.stage_memory_mb)[step_id]
        except KeyError as exc:
            raise KeyError(step_id) from exc

    def reporting_memory_for(self, kind: str) -> int:
        """Return total MiB reserved by one reporting job."""

        try:
            return dict(self.reporting_memory_mb)[kind]
        except KeyError as exc:
            raise KeyError(kind) from exc

    def effective_document(self) -> dict[str, Any]:
        """Return the canonical JSON-ready effective policy."""

        return {
            "schema_version": SCHEMA_VERSION,
            "workflow_cores": self.workflow_cores,
            "workflow_memory_mb": self.workflow_memory_mb,
            "stage_concurrency": dict(self.stage_concurrency),
            "step_threads": dict(self.step_threads),
            "stage_memory_mb": dict(self.stage_memory_mb),
            "reporting_memory_mb": dict(self.reporting_memory_mb),
        }

    @property
    def sha256(self) -> str:
        """Digest the exact effective policy independently of its sources."""

        return orchestration_contracts.canonical_sha256(self.effective_document())

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
            },
            "sources": {
                "default_sha256": self.default_sha256,
                "config_path": (
                    None if self.config_path is None else str(self.config_path)
                ),
                "config_sha256": self.config_sha256,
                "cli_overrides": list(self.override_labels),
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


def _load_yaml_mapping(data: bytes, path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(data.decode("utf-8"), Loader=_ClosedSafeLoader)
    except ResourceConfigError:
        raise
    except (UnicodeError, yaml.YAMLError) as exc:
        raise ResourceConfigError(
            f"Could not parse resource YAML {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ResourceConfigError(
            f"Resource YAML must contain one mapping object: {path}"
        )
    try:
        orchestration_contracts.validate_record("resource-config", value)
    except orchestration_contracts.ContractValidationError as exc:
        raise ResourceConfigError(str(exc)) from exc
    return value


def _read_real_config(path: Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    authored = Path(os.path.abspath(path))
    try:
        authored_state = authored.lstat()
        resolved = authored.resolve(strict=True)
        state = resolved.stat()
        data = resolved.read_bytes()
    except OSError as exc:
        raise ResourceConfigError(f"Could not read {label} {authored}: {exc}") from exc
    if stat.S_ISLNK(authored_state.st_mode) or not stat.S_ISREG(state.st_mode):
        raise ResourceConfigError(f"{label} must be one real file: {authored}")
    if not data:
        raise ResourceConfigError(f"{label} must be nonempty: {authored}")
    return resolved, data, _load_yaml_mapping(data, resolved)


def _merge_fragment(target: dict[str, Any], fragment: Mapping[str, Any]) -> None:
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


def _apply_overrides(target: dict[str, Any], overrides: ResourceOverrides) -> None:
    if overrides.workflow_cores is not None:
        target["workflow_cores"] = overrides.workflow_cores
    if overrides.workflow_memory_mb is not None:
        target["workflow_memory_mb"] = overrides.workflow_memory_mb
    for field in (
        "stage_concurrency",
        "step_threads",
        "stage_memory_mb",
        "reporting_memory_mb",
    ):
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
    stage_concurrency = _closed_map(
        value, "stage_concurrency", REPEATABLE_STAGE_IDS
    )
    step_threads = _closed_map(value, "step_threads", THREAD_CAPABLE_STAGE_IDS)
    stage_memory = _closed_map(value, "stage_memory_mb", STAGE_IDS)
    reporting_memory = _closed_map(
        value, "reporting_memory_mb", REPORTING_KINDS
    )
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
        reporting_memory_mb=tuple(
            (
                key,
                "workflow"
                if reporting_memory[key] == "workflow"
                else int(reporting_memory[key]),
            )
            for key in REPORTING_KINDS
        ),
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

    admitted = admit_resource_policy(
        policy.document(),
        default_sha256=policy.default_sha256,
        config_path=policy.config_path,
        config_sha256=policy.config_sha256,
        override_labels=policy.override_labels,
    )
    declaration = admitted.declaration
    workflow_cores = declaration.workflow_cores
    workflow_memory = (
        allocation.memory_mb
        if declaration.workflow_memory_mb == "allocation"
        else declaration.workflow_memory_mb
    )
    if workflow_cores > allocation.cores:
        raise ResourceConfigError(
            "Workflow cores exceed observed allocation: "
            f"{workflow_cores} > {allocation.cores}"
        )
    if workflow_memory > allocation.memory_mb:
        raise ResourceConfigError(
            "Workflow memory exceeds observed allocation: "
            f"{workflow_memory} > {allocation.memory_mb} MiB"
        )
    resolved_stage_memory = {
        step_id: workflow_memory if value == "workflow" else int(value)
        for step_id, value in declaration.stage_memory_mb
    }
    resolved_reporting_memory = {
        kind: workflow_memory if value == "workflow" else int(value)
        for kind, value in admitted.reporting_memory_mb
    }
    thread_values = dict(declaration.step_threads)
    concurrency_values = dict(declaration.stage_concurrency)
    for step_id in STAGE_IDS:
        threads = thread_values.get(step_id, 1)
        memory = resolved_stage_memory[step_id]
        concurrency = concurrency_values.get(step_id, 1)
        if concurrency * threads > workflow_cores:
            raise ResourceConfigError(
                f"Stage {step_id} concurrency x threads exceeds workflow cores: "
                f"{concurrency} x {threads} > {workflow_cores}"
            )
        if concurrency * memory > workflow_memory:
            raise ResourceConfigError(
                f"Stage {step_id} concurrency x memory exceeds workflow memory: "
                f"{concurrency} x {memory} > {workflow_memory} MiB"
            )
    for kind, memory in resolved_reporting_memory.items():
        if memory > workflow_memory:
            raise ResourceConfigError(
                f"Reporting {kind} memory exceeds workflow memory: "
                f"{memory} > {workflow_memory} MiB"
            )
    resolution = AttemptResourceResolution(
        allocation=allocation,
        workflow_memory_mb=workflow_memory,
        stage_memory_mb=tuple((key, resolved_stage_memory[key]) for key in STAGE_IDS),
    )
    return ResourcePlan(
        policy=admitted,
        resolution=resolution,
        reporting_memory_mb=tuple(
            (key, resolved_reporting_memory[key]) for key in REPORTING_KINDS
        ),
    )


def load_resource_policy(
    request_path: Path,
    *,
    config_path: Path | None = None,
    overrides: ResourceOverrides = ResourceOverrides(),
) -> ResourcePolicy:
    """Load defaults, optional YAML, and overrides without observing capacity."""

    default_path, default_data, default = _read_real_config(
        DEFAULT_CONFIG_PATH,
        "packaged resource defaults",
    )
    del default_path
    document = copy.deepcopy(default)
    selected_path: Path | None = None
    selected_data: bytes | None = None
    request_parent = Path(os.path.abspath(request_path)).parent
    candidate = (
        Path(config_path)
        if config_path is not None
        else request_parent / ADJACENT_CONFIG_NAME
    )
    if config_path is None:
        legacy_candidate = request_parent / LEGACY_ADJACENT_CONFIG_NAME
        if os.path.lexists(legacy_candidate):
            if os.path.lexists(candidate):
                raise ResourceConfigError(
                    "Conflicting adjacent resource configurations: "
                    f"{ADJACENT_CONFIG_NAME} and {LEGACY_ADJACENT_CONFIG_NAME}"
                )
            raise ResourceConfigError(
                f"Legacy adjacent resource configuration {LEGACY_ADJACENT_CONFIG_NAME} "
                f"is not accepted; rename it to {ADJACENT_CONFIG_NAME}"
            )
    if config_path is not None or os.path.lexists(candidate):
        selected_path, selected_data, fragment = _read_real_config(
            candidate,
            "resource configuration",
        )
        _merge_fragment(document, fragment)
    _apply_overrides(document, overrides)
    return admit_resource_policy(
        document,
        default_sha256=hashlib.sha256(default_data).hexdigest(),
        config_path=selected_path,
        config_sha256=(
            None if selected_data is None else hashlib.sha256(selected_data).hexdigest()
        ),
        override_labels=overrides.labels(),
    )


def load_resource_plan(
    request_path: Path,
    allocation: AllocationCapacity,
    *,
    config_path: Path | None = None,
    overrides: ResourceOverrides = ResourceOverrides(),
) -> ResourcePlan:
    """Compatibility wrapper that loads then resolves one resource policy."""

    return resolve_resource_policy(
        load_resource_policy(
            request_path,
            config_path=config_path,
            overrides=overrides,
        ),
        allocation,
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
    predecessor_policy: ResourcePolicy | Mapping[str, Any],
    *,
    overrides: ResourceOverrides = ResourceOverrides(),
) -> ResourcePolicy:
    """Re-admit a predecessor policy and explicit overrides without allocation."""

    if isinstance(predecessor_policy, ResourcePolicy):
        document = predecessor_policy.document()
        default_sha256 = predecessor_policy.default_sha256
        config_path = predecessor_policy.config_path
        config_sha256 = predecessor_policy.config_sha256
        prior_labels = predecessor_policy.override_labels
    else:
        effective = predecessor_policy.get("effective")
        sources = predecessor_policy.get("sources")
        if not isinstance(effective, dict):
            raise ResourceConfigError("Predecessor resource policy is malformed")
        if orchestration_contracts.canonical_sha256(
            effective
        ) != predecessor_policy.get("effective_sha256"):
            raise ResourceConfigError("Predecessor effective resource digest differs")
        document = copy.deepcopy(effective)
        default_sha256, config_path, config_sha256, prior_labels = (
            _admit_policy_sources(sources, label="Predecessor")
        )
    _apply_overrides(document, overrides)
    combined_labels = tuple(dict.fromkeys((*prior_labels, *overrides.labels())))
    return admit_resource_policy(
        document,
        default_sha256=default_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        override_labels=combined_labels,
    )


def resume_resource_plan(
    predecessor_policy: ResourcePolicy | Mapping[str, Any],
    allocation: AllocationCapacity,
    *,
    overrides: ResourceOverrides = ResourceOverrides(),
) -> ResourcePlan:
    """Compatibility wrapper that re-admits then resolves a predecessor policy."""

    if not isinstance(predecessor_policy, ResourcePolicy) and (
        "symbolic" in predecessor_policy or "symbolic_sha256" in predecessor_policy
    ):
        predecessor_policy = admit_resource_policy_record(
            predecessor_policy,
            require_symbolic=True,
        ).policy
    return resolve_resource_policy(
        resume_resource_policy(predecessor_policy, overrides=overrides),
        allocation,
    )


def admit_resource_policy_record(
    record: Mapping[str, Any],
    *,
    require_symbolic: bool = False,
) -> ResourcePlan:
    """Re-admit one closed persisted policy record.

    Historical records contain only the allocation-resolved policy. Successor
    records additionally retain the symbolic policy so a later Attempt can
    resolve the same Run declaration against a different allocation.
    """

    legacy_keys = {"effective", "effective_sha256", "allocation", "sources"}
    successor_keys = legacy_keys | {"symbolic", "symbolic_sha256"}
    observed_keys = set(record)
    if observed_keys == successor_keys:
        successor = True
    elif observed_keys == legacy_keys and not require_symbolic:
        successor = False
    else:
        expected = successor_keys if require_symbolic else legacy_keys
        raise ResourceConfigError(
            "Persisted resource policy keys are malformed; expected "
            + ", ".join(sorted(expected))
            + (" plus optional symbolic fields" if not require_symbolic else "")
        )

    allocation = record.get("allocation")
    if not isinstance(allocation, dict) or set(allocation) != {
        "cores",
        "memory_mb",
        "source",
    }:
        raise ResourceConfigError("Persisted resource allocation is malformed")
    try:
        capacity = AllocationCapacity(
            cores=allocation["cores"],
            memory_mb=allocation["memory_mb"],
            source=allocation["source"],
        )
    except KeyError as exc:  # Defensive against a nonstandard Mapping implementation.
        raise ResourceConfigError(
            "Persisted resource allocation is malformed"
        ) from exc

    if not successor:
        return resume_resource_plan(record, capacity)

    symbolic = record.get("symbolic")
    effective = record.get("effective")
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

    default_sha256, config_path, config_sha256, override_labels = (
        _admit_policy_sources(sources, label="Persisted")
    )

    policy = admit_resource_policy(
        symbolic,
        default_sha256=default_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        override_labels=override_labels,
    )
    resolved = resolve_resource_policy(policy, capacity)
    if resolved.effective_document() != effective:
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


def add_resource_arguments(parser: argparse.ArgumentParser) -> None:
    """Add optional highest-precedence execution-resource controls."""

    parser.add_argument(
        "--resource-config",
        type=Path,
        help=(
            "Optional resource YAML. A new run otherwise discovers "
            "emrys.resources.yaml beside the request; a resume otherwise "
            "reuses its predecessor policy."
        ),
    )
    parser.add_argument(
        "--workflow-cores",
        type=_positive_integer,
        help="Override workflow_cores from YAML and packaged defaults.",
    )
    parser.add_argument(
        "--workflow-memory-mb",
        type=_positive_integer,
        help="Override workflow_memory_mb from YAML and packaged defaults.",
    )
    parser.add_argument(
        "--stage-concurrency",
        action="append",
        default=[],
        metavar="STEP=COUNT",
        type=_assignment,
        help="Repeatable per-stage concurrency override.",
    )
    parser.add_argument(
        "--step-threads",
        action="append",
        default=[],
        metavar="STEP=THREADS",
        type=_assignment,
        help="Repeatable thread-capable stage override.",
    )
    parser.add_argument(
        "--stage-memory-mb",
        action="append",
        default=[],
        metavar="STEP=MIB",
        type=_assignment,
        help="Repeatable per-stage memory override in MiB.",
    )
    parser.add_argument(
        "--reporting-memory-mb",
        action="append",
        default=[],
        metavar="KIND=MIB",
        type=_assignment,
        help="Repeatable reporting memory override in MiB.",
    )


def overrides_from_args(arguments: argparse.Namespace) -> ResourceOverrides:
    """Project only explicitly supplied command-line resource values."""

    return ResourceOverrides(
        workflow_cores=getattr(arguments, "workflow_cores", None),
        workflow_memory_mb=getattr(arguments, "workflow_memory_mb", None),
        stage_concurrency=tuple(getattr(arguments, "stage_concurrency", ())),
        step_threads=tuple(getattr(arguments, "step_threads", ())),
        stage_memory_mb=tuple(getattr(arguments, "stage_memory_mb", ())),
        reporting_memory_mb=tuple(
            getattr(arguments, "reporting_memory_mb", ())
        ),
    )


__all__ = (
    "ADJACENT_CONFIG_NAME",
    "AllocationCapacity",
    "AttemptResourceResolution",
    "ComputationalResourceDeclaration",
    "DEFAULT_CONFIG_PATH",
    "REPORTING_KINDS",
    "REPEATABLE_STAGE_IDS",
    "ResourceConfigError",
    "ResourceOverrides",
    "ResourcePolicy",
    "ResourcePlan",
    "STAGE_IDS",
    "THREAD_CAPABLE_STAGE_IDS",
    "add_resource_arguments",
    "admit_resource_policy",
    "admit_resource_policy_record",
    "load_resource_policy",
    "load_resource_plan",
    "overrides_from_args",
    "resolve_resource_policy",
    "resume_resource_policy",
    "resume_resource_plan",
    "stage_slot_name",
)
