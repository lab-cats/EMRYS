"""Checks and observations for Project runtime admission."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RESULT_STATUSES = {"pass", "fail"}
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
    target: str
    probe_args: tuple[str, ...]
    expected: str


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


@dataclass(frozen=True, slots=True)
class RuntimeBinding:
    """One exact path-and-content binding admitted from the runtime inventory."""

    check_id: str
    path: Path
    resolved_path: Path
    sha256: str
    observed: str
    identity_kind: Literal["file", "package_tree"] | None = None
