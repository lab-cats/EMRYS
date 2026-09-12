# Execution, evidence, and reporting decisions

Owner-specific interfaces and failure behavior remain with their functional
owners. This record owns shared safety rules and the reasons that span owners.

## Execution and publication

### Plan before mutation

Every Run has an immutable inspectable plan before its first mutation.
Interactive `run` and `resume` show that plan and ask once; automation uses
`--execute`. Refusal, EOF, and interruption before authority write, submit, and
log nothing. Dry-run and execution use the same admitted values.

### Publish validated transactions

Scientific producers own computation, output checks and provenance. The existing
runner owns their execution and publication across reference, sample, cohort,
and analysis tasks. Requiring the runner removes duplicated standalone lifecycles
without introducing a manager hierarchy. The
[scientific-worker contract](../../../src/emrys/orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution)
owns staging, locks, publication order, rollback, retained evidence, and the
independent validation gate.

A new Run plan creates a new Run. Existing immutable plans retain their original
interpretation and require their bound implementation for execution. A completed
native publication does not imply task completion or promote scientific meaning.

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

### Fixed report-output consolidation

Fixed report outputs have one ordered declaration in the receipt-contract owner.
The declarations share one owner. Scientific identity is a separate responsibility:
[`run_implementation.py`](../../../src/emrys/orchestration/run_coordinator/run_implementation.py)
hashes whole files used by computation and scientific admission. Materialization
binds that digest into the Execution Plan and Run; resume reconstructs the same
binding. Shared headers, safe IDs, path rules, scope grouping, scientific evidence
and immutable-record admission remain covered. Mixed owners cannot be excluded
merely because reporting calls them.

#### Scientific compatibility and reporting provenance

Reporting source changes must not invalidate scientific work. The scientific
fingerprint includes computation, scientific validation and shared admission;
it excludes reporting-only artifact contracts and reporting ledger inspection. That
inspection lives in the reporting boundary. A distribution release number is
provenance, not a scientific module change. Exact module bytes, substantive
module metadata, backend semantics and the complete Python lock remain bound.
A dependency update can therefore still require a new Run; narrowing that lock
requires a separate dependency audit.

| Operation | Required behavior |
|---|---|
| Inspect current records | Admit original immutable Run, Attempt, task and lock evidence. Scientific Results and report status remain separate. |
| Resume locally or through Slurm | Rebuild the same scientific Run and recheck its data, tools, resources and implementation. Each new Attempt records its actual installed package. Code cannot change during an Attempt. |
| Generate missing reports | Require a successful complete scientific Attempt, identical scientific implementation and backend, and empty owned outputs. Record the actual reporting package and recheck it through publication. |
| Reuse completed reports | Bind the original receipt through its verified ledger; recheck its recorded data inputs, outputs, HTML contracts and complete file rosters. Retain the original publisher attribution without invoking the current renderer. |

The Run result manifest points once to the original scientific Run and Attempt
by path and hash. Those immutable records retain package identity, commands,
inputs, reused task origins and the Processing source chain. Reporting no longer
reconstructs scientific implementation claims from today's installed files or
repeats an implementation-status column for each artifact. The manifest's own
provenance identifies its publisher; the HTML receipt identifies its reporter.
The core reporter digest uses the already admitted full EMRYS package, covering
the excluded report contract as well as templates and rendering code.

New publication still compares deterministic output bytes and checks HTML safety
and accessibility. The manifest binds both TSV table hashes. The HTML receipt also persists the
reporting provider's complete
additional data-input roster, including figure references. This replaces the
need to rerun the renderer to rediscover those inputs during reuse. Template
and stylesheet hashes remain original producer provenance; they are not data
inputs checked against a newer installation.

