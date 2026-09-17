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

`emrys inspect --watch` provides overview/detail projections,
job discovery, explicit historical selection, accounting fallback, offline
stream access, configurable refresh, sample lanes/timings, stage context,
resources and activity. Its shared internal model owns diagnostic selection,
parsing and rendering. The terminal also provides a dated Run-evidence/log view
and fresh CLI action handoffs.

`emrys watch [RUN_OR_JOB]` is the ordinary entry point over that same owner. It
automatically selects the sole Project Run or pre-Run request, uses a picker for
ambiguity, and accepts exact scheduler IDs or names. A declared
`EMRYS_PROJECTS_ROOT` supplies read-only Run discovery outside a Project
directory. With no selectable Run, watch selects a sole bounded current-user
scheduler candidate or offers all candidates in the same picker; noninteractive
ambiguity fails with their IDs. Verified completion comes from inspection and
replaces stale final stage counts. A finished raw workflow log is labeled
unverified and clears misleading waiting/pending states without claiming Run
completion.

Use `--job-id [JOB_ID]` for scheduler-only selection; omitted ID discovers an
owned recent job only when exactly one candidate exists. Raw ambiguity requires
an explicit ID and never chooses the newest candidate. `--log-dir`,
`--out`/`--err --offline`, `--refresh` and `--snapshot` preserve the corresponding
diagnostic capabilities. Scheduler-only selection cannot execute actions or admit
a Run from log text. Project requests retain their stronger exact
owner/name/cluster/path binding and independently dated usage observations.

`1`/`o`, `2`/`d`, Tab and scrolling navigate overview/details. `3`/`v`
opens evidence/logs and `[`/`]` changes streams. Interactive `--watch --actions`
uses `p` for resume planning/confirmation, `b` for report preview, and `s` for
request-stop preview. Navigation never invokes an operation. Handoffs restore
the terminal and discard queued keys before fresh admission; report/stop remain
previews. Run handoffs use the default profile. Launch a new declared Analysis
with `emrys run --project PROJECT --analysis NAME`.

The interactive terminal view reserves mouse input without attaching an action
to it; scrolling remains on the arrow, `j`/`k`, Page Up/Down and Home/`g` keys.
The installed evidence/log view colors literal severity and workflow prefixes
without filtering or reinterpreting the sanitized diagnostic text. `NO_COLOR`
keeps the same content plain. The `r` key performs a read-only recheck of the
fixed selection and its dated evidence; it does not execute a Run action.

The installed evidence/log view opens at the newest retained line and follows
new text while it remains at the bottom. Upward movement pauses follow visibly;
`G` returns to the bottom and resumes it. Counts apply to `j`/`k`; `/` accepts a
regular-expression search, and `n`/`N` moves forward/backward through highlighted
matches. Displayed line numbers are one-based and relative to the bounded tail,
not absolute file positions. Changing streams resets search and resumes follow.

Full diagnostic history supports reconnecting and live progress; it remains
separate from scientific evidence, which is reverified explicitly. Every read
pins file/directory identity; rotation/truncation/replacement clears prior
history. Bounded waiting and one daemon read per stream preserve responsive
quit. Explicit Run views discover all admitted application-log associations
under the selected root, alongside Task streams; `--log-root` selects historical
custom roots. No latest-file heuristic or inferred scheduler binding is used.

`emrys inspect` stays the authority for Run status and recovery. Shared
selection preserves scheduler discovery, historical accounting fallback, exact
job identity, stream ownership, regular-file and symlink checks, and sanitized
display of raw streams. `--offline` with explicit job/stream paths makes no scheduler queries
during selection, snapshot or interactive refresh. It shows scheduler state as
`UNKNOWN`; raw-stream interpretation remains unverified diagnostic context.

The shared stream cache handles missing, replaced and truncated files without
carrying old bytes into a new generation. Its full-history memory is proportional
to retained diagnostics. Keep site validation separate from hosted fixtures;
the replaced standalone entry point, tests, Make target and duplicate scheduler
query were retired together after institutional acceptance.

Changing `emrys-local-pilot` names for new submissions is a separate caller-wide
part of that outcome. Preserve historical names, stream paths and accounting
records; never rename or delete them as a side effect. Include replacement code
when accounting for savings. Institutional scheduler behavior still needs site
qualification.
