# NORAD pipeline plan

This is the authoritative pipeline/package/evidence roadmap, status matrix,
acceptance criteria, and approved branch lineage. Task-workflow status is the
card's directory under [`../tasks/`](../tasks/). Current checkout details belong in
[`../operations/HANDOFF.md`](../operations/HANDOFF.md); commands belong in
[`../operations/RUNBOOK.md`](../operations/RUNBOOK.md).

## Pipeline

| ID | Purpose | Acceptance boundary | Status |
| --- | --- | --- | --- |
| `00a` | Build STAR index | Source identity, contigs, index structure, and configured overhang inspected | cluster-proven |
| `00b` | Convert GTF to BED12 | BED12 structure, sorting, blocks, and GTF agreement inspected | cluster-proven |
| `00c` | Build FASTA sidecars | FASTA/FAI/DICT identity and contig agreement inspected | cluster-proven |
| `01` | STAR alignment | STAR outputs, logs, mapping summary, and BAM inspected | cluster-proven |
| `02` | Canonical BAM | BAM/BAI, coordinate sorting, read groups, and alignment RG tags inspected | cluster-proven |
| `02b` | BAM QC | quickcheck and flagstat evidence inspected | cluster-proven evidence set |
| `03` | Infer library orientation | RSeQC structure and paired-orientation fractions inspected | cluster-proven |
| `04` | Mark duplicates | BAM/BAI/metrics, sorting, RG preservation, and duplication metrics inspected | cluster-proven |
| `05` | Split N cigars | declared output transaction and validation inspected | cluster-proven |
| `06` | Split mechanical orientations | outputs, indexes, and count arithmetic inspected | cluster-proven |
| `07` | Cohort mpileup | receipts, VCF structure, selectors, hashes, sample order, and counts inspected with real runtime | local mocked-runtime only |
| `08` | Preprocess and annotate VCFs | three-output transaction, schemas, hashes, ordering, uniqueness, and counts inspected | local real-R fixtures only |
| `09` | Paired CMH ranking | six-output transaction, statuses, subsets, mutation spectrum, and PDFs inspected | local real-R fixtures only |
| `09c` | Validate scientific evidence | explicit production evidence reconciled and review state lawfully published | local synthetic fixtures only |

Steps `07`–`09` are not cluster-proven. Step `09c` tooling does not constitute
a completed production review.

## Evidence and reporting packages

