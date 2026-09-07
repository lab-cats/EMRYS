from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "src/emrys/orchestration/run_coordinator/dashboard.py"
)
SPEC = importlib.util.spec_from_file_location("emrys_dashboard_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


JOB_ID = 605305
RUN_ID = "run-" + "a" * 64


def _make_logs(log_dir: Path, job_id: int = JOB_ID) -> tuple[Path, Path]:
    log_dir.mkdir()
    stdout = log_dir / f"emrys-local-pilot-{job_id}.out"
    stderr = log_dir / f"emrys-local-pilot-{job_id}.err"
    stdout.write_text("stdout\n", encoding="utf-8")
    stderr.write_text("stderr\n", encoding="utf-8")
    return stdout, stderr


def _flatten_render_lines(lines: list[object]) -> str:
    rendered: list[str] = []
    for line in lines:
        if isinstance(line, list):
            rendered.append("".join(str(segment[0]) for segment in line))
        elif isinstance(line, tuple):
            rendered.append(str(line[0]))
        else:
            rendered.append(str(line))
    return "\n".join(rendered)


def test_parse_and_render_dynamic_per_stage_resource_plan() -> None:
    control = f"""
Run ID: {RUN_ID}
Run root: /work/runs/{RUN_ID}
Step thread allocations:
  Step 00a: 12
  Step 01: 2
  Step 02: 1
  Step 06: 1
  Step 08: 4
Total workflow cores: 12
Total workflow memory: 524288 MiB
Stage concurrency:
  Step 01: 6
  Step 02: 6
  Step 02b: 6
  Step 03: 6
  Step 04: 4
  Step 05: 6
  Step 06: 6
  Step 07: 12
Stage memory per job:
  Step 00a: 262144 MiB
  Step 01: 40960 MiB
  Step 04: 32768 MiB
  Step 07: 8192 MiB
Reporting transactions: 3
Reporting memory per transaction:
  artifact_index: 8192 MiB
  run_summary: 16384 MiB
  html_report: 16384 MiB
"""

    identity = dashboard.parse_identity(control)

    assert identity["workflow_cores"] == "12"
    assert identity["workflow_memory_mb"] == "524288"
    assert identity["step_threads"] == {
        "00a": 12,
        "01": 2,
        "02": 1,
        "06": 1,
        "08": 4,
    }
    assert identity["stage_concurrency"] == {
        "01": 6,
        "02": 6,
        "02b": 6,
        "03": 6,
        "04": 4,
        "05": 6,
        "06": 6,
        "07": 12,
    }
    assert identity["stage_memory_mb"] == {
        "00a": 262144,
        "01": 40960,
        "04": 32768,
        "07": 8192,
    }
    assert identity["reporting_memory_mb"] == {
        "artifact_index": 8192,
        "run_summary": 16384,
        "html_report": 16384,
    }
    assert dashboard.configuration_text(identity) == (
        "Step 01: 6 sample processes x 2 configured threads | 12 workflow cores"
    )
    assert dashboard.stage_resource_text("01", identity, "unused") == (
        "Up to 6 sample processes x 2 STAR threads (12 nominal threads). "
        "Per-job memory: 40960 MiB."
    )
    assert dashboard.stage_resource_text("07", identity, "unused") == (
        "Up to 12 partition processes within the 12-core workflow envelope. "
        "Per-job memory: 8192 MiB."
    )
    assert dashboard.stage_resource_text("04", identity, "unused") == (
        "Up to 4 sample Java/Picard processes. Per-job memory: 32768 MiB."
    )

    workflow = dashboard.parse_workflow(
        """[Thu Aug 20 21:25:00 2026]
rule align_RNA_reads_with_STAR:
    jobid: 7
    wildcards: sample_id=ABE_EV_2
"""
    )
    rendered = _flatten_render_lines(
        dashboard.current_lines(workflow, identity, 1_800_000_000, 100)
    )
    assert "Step 01 - STAR alignment" in rendered
    normalized_rendered = " ".join(rendered.split())
    assert (
        "Up to 6 sample processes x 2 STAR threads (12 nominal threads). "
        "Per-job memory: 40960 MiB."
    ) in normalized_rendered


def test_parse_and_render_one_by_one_control_plan() -> None:
    identity = dashboard.parse_identity(
        """Step thread allocations:
  Step 00a: 1
  Step 01: 1
  Step 02: 1
  Step 06: 1
  Step 08: 1
Total workflow cores: 1
Maximum concurrent sample tasks: 1
"""
    )

    assert dashboard.configuration_text(identity) == (
        "Step 01: 1 sample process x 1 configured thread | 1 workflow core"
    )
    assert dashboard.stage_resource_text("00a", identity, "unused") == (
        "1 process x 1 STAR thread; sample concurrency does not apply."
    )
    assert dashboard.stage_resource_text("01", identity, "unused") == (
        "Up to 1 sample process x 1 STAR thread (1 nominal thread)."
    )
    assert dashboard.stage_resource_text("08", identity, "unused") == (
        "1 cohort process using 1 configured thread where supported."
    )
    assert dashboard.stage_resource_text("05", identity, "unused") == (
        "Up to 1 GATK process; JVM/native threads may exceed the configured "
        "workflow threads."
    )


def test_missing_control_plan_never_invents_six_by_two() -> None:
    identity = dashboard.parse_identity(f"Run ID: {RUN_ID}\n")

    assert dashboard.configuration_text(identity) == (
        "not yet reported by the EMRYS control plan"
    )
    assert dashboard.stage_resource_text("01", identity, "legacy fallback") == (
        "Resource plan not yet reported by the EMRYS control stream."
    )


def test_stream_cache_sanitizes_terminal_sequences_and_controls() -> None:
    cache = dashboard.StreamCache("unused")
    cache.data.extend(
        b"plain\x1b[31mred\x1b[0m\tkept\n\x1b]52;c;clipboard-secret\x07after\x00\x08"
    )

    assert cache.text() == "plainred\tkept\nafter"


def test_positional_overrides_take_precedence_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []
    monkeypatch.setenv("EMRYS_DASHBOARD_JOB_ID", "111")
    monkeypatch.setenv("EMRYS_DASHBOARD_LOG_DIR", "/environment")

    def fake_resolve(*args: object) -> dict[str, object]:
        calls.append(args)
        return {
            "job_id": 222,
            "log_dir": "/explicit",
            "out": "/explicit/emrys-local-pilot-222.out",
            "err": "/explicit/emrys-local-pilot-222.err",
        }

    monkeypatch.setattr(dashboard, "resolve_selection", fake_resolve)

    parsed = dashboard.parse_args(["222", "/explicit"])

    assert calls == [(222, "/explicit", None, None, False)]
    assert parsed.job_id == 222
    assert parsed.log_dir == "/explicit"


def test_explicit_job_failure_does_not_fall_back_to_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_explicit(
        job_id: int,
        log_dir: str | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        del log_dir, kwargs
        raise dashboard.DiscoveryError(f"invalid explicit job {job_id}")

    def unexpected_discovery() -> list[int]:
        pytest.fail("explicit selection must not call candidate discovery")

    monkeypatch.setattr(dashboard, "scheduler_selection", reject_explicit)
    monkeypatch.setattr(dashboard, "scheduler_candidate_ids", unexpected_discovery)
    monkeypatch.setattr(dashboard, "scheduler_candidates", unexpected_discovery)

    with pytest.raises(dashboard.DiscoveryError, match="invalid explicit job 605305"):
        dashboard.resolve_selection(JOB_ID)


def test_validate_log_selection_accepts_exact_owned_regular_pair(
    tmp_path: Path,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")

    selected = dashboard.validate_log_selection(JOB_ID, stdout, stderr)

    assert selected == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
    }


@pytest.mark.parametrize(
    ("stdout_name", "stderr_name", "message"),
    [
        ("wrong.out", f"emrys-local-pilot-{JOB_ID}.err", "stdout does not match"),
        (f"emrys-local-pilot-{JOB_ID}.out", "wrong.err", "stderr does not match"),
    ],
)
def test_validate_log_selection_rejects_wrong_contract_filenames(
    tmp_path: Path,
    stdout_name: str,
    stderr_name: str,
    message: str,
) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    stdout = log_dir / stdout_name
    stderr = log_dir / stderr_name
    stdout.write_text("", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")

    with pytest.raises(dashboard.DiscoveryError, match=message):
        dashboard.validate_log_selection(JOB_ID, stdout, stderr)


def test_validate_log_selection_rejects_symlinked_log(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    target = log_dir / "target"
    target.write_text("stdout", encoding="utf-8")
    stdout = log_dir / f"emrys-local-pilot-{JOB_ID}.out"
    stdout.symlink_to(target)
    stderr = log_dir / f"emrys-local-pilot-{JOB_ID}.err"
    stderr.write_text("stderr", encoding="utf-8")

    with pytest.raises(dashboard.DiscoveryError, match="real regular file"):
        dashboard.validate_log_selection(JOB_ID, stdout, stderr)


def test_validate_log_selection_rejects_symlinked_directory(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    stdout, stderr = _make_logs(real_dir)
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)

    with pytest.raises(dashboard.DiscoveryError, match="real directory"):
        dashboard.validate_log_selection(
            JOB_ID, linked_dir / stdout.name, linked_dir / stderr.name
        )


def test_scheduler_candidate_ids_prefers_live_then_recent_root_allocations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_command(argv: list[str], timeout: int = 10) -> str:
        del timeout
        if argv[0] == "squeue":
            return "605305|RUNNING\n605300|PENDING\n605305.batch|RUNNING"
        if argv[0] == "sacct":
            return (
                "605305|RUNNING\n605304|COMPLETED\n605304.batch|COMPLETED\n"
                "605303|FAILED"
            )
        pytest.fail(f"unexpected command: {argv}")

    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "command_text", fake_command)

    assert dashboard.scheduler_candidate_ids() == [
        605305,
        605300,
        605304,
        605303,
    ]


def test_auto_discovery_skips_unprovable_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = {
        "job_id": 605304,
        "log_dir": "/logs",
        "out": "/logs/emrys-local-pilot-605304.out",
        "err": "/logs/emrys-local-pilot-605304.err",
    }
    attempted: list[int] = []
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: [
            {"job_id": 605305, "accounting": None},
            {"job_id": 605304, "accounting": None},
        ],
    )

    def fake_selection(job_id: int, log_dir: str | None = None) -> dict[str, object]:
        del log_dir
        attempted.append(job_id)
        if job_id == 605305:
            raise dashboard.DiscoveryError("not an EMRYS wrapper job")
        return selected

    monkeypatch.setattr(dashboard, "scheduler_selection", fake_selection)

    assert dashboard.resolve_selection() == selected
    assert attempted == [605305, 605304]


def test_auto_discovery_uses_accounting_declared_completed_streams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: [
            {
                "job_id": JOB_ID,
                "accounting": {
                    "JobId": str(JOB_ID),
                    "JobName": "emrys-real-run",
                    "JobState": "COMPLETED",
                    "User": "2609214",
                    "UID": str(os.getuid()),
                    "StdOut": str(stdout),
                    "StdErr": str(stderr),
                },
            }
        ],
    )

    def unexpected_scontrol(*args: object) -> dict[str, object]:
        pytest.fail(f"valid accounting streams should avoid scontrol: {args}")

    monkeypatch.setattr(dashboard, "scheduler_selection", unexpected_scontrol)

    assert dashboard.resolve_selection() == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
        "selection_source": "sacct-stdout-stderr",
    }


