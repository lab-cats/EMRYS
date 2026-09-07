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
| CI control and latency | Manual dispatch now independently selects the ordinary and long CI groups. Hosted timings show that a new long end-to-end test still receives the default one-second scheduling estimate, placing it beside another long test despite the existing duration-aware planner. | `CI-01` owns reviewed estimate updates and measured critical-path reduction. Preserve complete, disjoint test selection and coverage checks; scheduling estimates are not a reason to delete slow production-path tests. Do not propose manual lane selection again. |
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
| Artifact and source topology | Artifact/schema guides do not orient a new reader; `SOURCE_TOPOLOGY.md` and its bespoke import-edge tooling duplicate detailed path rosters. | Preserve authored dependency permissions; observed imports cannot authorize themselves. `COMPRESS-IMPORT-01` consolidated fixed reporting permissions within the existing exact-exception mechanism. A maintained-tool replacement remains separate and needs full boundary parity. |
| Documentation gate | `validate_structure.py` hard-codes retired paths in addition to checking current owners, links, anchors, and Mermaid structure. | `COMPRESS-DOC-01` retires the completed integration bans and their dedicated tests. Current structural checks remain; they do not claim to detect every possible duplicate documentation authority. |
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
| 8. Artifact CLI version admission | The [artifact schema API](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py) uses default schema versions when its unversioned validation helper is called. A follow-up local reproduction published and readmitted current module reports through the existing production path: their v3 summary and v5 receipt decoded to JSON passed explicit schemas and semantic validation, but `emrys validate artifact-contracts` rejected both against older defaults. | Confirmed local defect; artifact CLI admission remains a separate, unselected change. Orchestration admission is addressed by `CONTRACT-API-01`. Preserve supported historical versions when selecting the artifact correction. |
| 9. Snakemake content identity | [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) obtains the Snakemake version through Python and records the Python executable as its file binding. [Runtime admission](../../src/emrys/orchestration/run_coordinator/lifecycle.py) requires that same executable identity. Determine whether Snakemake package contents must also be bound, and whether another existing identity already covers them. | Undecided guarantee; no demonstrated package-change reproduction or complete identity audit. `RUNTIME-CLOSURE-01` concerns the separate R closure. |
| 10. Duplicate runtime definitions | Runtime inspection now uses one immutable check definition and one observation definition throughout loading, probing, rendering, and public inspection. Resolved observation locations remain path objects internally. | Addressed by `RUNTIME-MODEL-01`. The [runtime owner](../../src/emrys/evidence/runtime_availability/README.md) documents the surviving model; public imports, report bytes, validation, and publication behavior are preserved. |
| 11. Whole reference reads | [Reference inspection](../../src/emrys/evidence/reference_provenance/_reference_contigs.py) reads whole FASTA and STAR Genome files to calculate hashes and lengths, and builds whole-text input for parsing. Existing streaming hash and iterable parsing mechanisms may remove these allocations. Preserve the second observation where it detects changes during inspection. | Existing stable streaming hashing can remove the hash-only allocation, but yields little maintained-code reduction. Parser streaming also needs to preserve decoding, newline, and error order. Keep this as a separate memory-reduction candidate; no timing or peak-memory measurements were taken. |
| 12. Repeated FASTQ scans | The [FASTQ check](../../src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh) counts each complete file and then scans it again for each selected read ID: the default prefix of 20 requires 21 passes per mate. A single pass could preserve complete record counts, decompression failures, and the explicitly limited prefix comparison. | Retain this independently useful read-only diagnostic under `OPS-03`. A single-pass `awk` draft changed embedded-zero-byte header handling in a local comparison, and no input-encoding rule excludes those bytes. Defer that implementation until the behavior is decided; no benchmark was run. |
| 13. Repeated processing declarations | [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) repeats task commands, inputs, outputs, and validation details in command and dispatch construction. Investigate deriving equivalent declarations from existing admitted facts. | The six sample-scoped shell owners (Steps 01, 02, 02b, 03, 04, and 05) now share command framing inside the existing materializer, retaining explicit ordered arguments and inputs. Passing already admitted validation paths and scope IDs could remove about 18 more lines, but is too small for a separate substantial slice. Module provenance roles, reused predecessor scopes, and positional Step 00c outputs remain distinct; do not combine them into a new registry. |
| 14. Source-topology rosters | [Dependency checks](../../tests/tools/source_dependencies.py), tests, and [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) maintain overlapping path and composition rosters. Determine which can be derived or replaced by a maintained boundary-checking tool while preserving real dependency rules. | The 12 fixed reporting permissions now use the existing exact-exception mechanism under `COMPRESS-IMPORT-01`; the separate bypass is retired, and stale reporting permissions now fail. Imports are already discovered from source; CLI targets and allowed exceptions are policy. A larger maintained-tool migration remains unqualified for dynamic imports, private-module rules, repository admission, and logging consumers. |
| 15. Historical output replacement | The Run coordinator selects no-clobber publication, while standalone owners retain historical replacement routes with different recovery behavior; the [Step 08 contract](../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md) is one example. Audit supported callers and whether the orchestrated path fully replaces each route. | Existing `OPS-03`. Retiring public behavior requires a decision; absence of external use has not been proved. |
| 16. Parallel configuration normalization | [Project normalization](../../src/emrys/orchestration/run_coordinator/normalization.py) and [application modeling](../../src/emrys/contracts/orchestration/application_model.py) retain overlapping flat paired-CMH configuration and module-policy forms. Trace current and historical inputs before proposing one surviving representation. | Revision construction and partition projection already share their existing owner. Flat and module forms bind different identity and admission semantics; no preserving helper retirement was found. Public migration and any broader paired-replicate validation consolidation remain undecided. |
| 17. Repeated reporting declarations | Reporting arguments, outputs, and kinds recur across owners. Current reporting uses direct producer APIs and one ordered execution loop; its materialization is already delegated outside the explicit scientific implementation roster. A follow-up caller audit found that `reporting_memory_mb` is validated, persisted, hashed, and overlaid on resume, but no scheduler or reporting execution consumes it for memory allocation. | Unused internal report-table labels, IDs, and truncation metadata are retired; source identities, actual row limits, rows, and snapshots remain. `REPORT-ROSTER-01` owns the remaining work. Retiring the active memory control requires a decision on accepted YAML/CLI inputs and exact historical policy admission. Its value is excluded from computational resource identity, but changing its schema/admission implementation can still change new Run identities. Preserve immutable Runs, historical reads, report regeneration, and module-specific reporting. |
| 18. Report check identities | Existing [artifact-adapter tests](../../tests/reporting/test_artifact_adapters.py) show that reordered or different unique check IDs can still be treated as complete. Completion should follow the admitted roster's actual identity and order when that roster is defined. | Existing `REPORT-ROSTER-01`. No neutral contract owner currently publishes a check-ID roster. Step 09 validation checks membership while reporting also checks order; importing its private validator or tightening generic artifact admission is not a preserving consolidation. External-module rosters need a contract decision; preserve independent expected-result tests. |
| 19. Eight-selection limit | The [scientific-context contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/CONTRACT.md) binds an eight-selection limit across generation, receipts, and validation, with reporting limits as well. Supporting nine panels requires reviewing the entire path, including labels and rendered output. | Existing `REPORT-04`. Preserve full underlying data and historical records; no rendered-output review was performed in this survey. |
| 20. Historical documentation exclusions | The [documentation gate](../../scripts/documentation/validate_structure.py) enumerates retired paths alongside current structural checks. Review which exclusions still prevent a credible regression after the architecture stack's integration. | Addressed by `COMPRESS-DOC-01`: the 18 file and five task-directory bans covered completed retirements, and open PRs #44/#45 did not modify them. Their ordinary merge could not restore unchanged old tree contents. The historical bans and their tests are retired; current ownership, links, anchors, and diagram checks remain. |

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
- **R command setup already shares argument parsing.** The remaining owner
  wrappers differ in script-path handling, package admission, diagnostics, and
  error precedence. A common bootstrap would add a new abstraction; inlining
  the argument wrappers alone saves too little for a substantial slice.
