# Project Handoff Notes

## What This Project Does

This repository rebuilds a Novogene Remora RNA-seq / RNA-editing workflow into a cleaner, manifest-driven, testable pipeline for local development and CSU SLURM execution.

The biological context is NORAD / PUM1 / rABE-related RNA-seq data. The downstream workflow appears to be RNA-editing / variant-like site calling rather than simple gene-count differential expression. Uploaded legacy scripts are treated as protocol references, not as runnable source of truth.

The intended high-level workflow is:

1. Build STAR index from the Novogene reference.
2. Convert GTF annotation to BED12 for RSeQC.
3. Align paired-end RNA-seq reads with STAR.
4. Create canonical coordinate-sorted, read-group-tagged, indexed BAMs.
5. QC canonical BAMs.
6. Infer library strandedness/orientation with RSeQC.
7. Mark duplicates.
8. Run GATK SplitNCigarReads.
9. Split BAMs by read orientation.
10. Run cohort bcftools mpileup by declared partition and mechanical read orientation.
11. Preprocess VCFs.
12. Run CMH/editing-site calling.

## Current Status

| Step | Status | Notes |
| ---- | ------ | ----- |
| `00a` STAR index | cluster-proven | Built Novogene STAR index at `refs/novogene_star_index`. |
| `00b` GTF to BED12 | cluster-proven | Wrote `refs/novogene_ref/genome.bed`; 206,601 BED12 transcript records. |
| `00c` GATK reference sidecars | cluster-proven | Script/job/test formalize creation and validation of `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict`; cluster validation succeeded. |
| `01` STAR alignment | complete and cluster-proven across all six samples | `ABE_EV_2` is a mapping outlier but not a pipeline blocker. |
| `02` canonical sort/read-group/index BAM | hardened and cluster-proven across all six samples | Final canonical BAMs have coordinate sort order, sample-specific RG metadata, BAI files, and `quickcheck` PASS. |
| `02b` BAM QC | implemented and refreshed across all six final hardened Step 02 BAMs | Initial cohort attempt exposed a samtools `PATH` inconsistency; rerun succeeded after prepending the known samtools bin path. |
| `03` RSeQC strandedness/orientation inference | cluster-proven across all six samples | All libraries are paired-end and reverse-stranded / first-strand-style. |
| `04` Picard MarkDuplicates | cluster-proven across all six samples | Duplicate-marked BAMs, indexes, Picard metrics, quickcheck, coordinate sort order, read groups, and metrics rows are confirmed. |
| `05` GATK SplitNCigarReads | implemented and cluster-proven across all six samples | Dry-run-first script/job consume Step `04` markdup BAMs and Step `00c` sidecars, publish validated `results/split_ncigar/<sample>/<sample>.split_ncigar.bam`, and route GATK temp spill files to project storage. |
| `06` read-orientation BAM split | cluster-proven across all six samples | Consumes Step `05` split-N-cigar BAMs and writes validated `FWD_like` / `REV_like` mechanical flag-group BAMs plus orientation counts TSVs. |
| `07` cohort mpileup | implemented locally and locally tested | Runs all manifest samples together for one declared partition and publishes neutral `FWD_like` / `REV_like` VCFs plus a receipt. Mocked-bcftools tests pass. Real-bcftools runtime validation, cluster dry-run, execute, and inspected cluster output evidence are pending; this step is not cluster-proven. |
| `08` VCF preprocessing | implemented locally; shell/fake-R and guarded real-R tested | Deterministically consumes the declared Step `07` receipt/VCF set and publishes a wide sites table, input receipt, and QC summary. Its real-R suite passes without `SKIP`; raw DP/AD/INFO AD lexemes are preflighted before semantic parsing. No cluster evidence exists, and this step is not cluster-proven. |
| `09` CMH editing-site calling | implemented locally; shell/fake-R and guarded real-R tested | Validates manifest-defined EV/PUM1 replicate pairs plus the Step `08` sites table and complete input receipt, retains every candidate with explicit statuses, and publishes four TSVs plus two PDFs. Its real-R suite passes without `SKIP`, including locale-independent raw-byte PDF validation. No cluster evidence exists, and this step is not cluster-proven. |
| `09c` scientific-evidence validation | implemented and fixture-tested locally at `b674a31` | Validates explicit Step `08`/`09` inputs, review plans, and evidence manifests; publishes 13 TSVs with the review summary last. No production review evidence, completed production science review, cluster evidence, or biological-readiness claim is recorded or supported by inspected evidence. |
| `artifact-schema-v1` contract package | implemented and fixture-tested locally at `5f4d3b4` | Provides one shared and four public Draft 2020-12 schemas, a read-only validator, a 67-row synthetic expected-artifact inventory, and valid fixtures. It does not inspect production sources, execute adapters, or generate an artifact index, run summary, or report. |

