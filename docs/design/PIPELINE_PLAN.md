# NORAD Pipeline Plan

This is the detailed map for the local-first, SLURM-scaled NORAD / Novogene Remora RNA-seq workflow.

The project rebuilds an uploaded/reference RNA-editing workflow into a cleaner, manifest-driven, testable pipeline. Legacy scripts are protocol references, not runnable source of truth.

Pipeline development follows a gated workflow:

```text
create stage branch from the latest clean docpatched predecessor
-> implement only that stage
-> focused and complete local validation
-> implementation commit
-> required-document reread and repository-wide docpatch
-> documentation-only commit
-> clean status/history and push
-> create the next descendant stage branch
```

Cluster promotion remains sequential from the earliest unproven upstream step and receives its own evidence docpatch after each validated stage.

## Cohort

Samples:

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

Approved paired strata:

```text
replicate 2: ABE_EV_2 / ABE_PUM1_2
replicate 3: ABE_EV_3 / ABE_PUM1_3
replicate 4: ABE_EV4  / ABE_PUM1_4
```

The full sample manifest is the only runtime pairing source. The tracked
`configs/step_09_pairs.NORAD_EV_PUM1.tsv` records this mapping for reference;
it is not an overlay, and pairing is never inferred from names.

## Pipeline Table

| Step | Purpose | Expected inputs | Expected outputs | Status | Main tool(s) |
| ---- | ------- | --------------- | ---------------- | ------ | ------------ |
| `00a` | Build the Novogene STAR index. | Novogene reference FASTA/GTF under `refs/novogene_ref/` | `refs/novogene_star_index/` | cluster-proven | STAR |
| `00b` | Convert reference GTF to sorted BED12 for strandedness checks. | `refs/novogene_ref/genome.gtf` | `refs/novogene_ref/genome.bed` | cluster-proven | Python, bedtools |
| `00c` | Create/validate GATK reference sidecars. | `refs/novogene_ref/genome.fa` | `refs/novogene_ref/genome.fa.fai`, `refs/novogene_ref/genome.dict` | cluster-proven | samtools, GATK |
| `01` | Align paired-end FASTQs to the reference. | FASTQ R1/R2 files, STAR index | `results/star/<sample_id>/` | complete and cluster-proven across all six samples | STAR |
| `02` | Create canonical coordinate-sorted, read-group-tagged, indexed BAMs. | STAR alignment BAM | `results/bam/<sample_id>/<sample_id>.sorted.bam` and `.bai` | hardened and cluster-proven across all six samples | samtools |
| `02b` | Run BAM integrity/QC checks. | canonical sorted BAM | `results/qc/bam/<sample_id>.quickcheck.txt`, `results/qc/bam/<sample_id>.flagstat.txt` | implemented and refreshed across all six final hardened Step 02 BAMs | samtools |
| `03` | Infer strandedness and read orientation. | canonical sorted BAM, `refs/novogene_ref/genome.bed` | `results/qc/strandedness/<sample_id>.infer_experiment.txt` | cluster-proven across all six samples | RSeQC `infer_experiment.py` |
| `04` | Mark PCR/optical duplicates. | canonical sorted BAM | `results/markdup/<sample_id>/<sample_id>.markdup.bam` and `.bai`, Picard metrics | cluster-proven across all six samples | Picard MarkDuplicates |
| `05` | Run RNA-seq SplitNCigarReads. | duplicate-marked BAM, Step `00c` reference FASTA/FAI/DICT | `results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam` and `.bai` | implemented and cluster-proven across all six samples | GATK SplitNCigarReads |
| `06` | Split processed BAMs by read-orientation group. | `results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam` and `.bai` | `results/orientation/<sample_id>/<sample_id>.FWD_like.bam` and `.bai`; `results/orientation/<sample_id>/<sample_id>.REV_like.bam` and `.bai`; `results/qc/orientation/<sample_id>.orientation_counts.tsv` | cluster-proven across all six samples | samtools |
| `07` | Run cohort mpileup by declared partition and neutral mechanical orientation. | `samples.tsv`; approved partition manifest; all Step `06` orientation BAM/BAI pairs; reference FASTA/FAI | two VCFs and `step07_outputs.tsv` under `results/mpileup/<cohort>/<partition>/` | implemented locally and locally tested with mocked bcftools; real runtime and cluster validation pending; not cluster-proven | bcftools |
| `08` | Preprocess the exact Step `07` receipt set for editing-site statistics. | partition manifest; Step `07` VCFs and receipts; sample manifest; Novogene GTF | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, input receipt, and QC summary | implemented locally and shell/fake-R tested; real-R runtime and cluster validation pending; not cluster-proven | R / Bioconductor |
| `09` | Run paired CMH editing-site calling and write summaries. | Step `08` table and input receipt; paired-replicate sample manifest; partition manifest | four tables and two plots under `results/editing/<analysis>/` | implemented locally at `e4371de` and shell/fake-R tested; real-R runtime and cluster validation pending; not cluster-proven | base R |

## Validated Outputs And Results

### Step 00a

```text
refs/novogene_star_index/
```

The STAR index was built using `sjdbOverhang=149`, matching 150 bp reads.

### Step 00b

```text
refs/novogene_ref/genome.bed
```

The BED12 file contains 206,601 transcript records.

### Step 00c

Purpose:

```text
GATK reference sidecars / reference FASTA index and sequence dictionary
```

Expected outputs:

```text
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Implemented entry points:

```text
scripts/step_00c_prepare_gatk_reference.sh
jobs/step_00c_prepare_gatk_reference.slurm
tests/shell/test_step_00c_prepare_gatk_reference.sh
```

The Step `00c` implementation is dry-run by default, creates only missing sidecars in execute mode, uses a reference-level lock, publishes run-token temp files only after validation, and fails rather than overwriting invalid existing sidecars.

The sidecars were also generated successfully before this implementation as an ad hoc cluster prep task; formal Step `00c` cluster validation is now complete.

Reference/BAM compatibility check:

```text
FAI contigs: 194
DICT contigs: 194
BAM header contigs: 194
Reference/BAM SQ check: PASS
```

Status:

```text
cluster-proven
```

### Step 01

All six samples completed STAR alignment.

| Sample | Approximate input reads | Unique mapping rate |
| ------ | ----------------------: | ------------------: |
| `ABE_EV_2` | 21.36 million | 58.50% |
| `ABE_EV_3` | 20.5 million | 82.95% |
| `ABE_EV4` | 26.6 million | 71.06% |
| `ABE_PUM1_2` | 21.1 million | 77.51% |
| `ABE_PUM1_3` | 23.2 million | 85.38% |
| `ABE_PUM1_4` | 22.5 million | 70.96% |

For `ABE_EV_2`, uniquely mapped reads were 58.50%, reads mapped to multiple loci were 24.19%, and reads unmapped because they were too short were 16.55%. `ABE_EV_2` is a cross-sample mapping outlier, especially in unique mapping, but this is an observed sample-level property rather than a pipeline blocker.

### Step 02

Canonical outputs:

```text
results/bam/<sample_id>/<sample_id>.sorted.bam
results/bam/<sample_id>/<sample_id>.sorted.bam.bai
```

The hardened Step `02` implementation guarantees:

* coordinate sorting
* one sample-specific read group per BAM
* read-group fields `ID=<sample_id>`, `SM=<sample_id>`, provisional `LB=<sample_id>`, and `PL=ILLUMINA`
* every alignment record has the expected `RG` tag
* `@HD` reports `SO:coordinate`
* validation before publication
* `samtools quickcheck`
* BAM indexing
* per-sample lock directory
* fresh job/process-specific temporary and backup paths
* rollback-protected publication
* stable canonical BAM/BAI paths are replaced only after validation succeeds
* dry-run mode creates no directories or files

The hardening was required because the original canonical `ABE_EV_2` BAM lacked read groups, causing Picard to fail with:

```text
SAMRecord.getReadGroup() is null
```

All six final Step `02` BAMs have been manually confirmed to have a nonempty BAM, matching BAI, `samtools quickcheck: PASS`, `SO:coordinate`, and the correct sample-specific `@RG`.

Confirmed final canonical BAM sizes were approximately:

| Sample | BAM size |
| ------ | -------: |
| `ABE_EV_2` | 3.0 GB |
| `ABE_EV_3` | 2.0 GB |
| `ABE_EV4` | 2.9 GB |
| `ABE_PUM1_2` | 2.2 GB |
| `ABE_PUM1_3` | 2.1 GB |
| `ABE_PUM1_4` | 2.5 GB |

Transient backup and lock paths are not stable interfaces.

Step `02` cleanup/trap handling was hardened after local validation-failure tests found an owned-lock cleanup regression. This did not change the canonical Step `02` BAM/BAI output contract.

### Step 02b

Outputs:

```text
results/qc/bam/<sample_id>.quickcheck.txt
results/qc/bam/<sample_id>.flagstat.txt
```

Step `02b` is implemented and refreshed across all six final hardened Step `02` BAMs.

The first Step `02b` cohort attempt failed immediately because `samtools` was not found on `PATH`, despite module output listing `samtools/1.19.2`. The successful rerun prepended the known samtools bin directory:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This is a cluster environment/PATH inconsistency, not a BAM/QC failure.

The current script creates the requested output directory before dry-run exit; do not describe Step `02b` dry-run mode as side-effect-free.

### Step 03

All six libraries are paired-end and consistently reverse-stranded / first-strand-style.

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| ------ | ------------------: | ----------------: | ----------------: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The dominant reverse-stranded orientation ranges from 0.8562 to 0.8740 across the cohort. The opposing orientation ranges from 0.0374 to 0.0433, and the failed-to-determine fraction ranges from 0.0828 to 0.1063.

There is no flipped-orientation sample and no obvious condition-specific strandedness inconsistency. The `ABE_EV_2` Step `03` report was preserved, rerun after Step `02` hardening, and compared with the previous report with an empty diff, confirming the Step `02` metadata hardening did not change the biological orientation inference.

Durable scientific conclusion:

```text
All six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.
```

Tool-specific examples that commonly correspond to this orientation include:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

### Step 04

Step `04` is cluster-proven across all six samples.

All six samples have:

* duplicate-marked BAM present
* BAM index present
* Picard metrics present
* `samtools quickcheck: PASS`
* `@HD` retained with `SO:coordinate`
* sample-specific `@RG` retained
* populated Picard metrics row
* duplicate records marked, not removed
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

Duplicate reads were marked, not removed. Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size.

The observed Step `04` memory range was about 22.7-24.3 GB MaxRSS. This is an observed resource range, not a guaranteed requirement.

### Step 05

Step `05` is implemented and cluster-proven across all six samples. The six-sample revalidation completed successfully and output inspection with `tests/data_checks/validate_step05_outputs.sh` reported:

```text
PASS=6
PENDING_OR_RUNNING=0
FAIL=0
```

Implemented entry points:

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

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`.

Step `05` treats `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` as prerequisites, fails clearly if they are missing, and must not silently create shared reference sidecars inside per-sample jobs.

The implementation is dry-run by default, side-effect-free in dry-run mode, validates the selected Java runtime is at least Java 17 in execute mode, writes GATK output to a run-token temp BAM, indexes and validates the temp pair with samtools, checks coordinate sort order and sample read-group preservation, and publishes final BAM/BAI only after validation succeeds.

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

The first `ABE_EV_2` cluster execute attempt provided useful partial evidence: GATK completed traversal pass 1, entered traversal pass 2, and then failed during HTSJDK temporary spill/write/close behavior because `SortingCollection` temp files were written to node-local `/tmp` and hit `No space left on device`.

