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
| `codex/doc-cons-08c-compress-operational-guidance` | Indexed exact-command and diagnostic owners, contract crosswalk, and no-loss inline-program dispositions; see completed [`DOC-CONS-08C`](../tasks/COMPLETED/DOC-CONS-08C-compress-operational-guidance.md) | separately approved local-only documentation exception complete and intentionally unpushed; duplicated commands and stage semantics now route to one owner while recovery and scientific-review meaning remain intact, and no executable, configuration, generation, schema, fixture, report-template, dependency, source-layout, public-interface, scientific-policy, or test-harness behavior changed |
| `codex/doc-cons-08d-establish-dated-documentation-history` | Shallow immutable audit/testing history plus concise current audit and baseline routes; see completed [`DOC-CONS-08D`](../tasks/COMPLETED/DOC-CONS-08D-establish-dated-documentation-history.md) | separately approved local-only documentation exception complete and intentionally unpushed; exact dated evidence and source provenance now have indexed owners while active recheck, coverage-policy, evidence-vocabulary, and risk routes remain current, and no executable, configuration, generation, schema, fixture, report-template, dependency, source-layout, public-interface, scientific-policy, or test-harness behavior changed |
| `codex/reconciliation-consolidated-01-integration` | Direct canonical recovery of reviewed proposal material from consolidated source `5a35a057cd9ca259f83ee1dde3116fee63928d72` onto parent `0fd6348e6cfe54457fef5f65f3468bea106e61f9` | documentation-only integration package; eight TODO cards and eight nonselectable UNREFINED proposals are preserved without selection, priority, implementation, or evidence promotion; all 80 fragment requests receive terminal commit-trailer dispositions, the fragment is absent from the final tree, and publication/upstream equality must be resolved from live Git |
| `codex/plan-02z-first-migration-readiness` | Rolling [`PLAN-02Z`](../tasks/COMPLETED/PLAN-02Z-integrate-future-task-sequence.md) checkpoint, tranche-specific reviews, and first migration-card readiness rooted at the verified integrated canonical tip | plan checkpoint `c45e748`, all three dedicated [`architecture`](../tasks/COMPLETED/REVIEW-ARCH-03A-review-validation-publication-migration.md), [`reliability`](../tasks/COMPLETED/REVIEW-REL-03A-review-validation-publication-migration.md), and [`usability`](../tasks/COMPLETED/REVIEW-UX-03A-review-validation-publication-migration.md) reviews, and the completed [`MIG-03A`](../tasks/COMPLETED/MIG-03A-extract-validation-report-library.md) task-specific plan remain the documentation-only readiness record; the branch is published/upstream-equal |
| `codex/mig-03a-extract-validation-report-library` | Physical migration campaign through completed [`MIG-03A`](../tasks/COMPLETED/MIG-03A-extract-validation-report-library.md)–[`MIG-03K`](../tasks/COMPLETED/MIG-03K-migrate-partition-bam-by-mechanical-read-orientation-owner.md), plus completed [`REVIEW-ARCH-03L`](../tasks/COMPLETED/REVIEW-ARCH-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md), [`REVIEW-REL-03L`](../tasks/COMPLETED/REVIEW-REL-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md), and [`REVIEW-UX-03L`](../tasks/COMPLETED/REVIEW-UX-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) | the first eleven units are complete through published documentation/lifecycle close `b73b12b`; the branch ends clean and published at usability completion `5a501df`, before MIG-03L execution. |
| `codex/mig-03l-generate-partitioned-cohort-mpileup-vcfs` | Fresh execution branch for active [`MIG-03L`](../tasks/IN_PROGRESS/MIG-03L-migrate-generate-partitioned-cohort-mpileup-vcfs-owner.md) | branched and published from clean/equal usability completion `5a501df`; MIG-03L alone is selected, its five ordered old-path test slices precede the atomic cutover, and Step `08` or later remains uncreated. |
| Conditional fragment/lifecycle infrastructure | Complete independent characterization of the extracted documentation validator, enforce the proven fragment contract, complete proposal/review-state validation support, then add logical epic indexes; see [`DOC-GATE-01`](../tasks/TODO/DOC-GATE-01-extract-documentation-validator.md), [`CONCURRENCY-03`](../tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md), [`TASK-LIFECYCLE-01`](../tasks/TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md), and [`TASK-EPIC-01`](../tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md) | future separately planned packages in dependency-valid order after the post-`PROGRAM-01` reassessment; actionable-card workflow remains directory-owned, authorized UNREFINED preservation is nonselectable, and the validator still rejects its nine current Markdown locations and lacks the card's independent invalid-state fixture coverage and separately approved Make exposure |
| `refactor-01c-validation-check-rosters` | Independent exact ordered check-roster characterization; see [`TEST-01C`](../tasks/COMPLETED/TEST-01C-characterize-validation-check-rosters.md) | implementation `8d58fc6` and separate docpatch complete locally; unpushed predecessor to completed `TEST-01D` |
| `refactor-01d-public-cli-contracts` | Complete public CLI/direct-CWD/exit characterization; see [`TEST-01D`](../tasks/COMPLETED/TEST-01D-characterize-public-cli-contracts.md) | implementation `a003065` and separate docpatch complete locally; unpushed predecessor to the approved `TEST-01E` descendant |
| `refactor-01e-slurm-contracts` | Every SLURM wrapper's mode/module/delegation/output/exit contract; see [`TEST-01E`](../tasks/COMPLETED/TEST-01E-characterize-slurm-wrapper-contracts.md) | implementation `9a4fb09` and separate docpatch complete locally; unpushed predecessor to completed `TEST-01F` |
| `refactor-01f-independent-goldens` | Independent critical serialized/state/evidence goldens; see [`TEST-01F`](../tasks/COMPLETED/TEST-01F-create-independent-contract-goldens.md) | implementation `dcb5dd4`, targeted shared-policy correction `1986898`, and separate docpatch complete locally; unpushed predecessor to completed `TEST-01Z` |
| `refactor-01z-test-sufficiency-gate` | Behavior-row classification, explicit readiness decision, and bounded Phase `0` evidence correction; see [`TEST-01Z`](../tasks/COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) | affirmative 88/88-row decision plus test-only corrections `0c64d1a`, `44d3255`, and `fd98244` complete, adversarially reviewed, pushed, and upstream-equal at `b2af738`; no closure cards or production behavior changes |
| `codex/log-01-characterize-current-output-reconciliation` | Current stdout, stderr, scheduler, Make, test, operational-check, durable-copy, and evidence-log inventory; see [`LOG-01`](../tasks/COMPLETED/LOG-01-characterize-current-output.md) | documentation-only characterization complete; every current surface has a normalized output profile and trace, candidate overclaims are corrected, and runtime output remains unchanged |
| `codex/log-02-define-logging-contract-reconciliation` | Public controls, streams, one-writer operation record, publication ordering, failure, security, retention, scheduler, evidence-role, scenario, and adoption contract; see [`LOG-02`](../tasks/COMPLETED/LOG-02-define-logging-contract.md) | documentation-only target contract complete; the rejected-ancestry candidate was evidence only, current output/defaults remain unchanged, and no rollout card was created |
| Phase `02` rolling checkpoint | Minimum shared architecture and one evidence-supported tranche in [`PLAN-02Z`](../tasks/COMPLETED/PLAN-02Z-integrate-future-task-sequence.md) | complete as documentation-only planning; later intake, report, logging, documentation, size, and broad-library inputs remain frozen rather than becoming false blockers |
| First-tranche reviews | [`REVIEW-ARCH-03A`](../tasks/COMPLETED/REVIEW-ARCH-03A-review-validation-publication-migration.md) → [`REVIEW-REL-03A`](../tasks/COMPLETED/REVIEW-REL-03A-review-validation-publication-migration.md) → [`REVIEW-UX-03A`](../tasks/COMPLETED/REVIEW-UX-03A-review-validation-publication-migration.md) | all three dedicated read-only passes complete; no broad `REVIEW-*` completion is claimed |
| Phase `03` first bounded package | Extract the neutral validation-report protocol through [`MIG-03A`](../tasks/COMPLETED/MIG-03A-extract-validation-report-library.md) | complete with atomic executable/test checkpoint `9d93694` and documentation/lifecycle checkpoint `f3f2c2a`, both published/upstream-equal |
| Second JIT-tranche reviews | [`REVIEW-ARCH-03B`](../tasks/COMPLETED/REVIEW-ARCH-03B-review-construct-star-index-migration.md) → [`REVIEW-REL-03B`](../tasks/COMPLETED/REVIEW-REL-03B-review-construct-star-index-migration.md) → [`REVIEW-UX-03B`](../tasks/COMPLETED/REVIEW-UX-03B-review-construct-star-index-migration.md) | all three dedicated independent-in-time adversarial passes complete; the corrected card owns exact final commands, CWD distinctions, Make/static inclusion, and maintainer discoverability without a wrapper |
| Phase `03` second bounded package | Move `construct_STAR_index` through [`MIG-03B`](../tasks/COMPLETED/MIG-03B-migrate-construct-star-index-owner.md) | complete in published executable/test checkpoint `4f9c863`; the final owner contains the byte-identical job, path-adjusted validator, and mirrored tests, with explicit mixed-layout callers and no wrapper, duplicate, package, descriptor, or schema. Documentation/lifecycle closure is the commit containing this row. |
| Third JIT-tranche reviews | [`REVIEW-ARCH-03C`](../tasks/COMPLETED/REVIEW-ARCH-03C-review-convert-gtf-to-bed12-migration.md) → [`REVIEW-REL-03C`](../tasks/COMPLETED/REVIEW-REL-03C-review-convert-gtf-to-bed12-migration.md) → [`REVIEW-UX-03C`](../tasks/COMPLETED/REVIEW-UX-03C-review-convert-gtf-to-bed12-migration.md) | all three independent-in-time passes complete; the corrected card owns exact producer, validator, scheduler, Make, documentation, recovery, and provenance journeys, and independent authorship is not claimed |
| Phase `03` third bounded package | Move `convert_GTF_to_BED12` through [`MIG-03C`](../tasks/COMPLETED/MIG-03C-migrate-convert-gtf-to-bed12-owner.md) | complete in published executable/test checkpoint `e19f281`; the final owner contains the byte-identical producer, path-adjusted validator and job, and mirrored tests, with explicit mixed-layout callers and no wrapper, duplicate, package, descriptor, or schema. Documentation/lifecycle closure is the commit containing this row. |
| Fourth JIT-tranche reviews | [`REVIEW-ARCH-03D`](../tasks/COMPLETED/REVIEW-ARCH-03D-review-align-rna-reads-with-star-migration.md) → [`REVIEW-REL-03D`](../tasks/COMPLETED/REVIEW-REL-03D-review-align-rna-reads-with-star-migration.md) → [`REVIEW-UX-03D`](../tasks/COMPLETED/REVIEW-UX-03D-review-align-rna-reads-with-star-migration.md) | all three independent-in-time passes complete; the corrected card owns exact producer, validator, scheduler, Make, diagnostics, recovery, and provenance journeys, and independent authorship is not claimed |
| Phase `03` fourth bounded package | Move `align_RNA_reads_with_STAR` through [`MIG-03D`](../tasks/COMPLETED/MIG-03D-migrate-align-rna-reads-with-star-owner.md) | complete in published executable/test checkpoint `12f9be5`; the final owner contains the path-adjusted producer, validator, and job plus mirrored direct tests, with explicit mixed-layout callers and no wrapper, duplicate, package, descriptor, or schema. Documentation/lifecycle closure is the commit containing this row. |
| Fifth JIT-tranche reviews | [`REVIEW-ARCH-03E`](../tasks/COMPLETED/REVIEW-ARCH-03E-review-construct-fasta-sidecars-migration.md) → [`REVIEW-REL-03E`](../tasks/COMPLETED/REVIEW-REL-03E-review-construct-fasta-sidecars-migration.md) → [`REVIEW-UX-03E`](../tasks/COMPLETED/REVIEW-UX-03E-review-construct-fasta-sidecars-migration.md) | all three independent-in-time passes complete; the corrected card owns exact producer, validator, scheduler, recovery, and evidence journeys, and independent authorship is not claimed |
| Phase `03` fifth bounded package | Move `construct_FASTA_sidecars` through [`MIG-03E`](../tasks/COMPLETED/MIG-03E-migrate-construct-fasta-sidecars-owner.md) | complete in published executable/test checkpoint `cd3b547`; the final owner contains the path-adjusted producer, validator, and job plus mirrored direct tests, an explicit private bridge to the unchanged public reference-provenance owner, and no wrapper, duplicate, package, descriptor, or schema. Documentation/lifecycle closure is the commit containing this row. |
| Sixth JIT-tranche reviews | completed [`REVIEW-ARCH-03F`](../tasks/COMPLETED/REVIEW-ARCH-03F-review-construct-canonical-bam-migration.md) → completed [`REVIEW-REL-03F`](../tasks/COMPLETED/REVIEW-REL-03F-review-construct-canonical-bam-migration.md) → completed [`REVIEW-UX-03F`](../tasks/COMPLETED/REVIEW-UX-03F-review-construct-canonical-bam-migration.md) | all three independent-in-time passes are complete with exact helper, rollback-defect, command, scheduler, recovery, and evidence journeys; independent authorship is not claimed |
| Phase `03` sixth bounded package | Move `construct_canonical_BAM` through [`MIG-03F`](../tasks/COMPLETED/MIG-03F-migrate-construct-canonical-bam-owner.md) | complete in published helper checkpoint `4726ad1` and executable/test checkpoint `13a2748`; the final owner contains the path-adjusted producer, validator, mode-`0644` job, and mirrored direct tests, while neutral `bam_validation.py` removes the Step `04`/`05` peer-stage imports. Documentation/lifecycle closure is the commit containing this row. |
| Seventh JIT-tranche reviews | completed [`REVIEW-ARCH-03G`](../tasks/COMPLETED/REVIEW-ARCH-03G-review-collect-canonical-bam-qc-evidence-migration.md) → completed [`REVIEW-REL-03G`](../tasks/COMPLETED/REVIEW-REL-03G-review-collect-canonical-bam-qc-evidence-migration.md) → completed [`REVIEW-UX-03G`](../tasks/COMPLETED/REVIEW-UX-03G-review-collect-canonical-bam-qc-evidence-migration.md) | all three independent-in-time passes completed before selection with exact cutover, mixed-attempt, command, scheduler, recovery, provenance, and local-only evidence boundaries; independent authorship is not claimed |
| Phase `03` seventh bounded package | Move `collect_canonical_BAM_QC_evidence` through completed [`MIG-03G`](../tasks/COMPLETED/MIG-03G-migrate-collect-canonical-bam-qc-evidence-owner.md) | complete in published test-only baseline `0904faf` and executable/test checkpoint `2f186dd`; the final owner contains the path-adjusted producer, validator, mode-`0644` job, and mirrored direct tests with no wrapper, alias, package, descriptor, schema, or behavior redesign. Documentation/lifecycle closure is the commit containing this row. |
| Eighth JIT-tranche reviews | completed [`REVIEW-ARCH-03H`](../tasks/COMPLETED/REVIEW-ARCH-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) → completed [`REVIEW-REL-03H`](../tasks/COMPLETED/REVIEW-REL-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) → completed [`REVIEW-UX-03H`](../tasks/COMPLETED/REVIEW-UX-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) | all three independent-in-time passes completed before migration selection with exact cutover, direct-final/stale-output, command, scheduler, recovery, provenance, and mechanical-orientation evidence boundaries; independent authorship is not claimed |
| Phase `03` eighth bounded package | Move `collect_RSeQC_paired_orientation_evidence` through completed [`MIG-03H`](../tasks/COMPLETED/MIG-03H-migrate-collect-rseqc-paired-orientation-evidence-owner.md) | complete in published test-only baseline `88f4994` and executable/test checkpoint `24ed9b1`; the final owner contains the path-adjusted producer, validator, mode-`0644` job, and mirrored direct tests with no wrapper, alias, package, descriptor, schema, transaction, or behavior redesign. Documentation/lifecycle closure is the commit containing this row. |
| Ninth JIT-tranche reviews | completed [`REVIEW-ARCH-03I`](../tasks/COMPLETED/REVIEW-ARCH-03I-review-mark-bam-duplicates-with-picard-migration.md) → completed [`REVIEW-REL-03I`](../tasks/COMPLETED/REVIEW-REL-03I-review-mark-bam-duplicates-with-picard-migration.md) → completed [`REVIEW-UX-03I`](../tasks/COMPLETED/REVIEW-UX-03I-review-mark-bam-duplicates-with-picard-migration.md) | all three read-only independent-in-time passes completed before migration selection with exact cutover, residue/parity/scheduler, command, diagnostics, preservation, provenance, evidence-ceiling, and rollback boundaries; independent authorship is not claimed |
| Phase `03` ninth bounded package | Move `mark_BAM_duplicates_with_Picard` through completed [`MIG-03I`](../tasks/COMPLETED/MIG-03I-migrate-mark-bam-duplicates-with-picard-owner.md) | complete in published producer `de52e93`, validator `3d73d52`, and scheduler `3e805ac` test baselines plus executable/test checkpoint `803fcc4`; the final owner contains the path-adjusted producer, validator, mode-`0644` job, and mirrored direct tests with no wrapper, alias, package, descriptor, schema, transaction, receipt, recovery marker, or behavior redesign. Documentation/lifecycle closure is the commit containing this row. |
| Tenth JIT-tranche reviews | completed [`REVIEW-ARCH-03J`](../tasks/COMPLETED/REVIEW-ARCH-03J-review-split-n-cigar-reads-with-gatk-migration.md) → completed [`REVIEW-REL-03J`](../tasks/COMPLETED/REVIEW-REL-03J-review-split-n-cigar-reads-with-gatk-migration.md) → completed [`REVIEW-UX-03J`](../tasks/COMPLETED/REVIEW-UX-03J-review-split-n-cigar-reads-with-gatk-migration.md) | all three read-only independent-in-time passes completed before migration selection with exact cutover, fault/parity/scheduler, final-command, recovery, provenance, evidence-ceiling, and rollback boundaries; independent authorship is not claimed. |
| Phase `03` tenth bounded package | Move `split_N_cigar_reads_with_GATK` through completed [`MIG-03J`](../tasks/COMPLETED/MIG-03J-migrate-split-n-cigar-reads-with-gatk-owner.md) | complete in published transaction `42bf851`, admission/signal `3913215`, validator `8eb3a0b`, and scheduler `ec240ae` test baselines plus executable/test checkpoint `ef4cad7`; the final owner contains the path-adjusted producer, validator, mode-`0644` job, and mirrored direct tests with exact neutral/report/reference bridges and no wrapper, alias, package, descriptor, schema, transaction, receipt, recovery marker, or behavior redesign. Documentation/lifecycle closure is the commit containing this row. |
| Eleventh JIT-tranche reviews | completed [`REVIEW-ARCH-03K`](../tasks/COMPLETED/REVIEW-ARCH-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) → completed [`REVIEW-REL-03K`](../tasks/COMPLETED/REVIEW-REL-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) → completed [`REVIEW-UX-03K`](../tasks/COMPLETED/REVIEW-UX-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) | all three read-only independent-in-time passes completed before migration selection with exact cutover, child/count/transaction/collision/scheduler oracles, final-command, recovery, provenance, evidence-ceiling, and rollback boundaries; independent authorship is not claimed. |
| Phase `03` eleventh bounded package | Move `partition_BAM_by_mechanical_read_orientation` through completed [`MIG-03K`](../tasks/COMPLETED/MIG-03K-migrate-partition-bam-by-mechanical-read-orientation-owner.md) | complete in published child/count `3ae6e3e`, transaction `dafcd18`, stability/collision `66e41fe`, validator `1332529`, and scheduler `e871d5c` test baselines plus executable/test checkpoint `1d5b76a`; the final owner contains the path-adjusted producer, validator, mode-`0755` job, and mirrored direct tests with an exact neutral-report bridge and no wrapper, alias, package, descriptor, schema, transaction, receipt, recovery marker, or behavior redesign. Documentation/lifecycle closure is the commit containing this row. |
| Twelfth JIT-tranche reviews | completed [`REVIEW-ARCH-03L`](../tasks/COMPLETED/REVIEW-ARCH-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) → completed [`REVIEW-REL-03L`](../tasks/COMPLETED/REVIEW-REL-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) → completed [`REVIEW-UX-03L`](../tasks/COMPLETED/REVIEW-UX-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) | all three read-only committed-time passes completed before migration selection with exact cutover, pipeline/transaction/provenance/validator/scheduler oracles, final-command, dry-run, recovery, provenance, evidence-ceiling, and rollback boundaries; independent authorship is not claimed. |
| Phase `03` twelfth bounded package | Active move of `generate_partitioned_cohort_mpileup_VCFs` through [`MIG-03L`](../tasks/IN_PROGRESS/MIG-03L-migrate-generate-partitioned-cohort-mpileup-vcfs-owner.md) | selected alone on fresh published branch `codex/mig-03l-generate-partitioned-cohort-mpileup-vcfs`; five ordered old-path test-only checkpoints precede one atomic five-move/nine-update cutover, one complete computational card-boundary gate, and one separate documentation/lifecycle close. |
| `refactor-99-final-audit` | Final finding/decision/card disposition, compatibility comparison, measured validation, documentation audit, and handoff; see [`AUDIT-99`](../tasks/TODO/AUDIT-99-final-refactor-and-documentation-audit.md) | future final local gate; workflow status is the linked card's directory |

