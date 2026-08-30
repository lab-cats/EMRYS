"""Targeted coverage for shared input validation helpers."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
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


READERS = pytest.mark.parametrize(
    "reader", (_read_all, _read_prefix), ids=("all-bytes", "prefix")
)


def test_read_bytes_with_identity_returns_bound_file_and_allows_declared_empty(
    tmp_path: Path,
) -> None:
    source = tmp_path / "empty.lock"
    source.touch()

    data, identity = INPUTS.read_bytes_with_identity(
        source,
        "Empty lock",
        nonempty=False,
    )

    assert data == b""
    assert (identity.st_dev, identity.st_ino) == (
        source.stat().st_dev,
        source.stat().st_ino,
    )


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
    for invalid in (True, 0, -1):
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