def test_scheduler_selection_binds_metadata_owner_and_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(
        dashboard,
        "slurm_job_metadata",
        lambda job_id: {
            "JobId": str(job_id),
            "UserId": f"2609214({os.getuid()})",
            "JobState": "RUNNING",
            "StdOut": str(stdout),
            "StdErr": str(stderr),
        },
    )

    assert dashboard.scheduler_selection(JOB_ID) == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
    }


def test_explicit_job_and_log_dir_use_terminal_accounting_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)

    def fake_command(argv: list[str], timeout: int = 10) -> str:
        del timeout
        assert argv[0] == "sacct"
        return (
            f"{JOB_ID}|emrys-real-run|COMPLETED+|2609214|{os.getuid()}\n"
            f"{JOB_ID}.batch|batch|COMPLETED|2609214|{os.getuid()}"
        )

    monkeypatch.setattr(dashboard, "command_text", fake_command)

    assert dashboard.resolve_selection(JOB_ID, str(tmp_path / "logs")) == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
        "selection_source": "sacct+explicit-log-dir",
    }


def test_explicit_completed_job_uses_exact_accounting_streams_without_log_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)
    calls: list[list[str]] = []

    def fake_command(argv: list[str], timeout: int = 10) -> str:
        del timeout
        calls.append(argv)
        assert argv[0] == "sacct"
        return (
            f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}|"
            f"{stdout}|{stderr}"
        )

    monkeypatch.setattr(dashboard, "command_text", fake_command)

    assert dashboard.resolve_selection(JOB_ID) == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
        "selection_source": "sacct-stdout-stderr",
    }
    assert len(calls) == 1
    assert calls[0][calls[0].index("-j") + 1] == str(JOB_ID)
    assert calls[0][-1].endswith(",StdOut,StdErr")


