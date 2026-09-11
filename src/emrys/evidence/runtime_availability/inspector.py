"""Check the runtime profiles used by Project discovery, Doctor, and execution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries.validation.tsv import tsv_bytes

from ._probes import run_checks
from ._profile_contract import load_profile, load_profile_bytes
from ._runtime_model import (
    PROFILE_HEADER,
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


def runtime_profile_bytes(checks: Iterable[RuntimeCheck]) -> bytes:
    """Render normalized checks through the runtime profile's sole TSV owner."""

    return tsv_bytes(
        PROFILE_HEADER,
        (
            {
                "check_id": check.check_id,
                "check_type": check.check_type,
                "runtime_context": check.runtime_context,
                "required": str(check.required).lower(),
                "target": check.target,
                "probe_args": json.dumps(check.probe_args, separators=(",", ":")),
                "expected": check.expected,
                "description": check.description,
            }
            for check in checks
        ),
    )


def inspect_runtime_profile_bytes(
    profile_data: bytes,
    profile_path: Path,
    runtime_context: str,
    *,
    environment: Mapping[str, str] | None = None,
) -> RuntimeInspection:
    """Probe validated candidate bytes without publishing a temporary profile."""

    try:
        if runtime_context not in {"local", "cluster_batch"}:
            _fail(f"Unsupported runtime context: {runtime_context}")
        profile_data, loaded_checks = load_profile_bytes(profile_data)
        profile_sha256 = hashlib.sha256(profile_data).hexdigest()
        results = run_checks(
            loaded_checks,
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


def load_runtime_profile_contract(
    profile: Path,
) -> tuple[bytes, tuple[RuntimeCheck, ...]]:
    """Read and validate one profile without running any declared probes."""

    try:
        data, checks = load_profile(profile)
    except PreflightError as exc:
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
)