When reporting planning is explicitly reactivated, readiness order is corrected
and tested [`RPT-01`](../tasks/TODO/RPT-01-characterize-comprehensive-report.md),
then corrected and independently reviewed
[`RPT-02`](../tasks/TODO/RPT-02-define-science-report-contract.md). The latter
must assign one normalized schema owner for experiment, reference, locus,
run/attempt, source-hash, and evidence-state inputs. Renderer relocation through
`RPT-05A` and decomposition through `RPT-05B` precede growth of the legacy
modules; `RPT-03`, `RPT-04`, and `RPT-06` then own projection, science layout,
and convergence/default activation. This is readiness order, not selection or
technological-blocker metadata. Current hostile-PDF terminology/markup,
publication-transition, identity, and SVG-accessibility corrections remain
independently selectable repairs. `RPT-META-02A`, `RPT-PDF-04B`, and
`RPT-PUB-05C` remain only proposed owner identities until explicitly
classified; this plan does not create or combine them.

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
are complete. The user separately selected and completed `DOC-IA-01` and
`DOC-CONS-08A` through `DOC-CONS-08D` as local-only documentation exceptions;
those completions do not select `DOC-CONS-08E` through `DOC-CONS-08H` or
change ordinary runway order. The separately authorized consolidated-recovery
integration preserves recovered cards, proposals, decisions, and deferred
decision points without selecting them. `PLAN-02Z` is complete and defines
only `MIG-03A` and its tranche-specific review chain. That checkpoint selected
no review or migration; all three dedicated reviews later completed, and
`MIG-03A`, `MIG-03B`, and `MIG-03C` are complete on the one physical-migration
campaign branch. `MIG-03C` documentation/lifecycle close `f9d6381` and the
`MIG-03D` definition checkpoint `5ef6c6a` and architecture selection checkpoint
`8fd0063`, architecture completion checkpoint `cd3f3d4`, and reliability
selection checkpoint `b961274` are published and upstream-equal.
`REVIEW-ARCH-03D` and `REVIEW-REL-03D` are complete and usability selection
checkpoint `be9e459`, usability completion checkpoint `7d31459`, and migration
selection checkpoint `d6abed1` are published and upstream-equal. All three
reviews are complete, and `MIG-03D` completed its exact fourteen-file cutover
in published executable/test checkpoint `12f9be5` and documentation close
`5259acb`. `MIG-03E` definition checkpoint `3c6aaf0`, architecture selection
checkpoint `79af085`, and architecture completion checkpoint `494889f` are
published and equal. Reliability selection checkpoint `e39f4b2` is also
published and equal, `REVIEW-REL-03E` is complete at `522a4b4`, and usability
selection checkpoint `4750161` and completion checkpoint `9ae3b12` are published
and equal. All three `03E` reviews are complete, and migration selection
checkpoint `177a912` is published and equal. The exact write set and old-path
baseline tranche are frozen in published and equal plan checkpoint `d7c29ad`
and baseline checkpoint `9850a8d`. `MIG-03E` completed its exact fourteen-file
cutover and executable acceptance in published checkpoint `cd3b547` and
documentation close `fa79883`. `MIG-03F` and its three review cards are defined
at published checkpoint `ee25492`; architecture selection `bc2112c` and
completion `c429d8d` and reliability selection `a49e45c` are published.
All three `03F` reviews are complete and migration selection `679aba9` is
published and equal. The exact helper/owner write sets and two old-path baseline
slices are frozen at published plan `d8638a0`, helper baseline `9a2517b`, and
native baseline `6a716b1`. The neutral-helper extraction is published at
`4726ad1`; the final owner cutover and executable acceptance are published at
`13a2748`; documentation/lifecycle close `543eb8f` is published and equal. The
live DAG then exposed three eligible owners. `MIG-03G` and its three reviews are
defined at published checkpoint `417a2a5`; architecture selection `450e38c` is
published; architecture completion `06a69c7` and reliability selection
`9b4b5a8` are published; reliability completion `56bac42` and usability
selection `5a491eb` and completion `7b86a5e` are published. `MIG-03G` alone is
selected at published checkpoint `18703e1`, its test-only baseline is published
at `0904faf`, and its executable/test cutover is published at `2f186dd`.
`MIG-03G` is complete in the commit containing this paragraph. Its aggregate
gate reached the expected documentation-only ceiling rather than green; the
close repairs ten migration links while nine inherited `UNREFINED` findings
remain. The live DAG then leaves Step `03` and Step `04` eligible. The commit
containing this paragraph defines only first-listed
`collect_RSeQC_paired_orientation_evidence` as `MIG-03H` plus its three
sequential reviews. Architecture selection `12eca35` is published and
`REVIEW-ARCH-03H` completes at published checkpoint `350223f`, and reliability
selection `13755af` is published. `REVIEW-REL-03H` completes at published
checkpoint `1d1de19`; `REVIEW-UX-03H` is complete at published checkpoint
`76923e1`. `MIG-03H` alone was selected at published checkpoint `13b8a7e`, its
task-specific plan was published at `3388466`, its exact test-only baseline at
`88f4994`, and its five-move/nine-update executable/test cutover at `24ed9b1`.
Focused final-path wiring passed `143` assertions, and serial coverage passed
`1,120` tests with `17` skips plus one intentional documentation-assertion
deselection. The aggregate gate was not fully green: its sole Python failure
listed ten deliberately deferred migration links plus the nine inherited
`UNREFINED` locations after all other lanes passed. This close repairs the ten
links while retaining the inherited nonpassing nine. `MIG-03H` is complete in
the commit containing this paragraph. No later owner or review card is
selected; refresh the live DAG before defining the next unit.
The published and equal `MIG-03H` documentation close is `ef990c8`. A fresh
edge check left only `mark_BAM_duplicates_with_Picard` eligible because its
sole direct predecessor, `construct_canonical_BAM`, was migrated; Step `05`
still required Step `04`. `REVIEW-ARCH-03I`, `REVIEW-REL-03I`, and
`REVIEW-UX-03I` completed at published checkpoints `403fdf5`, `fae9bae`, and
`beee633`. `MIG-03I` selection `0c88390` and task-specific plan `44e1db4`
followed. Its producer, validator, and scheduler test-only baselines are
published at `de52e93`, `3d73d52`, and `3e805ac`; exact five-move/ten-update
executable/test cutover `803fcc4` is published and equal.

