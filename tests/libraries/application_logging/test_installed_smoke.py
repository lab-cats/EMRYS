from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def test_clean_installed_scheduler_delegate_owns_one_attempt_and_separates_streams(
    tmp_path: Path,
) -> None:
    script = textwrap.dedent(
        """
        import os
        import sys
        from pathlib import Path
        from emrys.libraries.application_logging import (
            AttemptIdentity, event, open_attempt_log, resolve_log_controls
        )
        from emrys.libraries.source_authority import SourceCheckout

        controls = resolve_log_controls(
            source_checkout=SourceCheckout(Path(sys.argv[1])),
            environment=os.environ,
        )
        attempt = open_attempt_log(
            controls=controls,
            identity=AttemptIdentity("run", "run-1", "attempt-1", "smoke"),
            mode="execute",
            component="smoke",
            scheduler_environment=os.environ,
        )
        print("machine")
        attempt.logger(component="smoke", phase="execute").info(
            "Subprocess event.", extra=event("subprocess_event")
        )
        attempt.terminal(event_name="complete", message="Complete.")
        """
    )
    log_root = tmp_path / "application"
    scheduler_out = tmp_path / "job.out"
    scheduler_err = tmp_path / "job.err"
    environment = {
        **{
            name: value
            for name, value in os.environ.items()
            if not name.startswith(("EMRYS_LOG_", "SLURM_"))
        },
        "EMRYS_LOG_LEVEL": "normal",
        "EMRYS_LOG_ROOT": str(log_root),
        "SLURM_JOB_ID": "42",
    }
    with (
        scheduler_out.open("w", encoding="utf-8") as stdout,
        scheduler_err.open("w", encoding="utf-8") as stderr,
    ):
        result = subprocess.run(
            [sys.executable, "-I", "-c", script, str(tmp_path / "checkout")],
            stdout=stdout,
            stderr=stderr,
            text=True,
            check=False,
            env=environment,
        )
    stderr_text = scheduler_err.read_text(encoding="utf-8")
    if "No module named 'emrys'" in stderr_text:
        pytest.skip("the borrowed local interpreter has no installed EMRYS package")
    assert result.returncode == 0
    assert scheduler_out.read_text(encoding="utf-8") == "machine\n"
    assert "Subprocess event." in stderr_text
    path = log_root / "run-run-1/attempt-1/smoke.jsonl"
    assert stderr_text.count(str(path)) == 1
    assert list(log_root.rglob("*.jsonl")) == [path]
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert [record["event"] for record in records] == [
        "attempt_opened",
        "subprocess_event",
        "complete",
    ]
    expected_opening = {
        "log_level_source": "environment",
        "log_root_source": "environment",
        "slurm_job_id": "42",
    }
    assert {
        name: records[0]["fields"][name] for name in expected_opening
    } == expected_opening
