# Local-pilot orchestration readiness

This document is the canonical Campaign B owner-admission view for the local
CMH pilot defined by
[`ORCHESTRATION_CONTRACT.md`](ORCHESTRATION_CONTRACT.md). It records each
owner's orchestration disposition and the retained admission invariants for
the admitted fixed no-science local profile. It is not live runtime state, a
second DAG, roadmap authority, or
permission to change an owner.

Exact semantic edges remain in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md). Exact producer,
validator, transaction, defect, and recovery behavior remains in each linked
owner contract. Current blockers and evidence remain in
[`HANDOFF.md`](../operations/HANDOFF.md), and package order and acceptance
remain in [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md). Update a disposition here
only after its owner-local authority and current evidence record the accepted
proof; do not copy this B0 assessment into workflow rules as new behavior.

## Disposition vocabulary

| Disposition | Meaning |
| --- | --- |
| `ready` | Admitted to the fixed no-science local profile; the listed invariants remain mandatory for continued admission and reuse. |
| `harden` | A bounded owner change or explicit recovery/no-clobber contract is required before unattended profile execution. |
| `exclude` | The operation is intentionally outside the automatic version 1 profile. |

The generic semantic all-pass gate is required for every validator regardless
of disposition because current validators may publish failed rows with exit
zero.

## Owner matrix

| Owner and scope | Public producer / validator | Current admission state | Disposition | Retained admission invariant |
| --- | --- | --- | --- | --- |
| [`construct_STAR_index`](../../src/norad/stages/star_index/CONTRACT.md), one reference | Explicit local producer plus compatibility SLURM wrapper; grouped public validator | B1 added dry-run-first, declared-member, locked no-clobber publication | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`convert_GTF_to_BED12`](../../src/norad/stages/gtf_to_bed12/CONTRACT.md), one reference | Grouped `norad convert gtf-to-bed12`; grouped validator | B1 added explicit execute plus atomic no-replace publication | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`construct_FASTA_sidecars`](../../src/norad/stages/fasta_sidecars/CONTRACT.md), one reference | Public shell producer; grouped validator | B1 made controlled rollback fail closed and preserve ambiguous residue | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`align_RNA_reads_with_STAR`](../../src/norad/stages/star_alignment/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added explicit tool selection and a staged no-clobber transaction | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`construct_canonical_BAM`](../../src/norad/stages/canonical_bam/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and no-clobber admission to the existing transaction | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/canonical_bam_qc/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added explicit samtools selection and staged no-clobber pair publication | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/rseqc_orientation/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and staged no-clobber publication | `ready` | Pinned workflow dependency, validator all-pass, and verified-task binding remain required for continued rule admission and reuse |
| [`mark_BAM_duplicates_with_Picard`](../../src/norad/stages/duplicate_marking/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added explicit input/tool identity and staged no-clobber set publication | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_n_cigar/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and a sample-scoped no-clobber path | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/mechanical_orientation/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and no-clobber admission to the existing transaction | `ready` | Validator all-pass and verified-task binding remain required for continued rule admission and reuse |
| [`generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/partitioned_cohort_mpileup/CONTRACT.md), per cohort/partition | Public shell producer; grouped validator | B1 added no-clobber admission, pre-receipt final validation, and failed-restore preservation | `ready` | Full input/output binding, validator all-pass, and verified-task binding remain required for continued rule admission and reuse |
| [`preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/cohort_candidate_preprocessing/CONTRACT.md), one cohort | Public shell/R producer; grouped validator | B1 added no-clobber admission and failed-restore preservation | `ready` | Explicit locked `renv`, validator all-pass, and verified-task sibling binding remain required for continued rule admission and reuse |
| [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/paired_cmh_candidate_ranking/CONTRACT.md), one analysis | Public shell/R producer; grouped validator | No owner redesign is known; shared semantic-gate and resume proof remain | `ready` | Explicit locked `renv`, paired-strata admission, complete transaction, semantic all-pass, retained independent test oracle, and failure/resume proof |
| [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/scientific_review_package/CONTRACT.md), one review | Grouped public assembler; publisher performs its own validation | Requires explicit human/reviewer declarations and must not be fabricated by computational orchestration | `exclude` | Separately authorized post-run review only; automatic profile reports review evidence absent/incomplete |
| [Artifact index and run summary](../../src/norad/reporting/README.md), one run | Grouped public build routes | B4 schedules the deterministic projected inventory and re-admits both complete transactions through the direct reporting validator | `ready` | No-science fixed-profile proof exists; real owner artifacts and production evidence remain separate |
| [Jinja HTML report](../../src/norad/reporting/README.md), one run | Grouped public report builder | B4 schedules and semantically re-admits the HTML/TSV/v2 receipt transaction under distinct source-code and artifact roots | `ready` | No-science fixed-profile proof shows absent Step `09c` honestly; production reporting remains separate |

## Cross-cutting prerequisites

B2 satisfies prerequisites 1 and 2. B3 satisfies the fixed-profile/DAG,
closed-dispatch, verified-task, zero-retry local-executor, and no-science
reference/one-sample/cohort slice requirements. B4 satisfies the run-specific
inventory, reporting-tail, immutable attempt, aggregate
failure/interruption/between-task-resume, durable producer-entry, and
derived-inspection requirements
for the no-science test-double profile. B5 adds the exact runtime-profile-
bound public command projection and lock-before-attempt materialization while
retaining every disposition in this table. Explicit `renv` launch authority and
exact existing project-library selection are now admitted by the guarded local
runtime boundary; real-tool behavior remains a prerequisite for a later
real-runtime proof.

The admitted profile retains these prerequisites:

1. The generic seven-column `require-all-pass` contract exists and has
   independent malformed/header/empty/fail/pass tests.
2. The request normalizer, execution-contract schema, profile schema, verified
   task-record schema, workflow-attempt schema, and reporting projection are
   versioned and independently tested.
3. The fixed profile's semantic owner roster, direct edges, fan-out, barriers,
   and required/evidence roles are exact tested projections of `STAGE_MAP.md`.
4. A run-specific artifact inventory is materialized before compute.
5. Every admitted owner has explicit expected outputs and residue detection;
   none relies on filesystem discovery.
6. The local executor has automatic retries disabled and preserves task logs,
   validation reports, native receipts, and recovery evidence.
7. Step `08` and `09` bind the repository `renv` project and selected existing
   canonical project library explicitly, while clearing ambient R/renv path
   selectors rather than relying on job working directory.

`ready` does not waive these shared prerequisites. `harden` does not require a
generic transaction framework: change the smallest owner-local boundary that
makes clean execution, failure, and resume unambiguous.

The proof-sized package order and the acceptance rule for changing a
disposition are owned by [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
