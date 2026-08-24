# Local-pilot orchestration boundary

This owner exposes the fixed local-pilot admission, onboarding, and lifecycle
surface. The zero-context entry points are:

```bash
# Plan first; add --execute to create one absent starter directory.
emrys init local-pilot --output-dir /absolute/outside-checkout/starter

# Generate a tiny deterministic four-library science fixture the same way.
emrys init synthetic-local-pilot \
  --output-dir /absolute/outside-checkout/synthetic-smoke

# Validate all declared inputs without requiring or probing science tools.
emrys validate local-pilot-request \
  --request /absolute/path/to/request.yaml

# Print a fixed-policy runtime TSV to stdout; this command writes nothing.
emrys prepare local-pilot-runtime \
  --java /canonical/java-home/bin/java \
  --picard-jar /canonical/path/picard.jar \
  --rscript /canonical/path/Rscript \
  --renv-library /canonical/path/to/renv/library \
  > /new/absent/path/runtime.ready.tsv
```

`init local-pilot` publishes `request.yaml`, editable `emrys.launcher.yaml` and
`emrys.resources.yaml`, `samples.tsv`, `partitions.tsv`, `runtime.tsv`, and
executable `run-in-slurm.sh`, then writes `starter-set.manifest.tsv` last and
re-admits every path, mode, size, and byte.
The EMRYS identity cutover does not adopt or resume pre-cutover run roots.
Legacy adjacent `norad.launcher.yaml` or `norad.resources.yaml` files fail
closed instead of being silently ignored; rename them before admission. Use an
exact historical checkout for an already-entered historical run.
It neither fills unknown science-tool paths nor installs anything. The runtime
preparer requires explicit Java, Picard-jar, Rscript, and `renv`-library paths.
For Bash, STAR, samtools, GATK, bcftools, RSeQC `infer_experiment.py`, and
gunzip, omission of the corresponding optional path is allowed only when PATH
contains exactly one distinct resolved executable. It preserves the tracked
version policy and performs no version probe; the doctor remains the readiness
authority.

`run-in-slurm.sh` has two explicit modes. Outside an allocation it resolves
packaged launcher defaults, adjacent or explicit launcher YAML, and optional
wrapper arguments in that order, then calls `sbatch` once. Exact `{env:
EMRYS_NAME}` references read the invocation environment before the
generation-bound source checkout's private root `.env`; no shell interpolation
is accepted. The private file is optional, closed to launcher variables,
owner-only, and never copied into a starter or printed. The generated wrapper
binds its source checkout and controlled Python at generation instead of
accepting either from launcher configuration.

`memory: site-default` omits `--mem`; a positive explicit Slurm size is passed
exactly once. `exclusive: true` and a nonempty `nodelist` emit one
`--exclusive` and `--nodelist=...` respectively. These values request the
outer allocation; they are not workflow-resource minima. `PATH` inside the
allocation is sealed at submission to the generation-bound lexical Python
launcher parent followed by `/usr/bin:/bin`; the submit shell's ambient path is
not propagated. Virtualenv launcher symlinks retain their lexical identity
after stable target admission. Ambient `SBATCH_*` variables and ambient
`EMRYS_EXECUTE` are removed before the `sbatch` client is invoked.
Submission binds the live `/usr/bin/id` UID and user name, requires
`USER` and `LOGNAME` to agree, and exports that identity explicitly. Batch
mode re-observes the same identity before module loading or workspace access.
Module mode `exact` requires and loads the declared initializer and roster,
while `none` requires both module values to be empty and loads nothing. The
wrapper prints the job ID and exact stdout/stderr tail paths. Batch entry also
requires the exact internal marker emitted by that submit helper, not merely an
inherited `SLURM_JOB_ID`. Submission is dry-run-first regardless of ambient
`EMRYS_EXECUTE`; only the explicit wrapper `--execute` action derives the
internal batch execution flag.

Inside an allocation the wrapper creates one mode-`0700` job directory below
the declared `EMRYS_SCRATCH_PARENT`, exports it as `TMPDIR`, logs its
canonical path plus `df -PT` filesystem/capacity evidence, and removes it on
exit. It then validates the request, runs the doctor, and plans or executes the
whole single-host local pilot. EMRYS observes `SLURM_CPUS_PER_TASK`, Slurm's
memory environment, process CPU affinity, and the process memory limit before
resolving the resource policy. When a full-node allocation omits Slurm memory
variables, EMRYS uses process-visible memory; ambiguous partial-node
allocations without an explicit memory boundary remain rejected. Packaged
defaults are overridden by adjacent `emrys.resources.yaml`, then by any
explicit resource CLI values. The wrapper never runs
analysis or large-input validation on a login node and does not claim
per-owner Slurm scheduling or multi-node execution.

