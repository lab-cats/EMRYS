"""Targeted coverage for shared input validation helpers."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from emrys.libraries import validation as REPORT
from emrys.libraries.validation import inputs as INPUTS

Reader = Callable[[Path, str], bytes]


def _read_all(path: Path, label: str) -> bytes:
    return INPUTS.read_bytes(path, label)


def _read_prefix(path: Path, label: str) -> bytes:
    return INPUTS.read_prefix(path, label, 4)


def _read_sha256(path: Path, label: str) -> bytes:
    return INPUTS.sha256_with_identity(path, label)[0].encode()


def _read_suffix(path: Path, label: str) -> bytes:
    return INPUTS.read_suffix_with_identity(path, label, 4)[0]


READERS = pytest.mark.parametrize(
    "reader",
    (_read_all, _read_prefix, _read_sha256, _read_suffix),
    ids=("all-bytes", "prefix", "sha256", "suffix"),
)


@pytest.mark.parametrize("content", (b"", b"AB", b"prefix-ABCD"))
def test_suffix_reads_only_bounded_trailing_bytes(tmp_path, monkeypatch, content):
    source = tmp_path / "stream"
    source.write_bytes(content)
    original = INPUTS.os.read
    offsets = []

    def read(descriptor, size):
        offsets.append((os.lseek(descriptor, 0, os.SEEK_CUR), size))
        return original(descriptor, min(size, 1))

    monkeypatch.setattr(INPUTS.os, "read", read)
    data, identity = INPUTS.read_suffix_with_identity(source, "Stream", 4)

    assert data == content[-4:]
    assert identity.st_size == len(content)
    assert offsets[0] == (max(0, len(content) - 4), 4)
    assert all(size <= 4 for _, size in offsets)


def test_suffix_rejects_symlinks_nonregular_files_and_invalid_lengths(tmp_path):
    source = tmp_path / "stream"
    source.write_bytes(b"fixture")
    link = tmp_path / "alias"
    link.symlink_to(source)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    for path in (link, fifo, tmp_path):
        with pytest.raises(REPORT.ValidationError, match="regular non-symlink"):
            INPUTS.read_suffix_with_identity(path, "Stream", 4)
    for length in (None, True, 0, -1, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            INPUTS.read_suffix_with_identity(source, "Stream", length)


@pytest.mark.parametrize("content", [b"", b"bound-prefix-and-unread-tail"])
def test_read_bytes_with_identity_returns_bound_file_and_allows_declared_empty(
    tmp_path: Path,
    content: bytes,
) -> None:
    source = tmp_path / "empty.lock"
    source.write_bytes(content)

    data, identity = INPUTS.read_bytes_with_identity(
        source,
        "Empty lock",
        nonempty=False,
        limit=5,
    )

    assert data == content[:5]
    assert identity.st_size == len(content)
    assert (identity.st_dev, identity.st_ino) == (
        source.stat().st_dev,
        source.stat().st_ino,
    )


def test_sha256_with_identity_streams_bound_file_and_allows_declared_empty(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.bin"
    source.write_bytes(b"fixture")

    digest, identity = INPUTS.sha256_with_identity(source, "Input")

    assert digest == hashlib.sha256(b"fixture").hexdigest()
    assert identity.st_size == len(b"fixture")

    source.write_bytes(b"")
    digest, identity = INPUTS.sha256_with_identity(
        source,
        "Empty input",
        nonempty=False,
    )
    assert digest == hashlib.sha256(b"").hexdigest()
    assert identity.st_size == 0


def test_directory_entries_with_identity_lists_one_real_stable_directory(
    tmp_path: Path,
) -> None:
    (tmp_path / "b").touch()
    (tmp_path / "a").touch()

    entries, identity = INPUTS.directory_entries_with_identity(tmp_path, "Directory")

    assert entries == ("a", "b")
    assert (identity.st_dev, identity.st_ino) == (
        tmp_path.stat().st_dev,
        tmp_path.stat().st_ino,
    )
    alias = tmp_path.with_name("directory-alias")
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(REPORT.ValidationError, match="is unavailable"):
        INPUTS.directory_entries_with_identity(alias, "Directory")


def test_directory_entries_requires_no_follow_support(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(INPUTS.os, "O_NOFOLLOW", None)

    with pytest.raises(REPORT.ValidationError, match="symbolic-link protection"):
        INPUTS.directory_entries_with_identity(tmp_path, "Directory")


@pytest.mark.parametrize("count", (3, 10))
def test_directory_entry_limit_stops_enumeration_and_closes_iterator(
    tmp_path, monkeypatch, count
):
    for index in range(count):
        (tmp_path / str(index)).touch()
    original = INPUTS.os.scandir
    observed = []
    closed = []

    @contextmanager
    def scan(descriptor):
        try:
            with original(descriptor) as entries:

                def limited():
                    for entry in entries:
                        observed.append(entry.name)
                        yield entry

                yield limited()
        finally:
            closed.append(True)

    monkeypatch.setattr(INPUTS.os, "scandir", scan)
    if count == 3:
        entries, _ = INPUTS.directory_entries_with_identity(
            tmp_path, "Bounded directory", limit=3
        )
        assert entries == ("0", "1", "2")
    else:
        with pytest.raises(REPORT.ValidationError, match="3-entry inspection limit"):
            INPUTS.directory_entries_with_identity(
                tmp_path, "Bounded directory", limit=3
            )
    assert len(observed) == min(count, 4)
    assert closed == [True]


def test_bounded_directory_still_rejects_replacement(tmp_path, monkeypatch):
    directory = tmp_path / "directory"
    directory.mkdir()
    (directory / "one").touch()
    original = INPUTS.os.scandir

    @contextmanager
    def scan(descriptor):
        with original(descriptor) as entries:
            yield entries
        directory.rename(tmp_path / "old")
        directory.mkdir()

    monkeypatch.setattr(INPUTS.os, "scandir", scan)
    with pytest.raises(REPORT.ValidationError, match="changed while inspected"):
        INPUTS.directory_entries_with_identity(directory, "Bounded directory", limit=2)


def test_directory_entries_rejects_path_replacement_during_inspection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "directory"
    held = tmp_path / "held"
    directory.mkdir()
    (directory / "entry").touch()
    real_listdir = INPUTS.os.listdir

    def list_then_replace(descriptor: int) -> list[str]:
        entries = real_listdir(descriptor)
        directory.rename(held)
        directory.mkdir()
        return entries

    monkeypatch.setattr(INPUTS.os, "listdir", list_then_replace)

    with pytest.raises(REPORT.ValidationError, match="changed while inspected"):
        INPUTS.directory_entries_with_identity(directory, "Directory")


def test_require_executable_rejects_non_executable_file(tmp_path: Path) -> None:
    tool = tmp_path / "not_executable.sh"
    tool.write_text("#!/usr/bin/env bash\n")
    tool.chmod(0o644)

    with pytest.raises(REPORT.ValidationError, match="is not executable"):
        INPUTS.require_executable(tool, "Tool")


@READERS
def test_read_rejects_unreadable_file(
    reader: Reader,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.txt"
    source.write_text("fixture")

    def fail_open(*_args: object, **_kwargs: object) -> int:
        raise OSError("inject unreadable input")

    monkeypatch.setattr(INPUTS.os, "open", fail_open)

    with pytest.raises(REPORT.ValidationError, match="is unavailable"):
        reader(source, "Unreadable file")


@READERS
def test_read_rejects_mutated_source(
    reader: Reader, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "input.txt"
    source.write_text("fixture")
    real_read = INPUTS.os.read
    mutated = False

    def read_then_mutate(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = real_read(descriptor, size)
        if data and not mutated:
            mutated = True
            source.write_bytes(b"mutated fixture")
        return data

    monkeypatch.setattr(INPUTS.os, "read", read_then_mutate)

    with pytest.raises(REPORT.ValidationError, match="changed while read"):
        reader(source, "Mutable fixture")


@READERS
def test_read_rejects_path_replacement_after_open(
    reader: Reader,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.txt"
    held = tmp_path / "held.txt"
    replacement = tmp_path / "replacement.txt"
    source.write_text("admitted")
    replacement.write_text("foreign")
    real_open = INPUTS.os.open
    replaced = False

    def open_then_replace(
        path: str | bytes | os.PathLike[str],
        flags: int,
    ) -> int:
        nonlocal replaced
        descriptor = real_open(path, flags)
        if Path(path) == source and not replaced:
            replaced = True
            source.rename(held)
            replacement.rename(source)
        return descriptor

    monkeypatch.setattr(INPUTS.os, "open", open_then_replace)

    with pytest.raises(
        REPORT.ValidationError,
        match="pathname changed while read",
    ):
        reader(source, "Replaced fixture")


@READERS
def test_read_rejects_path_metadata_change_after_final_descriptor_snapshot(
    reader: Reader,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.txt"
    source.write_text("admitted")
    real_stat = INPUTS.os.stat
    path_checks = 0

    def stat_then_change(
        path: str | bytes | os.PathLike[str],
        *args: object,
        **kwargs: object,
    ) -> os.stat_result:
        nonlocal path_checks
        if Path(path) == source and kwargs.get("follow_symlinks") is False:
            path_checks += 1
            if path_checks == 2:
                source.chmod(0o600)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(INPUTS.os, "stat", stat_then_change)

    with pytest.raises(REPORT.ValidationError, match="pathname changed while read"):
        reader(source, "Metadata-mutated fixture")


def test_read_prefix_handles_short_descriptor_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "input.txt"
    source.write_bytes(b"ABCDremainder")
    real_read = INPUTS.os.read
    requests: list[int] = []

    def one_byte_read(descriptor: int, size: int) -> bytes:
        requests.append(size)
        return real_read(descriptor, 1)

    monkeypatch.setattr(INPUTS.os, "read", one_byte_read)

    assert INPUTS.read_prefix(source, "Short-read fixture", 4) == b"ABCD"
    assert requests == [4, 3, 2, 1]


def test_read_prefix_rejects_symlinks_and_invalid_lengths(tmp_path: Path) -> None:
    source = tmp_path / "input.txt"
    source.write_bytes(b"fixture")
    link = tmp_path / "input-link.txt"
    link.symlink_to(source)

    with pytest.raises(REPORT.ValidationError, match="regular non-symlink"):
        INPUTS.read_prefix(link, "Linked prefix fixture", 4)
    for invalid in (None, True, 0, -1):
        with pytest.raises(ValueError, match="positive integer"):
            INPUTS.read_prefix(source, "Invalid prefix fixture", invalid)


def test_integer_stdout_rejects_failed_process() -> None:
    result = subprocess.CompletedProcess(
        ["fake"], returncode=1, stdout="5", stderr="failed"
    )

    with pytest.raises(REPORT.ValidationError, match="failed"):
        INPUTS.integer_stdout(result, "Example command")


def test_integer_stdout_rejects_non_integer_output() -> None:
    result = subprocess.CompletedProcess(
        ["fake"], returncode=0, stdout="not-a-number", stderr=""
    )

    with pytest.raises(REPORT.ValidationError, match="noninteger count"):
        INPUTS.integer_stdout(result, "Example command")


def test_integer_stdout_rejects_negative_output() -> None:
    result = subprocess.CompletedProcess(["fake"], returncode=0, stdout="-9", stderr="")

    with pytest.raises(REPORT.ValidationError, match="negative count"):
        INPUTS.integer_stdout(result, "Example command")


def test_integer_stdout_accepts_positive_count() -> None:
    result = subprocess.CompletedProcess(["fake"], returncode=0, stdout="12", stderr="")

    assert INPUTS.integer_stdout(result, "Example command") == 12
