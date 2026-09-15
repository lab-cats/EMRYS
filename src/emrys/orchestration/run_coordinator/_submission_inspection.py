"""Bound one selected submission to recorded application and admitted Run identity."""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as contracts
from emrys.contracts.orchestration.application_model import validate_successor_run
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    directory_entries_with_identity,
    read_bytes_with_identity,
)
from ._inspection_admission import (
    InspectionError,
    admit_canonical_record,
    admit_successor_run,
)
from .execution_profile import execution_profile_binding_sha256
from .slurm_submission import (
    SlurmSubmissionError,
    SubmissionRequestObservation,
    _submitted_response,
    _validate_request_token,
)

_MAX_APPLICATIONS = 128
_LOG_LIMIT = 1024 * 1024
_LOG_TOTAL_LIMIT = 8 * _LOG_LIMIT
_AUTHORITY_LIMIT = 4 * _LOG_LIMIT
_AUTHORITY_TOTAL_LIMIT = 16 * _LOG_LIMIT
_LOG_FIELDS = frozenset(
    "schema_version timestamp_utc monotonic_seconds sequence severity console_detail "
    "entrypoint component scope_kind scope_id execution_attempt_id mode phase event "
    "message fields".split()
)
_STATE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_uid",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)
_EVIDENCE_ERRORS = (
    OSError,
    ValidationError,
    InspectionError,
    contracts.ContractValidationError,
    SlurmSubmissionError,
    KeyError,
    ValueError,
    TypeError,
    OverflowError,
    RecursionError,
)


def _diagnostic(error: Exception) -> str:
    detail = str(error)
    return detail[:4096] + (" [truncated]" if len(detail) > 4096 else "")


@dataclass(frozen=True, slots=True)
class SubmissionApplicationObservation:
    """Correlation evidence; never completion, live ownership or recovery authority."""

    status: str = "unknown"
    application_log: Path | None = None
    application_log_sha256: str | None = None
    recorded_event: str | None = None
    recorded_run_id: str | None = None
    recorded_workflow_attempt_id: str | None = None
    run_root: Path | None = None
    workflow_attempt_id: str | None = None
    diagnostics: tuple[str, ...] = ()


class _Snapshots:
    def __init__(self) -> None:
        self.states: dict[Path, os.stat_result] = {}
        self.log_bytes = self.authority_bytes = 0

    def remember(self, path: Path, state: os.stat_result) -> None:
        try:
            resolved = path.resolve(strict=True)
        except RuntimeError as exc:
            raise InspectionError(f"Path cannot be resolved: {path}") from exc
        if resolved != path or state.st_uid != os.getuid():
            raise InspectionError(
                f"Path is not canonical and current-UID owned: {path}"
            )
        previous = self.states.setdefault(path, state)
        if any(getattr(previous, key) != getattr(state, key) for key in _STATE_FIELDS):
            raise InspectionError(f"Path changed during application inspection: {path}")

    def directory(self, path: Path, *, limit: int) -> tuple[str, ...]:
        self.remember(path, path.lstat())
        entries, state = directory_entries_with_identity(
            path, "Application directory", limit=limit
        )
        self.remember(path, state)
        return entries

    def read(
        self,
        path: Path,
        *,
        authority: bool = False,
        limit: int | None = None,
        prefix: bool = False,
    ) -> bytes:
        self.remember(path, path.lstat())
        limit = (
            min(limit or _AUTHORITY_LIMIT, _AUTHORITY_LIMIT)
            if authority
            else _LOG_LIMIT
        )
        remaining = (
            _AUTHORITY_TOTAL_LIMIT - self.authority_bytes
            if authority
            else _LOG_TOTAL_LIMIT - self.log_bytes
        )
        if remaining <= 0:
            raise InspectionError("Selected-request aggregate byte limit exceeded")
        data, state = read_bytes_with_identity(
            path,
            "Selected-request evidence",
            nonempty=False,
            limit=min(limit, remaining) + (0 if prefix else 1),
        )
        self.remember(path, state)
        if not prefix and state.st_size > min(limit, remaining):
            raise InspectionError(
                f"Selected-request evidence byte limit exceeded: {path}"
            )
        if authority:
            self.authority_bytes += len(data)
        else:
            self.log_bytes += len(data)
        return data

    def authority(self, path: Path, root: Path, _label: str) -> bytes:
        if not path.is_relative_to(root):
            raise InspectionError("Authority path escapes its Run")
        parent = root
        self.remember(parent, parent.lstat())
        for part in path.relative_to(root).parts[:-1]:
            parent /= part
            self.remember(parent, parent.lstat())
        return self.read(path, authority=True)

    def recheck(self) -> None:
        for path in tuple(self.states):
            self.remember(path, path.lstat())