Current records use artifact entries v2, Run summaries v5 and report receipts v6.
The [version policy](platform-direction.md#version-support) applies: no old-hash
translation, record rewriting or historical-format reader is added. Existing
data and evidence remain intact for ordinary tools or the originating software.
All current reports use `results/reports/RUN_ID`. Publication still refuses
existing or ambiguous output state and preserves locks and recovery evidence.

#### Declaration owner and consumers

The receipt contract owns the immutable `REPORT_OUTPUTS` tuple of output ID,
kind, and suffix, exported through the artifact API. The
[reporting output contract](../../../src/emrys/reporting/README.md#report-outputs)
owns the exact roster and path order. The receipt remains outside that roster;
only the two HTML entries are displayed as HTML Results.

Shared declarations do not merge validation or publication boundaries. Context
preparation still owns named paths and snapshots; publication owns staged/final
paths, input rechecks, and receipt-last order. Transaction validation owns
historical roots, producer admission, version pairs, diagnostics, and output
rechecks. The coordinator re-admits its displayed absolute paths. Retired
single-HTML paths, upstream summary TSVs, media types, and template navigation
have different purposes and retain their owners.

#### Acceptance and stopping point

Future changes must retain independent literal expectations for output order,
IDs, kinds, basenames, current/historical receipts, and error messages. Schema
and test expectations must not be derived from the production tuple they check.
Identity, runtime, originating-checkout, historical-read, refusal, and recovery
protections remain required at their existing boundaries.

[Rendered goldens](../../../tests/contract_integration/independent_contract_goldens/test_independent_contract_goldens.py)
can compare exact HTML bytes with fixed provenance inputs. Actual source commits
and covered package hashes must still reflect the producing code. Preserve
standalone `local_build` attribution; never falsify provenance to claim byte
identity across revisions. Test policy and evidence levels remain in the
[test baseline](../TEST_BASELINE.md).

### Reporting lifecycle compression

Private reporting publishers create absent outputs because that is the behavior
selected by public Run reporting. A complete bundle is revalidated and reused;
a prepared predecessor cannot authorize overwriting its files. Historical reads remain supported. The
[publication contract](../../../src/emrys/reporting/README.md#publication-and-recovery)
owns current ordering, file ownership, cleanup, and recovery behavior.

The predecessor implementation and its replacement-failure characterization
remain inspectable at `0ece377ca2b285d6ec2a46f7d2441c78f16409e1`, the head of
[PR #146](https://github.com/lab-cats/EMRYS/pull/146). The retirement intentionally
removed private overwrite, predecessor backup/restoration, and repeated private
publication. It did not authorize deletion or repair of existing residue.

The same change retired three publication operation records, two identity
operation records, `ReceiptValidationOps` and its public testing arguments,
and the `report.py` facade. Production calls now use existing owners directly;
source admission belongs to HTML context preparation. The receipt's logical
producer identifier remains `emrys.reporting.report`. Fault tests patch real
operations rather than requiring a parallel production callback API. The
captured artifact source observer and transaction recheck callbacks remain
because later publication and reuse depend on them. The later combined
index/summary operation also retires `RunSummaryBuildDeps` and the separate
summary builder and publisher; readers use admitted records and pure projections.

The surviving publication path records ownership before linking, verifies
successful links, and stops path-based cleanup when the output directory is
replaced. Current contracts, output order, Attempt lineage,
source attribution, input rechecks, independent goldens, scientific oracles,
and retained evidence remain protected. Local filesystem and signal tests do
not establish Slurm, institutional-site, production, or biological behavior.

Indexing and summary generation now share one publication owner, completion
marker, and recovery scope. The result manifest contains shared Run and publication provenance once, with
per-artifact computation and validation facts. It commits the summary and QC
TSVs without a second receipt or per-artifact record files.
HTML publication and validation-roster policy retain their separate scope. Reporting-memory policy belongs to the
[Run contract](../../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning).
Dashboard replacement and retirement remain separate decisions.

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
frozen under `DASHBOARD-RETIRE-01` until a replacement dashboard is implemented
and validated; retirement then requires its own approved scope.