| Package | Responsibility | Package/evidence status |
| --- | --- | --- |
| `artifact-schema-v1` | Public artifact, scientific-review, run-summary, and report-receipt contracts | implemented and fixture-tested |
| `artifact-adapters-v1` | Explicit read-only artifact inventory adaptation | implemented and fixture-tested |
| `artifact-run-summary` | Canonical summary and deterministic TSV/QC projections | implemented and fixture-tested |
| `report-html-v1` | Static self-contained HTML rendering | implemented and locally renderer-tested |
| `report-html-v1a-report-table-approvals` | Exact run-bound supplemental-table approvals | implemented and fixture-tested |
| `report-html-v1b-docs-responsibility-consolidation` | One canonical owner per documentation category | completed |
| `report-exports-v1` | Atomic HTML/PDF/TSV/report-receipt bundle | implemented and locally tested |
| `post09-runtime-preflight` | Explicit-profile runtime availability checks | implemented and locally fixture-tested; CSU batch execution pending |
| `post09-reference-provenance` | Explicit reference hashes, provenance, and contig reconciliation | implemented and locally fixture-tested; production execution pending |
| `post09-storage-inventory-retention` | Explicit storage measurement and retention-policy recording | implemented and locally fixture-tested; production inventory and approvals pending |
| `post09-validation-report-00a` | Structured STAR-index validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-00b` | Structured BED12/GTF validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-00c` | Structured FASTA/FAI/DICT validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-01` | Structured STAR-alignment output validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-02` | Structured canonical-BAM validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-02b` | Structured persisted BAM-QC validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-03` | Structured RSeQC orientation-fraction validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-04` | Structured marked-BAM/Picard-metrics validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-05` | Structured split-N-cigar/reference-prerequisite validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-06` | Structured mechanical-orientation output/count validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-07` | Structured VCF/receipt/selector/manifest/count validation and report propagation | implemented and locally fixture-tested; real-runtime and production report pending |
| `post09-validation-report-08` | Structured three-output preprocessing transaction validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-09` | Structured six-output CMH transaction and semantic validation with report propagation | implemented and locally fixture-tested; production report pending |
| `refactor-00-comprehensive-audit` | Final evidence-ranked audit, one-time locked dependency refresh, do-not-abstract boundaries, and documentation consistency correction | complete |
| `refactor-01-test-baseline` | Measured Python line/branch baseline and public-contract risk-to-test matrix | complete |
| `refactor-01a-step09-independent-cmh-oracle` | Independent Step `09` DP/AD-derived CMH and estimability characterization | complete, pushed, and upstream-equal |
| `refactor-01a1-demo-report-command` | Populated synthetic demo command plus bounded, broadly categorized HTML and readable PDF projection | complete; predecessor to the completed validation-efficiency package |
| `refactor-01aa-validation-efficiency` | Quiet failure-first output, de-duplicated validation lanes, and measured bounded parallel execution | complete; predecessor to the validation-publication characterization package |
| `refactor-01b-validation-publication-faults` | Shared validation-report publication, recheck, rollback, cleanup, and recovery fault characterization | implementation and docpatch complete; verified clean, pushed, and upstream-equal before the documentation descendant |
| `refactor-01-architecture-direction-docs` | Documentation-only task registry, durable architecture decisions, future constraints, open choices, and future diagrams | complete in this documentation package; no executable or evidence-state change |
| `codex/context-start-policy` | Version-aware task-start routing, selective phase-boundary inspection, impact-directed documentation review, and explicit documentation-only validation; see [`CONTEXT-00`](../tasks/COMPLETED/CONTEXT-00-define-minimal-task-start-context.md) | documentation-only package complete, pushed, and upstream-equal at the verified predecessor boundary; no executable or evidence-state change |
| `codex/concurrent-doc-sidecars` | Isolated concurrent documentation/card sidecars with serialized integration; see [`CONCURRENCY-01`](../tasks/COMPLETED/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md) | documentation-only policy package complete, pushed, and upstream-equal at the verified predecessor boundary; no executable/evidence-state change |
| `codex/strategy-task-cards` | Capture the completed concurrency/program strategy as four bounded future cards ready for task-specific planning plus canonical references | documentation-only card-bootstrap package; no future card is selected, no pilot content is reviewed or integrated, and live Git remains authoritative for publication/upstream equality |
| `codex/concurrency-02-fragment-protocol-reconciliation` | Manual integration-fragment protocol plus bounded, dry-run-first Git safeguards; see [`CONCURRENCY-02`](../tasks/COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md) | protocol and tested operator tooling complete after a durable coordination checkpoint and one consumed, remotely preserved synthetic exchange; no pipeline/scientific behavior or pilot-content review/integration |
| `codex/program-01-slice-1-critical-runway` | First rolling-wave slice establishing the temporary critical runway; see [`PROGRAM-01`](../tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md) | first documentation-only slice complete; the card remains in progress, and its unsliced remainder is frozen pending reassessment |
| `codex/arch-02a-slice-7-infer-paired-read-orientation-contract` | Implementation-backed functional-owner contracts and exact public-surface inventory; see completed [`ARCH-02A`](../tasks/COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md) | documentation-only inventory complete across 14 JIT slices; all 88 public surfaces map once, unresolved ownership leaks remain explicit, and no executable or evidence state changed |
| `codex/jit-01-self-hosting-thin-slice-delivery` | Minimal self-hosting thin-slice procedure before ARCH-02B; see completed [`JIT-01`](../tasks/COMPLETED/JIT-01-establish-self-hosting-thin-slice-delivery.md) | documentation-only workflow bootstrap complete, published, and upstream-equal; noncritical input-dependent items remain in a retained decision record, and no executable or evidence state changed |
| `codex/arch-02b-through-02d-jit` | Sequential semantic-map, target-topology, and direct-migration-mechanics package; see completed [`ARCH-02B`](../tasks/COMPLETED/ARCH-02B-define-semantic-stage-map.md), [`ARCH-02C`](../tasks/COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md), and [`ARCH-02D`](../tasks/COMPLETED/ARCH-02D-define-direct-migration-mechanics.md) | documentation-only package complete locally on one branch and intentionally unpushed; exact identities/DAG, 14 target homes and dependency rules, and reversible parity/removal mechanics are frozen without executable, schema, fixture, report-template, dependency, or test-harness change |
| `codex/doc-ia-01-documentation-compression` | Audience-aware ownership map, full Markdown/Mermaid disposition, no-loss source ledger, resolved documentation locations, and eight bounded consolidation cards; see completed [`DOC-IA-01`](../tasks/COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) | explicitly selected documentation-only exception complete locally and intentionally unpushed; root ownership rosters now route to one owner, later consolidation remains separately planned, and no executable, schema, fixture, report-template, dependency, or test-harness behavior changed |
| `codex/doc-cons-08a-slim-root-agent-router` | Root-router compression, neutral engineering-conventions owner, and package-delivery procedure; see completed [`DOC-CONS-08A`](../tasks/COMPLETED/DOC-CONS-08A-slim-root-agent-router.md) | separately approved documentation-only exception complete locally and intentionally unpushed; root automatic guards remain intact, detailed conventions and procedure have one dedicated owner each, and no executable, schema, fixture, report-template, dependency, source-layout, public-interface, scientific-policy, or test-harness behavior changed |
| `codex/doc-cons-08b-compress-root-entry-and-priority-views` | Concise newcomer and current-priority root views with canonical routes and no-loss dispositions; see completed [`DOC-CONS-08B`](../tasks/COMPLETED/DOC-CONS-08B-compress-root-entry-and-priority-views.md) | separately approved local-only documentation exception complete and intentionally unpushed; completed history, roadmap, live state, blockers, task scope, and questions retain one canonical owner, later consolidation remains separately planned, and no executable, configuration, generation, schema, fixture, report-template, dependency, source-layout, public-interface, scientific-policy, or test-harness behavior changed |
| Conditional fragment/lifecycle infrastructure | Complete independent characterization of the extracted documentation validator, enforce the proven fragment contract, implement proposal/review states, then add logical epic indexes; see [`DOC-GATE-01`](../tasks/TODO/DOC-GATE-01-extract-documentation-validator.md), [`CONCURRENCY-03`](../tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md), [`TASK-LIFECYCLE-01`](../tasks/TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md), and [`TASK-EPIC-01`](../tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md) | future separately planned packages in dependency-valid order after the post-`PROGRAM-01` reassessment; current registry remains three-state, while the validator is executable but still lacks the card's independent invalid-state fixture coverage and any separately approved Make exposure |
| `refactor-01c-validation-check-rosters` | Independent exact ordered check-roster characterization; see [`TEST-01C`](../tasks/COMPLETED/TEST-01C-characterize-validation-check-rosters.md) | implementation `8d58fc6` and separate docpatch complete locally; unpushed predecessor to completed `TEST-01D` |
| `refactor-01d-public-cli-contracts` | Complete public CLI/direct-CWD/exit characterization; see [`TEST-01D`](../tasks/COMPLETED/TEST-01D-characterize-public-cli-contracts.md) | implementation `a003065` and separate docpatch complete locally; unpushed predecessor to the approved `TEST-01E` descendant |
| `refactor-01e-slurm-contracts` | Every SLURM wrapper's mode/module/delegation/output/exit contract; see [`TEST-01E`](../tasks/COMPLETED/TEST-01E-characterize-slurm-wrapper-contracts.md) | implementation `9a4fb09` and separate docpatch complete locally; unpushed predecessor to completed `TEST-01F` |
| `refactor-01f-independent-goldens` | Independent critical serialized/state/evidence goldens; see [`TEST-01F`](../tasks/COMPLETED/TEST-01F-create-independent-contract-goldens.md) | implementation `dcb5dd4`, targeted shared-policy correction `1986898`, and separate docpatch complete locally; unpushed predecessor to completed `TEST-01Z` |
| `refactor-01z-test-sufficiency-gate` | Behavior-row classification, explicit readiness decision, and bounded Phase `0` evidence correction; see [`TEST-01Z`](../tasks/COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) | affirmative 88/88-row decision plus test-only corrections `0c64d1a`, `44d3255`, and `fd98244` complete, adversarially reviewed, pushed, and upstream-equal at `b2af738`; no closure cards or production behavior changes |
| `codex/log-01-characterize-current-output-reconciliation` | Current stdout, stderr, scheduler, Make, test, operational-check, durable-copy, and evidence-log inventory; see [`LOG-01`](../tasks/COMPLETED/LOG-01-characterize-current-output.md) | documentation-only characterization complete; every current surface has a normalized output profile and trace, candidate overclaims are corrected, and runtime output remains unchanged |
| `codex/log-02-define-logging-contract-reconciliation` | Public controls, streams, one-writer operation record, publication ordering, failure, security, retention, scheduler, evidence-role, scenario, and adoption contract; see [`LOG-02`](../tasks/COMPLETED/LOG-02-define-logging-contract.md) | documentation-only target contract complete; the rejected-ancestry candidate was evidence only, current output/defaults remain unchanged, and no rollout card was created |
| Phase `02` design cards | Functional inventory, semantic map, target topology, migration, intake, library, report, logging, documentation, code-doc, size, and local-context designs ending in [`PLAN-02Z`](../tasks/TODO/PLAN-02Z-integrate-future-task-sequence.md) | `LOG-01`, `LOG-02`, `ARCH-02A` through `ARCH-02D`, interposed `JIT-01`, and explicitly selected documentation exceptions `DOC-IA-01`, `DOC-CONS-08A`, and `DOC-CONS-08B` are complete; recasting `PLAN-02Z` and selecting its independent review remain the next eligible ordinary runway actions, while all other workflow status remains owned by each card's directory |
| Phase `02` independent reviews | Architecture, reliability, and usability reviews in `REVIEW-ARCH-01` → `REVIEW-REL-02` → `REVIEW-UX-03` order | future review set; workflow status is owned by each card's directory |
| Phase `03` bounded packages | Exact stage/domain migrations, logging adoption, code documentation, consolidation, corrections, and extractions generated by the reviewed plan | not yet named; cards must be evidence-derived and separately approved |
| `refactor-99-final-audit` | Final finding/decision/card disposition, compatibility comparison, measured validation, documentation audit, and handoff; see [`AUDIT-99`](../tasks/TODO/AUDIT-99-final-refactor-and-documentation-audit.md) | future final local gate; workflow status is the linked card's directory |

Schema validation, adapter completion, summary completion, table approval, and
report rendering never promote computational, scientific, or biological
state.

The former `refactor-02-high-level-plan` and `refactor-02a-detailed-plan`
placeholders are superseded by the bounded Phase `02` design cards plus
`PLAN-02Z`. The former `refactor-02b`/`02c`/`02d` review placeholders map to
`REVIEW-ARCH-01`, `REVIEW-REL-02`, and `REVIEW-UX-03`. Cards are not branch
names: each live task-specific plan selects its descendant branch only after
inspection and approval.

## Active critical runway

`ARCH-02A` through `ARCH-02D` and the interposed `JIT-01` workflow bootstrap
are complete. The user separately selected and completed `DOC-IA-01`,
`DOC-CONS-08A`, and `DOC-CONS-08B` as local-only documentation exceptions;
those completions do not select `DOC-CONS-08C` through `DOC-CONS-08H` or
change ordinary runway order. The next
eligible ordinary runway action is still to recast `PLAN-02Z` and select its
independent review just in time before planning the first physical migration;
neither is selected by this status. Every other package is preserved but
currently dead/out of scope under the temporary boundary in
[`TASK_START.md`](../operations/TASK_START.md#temporary-critical-runway).

## Frozen pre-runway maintenance context

The earlier sequence below is retained for later reassessment, not as active
work. Maintenance order remains distinct from technical blocking:

1. [`CONCURRENCY-01`](../tasks/COMPLETED/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
   established isolated candidate worktrees, multiple documentation/card
   sidecars, single-owner integration, and combined validation policy. The
   required first-use strategy discussion was completed on 2026-07-31.
2. Complete and publish the `codex/strategy-task-cards` documentation package.
   It records the resulting cards and decisions but selects none of them.
3. Preserve the completed
   [`CONCURRENCY-02`](../tasks/COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md)
   manual protocol and synthetic exchange without reviewing or integrating the
   preserved pilot.
4. Preserve the completed first critical-runway slice of
   [`PROGRAM-01`](../tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md),
   while its unsliced remainder stays in progress and frozen during the
   architecture runway.
5. Reassess the remaining order under that model. The current expected
   candidates begin with
   [`DOC-GATE-01`](../tasks/TODO/DOC-GATE-01-extract-documentation-validator.md),
   which should characterize, extract, and test the embedded documentation
   validator without changing accepted behavior.
6. Once their genuine prerequisites are complete,
   [`CONCURRENCY-03`](../tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md)
   may enforce the proven fragment contract using `CONCURRENCY-02`'s synthetic
   exchange evidence,
   [`TASK-LIFECYCLE-01`](../tasks/TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md)
   may implement `UNREFINED` and `INTEGRATION_REVIEW`, and
   [`TASK-EPIC-01`](../tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md)
   may then add orthogonal logical epic indexes. `CONCURRENCY-03` and
   `TASK-LIFECYCLE-01` are independent after their own prerequisites; epic
   indexing follows the lifecycle package.
7. Only after `CONCURRENCY-02`, `PROGRAM-01`, `DOC-GATE-01`, `CONCURRENCY-03`,
   and `TASK-LIFECYCLE-01` establish the applicable infrastructure may the
   separately approved pilot-integration card generated by `PROGRAM-01` be
   selected. The preserved researcher-path sidecar is the intended first
   substantive integration candidate; `TASK-EPIC-01` is not a prerequisite
   unless later evidence establishes a genuine dependency.
8. [`TASK-REG-01`](../tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md)
   should then migrate active dependency metadata and validator behavior to the
   approved true-technological-blocker model.
9. Completed
   [`DOC-IA-01`](../tasks/COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md)
   leads the Phase `02` documentation family and produced the no-loss bounded
   consolidation cards. Separately approved
   [`DOC-CONS-08A`](../tasks/COMPLETED/DOC-CONS-08A-slim-root-agent-router.md)
   and
   [`DOC-CONS-08B`](../tasks/COMPLETED/DOC-CONS-08B-compress-root-entry-and-priority-views.md)
   completed the root router and entry/priority slim-down; `DOC-CONS-08C`
   through `DOC-CONS-08H` remain unselected and require separate selection,
   task-specific planning, and approval.

Each remains separately planned and approved. If live technical evidence later
establishes a real blocker, record that evidence on the affected cards rather
than inferring it from this order.

## Approved local lineage

```text
report-html-v1a-report-table-approvals
└── report-html-v1b-docs-responsibility-consolidation
    └── report-exports-v1
        └── post09-runtime-preflight
            └── post09-reference-provenance
                └── post09-storage-inventory-retention
                    └── post09-validation-report-00a
                        └── post09-validation-report-00b
                            └── post09-validation-report-00c
                                └── post09-validation-report-01
                                    └── post09-validation-report-02
                                        └── post09-validation-report-02b
                                            └── post09-validation-report-03
                                                └── post09-validation-report-04
                                                    └── post09-validation-report-05
                                                        └── post09-validation-report-06
                                                            └── post09-validation-report-07
                                                                └── post09-validation-report-08
                                                                    └── post09-validation-report-09
                                                                        └── refactor-00-comprehensive-audit
                                                                            └── refactor-01-test-baseline
                                                                                └── refactor-01a-step09-independent-cmh-oracle
                                                                                    └── refactor-01a1-demo-report-command
                                                                                        └── refactor-01aa-validation-efficiency
                                                                                            └── refactor-01b-validation-publication-faults
                                                                                                └── refactor-01-architecture-direction-docs
                                                                                                    └── codex/context-start-policy
                                                                                                        └── codex/concurrent-doc-sidecars
                                                                                                            └── codex/strategy-task-cards
                                                                                                                └── codex/refactor-01c-validation-check-rosters
                                                                                                                    └── codex/refactor-01d-public-cli-contracts
                                                                                                                        └── codex/refactor-01e-slurm-contracts
                                                                                                                            └── codex/refactor-01f-independent-goldens
                                                                                                                                └── codex/refactor-01z-test-sufficiency-gate
                                                                                                                                    └── codex/log-01-characterize-current-output-reconciliation
                                                                                                                                        └── codex/log-02-define-logging-contract-reconciliation
                                                                                                                                            └── codex/concurrency-02-fragment-protocol-reconciliation
                                                                                                                                                └── codex/program-01-slice-1-critical-runway
                                                                                                                                                    └── codex/arch-02a-slice-7-infer-paired-read-orientation-contract
                                                                                                                                                        └── [future descendants selected after reassessment]
                                                                                                                                                            └── refactor-99-final-audit
