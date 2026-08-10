# Troubleshooting

Use this guide to preserve evidence, classify a failure, and route recovery.
Exact commands live in the adjacent owner README; exact interfaces and checks
live in its `CONTRACT.md`.

## Common recovery rules

Before retry, deletion, restoration, or adoption of uncertain output:

1. Stop new writers and downstream readers. Inspect scheduler/process state,
   the lock owner, and every declared output root.
2. Preserve stable outputs, run-token staging, temporary, backup, quarantine,
   recovery, and lock paths; logs and accounting; command and checkout; tools
   and environment; input identities and hashes; filesystem identity; and
   unrelated directory entries.
3. Treat an absent lock, backup, receipt, or marker as missing evidence—not a
   clean state. A visible receipt or summary is valid only when the complete
   transaction validates.
4. Never delete a foreign lock, combine attempts, manufacture a receipt, infer
   ownership from names or timestamps, or overwrite a late or identity-changed
   path.
5. Choose and record one recovery target: a validated predecessor, a validated
   new transaction, or a clean first-publication state. Remove only residue
   whose ownership is proved.
6. Use an isolated absolute output root for diagnostics that must not disturb
   the questioned state. Diagnostic success is not production evidence.

Git rollback changes tracked implementation only. It does not authenticate or
restore runtime artifacts. A validator or evidence command can exit `0` while
recording failed evidence rows; exit `2` means unsafe input, CLI, tool, or
publication failure.

## Common environment and operation matrix

| Symptom | Response |
| --- | --- |
| `logs/...: No such file or directory` at submission | Create `logs/` before `sbatch`; SLURM opens streams before the job body. |
| Empty `.err` or `COMPLETED 0:0` | Inspect both streams, accounting, outputs, and owner validation; neither is proof alone. |
| Wrong log prefix | Locate the job's actual files; do not borrow a prefix from another owner. |
| `/local/tmp` is unwritable | Confirm the effective writable `TMPDIR`; use the Step `05` project-storage route for large GATK spill. |
| Tool/module appears on login but not in a job | Establish the exact executable in the approved batch context. Module names are not runtime proof. |
| Picard `UnsupportedClassVersionError` | Step `04` requires the effective Java major version to be at least 17. Validate the selected executable, not `JAVA_HOME` alone. |
| R or namespace unavailable | Use explicit guarded restoration/checks; local availability does not prove batch visibility. Never bootstrap from compute. |
| Quiet local gate appears silent | Wait for the lane result or inspect retained failure/interruption logs; use serial or verbose mode for diagnosis. |
| Coverage regression | Inspect the exact environment, subprocess data, module, and JSON diff. Never update the baseline merely to pass. |
| Schema fixture or synthetic report passes | Report local contract evidence only; it is not production, cluster, scientific-review, or biological proof. |

## Owner-specific defect matrix

These are current characterized boundaries, not approved behavior. Follow the
linked owner after applying the common rules.