Current demo state:

* Cluster-proven: Steps `00a`-`00c`; Steps `01`-`06` across all six samples.
* Implemented locally and locally tested: Step `07`, using mocked bcftools rather than a real bcftools runtime.
* Local R runtime: official signed/notarized Apple-silicon CRAN R `4.6.1`,
  verified against published SHA-1
  `fc9f4ada15589e8e037b9bf05563d21e97181635`, with guarded `renv` `1.2.3`,
  Bioconductor `3.23`, and the exact eight direct Step `08` namespaces plus
  their dependency closure.
* Locally runtime-checked: normal and empty cache-disabled binary restores,
  namespace loading, `BiocManager::valid()`, `renv::status()`, and headless PDF
  creation pass.
* Step `08` and Step `09` real-R fixtures pass without `SKIP` after the
  `step-09b1-real-r-fixes` implementation at `eae5eca`.
* Step `08` now validates raw `FORMAT/DP`, `FORMAT/AD`, and `INFO/AD` lexemes
  before `VariantAnnotation`; its partition-overlap validator was already
  correct, and the prior generic fixture error had misattributed the failure.
* Step `09` now validates PDF EOF signatures as raw bytes without
  locale-sensitive text conversion.
* The Step `09` implementation/docpatch gate is complete and pushed at
  `9ac8307`.
* Documentation-only `step-09a-roadmap-docpatch` records the reconciled
  roadmap and is the clean/pushed base of `step-09b-local-r-runtime`.
* Step `09c` is implemented locally at `b674a31`, with active Python and shell
  fixtures for dry-run, status policy, evidence validation, locking,
  publication, rollback, and cleanup.
* `artifact-schema-v1` is implemented locally at `5f4d3b4`; its 54 focused
  contract tests and the complete local repository gate pass.
* After this schema docpatch/push gate, the next branch is
  `artifact-adapters-v1`, followed by the canonical run summary, immediate
  HTML/PDF reporting, foundational read-only tooling, and one validator branch
  per pipeline step.
* Remote promotion is paused. No Step `07` cluster evidence has yet been
  inspected, and the CSU batch-visible R environment remains unresolved.
* Not cluster-proven: Steps `07`, `08`, and `09`.
* No final biological result exists. Even future computational cluster proof
  will leave the provisional orientation policy and candidate interpretation
  for the separate scientific evidence-and-decision gate.
* No production Step `09c` evidence package is recorded or supported by
  inspected evidence; production science remains `evidence_incomplete`.

## Cohort

Known paired-end samples:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

Conditions:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Note that `ABE_EV4` lacks the underscore before `4`.

Approved paired strata are explicit:

```text
replicate 2: ABE_EV_2 / ABE_PUM1_2
replicate 3: ABE_EV_3 / ABE_PUM1_3
replicate 4: ABE_EV4  / ABE_PUM1_4
```

`configs/step_09_pairs.NORAD_EV_PUM1.tsv` records this mapping for reference.
It is not a runtime overlay. Step `09` reads pairing only from the full sample
manifest, and pairing is never inferred from names. Before Step `07` cluster
promotion, add these `replicate` values to the full cluster sample manifest so
the same sample-manifest hash propagates through the complete Steps `07`-`09`
chain. `samples.tsv` is absent from this checkout; the cluster-local runtime
copy, its persistence, and its hash have not yet been inspected.

## Current Scientific And Workflow Conclusions

Step `03` confirmed all six libraries are paired-end and reverse-stranded / first-strand-style.

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| ------ | ------------------: | ----------------: | ----------------: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The `ABE_EV_2` Step `03` output was rerun after Step `02` hardening and matched the previous report exactly. Step `02` changed operational metadata and publication safety without changing the biological orientation inference.

Current downstream conclusions must remain bounded:

* Step `09` output statuses will identify CMH-ranked candidates under the
  configured policy; they are not validated editing sites.
* `cluster-proven` means the declared computation ran and its contracts were
  inspected. It does not approve `legacy_provisional_v1`, annotation
  interpretation, thresholds, or biological causality.
* A separate post-Step-09 scientific gate must resolve orientation evidence,
  annotation provenance, sensitivity/replicate robustness, candidate
  adjudication, and the eligible-background decision before interpretation.
  Its Step `09c` schemas/tooling are implemented and fixture-tested locally;
  that does not create or complete a production review.
* `science_review_complete_exploratory` records a completed review while
  retaining provisional results. `biological_interpretation_ready` is the only
  state that could permit biological interpretation, but it is currently
  reserved and unavailable until a separately approved policy defines and
  unlocks its stricter exits.

## Main Entry Points

Implemented scripts:

```text
scripts/validate_manifest.py
scripts/restore_r_environment.R
scripts/check_r_environment.R
scripts/gtf_to_bed12.py
scripts/step_00c_prepare_gatk_reference.sh
scripts/step_01_star_align.sh
scripts/step_02_sort_index_bam.sh
scripts/step_02b_bam_qc.sh
scripts/step_03_infer_strandedness_and_orientation.sh
scripts/step_04_mark_duplicates.sh
scripts/step_05_split_n_cigar_reads.sh
scripts/step_06_split_bam_by_read_orientation.sh
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
scripts/step_09_cmh_editing_site_calling.sh
scripts/step_09_cmh_editing_site_calling.R
scripts/step_09c_scientific_validation.sh
scripts/step_09c_scientific_validation.py
scripts/validate_artifact_contracts.py
```

Implemented SLURM jobs:

```text
jobs/step_00a_build_novogene_star_index.slurm
jobs/step_00b_gtf_to_bed12.slurm
jobs/step_00c_prepare_gatk_reference.slurm
jobs/step_01_star_align.slurm
jobs/step_02_sort_index_bam.slurm
jobs/step_02b_bam_qc.slurm
jobs/step_03_infer_strandedness_and_orientation.slurm
jobs/step_04_mark_duplicates.slurm
jobs/step_05_split_n_cigar_reads.slurm
jobs/step_06_split_bam_by_read_orientation.slurm
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
jobs/step_08_vcf_preprocessing.slurm
jobs/step_09_cmh_editing_site_calling.slurm
```

Step `07` also has:

```text
tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
configs/step_07_partitions.pilot.tsv
configs/step_07_partitions.primary_contigs.tsv
configs/step_07_partitions.example.tsv
```

Step `08` also has:

```text
tests/shell/test_step_08_vcf_preprocessing.sh
tests/r/run_step_08_vcf_preprocessing_tests.sh
tests/r/test_step_08_vcf_preprocessing.R
```

Step `09` also has:

```text
tests/shell/test_step_09_cmh_editing_site_calling.sh
tests/r/run_step_09_cmh_tests.sh
tests/r/test_step_09_cmh_editing_site_calling.R
configs/step_09_pairs.NORAD_EV_PUM1.tsv
```

Step `09c` also has:

```text
tests/test_step_09c_scientific_validation.py
tests/shell/test_step_09c_scientific_validation.sh
tests/fixtures/step09c/build_fixture.py
configs/step_09c_review_plan.example.tsv
configs/step_09c_evidence_manifest.example.tsv
configs/step_09c_evidence_schemas/
```

The `artifact-schema-v1` package also has:

```text
schemas/artifacts/v1/common.schema.json
schemas/artifacts/v1/artifact_record.schema.json
schemas/artifacts/v1/scientific_review_record.schema.json
schemas/artifacts/v1/run_summary.schema.json
schemas/artifacts/v1/report_receipt.schema.json
configs/artifact_inventory.example.tsv
tests/fixtures/artifact_schema_v1/
tests/test_artifact_schema_contracts.py
```

The example inventory contains 67 explicit physical artifact rows spanning
Steps `00a`-`09c`. It is synthetic and is not a production inventory.

Local R interfaces:

```text
NORAD_USE_RENV=1 make r-restore RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make r-check RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make local-real-r-test RSCRIPT_BIN=/usr/local/bin/Rscript
```

The project library is activated only when `NORAD_USE_RENV=1`. Existing
compute and SLURM wrappers never install or bootstrap packages.

## Operator Pointers

For operational commands, validation checklists, cluster setup, and per-step run examples, start with `docs/operations/RUNBOOK.md`.

Useful optional cluster helper commands, when installed:

```text
norad
nlogs
sqme
sj <jobid>
sjtail <jobid>
sjcheck <jobid>
```

Expected output families:

```text
results/star/<sample>/
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
results/qc/bam/<sample>.quickcheck.txt
results/qc/bam/<sample>.flagstat.txt
results/qc/strandedness/<sample>.infer_experiment.txt
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt
results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai
results/orientation/<sample>/<sample>.FWD_like.bam
results/orientation/<sample>/<sample>.FWD_like.bam.bai
results/orientation/<sample>/<sample>.REV_like.bam
results/orientation/<sample>/<sample>.REV_like.bam.bai
results/qc/orientation/<sample>.orientation_counts.tsv
results/mpileup/<cohort>/<partition>/<cohort>.<partition>.FWD_like.mpileup.vcf
results/mpileup/<cohort>/<partition>/<cohort>.<partition>.REV_like.mpileup.vcf
results/mpileup/<cohort>/<partition>/<cohort>.<partition>.step07_outputs.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
results/scientific_validation/<review_id>/<review_id>.step09c_review_plan.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_evidence_index.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_orientation_locus_audit.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_annotation_audit.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_qc_funnel.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_replicate_effects.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_sensitivity_matrix.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_leave_one_pair_out.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_candidate_selection.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_candidate_adjudication.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_decisions.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_limitations.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_review_summary.tsv
```