def test_explicit_log_dir_must_agree_with_exact_accounting_streams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "scheduler-logs")
    requested = tmp_path / "requested-logs"
    requested.mkdir()
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)
    calls = 0

    def fake_command(argv: list[str], timeout: int = 10) -> str:
        nonlocal calls
        del argv, timeout
        calls += 1
        return (
            f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}|"
            f"{stdout}|{stderr}"
        )

    monkeypatch.setattr(dashboard, "command_text", fake_command)

    with pytest.raises(dashboard.DiscoveryError, match="LOG_DIR disagrees"):
        dashboard.resolve_selection(JOB_ID, str(requested))
    assert calls == 1


def test_exact_accounting_uses_one_basic_fallback_when_stream_fields_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)
    formats: list[str] = []

    def fake_command(argv: list[str], timeout: int = 10) -> str:
        del timeout
        format_value = argv[-1]
        formats.append(format_value)
        if format_value.endswith(",StdOut,StdErr"):
            return ""
        return f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}"

    monkeypatch.setattr(dashboard, "command_text", fake_command)

    assert dashboard.resolve_selection(JOB_ID, str(tmp_path / "logs")) == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
        "selection_source": "sacct+explicit-log-dir",
    }
    assert formats == [
        "--format=JobIDRaw,JobName,State,User,UID,StdOut,StdErr",
        "--format=JobIDRaw,JobName,State,User,UID",
    ]