Step `05` was hardened to use a per-run project-storage GATK temp directory via `--java-options -Djava.io.tmpdir=...`, `--tmp-dir ...`, and `TMPDIR` for the GATK process. Cleanup now removes owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks on failure.

Step `06` consumes the Step `05` output contract:

```text
results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai
```

### Step 06

Step `06` is cluster-proven across all six samples.

Implemented entry points:

```text
jobs/step_06_split_bam_by_read_orientation.slurm
scripts/step_06_split_bam_by_read_orientation.sh
tests/shell/test_step_06_split_bam_by_read_orientation.sh
```

Input contract:

```text
results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai
```

Expected output contract:

```text
results/orientation/<sample>/<sample>.FWD_like.bam
results/orientation/<sample>/<sample>.FWD_like.bam.bai
results/orientation/<sample>/<sample>.REV_like.bam
results/orientation/<sample>/<sample>.REV_like.bam.bai
results/qc/orientation/<sample>.orientation_counts.tsv
```

Legacy read-orientation groups to preserve:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

These are mechanical flag groups. `samtools view -f FLAG` means a read has all bits in `FLAG`; it is not exact flag equality. Do not describe `FWD_like` or `REV_like` as biological sense, antisense, transcript-strand, or biological-strand calls.

The implementation is dry-run by default, side-effect-free in dry-run mode, writes run-token temp outputs first, validates the temp BAMs/BAIs/counts TSV before publication, protects existing final outputs with rollback, and computes `assigned_fraction` in the counts TSV with `awk`.

All six Step `06` jobs completed `0:0`; `FWD_like` / `REV_like` BAM+BAI outputs were published for all six samples; `samtools quickcheck` passed silently; orientation counts TSVs were present; `assigned_fraction = 1.000000` and `unassigned_records = 0` for all six samples; and no Step `06` scratch files remained.

### Step 07

Step `07` is implemented locally at commit `e68b00c` and locally tested with mocked bcftools. Real-bcftools runtime validation is unavailable on this workstation. No Step `07` cluster dry-run, execute run, log, or output evidence has been inspected, so the step is not cluster-proven.

Implemented entry points and active test:

```text
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
```

Committed partition manifests:

```text
configs/step_07_partitions.pilot.tsv
configs/step_07_partitions.primary_contigs.tsv
configs/step_07_partitions.example.tsv
```

The analysis-specific partition contract is:

```text
partition_id    selector_type    selector_value
```

`region` maps to bcftools `-r`, and `regions_file` maps to `-R`. The approved manifest is the explicit correction universe; downstream steps must consume that declared set rather than globbing whatever VCFs exist. The separate one-row pilot selects `pilot_1` at `1:1-100000`. The tracked primary manifest declares `1`-`22`, `X`, `Y`, and `MT`; cluster dry-run must compare that set with the actual Novogene FAI, including the exact `MT` name, before runtime validation.

One invocation chooses one partition and passes every manifest sample to bcftools together, in manifest order, for both `FWD_like` and `REV_like`. These remain mechanical labels, not biological strand calls.

The command streams `bcftools mpileup -Ou` into `bcftools filter -Ov` and preserves:

```text
maximum depth: 10000000
skip indels
FORMAT annotations: DP, AD, ADF, ADR, SP
INFO annotations: AD, ADF, ADR
filter: INFO/AD[1-]>2 & MAX(FORMAT/DP)>20
plain VCF output
no bcftools call stage
```

Output contract:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

Receipt columns:

```text
cohort_id
partition_id
selector_type
selector_value
orientation
vcf_path
sample_manifest_sha256
partition_manifest_sha256
sample_count
vcf_record_count
```

The receipt is published last and is the commit marker for the complete two-orientation partition transaction. Execute mode validates BAM/BAI pairs, FASTA/FAI structure, selectors, VCF structure, stable manifest hashes, and exact manifest-ordered sample columns. Header-only VCFs are valid and receive a zero record count.

The local implementation follows the Step `05`-`06` reliability contract: side-effect-free dry-run, an owned cohort/partition lock, run-token scratch and backup paths, validation before publication, rollback of a replaced complete set, and owned cleanup. The active fake-bcftools test covers command construction, both selectors, receipt and sample-order validation, header-only output, failure handling, locks, cleanup, and rollback. The complete local repository gate passed with 22 Python tests and all shell tests through Step `07`.

Cluster-proof exit contract: after pilot and chromosome-1 promotion gates, all
25 primary partitions must yield 25 valid receipts and 50 structurally valid
primary VCFs. Every VCF must preserve the exact six-sample manifest order;
receipt record counts and the unchanged replicate-bearing sample-manifest and
partition-manifest hashes must reconcile; jobs/logs/outputs must be inspected
as `COMPLETED 0:0`; and no owned lock or run-token residue may remain. The
separate pilot produces one receipt/two VCFs for validation only and never
enters those totals or the primary correction universe.

### Step 08

Step `08` is implemented locally at implementation commit `90335d8`. The
shell wrapper and its publication transaction are locally tested with a fake
`Rscript`. This workstation has no `Rscript`, so the real-R semantic fixture
suite has not run. No cluster dry-run, execute job, log, or output evidence has
been inspected; Step `08` is not cluster-proven.

Implemented entry points and active tests:

```text
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
jobs/step_08_vcf_preprocessing.slurm
tests/shell/test_step_08_vcf_preprocessing.sh
tests/r/run_step_08_vcf_preprocessing_tests.sh
tests/r/test_step_08_vcf_preprocessing.R
```

The shell CLI is:

```text
scripts/step_08_vcf_preprocessing.sh
  --cohort-id COHORT
  --sample-manifest SAMPLE_MANIFEST
  --partition-manifest PARTITION_MANIFEST
  --step07-root STEP07_ROOT
  --annotation-gtf ANNOTATION_GTF
  --output-root OUTPUT_ROOT
  --qc-root QC_ROOT
  [--rscript-bin RSCRIPT_BIN]
  [--r-script R_SCRIPT]
  [--execute]
```