The final direct shell suite, `9` validator tests, `18` selected scheduler
tests with `108` unrelated cases deselected, and `68` focused integration
assertions passed. Coverage passed `1,134` tests with `17` skips plus one
intentional documentation-assertion deselection; the moved validator measured
`146/155` lines and `35/42` branches, while the global surface measured
`9510/11677` lines and `3333/4756` branches. Every non-target row remained
exact and the standalone comparison passed.

The aggregate gate was not fully green. Its first sandboxed attempt passed
static preflight before guarded R stopped on Bioconductor DNS and retained the
inherited malformed `macos` warning. The exact network-enabled rerun changed no
dependency; static, shell, guarded-R, and report-runtime lanes passed. Python
ran `1,134` passes and `17` skips before its sole documentation assertion
listed exactly ten deliberately deferred Step `04` links plus nine inherited
`UNREFINED` locations. The published `MIG-03I` close `c6814e0` repairs the ten
migration links while the inherited nine remain nonpassing. A fresh edge check
then left only `split_N_cigar_reads_with_GATK` eligible because both direct
predecessors are migrated. Definition checkpoint `f88f56e` created only
selected [`MIG-03J`](../tasks/COMPLETED/MIG-03J-migrate-split-n-cigar-reads-with-gatk-owner.md)
and sequential [`REVIEW-ARCH-03J`](../tasks/COMPLETED/REVIEW-ARCH-03J-review-split-n-cigar-reads-with-gatk-migration.md)
→ [`REVIEW-REL-03J`](../tasks/COMPLETED/REVIEW-REL-03J-review-split-n-cigar-reads-with-gatk-migration.md)
→ [`REVIEW-UX-03J`](../tasks/COMPLETED/REVIEW-UX-03J-review-split-n-cigar-reads-with-gatk-migration.md).
Architecture is complete at published checkpoint `e40fb3b` with the
exact loader, five-move/ten-update ceiling, projected hashes, test ownership,
artifact/coverage, and rollback boundary recorded. Reliability is complete at
`daa7ec4`, usability at `0328fbe`, selection at `5415538`, and task-specific
planning at `d9bdf21`. Published test-only baselines are `42bf851`, `3913215`,
`8eb3a0b`, and `ec240ae`; executable/test checkpoint `ef4cad7` moved exactly
five files and updated ten reviewed integration owners.

