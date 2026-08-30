"""Focused boundaries for the retained real-tool Slurm E2E driver."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.tools import real_synthetic_e2e as driver


def _argv(root: Path, *, execute: bool = False) -> list[str]:
    values = [
        "--profile",
        "130",
        "--repo-root",
        str(root / "repo"),
        "--operator-root",
        str(root / "operator"),
        "--runtime-prefix",
        str(root / "runtime"),
        "--rscript",
        str(root / "Rscript"),
        "--renv-library",
        str(root / "renv"),
        "--storage-compute-launcher-json",
        json.dumps(["/usr/bin/true"]),
        "--slurm-partition",
        "emrys-ci",
        "--slurm-memory",
        "6G",
    ]
    return [*values, "--execute"] if execute else values


def _plan(workspace: Path) -> str:
    return "\n".join(
        (
            f"Run root: {workspace}/runs/run-{'a' * 64}",
            "Reporting: automatic after scientific work",
            "Dry-run complete; no workspace state was written.",
        )
    )


def test_cli_defaults_to_a_no_write_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    arguments = driver.build_parser().parse_args(_argv(tmp_path))
    assert arguments.execute is False
    assert arguments.slurm_memory == 6144
    assert driver.main(_argv(tmp_path)) == 0
    output = capsys.readouterr().out
    assert '"operation": "plan"' in output
    assert "Dry-run complete; no directories or files were created." in output
    assert not (tmp_path / "operator").exists()


def test_operator_root_is_external_empty_and_never_adopts_contents(tmp_path: Path) -> None:
    repo, operator = tmp_path / "repo", tmp_path / "operator"
    repo.mkdir()
    operator.mkdir()
    admitted = driver.require_operator_root(operator, repo)
    assert admitted.root == operator.resolve()
    assert not any(operator.iterdir())
    marker = operator / "keep.txt"
    marker.write_text("keep\n", encoding="utf-8")
    with pytest.raises(driver.DriverError, match="must be empty"):
        driver.require_operator_root(operator, repo)
    assert marker.read_text() == "keep\n"


def test_launcher_adapters_and_default_resource_projection(tmp_path: Path) -> None:
    launcher = tmp_path / "srun"
    launcher.write_text("#!/bin/sh\n", encoding="utf-8")
    launcher.chmod(0o755)
    assert driver.parse_launcher(json.dumps([str(launcher), "--nodes=1"])) == (
        str(launcher),
        "--nodes=1",
    )
    python = Path("/runtime/bin/python")
    java = Path("/runtime/bin/java")
    assert b"importlib.metadata" in driver.rseqc_adapter_bytes(
        python, Path("/runtime/bin/infer_experiment.py")
    )
    gatk = driver.gatk_adapter_bytes(python, Path("/runtime/bin/gatk"), java)
    assert b"JAVA_HOME=/runtime" in gatk and b"exec /runtime/bin/python" in gatk
    assert b'exec /runtime/bin/gunzip -d "$@"' in driver.gunzip_adapter_bytes(
        Path("/runtime/bin/gunzip")
    )

    from emrys.orchestration.local_pilot.execution_profile import load_execution_profile

    project = tmp_path / "project.yaml"
    project.write_text("fixture\n", encoding="utf-8")
    rendered = driver.slurm_execution_profile_bytes(
        project,
        account=None,
        partition="emrys-ci",
        qos=None,
        cpus_per_task=2,
        memory_mb=6144,
        time_limit="02:00:00",
        nodelist=None,
        scratch_parent=tmp_path / "scratch",
    )
    profile = tmp_path / "slurm.json"
    profile.write_bytes(rendered)
    assert load_execution_profile(
        project, config_path=profile
    ).resource_policy.document() == load_execution_profile(project).resource_policy.document()


def test_run_submission_and_wait_failure_cancel_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    run_root = driver.parse_run_plan(_plan(workspace), workspace, no_write=True)
    logs = workspace / "logs"
    submission = driver.parse_submission(
        f"JOB_ID=42\nOUT={logs}/emrys-local-pilot-42.out\n"
        f"ERR={logs}/emrys-local-pilot-42.err\n",
        logs,
    )
    calls: list[tuple[str, ...]] = []

    def scheduler(argv: tuple[str, ...], _cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        if argv[0] == "scancel":
            return subprocess.CompletedProcess(argv, 0, "", "")
        if len(calls) == 1:
            return subprocess.CompletedProcess(argv, 1, "", "lost scheduler response")
        return subprocess.CompletedProcess(
            argv, 0, "JobState=CANCELLED ExitCode=0:15", ""
        )

    monkeypatch.setattr(driver, "_scheduler", scheduler)
    with pytest.raises(driver.DriverError, match="cancellation: CANCELLED"):
        driver.wait_for_job(
            submission,
            scontrol=Path("scontrol"),
            scancel=Path("scancel"),
            cwd=tmp_path,
            timeout_seconds=1,
            poll_seconds=0.01,
        )
    assert run_root.parent == workspace / "runs"
    assert sum(argv[0] == "scancel" for argv in calls) == 1


def _table(path: Path, rows: tuple[tuple[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "candidate_id\tcall_status\n"
        + "".join(f"{candidate}\t{status}\n" for candidate, status in rows),
        encoding="utf-8",
    )


def test_completed_results_use_inspection_reports_and_direct_step09_oracle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root, analysis = tmp_path / "run", "analysis-1"
    all_sites = run_root / f"results/editing/{analysis}/{analysis}.cmh_all_sites.tsv"
    significant = (
        run_root / f"results/editing/{analysis}/{analysis}.cmh_significant_sites.tsv"
    )
    _table(all_sites, (("a", "not_significant"), ("b", "significant_up"), ("c", "not_significant")))
    _table(significant, (("b", "significant_up"),))
    scientific, evidence = run_root / "scientific.html", run_root / "evidence.html"
    scientific.write_text("science\n")
    evidence.write_text("evidence\n")
    observed = SimpleNamespace(
        integrity="valid",
        attempt_outcome="succeeded",
        results_status="complete",
        reporting_status="complete",
        blockers=(),
        run_id="run-1",
        verified_report_locations=(
            ("scientific-report-html", scientific),
            ("evidence-report-html", evidence),
        ),
    )
    from emrys.orchestration.local_pilot import inspection

    monkeypatch.setattr(inspection, "inspect_run", lambda _root: observed)
    result = driver.assert_completed_run(
        run_root,
        {
            "expected_terminal_computational_result": {
                "all_sites_rows": 3,
                "significant_sites_rows": 1,
                "significant_candidate_id": "b",
            }
        },
    )
    assert result["step09_oracle"]["significant_candidate_id"] == "b"
    assert set(result["reports"]) == {
        "scientific-report-html",
        "evidence-report-html",
    }


def test_transcripts_and_failure_summary_retain_streams(tmp_path: Path) -> None:
    root = tmp_path / "transcripts"
    root.mkdir()
    transcripts = driver.Transcripts(root)
    result = transcripts.run(
        "probe", [sys.executable, "-c", "print('retained')"], cwd=tmp_path
    )
    assert result.stdout == "retained\n"
    record = transcripts.records[0]
    assert Path(record["stdout"]).read_text() == "retained\n"
    arguments = driver.build_parser().parse_args(_argv(tmp_path))
    summary = driver._summary(
        arguments, transcripts, driver.DriverError("probe", "injected")
    )
    assert summary["status"] == "failed"
    assert summary["commands"] == transcripts.records
    assert "retained" in summary["retention"]
    assert "no completion" in summary["evidence_boundary"]
