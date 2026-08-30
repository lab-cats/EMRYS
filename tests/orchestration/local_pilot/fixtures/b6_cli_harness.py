#!/usr/bin/env python3
"""Clone-local B6 harness for the public CLI with explicit no-science ops."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from emrys import __main__ as emrys_cli  # noqa: E402
from emrys.orchestration.local_pilot import control, lifecycle  # noqa: E402
from tests.orchestration.local_pilot.fixtures.b5_doubles import (  # noqa: E402
    with_owner_doubles,
)

def _lifecycle_ops(
    base: lifecycle.LifecycleOps,
    *,
    stop_after_target: str | None,
) -> lifecycle.LifecycleOps:

    def run_workflow(
        argv: tuple[str, ...],
        cwd: Path,
    ) -> lifecycle.WorkflowResult:
        invoked = (*argv[:-1], stop_after_target) if stop_after_target else argv
        completed = subprocess.run(
            invoked,
            cwd=cwd,
            env={**os.environ, "XDG_CACHE_HOME": str(cwd / "cache")},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if stop_after_target is not None and completed.returncode == 0:
            return lifecycle.WorkflowResult(
                exit_code=23,
                termination_signal=None,
                message="controlled failure between owner tasks",
            )
        return lifecycle.WorkflowResult(
            exit_code=completed.returncode,
            termination_signal=None,
            message=completed.stdout if completed.returncode else None,
        )

    return replace(base, run_workflow=run_workflow)


def _install_control_doubles(mode: str) -> None:
    stop_after_target = "one_sample_slice" if mode == "failure" else None
    real_build = control.build_attempt_plan
    real_ops = control.lifecycle.default_lifecycle_ops
    control.build_attempt_plan = lambda *args, **kwargs: with_owner_doubles(
        real_build(*args, **kwargs)
    )
    control.lifecycle.default_lifecycle_ops = lambda: _lifecycle_ops(
        real_ops(), stop_after_target=stop_after_target
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise the public EMRYS parser and control plane with an explicit "
            "repository-only no-science dependency."
        )
    )
    parser.add_argument("mode", choices=("failure", "success"))
    arguments, command = parser.parse_known_args()
    if not command:
        parser.error("one EMRYS command is required after mode")
    _install_control_doubles(arguments.mode)
    return emrys_cli.main(command)


if __name__ == "__main__":
    raise SystemExit(main())
