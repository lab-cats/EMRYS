"""Check the runtime profiles used by Project discovery, Doctor, and execution."""

from __future__ import annotations

import hashlib
import stat
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from emrys.contracts.orchestration import api as contracts
from emrys.libraries import validation as report
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_package_tree_identity,
)
from emrys.libraries.validation.inputs import sha256_with_identity
from emrys.libraries.validation.tsv import tsv_bytes

from ._probes import run_checks
from . import _profile_contract as profile_contract
from ._profile_contract import RuntimeSeal
from ._profile_contract import CHOICE_IDS, PYTHON_CHECK_IDS, load_runtime_policy
from ._profile_contract import runtime_profile_checks as _runtime_profile_checks
from ._runtime_model import (
    PreflightError,
    RuntimeBinding,
    RuntimeCheck,
    RuntimeObservation,
)


@dataclass(frozen=True, slots=True)
class RuntimeInspection:
    """Immutable read-only result for one explicit runtime profile."""

    profile_path: Path
    profile_sha256: str
    profile_bytes: bytes
    observations: tuple[RuntimeObservation, ...]

    @property
    def required_ready(self) -> bool:
        """Return whether every required check ran and passed."""

        return all(observation.status == "pass" for observation in self.observations)


class RuntimeInspectionError(RuntimeError):
    """The declared runtime profile could not be inspected safely."""


class RuntimeContentMismatchError(RuntimeInspectionError):
    """A valid shared selector no longer matches the sealed fixed content."""


_Result = TypeVar("_Result")


def _profile_call(
    operation: Callable[..., _Result], /, *args: object, **kwargs: object
) -> _Result:
    try:
        return operation(*args, **kwargs)
    except (PreflightError, report.ValidationError, OSError) as exc:
        raise RuntimeInspectionError(str(exc)) from exc


def runtime_profile_bytes(choices: Mapping[str, Path]) -> bytes:
    """Store each selected path once; probe rules belong to the installed policy."""

    return tsv_bytes(
        ("check_id", "target"),
        ({"check_id": key, "target": str(choices[key])} for key in CHOICE_IDS),
    )


def inspect_runtime_profile_bytes(
    profile_data: bytes,
    profile_path: Path,
    *,
    checks: Iterable[RuntimeCheck],
    environment: Mapping[str, str],
) -> RuntimeInspection:
    """Probe validated candidate bytes without publishing a temporary profile."""

    try:
        profile_sha256 = hashlib.sha256(profile_data).hexdigest()
        results = run_checks(
            checks,
            environment=environment,
        )
    except PreflightError as exc:
        raise RuntimeInspectionError(str(exc)) from exc
    return RuntimeInspection(
        profile_path=profile_path,
        profile_sha256=profile_sha256,
        profile_bytes=profile_data,
        observations=tuple(results),
    )


def runtime_profile_checks(data: bytes, source_root: Path) -> tuple[RuntimeCheck, ...]:
    """Admit runtime choices and derive their complete fixed probe policy."""

    return _profile_call(_runtime_profile_checks, data, source_root)


def load_runtime_profile_contract(
    profile: Path,
    source_root: Path,
) -> tuple[bytes, tuple[RuntimeCheck, ...]]:
    """Read and validate one profile without running any declared probes."""

    data = _profile_call(report.read_bytes, profile, "Runtime choices")
    return data, runtime_profile_checks(data, source_root)


