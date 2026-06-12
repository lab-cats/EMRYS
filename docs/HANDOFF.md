# Project handoff notes

## What this project does

This repository rebuilds a Novogene Remora RNA-seq / RNA-editing workflow into a cleaner, manifest-driven, testable pipeline for local development and CSU SLURM execution.

The biological context is NORAD / PUM1 / rABE-related RNA-seq data. The downstream workflow appears to be RNA-editing / variant-like site calling rather than simple gene-count differential expression. Uploaded legacy scripts are treated as protocol references, not as runnable source of truth.

The intended high-level workflow is:

1. Build STAR index from the Novogene reference.
2. Convert GTF annotation to BED12 for RSeQC.
3. Align paired-end RNA-seq reads with STAR.
4. Sort/index canonical BAMs.
5. QC canonical BAMs.
6. Infer library strandedness/orientation with RSeQC.
7. Mark duplicates.
8. Run GATK SplitNCigarReads.
9. Split BAMs by read orientation.
10. Run bcftools mpileup by chromosome and orientation/strand.
11. Preprocess VCFs.
12. Run CMH/editing-site calling.

The pipeline is being rebuilt one validated step at a time.

## Current status

### Proven on cluster

The following steps have been implemented, committed, pushed, pulled on the cluster, and validated for sample `ABE_EV_2`:

| Step                                          | Status                | Notes                                                                   |
| --------------------------------------------- | --------------------- | ----------------------------------------------------------------------- |
| `00a` STAR index                              | Proven                | Built Novogene STAR index at `refs/novogene_star_index`.                |
| `00b` GTF to BED12                            | Proven                | Wrote `refs/novogene_ref/genome.bed`; 206,601 BED12 transcript records. |
| `01` STAR alignment                           | Proven for `ABE_EV_2` | Produced STAR coordinate-sorted BAM.                                    |
| `02` canonical sort/index BAM                 | Proven for `ABE_EV_2` | Produced canonical downstream BAM and BAI.                              |
| `02b` BAM QC                                  | Proven for `ABE_EV_2` | Produces quickcheck and flagstat outputs.                               |
| `03` RSeQC strandedness/orientation inference | Proven for `ABE_EV_2` | Strong reverse-stranded / first-strand signal.                          |

### Current Step 03 result

RSeQC `infer_experiment.py` output for `ABE_EV_2`:

```text
This is PairEnd Data
Fraction of reads failed to determine: 0.0828
Fraction of reads explained by "1++,1--,2+-,2-+": 0.0432
Fraction of reads explained by "1+-,1-+,2++,2--": 0.8740
```

Interpretation:

* The library appears strongly reverse-stranded / first-strand-style for `ABE_EV_2`.
* Read 1 is mostly antisense to annotated transcript.
* Read 2 is mostly sense.
* Common tool settings implied by this result:

  * `featureCounts -s 2`
  * `HTSeq stranded=reverse`
  * `fr-firststrand`

Caution: this has only been confirmed on `ABE_EV_2`. Before making a global library-prep assumption, run Step 03 on all six samples once their canonical BAMs exist.

### Pending / incomplete

Steps `04` through `09` are scaffolded only and should remain non-runnable until implemented.

Pending steps:

| Step | Planned purpose                                       |
| ---- | ----------------------------------------------------- |
| `04` | Picard MarkDuplicates                                 |
| `05` | GATK SplitNCigarReads                                 |
| `06` | Split BAMs by read orientation                        |
| `07` | bcftools mpileup by chromosome and orientation/strand |
| `08` | VCF preprocessing                                     |
| `09` | CMH editing-site calling                              |

The next likely implementation target is Step `04`: Picard MarkDuplicates.

## Main entry points

### Implemented scripts

```text
scripts/validate_manifest.py
scripts/gtf_to_bed12.py
scripts/step_01_star_align.sh
scripts/step_02_sort_index_bam.sh
scripts/step_02b_bam_qc.sh
scripts/step_03_infer_strandedness_and_orientation.sh
```

### Implemented SLURM jobs

```text
jobs/step_00a_build_novogene_star_index.slurm
jobs/step_00b_gtf_to_bed12.slurm
jobs/step_01_star_align.slurm
jobs/step_02_sort_index_bam.slurm
jobs/step_02b_bam_qc.slurm
jobs/step_03_infer_strandedness_and_orientation.slurm
```