Generated local-roadmap output families not yet implemented:

```text
results/artifacts/
results/reports/
```

Where to look:

```text
docs/design/PIPELINE_PLAN.md        current step status and validation detail
docs/operations/RUNBOOK.md          how to run and validate jobs
docs/design/                       durable decisions and rationale
docs/operations/                   symptom -> cause -> fix
docs/design/QUESTIONS.md            unresolved and answered questions
TODO.md                tactical next work
README.md              concise entrypoint
```

### Operator Checklist

- **Dry-run by default:** SLURM job wrappers default to dry-run; submit a dry-run first to validate resolved inputs and printed commands.
- **Execute on cluster:** When ready to run, submit with `EXECUTE=1` exported to the job, for example:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

- **Script-level execution:** Workflow shell scripts print resolved context by default and only run tool commands when passed `--execute`; include all required step arguments when invoking a script directly.
- **Where to validate:** Use `docs/operations/RUNBOOK.md` for per-step dry-run/execute checks, the design decisions log for the execution policy, and `docs/design/PIPELINE_PLAN.md` for step status.
- **Quick post-run checks:** Confirm expected outputs appear under `results/` (star, bam, qc, markdup) and inspect SLURM logs under `logs/`.

## Data Locations

Local development repo:

```text
/Users/elisteiger/dev/norad
```

Cluster repo:

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

Raw data symlink on cluster:

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs are under:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

Prepared references:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

The GATK reference sidecars are cluster-proven. Reference/BAM compatibility passed with 194 FAI contigs, 194 DICT contigs, 194 BAM header contigs, and reference/BAM SQ check `PASS`. Step `00c` exists as a dry-run-first script and SLURM wrapper that prepares and validates these shared sidecars. Step `05` requires these files rather than creating shared reference sidecars inside per-sample jobs.

## Step 02b Current State

Step `02b` is implemented and refreshed across all six final hardened Step `02` BAMs.

The first cohort attempt failed immediately because `samtools` was not found on `PATH` even though module output listed `samtools/1.19.2`. The successful rerun prepended the known samtools bin directory:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This is a cluster environment/PATH inconsistency, not a BAM/QC failure. The current Step `02b` script creates the requested output directory before dry-run exit, so do not describe that dry-run as side-effect-free.

Step `02` cleanup/trap handling was hardened after local validation-failure tests found an owned-lock cleanup regression. Treat this as operational hardening of the existing canonical BAM publication boundary, not as a change to the Step `02` output contract.

## Step 04 Current State

Step `04` is cluster-proven across all six samples with:

* completed scheduler state and exit code `0:0`
* nonempty duplicate-marked BAM, BAI, and Picard metrics
* passing `samtools quickcheck`
* coordinate sorting retained
* sample-specific read group retained
* duplicates marked, not removed
* `REMOVE_DUPLICATES=false`

Confirmed final Step `04` outputs:

| Sample | Markdup BAM size | Metrics size |
| ------ | ---------------: | -----------: |
| `ABE_EV_2` | 3.1G | 16K |
| `ABE_EV_3` | 2.1G | 7.8K |
| `ABE_EV4` | 3.0G | 15K |
| `ABE_PUM1_2` | 2.3G | 12K |
| `ABE_PUM1_3` | 2.1G | 8.5K |
| `ABE_PUM1_4` | 2.5G | 13K |

Confirmed Step `04` runtime/resource observations:

| Sample | Runtime | MaxRSS |
| ------ | ------: | -----: |
| `ABE_EV_2` | 00:08:29 | 22,660,004K |
| `ABE_EV_3` | 00:06:06 | 23,912,380K |
| `ABE_EV4` | 00:08:52 | 23,287,592K |
| `ABE_PUM1_2` | 00:06:40 | 24,293,400K |
| `ABE_PUM1_3` | 00:06:33 | 24,341,032K |
| `ABE_PUM1_4` | 00:07:32 | 23,376,504K |

Confirmed MarkDuplicates metrics:

| Sample | Read pairs examined | Duplicate read pairs | Optical duplicate pairs | Percent duplication | Estimated library size |
| ------ | ------------------: | -------------------: | ----------------------: | ------------------: | ---------------------: |
| `ABE_EV_2` | 17,663,180 | 11,731,288 | 120,669 | 0.664166 | 6,327,403 |
| `ABE_EV_3` | 18,867,589 | 11,371,887 | 130,069 | 0.602721 | 8,397,468 |
| `ABE_EV4` | 23,240,508 | 19,860,628 | 177,257 | 0.854569 | 3,383,587 |
| `ABE_PUM1_2` | 19,087,654 | 13,522,128 | 128,791 | 0.708423 | 5,783,576 |
| `ABE_PUM1_3` | 21,657,503 | 14,809,440 | 150,924 | 0.683802 | 7,214,041 |
| `ABE_PUM1_4` | 19,424,683 | 16,348,986 | 132,657 | 0.841660 | 3,081,584 |