def _log_records(
    data: bytes, path: Path, command: str, scope: str
) -> list[dict[str, Any]]:
    if not data or not data.endswith(b"\n"):
        raise InspectionError(f"Application log is empty or truncated: {path}")
    records = []
    last_monotonic = -math.inf
    for index, line in enumerate(data.splitlines(), 1):
        record = contracts.load_json_object_bytes(line, "Application event")
        timestamp = record.get("timestamp_utc")
        monotonic = record.get("monotonic_seconds")
        if (
            set(record) != _LOG_FIELDS
            or record["schema_version"] != "1.0.0"
            or type(record["sequence"]) is not int
            or record["sequence"] != index
            or record["entrypoint"] != f"emrys-{command}"
            or record["scope_kind"] != "run"
            or record["scope_id"] != scope
            or record["execution_attempt_id"] != path.parent.name
            or record["mode"]
            != {"run": "execute", "resume": "resume", "report": "report"}[command]
            or record["severity"] not in ("debug", "info", "warning", "error")
            or record["console_detail"]
            not in ("normal", "verbose", "debug", "durable_only")
            or not isinstance(record["fields"], dict)
            or any(
                not isinstance(record[key], str) or not record[key]
                for key in ("component", "phase", "event", "message")
            )
            or not isinstance(timestamp, str)
            or datetime.fromisoformat(timestamp.replace("Z", "+00:00")).tzinfo != UTC
            or type(monotonic) not in (int, float)
            or not math.isfinite(monotonic)
            or monotonic < last_monotonic
        ):
            raise InspectionError(f"Application event metadata is malformed: {path}")
        records.append(record)
        last_monotonic = monotonic
    opening = records[0]
    if (
        opening["event"] != "attempt_opened"
        or any(record["event"] == "attempt_opened" for record in records[1:])
        or any(
            record["phase"] == "terminal"
            or record["event"] in ("attempt_failed", "attempt_interrupted")
            for record in records[:-1]
        )
        or any(
            opening["fields"].get(key) != expected
            for key, expected in (
                ("entrypoint", f"emrys-{command}"),
                ("execution_attempt_id", path.parent.name),
                ("log_path", str(path)),
                ("scope", f"run:{scope}"),
            )
        )
    ):
        raise InspectionError(
            f"Application opening differs from its file identity: {path}"
        )
    return records


def _admit_candidate(
    result: SubmissionApplicationObservation,
    request: SubmissionRequestObservation,
    snapshots: _Snapshots,
) -> SubmissionApplicationObservation:
    context = request.context
    assert context is not None and result.recorded_run_id is not None
    project = Path(str(context["project"]))
    root = project.parent / "runs" / result.recorded_run_id
    authority = admit_successor_run(root, read_bytes=snapshots.authority)
    profile, _ = admit_canonical_record(
        root / "contract/profile.json", root, "profile", read_bytes=snapshots.authority
    )
    attempt = None
    if result.recorded_workflow_attempt_id is not None:
        attempt_root = root / "attempts" / result.recorded_workflow_attempt_id
        attempt, _ = admit_canonical_record(
            attempt_root / "attempt.json",
            root,
            "workflow-attempt",
            read_bytes=snapshots.authority,
        )
        placement = attempt.get("placement", {})
        if (
            attempt["workflow_attempt_id"] != result.recorded_workflow_attempt_id
            or attempt["workspace"] != str(project.parent)
            or attempt["authored_paths"]["request"] != str(project)
            or attempt["operation"]
            != ("execute" if context["command"] == "run" else "resume")
            or placement.get("kind") != "slurm"
            or placement.get("scheduler_job_id") != request.recorded_job_id
            or execution_profile_binding_sha256(
                placement["effective_sha256"], placement["source"]["sha256"]
            )
            != context["profile_binding_sha256"]
        ):
            raise InspectionError(
                "Recorded Attempt differs from the selected submission"
            )
        request_path = attempt_root / "request.yaml"
        request_data = snapshots.authority(request_path, root, "Attempt request")
        if attempt["request"] != {
            "path": str(request_path),
            "size_bytes": len(request_data),
            "sha256": hashlib.sha256(request_data).hexdigest(),
        }:
            raise InspectionError("Recorded Attempt request snapshot differs")
    validate_successor_run(
        analysis=authority.analysis_revision,
        plan=authority.execution_plan,
        run=authority.run_binding,
        profile=profile,
        attempt=attempt,
        resource_policy=None
        if attempt is None
        else attempt["workflow"]["resource_policy"],
    )
    return replace(
        result,
        status="run-associated" if attempt is None else "run-and-attempt-associated",
        run_root=root,
        workflow_attempt_id=result.recorded_workflow_attempt_id,
    )