Dry-run is the default, constructs the exact command and input set, invokes no
R process, and creates no output directories or files. The declared input
universe is the partition manifest crossed with `{FWD_like, REV_like}`; no VCF
glob is used. For each partition the implementation requires the Step `07`
receipt plus both named VCFs and verifies receipt hashes, paths, selector
values, manifest hashes, record counts, and exact manifest-ordered VCF sample
columns. Partition selectors must not overlap, candidate IDs must remain
globally unique, and the sample manifest, partition manifest, GTF, receipts,
and VCFs must not change during execution.

The R implementation uses `VariantAnnotation`, `GenomicRanges`,
`rtracklayer`, and their required Bioconductor dependencies; base R is used
otherwise. It imports the project Novogene GTF directly, expands each
multiallelic record by ALT index, and extracts the matching alternate AD.
Symbolic and non-SNV alleles are counted and excluded rather than truncated.
Missing FORMAT definitions, malformed or negative counts, one-sided missing
DP/AD, AD greater than DP, sample mismatches, partition overlap, duplicate
candidate IDs, or receipt/count inconsistencies fail.

The approved provisional legacy mapping is:

```text
FWD_like -> legacy neg -> compatible + transcripts -> complement genomic REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain genomic REF/ALT
orientation_policy=legacy_provisional_v1
```

This policy is retained for legacy compatibility and is not biologically
validated. The deterministic sites table has these fixed metadata columns:

```text
partition_id
candidate_id
orientation
chromosome
position
alt_index
genomic_ref
genomic_alt
rna_ref
rna_alt
annotation_strand
gene_ids
transcript_ids
is_cds
is_five_prime_utr
is_three_prime_utr
is_exon
is_intron
qual
filter
info_alt_depth
orientation_policy
```

They are followed by all `DP__<sample>` columns, then all `AD__<sample>`
columns, then all `AF__<sample>` columns in sample-manifest order. Candidate
IDs are `orientation|chromosome|position|REF>ALT` and do not include the
partition ID, allowing overlap/duplicate detection across the declared
universe. Intergenic candidates are retained with `NA` annotation identifiers
and false feature flags.

Published output contract:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The input receipt schema is:

```text
cohort_id, partition_id, selector_type, selector_value, orientation,
step07_receipt_path, step07_receipt_sha256, vcf_path, vcf_sha256,
sample_manifest_sha256, partition_manifest_sha256, annotation_gtf,
annotation_gtf_sha256, sample_count, declared_vcf_record_count,
observed_vcf_record_count, observed_alt_allele_count, supported_snv_count,
skipped_symbolic_count, skipped_non_snv_count, published_candidate_count,
orientation_policy
```

The summary schema is:

```text
cohort_id, partition_count, step07_receipt_count, input_vcf_count,
sample_count, observed_vcf_record_count, observed_alt_allele_count,
supported_snv_count, skipped_symbolic_count, skipped_non_snv_count,
published_candidate_count, sample_manifest_sha256,
partition_manifest_sha256, annotation_gtf, annotation_gtf_sha256,
orientation_policy
```

For every input and for the cohort summary, observed alternate alleles equal
supported SNVs plus skipped symbolic plus skipped non-SNV alleles, and
published candidates equal supported SNVs. Receipt rows follow partition
manifest order with `FWD_like` then `REV_like`; the sites table follows the
same declared order and VCF record/ALT order.

Execute mode uses an owned cohort lock, run-token temporary and backup paths,
stable hashes, validation before publication, cleanup, and rollback. Existing
stable outputs must be all three present or all three absent. It publishes the
sites table, then summary, then the input receipt last as the transaction
commit marker. Header-only input VCFs and a header-only sites table are valid
when all counts reconcile.

The active shell test covers wrapper CLI and dry-run behavior, exact input
enumeration, locks, cleanup, validation, publication order, and rollback with a
fake R executable. The real-R fixture suite covers semantic VCF/GTF parsing,
multiallelic mapping, annotation, deterministic ordering, count reconciliation,
header-only inputs, and strict failures. `make real-r-test` reports `SKIP` on
this workstation because `Rscript` is unavailable; that skip is not real-R
validation.

Cluster-proof exit contract: both real-R fixture suites must pass in the same
supported batch-visible environment used for execution. One successful
three-file transaction over the primary universe must contain exactly 50
input-receipt rows in partition-manifest order with `FWD_like` then
`REV_like`; schemas, immutable hashes, exact sample columns, candidate
uniqueness, and all per-input/summary count invariants must reconcile; the job
must be `COMPLETED 0:0`; and no owned lock or run-token residue may remain.

### Step 09

Step `09` is implemented locally at implementation commit `e4371de`. The
shell/fake-R suite and complete local repository gate pass, including 23 Python
tests and shell tests through Step `09`. The real-R fixture runner reports
`SKIP` because this workstation has no `Rscript`; that skip is not semantic R
validation. No cluster dry-run, execute job, log, or output evidence has been
inspected, and Step `09` is not cluster-proven.

Implemented entry points and active tests:

```text
scripts/step_09_cmh_editing_site_calling.sh
scripts/step_09_cmh_editing_site_calling.R
jobs/step_09_cmh_editing_site_calling.slurm
tests/shell/test_step_09_cmh_editing_site_calling.sh
tests/r/run_step_09_cmh_tests.sh
tests/r/test_step_09_cmh_editing_site_calling.R
configs/step_09_pairs.NORAD_EV_PUM1.tsv
```

Public shell CLI:

```text
scripts/step_09_cmh_editing_site_calling.sh
  --analysis-id ANALYSIS_ID
  --cohort-id COHORT_ID
  --sample-manifest SAMPLE_MANIFEST
  --partition-manifest PARTITION_MANIFEST
  --step08-root STEP08_ROOT
  --output-root OUTPUT_ROOT
  [--control-condition EV]
  [--treatment-condition PUM1]
  [--rna-ref A]
  [--rna-alt G]
  [--min-sample-dp 1]
  [--mean-dp-threshold 50]
  [--fdr-threshold 0.05]
  [--common-or-threshold 1.2]
  [--absolute-difference-threshold 0.005]
  [--background-condition CONDITION]
  [--background-max-fraction 0.01]
  [--rscript-bin RSCRIPT_BIN]
  [--r-script R_SCRIPT]
  [--execute]
```

Dry-run is the default. It resolves an executable `Rscript`, validates the
manifests, explicit replicate pairs, exact Step `08` input set, receipt
order/counts/hashes, sample columns, candidate uniqueness, and count/AF
consistency, then prints the exact R command. It does not invoke R, acquire a
lock, or create the output directory. Therefore even a real dry-run requires a
supported `Rscript`; fake-R tests prove wrapper behavior only.

The generic manifest validator accepts optional `replicate` without breaking
earlier manifests. Step `09` requires one control and one treatment per
explicit replicate, identical control/treatment replicate sets, and at least
two strata. Pairing comes from the full sample manifest only. That same
replicate-bearing manifest must be used before Step `07`, so its SHA-256 hash
propagates through the complete Steps `07`-`09` chain.

For every target row with complete counts and per-sample depth at least the
configured minimum, the base-R engine builds treatment/control by
edited/unedited tables for each manifest-defined stratum and runs:

```text
mantelhaen.test(..., alternative="two.sided", correct=TRUE, exact=FALSE)
```

The common odds ratio is treatment relative to control. BH is applied exactly
once across all successfully tested target candidates from every declared
partition and both orientations, before mean-depth, background, FDR, or effect
call filters. Missing, low-coverage, degenerate, and non-target candidates
remain in the all-sites table.

Default call contract:

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

Background filtering is disabled unless an explicit condition different from
control and treatment is supplied. When enabled, every background sample must
have complete counts, adequate depth, and AF strictly below `0.01` by default;
equality fails. EV is never repurposed as a missing no-dox cohort.

Published output contract:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

All-sites preserves every Step `08` row and order. Significant-sites is the
deterministic ordered subset whose call is `significant_up` or
`significant_down`. Their fixed 42-column prefix is:

```text
analysis_id, partition_id, candidate_id, orientation, chromosome, position,
alt_index, genomic_ref, genomic_alt, rna_ref, rna_alt, annotation_strand,
gene_ids, transcript_ids, is_cds, is_five_prime_utr, is_three_prime_utr,
is_exon, is_intron, qual, filter, info_alt_depth, orientation_policy,
control_condition, treatment_condition, target_rna_change, replicate_count,
test_status, call_status, background_condition, background_status,
min_analysis_dp, mean_analysis_dp, mean_control_af, mean_treatment_af,
treatment_control_difference, max_background_af, cmh_statistic,
cmh_degrees_freedom, cmh_p_value, cmh_fdr_bh, common_odds_ratio
```

Those fields are followed by manifest-ordered `DP__<sample>`, then
`AD__<sample>`, then `AF__<sample>` columns. Exact vocabularies are:

```text
test_status:
  not_target_change | missing_counts | low_coverage | degenerate_table | tested
call_status:
  not_tested | below_mean_dp | background_not_passed | fdr_not_met |
  effect_not_met | significant_up | significant_down
background_status:
  disabled | pass | missing_counts | low_coverage | fail_fraction
```

The one-row summary has 39 fixed fields covering identity, counts, input paths
and hashes, thresholds, `multiple_testing_method=BH`,
`cmh_alternative=two.sided`, continuity correction, and the provisional
orientation policy. The nine-column mutation table always emits the 12 ordered
canonical substitutions:

```text
A>C A>G A>T C>A C>G C>T G>A G>C G>T T>A T>C T>G
```

The mutation plot reports candidate counts. The depth/delta plot uses
successfully tested targets with log mean-depth on x and treatment-control AF
on y. Both PDFs use a fixed 7-by-5-inch base-R device, are signature/EOF
validated, and remain valid for empty input. Step `09` retains
`orientation_policy=legacy_provisional_v1`; this is not biologically
validated.

Execute mode requires either all six existing outputs or none, uses an owned
analysis lock and run-token temporary/backup paths, checks immutable inputs,
validates and reconciles every temporary output, then publishes five outputs
and the summary last as the commit marker. Final hashes and content are
revalidated. Failure before commit restores the prior complete set. If
rollback is incomplete, the owned lock remains for explicit operator recovery.

Cluster-proof exit contract: one inspected default-analysis job must be
`COMPLETED 0:0` and publish one reconciled six-file transaction. The all-sites
row count must equal the Step `08` candidate count; significant-sites must be
the exact ordered `significant_up`/`significant_down` subset; summary must have
one row; mutation spectrum must have 12 rows; statuses, hashes, thresholds,
and background-disabled state must reconcile; both PDFs must pass `%PDF-` and
`%%EOF` checks; and no owned lock or run-token residue may remain. This proves
the computation, not the biological validity of `legacy_provisional_v1`.

## Post-Step 09 Scientific Validation Gate

This planned evidence-and-decision package is outside the core Steps
`00a`-`09` computation and is not a runnable Step `10`. It begins only from a
clean, pushed `validate-step-09` branch with inspected production outputs:

```text
validate-step-09
└── step-09b-scientific-validation
```

Required evidence categories:

1. **Orientation policy.** Independently derive the relationship among legacy
   flag groups, transcript strand, genomic/RNA alleles, and raw counts from
   library protocol, RSeQC, and predeclared plus-strand and minus-strand
   transcript loci in the BAMs. Compare the current and inverted policies.
   A>G enrichment is
   supporting evidence only, not a circular proof. Record a locus-audit TSV
   with flags, transcript strand, genomic/RNA alleles, raw counts, expected
   mapping, and concordance, then decide whether to retain
   `legacy_provisional_v1` or introduce a versioned replacement.
