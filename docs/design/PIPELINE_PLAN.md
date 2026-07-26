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
| `08` | Preprocess the exact Step `07` receipt set for editing-site statistics. | partition manifest; Step `07` VCFs and receipts; sample manifest; Novogene GTF | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, input receipt, and QC summary | implemented locally; shell/fake-R and guarded real-R suites pass locally; raw-count lexical validation hardened; no cluster evidence; not cluster-proven | R / Bioconductor |
| `09` | Run paired CMH editing-site calling and write summaries. | Step `08` table and input receipt; paired-replicate sample manifest; partition manifest | four tables and two plots under `results/editing/<analysis>/` | implemented locally; shell/fake-R and guarded real-R suites pass locally; locale-independent raw-byte PDF fixture validation; no cluster evidence; not cluster-proven | base R |
| `09c` | Validate and summarize explicit scientific-review evidence without rerunning analysis. | sample/partition manifests; exact Step `08` transaction; Step `09` analysis directory; review plan; evidence manifest | 13 TSVs under `results/scientific_validation/<review_id>/`, with review summary last | implemented locally at `b674a31`; Python/shell synthetic fixtures pass; production evidence/review and cluster validation unavailable; no biological-readiness claim | Python / shell |

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

Step `08` was implemented locally at implementation commit `90335d8` and
hardened on `step-09b1-real-r-fixes` at `eae5eca`. The shell wrapper and its
publication transaction pass the fake-`Rscript` suite, and the semantic
fixture suite passes under the guarded local R environment without `SKIP`.
The earlier generic negative-fixture failure was misdiagnosed as a
partition-overlap defect: expected-reason assertions confirmed that overlap
rejection already worked. The actual defect was permissive semantic-parser
coercion of malformed raw count tokens, now rejected by a lexical preflight.
No cluster dry-run, execute job, log, or output evidence has been inspected;
Step `08` is not cluster-proven.

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
otherwise. Before semantic VCF parsing, a bounded-memory streaming lexical
preflight requires FORMAT/DP to contain one non-negative integer or `.`, and
allows FORMAT/AD and present INFO/AD to be a single `.` when the entire vector
is missing. Otherwise, each AD value must contain exactly one token for REF
plus one for every ALT, with each token a non-negative integer or `.`.
This fail-closed pass prevents malformed tokens from being silently coerced
into parsed numeric values by the semantic parser. The implementation then
imports the project Novogene GTF directly, expands each multiallelic record by
ALT index, and extracts the matching alternate AD. Symbolic and non-SNV
alleles are counted and excluded rather than truncated. Missing FORMAT
definitions, malformed or negative counts, one-sided missing DP/AD, AD greater
than DP, sample mismatches, partition overlap, duplicate candidate IDs, or
receipt/count inconsistencies fail.

The lexical preflight intentionally adds one complete streaming read of every
VCF before `VariantAnnotation` parses it. Memory use is bounded, but the added
I/O has not been measured on production inputs. Record elapsed time and input
size for this pass during the first supported Step `08` pilot benchmark and
again during primary-universe cluster validation before claiming acceptable
production scaling.

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
header-only inputs, partition overlap, and strict raw FORMAT/DP, FORMAT/AD,
and INFO/AD failures. Negative fixtures identify their mode and selected
contracts assert the expected failure reason, preventing another generic
failure from being attributed to the wrong case. The complete suite passes
without `SKIP` in the local pinned runtime.

Cluster-proof exit contract: both real-R fixture suites must pass in the same
supported batch-visible environment used for execution. One successful
three-file transaction over the primary universe must contain exactly 50
input-receipt rows in partition-manifest order with `FWD_like` then
`REV_like`; schemas, immutable hashes, exact sample columns, candidate
uniqueness, and all per-input/summary count invariants must reconcile; the job
must be `COMPLETED 0:0`; and no owned lock or run-token residue may remain.

### Step 09

Step `09` was implemented locally at implementation commit `e4371de` and its
fixture was hardened on `step-09b1-real-r-fixes` at `eae5eca`. The
shell/fake-R suite and complete local repository gate pass, including 23
Python tests and shell tests through Step `09`. The real-R fixture runner now
passes without `SKIP` under the guarded local runtime. Its former
locale-sensitive raw-to-text PDF EOF assertion was a test defect, not a
corrupt-PDF finding; the fixture now searches for `%PDF-` and `%%EOF` as raw
bytes. No cluster dry-run, execute job, log, or output evidence has been
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

## Local R Runtime: Step 09b

The `step-09b-local-r-runtime` package establishes a guarded, reproducible
local R environment without changing any compute wrapper into a package
installer.

