from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path

import pytest

from emrys.orchestration.run_coordinator import dashboard
from tests.orchestration.run_coordinator.test_slurm_submission import _scheduler_replies


JOB_ID = 605305
RUN_ID = "run-" + "a" * 64


def _make_logs(log_dir: Path, job_id: int = JOB_ID) -> tuple[Path, Path]:
    log_dir.mkdir()
    stdout = log_dir / f"emrys-local-pilot-{job_id}.out"
    stderr = log_dir / f"emrys-local-pilot-{job_id}.err"
    stdout.write_text("stdout\n", encoding="utf-8")
    stderr.write_text("stderr\n", encoding="utf-8")
    return stdout, stderr


def _accounting_replies(monkeypatch, *replies: str) -> list[list[str]]:
    calls = []
    responses = iter(replies)

    def command(argv: list[str], timeout: int = 10) -> str:
        assert argv[0] == "sacct"
        calls.append(argv)
        return next(responses)

    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setattr(dashboard._scheduler, "slurm_job_metadata", lambda _: None)
    monkeypatch.setattr(dashboard._scheduler, "command_text", command)
    return calls


def _blocked_stream_reader(monkeypatch: pytest.MonkeyPatch):
    entered, release = threading.Event(), threading.Event()
    read_stream = dashboard._read_stream
    calls = []

    def blocked(*arguments):
        calls.append(arguments[0])
        entered.set()
        assert release.wait(5)
        return read_stream(*arguments)

    monkeypatch.setattr(dashboard, "_read_stream", blocked)
    monkeypatch.setattr(dashboard, "_STREAM_WAIT_SECONDS", 0.01)
    return entered, release, calls


@pytest.mark.parametrize("matching_token", [True, False])
@pytest.mark.parametrize("prefix", ["emrys-local-pilot-", "emrys-"])
def test_request_specific_scheduler_stream_pair_admission(
    tmp_path: Path, matching_token: bool, prefix: str
) -> None:
    stdout = tmp_path / f"{prefix}{'a' * 32}-{JOB_ID}.out"
    stderr = tmp_path / f"{prefix}{('a' if matching_token else 'b') * 32}-{JOB_ID}.err"
    stdout.write_bytes(b"")
    stderr.write_bytes(b"")
    if matching_token:
        selected = dashboard.validate_log_selection(JOB_ID, str(stdout), str(stderr))
        assert (selected["out"], selected["err"]) == (str(stdout), str(stderr))
    else:
        with pytest.raises(
            dashboard._scheduler.DiscoveryError, match="stderr does not match"
        ):
            dashboard.validate_log_selection(JOB_ID, str(stdout), str(stderr))


def test_doctor_scheduler_stream_pair_admission(tmp_path: Path) -> None:
    stdout = tmp_path / f"emrys-doctor-{JOB_ID}.out"
    stderr = tmp_path / f"emrys-doctor-{JOB_ID}.err"
    stdout.write_bytes(b"")
    stderr.write_bytes(b"")
    selected = dashboard.validate_log_selection(JOB_ID, stdout, stderr)
    assert (selected["out"], selected["err"]) == (str(stdout), str(stderr))


@pytest.mark.parametrize("job_name", ["", "a,b", "-other", "unsafe\n", True, "x" * 129])
def test_invalid_expected_job_name_does_not_query_scheduler(monkeypatch, job_name):
    command = _scheduler_replies(monkeypatch, dashboard._scheduler)
    result = dashboard._scheduler.observe_job(
        JOB_ID, "/logs/out", "/logs/err", "alpha", job_name=job_name
    )
    command.assert_not_called()
    assert result["state"] == "UNKNOWN" and result["diagnostic"]


@pytest.mark.parametrize(
    "state", ["COMPLETING", "REQUEUED", "SUSPENDED", "RECONFIG_FAIL"]
)
def test_exact_queue_transition_states_remain_nonterminal(monkeypatch, state):
    _scheduler_replies(
        monkeypatch,
        dashboard._scheduler,
        f"{JOB_ID}|{os.getuid()}|{state}|alpha|/logs/out|/logs/err|None\n".encode(),
    )
    observed = dashboard._scheduler.observe_job(
        JOB_ID, "/logs/out", "/logs/err", "alpha"
    )
    assert observed["state"] == state and observed["terminal"] is False
    assert observed["source"] == "squeue" and observed["reason"] == "None"


