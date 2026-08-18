# Local-pilot orchestration boundary

This owner exposes the fixed local-pilot admission, onboarding, and lifecycle
surface. The zero-context entry points are:

```bash
# Plan first; add --execute to create one absent starter directory.
norad init local-pilot --output-dir /absolute/outside-checkout/starter

# Generate a tiny deterministic four-library science fixture the same way.
norad init synthetic-local-pilot \
  --output-dir /absolute/outside-checkout/synthetic-smoke

# Validate all declared inputs without requiring or probing science tools.
norad validate local-pilot-request \
  --request /absolute/path/to/request.yaml

# Print a fixed-policy runtime TSV to stdout; this command writes nothing.
norad prepare local-pilot-runtime \
  --java /canonical/java-home/bin/java \
  --picard-jar /canonical/path/picard.jar \
  --rscript /canonical/path/Rscript \
  --renv-library /canonical/path/to/renv/library \
  > /new/absent/path/runtime.ready.tsv
```

`init local-pilot` publishes `request.yaml`, `samples.tsv`, `partitions.tsv`,
`runtime.tsv`, and executable `run-in-slurm.sh`, then writes
`starter-set.manifest.tsv` last and re-admits every path, mode, size, and byte.
It neither fills unknown science-tool paths nor installs anything. The runtime
preparer requires explicit Java, Picard-jar, Rscript, and `renv`-library paths.
For Bash, STAR, samtools, GATK, bcftools, RSeQC `infer_experiment.py`, and
gunzip, omission of the corresponding optional path is allowed only when PATH
contains exactly one distinct resolved executable. It preserves the tracked
version policy and performs no version probe; the doctor remains the readiness
authority.

`run-in-slurm.sh` has two explicit modes. Outside an allocation it only calls
`sbatch` after its named `NORAD_*` scheduler, input, runtime, module, and
scratch settings are provided. `NORAD_SLURM_MEMORY=site-default` omits
`--mem`; a positive explicit Slurm size is passed exactly once.
`NORAD_MODULE_MODE=exact` requires and loads the declared initializer and
colon-delimited roster, while `none` requires both module values to be
explicitly empty and loads nothing. It prints the job ID and exact
stdout/stderr tail paths.

Inside an allocation the wrapper creates one mode-`0700` job directory below
the declared `NORAD_SCRATCH_PARENT`, exports it as `TMPDIR`, logs its
canonical path plus `df -PT` filesystem/capacity evidence, and removes it on
exit. It then validates the request, runs the doctor, and plans or executes the
whole single-host local pilot. `NORAD_SLURM_CPUS` is an allocation assertion;
the request's closed `resources` block remains the authority for workflow
capacity, concurrent samples, and owner threads. The wrapper never runs
analysis or large-input validation on a login node and does not claim
per-owner Slurm scheduling or multi-node execution.

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
  tests/orchestration/local_pilot/test_onboarding.py \
  tests/test_public_cli_contracts.py
```

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
  `renv`, and Step `08` namespaces without creating or repairing anything.

The doctor also has the grouped public command:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad doctor local-pilot \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

Exit `0` means every declared readiness check passed, exit `1` reports exact
readiness blockers and remediation routes, and exit `2` identifies malformed
or unsafe input. The doctor runs only bounded version, namespace, hash, and
path probes. Even exit `0` is only local readiness evidence: no workflow or
scientific-owner computation, scheduler, cluster job, scientific review, or
biological validation ran.

B5 adds the source-checkout-bound public control surface. Every mutating route
requires the controlled Python runtime, is dry-run-first, and delegates owner
work only through the accepted fixed profile:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv

.venv/bin/python -X pycache_prefix=/dev/null -I -m norad inspect \
  local-pilot-run --run-root /absolute/path/to/workspace/runs/run-DIGEST

.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

`run` and `resume` print the exact owner and Snakemake plan and write nothing
unless `--execute` is present. `inspect local-pilot-run` is always read-only.
The direct public Python surface is `control.plan_run`, `plan_resume`, and
`execute_plan`, backed by the single production owner
`materialization.build_attempt_plan`; tests pass explicit collaborators rather
than monkeypatching module globals. Exact setup and execution order lives in
the [runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-execution).

The neutral
`norad.contracts.orchestration.projection.project_reporting(...)` API
reproduces the exact legacy reporting contract and deterministic artifact
inventory without depending on the local-pilot application owner.

This local pilot assumes a single-user, cooperative workspace on a POSIX local
filesystem that provides working advisory `flock` and same-filesystem hard
links. Its no-follow and descriptor-bound checks reject admitted symlink
components, observed leaf substitution, unstable bytes, and unexpected state
rosters. All sanctioned lifecycle writers hold the acquisition mutex. A
hostile process concurrently replacing a lock leaf in the narrow post-link,
pre-unlink interval, renaming ancestor directories, or changing mount
namespaces is outside this boundary and invalidates the evidence. NFS,
network/distributed filesystems, and cluster locking semantics are not claimed
until separately validated at the site.

The semantic checker also has this grouped command:

```bash
.venv/bin/python -I -m norad validate all-pass \
  --report /absolute/path/SCOPE.validation.tsv \
  --step-id 01 \
  --scope-id SAMPLE
```

It verifies report meaning after an owner validator has run, because
validators may publish failed rows while exiting zero. It prints the report
hash, row count, and ordered check IDs on success and creates no files.

The internal `python -X pycache_prefix=/dev/null -I -m
norad.orchestration.local_pilot.task --dispatch ...` module is the B3 one-owner
job boundary. It runs the exact admitted public producer and validator,
performs semantic all-pass and stable-content checks, preserves failure
evidence, and publishes a verified-task record only after complete success.
The fixed profile and local Snakemake graph live under
[`workflow/`](../../../../workflow/README.md).

B4 supplies the internal lifecycle authorities used by the B5 public adapter:

- `lifecycle.run_attempt(...)` owns the persistent benign advisory acquisition
  mutex, under-mutex stale-attempt revalidation, one create-exclusive aggregate
  run lock, no-replace hard-link release evidence,
  immutable attempt record, exact reviewed Snakefile and absolute workflow
  profile, the same content-admitted Python runtime running
  `-X pycache_prefix=/dev/null -I -m snakemake`, new-process-group invocation,
  transaction-wide SIGINT/SIGTERM deferral and one-time forwarding,
  sanitized subprocess startup state, bounded process-group quiescence proof,
  semantic task/report transaction revalidation, retained released-lock
  evidence, exact producer-entry/reporting ledgers, recursively closed
  attempt-local task evidence, and the terminal attempt receipt published last;
- `inspection.inspect_run(...)` derives prepared, running,
  resume-available, blocked, or complete state from NORAD contracts and
  receipts, never from `.snakemake/` metadata;
- `reporting_boundary.publish_start(...)` and `publish_verified(...)` own the
  irreversible entry and semantic-completion records for each of the three
  reporting transactions; `validate_start(...)` and `validate_verified(...)`
  are their read-only admission surface. Its grouped module CLI is internal to
  the fixed workflow, not a user lifecycle command.

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
latter is an internal engine-admission flag used only after NORAD independently
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
original process group. NORAD uses bounded TERM/KILL escalation; inability to
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