Verified host runtime:

```text
R: 4.6.1, official CRAN Apple-silicon package
published SHA-1: fc9f4ada15589e8e037b9bf05563d21e97181635
signature: valid Developer ID Installer signature
notarization: accepted
renv: 1.2.3
Bioconductor: 3.23
```

The repository-local lock contains the eight direct Step `08` namespaces and
their transitive closure:

```text
VariantAnnotation
GenomicRanges
IRanges
S4Vectors
SummarizedExperiment
GenomeInfoDb
BiocGenerics
rtracklayer
```

Activation is opt-in only:

```text
NORAD_USE_RENV=1
```

The guarded `.Rprofile` does not activate the project library otherwise.
SLURM and compute wrappers never restore, bootstrap, or install packages.
Explicit local interfaces are:

```text
RSCRIPT_BIN=/usr/local/bin/Rscript NORAD_USE_RENV=1 make r-restore
RSCRIPT_BIN=/usr/local/bin/Rscript NORAD_USE_RENV=1 make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript NORAD_USE_RENV=1 make local-real-r-test
```

The normal restore and a cache-disabled restore into an empty temporary
library both passed using binary packages. Namespace loading,
`BiocManager::valid()`, `renv::status()`, and headless PDF creation also
passed. After the `step-09b1-real-r-fixes` hardening, the Step `08` and Step
`09` real-R suites both pass without `SKIP` under the guarded local runtime.
The CSU batch-visible R path and packages remain unresolved. This evidence is
local only and does not make Steps `07`-`09` cluster-proven.

## Step 09c Scientific-Validation Tooling

The `step-09c-scientific-validation` package is implemented locally at
`b674a31`. It is outside the core Steps `00a`-`09` computation and is not a
runnable Step `10` or a SLURM stage. It is local, dry-run-first evidence
tooling: it validates and summarizes explicit evidence but does not rerun CMH
statistics, infer reviewer decisions, or claim production scientific
validation.

Implemented files and active fixtures:

```text
scripts/step_09c_scientific_validation.sh
scripts/step_09c_scientific_validation.py
configs/step_09c_review_plan.example.tsv
configs/step_09c_evidence_manifest.example.tsv
configs/step_09c_evidence_schemas/
tests/fixtures/step09c/build_fixture.py
tests/test_step_09c_scientific_validation.py
tests/shell/test_step_09c_scientific_validation.sh
```

Public interface:

```text
scripts/step_09c_scientific_validation.sh
  --review-id REVIEW_ID
  --sample-manifest SAMPLE_MANIFEST
  --partition-manifest PARTITION_MANIFEST
  --step08-sites STEP08_SITES
  --step08-inputs STEP08_INPUTS
  --step08-summary STEP08_SUMMARY
  --step09-analysis-dir STEP09_ANALYSIS_DIR
  --review-plan REVIEW_PLAN
  --evidence-manifest EVIDENCE_MANIFEST
  --output-root OUTPUT_ROOT
  [--execute]
```

Atomic output contract:

```text
results/scientific_validation/<review_id>/
  <review_id>.step09c_review_plan.tsv
  <review_id>.step09c_evidence_index.tsv
  <review_id>.step09c_orientation_locus_audit.tsv
  <review_id>.step09c_annotation_audit.tsv
  <review_id>.step09c_qc_funnel.tsv
  <review_id>.step09c_replicate_effects.tsv
  <review_id>.step09c_sensitivity_matrix.tsv
  <review_id>.step09c_leave_one_pair_out.tsv
  <review_id>.step09c_candidate_selection.tsv
  <review_id>.step09c_candidate_adjudication.tsv
  <review_id>.step09c_decisions.tsv
  <review_id>.step09c_limitations.tsv
  <review_id>.step09c_review_summary.tsv
```

The summary is published last as the transaction marker. Input records include
paths, SHA-256 hashes, row counts, evidence IDs, analysis IDs, reviewers,
owners, dates, policy versions, and preregistered selection/sensitivity rules.
Only schemas, examples, and synthetic fixtures are committed; production
evidence stays under ignored results storage.

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

Step `09c` keeps computational status separate from scientific state.
Computational status distinguishes implementation, local tests, runtime
blocking, cluster dry-run, and cluster proof. Evidence-category status is one
of `missing`, `incomplete`, `complete`, or justified `not_applicable`;
orientation status is `provisional`, `validated`, or
`replacement_required`. Background, matched-DNA, orthogonal-evidence,
annotation, threshold, and adjudication decisions remain separate dimensions.

The only science states Step `09c` may publish are:

```text
evidence_incomplete
  required evidence or decisions remain incomplete

science_review_complete_exploratory
  evidence and decisions recorded; results remain provisional
```

`biological_interpretation_ready` is reserved and Step `09c` must reject it
until a separate approved scientific-policy branch defines and unlocks its
exit criteria. Local Step `09c` completion means implemented and
fixture-tested, not completion of a production scientific review.
`science_review_complete_exploratory` permits only explicitly provisional
reporting and never biological candidate claims. If later inspected evidence
changes policy, inputs, or code, use this rerun matrix:

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

Current local evidence: dry-run creates no output directory or stable files;
execute-mode fixtures publish exactly 13 validated TSVs with the review
summary last; and active Python/shell tests cover incomplete and exploratory
states, reserved-state rejection, unrelated-file immunity, input/hash
mutation, exact output publication, locks, cleanup, and rollback. The complete
repository Python, shell, guarded real-R, and R-environment gates pass at this
implementation boundary. No production Step `07`-`09` transaction or Step
`09c` evidence package is recorded or supported by inspected evidence, so
production science remains `evidence_incomplete`.

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

## Immediate Artifact, Run-Summary, And Reporting Slice

This layer is the approved immediate local implementation sequence after
Step `09c`; it is no longer deferred behind remote promotion. It remains
outside the core Steps `00a`-`09` computation and none of its packages is a
runnable Step `10`. `artifact-schema-v1` is implemented and locally
fixture-tested at `5f4d3b4`; the remaining packages below are approved but
not yet implemented:

```text
artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
```

`artifact-schema-v1` provides a shared common schema plus four public JSON
Schema Draft 2020-12 contracts for artifact records, scientific-review
records, run summaries, and report receipts. The tracked synthetic
expected-artifact inventory has 67 concrete physical-artifact rows and this
exact header:

```text
artifact_id
step_id
scope_type
scope_id
adapter
source_path
required
```

Inputs are never discovered by glob. Inventory paths are repository-root
relative concrete paths; wildcard/template/traversal forms and canonical
aliases are rejected. Rows use stable order, and rows for the same
step/scope are contiguous. Execution attempt, implementation, local testing,
runtime validation, cluster validation, warnings/errors, paths/hashes, tools,
parameters, metrics, and scientific state remain separate fields.

A `run_id` identifies an immutable manifest/reference/partition/primary-
analysis contract. The canonical contract hash is SHA-256 over compact,
sorted-key UTF-8 JSON containing the sample-manifest, reference-contract,
partition-manifest, primary-analysis ID, and primary-analysis-policy
components. Identical-input retries have distinct `attempt_id` values;
connected attempt histories and status/evidence dimensions are reconciled.
Any input or policy hash change requires a new `run_id`.

The read-only validator checks the schemas, inventory, and synthetic
documents. It rejects duplicate JSON keys, non-standard numeric constants,
inconsistent physical path/hash identities, unsupported status/evidence
claims, disconnected retry histories, and the currently reserved
`biological_interpretation_ready` science state. Its typed evidence roles
prevent local tests or tool probes from being represented as runtime or
cluster proof. A passing schema check does not inspect source artifacts,
execute an adapter, maintain the future stateful run-ID registry, or produce
anything under `results/`.

Current validation interface:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
```

`artifact-adapters-v1` adds read-only adapters over existing Step `00a`-`09`
outputs, receipts, summaries, and Step `09c` review records. Missing, failed,
incomplete, or externally unavailable evidence is emitted explicitly rather
than omitted. Existing compute CLIs and paths remain unchanged; no native
per-step JSON retrofit is part of this slice. Atomic outputs are:

```text
python scripts/build_artifact_index.py
  --run-id RUN_ID
  --inventory INVENTORY_TSV
  --output-root OUTPUT_ROOT
  [--execute]

results/artifacts/<run_id>/
  records/<artifact_id>.json
  <run_id>.artifacts.tsv
  <run_id>.artifact_receipt.tsv
```

`artifact-run-summary` consumes the completed artifact receipt and optional
science-review summary and publishes:

```text
python scripts/build_run_summary.py
  --run-id RUN_ID
  --artifact-receipt ARTIFACT_RECEIPT
  --output-root OUTPUT_ROOT
  [--science-review-summary REVIEW_SUMMARY]
  [--execute]

results/artifacts/<run_id>/
  <run_id>.run_summary.json
  <run_id>.run_summary.tsv
  <run_id>.qc_summary.tsv
  <run_id>.run_summary_receipt.tsv
