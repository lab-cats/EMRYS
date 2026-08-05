# MIG-04F — Converge validation-roster agreement under final contract-integration owner

## Objective

Move the validation-roster suite and expectation helper to the exact permanent
contract-integration owner fixed by `SOURCE_TOPOLOGY.md`, and cut over all
fourteen repository-owned exact-file consumers without changing any roster,
oracle, report, adapter, or non-path behavior.

## Why this exists

The independent contract goldens are final through `MIG-04E`. The remaining
cross-owner contract-test pair has a separate suite/helper boundary and
fourteen exact-file consumers. This card moves only that validation-roster
owner so the repository continues to execute one bounded JIT owner at a time.

## Fixed decisions

- Move `tests/test_validation_check_rosters.py` and
  `tests/validation_roster_expectations.py` directly into
  `tests/contract_integration/validation_rosters/` at one level.
- Use one Git-preserving direct cutover. Change only the moved suite's
  repository-root anchor from `parents[1]` to `parents[3]`; keep its adjacent
  `validation_roster_expectations` import unchanged.
- Change only the `ROSTER_ORACLE` path literal in the fourteen reviewed
  consumer suites so each directly loads the final helper. Preserve every
  private module name, loader, import, case, assertion, and non-path byte.
  The exact consumers are:
  - `tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py`;
  - `tests/evidence/collect_RSeQC_paired_orientation_evidence/test_validate_step_03_rseqc_orientation.py`;
  - `tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py`;
  - `tests/reporting/test_artifact_adapters.py`;
  - `tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py`;
  - `tests/stages/construct_FASTA_sidecars/test_validate_step_00c_reference_sidecars.py`;
  - `tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py`;
  - `tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py`;
  - `tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py`;
  - `tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_validate_step_07_mpileup_outputs.py`;
  - `tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py`;
  - `tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py`;
  - `tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py`;
  - `tests/stages/split_N_cigar_reads_with_GATK/test_validate_step_05_split_ncigar.py`.
- Keep the helper byte-identical at mode `0644`. Preserve all thirteen ordered
  step rosters and all `67` ordered step-scoped roster entries.
- Preserve characterized limitations without approving or repairing them:
  shared report validation accepts exact-ID reordering; the reporting adapter
  accepts reordered and wrong-but-unique IDs; and the suite's legacy-root glob
  cannot discover an added final-owner validator.
- Add no package marker, import re-export, wrapper, compatibility copy,
  symlink, descriptor, installation surface, `PYTHONPATH`, or `sys.path`
  mutation. The two old root paths must be absent.
- Historical completed cards and dated audit records retain their
  time-specific paths.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal MIG-04E documentation close
  `26daa84ca8b52e7b8fc36c38d83921f6f983264f`.
- Reverify the exact two-file owner roster, fourteen exact-file consumers,
  recursive discovery, sibling-import behavior, current documentation links,
  final direct-root layout, modes, sizes, hashes, and absence of an external or
  unmovable caller.
- Freeze exact collection and results from repository root and an unrelated
  working directory before movement.

## Required context

- `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, completed `PLAN-03A` and
  `MIG-04E`, the suite/helper and fourteen consumers, current test/coverage
  policy, and current operational routes only.

## Questions owned by this card

- None.

## In scope

- The two Git-preserving moves; one suite-root repair; fourteen exact caller
  path cutovers; exact helper, mode, collection, root/arbitrary-CWD, focused,
  complete-coverage, and old-path parity checks; and impact-directed
  documentation/lifecycle close.

## Out of scope

- Any roster, check ID/order, report schema, status, validator, adapter,
  artifact, scientific-evidence, or production behavior change; any defect
  repair; new package or compatibility surface; legacy-test review; final
  audit; scheduler, ingestion, orchestration/profile, runtime execution,
  cluster, production, scientific-review, or biological work.

## Deliverables

- One final validation-rosters owner containing the direct suite and
  byte-identical helper, with all fourteen repository-owned callers cut over
  directly and no legacy or compatibility path.

## Acceptance evidence

- The exact `105` suite tests pass before and after from repository root and an
  unrelated working directory; normalized node IDs differ only by the
  approved path prefix.
- The complete fifteen-file focused closure retains the frozen `369` passing
  tests and equivalent normalized collection.
- Both moved files retain mode `0644`. The helper retains size `2,957` bytes
  and SHA-256
  `d44e6a0e3066d0c8e79db9c4392f157c3a570f0221d303bc9701637a6e8d2f1e`.
  A normalized executable diff contains only the approved suite root anchor
  and fourteen `ROSTER_ORACLE` path literals.
- Static validation, all shell contracts, complete undeselected Python
  coverage, documentation validation, semantic diff review, and exact live
  old-path searches pass at the final state.
- Production coverage remains exact across the same `36` files at
  `10592/12491` lines and `3789/5048` branches, rates `0.847971` and `0.750594`,
  with no baseline promotion or measured-file identity change.
- Exact searches prove one final two-file owner, fourteen final-path consumers,
  no old executable path, and no package marker, wrapper, copy, symlink,
  re-export, descriptor, or path-environment mutation.
- Evidence remains local synthetic-characterization and relocation parity
  only. It is not runtime, cluster, production, scientific-review, or
  biological-readiness evidence.

## Canonical documentation updates

- Functional-owner inventory and residual counts, source-topology implemented
  state, validation-roster commands/links in `TEST_BASELINE.md` and seven owner
  contracts, `PIPELINE_PLAN.md`, `HANDOFF.md`, lifecycle routes,
  documentation ownership, and this card.

## Escalation conditions

- Stop for adjacent-import failure; either moved file's mode drift; helper
  byte/oracle drift; any roster,
  check-ID/order, report, adapter, loader, test-count, collection, or
  production-coverage change; an external/unmovable or unknown caller; any
  compatibility/package/path-environment need; or scope into legacy review,
  final audit, scheduler, ingestion, orchestration/profile, runtime execution,
  cluster, scientific-review, or biological work.

## Completion record

Selected from clean, published, live-remote-equal MIG-04E documentation close
`26daa84ca8b52e7b8fc36c38d83921f6f983264f`. Three bounded read-only audits
found exactly two owned mode-`0644` files, fourteen repository-owned exact-file
consumers, recursive pytest discovery, working default-prepend sibling import,
and no external or unmovable caller. The suite is `190` lines, `5,842` bytes,
SHA-256
`cb04e284fc1871fcbcfffa212bd15be4a5f027cbedf3d7b3e00f79debe2ddf70`;
the helper is `114` lines, `2,957` bytes, SHA-256
`d44e6a0e3066d0c8e79db9c4392f157c3a570f0221d303bc9701637a6e8d2f1e`.
The exact `105` suite tests passed from repository root and unrelated working
directory `/private/tmp` in `0.09s` each, with identical normalized collection
hash `6d8f586a5762a834a1c099006f32eae30c385abe885fffe0e91a1656b3b6c5a5`.
The complete suite-plus-fourteen-consumer closure passed `369` tests in
`56.72s`; its pre-move collection hash is
`b7a5b54d8cafa125a09335a6f728f39c0e1a473670e83f74da8da9227a182528`.
The earlier cached `385` estimate was not used. Executable/test work has not
begun.
