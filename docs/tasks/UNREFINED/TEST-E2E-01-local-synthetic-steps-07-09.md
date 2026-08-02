# TEST-E2E-01 — Prove local synthetic cohort-candidate integration

State: [`UNREFINED` proposal](README.md). No test, fixture, production code,
runtime command, or evidence state is changed by preserving it.

## Proposal

Add one small local synthetic integration path across
`generate_partitioned_cohort_mpileup_VCFs` receipts and VCFs,
`preprocess_and_annotate_cohort_candidates` outputs, and
`rank_cohort_candidates_with_paired_CMH` outputs. Their numeric `07`, `08`,
and `09` labels are historical aliases and provenance only.

## Why preserve it

Stage-local mocked and guarded-runtime fixtures do not by themselves prove that
the mpileup stage's manifest, receipt, output identity, ordering, and provenance
are carried through preprocessing and checked at the ranking boundary. That
seam may be valuable to characterize before structural migration.

## Settled boundaries

- Use tiny synthetic, non-sensitive inputs and producer-independent expected
  contracts; require no production FASTQ, BAM, VCF, results, or cluster run.
- Exercise public semantic-stage boundaries and provenance propagation without
  restructuring or approving scientific algorithms.
- Preserve dry-run and execute behavior, no-clobber rules,
  validation-before-publication, rollback, receipt-last publication, manifest
  identity, sample order, and evidence vocabulary.
- A pass would be local synthetic integration evidence only. It is not real-
  bcftools evidence unless a guarded real runtime is actually used, and it is
  never production, cluster, completed scientific-review, or biological
  evidence.

## Questions before refinement

- Can the smallest deterministic path use the mocked
  `generate_partitioned_cohort_mpileup_VCFs` tool boundary and guarded real-R
  preprocessing and ranking stages, or is an optional local real-bcftools lane
  needed?
- Which current fixtures can be composed without importing production
  expectations or duplicating a large fixture builder?
- Which hashes, receipts, counts, headers, ordering, status transitions, and
  failure cases define the smallest meaningful cross-stage contract?
- Does current test-sufficiency evidence justify promotion, deferral, or a
  differently bounded integration package?

## Refinement inputs

- [`STAGE_MAP.md`](../../../src/norad/contracts/STAGE_MAP.md) owns the semantic
  stage identities, artifact edges, and historical numeric aliases.
- Completed `TEST-01F` independent goldens and `TEST-01Z` sufficiency evidence
  are historical prerequisites and comparison context, not active blockers.
- `RA-025` remains a scientific-evidence boundary: this proposal cannot use a
  local synthetic seam to justify algorithm refactoring.

These are refinement inputs, not dependency relationships.

## Promotion conditions

- Reconcile this proposal against the current semantic-stage map, public
  contracts, tests, fixtures, local tool availability, independent-golden
  rules, and evidence boundary.
- Define the exact execution profile, deterministic fixture, failure matrix,
  and acceptance evidence.
- Convert it into a complete reviewed TODO card through an explicit
  integration-owner promotion before implementation.
