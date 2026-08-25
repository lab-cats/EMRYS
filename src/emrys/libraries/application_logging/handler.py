"""Standard-library logging bound to one durable EMRYS attempt."""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from collections import deque
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from pathlib import Path
from typing import Any

from .controls import LogControls
from .helpers import LogValueError, _text, field, split_fields, slurm_correlation
from .storage import ApplicationLogStorageError, create_application_log_file

APPLICATION_LOG_SCHEMA_VERSION = "1.0.0"
_SCOPES = frozenset(
    {"run", "sample", "cohort", "reference", "review", "validation", "maintenance"}
)
_DETAIL_RANK = {"normal": 0, "verbose": 1, "debug": 2}
_RESERVED_EVENTS = frozenset(
    {
        "attempt_opened",
        "attempt_failed",
        "attempt_interrupted",
        "publication_ready",
        "receipt_publication_failed",
    }
)
_LOGGER_SEQUENCE = count(1)


class ApplicationLogError(RuntimeError):
    """An attempt could not admit, persist, synchronize, or close a record."""

    def __init__(self, message: str, *, stage: str, path: Path | None) -> None:
        super().__init__(message)
        self.stage = stage
        self.path = path


@dataclass(frozen=True, slots=True)
class AttemptIdentity:
    """The public identity of one application-log attempt."""

    scope_kind: str
    scope_id: str
    execution_attempt_id: str
    entrypoint: str

    def __post_init__(self) -> None:
        if self.scope_kind not in _SCOPES:
            raise ValueError(f"unsupported scope kind: {self.scope_kind!r}")
        for name, value in (
            ("scope_id", self.scope_id),
            ("execution_attempt_id", self.execution_attempt_id),
            ("entrypoint", self.entrypoint),
        ):
            if not isinstance(value, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]*", value
            ):
                raise ValueError(f"{name} is not a safe path component")

    @property
    def relative_parts(self) -> tuple[str, str, str]:
        return (
            f"{self.scope_kind}-{self.scope_id}",
            self.execution_attempt_id,
            f"{self.entrypoint}.jsonl",
        )


