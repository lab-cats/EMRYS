"""Checks and observations for Project runtime admission."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

PROFILE_HEADER = (
    "check_id",
    "check_type",
    "runtime_context",
    "required",
    "target",
    "probe_args",
    "expected",
    "description",
)
CHECK_TYPES = {
    "tool_version",
    "tool_version_exit_1",
    "r_namespace",
    "hash_utility",
    "path_visibility",
}
RUNTIME_CONTEXTS = {"local", "cluster_batch", "any"}
RESULT_STATUSES = {"pass", "fail", "blocked", "not_checked"}
VISIBILITY_PROBES = {
    "file_readable",
    "directory_readable",
    "executable",
}
HASH_PROBES = {"python_hashlib", "sha256sum", "shasum"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VERSION_TEXT_LIMIT = 4096
TOOL_PROBE_TIMEOUT_SECONDS = 30
R_NAMESPACE_PROBE_TIMEOUT_SECONDS = 120
HASH_PAYLOAD = b"emrys-runtime-preflight\n"
HASH_EXPECTED = hashlib.sha256(HASH_PAYLOAD).hexdigest()


class PreflightError(RuntimeError):
    """Raised when a runtime profile or probe result is invalid."""


@dataclass(frozen=True, slots=True)
class RuntimeCheck:
    """One normalized check admitted from an explicit runtime profile."""

    check_id: str
    check_type: str
    runtime_context: str
    required: bool
    target: str
    probe_args: tuple[str, ...]
    expected: str
    description: str


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    """One completed availability observation without publication authority."""

    check: RuntimeCheck
    status: str
    observed: str
    detail: str
    resolved_path: Path | None = None


def _fail(message: str) -> None:
    raise PreflightError(message)


def _single_line(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())
