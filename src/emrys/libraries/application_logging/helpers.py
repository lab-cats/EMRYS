"""Sensitive fields, Slurm context, and failure output."""

from __future__ import annotations

import json
import os
import sys
import time
import unicodedata
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

_MAX_FIELD_BYTES = 16 * 1024
_UNSAFE_TEXT_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})
_STATUS_STYLES = {
    **dict.fromkeys(
        "admitted complete completed pass ready succeeded valid yes".split(),
        "bold green",
    ),
    **dict.fromkeys("blocked fail failed invalid".split(), "bold red"),
    **dict.fromkeys(
        "incomplete pending planned running unknown unverified".split(),
        "bold yellow",
    ),
    "not admitted": "bold red",
    "not ready": "bold red",
    **dict.fromkeys(("not applicable", "no", "none"), "dim"),
}


def _console(file: Any = None) -> Console:
    stream = sys.stderr if file is None else file
    terminal = (
        bool(getattr(stream, "isatty", lambda: False)())
        and "NO_COLOR" not in os.environ
        and os.environ.get("TERM") != "dumb"
    )
    return Console(
        file=stream,
        force_terminal=terminal,
        no_color=not terminal,
        markup=False,
        highlight=False,
        soft_wrap=True,
    )


def console_print(
    message: str, *, style: str | None = None, file: Any = None, end: str = "\n"
) -> None:
    """Print literal human text, styling only an eligible terminal."""
    _console(file).print(message, style=style, end=end)


def console_field(
    label: str,
    value: object,
    *,
    file: Any = None,
    value_style: str | None = None,
    indent: str = "",
) -> None:
    """Print one literal label/value pair with a stable visual hierarchy."""
    text = Text.assemble(
        (f"{indent}{label}: ", "bold cyan"),
        (str(value), value_style),
    )
    _console(file).print(text)


def console_status(
    label: str, value: object, *, file: Any = None, indent: str = ""
) -> None:
    """Print a field whose value has a restrained semantic status style."""
    style = _STATUS_STYLES.get(str(value).strip().casefold(), "bold")
    console_field(label, value, file=file, value_style=style, indent=indent)


@contextmanager
def phase_progress(
    message: str,
    *,
    file: Any = None,
    on_complete: Callable[[str, float | None, str], None] | None = None,
) -> Iterator[None]:
    """Show the current phase and elapsed time without estimating completion."""
    started = None
    with suppress(Exception):
        started = time.monotonic()
    progress = None
    with suppress(Exception):
        console = _console(file)
        live = console.is_terminal and not console.no_color
        progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}", markup=False),
            TimeElapsedColumn(),
            console=console,
            transient=True,
            disable=not live,
            redirect_stdout=True,
            redirect_stderr=True,
        )
        if not live:
            console.print(f"{message}...")
        progress.add_task(message, total=None)
        progress.start()
    outcome = "complete"
    try:
        yield
    except BaseException:
        outcome = "interrupted or failed"
        raise
    finally:
        with suppress(Exception):
            if progress is not None:
                progress.stop()
        elapsed = None
        with suppress(Exception):
            if started is not None:
                elapsed = time.monotonic() - started
        with suppress(Exception):
            if on_complete is not None:
                on_complete(message, elapsed, outcome)
        with suppress(Exception):
            duration = "elapsed unavailable"
            if elapsed is not None:
                seconds = int(elapsed)
                duration = f"{seconds // 60}m {seconds % 60:02d}s"
            console_print(
                f"{message}: {outcome} ({duration})",
                style="green" if outcome == "complete" else "red",
                file=file,
            )


class LogValueError(ValueError):
    """A value cannot be represented safely in an application log."""


@dataclass(frozen=True, slots=True)
class _Field:
    value: object
    console: bool