Duplicate reads were marked, not removed. Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size. The observed Step `04` memory range was about 22.7-24.3 GB MaxRSS; this is observed evidence, not a guaranteed resource requirement.

## Step 05 Current State

Step `05` is implemented and cluster-proven across all six samples. The six-sample revalidation completed successfully and output inspection with `tests/data_checks/validate_step05_outputs.sh` reported:

```text
PASS=6
PENDING_OR_RUNNING=0
FAIL=0
```

Entry points:

```text
jobs/step_05_split_n_cigar_reads.slurm
scripts/step_05_split_n_cigar_reads.sh
tests/shell/test_step_05_split_n_cigar_reads.sh
```

Inputs:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Outputs:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

The Step `05` script is dry-run by default, creates no files in dry-run mode, requires Step `00c` sidecars instead of creating them, validates Java `>=17`, uses run-token temp outputs, validates the split BAM/index before publication, and rolls back an existing final BAM/BAI pair if publication fails after backups begin.

All six final Step `05` outputs have:

* final `results/split_ncigar/<sample>/<sample>.split_ncigar.bam`
* final `.bam.bai`
* passing `samtools quickcheck`
* `@HD` with `SO:coordinate`
* sample-matching `@RG`
* no Step `05` scratch files remaining

Confirmed final Step `05` output sizes:

| Sample | Split-N-cigar BAM size | BAI size |
| ------ | ---------------------: | -------: |
| `ABE_EV_2` | 4.4G | 2.0M |
| `ABE_EV_3` | 3.5G | 1.6M |
| `ABE_EV4` | 4.4G | 1.8M |
| `ABE_PUM1_2` | 3.7G | 1.6M |
| `ABE_PUM1_3` | 3.7G | 1.6M |
| `ABE_PUM1_4` | 3.8G | 1.8M |

The first Step `05` `ABE_EV_2` cluster execute attempt reached useful GATK `SplitNCigarReads` behavior: inputs, tools, and reference sidecars were far enough along for GATK to complete traversal pass 1 and enter traversal pass 2. It later failed during HTSJDK temporary spill/write/close behavior because `SortingCollection` temp files were written to node-local `/tmp` and hit `No space left on device`.

