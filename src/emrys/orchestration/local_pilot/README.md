# Local-pilot orchestration boundary

This owner exposes the fixed local-pilot admission, onboarding, and lifecycle
surface. The zero-context entry points are:

```bash
# Infer exact <sample>_R1/_R2 pairs and require all biological metadata.
emrys init manifests \
  --output-dir /absolute/outside-checkout/manifest-drafts \
  --fastq /data/control_1_R1.fastq.gz /data/control_1_R2.fastq.gz \
  --sample control_1 control pair_1 forward

# Collect the remaining scientific answers and plan an absent Project root.
# Omitted answers are prompted on a terminal; the first Analysis defaults to
# "primary". Add --execute after review.
emrys init project

# Generate the default 130-pair deterministic science fixture the same way.
emrys init synthetic \
  --output-dir /absolute/outside-checkout/synthetic-smoke \
  --dataset-profile smoke-v1

# Select the closed 100,000-pair-per-library, 5 Mb profile explicitly.
emrys init synthetic \
  --output-dir /absolute/outside-checkout/synthetic-production-like \
  --dataset-profile production-like-v1

# Validate all declared inputs without requiring or probing science tools.
emrys validate project \
  --project /absolute/path/to/project.yaml

# Preview the fixed runtime policy, then publish the admitted Project profile.
emrys runtime discover --project /absolute/path/to/project.yaml
emrys runtime discover --project /absolute/path/to/project.yaml --execute
```

`init manifests` produces deterministic strict manifests with absolute data
paths and requires every biological assignment explicitly. `init project`
validates them, records their admitted absolute paths without copying manifests
or raw data, creates mode-`0700` `runs/`, `logs/`, and `runtime/`, and publishes
`emrys.project.v1` `project.yaml` last. Its canonical parent is the Project root
used by run and Doctor; Results remain under `runs/<run-id>/results`. Setup
creates one initial named Analysis (`primary` unless `--analysis-name` is
supplied) and creates no execution or runtime profile, Run, Attempt, Results,
or application log.

The public model is `Project -> named Analysis -> immutable Run -> Results`.
A Project shares one Dataset and Reference across one or more named Analyses;
each Analysis owns its partition manifest and scientific policy. Project
validation, runtime discovery, and Doctor admit every Analysis. `emrys run` and
Doctor select one with `--analysis NAME`, and omission is accepted only for a
single-Analysis Project. The name is human selection metadata, not part of the
content-derived Analysis identity.

Runtime discovery probes the active environment without installing or loading
modules. Missing or ambiguous identities fail closed. `--execute` publishes
the sole ordinary runtime authority at `<project-root>/runtime/runtime.tsv`;
run, resume, and Doctor derive it. The generic `inspect runtime-availability`
route remains available for advanced profile-driven evidence. Use an exact
historical checkout for an entered historical Run.

`emrys run` and `emrys resume` accept one optional explicit
`--execution-profile`. Without it, EMRYS uses its built-in conservative
resources and executes directly. The profile combines the Run-bound
computational declaration with Attempt-local direct or Slurm placement; CLI
resource flags have highest precedence. EMRYS performs no adjacent discovery.

Slurm placement is a transport around the same one-host workflow, not another
scientific backend. On a terminal, EMRYS prints concise placement and asks
before creating the scheduler-log directory or submitting. Refusal, EOF, or
interruption writes and submits nothing; verbose output adds the exact profile
and stream paths. `--execute` is the noninteractive automation path. An
accepted command submits the whole Run once and prints exact `JOB_ID`, `OUT`,
and `ERR` values. The compute
delegate re-admits the profile digest, submission UID, internal marker, and
Slurm job ID before planning the immutable Run. It loads only an exact declared
module roster, creates and later removes one mode-`0700` private scratch
directory, and runs doctor inside the allocation. Ambient `SBATCH_*` values do
not alter the admitted Project.