The adjacent `dashboard.py` owns a read-only live view over one wrapper job's
Slurm metadata and append-only stdout/stderr streams. The repository-level
`make dashboard` target is only a thin entry point to that owner. Selection,
bounded current-user scheduler discovery, stream admission and sanitization,
incremental parsing, and terminal rendering stay here; the dashboard never
scans shared storage, mutates the workflow, or replaces final EMRYS
inspection. Scheduler state, inferred progress and timing, displayed report
paths, and the dashboard process exit are operational observations rather than
completion, validation, or evidence authority.

This dashboard is currently a CSU-oriented preview, not a portable execution
contract. It expects CSU Slurm metadata and the generated local-pilot wrapper's
exact stream naming, and parts of its display still encode the fixed qualified
stage topology, six-sample cohort, and 25-partition qualification run.
Workflow cores, per-stage concurrency, per-step thread allocations, and memory
policy are read from the selected run's control stream rather than fixed to one
benchmark policy. See the
[runbook](../../../../docs/operations/RUNBOOK.md#live-whole-run-dashboard) for
the supported preview commands and explicit override rules.

`init synthetic-local-pilot` publishes a deterministic 100-kb reference, GTF,
four paired 130-read libraries across two control/treatment strata, matched
request/manifests, and metadata. `fixture.manifest.json` is written last after
the generated request passes the same normalizer and reference-compatibility
checks. The engineered smoke expectation is three Step 09 computational rows
and one significant row; it is not scientific adjudication or biological
evidence.

Focused protection is:

```bash
.venv/bin/python -m pytest -q \
  tests/orchestration/local_pilot/test_launcher_config.py \
  tests/orchestration/local_pilot/test_onboarding.py \
  tests/orchestration/local_pilot/test_dashboard.py \
  tests/test_public_cli_contracts.py
```

Run the deferred workstation acceptance sequence in
[`docs/operations/LOCAL_PILOT_LAUNCHER_TEST_PLAN.md`](../../../../docs/operations/LOCAL_PILOT_LAUNCHER_TEST_PLAN.md)
after restoring the locked development environment. Checks that require that
environment remain explicitly `NOT RUN` until then; they are not inferred from
static validation.

The underlying narrow read-only admission APIs are:

- `normalization.normalize_request(request_path, profile)` safely admits one
  YAML request plus its ordered TSV manifests and returns a canonical,
  content-bound execution identity without writing a run. Its no-follow,
  descriptor-bound admission makes the exact read bytes the only parse and
  identity authority;
- `all_pass.require_all_pass(...)` checks the meaning of one owner-validation
  report rather than trusting its process exit;
- `doctor.inspect_local_pilot(...)` admits one request plus the fixed profile,
  checks a disjoint workspace plan, exact clean source checkout, controlled
  Python/Snakemake, science-tool paths and versions, Picard jar, guarded
  `renv`, Step `08` namespaces, and the exact final storage qualification
  without creating or repairing anything.

The doctor also has the grouped public command:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys doctor local-pilot \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
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
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys inspect \
  local-pilot-run --run-root /absolute/path/to/workspace/runs/run-DIGEST

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys resume \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

`run` and `resume` print the exact owner and Snakemake plan and write nothing
unless `--execute` is present. `inspect local-pilot-run` is always read-only.
The request defines scientific identity only. Execution-resource precedence is
packaged defaults, optional YAML, then explicit CLI values. A resume without a
new resource source reuses its predecessor's immutable effective policy while
checking that it still fits the newly observed allocation.
Execution re-admits the normalized reference/workspace storage qualification
before delegation and after the child terminates. A missing, changed, or
semantically invalid receipt blocks the attempt; the immutable attempt cannot
accept its own declared storage identity as proof.
The direct public Python surface is `control.plan_run`, `plan_resume`, and
`execute_plan`, backed by the single production owner
`materialization.build_attempt_plan`; tests pass explicit collaborators rather
than monkeypatching module globals. Exact setup and execution order lives in
the [runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-execution).

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
  validation. Its grouped module CLI is internal to the fixed workflow.

Each science scope publishes
`state/task-starts/<machine>/<scope>.json` immediately before producer entry.
An entered scope is reusable only with its succeeded task attempt and exact
verified record. A failed pre-entry diagnostic has no start record, remains
bound in terminal receipts, and may be retried by a later attempt. Reporting
uses the equivalent fixed `state/reporting/<kind>/{start,verified}.json`
ledger, with full semantic receipt revalidation.

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
define request, profile, normalized execution, lock, attempt, receipt,
task-start/task-attempt/verified-task, and reporting-ledger record shapes. No
automatic owner-recovery mechanism is implemented. B5 materializes only the
fixed source-checkout profile and public owner commands. B6 adds matched public
request, sample, and partition starters plus a clean fresh-clone no-science E2E
covering readiness, no-write planning, separate clean success, controlled
between-task failure, byte-preserving resume, inspection, reporting, and
completed-run refusal. The E2E supplies explicit repository-only collaborators;
the shipped command has no fake mode or engine escape hatch. Real-tool, VM,
SLURM, CSU, scientific-review, and biological evidence remain unclaimed.
See [`CONTRACT.md`](CONTRACT.md) for the exact boundary.
