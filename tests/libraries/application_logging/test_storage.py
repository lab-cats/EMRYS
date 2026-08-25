from __future__ import annotations

import errno
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from emrys.libraries.application_logging import AttemptIdentity
from emrys.libraries.application_logging import storage


def identity() -> AttemptIdentity:
    return AttemptIdentity(
        scope_kind="run",
        scope_id="run-001",
        execution_attempt_id="attempt-001",
        entrypoint="emrys-run",
    )


def expected_path(root: Path) -> Path:
    return root / "run-run-001" / "attempt-001" / "emrys-run.jsonl"


def test_creates_protected_exclusive_file_and_persists_complete_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_write = os.write
    calls = 0

    def interrupted_short_write(descriptor: int, payload: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise InterruptedError(errno.EINTR, "retry")
        return real_write(descriptor, payload[:2] if calls == 2 else payload)

    monkeypatch.setattr(storage, "_write", interrupted_short_write)
    root = tmp_path / "logs" / "application"
    log = storage.create_application_log_file(root, identity())
    log.write_bytes(b'{"event":"opened"}\n')
    log.synchronize()
    log.close()
    log.close()

    path = expected_path(root)
    assert log.path == path
    assert path.read_bytes() == b'{"event":"opened"}\n'
    assert calls == 3
    for directory in (root, path.parent.parent, path.parent):
        assert stat.S_IMODE(directory.stat().st_mode) & ~storage.DIRECTORY_MODE == 0
    assert stat.S_IMODE(path.stat().st_mode) & ~storage.FILE_MODE == 0


def test_rejects_existing_attempt_without_adoption_or_mutation(tmp_path: Path) -> None:
    root = tmp_path / "application"
    first = storage.create_application_log_file(root, identity())
    first.write_bytes(b"first\n")
    first.close()

    with pytest.raises(
        storage.ApplicationLogStorageError, match="Attempt log already exists"
    ):
        storage.create_application_log_file(root, identity())

    assert expected_path(root).read_bytes() == b"first\n"


@pytest.mark.parametrize("target", ["root", "ancestor", "scope"])
def test_rejects_symlink_in_managed_path(tmp_path: Path, target: str) -> None:
    destination = tmp_path / "destination"
    destination.mkdir(mode=storage.DIRECTORY_MODE)
    root = tmp_path / "application"
    selected_root = root
    if target == "root":
        root.symlink_to(destination, target_is_directory=True)
    elif target == "ancestor":
        parent = tmp_path / "linked-parent"
        parent.symlink_to(destination, target_is_directory=True)
        selected_root = parent / "application"
    else:
        root.mkdir(mode=storage.DIRECTORY_MODE)
        (root / "run-run-001").symlink_to(destination, target_is_directory=True)

    with pytest.raises(storage.ApplicationLogStorageError):
        storage.create_application_log_file(selected_root, identity())

    assert list(destination.iterdir()) == []


def test_rejects_insecure_existing_root_without_changing_it(tmp_path: Path) -> None:
    root = tmp_path / "application"
    root.mkdir(mode=0o755)

    with pytest.raises(storage.ApplicationLogStorageError, match="Insecure"):
        storage.create_application_log_file(root, identity())

    assert stat.S_IMODE(root.stat().st_mode) == 0o755


@pytest.mark.parametrize("change", ["replace", "missing", "mode"])
def test_rejects_pinned_path_identity_or_mode_change(
    tmp_path: Path, change: str
) -> None:
    log = storage.create_application_log_file(tmp_path / "application", identity())
    original = log.path
    if change in {"replace", "missing"}:
        displaced = original.with_name("displaced.jsonl")
        original.rename(displaced)
        if change == "replace":
            original.write_bytes(b"replacement\n")
            original.chmod(storage.FILE_MODE)
    else:
        original.chmod(0o644)

    with pytest.raises(
        storage.ApplicationLogStorageError,
        match="Pinned log path changed|Unavailable pinned log path",
    ):
        log.write_bytes(b"must-not-be-written\n")
    log.close()

    if change == "replace":
        assert displaced.read_bytes() == b""
        assert original.read_bytes() == b"replacement\n"
    elif change == "missing":
        assert displaced.read_bytes() == b""
    else:
        assert original.read_bytes() == b""


@pytest.mark.parametrize("failure", ["zero", "error", "after-prefix"])
def test_write_failure_preserves_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    real_write = os.write
    calls = 0

    def failing_write(descriptor: int, payload: bytes) -> int:
        nonlocal calls
        calls += 1
        if failure == "zero":
            return 0
        if failure == "after-prefix" and calls == 1:
            return real_write(descriptor, payload[:3])
        raise OSError(errno.ENOSPC, "full")

    monkeypatch.setattr(storage, "_write", failing_write)
    log = storage.create_application_log_file(tmp_path / "application", identity())

    with pytest.raises(storage.ApplicationLogStorageError):
        log.write_bytes(b"partial-event\n")
    log.close()

    assert log.path.read_bytes() == (b"par" if failure == "after-prefix" else b"")


def test_sync_failure_preserves_written_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_fsync = os.fsync

    def fail_file_sync(descriptor: int) -> None:
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(errno.EIO, "sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr(storage.os, "fsync", fail_file_sync)
    log = storage.create_application_log_file(tmp_path / "application", identity())
    log.write_bytes(b"partial\n")

    with pytest.raises(
        storage.ApplicationLogStorageError, match="Could not synchronize"
    ):
        log.synchronize()
    log.close()

    assert log.path.read_bytes() == b"partial\n"


def test_interrupted_creation_closes_accumulated_pins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_pin = storage._pin
    original_close_all = storage._close_all
    closed: list[int] = []

    def interrupt_file_pin(
        path: Path, descriptor: int, *, directory: bool, secure: bool = True
    ):
        if not directory:
            raise KeyboardInterrupt
        return original_pin(path, descriptor, directory=directory, secure=secure)

    def record_cleanup(pins: list[storage._Pin]) -> None:
        closed.extend(pin.fd for pin in pins)
        original_close_all(pins)

    monkeypatch.setattr(storage, "_pin", interrupt_file_pin)
    monkeypatch.setattr(storage, "_close_all", record_cleanup)
    with pytest.raises(KeyboardInterrupt):
        storage.create_application_log_file(tmp_path / "application", identity())
    assert closed
    for descriptor in closed:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_closed_file_rejects_writes_and_sync(tmp_path: Path) -> None:
    log = storage.create_application_log_file(tmp_path / "application", identity())
    log.close()

    with pytest.raises(storage.ApplicationLogStorageError, match="already closed"):
        log.write_bytes(b"event\n")
    with pytest.raises(storage.ApplicationLogStorageError, match="already closed"):
        log.synchronize()


def test_close_reports_descriptor_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = storage.create_application_log_file(tmp_path / "application", identity())
    real_close = os.close
    failed: list[int] = []

    def fail_once(descriptor: int) -> None:
        if not failed:
            failed.append(descriptor)
            raise OSError(errno.EIO, "close failed")
        real_close(descriptor)

    with monkeypatch.context() as selected:
        selected.setattr(storage.os, "close", fail_once)
        with pytest.raises(storage.ApplicationLogStorageError, match="close"):
            log.close()
    real_close(failed[0])


@pytest.mark.parametrize(
    "root",
    [Path("relative"), Path("/"), Path("//"), Path("/tmp/../application")],
)
def test_rejects_unsafe_roots(root: Path) -> None:
    with pytest.raises(storage.ApplicationLogStorageError):
        storage.create_application_log_file(root, identity())


def test_rejects_invalid_structural_inputs(tmp_path: Path) -> None:
    with pytest.raises(storage.ApplicationLogStorageError):
        storage.create_application_log_file("not-a-path", identity())  # type: ignore[arg-type]
    for invalid in (
        object(),
        SimpleNamespace(relative_parts=("../escape", "attempt", "event.jsonl")),
    ):
        with pytest.raises(storage.ApplicationLogStorageError):
            storage.create_application_log_file(tmp_path / "application", invalid)