Step `05` was hardened so GATK uses a per-run project-storage temp directory through `--java-options -Djava.io.tmpdir=...`, `--tmp-dir ...`, and `TMPDIR` for the GATK process. Failure cleanup now removes owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks.

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`.

## Step 06 Current State

Step `06` is cluster-proven across all six samples. It consumes the Step `05` output contract:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

It writes:

```text
results/orientation/<sample_id>/<sample_id>.FWD_like.bam
results/orientation/<sample_id>/<sample_id>.FWD_like.bam.bai
results/orientation/<sample_id>/<sample_id>.REV_like.bam
results/orientation/<sample_id>/<sample_id>.REV_like.bam.bai
results/qc/orientation/<sample_id>.orientation_counts.tsv
```

The implementation is dry-run by default, creates no files in dry-run mode, uses run-token temp outputs, validates temp BAMs/indexes/counts before publication, protects existing final outputs with rollback, and has active shell tests under `tests/shell/test_step_06_split_bam_by_read_orientation.sh`.

All six Step `06` jobs completed `0:0`; `FWD_like` / `REV_like` BAM+BAI outputs were published for all six samples; `samtools quickcheck` passed silently; orientation counts TSVs were present; `assigned_fraction = 1.000000` and `unassigned_records = 0` for all six samples; and no Step `06` scratch files remained.

`FWD_like` and `REV_like` are mechanical read-orientation groups built from the legacy `samtools view -f 99`, `-f 147`, `-f 83`, and `-f 163` filters. They are not biological strand, transcript strand, sense, or antisense labels.

## Step 07 Current State

Step `07` is implemented locally and locally tested with mocked bcftools. It has not run with real bcftools on this workstation, no cluster dry-run or execute evidence has been inspected, and it is not cluster-proven.

One invocation selects exactly one row from the approved partition manifest and runs every sample in `samples.tsv` together, in manifest order, for both neutral mechanical orientations. The partition schema is:

```text
partition_id    selector_type    selector_value
```

`region` maps to bcftools `-r`; `regions_file` maps to `-R`. The approved primary-contig manifest defines the correction universe, while the separate one-row pilot manifest selects `1:1-100000`. The tracked primary manifest declares `1`-`22`, `X`, `Y`, and `MT`; its exact compatibility, including `MT`, with the Novogene FASTA index must be confirmed during cluster dry-run before it is treated as runtime validated.

The implementation preserves these legacy defaults:

```text
maximum depth: 10000000
skip indels
FORMAT annotations: DP, AD, ADF, ADR, SP
INFO annotations: AD, ADF, ADR
filter: INFO/AD[1-]>2 & MAX(FORMAT/DP)>20
plain VCF output
no bcftools call stage
```

For each partition it publishes:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

The receipt records `cohort_id`, `partition_id`, `selector_type`, `selector_value`, `orientation`, `vcf_path`, both manifest SHA-256 hashes, `sample_count`, and `vcf_record_count`. It is published last and is the transaction commit marker for downstream consumers. Validation requires the exact manifest-ordered VCF sample columns; structurally valid header-only VCFs are accepted and recorded with zero records.

Dry-run is side-effect-free. Execute mode validates BAM/BAI and FASTA/FAI inputs, selectors, and complete outputs; uses an owned cohort/partition lock and run-token scratch paths; validates before publication; and rolls back a replaced complete final set on failure. Local coverage is active at `tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh`, including mocked multi-BAM command construction, dry-run, validation, locks, cleanup, and rollback.

The primary manifest has 25 partitions. Step `07` becomes cluster-proven only
after the pilot and chromosome-1 gates plus inspected execution of all primary
partitions yields 25 valid primary receipts and 50 valid primary VCFs with
exact sample order, unchanged manifest hashes, reconciled record counts,
successful scheduler/log evidence, and no owned lock or run-token residue.
The separate pilot adds one receipt/two VCFs for validation only and is never
part of those totals or the correction universe.

## Step 08 Current State

Step `08` is implemented locally at implementation commit `90335d8`. Its
shell wrapper and publication behavior pass active fake-R tests. Its semantic
suite now passes locally under the guarded real-R environment without `SKIP`
after the corrective implementation at `eae5eca`. The existing
partition-overlap validator already rejected overlapping selectors; the
earlier generic negative-fixture message had misidentified the later failure.
The actual defect was malformed DP/AD/INFO AD lexemes being silently coerced
during semantic parsing. A streaming raw-count preflight now rejects those
lexemes before `VariantAnnotation`. There is no cluster dry-run, execute job,
log, or inspected output evidence. Step `08` is not cluster-proven.

Implemented entry points:

```text
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
jobs/step_08_vcf_preprocessing.slurm
```

The input universe is exactly the partition manifest crossed with
`FWD_like` and `REV_like`, in that order; VCF globbing is prohibited. The
workflow checks every Step `07` receipt and VCF path, SHA-256 hash, declared
and observed record count, and exact manifest-ordered sample columns. It also
requires disjoint partition selectors, stable sample/partition/GTF inputs, and
globally unique partition-independent candidate IDs.

The R engine uses `VariantAnnotation`, `GenomicRanges`, and `rtracklayer`
with the Novogene GTF. It expands multiallelic records by ALT index, extracts
the matching AD value, and counts/excludes symbolic and non-SNV alleles.
Before semantic parsing, it requires raw `FORMAT/DP` width `1` and raw
`FORMAT/AD`/present `INFO/AD` values to be a single `.` when the whole vector
is missing or otherwise have width equal to reference plus alternate allele
count; each token must be `.` or a non-negative integer. Missing required
FORMAT definitions, malformed or negative counts, one-sided missing DP/AD, AD
greater than DP, overlaps, duplicates, or receipt inconsistencies fail rather
than being coerced. A paired missing DP/AD value is retained as missing.

The retained legacy mapping is explicit and provisional:

```text
orientation_policy=legacy_provisional_v1
FWD_like -> legacy neg -> compatible + transcripts -> complement genomic REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain genomic REF/ALT
```

It is not a biologically validated orientation policy. The sites table keeps
genomic and RNA-normalized alleles, mechanical orientation, compatible
annotation strand, annotation flags, and manifest-ordered `DP__<sample>`,
`AD__<sample>`, and `AF__<sample>` columns. Output rows and collapsed
identifiers are deterministic.

The output transaction is:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

Observed ALT, supported SNV, skipped symbolic, skipped non-SNV, and published
candidate counts reconcile per input and in the summary. An owned cohort lock,
run-token temporary and backup paths, immutable input hashes,
validation-before-publication, cleanup, and rollback protect the three-file
set. The input receipt is published last as the transaction commit marker.

The Step `08` cluster exit requires both real-R fixture suites to pass in the
supported batch-visible environment and one inspected successful three-file
transaction. For the primary manifest, the input receipt must contain exactly
50 rows in partition order with `FWD_like` then `REV_like`; schemas, hashes,
sample columns, candidate uniqueness, and count invariants must reconcile, the
job must be `COMPLETED 0:0`, and no owned lock or run-token residue may remain.

## Step 09 Current State

Step `09` is implemented locally at implementation commit `e4371de`. The
active shell/fake-R suite passes. The real-R fixture runner now also passes
without `SKIP` after `eae5eca` replaced locale-sensitive PDF raw-to-text
conversion with raw-byte EOF matching. There is no Step `09` cluster dry-run,
execute job, log, or inspected output evidence, so the step is not
cluster-proven.

The full sample manifest is the only pairing source. It must contain
`replicate`, with exactly one control and one treatment per replicate,
identical replicate sets, and at least two strata. The approved current pairs
are replicates `2`, `3`, and `4`; names are never parsed to infer them. Step
`09` rejects a sample-manifest hash that does not match every row of the Step
`08` input receipt, so the replicate-bearing manifest must be established
before Step `07`, not overlaid at Step `09`.

The default analysis is:

```text
control: EV
treatment: PUM1
RNA change: A>G
minimum per-sample DP: 1
mean analysis DP: strictly >50
BH FDR: strictly <0.05
common OR: strictly >1.2 or <1/1.2
absolute treatment-control fraction difference: strictly >0.005
```

For every target candidate with complete counts and adequate per-sample depth,
the base-R engine builds treatment/control by edited/unedited tables for each
manifest-defined replicate and runs a two-sided,
continuity-corrected `mantelhaen.test`. The common odds ratio is treatment
relative to control. BH is applied once across every successfully tested
target candidate from all declared partitions and both orientations; mean
depth remains a later call threshold. Missing, low-coverage, degenerate, and
non-target candidates remain in the all-sites table with explicit statuses.

Background filtering is disabled by default. When an explicit condition
different from control and treatment is provided, every background sample
must have AF strictly below `0.01` by default. EV is never repurposed as a
missing no-dox condition.

Successful execute mode publishes:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

The all-sites and significant tables have 42 fixed analysis/annotation fields
followed by manifest-ordered `DP__`, `AD__`, and `AF__` groups. The summary has
39 fixed provenance/count/threshold fields. The mutation table always has the
12 ordered canonical substitutions. Both PDFs use a fixed 7-by-5-inch base-R
device, are signature/EOF validated, and remain valid for empty input. The
workflow retains
`orientation_policy=legacy_provisional_v1`, which is not biologically
validated.

Dry-run validates the complete contract and writes nothing. Execute mode uses
an owned analysis lock, run-token temporary/backup paths, stable input hashes,
exact six-output validation, and rollback. The summary is published last as
the commit marker. If rollback cannot restore a complete prior state, the
owned lock is deliberately retained for operator recovery; never delete such
a lock before inspecting its owner metadata, backups, final paths, and logs.

The Step `09` cluster exit requires one inspected `COMPLETED 0:0` transaction
with all six outputs, all-sites row count equal to the Step `08` candidate
count, significant-sites as the exact ordered rows whose `call_status` is
`significant_up` or `significant_down`, one summary row, 12 mutation-spectrum
rows, reconciled statuses and upstream hashes, valid PDF
signatures/EOF markers, background disabled for the default analysis, and no
owned lock or run-token residue. Passing this gate establishes computational
proof only.

## Step 09c Current State

Step `09c` is implemented locally at `b674a31`. It is a local,
dry-run-first Python/shell evidence validator, not a compute stage, SLURM job,
CMH rerun, decision engine, or biological-interpretation gate.

Public interface:

```bash
scripts/step_09c_scientific_validation.sh \
  --review-id REVIEW_ID \
  --sample-manifest SAMPLE_MANIFEST \
  --partition-manifest PARTITION_MANIFEST \
  --step08-sites STEP08_SITES \
  --step08-inputs STEP08_INPUTS \
  --step08-summary STEP08_SUMMARY \
  --step09-analysis-dir STEP09_ANALYSIS_DIR \
  --review-plan REVIEW_PLAN \
  --evidence-manifest EVIDENCE_MANIFEST \
  --output-root results/scientific_validation