### Pending scaffold jobs

```text
jobs/step_04_mark_duplicates.slurm
jobs/step_05_split_n_cigar_reads.slurm
jobs/step_06_split_bam_by_read_orientation.slurm
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
jobs/step_08_vcf_preprocessing.slurm
jobs/step_09_cmh_editing_site_calling.slurm
```

These future jobs are intentionally pending/non-runnable until implemented.

### Documentation

```text
docs/PIPELINE_PLAN.md
docs/HANDOFF.md
```

`docs/PIPELINE_PLAN.md` is the canonical roadmap for steps `00a` through `09`.

## Data locations

### Local development repo

```text
/Users/elisteiger/dev/norad
```

### Cluster repo

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

### Raw data on cluster

The repo uses a symlink:

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs are under:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

### Samples

The manifest is:

```text
samples.tsv
```

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

### Reference files

Novogene reference source files came from `04.Ref`:

```text
genome.fa.gz
genome.gtf.gz
genome_gene.fa.gz
```

Prepared reference outputs:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_star_index/
```

Reference notes:

* Genome is GRCh38-like.
* Chromosome names look like `1`, `2`, etc., not `chr1`, `chr2`.
* FASTA and GTF chromosome naming match.

## How to run local validation

Run from the local repo root:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
git status --short
git diff --name-status
```

Local tests are lightweight and should not require real full-size BAM/FASTQ data.

## Cluster execution pattern

The project uses a gated local-to-cluster workflow:

1. Implement locally.
2. Run local validation.
3. Commit and push.
4. Pull on cluster.
5. Run SLURM dry-run.
6. Inspect logs.
7. Run SLURM execute mode.
8. Inspect outputs.
9. Only then proceed to the next step.

Cluster setup:

```bash
ssh csu-hpc
cd ~/norad
git pull
git status --short
mkdir -p logs
```

Dry-run pattern:

```bash
sbatch jobs/<step>.slurm
```

Execute pattern:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Manual job check:

```bash
ls -ltr logs | tail
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Optional cluster shell helpers may exist in `~/.bashrc`:

```bash
norad       # cd to repo
nlogs       # show recent logs
sqme        # show user's SLURM queue
sj <jobid>  # sacct summary
sjtail <jobid>
sjcheck <jobid>
```

These helpers are convenience only and are not required by the repo.

## Step-specific cluster commands used so far

### Step 02 sort/index BAM

Dry-run:

```bash
sbatch jobs/step_02_sort_index_bam.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_02_sort_index_bam.slurm
```

Validated output:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

### Step 02b BAM QC

Dry-run:

```bash
sbatch jobs/step_02b_bam_qc.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_02b_bam_qc.slurm
```

Expected output:

```text
results/qc/bam/ABE_EV_2.quickcheck.txt
results/qc/bam/ABE_EV_2.flagstat.txt
```

### Step 03 strandedness/orientation inference

Dry-run:

```bash
sbatch jobs/step_03_infer_strandedness_and_orientation.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_03_infer_strandedness_and_orientation.slurm
```

Validated output:

```text
results/qc/strandedness/ABE_EV_2.infer_experiment.txt
```

## Expected outputs

### STAR alignment

For sample `ABE_EV_2`:

```text
results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam
results/star/ABE_EV_2/ABE_EV_2.Log.final.out
results/star/ABE_EV_2/ABE_EV_2.Log.out
results/star/ABE_EV_2/ABE_EV_2.Log.progress.out
results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab
```

### Canonical BAM

```text
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
```

Current proven example:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

### BAM QC

```text
results/qc/bam/<sample>.quickcheck.txt
results/qc/bam/<sample>.flagstat.txt
```

### RSeQC strandedness/orientation

```text
results/qc/strandedness/<sample>.infer_experiment.txt
```

### Future expected outputs

Likely future output paths, subject to implementation:

```text
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt

results/splitncigar/<sample>/<sample>.splitncigar.bam
results/splitncigar/<sample>/<sample>.splitncigar.bam.bai

results/orientation/<sample>/<sample>.<orientation>.bam
results/orientation/<sample>/<sample>.<orientation>.bam.bai