def runtime_file_bindings(
    inspection: RuntimeInspection,
    *,
    package_tree_ids: frozenset[str] = frozenset(),
    explicit_file_ids: frozenset[str] = frozenset(),
    donor_seal: Path | None = None,
) -> tuple[RuntimeBinding, ...]:
    """Bind executable/jar bytes and exact installed R package trees."""

    bindings: list[RuntimeBinding] = []
    renv_library = next(
        Path(item.check.target)
        for item in inspection.observations
        if item.check.check_id == "renv_library"
    )
    for observation in inspection.observations:
        check = observation.check
        if observation.status != "pass" or check.check_id in {
            "renv_project",
            "renv_library",
        }:
            continue
        if check.check_type == "r_namespace" or check.check_id in package_tree_ids:
            try:
                root = (
                    renv_library / check.target
                    if check.check_type == "r_namespace"
                    else Path(check.target)
                )
                resolved_root = root.resolve(strict=True)
                identity = installed_package_tree_identity(resolved_root)
                confirmed_root = root.resolve(strict=True)
            except (OSError, InstalledPackageIdentityError) as exc:
                raise RuntimeInspectionError(
                    f"Could not bind runtime package tree {check.check_id}: {exc}"
                ) from exc
            expected_root = (
                observation.resolved_path
                if check.check_type == "r_namespace"
                else Path(check.target)
            )
            if (
                expected_root is None
                or identity.root != expected_root
                or confirmed_root != resolved_root
            ):
                raise RuntimeInspectionError(
                    f"Runtime package-tree root changed: {check.check_id}"
                )
            bindings.append(
                RuntimeBinding(
                    check.check_id,
                    identity.root,
                    identity.root,
                    identity.sha256,
                    observation.observed,
                    ("package_tree" if check.check_id in package_tree_ids else None),
                )
            )
            continue
        path = Path(check.target)
        try:
            resolved = path.resolve(strict=True)
            state = path.lstat()
        except (OSError, report.ValidationError) as exc:
            raise RuntimeInspectionError(
                f"Could not bind runtime file {check.check_id}: {exc}"
            ) from exc
        if check.check_id in explicit_file_ids and (
            stat.S_ISLNK(state.st_mode)
            or not stat.S_ISREG(state.st_mode)
            or resolved != path
        ):
            raise RuntimeInspectionError(
                f"Analysis dependency must be a canonical real file: {check.check_id}"
            )
        try:
            digest, _state = sha256_with_identity(
                resolved, "Runtime file", nonempty=False
            )
            if path.resolve(strict=True) != resolved:
                raise RuntimeInspectionError(
                    f"Runtime file target changed: {check.check_id}"
                )
        except (OSError, report.ValidationError) as exc:
            raise RuntimeInspectionError(
                f"Could not bind runtime file {check.check_id}: {exc}"
            ) from exc
        bindings.append(
            RuntimeBinding(
                check.check_id,
                path,
                resolved,
                digest,
                observation.observed,
                "file" if check.check_id in explicit_file_ids else None,
            )
        )
    try:
        seal = profile_contract.runtime_profile_seal(inspection.profile_bytes)
        if donor_seal is not None:
            if seal is not None:
                raise RuntimeInspectionError(
                    "A borrowed runtime cannot be a managed donor"
                )
            seal = profile_contract.load_runtime_seal(donor_seal)
        if seal is not None:
            expected = {item.check_id: item for item in seal.bindings}
            observations = {
                item.check.check_id: item for item in inspection.observations
            }
            if not set(expected) <= set(observations):
                raise RuntimeInspectionError("Inspection omitted sealed runtime checks")
            for binding in bindings:
                if binding.check_id in profile_contract.PYTHON_CHECK_IDS:
                    continue
                if binding.check_id in expected:
                    if _binding_record(
                        binding, observations[binding.check_id].check
                    ) != _binding_record(
                        expected[binding.check_id], observations[binding.check_id].check
                    ):
                        raise RuntimeContentMismatchError(
                            f"Sealed runtime content or version changed: {binding.check_id}"
                        )
                elif binding.path.is_relative_to(
                    seal.managed_root
                ) or binding.resolved_path.is_relative_to(seal.managed_root):
                    raise RuntimeInspectionError(
                        f"Analysis dependency is not covered by the runtime seal: {binding.check_id}"
                    )
    except (PreflightError, report.ValidationError, OSError) as exc:
        raise RuntimeInspectionError(str(exc)) from exc
    return tuple(bindings)