| Owner | Characterized defect or evidence limit | Required disposition |
| --- | --- | --- |
| [`construct_STAR_index`](../../src/norad/stages/star_index/README.md) | Reference/index disagreement or ambiguous validation-report predecessor can survive around publication. | Preserve index, parameters, reference identities, report transaction, lock, and logs; rebuild only through the owner. |
| [`convert_GTF_to_BED12`](../../src/norad/stages/gtf_to_bed12/README.md) | Final/intermediate BED may disagree with deterministic GTF normalization. | Preserve both plus GTF and logs; never hand-edit BED12. |
| [`construct_FASTA_sidecars`](../../src/norad/stages/fasta_sidecars/README.md) | FAI may publish before DICT failure; malformed or mismatched sidecars are not repaired. | Preserve FASTA, both sidecars, stage/backup/lock state, and provenance; recover through the owner. |
| [`align_RNA_reads_with_STAR`](../../src/norad/stages/star_alignment/README.md) | Five direct final outputs may be partial or mixed after failure. | Preserve the entire attempt and scheduler evidence; diagnose in an isolated root. |
| [`construct_canonical_BAM`](../../src/norad/stages/canonical_bam/README.md) | A severe restoration failure can lose the prior BAM while leaving a prior BAI with no recovery marker. | Stop downstream readers; preserve the whole directory and reconstruct only after separate review. |
| [`collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/canonical_bam_qc/README.md) | Direct-final quickcheck/flagstat writes can leave a partial, mixed, or stale pair accepted by existence checks. | Establish attempt identity for both files before retry or reuse. |
| [`collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/rseqc_orientation/README.md) | Direct stdout redirection can leave partial, empty, or stale reports. | Preserve report, streams, BAM/BAI, BED12, tool, and job identity; retain mechanical labels. |
| [`mark_BAM_duplicates_with_Picard`](../../src/norad/stages/duplicate_marking/README.md) | BAM, BAI, and metrics are not an all-or-none transaction and may be mixed or stale. | Stop Step `05`; preserve the triplet, input, Java/Picard/samtools identities, streams, and directory metadata. |
| [`split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_n_cigar/README.md) | Best-effort restoration may lose the prior BAM, restore only BAI, and erase recovery evidence. | Stop Step `06`; isolate diagnostics and preserve all final, staged, backup, temp, lock, reference, and scheduler state. |
| [`partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/mechanical_orientation/README.md) | Two output roots can collide on shared counts; severe rollback can lose one prior BAM and stale files may pass existence checks. | Stop every writer/reader to both roots; isolate both roots for diagnosis and preserve all five outputs and locks. |
| [`generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/partitioned_cohort_mpileup/README.md) | Receipt visibility precedes final validation; restoration can leave a prior final absent and wrapper checks can accept a stale set. | Preserve VCFs, receipt, manifests, input pairs, run-token paths, lock, selector, and tool identity. A header-only VCF is valid only when its zero count reconciles. |
| [`preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/cohort_candidate_preprocessing/README.md) | Cross-root rollback lacks a durable marker; receipt visibility precedes final validation and stale triples may pass existence checks. | Stop Step `09`; preserve both roots, all transactions and manifests, R environment, locks, backups, and streams. |
| [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/paired_cmh_candidate_ranking/README.md) | Scheduler success can accept stale six-file output; severe rollback and lock states remain. Production validation does not independently recompute CMH statistics. | Preserve all six outputs, upstream transaction, selected R program/runtime, streams, lock, backups, and scheduler identity; retain the separate test oracle evidence ceiling. |
| [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/scientific_review_package/README.md) | After replacement-summary publication, `SIGTERM` retains unvalidated finals plus predecessor backup/temp/lock without a notice, while `KeyboardInterrupt` removes those recovery paths but leaves the unvalidated finals; visible summary or absent lock is not commit proof. | Preserve every final and recovery path, rule out writers/readers, and reconstruct only from the exact owner contract; never infer commit, reviewer decisions, or biological readiness. |
| [Runtime availability](../../src/norad/evidence/runtime_availability/README.md) | Exit `0` may contain `fail`, `blocked`, or `not_checked`. Lock acquisition can strand a lock; failed restoration leaves only a `.previous` file without a lock or marker; suppressed lock-cleanup failure can report success while retaining the lock. | Inspect every row and asserted context. Preserve the report and all lock, temporary, and previous paths; absence of the lock is not publication proof. |
| [Reference provenance](../../src/norad/evidence/reference_provenance/README.md) | Hash/contig disagreement is observation only. | Correct declarations or regenerate through the upstream owner; never repair references in the evidence tool. |
| [Storage inventory](../../src/norad/evidence/storage_inventory/README.md) | Measurement or policy state grants no retention authority; its three-file publication can remain ambiguous. | Preserve the transaction and approval state; never mutate storage content through this tool. |
| [Artifact contracts and reporting](../../src/norad/reporting/README.md) | Schema, adapter, summary, Quarto, and report transactions have distinct locks, identities, receipts, and rollback boundaries. Completion markers do not promote evidence. | Recover within the exact owner transaction; never mix records, edit hashes/statuses, install from rendering, or call synthetic output production evidence. |

## Scientific and evidence ceiling

`FWD_like` and `REV_like` remain mechanical groupings. Step `09` produces
CMH-ranked candidates, not validated editing sites. A report, review package,
application log, transaction receipt, or successful computation cannot promote
scientific or biological state. `science_review_complete_exploratory` remains
provisional; `biological_interpretation_ready` remains reserved.
