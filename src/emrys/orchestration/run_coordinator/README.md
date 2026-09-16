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
operator execution profiles remain outside managed repair. On a Slurm Project, normal repair stays on the head node
and submits the required runtime/storage checks. `--compute` is the explicit
advanced allocation route. Both Project-creation commands accept `--site viking`
and use the same built-in placement; Run, resume and standalone report execution
follow the selected Project profile.
[Workflow composition](../../workflow/README.md) explains the graph;
[the profile contract](CONTRACT.md#profiles-and-immutable-planning) defines resource selection.

## Frozen dashboard and replacement

`emrys inspect --watch` reproduces the legacy overview/detail projections,
job discovery, explicit historical selection, accounting fallback, offline
stream access, configurable refresh, sample lanes/timings, stage context,
resources and activity. It reuses `dashboard.py` as the shared diagnostic
selection, parsing and presentation owner. The installed terminal adds a
separate dated Run-evidence/log view and fresh CLI action handoffs.

Use `--job-id [JOB_ID]` for scheduler-only selection; omitted ID discovers an
owned recent job, as does watch without a current Project. `--log-dir`,
`--out`/`--err --offline`, `--refresh` and `--snapshot` preserve the corresponding
legacy capabilities. Scheduler-only selection cannot execute actions or admit
a Run from log text. Project requests retain their stronger exact
owner/name/cluster/path binding and independently dated usage observations.

Legacy `1`/`o`, `2`/`d`, Tab and scrolling navigate overview/details. `3`/`v`
opens evidence/logs and `[`/`]` changes streams. Interactive `--watch --actions`
uses `p` for resume planning/confirmation, `b` for report preview, and `s` for
request-stop preview. Navigation never invokes an operation. Handoffs restore
the terminal and discard queued keys before fresh admission; report/stop remain
previews. Run handoffs use the default profile. Launch a new declared Analysis
with `emrys run --project PROJECT --analysis NAME`.

Full diagnostic history supports reconnecting and live progress; it remains
separate from scientific evidence, which is reverified explicitly. Every read
pins file/directory identity; rotation/truncation/replacement clears prior
history. Bounded waiting and one daemon read per stream preserve responsive
quit. Explicit Run views discover all admitted application-log associations
under the selected root, alongside Task streams; `--log-root` selects historical
custom roots. No latest-file heuristic or inferred scheduler binding is used.

The installed dashboard uses the same legacy functionality. The original
CSU-oriented entry point remains until institutional validation and coordinated
retirement under `DASHBOARD-RETIRE-01`. `emrys inspect` stays the authority for Run
status and recovery. Shared selection preserves scheduler discovery, historical
accounting fallback, exact job identity, stream ownership, regular-file and
symlink checks, and sanitized display of raw streams.
Legacy `--offline` with explicit job/stream paths makes no scheduler queries
during selection, snapshot or interactive refresh. It shows scheduler state as
`UNKNOWN`; raw-stream interpretation remains unverified diagnostic context.

The shared stream cache handles missing, replaced and truncated files without
carrying old bytes into a new generation. Its full-history memory is proportional
to retained diagnostics. Keep site validation separate from hosted fixtures;
retire the old entry point, tests, Make target and callers only together.

Changing `emrys-local-pilot` names for new submissions is a separate caller-wide
part of that outcome. Preserve historical names, stream paths and accounting
records; never rename or delete them as a side effect. Include replacement code
when accounting for savings. Institutional scheduler behavior still needs site
qualification.