The final shell suite, `14` validator tests, `24` selected scheduler tests with
`118` unrelated cases deselected, and `392` focused integration tests passed.
Coverage passed `1,159` tests with `17` skips plus one intentional
documentation-assertion deselection; the moved validator measured `178/192`
lines and `45/54` branches, while the global surface measured `9550/11720`
lines and `3347/4772` branches. Every non-target row remained exact and the
standalone comparison passed.

The aggregate gate was not fully green. Static preflight, shell contracts,
guarded R, and report runtime passed. Python ran `1,159` passes and `17` skips
before its sole documentation assertion listed exactly ten deliberately
deferred Step `05` links plus nine inherited `UNREFINED` locations. This
documentation close repairs the ten links while the inherited nine remain
nonpassing. The preserved rollback-failure, admitted-input-mutation, missing-
receipt, output-directory lock, Bash `3.2`, tool-probe, dry-run-log, and stale-
pair defects are not approved. Historical cluster observations remain
historical; MIG-03J created no real GATK, Java, samtools, scheduler, cluster,
production, scientific-review, or biological evidence.

Published documentation close `db60dfa` was clean and equal across local
`HEAD`, configured upstream, and the live remote before the next DAG refresh.
That refresh left only `partition_BAM_by_mechanical_read_orientation`
eligible because its sole direct predecessor was migrated. Definition
checkpoint `0bc12ac` created only
[`MIG-03K`](../tasks/COMPLETED/MIG-03K-migrate-partition-bam-by-mechanical-read-orientation-owner.md)
and sequential
[completed `REVIEW-ARCH-03K`](../tasks/COMPLETED/REVIEW-ARCH-03K-review-partition-bam-by-mechanical-read-orientation-migration.md)
→ [completed `REVIEW-REL-03K`](../tasks/COMPLETED/REVIEW-REL-03K-review-partition-bam-by-mechanical-read-orientation-migration.md)
→ [completed `REVIEW-UX-03K`](../tasks/COMPLETED/REVIEW-UX-03K-review-partition-bam-by-mechanical-read-orientation-migration.md).
Architecture completed at `2452332`, reliability at `1d5406a`, usability at
`5653ce2`, selection at `cd5d8e9`, and task-specific planning in that selected
card. Published test-only baselines are `3ae6e3e`, `dafcd18`, `66e41fe`,
`1332529`, and `e871d5c`; executable/test checkpoint `1d5b76a` moved exactly
five files and updated nine reviewed integration owners.