@pytest.mark.parametrize(
    "state,exit_code,admitted",
    [
        ("COMPLETED", "0:0", True),
        ("FAILED", "255:0", True),
        ("CANCELLED by 0", "0:15", True),
        (f"CANCELLED by {os.getuid()}", "0:9", True),
        ("CANCELLED by user", "0:15", False),
        ("CANCELLED by 00", "0:15", False),
        ("FAILED", "", False),
        ("FAILED", "0", False),
        ("FAILED", "0:", False),
        ("FAILED", "00:0", False),
        ("FAILED", "0:09", False),
        ("FAILED", "-1:0", False),
        ("FAILED", "256:0", False),
        ("FAILED", "0:128", False),
        ("FAILED", "0:9:0", False),
        ("FAILED", "0:９", False),
    ],
)
def test_exact_accounting_requires_complete_state_and_canonical_exit_code(
    monkeypatch, state, exit_code, admitted
):
    _scheduler_replies(
        monkeypatch,
        dashboard._scheduler,
        b"",
        f"{JOB_ID}|{os.getuid()}|{state}|alpha|/logs/out|/logs/err|{exit_code}\n".encode(),
    )
    observed = dashboard._scheduler.observe_job(
        JOB_ID, "/logs/out", "/logs/err", "alpha"
    )
    if admitted:
        assert observed["state"] == state.split()[0] and observed["terminal"] is True
        assert observed["source"] == "sacct" and observed["exit_code"] == exit_code
    else:
        assert observed["state"] == "UNKNOWN" and observed["terminal"] is False
        assert observed["source"] is None and observed["diagnostic"]


@pytest.mark.parametrize(
    "cluster", ["all", "ALL", "alpha,beta", "-alpha", "alpha\n", ""]
)
def test_request_cluster_cannot_expand_or_redirect_query(monkeypatch, cluster):
    command = _scheduler_replies(monkeypatch, dashboard._scheduler)
    observed = dashboard._scheduler.observe_job(
        JOB_ID, "/logs/out", "/logs/err", cluster
    )
    command.assert_not_called()
    assert observed["state"] == "UNKNOWN" and observed["diagnostic"]


def test_accounting_nonterminal_record_is_not_current_queue_state(monkeypatch):
    _scheduler_replies(
        monkeypatch,
        dashboard._scheduler,
        b"",
        f"{JOB_ID}|{os.getuid()}|RUNNING|alpha|/logs/out|/logs/err|0:0\n".encode(),
    )
    observed = dashboard._scheduler.observe_job(
        JOB_ID, "/logs/out", "/logs/err", "alpha"
    )
    assert observed["state"] == "UNKNOWN" and "not terminal" in observed["diagnostic"]


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


@pytest.mark.parametrize("samples,partitions", [(1, 2), (9, 37)])
def test_workflow_counts_follow_complete_job_stats_for_arbitrary_project_sizes(
    samples, partitions
):
    total = samples + partitions + 1
    model = dashboard.parse_workflow(
        f"""Job stats:
job                                                   count
---------------------------------------------------  -------
align_RNA_reads_with_STAR                              {samples}
generate_partitioned_cohort_mpileup_VCFs                {partitions}
cohort_slice                                          1
total                                                 {total}
[Mon Sep 14 12:00:00 2026]
rule align_RNA_reads_with_STAR:
    jobid: 1
    wildcards: sample_id=first
[Mon Sep 14 12:01:00 2026]
Finished jobid: 1 (Rule: align_RNA_reads_with_STAR)
"""
    )
    assert model["expected"] == {"01": samples, "07": partitions, "FINAL": 1}
    assert dashboard.progress_values(model) == (1, total, total - 1)
    lines = _flatten_render_lines(
        dashboard.pipeline_lines(model, 1_800_000_000, 100)
    ).splitlines()
    alignment = next(line for line in lines if line.startswith("01 "))
    assert f"1/{samples}" in alignment
    assert ("DONE" in alignment) is (samples == 1)
    partitions_line = next(line for line in lines if line.startswith("07 "))
    assert f"0/{partitions}" in partitions_line


@pytest.mark.parametrize(
    "stats",
    [
        "",
        "Job stats:\njob count\n--- -----\nalign_RNA_reads_with_STAR 9\n",
        "Job stats:\njob count\n--- -----\nalign_RNA_reads_with_STAR 9\ntotal 2\n",
        "Job stats:\njob count\n--- -----\nalign_RNA_reads_with_STAR 1\nalign_RNA_reads_with_STAR 1\ntotal 2\n",
    ],
)
def test_missing_or_invalid_counts_never_invent_completion(stats):
    model = dashboard.parse_workflow(stats)
    model["done"]["01"] = 6
    model["done"]["07"] = 25
    model["active"]["10"] = {
        "stage": "01",
        "rule": "align_RNA_reads_with_STAR",
        "wildcards": "sample_id=only_seen",
        "started": None,
    }
    model["sample_order"] = ["only_seen"]
    model["samples"] = {"only_seen": {"history": {"06": 1}}}
    assert dashboard.progress_values(model) == (31, None, None)
    assert "total and remaining unknown" in dashboard.progress_line(model, 100)
    assert not any(
        line.endswith("DONE")
        for line in _flatten_render_lines(
            dashboard.pipeline_lines(model, 10, 100)
        ).splitlines()
    )
    assert "unknown waiting" in _flatten_render_lines(
        dashboard.current_lines(model, {}, 10, 100)
    )
    assert "1/?" in _flatten_render_lines(dashboard.sample_lane_lines(model, 10, 100))
    assert "1/? samples completed Step 06" in _flatten_render_lines(
        dashboard.workflow_frontier_lines(model, 10, 100)
    )
    assert dashboard.workflow_phase(model) == (2, "SAMPLE PROCESSING (observed)")
    dashboard.activity_lines(model, _slurm(terminal=True), {}, 10)