def field(
    value: object = None, *, console: bool = False, secret: bool = False
) -> _Field:
    """Classify one field before it reaches a logger.

    Secret values are discarded without inspection. Other values are reduced to
    finite JSON data, with paths represented as strings.
    """

    if secret:
        admitted: object = "<redacted>"
        encoded = b'"<redacted>"'
    else:
        try:
            encoded = json.dumps(
                value,
                default=_path_value,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
            admitted = json.loads(encoded)
        except (OverflowError, TypeError, UnicodeError, ValueError):
            raise LogValueError("field must contain finite JSON metadata") from None
    if len(encoded) > _MAX_FIELD_BYTES:
        raise LogValueError("application-log fields must contain bounded metadata")
    if console and isinstance(admitted, (dict, list)):
        raise LogValueError("console fields must be JSON scalars")
    if console and isinstance(admitted, str):
        _text(admitted)
    return _Field(admitted, console)


def split_fields(
    fields: Mapping[str, object] | None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Return durable and console projections of explicitly classified fields."""

    durable: dict[str, object] = {}
    console: dict[str, object] = {}
    for name, selected in (fields or {}).items():
        _token("field name", name)
        if not isinstance(selected, _Field):
            raise LogValueError("application-log fields must be created with field()")
        durable[name] = selected.value
        if selected.console:
            console[name] = selected.value
    return durable, console


def slurm_correlation(environment: Mapping[str, str]) -> dict[str, str]:
    """Select safe SLURM identity fields without reading the ambient environment."""

    names = (
        "SLURM_JOB_ID",
        "SLURM_ARRAY_JOB_ID",
        "SLURM_ARRAY_TASK_ID",
    )
    selected: dict[str, str] = {}
    for name in names:
        value = environment.get(name)
        if value is None:
            continue
        text = _text(value)
        allow_zero = name == "SLURM_ARRAY_TASK_ID"
        if (
            not text.isascii()
            or not text.isdigit()
            or str(int(text)) != text
            or (not allow_zero and int(text) == 0)
        ):
            raise LogValueError(f"{name} must be a canonical decimal identifier")
        selected[name.lower()] = text
    array_fields = {"slurm_array_job_id", "slurm_array_task_id"}
    if array_fields.intersection(selected) and not {
        "slurm_job_id",
        *array_fields,
    }.issubset(selected):
        raise LogValueError("SLURM array correlation requires job, array, and task IDs")
    return selected


def render_failure_summary(
    *,
    entrypoint: str,
    phase: str,
    status: str,
    scope: str,
    execution_attempt_id: str,
    log_path: Path | None,
    owned_paths: Mapping[str, Path] | None = None,
    recent_events: Sequence[str] = (),
    durable_only_count: int = 0,
    next_action: str,
) -> str:
    """Render the contract's bounded, console-safe final failure summary."""

    lines = [
        f"{_clip(entrypoint)} failed: phase={_clip(phase)} status={_clip(status)}",
        f"Scope: {_clip(scope)}; execution attempt: {_clip(execution_attempt_id)}",
        f"Application log: {_clip(str(log_path))}"
        if log_path
        else "Application log: unavailable; no durable log exists",
    ]
    selected_paths = owned_paths or {}
    for role in ("lock", "stage", "backup", "recovery"):
        if role in selected_paths:
            lines.append(f"Owned {role}: {_clip(str(selected_paths[role]))}")
    admitted = [_clip(event, limit=768) for event in recent_events[-20:]]
    omitted = max(0, len(recent_events) - len(admitted))
    if durable_only_count:
        lines.append(
            "Durable-only events omitted: "
            f"{_clip(str(durable_only_count))}; inspect the application log"
        )
    action = "Next action: " + _clip(next_action)
    event_lines: list[str] = []
    reserved_marker = f"Console-safe events truncated: {max(1, len(recent_events))}"
    for selected in admitted:
        candidate = [*lines, *event_lines, f"Event: {selected}"]
        if _byte_count([*candidate, reserved_marker, action]) <= 8192:
            event_lines.append(f"Event: {selected}")
        else:
            omitted += 1
    marker = [f"Console-safe events truncated: {omitted}"] if omitted else []
    return "\n".join([*lines, *event_lines, *marker, action]) + "\n"


def _path_value(value: object) -> str:
    if isinstance(value, Path):
        return _text(str(value))
    raise TypeError


def _token(label: str, value: Any) -> str:
    text = _text(value)
    if not text or any(character in text for character in "\r\n"):
        raise LogValueError(f"{label} must be nonempty single-line text")
    return text


def _text(value: Any) -> str:
    if not isinstance(value, str):
        raise LogValueError("logged text must be a string")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise LogValueError("logged text must be valid UTF-8") from exc
    if any(
        unicodedata.category(character) in _UNSAFE_TEXT_CATEGORIES
        for character in value
    ):
        raise LogValueError("logged text contains an unsafe character")
    return value


def _clip(value: str, *, limit: int = 512) -> str:
    safe = " ".join(_text(value).splitlines())
    encoded = safe.encode("utf-8")
    if len(encoded) <= limit:
        return safe
    marker = "...<truncated>"
    prefix = encoded[: limit - len(marker)].decode("utf-8", errors="ignore")
    return prefix + marker


def _byte_count(lines: Sequence[str]) -> int:
    return len(("\n".join(lines) + "\n").encode("utf-8"))
