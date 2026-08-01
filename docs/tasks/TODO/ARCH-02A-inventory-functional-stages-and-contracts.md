# ARCH-02A — Inventory functional stages and contracts

**JIT slice record**

- Slice 1 records historical Step `00a` under the working name
  `construct_STAR_index` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/construct_STAR_index/CONTRACT.md).
  The slice inventories current behavior and the shared-validator ownership
  leak without moving code or settling later naming, topology, extraction, or
  migration decisions.
- Slice 2 records historical Step `00b` under the working name
  `convert_GTF_to_BED12` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/convert_GTF_to_BED12/CONTRACT.md)
  and makes hard, operational, downstream, and parallel execution edges
  explicit in both recorded stage contracts. It does not convert historical
  numbering into orchestration or settle the future DAG.
- Slice 3 records historical Step `00c` under the working name
  `construct_FASTA_sidecars` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/construct_FASTA_sidecars/CONTRACT.md).
  It distinguishes materialization, parallel, and downstream prerequisites and
  preserves current publication and wrapper defects without changing behavior.
- Slice 4 records historical Step `01` under the working name
  `align_RNA_reads_with_STAR` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/align_RNA_reads_with_STAR/CONTRACT.md).
  It traces the paired-read/index inputs and Step `02` handoff while preserving
  current dry-run, publication, and validation boundaries.
- Slice 5 records historical Step `02` under the working name
  `construct_canonical_BAM` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/construct_canonical_BAM/CONTRACT.md).
  It records the canonical pair's fan-out and rollback contract while exposing
  producer/validator asymmetry and shared BAM-helper ownership.
- Slice 6 classifies historical Step `02b` as the evidence operation
  `collect_canonical_BAM_QC_evidence` in its colocated
  [`CONTRACT.md`](../../../src/norad/evidence/collect_canonical_BAM_QC_evidence/CONTRACT.md).
  It preserves the native evidence and failure semantics without treating QC
  text as a computational prerequisite or a peer transformation stage.
- Slice 7 classifies historical Step `03` as the scientific-evidence operation
  `collect_RSeQC_paired_orientation_evidence` in its colocated
  [`CONTRACT.md`](../../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/CONTRACT.md).
  It traces the converging BAM/BED12 prerequisites while keeping mechanical
  orientation evidence separate from biological strand, manifest policy, and
  the computational DAG.
- Slice 8 records historical Step `04` as `mark_BAM_duplicates_with_Picard` in
  its colocated
  [`CONTRACT.md`](../../../src/norad/stages/mark_BAM_duplicates_with_Picard/CONTRACT.md),
  including its Step `02` input, Step `05` handoff, final-path publication, and
  producer/validator ownership gaps.
- Slice 9 records historical Step `05` as `split_N_cigar_reads_with_GATK` in
  its colocated
  [`CONTRACT.md`](../../../src/norad/stages/split_N_cigar_reads_with_GATK/CONTRACT.md),
  including the Step `04`/`00c` convergence, Step `06` handoff, protected pair
  publication, and rollback-failure boundary.
- Slice 10 records historical Step `06` as
  `partition_BAM_by_mechanical_read_orientation` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/CONTRACT.md),
  preserving exact flag groups, the Step `07` cohort gate, five-output
  transaction, and biological-strand prohibition.
- Slice 11 records historical Step `07` as
  `generate_partitioned_cohort_mpileup_VCFs` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md),
  preserving manifest-ordered cohort pileups, selector and transaction
  boundaries, the Step `08` handoff, and incomplete-provenance limitations.
- Slice 12 records historical Step `08` as
  `preprocess_and_annotate_cohort_candidates` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md),
  preserving the complete Step `07` barrier, provisional orientation policy,
  three-table transaction, and Step `09` analysis handoff.
- Slice 13 records historical Step `09` as analysis operation
  `rank_cohort_candidates_with_paired_CMH` in its colocated
  [`CONTRACT.md`](../../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md),
  preserving explicit replicate pairing, paired CMH/BH policy, the six-output
  transaction, and the boundary between ranked candidates and review.

## Objective

Produce an implementation-backed inventory of functional stages, shared
domains, public entry points, and cross-stage contracts.

## Why this exists

Numeric names and flat `scripts/`/`jobs/` ownership obscure what each stage
does and where one stage's responsibility ends. A vertical target cannot be
designed safely from filenames alone.

## Fixed decisions

- Inventory behavior before choosing target names or moving files.
- Treat stages as future black boxes whose neighbors know only typed input and
  output contracts; do not infer a universal preprocessing trunk.
- Preserve current numeric identifiers as historical provenance until a
  [semantic map](../../design/DECISIONS.md#identify-stages-semantically-and-order-them-with-a-dag)
  is approved.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest sufficiency decision is affirmative.

## Completion unblocks

- [ARCH-02B](../TODO/ARCH-02B-define-semantic-stage-map.md) — Fully: semantic names can be derived from inspected responsibilities.
- [LIB-02F](../TODO/LIB-02F-define-shared-library-ownership.md) — Partially: shared-domain candidates also require the target topology.
- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Partially: size findings can be mapped to functional ownership.

## Prerequisites

- Refresh the live script, job, test, schema, config, report, and Make-target
  inventories.

## Required context

- Current `ARCHITECTURE.md` and `pipeline.mmd`, `REFACTOR_AUDIT.md`,
  `TEST_BASELINE.md`, all public entry points, their consumers, and directly
  associated tests/contracts.

## Questions owned by this card

- None.

## In scope

- Stage purposes, entry points, job boundaries, inputs, outputs, validators,
  contracts, consumers, shared domains, and observed dependency direction.
- Explicit classification of orchestration, scheduler, evidence, reporting,
  ingestion, and library responsibilities that are not stages.

## Out of scope

- Renaming, relocation, package creation, generic abstraction, or changing
  current step order and behavior.

## Deliverables

- A source-backed stage/domain inventory with unresolved ambiguities called out.
- Direct links from each row to implementation and protected tests.

## Acceptance evidence

- Every current public workflow entry point and validator maps exactly once to
  a functional owner or an explicitly justified cross-cutting domain.
- Inputs, outputs, upstream/downstream consumers, and contract ownership are
  traceable without relying on filename inference.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, `FUTURE_ARCHITECTURE.md` only if the target constraints
  need correction, `QUESTIONS.md`, and this card.

## Escalation conditions

- Stop if one file's mixed responsibilities cannot be assigned without making
  an implementation decision, or if scientific boundaries are ambiguous.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
