# Run coordinator

This package turns a validated Project and selected Analysis into a Run plan,
executes that plan, and reports its state. Operators use the grouped `emrys`
commands; these modules are private implementation details.

## Ordinary journey

Use the [quickstart](../../../../quickstart.md) for a first Run and the
[Runbook](../../../../docs/operations/RUNBOOK.md) for later operation and Slurm.
[The contract](CONTRACT.md) defines command confirmation, immutable records,
inspection, current-version compatibility, and recovery. It is the authoritative
home for those rules; this README explains how the implementation fits together.

## Specialized setup and reuse

The [configuration guide](../../../../configs/README.md) explains manifests and
Analysis fields. The [runtime procedure](../../../../docs/operations/RUNBOOK.md#institution-provided-runtime)
explains discovery and managed/site setup. The [reuse procedure](../../../../docs/operations/RUNBOOK.md#reusable-processing)
explains how a new downstream Run uses a compatible processing Run without
changing it. Synthetic dataset choices belong in the [quickstart](../../../../quickstart.md).

## Internal boundary

| Responsibility | Existing implementation |
|---|---|
| Parse grouped commands and coordinate the requested action | `control.py` |
| Create a Project or discover inputs/runtime | `onboarding.py`, `normalization.py` |
| Diagnose runtime, storage, and resource readiness | `doctor.py`, `resource_policy.py`, `execution_profile.py` |
| Build task commands, dependencies, and their recorded plan | `materialization.py`, `run_implementation.py` |
| Run Snakemake and record Attempt success, interruption, or failure | `lifecycle.py`, `task.py` |
| Read and validate Run state and identify supported recovery | `inspection.py`, `_inspection_evidence.py` |
| Present dated inspection evidence and a read-only terminal watch | `_inspection_presentation.py` |
| Start reporting after computation or on request | `reporting_operation.py`, `reporting_boundary.py` |
| Submit the same execution backend to one Slurm allocation | `slurm_submission.py` |

The runner owns native-output publication. Scientific algorithms and validation,
report rendering, and package installation stay with their existing owners.
Doctor binds the executing installed package and rechecks its full identity
before and after repair. Managed repair uses Pixi and renv for Project-owned
native tools and R libraries; Python installation stays with the environment's
package manager. Existing site runtimes and operator execution profiles remain
outside managed repair. On a Slurm Project, normal repair stays on the head node
and submits the required runtime/storage checks. `--compute` is the explicit
advanced allocation route. Both Project-creation commands accept `--site viking`
and use the same built-in placement; Run, resume and standalone report execution
follow the selected Project profile.
[Workflow composition](../../workflow/README.md) explains the graph;
[the profile contract](CONTRACT.md#profiles-and-immutable-planning) defines resource selection.

## Frozen dashboard and replacement

`emrys inspect --watch` adds an installed-package view of one exact selection.
It shares static inspection's milestone, Task and elapsed presentation and
uses existing scheduler, application-association and Run admission owners.
Automatic refresh reads scheduler diagnostics and a bounded stream tail;
scientific evidence is dated and reverified explicitly. Operational actions
remain in the ordinary CLI. This first view does not retire the standalone
dashboard or establish institutional replacement acceptance.
Interactive `--watch --actions` leaves the view for an ordinary CLI operation:
`p` reviews a selected Run's resume plan and confirmation, `o` previews its
report, and `s` previews stopping a selected request. Run handoffs use the
default profile. All handlers run after terminal cleanup with fresh admission;
report/stop previews do not execute, and no worker owns an operation or recovery.
Explicit Run inspection/watch discovers all admitted application-log associations
within the selected root, alongside Task streams. `--log-root` selects a
historical custom root; no latest-file heuristic or scheduler inference is used.
Default roster and implicit Run selection retain their no-scan behavior.

The old CSU-oriented `dashboard.py` preview remains until a replacement is
implemented and validated under `DASHBOARD-RETIRE-01`. `emrys inspect` stays the
authority for Run status and recovery; expert commands alone do not replace the
dashboard. The replacement must preserve scheduler discovery and historical
accounting fallback, exact job identity, stream ownership, regular-file and
symlink checks, and sanitized display of raw streams.
Legacy `--offline` with explicit job/stream paths makes no scheduler queries
during selection, snapshot or interactive refresh. It shows scheduler state as
`UNKNOWN`; raw-stream interpretation remains unverified diagnostic context.

The legacy dashboard's stream cache resets after truncation but does not protect against
inode rotation. `tail -F` does not remove terminal-control sequences from logs.
Validate missing and replaced streams as well as the normal display before
retiring the owner, tests, Make target, and documented callers together.

Changing `emrys-local-pilot` names for new submissions is a separate caller-wide
part of that outcome. Preserve historical names, stream paths and accounting
records; never rename or delete them as a side effect. Include replacement code
when accounting for savings. Institutional scheduler behavior still needs site
qualification.
