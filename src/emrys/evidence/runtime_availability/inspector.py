"""Check the runtime profiles used by Project discovery, Doctor, and execution."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries import validation as report
from emrys.libraries.validation.tsv import tsv_bytes

from ._probes import run_checks
from ._profile_contract import CHOICE_IDS, load_runtime_policy
from ._profile_contract import runtime_profile_checks as _runtime_profile_checks
from ._runtime_model import (
    PreflightError,
    RuntimeCheck,
    RuntimeObservation,
    _fail,
)


@dataclass(frozen=True, slots=True)
class RuntimeInspection:
    """Immutable read-only result for one explicit runtime profile."""

    profile_path: Path
    profile_sha256: str
    profile_bytes: bytes
    runtime_context: str
    observations: tuple[RuntimeObservation, ...]

    @property
    def required_ready(self) -> bool:
        """Return whether every required check ran and passed."""

        return all(
            not observation.check.required or observation.status == "pass"
            for observation in self.observations
        )


class RuntimeInspectionError(RuntimeError):
    """The declared runtime profile could not be inspected safely."""


def runtime_profile_bytes(choices: Mapping[str, Path]) -> bytes:
    """Store each selected path once; probe rules belong to the installed policy."""

    return tsv_bytes(
        ("check_id", "target"),
        ({"check_id": key, "target": str(choices[key])} for key in CHOICE_IDS),
    )


def inspect_runtime_profile_bytes(
    profile_data: bytes,
    profile_path: Path,
    runtime_context: str,
    *,
    checks: Iterable[RuntimeCheck],
    environment: Mapping[str, str] | None = None,
) -> RuntimeInspection:
    """Probe validated candidate bytes without publishing a temporary profile."""

    try:
        if runtime_context not in {"local", "cluster_batch"}:
            _fail(f"Unsupported runtime context: {runtime_context}")
        profile_sha256 = hashlib.sha256(profile_data).hexdigest()
        results = run_checks(
            checks,
            runtime_context,
            environment=environment,
        )
    except PreflightError as exc:
        raise RuntimeInspectionError(str(exc)) from exc
    return RuntimeInspection(
        profile_path=profile_path,
        profile_sha256=profile_sha256,
        profile_bytes=profile_data,
        runtime_context=runtime_context,
        observations=tuple(results),
    )


def runtime_profile_checks(data: bytes, source_root: Path) -> tuple[RuntimeCheck, ...]:
    """Admit runtime choices and derive their complete fixed probe policy."""

    try:
        return _runtime_profile_checks(data, source_root)
    except (PreflightError, report.ValidationError, OSError) as exc:
        raise RuntimeInspectionError(str(exc)) from exc


def load_runtime_profile_contract(
    profile: Path,
    source_root: Path,
) -> tuple[bytes, tuple[RuntimeCheck, ...]]:
    """Read and validate one profile without running any declared probes."""

    try:
        data = report.read_bytes(profile, "Runtime choices")
        checks = runtime_profile_checks(data, source_root)
    except (PreflightError, report.ValidationError, OSError) as exc:
        raise RuntimeInspectionError(str(exc)) from exc
    return data, tuple(checks)


__all__ = (
    "RuntimeCheck",
    "RuntimeInspection",
    "RuntimeInspectionError",
    "RuntimeObservation",
    "inspect_runtime_profile_bytes",
    "load_runtime_profile_contract",
    "runtime_profile_bytes",
    "runtime_profile_checks",
    "load_runtime_policy",
)