def test_explicit_job_without_log_dir_fails_if_accounting_has_no_stream_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)

    def fake_command(argv: list[str], timeout: int = 10) -> str:
        del timeout
        if argv[-1].endswith(",StdOut,StdErr"):
            return ""
        return f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}"

    monkeypatch.setattr(dashboard, "command_text", fake_command)

    with pytest.raises(dashboard.DiscoveryError, match="pass LOG_DIR explicitly"):
        dashboard.resolve_selection(JOB_ID)


@pytest.mark.parametrize(
    ("accounting", "message"),
    [
        (
            f"{JOB_ID}|emrys-real-run|RUNNING|2609214|{os.getuid()}",
            "is not terminal",
        ),
        (
            f"{JOB_ID}|emrys-real-run|COMPLETED|someone-else|999999",
            "is not owned",
        ),
        (
            "\n".join(
                [
                    f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}",
                    f"{JOB_ID}|duplicate|COMPLETED|2609214|{os.getuid()}",
                ]
            ),
            "did not return one exact root record",
        ),
    ],
)
def test_historical_accounting_fallback_rejects_unproven_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    accounting: str,
    message: str,
) -> None:
    _make_logs(tmp_path / "logs")
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)
    monkeypatch.setattr(
        dashboard,
        "command_text",
        lambda argv, timeout=10: accounting,
    )

    with pytest.raises(dashboard.DiscoveryError, match=message):
        dashboard.resolve_selection(JOB_ID, str(tmp_path / "logs"))


def test_auto_discovery_never_uses_historical_accounting_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: [{"job_id": JOB_ID, "accounting": None}],
    )
    monkeypatch.setattr(dashboard, "slurm_job_metadata", lambda job_id: None)

    def unexpected_accounting(*args: object) -> dict[str, str]:
        pytest.fail(f"auto-discovery must not use explicit accounting fallback: {args}")

    monkeypatch.setattr(
        dashboard,
        "slurm_accounting_metadata",
        unexpected_accounting,
    )
    monkeypatch.setattr(
        dashboard,
        "accounting_log_selection",
        unexpected_accounting,
    )

    with pytest.raises(dashboard.DiscoveryError, match="no recent current-user"):
        dashboard.resolve_selection()


