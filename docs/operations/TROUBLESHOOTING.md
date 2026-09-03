# Troubleshooting

Use this guide to classify a failure and preserve evidence. Exact owner-specific
inputs, outputs, locks, rollback, and recovery behavior live in the adjacent
`CONTRACT.md`.

## First response

Before retry, repair, deletion, restoration, or adoption:

1. Stop new writers and downstream readers.
2. Run `emrys inspect [RUN]`; use verbose/debug only when normal output is not
   sufficient.
3. Preserve the complete Run root, Project definition, input manifests,
   receipts, locks, task/reporting ledgers, logs, native artifacts, partials,
   backups, and recovery markers.
4. Verify the exact checkout and runtime from live Git and admitted records.
5. Use only the recovery action offered by inspection or the owning contract.

Never force, unlock, clean, hand-edit, regenerate one member of a transaction,
or treat file presence, timestamps, scheduler state, logs, or `.snakemake` as
completion authority.

## Run and reporting state

| Observation | Safe response |
|---|---|
| No Runs exist | Validate the Project and runtime, review `emrys run`, then confirm or use `--execute` for automation. |
| Several Runs exist | Select the exact two-word name, full ID, or unique ID prefix. A terminal picker may help; EMRYS never infers latest. |
| Failure or interruption says recovery is available | Review `emrys resume [RUN]`. It creates a new Attempt for the same immutable Run and re-admits prior work before reuse. |
| State is `blocked` | Preserve everything. No public command reconciles or erases ambiguous evidence; route the named domain to its owner. |
| Science is complete but reports are missing/incomplete | Review `emrys report [RUN]`, then execute only from the admitted empty or reusable reporting state. The scientific receipt remains unchanged. |
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
| `No module named emrys` or wrong checkout imports | Activate the intended clean checkout's locked `.venv` and run the installed `emrys`; do not add `PYTHONPATH` or copy package files. |
| Dirty checkout | Resolve or preserve the changes through the development workflow. Do not discard unrelated work to make Doctor pass. |
| Unknown/duplicate YAML field, merge, template, or unsafe path | Project input is intentionally closed. Supply each supported value once, use stable regular files, and avoid anchors, `~`, environment interpolation, globs, and traversal. |
| Pairing rejected | Declare at least two matching control/treatment replicate strata explicitly. Names and row position are not pairing authority. |
| Project root exists | Inspect it if it is an EMRYS Project; otherwise choose a different absent child. Initialization never adopts or overwrites. |
| Runtime tool missing or ambiguous | Prepare one exact environment, then rerun `emrys runtime discover`. Discovery neither loads modules nor installs. |
| Tool appears only on the login node | Discover again inside the intended compute environment. Login visibility is not batch evidence. |
| Java/Picard mismatch | Make the selected Java 17+ launcher and declared Picard jar exact and readable, then rediscover. Module names and `JAVA_HOME` alone are insufficient. |
| R namespace unavailable | Use explicit Doctor repair or an operator-owned `renv` restore, then rediscover. Workflow execution never installs. |
| Lock file is stale or dependency graph differs | Stop and review the manifest/lock diff. Never relock incidentally during validation or execution. |

## Storage and Slurm

Direct placement requires the Doctor-owned single-host storage receipt or the
stronger site receipt. Slurm requires the completed two-phase qualification for
the exact Project and reference-sidecar roots. Scheduler availability does not
prove locking, hard-link, rename, visibility, or durability semantics.

| Symptom | Safe response |
|---|---|
| Invalid partition/account/QOS/node request | Inspect site policy and eligible nodes; replace placeholders with an authorized profile value. |
| Allocation cannot satisfy CPU or memory | Revise the execution profile and create a new Run when the immutable resource envelope changes. Do not silently reduce owner requirements. |
| Scheduler stream absent | Inspect the exact job with `squeue`/`sacct`; Slurm may not have opened the stream yet. Scheduler state is not Run completion. |
| Scratch is unwritable | Point `scratch_parent` at an existing approved compute path and verify capacity. Do not rely on silent `/tmp` fallback. |
| Network/distributed root is unqualified | Stop. Run both storage-qualification phases for the exact roots; there is no implicit staging or copy exception. |
