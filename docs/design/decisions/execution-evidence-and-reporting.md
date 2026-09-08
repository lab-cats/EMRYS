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

Multi-file owners use declared destinations, owned locks, staging, stable-input
rechecks, validation before publication, no-clobber behavior, bounded rollback,
and a receipt or summary published last. Transaction completion says only that
the declared transaction was admitted; it does not promote scientific meaning
or unrelated evidence.

Preserve locks, backups, partials, and recovery markers whenever ownership or
cleanup cannot be proved. Characterize unsafe states before correcting them.
An observed defect is neither an approved contract nor evidence that unlike
transaction implementations should share one abstraction.

#### No-clobber rollback

Steps 07–09 follow this rule when `--no-clobber` is selected. An output path
that is already absent needs no cleanup. Remove a present output only if it
still identifies the same file as this attempt's staging entry, proven by
matching device and inode. A complete, unambiguous rollback removes owned
staging and releases the lock so an ordinary rerun can proceed. If an output's
ownership cannot be proved or removal fails, preserve the lock and remaining
files for inspection.

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

The bounded `REPORT-ROSTER-01` consolidation retains the existing implementation
identity, historical resume, and report-producer provenance rules. Retaining
those rules is within the approved consolidation; changing them requires a
separate decision. An edit to the report-contract owner changes the
implementation identity calculated for new Runs and can prevent resuming an
existing Run with that newer code.
An existing Run remains immutable; a retained matching checkout and environment
must satisfy its original admission rules. This does not guarantee
that every old Run is resumable or that current software can regenerate its
reports. The broader goal of report-only changes preserving scientific Run
identity remains open in the existing backlog row.

A compatibility/provenance redesign crosses additional immutable-record and
producer-admission boundaries. It remains separate from output-declaration
consolidation and has no qualified net-negative draft.

#### What the present identity actually protects

[`run_implementation.py`](../../../src/emrys/orchestration/run_coordinator/run_implementation.py)
hashes paths and whole file bytes in separate scientific and admission
components. `_ADMISSION_ROOTS` includes the entire artifacts-contract directory,
mixed inspection owners, and the identity implementation itself.
`materialization.build_run_candidate` binds the resulting digest into the
Execution Plan and Run. `control._plan_resume` reconstructs the candidate;
Attempt planning and lifecycle admission also recompute implementation and
backend identities. `application_model.validate_successor_run` rejects a
different observed implementation digest.

| Existing owner | Actual responsibility and consumer | Decision for this slice |
|---|---|---|
| [`report_receipt.py`](../../../src/emrys/contracts/artifacts/_artifact_contracts/report_receipt.py) | Its semantic validator owns renderer relationships, output IDs/kinds/basenames/order, summary binding, and truncation admission. Production calls arrive through the artifact API and report receipt validation. It is the narrow report-specific leaf relevant to this consolidation. | Keep it in the current identity component and use it as the declaration owner. |
| [`api.py`](../../../src/emrys/contracts/artifacts/api.py), `definitions.py`, `identity.py`, and `run_summary_status.py` in the artifacts owner | The API also supplies inventory headers, safe IDs, path validation, and scope grouping to scientific artifact-inventory admission. The filename `run_summary_status.py` does not make its `scope_key` function presentation-only. | Keep all identity coverage and scientific consumers. Add only the curated declaration export needed by the fixed-output consumers. |
| [`artifact_inventory.py`](../../../src/emrys/contracts/orchestration/artifact_inventory.py) | `_validate_rows` admits explicit paths, uniqueness, and contiguous scope groups before materialization. The same file also owns historical/current report-root interpretation. | Preserve both responsibilities and its fingerprint coverage. It is outside the consolidation edit set. |
| Artifact record, evidence, run-summary, and schema owners | Reporting uses their input, provenance, status, strict-JSON, schema, and history admission. These are substantive protections even where they do not execute a native scientific stage. | Preserve them; no directory-wide exclusion or validator retirement. |
| [`_inspection_admission.py`](../../../src/emrys/orchestration/run_coordinator/_inspection_admission.py) and `_inspection_attempts.py` | Admit Run/Attempt authority, paths, task scopes, immutable record chains, and locks. | Preserve whole-file protection. |
| [`_inspection_evidence.py`](../../../src/emrys/orchestration/run_coordinator/_inspection_evidence.py) and [`inspection.py`](../../../src/emrys/orchestration/run_coordinator/inspection.py) | Combine scientific task/Results evidence with reporting-ledger observation. Historical Attempt receipt v1 retains its original reporting relationships; current Results and recovery have separate domain calculations. | Do not move or exclude whole files to obtain a smaller fingerprint. |
| [`reporting_boundary.py`](../../../src/emrys/orchestration/run_coordinator/reporting_boundary.py), `reporting_operation.py`, orchestration `projection.py`, and the reporting package | Already outside the explicit Run implementation roster. They still perform source, receipt, and publication admission. | Preserve those checks. Only the fixed two-HTML result-location declaration in `reporting_boundary.py` belongs to this consolidation. |

