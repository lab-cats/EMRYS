# Local-pilot orchestration readiness

This document is the canonical Campaign B owner-admission view for the local
CMH pilot defined by
[`ORCHESTRATION_CONTRACT.md`](ORCHESTRATION_CONTRACT.md). It records each
owner's orchestration disposition and the proof target required before profile
admission. It is not live runtime state, a second DAG, roadmap authority, or
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
| `ready` | No owner redesign is known to be required, but the listed proof is still mandatory before profile admission. |
| `harden` | A bounded owner change or explicit recovery/no-clobber contract is required before unattended profile execution. |
| `exclude` | The operation is intentionally outside the automatic version 1 profile. |

The generic semantic all-pass gate is required for every validator regardless
of disposition because current validators may publish failed rows with exit
zero.

## Owner matrix

| Owner and scope | Public producer / validator | Current admission state | Disposition | Proof target |
| --- | --- | --- | --- | --- |
| [`construct_STAR_index`](../../src/norad/stages/star_index/CONTRACT.md), one reference | Explicit local producer plus compatibility SLURM wrapper; grouped public validator | B1 added dry-run-first, declared-member, locked no-clobber publication | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`convert_GTF_to_BED12`](../../src/norad/stages/gtf_to_bed12/CONTRACT.md), one reference | Grouped `norad convert gtf-to-bed12`; grouped validator | B1 added explicit execute plus atomic no-replace publication | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`construct_FASTA_sidecars`](../../src/norad/stages/fasta_sidecars/CONTRACT.md), one reference | Public shell producer; grouped validator | B1 made controlled rollback fail closed and preserve ambiguous residue | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`align_RNA_reads_with_STAR`](../../src/norad/stages/star_alignment/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added explicit tool selection and a staged no-clobber transaction | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`construct_canonical_BAM`](../../src/norad/stages/canonical_bam/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and no-clobber admission to the existing transaction | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/canonical_bam_qc/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added explicit samtools selection and staged no-clobber pair publication | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/rseqc_orientation/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and staged no-clobber publication | `ready` | Pinned workflow dependency, validator all-pass, and verified-task binding remain required before rule admission |
| [`mark_BAM_duplicates_with_Picard`](../../src/norad/stages/duplicate_marking/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added explicit input/tool identity and staged no-clobber set publication | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_n_cigar/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and a sample-scoped no-clobber path | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/mechanical_orientation/CONTRACT.md), per sample | Public shell producer; grouped validator | B1 added stable-input checks and no-clobber admission to the existing transaction | `ready` | Validator all-pass and verified-task binding remain required before rule admission |
| [`generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/partitioned_cohort_mpileup/CONTRACT.md), per cohort/partition | Public shell producer; grouped validator | B1 added no-clobber admission, pre-receipt final validation, and failed-restore preservation | `ready` | Full input/output binding, validator all-pass, and verified-task binding remain required before rule admission |
| [`preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/cohort_candidate_preprocessing/CONTRACT.md), one cohort | Public shell/R producer; grouped validator | B1 added no-clobber admission and failed-restore preservation | `ready` | Explicit locked `renv`, validator all-pass, and verified-task sibling binding remain required before rule admission |
| [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/paired_cmh_candidate_ranking/CONTRACT.md), one analysis | Public shell/R producer; grouped validator | No owner redesign is known; shared semantic-gate and resume proof remain | `ready` | Explicit locked `renv`, paired-strata admission, complete transaction, semantic all-pass, retained independent test oracle, and failure/resume proof |
| [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/scientific_review_package/CONTRACT.md), one review | Grouped public assembler; publisher performs its own validation | Requires explicit human/reviewer declarations and must not be fabricated by computational orchestration | `exclude` | Separately authorized post-run review only; automatic profile reports review evidence absent/incomplete |
| [Artifact index and run summary](../../src/norad/reporting/README.md), one run | Grouped public build routes | Tracked inventory is structural only; execution contract is wider than the existing reporting run contract | `ready` | Deterministic precomputed run inventory; explicit reporting projection; admitted matching source checkout; receipt-last transactions |
| [Jinja HTML report](../../src/norad/reporting/README.md), one run | Grouped public report builder | Requires validated canonical run summary and explicit checkout authority | `ready` | Dry-run then execute; packaged Jinja/CSS resources; HTML/TSV/v2 receipt transaction; absent Step `09c` shown honestly |

## Cross-cutting prerequisites

B2 satisfies prerequisites 1 and 2. B3 satisfies the fixed-profile/DAG,
closed-dispatch, verified-task, zero-retry local-executor, and no-science
reference/one-sample/cohort slice requirements. Run-specific inventory
materialization, explicit `renv` launch authority for real R owners, reporting
tail, and aggregate failure/resume/interruption proof remain for later packages.

Before the first executable rule is admitted:

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
7. Step `08` and `09` bind the repository `renv` project explicitly rather than
   relying on job working directory.

`ready` does not waive these shared prerequisites. `harden` does not require a
generic transaction framework: change the smallest owner-local boundary that
makes clean execution, failure, and resume unambiguous.

The proof-sized package order and the acceptance rule for changing a
disposition are owned by [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