2. **Annotation provenance and semantics.** Fix the annotation file identity,
   path, SHA-256, and Novogene delivery provenance. Record the exact release
   if recoverable; otherwise explicitly retain the unresolved release as an
   accepted limitation. Audit plus-strand and minus-strand transcript loci
   across CDS, UTR, exon, intron, intergenic, overlapping-gene, and
   multi-transcript cases. Quantify multiple assignments and decide whether
   collapsed flags suffice or a transcript-level table is required.
3. **Production QC funnel.** Reconcile Step `07` records through Step `08`
   exclusions to Step `09` test/call statuses by partition and orientation;
   review mutation spectrum/orientation balance and per-sample DP/AF
   distributions. These are pileup-derived candidates, not genotype calls.
4. **Statistical robustness.** Freeze the legacy primary defaults and
   predeclare sensitivity analyses rather than tuning for hits. Review
   per-replicate AF/delta, leave-one-pair-out results, modest DP/effect
   alternatives, the unweighted mean-sample-AF effect metric, `ABE_EV_2`
   mapping behavior, and replicate `4` duplication. Record a threshold matrix,
   leave-one-out table, replicate-direction concordance/discordance and its
   interpretation, and a PI-approved primary threshold decision. Every
   sensitivity run uses a distinct analysis ID and never overwrites the
   primary transaction. A min-sample-DP, pairing, target, or testability change
   recomputes BH over that run's complete applicable tested family.
5. **Candidate adjudication.** Review the predeclared top up/down, discordant,
   and near-threshold sets for coverage, base/mapping quality, read-position
   and splice bias, repeats/multimapping, duplicates, nearby indels,
   annotation ambiguity, and known polymorphisms. Record pass/flag/reject,
   reason, reviewer, and evidence. Record whether matched DNA exists; when it
   does not, retain that limitation. Candidate review is not orthogonal
   experimental validation.
6. **Background decision.** Determine whether a genuine distinct comparable
   no-dox/rABE-negative cohort exists. If not, record background disabled/no
   eligible cohort; EV is never substituted. Adding a background changes the
   sample-manifest hash and requires Steps `07`-`09` regeneration. Separately
   review whether the legacy all-background-samples AF `<0.01` rule is
   scientifically intended.

Before inspecting concordance or candidate rankings, freeze a reproducible
evidence plan that defines deterministic locus/candidate selection, sample
size, coverage of both orientations and plus/minus transcript strands, the
sensitivity grid and decision thresholds, required input hashes, git commit,
commands/scripts and software versions, reviewer/date/decision owner, and
current/superseded analysis IDs.

Keep production-derived evidence tables in approved results storage. The
evidence docpatch records compact non-sensitive summaries plus paths and
hashes; it must not commit biological result TSV snapshots without explicit
approval.

The gate has two outcomes:

```text
science_review_complete_exploratory
  evidence and decisions recorded; results remain provisional

biological_interpretation_ready
  runtime proof plus validated orientation policy, accepted annotation
  provenance/limitations, approved primary thresholds, reviewed replicate
  sensitivity, candidate adjudication, and recorded background/DNA decisions
```

Exploratory completion may unlock operational/provenance/artifact tooling, but
not biological candidate claims. If the gate changes policy, inputs, or code,
use this rerun matrix:

| Change | Required action |
| ------ | --------------- |
| sample manifest or partition universe | rerun Steps `07`-`09` through a gated config/evidence package |
| Step `07` filter or maximum depth | first make a gated contract/versioning decision because current receipts do not record these parameters; use a distinct cohort/output namespace or extend provenance, then rerun Steps `07`-`09` |
| newly added background samples | first prove their required Steps `01`-`06` inputs, then rerun Steps `07`-`09` |
| background condition already present in unchanged Step `08` sample columns | rerun Step `09` under a new analysis ID |
| GTF input | rerun Steps `08`-`09` |
| orientation normalization policy | separately gated Steps `08`-`09` contract/code/test/docpatch change, then rerun Steps `08`-`09` |
| supported Step `09` target, unchanged-manifest contrast/background selection, minimum DP, or threshold defaults | rerun Step `09` under a new analysis ID and recompute BH over the complete applicable family |
| CMH method/correction or testability logic | separately gated Step `09` implementation/fix with tests and docpatch, then a new analysis ID and runtime validation with full applicable-family BH |
| FASTA/reference coordinates | perform an upstream reference/alignment impact review; do not assume Step `07`-only regeneration |
| manual adjudication labels only | no compute rerun; a new automated filter requires a separate implementation/test/docpatch package |

Any required implementation/fix receives tests and a separate docpatch before
runtime reruns. An evidence-only package uses an evidence/status docpatch
without fabricating an implementation commit.

## Reference Workflow Alignment

Steps `04`-`09` are based on the uploaded/reference RNA-editing workflow:

```text
MarkDuplicates
-> SplitNCigarReads
-> split BAM by read orientation
-> bcftools mpileup
-> VCF preprocessing
-> CMH editing-site calling
```

This repository is rebuilding that workflow in a cleaner SLURM/script/testable structure rather than using the hardcoded original scripts directly.

The old workflow split read orientation using samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

Because Step `03` confirms reverse-stranded / first-strand behavior across the
cohort, Step `07` preserves `FWD_like` and `REV_like` as
read-orientation/mechanical flag groups. Step `08` records the explicit
provisional `legacy_provisional_v1` mapping, and Step `09` preserves it.
Neither implementation nor local testing biologically validates that mapping.

## Future Artifact And Reporting Layer

This layer is planned, deferred, and non-runnable. It is not a new core pipeline step and is not a runnable Step `10`. The existing Steps `00a`-`09` remain the core computational pipeline.