def test_validate_log_selection_rejects_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(dashboard.DiscoveryError, match="absolute"):
        dashboard.validate_log_selection(
            JOB_ID,
            stdout.relative_to(tmp_path),
            stderr.relative_to(tmp_path),
        )


def _rich_model(now: float) -> dict[str, object]:
    model = dashboard.parse_workflow("")
    model["done"].update({"00a": 1, "00b": 1, "00c": 1, "01": 2, "06": 1})
    model["started"].update({"00a": now - 900, "01": now - 600, "06": now - 90})
    model["finished"].update({"00a": now - 800, "01": now - 300})
    model["active"] = {
        "11": {
            "rule": "align_RNA_reads_with_STAR",
            "stage": "01",
            "wildcards": "sample_id=ABE_EV_2",
            "started": now - 180,
        },
        "12": {
            "rule": "merge_candidate_partitions",
            "stage": "07",
            "wildcards": "partition_id=chr1",
            "started": now - 60,
        },
    }
    model["samples"] = {
        "ABE_EV_2": {
            "last_stage": "00c",
            "last_finished": now - 500,
            "history": {"00a": 40, "00b": 20, "00c": 30},
        },
        "ABE_PUM1_2": {
            "last_stage": "06",
            "last_finished": now - 30,
            "history": {
                "00a": 35,
                "00b": 20,
                "00c": 30,
                "01": 100,
                "02": 40,
                "02b": 30,
                "03": 20,
                "04": 20,
                "05": 20,
                "06": 15,
            },
        },
        "ABE_EV_3": {
            "last_stage": "01",
            "last_finished": now - 100,
            "history": {"00a": 30, "00b": 20, "00c": 25, "01": 120},
        },
        "ABE_PUM1_3": {
            "last_stage": "01",
            "last_finished": now - 120,
            "history": {"00a": 30, "00b": 20, "00c": 25, "01": 150},
        },
        "unpaired": {"last_stage": None, "last_finished": None, "history": {}},
    }
    model["sample_order"] = list(model["samples"])
    model["recent"] = [
        ("8", "00a", "build_reference", now - 500),
        ("9", "01", "align_RNA_reads_with_STAR", now - 100),
    ]
    model["completion_times"] = [now - 100, now - 1200, now - 7200]
    model["last_completion"] = now - 100
    model["progress_done"] = 7
    model["progress_total"] = 20
    model["warning"] = "WorkflowError: injected fixture"
    return model


def _dashboard_identity() -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "run_root": f"/work/runs/{RUN_ID}",
        "source_commit": "a" * 40,
        "attempt": "attempt-" + "b" * 20,
        "attempt_status": "running",
        "runtime_hash": "c" * 64,
        "workflow_cores": "12",
        "step_threads": {"01": 2, "06": 1},
        "stage_concurrency": {"01": 6, "06": 6, "07": 12},
        "stage_memory_mb": {"01": 40960},
    }


def _slurm(*, terminal: bool = False, state: str = "RUNNING") -> dict[str, object]:
    return {
        "terminal": terminal,
        "state": state,
        "elapsed": "00:10:00",
        "left": "01:50:00",
        "cpus": "12",
        "partition": "compute",
        "node": "node01",
        "reason": "None",
        "ave_cpu": "00:01:00",
        "max_rss": "2048M",
        "disk_read": "1G",
        "disk_write": "512M",
        "exit_code": "0:0",
    }