results/vcf/...
results/editing/...
```

## Known assumptions

* Data are paired-end RNA-seq.
* Primary development/validation sample is currently `ABE_EV_2`.
* Full sample set has six samples.
* Genome/reference is Novogene-provided GRCh38-like reference.
* Chromosome names are numeric-style, for example `1`, not `chr1`.
* STAR index was built with `sjdbOverhang=149`, matching 150 bp reads.
* RSeQC Step 03 for `ABE_EV_2` strongly supports reverse-stranded / first-strand-style library behavior.
* Do not yet assume this strandedness globally until additional samples are checked.
* Dry-run mode should not create final outputs.
* Execute mode should validate required inputs and outputs.
* Future RNA-editing steps should preserve the distinction between read orientation and biological transcript strand.
* Old workflow orientation labels such as FWD/REV need careful interpretation in light of Step 03.

## Known cluster/tool assumptions

* SLURM is available on the CSU cluster.
* `short` partition supports jobs up to about 3 hours.
* `long` partition supports jobs up to about 3 days.
* `TMPDIR=/tmp` should be exported for jobs.
* `logs/` must exist before `sbatch`.
* Known modules:

  * `star/2.7.11b`
  * `samtools/1.19.2`
  * `bedtools/2.31.1`
  * `picard/3.1.1`
  * `python39`
  * `java/17.0.10`
* RSeQC is available through the project virtual environment:

  * `.venv/bin/infer_experiment.py`
* GATK availability has not yet been validated.

## Known job IDs from development

Useful historical job IDs:

```text
594742  Step 01 STAR alignment for ABE_EV_2; completed successfully.
594746  First Step 00b GTF-to-BED12 attempt; had issue.
594747  Fixed Step 00b GTF-to-BED12; completed successfully.
594748  Step 02 dry-run; completed successfully.
594749  Step 02 execute; completed successfully.
594750  Step 02b dry-run; completed successfully.
```

Step 02b execute and Step 03 execute also completed successfully, but their job IDs were not recorded in the visible notes.

## Known issues/TODOs

### Near-term

* Decide whether to implement Step 04 MarkDuplicates next or first generalize/run Steps 01–03 across all six samples.
* Recommended next implementation target is Step 04 MarkDuplicates on `ABE_EV_2`.
* Before any global strandedness assumption, run Step 03 on all six samples once their canonical BAMs exist.

### Step 04 TODO

Implement Picard MarkDuplicates.

Expected input:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Likely outputs:

```text
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai
results/qc/markdup/ABE_EV_2.markdup.metrics.txt
```

Expected tool:

```text
picard/3.1.1
```

Implementation notes:

* Use Picard MarkDuplicates.
* Mark duplicates; do not remove duplicates unless explicitly justified.
* Write metrics file.
* Index output BAM.
* Preserve dry-run-first behavior.
* Use local tests with fake Picard/Java if needed.

### Step 05 TODO

Implement GATK SplitNCigarReads.

Needs validation:

* GATK availability on cluster.
* Reference FASTA path.
* FASTA `.fai`.
* Picard/GATK sequence dictionary `.dict`.

### Step 06 TODO

Implement read-orientation BAM splitting.

Old workflow used samtools flags:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Do not assume these labels directly equal biological sense/antisense without documenting the interpretation, especially because Step 03 indicates reverse-stranded library behavior.

### Step 07 TODO

Implement bcftools mpileup by chromosome and orientation/strand.

Needs decisions:

* chromosome/region handling
* grouping EV vs PUM1 samples
* reference FASTA path
* output naming

### Step 08 TODO

Port/customize VCF preprocessing from old `vcf_preprocess1.R`.

Needs work:

* remove hardcoded paths
* make CLI/manifest-driven
* document assumptions about strand/orientation

### Step 09 TODO

Port/customize CMH editing-site calling from old `Edit_call_cmh.R`.

Needs work:

* remove hardcoded paths
* make CLI/manifest-driven
* document statistical assumptions
* define expected final tables/plots

## Development rule

Do not jump ahead. The pipeline should continue to be developed as:

```text
implement locally -> local tests -> commit/push -> pull cluster -> dry-run -> execute -> inspect outputs -> proceed
```