```

Canonical, stably ordered JSON is the report layer's single structured entry
point. It records every expected step/scope, including missing or incomplete
states, provenance and hashes, superseded attempts, validation evidence,
scientific status, limitations, and only explicitly approved report-table
paths.

Reporting uses pinned Quarto `1.9.38` with its bundled Pandoc and Typst. Its
approved SHA-256 is
`47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6f18a`.
The checksum-verified `make quarto-restore` target installs it only into
ignored local tooling storage; rendering never installs dependencies. One
static QMD view consumes the validated run summary and contains no
analysis-executing code. `report-html-v1` first provides self-contained HTML.
Then `report-exports-v1` extends the same dry-run-first interface to
`--formats html|pdf|all`, default `all`:

```text
scripts/render_run_report.sh
  --run-summary RUN_SUMMARY_JSON
  --output-root OUTPUT_ROOT
  --quarto-bin QUARTO_BIN
  [--formats html|pdf|all]
  [--execute]

results/reports/<run_id>/
  <run_id>.run_report.html
  <run_id>.run_report.pdf
  <run_id>.run_summary.tsv
  <run_id>.report_outputs.tsv
```

The receipt is published last and records input/output hashes, schema
versions, renderer version, and report state. PDF rendering uses bundled
Typst; reports use no external network assets and never invoke analysis
engines. Reports distinguish computational and scientific status, retain a
persistent limitations banner, show expected/missing evidence and the
Step `07`-`09` scientific summaries, and label candidate rows only as
“CMH-ranked candidates.”

Required report banners are:

```text
evidence_incomplete:
  SCIENTIFIC REVIEW INCOMPLETE — NO BIOLOGICAL INTERPRETATION.

science_review_complete_exploratory:
  EXPLORATORY / PROVISIONAL — NOT BIOLOGICALLY VALIDATED.
