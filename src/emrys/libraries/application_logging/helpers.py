"""Small helpers for sensitive fields, diagnostics, and failure output."""

from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_MAX_FIELD_BYTES = 16 * 1024
_DIAGNOSTIC_CHUNK_BYTES = 12_000
_UNSAFE_TEXT_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


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


def classify_invocation(
    argv: Sequence[str],
    *,
    secret_arguments: Iterable[int] = (),
    environment: Mapping[str, str] | None = None,
    selected_environment: Iterable[str] = (),
    secret_environment: Iterable[str] = (),
) -> dict[str, object]:
    """Classify a command and an explicit environment allow-list for logging."""

    secret_indexes = frozenset(secret_arguments)
    if any(
        not isinstance(index, int)
        or isinstance(index, bool)
        or index < 0
        or index >= len(argv)
        for index in secret_indexes
    ):
        raise LogValueError("secret argument indexes must select command arguments")
    command = [
        "<redacted>" if index in secret_indexes else _text(value)
        for index, value in enumerate(argv)
    ]
    source = environment or {}
    selected_names = tuple(selected_environment)
    secret_names = frozenset(secret_environment)
    if not secret_names.issubset(selected_names):
        raise LogValueError("secret environment names must be explicitly selected")
    selected: dict[str, str] = {}
    for name in selected_names:
        _token("environment name", name)
        if name in source:
            selected[name] = (
                "<redacted>" if name in secret_names else _text(source[name])
            )
    return {"argv": command, "environment": selected}


def child_diagnostic_events(
    data: bytes,
    *,
    stream: str,
    component: str,
) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
    """Preserve binary child diagnostics and pair them with a safe warning."""

    if stream not in {"stdout", "stderr"}:
        raise LogValueError("diagnostic stream must be stdout or stderr")
    if not isinstance(data, bytes) or not data:
        raise LogValueError("diagnostic data must be nonempty bytes")
    _token("component", component)
    chunks = tuple(
        data[offset : offset + _DIAGNOSTIC_CHUNK_BYTES]
        for offset in range(0, len(data), _DIAGNOSTIC_CHUNK_BYTES)
    )
    durable = tuple(
        {
            "event": "child_diagnostic_bytes",
            "detail": "durable_only",
            "message": "Child diagnostic bytes were preserved.",
            "fields": {
                "base64": field(base64.b64encode(chunk).decode("ascii")),
                "byte_count": field(len(chunk)),
                "sha256": field(hashlib.sha256(chunk).hexdigest()),
                "stream": field(stream),
                "component": field(component),
                "chunk_index": field(index),
                "chunk_count": field(len(chunks)),
            },
        }
        for index, chunk in enumerate(chunks, start=1)
    )
    warning = {
        "event": "child_diagnostic_warning",
        "detail": "normal",
        "message": "A child emitted non-text diagnostics; inspect the application log.",
        "fields": {
            "byte_count": field(len(data), console=True),
            "stream": field(stream, console=True),
            "component": field(component, console=True),
        },
    }
    return durable, warning


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