The ordered future separation is:

```text
proven computation and scientific policy
    -> artifact-schema-v1
    -> artifact-adapters-v1 over existing receipts/summaries
    -> artifact-run-summary
    -> report-html-v1
    -> report-exports-v1
```

The schema must define completed, attempted, failed, missing, incomplete, and
rerun states plus run IDs, versions, paths, and hashes. Read-only adapters
come before any native sidecar retrofit and must preserve existing compute
CLIs and output paths. Native per-step JSON emitters may be considered only
after the adapters prove the schema. A future layout may look like:

```text
results/
  bam/ABE_EV_2/ABE_EV_2.sorted.bam
  bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai

  artifacts/
    ABE_EV_2/
      01_star_align.json
      02_sort_index.json
      02b_bam_qc.json
      03_strandedness.json
      04_mark_duplicates.json
      ...
    run_summary.json

  reports/
    run_report.html
    run_report.pdf
    run_summary.tsv
```

Future sidecars should use a consistent, versioned JSON schema. The minimum shared fields are expected to include:

```text
schema version
pipeline version or git commit
run ID
step ID/name
sample ID when applicable
status
timing
inputs
outputs
tool names and versions
resolved parameters
key metrics
warnings
exit status
```

The future aggregation phase should discover or receive expected sidecars, validate schema versions, combine sample-level and run-level information, record missing/failed/incomplete steps explicitly, and write:

```text
results/artifacts/run_summary.json
```

The future report layer should read only structured artifacts and final result tables. It must not require rerunning STAR, samtools, Picard, GATK, bcftools, or CMH computation.

Compute outputs and rendering outputs should stay separate: core steps write BAMs, indexes, metrics, VCF-like tables, and CMH result tables; the reporting layer consumes those outputs plus structured artifacts to produce human-readable summaries.

Initial report targets:

```text
results/reports/run_report.html
results/reports/run_report.pdf
results/reports/run_summary.tsv
```

Jinja2 may be a good fit for HTML rendering. Quarto or R Markdown may be useful for publication-quality biological figures and PDF output. The renderer layer should remain replaceable without modifying compute steps.

Step `09` CMH/editing-site results should eventually receive a richer, domain-specific artifact schema rather than being flattened into generic key/value metrics. That schema may include:

```text
comparison definitions
editing type
filter thresholds
site counts
significant up/down site counts
effect-size summaries
coverage summaries
result-table paths
plot paths
annotation/reference metadata
multiple-testing method
```

## Future Architecture: Core Preprocessing, Analysis Modules, and Reporting

This architecture is a deferred design direction. It must not block the
current `step-09a-roadmap-docpatch`, upstream-first runtime promotion, or the
post-Step-09 scientific evidence gate.

A compact visual version of this deferred design lives at `docs/architecture/FUTURE_ARCHITECTURE.md`.

The long-term shape is:

```text
FASTQs + manifest
        ->
core preprocessing pipeline
        ->
validated analysis-ready artifacts
        ->
assay-specific analysis modules
        ->
standardized result artifacts
        ->
reporting layer
        ->
configured lab-facing reports
```

The core preprocessing pipeline should eventually be able to ingest arbitrary FASTQ files placed on ADAM, plus a sample manifest, and robustly process them through reusable preprocessing and QC stages. Core responsibilities include manifest validation, reference validation/prep, alignment, canonical BAM publication, BAM QC, strandedness inference, duplicate marking, SplitNCigarReads, and optional orientation-aware preprocessing when required by an analysis module.

Steps `00a`-`06` currently form the validated preprocessing backbone for this project. Step `06` may eventually be treated as an optional prerequisite for orientation-aware analysis modules rather than a universal requirement for every RNA-seq analysis.

This architecture would support current lab-generated datasets first, but the same model could later support independent analysis of public genomics datasets. Public FASTQs or derived inputs should still enter through the same manifest/config/provenance system rather than bypassing the pipeline contracts. Examples include public repositories such as SRA, GEO, ENA, or other public genomics archives.

The intended separation is:

* The manifest describes what data exist.
* The analysis config describes what to do with those data.

Example manifest fields:

```text
sample_id
condition
replicate
fastq_r1
fastq_r2
batch
notes
```

Illustrative analysis config fields:

```yaml
analysis_module: rna_editing_cmh
reference: novogene_ref
contrast:
  control: EV
  treatment: PUM1
strandedness_policy: infer_or_validate
orientation_policy: preserve_legacy_mechanical_labels
filters:
  min_alt_depth: null
  min_total_depth: null
reports:
  - qc_summary
  - editing_candidates
```

These examples are design notes only. They do not create a real config interface yet.

Bundled analysis modules should conceptually live outside the reusable preprocessing core. For this project, the first likely module is `rna_editing_cmh`. It would consume validated core artifacts, the sample manifest, and an explicit analysis config; it would produce mpileup/VCF artifacts, preprocessed analysis tables, CMH/editing-site result tables, module-specific QC summaries, and report-ready summaries.

Step `07` now provides the locally tested cohort/partition mpileup boundary,
Step `08` provides the locally shell/fake-R-tested preprocessing boundary, and
Step `09` provides the locally shell/fake-R-tested paired-CMH boundary. All
three reproduce the legacy path conservatively but remain upstream-gated for
real-runtime and cluster promotion before any major modular refactor.

Core preprocessing should preserve mechanical labels such as `FWD_like` and `REV_like`. Mapping those groups to `pos`, `neg`, sense, antisense, or edit direction belongs in the assay-specific analysis module and must be explicit in config or PI-approved. Incorrect strand/orientation interpretation can produce plausible-looking but biologically wrong results. As above, `samtools view -f FLAG` means a record has all bits in `FLAG`; it is not exact flag equality.