def test_finished_log_without_run_evidence_is_not_presented_as_active_waiting():
    model = dashboard.parse_workflow(
        """Finished jobid: 1 (Rule: rank_cohort_candidates_with_paired_CMH)
Finished jobid: 2 (Rule: project_candidate_scientific_context)
Finished jobid: 3 (Rule: local_pipeline_slice)
36 of 36 steps (100%) done
"""
    )

    assert model["log_done"] is True
    assert dashboard.progress_line(model, 100) == (
        "Workflow log finished; Run completion unverified"
    )
    assert dashboard.workflow_phase(model) == (4, "LOG FINISHED; RUN UNVERIFIED")
    pipeline = _flatten_render_lines(dashboard.pipeline_lines(model, 10, 100))
    rows = pipeline.splitlines()
    for key in ("09", "10"):
        row = next(line for line in rows if line.startswith(key))
        assert "1/?" in row and row.endswith("OBSERVED")
    report = next(line for line in rows if line.startswith("REPORT"))
    assert "0/?" in report and report.endswith("NOT OBSERVED")
    assert "OBSERVED" in pipeline and "NOT OBSERVED" in pipeline
    assert "WAITING" not in pipeline and "PENDING" not in pipeline


def test_expected_counts_are_fallback_context_not_fabricated_global_progress():
    expected = {"01": 12, "06": 12, "07": 40}
    model = dashboard.parse_workflow(
        "Job stats:\njob count\n--- -----\nalign_RNA_reads_with_STAR 2\ntotal 2\n",
        expected=expected,
    )
    assert model["expected"] == {"01": 2, "06": 12, "07": 40}
    assert expected == {"01": 12, "06": 12, "07": 40}
    assert dashboard.progress_values(model) == (0, 2, 2)
    without_stats = dashboard.parse_workflow("", expected=expected)
    assert dashboard.progress_values(without_stats) == (0, None, None)


@pytest.mark.parametrize(
    "timestamp",
    [
        "[Mon Xxx 14 12:00:00 2026]",
        "[Mon Sep 99 12:00:00 2026]",
        "[Mon Sep 14 99:00:00 2026]",
    ],
)
def test_current_analysis_rules_unknown_rules_and_invalid_timestamps_are_safe(
    timestamp,
):
    model = dashboard.parse_workflow(
        f"""[Mon Sep 14 12:00:00 2026]
rule analysis_owner:
    jobid: 1
    wildcards: analysis_owner=emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1
[Mon Sep 14 12:00:01 2026]
Finished jobid: 1 (Rule: analysis_owner)
Finished jobid: 1 (Rule: analysis_owner)
{timestamp}
rule analysis_owner:
    jobid: 2
    wildcards: analysis_owner=custom.owner
rule unfamiliar_future_rule:
    jobid: 3
    wildcards: sample_id=third
WorkflowError: real failure text
""",
        rule_stages={"custom.owner": "10"},
    )
    assert model["done"]["09"] == 1
    assert model["samples"]["third"]["history"] == {}
    assert model["active"]["2"]["stage"] == "10"
    assert model["active"]["2"]["started"] is None
    assert model["active"]["3"]["stage"] == "?"
    assert model["warning"] == "WorkflowError: real failure text"
    assert "Unmapped rule" in _flatten_render_lines(
        dashboard.current_lines(model, {}, 10, 100)
    )
    dashboard.pipeline_lines(model, 10, 100)
    frontier = _flatten_render_lines(dashboard.workflow_frontier_lines(model, 10, 100))
    assert "Unmapped active rules" in frontier
    assert "unfamiliar_future_rule" in frontier
    assert dashboard.workflow_phase(model) == (3, "COHORT ANALYSIS (observed)")


def test_dashboard_processing_rule_mapping_matches_current_backend_contract():
    import json

    profile = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "src/emrys/workflow/contracts/local_cmh_v2.json"
        ).read_text()
    )
    for task in profile["owner_tasks"]:
        assert dashboard.RULE_TO_STAGE[task["rule_name"]] == task["step_id"]
    assert dashboard.RULE_TO_STAGE["cohort_slice"] == "FINAL"
    assert dashboard.RULE_TO_STAGE["local_pipeline_slice"] == "FINAL"