The effective resource declaration must fit the observed CPU and memory
allocation. Placement request, profile source/digest, observed allocation, and
scheduler job ID are Attempt provenance and do not make scheduler success
workflow completion. Hosted 130-pair direct/disposable-single-node-Slurm
execution proves matching immutable authority, Attempt common fields/task
roster, path-neutral science, and symbolic resources. Each placement separately
admits successful receipt/reporting and one application log; effective
allocation and scheduler streams differ as intended. It does not establish the
100,000-pair case, institutional site/module portability, failure/recovery,
multi-node, production, scientific-review, or biological-validation evidence.
Owner-local scheduler entry points are retired; the private whole-Run batch
bootstrap remains the sole Slurm delegation boundary.

An executing Run Attempt owns one application log, by default beneath
`<project-root>/logs/application`. For a full Run, reporting is invoked
automatically after scientific work, publishes its transaction receipts last,
and is not a scientific stage. Reporting does not apply to a processing Run.

The adjacent `dashboard.py` owns a read-only live view over one wrapper job's
Slurm metadata and append-only stdout/stderr streams. The repository-level
`make dashboard` target is only a thin entry point to that owner. Selection,
bounded current-user scheduler discovery, stream admission and sanitization,
incremental parsing, and terminal rendering stay here; the dashboard never
scans shared storage, mutates the workflow, or replaces final EMRYS
inspection. It does not derive or display result locations. Scheduler state,
inferred progress and timing, and the dashboard process exit are operational
observations rather than completion, validation, or evidence authority.

