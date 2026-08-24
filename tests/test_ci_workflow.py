"""Contract tests for the GitHub Actions CI workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SHELL_RECEIPT_ROOT = "${RUNNER_TEMP}/emrys-python311-test-shards"
ACTION_RECEIPT_ROOT = "${{ runner.temp }}/emrys-python311-test-shards"


def _workflow_jobs() -> dict[str, Any]:
    document = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return document["jobs"]


def _named_step(job: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one CI step named {name!r}"
    return matches[0]


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
