from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "src/norad/orchestration/local_pilot/dashboard.py"
)
SPEC = importlib.util.spec_from_file_location("norad_dashboard_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


JOB_ID = 605305
RUN_ID = "run-" + "a" * 64


def _make_logs(log_dir: Path, job_id: int = JOB_ID) -> tuple[Path, Path]:
    log_dir.mkdir()
    stdout = log_dir / f"norad-local-pilot-{job_id}.out"
    stderr = log_dir / f"norad-local-pilot-{job_id}.err"
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
        "Step 01: 6 sample processes x 2 configured threads | "
        "12 workflow cores"
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
        "not yet reported by the NORAD control plan"
    )
    assert dashboard.stage_resource_text("01", identity, "legacy fallback") == (
        "Resource plan not yet reported by the NORAD control stream."
    )


def test_stream_cache_sanitizes_terminal_sequences_and_controls() -> None:
    cache = dashboard.StreamCache("unused")
    cache.data.extend(
        b"plain\x1b[31mred\x1b[0m\tkept\n"
        b"\x1b]52;c;clipboard-secret\x07after\x00\x08"
    )

    assert cache.text() == "plainred\tkept\nafter"


def test_positional_overrides_take_precedence_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []
    monkeypatch.setenv("NORAD_DASHBOARD_JOB_ID", "111")
    monkeypatch.setenv("NORAD_DASHBOARD_LOG_DIR", "/environment")

    def fake_resolve(*args: object) -> dict[str, object]:
        calls.append(args)
        return {
            "job_id": 222,
            "log_dir": "/explicit",
            "out": "/explicit/norad-local-pilot-222.out",
            "err": "/explicit/norad-local-pilot-222.err",
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


def test_validate_log_selection_accepts_exact_owned_regular_pair(tmp_path: Path) -> None:
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
        ("wrong.out", f"norad-local-pilot-{JOB_ID}.err", "stdout does not match"),
        (f"norad-local-pilot-{JOB_ID}.out", "wrong.err", "stderr does not match"),
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
    stdout = log_dir / f"norad-local-pilot-{JOB_ID}.out"
    stdout.symlink_to(target)
    stderr = log_dir / f"norad-local-pilot-{JOB_ID}.err"
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
        "out": "/logs/norad-local-pilot-605304.out",
        "err": "/logs/norad-local-pilot-605304.err",
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
            raise dashboard.DiscoveryError("not a NORAD wrapper job")
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
        lambda: [{
            "job_id": JOB_ID,
            "accounting": {
                "JobId": str(JOB_ID),
                "JobName": "norad-real-run",
                "JobState": "COMPLETED",
                "User": "2609214",
                "UID": str(os.getuid()),
                "StdOut": str(stdout),
                "StdErr": str(stderr),
            },
        }],
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
            f"{JOB_ID}|norad-real-run|COMPLETED+|2609214|{os.getuid()}\n"
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
            f"{JOB_ID}|norad-real-run|COMPLETED|2609214|{os.getuid()}|"
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
            f"{JOB_ID}|norad-real-run|COMPLETED|2609214|{os.getuid()}|"
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
        return f"{JOB_ID}|norad-real-run|COMPLETED|2609214|{os.getuid()}"

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
        return f"{JOB_ID}|norad-real-run|COMPLETED|2609214|{os.getuid()}"

    monkeypatch.setattr(dashboard, "command_text", fake_command)

    with pytest.raises(dashboard.DiscoveryError, match="pass LOG_DIR explicitly"):
        dashboard.resolve_selection(JOB_ID)


@pytest.mark.parametrize(
    ("accounting", "message"),
    [
        (
            f"{JOB_ID}|norad-real-run|RUNNING|2609214|{os.getuid()}",
            "is not terminal",
        ),
        (
            f"{JOB_ID}|norad-real-run|COMPLETED|someone-else|999999",
            "is not owned",
        ),
        (
            "\n".join(
                [
                    f"{JOB_ID}|norad-real-run|COMPLETED|2609214|{os.getuid()}",
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
        pytest.fail(
            f"auto-discovery must not use explicit accounting fallback: {args}"
        )

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


def test_report_locations_are_derived_only_from_valid_run_identity() -> None:
    run_root = f"/work/runs/{RUN_ID}"

    locations = dashboard.report_locations({"run_id": RUN_ID, "run_root": run_root})

    assert locations == {
        "directory": f"{run_root}/products/report/{RUN_ID}",
        "scientific": (
            f"{run_root}/products/report/{RUN_ID}/{RUN_ID}.scientific_report.html"
        ),
        "evidence": (
            f"{run_root}/products/report/{RUN_ID}/{RUN_ID}.evidence_report.html"
        ),
    }
    assert dashboard.report_locations(
        {"run_id": "../not-a-run", "run_root": run_root}
    ) is None
    assert dashboard.report_locations(
        {"run_id": RUN_ID, "run_root": "relative/run-root"}
    ) is None


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