def _binding_record(binding: RuntimeBinding, check: RuntimeCheck) -> dict[str, str]:
    return {
        "check_id": binding.check_id,
        "path": str(binding.path),
        "resolved_path": str(binding.resolved_path),
        "sha256": binding.sha256,
        "observed": binding.observed,
        "identity_kind": "package_tree"
        if check.check_type == "r_namespace"
        else binding.identity_kind or "file",
    }


def load_runtime_seal(path: Path) -> RuntimeSeal:
    return _profile_call(profile_contract.load_runtime_seal, path)


def admit_runtime_seal_bytes(path: Path, data: bytes) -> RuntimeSeal:
    """Admit retained seal bytes while an owning maintenance claim is held."""

    return _profile_call(
        profile_contract.admit_runtime_seal, path, data, require_content=False
    )


def shared_runtime_selection(
    data: bytes,
) -> profile_contract.SharedRuntimeSelection | None:
    """Read one shared selector without requiring the referenced seal."""

    return _profile_call(profile_contract.shared_runtime_selection, data)


def runtime_root_for_seal(path: Path) -> Path:
    return _profile_call(profile_contract.runtime_root_for_seal, path)


def runtime_profile_choices(data: bytes) -> dict[str, Path]:
    return {
        key: Path(value)
        for key, value in _profile_call(
            profile_contract.runtime_profile_choices, data
        ).items()
    }


def runtime_seal_bytes(inspection: RuntimeInspection, path: Path) -> bytes:
    """Prepare immutable native/R expectations from fresh required observations."""
    if not inspection.required_ready:
        raise RuntimeInspectionError("Runtime must pass every probe before sealing")
    if tuple(item.check.check_id for item in inspection.observations) != tuple(
        check.check_id for check in load_runtime_policy()
    ):
        raise RuntimeInspectionError(
            "Sealing requires the complete fixed runtime probe roster"
        )
    choices = runtime_profile_choices(inspection.profile_bytes)
    bindings = {item.check_id: item for item in runtime_file_bindings(inspection)}
    try:
        data = contracts.canonical_json_bytes(
            {
                "schema_version": 1,
                "managed_root": str(path.parent / "managed"),
                "choices": {
                    key: str(choices[key]) for key in CHOICE_IDS if key != "python"
                },
                "bindings": [
                    _binding_record(bindings[check.check_id], check)
                    for check in load_runtime_policy()
                    if check.check_id not in profile_contract.UNSEALED_CHECK_IDS
                ],
            }
        )
        profile_contract.admit_runtime_seal(path, data)
    except (
        KeyError,
        PreflightError,
        report.ValidationError,
        OSError,
        contracts.ContractValidationError,
    ) as exc:
        raise RuntimeInspectionError(f"Could not seal managed runtime: {exc}") from exc
    return data


def shared_runtime_profile_bytes(seal: Path, data: bytes, python: Path) -> bytes:
    return tsv_bytes(
        profile_contract.SHARED_PROFILE_HEADER,
        (
            {
                "seal_path": str(seal),
                "seal_sha256": hashlib.sha256(data).hexdigest(),
                "python": str(python),
            },
        ),
    )


__all__ = (
    "PYTHON_CHECK_IDS",
    "RuntimeBinding",
    "runtime_file_bindings",
    "admit_runtime_seal_bytes",
    "load_runtime_seal",
    "shared_runtime_selection",
    "runtime_root_for_seal",
    "runtime_profile_choices",
    "runtime_seal_bytes",
    "shared_runtime_profile_bytes",
    "RuntimeCheck",
    "RuntimeInspection",
    "RuntimeInspectionError",
    "RuntimeContentMismatchError",
    "RuntimeObservation",
    "inspect_runtime_profile_bytes",
    "load_runtime_profile_contract",
    "runtime_profile_bytes",
    "runtime_profile_checks",
    "load_runtime_policy",
)