```

Bracketed entries are planning boundaries, not branch names or completed
lineage. The explicitly approved local-only characterization tranche selected
`TEST-01C`, `TEST-01D`, `TEST-01E`, `TEST-01F`, and `TEST-01Z` from the pinned
strategy-card base. `TEST-01C` through `TEST-01Z` are complete and published,
and TEST-01Z recorded an affirmative 88-row decision with no undefined row or
closure card. A later Phase `0` adversarial review found two overstated
protection claims; correction `0c64d1a` closes them. After the first final
review exposed a bare recursive-Make portability defect, `44d3255` closed that
blocker. A second review exposed ambient Make-state contamination; `fd98244`
closed it with a bounded environment and direct regression. Final independent
review at `fb21c9d` reproduced both blockers and returned `PUBLISHABLE`; the
corrected Phase `0` tip was then pushed and verified upstream-equal at
`b2af738`. A separate descendant completed LOG-01 as documentation-only current-
output characterization and was published at `ead6ff4`. Its next descendant
completes LOG-02 as a documentation-only target contract. The preserved
`dad6b79` proposal was not merged, rebased, or cherry-picked because it descends
from the rejected pre-correction LOG-01 candidate; only reviewed design material
was re-authored against current state. `CONCURRENCY-02` is complete, the first
`PROGRAM-01` critical-runway slice is complete without completing that card,
and `ARCH-02A` is complete as a 14-slice documentation-only inventory. The
interposed `JIT-01` workflow bootstrap is also complete; its retained record
contains only noncritical input-dependent decisions, and
[`DOC-SITEMAP-01`](../tasks/TODO/DOC-SITEMAP-01-classify-temporary-task-start-routing.md)
owns later temporary-routing migration. `ARCH-02B` through `ARCH-02D` are
complete on one local-only branch. `DOC-IA-01` and its separately selected
`DOC-CONS-08A` and `DOC-CONS-08B` children are complete on successive
local-only descendants as explicit documentation exceptions; the remaining
consolidation cards are not selected. Recasting `PLAN-02Z` and selecting its
independent review are next eligible but not selected; other candidate work
remains frozen rather than becoming blocker metadata.

Do not perform remote or cluster
validation during this sequence.

## Package acceptance criteria

### Documentation consolidation

- one canonical owner for each mutable fact;
- no current status, detailed product contract, tool snapshot, commit ID, test
  total, or current-next-stage narrative in `AGENTS.md`;
- one authoritative status matrix and branch lineage in this file;
- takeover evidence only in `HANDOFF.md`;
- executable commands only in `RUNBOOK.md`;
- detailed operational task-start freshness, routing, and expansion rules in
  `TASK_START.md`, with concise enforcement in `AGENTS.md`;
- durable rationale only in `DECISIONS.md`;
- open questions plus a resolved index only in `QUESTIONS.md`;
- troubleshooting contains symptom, cause, diagnosis, and fix—not roadmap;
- current topology in `ARCHITECTURE.md`, future constraints in
  `FUTURE_ARCHITECTURE.md`;
- standalone `.mmd` files are canonical and contain no transient status;
- demos are explicitly presentation material or dated snapshots;
- every task card has one stable ID and status directory, the required sections,
  valid links, and no duplicate ID;
- new or edited active hard dependencies represent genuine technological
  blockers, are reciprocal while both cards remain mutable, and are acyclic;
  a `Fully` unblock leaves no other card blocker, while `Partially` never
  authorizes a target; legacy-edge migration remains with `TASK-REG-01`;
- cards link to canonical rationale/state/commands/topology instead of owning
  those facts, and moving a card updates every inbound link in the same commit;
- moving a card to `IN_PROGRESS` starts read-only planning only; each card
  requires a separately approved task-specific plan before implementation;
- the `ARCH-DOC-00` decision-capture crosswalk maps every approved or deferred
  architecture discussion item to a durable owner and task card;
- unique scientific and validation evidence is preserved;
- no NORAD workflow, validator, schema, config, scientific-method, or
  public-contract behavior changes; the separately committed one-time
  dependency lock refresh is limited to resolving the guarded local gate;
- the documentation gate passes; computational gates apply only to executable
  or test-affecting changes.

### Concurrent authoring and serialized integration

- one canonical integration/control worktree owns accepted history and current
  state;
- at most one implementation-candidate or immutable-execution lane coexists
  with multiple disjoint documentation/card sidecars;
- every authoring candidate has a unique branch and absolute sibling worktree;
  immutable execution uses a locked detached worktree at its exact pushed
  commit; every lane records its base and target, owner, role, reserved card
  IDs and paths, prohibited overlaps, coupling classification, and validation
  obligation;
- candidate branches and card placement remain proposals until the integration
  owner accepts them; only that owner moves canonical card status or publishes
  lineage, priority, completion, or evidence;
- independent sidecars may land one at a time, while coupled documentation
  remains a draft or triggers a checkpoint and re-plan;
- immutable execution records the exact commit, inputs, configuration,
  command/job, and output/log identity without broadening runtime authority;
- final combined validation governs closure, and computational evidence is
  reused only when path classification and Git identity prove the tested
  executable state unchanged;
- a candidate may reserve exact deliverables plus one transient fragment,
  while nonexclusive target declarations grant no canonical write authority;
- every valid frozen fragment request and partial residual receives a
  structured terminal disposition, and invalid handoffs are returned without
  request dispositions; and
- final publication removes the fragment while its immutable remote source ref
  preserves raw provenance; and
- conflicts and unfinished candidates are preserved, never force-integrated or
  automatically deleted.

### Comprehensive refactor program

- [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) owns the evidence-ranked findings,
  test-first dispositions, and explicit retained/deferred boundaries;
- [`TEST_BASELINE.md`](TEST_BASELINE.md) owns the measured global Python
  line/branch summary, public-contract risk-to-test matrix, fixture
  independence classification, and the evidence behind the exact Phase `01`
  characterization sequence;
- the independent Step `09` characterization oracle is complete without
  changing the production validator or statistical method;
- validation efficiency is measured and hardened before the five
  critical/high-risk characterization branches named above;
- `refactor-01aa-validation-efficiency` preserves existing public Make targets,
  separates non-overlapping Python-coverage, shell-contract, sequential
  guarded-R, and pinned-report-runtime lanes, retains quiet failure logs and a
  serial fallback, and leaves no stale child, lock, staging, or coverage
  residue;
- xdist becomes a default only with repeated exact serial/parallel pass, skip,
  file, line, and branch equality plus at least a 15% Python-lane improvement;
  parallel orchestration becomes a default only with at least a 25% complete
  gate improvement, using the smallest stable concurrency within 5% of the
  fastest result and no more than four top-level lanes;
- `refactor-01b-validation-publication-faults` characterizes the shared
  thirteen-validator publisher plus the distinct reference-provenance,
  runtime-preflight, and storage-inventory publishers with injected input
  mutation, symlink, fsync, move, validation, cleanup, rollback, and
  interruption failures; known unsafe recovery states remain explicitly
  labeled rather than being normalized into passing behavior;
- `refactor-01z-test-sufficiency-gate` classifies every applicable behavior as
  preserved, characterized defect, undefined/decision-required, or environment-
  deferred and releases Phase `02` only when every applicable preserved row is
  protected; a negative decision creates bounded closure and repeat-decision
  cards;
- `codex/log-01-characterize-current-output-reconciliation` maps every current
  command and validation surface to explicit stream, audience, stability,
  consumer/test, durability, recovery, and exposure semantics without changing
  output; mixed streams and unsafe or mode-dependent durability are labeled
  rather than approved;
- `codex/log-02-define-logging-contract-reconciliation` defines level/control
  resolution, machine/human streams, dry-run visibility, a single-writer
  operation-attempt record, receipt-safe writes, bounded failures, protected
  retention, scheduler separation, evidence authorization, and normalized
  cross-level equivalence without implementing or activating logging;
- the Phase `02` design-card set produces evidence-backed local decisions and
  `PLAN-02Z` integrates them without executing the repo-spanning refactor;
- separate architecture, reliability, and usability reviews correct the plan
  before any Phase `03` executable architecture package;
- Phase `03` implements only reviewed, bounded cards, each with its own live
  plan and approval. It preserves behavior/science/output/evidence/recovery
  contracts while allowing explicitly approved and parity-tested path/interface
  migrations;
- Step `07`–`09` scientific/statistical algorithms remain unchanged until
  inspected remote baseline evidence and separate authorization exist;
- `refactor-99-final-audit` classifies every finding and closes the local
  program without beginning cluster work.

### Report exports

Extend the report renderer with explicit `html`, `pdf`, and `all` formats,
defaulting to `all`. Publish an all-or-none bundle containing HTML, PDF,
deterministic summary TSV, and a report receipt published last.

Use canonical run-summary `1.1.0`, the existing report-receipt `1.1.0`
contract, pinned Quarto with bundled Typst, and an explicitly pinned
pure-Python PDF reader. Preserve the existing HTML path and safely handle a
valid HTML-only predecessor.

Validate PDF signatures, EOF, extractable text, page order, and the applicable
banner on every page. Preserve explicit-input-only behavior, owned locks,
staging, stable input rechecks, no-clobber rules, rollback, cleanup, and
recovery evidence. Rendering must not install software, invoke analysis
engines, discover inputs, or promote state.

Test incomplete, failed, missing, exploratory, empty-candidate, orientation,
strand, truncation, limitation, reserved-state, mutation, determinism,
accessibility, isolation, lock, signal, cleanup, and rollback cases without
regressing HTML behavior.

### Populated demo report

Provide `make demo-report` as a local, repeatable demonstration that requires
the already restored pinned Quarto and report Python environment and never
installs dependencies. Build one complete synthetic run with 81 artifacts,
15 expected scopes, an exploratory Step `09c` review, and all 11 supported
approved report-table roles. Run the renderer dry-run before execute and
publish HTML, PDF, summary TSV, and receipt under the ignored
`results/demo-report/` root.

Place scientific status, CMH-ranked candidates, adjudication, and limitations
in the initially open Overview category. Group remaining HTML material into
broad script-free native categories, bound the reading width, and keep wide
tables in local keyboard-focusable scroll regions. Preserve the linear PDF
projection and render candidate evidence in compact readable records. Retain
the explicit exploratory banner and never describe the fixture as production,
runtime, cluster, completed production review, or biological evidence.

Richer tab semantics, responsive/print behavior, and expanded interaction
coverage remain deferred until separately reviewed.

### Foundation packages

`post09-runtime-preflight` publishes read-only explicit-profile tool,
namespace, hash-utility, and visibility checks. It never installs software or
claims runtime proof merely because preflight passed.

`post09-reference-provenance` explicitly inventories FASTA, FAI, DICT, GTF,
BED, STAR index, hashes, annotation provenance, and contig agreement. It
reports inconsistencies but never repairs references.

`post09-storage-inventory-retention` records storage roots, sizes, capacity or
quota evidence, and an approved retention-policy TSV. It never deletes,
moves, compresses, or cleans data.

### Per-step validation reports

Each validator is dry-run-first, explicit-input-only, and publishes:

```text
results/qc/validation/<step>/<scope>.validation.tsv
```

with:

```text
step_id
scope_id
check_id
status
observed
expected
detail
```

Each package adds its read-only artifact adapter and an end-to-end fixture
showing the status in the run summary and consolidated HTML/PDF report. Do not
introduce a generic dispatcher or job array.

Checks cover:

- `00a`: index/source identity, contigs, and `sjdbOverhang`;
- `00b`: BED12 structure, sorting, blocks, and GTF agreement;
- `00c`: FASTA/FAI/DICT identity and contig agreement;
- `01`: STAR outputs, logs, BAM, and mapping summary;
- `02`: BAM/BAI, sorting, read groups, and alignment RG tags;
- `02b`: quickcheck and flagstat;
- `03`: RSeQC structure and paired-orientation fractions;
- `04`: BAM/BAI/metrics, sorting, RG preservation, and duplication metrics;
- `05`: parameterized existing output validation;
- `06`: orientation outputs and count arithmetic;
- `07`: receipts, VCF structure, selectors, hashes, order, and counts;
- `08`: three-output transaction, schemas, hashes, ordering, uniqueness, counts;
- `09`: four exact TSV headers; analysis-bound basenames; one shared native
  output parent; six distinct physical outputs; explicit analysis/cohort and
  provisional-policy identity; complete ordered Step `08` candidate universe;
  count-derived target/test/call, depth, AF, and enabled-background semantics;
  type/range validation of reported CMH fields; global BH recomputation from
  the reported p-values; exact significant subset; summary/provenance
  reconciliation; canonical mutation spectrum; and PDF structure. Independent
  CMH statistic, p-value, odds-ratio, and estimability recomputation from DP/AD
  counts is a critical audited gap.

## Deferred remote lineage

Only after new user direction and completion of the local sequence:

```text
refactor-99-final-audit
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Remote promotion is upstream-sequential. Each validation branch inspects
evidence, regenerates the structured summary and reports, performs a separate
docpatch, and reaches a clean pushed gate before the next branch.

## Scientific exit boundary

Mechanical orientation, annotation provenance, statistical policy,
replicate/sensitivity evidence, candidate adjudication, and limitations require
explicit review. `science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
policy defines and unlocks its stricter exits.