def inspect_submission_application(
    request: SubmissionRequestObservation,
) -> SubmissionApplicationObservation:
    """Inspect only one selected request's command scope, without scheduler calls."""
    context = request.context
    if (
        request.record_status != "recorded-response"
        or context is None
        or context["schema_version"]
        not in ("emrys.submission-request.v2", "emrys.submission-request.v3")
    ):
        return SubmissionApplicationObservation(
            diagnostics=("Complete token-bound request evidence is unavailable",)
        )
    snapshots = _Snapshots()
    try:
        if snapshots.directory(request.request_root, limit=3) != (
            "request.json",
            "sbatch.stderr",
            "sbatch.stdout",
        ):
            raise InspectionError(
                "Selected submission records changed or are incomplete"
            )
        if snapshots.read(
            request.request_root / "request.json", authority=True, limit=64 * 1024
        ) != contracts.canonical_json_bytes(dict(context)):
            raise InspectionError("Selected submission context changed since admission")
        response = snapshots.read(
            request.request_root / "sbatch.stdout", authority=True, limit=4096
        )
        if not response.endswith(b"\n") or _submitted_response(
            response.decode("utf-8")
        ) != (request.recorded_job_id, request.recorded_cluster):
            raise InspectionError(
                "Selected submission response changed since admission"
            )
        snapshots.read(
            request.request_root / "sbatch.stderr",
            authority=True,
            limit=4096,
            prefix=True,
        )
        command = str(context["command"])
        scope = "pending" if command == "run" else str(context["requested_run"])
        log_root = Path(str(context["application_log_root"]))
        snapshots.remember(log_root, log_root.lstat())
        scope_root = log_root / f"run-{scope}"
        entries = snapshots.directory(scope_root, limit=_MAX_APPLICATIONS)
        matches = []
        token = request.request_root.name.removeprefix("submission-")
        for name in entries:
            if not re.fullmatch(r"application-[0-9a-f]{32}", name):
                raise InspectionError("Application directory name is not canonical")
            application_root = scope_root / name
            children = snapshots.directory(application_root, limit=1)
            if len(children) != 1 or children[0] not in (
                "emrys-run.jsonl",
                "emrys-resume.jsonl",
                "emrys-report.jsonl",
            ):
                raise InspectionError(
                    "Application directory is incomplete or contains unexpected entries"
                )
            path = application_root / f"emrys-{command}.jsonl"
            if path.name not in children:
                continue
            data = snapshots.read(path)
            records = _log_records(data, path, command, scope)
            contexts = [
                record for record in records if record["event"] == "submission_context"
            ]
            if not contexts:
                continue
            if len(contexts) != 1:
                raise InspectionError(
                    "Application log has conflicting submission context"
                )
            binding = contexts[0]
            _validate_request_token(binding["fields"].get("request_token"))
            if binding["fields"].get("request_token") is None or set(
                binding["fields"]
            ) != {
                "request_token",
                "profile_binding_sha256",
                "project_root",
            }:
                raise InspectionError("Application submission context fields differ")
            if binding["fields"].get("request_token") != token:
                continue
            if (
                binding is not records[1]
                or binding["console_detail"] != "durable_only"
                or binding["fields"]
                != {
                    "request_token": token,
                    "profile_binding_sha256": context["profile_binding_sha256"],
                    "project_root": str(Path(str(context["project"])).parent),
                }
                or records[0]["fields"].get("slurm_job_id") != request.recorded_job_id
            ):
                raise InspectionError(
                    "Application context differs from the selected submission"
                )
            event_name = (
                "reporting_started" if command == "report" else "analysis_prepared"
            )
            prepared = [record for record in records if record["event"] == event_name]
            if len(prepared) > 1:
                raise InspectionError(
                    "Application log has conflicting preparation observations"
                )
            run_id = attempt_id = None
            if prepared:
                fields = prepared[0]["fields"]
                if command == "report":
                    run_id = str(context["requested_run"])
                    if fields != {
                        "run_root": str(
                            Path(str(context["project"])).parent / "runs" / run_id
                        )
                    }:
                        raise InspectionError(
                            "Recorded report Run differs from the request"
                        )
                else:
                    run_id, attempt_id = (
                        fields.get("run_id"),
                        fields.get("workflow_attempt_id"),
                    )
                    if (
                        set(fields) != {"run_id", "workflow_attempt_id"}
                        or not isinstance(run_id, str)
                        or not re.fullmatch(r"run-[0-9a-f]{64}", run_id)
                        or not isinstance(attempt_id, str)
                        or not re.fullmatch(
                            r"workflow-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}", attempt_id
                        )
                        or (command == "resume" and run_id != context["requested_run"])
                    ):
                        raise InspectionError(
                            "Recorded preparation identity is malformed or differs"
                        )
            matches.append(
                SubmissionApplicationObservation(
                    status="application-log-bound",
                    application_log=path,
                    application_log_sha256=hashlib.sha256(data).hexdigest(),
                    recorded_event=event_name if prepared else None,
                    recorded_run_id=run_id,
                    recorded_workflow_attempt_id=attempt_id,
                )
            )
        if len(matches) != 1:
            raise InspectionError(
                "Exactly one matching application log is required; association is unknown"
            )
        result = matches[0]
        if result.recorded_run_id is not None:
            try:
                result = _admit_candidate(result, request, snapshots)
            except _EVIDENCE_ERRORS as exc:
                result = replace(
                    result,
                    diagnostics=(
                        "Recorded preparation is not admitted Run/Attempt identity: "
                        + _diagnostic(exc),
                    ),
                )
        snapshots.recheck()
        return result
    except _EVIDENCE_ERRORS as exc:
        return SubmissionApplicationObservation(diagnostics=(_diagnostic(exc),))