The final shell suite, `15` validator tests, `16` selected scheduler tests with
`134` unrelated cases deselected, and `432` focused integration tests passed.
Coverage passed `1,177` tests with `17` skips plus one intentional
documentation-assertion deselection; the moved validator measured `108/119`
lines and `24/30` branches, while the global surface measured `9551/11720`
lines and `3348/4772` branches. Every non-target row remained exact and the
standalone comparison passed.

The aggregate gate was not fully green. Static preflight, shell contracts,
guarded R, and report runtime passed. Python ran `1,177` passes and `17` skips
before its sole documentation assertion listed exactly ten deliberately
deferred Step `06` links plus nine inherited `UNREFINED` locations. This
documentation close repairs the ten links while the inherited nine remain
nonpassing. The preserved flag/merged-count disagreement, admitted-input
mutation, best-effort restoration and erased recovery evidence, shared-QC
collision, missing receipt, validator exit-`0` failed rows, one-CPU/thread,
Bash `3.2`, tool-probe, dry-run-log, and stale-five-file defects are not
approved. Historical six-sample cluster observations remain historical;
MIG-03K created no real samtools, scheduler, cluster, production, scientific-
review, or biological evidence.

Published documentation close `b73b12b` was clean and equal across local
`HEAD`, configured upstream, and the live remote before the next DAG refresh.
That refresh leaves only `generate_partitioned_cohort_mpileup_VCFs` eligible:
all declared-sample Step `06` BAM/BAI pairs and the reference FAI direct
predecessors are migrated, while Step `08` still depends on Step `07`. The
definition checkpoint containing this plan created only
[`MIG-03L`](../tasks/IN_PROGRESS/MIG-03L-migrate-generate-partitioned-cohort-mpileup-vcfs-owner.md)
and sequential
[completed `REVIEW-ARCH-03L`](../tasks/COMPLETED/REVIEW-ARCH-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md)
→ [completed `REVIEW-REL-03L`](../tasks/COMPLETED/REVIEW-REL-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md)
→ [completed `REVIEW-UX-03L`](../tasks/COMPLETED/REVIEW-UX-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md).
Architecture is complete in the commit containing this plan with the exact
five-move/nine-update ceiling, modes, final roots, shared-config disposition,
projected native hashes, artifact/coverage boundary, and reverse rollback
recorded. Reliability is complete in the commit containing this plan with five
bounded old-path test-only checkpoints and exact defect-preservation oracles.
Usability is complete from published/equal selection `3ec8307` with final
commands, distinct dry-run effects, recovery preservation, non-calling
language, owner findability, evidence ceilings, and reverse rollback fixed.
Usability completion `5a501df` is published/equal on the prior campaign branch
and is also the clean published base of fresh branch
`codex/mig-03l-generate-partitioned-cohort-mpileup-vcfs`. MIG-03L alone is now
selected; no executable/test path changed or computational check ran at
selection, and Step `08` and every later owner/review card remain absent.
Unrelated packages remain preserved but dead/out of scope under the temporary boundary in
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
   may complete validator/transition support for the authorized nonselectable
   `UNREFINED` intake and implement `INTEGRATION_REVIEW`, and
   [`TASK-EPIC-01`](../tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md)
   may then add orthogonal logical epic indexes. `CONCURRENCY-03` and
   `TASK-LIFECYCLE-01` are independent after their own prerequisites; epic
   indexing follows the lifecycle package.
