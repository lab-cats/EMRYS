"""Checks and observations for Project runtime admission."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

RESULT_STATUSES = {"pass", "fail", "blocked", "not_checked"}
VERSION_TEXT_LIMIT = 4096
TOOL_PROBE_TIMEOUT_SECONDS = 30
R_NAMESPACE_PROBE_TIMEOUT_SECONDS = 120
HASH_PAYLOAD = b"emrys-runtime-preflight\n"
HASH_EXPECTED = hashlib.sha256(HASH_PAYLOAD).hexdigest()


class PreflightError(RuntimeError):
    """Raised when a runtime profile or probe result is invalid."""


@dataclass(frozen=True, slots=True)
class RuntimeCheck:
    """One effective check derived from installed runtime or analysis policy."""

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
