# Runbook

Operational guide for the NORAD / Novogene Remora RNA-seq pipeline.

This project is developed locally and executed at full scale on the CSU SLURM cluster.

Core workflow rule:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs -> proceed
```

Do not skip gates. Do not run scaffolded future jobs. Keep the pipeline boring.

## Project Locations

Local repo:

```bash
/Users/elisteiger/dev/norad
```

Cluster repo:

```bash
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

Raw data symlink on cluster:

```bash
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs are under:

```bash
data/raw/novogene_remora/01.RawData/*.fq.gz
```

Manifest:

```bash
samples.tsv
```

Known samples:

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

Note: `ABE_EV4` does not have an underscore before `4`.

## Demo / Inspection Checklist

Use this checklist for a short read-only project demo. These commands inspect the repo, docs, or existing outputs; they do not submit jobs.

1. Show repo state and docs:

```bash
git status --short
sed -n '1,90p' README.md
```

2. Show the tactical pipeline map:

```bash
sed -n '1,120p' docs/PIPELINE_PLAN.md
```

3. Show the sample manifest:

```bash
sed -n '1,20p' samples.tsv
```

4. Show proven output locations when present:

```bash
for path in \
  refs/novogene_star_index \
  refs/novogene_ref/genome.bed \
  refs/novogene_ref/genome.fa.fai \
  refs/novogene_ref/genome.dict \
  results/bam \
  results/qc/bam \
  results/qc/strandedness \
  results/markdup \
  results/split_ncigar
do
  if [ -e "$path" ]; then
    ls -ld "$path"
  else
    printf 'pending or unavailable here: %s\n' "$path"
  fi
done
```

5. Show Step `05` validation status and resolved temp-spill hardening:

```bash
squeue -u "$USER"
ls -ltr logs | tail
grep -n "SplitNCigarReads\|No space left on device\|tmp-dir\|java.io.tmpdir" \
  logs/norad-split-n-cigar-*.out logs/norad-split-n-cigar-*.err 2>/dev/null | tail -40
```

Step `05` is cluster-proven across all six samples after final split-N-cigar BAM/BAI validation.

6. Show the dry-run/execute gate:

```bash
grep -n "EXECUTE\|--execute\|dry-run" \
  jobs/step_05_split_n_cigar_reads.slurm \
  scripts/step_05_split_n_cigar_reads.sh | head -60
```

Do not run scaffolded Steps `06`-`09` during the demo.

## Confirmed Cluster Tools / Modules

### STAR

```bash
module load star/2.7.11b
STAR --version
```

### samtools

```bash
module load samtools/1.19.2
samtools --version
```

### bedtools

```bash
module load bedtools/2.31.1
bedtools --version
```

### Picard And Java

```bash
module load picard/3.1.1
```

Known module behavior:

```text
sets PICARD=/cm/shared/apps/picard/picard/build/libs/picard.jar
may load java/17.0.10
```

Do not infer the effective Java runtime from the module name or `JAVA_HOME` alone. Step `04` logs and validates the selected executable's actual `java -version` before Picard starts.

Step `04` Java resolution order:

1. Use `JAVA_BIN_OVERRIDE`, when explicitly provided.
2. Use `$JAVA_HOME/bin/java`, only if that path exists and is executable.
3. Fall back to `command -v java`.

The wrapper then:

* verifies the selected Java path exists and is executable
* runs the selected executable with `-version`
* parses the actual major Java version
* fails clearly before Picard starts if the version is below 17

Step `04` logs should retain:

* compute-node name
* loaded modules
* `JAVA_HOME`
* selected Java executable
* actual `java -version`
* resolved Picard JAR
* resolved samtools executable

### Python And RSeQC

Known Python modules:

```bash
python39
python3
python314
```

RSeQC is available through the project virtual environment on the cluster:

```bash
.venv/bin/infer_experiment.py
```

### GATK

GATK availability is confirmed on compute node `node002`:

```text
Java: OpenJDK 17.0.14
GATK: 4.6.1.0
GATK path: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
tool probe exit code: 0:0
```

Step `05` is implemented and cluster-proven across all six samples.

### bcftools

bcftools availability is confirmed on compute node `node002`:

```text
bcftools: 1.21
bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
tool probe exit code: 0:0
```

Step `07` remains scaffolded / not implemented / not cluster-proven until implemented.

### Still Unresolved Tools

The following have not yet been validated in the rebuilt pipeline:

```text
R / Rscript
```

## Cluster Facts And Quirks

### First Login / Fresh Checkout

```bash
hostname
whoami
pwd
which sbatch
which squeue
which sinfo
squeue -u "$USER"
sinfo
module avail
module list
```

Create or enter the project checkout:

```bash
mkdir -p ~/norad
cd ~/norad
```

If the repository is not already cloned:

```bash
git clone https://github.com/Glen-Cocoa/norad.git .
```

After cloning or before running jobs:

```bash
git pull
git status --short
mkdir -p logs
```

Run a lightweight manifest-validation smoke job after cloning or pulling:

```bash
sbatch jobs/validate_manifest.slurm
```

### SLURM

Known partition behavior:

```text
short: about 3 hour max walltime
long: about 3 day max walltime
```

Most current development jobs use `short`. No special account setting has been required so far.

### Logs

Always create logs before submitting jobs:

```bash
mkdir -p logs
```

Jobs use:

```bash
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

### TMPDIR

Use:

```bash
TMPDIR=/tmp
```

Submit execute jobs like:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Known cluster warning:

```text
slurmstepd: error: TMPDIR [/local/tmp] is not writeable
slurmstepd: error: Setting TMPDIR to /tmp
```

This has not been fatal when the job itself logs `TMPDIR: /tmp`.

Exception: Step `05` GATK `SplitNCigarReads` must route Java/HTSJDK/GATK temp files to a per-run project-storage temp directory rather than relying on node-local `/tmp`.

### module list

`module list` writes to stderr. In scripts, use:

```bash
module list 2>&1 || true
```

## Optional Cluster Shell Helpers

The cluster shell is bash, not zsh.

Optional helpers may be installed in `~/.bashrc`:

```bash
norad       # cd to NORAD repo
nlogs       # show recent logs
sqme        # show user's SLURM queue
sj <jobid>  # sacct summary
sjtail <jobid>
sjcheck <jobid>
```

Recommended quick checks:

```bash
norad
sqme
nlogs
sjcheck <JOBID>
sjtail <JOBID>
```

If helpers are not installed, use the manual commands in the next section.

## Future Operational Helpers

The deferred engineering roadmap in `TODO.md` includes possible future operational helpers for manifest-driven submission/validation, environment probes, standardized validation reports, reference provenance checks, retention/cleanup policy, and conservative admin utilities.

These helpers are roadmap ideas unless their scripts, tests, and runbook commands exist in the repo. Do not treat candidate helper names, config files, Makefile targets, validators, reports, or cleanup utilities as available commands.

## Manual Job Checking

Recent logs:

```bash
ls -ltr logs | tail
```

SLURM accounting:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Tail logs:

```bash
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Live tail:

```bash
tail -F logs/<log-prefix>-<JOBID>.out logs/<log-prefix>-<JOBID>.err
```

Queue status:

```bash
squeue -j <JOBID>
squeue -u "$USER"
```

Watch an output directory while a job runs:

```bash
du -sh <output_dir>
ls -lh <output_dir>
```

## Local Validation Gate

Run from the local repo root before committing:

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

Only commit after the local gate passes.

## Cluster Execution Pattern

On local:

```bash
cd /Users/elisteiger/dev/norad
git status --short
git add <changed-files>
git commit -m "<message>"
git push
```

On cluster:

```bash
ssh csu-hpc
cd ~/norad
git pull
git status --short
mkdir -p logs
```

Dry-run:

```bash
sbatch jobs/<step>.slurm
```

Check dry-run:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Check execute job:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Inspect outputs before declaring the step proven.

## Reference Prep

Novogene reference source files:

```text
genome.fa.gz
genome.gtf.gz
genome_gene.fa.gz
```

Prepared reference paths:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

Reference notes:

```text
Genome: GRCh38-like
Chromosome naming: numeric-style, e.g. 1, 2, 3
Not chr1, chr2, chr3
```

FASTA and GTF chromosome naming match.

### Step 00a: STAR Index

Job:

```bash
jobs/step_00a_build_novogene_star_index.slurm
```

Output:

```bash
refs/novogene_star_index/
```

STAR index was built with:

```text
sjdbOverhang=149
```

because reads are 150 bp.

Status:

```text
cluster-proven
```

### Step 00b: GTF To BED12

Script:

```bash
scripts/gtf_to_bed12.py
```

Job:

```bash
jobs/step_00b_gtf_to_bed12.slurm
```

Outputs:

```bash
refs/novogene_ref/genome.unsorted.bed
refs/novogene_ref/genome.bed
```

Validated output:

```text
206,601 BED12 transcript records
```

Status:

```text
cluster-proven
```

### Step 00c: GATK Reference Sidecars

Script:

```bash
scripts/step_00c_prepare_gatk_reference.sh
```

Job:

```bash
jobs/step_00c_prepare_gatk_reference.slurm
```

Purpose:

```text
Create and validate the FASTA index and sequence dictionary required by GATK.
```

Expected outputs:

```bash
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Current evidence:

```text
Ad hoc sidecar prep completed with exit code 0:0.
FAI contigs: 194
DICT contigs: 194
BAM header contigs: 194
Reference/BAM SQ check: PASS
```

Dry-run:

```bash
sbatch jobs/step_00c_prepare_gatk_reference.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_00c_prepare_gatk_reference.slurm
```

Direct script dry-run with explicit cluster tools:

```bash
scripts/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
```

Direct script execute with explicit cluster tools:

```bash
scripts/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --execute
```

Status:

```text
cluster-proven
```

Step `00c` formalizes the prep required before Step `05` execute-mode validation. It is dry-run by default, uses a reference-level lock in execute mode, reuses valid existing sidecars, generates only missing sidecars, and validates `.fai`/`.dict` contig-name and length agreement. Step `05` treats these files as prerequisites, fails clearly if they are missing, and must not silently create shared reference sidecars inside per-sample jobs.

## Step 01: STAR Alignment

Script:

```bash
scripts/step_01_star_align.sh
```

Job:

```bash
jobs/step_01_star_align.slurm
```

Purpose:

```text
Align paired-end FASTQs to the STAR index and write coordinate-sorted BAM output.
```

Main output family:

```bash
results/star/<sample>/<sample>.Aligned.sortedByCoord.out.bam
```

Other STAR output families:

```bash
results/star/<sample>/<sample>.Log.final.out
results/star/<sample>/<sample>.Log.out
results/star/<sample>/<sample>.Log.progress.out
results/star/<sample>/<sample>.SJ.out.tab
```

Status:

```text
complete and cluster-proven across all six samples
```

Known alignment summaries:

| Sample | Approximate input reads | Unique mapping rate |
| ------ | ----------------------: | ------------------: |
| `ABE_EV_2` | 21.36 million | 58.50% |
| `ABE_EV_3` | 20.5 million | 82.95% |
| `ABE_EV4` | 26.6 million | 71.06% |
| `ABE_PUM1_2` | 21.1 million | 77.51% |
| `ABE_PUM1_3` | 23.2 million | 85.38% |
| `ABE_PUM1_4` | 22.5 million | 70.96% |

## Step 02: Canonical Sort, Read-Group Tagging, And BAM Indexing

Script:

```bash
scripts/step_02_sort_index_bam.sh
```

Job:

```bash
jobs/step_02_sort_index_bam.slurm
```

Status:

```text
hardened and cluster-proven across all six samples
```

Canonical outputs:

```bash
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
```

Read-group convention:

```text
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

`LB=<sample_id>` is provisional until more specific library or lane metadata is recovered.

Dry-run:

```bash
sbatch jobs/step_02_sort_index_bam.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 \
  jobs/step_02_sort_index_bam.slurm
```

Hardened execution flow:

```text
1. Create the output directory in execute mode.
2. Acquire the per-sample lock directory:
   results/bam/<sample>/.<sample>.step02.lock/
3. Sort the input alignment to a job-specific temporary BAM.
4. Run samtools addreplacerg with repeated -r arguments and -w.
5. Index the temporary read-group-tagged BAM.
6. Validate the temporary BAM and BAI.
7. Confirm existing canonical BAM/BAI are either both present or both absent.
8. Back up any existing canonical pair to job-specific backup paths.
9. Publish the replacement BAM and BAI to the stable canonical paths.
10. Revalidate the published canonical BAM and BAI.
11. Remove backups and the owned lock only after successful final validation.
```

Publication uses rollback protection, but the BAM/BAI pair is not a single indivisible atomic operation. If a failure occurs after backups begin, Step `02` restores the previous complete canonical pair. If no prior pair existed, it removes any partially published canonical outputs.

Validation checklist for each final canonical BAM:

```bash
module load samtools/1.19.2

sample=<sample_id>
bam="results/bam/$sample/$sample.sorted.bam"

samtools quickcheck "$bam"
samtools view -H "$bam" | grep '^@HD.*SO:coordinate'
samtools view -H "$bam" | grep '^@RG'

total_records="$(samtools view -c "$bam")"
tagged_records="$(samtools view -c -d "RG:$sample" "$bam")"

test "$total_records" -gt 0
test "$tagged_records" -eq "$total_records"
ls -lh "$bam" "$bam.bai"
```

Confirmed final canonical BAM sizes were approximately:

| Sample | BAM size |
| ------ | -------: |
| `ABE_EV_2` | 3.0 GB |
| `ABE_EV_3` | 2.0 GB |
| `ABE_EV4` | 2.9 GB |
| `ABE_PUM1_2` | 2.2 GB |
| `ABE_PUM1_3` | 2.1 GB |
| `ABE_PUM1_4` | 2.5 GB |

Historical resource observations from the pre-hardening `ABE_EV_2` Step `02` run:

```text
Elapsed: about 3 minutes 46 seconds
MaxRSS: about 6.8G
Output BAM: about 3.0G
Output BAI: about 3.3M
```

These observations are historical, not guaranteed resource requirements for future cohort runs.

Normal tool progress may appear on stderr. For example, samtools sort can emit:

```text
[bam_sort_core] merging from 4 files and 8 in-memory blocks...
```

## Step 02b: BAM QC

Script:

```bash
scripts/step_02b_bam_qc.sh
```

Job:

```bash
jobs/step_02b_bam_qc.slurm
```

Status:

```text
implemented and refreshed across all six final hardened Step 02 BAMs
```

Outputs:

```bash
results/qc/bam/<sample>.quickcheck.txt
results/qc/bam/<sample>.flagstat.txt
```

Dry-run:

```bash
sbatch jobs/step_02b_bam_qc.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_02b_bam_qc.slurm
```

Validation checklist:

```bash
sample=<sample_id>
cat "results/qc/bam/$sample.quickcheck.txt"
head -40 "results/qc/bam/$sample.flagstat.txt"
grep -E "in total|primary|secondary|mapped|properly paired|duplicates" \
  "results/qc/bam/$sample.flagstat.txt"
```

Important nuance: the current Step `02b` script creates the requested output directory before dry-run exit. It should not be described as side-effect-free.

Cluster PATH note: the first Step `02b` cohort attempt failed immediately because `samtools` was not found on `PATH`, despite module output listing `samtools/1.19.2`. The successful rerun prepended the known samtools bin directory:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This is a cluster environment/PATH inconsistency, not a BAM/QC failure.

## Step 03: RSeQC Strandedness / Orientation Inference

Script:

```bash
scripts/step_03_infer_strandedness_and_orientation.sh
```

Job:

```bash
jobs/step_03_infer_strandedness_and_orientation.slurm
```

Status:

```text
cluster-proven across all six samples
```

Output:

```bash
results/qc/strandedness/<sample>.infer_experiment.txt
```

Dry-run:

```bash
sbatch jobs/step_03_infer_strandedness_and_orientation.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_03_infer_strandedness_and_orientation.slurm
```

Validation checklist:

```bash
sample=<sample_id>
cat "results/qc/strandedness/$sample.infer_experiment.txt"
```

Confirmed result:

```text
All six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.
```

Tool-specific examples:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

## Step 04: MarkDuplicates

Script:

```bash
scripts/step_04_mark_duplicates.sh
```

Job:

```bash
jobs/step_04_mark_duplicates.slurm
```

Status:

```text
cluster-proven across all six samples
```

Inputs:

```bash
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
```

Outputs:

```bash
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt
```

Dry-run:

```bash
sbatch jobs/step_04_mark_duplicates.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_04_mark_duplicates.slurm
```

If a supported Java 17 executable is known, pass it explicitly:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,JAVA_BIN_OVERRIDE=/path/to/java \
  jobs/step_04_mark_duplicates.slurm
```

Validation checklist for promotion of each sample:

```bash
sample=<sample_id>
bam="results/markdup/$sample/$sample.markdup.bam"
metrics="results/qc/markdup/$sample.markdup.metrics.txt"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
samtools quickcheck "$bam"
samtools view -H "$bam" | grep '^@HD.*SO:coordinate'
samtools view -H "$bam" | grep '^@RG'
ls -lh "$bam" "$bam.bai" "$metrics"
```

Step `04` uses `REMOVE_DUPLICATES=false`; duplicate reads remain present with the duplicate flag set.

All six samples have duplicate-marked BAM, BAM index, Picard metrics, `samtools quickcheck: PASS`, retained `@HD SO:coordinate`, retained sample-specific `@RG`, and a populated Picard metrics row.

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

Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size. The observed Step `04` memory range was about 22.7-24.3 GB MaxRSS; this is observed evidence, not a guaranteed resource requirement.

## Step 05: SplitNCigarReads

Status:

```text
implemented and cluster-proven across all six samples
```

Expected tool:

```text
GATK SplitNCigarReads
```

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`.

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

Dry-run:

```bash
sbatch jobs/step_05_split_n_cigar_reads.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_05_split_n_cigar_reads.slurm
```

Step `05` still follows the normal dry-run/execute submission pattern, but the GATK process must use a per-run project-storage temp directory. The hardened script passes that directory through:

```text
--java-options -Djava.io.tmpdir=...
--tmp-dir ...
TMPDIR
```

If a supported Java 17 executable is known, pass it explicitly:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,JAVA_BIN_OVERRIDE=/path/to/java \
  jobs/step_05_split_n_cigar_reads.slurm
```

Direct script dry-run with explicit cluster tools:

```bash
scripts/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools
```

Direct script execute with explicit cluster tools:

```bash
scripts/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --execute
```

Validation checklist for promotion of each sample:

```bash
sample=<sample_id>
bam="results/split_ncigar/$sample/$sample.split_ncigar.bam"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
samtools quickcheck "$bam"
samtools view -H "$bam" | grep '^@HD.*SO:coordinate'
samtools view -H "$bam" | grep '^@RG'
ls -lh "$bam" "$bam.bai"
```

Step `05` requires the Step `00c` sidecars, fails clearly if they are missing, and must not create shared reference sidecars inside per-sample jobs. It is dry-run by default, writes GATK output to run-token temporary paths in execute mode, validates the temporary BAM/BAI pair before publication, and rolls back an existing final pair if publication fails after backups begin.

The six-sample Step `05` output inspection with `tests/data_checks/validate_step05_outputs.sh` reported:

```text
PASS=6
PENDING_OR_RUNNING=0
FAIL=0
```

All six final Step `05` outputs have final BAM/BAI files, passing `samtools quickcheck`, `@HD` with `SO:coordinate`, sample-matching `@RG`, and no remaining Step `05` scratch files.

Confirmed final Step `05` output sizes:

| Sample | Split-N-cigar BAM size | BAI size |
| ------ | ---------------------: | -------: |
| `ABE_EV_2` | 4.4G | 2.0M |
| `ABE_EV_3` | 3.5G | 1.6M |
| `ABE_EV4` | 4.4G | 1.8M |
| `ABE_PUM1_2` | 3.7G | 1.6M |
| `ABE_PUM1_3` | 3.7G | 1.6M |
| `ABE_PUM1_4` | 3.8G | 1.8M |

The first `ABE_EV_2` cluster execute attempt confirmed that GATK reached useful traversal behavior: pass 1 completed and pass 2 started. It later failed during HTSJDK temporary spill/write/close behavior because `SortingCollection` temp files were written to node-local `/tmp` and hit `No space left on device`. Treat that failed attempt as resolved hardening context, not as current blocker language.

Failure cleanup now removes owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks.

## Step 06: Split BAM By Read Orientation

Status:

```text
implemented and locally tested; pending cluster validation
```

Entry points:

```text
jobs/step_06_split_bam_by_read_orientation.slurm
scripts/step_06_split_bam_by_read_orientation.sh
tests/shell/test_step_06_split_bam_by_read_orientation.sh
```

Old reference workflow used samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

These are mechanical read-orientation flag groups. `samtools view -f FLAG` means a read has all bits in `FLAG`; it is not exact flag equality. Do not assume `FWD_like` / `REV_like` labels directly equal biological sense/antisense.

Step `06` consumes the Step `05` output contract:

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

Dry-run:

```bash
sbatch jobs/step_06_split_bam_by_read_orientation.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_06_split_bam_by_read_orientation.slurm
```

Direct script dry-run with explicit cluster samtools:

```bash
scripts/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir results/orientation/ABE_EV_2 \
  --qc-dir results/qc/orientation \
  --threads 1 \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools
```

Direct script execute with explicit cluster samtools:

```bash
scripts/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir results/orientation/ABE_EV_2 \
  --qc-dir results/qc/orientation \
  --threads 1 \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --execute
```

Validation checklist for promotion of each sample:

```bash
sample=<sample_id>
fwd="results/orientation/$sample/$sample.FWD_like.bam"
rev="results/orientation/$sample/$sample.REV_like.bam"
counts="results/qc/orientation/$sample.orientation_counts.tsv"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
samtools quickcheck "$fwd"
samtools quickcheck "$rev"
ls -lh "$fwd" "$fwd.bai" "$rev" "$rev.bai" "$counts"
cat "$counts"
```

The counts TSV includes `input_records`, per-flag counts for `99`, `147`, `83`, and `163`, merged `fwd_like_records` and `rev_like_records`, `assigned_records`, `unassigned_records`, and `assigned_fraction`.

Step `06` is not cluster-proven until a SLURM dry-run, execute run, and final output inspection have completed successfully.

## Step 07: bcftools mpileup

Status:

```text
scaffolded / not implemented / not cluster-proven
```

bcftools availability is confirmed on compute node `node002`: bcftools `1.21`, path `/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools`; the tool probe completed successfully with exit code `0:0`. Step `07` remains scaffolded / not implemented / not cluster-proven.

## Step 08: VCF Preprocessing

Status:

```text
scaffolded / not implemented / not cluster-proven
```

Future work should port and parameterize the reference `vcf_preprocess1.R`.

## Step 09: CMH Editing-Site Calling

Status:

```text
scaffolded / not implemented / not cluster-proven
```

Future work should port and parameterize the reference `Edit_call_cmh.R`.

## Temporary Java Workaround

Node-specific Java evidence is mixed: `node002` has Java 17 and worked for the GATK/bcftools probe, `node003` previously worked with Java 17 for Step `04`, and `node007` previously exposed Java 11 / a missing Java 17 path.

Do not:

* embed `node003` as a permanent default in the SLURM script
* describe node pinning as a pipeline architecture requirement
* assume any single working node will remain the long-term solution
* recommend copying a JDK from the head node or another compute node

Scripts should continue logging and validating the actual Java runtime instead of trusting module names or `JAVA_HOME` alone. The durable action is to report or clarify the inconsistent Java 17 installation with CSU HPC and identify a supported cluster-wide Java 17 executable or installation path.

## Reference Workflow Alignment

The uploaded/reference workflow sequence is:

```text
STAR alignment
-> MarkDuplicates
-> SplitNCigarReads
-> split BAM by read orientation
-> bcftools mpileup
-> VCF preprocessing
-> CMH editing-site calling
```

This repo is rebuilding that workflow in a cleaner SLURM/script/testable structure.
