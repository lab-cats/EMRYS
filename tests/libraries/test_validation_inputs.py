"""Targeted coverage for shared input validation helpers."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from emrys.libraries import validation as REPORT
from emrys.libraries.validation import inputs as INPUTS


def test_require_executable_rejects_non_executable_file(tmp_path: Path) -> None:
    tool = tmp_path / "not_executable.sh"
    tool.write_text("#!/usr/bin/env bash\n")
    tool.chmod(0o644)

    with pytest.raises(REPORT.ValidationError, match="is not executable"):
        INPUTS.require_executable(tool, "Tool")


def test_read_bytes_rejects_unreadable_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.txt"
    source.write_text("fixture")

    def fail_open(*_args: object, **_kwargs: object) -> int:
        raise OSError("inject unreadable input")

    monkeypatch.setattr(INPUTS.os, "open", fail_open)

    with pytest.raises(REPORT.ValidationError, match="is unavailable"):
        INPUTS.read_bytes(source, "Unreadable file")


def test_read_bytes_rejects_mutated_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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
        INPUTS.read_bytes(source, "Mutable fixture")


def test_read_bytes_rejects_path_replacement_after_open(
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
        INPUTS.read_bytes(source, "Replaced fixture")


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
