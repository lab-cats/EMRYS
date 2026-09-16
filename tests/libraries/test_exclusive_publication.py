"""Ownership and durability boundaries shared by reporting and maintenance."""

from __future__ import annotations

import os
import signal
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from emrys.libraries import exclusive_publication as publication


class ClaimError(RuntimeError):
    pass


def test_claim_and_staged_writer_handle_short_writes_and_sync_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claim = tmp_path / "maintenance.lock"
    payload = b"unique ownership token\n"
    writes = os.write
    fsync = os.fsync
    synchronized: list[str] = []

    def sync(descriptor: int) -> None:
        synchronized.append(
            "directory" if stat.S_ISDIR(os.fstat(descriptor).st_mode) else "file"
        )
        fsync(descriptor)

    monkeypatch.setattr(os, "write", lambda fd, data: writes(fd, data[:3]))
    monkeypatch.setattr(os, "fsync", sync)
    owned = publication.acquire_lock(claim, payload, ClaimError)
    assert claim.read_bytes() == payload
    assert synchronized == ["file", "directory"]
    assert stat.S_IMODE(claim.stat().st_mode) == 0o600
    staged = tmp_path / "staged"
    publication.write_bytes_exclusive(staged, payload)
    assert staged.read_bytes() == payload
    with pytest.raises(FileExistsError):
        publication.write_bytes_exclusive(staged, b"replacement")
    publication.release_lock(claim, owned, payload, ClaimError)
    assert not claim.exists()
    assert synchronized == ["file", "directory", "file", "directory"]


@pytest.mark.parametrize("retain", (False, True))
@pytest.mark.parametrize("replaced", (False, True))
def test_interrupted_acquisition_never_removes_another_owners_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, retain: bool, replaced: bool
) -> None:
    claim = tmp_path / "maintenance.lock"

    def interrupt(_descriptor: int, _payload: bytes) -> int:
        if replaced:
            claim.unlink()
            claim.write_bytes(b"other owner\n")
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "write", interrupt)
    expected = ClaimError if replaced and not retain else KeyboardInterrupt
    with pytest.raises(expected):
        publication.acquire_lock(claim, b"mine\n", ClaimError, retain_on_failure=retain)
    if replaced:
        assert claim.read_bytes() == b"other owner\n"
    else:
        assert claim.exists() is retain
        if retain:
            assert claim.read_bytes() == b""


@pytest.mark.parametrize("retain", (False, True))
@pytest.mark.parametrize("failure", ("write", "file", "directory"))
def test_acquisition_failure_has_explicit_retention_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, retain: bool, failure: str
) -> None:
    claim = tmp_path / "maintenance.lock"
    real_sync = os.fsync
    failed = False

    def sync(descriptor: int) -> None:
        nonlocal failed
        kind = "directory" if stat.S_ISDIR(os.fstat(descriptor).st_mode) else "file"
        if kind == failure and not failed:
            failed = True
            raise OSError(f"injected {failure} failure")
        real_sync(descriptor)

    monkeypatch.setattr(os, "fsync", sync)
    if failure == "write":
        monkeypatch.setattr(os, "write", lambda *_args: 0)
    with pytest.raises(ClaimError, match="Could not write publication lock"):
        publication.acquire_lock(claim, b"mine\n", ClaimError, retain_on_failure=retain)
    assert claim.exists() is retain
    if retain:
        assert claim.read_bytes() == (b"" if failure == "write" else b"mine\n")
        with pytest.raises(ClaimError, match="already exists"):
            publication.acquire_lock(claim, b"retry\n", ClaimError)


@pytest.mark.parametrize("changed", ("replaced", "content", "symlink", "fifo"))
def test_competing_claim_and_changed_release_preserve_existing_owner(
    tmp_path: Path, changed: str
) -> None:
    claim = tmp_path / "maintenance.lock"
    owned = publication.acquire_lock(claim, b"mine\n", ClaimError)
    with pytest.raises(ClaimError, match="already exists"):
        publication.acquire_lock(claim, b"competitor\n", ClaimError)
    assert claim.read_bytes() == b"mine\n"
    if changed == "content":
        claim.write_bytes(b"changed\n")
    else:
        claim.rename(tmp_path / "original")
        if changed == "symlink":
            target = tmp_path / "target"
            target.write_bytes(b"other owner\n")
            claim.symlink_to(target)
        elif changed == "fifo":
            os.mkfifo(claim)
        else:
            claim.write_bytes(b"mine\n")
    before = claim.lstat()
    with pytest.raises(ClaimError, match="changed|Could not release"):
        publication.release_lock(claim, owned, b"mine\n", ClaimError)
    assert publication.stat_identity(claim.lstat()) == publication.stat_identity(before)


def test_symlink_parent_is_refused_without_creating_a_claim(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ClaimError, match="Could not acquire"):
        publication.acquire_lock(alias / "maintenance.lock", b"mine\n", ClaimError)
    assert not list(real.iterdir())


@pytest.mark.parametrize("retain", (False, True))
def test_parent_replacement_during_acquisition_never_cleans_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, retain: bool
) -> None:
    parent = tmp_path / "runtime"
    parent.mkdir()
    moved = tmp_path / "moved"
    claim = parent / "maintenance.lock"
    writes = os.write

    def replace_parent(descriptor: int, payload: bytes) -> int:
        parent.rename(moved)
        parent.mkdir()
        claim.write_bytes(b"other owner\n")
        return writes(descriptor, payload)

    monkeypatch.setattr(os, "write", replace_parent)
    with pytest.raises(ClaimError, match="parent changed"):
        publication.acquire_lock(claim, b"mine\n", ClaimError, retain_on_failure=retain)
    assert claim.read_bytes() == b"other owner\n"
    assert (moved / claim.name).exists() is retain


def test_release_directory_sync_failure_is_reported_after_owned_unlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claim = tmp_path / "maintenance.lock"
    owned = publication.acquire_lock(claim, b"mine\n", ClaimError)

    def fail(_descriptor: int) -> None:
        raise OSError("directory sync failed")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(ClaimError, match="directory sync failed"):
        publication.release_lock(claim, owned, b"mine\n", ClaimError)
    assert not claim.exists()


def test_process_termination_leaves_a_blocking_claim(tmp_path: Path) -> None:
    claim = tmp_path / "maintenance.lock"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os,signal,sys; from pathlib import Path; "
            "from emrys.libraries.exclusive_publication import acquire_lock; "
            "acquire_lock(Path(sys.argv[1]),b'owner\\n',RuntimeError,retain_on_failure=True); "
            "os.kill(os.getpid(),signal.SIGTERM)",
            str(claim),
        ],
        check=False,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == -signal.SIGTERM, result.stderr
    assert claim.read_bytes() == b"owner\n"
    with pytest.raises(ClaimError, match="already exists"):
        publication.acquire_lock(claim, b"next\n", ClaimError)
