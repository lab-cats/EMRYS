# Compression campaign intake

Status: **temporary discovery record**

Started: **2026-09-02**

This file preserves findings discovered while reviewing the cumulative
architecture change. It is not a second backlog, a design specification, or
authority to implement a proposed change. The
[`COMPRESS-01`](backlog_matrix.md#repository-maintenance) row owns the intake;
the backlog remains the only task authority.

The user has completed the repository review. Examples below record recurring
patterns; repairing one example does not resolve its whole family. Remaining
work is to select findings, define finite outcomes, transfer accepted work to
the backlog, and retire this temporary record after verifying the transfer.

The [continued code-compression audit](#continued-code-compression-audit)
records the later owner reviews, proposed packages, unresolved decisions,
rejected simplifications, and required evidence. Its package headings are
discussion labels, not additional backlog IDs or implementation approval.

## Campaign rules

- Prefer existing language, library, packaging, validation, and workflow tools
  before adding bespoke machinery.
- Each implementation slice must remove a meaningful amount of maintained
  product code and must not grow the product-file count unless an explicit,
  quantified exception is approved.
- Deleting tests, documentation, or evidence does not offset product growth.
- Preserve scientific meaning, immutable Run identity, provenance, publication,
  recovery, concurrency, and supported public behavior. Delete checks for
  impossible states only after their producers and mutation paths are audited.
- Exact retained evidence may be deleted only with separate user approval.
- Rename or extract code only as part of a caller-complete simplification. Do
  not perform repository-wide cosmetic churn or replace one large abstraction
  with many one-caller wrappers.
- Documentation and code must explain their purpose to the intended reader in
  common language without requiring campaign history.

## Current finding families

| Family | Representative observations | Present disposition |
|---|---|---|
| CI control and latency | Manual dispatch independently selects the ordinary and long CI groups. Reviewed estimates in the [duration baseline](../../tests/baselines/python_test_durations.json) now place the two long end-to-end tests on separate shards. | `CI-01` owns the remaining measured critical path and duplicated setup or work. Estimated balance is not measured wall-clock improvement. Preserve complete, disjoint test selection and coverage checks; scheduling estimates are not a reason to delete slow production-path tests. Do not propose manual lane selection again. |
| Reader-oriented documentation | Much of the documentation assumes complete EMRYS context or uses internal vocabulary before explaining purpose. | Record as a repository-wide future pass. Individual wording edits do not close it. |
| Documentation ownership | `configs/README.md` contains setup/runtime procedure; Architecture contains validation-status prose; Runbook contains developer CI/task-selection material; Troubleshooting contains scientific interpretation; logging and Run-coordinator contracts may mix context with exact owner behavior. | Reconcile these examples with current documentation before selecting changes. Audit every surviving document, contract, and directory guide as a future family. |
| Examples and configuration guidance | Execution-profile examples do not explain fields or top-level resource groups; `qos` is unexplained. | Audit all human-authored examples for self-explanation. Retain the standard Slurm `qos` spelling and explain Quality of Service rather than add a cosmetic schema migration. |
| Code comprehension | Names such as `executable`, `_paths`, `build_context`, and `Publication` lack useful context; fixed-position tuples and opaque mappings obscure meaning; large modules have unhelpful opening docstrings. | Future repository-wide owner audit. The Step 09 threshold tuple and `application_model.py`/`artifact_inventory.py` docstrings are examples, not the scope boundary. |
| Module size and responsibility | Processing producers and application owners may combine admission, paths, locking, execution, validation, rollback, publication, and evidence in one file. | Measure responsibility and duplication across the full owner family before splitting or sharing anything. Prefer deletion and a few cohesive owners over micro-modules. |
| Repeated protection and evidence logic | Locking, validation, evidence, publication, and defensive negative cases appear repeatedly across owners. | Compare threat models and semantics first. Share only truly identical mechanics; delete redundant or impossible-state protection; preserve distinct trust/recovery boundaries. |
| Coverage and branch surface | Run-coordinator control-plane and runtime-admission branch ratios are low. | Treat this first as a branch/complexity audit, not an instruction to add tests. Delete low-value branches, then add focused protection only for retained high-risk behavior. |
| Schema and compatibility surface | Many schema generations, confusing directory/version labels, historical artifact formats, repeated shape checks, and alternative configuration spellings remain. | Inventory every reader, writer, registry, persisted record, and compatibility requirement. Do not retire “v3” as a class: run-summary v3 is active while report-receipt v3 appears historical. Evidence deletion remains separately approval-gated. |
| Configuration normalization | Paired-CMH accepts or derives overlapping forms such as `target_change` and `rna_ref`/`rna_alt`; generated records may be revalidated after construction. | Audit external-provider and public-input boundaries before deleting normalization. Remove alternate forms and self-validation only when no supported reader requires them. |
| Scripts and historical stage language | Numeric step names, standalone owner commands, shell owners, inline/generated programs, and a site-specific Step 05 validation script remain. | Existing `OPS-03` owns caller-complete retain/migrate/retire decisions. Give semantic names only to surviving programs during real migration. |
| Contracts, READMEs, and docstrings | Some READMEs and contracts duplicate one another; others are so terse that their purpose is unclear. | Exact cross-language/public behavior remains in contracts. Implementation purpose belongs in concise docstrings. Remove duplication owner by owner rather than copying contracts into code. |
| Artifact and source topology | Artifact/schema guides do not orient a new reader; `SOURCE_TOPOLOGY.md` and its bespoke import-edge tooling duplicate detailed path rosters. | Preserve authored dependency permissions; observed imports cannot authorize themselves. Fixed reporting permissions now use the [existing exact-exception mechanism](../../tests/tools/source_dependencies.py); the separate bypass is retired and stale permissions fail. A maintained-tool replacement remains separate and needs full boundary parity. |
| Documentation gate | The [documentation gate](../../scripts/documentation/validate_structure.py) retains current owner, local-link, anchor, and Mermaid checks; completed integration bans have been retired. | Keep these checks tied to current contracts. They do not claim to detect every possible duplicate documentation authority. |
| Analysis extension guidance | Multiple named Analyses are supported, but there is no practical walk-through for adding an external computation provider and bespoke reporter. | Retain as a future documentation deliverable based on one minimal working provider, without creating a generic workflow or report DSL. |
| Golden-path workspace behavior | The operator should not manually create required Project directories and should not need internal manifests or execution machinery. | Already a permanent Project/setup requirement. Do not add checkout-level `data/raw` or `data/full`; scientific inputs remain referenced, and filenames cannot safely infer conditions or replicates. |

## Discovery findings for selection

The following source survey used master
`372844269131568af815e117bd4508e4e200561a`. It inventoried 593 tracked files
and sampled production owners, callers, contracts, tests, configuration, and
documentation; it was not an exhaustive verification of every file. No
reproductions, benchmarks, or scientific runs were performed. Existing tests
that describe known behavior were read, not rerun. Consequences predicted
from source still require verification.

Numbers retain the discussion labels only; they are not backlog IDs, priority
scores, or implementation approval. The matrix owns accepted work. Findings
below are marked addressed, awaiting selection, or covered by existing work;
references to existing rows identify coverage rather than duplicate it.

| Discussion | Observed issue and possible outcome | Selection or existing coverage |
|---|---|---|
| 1. Validation-report publication | [Publication](../../src/emrys/libraries/validation/publication.py) can remove a file another process created at the output path during rollback, and releases the lock when restoring old outputs fails. Existing [tests](../../tests/libraries/test_validation_report.py) describe both cases. Define recovery for this owner so cleanup removes only files it owns and preserves unresolved state. | Proposed recovery work; not covered by the current `RECOVERY-01` implementation. |
| 2. Storage inventory replacement | [Inventory publication](../../src/emrys/evidence/storage_inventory/_storage_publication.py) moves old outputs to backups before entering its rollback handler, then releases the lock even if restoration fails. Audit and repair the entire replacement transaction. | Proposed recovery work. Storage inventory is separate from storage qualification, which PR #115 repairs. |
| 3. Reference provenance replacement | [Reference reconciliation](../../src/emrys/evidence/reference_provenance/reconciler.py) also moves old outputs before entering its rollback handler and releases the lock after failed restoration. Define and preserve recoverable state across these failures. | Proposed recovery work. Similar spelling does not establish equivalent publication semantics. |
| 4. Runtime report publication | [Runtime inspection](../../src/emrys/evidence/runtime_availability/inspector.py) can leave its lock descriptor open when lock writing or syncing fails, release the lock after failed restoration, or report success after lock removal fails. Existing [tests](../../tests/evidence/runtime_availability/test_runtime_availability.py) describe these behaviors. | Proposed recovery work within the runtime owner; separate from model consolidation. |
| 5. Input snapshots | [Validation inputs](../../src/emrys/libraries/validation/inputs.py) use device, inode, size, and modification time to recognize an unchanged input. An existing [test](../../tests/libraries/test_validation_report.py) changes bytes while preserving size and restoring modification time. Compare this with the existing descriptor-based checks that also retain change time, and consolidate only after matching the required stability guarantee across callers. | A follow-up caller audit found different active guarantees: the simple snapshot omits change time and mode, while descriptor-bound reads retain them. Consolidation needs an explicit stability decision; do not replace it with another wrapper or claim that metadata proves content identity. |
| 6. Doctor storage repair | [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) admits qualification for the selected direct or Slurm profile but constructs a direct repair when storage is unready. Source inspection predicts that this repair cannot satisfy a Slurm Project's qualification requirement. | Proposed bounded defect investigation. Local plan checks and institutional-site execution remain distinct evidence. |
| 7. Empty FASTA header | [Contig parsing](../../src/emrys/libraries/references/contigs.py) indexes the first header token before checking that it exists; an empty header produces `IndexError`, as the existing [test](../../tests/libraries/test_reference_contigs.py) expects. Return the parser's normal input error and review affected callers. | Proposed bounded input-validation correction. |
| 8. Artifact CLI version admission | The [artifact schema API](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py) uses default schema versions when its unversioned validation helper is called. A follow-up local reproduction published and readmitted current module reports through the existing production path: their v3 summary and v5 receipt decoded to JSON passed explicit schemas and semantic validation, but `emrys validate artifact-contracts` rejected both against older defaults. | Confirmed local defect; artifact CLI admission remains a separate, unselected change. Orchestration admission already uses its [shared schema validator](../../src/emrys/contracts/orchestration/api.py). Preserve supported historical versions when selecting the artifact correction. |
| 9. Snakemake content identity | [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) obtains the Snakemake version through Python and records the Python executable as its file binding. [Runtime admission](../../src/emrys/orchestration/run_coordinator/lifecycle.py) requires that same executable identity. Determine whether Snakemake package contents must also be bound, and whether another existing identity already covers them. | Undecided guarantee; no demonstrated package-change reproduction or complete identity audit. `RUNTIME-CLOSURE-01` concerns the separate R closure. |
| 10. Duplicate runtime definitions | Runtime inspection now uses one immutable check definition and one observation definition throughout loading, probing, rendering, and public inspection. Resolved observation locations remain path objects internally. | Addressed; the [runtime owner](../../src/emrys/evidence/runtime_availability/README.md) documents the surviving model. Public imports, report bytes, validation, and publication behavior are preserved. |
| 11. Whole reference reads | [Reference inspection](../../src/emrys/evidence/reference_provenance/_reference_contigs.py) reads whole FASTA and STAR Genome files to calculate hashes and lengths, and builds whole-text input for parsing. Existing streaming hash and iterable parsing mechanisms may remove these allocations. Preserve the second observation where it detects changes during inspection. | Existing stable streaming hashing can remove the hash-only allocation, but yields little maintained-code reduction. Parser streaming also needs to preserve decoding, newline, and error order. Keep this as a separate memory-reduction candidate; no timing or peak-memory measurements were taken. |
| 12. Repeated FASTQ scans | The [FASTQ check](../../src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh) counts each complete file and then scans it again for each selected read ID: the default prefix of 20 requires 21 passes per mate. A single pass could preserve complete record counts, decompression failures, and the explicitly limited prefix comparison. | Retain this independently useful read-only diagnostic under `OPS-03`. A single-pass `awk` draft changed embedded-zero-byte header handling in a local comparison, and no input-encoding rule excludes those bytes. Defer that implementation until the behavior is decided; no benchmark was run. |
| 13. Repeated processing declarations | [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) repeats task commands, inputs, outputs, and validation details in command and dispatch construction. Investigate deriving equivalent declarations from existing admitted facts. | The six sample-scoped shell owners (Steps 01, 02, 02b, 03, 04, and 05) now share command framing inside the existing materializer, retaining explicit ordered arguments and inputs. Passing already admitted validation paths and scope IDs could remove about 18 more lines, but is too small for a separate substantial slice. Module provenance roles, reused predecessor scopes, and positional Step 00c outputs remain distinct; do not combine them into a new registry. |
| 14. Source-topology rosters | [Dependency checks](../../tests/tools/source_dependencies.py), tests, and [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) maintain overlapping path and composition rosters. Determine which can be derived or replaced by a maintained boundary-checking tool while preserving real dependency rules. | The 12 fixed reporting permissions now use the [existing exact-exception mechanism](../../tests/tools/source_dependencies.py); the separate bypass is retired, and stale reporting permissions fail. Imports are already discovered from source; CLI targets and allowed exceptions are policy. A larger maintained-tool migration remains unqualified for dynamic imports, private-module rules, repository admission, and logging consumers. |
| 15. Historical output replacement | The Run coordinator selects no-clobber publication, while standalone owners retain historical replacement routes with different recovery behavior; the [Step 08 contract](../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md) is one example. Audit supported callers and whether the orchestrated path fully replaces each route. | Existing `OPS-03`. Retiring public behavior requires a decision; absence of external use has not been proved. |
| 16. Parallel configuration normalization | [Project normalization](../../src/emrys/orchestration/run_coordinator/normalization.py) and [application modeling](../../src/emrys/contracts/orchestration/application_model.py) retain overlapping flat paired-CMH configuration and module-policy forms. Trace current and historical inputs before proposing one surviving representation. | Revision construction and partition projection already share their existing owner. Flat and module forms bind different identity and admission semantics; no preserving helper retirement was found. Public migration and any broader paired-replicate validation consolidation remain undecided. |
| 17. Repeated reporting declarations | Reporting arguments, outputs, and kinds recur across owners. Current reporting uses direct producer APIs and one ordered execution loop; its materialization is already delegated outside the explicit scientific implementation roster. A follow-up caller audit found that `reporting_memory_mb` is validated, persisted, hashed, and overlaid on resume, but no scheduler or reporting execution consumes it for memory allocation. | Report preparation retains consumed values: unused presentation and summary-context fields are retired, and scientific-context bound inputs reuse existing immutable file snapshots. Ordered inputs, source identities, actual row limits, prepared bytes, and the FASTA-only identity recheck remain. `REPORT-ROSTER-01` owns the remaining work. Retiring the active memory control requires a decision on accepted YAML/CLI inputs and exact historical policy admission. Its value is excluded from computational resource identity, but changing its schema/admission implementation can still change new Run identities. Preserve immutable Runs, historical reads, report regeneration, and module-specific reporting. |
| 18. Report check identities | Existing [artifact-adapter tests](../../tests/reporting/test_artifact_adapters.py) show that reordered or different unique check IDs can still be treated as complete. Completion should follow the admitted roster's actual identity and order when that roster is defined. | Existing `REPORT-ROSTER-01`. No neutral contract owner currently publishes a check-ID roster. Step 09 validation checks membership while reporting also checks order; importing its private validator or tightening generic artifact admission is not a preserving consolidation. External-module rosters need a contract decision; preserve independent expected-result tests. |
| 19. Eight-selection limit | The [scientific-context contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/CONTRACT.md) binds an eight-selection limit across generation, receipts, and validation, with reporting limits as well. Supporting nine panels requires reviewing the entire path, including labels and rendered output. | Existing `REPORT-04`. Preserve full underlying data and historical records; no rendered-output review was performed in this survey. |
| 20. Historical documentation exclusions | The [documentation gate](../../scripts/documentation/validate_structure.py) previously enumerated retired paths alongside current structural checks. Those bans covered completed integration work. | Addressed: historical integration bans and their dedicated tests are retired; current ownership, links, anchors, and diagram checks remain. |

### Follow-up findings

The following bounded follow-up audits and local reproductions supplement the
original source-only survey. They do not establish hosted, site, production, or scientific evidence.

- **Timestamp checking depends on an optional checker.** With the current
  declared dependencies and the available local Python environment, both
  historical v1 and current v2 Attempt receipts accept
  `finished_at: "not-a-time"` when the JSON Schema date-time checker is absent.
  This reproduced before and after orchestration-validator consolidation.
  The schema declares `format: date-time`, but the project declares base
  `jsonschema` and its lock has no RFC 3339 checker package. Audit timestamp
  admission across callers and select the dependency/validation correction
  separately; no dependency change is authorized by this finding.
- **A single-pass FASTQ draft changed accepted input.** For paired headers
  `@re<NUL>ad/1` and `@read/2`, where `<NUL>` denotes a zero byte, the existing
  helper succeeds locally. The proposed system-`awk` scan truncated the first
  ID to `re` and failed the pair. The draft was not published. Preserving byte
  handling and shell diagnostics needs further design before this optimization.
- **Runtime lock acquisition is a small defect fix, not substantial compression.**
  Standard-library descriptor ownership can close the write/fsync leak, but
  shortening the current descriptor lifetime changes close-failure timing.
  Preserving that timing requires additional handling. Keep the bounded leak
  repair separate from the other unresolved runtime publication failures.
- **Immutable configuration and record projection have different purposes.**
  Module planning has one recursive freeze helper. It supplies read-only
  mappings and tuples after strict JSON admission; the existing record decoder
  instead returns fresh mutable dictionaries and lists. Neither replaces the
  other without changing the provider boundary. Canonical record storage is
  already shared by the existing application-model owner.
- **TSV readers have different admission contracts.** [Run-summary parsing](../../src/emrys/reporting/_run_summary/inputs.py)
  uses strict quoting while [artifact-index parsing](../../src/emrys/reporting/_artifact_index/records.py)
  uses lax quoting; both retain `DictReader` row shapes. The [shared strict parser](../../src/emrys/libraries/validation/tsv.py)
  rejects ragged rows and defers header and row-shape errors until lexing ends.
  Blank rows, malformed quotes, duplicate or empty headers, and diagnostics
  therefore differ. The [all-pass reader](../../src/emrys/orchestration/run_coordinator/all_pass.py)
  also accepts its own unique check roster and requires every status to pass;
  report validation checks an external roster and accepts pass/fail. Reuse
  would change behavior or need a new configurable adapter; defer consolidation.
- **Resource normalization preserves historical identity.** [Resource policy](../../src/emrys/orchestration/run_coordinator/resource_policy.py)
  distinguishes partial fragments, complete symbolic policies, persisted
  effective records, and allocation resolution. Historical records retain
  fixed numeric memory; symbolic records re-resolve allocation/workflow values.
  Historical omissions of thread settings for Steps 09 and 10 default to one
  without adding fields, and integer conversion canonicalizes accepted integral
  numbers. Existing owners already share admission and record mechanics;
  no substantial preserving retirement was qualified.
- **Limitation-ID collision handling has no current collision input.** The
  [summary projection](../../src/emrys/reporting/_run_summary/projection.py)
  emits zero or one limitation with a fixed base ID, and its ID allocator starts
  with an empty set. Full retirement would remove about 14 lines; defer it as
  too small for a standalone substantial slice.
- **R command setup already shares argument parsing.** The remaining owner
  wrappers differ in script-path handling, package admission, diagnostics, and
  error precedence. A common bootstrap would add a new abstraction; inlining
  the argument wrappers alone saves too little for a substantial slice.
- **The dashboard remains frozen.** Its two renderers repeat roughly 35–40
  lines of setup and layout framing, but the owner's documented frozen status
  excludes incidental renderer cleanup. `DASHBOARD-RETIRE-01` owns the
  [whole-owner retirement proposal](#dashboard-retirement-prerequisites);
  documenting that proposal does not select implementation.

### Reconciliation with other work

- Old labels such as `RA-002` and `TG-02` in tests are historical references,
  not revived backlog items.
- [PR #115](https://github.com/lab-cats/EMRYS/pull/115) repairs Steps 07–09
  rollback and storage-qualification publication. It does not close the other
  publication findings above. A common rollback rule does not by itself justify
  a shared publication implementation.
- [PR #44](https://github.com/lab-cats/EMRYS/pull/44) covers Step 05 BAM I/O
  work, and [PR #45](https://github.com/lab-cats/EMRYS/pull/45) covers Step 08
  VCF performance work. Check their current state and exact overlap before
  proposing another performance slice.
- `SITE-PARITY-01` already owns practical site setup, storage semantics, and
  the complete operator walkthrough. `CI-01` owns remaining CI latency.
- Scientific review and independent numerical validation remain separate
  backlog outcomes. Similar validation code alone is not evidence that an
  independent scientific oracle can be deleted.

## Quantified deferred findings

These survey-time measurements define future audit boundaries, not a live
source inventory. File length alone is not a defect or authority to split a
cohesive owner.

| Finding | Evidence | Disposition at intake exit |
|---|---|---|
| Large-file surface | 101 tracked files exceed 500 lines: 42 product, 52 test, and 7 other files. Of the 37 over 1,000 lines, 15 are hand-maintained product files, 17 are tests, and 5 are generated lock, CI, or third-party bootstrap files. | Under `COMPRESS-01`, rank owners by duplicated responsibility and removable behavior, not line count. Transfer only finite, net-negative owner changes. |
| Run-coordinator concentration | `run_coordinator` contains about 20,225 product lines and 20,824 test lines. `task.py`, `lifecycle.py`, `materialization.py`, `dashboard.py`, `control.py`, `doctor.py`, `onboarding.py`, and `reporting_boundary.py` each exceed 1,000 product lines. `materialization.py` devotes about 1,086 lines to repeated task command and dispatch declarations; its main test file is about 4,959 lines. | Investigate deriving repeated processing-owner plans from existing admitted facts and removing duplicate declarations and low-value defensive cases while preserving exact arguments, ordering, identity, reuse, recovery, and fault behavior. Select a finite outcome before committing to a shared representation; do not mechanically split files or add one-caller wrappers. `DASHBOARD-RETIRE-01` remains separate. |
| Generated dependency lock | `pixi.lock` is about 3,881 lines/140 KB and binds the managed Linux native/R environment used by Doctor and CI. | Retain it as generated reproducibility input; it is not maintained product-code bloat. |
| Repeated constants | Persisted filenames such as `run.json`, `normalized.json`, and `attempt.json` are repeated contract vocabulary, while the three reporting kinds recur across five owners. Small path/publication helpers have similar spelling but different trust and error semantics. | Do not add constants or helpers merely to replace strings. `REPORT-ROSTER-01` owns derivation of reporting declarations; consolidate other values only when one semantic authority deletes validation or branches. |
| Schema layout | The 27 JSON schemas occupy about 5,353 lines across artifact `v1`-`v5` and orchestration `v1`-`v3`, but those directories are family-specific physical revisions rather than five whole-system generations. Active schemas intentionally reuse definitions across directories. | Audit current and historical readers, then compare the present version directories with a flatter resource layout; pre-release paths are not protected merely because they exist. Prefer whichever model reduces cognitive and maintenance surface while preserving required identities and historical reads. Orchestration admission already uses its [shared schema validator](../../src/emrys/contracts/orchestration/api.py); artifact admission remains separately unselected. Consider a finite caller-complete retirement audit for apparently historical resources; do not bulk-renumber or delete retained evidence without approval. |
| Numeric stage and resource identities | Fourteen historical stage IDs and related rosters appear in resource policy, profile schema, and the Snakefile; Analysis admission currently permits one Step `09` and optional Step `10`. Some historical profiles intentionally omit newer task IDs. | Propose a finite semantic task/resource-key migration only when module extension needs it: derive current rosters from admitted task descriptors, preserve exact historical profile reads, and remove duplicated stage lists. `QUAL-04` and `PROFILE-CONTRACT-01` own narrower existing derivations; avoid a cosmetic global rename. |

## Continued code-compression audit

### Source, authority, and evidence boundary

This continuation reviewed source at
`d64baed27a7315aa585dd336dac43c177b837e7e`, the cumulative implementation
through [PR #137](https://github.com/lab-cats/EMRYS/pull/137), on
2026-09-07. The checkout was clean before this documentation change. Remote
master was separately verified as
`fdf76760311e6c8076320a289ef3956d754c190d`; these findings describe the
audited cumulative source, not an assertion that its open PRs are merged.
Reconcile changed owners with the selected source revision before implementation.

The review traced producers, callers, admission, persistence, contracts,
configuration, tests, and adjacent owners. It did not run new product tests,
fault injections, benchmarks, scientific computations, or cluster work.
Previously reproduced findings above retain their stated evidence level;
reading an existing test does not rerun it. In particular, the publication
handoff finding below is a source-derived counterexample awaiting reproduction.
Prior hosted CI does not establish that a newly identified failure case passes.

Classify behavior within each selected slice before changing structure:

| Classification | Meaning in this continuation |
|---|---|
| Preserved | Output, admission, ordering, identity, recovery, and public behavior must remain equivalent. A preserving proposal still needs a complete draft and validation. |
| Defective | A specific existing behavior is characterized or predicted to violate its intended contract. State which evidence supports that conclusion and obtain the required correction decision. |
| Undecided | Supported inputs, execution modes, historical treatment, or protection boundaries need an explicit decision. A code-size estimate cannot settle that decision. |
| Environment-deferred | Institutional storage, Slurm, production use, scientific review, and biological validity need their own environment and authority. Local or hosted fixtures cannot substitute for them. |

All size figures below refer to the audited revision. A counted block is a
review surface, not a deletion budget. A provisional reduction excludes
unwritten compatibility or recovery work until a caller-complete draft
establishes the net result. Product, tests/protections, documentation,
configuration, tooling, and retained evidence must be accounted separately.
This documentation request selects no new backlog item and grants no product,
public-policy, dependency, evidence-deletion, or cluster authority.

### Recommended continuation and existing ownership

The strongest next primary objective is completing reporting ownership and
declaration consolidation. The next larger retirement family is the older
stage-publication modes. Small construction cleanups remain bounded options;
they do not establish that the larger campaign is finished.

| Proposed order | Finite outcome | Existing coverage and next gate |
|---|---|---|
| Reporting ownership | Decide the fixed-output consolidation policy, then consolidate its equivalent declarations. | `REPORT-ROSTER-01`; the [decision proposal](../design/decisions/execution-evidence-and-reporting.md#proposed-fixed-report-output-consolidation) is ready for review. Broader identity and transaction-layout work remain separate. |
| Ineffective report resource control | Remove active reporting-memory configuration and transport while retaining exact historical policy admission. | `REPORT-ROSTER-01`; select new-input and persisted-policy behavior. |
| Stage publication | Qualify surviving publication, then retire replacement/direct-write modes one owner at a time. | `OPS-03`; reproduce the handoff finding and approve the public policy. |
| Processing declarations | Find one caller-complete removal using existing admitted task/output facts, or retain the mechanism with evidence. | `COMPRESS-01` discovery, with reporting adapter work under `REPORT-ROSTER-01`; no general registry is preselected. |
| Dashboard | Retire the frozen display after preserving agreed scheduler and safe-log capabilities. | `DASHBOARD-RETIRE-01`; supported replacement surface remains undecided. |
| Compatibility | Select exact schema, configuration, or TSV changes whose full migration is worthwhile. | Existing `PROFILE-CONTRACT-01` where applicable; other findings remain unselected. |

This is a recommendation for selecting bounded work, not a dependency graph
or a second status table. The [backlog](backlog_matrix.md) retains sole
authority for accepted outcomes, status, scores, and acceptance.

### Reporting source-identity prerequisite

The approved first decision package now lives in the
[fixed report-output proposal](../design/decisions/execution-evidence-and-reporting.md#proposed-fixed-report-output-consolidation).
It contains the exact ownership map, current/historical read and resume rules,
report-source restrictions, alternatives, and surviving defenses. The proposed
bounded choice preserves current Run identity and reporting-producer rules for
the output consolidation; it does not close the broader identity goal or
approve a different reporting producer. That specific policy still requires
approval before product changes.

### One fixed HTML output declaration

The same [decision proposal](../design/decisions/execution-evidence-and-reporting.md#complete-consolidation-after-the-recommended-policy-is-approved)
owns the complete receipt-contract/API/caller edit set, three-output versus
two-HTML distinction, historical version pairs, independent tests, and stopping
conditions. The original 25–50-line estimate is refined to approximately
30–35 net product lines using the existing frozen context's path order; this
is an unexecuted source sketch, not a deletion commitment. No new product file,
wrapper, catalog, schema, or identity-translation mechanism is selected.

### One three-transaction reporting layout

**Observed owners.** Transaction kinds, predecessor order, receipt locations,
and shared paths recur in
[`reporting_operation.py`](../../src/emrys/orchestration/run_coordinator/reporting_operation.py),
`reporting_boundary.py`, `transaction_validation.py`, and inspection.
The inspection consumers include
[`inspection.py`](../../src/emrys/orchestration/run_coordinator/inspection.py)
and
[`_inspection_evidence.py`](../../src/emrys/orchestration/run_coordinator/_inspection_evidence.py).
The ordered producer execution loop is already consolidated; do not count
that completed work again. The historical/current report-root distinction
already has an owner in
[`artifact_inventory.py`](../../src/emrys/contracts/orchestration/artifact_inventory.py).

**Proposed outcome.** Derive the fixed artifact-index → run-summary → HTML
layout from one existing contract owner and remove the equivalent local
declarations. Keep producer-specific preparation with its production owner.
This does not select a new transaction kind, extension protocol, generic
pipeline description, or parallel reporting registry.

**Preserved behavior and proof.** Compare prepared arguments and bytes,
receipt/input/output paths, ledger order and timing, predecessor selection,
processing-source rechecks, independent regeneration, and exact failure
stopping points. Preserve historical root interpretation. Use
[reporting-operation tests](../../tests/orchestration/run_coordinator/test_reporting_operation.py),
reporting-boundary tests, transaction-validation tests, and
[ledger contract tests](../../tests/contracts/orchestration/test_reporting_ledger_contracts.py).

**Economics and gate.** No defensible net estimate is available yet.
This is outside the first fixed-output slice. Qualify a complete negative
draft and its shared-owner identity policy separately. Abandon a proposed
shared representation if equivalent declarations do not retire or it creates
an inspection/reporting dependency cycle.

### Retire active reporting-memory control

**Observed.** `reporting_memory_mb` is admitted, transported, persisted,
hashed, capped during resource resolution, and overlaid during resume. No
scheduler or reporting execution consumes it to allocate reporting memory.
The audit found 35 matching source lines across seven files; that measures
spread, not the number of removable lines.

The affected vertical includes
[`resource_policy.py`](../../src/emrys/orchestration/run_coordinator/resource_policy.py),
[`execution_profile.py`](../../src/emrys/orchestration/run_coordinator/execution_profile.py),
[`control.py`](../../src/emrys/orchestration/run_coordinator/control.py),
[`application_model.py`](../../src/emrys/contracts/orchestration/application_model.py),
the
[resource schema](../../src/emrys/contracts/schemas/orchestration/v3/resource_config.schema.json),
the packaged
[default execution profile](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml),
and the
[CSU profile](../../configs/execution_profile.csu_viking_ev_pum1.yaml).
The frozen dashboard's historical display belongs to its own retirement.

**Proposed outcome.** Remove the active YAML/default field, CLI option,
override carriers, symbolic/effective fields, resolution checks, and resume
overlay code together. Preserve genuine computational resource declarations.
The value's exclusion from computational resource identity does not make
editing its admission implementation identity-neutral.

**Decisions.** Choose rejection or an explicit migration for new YAML/CLI
uses, including its diagnostics, the policy representation emitted for new
records, and exact historical policy reading and resume. Do not silently
ignore an ineffective user control, rewrite old
policy bytes, or weaken their original hash checks. A compatibility design
that costs more than the active removal does not satisfy compression.

**Proof.** Exercise the selected current-configuration and CLI behavior, historical
symbolic and effective records, unchanged computational policy, resume with
and without explicit resource overrides, and report regeneration. The
[resource-policy](../../tests/orchestration/run_coordinator/test_resource_policy.py),
[execution-profile](../../tests/orchestration/run_coordinator/test_execution_profile.py),
application-model, materialization, control, and public CLI tests must agree.
The net reduction remains unqualified until historical behavior is designed.

### Validation check identities and completeness

**Observed.**
[`_artifact_index/inspection.py`](../../src/emrys/reporting/_artifact_index/inspection.py)
checks row shape, safe and unique check IDs, statuses, and count.
[Artifact-adapter tests](../../tests/reporting/test_artifact_adapters.py)
characterize different or reordered unique IDs still being considered
complete. Count and uniqueness do not establish the intended check roster.
The public `AnalysisArtifactV1` declaration has headers/counts but no
declared check-ID roster. Some scientific validators require membership;
reporting may also depend on order.

**Proposed outcome.** Start with one owner whose neutral scientific contract
can own the agreed roster. Migrate that validator, artifact declaration,
and report admission together, removing repeated declarations and superseded
checks. Keep independent expected-result tests.

**Decisions and proof.** Approve ordered versus unordered completeness,
historical treatment, and external-provider obligations. Characterize
missing, extra, wrong, reordered, and duplicate IDs independently of status
and count. Preserve valid output bytes and allowed pass/fail evidence.
Do not import a private validator into reporting or silently tighten every
generic artifact. This is a correctness/interface proposal, not a preserving
helper extraction; size is unknown and any growth requires its own exception.

### Processing-output declarations and materialization

**Reporting adapter finding.**
[`_artifact_index/registry.py`](../../src/emrys/reporting/_artifact_index/registry.py)
has a roughly 175-line `build_adapter_registry`, including processing
declarations, local assembly, and the existing module-adapter call.
The `_add_analysis_adapters` path already
derives module adapters. Current processing profile templates lack some
adapter semantics, so their existing facts are not a complete replacement.

An implementation proposal must identify the rightful existing home for
output metadata across
[`analyses/__init__.py`](../../src/emrys/analyses/__init__.py),
artifact inventory, the
[authored profile](../../workflow/contracts/local_cmh_v2.json), its
[closed schema](../../src/emrys/contracts/schemas/orchestration/v2/profile.schema.json),
profile admission, and reporting. Derive kinds, scope,
paths, and completeness only where semantics are equivalent. Retain native
format readers, independent scientific reconciliation, historical profiles,
and bespoke module output interpretation. The 175-line block is a target
surface, not promised savings. Stop if a new table must coexist indefinitely
with the old one or the migration grows maintained product code.

**Materialization finding.**
[`materialization.py`](../../src/emrys/orchestration/run_coordinator/materialization.py)
has 1,960 lines at this revision; `_task_commands` and `_dispatches`
are the relevant construction owners. Artifact rows are resolved into paths,
grouped by owner and scope, and projected into commands, inputs, outputs,
resource declarations, and dispatches. These transformations are candidates
for a focused producer-to-consumer audit, not proof of redundant logic.

Audit one processing owner through profile, artifact inventory, resource
resolution, materialization, task admission, and its native producer. The
deliverable is either one complete deletion proposal or a retain decision
with its semantic reason. Compare exact ordered arguments, planned-file
bytes, graph/scopes, input snapshots, output roles, retained predecessor
paths, source identity, and resource choices. Use existing materialization,
workflow, task, and public-path tests. No new step registry or shell-to-Python
conversion is selected.

**Important retained distinctions.** Module descriptors are re-admitted at
execution planning; this is not necessarily duplicate construction.
Current AnalysisRevision scopes and historical execution scopes differ.
Processing-source snapshots must match the immutable Run binding.
Positional FASTA-sidecar outputs and reused predecessor scopes have distinct
roles. The previously noted roughly 18-line validation-path handoff and
8–10-line inventory-copy opportunities do not justify bundling unrelated
owners into one slice.

### Older publication modes

**Proposed public policy, not yet approved.** Retain independently useful
standalone commands, but make their publication create-exclusive: existing
outputs are preserved and replacement is refused. Normal Run materialization
already selects `--no-clobber` for the shell owners below, and the paired-CMH
provider selects it for its producer. This does not establish that the
standalone interfaces are unused or that every surviving failure path is
already sufficient.

The policy decision must also cover the continued acceptance of the
`--no-clobber` spelling, newly unconditional safe-ID and input-hash
admission, and where failed tool captures and diagnostics survive. These
are public behavior, not incidental cleanup. For example, QC's direct
quickcheck failure retains its capture and prints its location, while
staged cleanup can remove that capture. A universal staged path must
preserve an approved useful diagnostic outcome and truthful messages.

The common preservation and evidence rules live in the
[workflow](../operations/WORKFLOW.md#deliver) and
[architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
Across these proposed retirements, preserve scientific computation, native
artifacts, provenance, original inputs, historical readers, and recovery
evidence. Validate present outputs, partial publication, input changes,
replacement by another process, tool failure, cleanup failure, and retained
ambiguous state. Owner-specific requirements follow; they do not create
five separate versions of the common rollback rule.

| Proposed slice | Audited owner and removable mode | Owner-specific requirements and size |
|---|---|---|
| RSeQC first | [RSeQC producer](../../src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh): always use existing staged report capture, retiring direct-to-final capture and mode-dependent publication. | One tool invocation and one report make this the smallest initial proof boundary. Preserve native report text, orientation evidence, sample-ID admission decisions, and failure diagnostics. Approximate branch opportunity: 10–20 product lines. |
| BAM QC second | [QC producer](../../src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh): retire final-versus-staged capture for its two outputs. | Preserve empty quickcheck success-marker semantics, nonempty success behavior, native flagstat text, and producer/validator interpretation differences. Approximate branch opportunity: 12–22 product lines. |
| Duplicate marking | [Picard producer](../../src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh): retire direct destinations and mode branches for BAM, index, and metrics. | Preserve `REMOVE_DUPLICATES=false`, Java/Picard admission, indexing, three-output validation, input/JAR identities, and partial-publication recovery. Approximate branch opportunity: 15–25 product lines. |
| Canonical BAM | [Canonicalization producer](../../src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh): retire predecessor backup creation, replacement, restoration, and backup cleanup. | Retain sort bypass, canonical-input reuse, exact read-group/record checks, indexing, input hashes, staged-file identity, and final checks. Approximate replacement opportunity: 60–90 product lines, excluding the separate print-array proposal. |
| Paired CMH | [CMH producer](../../src/emrys/analyses/paired_cmh_candidate_ranking/producer.py): retire six-file predecessor backup/replacement and restoration. | Retain R computation, paired strata, statistical/threshold admission, six outputs and headers, summary-last publication, process-group handling, and native/historical readers. Recognize existing `.previous` recovery residue even if new attempts cease creating it. Approximate branch opportunity: 35–60 product lines. |

The revised rough total is 132–217 product lines before recovery and
compatibility costs. A closer branch review narrowed the earlier 205–345
estimate: QC, RSeQC, and duplicate marking primarily shed mode conditionals,
sentinel digest values, and target aliases; their substantive staging and
protection code remains. Their main additional value is a consistent safer
publication policy. Qualify each slice against Rule 5 rather than treating
that policy value as an automatic compression exception.

Recount each actual draft; this range is neither a net commitment nor a
reason to delete tests. Existing owner suites are the
[RSeQC shell tests](../../tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh),
[QC shell tests](../../tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh),
[duplicate-marking shell tests](../../tests/stages/duplicate_marking/test_step_04_mark_duplicates.sh),
[canonical BAM shell tests](../../tests/stages/canonical_bam/test_step_02_sort_index_bam.sh),
and
[CMH producer tests](../../tests/analyses/paired_cmh_candidate_ranking/test_paired_cmh_producer.py).
Their corresponding native-output validators and independent scientific
oracles survive. Retiring tests for deliberately retired behavior requires
preserving useful decisions and failure evidence first; retained evidence
deletion still needs its separate exact proposal and commit.

Step 05 remains part of the broader `OPS-03` family but is excluded from
this proposed tranche pending reconciliation with its separate I/O work.
Step 08 optimization is likewise not absorbed.

### Publication handoff requiring characterization

The source review identified a specific gap in the proposed surviving path
for RSeQC, BAM QC, and duplicate marking. These owners set a per-output
published flag only after
[`publish_file_create_exclusive`](../../src/emrys/libraries/file_checks.sh)
returns. The helper creates the final hard link and then checks that it
still refers to the staged file.

The source-derived failure sequence is:

1. The helper links staging to the final path.
2. Before its identity check succeeds, that final is removed or replaced.
3. The helper exits with failure before the caller sets the published flag.
4. EXIT cleanup sees that flag as false and skips ownership-aware rollback
   for this output. If its ordinary cleanup operations succeed, it removes
   staging and the owned lock without preserving the recovery anchors.

A replacement created by another process is not deleted in this sequence.
The predicted defect is loss of staging and lock evidence for unresolved
publication, not deletion of that replacement.

At the audited revision, the caller handoffs are RSeQC lines 240–243,
BAM QC lines 245–251, and duplicate marking lines 311–318; the shared helper
links at line 114 and checks identity at lines 117–120. In a multi-output
owner, an earlier sibling can already be marked published while the newest
output is still unaccounted for.

This is a predicted failure from source, not an injected or observed run.
It is distinct from a failure after the caller's flag is set, where existing
ownership-aware rollback applies. Handled HUP/INT/TERM signals may encounter
the same state only if their trap runs in this interval; signal timing needs
its own controlled characterization. SIGKILL and power loss do not execute
this EXIT-cleanup sequence. Canonical BAM and paired CMH use different
transaction state; absence of this particular pattern does not certify
their entire recovery behavior.

Before treating the no-clobber path as a complete replacement, characterize
the post-link ownership handoff through the real helper and each affected
cleanup owner. Prove both that cleanup never removes another process's
output and that it retains the required ownership/recovery anchors when
publication cannot be resolved. Select any confirmed defect correction
separately from the public overwrite-policy decision. Do not weaken the
helper's identity check or introduce a generic transaction framework merely
to shorten this repair.

### Dashboard retirement prerequisites

[`dashboard.py`](../../src/emrys/orchestration/run_coordinator/dashboard.py)
contains 1,985 product lines and its
[dedicated test module](../../tests/orchestration/run_coordinator/test_dashboard.py)
contains 986 lines. These are owner sizes, not net deletion estimates.
The Make dashboard target and direct script invocation are current callers;
the interface is documented as frozen.

Project-local `inspect` provides admitted status and task-log paths.
It does not fully replace dashboard scheduler discovery/accounting,
historical accounting fallback, exact job identity, stream ownership,
regular-file/no-symlink admission, or sanitized display of raw streams.
The dashboard's incremental stream cache tracks size and resets on truncation; it
does not provide inode-based rotation protection.
A raw `tail -F` invocation does not provide the dashboard's terminal-control
sanitization. Retiring the display therefore needs an explicit supported
home for the capabilities that remain necessary.

**Proposed two-part plan.** First decide and qualify scheduler history and
safe log access through existing expert surfaces or the smallest justified
replacement. Then remove the dashboard owner, dedicated tests, Make target,
public CLI fixture assertions, and stale documentation caller-completely.
Do not implement a new dashboard as the prerequisite by default. Account
for any surviving observation code before claiming the retirement's net size.

[`slurm_submission.py`](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
still generates `emrys-local-pilot` job/stream names. The existing
`DASHBOARD-RETIRE-01` acceptance includes retiring that spelling from
new submissions. Treat this as a distinct caller-complete slice within
that accepted outcome: approve the replacement naming before changing
submission, materialization, synthetic-harness, and logging consumers.
It is not a technical prerequisite for removing the display itself.
Preserve exact historical names and paths; never rename old streams or
delete retained accounting evidence as a side effect.

**Acceptance.** Preserve `inspect` as status authority and prove exact job
selection, historical accounting fallback, missing/replaced streams,
ownership and symlink rejection, terminal-control sanitization, and new
submission names. Use dashboard tests to identify obligations before their
retirement and retain direct protection for surviving capabilities.
Institutional scheduler behavior remains environment-deferred until the
separately authorized site qualification.

### Artifact CLI document-version admission

**Characterized defect.** The earlier local production-path reproduction
established that current module run-summary v3 and report-receipt v5 pass
their explicit schemas but fail the unversioned artifact CLI. The default
`schema_errors` call in
[`schema.py`](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py)
does not select the document's version, although `schema_validator`
already supports the closed versioned schema map.

**Proposed correction.** For an object document, pass its declared version
through the existing schema selection owner. Reuse the resulting ordered
error collection at the two manual call sites in
[`_run_summary/validation.py`](../../src/emrys/reporting/_run_summary/validation.py)
and the one in
[`_run_report/inputs.py`](../../src/emrys/reporting/_run_report/inputs.py).
This could remove about 9–13 net product lines across three existing files.
It is a public correctness change requiring selection, not pure preservation.

**Preserve.** Keep default `schema_validator` behavior, raw registry keys
and schema IDs, local references, deterministic diagnostic ordering,
the active artifact-record v2 and supported flat summary v2 and receipt v4.
Frozen receipt v3 remains outside this public admission proposal. Retain
explicit supported-version guards with their distinct first errors,
duplicate-key/non-finite JSON rejection, and semantic validation after
schema success. Unknown versions must not become silently accepted.

**Proof.** Use the real public CLI and API for valid current/historical
records and malformed versions; cover non-object documents, missing,
unknown, non-string versions, schema-first failures, and semantic failures.
In particular, object/array version values must produce a schema failure,
not an unhashable registry-key exception.
The starting suites are
[artifact-schema contracts](../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
artifact/run-summary tests, and report transaction tests. Verify that local
invocation imports the selected checkout rather than an older installed
package. This review did not rerun the prior reproduction.

### Workflow-profile fields

`PROFILE-CONTRACT-01` concerns the persisted workflow-profile v2 contract,
not the resource `ExecutionProfile` class. Clarify that terminology when
the backlog subject is next edited.

**Observed.** The
[profile schema](../../src/emrys/contracts/schemas/orchestration/v2/profile.schema.json)
requires `owner_tasks[].rule_name`, owner-task `scope_selector`, and
artifact-template `scope_selector`.
[`api.py`](../../src/emrys/contracts/orchestration/api.py) forces selectors
from `scope_type`; this makes those values redundant in admitted records.
However, `rule_name` is consumed:
[`workflow/Snakefile`](../../workflow/Snakefile) reconstructs and checks the
authored processing-rule projection against its static base graph.
The profile schema also enforces its presence and admission checks uniqueness.
It is incorrect to describe the field as unused merely because the
Execution-Plan projection omits it.

The existing functional projection in `application_model.py` excludes
both fields and provides a semantic starting point for a later migration.
The tracked
[current profile](../../workflow/contracts/local_cmh_v2.json) contains 81
rule-name/selector occurrence lines; retaining the historical profile means
these are not 81 automatically deletable lines.

**Conditional outcome.** During an independently justified profile-contract
transition, determine whether semantic owner keys and scope types can
replace the repeated adapter metadata and backend projection checks
caller-completely. Migrate profile generation, workflow consumers, schema
admission, artifact inventory, and historical inspection together. Preserve
static graph equivalence, rule/owner uniqueness, scope expansion, artifact
group order, Execution-Plan identity, and direct/Slurm behavior.

**Disposition.** Retain deferred. Do not bump the contract solely for
cleanup, silently discard authored metadata, or add a compatibility writer.
Require a net-negative migration after counting the exact v2 reader,
validator, retained profile, and tests. The source review has not established
that those economics work. Profile, workflow, materialization, and
orchestration-contract suites are the validation boundary.

### Paired-CMH configuration normalization

**Observed.** Current Project v1 accepts both flat paired-CMH fields and an
explicit module form.
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
still writes the flat form. In
[`normalization.py`](../../src/emrys/orchestration/run_coordinator/normalization.py),
the flat branch translates target/background values separately from the
existing module's `_normalize_config` in
[`paired_cmh_candidate_ranking/__init__.py`](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py).
The forms differ in policy envelope and provider binding; one is not merely
a different spelling of identical persisted intent.

**Conditional outcome.** Have the existing module normalizer own newly
admitted scientific configuration, retiring the duplicated flat transformation
only when equivalent canonical values and errors are demonstrated or their
correction is approved. Changing onboarding's emitted form is a separate
public/provenance decision. No new normalization abstraction is proposed.

**Preserve and prove.** Retain historical request-v3/execution-v1 reading,
the module readmission flat fallback, and exact flat policy semantics until
every consumer is accounted for. Compare canonical numeric types/defaults,
target aliases, absent versus null background, condition and pair errors,
error order, provider binding, and exact historical Run bytes. Use
normalization, onboarding, module, profile, and materialization tests.

The gross duplicated flat transformation is about 17 lines. Net saving is
unproven and likely small unless equivalent semantic validation can also
retire. Defer if preservation requires a new adapter or parallel pathway.
Do not describe active flat configuration or all request-v3 support as obsolete.

### Reporting TSV input grammar

**Observed.** The CSV engines in
[`_run_summary/inputs.py`](../../src/emrys/reporting/_run_summary/inputs.py)
and
[`_artifact_index/records.py`](../../src/emrys/reporting/_artifact_index/records.py)
occupy about 49 lines combined. Summary parsing uses strict quoting; index
parsing uses lax quoting. Both use `DictReader`, skip blank records, and
can retain ragged row shapes. They can reject headers before lexing the
remaining body.

The existing
[`parse_strict_tsv_bytes`](../../src/emrys/libraries/validation/tsv.py)
rejects blank/ragged rows and empty/duplicate headers, and defers shape/header
errors until lexical scanning finishes. A later quote error can therefore
take precedence. It is not a preserving drop-in replacement.

**Conditional outcome.** After an explicit input-compatibility decision,
parse already captured report bytes through that existing owner and retire
both local CSV engines. Keep domain row-count checks, hashes, snapshots,
rechecks, and diagnostics in their owners. Do not reopen a pathname or create
a configurable parser adapter to emulate every previous behavior.

**Decision and proof.** Specify malformed quotes, quoted tabs/newlines, blank
and ragged rows, duplicate/empty/wrong headers, CRLF, invalid UTF-8, and
header-plus-later-lexical-error precedence. Test complete artifact-index and
run-summary transactions, including historical valid TSVs and raw-byte
provenance. The 49-line surface is not a net estimate because domain checks
and error translation remain. Exclude sample manifests, storage roots/policy,
and the all-pass reader: their accepted forms and status semantics differ.

### Two smaller construction candidates

**Canonical BAM print arrays.** Four arrays in the canonical BAM producer
are used only to print quickcheck, header, record-count, and sample-tag-count
commands. Their declarations occupy exactly 30 lines at audited lines
148–177, including the comment; their sole reads are `print_command`
calls at lines 372, 375, 378, and 381. Replace those calls with the same
directly quoted arguments and retire the declarations. Keep executable sort,
read-group, index, and input-header command arrays.

The proposal removes 30 product lines in one existing file and leaves real
validation with `validate_bam_pair`. These commands are printed in both
dry-run and execute modes. Before acceptance, compare complete rendered
command bytes with fixed tokens and quoted paths, preserving
`printf '%q '` escaping, trailing spaces, headings, and order; verify
execute-mode invocation logs are unchanged. Run the owner shell and
executable-resolution checks through the selected production path.
This estimate is independent of canonical BAM replacement retirement.

**Runtime-profile construction.** The onboarding helper
`_runtime_profile_bytes` has one caller, `discover_runtime_profile`.
It rebuilds each frozen eight-field `RuntimeCheck`, copying six fields
unchanged. Standard-library `dataclasses.replace` can retain those fields
while replacing `target` and `probe_args`; no new carrier is needed.
That constructor-only change is approximately 11 net physical lines and
does not by itself establish a substantial slice.

An earlier in-memory construction sketch estimated about 20 net product
lines by also expanding the existing selected-tool mapping with derived
aliases and retiring the private bytes/library-path handoff within the same
owner. That combined estimate is provisional, not an executed or validated
patch. Preserve Project/runtime-directory admission, Python default
resolution, policy load, PATH tools, Rscript, Picard, renv, and Python
admission order; preserve policy-row order, authored Python spelling,
Picard/R namespace arguments, and the unknown-check diagnostic.

Validate the static selected-tool/derived-alias noncollision assumption
before changing dispatch, then compare every generated check field and
ordered row. Preserve environment construction before probing.
Use onboarding discovery, Doctor, and runtime-identity tests. Retain the
helper if removing it harms clarity or the complete draft lacks meaningful
reduction. Neither candidate authorizes installation or weakening a
checkout-origin check to make local testing convenient.

### Retained mechanisms and rejected shortcuts

The following distinctions limit the current proposals; they do not claim
that every surrounding owner has been exhaustively audited.

| Mechanism | Evidence for retaining it or narrowing the proposal |
|---|---|
| Resource override intent | `computational_resources_explicit` and `selected_reporting_memory` record authored omission and overlay intent. Effective merged resources cannot reconstruct that distinction. Retire the reporting-specific field only as part of the explicit memory-control decision, not as allegedly derivable state. |
| Repeated predecessor admission | Resource selection before Slurm submission and later child planning independently admit the predecessor. They cross a time/process boundary; do not cache one result across that boundary merely to delete validation. |
| Resource normalization | Partial fragments, complete symbolic policies, historical effective records, numeric canonicalization, and allocation resolution carry different semantics. Historical missing thread fields and accepted integral numbers affect exact record identity. |
| Immutable and mutable projections | A frozen mapping/tuple boundary for providers does not duplicate decoding into a fresh mutable JSON object. Shared canonical record storage is already implemented. |
| Input stability checks | Four-field metadata snapshots and descriptor-bound mode/change-time checks make different guarantees. Metadata is not proof of unchanged content; any consolidation needs an explicit threat-model decision. |
| Schema generations | Physical directories contain different contract families and cross-directory references. Current summary v3, frozen receipt v3, current resource/execution-profile v1 IDs, and historical request v3 cannot share one version-retirement decision. |
| Publication mechanisms | Validation reports, inventory replacement, reference provenance, runtime inspection, and stage outputs have different ownership/recovery contracts. Similar backup/lock spelling does not justify one shared transaction implementation. |
| Runtime and source identity | R dependency closure and Snakemake package-content binding remain separate assurance questions. A smaller file roster is not evidence of equally strong identity. |
| Small independent fragments | The fixed limitation-ID allocator, tiny unused helpers, small row-copy handoffs, and R wrappers did not qualify a substantial standalone change in the reviewed scopes. This is a value judgment per candidate, not an arbitrary repository-wide line-count threshold. |
| Scientific oracles and generated locks | Independent numerical expectations and reproducibility locks have different maintenance and evidence roles from duplicated production logic. Their removal cannot manufacture a product-code reduction. |

### Reconciliation, validation, and stopping conditions

The related [polish](polish-campaign.md) and
[optimization](optimization_campaign.md) campaign documents are included
from [PR #131](https://github.com/lab-cats/EMRYS/pull/131), together with its
expanded [quickstart](../../quickstart.md) and operator guidance. Their
correctness, operator-UX, developer-checking, and performance proposals
remain in those subject homes rather than being counted again as compression
outcomes. Reconcile documentation findings with the included guidance before
selection; the broader reader review and institutional walkthrough are not
completed merely by expanding the quickstart. Reconcile product-source
changes separately before implementing a slice.

In particular, the four previously recorded recovery owners, artifact CLI
version admission, timestamp checking, reporting-memory control, and dashboard
retirement overlap polish planning. Reference streaming, repeated FASTQ or
cohort scans, and allocation tuning belong to measured optimization where
runtime/memory benefit is their main purpose. Compression makes no speed,
RAM, storage, or institutional-validation claim from code size.
The existing dependency checker and documentation gate may merit a separate
maintained-tool comparison, but no replacement has qualified full policy
parity. Tooling-only work needs an explicit Rule 5 exception; the previous
two tooling approvals do not authorize a general tooling campaign.

Each selected package must state its one observable outcome, production
owner boundary, complete caller migration, behavior classification, removed
mechanism, surviving defenses, historical treatment, separate footprint,
focused local proof, required hosted checks, and stopping condition.
Do not bundle an unrelated correctness fix solely to improve the size total.
Any product-file growth, net-growth exception, public contract change, or
high-risk protection change needs its explicit decision.

For an approved autonomous stack, follow the
[delivery workflow](../operations/WORKFLOW.md#close-and-publish): publish the
locally checked bounded PR, start CI on its exact commit, and continue the
next authorized slice. After completing the current work, inspect outstanding
checks and make bounded fixes. Acceptance remains pending until the final
required evidence passes; rerun only evidence invalidated by later changes.
Do not pause useful work solely to wait for hosted CI.

The immediate deliverable is review of the completed
[fixed-output policy proposal](../design/decisions/execution-evidence-and-reporting.md#proposed-fixed-report-output-consolidation),
then a caller-complete consolidation after the specific policy is approved.
Reporting-memory policy and publication qualification remain separately
selected work; neither is absorbed into that first output slice.

An audit package stops with either a qualified bounded proposal or a reasoned
retain/defer decision. An implementation stops at its approved scope and
evidence boundary. The campaign is not complete merely because no further
small preserving edit was found. Its exit remains the evidenced disposition
of every finding, acceptance of selected outcomes at the claimed evidence
level, and verified transfer to the authoritative homes below.

## Addressed before this intake

The following cited instances no longer require work unless the remaining
review finds a broader live pattern:

- the obsolete Run-coordinator diagram and stale links were removed, while the
  current-user, grouped-pipeline, and reliability diagrams remain as concise
  reader aids rather than contract authorities;
- the functional-owner repository exception and `docs/demo` were removed;
- the global orchestration contract and orchestration-readiness document were
  retired;
- decision records, the test baseline, engineering conventions, the
  documentation index, and paired-CMH/scientific-context READMEs were
  substantially compressed;
- the stale sitemap, rolling handoff, resource README, and path-heavy standalone
  scientific-context command were removed;
- directory orientation removed too broadly during compression was restored for
  the current tracked tree without reviving retired checkout-level storage
  directories or the stale sitemap;
- the glossary remains the comprehensive terminology authority and describes
  the current public model without replacing owner contracts;
- `data/test` and `refs/test_star_index` have no tracked contents; and
- `project.yaml` already supports multiple named Analyses, with one Analysis
  selected per Run.

## Rejected proposals and retained underlying concerns

| Proposal not accepted | Technical reason | Concern that remains |
|---|---|---|
| Flatten `src/emrys` into `src` | `src/` is the standard packaging root and `emrys/` is the stable import package. Flattening would destroy or fragment package identity. | Audit unnecessary package and module fragmentation within `emrys`. |
| Add repository `data/raw` and `data/full` placeholders with automatic discovery | Git cannot retain empty directories without placeholders; Projects intentionally live independently of the source checkout; filenames do not establish biological design. | `emrys init` must create all EMRYS-owned Project directories and ingestion helpers must request explicit scientific metadata. |
| Rename `qos` to a longer field | QoS is Slurm's established term, and a public-schema migration adds more surface than it removes. | Explain it in examples and user-facing help. |
| Maintain a handoff document on every commit | It would duplicate live Git, PR, check, and task state and immediately become another stale registry. | Generate a compact handoff at an actual transfer boundary when needed. |
| Rename every numeric script immediately | Names participate in callers, package data, tests, and sometimes persisted identities; cosmetic churn would not simplify execution. | Rename retained survivors semantically during `OPS-03` migration. |
| Move whole contracts into docstrings | That would hide or duplicate cross-language behavior and recovery guarantees. | Make module docstrings explain local purpose, inputs, outputs, and architectural role. |
| Replace every `row[column]` access | Declared schema iteration can be clear and appropriate. | Replace fixed-position or context-free structures where named values materially improve comprehension. |
| Retire all v3 schemas | Several v3 records remain active and “v3” spans unrelated contract families. | Audit each exact schema and historical reader before consolidation. |

## Selection boundary

The architecture stack is integrated and the repository review is complete.
Recording a finding here does not select its implementation. Each selected
outcome still needs a bounded plan, the full affected-owner review, separate
footprint accounting, and the authority required by the
[workflow](../operations/WORKFLOW.md).

## Intake exit

The intake is complete only when:

1. the completed review is reconciled with current source and overlapping work;
2. every finding has one evidenced disposition;
3. accepted findings are consolidated by root cause rather than example;
4. each selected implementation family has a finite outcome, acceptance criteria,
   importance, complexity, and evidence boundary in the backlog;
5. useful decisions and accepted outcomes each have one durable authority; and
6. this temporary file is deleted after the transfer is verified.