# add --execute only to publish
```

Dry-run validates and prints the declared context without creating the output
directory, acquiring a lock, or writing stable files. Execute mode verifies
the exact Step `08` three-file and Step `09` six-file contracts, manifest and
artifact hashes, row counts, sample/partition/candidate relationships,
scientific evidence schemas, status coherence, policy versions, decisions,
and immutable inputs.

It publishes all 13 named TSVs under
`results/scientific_validation/<review_id>/` as one rollback-protected
transaction and writes `<review_id>.step09c_review_summary.tsv` last. The
implementation uses a review-scoped regular lock file with review/PID/run-token
metadata, run-token temporary and backup paths, validation before publication,
stable-input hash rechecks, rollback, and explicit cleanup failure reporting.
Existing stable outputs must be all 13 present or all absent. Incomplete
rollback retains recovery state; cleanup-only failures report the paths that
could not be removed and do not guarantee that the lock remains.

The active Python and shell fixture suites cover incomplete and exploratory
evidence, the reserved-state guard, unrelated-file immunity, input/hash
mutation, side-effect-free dry-run, exact output publication, locks, cleanup,
and rollback. The complete local Python, shell, and guarded R gates pass. This
is synthetic local evidence only. No production review package is recorded or
supported by inspected evidence;
`science_review_complete_exploratory` has not been established for production,
and `biological_interpretation_ready` is rejected by this implementation.

## Current Next Work

Use this clean descendant sequence:

```text
step-09b-local-r-runtime
└── step-09b1-real-r-fixes
    └── step-09c-scientific-validation
        └── artifact-schema-v1
            └── artifact-adapters-v1
                └── artifact-run-summary
                    └── report-html-v1
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
```

The Step `09b1` and Step `09c` gates are complete and pushed.
`artifact-schema-v1` is implemented at `5f4d3b4`; its schemas, synthetic
inventory, validator, fixtures, and 54 focused tests pass. This documentation
commit is its remaining predecessor gate before branching.

1. Implement `artifact-adapters-v1`, then the canonical run summary and
   self-contained HTML plus Quarto/Typst PDF/TSV reporting slice. No generated
   artifact index, run summary, or report exists at this handoff boundary.
2. Implement the three read-only foundation packages and then one explicit
   validator branch for each of `00a`, `00b`, `00c`, `01`, `02`, `02b`, `03`,
   `04`, `05`, `06`, `07`, `08`, and `09`.
3. Stop local work after `post09-validation-report-09`.

When remote work resumes, continue only from that final clean branch:

```text
validate-step-07
-> validate-step-08
-> validate-step-09
-> validate-step-09c-scientific-evidence
-> post09-targeted-reruns
```

Each remote validation branch regenerates the structured run summary and
HTML/PDF report after evidence inspection and records their paths and hashes
in its evidence docpatch. Remote promotion remains upstream-sequential.
Cluster proof and biological readiness remain independent.

## Java And Picard Handoff

Step `04` resolves Java in the local checkout as:

1. `JAVA_BIN_OVERRIDE`, when provided.
2. `$JAVA_HOME/bin/java`, only if that path exists and is executable.
3. `command -v java`.

The wrapper then verifies the selected executable exists, logs the actual `java -version`, parses the runtime major version, and fails before Picard starts if the runtime is below Java 17.

Known cluster issue:

* `node002` provided Java 17, completed the GATK/bcftools tool probe successfully, and ran OpenJDK `17.0.14`.
* `node003` provided working Java 17 via `/usr/bin/java` and completed `ABE_EV_2` MarkDuplicates.
* `node007` reported Java 11 at `/usr/bin/java`; Picard classes require Java 17 class-file version 61.
* The Java 17 module's advertised `JAVA_HOME` path was missing on `node007`.

Do not infer the effective Java runtime from the module name or `JAVA_HOME` alone. Scripts should continue logging and validating the actual Java runtime. Node-specific success is evidence, not a durable architecture decision.

## Local Validation Gate

Run from the local repo root:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
.venv/bin/python -m compileall scripts tests
.venv/bin/python -m pytest
.venv/bin/python scripts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
make shell-test
NORAD_USE_RENV=1 make r-check RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make local-real-r-test RSCRIPT_BIN=/usr/local/bin/Rscript
git status --short
git diff --name-status
```

Local tests are lightweight and should not require real full-size BAM/FASTQ
data. Bare `python` is absent on this workstation, so the passing Python gate
uses the existing project `.venv`. The R environment check passes. The two
real-R runners and the aggregate local R target pass without `SKIP` after
`eae5eca`; the shell, Python, and `r-check` gates also pass locally. This is
synthetic/local evidence only. Step `09c` is implemented at `b674a31`.
`artifact-schema-v1` is implemented at `5f4d3b4`; its 54 focused tests and
schema/inventory validation pass. These checks do not inspect production
artifacts or establish runtime, cluster, report, scientific-review, or
biological evidence. `artifact-adapters-v1` is next after this docpatch/push
gate.

## Development Rule

Do not jump ahead. Each stage must use its own descendant branch and complete both commits before the next branch is created:

```text
create stage branch
-> implement and run focused/full local tests
-> implementation commit
-> reread required docs and perform repository-wide consistency pass
-> documentation-only commit
-> clean status/history and push
-> create the next descendant stage branch
```

Cluster promotion remains upstream-sequential. A step is `cluster-proven` only after its scheduler state, logs, validation commands, and outputs have been inspected; a tool probe or local mocked test is not cluster proof.