7. The separately authorized recovery integration materializes the reviewed
   researcher-path proposals without selecting or implementing them. Any later
   local-pilot card still requires its own task-specific planning and the
   applicable then-current infrastructure; `TASK-EPIC-01` is not a
   prerequisite unless later evidence establishes a genuine dependency.
8. [`TASK-REG-01`](../tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md)
   must precede or share the approved atomic cutover to permanent ID-only card
   paths and committed generated views. Include minimum `TASK-EPIC-01` support
   in that atom only if approved epic metadata is mandatory for every card;
   otherwise keep epic work downstream. This is migration readiness, not a
   technological blocker edge.
9. Completed
   [`DOC-IA-01`](../tasks/COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md)
   leads the Phase `02` documentation family and produced the no-loss bounded
   consolidation cards. Separately approved
   [`DOC-CONS-08A`](../tasks/COMPLETED/DOC-CONS-08A-slim-root-agent-router.md)
   and
   [`DOC-CONS-08B`](../tasks/COMPLETED/DOC-CONS-08B-compress-root-entry-and-priority-views.md)
   and
   [`DOC-CONS-08C`](../tasks/COMPLETED/DOC-CONS-08C-compress-operational-guidance.md)
   and
   [`DOC-CONS-08D`](../tasks/COMPLETED/DOC-CONS-08D-establish-dated-documentation-history.md)
   completed the root router, entry/priority, operational-guidance, and dated
   audit/testing-history compression; `DOC-CONS-08E` through `DOC-CONS-08H` remain unselected and
   require separate selection,
   task-specific planning, and approval.

