"""Contract tests for the GitHub Actions CI workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REAL_TOOLS_LOCK_PATH = REPO_ROOT / ".github" / "ci" / "real-tools.conda-lock.yml"
SLURM_SETUP_PATH = REPO_ROOT / "tests" / "tools" / "configure_ci_slurm.sh"
SHELL_RECEIPT_ROOT = "${RUNNER_TEMP}/emrys-python311-test-shards"
ACTION_RECEIPT_ROOT = "${{ runner.temp }}/emrys-python311-test-shards"
ORDINARY_JOB_IDS = (
    "workflow-lint",
    "static-wheel",
    "shell-slurm",
    "guarded-r",
    "fresh-clone-e2e",
    "python314-coverage-shards",
    "python314-coverage",
    "python311-smoke",
)


def _workflow_document() -> dict[str | bool, Any]:
    document = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _workflow_jobs() -> dict[str, Any]:
    return _workflow_document()["jobs"]


def _workflow_triggers() -> dict[str, Any]:
    document = _workflow_document()
    triggers = document.get("on", document.get(True))
    assert isinstance(triggers, dict)
    return triggers


def _named_step(job: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one CI step named {name!r}"
    return matches[0]


def _expression(value: object) -> str:
    return " ".join(str(value).split())


def test_long_lane_triggers_are_closed_and_independently_selectable() -> None:
    triggers = _workflow_triggers()
    assert triggers["schedule"] == [
        {"cron": "17 5 * * 1-6"},
        {"cron": "17 5 * * 0"},
    ]
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"python311", "synthetic_130", "synthetic_100000"}
    for value in inputs.values():
        assert value["type"] == "boolean"
        assert value["required"] is True
        assert value["default"] is False

    jobs = _workflow_jobs()
    manual = jobs["manual-selection"]
    assert _expression(manual["if"]) == "github.event_name == 'workflow_dispatch'"
    guard = _named_step(manual, "Require at least one selected long lane")
    assert set(guard["env"]) == {
        "RUN_PYTHON311",
        "RUN_SYNTHETIC_130",
        "RUN_SYNTHETIC_100000",
    }
    assert "select at least one lane" in guard["run"]


def test_ordinary_jobs_do_not_run_for_schedules_or_manual_long_lanes() -> None:
    jobs = _workflow_jobs()
    for job_id in ORDINARY_JOB_IDS:
        condition = _expression(jobs[job_id]["if"])
        assert "github.event_name != 'workflow_dispatch'" in condition
        assert "github.event_name != 'schedule'" in condition


def test_long_runs_have_unique_non_cancelling_concurrency() -> None:
    concurrency = _workflow_document()["concurrency"]
    group = _expression(concurrency["group"])
    cancellation = _expression(concurrency["cancel-in-progress"])
    assert "github.event_name == 'schedule'" in group
    assert "github.event_name == 'workflow_dispatch'" in group
    assert "github.run_id" in group
    assert cancellation == (
        "${{ github.event_name != 'schedule' && "
        "github.event_name != 'workflow_dispatch' }}"
    )


def test_python311_full_suite_is_nightly_or_explicitly_selected() -> None:
    jobs = _workflow_jobs()
    for job_id in ("python311-full-shards", "python311-full"):
        condition = _expression(jobs[job_id]["if"])
        assert "github.event_name == 'schedule'" in condition
        assert (
            "github.event_name == 'workflow_dispatch' && inputs.python311" in condition
        )


def test_synthetic_job_uses_locked_real_runtime_and_real_slurm() -> None:
    job = _workflow_jobs()["synthetic-e2e"]
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 360
    condition = _expression(job["if"])
    assert "github.event_name == 'schedule'" in condition
    assert "inputs.synthetic_130 || inputs.synthetic_100000" in condition

    seed = _named_step(job, "Seed external evidence roots for selected profiles")
    assert "${RUNNER_TEMP}/emrys-synthetic-e2e" in seed["run"]
    assert "${GITHUB_WORKSPACE}" not in seed["run"]

    tools = _named_step(job, "Restore exact real-tool environment from the Linux lock")
    assert tools["uses"] == (
        "mamba-org/setup-micromamba@f457c30a868e4760d3a6fcea5f25dc655b8edf39"
    )
    assert tools["with"]["environment-file"] == (".github/ci/real-tools.conda-lock.yml")
    assert tools["with"]["environment-name"] == "emrys-real-e2e-tools"
    assert tools["with"]["micromamba-version"] == "${{ env.MICROMAMBA_VERSION }}"
    assert "create-args" not in tools["with"]

    slurm = _named_step(job, "Configure and prove one disposable Slurm node")
    assert "tests/tools/configure_ci_slurm.sh" in slurm["run"]

    authorities = _named_step(
        job, "Record exact runtime authorities outside the checkout"
    )
    assert "picard-slim-3.1.1-*/picard.jar" in authorities["run"]
    assert "*/picard-3.1.1-*/picard.jar" not in authorities["run"]

    renv_restore = _named_step(job, "Restore exact R dependency cache")
    assert renv_restore["id"] == "renv-cache"
    assert renv_restore["uses"] == (
        "actions/cache/restore@caa296126883cff596d87d8935842f9db880ef25"
    )
    renv_save = _named_step(
        job, "Save exact R dependency cache after successful restore"
    )
    assert _expression(renv_save["if"]) == (
        "steps.renv-cache.outputs.cache-hit != 'true'"
    )
    assert renv_save["uses"] == (
        "actions/cache/save@caa296126883cff596d87d8935842f9db880ef25"
    )
    assert renv_save["with"]["path"] == renv_restore["with"]["path"]
    assert renv_save["with"]["key"] == (
        "${{ steps.renv-cache.outputs.cache-primary-key }}"
    )

    profile_expectations = (
        (
            "Run the selected 130-pair real synthetic E2E",
            "--profile 130",
            "inputs.synthetic_130",
        ),
        (
            "Run the selected 100,000-pair real synthetic E2E",
            "--profile 100000",
            "inputs.synthetic_100000",
        ),
    )
    for name, profile_argument, selector in profile_expectations:
        step = _named_step(job, name)
        assert step["continue-on-error"] is True
        assert selector in _expression(step["if"])
        assert profile_argument in step["run"]
        assert "tests/tools/real_synthetic_e2e.py" in step["run"]
        assert '"/usr/bin/srun"' in step["run"]
        assert "--execute" in step["run"]

    weekly = _named_step(job, "Run the selected 100,000-pair real synthetic E2E")
    assert "github.event.schedule == '17 5 * * 0'" in _expression(weekly["if"])


def test_real_tool_lock_is_linux_only_and_keeps_exact_science_versions() -> None:
    lock = yaml.safe_load(REAL_TOOLS_LOCK_PATH.read_text(encoding="utf-8"))
    assert lock["metadata"]["platforms"] == ["linux-64"]
    packages = {
        row["name"]: row for row in lock["package"] if row["platform"] == "linux-64"
    }
    expected = {
        "star": "2.7.11b",
        "samtools": "1.19.2",
        "bcftools": "1.21",
        "gatk4": "4.6.1.0",
        "gzip": "1.14",
        "openjdk": "17.0.11",
        "picard-slim": "3.1.1",
        "rseqc": "5.0.4",
    }
    assert {name: packages[name]["version"] for name in expected} == expected
    assert {row["manager"] for row in lock["package"]} == {"conda"}
    assert {row["platform"] for row in lock["package"]} == {"linux-64"}
    for row in lock["package"]:
        assert row["hash"]["sha256"]
        assert row["url"].startswith(
            (
                "https://conda.anaconda.org/bioconda/",
                "https://conda.anaconda.org/conda-forge/",
            )
        )


def test_retained_stage_benchmark_follows_successful_100000_e2e() -> None:
    job = _workflow_jobs()["synthetic-e2e"]
    benchmark_name = "Run retained-stage benchmark comparisons"
    upload_name = "Upload retained 100,000-pair evidence"
    step_names = [step.get("name") for step in job["steps"]]
    assert step_names.index("Run the selected 100,000-pair real synthetic E2E") < (
        step_names.index(benchmark_name)
    )
    assert step_names.index(benchmark_name) < step_names.index(upload_name)

    benchmark = _named_step(job, benchmark_name)
    assert benchmark["id"] == "retained-stage-benchmark"
    assert benchmark["continue-on-error"] is True
    assert benchmark["timeout-minutes"] == 180
    condition = _expression(benchmark["if"])
    assert "github.event.schedule == '17 5 * * 0'" in condition
    assert "inputs.synthetic_100000" in condition
    assert "steps.synthetic-100000.outcome == 'success'" in condition
    assert benchmark["env"]["REAL_TOOLS_PREFIX"] == (
        "${{ steps.real-tools.outputs.environment-path }}"
    )

    command = benchmark["run"]
    assert ".venv/bin/python tests/tools/retained_stage_benchmark.py" in command
    assert '--repo-root "${GITHUB_WORKSPACE}"' in command
    assert (
        '"${E2E_EVIDENCE_ROOT}/100000/operator/e2e-summary.json"' in command
    )
    assert (
        '"${E2E_EVIDENCE_ROOT}/100000/retained-stage-benchmark"' in command
    )
    assert '--runtime-prefix "${REAL_TOOLS_PREFIX}"' in command
    assert '--rscript "$(command -v Rscript)"' in command
    assert '--renv-library "${RENV_LIBRARY}"' in command
    assert "--suite all" in command
    assert "--execute" in command
    assert "threshold" not in command.lower()

    upload = _named_step(job, upload_name)
    assert upload["with"]["path"] == (
        "${{ runner.temp }}/emrys-synthetic-e2e/100000"
    )


def test_synthetic_evidence_is_always_uploaded_with_hidden_state() -> None:
    job = _workflow_jobs()["synthetic-e2e"]
    upload_names = (
        "Upload retained 130-pair evidence",
        "Upload retained 100,000-pair evidence",
        "Upload shared runtime and Slurm evidence",
    )
    for name in upload_names:
        step = _named_step(job, name)
        assert "always()" in _expression(step["if"])
        assert step["continue-on-error"] is True
        assert step["uses"] == (
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
        )
        assert step["with"]["if-no-files-found"] == "error"
        assert step["with"]["include-hidden-files"] is True
        assert step["with"]["retention-days"] == 14

    final = _named_step(
        job, "Require every selected synthetic lane and evidence upload to pass"
    )
    assert "steps.synthetic-130.outcome" in final["env"]["OUTCOME_130"]
    assert "steps.synthetic-100000.outcome" in final["env"]["OUTCOME_100000"]
    assert "steps.retained-stage-benchmark.outcome" in (
        final["env"]["OUTCOME_RETAINED_STAGE_BENCHMARK"]
    )
    assert '"${SELECT_100000}" == true' in final["run"]
    assert '"${OUTCOME_RETAINED_STAGE_BENCHMARK}" != success' in final["run"]
    assert "UPLOAD_INFRASTRUCTURE" in final["run"]


def test_ci_slurm_setup_is_guarded_real_and_diagnostic() -> None:
    script = SLURM_SETUP_PATH.read_text(encoding="utf-8")
    assert "GITHUB_ACTIONS" in script
    assert "AuthType=auth/munge" in script
    assert "ProctrackType=proctrack/linuxproc" in script
    assert "TaskPlugin=task/none" in script
    assert "PartitionName=emrys-ci" in script
    assert "node_record=\"${node_probe%%$'\\n'*}\"" in script
    assert "node_probe%% UpTime=" not in script
    assert "scontrol ping" in script
    assert '[[ "$state" =~ ^[[:space:]]*idle[[:space:]]*$ ]]' in script
    assert "idle([*~+#-])?" not in script
    assert "single-node CI Slurm partition did not become idle" in script
    assert "journalctl" in script
    assert "slurmdbd" not in script
    assert "mariadb" not in script


def test_python311_shard_receipts_round_trip_outside_source_checkout() -> None:
    jobs = _workflow_jobs()
    shard_job = jobs["python311-full-shards"]
    aggregate_job = jobs["python311-full"]

    run_step = _named_step(
        shard_job, "Run complete-suite shard with live slow-test timings"
    )
    run_command = run_step["run"]
    assert '--repo-root "${GITHUB_WORKSPACE}"' in run_command
    assert f'--receipt "{SHELL_RECEIPT_ROOT}/python-test-shard-' in run_command
    assert "${GITHUB_WORKSPACE}/.test-shards" not in run_command

    upload_step = _named_step(shard_job, "Upload selection receipt")
    upload_inputs = upload_step["with"]
    assert upload_inputs["path"] == (f"{ACTION_RECEIPT_ROOT}/python-test-shard-*.json")
    assert upload_inputs["if-no-files-found"] == "error"

    download_step = _named_step(
        aggregate_job, "Download every Python 3.11 shard receipt"
    )
    download_inputs = download_step["with"]
    assert download_inputs["pattern"] == "python311-test-shard-*"
    assert download_inputs["path"] == f"{ACTION_RECEIPT_ROOT}/merged"
    assert download_inputs["merge-multiple"] is True

    verify_step = _named_step(
        aggregate_job, "Verify complete and disjoint shard receipts"
    )
    assert f'--receipt-dir "{SHELL_RECEIPT_ROOT}/merged"' in verify_step["run"]