def test_dashboard_model_and_text_views_cover_active_terminal_and_empty_states(
    capsys: pytest.CaptureFixture[str],
) -> None:
    now = 1_800_000_000.0
    model = _rich_model(now)
    identity = _dashboard_identity()

    assert dashboard.human_size(None) == "-"
    assert dashboard.human_size("invalid") == "invalid"
    assert dashboard.human_size("1024") == "1.0 KiB"
    assert dashboard.human_size("1G") == "1.0 GiB"
    assert dashboard.duration(None) == "-"
    assert dashboard.duration(-1) == "-"
    assert dashboard.duration(45) == "45s"
    assert dashboard.duration(125) == "2m05s"
    assert dashboard.duration(3725) == "1h02m05s"
    assert dashboard.duration(90061) == "1d01h01m"
    assert dashboard.sample_sort_key("sample2") < dashboard.sample_sort_key("sample10")
    assert dashboard.sample_sort_key("unpaired")[0] > 10
    assert dashboard.active_sample_info(model, "ABE_EV_2")[0] == "11"
    assert dashboard.active_sample_info(model, "missing") == (None, None)
    assert (
        dashboard.latest_sample_state(model, "ABE_PUM1_2", now)[1] == "READY FOR COHORT"
    )
    assert dashboard.latest_sample_state(model, "unpaired", now)[1] == "PENDING"
    assert dashboard.peer_runtime_comparison(model, "ABE_EV_2", now)[0].startswith(
        "LONGER THAN PEERS"
    )
    assert dashboard.peer_runtime_comparison(model, "unpaired", now) == (
        "NOT RUNNING",
        "dim",
    )
    assert dashboard.replicate_groups(model)
    assert dashboard.completion_velocity(model, now) == (1, 2)
    assert dashboard.progress_values(model) == (7, 20, 13)
    assert "7/20" in dashboard.progress_line(model, 100)

    rendered_groups = (
        dashboard.job_lines(_slurm(), identity, 100, {}),
        dashboard.pipeline_lines(model, now, 100),
        dashboard.current_lines(model, identity, now, 100),
        dashboard.sample_lines(model, now, 120),
        dashboard.sample_lane_lines(model, now, 120),
        dashboard.sample_lane_lines(model, now, 50),
        dashboard.compact_activity_lines(model, now, 90),
        dashboard.overview_lines(_slurm(), identity, model, 100),
        dashboard.workflow_frontier_lines(model, now, 90),
    )
    assert all(lines for lines in rendered_groups)
    title, provenance = dashboard.provenance_activity_lines(
        _slurm(), identity, model, now, 90
    )
    assert title == "FLOW, RUN ID & ACTIVITY"
    assert provenance
    terminal_title, terminal_lines = dashboard.activity_lines(
        model, _slurm(terminal=True, state="COMPLETED"), identity, now
    )
    assert terminal_title == "COMPLETION"
    assert any("final EMRYS inspection" in str(line) for line in terminal_lines)
    assert not any("Scientific report" in str(line) for line in terminal_lines)
    assert not any("Evidence report" in str(line) for line in terminal_lines)

    empty = dashboard.parse_workflow("")
    assert "No scientific owner" in dashboard.current_lines(empty, {}, now, 80)[0]
    assert "Waiting for sample jobs" in dashboard.sample_lines(empty, now, 80)[-1]
    assert dashboard.workflow_frontier_lines(empty, now, 80)

    dashboard.snapshot(JOB_ID, _slurm(), identity, model)
    snapshot = capsys.readouterr().out
    assert "EMRYS LIVE DASHBOARD" in snapshot
    assert "Reports:" not in snapshot
    assert "/products/report/" not in snapshot


class _FakeScreen:
    def __init__(
        self, height: int = 50, width: int = 160, keys: list[int] | None = None
    ):
        self.height = height
        self.width = width
        self.keys = iter(keys or [])
        self.writes: list[tuple[int, int, str, int, int]] = []
        self.refreshes = 0
        self.erases = 0

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def addnstr(self, y: int, x: int, text: str, limit: int, attr: int) -> None:
        self.writes.append((y, x, text, limit, attr))

    def erase(self) -> None:
        self.erases += 1

    def refresh(self) -> None:
        self.refreshes += 1

    def keypad(self, _enabled: bool) -> None:
        return None

    def timeout(self, _milliseconds: int) -> None:
        return None

    def getch(self) -> int:
        return next(self.keys)