```

The renderer understands the reserved `biological_interpretation_ready` state,
but Step `09c` cannot produce it. Every PDF page carries the applicable state
banner. Truncated tables declare the full table's explicit path and hash.
Generating a run summary or report is never evidence of computational or
biological validation. Production outputs and reports remain ignored; local
completion is demonstrated only with synthetic, incomplete, and exploratory
fixtures until production evidence exists.

## Future Architecture: Core Preprocessing, Analysis Modules, and Reporting

This architecture is a deferred design direction. It must not block the
approved local runtime, scientific-validation, artifact/reporting, and
validator sequence. Remote promotion is intentionally paused until that local
sequence is complete.

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
three reproduce the legacy path conservatively. The local real-R runtime is
available, and the Step `08` and Step `09` suites pass after the completed
local `step-09b1-real-r-fixes` package. All three remain upstream-gated for
remote and cluster promotion and are not cluster-proven.

Core preprocessing should preserve mechanical labels such as `FWD_like` and `REV_like`. Mapping those groups to `pos`, `neg`, sense, antisense, or edit direction belongs in the assay-specific analysis module and must be explicit in config or PI-approved. Incorrect strand/orientation interpretation can produce plausible-looking but biologically wrong results. As above, `samtools view -f FLAG` means a record has all bits in `FLAG`; it is not exact flag equality.

The implemented schema contract defines how the artifact vertical slice will
record the manifest used, git commit, reference and partition identity, tool
versions, sample set, step statuses, paths, and hashes. Analysis-config work
remains deferred. The adapters and run-summary builder that will create these
machine-readable outputs remain pending:

```text
run_summary.json
artifacts.tsv
qc_summary.tsv
```

The approved reporting layer will ingest the canonical run-summary JSON and
generate consolidated HTML/PDF plus TSV summaries without executing analysis.

Assay modules should refuse to run when required metadata or config is missing, such as missing condition labels, missing replicate structure, missing contrast definition, missing orientation policy, or inconsistent strandedness assumptions.

## Approved Foundational Engineering After Reports

After the immediate artifact/report slice, the approved local sequence
continues with three read-only foundation packages:

1. `post09-runtime-preflight`: explicit-profile checks for tools, versions,
   R packages, hash utilities, and runtime visibility; no installation and no
   runtime-proof claim.
2. `post09-reference-provenance`: explicit FASTA/GTF/BED/FAI/DICT/STAR-index
   inventory, hashes, annotation provenance, and contig agreement; no repair.
3. `post09-storage-inventory-retention`: explicit storage roots, sizes,
   capacity/quota evidence, and a validated retention-policy TSV; no deletion,
   movement, compression, or cleanup.

Each publishes an atomic TSV record, adds a read-only artifact adapter, and is
represented in consolidated report fixtures.

One dedicated validator branch then follows for each core step:

```text
post09-validation-report-00a
post09-validation-report-00b
post09-validation-report-00c
post09-validation-report-01
post09-validation-report-02
post09-validation-report-02b
post09-validation-report-03
post09-validation-report-04
post09-validation-report-05
post09-validation-report-06
post09-validation-report-07
post09-validation-report-08
post09-validation-report-09
```

Every validator is dry-run-first, explicit-input-only, and publishes:

```text
results/qc/validation/<step>/<scope>.validation.tsv
```

with fixed columns `step_id`, `scope_id`, `check_id`, `status`, `observed`,
`expected`, and `detail`. Each branch also adds that step's read-only artifact
adapter and an end-to-end synthetic fixture proving the validation result is
represented correctly in the canonical run summary and consolidated
HTML/PDF. No generic dispatcher, job array, native artifact retrofit, or
automatic cleanup is added.

Required validator scopes are:

| Step | Required checks |
| --- | --- |
| `00a` | STAR index/source identity, contigs, and `sjdbOverhang` |
| `00b` | BED12 structure, sorting, blocks, and GTF agreement |
| `00c` | FASTA/FAI/DICT identity and contig agreement |
| `01` | STAR outputs, logs, BAM, and mapping summary |
| `02` | BAM/BAI, sorting, read groups, and alignment RG tags |
| `02b` | quickcheck and flagstat reports |
| `03` | RSeQC report structure and paired-orientation fractions |
| `04` | BAM/BAI/metrics, sorting, RG preservation, and duplication metrics |
| `05` | Parameterize the existing Step `05` output validator |
| `06` | Orientation outputs and count arithmetic |
| `07` | Receipts, VCF structure, selectors, hashes, sample order, and counts |
| `08` | Three-output transaction, schemas, hashes, ordering, uniqueness, and counts |
| `09` | Six-output transaction, statuses, subsets, spectrum, and PDFs |

Targeted reruns, analysis-config work, module wrapping, general refactoring,
and public-data ingestion remain deferred beyond this local sequence and
require separately approved packages.

Every activated package is a linear descendant of the latest clean, pushed
docpatched branch. An implementation package receives an implementation
commit plus separate docpatch; a documentation/evidence-only package receives
one documentation commit, validation, clean-history inspection, and push.
Premature work includes generic dispatchers/arrays, broad shared-library
extraction, automatic package installation inside compute/render wrappers,
unproven tool-path config, automatic cleanup/stale-lock deletion, moving proven
scripts, report globbing or compute reruns, and public importers.

## Current Next Work

The exact local descendant history now continues:

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

At this boundary `step-09b1-real-r-fixes` and
`step-09c-scientific-validation` are complete and pushed.
`artifact-schema-v1` is implemented at `5f4d3b4`; its 54 focused tests and
complete local gate pass. After this schema docpatch is committed and pushed,
the next descendant package is `artifact-adapters-v1`. Every package after
the schema remains approved but unimplemented. Remote work stays paused
through the final Step `09` validator branch.

When remote work resumes, continue from that final clean branch:

```text
post09-validation-report-09
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Runtime promotion remains upstream-first. Each remote validation branch must
regenerate the structured run summary and HTML/PDF report after evidence
inspection, then record report paths and hashes in its evidence docpatch.

## Local Validation Gate

Run from the local repo root:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
.venv/bin/python -m compileall scripts tests
.venv/bin/python -m pytest
make shell-test
NORAD_USE_RENV=1 make real-r-test RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make r-check RSCRIPT_BIN=/usr/local/bin/Rscript
# after report-html-v1 exists:
make report-test
git status --short
git diff --name-status
```

For the local pinned runtime, use explicit
`RSCRIPT_BIN=/usr/local/bin/Rscript NORAD_USE_RENV=1` or the consolidated
`make local-real-r-test` target. `make real-r-test` may report `SKIP` only
when its default R executable is absent; the explicit local runtime must not
skip. Both real-R suites pass in the guarded local environment after
`step-09b1-real-r-fixes`. `make report-test` becomes applicable only after
`report-html-v1` exists.

The Step `09c` Python and shell fixtures are active in these gates and pass at
the local implementation boundary. They prove explicit-input validation and
transaction behavior on synthetic evidence only; they do not establish a
production science review, runtime/cluster proof, or biological readiness.

The artifact schema focused gate is:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
.venv/bin/python -m pytest -q tests/test_artifact_schema_contracts.py
```

All 54 focused tests pass at `5f4d3b4`. They prove structural and semantic
contract behavior on synthetic fixtures only. Artifact adapters, source-file
inspection, generated indexes/summaries/reports, production evidence, runtime
validation, and cluster validation remain pending.

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