Each remains separately planned and approved. If live technical evidence later
establishes a real blocker, record that evidence on the affected cards rather
than inferring it from this order.

### Recovered proposal families

The unselected local-pilot family has three parallel inputs:
[`SETUP-03A`](../tasks/TODO/SETUP-03A-implement-local-pilot-dependency-profile-and-doctor.md),
[`INTAKE-03A`](../tasks/TODO/INTAKE-03A-implement-yaml-tsv-run-lifecycle.md),
and [`PROFILE-03A`](../tasks/TODO/PROFILE-03A-materialize-local-pilot-workflow-profile.md).
Together they feed
[`CLI-03A`](../tasks/TODO/CLI-03A-implement-local-pilot-control-plane.md)
→ [`E2E-03A`](../tasks/TODO/E2E-03A-prove-fresh-clone-local-pilot.md)
→ [`ONBOARD-03A`](../tasks/TODO/ONBOARD-03A-publish-researcher-onboarding.md).
`INTAKE-03A` is separately blocked by the still-unavailable accepted design
from `INTAKE-02E`.
The arrows preserve reviewed interface/readiness order, not automatic
selection or newly invented blockers. SETUP owns local-environment readiness;
INTAKE owns admission/normalization while neutral schemas and orchestration
retain their cross-owner boundaries; PROFILE owns a non-executable projection
without taking semantic DAG identity; CLI remains thin over orchestration; E2E
owns clean-clone proof; and ONBOARD owns researcher guidance. This direct local
pilot excludes future analysis modules, public acquisition, installable
distribution, optional-analysis policy, and site/container profiles.

