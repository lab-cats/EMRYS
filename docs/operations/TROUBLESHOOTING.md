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
   picker; EMRYS never assumes latest. Add `--detail verbose` or `debug` for evidence.
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

For Slurm, explicitly select the intended profile: `emrys resume RUN --profile slurm`.
Resume creates a new Attempt for the same immutable Run and checks prior work
before reuse; do not bypass it with raw Snakemake. A `blocked` state has no public
reconciliation or cleanup command; keep the evidence and consult the named
component's owner.

**Scientific Results complete, reporting skipped.** On a permitted compute host,
preview `emrys report RUN`. Only when generation is admitted, execute
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

**Managed setup rejected.** Follow the quickstart's x86-64 Linux/Pixi prerequisites
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
compilation can take time. Read the maintenance log and package-manager error,
keep partial state, and resolve the cause before reviewing another repair plan.
Do not clear caches/libraries wholesale, modify a shared library, or relock
during diagnosis. A stale lock requires manifest/lock review; workflow execution
never installs dependencies.

**Runtime inventory already exists.** Discovery preserves even identical-looking
inventories. Use Doctor to inspect the admitted runtime; replacing it requires
an explicit migration/recovery decision, not deletion followed by rediscovery.

## Storage and Slurm

Direct placement accepts Doctor's single-host receipt or the stronger site
receipt. A ready runtime with unqualified local storage can use
`emrys doctor --repair` on the intended host: this qualifies storage without
installing packages or changing the inventory.

Slurm needs [both storage phases](RUNBOOK.md#2-qualify-the-exact-storage-roots)
for the exact Project and reference-sidecar roots. Compute qualification requires
a real allocated shell; finalize after releasing it and returning to the head
node. Never set or unset scheduler variables to imitate either context.
Scheduler availability does not prove locking, hard-link, rename, visibility,
or durability behavior. An unqualified network/distributed root has no implicit
staging or copy exception.

**Existing receipts or staged markers.** Keep receipts and probes. Completed
qualification can be reused; interrupted or inconsistent publication needs owner
review. Repeating `--execute` is not recovery or cleanup.

**Rejected allocation or scratch.** Replace profile placeholders with authorized
partition/account/QoS/node values and preview the submission with
`--log-level debug </dev/null`. If CPU or memory is inadequate, revise the profile
and create a new Run when its immutable resource envelope changes; do not lower
owner requirements silently. `scratch_parent` must be an existing approved
writable compute path with enough capacity; there is no silent `/tmp` fallback.

**Missing scheduler stream.** Check the exact job with the Runbook's
[`squeue`/`sacct` commands](RUNBOOK.md#inspecting-a-slurm-run). Slurm may not have
opened its stream yet; scheduler success does not establish Run completion.
