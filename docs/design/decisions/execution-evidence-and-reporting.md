# Execution, evidence, and reporting decisions

Exact interfaces and failure behavior remain with their functional owners. This
record preserves the reasons that span owners.

## Execution and publication

### Plan before mutation

Every Run has an immutable inspectable plan before its first mutation.
Interactive `run` and `resume` show that plan and ask once; automation uses
`--execute`. Refusal, EOF, and interruption before authority write, submit, and
log nothing. Dry-run and execution use the same admitted values.

### Publish validated transactions

Multi-file owners use declared destinations, owned locks, staging, stable-input
rechecks, validation before publication, no-clobber behavior, bounded rollback,
and a receipt or summary published last. Transaction completion says only that
the declared transaction was admitted; it does not promote scientific meaning
or unrelated evidence.

Preserve locks, backups, partials, and recovery markers whenever ownership or
cleanup cannot be proved. Characterize unsafe states before correcting them.
An observed defect is neither an approved contract nor evidence that unlike
transaction implementations should share one abstraction.

### Separate placement from authority

Direct and whole-Run single-node Slurm placement use the same Snakemake
backend. Scheduler and engine metadata are observations, never scientific,
completion, artifact-admission, or recovery authority. Local, hosted Slurm,
institutional site, multi-node, and production behavior require separate proof.

## Runtime, storage, and repair

The Project-owned runtime inventory is the one admitted authority regardless of
whether an environment was Managed, Site-provided, or explicitly prepared.
Runtime discovery observes a declared environment and silently selects or
installs nothing. The advanced runtime, reference, and storage evidence owners
reconcile explicit inventories without repair.

Doctor diagnosis is read-only. Confirmed repair may mutate only its declared
EMRYS-owned environment and storage-evidence locations, delegates dependency
solving and installation to `uv`, Pixi, and `renv`, preserves scientific inputs
and site/user environments, records one maintenance log, and requalifies.
Compute, validation, and reporting never install dependencies.

Repository R activation remains opt-in through `EMRYS_USE_RENV=1`. Report
rendering uses only the locked packaged Jinja2, Matplotlib, and Logomaker
environment and a private temporary cache. Neither path accesses the network or
repairs itself during computation.

## Evidence and external interpretation

Implementation checks, fixtures, real-runtime checks, scheduler execution,
institutional-site evidence, production data, scientific review, and biological
validation are distinct claims. A passed workflow does not make a candidate an
editing site or a causal biological conclusion.

Expected evidence remains represented when missing, failed, incomplete,
blocked, unavailable, or not run. Passed claims require their declared evidence
relationships and exact content bindings. External review and adjudication may
reference immutable EMRYS outputs but are not pipeline inputs, states, gates, or
completion criteria.

## Structured artifacts and reporting

Reporting consumes versioned admitted artifacts through read-only adapters. It
does not discover inputs, rerun analysis, install tools, repair artifacts, or
grant upstream completion. Expected artifacts have explicit unique paths and
identities; globs, traversal, unresolved templates, and implicit substitution
are rejected.

A successful full Run invokes reporting by default after scientific Attempt
completion; `--no-report` disables it. `emrys report` can independently plan,
generate, or reuse reports. Reporting creates neither a Run nor an Attempt, and
failure or regeneration does not invalidate admitted science.

The selected analysis reporter owns bespoke scientific presentation. EMRYS
owns the fixed evidence and operations projection. The two receipt-bound HTML
files answer three questions:

| Section | Question |
|---|---|
| Scientific | What did the analysis find, and what are its limitations? |
| Evidence and provenance | Why does this result correspond to these inputs, tools, validations, and artifacts? |
| Operations | How did execution proceed, consume resources, fail, recover, or complete? |

Reports are deterministic, self-contained, script-free, autoescaped projections
of admitted values. Figure inputs, policy, renderer versions, hashes, and
availability are disclosed. Native scientific PDFs remain analysis artifacts,
not alternate report formats. Published validation rows preserve their exact
meaning and cannot promote runtime, site, scientific, or biological claims.

## Console, logs, and status

Normal output presents Run identity, scientific milestones, actionable failure,
Results, and the durable log location. Verbose and debug progressively expose
resources, placement, engine, scheduler, task, transaction, receipt, and raw
stream detail. Projection level never changes behavior or exit status.

One executing application operation owns one no-clobber log; delegated owners
do not append concurrently. Logs are protected diagnostics, not completion
authority. There is no automatic upload, rotation, truncation, or deletion.
The binding sink, redaction, degradation, and ownership behavior is in
[`LOGGING_CONTRACT.md`](../LOGGING_CONTRACT.md).

Status is derived from immutable Run, Attempt, task, reporting, receipt, and
lock records. No mutable status cache competes with them. Elapsed time belongs
to one current or latest Attempt; resumes are not silently summed and no ETA is
invented. The stale dashboard is not a status or Results authority and remains
frozen under `DASHBOARD-RETIRE-01` pending separately approved retirement.