def test_parse_and_render_dynamic_per_stage_resource_plan() -> None:
    control = f"""
Run ID: {RUN_ID}
Run root: /work/runs/{RUN_ID}
Package SHA-256: {"d" * 64}
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
    assert identity["package_sha256"] == "d" * 64

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


def test_stream_cache_retains_full_history_and_reads_only_appended_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "stream.log"
    original = b"old history\n" * 20000
    path.write_bytes(original)
    reads = []
    read = dashboard.os.read

    def recorded_read(descriptor, size):
        data = read(descriptor, size)
        reads.append((size, len(data)))
        return data

    monkeypatch.setattr(dashboard.os, "read", recorded_read)
    cache = dashboard.StreamCache(path)
    assert cache.sync()
    assert cache.data == original and cache.offset == len(original)
    assert max(size for size, _ in reads) <= 64 * 1024
    assert sum(count for _, count in reads) == len(original)
    assert cache.observed_at is not None and not cache.pending
    reads.clear()
    assert cache.sync() and reads == []
    with path.open("ab") as stream:
        stream.write(b"new history\n")
    assert cache.sync()
    assert cache.data == original + b"new history\n"
    assert sum(count for _, count in reads) == len(b"new history\n")
    assert "content not verified" in cache.diagnostic


@pytest.mark.parametrize("change", ["replace", "truncate", "rewrite"])
def test_stream_cache_resets_changed_generations(tmp_path: Path, change: str) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"original bytes\n")
    cache = dashboard.StreamCache(path)
    assert cache.sync()
    if change == "replace":
        path.rename(tmp_path / "previous.log")
        replacement = b"replacement is longer than the old stream\n"
    elif change == "truncate":
        replacement = b"short\n"
    else:
        replacement = b"modified bytes\n"
    path.write_bytes(replacement)
    os.utime(path, ns=(path.stat().st_atime_ns, path.stat().st_mtime_ns + 1000000))
    assert cache.sync() and cache.data == replacement
    assert cache.generation_changed
    assert {"replace": "replaced", "truncate": "truncated", "rewrite": "changed"}[
        change
    ] in cache.diagnostic


@pytest.mark.parametrize("defect", ["missing", "symlink", "directory", "fifo", "owner"])
def test_stream_cache_failed_admission_clears_retained_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"old bytes\n")
    cache = dashboard.StreamCache(path)
    assert cache.sync()
    path.unlink()
    if defect == "symlink":
        target = tmp_path / "target.log"
        target.write_bytes(b"must not follow")
        path.symlink_to(target)
    elif defect == "directory":
        path.mkdir()
    elif defect == "fifo":
        os.mkfifo(path)
    elif defect == "owner":
        path.write_bytes(b"wrong owner")
        actual_uid = os.getuid()
        monkeypatch.setattr(dashboard.os, "getuid", lambda: actual_uid + 1)
    assert not cache.sync()
    assert cache.text() == "" and cache.offset == 0 and cache.observed_at is None
    assert cache.diagnostic.startswith("Unavailable:")


def test_stream_cache_refuses_relative_and_symlinked_ancestor_paths(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "real"
    parent.mkdir()
    path = parent / "stream.log"
    path.write_bytes(b"must not follow")
    alias = tmp_path / "alias"
    alias.symlink_to(parent, target_is_directory=True)
    for selected in (Path("relative.log"), alias / path.name):
        cache = dashboard.StreamCache(selected)
        assert not cache.sync() and cache.text() == ""


@pytest.mark.parametrize("restricted", ["ancestor", "log-directory"])
def test_stream_cache_reads_through_search_only_directories(
    tmp_path: Path, restricted: str
) -> None:
    ancestor = tmp_path / "search-only"
    ancestor.mkdir()
    stdout, stderr = _make_logs(ancestor / "logs")
    directory = ancestor if restricted == "ancestor" else stdout.parent
    directory.chmod(0o111)
    cache = dashboard.StreamCache(stdout)
    try:
        assert stdout.read_bytes() == b"stdout\n"
        selected = dashboard.validate_log_selection(JOB_ID, str(stdout), str(stderr))
        assert selected["out"] == str(stdout)
        assert cache.sync() and cache.text() == "stdout\n"
        assert cache.observed_at is not None and not cache.pending
    finally:
        cache.close()
        directory.chmod(0o700)


def test_stream_cache_refuses_foreign_file_inside_owned_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"foreign file bytes")
    real_stat = dashboard.os.stat

    def foreign_file_stat(selected, **kwargs):
        state = real_stat(selected, **kwargs)
        if selected == path.name and kwargs.get("follow_symlinks") is False:
            fields = list(state)
            fields[4] += 1
            return os.stat_result(fields)
        return state

    monkeypatch.setattr(dashboard.os, "stat", foreign_file_stat)
    cache = dashboard.StreamCache(path)
    assert not cache.sync() and cache.text() == ""
    assert "regular file owned by the current UID" in cache.diagnostic


@pytest.mark.parametrize("failure", ["error", "early-eof"])
def test_stream_cache_read_failure_clears_prior_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"old bytes")
    cache = dashboard.StreamCache(path)
    assert cache.sync()
    with path.open("ab") as stream:
        stream.write(b"new bytes")

    def failed_read(*_args):
        if failure == "error":
            raise OSError("fixture read failure")
        return b""

    monkeypatch.setattr(dashboard.os, "read", failed_read)
    assert not cache.sync() and cache.text() == "" and cache.offset == 0
    assert cache.observed_at is None and cache.diagnostic.startswith("Unavailable:")


@pytest.mark.parametrize("replace", ["file", "parent"])
def test_stream_cache_rejects_replacement_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replace: str
) -> None:
    parent = tmp_path / "logs"
    parent.mkdir()
    path = parent / "stream.log"
    path.write_bytes(b"old generation\n")
    cache = dashboard.StreamCache(path)
    assert cache.sync()
    with path.open("ab") as stream:
        stream.write(b"appended data\n")
    read = dashboard.os.read
    swapped = False

    def replace_during_read(descriptor, size):
        nonlocal swapped
        data = read(descriptor, size)
        if not swapped:
            swapped = True
            if replace == "file":
                path.rename(parent / "old.log")
            else:
                parent.rename(tmp_path / "old-logs")
                parent.mkdir()
            path.write_bytes(b"replacement generation\n")
        return data

    monkeypatch.setattr(dashboard.os, "read", replace_during_read)
    assert not cache.sync() and swapped
    assert cache.text() == "" and cache.observed_at is None
    assert "changed while read" in cache.diagnostic


def test_stream_cache_captures_growth_for_the_next_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"first generation\n")
    read = dashboard.os.read
    appended = False

    def append_during_read(descriptor, size):
        nonlocal appended
        data = read(descriptor, size)
        if not appended:
            appended = True
            with path.open("ab") as stream:
                stream.write(b"later bytes\n")
        return data

    monkeypatch.setattr(dashboard.os, "read", append_during_read)
    cache = dashboard.StreamCache(path)
    assert cache.sync() and cache.text() == "first generation\n"
    assert cache.sync() and cache.text() == "first generation\nlater bytes\n"


def test_stream_cache_bounds_wait_and_keeps_one_stalled_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"prior history\n")
    cache = dashboard.StreamCache(path)
    assert cache.sync()
    previous_date = cache.observed_at
    with path.open("ab") as stream:
        stream.write(b"new history\n")
    entered, release, calls = _blocked_stream_reader(monkeypatch)
    started = time.monotonic()
    try:
        assert not cache.sync() and entered.wait(1)
        reader = cache._reader
        assert reader.daemon
        assert not cache.sync() and cache._reader is reader and cache.pending
        assert time.monotonic() - started < 1
        assert calls == [str(path)]
        assert cache.text() == "prior history\n" and cache.observed_at == previous_date
        assert "Read pending" in cache.diagnostic
    finally:
        release.set()
        cache._reader.join(2)
    assert cache.sync() and not cache.pending
    assert cache.text() == "prior history\nnew history\n"


def test_stream_cache_close_never_waits_or_starts_another_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"history")
    entered, release, calls = _blocked_stream_reader(monkeypatch)
    cache = dashboard.StreamCache(path)
    try:
        assert not cache.sync() and entered.wait(1)
        reader = cache._reader
        started = time.monotonic()
        cache.close()
        assert time.monotonic() - started < 0.5
        assert not cache.sync() and cache.pending and calls == [str(path)]
    finally:
        release.set()
        cache._reader.join(2)
    assert not cache.sync() and cache.text() == "" and calls == [str(path)]
    assert cache._reader is reader


def test_stream_cache_close_serializes_start_without_waiting_for_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "stream.log"
    path.write_bytes(b"history")
    cache = dashboard.StreamCache(path)
    starting, allow_start = threading.Event(), threading.Event()
    reading, allow_read = threading.Event(), threading.Event()
    closing, closed = threading.Event(), threading.Event()
    real_thread, real_read = threading.Thread, dashboard._read_stream

    class GatedStart(real_thread):
        def start(self):
            starting.set()
            assert allow_start.wait(5)
            super().start()

    def blocked_read(*arguments):
        reading.set()
        assert allow_read.wait(5)
        return real_read(*arguments)

    def close():
        closing.set()
        cache.close()
        closed.set()

    sync_thread = real_thread(target=cache.sync)
    close_thread = real_thread(target=close)
    monkeypatch.setattr(dashboard.threading, "Thread", GatedStart)
    monkeypatch.setattr(dashboard, "_read_stream", blocked_read)
    try:
        sync_thread.start()
        assert starting.wait(1)
        close_thread.start()
        assert closing.wait(1)
        assert not closed.wait(0.02)
        allow_start.set()
        assert reading.wait(1) and closed.wait(1)
        assert cache.pending and not cache.sync()
    finally:
        allow_start.set()
        allow_read.set()
        sync_thread.join(2)
        close_thread.join(2)
        if cache._reader is not None:
            cache._reader.join(2)
    assert not cache.sync() and cache.text() == "" and cache.observed_at is None


def test_explicit_job_failure_does_not_fall_back_to_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_explicit(
        job_id: int,
        log_dir: str | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        del log_dir, kwargs
        raise dashboard._scheduler.DiscoveryError(f"invalid explicit job {job_id}")

    def unexpected_discovery() -> list[int]:
        pytest.fail("explicit selection must not call candidate discovery")

    monkeypatch.setattr(dashboard, "scheduler_selection", reject_explicit)
    monkeypatch.setattr(dashboard, "scheduler_candidates", unexpected_discovery)

    with pytest.raises(
        dashboard._scheduler.DiscoveryError, match="invalid explicit job 605305"
    ):
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

    with pytest.raises(dashboard._scheduler.DiscoveryError, match=message):
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

    with pytest.raises(dashboard._scheduler.DiscoveryError, match="real regular file"):
        dashboard.validate_log_selection(JOB_ID, stdout, stderr)


def test_validate_log_selection_rejects_symlinked_directory(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    stdout, stderr = _make_logs(real_dir)
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)

    with pytest.raises(dashboard._scheduler.DiscoveryError, match="real directory"):
        dashboard.validate_log_selection(
            JOB_ID, linked_dir / stdout.name, linked_dir / stderr.name
        )


def test_scheduler_candidates_prefer_live_then_recent_root_allocations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_command(argv: list[str], timeout: int = 10) -> str:
        del timeout
        assert argv[argv.index("-u") + 1] == str(os.getuid())
        if argv[0] == "squeue":
            return "605305|RUNNING\n605300|PENDING\n605305.batch|RUNNING"
        if argv[0] == "sacct":
            assert "--duplicates" in argv
            return (
                "605305|RUNNING\n605304|COMPLETED\n605304.batch|COMPLETED\n"
                "605303|FAILED"
            )
        pytest.fail(f"unexpected command: {argv}")

    monkeypatch.setenv("USER", "2609214")
    monkeypatch.setenv("LOGNAME", "another-user")
    monkeypatch.setattr(dashboard._scheduler, "command_text", fake_command)

    assert [candidate["job_id"] for candidate in dashboard.scheduler_candidates()] == [
        605305,
        605300,
        605304,
        605303,
    ]


def test_auto_discovery_refuses_multiple_candidates_without_probing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: [
            {"job_id": 605305, "accounting": None},
            {"job_id": 605304, "accounting": None},
        ],
    )
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidate_selection",
        lambda _candidate: pytest.fail("ambiguous candidates must not be probed"),
    )

    with pytest.raises(
        dashboard._scheduler.DiscoveryError,
        match="candidates: 605305, 605304",
    ):
        dashboard.resolve_selection()


def test_auto_discovery_selects_the_only_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = {"job_id": 605304, "accounting": None}
    selected = {"job_id": 605304, "out": "/logs/out", "err": "/logs/err"}
    monkeypatch.setattr(dashboard, "scheduler_candidates", lambda: [candidate])
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidate_selection",
        lambda observed: (
            selected if observed is candidate else pytest.fail("wrong job")
        ),
    )

    assert dashboard.resolve_selection() is selected


def test_exact_job_name_selection_reuses_scheduler_identity_owner(monkeypatch):
    selected = {"job_id": JOB_ID, "out": "/logs/out", "err": "/logs/err"}
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: [{"job_id": JOB_ID, "job_name": "emrys-request", "accounting": None}],
    )
    observed = []

    def select(job_id, **options):
        observed.append((job_id, options))
        return selected

    monkeypatch.setattr(dashboard, "scheduler_selection", select)
    assert dashboard.resolve_named_selection("emrys-request") is selected
    assert observed == [
        (JOB_ID, {"accounting_metadata": None, "job_name": "emrys-request"})
    ]


def test_exact_job_name_selection_refuses_ambiguous_ids(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: [
            {"job_id": 41, "job_name": "emrys-request", "accounting": None},
            {"job_id": 42, "job_name": "emrys-request", "accounting": None},
        ],
    )
    with pytest.raises(dashboard._scheduler.DiscoveryError, match="ambiguous"):
        dashboard.resolve_named_selection("emrys-request")


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
        dashboard._scheduler,
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


@pytest.mark.parametrize(
    "record",
    [
        f"UserId=user({os.getuid()}) JobState=RUNNING",
        f"JobId={JOB_ID + 1} UserId=user({os.getuid()}) JobState=RUNNING",
        f"JobId={JOB_ID} JobId={JOB_ID} UserId=user({os.getuid()}) JobState=RUNNING",
        f"JobId={JOB_ID} UserId=user({os.getuid()}) JobState=RUNNING\n"
        f"JobId={JOB_ID} UserId=user({os.getuid()}) JobState=RUNNING",
        f"JobId={JOB_ID} UserId=user JobState=RUNNING",
        f"JobId={JOB_ID} UserId=user({os.getuid() + 1}) JobState=RUNNING",
        f"JobId={JOB_ID} UserId=user({os.getuid()})",
    ],
)
def test_live_selection_rejects_unproven_identity_without_accounting_fallback(
    monkeypatch: pytest.MonkeyPatch,
    record: str,
) -> None:
    monkeypatch.setenv("USER", "user")
    monkeypatch.setenv("LOGNAME", "user")
    calls = []

    def command(argv: list[str], timeout: int = 10) -> str:
        calls.append(argv)
        return record

    monkeypatch.setattr(dashboard._scheduler, "command_text", command)
    with pytest.raises(dashboard._scheduler.DiscoveryError):
        dashboard.scheduler_selection(JOB_ID, allow_accounting_fallback=True)
    assert len(calls) == 1
    assert calls[0][0] == "scontrol"


def test_explicit_completed_job_uses_exact_accounting_streams_without_log_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    calls = _accounting_replies(
        monkeypatch,
        f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}|{stdout}|{stderr}||||",
    )

    assert dashboard.resolve_selection(JOB_ID) == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
        "selection_source": "sacct-stdout-stderr",
    }
    assert len(calls) == 1
    assert calls[0][calls[0].index("-j") + 1] == str(JOB_ID)
    assert ",StdOut,StdErr" in calls[0][-1]


def test_explicit_log_dir_must_agree_with_exact_accounting_streams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "scheduler-logs")
    requested = tmp_path / "requested-logs"
    requested.mkdir()
    calls = _accounting_replies(
        monkeypatch,
        f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}|{stdout}|{stderr}||||",
    )

    with pytest.raises(dashboard._scheduler.DiscoveryError, match="LOG_DIR disagrees"):
        dashboard.resolve_selection(JOB_ID, str(requested))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "accounting",
    [
        pytest.param(
            f"{JOB_ID}|emrys-real-run|COMPLETED+|2609214|{os.getuid()}||||\n"
            f"{JOB_ID}.batch|batch|COMPLETED|2609214|{os.getuid()}",
            id="completed-plus-with-batch",
        ),
        pytest.param(
            f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}||||",
            id="completed",
        ),
    ],
)
def test_exact_accounting_uses_one_basic_fallback_when_stream_fields_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    accounting: str,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    calls = _accounting_replies(monkeypatch, "", accounting)

    assert dashboard.resolve_selection(JOB_ID, str(tmp_path / "logs")) == {
        "job_id": JOB_ID,
        "log_dir": str(tmp_path / "logs"),
        "out": str(stdout),
        "err": str(stderr),
        "selection_source": "sacct+explicit-log-dir",
    }
    assert [argv[-1] for argv in calls] == [
        "--format=JobIDRaw,JobName,State,User,UID,StdOut,StdErr,ExitCode,Elapsed,AllocCPUS,NodeList",
        "--format=JobIDRaw,JobName,State,User,UID,ExitCode,Elapsed,AllocCPUS,NodeList",
    ]


def test_explicit_job_without_log_dir_fails_if_accounting_has_no_stream_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _accounting_replies(
        monkeypatch,
        "",
        f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}||||",
    )

    with pytest.raises(
        dashboard._scheduler.DiscoveryError, match="pass LOG_DIR explicitly"
    ):
        dashboard.resolve_selection(JOB_ID)


@pytest.mark.parametrize(
    ("accounting", "message"),
    [
        (
            f"{JOB_ID}|emrys-real-run|RUNNING|2609214|{os.getuid()}||||",
            "is not terminal",
        ),
        (
            f"{JOB_ID}|emrys-real-run|COMPLETED|someone-else|999999||||",
            "is not owned",
        ),
        (
            "\n".join(
                [
                    f"{JOB_ID}|emrys-real-run|COMPLETED|2609214|{os.getuid()}||||",
                    f"{JOB_ID}|duplicate|COMPLETED|2609214|{os.getuid()}||||",
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
    _accounting_replies(monkeypatch, "", accounting)

    with pytest.raises(dashboard._scheduler.DiscoveryError, match=message):
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
    monkeypatch.setattr(dashboard._scheduler, "slurm_job_metadata", lambda job_id: None)

    def unexpected_accounting(*args: object) -> dict[str, str]:
        pytest.fail(f"auto-discovery must not use explicit accounting fallback: {args}")

    monkeypatch.setattr(
        dashboard._scheduler,
        "slurm_accounting_metadata",
        unexpected_accounting,
    )
    monkeypatch.setattr(
        dashboard,
        "accounting_log_selection",
        unexpected_accounting,
    )

    with pytest.raises(
        dashboard._scheduler.DiscoveryError, match="metadata is unavailable"
    ):
        dashboard.resolve_selection()


def test_validate_log_selection_rejects_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout, stderr = _make_logs(tmp_path / "logs")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(dashboard._scheduler.DiscoveryError, match="absolute"):
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
        "package_sha256": "a" * 64,
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


def test_dashboard_model_and_text_views_cover_active_terminal_and_empty_states() -> (
    None
):
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


def _rendered_dashboard(*, height=50, width=160, selected="overview", terminal=False):
    model = _rich_model(1_800_000_000.0)
    view = dashboard.dashboard_view(
        JOB_ID,
        _slurm(terminal=terminal, state="TIMEOUT" if terminal else "RUNNING"),
        _dashboard_identity(),
        model,
        height=height,
        width=width,
        view=selected,
        work_scroll=0,
        now=1_800_000_000.0,
    )
    return "\n".join(
        "".join(character for character, _ in row)
        for row in dashboard.render_view(view)
    )


def test_dashboard_rendering_supports_wide_compact_and_small_screens() -> None:
    for selected in ("overview", "details"):
        text = _rendered_dashboard(selected=selected)
        assert "PIPELINE" in text and "CURRENT WORK" in text

    compact_text = "\n".join(
        _rendered_dashboard(height=30, width=100, selected=selected)
        for selected in ("overview", "details")
    )
    for label in (
        "State:",
        "Slurm placement:",
        "Batch per-task maxima:",
        "Batch CPU / sample:",
        "Run:",
        "Code / attempt:",
        "Run root:",
    ):
        assert label in compact_text
    assert "too small" in _rendered_dashboard(height=10, width=60)


def test_terminal_timeout_never_presents_stale_work_as_pending_or_running() -> None:
    now = 1_800_000_000.0
    model = _rich_model(now)
    slurm = _slurm(terminal=True, state="TIMEOUT")
    identity = _dashboard_identity()

    assert dashboard.latest_sample_state(model, "ABE_EV_2", now, "TIMEOUT") == (
        "01",
        "INTERRUPTED",
        "-",
    )
    assert dashboard.latest_sample_state(model, "unpaired", now, "TIMEOUT")[1] == (
        "NOT REACHED"
    )
    pipeline = _flatten_render_lines(
        dashboard.pipeline_lines(model, now, 100, terminal_state="TIMEOUT")
    )
    assert "INTERRUPTED (1)" in pipeline
    assert "NOT REACHED" in pipeline
    assert "RUNNING" not in pipeline
    assert "PENDING" not in pipeline
    lanes = _flatten_render_lines(
        dashboard.sample_lane_lines(model, now, 120, "TIMEOUT")
    )
    assert "[!] interrupted" in lanes
    assert "[-] not reached" in lanes
    assert "job ended before all samples were ready" in lanes
    assert "ended this job in TIMEOUT" in _flatten_render_lines(
        dashboard.current_lines(model, identity, now, 100, terminal_state="TIMEOUT")
    )
    title, activity = dashboard.activity_lines(model, slurm, identity, now)
    assert title == "JOB ENDED"
    assert "scheduler termination alone does not establish recovery" in str(activity)

    rendered = _rendered_dashboard(selected="details", terminal=True)
    assert "JOB ENDED" in rendered
    assert "INTERRUPTED" in rendered
    assert "PENDING" not in rendered


def test_scheduler_command_transport_covers_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_command_bytes = dashboard._scheduler.command_bytes
    real_command_text = dashboard._scheduler.command_text
    monkeypatch.setattr(dashboard._scheduler, "command_bytes", real_command_bytes)
    monkeypatch.setattr(
        dashboard._scheduler.subprocess,
        "run",
        lambda argv, **_kwargs: subprocess.CompletedProcess(argv, 0, b"value\n", b""),
    )
    assert real_command_text(["fixture"]) == "value"
    monkeypatch.setattr(
        dashboard._scheduler.subprocess,
        "run",
        lambda argv, **_kwargs: subprocess.CompletedProcess(argv, 1, b"", b""),
    )
    assert dashboard._scheduler.command_bytes(["fixture"]) is None


@pytest.mark.parametrize("usage", ["complete", "unavailable"])
def test_dashboard_resource_labels_preserve_batch_scope_and_unknown(usage):
    slurm = {
        "state": "PENDING" if usage == "unavailable" else "RUNNING",
        "cpus": "4",
        "partition": "compute",
        "node": "node1",
    }
    if usage == "complete":
        slurm.update(
            max_rss="1024K",
            disk_read="8M",
            disk_write="0",
            ave_cpu="00:00:02",
            usage_observed_at="2026-09-15T12:00:00+00:00",
            usage_diagnostic=None,
        )
    else:
        slurm["usage_diagnostic"] = "Exact local batch-step usage is unavailable"
    detailed = _flatten_render_lines(dashboard.job_lines(slurm, {}, 180, {}))
    overview = _flatten_render_lines(
        dashboard.overview_lines(slurm, {}, dashboard.parse_workflow(""), 180)
    )
    for text in (detailed, overview):
        assert "Slurm placement" in text and "Allocation:" not in text
        assert "peak RSS" not in text and "I/O" not in text
    if usage == "complete":
        assert (
            "Batch per-task maxima: RSS 1.0 MiB | read 8.0 MiB | written 0.0 B"
            in detailed
        )
        assert (
            "average task CPU time 00:00:02; as of 2026-09-15T12:00:00+00:00"
            in detailed
        )
        assert "per-task max RSS 1.0 MiB" in overview
    else:
        assert slurm["usage_diagnostic"] in detailed and "as of unknown" in detailed
        assert "usage unknown" in overview


@pytest.mark.parametrize("value", ["1.2.3M", ".K", "..", "unknown"])
def test_dashboard_malformed_raw_usage_remains_printable(value):
    assert dashboard.human_size(value) == value
    text = _flatten_render_lines(dashboard.job_lines({"max_rss": value}, {}, 180, {}))
    assert value in text


def test_unbounded_numeric_diagnostics_remain_unknown():
    huge = "9" * 5000
    trace = (
        "Job stats:\njob count\nalign_RNA_reads_with_STAR "
        + huge
        + "\ntotal "
        + huge
        + "\n"
        + huge
        + " of "
        + huge
        + " steps (10%) done\n"
    )
    observed = dashboard.parse_workflow(trace)
    assert observed["expected"] == {} and observed["progress_total"] is None
    identity = dashboard.parse_identity("Stage concurrency:\n  Step 01: " + huge + "\n")
    assert identity["stage_concurrency"] == {}
