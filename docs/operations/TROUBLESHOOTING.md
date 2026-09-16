# Troubleshooting

Read the first error before retrying. If no Run exists, start with
[Project and runtime checks](#project-and-runtime-checks). Component-specific
inputs, outputs, locks, rollback, and recovery belong in that owner's
`CONTRACT.md` or README.

## First response

1. Stop downstream work and avoid another Run while the failure is unresolved.
   A quiet command alone is not a reason to kill an active job.
2. From the Project, run `emrys inspect RUN`, replacing `RUN` with its two-word
   name, full ID, or unique ID prefix. Omit it for the sole Run or terminal
   picker; EMRYS never assumes latest. Add `--verbose` for evidence.
3. Preserve the complete Run, Project definition, manifests, receipts, locks,
   task/reporting ledgers, logs, native artifacts, partials, backups, and recovery
   markers. Verify the installed package identity and runtime against admitted records.
4. Follow only the recovery offered by inspection or the owning contract.
   Otherwise send the maintainer the command, package identity, error, Run/Attempt identity,
   and relevant log/receipt paths through an approved channel, without private
   study data or credentials.

Never force, unlock, clean, hand-edit, or regenerate one transaction member to
bypass a refusal. File presence, timestamps, scheduler state, logs, and
`.snakemake` do not establish completion.

## Run and reporting state

**No Run yet or an existing root.** Validate the Project/runtime and follow the
[quickstart](../../quickstart.md) or [Slurm setup](RUNBOOK.md#slurm-setup-and-submission).
A queued job may not have created its Run: check its exact scheduler ID before
resubmitting. Inspect or resume an existing Run; do not delete or rename its
root to make initialization succeed.

**Failed or interrupted, with recovery available.** Preview, then confirm:

```bash
emrys resume RUN </dev/null
emrys resume RUN
```

Viking Projects created with `--site viking` already select Slurm. Use
`emrys resume RUN --profile NAME` only to select another existing profile.
Resume creates a new Attempt for the same immutable Run and checks prior work
before reuse; do not bypass it with raw Snakemake. A `blocked` state has no public
reconciliation or cleanup command; keep the evidence and consult the named
component's owner.

**Snakemake fails with `No username set in the environment`.** A compute node
may have no passwd entry for the job's numeric UID. Older EMRYS submissions
also dropped the login-name variables, so Snakemake failed while preparing its
startup header. Update EMRYS to the submission fix that preserves `LOGNAME`,
`USER`, `LNAME`, and `USERNAME`; exporting them only on the head node cannot fix
an older wrapper's explicit export list. Inspect the failed Run and use the
offered resume plan. Preserve its evidence; reinstalling native/R packages
does not address this failure.

**Scientific Results complete, reporting skipped.** From the Project,
preview `emrys report RUN`. A Slurm default profile submits generation from the
head node; direct placement requires a permitted compute host. Only when generation is admitted, execute
`emrys report RUN --execute` and inspect again. The scientific receipt stays
unchanged. Incomplete or blocked reporting needs owner review: preserve its
start/verified records, logs, outputs, and partials. Do not rerun science or
delete report files; `report` cannot force repair or overwrite a partial bundle.

**Empty or incomplete results.** A header-only table can be valid if upstream
receipts and candidate counts agree. Use the linked machine-readable tables for
complete data; silent truncation is a defect. Trace missing report sections to
checked Analysis outputs and reporting records. Direct owner commands do not
create an admissible Run/report; use the grouped Run route when those are needed.

**Step 00c sidecars fail.** Keep the FASTA, FAI, dictionary, and adjacent
lock/staging state together. Never recreate one member independently.

## Project and runtime checks

**Missing command or wrong installation.** Activate the Python environment in
which EMRYS was installed, then check `emrys --version -v`. Install or update
EMRYS in that environment using its package manager; Doctor does not repair
Python packages. Return to the Project for Project commands. Do not add
`PYTHONPATH` or copy package files. Execution identifies the installed code and
its build metadata, independently of the working directory and Git checkout.

**Project initialization or input rejected.** Enter the directory containing
`project.yaml`, or supply its full path with `--project`. Preview-only `init`
creates nothing: execute the reviewed command. Initialization needs an existing,
real writable parent and an absent child, without symlink aliases; do not create
the child yourself. Inspect an existing EMRYS Project or choose another path.
Supply supported YAML fields once and stable regular input files: no duplicate
keys, merges/anchors, templates, `~`, environment interpolation, globs, or
traversal. Pairing needs at least two explicit matching control/treatment
replicate strata; names and row order do not establish pairing. See
[configuration](../../configs/README.md).

**Managed setup rejected.** The managed runtime requires x86-64 Linux, kernel 4.18 or newer, glibc 2.28 or newer,
and Pixi >=0.75.0,<0.76. Follow the quickstart
and activate the Python environment where EMRYS is installed. Doctor repairs
Project-owned native and R state; use the package manager for Python dependencies.
Use an exact institutional runtime if managed
setup is unavailable; do not edit locks to bypass platform or dependency checks.

**Missing or ambiguous runtime tools.** Prepare one exact environment and preview
`emrys runtime discover`. Follow the [institutional selectors and versions](RUNBOOK.md#institution-provided-runtime):
absolute/nonempty `PATH` entries, one distinct installation per tool, readable
Picard jar, matching `JAVA_HOME`/Java, and an actual R package library including
`renv`, not its parent/cache. Discovery neither installs nor loads modules.
Login-node availability is insufficient: probe inside the intended compute
allocation and record batch modules in the profile; interactive modules are not inherited.

**R packages missing or repair stalled.** Managed inventories use a reviewed
`emrys doctor --repair` plan; institutional runtimes need their administrator or
[explicit restore/check](RUNBOOK.md#dependency-maintenance). Download and R
compilation can take time. Read the maintenance JSONL and its sibling
[`package-output.log`](#watching-doctors-installation-log),
keep partial state, and resolve the cause before reviewing another repair plan.
Do not clear caches/libraries wholesale, modify a shared library, or relock
during diagnosis. A stale lock requires manifest/lock review; workflow execution
never installs dependencies.

**Runtime maintenance claim remains.** `runtime/maintenance.lock` blocks another
managed repair after interrupted or failed work. Keep it with the runtime and
Doctor log. A missing process, elapsed time, or cancelled job does not establish
that package-manager descendants stopped; do not delete the claim to retry.
Resolve ownership and partial installation with the maintainer. Successful
repair releases its exact claim before reporting success; a release durability
error still reports failure, even if the pathname is already absent.
Verification without package work does not acquire this claim and is not proof
that the runtime is safe to modify or share.

**Shared runtime needs replacement.** Keep the selected seal, its managed
generation, the dependent Project's inventory, and any `maintenance.lock`.
Missing or changed fixed tool/package content, unresolved claims and unavailable
source paths block admission. Run Doctor in the Project that owns the shared
tools. Doctor prepares a separate verified generation and preserves the old
one. Then preview and apply the exact replacement from each dependent Project:

```bash
emrys runtime discover --from-project /absolute/source/project.yaml --replace
emrys runtime discover --from-project /absolute/source/project.yaml --replace --execute
```

Replacement accepts only an existing shared selection from the same source
Project. Do not edit the recorded digest, copy qualification receipts, remove a
seal, or delete the old generation to bypass admission. A failed repair or
selection can leave a partial generation and claim; retain both for the
maintainer.

**Runtime inventory already exists.** Discovery preserves even identical-looking
inventories. Use Doctor to inspect the admitted runtime. `--replace` changes only
an existing shared selection to a freshly verified generation from the same
source Project; other replacement decisions still require explicit migration or
recovery rather than deletion followed by rediscovery.

**Runtime qualification failed after installation.** Read the exact maintenance
log printed as `diagnostics:`. Its `runtime_check_failed` records identify the
check, target, expected and observed result, exit/error details, host, inventory
digest, and phase. For automatic compute qualification, use the exact job's
stderr path printed at submission; those checks retain their details there
without a second maintenance log. Package installation success does not imply
runtime qualification. Preserve these logs before retrying. For a new read-only
diagnosis, `emrys doctor --verbose` shows individual failed checks;
it observes the current environment and cannot reconstruct an older failure.

### Watching Doctor's installation log

Doctor shows installation stages and elapsed time. Package-manager output is
saved in `package-output.log`, beside the maintenance JSONL; it does not stream
to Doctor's terminal, even with `--verbose`.

To watch those details while installation continues, leave Doctor running and
open a second terminal on the same host: the Viking head node for the
quickstart, or your standalone compute host. Replace the example path below
with the full path printed after **Package output:**, keeping the quotation marks:

```bash
tail -f "/full/path/from/Package output/package-output.log"
```

This shows the last ten lines, then follows new output as it is written. Press
**Ctrl+C in this second terminal** to stop watching; Doctor keeps running in
the first terminal. Package managers may buffer output, so a pause in this log
alone does not mean setup is stuck. Read Doctor's final readiness result in the
first terminal; package installation alone does not finish all checks.

## Storage and Slurm

Direct placement accepts Doctor's single-host receipt or the stronger site
receipt. A ready runtime with unqualified local storage can use
`emrys doctor --repair` on the intended host: this qualifies storage without
installing packages or changing the inventory.

Slurm needs [both storage phases](RUNBOOK.md#slurm-setup-and-submission)
for the exact Project and reference-sidecar roots. Head-node `emrys doctor --repair`
submits the compute phase and finalizes its evidence. Advanced manual compute
qualification requires a real Slurm job; finalize outside that job on the head
node. Never set or unset scheduler variables to imitate either context.
Scheduler availability does not prove locking, hard-link, rename, visibility,
or durability behavior. An unqualified network/distributed root has no implicit
staging or copy exception.

**Existing receipts or staged markers.** Keep receipts and probes. Completed
qualification can be reused; interrupted or inconsistent publication needs owner
review. Repeating `--execute` is not recovery or cleanup.

**Rejected allocation or scratch.** Replace profile placeholders with authorized
partition/account/QoS/node values and preview the submission with
`--verbose </dev/null`. If CPU or memory is inadequate, revise the profile
and create a new Run when its immutable resource envelope changes; do not lower
owner requirements silently. `scratch_parent` must be an existing approved
writable compute path with enough capacity; there is no silent `/tmp` fallback.

**Viking memory request rejected or missing memory metadata.** Retained Viking
submissions reject explicit memory requests with `Memory specification can not
be satisfied`; use the site's `memory_mb: null` placement. EMRYS uses host RAM
constrained by observed process memory limits when Slurm reports no memory
limit, including for four-CPU jobs. It retains the CPU allocation and records
that memory was process-visible, not reserved. A `complete node CPU visibility`
refusal identifies the older capacity policy; update the installation to a
revision containing the process-memory fallback rather than inventing Slurm
variables, requesting an exclusive node, or imposing an arbitrary memory request.

**Missing scheduler stream.** Check the exact job with the Runbook's
[`squeue`/`sacct` commands](RUNBOOK.md#inspecting-a-slurm-run). Slurm may not have
opened its stream yet; scheduler success does not establish Run completion.

**Submission or waited-job error.** Read the operation and underlying error:
failure to invoke `sbatch` differs from failure to prepare or read Doctor's
submission records. Retain the printed scheduler diagnostics and, for Doctor,
both submission transcripts. Escaped characters in the message represent the
original scheduler text; full Doctor transcripts remain at the printed paths.

If a job ID was confirmed, the job was accepted: inspect that exact ID and its
printed stdout/stderr paths before another action. A nonzero
[`sbatch --wait` exit](https://slurm.schedmd.com/sbatch.html#OPT_wait) can reflect
job failure or signal termination; exit 1 alone does not establish cancellation.
During task finalization, a catchable termination signal can arrive after one
terminal record is written but before the next reference is published. Keep
both present and absent-record diagnostics: a retained successful task-attempt
record alone does not prove a complete verified task or a recoverable Run.
Use inspection's supported recovery decision; preserve incomplete chains,
logs, native partials, and locks. SIGKILL and lost native-worker ownership can
still leave ambiguity that requires maintainer investigation.
`Forced workflow termination cannot prove separately owned native groups
stopped` means the outer workflow ended without proof that all native writers
stopped. EMRYS retains the Run lock and omits the Attempt receipt. A missing
outer process or completed scheduler job does not authorize removing that lock;
retain the Run and native workspace for investigation.
If the response leaves the job ID unconfirmed, keep the command, submission
time, and response, and resolve acceptance with the scheduler/operator before
retrying. EMRYS does not automatically resubmit an uncertain request. Scheduler
accounting is operational evidence; inspect the Run to determine its actual
completion and supported recovery.

**Job reached its wall-time limit.** Preserve the exact `sacct` row, scheduler
streams, application log, Run directory, Attempt records, lock, partials, and
native workspace. New submissions request a batch-only `TERM` warning five
minutes before the limit and forward it to the EMRYS delegate, but the hard
limit can still arrive before finalization closes. A dashboard `INTERRUPTED`,
`INCOMPLETE`, or `NOT REACHED` label means only that the scheduler job stopped.
Run `emrys inspect RUN` from the Project and follow its printed supported action.
If inspection says `Do not resume` or `Recovery available: no`, retain the Run
for integrity review; do not remove its lock or retry into that Run.