def test_dashboard_drawing_and_rendering_support_wide_compact_and_small_screens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    attrs = dashboard.init_colors()
    model = _rich_model(1_800_000_000.0)
    identity = _dashboard_identity()
    screen = _FakeScreen()
    dashboard.render.attrs = attrs

    assert (
        dashboard.draw_box(
            screen,
            1,
            1,
            8,
            40,
            "FIXTURE",
            ["plain", ("styled", "green"), [("segment", "yellow")]] * 4,
            attrs,
            scroll=2,
            scrollable=True,
        )
        > 0
    )
    dashboard.safe_add(screen, -1, 0, "outside")
    dashboard.safe_add(screen, 0, screen.width, "outside")
    dashboard.render_overview(screen, JOB_ID, _slurm(), identity, model, 30, 0, 0)
    dashboard.render_details(screen, JOB_ID, _slurm(), identity, model, 30, 0, 0)
    dashboard.render(screen, JOB_ID, _slurm(), identity, model, 30, 0, "details", 0)
    dashboard.render(screen, JOB_ID, _slurm(), identity, model, 30, 0, "overview", 0)
    assert screen.writes
    assert screen.refreshes == 4

    compact = _FakeScreen(height=30, width=100)
    dashboard.render_overview(compact, JOB_ID, _slurm(), identity, model, 30, 0, 0)
    dashboard.render_details(compact, JOB_ID, _slurm(), identity, model, 30, 0, 0)
    small = _FakeScreen(height=10, width=60)
    dashboard.render_overview(small, JOB_ID, _slurm(), identity, model, 30, 0, 0)
    assert any("too small" in write[2] for write in small.writes)


def test_stream_cache_commands_and_slurm_queries_cover_success_and_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_command_bytes = dashboard.command_bytes
    real_command_text = dashboard.command_text
    outputs = iter((b"5\n", b"hello", b"3\n", b"bye"))
    monkeypatch.setattr(
        dashboard, "command_bytes", lambda *_args, **_kwargs: next(outputs)
    )
    cache = dashboard.StreamCache("/remote/log")
    assert cache.sync()
    assert cache.text() == "hello"
    assert cache.sync()
    assert cache.text() == "bye"

    monkeypatch.setattr(dashboard, "command_bytes", lambda *_args, **_kwargs: None)
    assert not dashboard.StreamCache("missing").sync()
    monkeypatch.setattr(
        dashboard, "command_bytes", lambda *_args, **_kwargs: b"bad-size"
    )
    assert not dashboard.StreamCache("invalid").sync()

    calls = iter(
        (
            "RUNNING|00:10:00|01:50:00|12|compute|node01|None",
            "605305.batch|00:01:00|2G|1G|512M",
        )
    )
    monkeypatch.setattr(
        dashboard, "command_text", lambda *_args, **_kwargs: next(calls)
    )
    live = dashboard.query_slurm(JOB_ID)
    assert live["state"] == "RUNNING"
    assert live["max_rss"] == "2G"

    calls = iter(("", "COMPLETED|0:0|00:20:00|12|node01"))
    monkeypatch.setattr(
        dashboard, "command_text", lambda *_args, **_kwargs: next(calls)
    )
    completed = dashboard.query_slurm(JOB_ID)
    assert completed["terminal"] is True
    assert completed["state"] == "COMPLETED"

    monkeypatch.setattr(dashboard, "command_bytes", real_command_bytes)
    monkeypatch.setattr(
        dashboard.subprocess,
        "run",
        lambda argv, **_kwargs: subprocess.CompletedProcess(argv, 0, b"value\n", b""),
    )
    assert real_command_text(["fixture"]) == "value"
    monkeypatch.setattr(
        dashboard.subprocess,
        "run",
        lambda argv, **_kwargs: subprocess.CompletedProcess(argv, 1, b"", b""),
    )
    assert dashboard.command_bytes(["fixture"]) is None


def test_dashboard_event_loop_handles_navigation_refresh_and_quit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keys = [
        ord("2"),
        ord("1"),
        9,
        ord("r"),
        dashboard.curses.KEY_UP,
        dashboard.curses.KEY_DOWN,
        dashboard.curses.KEY_PPAGE,
        dashboard.curses.KEY_NPAGE,
        dashboard.curses.KEY_HOME,
        dashboard.curses.KEY_RESIZE,
        ord("q"),
    ]
    screen = _FakeScreen(keys=keys)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(dashboard.curses, "curs_set", lambda _value: None)
    monkeypatch.setattr(dashboard, "query_slurm", lambda _job: _slurm())
    monkeypatch.setattr(dashboard, "render", lambda *_args, **_kwargs: None)
    arguments = SimpleNamespace(
        out="/missing/out",
        err="/missing/err",
        refresh=30,
        job_id=JOB_ID,
    )

    dashboard.dashboard(screen, arguments)

    assert screen.erases == 1
