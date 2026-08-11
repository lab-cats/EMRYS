"""Targeted coverage for shared input validation helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from norad.libraries import validation as REPORT
from norad.libraries.validation import inputs as INPUTS


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

    def fail_read_bytes(self: Path) -> bytes:
        raise OSError("inject unreadable input")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    with pytest.raises(REPORT.ValidationError, match="is unavailable"):
        INPUTS.read_bytes(source, "Unreadable file")


def test_read_bytes_rejects_mutated_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "input.txt"
    source.write_text("fixture")
    before = INPUTS.regular_snapshot(source, "Mutable fixture")
    after = INPUTS.Snapshot(
        before.device,
        before.inode,
        before.size + 1,
        before.mtime_ns + 1,
    )
    snapshots = iter((before, after))
    monkeypatch.setattr(
        INPUTS,
        "regular_snapshot",
        lambda *_args, **_kwargs: next(snapshots),
    )

    with pytest.raises(REPORT.ValidationError, match="changed while read"):
        INPUTS.read_bytes(source, "Mutable fixture")


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