This dashboard is currently a CSU-oriented preview, not a portable execution
contract. It expects CSU Slurm metadata and the generated local-pilot wrapper's
exact stream naming, and parts of its display still encode the fixed qualified
stage topology, six-sample cohort, and 25-partition qualification run.
Workflow cores, per-stage concurrency, per-step thread allocations, and memory
policy are read from the selected run's control stream rather than fixed to one
benchmark policy. See the
[runbook](../../../../docs/operations/RUNBOOK.md#live-whole-run-dashboard) for
the supported preview commands and explicit override rules.

`init synthetic` has two closed dataset profiles. The default
`smoke-v1` publishes a deterministic 100-kb reference, GTF, and four paired
130-read libraries across two control/treatment strata. The explicit
`production-like-v1` profile retains the same engineered core and oracle, adds
deterministic neutral background and deliberate duplicate templates to reach
100,000 pairs per library, and uses a 5 Mb reference. Both profiles publish
matched Project/manifests and explicit fixture metadata for the current
Step 00a-10 scientific workflow and downstream reporting. `fixture.manifest.json` is written last
after the generated Project passes the same admission and reference-
compatibility checks. Their expectation is three Step 09 computational rows,
one significant row, and a complete Step 10 projection; none is production
data, scientific adjudication, or biological evidence.

Focused protection is:

```bash
.venv/bin/python -m pytest -q \
  tests/orchestration/local_pilot/test_execution_profile.py \
  tests/orchestration/local_pilot/test_slurm_submission.py \
  tests/orchestration/local_pilot/test_onboarding.py \
  tests/orchestration/local_pilot/test_dashboard.py \
  tests/test_public_cli_contracts.py
```

Run the focused suite above after restoring the locked development environment,
and use CI checks attached to the exact commit for any selected hosted lane.
Checks that require an unavailable environment remain explicitly `NOT RUN`;
they are not inferred from static validation.

The underlying narrow read-only admission APIs are:

- `normalization.admit_project(project_path, profile)` safely admits one
  mutable project-v1 definition plus its TSV manifests and returns one
  immutable `ProjectAdmission` snapshot containing all named Analysis
  revisions without writing a Run. `ProjectAdmission.select_analysis()`
  selects one Analysis. No-follow, descriptor-bound admission makes exact
  source bytes the parse and provenance authority; canonical normalized
  scientific content, not formatting or row order, determines Analysis
  identity. Shared Dataset and Reference inputs are admitted once, repeated
  partition-manifest spellings are cached, and every Analysis remains
  immutable;
- `all_pass.require_all_pass(...)` checks the meaning of one owner-validation
  report rather than trusting its process exit;
- `doctor.inspect_local_pilot(...)` admits one Project plus the fixed profile,
  checks its external Project root, exact clean source checkout, controlled
  Python/Snakemake, science-tool paths and versions, Picard jar, guarded
  `renv`, Step `08` namespaces, and the placement-appropriate storage
  qualification. It remains the read-only internal readiness capability used
  by Run and resume.

The Project-aware public command is top-level:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys doctor \
  --project /absolute/path/to/project.yaml
```

Exit `0` means every declared readiness check passed, exit `1` reports exact
readiness blockers and remediation routes, and exit `2` identifies malformed
or unsafe input. The doctor runs only bounded version, namespace, hash, and
path probes. Ordinary commands retain a 30-second bound; guarded R namespace
loads have a separate 120-second bound with elapsed diagnostics and fail closed
on timeout. Even exit `0` is only local readiness evidence: no workflow or
scientific-owner computation, scheduler, cluster job, scientific review, or
biological validation ran. Diagnosis, detail projection, help, repair preview,
refusal, EOF, and interruption before repair authority write nothing and open
no log. `--log-level verbose` adds source/runtime observations and
`--log-level debug` adds exact path/hash bindings.

A missing direct-storage receipt or absent/incomplete EMRYS-managed runtime has
one explicit repair path:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys doctor \
  --project /absolute/path/to/project.yaml --repair
```

On a terminal, Doctor prints and confirms the exact plan. Noninteractive
mutation requires `--repair --execute`; `--execute` alone is invalid. Doctor
may publish one Project-owned single-host storage receipt. When runtime repair
is also needed, it currently supports Linux x86-64, requires the active
checkout-owned `.venv`, and delegates the locked Python environment to `uv`,
the packaged native/R lock to Pixi, and the R library to `renv`; only `.venv`,
`<project-root>/runtime/managed`, a create-absent canonical runtime profile,
the direct receipt/probes, and one maintenance log are writable. It then reruns
complete Project readiness. Declared input files and ready site/user profiles
are preserved rather than modified, repaired, or silently migrated.

The source-checkout-bound public control surface requires every mutating route
to use the controlled Python runtime, remain dry-run-first, and delegate owner
work only through the accepted fixed profile:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys run \
  --project /absolute/path/to/project.yaml \
  --analysis ANALYSIS_NAME \
  --execution-profile /absolute/path/to/emrys.execution.yaml

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys run \
  --project /absolute/path/to/project.yaml \
  --analysis ANALYSIS_NAME \
  --through processing

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys run \
  --project /absolute/path/to/project.yaml \
  --analysis ANALYSIS_NAME \
  --from-processing-run run-DIGEST

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys inspect \
  run --run-root /absolute/project/runs/run-DIGEST

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys resume \
  --run-root /absolute/project/runs/run-DIGEST \
  --execution-profile /absolute/path/to/emrys.execution.yaml

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys report \
  --run-root /absolute/project/runs/run-DIGEST
```

The first `run` command retains the full default Analysis. The semantic
`emrys run --through processing` form creates a distinct immutable Run
selecting the evidence-complete, all-sample Steps `00`–`06` closure. The
four-sample synthetic fixture expands that closure to 31 owner tasks. A
successful processing Run is complete and not resumable, and reporting is not
applicable. The `--from-processing-run` form admits that exact successful Run
from the same Project and creates a distinct complete downstream Run. Samples,
Reference, and the entire Execution Plan identity except its source/stopping
fields must match; partitions and scientific policy may differ. Source
artifacts stay in place and content-bound;
the target owns only Steps `07`–`10`, its evidence, Results, reports, and log.
Authored subsets and generalized modular analyses remain ANALYSIS-01/02 work.

With direct placement, `run` and `resume` print concise Run identity, combined
pending/reusable work within that Run, and reporting information; a terminal
asks once before executing that exact plan. With Slurm placement, EMRYS constructs one frozen
submission plan, prints its placement summary, and after confirmation submits
that same object once; Run planning occurs inside the allocation. Refusal, EOF,
or interruption opens no application log and writes nothing. Noninteractive
omission of `--execute` retains the no-write/no-submit behavior, while
`--execute` remains the explicit automation path. After successful full
scientific execution they generate the fixed reports by
default; `--no-report` stops after the successful v2 Attempt receipt without
changing Results. `report` independently validates a completed Run and plans
without writes, then generates with `--execute` or reuses an exact complete
report transaction. Verbose output adds the Run root,
resources/allocation, execution profile, and scheduler streams; debug output
adds exact engine, scheduler, and task commands. `inspect run` is
always read-only. With no execution profile, `run` uses the built-in direct
default; `resume` reuses its predecessor's symbolic computational resources and
places the new Attempt directly. An explicit profile may select Slurm for either
command. Explicit resource CLI flags override the selected or inherited policy.

Direct execution writes its application log beneath the selected root, which
defaults to `<project-root>/logs/application`. Slurm submission writes scheduler
streams beneath `<project-root>/logs`, while the compute delegate owns the single
application log. Automatic reporting shares that Run log. A standalone
executing `emrys report` owns a reporting log; dry-run and verified reuse own no
durable application log. Logging failure never changes reporting admission or
publication. Normal human output keeps raw Snakemake/task commands in the
evidence and debug surfaces rather than the primary control stream.
Execution re-admits the normalized reference/Project-root storage qualification
before delegation and after the child terminates. Direct Attempts accept the
Doctor-owned single-host receipt or a stronger two-phase receipt; Slurm and
historical unplaced Attempts require the two-phase site receipt. A missing,
changed, or semantically invalid receipt
blocks the Attempt; the immutable Attempt cannot accept its own declared
storage identity as proof.
The grouped CLI is the supported control surface. Its private planning helpers
delegate to the single production owner `materialization.build_attempt_plan`;
tests pass explicit collaborators rather than monkeypatching module globals.
Exact setup and execution order lives in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

The neutral
`emrys.contracts.orchestration.projection.project_reporting(...)` API
reproduces the exact legacy reporting contract and deterministic artifact
inventory without depending on the local-pilot application owner.

Direct readiness accepts one Doctor-owned single-host receipt or the stronger
site receipt for the Project root and Step `00c` sidecar parent. The narrow
receipt proves hard-link, advisory-`flock`,
atomic-rename, and fsync behavior only on the current host and current numeric
identity. Slurm readiness requires the separate final two-phase receipt, which
adds compute/head access, mount, cross-node visibility, and post-allocation
durability checks for those exact roots. NFS and other network/distributed
filesystems remain unsupported for Slurm until that site check finalizes;
node-local storage that is not durably visible to the head node cannot finalize.
The qualification owner never stages or copies data.

Inspection's shared read-side admission rejects symlinks, unstable or
noncanonical schema records. Lifecycle, task, and reporting reuse it for
equivalent direct-path reads. Hash-bound, schema-free, in-memory, writer, and
state-roster semantics remain owner-local; hostile replacement invalidates evidence.

The semantic checker also has this grouped command:

```bash
.venv/bin/python -I -m emrys validate all-pass \
  --report /absolute/path/SCOPE.validation.tsv \
  --step-id 01 \
  --scope-id SAMPLE
```

It verifies report meaning after an owner validator has run, because
validators may publish failed rows while exiting zero. It prints the report
hash, row count, and ordered check IDs on success and creates no files.

The internal `python -X pycache_prefix=/dev/null -I -m
emrys.orchestration.local_pilot.task --dispatch ...` module is the one-owner
task boundary. It runs the exact admitted public producer and validator,
performs semantic all-pass and stable-content checks, preserves failure
evidence, and publishes a verified-task record only after complete success.
The fixed profile and local Snakemake graph live under
[`workflow/`](../../../../workflow/README.md).

The public control surface uses these internal lifecycle authorities:

- `lifecycle.run_attempt(...)` owns serialization, locks, attempts, receipts,
  processes, recovery policy, and state transitions while consuming admitted
  state;
- `inspection.admit_canonical_record(...)` owns direct-path schema admission;
  `inspect_run(...)` derives state without `.snakemake/` metadata;
- `reporting_boundary` owns reporting transaction publication and semantic
  validation; `reporting_operation` alone composes the three private reporting
  producers for public Run-oriented control.

Each science scope publishes
`state/task-starts/<machine>/<scope>.json` immediately before producer entry.
Within the same Run, an entered scope is reusable only with its succeeded task
attempt and exact verified record. A failed pre-entry diagnostic has no start
record, remains bound in terminal receipts, and may be retried by a later
attempt. Reporting is
downstream of the released scientific Attempt and uses the fixed
`state/reporting/<kind>/{start,verified}.json` ledger with full semantic receipt
revalidation. New generation requires completely empty reporting ledgers and
output directories; partial, corrupt, orphaned, symlinked, or concurrent state
fails closed and is never repaired, overwritten, or adopted.

Resume creates a new immutable attempt, accepts only a failed/interrupted
between-task boundary, rechecks source/tool/config/contracts and every ledger
binding, and adds exactly `--rerun-triggers input --ignore-incomplete`. The
latter is an internal engine-admission flag used only after EMRYS independently
proves that every entered scope is verified and every remaining scope never
crossed producer entry. It never unlocks, cleans metadata, forces work, or
invokes owner recovery.
Blocked attempt receipts are deliberately not resumable; an explicit
future reconciliation record is required to turn historical ambiguity into a
safe automatic boundary. A pre-attempt establishment failure retains its owned
lock under `locks/released-<workflow-attempt-id>-run-lock.json`; inspection
blocks on that evidence and never repairs or removes it.

Ordinary SIGINT/SIGTERM is controlled from before mutex acquisition through a
durable receipt or recovery disposition. A signal before `run.lock` leaves no
attempt evidence; after `run.lock` but before `attempt.json`, it retains
aggregate released-lock evidence and no receipt; after attempt publication, it
is finalized as an interrupted attempt only after the delegated process group
is proved absent. A leader exit is insufficient while a member remains in the
original process group. EMRYS uses bounded TERM/KILL escalation; inability to
prove absence retains the public run lock and publishes no resumable receipt.
SIGKILL, power loss, and descendants that deliberately escape the delegated
session/process group remain outside automatic signal recovery.

The adjacent neutral [machine contracts](../../contracts/orchestration/README.md)
define project-v1, the fixed profile, successor Analysis/Execution-Plan/Run or
historical normalized execution, lock, Attempt, receipt,
task-start/task-attempt/verified-task, and reporting-ledger record shapes. No
automatic owner-recovery mechanism is implemented. Materialization uses only
the fixed source-checkout profile and public owner commands. Request-v3 remains a
private compatibility schema used only to re-admit exact historical Runs. New
and historical Attempts retain the exact `emrys.workflow-attempt.v1` shape and
its `attempts/<attempt-id>/request.yaml` source snapshot; those evidence names
do not make request-v3 a public input. Project and manifest initialization plus
the clean fresh-clone no-science E2E cover
readiness, no-write planning, separate clean success, controlled
between-task failure, byte-preserving resume, inspection, reporting, and
completed-run refusal. The E2E supplies explicit repository-only collaborators;
the shipped command has no fake mode or engine escape hatch. Hosted
real-synthetic direct and disposable single-node Slurm success is recorded
separately; CSU/site, multi-node, production-data, scientific-review, and
biological evidence remain unclaimed.
See [`CONTRACT.md`](CONTRACT.md) for the exact boundary.
