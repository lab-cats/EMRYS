"""Read-only summary file admission and errors."""

from __future__ import annotations

import os
import stat
from pathlib import Path


from .models import RunSummaryError


def _fail(message: str) -> None:
    raise RunSummaryError(message)


def _resolved_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(Path(value).expanduser())))


def _require_regular_file(label: str, value: str | Path) -> Path:
    path = _resolved_path(value)
    try:
        metadata = path.lstat()
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(metadata.st_mode):
        _fail(f"{label} must not be a symbolic link: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        _fail(f"{label} is not a regular file: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} cannot be resolved: {path}: {exc}")
    if not resolved.is_file():
        _fail(f"{label} does not resolve to a regular file: {path}")
    return resolved
