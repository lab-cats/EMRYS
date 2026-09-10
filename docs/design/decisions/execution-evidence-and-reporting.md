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
This removes repeated declarations while preserving existing Run identity,
resume, and reporting-producer rules. It does not make report-contract edits
independent of scientific Run identity. The [findings matrix](../../tasks/backlog_matrix.md)
routes any further identity or compatibility work.

An edit to the receipt-contract Python source changes new Runs' implementation
identity and can prevent an existing Run from resuming under newer code. That Run
remains immutable. A retained checkout and environment must satisfy its
original admission rules; neither resumability of every old Run nor report
regeneration by current software is guaranteed.

#### What the present identity actually protects

[`run_implementation.py`](../../../src/emrys/orchestration/run_coordinator/run_implementation.py)
hashes paths and whole file bytes in scientific and admission components.
The admission component includes the artifacts-contract directory, mixed
inspection owners, and the hasher itself. Materialization binds the digest
into the Execution Plan and Run. Resume rebuilds that candidate; Attempt and
lifecycle admission also recheck implementation and backend identities.
[`application_model.py`](../../../src/emrys/contracts/orchestration/application_model.py)
rejects a different observed implementation digest.

A filename or reporting caller does not make a whole owner presentation-only:

- The report-receipt contract validates renderer relationships, ordered output
  identities and paths, summary binding, and truncation. It is a report-specific
  leaf, but remains in the current identity component.
- The artifact API also supplies headers, safe IDs, paths, and scope grouping
  to scientific inventory admission. In particular, `run_summary_status.scope_key`
  serves scientific consumers.
- [`artifact_inventory.py`](../../../src/emrys/contracts/orchestration/artifact_inventory.py)
  combines path, uniqueness, contiguous-scope validation, and report-root admission.
- Artifact, evidence, summary, and schema owners validate provenance, status,
  strict JSON, and current records even when they do not execute science.
- Inspection owners combine immutable Run/Attempt chains, locks, task scopes,
  scientific Results, and reporting observations. Results and recovery use
  separate calculations. Excluding those whole files would drop substantive coverage.
- The reporting package, `reporting_boundary.py`, `reporting_operation.py`, and
  orchestration `projection.py` are already outside the explicit Run source
  roster. Their source, receipt, and publication checks still apply.

Under the [version policy](platform-direction.md#version-support), reading,
resuming, and reusing current reports are separate promises:

| Operation | Required behavior |
|---|---|
| Read current Run/Attempt records | Validate the original canonical records, IDs, hashes, profile, tools, and resources. This read does not itself recompute the installed scientific implementation; full inspection can report separate reporting blockers. |
| Resume a current Run | Rebuild the candidate, require identical binding bytes, and recheck implementation/backend identities. A report-contract source edit can change this comparison. |
| Resume through Slurm | The child repeats full planning and execution admission. Successful submission alone proves no compatibility. |
| Reuse current-root reports | Transaction validation attests the executing package against the originating Attempt checkout and commit. New core code can block reuse independently of the Run hash. |
| Generate missing reports | Require current authority, successful complete Results, terminal Attempt receipt v2, admissible empty output locations, and the originating Attempt's source attestation. Partial or ambiguous state is preserved. |

The bound profile determines the report root; a Run's age or schema directory
name does not. A complete bundle is not automatically reusable by a newer
checkout. The [reporting owner](../../../src/emrys/reporting/README.md) defines
current publication and re-admission behavior.

#### The alternative requires a separate compatibility decision

Separating report-contract edits from Run identity requires one coherent
compatibility design covering:

- **Source coverage.** Identify the exact excluded responsibility, initially
  the report-receipt leaf. Keep every scientific and admission dependency
  bound; do not exclude the artifacts directory or mixed inspection owners.
- **Plan identity.** Define which current code determines scientific execution.
  Since the hasher is itself hashed, removing a file or changing a digest label
  changes Run compatibility. Old-version reads are outside support.
- **Reporting provenance.** The core-renderer digest hashes `emrys.reporting`,
  not the receipt-contract leaf. A checkout commit is recorded when available;
  standalone `local_build` attribution is not an independent content digest
  for an excluded contract.
- **Reuse and generation.** Decide whether newer software may report on an
  earlier successful Attempt. Current boundaries require the originating
  checkout. Any replacement must identify the actual reporting producer while
  preserving the original scientific Attempt and predecessor evidence.

This crosses implementation hashing, application-model schemas/readers,
materialization, lifecycle, reporting source admission, and receipt provenance.
No compatibility redesign is implied by declaration consolidation. An old-hash
translation table, function-body hashing, generic registry, or automatic record
rewrite would require its own justified design and approval.

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
