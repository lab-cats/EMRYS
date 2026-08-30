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
# Omitted answers are prompted on a terminal; add --execute after review.
emrys init project

# Generate the default 130-pair deterministic science fixture the same way.
emrys init synthetic-local-pilot \
  --output-dir /absolute/outside-checkout/synthetic-smoke \
  --dataset-profile smoke-v1

# Select the closed 100,000-pair-per-library, 5 Mb profile explicitly.
emrys init synthetic-local-pilot \
  --output-dir /absolute/outside-checkout/synthetic-production-like \
  --dataset-profile production-like-v1

# Validate all declared inputs without requiring or probing science tools.
emrys validate project \
  --project /absolute/path/to/project.yaml

# Print a fixed-policy runtime TSV to stdout; this command writes nothing.
emrys prepare local-pilot-runtime \
  --java /canonical/java-home/bin/java \
  --picard-jar /canonical/path/picard.jar \
  --rscript /canonical/path/Rscript \
  --renv-library /canonical/path/to/renv/library \
  > /new/absent/path/runtime.ready.tsv
```

`init manifests` produces deterministic strict manifests with absolute data
paths and requires every biological assignment explicitly. `init project`
validates them, records their admitted absolute paths without copying manifests
or raw data, creates mode-`0700` `runs/`, `logs/`, and `runtime/`, and publishes
request-v3 `project.yaml` last. Its canonical parent is the Project root used by
run and Doctor; Results remain under `runs/<run-id>/results`. Setup creates no
execution or runtime profile, Run, Attempt, Results, or application log.

The retained runtime preparer renders the fixed roster without probing or
installing; ambiguous PATH resolution fails closed and Doctor remains the
readiness authority. Use an exact historical checkout for an entered
historical Run.

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
workflow completion. Per-owner Slurm scheduling, multi-node execution, and the
16 existing stage/utility `.slurm` files are unchanged by this whole-Run
cutover.

An executing Run Attempt owns one application log, by default beneath
`<project-root>/logs/application`. Reporting is invoked automatically after
scientific work, publishes its transaction receipts last, and is not a
scientific stage.

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

`init synthetic-local-pilot` has two closed dataset profiles. The default
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
  YAML Project definition plus its ordered TSV manifests and returns an
  immutable Analysis revision without writing a Run. Its no-follow,
  descriptor-bound admission makes the exact read bytes the only parse and
  identity authority. `ProjectAdmission` retains immutable source, profile,
  and construction bytes plus that Analysis; mapping access returns fresh
  disposable views that cannot mutate that authority;
- `all_pass.require_all_pass(...)` checks the meaning of one owner-validation
  report rather than trusting its process exit;
- `doctor.inspect_local_pilot(...)` admits one Project plus the fixed profile,
  checks its external Project root, exact clean source checkout, controlled
  Python/Snakemake, science-tool paths and versions, Picard jar, guarded
  `renv`, Step `08` namespaces, and the exact final storage qualification
  without creating or repairing anything.

The doctor also has the grouped public command:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys doctor local-pilot \
  --project /absolute/path/to/project.yaml \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

Exit `0` means every declared readiness check passed, exit `1` reports exact
readiness blockers and remediation routes, and exit `2` identifies malformed
or unsafe input. The doctor runs only bounded version, namespace, hash, and
path probes. Ordinary commands retain a 30-second bound; guarded R namespace
loads have a separate 120-second bound with elapsed diagnostics and fail closed
on timeout. Even exit `0` is only local readiness evidence: no workflow or
scientific-owner computation, scheduler, cluster job, scientific review, or
biological validation ran.

B5 adds the source-checkout-bound public control surface. Every mutating route
requires the controlled Python runtime, is dry-run-first, and delegates owner
work only through the accepted fixed profile:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys run \
  --project /absolute/path/to/project.yaml \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv \
  --execution-profile /absolute/path/to/emrys.execution.yaml

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys inspect \
  local-pilot-run --run-root /absolute/project/runs/run-DIGEST

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys resume \
  --run-root /absolute/project/runs/run-DIGEST \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv \
  --execution-profile /absolute/path/to/emrys.execution.yaml

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys report \
  --run-root /absolute/project/runs/run-DIGEST
```

With direct placement, `run` and `resume` print concise Run identity, combined
pending/reusable work, and reporting information; a terminal asks once before
executing that exact plan. With Slurm placement, EMRYS constructs one frozen
submission plan, prints its placement summary, and after confirmation submits
that same object once; Run planning occurs inside the allocation. Refusal, EOF,
or interruption opens no application log and writes nothing. Noninteractive
omission of `--execute` retains the no-write/no-submit behavior, while
`--execute` remains the explicit automation path. After successful scientific
execution they generate the fixed reports by
default; `--no-report` stops after the successful v2 Attempt receipt without
changing Results. `report` independently validates a completed Run and plans
without writes, then generates with `--execute` or reuses an exact complete
report transaction. Verbose output adds the Run root,
resources/allocation, execution profile, and scheduler streams; debug output
adds exact engine, scheduler, and task commands. `inspect local-pilot-run` is
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
before delegation and after the child terminates. A missing, changed, or
semantically invalid receipt blocks the attempt; the immutable attempt cannot
accept its own declared storage identity as proof.
The grouped CLI is the supported control surface. Its private planning helpers
delegate to the single production owner `materialization.build_attempt_plan`;
tests pass explicit collaborators rather than monkeypatching module globals.
Exact setup and execution order lives in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

The neutral
`emrys.contracts.orchestration.projection.project_reporting(...)` API
reproduces the exact legacy reporting contract and deterministic artifact
inventory without depending on the local-pilot application owner.

This local pilot requires one final two-phase storage-qualification receipt for
the workflow parent and Step `00c` sidecar parent before doctor can report
ready. The receipt proves the required hard-link, advisory-`flock`, atomic
rename, fsync, numeric-identity, mount, cross-node visibility, and
post-allocation durability checks for those exact roots. NFS and other
network/distributed filesystems remain unsupported until that site check
finalizes; node-local storage that is not durably visible to the head node
cannot finalize. The qualification owner never stages or copies data.

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
emrys.orchestration.local_pilot.task --dispatch ...` module is the B3 one-owner
job boundary. It runs the exact admitted public producer and validator,
performs semantic all-pass and stable-content checks, preserves failure
evidence, and publishes a verified-task record only after complete success.
The fixed profile and local Snakemake graph live under
[`workflow/`](../../../../workflow/README.md).

B4 supplies the internal lifecycle authorities used by the B5 public adapter:

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
An entered scope is reusable only with its succeeded task attempt and exact
verified record. A failed pre-entry diagnostic has no start record, remains
bound in terminal receipts, and may be retried by a later attempt. Reporting is
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
Blocked attempt receipts are deliberately not resumable in B4; an explicit
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
define the temporary Project-adapter request schema, profile, successor Analysis/Execution-Plan/Run or historical
normalized execution, lock, attempt, receipt,
task-start/task-attempt/verified-task, and reporting-ledger record shapes. No
automatic owner-recovery mechanism is implemented. B5 materializes only the
fixed source-checkout profile and public owner commands. B6 adds Project and
manifest initialization plus a clean fresh-clone no-science E2E covering
readiness, no-write planning, separate clean success, controlled
between-task failure, byte-preserving resume, inspection, reporting, and
completed-run refusal. The E2E supplies explicit repository-only collaborators;
the shipped command has no fake mode or engine escape hatch. Real-tool, VM,
SLURM, CSU, scientific-review, and biological evidence remain unclaimed.
See [`CONTRACT.md`](CONTRACT.md) for the exact boundary.