def event(
    name: str,
    *,
    detail: str = "normal",
    fields: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build standard ``logging`` extras for one structured EMRYS event."""

    return {
        "emrys_event": name,
        "emrys_detail": detail,
        "emrys_fields": dict(fields or {}),
    }


class _AttemptAdapter(logging.LoggerAdapter):
    def process(
        self, msg: object, kwargs: MutableMapping[str, Any]
    ) -> tuple[object, MutableMapping[str, Any]]:
        supplied = kwargs.get("extra")
        if supplied is None:
            merged: dict[str, object] = {}
        elif isinstance(supplied, Mapping):
            merged = dict(supplied)
        else:
            raise TypeError("logging extra must be a mapping")
        merged.update(self.extra)
        kwargs["extra"] = merged
        return msg, kwargs


class _AttemptLogger(logging.Logger):
    def isEnabledFor(self, level: int) -> bool:  # noqa: N802 - stdlib API
        return not self.disabled and level >= self.getEffectiveLevel()


class _AttemptHandler(logging.Handler):
    def __init__(self, attempt: AttemptLog) -> None:
        super().__init__(logging.DEBUG)
        self._attempt = attempt

    def emit(self, record: logging.LogRecord) -> None:
        self._attempt._write_record(record, owner=False)


class AttemptLog:
    """A small attempt owner; construct it only with ``open_attempt_log``."""

    def __init__(
        self,
        *,
        controls: LogControls,
        identity: AttemptIdentity,
        mode: str,
        component: str,
        stderr: Any,
        utc_now: Callable[[], datetime],
        monotonic: Callable[[], float],
        scheduler_environment: Mapping[str, str],
    ) -> None:
        self.identity = identity
        self.mode = _token("mode", mode)
        self._controls = controls
        self._state = "initializing"
        self._sequence = 0
        self._last_monotonic: float | None = None
        self._utc_now = utc_now
        self._monotonic = monotonic
        self._stderr = stderr
        self._recent: deque[str] = deque(maxlen=20)
        self._durable_only_count = 0
        self._logger = _AttemptLogger(
            f"emrys.application.{next(_LOGGER_SEQUENCE)}", logging.DEBUG
        )
        self._logger.propagate = False
        self._logger.disabled = False
        self._handler = _AttemptHandler(self)
        correlation = slurm_correlation(scheduler_environment)
        try:
            self._file = create_application_log_file(controls.root, identity)
            self.path = self._file.path
        except ApplicationLogStorageError as exc:
            raise ApplicationLogError(
                "Could not initialize durable application logging",
                stage="initialization",
                path=None,
            ) from exc
        try:
            self._logger.addHandler(self._handler)
            self._state = "open"
            opening_fields = {
                "entrypoint": field(identity.entrypoint, console=True),
                "execution_attempt_id": field(
                    identity.execution_attempt_id, console=True
                ),
                "log_level": field(controls.level.value, console=True),
                "log_level_source": field(controls.level_source, console=True),
                "log_root_source": field(controls.root_source, console=True),
                "log_path": field(str(self.path), console=True),
                "scope": field(
                    f"{identity.scope_kind}:{identity.scope_id}", console=True
                ),
                **{name: field(value) for name, value in correlation.items()},
            }
            self._transition(
                "attempt_opened",
                "Application logging attempt opened.",
                component=component,
                phase="initialization",
                fields=opening_fields,
                allowed={"open"},
            )
        except BaseException:
            self._abort()
            raise

    def logger(self, *, component: str, phase: str) -> logging.LoggerAdapter:
        _token("component", component)
        _token("phase", phase)
        self._require_state("logger", {"open", "recovery"})
        return _AttemptAdapter(
            self._logger, {"emrys_component": component, "emrys_phase": phase}
        )

    @property
    def recent_console_events(self) -> tuple[str, ...]:
        return tuple(self._recent)

    @property
    def durable_only_count(self) -> int:
        return self._durable_only_count

    def synchronize(self, boundary: str) -> None:
        _token("synchronization boundary", boundary)
        self._handler.acquire()
        try:
            self._require_state("synchronize", {"open", "ready", "recovery"})
            self._sync(boundary)
        finally:
            self._handler.release()

    def publication_ready(
        self,
        *,
        message: str = "Publication is ready for authoritative receipt.",
        fields: Mapping[str, object] | None = None,
    ) -> None:
        self._transition(
            "publication_ready",
            message,
            component="publication",
            phase="publication",
            fields=fields,
            allowed={"open"},
            sync="pre_receipt",
            state="ready",
        )

    def receipt_committed(self) -> None:
        self._handler.acquire()
        try:
            self._require_state("receipt_committed", {"ready"})
            self._state = "post_receipt"
        finally:
            self._handler.release()

    def receipt_failed(
        self,
        *,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        self._transition(
            "receipt_publication_failed",
            message,
            level=logging.ERROR,
            component="publication",
            phase="publication",
            fields=fields,
            allowed={"ready"},
            sync="failure",
            state="recovery",
        )

    def terminal(
        self,
        *,
        event_name: str,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        _require_unreserved(event_name)
        self._transition(
            event_name,
            message,
            phase="terminal",
            fields=fields,
            allowed={"open", "recovery"},
            sync="terminal",
            close=True,
        )

    def fail(
        self,
        *,
        phase: str,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        self._transition(
            "attempt_failed",
            message,
            level=logging.ERROR,
            phase=phase,
            fields=fields,
            allowed={"open", "ready", "recovery"},
            sync="failure",
            close=True,
        )

    def observe_post_receipt(
        self,
        *,
        event_name: str,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> bool:
        _require_unreserved(event_name)
        try:
            self._require_state("observe_post_receipt", {"post_receipt"})
            self._transition(
                event_name,
                message,
                component="publication",
                phase="post_receipt",
                detail="durable_only",
                fields=fields,
                allowed={"post_receipt"},
            )
        except ApplicationLogError:
            return False
        return True

    def interrupt_best_effort(self, *, message: str) -> bool:
        try:
            self._require_state("interrupt", {"open", "ready", "recovery"})
            self._transition(
                "attempt_interrupted",
                message,
                level=logging.ERROR,
                phase="interrupt",
                allowed={"open", "ready", "recovery"},
                sync="failure",
                close=True,
            )
        except ApplicationLogError:
            return False
        return True

    def close(self) -> bool:
        self._handler.acquire()
        try:
            post_receipt = self._state == "post_receipt"
            try:
                self._close()
            except ApplicationLogError:
                if post_receipt:
                    return False
                raise
            return True
        finally:
            self._handler.release()

    def _close(self) -> None:
        if self._state == "closed":
            return
        try:
            self._file.close()
        except ApplicationLogStorageError as exc:
            self._state = "closed"
            self._detach()
            raise ApplicationLogError(
                "Could not close application log", stage="close", path=self.path
            ) from exc
        self._state = "closed"
        self._detach()

    def _transition(
        self,
        event_name: str,
        message: str,
        *,
        phase: str,
        allowed: set[str],
        component: str = "operation",
        level: int = logging.INFO,
        detail: str = "normal",
        fields: Mapping[str, object] | None = None,
        sync: str | None = None,
        state: str | None = None,
        close: bool = False,
    ) -> None:
        record = logging.LogRecord(
            f"emrys.{component}", level, "", 0, message, (), None
        )
        for name, value in {
            "emrys_component": component,
            "emrys_phase": phase,
            "emrys_event": event_name,
            "emrys_detail": detail,
            "emrys_fields": dict(fields or {}),
        }.items():
            setattr(record, name, value)
        self._handler.acquire()
        try:
            self._write_record(record, owner=True, allowed=allowed)
            if sync:
                self._sync(sync)
            if state:
                self._state = state
            if close:
                self._close()
        finally:
            self._handler.release()

    def _write_record(
        self,
        record: logging.LogRecord,
        *,
        owner: bool,
        allowed: set[str] | None = None,
    ) -> None:
        self._require_state("emit", allowed or {"open", "recovery"})
        event_name = _token("event", getattr(record, "emrys_event", "python_log"))
        if event_name in _RESERVED_EVENTS and not owner:
            raise ApplicationLogError(
                f"{event_name} requires an attempt lifecycle method",
                stage="admission",
                path=self.path,
            )
        detail = getattr(
            record,
            "emrys_detail",
            "debug" if record.levelno <= logging.DEBUG else "normal",
        )
        if detail not in {*_DETAIL_RANK, "durable_only"}:
            raise ApplicationLogError(
                "Unknown console detail", stage="admission", path=self.path
            )
        component = _token("component", getattr(record, "emrys_component", record.name))
        phase = _token("phase", getattr(record, "emrys_phase", "runtime"))
        message = _token("message", record.getMessage())
        try:
            durable_fields, console_fields = split_fields(
                getattr(record, "emrys_fields", None)
            )
        except LogValueError as exc:
            raise ApplicationLogError(
                "Invalid application-log fields", stage="admission", path=self.path
            ) from exc
        monotonic = self._monotonic()
        if self._last_monotonic is not None and monotonic < self._last_monotonic:
            raise ApplicationLogError(
                "Monotonic clock regressed", stage="emit", path=self.path
            )
        timestamp = self._utc_now()
        if timestamp.tzinfo is None:
            raise ApplicationLogError(
                "UTC clock returned a naive timestamp", stage="emit", path=self.path
            )
        sequence = self._sequence + 1
        document = {
            "schema_version": APPLICATION_LOG_SCHEMA_VERSION,
            "timestamp_utc": timestamp.astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "monotonic_seconds": monotonic,
            "sequence": sequence,
            "severity": _severity(record.levelno),
            "console_detail": detail,
            "entrypoint": self.identity.entrypoint,
            "component": component,
            "scope_kind": self.identity.scope_kind,
            "scope_id": self.identity.scope_id,
            "execution_attempt_id": self.identity.execution_attempt_id,
            "mode": self.mode,
            "phase": phase,
            "event": event_name,
            "message": message,
            "fields": durable_fields,
        }
        try:
            payload = (
                json.dumps(
                    document, ensure_ascii=False, allow_nan=False, separators=(",", ":")
                ).encode("utf-8")
                + b"\n"
            )
            self._file.write_bytes(payload)
        except (
            ApplicationLogStorageError,
            OverflowError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as exc:
            self._abort()
            raise ApplicationLogError(
                "Could not persist application-log event", stage="emit", path=self.path
            ) from exc
        self._sequence = sequence
        self._last_monotonic = monotonic
        self._project(document, console_fields)

    def _project(
        self, document: Mapping[str, object], fields: Mapping[str, object]
    ) -> None:
        detail = str(document["console_detail"])
        if detail == "durable_only":
            self._durable_only_count += 1
            return
        if _DETAIL_RANK[detail] > _DETAIL_RANK[self._controls.level.value]:
            return
        rendered_fields = " ".join(
            f"{name}={json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
            for name, value in sorted(fields.items())
        )
        line = f"{document['severity']}: {document['message']}"
        if rendered_fields:
            line += " " + rendered_fields
        self._recent.append(line)
        try:
            self._stderr.write(line + "\n")
            self._stderr.flush()
        except Exception:
            pass

    def _sync(self, boundary: str) -> None:
        try:
            self._file.synchronize()
        except ApplicationLogStorageError as exc:
            self._abort()
            raise ApplicationLogError(
                "Could not synchronize application log",
                stage=f"synchronize_{boundary}",
                path=self.path,
            ) from exc

    def _require_state(self, operation: str, allowed: set[str]) -> None:
        if self._state not in allowed:
            raise ApplicationLogError(
                f"{operation} is unavailable while attempt is {self._state}",
                stage=operation,
                path=self.path,
            )

    def _abort(self) -> None:
        if self._state == "closed":
            return
        self._state = "closed"
        try:
            self._file.close()
        except BaseException:
            pass
        self._detach()

    def _detach(self) -> None:
        self._handler.close()


def open_attempt_log(
    *,
    controls: LogControls,
    identity: AttemptIdentity,
    mode: str,
    component: str,
    scheduler_environment: Mapping[str, str] = {},
    stderr: Any = sys.stderr,
    _utc_now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    _monotonic: Callable[[], float] = time.monotonic,
) -> AttemptLog:
    """Open one protected attempt log and emit its opening record."""

    return AttemptLog(
        controls=controls,
        identity=identity,
        mode=mode,
        component=_token("component", component),
        stderr=stderr,
        utc_now=_utc_now,
        monotonic=_monotonic,
        scheduler_environment=scheduler_environment,
    )


def _severity(level: int) -> str:
    if level >= logging.ERROR:
        return "error"
    if level >= logging.WARNING:
        return "warning"
    if level >= logging.INFO:
        return "info"
    return "debug"


def _token(label: str, value: object) -> str:
    try:
        text = _text(value)
    except LogValueError as exc:
        raise ApplicationLogError(
            f"{label} must be console-safe text", stage="admission", path=None
        ) from exc
    if not text:
        raise ApplicationLogError(
            f"{label} must be nonempty", stage="admission", path=None
        )
    return text


def _require_unreserved(event_name: str) -> None:
    selected = _token("event", event_name)
    if selected in _RESERVED_EVENTS:
        raise ApplicationLogError(
            f"{selected} requires its dedicated lifecycle method",
            stage="admission",
            path=None,
        )
