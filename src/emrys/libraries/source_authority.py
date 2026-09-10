"""Installed-code identity and independent scientific-artifact roots."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_python_package_identity,
)

PROJECT_NAME = "emrys-rna-workflow"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONTROLLED_PYTHON_CACHE_PREFIX = "/dev/null"
CONTROLLED_PYTHON_OPTIONS = (
    "-X",
    f"pycache_prefix={CONTROLLED_PYTHON_CACHE_PREFIX}",
    "-I",
)


class InstalledPackageError(RuntimeError):
    """The installed code or its build metadata cannot be admitted."""


class ArtifactSourceRootError(RuntimeError):
    """The scientific artifact root is not an admissible directory."""


@dataclass(frozen=True, slots=True)
class ArtifactSourceRoot:
    root: Path


@dataclass(frozen=True, slots=True)
class InstalledPackage:
    """One observed installed package, including exact bytes and build origin."""

    root: Path
    content_sha256: str
    version: str
    git_commit: str | None
    git_dirty: bool | None
    python_lock_sha256: str

    @property
    def record(self) -> dict[str, object]:
        return {
            "path": str(self.root),
            "distribution": PROJECT_NAME,
            "version": self.version,
            "content_sha256": self.content_sha256,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "python_lock_sha256": self.python_lock_sha256,
        }


def admit_installed_package(*, root: Path = PACKAGE_ROOT) -> InstalledPackage:
    """Observe installed bytes without requiring a Git checkout at execution time."""

    if root != PACKAGE_ROOT:
        raise InstalledPackageError(
            "Requested package root differs from the executing package"
        )
    try:
        distribution = importlib.metadata.distribution(PROJECT_NAME)
        raw = distribution.read_text("emrys-build.json")
        if raw is None:
            raise InstalledPackageError(
                "Installed EMRYS has no build provenance; reinstall the package"
            )
        build = json.loads(raw)
        lock_sha256 = build["python_lock_sha256"]
        if (
            not isinstance(lock_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", lock_sha256) is None
        ):
            raise InstalledPackageError(
                "Installed EMRYS build metadata has no Python lock identity"
            )
        if build["git_commit"] is not None and (
            not isinstance(build["git_commit"], str)
            or re.fullmatch(r"[0-9a-f]{40}", build["git_commit"]) is None
        ):
            raise InstalledPackageError("Installed build origin is malformed")
        if build["git_dirty"] is not None and not isinstance(build["git_dirty"], bool):
            raise InstalledPackageError(
                "Installed build modification state is malformed"
            )
        identity = installed_python_package_identity(root)
        if distribution.read_text("emrys-build.json") != raw:
            raise InstalledPackageError(
                "Installed build metadata changed during admission"
            )
        content_sha256 = hashlib.sha256(
            json.dumps(
                {
                    "domain": "emrys.installed-runtime.v1",
                    "package_sha256": identity.sha256,
                    "version": distribution.version,
                    "build": build,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        return InstalledPackage(
            root,
            content_sha256,
            distribution.version,
            build["git_commit"],
            build["git_dirty"],
            lock_sha256,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        importlib.metadata.PackageNotFoundError,
        InstalledPackageIdentityError,
    ) as exc:
        raise InstalledPackageError(f"Could not admit installed EMRYS: {exc}") from exc


def controlled_python_argv(
    python_executable: str | Path,
    *arguments: str,
) -> tuple[str, ...]:
    """Build the one Python launch prefix used by controlled EMRYS children."""

    return (str(python_executable), *CONTROLLED_PYTHON_OPTIONS, *arguments)


def controlled_console_main() -> NoReturn:
    """Restart the installed command before importing its functional owners."""

    os.execv(
        sys.executable,
        controlled_python_argv(sys.executable, "-m", "emrys", *sys.argv[1:]),
    )


def is_controlled_python_argv(
    argv: Sequence[str],
    *,
    python_executable: str | Path,
) -> bool:
    """Return whether ``argv`` begins with the exact controlled Python prefix."""

    expected = controlled_python_argv(python_executable)
    return tuple(argv[: len(expected)]) == expected


def require_controlled_python_runtime() -> None:
    """Reject a Python child that could load adjacent package bytecode caches."""

    if sys.pycache_prefix != CONTROLLED_PYTHON_CACHE_PREFIX:
        raise InstalledPackageError(
            "Controlled EMRYS Python children require "
            "-X pycache_prefix=/dev/null before -I"
        )


def _canonical_directory(
    value: Path,
    label: str,
    error_type: type[RuntimeError] = InstalledPackageError,
) -> Path:
    if not value.is_absolute():
        raise error_type(f"{label} must be absolute: {value}")
    if value.is_symlink():
        raise error_type(f"{label} must not be a symbolic link: {value}")
    try:
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise error_type(f"{label} is unavailable: {value}") from exc
    if value != resolved:
        raise error_type(
            f"{label} must be canonical: expected {resolved}; received {value}"
        )
    if not resolved.is_dir():
        raise error_type(f"{label} is not a directory: {resolved}")
    return resolved


def admit_artifact_source_root(*, root: Path) -> ArtifactSourceRoot:
    """Admit an explicit canonical directory for contract-relative artifacts."""

    canonical_root = _canonical_directory(
        root,
        "Artifact source root",
        ArtifactSourceRootError,
    )
    return ArtifactSourceRoot(root=canonical_root)