- **The dashboard remains frozen.** Its two renderers repeat roughly 35–40
  lines of setup and layout framing, but the owner's documented frozen status
  keeps this outside the current campaign. `DASHBOARD-RETIRE-01` still owns its
  separate disposition and historical compatibility.

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

These measurements define future audit boundaries; file length alone is not a
defect or authority to split a cohesive owner.

| Finding | Evidence | Disposition at intake exit |
|---|---|---|
| Large-file surface | 101 tracked files exceed 500 lines: 42 product, 52 test, and 7 other files. Of the 37 over 1,000 lines, 15 are hand-maintained product files, 17 are tests, and 5 are generated lock, CI, or third-party bootstrap files. | Under `COMPRESS-01`, rank owners by duplicated responsibility and removable behavior, not line count. Transfer only finite, net-negative owner changes. |
| Run-coordinator concentration | `run_coordinator` contains about 20,225 product lines and 20,824 test lines. `task.py`, `lifecycle.py`, `materialization.py`, `dashboard.py`, `control.py`, `doctor.py`, `onboarding.py`, and `reporting_boundary.py` each exceed 1,000 product lines. `materialization.py` devotes about 1,086 lines to repeated task command and dispatch declarations; its main test file is about 4,959 lines. | Investigate deriving repeated processing-owner plans from existing admitted facts and removing duplicate declarations and low-value defensive cases while preserving exact arguments, ordering, identity, reuse, recovery, and fault behavior. Select a finite outcome before committing to a shared representation; do not mechanically split files or add one-caller wrappers. `DASHBOARD-RETIRE-01` remains separate. |
| Generated dependency lock | `pixi.lock` is about 3,881 lines/140 KB and binds the managed Linux native/R environment used by Doctor and CI. | Retain it as generated reproducibility input; it is not maintained product-code bloat. |
| Repeated constants | Persisted filenames such as `run.json`, `normalized.json`, and `attempt.json` are repeated contract vocabulary, while the three reporting kinds recur across five owners. Small path/publication helpers have similar spelling but different trust and error semantics. | Do not add constants or helpers merely to replace strings. `REPORT-ROSTER-01` owns derivation of reporting declarations; consolidate other values only when one semantic authority deletes validation or branches. |
| Schema layout | The 27 JSON schemas occupy about 5,353 lines across artifact `v1`-`v5` and orchestration `v1`-`v3`, but those directories are family-specific physical revisions rather than five whole-system generations. Active schemas intentionally reuse definitions across directories. | Audit current and historical readers, then compare the present version directories with a flatter resource layout; pre-release paths are not protected merely because they exist. Prefer whichever model reduces cognitive and maintenance surface while preserving required identities and historical reads. `CONTRACT-API-01` addressed orchestration admission; artifact admission remains separately unselected. Consider a finite caller-complete retirement audit for apparently historical resources; do not bulk-renumber or delete retained evidence without approval. |
| Numeric stage and resource identities | Fourteen historical stage IDs and related rosters appear in resource policy, profile schema, and the Snakefile; Analysis admission currently permits one Step `09` and optional Step `10`. Some historical profiles intentionally omit newer task IDs. | Propose a finite semantic task/resource-key migration only when module extension needs it: derive current rosters from admitted task descriptors, preserve exact historical profile reads, and remove duplicated stage lists. `QUAL-04` and `PROFILE-CONTRACT-01` own narrower existing derivations; avoid a cosmetic global rename. |

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
