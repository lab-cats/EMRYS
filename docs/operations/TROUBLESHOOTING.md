# Troubleshooting

Use this guide when a quickstart or runbook command stops. Read the first
reported error before retrying. If no Run has been created, start with
[Project and runtime checks](#project-and-runtime-checks). Exact owner-specific
inputs, outputs, locks, rollback, and recovery behavior live beside the
implementation in its `CONTRACT.md` or README.

## First response

Before retry, repair, deletion, restoration, or adoption:

1. Avoid starting another Run or downstream work while the failed state is
   unresolved. Do not kill an active job merely because a command is quiet.
2. From the Project root, run `emrys inspect`. With several Runs, select the
   exact Run when prompted or supply its name: `emrys inspect RUN`. Replace
   `RUN` with the displayed name or ID; brackets in command documentation are
   not literal shell text. Use `--detail verbose` or `--detail debug` for more
   evidence.
3. Preserve the complete Run root, Project definition, input manifests,
   receipts, locks, task/reporting ledgers, logs, native artifacts, partials,
   backups, and recovery markers.
4. Verify the exact checkout and runtime from live Git and admitted records.
5. Use only the recovery action offered by inspection or the owning contract.
   If no action is available, give the maintainer the exact command, source
   commit, error, Run/Attempt identity, and relevant log/receipt paths through
   an institution-approved channel. Do not publish study data or credentials.

Never force, unlock, clean, hand-edit, regenerate one member of a transaction,
or treat file presence, timestamps, scheduler state, logs, or `.snakemake` as
completion authority.

## Run and reporting state

| Observation | Safe response |
|---|---|
| No Runs exist | Validate the Project and runtime, then follow the quickstart or [Slurm setup](RUNBOOK.md#slurm-setup-and-submission). A queued Slurm job may not have created its Run yet; inspect its exact scheduler ID before submitting again. |
| Several Runs exist | Select the exact two-word name, full ID, or unique ID prefix. A terminal picker may help; EMRYS never infers latest. |
| Failure or interruption says recovery is available | Preview `emrys resume RUN </dev/null`, then use `emrys resume RUN` and confirm. Add `--profile slurm` for the intended Slurm profile. Resume creates a new Attempt for the same immutable Run and re-admits prior work before reuse. |
| State is `blocked` | Preserve everything. No public command reconciles or erases ambiguous evidence; route the named domain to its owner. |
| Scientific Results are complete but reports were skipped | On a permitted compute host, run `emrys report RUN` to preview. Use `emrys report RUN --execute` only when the command admits generation, then inspect again. The scientific receipt remains unchanged. |
| Reporting is incomplete or blocked | Preserve the reporting start/verified records, logs, outputs, and partials. A failed report may leave an inadmissible partial transaction; `report` does not force repair or overwrite it. Do not rerun scientific work or delete report files to bypass this state. |
| A results table contains only its header | Check the upstream receipt and candidate counts. An empty table can be valid when those records agree. |
| A report omits or truncates expected rows | Use the linked machine-readable result for the complete data. Silent truncation is a defect; missing sections must be traced to the checked Analysis outputs and reporting records. |
| Run root already exists | Inspect or resume it. Never delete or rename it merely to make a new initial Run start. |
| Step 00c sidecars fail | Preserve the FASTA, FAI, dictionary, and adjacent lock/staging state. Do not recreate one member independently. |

Direct owner invocations publish native outputs and do not create an admissible
Run or report. Use the grouped Run path when immutable orchestration and default
reporting are required.

## Project and runtime checks

| Symptom | Meaning and response |
|---|---|
| `emrys: command not found`, `No module named emrys`, or wrong checkout imports | Restore `EMRYS_SOURCE_ROOT` to the intended checkout path and run `source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"`, then `emrys --help`. Return to the Project root for Project commands. Do not add `PYTHONPATH` or copy package files. |
| Dirty checkout | The requirement includes nonignored untracked files. Inspect `git -C "$EMRYS_SOURCE_ROOT" status --porcelain=v1 --untracked-files=all`; preserve unexpected changes and use a separate clean reviewed checkout. Do not discard unrelated work to make Doctor pass. |
| Project definition is unavailable | Enter the exact Project directory containing `project.yaml`, or supply `--project` with its full path. A preview-only `init` has not created a Project; run its reviewed command with `--execute`. |
| Output parent is not canonical or does not exist | Choose an existing real writable parent and an absent final child. Use physical paths without symlink aliases. Creating the final child yourself makes create-absent initialization fail. |
| Unknown/duplicate YAML field, merge, template, or unsafe path | Project input is intentionally closed. Supply each supported value once, use stable regular files, and avoid anchors, `~`, environment interpolation, globs, and traversal. |
| Pairing rejected | Declare at least two matching control/treatment replicate strata explicitly. Names and row position are not pairing authority. |
| Project root exists | Inspect it if it is an EMRYS Project; otherwise choose a different absent child. Initialization never adopts or overwrites. |
| Managed repair rejects the platform or Pixi | Managed setup requires x86-64 Linux and the compatible Pixi version recorded in the [quickstart](../../quickstart.md). Use its host prerequisites or obtain the exact institution-provided runtime; do not edit the runtime lock to bypass them. |
| Repair is restricted to the checkout-owned `.venv` | Activate that checkout's real writable `.venv`. A different virtual environment or symlinked environment is not an authorized managed repair target. |
| Runtime tool missing or ambiguous | Prepare one exact environment, then preview `emrys runtime discover`. All `PATH` entries must be absolute/nonempty and expose only one distinct installation per tool. Follow the [institution-runtime selectors](RUNBOOK.md#institution-provided-runtime). Discovery neither loads modules nor installs. |
| `Picard jar is not selected` or `renv library is not selected` | Set the mandatory absolute `EMRYS_PICARD_JAR` and `EMRYS_RENV_LIBRARY` paths. The R selection must be the existing package library, including `renv`, not its parent or cache. |
| Tool appears only on the login node | Prepare and probe the environment inside the intended compute allocation. For batch execution, record required modules in the execution profile; interactive module loading is not inherited. |
| Java/Picard mismatch | Make the selected Java 17+ launcher and Picard 3.1.1 jar exact and readable. If set, `JAVA_HOME` must identify the same Java as `PATH`; module names alone are insufficient. |
| R namespace unavailable | For a managed inventory, review `emrys doctor --repair`. For an institution runtime, use its administrator or the [explicit R restore/check procedure](RUNBOOK.md#dependency-maintenance). Do not edit `renv.lock` or a shared library. Workflow execution never installs. |
| `runtime inventory already exists and was preserved` | Discovery does not replace inventories, even if the proposed values look identical. Use Doctor to inspect the admitted runtime. Preserve the inventory and obtain an explicit migration/recovery decision before replacing it; do not remove it to rerun discovery. |
| Repair is quiet, fails, or is interrupted | Package download and R compilation may take time. Inspect the displayed maintenance log and package-manager error. Preserve partial managed state; review a new Doctor repair plan only after resolving the reported cause. Never clear caches or libraries wholesale. |
| Lock file is stale or dependency graph differs | Stop and review the manifest/lock diff. Never relock incidentally during validation or execution. |

## Storage and Slurm

Direct placement requires the Doctor-owned single-host storage receipt or the
stronger site receipt. Slurm requires the completed two-phase qualification for
the exact Project and reference-sidecar roots. Scheduler availability does not
prove locking, hard-link, rename, visibility, or durability semantics.

| Symptom | Safe response |
|---|---|
| Runtime is ready but single-host storage is unqualified | On the intended direct execution host, review `emrys doctor --repair`. With a ready runtime it qualifies storage without installing packages or modifying the inventory. This does not satisfy Slurm's two-phase requirement. |
| Storage is not site-qualified | Complete the [compute and finalize phases](RUNBOOK.md#2-qualify-the-exact-storage-roots) for the exact Project and FASTA roots before submitting the whole Run. |
| Compute qualification requires an allocation | Obtain a real compute shell through the site scheduler. Do not set `SLURM_JOB_ID` manually. |
| Final qualification must execute after the allocation | Finish the qualification allocation and return to the head node. Do not unset scheduler variables to bypass context checks. |
| Qualification evidence already exists, or a staged marker remains | Preserve the receipts and probes. A completed qualification can be reused; interrupted or inconsistent publication requires owner review. Repeating `--execute` is not cleanup or recovery. |
| Invalid partition/account/QOS/node request | Inspect site policy and eligible nodes; replace every profile placeholder with an authorized value. Preview the submission with `--log-level debug </dev/null` before executing. |
| Allocation cannot satisfy CPU or memory | Revise the execution profile and create a new Run when the immutable resource envelope changes. Do not silently reduce owner requirements. |
| Scheduler stream absent | Inspect the exact job with `squeue`/`sacct`; Slurm may not have opened the stream yet. Scheduler state is not Run completion. |
| Scratch is unwritable | Point `scratch_parent` at an existing approved compute path and verify capacity. Do not rely on silent `/tmp` fallback. |
| Network/distributed root is unqualified | Stop. For Slurm, run both storage-qualification phases for the exact roots; there is no implicit staging or copy exception. |
