"""Exclusive, descriptor-pinned storage for one application log."""

from __future__ import annotations

import errno
import os
import stat
from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path

DIRECTORY_MODE = 0o700
FILE_MODE = 0o600
_write = os.write  # Private seam for EINTR and short-write tests.
_identity = attrgetter("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")


class ApplicationLogStorageError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _Pin:
    path: Path
    fd: int
    identity: tuple[int, int, int, int, int]


@dataclass(slots=True)
class ApplicationLogFile:
    path: Path
    _pins: tuple[_Pin, ...]
    _closed: bool = False

    def write_bytes(self, payload: bytes) -> None:
        self._require_open()
        self._verify()
        descriptor = self._pins[-1].fd
        offset = 0
        while offset < len(payload):
            try:
                written = _write(descriptor, payload[offset:])
            except OSError as exc:
                if exc.errno == errno.EINTR:
                    continue
                raise self._error("write", exc) from exc
            if written <= 0:
                raise ApplicationLogStorageError("Log write made no progress")
            offset += written
        self._verify()

    def synchronize(self) -> None:
        self._require_open()
        self._verify()
        try:
            os.fsync(self._pins[-1].fd)
        except OSError as exc:
            raise self._error("synchronize", exc) from exc
        self._verify()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        first_error: OSError | None = None
        for pin in reversed(self._pins):
            try:
                os.close(pin.fd)
            except OSError as exc:
                first_error = first_error or exc
        if first_error:
            raise self._error("close", first_error) from first_error

    def _require_open(self) -> None:
        if self._closed:
            raise ApplicationLogStorageError("Application log is already closed")

    def _verify(self) -> None:
        for pin in self._pins:
            try:
                states = (
                    os.fstat(pin.fd),
                    os.stat(pin.path, follow_symlinks=False),
                )
            except OSError as exc:
                raise ApplicationLogStorageError(
                    f"Unavailable pinned log path: {pin.path}"
                ) from exc
            if any(_identity(observed) != pin.identity for observed in states):
                raise ApplicationLogStorageError(f"Pinned log path changed: {pin.path}")

    def _error(self, action: str, exc: OSError) -> ApplicationLogStorageError:
        return ApplicationLogStorageError(f"Could not {action} application log: {exc}")


def create_application_log_file(root: Path, identity: object) -> ApplicationLogFile:
    _validate_root(root)
    pins: list[_Pin] = []
    try:
        pins.append(_open_root(root))
        scope_name, attempt_name, file_name = _relative_parts(identity)
        path = root
        for name, exclusive in ((scope_name, False), (attempt_name, True)):
            path /= name
            pins.append(_open_dir(pins[-1].fd, name, path, exclusive, True))
        log_path = path / file_name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
        try:
            descriptor = os.open(file_name, flags, FILE_MODE, dir_fd=pins[-1].fd)
        except FileExistsError as exc:
            raise ApplicationLogStorageError("Log file already exists") from exc
        try:
            pins.append(_pin(log_path, descriptor, directory=False))
        except BaseException:
            os.close(descriptor)
            raise
        os.fsync(pins[-2].fd)
        result = ApplicationLogFile(log_path, tuple(pins))
        result._verify()
        pins.clear()
        return result
    except ApplicationLogStorageError:
        _close_all(pins)
        raise
    except OSError as exc:
        _close_all(pins)
        raise ApplicationLogStorageError(
            f"Could not initialize application log: {exc}"
        ) from exc
    except BaseException:
        _close_all(pins)
        raise


def _open_root(root: Path) -> _Pin:
    descriptor = os.open(os.sep, _dir_flags())
    path = Path(os.sep)
    try:
        parts = root.parts[1:]
        for index, name in enumerate(parts):
            path /= name
            child = _open_dir(descriptor, name, path, False, index == len(parts) - 1)
            os.close(descriptor)
            descriptor = child.fd
        return child
    except BaseException:
        os.close(descriptor)
        raise


def _open_dir(
    parent: int,
    name: str,
    path: Path,
    exclusive: bool = False,
    secure: bool = False,
) -> _Pin:
    try:
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        secure = True
        try:
            os.mkdir(name, DIRECTORY_MODE, dir_fd=parent)
            os.fsync(parent)
        except FileExistsError as exc:
            if exclusive:
                raise ApplicationLogStorageError("Attempt log already exists") from exc
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    else:
        if exclusive:
            raise ApplicationLogStorageError("Attempt log already exists")
    _require(before, path, directory=True, secure=False)
    descriptor = os.open(name, _dir_flags(), dir_fd=parent)
    try:
        pin = _pin(path, descriptor, directory=True, secure=secure)
        if pin.identity != _identity(before):
            raise ApplicationLogStorageError("Log path changed during admission")
        return pin
    except BaseException:
        os.close(descriptor)
        raise


def _pin(path: Path, descriptor: int, *, directory: bool, secure: bool = True) -> _Pin:
    observed = os.fstat(descriptor)
    _require(observed, path, directory=directory, secure=secure)
    return _Pin(path, descriptor, _identity(observed))


def _require(
    observed: os.stat_result, path: Path, *, directory: bool, secure: bool
) -> None:
    expected_type = stat.S_IFDIR if directory else stat.S_IFREG
    if stat.S_IFMT(observed.st_mode) != expected_type:
        raise ApplicationLogStorageError(
            f"Application-log path has the wrong type: {path}"
        )
    mode = DIRECTORY_MODE if directory else FILE_MODE
    if secure and (
        observed.st_uid != os.getuid() or stat.S_IMODE(observed.st_mode) & ~mode
    ):
        raise ApplicationLogStorageError(f"Insecure application-log path: {path}")


def _validate_root(root: object) -> None:
    if (
        not isinstance(root, Path)
        or not root.is_absolute()
        or root.anchor != os.sep
        or root == Path(os.sep)
        or any(part in {".", ".."} for part in root.parts)
    ):
        raise ApplicationLogStorageError(
            "Application-log root must be an absolute safe path"
        )
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ApplicationLogStorageError(
            "Required no-follow directory admission is unavailable"
        )


def _relative_parts(identity: object) -> tuple[str, str, str]:
    try:
        parts = identity.relative_parts  # type: ignore[attr-defined]
    except Exception as exc:
        raise ApplicationLogStorageError("Application-log identity is invalid") from exc
    if (
        not isinstance(parts, tuple)
        or len(parts) != 3
        or any(
            not isinstance(part, str)
            or not part
            or part in {".", ".."}
            or "/" in part
            or "\\" in part
            or not part.isprintable()
            for part in parts
        )
    ):
        raise ApplicationLogStorageError("Application-log identity is invalid")
    return parts


def _dir_flags() -> int:
    return os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW


def _close_all(pins: list[_Pin]) -> None:
    for pin in reversed(pins):
        try:
            os.close(pin.fd)
        except OSError:
            pass
