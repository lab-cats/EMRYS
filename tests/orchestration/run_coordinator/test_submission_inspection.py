"""Exact selected-request correlation, without scheduler or scientific execution."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from emrys.contracts.orchestration import api as contracts
from emrys.orchestration.run_coordinator import _submission_inspection as reader
from emrys.orchestration.run_coordinator import slurm_submission
from emrys.orchestration.run_coordinator.execution_profile import (
    DEFAULT_PROFILE_PATH,
    admit_execution_profile_bytes,
    project_default_profile_bytes,
)
from tests.contracts.orchestration.test_application_model_contracts import (
    successor_run_fixture,
)
from tests.orchestration.run_coordinator.test_slurm_submission import _request_record


def _request(
    tmp_path: Path, command: str = "run", run_id: str | None = None, *, version="v2"
):
    project, root, context = _request_record(tmp_path)
    profile = admit_execution_profile_bytes(
        DEFAULT_PROFILE_PATH.read_bytes(),
        tmp_path / "selected.yaml",
        project_default_profile_bytes(site="viking"),
    )
    context.update(
        schema_version=f"emrys.submission-request.{version}",
        command=command,
        requested_run=run_id,
        profile_binding_sha256=profile.binding_sha256,
        scheduler_stdout_pattern=str(
            root.parent / f"emrys-local-pilot-{'a' * 32}-%j.out"
        ),
        scheduler_stderr_pattern=str(
            root.parent / f"emrys-local-pilot-{'a' * 32}-%j.err"
        ),
    )
    if version == "v3":
        context["scheduler_job_name"] = slurm_submission._scheduler_job_name("a" * 32)
    (root / "request.json").write_bytes(contracts.canonical_json_bytes(context))
    return slurm_submission.submission_requests(project)[0], profile


def _log(request, *, suffix="b", token="a", prepared=None):
    context = request.context
    command = context["command"]
    scope = "pending" if command == "run" else context["requested_run"]
    application = "application-" + suffix * 32
    path = (
        Path(context["application_log_root"])
        / f"run-{scope}"
        / application
        / f"emrys-{command}.jsonl"
    )
    path.parent.mkdir(parents=True)
    events = [
        (
            "attempt_opened",
            {
                "entrypoint": f"emrys-{command}",
                "execution_attempt_id": application,
                "scope": f"run:{scope}",
                "log_path": str(path),
                "slurm_job_id": "700123",
            },
        ),
        (
            "submission_context",
            {
                "request_token": token * 32,
                "project_root": str(Path(context["project"]).parent),
                "profile_binding_sha256": context["profile_binding_sha256"],
            },
        ),
    ]
    if prepared is not None:
        events.append(
            (
                "reporting_started" if command == "report" else "analysis_prepared",
                prepared,
            )
        )
    records = [
        {
            "schema_version": "1.0.0",
            "timestamp_utc": "2026-09-15T12:00:00.000000Z",
            "monotonic_seconds": index * 1.0,
            "sequence": index,
            "severity": "info",
            "console_detail": "durable_only"
            if name == "submission_context"
            else "normal",
            "entrypoint": f"emrys-{command}",
            "component": "orchestration",
            "scope_kind": "run",
            "scope_id": scope,
            "execution_attempt_id": application,
            "mode": {"run": "execute", "resume": "resume", "report": "report"}[command],
            "phase": "initialization",
            "event": name,
            "message": "Fixture observation.",
            "fields": fields,
        }
        for index, (name, fields) in enumerate(events, 1)
    ]
    _write_log(path, records)
    return path, records


def _write_log(path, records):
    path.write_bytes(
        b"".join(
            json.dumps(
                record, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode()
            + b"\n"
            for record in records
        )
    )


def _authority(tmp_path: Path, *, command="run"):
    analysis, plan, run, profile, attempt, resources = successor_run_fixture()
    request, selected_profile = _request(
        tmp_path, command, None if command == "run" else run.run_id
    )
    root = tmp_path / "runs" / run.run_id
    contract = root / "contract"
    contract.mkdir(parents=True)
    for name, data in (
        ("analysis.json", analysis.canonical_bytes),
        ("execution-plan.json", plan.canonical_bytes),
        ("run.json", run.canonical_bytes),
        ("profile.json", contracts.canonical_json_bytes(profile)),
    ):
        (contract / name).write_bytes(data)
    attempt["workspace"] = str(tmp_path)
    attempt["authored_paths"]["request"] = request.context["project"]
    attempt["placement"] = selected_profile.attempt_placement("700123")
    attempt["workflow"]["resource_policy"] = resources
    if command == "resume":
        attempt["operation"] = "resume"
        attempt["snakemake_argv"].extend(
            ["--rerun-triggers", "input", "--ignore-incomplete"]
        )
        attempt["supersedes_workflow_attempt_id"] = (
            "workflow-20260811T120000Z-" + "e" * 32
        )
    attempt_path = root / "attempts" / attempt["workflow_attempt_id"] / "attempt.json"
    attempt_path.parent.mkdir(parents=True)
    request_path = attempt_path.with_name("request.yaml")
    request_path.write_bytes(b"fixture Project snapshot\n")
    attempt["request"] = {
        "path": str(request_path),
        "size_bytes": request_path.stat().st_size,
        "sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
    }
    contracts.validate_record("workflow-attempt", attempt)
    attempt_path.write_bytes(contracts.canonical_json_bytes(attempt))
    return request, root, attempt_path, attempt


@pytest.mark.parametrize("command", ["run", "resume", "report"])
@pytest.mark.parametrize("version", ["v2", "v3"])
def test_early_context_binds_one_custom_log_without_run_or_terminal_event(
    tmp_path, command, version
):
    request, _ = _request(
        tmp_path,
        command,
        None if command == "run" else "run-" + "d" * 64,
        version=version,
    )
    path, _ = _log(request)
    _log(request, suffix="c", token="d")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = reader.inspect_submission_application(request)
    assert result.status == "application-log-bound" and result.application_log == path
    assert (
        result.application_log_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert (
        result.run_root is result.workflow_attempt_id is result.recorded_run_id is None
    )
    assert result.diagnostics == ()
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("command", ["run", "resume", "report"])
def test_exact_candidate_authority_is_admitted_without_results_or_latest_selection(
    tmp_path, command
):
    request, root, attempt_path, attempt = _authority(tmp_path, command=command)
    prepared = (
        {"run_root": str(root)}
        if command == "report"
        else {
            "run_id": root.name,
            "workflow_attempt_id": attempt["workflow_attempt_id"],
        }
    )
    path, _ = _log(request, prepared=prepared)
    later = root / "attempts" / ("workflow-20260915T120000Z-" + "f" * 32)
    later.mkdir()
    (later / "attempt.json").write_bytes(
        b"unrelated later record must not be selected\n"
    )
    result = reader.inspect_submission_application(request)
    assert result.status == (
        "run-associated" if command == "report" else "run-and-attempt-associated"
    ), result.diagnostics
    assert result.application_log == path and result.run_root == root
    assert result.workflow_attempt_id == (
        None if command == "report" else attempt_path.parent.name
    )
    assert not (root / "results").exists()
    assert not attempt_path.with_name("attempt-receipt.json").exists()


@pytest.mark.parametrize(
    "defect",
    [
        "missing-authority",
        "profile",
        "attempt-run",
        "attempt-profile",
        "placement-profile",
        "job",
        "project",
        "workspace",
        "operation",
        "request-snapshot",
        "missing-attempt",
    ],
)
def test_recorded_preparation_cannot_replace_independent_run_and_attempt_admission(
    tmp_path, defect
):
    request, root, attempt_path, attempt = _authority(tmp_path)
    path, _ = _log(
        request,
        prepared={
            "run_id": root.name,
            "workflow_attempt_id": attempt["workflow_attempt_id"],
        },
    )
    if defect == "missing-authority":
        (root / "contract/run.json").unlink()
    elif defect == "profile":
        (root / "contract/profile.json").write_bytes(b"{}\n")
    elif defect == "missing-attempt":
        attempt_path.unlink()
    elif defect == "request-snapshot":
        attempt_path.with_name("request.yaml").write_bytes(b"changed\n")
    else:
        if defect == "attempt-run":
            attempt["run_id"] = "run-" + "d" * 64
        elif defect == "attempt-profile":
            attempt["profile_sha256"] = "d" * 64
        elif defect == "placement-profile":
            attempt["placement"]["effective_sha256"] = "d" * 64
        elif defect == "job":
            attempt["placement"]["scheduler_job_id"] = "700124"
        elif defect == "project":
            attempt["authored_paths"]["request"] = "/other/project.yaml"
        elif defect == "workspace":
            attempt["workspace"] = "/other"
        elif defect == "operation":
            attempt["operation"] = "resume"
        attempt_path.write_bytes(contracts.canonical_json_bytes(attempt))
    result = reader.inspect_submission_application(request)
    assert result.status == "application-log-bound" and result.application_log == path
    assert result.recorded_run_id == root.name
    assert result.run_root is result.workflow_attempt_id is None
    assert "not admitted" in " ".join(result.diagnostics)


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate-match",
        "truncated",
        "invalid-utf8",
        "duplicate-json-key",
        "sequence",
        "scope",
        "entrypoint",
        "opening-job",
        "opening-path",
        "profile",
        "project",
        "duplicate-context",
        "missing-token",
        "post-terminal",
        "oversized-number",
        "deep-json",
        "unknown-field",
        "bad-timestamp",
        "regressing-clock",
        "prepared-traversal",
        "duplicate-prepared",
        "symlink-log",
        "symlink-loop",
        "symlink-scope",
        "unexpected-entry",
    ],
)
def test_malformed_or_ambiguous_scope_cannot_bind_application(tmp_path, defect):
    request, _ = _request(tmp_path)
    path, records = _log(request)
    if defect == "duplicate-match":
        _log(request, suffix="c")
    elif defect == "truncated":
        path.write_bytes(path.read_bytes()[:-1])
    elif defect == "invalid-utf8":
        path.write_bytes(b"\xff\n")
    elif defect == "duplicate-json-key":
        path.write_bytes(
            path.read_bytes().replace(b'"sequence":1', b'"sequence":1,"sequence":1', 1)
        )
    elif defect == "deep-json":
        path.write_bytes(b'{"nested":' + b"[" * 2000 + b"0" + b"]" * 2000 + b"}\n")
    elif defect == "symlink-loop":
        path.unlink()
        path.symlink_to(path.name)
    elif defect in ("symlink-log", "symlink-scope"):
        target = path if defect == "symlink-log" else path.parent.parent
        moved = target.with_name(target.name + "-moved")
        target.rename(moved)
        target.symlink_to(moved, target_is_directory=defect == "symlink-scope")
    elif defect == "unexpected-entry":
        (path.parent / "extra").touch()
    else:
        if defect == "sequence":
            records[1]["sequence"] = 4
        elif defect == "scope":
            records[1]["scope_id"] = "other"
        elif defect == "entrypoint":
            records[1]["entrypoint"] = "emrys-resume"
        elif defect == "opening-job":
            records[0]["fields"]["slurm_job_id"] = "700124"
        elif defect == "opening-path":
            records[0]["fields"]["log_path"] = "/other/log.jsonl"
        elif defect == "profile":
            records[1]["fields"]["profile_binding_sha256"] = "d" * 64
        elif defect == "project":
            records[1]["fields"]["project_root"] = "/other"
        elif defect == "duplicate-context":
            records.append({**records[1], "sequence": 3})
        elif defect == "missing-token":
            records[1]["fields"]["request_token"] = None
        elif defect == "post-terminal":
            records.append({**records[1], "sequence": 3, "event": "attempt_failed"})
            records.append({**records[1], "sequence": 4, "event": "after_failure"})
        elif defect == "oversized-number":
            records[1]["monotonic_seconds"] = 10**1000
        elif defect == "unknown-field":
            records[1]["unexpected"] = True
        elif defect == "bad-timestamp":
            records[1]["timestamp_utc"] = "invalid"
        elif defect == "regressing-clock":
            records[1]["monotonic_seconds"] = 0
        else:
            records.append(
                {
                    **records[1],
                    "sequence": 3,
                    "event": "analysis_prepared",
                    "fields": {
                        "run_id": "../../escape",
                        "workflow_attempt_id": "../escape",
                    },
                }
            )
            if defect == "duplicate-prepared":
                records.append({**records[-1], "sequence": 4})
        _write_log(path, records)
    result = reader.inspect_submission_application(request)
    assert (
        result.status == "unknown" and result.application_log is result.run_root is None
    )
    assert result.diagnostics


@pytest.mark.parametrize(
    "limit", ["directories", "log", "aggregate", "authority", "authority-aggregate"]
)
def test_admission_limits_are_explicit_and_do_not_promote_partial_reads(
    tmp_path, monkeypatch, limit
):
    if limit.startswith("authority"):
        request, root, _attempt_path, attempt = _authority(tmp_path)
        path, _ = _log(
            request,
            prepared={
                "run_id": root.name,
                "workflow_attempt_id": attempt["workflow_attempt_id"],
            },
        )
        original = reader.admit_successor_run

        def limited_authority(*args, **kwargs):
            monkeypatch.setattr(
                reader,
                "_AUTHORITY_LIMIT"
                if limit == "authority"
                else "_AUTHORITY_TOTAL_LIMIT",
                1,
            )
            return original(*args, **kwargs)

        monkeypatch.setattr(reader, "admit_successor_run", limited_authority)
    else:
        request, _ = _request(tmp_path)
        path, _ = _log(request)
    if limit == "directories":
        monkeypatch.setattr(reader, "_MAX_APPLICATIONS", 0)
    elif limit == "log":
        monkeypatch.setattr(reader, "_LOG_LIMIT", path.stat().st_size - 1)
    elif limit == "aggregate":
        monkeypatch.setattr(reader, "_LOG_TOTAL_LIMIT", path.stat().st_size - 1)
    result = reader.inspect_submission_application(request)
    assert result.status == (
        "application-log-bound" if limit.startswith("authority") else "unknown"
    )
    assert result.run_root is None and "limit" in " ".join(result.diagnostics)


@pytest.mark.parametrize("defect", ["append", "replace-scope", "foreign-uid"])
def test_path_identity_is_rechecked_after_reading(tmp_path, monkeypatch, defect):
    request, _ = _request(tmp_path)
    path, _records = _log(request)
    original = reader.read_bytes_with_identity

    def read(*args, **kwargs):
        data, state = original(*args, **kwargs)
        if args[0] != path:
            return data, state
        if defect == "append":
            with path.open("ab") as output:
                output.write(b"{}\n")
        elif defect == "replace-scope":
            path.parent.rename(path.parent.with_name("moved"))
            path.parent.mkdir()
            path.write_bytes(data)
        else:
            values = list(state)
            values[4] += 1
            state = os.stat_result(values)
        return data, state

    monkeypatch.setattr(reader, "read_bytes_with_identity", read)
    result = reader.inspect_submission_application(request)
    assert result.status == "unknown" and result.application_log is None


@pytest.mark.parametrize("kind", ["legacy", "unconfirmed", "partial"])
def test_ineligible_request_does_not_scan_application_logs(tmp_path, monkeypatch, kind):
    request, _ = _request(tmp_path)
    if kind == "legacy":
        request = replace(
            request,
            context={
                **request.context,
                "schema_version": "emrys.submission-request.v1",
            },
        )
    else:
        request = replace(request, record_status=kind)
    monkeypatch.setattr(
        reader,
        "directory_entries_with_identity",
        lambda *_a, **_k: pytest.fail("ineligible request scanned logs"),
    )
    result = reader.inspect_submission_application(request)
    assert result.status == "unknown" and result.application_log is None


@pytest.mark.parametrize(
    "defect",
    [
        "context",
        "response",
        "extra",
        "missing-stream",
        "stderr-symlink",
        "stderr-directory",
    ],
)
def test_selected_request_is_rechecked_before_log_correlation(tmp_path, defect):
    request, _ = _request(tmp_path)
    _log(request)
    if defect == "context":
        context = {**request.context, "analysis": "changed"}
        (request.request_root / "request.json").write_bytes(
            contracts.canonical_json_bytes(context)
        )
    elif defect == "response":
        (request.request_root / "sbatch.stdout").write_bytes(b"700124\n")
    elif defect == "extra":
        (request.request_root / "extra").touch()
    else:
        stderr = request.request_root / "sbatch.stderr"
        stderr.unlink()
        if defect == "stderr-symlink":
            stderr.symlink_to(request.request_root / "sbatch.stdout")
        elif defect == "stderr-directory":
            stderr.mkdir()
    result = reader.inspect_submission_application(request)
    assert result.status == "unknown" and result.application_log is None
    assert result.diagnostics


def test_large_stderr_is_pinned_as_bounded_diagnostics_without_full_read(
    tmp_path, monkeypatch
):
    request, _ = _request(tmp_path)
    path, _ = _log(request)
    stderr = request.request_root / "sbatch.stderr"
    stderr.write_bytes(b"diagnostic\xff\n" * 10000)
    original = reader.read_bytes_with_identity
    admitted = []

    def read(source, *args, **kwargs):
        data, identity = original(source, *args, **kwargs)
        if source == stderr:
            assert kwargs["limit"] == 4096
            admitted.append(len(data))
        return data, identity

    monkeypatch.setattr(reader, "read_bytes_with_identity", read)
    result = reader.inspect_submission_application(request)
    assert result.status == "application-log-bound" and result.application_log == path
    assert admitted == [4096]


def test_python311_symlink_loop_error_is_an_unknown_observation(tmp_path, monkeypatch):
    request, _ = _request(tmp_path)
    path, _ = _log(request)
    original = Path.resolve

    def resolve(source, *args, **kwargs):
        if source == path:
            raise RuntimeError("Symlink loop from Python 3.11")
        return original(source, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    result = reader.inspect_submission_application(request)
    assert result.status == "unknown" and result.application_log is None
    assert "cannot be resolved" in " ".join(result.diagnostics)


def _discover(request, root):
    return reader.inspect_run_applications(
        Path(request.context["project"]),
        root,
        Path(request.context["application_log_root"]),
    )


def _prepared(root, attempt):
    return {
        "run_id": root.name,
        "workflow_attempt_id": attempt["workflow_attempt_id"],
    }


@pytest.mark.parametrize("command", ["run", "resume", "report"])
def test_run_discovery_admits_current_writer_without_submission_or_live_project(
    tmp_path, monkeypatch, command
):
    import io

    from emrys.libraries.application_logging import (
        AttemptIdentity,
        LogControls,
        LogLevel,
        event,
        field,
        open_attempt_log,
    )

    request, root, _attempt_path, attempt = _authority(tmp_path, command=command)
    log_root = Path(request.context["application_log_root"])
    application = open_attempt_log(
        controls=LogControls(LogLevel.NORMAL, log_root, "default", "command_line"),
        identity=AttemptIdentity(
            "run",
            "pending" if command == "run" else root.name,
            "application-" + "b" * 32,
            f"emrys-{command}",
        ),
        mode={"run": "execute", "resume": "resume", "report": "report"}[command],
        component="orchestration",
        stderr=io.StringIO(),
    )
    logger = application.logger(component="orchestration", phase="preflight")
    logger.info(
        "Preparation recorded.",
        extra=event(
            "reporting_started" if command == "report" else "analysis_prepared",
            fields={
                key: field(value)
                for key, value in (
                    {"run_root": root}
                    if command == "report"
                    else _prepared(root, attempt)
                ).items()
            },
        ),
    )
    if command != "report":
        logger.info("Automatic reporting started.", extra=event("reporting_started"))
    application.terminal(event_name="fixture_finished", message="Fixture finished.")
    # Historical association uses retained records, not current authored inputs.
    Path(request.context["project"]).unlink()
    (tmp_path / "selected.yaml").write_bytes(b"current placement has changed\n")
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    reads = []
    original = reader.read_bytes_with_identity

    def read(path, *args, **kwargs):
        reads.append(path)
        assert path.is_relative_to(root) or path.is_relative_to(log_root)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(reader, "read_bytes_with_identity", read)
    result = _discover(request, root)
    assert result.status == "complete" and result.diagnostics == ()
    assert len(result.logs) == 1 and result.logs[0].application_log == application.path
    assert result.logs[0].status == (
        "run-associated" if command == "report" else "run-and-attempt-associated"
    )
    assert result.logs[0].workflow_attempt_id == (
        None if command == "report" else attempt["workflow_attempt_id"]
    )
    assert len(reads) == len(set(reads))
    assert {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*")
        if p.is_file()
    } == before
    assert not (root / "results").exists()


def test_run_discovery_retains_all_historical_and_duplicate_attempt_logs(
    tmp_path, monkeypatch
):
    request, root, attempt_path, attempt = _authority(tmp_path)
    first, first_records = _log(request, prepared=_prepared(root, attempt))
    duplicate, _ = _log(request, suffix="c", prepared=_prepared(root, attempt))
    later = json.loads(attempt_path.read_bytes())
    later_id = "workflow-20260915T120000Z-" + "f" * 32
    later.update(
        workflow_attempt_id=later_id,
        created_at="2026-09-15T12:00:00Z",
        operation="resume",
        supersedes_workflow_attempt_id=attempt["workflow_attempt_id"],
    )
    later["snakemake_argv"].extend(["--rerun-triggers", "input", "--ignore-incomplete"])
    later_path = root / "attempts" / later_id / "attempt.json"
    later_path.parent.mkdir()
    later_request = later_path.with_name("request.yaml")
    later_request.write_bytes(attempt_path.with_name("request.yaml").read_bytes())
    later["request"]["path"] = str(later_request)
    contracts.validate_record("workflow-attempt", later)
    later_path.write_bytes(contracts.canonical_json_bytes(later))
    resumed = replace(
        request,
        context={**request.context, "command": "resume", "requested_run": root.name},
    )
    second, _ = _log(resumed, suffix="d", prepared=_prepared(root, later))
    report = replace(
        request,
        context={**request.context, "command": "report", "requested_run": root.name},
    )
    report_path, _ = _log(report, suffix="e", prepared={"run_root": str(root)})
    # A terminal diagnostic outcome is not required and confers no Task/Run receipt.
    first_records.append(
        {
            **first_records[-1],
            "sequence": 4,
            "monotonic_seconds": 4.0,
            "phase": "terminal",
            "event": "attempt_failed",
            "fields": {},
        }
    )
    _write_log(first, first_records)
    reads = []
    original = reader.read_bytes_with_identity

    def read(path, *args, **kwargs):
        reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(reader, "read_bytes_with_identity", read)
    result = _discover(request, root)
    assert result.status == "complete" and result.diagnostics == (), result.diagnostics
    assert [item.application_log for item in result.logs] == [
        first,
        duplicate,
        second,
        report_path,
    ]
    assert [item.workflow_attempt_id for item in result.logs] == [
        attempt["workflow_attempt_id"],
        attempt["workflow_attempt_id"],
        later_id,
        None,
    ]
    assert len(reads) == len(set(reads)), "Each distinct frozen record is read once"
    assert not attempt_path.with_name("attempt-receipt.json").exists()
    # Selected-request identity remains strictly unique, despite Run discovery preserving both.
    assert reader.inspect_submission_application(request).status == "unknown"


@pytest.mark.parametrize(
    "defect",
    [
        "truncated",
        "duplicate-prepared",
        "wrong-project",
        "wrong-workspace",
        "wrong-operation",
        "wrong-run",
        "request-snapshot",
        "missing-attempt",
        "placement-profile",
        "opening-job",
        "unexpected-entry",
        "symlink",
        "log-limit",
        "aggregate-limit",
        "directory-limit",
    ],
)
def test_run_discovery_keeps_stable_matches_but_reports_incomplete_scan(
    tmp_path, monkeypatch, defect
):
    request, root, attempt_path, attempt = _authority(tmp_path)
    first, _ = _log(request, prepared=_prepared(root, attempt))
    bad, records = _log(request, suffix="c", prepared=_prepared(root, attempt))
    # Apply semantic defects to a separate Attempt, preserving the first log's authority.
    if defect in {
        "wrong-project",
        "wrong-workspace",
        "wrong-operation",
        "wrong-run",
        "request-snapshot",
        "missing-attempt",
    }:
        other_id = "workflow-20260915T120000Z-" + "e" * 32
        other_path = root / "attempts" / other_id / "attempt.json"
        other_path.parent.mkdir()
        other = json.loads(attempt_path.read_bytes())
        other["workflow_attempt_id"] = other_id
        other["created_at"] = "2026-09-15T12:00:00Z"
        other_request = other_path.with_name("request.yaml")
        other_request.write_bytes(attempt_path.with_name("request.yaml").read_bytes())
        other["request"]["path"] = str(other_request)
        contracts.validate_record("workflow-attempt", other)
        records[-1]["fields"]["workflow_attempt_id"] = other_id
        if defect == "wrong-project":
            other["authored_paths"]["request"] = "/elsewhere/project.yaml"
        elif defect == "wrong-workspace":
            other["workspace"] = "/elsewhere"
        elif defect == "wrong-operation":
            other["operation"] = "resume"
            other["supersedes_workflow_attempt_id"] = attempt["workflow_attempt_id"]
            other["snakemake_argv"].extend(
                ["--rerun-triggers", "input", "--ignore-incomplete"]
            )
            contracts.validate_record("workflow-attempt", other)
        elif defect == "wrong-run":
            other["run_id"] = "run-" + "e" * 64
        elif defect == "request-snapshot":
            other_request.write_bytes(b"changed\n")
        if defect != "missing-attempt":
            other_path.write_bytes(contracts.canonical_json_bytes(other))
    elif defect == "duplicate-prepared":
        records.append({**records[-1], "sequence": 4, "monotonic_seconds": 4.0})
    elif defect == "placement-profile":
        records[1]["fields"]["profile_binding_sha256"] = "d" * 64
    elif defect == "opening-job":
        records[0]["fields"]["slurm_job_id"] = "700124"
    _write_log(bad, records)
    if defect == "truncated":
        bad.write_bytes(bad.read_bytes()[:-1])
    elif defect == "unexpected-entry":
        bad.with_name("unexpected").touch()
    elif defect == "symlink":
        target = tmp_path / "copied-log"
        target.write_bytes(bad.read_bytes())
        bad.unlink()
        bad.symlink_to(target)
    elif defect == "log-limit":
        monkeypatch.setattr(reader, "_LOG_LIMIT", first.stat().st_size)
        bad.write_bytes(bad.read_bytes() + b" " * 100)
    elif defect == "aggregate-limit":
        monkeypatch.setattr(reader, "_LOG_TOTAL_LIMIT", first.stat().st_size)
    elif defect == "directory-limit":
        # The first scope fits; the second scope exceeds the shared application budget.
        bad.unlink()
        bad.parent.rmdir()
        report = replace(
            request,
            context={
                **request.context,
                "command": "report",
                "requested_run": root.name,
            },
        )
        _log(report, suffix="d", prepared={"run_root": str(root)})
        monkeypatch.setattr(reader, "_MAX_APPLICATIONS", 1)
    result = _discover(request, root)
    assert result.status == "unknown" and result.diagnostics
    assert [item.application_log for item in result.logs] == [first]
    expected_diagnostic = {
        "wrong-project": "Recorded Attempt differs from the selected Project",
        "wrong-workspace": "Recorded Attempt differs from the selected Project",
        "wrong-operation": "Recorded Attempt differs from the application command",
        "wrong-run": "Attempt Run ID differs",
        "request-snapshot": "Recorded Attempt request snapshot differs",
    }.get(defect)
    if expected_diagnostic is not None:
        assert any(expected_diagnostic in item for item in result.diagnostics)


@pytest.mark.parametrize(
    "defect", ["append", "replace-root", "replace-scope", "foreign-uid"]
)
def test_run_discovery_drift_invalidates_all_paths(tmp_path, monkeypatch, defect):
    request, root, _attempt_path, attempt = _authority(tmp_path)
    path, _ = _log(request, prepared=_prepared(root, attempt))
    original = reader.read_bytes_with_identity

    def read(selected, *args, **kwargs):
        data, state = original(selected, *args, **kwargs)
        if selected == path:
            if defect == "append":
                with path.open("ab") as stream:
                    stream.write(b"{}\n")
            elif defect in {"replace-root", "replace-scope"}:
                replaced = (
                    path.parent.parent
                    if defect == "replace-scope"
                    else path.parent.parent.parent
                )
                replaced.rename(replaced.with_name("moved"))
                path.parent.mkdir(parents=True)
                path.write_bytes(data)
            else:
                values = list(state)
                values[4] += 1
                state = os.stat_result(values)
        return data, state

    monkeypatch.setattr(reader, "read_bytes_with_identity", read)
    result = _discover(request, root)
    assert result.status == "unknown" and result.diagnostics and result.logs == ()


def test_run_discovery_does_not_infer_association_from_scope_or_latest(tmp_path):
    request, root, _attempt_path, attempt = _authority(tmp_path)
    _log(request)  # A real preflight failure may lack preparation identity.
    _log(
        request,
        suffix="c",
        prepared={**_prepared(root, attempt), "run_id": "run-" + "e" * 64},
    )
    result = _discover(request, root)
    assert (
        result.status == "complete" and result.logs == () and result.diagnostics == ()
    )
    # An unrelated Run scope is never enumerated or selected as latest.
    unrelated = Path(request.context["application_log_root"]) / ("run-run-" + "e" * 64)
    unrelated.mkdir()
    (unrelated / "malformed").touch()
    assert _discover(request, root) == result


@pytest.mark.parametrize("authority", [False, True])
@pytest.mark.parametrize("failure", ["oversize", "after-read"])
def test_rejected_siblings_cannot_repeat_reads_beyond_aggregate_budget(
    tmp_path, monkeypatch, authority, failure
):
    monkeypatch.setattr(reader, "_AUTHORITY_LIMIT" if authority else "_LOG_LIMIT", 17)
    monkeypatch.setattr(
        reader, "_AUTHORITY_TOTAL_LIMIT" if authority else "_LOG_TOTAL_LIMIT", 32
    )
    paths = [tmp_path / str(index) for index in range(5)]
    for path in paths:
        path.write_bytes(b"x" * 100)
    returned = []
    original = reader.read_bytes_with_identity

    def read(*args, **kwargs):
        result = original(*args, **kwargs)
        returned.append(len(result[0]))
        if failure == "after-read":
            raise reader.ValidationError("Injected drift after actual bounded read")
        return result

    monkeypatch.setattr(reader, "read_bytes_with_identity", read)
    snapshots = reader._Snapshots()
    for path in paths:
        with pytest.raises((reader.InspectionError, reader.ValidationError)):
            snapshots.read(path, authority=authority)
    assert returned == [18, 15]
    assert sum(returned) == 33  # The 32-byte budget plus one overflow sentinel.


@pytest.mark.parametrize("digest", [None, [], "bad"])
def test_report_discovery_rejects_malformed_optional_submission_context(
    tmp_path, digest
):
    request, root, _attempt_path, _attempt = _authority(tmp_path, command="report")
    path, records = _log(request, prepared={"run_root": str(root)})
    records[1]["fields"]["profile_binding_sha256"] = digest
    _write_log(path, records)
    result = _discover(request, root)
    assert result.status == "unknown" and result.diagnostics and result.logs == ()


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("unexpected read failure"), KeyboardInterrupt(), SystemExit(7)],
)
def test_run_discovery_isolates_ordinary_errors_but_preserves_cancellation(
    tmp_path, monkeypatch, failure
):
    def fail(*_args):
        raise failure

    monkeypatch.setattr(reader, "_CandidateAdmission", fail)
    args = (tmp_path / "project.yaml", tmp_path / "runs/run", tmp_path / "logs")
    if isinstance(failure, Exception):
        observed = reader.inspect_run_applications(*args)
        assert observed.logs == () and observed.status == "unknown"
        assert observed.diagnostics == (str(failure),)
    else:
        with pytest.raises(type(failure)) as caught:
            reader.inspect_run_applications(*args)
        assert caught.value is failure
    assert list(tmp_path.iterdir()) == []
