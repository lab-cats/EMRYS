"""Shared data and literal contracts for runtime-preflight evidence."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

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
RESULT_HEADER = (
    "profile_sha256",
    "runtime_context",
    "check_id",
    "check_type",
    "target",
    "required",
    "status",
    "observed",
    "expected",
    "detail",
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
PROBE_TIMEOUT_SECONDS = 120
HASH_PAYLOAD = b"norad-runtime-preflight\n"
HASH_EXPECTED = hashlib.sha256(HASH_PAYLOAD).hexdigest()


class PreflightError(RuntimeError):
    """Raised for invalid inputs or unsafe publication state."""


@dataclass(frozen=True)
class Check:
    check_id: str
    check_type: str
    runtime_context: str
    required: bool
    target: str
    probe_args: tuple[str, ...]
    expected: str
    description: str


@dataclass(frozen=True)
class Result:
    check: Check
    status: str
    observed: str
    detail: str


def _fail(message: str) -> None:
    raise PreflightError(message)


def _single_line(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())
