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
changing it. Synthetic dataset choices belong in the
[quickstart](../../../../quickstart.md). `emrys setup` owns the closed
repository-root `.env` for Projects home, site and optional application-log
defaults; command-line and process values remain higher precedence.
The ordinary named initializer guides FASTQ pairing, biological assignments and
regions, then owns the resulting manifests inside the Project. The separate
manifest drafting command remains an advanced structural helper.

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
package manager. A shared generation is never repaired in place: Doctor creates
a verified replacement, and dependent Projects explicitly move their current
selection while retained Attempts keep the old one. Existing site runtimes and
operator execution profiles remain outside managed repair. On a Slurm Project,
normal repair stays on the head node and submits the required runtime/storage
checks. `--compute` is the explicit advanced allocation route. Both
Project-creation commands accept `--site viking` and use the same built-in
placement; saved `EMRYS_SITE` supplies that choice when the flag is omitted.
Run, resume and standalone report execution follow the selected Project profile.
[Workflow composition](../../workflow/README.md) explains the graph;
[the profile contract](CONTRACT.md#profiles-and-immutable-planning) defines resource selection.

## Installed watch

`_inspection_presentation.py` owns the installed terminal interaction,
dated inspection/log projection, and fresh CLI action handoff. `dashboard.py`
owns scheduler-diagnostic selection, the full-history stream cache, parsing,
the overview/detail view model, and its renderer. `inspection.py` remains the
Run status and recovery authority; diagnostic text never replaces it.

The [Runbook watch procedure](../../../../docs/operations/RUNBOOK.md#watch-one-fixed-selection)
owns selectors, keys, refresh, offline use, and action previews;
[CONTRACT](CONTRACT.md#resume-inspection-results-and-reporting) owns selection,
evidence, completion, and recovery semantics. Historical scheduler names and
paths remain readable; the retired standalone dashboard is not a second owner.