Recovered [`DOC-TASK-SCAN-01`](../tasks/TODO/DOC-TASK-SCAN-01-scan-documentation-for-task-intake.md)
and [`GATE-REC-01`](../tasks/TODO/GATE-REC-01-define-machine-readable-gates-and-validation-receipts.md)
are also unselected, separately bounded TODO proposals. `FUT-SITE-01` and
`FUT-SITE-02`, along with the other recovered
[`UNREFINED` proposals](../tasks/UNREFINED/), are discovery links only and do
not join this roadmap. None of these eight TODO cards joins or changes the
completed `PLAN-02Z` first tranche.

Documentation-package readiness remains parent-first: resolve legacy task-edge
semantics through `TASK-REG-01` or an explicit reviewed exception, correct and
review `DOC-REF-02`, then synthesize and review only `DOC-PIPE-04`-owned work on
that accepted parent. This is integration/readiness order, not a new blocker or
completion claim.

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
`DOC-CONS-08A` through `DOC-CONS-08D` children are complete on successive
local-only descendants as explicit documentation exceptions; the remaining
consolidation cards are not selected. `PLAN-02Z` completed on the verified
integration descendant only for the first `MIG-03A` tranche and its dedicated
review chain. After that unit, the user separately authorized the one-branch
physical-migration campaign to select and complete only one next unit at a
time; other candidate work remains frozen rather than becoming blocker
metadata.

Do not perform remote-runtime or cluster validation during this sequence. Git
publication and local/upstream/live-ref equality remain required campaign
checkpoints.

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

- [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) owns the current finding index and
  recheck triggers and links the immutable dated audit that owns the original
  evidence-ranked findings, test-first dispositions, and retained/deferred
  boundaries;
- [`TEST_BASELINE.md`](TEST_BASELINE.md) owns the current Python non-regression
  policy, evidence vocabulary, contract-risk checklist, and direct regression
  routes and links the immutable dated baseline that owns exact counts,
  matrices, and Phase `01` characterization evidence;
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