Readability, resumability, and report reuse are separate promises:

| Operation | Present rule to preserve |
|---|---|
| Read recorded successor Run/Attempt authority | Validate original canonical records, IDs, hashes, profile, tools, and resources. Reading this authority does not itself recompute the installed scientific implementation. Full inspection can still report separate reporting blockers. |
| Resume a successor Run | Rebuild the Run candidate and require identical binding bytes; recheck implementation and backend identities before execution. A report-contract source edit is currently sufficient to change that comparison. |
| Resume historical `execution.v1` | Retain the separate normalized-execution reconstruction and exact byte comparison, along with its source/tool compatibility checks. Historical execution is not an alias for `run-binding.v1` plus `execution-plan.v1`. |
| Resume through Slurm | The delegated child performs full planning and the same execution admission. A successful submission is not compatibility evidence. |
| Reuse reports at the current report root | Receipt revalidation in [`transaction_validation.py`](../../../src/emrys/reporting/transaction_validation.py) attests the executing package against the originating Attempt checkout and commit. New core code can block reuse independently of Run-hash comparison. |
| Read reports through the supported legacy-root path | Re-admit recorded producer identity, canonical paths, supported summary/receipt pairing, input/output hashes and sizes, and upstream evidence. This path does not require the current renderer bytes to equal the historical producer. |
| Generate missing reports | Require successor authority, complete successful Results, a successful terminal Attempt receipt v2, admissible empty output locations, and the original Attempt's source attestation. Historical `execution.v1` generation remains refused. Partial or ambiguous report state is preserved. |

The report-root distinction is determined from the bound profile, not merely
the age of a Run or a schema directory name. In particular, a complete report
is not automatically reusable from any newer checkout.

#### The alternative requires a separate compatibility decision

If report-contract edits must preserve Run identity across software revisions,
select that as a distinct outcome. Its minimum design
must specify all of the following together:

- The exact excluded responsibility: initially the report-receipt leaf, not
  the artifacts directory or mixed inspection files. Every surviving scientific
  and admission dependency must remain bound.
- An explicit identity interpretation for new plans and exact reading of old
  plans. A new Execution-Plan version is a candidate, not an approved schema
  change. Because the hasher is itself hashed, simply subtracting one file or
  bumping an internal digest label does not make old Runs compatible.
- How the excluded contract implementation is bound as reporting provenance.
  `_run_report.context._core_renderer_sha256` hashes `emrys.reporting`; it does
  **not** cover `contracts/artifacts/_artifact_contracts/report_receipt.py`.
  A matching checkout commit is recorded where available, while the standalone
  producer permits `local_build`. That fallback cannot be treated as an independent content
  digest for the excluded contract.
- Whether newer core software may reuse or generate reports for an earlier
  successful Attempt. Both the reporting boundary and current-root transaction
  admission enforce the originating checkout today. Relaxing these checks
  requires binding the actual reporting producer while retaining the original
  scientific Attempt and all predecessor evidence.

The affected policy owners would include `run_implementation.py`,
`application_model.py` and its schema/readers, materialization/lifecycle,
reporting source admission, and receipt provenance. No such implementation or
size exception is selected here. Do not add an old-hash translation table,
AST/function-body hashing, generic registry, or automatic record rewrite to
make this small consolidation appear complete.

#### Declaration owner and consumers

The existing receipt-contract owner declares the immutable ordered
`REPORT_OUTPUTS` tuple, exported through the curated artifact API. Each row
carries the output ID, kind, and filename suffix. All fixed outputs keep the
Run ID as their basename prefix:

| Order | Output ID | Kind | Suffix |
|---|---|---|---|
| 1 | `scientific-report-html` | `scientific_html` | `scientific_report.html` |
| 2 | `evidence-report-html` | `evidence_html` | `evidence_report.html` |
| 3 | `run-summary-tsv` | `run_summary_tsv` | `run_summary.tsv` |

The report receipt itself, `RUN_ID.report_outputs.tsv`, remains outside its
own three-output roster. The first two entries alone are displayed as HTML
Results. No new carrier class, product file, output factory, or report catalog
is needed. This is an internal declaration; it creates no public CLI option
or schema generation.

| Consumer | Declaration use | Semantics that stay local |
|---|---|---|
| Receipt contract and curated API | Expected IDs, order, kinds, and basenames. | Validation order and exact error messages, including duplicate IDs/kinds/paths and renderer/summary relationships. |
| [`_run_report/context.py`](../../../src/emrys/reporting/_run_report/context.py) | Three output paths and ordered path assembly. | Explicit named context path fields, receipt/lock/retired paths, admission and snapshots. |
| [`_run_report/publication.py`](../../../src/emrys/reporting/_run_report/publication.py) | ID/kind assembly paired with staged and final paths. | Distinct HTML/TSV preparation and validation, owned state, input rechecks, and receipt-last publication. |
| [`transaction_validation.py`](../../../src/emrys/reporting/transaction_validation.py) | Current receipt reconstruction, historical canonical output paths, and two-HTML location IDs. | Historical/current producer rules, exact diagnostics, root interpretation, schema-version pairing, and output rechecks. |
| [`reporting_boundary.py`](../../../src/emrys/orchestration/run_coordinator/reporting_boundary.py) | Expected two-HTML result-location IDs. | Re-admission of absolute path objects and ledger/publication authority. |

`ReportContext` is frozen and `prepare_context` is its only repository
constructor. Its existing `stable_paths` tuple is scientific HTML, evidence
HTML, summary TSV, then receipt; the report tests independently compare that
order with the named path fields. Consumers reuse its first three path objects
when assembling output rows. Supported run-summary v2/report-receipt v4 and
v3/v5 pairs, and refusal of unsupported historical versions, remain unchanged.
The retired single-HTML paths, upstream artifact-summary TSV, media-type rules,
and template navigation have distinct responsibilities and retain their owners.
Schema literals and independent test expectations remain protections; they are
not derived from the production tuple.

#### Acceptance and stopping point

- Preserve the existing positive and negative identity expectations in
  [`test_materialization.py`](../../../tests/orchestration/run_coordinator/test_materialization.py)
  and observed-digest rejection in the application-model contract tests, along
  with runtime-identity checks. The selected policy must not gain a test that
  simply declares the report-contract source irrelevant to identity.
- Compare current and historical receipts, exact output order/kinds/basenames,
  materialized paths, both displayed HTML locations, and malformed-input
  diagnostics using literal expectations independent of the production tuple
  in the [artifact-contract tests](../../../tests/contracts/artifacts/test_artifact_schema_contracts.py)
  and [report tests](../../../tests/reporting/test_report.py).
- Retain reporting-operation/boundary tests for historical reuse, refused
  generation, and empty-state publication, plus transaction-validation tests
  for originating checkout admission, changed receipts/outputs, predecessor
  evidence, and supported legacy-root reads.
- Keep [independent rendered goldens](../../../tests/contract_integration/independent_contract_goldens/test_independent_contract_goldens.py)
  and publication fault cases. Exact HTML
  bytes can be compared with fixed provenance inputs; source commits and
  renderer-package hashes must reflect the actual checkout and covered package
  bytes, with existing standalone `local_build` attribution preserved. Do not
  freeze or falsify provenance to claim cross-revision byte equality.
- Run focused owner checks locally and applicable long checks in hosted CI.
  Direct execution, Slurm planning, hosted Slurm, institutional-site execution,
  and scientific validation remain separate claims.

The implementation ends with one caller-complete fixed-output consolidation and
its required checks. Transaction-layout consolidation, reporting-memory
removal, check-ID corrections, and independent-producer reporting remain
outside this slice. `REPORT-ROSTER-01` stays open for its remaining outcomes.

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