Future runs should eventually record the manifest used, analysis config used, git commit, reference version/paths, tool versions, sample set, step statuses, and output paths. Future artifacts should ideally include machine-readable indexes such as:

```text
run_summary.json
artifacts.tsv
qc_summary.tsv
```

The reporting layer should eventually ingest the structured artifact directory and generate configured reports such as QC summaries, preprocessing validation reports, runtime/provenance summaries, assay-specific candidate result reports, and PI/demo summaries.

Assay modules should refuse to run when required metadata or config is missing, such as missing condition labels, missing replicate structure, missing contrast definition, missing orientation policy, or inconsistent strandedness assumptions.

## Future Cross-Cutting Engineering Roadmap

Deferred engineering improvements are tracked canonically in `TODO.md`. They
are not current blockers. Activate them only after runtime and scientific
gates, in this dependency order. The package IDs below are candidate labels
until separately approved; the order is fixed. Promotion-specific environment,
reference, and storage evidence is collected manually now, while these later
packages productize the checks for future runs/cohorts:

1. `post09-runtime-preflight`: read-only tool/runtime/package probe; no
   installation and no replacement for per-step validation.
2. `post09-reference-provenance`: FASTA/GTF/BED/FAI/DICT/STAR-index identity,
   checksums, annotation release, and contig agreement.
3. `post09-storage-inventory-retention`: read-only size/quota/scratch inventory,
   then an approved retention matrix; no cleanup.
4. `post09-validation-reports`: step-specific read-only validators first,
   including Step `00a`/`00b` shell coverage; no generic dispatcher first.
5. `post09-targeted-reruns`: manifest-driven rerun planning/submission after
   validators stabilize; arrays only after repeated operational need.
6. `artifact-schema-v1`, `artifact-adapters-v1`, and
   `artifact-run-summary`, in that order.
7. `report-html-v1`, then `report-exports-v1`.
8. `analysis-config-v1`: manifest=data, config=analysis, with required
   contrast, replicate, reference, strandedness/orientation, and filter policy.
9. `rna-editing-cmh-module`: a thin orchestration layer around proven Steps
   `07`-`09`, preserving existing CLIs/paths and treating Step `06` as an
   optional prerequisite for orientation-aware modules.
10. General reusable-core refactoring only after a second real cohort, and
    public SRA/GEO/ENA ingestion last through the same contracts.

Every activated package is a linear descendant of the latest clean, pushed
docpatched branch. An implementation package receives an implementation
commit plus separate docpatch; a documentation/evidence-only package receives
one documentation commit, validation, clean-history inspection, and push.
Premature work includes generic dispatchers/arrays, broad shared-library
extraction, automatic R installation, unproven tool-path config, automatic
cleanup/stale-lock deletion, moving proven scripts, report globbing or compute
reruns, and public importers.

## Current Next Work

1. Before Step `07`, establish the absent-from-this-checkout cluster runtime
   `samples.tsv` with explicit replicates and one immutable hash; resolve the
   compute-node `Rscript`/packages/hash utilities and pass both real-R suites;
   verify Step `06` BAM/BAI inputs, FAI selectors including `MT`,
   storage/quota, logs, and provisional resources.
   If repository manifest/config content must change, insert a gated
   `step-07a-runtime-manifest`-style descendant with a config/validation commit
   and separate docpatch; do not alter config on the evidence-only
   `validate-step-07` branch. A byte-identical cluster-local copy is recorded
   as provenance evidence instead.
2. Create `validate-step-07` from the clean/pushed
   `step-09a-roadmap-docpatch`, run pilot then chromosome `1` then the remaining
   24 primary partitions, meet the 25-receipt/50-VCF exit, evidence-docpatch,
   and push.
3. Create `validate-step-08`, meet the three-file/50-row exit,
   evidence-docpatch, and push.
4. Create `validate-step-09`, meet the six-file reconciled exit,
   evidence-docpatch, and push.
5. Create `step-09b-scientific-validation`, complete the evidence/decision
   gate above, and only then consider the ordered post-proof packages.

## Local Validation Gate

Run from the local repo root:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
make real-r-test
git status --short
git diff --name-status
```

`make real-r-test` runs the Step `08` and Step `09` suites. Either runner may
report `SKIP` when the default `Rscript` executable is unavailable; each skip
is a recorded runtime-validation gap, not a semantic pass. An explicit bad
runtime override fails.

## Known Cluster Notes

* `logs/` must exist before `sbatch`.
* Use `TMPDIR=/tmp` for the general SLURM wrapper convention.
* Step `05` GATK work must route Java/HTSJDK/GATK temp files to project storage, not node-local `/tmp`.
* The bcftools `1.21` executable probe on `node002` confirms tool availability only. It is not Step `07` dry-run, execute, output, or cluster-proof evidence.
* Before Step `07` execute mode, compare every approved partition selector with the actual Novogene `genome.fa.fai`; the tracked primary set includes `MT`, whose exact reference spelling has not yet been runtime-confirmed.
* The cluster may warn that `/local/tmp` is not writable and fall back to `/tmp`; this has not been fatal.
* `module list` writes to stderr, so scripts should use `module list 2>&1 || true`.
* Known useful modules include `star/2.7.11b`, `samtools/1.19.2`, `bedtools/2.31.1`, `picard/3.1.1`, `python39`, and `java/17.0.10`.
* Step `04` validates the selected Java executable and actual runtime version; loading a module or reading `JAVA_HOME` alone is not enough.
* RSeQC is available through `.venv/bin/infer_experiment.py`.
* GATK is available at `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the confirmed version is `4.6.1.0`.
* bcftools is available at `/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools`; the confirmed version is `1.21`.
* The GATK/bcftools tool probe succeeded on `node002` with exit code `0:0`; `node002` used OpenJDK `17.0.14`.
* The Java inconsistency remains relevant: `node002` and `node003` have provided Java 17, while `node007` previously exposed Java 11 / a missing Java 17 path.
