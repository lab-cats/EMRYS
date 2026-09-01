"""Deterministic byte identity for one installed package directory tree."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.resources
import inspect
import os
import re
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# The renamed package namespace starts a new digest domain. A v2 EMRYS digest
# cannot be mistaken for a pre-cutover installed-package identity.
_DIGEST_DOMAIN = b"emrys-installed-package-tree-v2\0"
_PYTHON_DIGEST_DOMAIN = b"emrys-installed-python-package-tree-v1\0"
_READ_CHUNK_BYTES = 1024 * 1024
_PROVIDER_RE = re.compile(
    r"(?P<package>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*):(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
)


class InstalledPackageIdentityError(RuntimeError):
    """An installed package tree could not be admitted without ambiguity."""


class _Digest(Protocol):
    def update(self, value: bytes) -> None: ...


@dataclass(frozen=True, slots=True)
class InstalledPackageTreeIdentity:
    """Canonical root and deterministic content digest for one package tree."""

    root: Path
    sha256: str


@dataclass(frozen=True, slots=True)
class InstalledProviderV1:
    """One exact callable entry point and its installed package identity."""

    provider: Callable[..., object]
    entry_point_value: str
    distribution_name: str
    distribution_version: str
    package: InstalledPackageTreeIdentity

    def require_callables(self, *values: Callable[..., object], label: str) -> None:
        """Require additional callable implementations inside this package."""

        for value in (self.provider, *values):
            try:
                source = inspect.getsourcefile(value)
                path = None if source is None else Path(source).resolve(strict=True)
            except (OSError, TypeError):
                path = None
            if (
                path is None
                or not path.is_file()
                or not path.is_relative_to(self.package.root)
            ):
                raise InstalledPackageIdentityError(
                    f"{label} callable is outside its admitted package"
                )


def _metadata_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _framed(digest: _Digest, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def _entry_frame(
    digest: _Digest,
    *,
    kind: bytes,
    relative: bytes,
    metadata: os.stat_result,
    content_sha256: bytes,
) -> None:
    _framed(digest, kind)
    _framed(digest, relative)
    _framed(digest, stat.S_IMODE(metadata.st_mode).to_bytes(4, "big"))
    size = metadata.st_size if stat.S_ISREG(metadata.st_mode) else 0
    _framed(digest, size.to_bytes(8, "big"))
    _framed(digest, content_sha256)


def _read_regular_file(path: Path, admitted: os.stat_result) -> bytes:
    if not hasattr(os, "O_NOFOLLOW"):
        raise InstalledPackageIdentityError(
            "This platform lacks required no-follow package-tree admission"
        )
    descriptor = -1
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise InstalledPackageIdentityError(
                f"Installed package entry is not a regular file: {path}"
            )
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, _READ_CHUNK_BYTES):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise InstalledPackageIdentityError(
            f"Could not read installed package file: {path}: {exc}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    try:
        named = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise InstalledPackageIdentityError(
            f"Could not re-admit installed package file: {path}: {exc}"
        ) from exc
    if (
        _metadata_identity(admitted) != _metadata_identity(before)
        or _metadata_identity(before) != _metadata_identity(after)
        or _metadata_identity(after) != _metadata_identity(named)
    ):
        raise InstalledPackageIdentityError(
            f"Installed package file changed while it was read: {path}"
        )
    data = b"".join(chunks)
    if len(data) != before.st_size:
        raise InstalledPackageIdentityError(
            f"Installed package file size changed while it was read: {path}"
        )
    return data


def _digest_directory(
    root: Path,
    directory: Path,
    digest: _Digest,
    *,
    ignore_python_cache: bool = False,
) -> None:
    try:
        before = directory.stat(follow_symlinks=False)
        with os.scandir(directory) as scanned:
            entries = sorted(scanned, key=lambda item: os.fsencode(item.name))
    except OSError as exc:
        raise InstalledPackageIdentityError(
            f"Could not inspect installed package directory: {directory}: {exc}"
        ) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise InstalledPackageIdentityError(
            f"Installed package directory is not a real directory: {directory}"
        )
    relative_directory = (
        b"."
        if directory == root
        else directory.relative_to(root)
        .as_posix()
        .encode("utf-8", errors="surrogateescape")
    )
    _entry_frame(
        digest,
        kind=b"directory",
        relative=relative_directory,
        metadata=before,
        content_sha256=b"",
    )
    for entry in entries:
        path = Path(entry.path)
        if ignore_python_cache and entry.name == "__pycache__":
            continue
        relative = (
            path.relative_to(root).as_posix().encode("utf-8", errors="surrogateescape")
        )
        try:
            admitted = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise InstalledPackageIdentityError(
                f"Could not inspect installed package entry: {path}: {exc}"
            ) from exc
        if stat.S_ISLNK(admitted.st_mode):
            raise InstalledPackageIdentityError(
                f"Installed package tree contains a symbolic link: {path}"
            )
        if stat.S_ISDIR(admitted.st_mode):
            _digest_directory(
                root,
                path,
                digest,
                ignore_python_cache=ignore_python_cache,
            )
        elif stat.S_ISREG(admitted.st_mode):
            data = _read_regular_file(path, admitted)
            _entry_frame(
                digest,
                kind=b"file",
                relative=relative,
                metadata=admitted,
                content_sha256=hashlib.sha256(data).digest(),
            )
        else:
            raise InstalledPackageIdentityError(
                f"Installed package tree contains a special entry: {path}"
            )
    try:
        after = directory.stat(follow_symlinks=False)
    except OSError as exc:
        raise InstalledPackageIdentityError(
            f"Could not re-admit installed package directory: {directory}: {exc}"
        ) from exc
    if _metadata_identity(before) != _metadata_identity(after):
        raise InstalledPackageIdentityError(
            f"Installed package directory changed while it was read: {directory}"
        )


def _tree_identity(
    root: Path, *, digest_domain: bytes, ignore_python_cache: bool = False
) -> InstalledPackageTreeIdentity:
    if not root.is_absolute():
        raise InstalledPackageIdentityError(
            f"Installed package root must be absolute: {root}"
        )
    try:
        state = root.lstat()
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise InstalledPackageIdentityError(
            f"Could not inspect installed package root: {root}: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != root
    ):
        raise InstalledPackageIdentityError(
            f"Installed package root must be one canonical real directory: {root}"
        )
    digest = hashlib.sha256(digest_domain)
    _digest_directory(
        root,
        root,
        digest,
        ignore_python_cache=ignore_python_cache,
    )
    return InstalledPackageTreeIdentity(root=root, sha256=digest.hexdigest())


def installed_package_tree_identity(root: Path) -> InstalledPackageTreeIdentity:
    """Bind an exact canonical tree by kind, path, mode, size, and file bytes.

    Traversal order and filesystem timestamps do not enter the digest. Symbolic
    links and non-regular, non-directory entries are rejected rather than
    followed or silently omitted.
    """

    return _tree_identity(root, digest_domain=_DIGEST_DOMAIN)


def installed_python_package_identity(root: Path) -> InstalledPackageTreeIdentity:
    """Bind installed Python package content while ignoring interpreter caches."""

    return _tree_identity(
        root,
        digest_domain=_PYTHON_DIGEST_DOMAIN,
        ignore_python_cache=True,
    )


def admit_installed_provider(
    group: str, name: str, *, label: str
) -> InstalledProviderV1:
    """Admit one package-level callable entry point and its exact provenance."""

    matches = tuple(
        item
        for item in importlib.metadata.entry_points(group=group)
        if item.name == name
    )
    if len(matches) != 1:
        detail = "not installed" if not matches else "selection is ambiguous"
        raise InstalledPackageIdentityError(f"{label} {detail}: {name!r}")
    entry_point = matches[0]
    matched = _PROVIDER_RE.fullmatch(entry_point.value)
    if matched is None:
        raise InstalledPackageIdentityError(f"{label} provider must be package-level")
    try:
        provider = entry_point.load()
        if not callable(provider):
            raise TypeError("entry point is not callable")
        root = Path(
            os.path.abspath(os.fspath(importlib.resources.files(matched["package"])))
        )
        package = installed_python_package_identity(root)
    except Exception as exc:
        raise InstalledPackageIdentityError(
            f"{label} provider could not be loaded: {name!r}"
        ) from exc
    distribution = getattr(entry_point, "dist", None)
    distribution_name = getattr(distribution, "name", None) or (
        distribution.metadata.get("Name") if distribution is not None else None
    )
    distribution_version = getattr(distribution, "version", None)
    if distribution_name is None or distribution_version is None:
        raise InstalledPackageIdentityError(
            f"{label} entry point has no distribution provenance"
        )
    admitted = InstalledProviderV1(
        provider,
        entry_point.value,
        str(distribution_name),
        str(distribution_version),
        package,
    )
    admitted.require_callables(label=label)
    return admitted


__all__ = (
    "InstalledPackageIdentityError",
    "InstalledPackageTreeIdentity",
    "InstalledProviderV1",
    "admit_installed_provider",
    "installed_package_tree_identity",
    "installed_python_package_identity",
)
