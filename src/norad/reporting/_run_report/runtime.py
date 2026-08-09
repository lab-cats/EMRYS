"""Pinned Quarto environment and subprocess lifecycle."""

from __future__ import annotations

import contextlib
import os
import shlex
import signal
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

from .inputs import _fail
from .models import QUARTO_VERSION, SAFE_RENDER_PATH


def _sanitized_tool_environment() -> dict[str, str]:
    """Return the small ambient environment allowed for pinned report tools."""

    return {
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "PATH": SAFE_RENDER_PATH,
        "TMPDIR": "/tmp",
        "TZ": "UTC",
    }
def _quarto_version(path: Path) -> str:
    try:
        result = subprocess.run(
            [str(path), "--version"],
            env=_sanitized_tool_environment(),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _fail(f"Could not execute {path} --version: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        _fail(f"Quarto version check failed: {detail}")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if lines != [QUARTO_VERSION]:
        _fail(
            f"Quarto reported {result.stdout.strip()!r}; expected exactly "
            f"{QUARTO_VERSION!r}"
        )
    return lines[0]
def _source_date_epoch(summary: Mapping[str, Any]) -> str:
    value = summary["generated_at"]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # schema validation should make this unreachable
        _fail(f"Could not derive fixed report time from generated_at: {exc}")
    return str(int(parsed.timestamp()))
def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Stop the complete Quarto process group and reap its direct process."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        if process.poll() is None:
            process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
def _run_quarto_process(
    command: Sequence[str],
    stage: Path,
    environment: Mapping[str, str],
    fail: Callable[[str], NoReturn],
) -> tuple[int, str, str]:
    """Own the shared timeout and process-group lifecycle for Quarto renders."""
    print("Quarto render command:")
    print(f"  {shlex.join(command)}")
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=stage,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_group(process)
            fail(f"Quarto render exceeded the 300-second timeout: {exc}")
    except OSError as exc:
        if process is not None:
            _terminate_process_group(process)
        fail(f"Could not execute Quarto render: {exc}")
    except BaseException:
        if process is not None:
            _terminate_process_group(process)
        raise
    assert process is not None and process.returncode is not None
    if stdout.strip():
        print(stdout.rstrip())
    return process.returncode, stdout, stderr
