# Runbook

Operational guide for the NORAD / Novogene Remora RNA-seq pipeline.

This project is developed locally and executed at full scale on the CSU SLURM cluster.

Core workflow rule:

```text
create stage branch from latest clean docpatched predecessor
-> implement only that stage
-> focused and complete local validation
-> implementation commit
-> reread required docs and repository-wide docpatch
-> documentation-only commit
-> clean status/history and push
-> create the next descendant stage branch
```

Cluster promotion is a later upstream-sequential gate: pull the completed branch, dry-run, execute the approved scope, inspect scheduler/log/output evidence, and docpatch that evidence before promoting the next step. Do not skip gates. Do not run scaffolded future jobs. Keep the pipeline boring.

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
sed -n '1,120p' docs/design/PIPELINE_PLAN.md
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
	  results/split_ncigar \
	  results/orientation \
	  results/qc/orientation
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

Step `07` source and mocked local-test evidence may be inspected during the
demo, but do not claim or demonstrate real Step `07` VCFs because no cluster
run has been validated. Step `08` and Step `09` source and fake-R wrapper tests
may also be inspected. Their real-R suites now execute locally without `SKIP`,
and pass with synthetic fixtures. Neither step has production or cluster
output evidence. Do not demonstrate Step `09` as a biological result.

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

Step `07` is implemented locally and locally tested with mocked bcftools. The executable probe above confirms tool availability only; no Step `07` cluster dry-run, execute run, or output evidence has been inspected. Step `07` is not cluster-proven.

### Local R And Unresolved Cluster Runtime

The signed Apple-silicon CRAN R `4.6.1` runtime is installed locally and the
guarded repository `renv` environment is locked to Bioconductor `3.23`. Local
runtime and package-environment checks pass. The Step `08` and Step `09`
real-R suites also pass locally without `SKIP` after the `step-09b1` fixes.
This is local fixture evidence only; see the local R section and
troubleshooting guide for the exact scope.

A supported R/Rscript path and compatible package library visible in the CSU
batch/compute environment remain unresolved. Local runtime evidence is not
cluster runtime evidence.

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

The approved local descendant roadmap implements scientific-validation tooling
first, then the reporting vertical slice immediately:

```text
step-09c-scientific-validation
-> artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
-> post09-runtime-preflight
-> post09-reference-provenance
-> post09-storage-inventory-retention
-> one validation-report branch for each Step 00a through 09
```

Run summaries and consolidated HTML/PDF reports therefore precede the
remaining foundational engineering. Remote validation, targeted reruns,
analysis configuration, module wrapping, job arrays, public-data ingestion,
publishing infrastructure, and broad refactors remain deferred.

These helpers are roadmap ideas unless their scripts, tests, and runbook commands exist in the repo. Do not treat candidate helper names, config files, Makefile targets, validators, reports, or cleanup utilities as available commands.

The future preflight will supplement, not replace, each step's own validation.
It must not install packages, guess tool paths, delete outputs, or clear locks.
Do not use a generic dispatcher or job array before the step-specific
validators and repeated operational need establish their contracts.

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

Run from the local repo root before each implementation or documentation commit:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
make real-r-test
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
git status --short
git diff --name-status
```

`make real-r-test` runs the Step `08` and Step `09` semantic fixtures when
`Rscript` is available. When the default `Rscript` is absent, each runner
reports `SKIP`; those skips are not semantic R validation. An explicit bad
override fails. A present runtime with missing Step `08` packages also fails;
Step `09` uses base R only.

Commit implementation/tests first. Then reread the required project documents, perform the repository-wide documentation consistency pass, rerun this gate, and make the separate documentation-only commit. Require a clean worktree and inspect history before pushing or creating the next descendant stage branch.

### Guarded local R environment

Local R setup is an explicit developer action:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

These targets activate the project library with `NORAD_USE_RENV=1`. The
tracked lock describes R `4.6.1`, Bioconductor `3.23`, the eight direct Step
`08` namespaces, and their transitive dependencies. The restore target uses
the configured release repositories and performs installation only when the
operator invokes it. Existing analysis scripts, compute wrappers, and future
renderers never install packages.

The guarded startup contract disables automatic snapshots and the `renv`
sandbox. The latter avoids a reproduced high-CPU directory-creation loop on
this macOS/R combination. Do not remove the guard or enable implicit package
mutation without a separately reviewed change.

Current local evidence:

```text
R 4.6.1 runtime and all required namespaces load
BiocManager::valid() passes
renv::status() reports synchronization
empty cache-disabled binary restore passes
headless PDF creation passes
Step 08 and Step 09 real-R suites pass without SKIP
Step 08 validates consumed FORMAT/DP, FORMAT/AD, and INFO/AD lexical values
  before VariantAnnotation parsing, including wholly missing AD vectors;
  its overlap-rejection fixture passes
Step 09 validates the PDF EOF marker by scanning raw bytes
```

Therefore the guarded environment and both semantic fixture suites are
validated locally. This does not validate production data, establish CSU
batch/compute visibility, or make Steps `08` or `09` cluster-proven. The
`step-09b1-real-r-fixes` branch is complete and pushed at docpatch `859aba2`;
the next descendant is `step-09c-scientific-validation`.

## Cluster Execution Pattern

On local:

```bash
cd /Users/elisteiger/dev/norad
git status --short
git add <changed-files>
git commit -m "<stage implementation message>"
# after the required document reread and repository-wide docpatch:
git add <documentation-files>
git commit -m "step NN docpatch"
git diff --check
git status --short
git log --oneline -3
git push
```

Remote promotion is currently paused. After local work reaches the clean,
pushed, docpatched `post09-validation-report-09` branch and remote work is
explicitly resumed, open a cluster shell:

```bash
ssh csu-hpc
```

Then run the fail-closed checkout gate in that cluster shell:

```bash
set -euo pipefail

cd ~/norad
git fetch origin
validation_branch=validate-step-07
git switch "$validation_branch" ||
  git switch --track -c "$validation_branch" "origin/$validation_branch"
git pull --ff-only origin "$validation_branch"
test "$(git branch --show-current)" = "$validation_branch"
git rev-parse HEAD
test -z "$(git status --porcelain)"
mkdir -p logs
```

Set `validation_branch` to the exact active gate:

```text
validate-step-07
validate-step-08
validate-step-09
validate-step-09c-scientific-evidence
post09-targeted-reruns
```

Do not use an unqualified `git pull` and assume the checkout changed branches.
Record the branch and commit with the validation evidence before submitting.

Create and push each local descendant only after its predecessor is clean and
pushed:

```bash
set -euo pipefail

predecessor=post09-validation-report-09
next_branch=validate-step-07

git switch "$predecessor"
git pull --ff-only origin "$predecessor"
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$predecessor")"
git log --oneline -3
git switch -c "$next_branch"
git push -u origin "$next_branch"
```

For later gates, use `validate-step-07` -> `validate-step-08` ->
`validate-step-09` -> `validate-step-09c-scientific-evidence` ->
`post09-targeted-reruns`. Never create the descendant before the predecessor's
inspected evidence/report docpatch, clean-history check, and push.

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
cluster-proven across all six samples
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

Validation checklist for rerun or spot inspection:

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

All six Step `06` jobs completed `0:0`; `FWD_like` / `REV_like` BAM+BAI outputs were published for all six samples; `samtools quickcheck` passed silently; orientation counts TSVs were present; `assigned_fraction = 1.000000` and `unassigned_records = 0` for all six samples; and no Step `06` scratch files remained.

## Step 07: bcftools mpileup

Status:

```text
implemented locally
locally tested with mocked bcftools
real-bcftools runtime and cluster validation pending
not cluster-proven
```

No command in this section has yet produced inspected Step `07` cluster evidence. The prior compute-node probe confirmed bcftools `1.21` at `/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools` with exit code `0:0`; it did not validate this workflow.

Implemented files:

```text
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
configs/step_07_partitions.pilot.tsv
configs/step_07_partitions.primary_contigs.tsv
configs/step_07_partitions.example.tsv
```

Partition manifest schema:

```text
partition_id    selector_type    selector_value
```

`region` passes `selector_value` to bcftools `-r`. `regions_file` passes it to `-R`; a relative regions-file path resolves from the partition manifest directory. The primary manifest is the declared correction universe. The separate one-row pilot manifest selects `pilot_1` at `1:1-100000`. Never replace either contract with a VCF glob.

Before any Step `07` dry-run, locate or deliberately provision the full
cluster `samples.tsv`. It is absent from the current Git checkout, and neither
its cluster-local persistence nor its current bytes have been inspected.
Update that full runtime manifest with the optional `replicate` column carrying
the approved Step `09` pairs:

```text
ABE_EV_2 / ABE_PUM1_2 -> 2
ABE_EV_3 / ABE_PUM1_3 -> 3
ABE_EV4  / ABE_PUM1_4 -> 4
```

Use `configs/step_09_pairs.NORAD_EV_PUM1.tsv` only as a reference while editing
the full manifest; it is not a runtime overlay. Validate the full manifest:

```bash
python scripts/validate_manifest.py --manifest samples.tsv
head -1 samples.tsv
sed -n '1,8p' configs/step_09_pairs.NORAD_EV_PUM1.tsv
sha256sum samples.tsv 2>/dev/null || shasum -a 256 samples.tsv
```

The generic validator permits empty optional `replicate` values, so also
assert that the runtime manifest's exact `(sample_id, condition, replicate)`
set matches the approved pairing reference:

```bash
diff -u \
  <(tail -n +2 configs/step_09_pairs.NORAD_EV_PUM1.tsv | LC_ALL=C sort) \
  <(awk -F '\t' '
      NR == 1 {
          for (i = 1; i <= NF; i++) {
              if ($i == "sample_id") sample_column = i
              if ($i == "condition") condition_column = i
              if ($i == "replicate") replicate_column = i
          }
          if (!sample_column || !condition_column || !replicate_column) exit 1
          next
      }
      {
          if ($sample_column == "" || $condition_column == "" ||
              $replicate_column == "") exit 1
          print $sample_column "\t" $condition_column "\t" $replicate_column
      }
  ' samples.tsv | LC_ALL=C sort)
```

The `diff` must be empty with exit status `0`.

This must happen before Step `07` because the manifest SHA-256 is embedded in
the Step `07` receipts, propagated into Step `08`, checked again by Step `09`,
and recorded in the Step `09` summary. If any Step `07` or Step `08` artifacts
were made from the pre-replicate manifest, regenerate them through the normal
upstream workflow; never edit receipt hashes to force a match.

If establishing this file requires adding or changing tracked repository
manifest/config content, stop before `validate-step-07` and create a separately
gated descendant such as `step-07a-runtime-manifest`. Commit the config and
validation change, run the full gate, make a separate docpatch, clean/push, and
create `validate-step-07` from that branch. Do not combine configuration
implementation with an evidence-only validation branch. If the runtime file
is a byte-identical cluster-local copy, record its path and SHA-256 as
validation evidence without fabricating an implementation commit.

Complete the remaining preflight before submission:

```bash
set -euo pipefail

test -z "$(git status --porcelain)"
mkdir -p logs
df -h .
quota -s 2>/dev/null || true
/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools --version
test -s refs/novogene_ref/genome.fa
test -s refs/novogene_ref/genome.fa.fai
test -s refs/novogene_ref/genome.gtf
command -v sha256sum >/dev/null || command -v shasum >/dev/null
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript make real-r-test
```

The exact `/supported/path/to/Rscript` must be visible in the same
compute-node/batch environment planned for Steps `08`-`09`. Run the displayed
test command inside an allocated compute-node or batch context; running it in
the login shell proves only the login-shell environment. Both real-R suites
must pass in the supported execution context; the Step `08` packages and
`sha256sum` or `shasum` must be available. Separately inspect all six samples'
`FWD_like` and `REV_like` BAM/BAI pairs (12 BAM/BAI pairs total), confirm the
reference/GTF identity, and record free-space/quota evidence. The dry-run
validates inputs but does not replace this operator inventory.

Before the first cluster dry-run, inspect the reference contigs and specifically confirm the tracked `MT` selector:

```bash
awk -F '\t' '$1 == "MT" { print }' refs/novogene_ref/genome.fa.fai
sed -n '1,30p' configs/step_07_partitions.primary_contigs.tsv
```

Assert every primary manifest selector appears exactly once in the FAI:

```bash
awk -F '\t' '
    FNR == NR {
        if (FNR > 1) {
            if ($2 != "region" || required[$3]++) exit 1
            required_count++
        }
        next
    }
    { fai_count[$1]++ }
    END {
        if (required_count != 25) exit 1
        for (contig in required) {
            if (fai_count[contig] != 1) {
                print "FAI mismatch for " contig > "/dev/stderr"
                exit 1
            }
        }
        print "primary_fai_contigs=" required_count
    }
' configs/step_07_partitions.primary_contigs.tsv \
  refs/novogene_ref/genome.fa.fai
```

The script validates every selector against the FAI and will fail on spelling differences such as `chr1` versus `1`. The repository currently records the primary set as `1`-`22`, `X`, `Y`, and `MT`, but its exact compatibility with the cluster reference has not yet been inspected for Step `07`.

Direct cluster dry-run for the one-row pilot:

```bash
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.pilot.tsv \
  --partition-id pilot_1 \
  --orientation-root results/orientation \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-root results/mpileup \
  --bcftools-bin /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
```

Dry-run is the default and creates no output directory, lock, scratch path, VCF, or receipt. Inspect the resolved BAM order and both printed pipelines. Each orientation must pass all six manifest-ordered BAMs in one bcftools invocation. The preserved defaults are maximum depth `10000000`, skip indels, FORMAT `DP,AD,ADF,ADR,SP`, INFO `AD,ADF,ADR`, filter `INFO/AD[1-]>2 & MAX(FORMAT/DP)>20`, plain VCF output, and no `bcftools call`.

Planned pilot SLURM dry-run:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
PARTITION_MANIFEST=configs/step_07_partitions.pilot.tsv,\
PARTITION_ID=pilot_1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

Inspect scheduler state and both logs before execute mode:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -160 logs/norad-mpileup-<JOBID>.out
tail -160 logs/norad-mpileup-<JOBID>.err
```

Only after the pilot dry-run is clean, submit the pilot execute job:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
PARTITION_MANIFEST=configs/step_07_partitions.pilot.tsv,\
PARTITION_ID=pilot_1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

One primary chromosome is the next promotion gate:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv,\
PARTITION_ID=1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm

# after inspection of the dry-run job:
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv,\
PARTITION_ID=1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

Do not submit the remaining primary partitions until the one-chromosome outputs pass inspection. Submit each declared partition explicitly; Step `07` does not add a job array or generic dispatcher. The wrapper's `long` partition and eight-hour, one-CPU request are provisional and have not been cluster-proven.

Record pilot and chromosome-1 elapsed time, maximum RSS, and both VCF sizes.
Use those observations to estimate the remaining storage requirement before
submitting the other 24 primary partitions.

Each successful partition publishes this complete set atomically:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

For the pilot, inspect the committed set:

```bash
cohort=NORAD_EV_PUM1
partition=pilot_1
out_dir="results/mpileup/$cohort/$partition"
fwd="$out_dir/$cohort.$partition.FWD_like.mpileup.vcf"
rev="$out_dir/$cohort.$partition.REV_like.mpileup.vcf"
receipt="$out_dir/$cohort.$partition.step07_outputs.tsv"
bcftools=/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools

ls -lh "$fwd" "$rev" "$receipt"
"$bcftools" view -h "$fwd"
"$bcftools" view -h "$rev"
"$bcftools" query -l "$fwd"
"$bcftools" query -l "$rev"
"$bcftools" view -H "$fwd" | wc -l
"$bcftools" view -H "$rev" | wc -l
awk -F '\t' 'NR == 1 || NR <= 3 { print }' "$receipt"
```

Compare both `query -l` results exactly, line for line, with the `sample_id` order in `samples.tsv`. Reconcile the two observed record counts with the receipt. A header-only VCF is valid when its header and sample order validate and the receipt records `0`.

The receipt records cohort, partition selector, orientation, VCF path, both manifest hashes, sample count, and record count. It is published last and is the downstream commit marker. A VCF pair without its matching valid receipt is incomplete and must not be consumed.

Execute mode validates input BAM/BAI pairs, FASTA/FAI, selectors, VCF structure, sample order, record counts, and stable manifests. It uses an owned cohort/partition lock, run-token scratch paths, validation-before-publication, rollback, and owned cleanup. Do not delete a foreign lock or adopt an incomplete output set without first inspecting its owner and scheduler state.

Primary Step `07` exit gate:

```text
25 primary partition receipts
50 structurally valid primary VCFs
exact manifest-ordered six-sample columns in every VCF
one unchanged replicate-bearing sample-manifest hash
one unchanged primary partition-manifest hash
receipt record counts reconciled
all jobs COMPLETED 0:0 with logs and outputs inspected
no owned lock or run-token scratch residue
```

`pilot_1` adds one receipt and two VCFs under the output root, but it is
validation-only. Exclude it from the 25/50 totals and never include it in the
Step `08` correction universe.

Count only manifest-named primary outputs, never every file under the output
root:

```bash
set -euo pipefail

cohort=NORAD_EV_PUM1
partition_manifest=configs/step_07_partitions.primary_contigs.tsv
receipt_count=0
vcf_count=0

while IFS=$'\t' read -r partition_id selector_type selector_value; do
    [[ "$partition_id" == "partition_id" ]] && continue
    out_dir="results/mpileup/$cohort/$partition_id"
    receipt="$out_dir/$cohort.$partition_id.step07_outputs.tsv"
    test -s "$receipt"
    for orientation in FWD_like REV_like; do
        test -s "$out_dir/$cohort.$partition_id.$orientation.mpileup.vcf"
        vcf_count=$((vcf_count + 1))
    done
    receipt_count=$((receipt_count + 1))
done < "$partition_manifest"

[[ "$receipt_count" -eq 25 ]]
[[ "$vcf_count" -eq 50 ]]
printf 'primary_receipts=%s primary_vcfs=%s\n' "$receipt_count" "$vcf_count"
```

This loop intentionally never reads the pilot manifest. Continue with the
per-file bcftools/sample-order, receipt-hash, selector, and record-count
validation; counts alone are not proof.

Cluster promotion order:

```text
Step 07 dry-run
-> pilot execute and output inspection
-> one primary chromosome execute and output inspection
-> remaining approved primary partitions and combined receipt inspection
-> Step 07 evidence docpatch
-> Step 08 runtime validation
-> Step 08 evidence docpatch
-> Step 09 runtime validation
-> Step 09 evidence docpatch
```

Remote promotion is paused during the approved local implementation sequence.
When it resumes, create validation branches only after the final local
validator branch is clean, docpatched, and pushed:

```text
post09-validation-report-09
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Each validation branch receives its inspected evidence/status docpatch,
clean-status/history check, and push before the next branch is created.
Each remote validation branch must also regenerate the structured run summary
and consolidated HTML/PDF report in results storage after evidence inspection,
then record the report paths and hashes in its evidence docpatch. Cluster proof
and biological readiness remain independent.

## Step 08: VCF Preprocessing

Status:

```text
implemented locally at implementation commit 90335d8
locally tested with shell/fake-R coverage
real-R fixture suite passes locally without SKIP
cluster validation pending
not cluster-proven
```

No Step `08` cluster dry-run, execute job, log, or output evidence has been
inspected. Do not runtime-promote Step `08` before Step `07` is
cluster-proven.

Implemented files:

```text
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
jobs/step_08_vcf_preprocessing.slurm
tests/shell/test_step_08_vcf_preprocessing.sh
tests/r/run_step_08_vcf_preprocessing_tests.sh
tests/r/test_step_08_vcf_preprocessing.R
```

Runtime requirements:

```text
supported Rscript
VariantAnnotation
GenomicRanges
IRanges
S4Vectors
SummarizedExperiment
GenomeInfoDb
BiocGenerics
rtracklayer
sha256sum or shasum
```

The wrapper does not guess an R module or install packages. Record a supported
cluster executable/environment and pass it explicitly. `Rscript` resolution is
the CLI `--rscript-bin`, then `RSCRIPT_BIN_OVERRIDE`, then `Rscript` on
`PATH`. The R implementation defaults to
`scripts/step_08_vcf_preprocessing.R` and can be overridden with
`--r-script` or `STEP08_R_SCRIPT`.

Before the Step `08` dry-run, prove the exact batch-visible environment:

```bash
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript make real-r-test
```

Both Step `08` and Step `09` real-R fixture suites must pass. A missing
runtime/package or a `SKIP` does not satisfy this gate. Execute the command in
an allocated compute-node/batch context; a login-shell pass alone does not
prove batch visibility.

The direct production dry-run below hashes and validates the complete declared
input set. It is an interface/reference command for an allocated compute-node
context, not a login-node command. Use the SLURM dry-run below for cluster
promotion.

Direct dry-run:

```bash
scripts/step_08_vcf_preprocessing.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --rscript-bin /supported/path/to/Rscript
```

Dry-run is the default. It validates and prints the exact declared input set
and R command, invokes no R process, and creates no output directory, lock,
temporary file, or final output.

Only after Step `07` is cluster-proven and the supported R environment and
packages have passed the real-R fixtures, add execute mode:

The direct command below documents the shell interface. Run production-scale
execution through the SLURM wrapper; do not run it on the cluster login node.
Direct execute is limited to an explicitly allocated compute-node context or a
tiny approved fixture.

```bash
scripts/step_08_vcf_preprocessing.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --rscript-bin /supported/path/to/Rscript \
  --execute
```

SLURM dry-run:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_08_vcf_preprocessing.slurm
```

SLURM execute, only after the dry-run and prerequisites are inspected:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_08_vcf_preprocessing.slurm
```

Wrapper variables and defaults:

```text
COHORT_ID=NORAD_EV_PUM1
SAMPLE_MANIFEST=samples.tsv
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv
STEP07_ROOT=results/mpileup
ANNOTATION_GTF=refs/novogene_ref/genome.gtf
OUTPUT_ROOT=results/vcf_preprocessed
QC_ROOT=results/qc/vcf_preprocessing
RSCRIPT_BIN_OVERRIDE=<unset; defaults to Rscript on PATH>
STEP08_R_SCRIPT=scripts/step_08_vcf_preprocessing.R
EXECUTE=0
```

The current job requests the `long` partition, eight hours, and one CPU. Those
resources are provisional and have not been cluster-proven. The engine now
makes one additional bounded-memory streaming pass over each VCF before
`VariantAnnotation` parsing. During future runtime promotion, benchmark that
extra I/O on a representative pilot or chromosome-scale input set using an
isolated output namespace, and record input size, elapsed time, and maximum
RSS before relying on the full-universe resource request.

Step `08` constructs the exact partition-manifest cross-product with
`FWD_like` and `REV_like`; it never globs VCFs. It requires each partition's
Step `07` receipt and named two-orientation VCF pair, validates receipt/VCF
paths and SHA-256 hashes, declared/observed record counts, both manifest
hashes, and exact sample-manifest VCF column order. It also rejects overlapping
partition selectors, duplicate partition-independent candidate IDs, and
inputs that change during the run.

Before semantic VCF parsing, the R implementation streams the raw records in
bounded chunks and validates the lexical values and expected widths of every
consumed `FORMAT/DP`, `FORMAT/AD`, and present `INFO/AD` field. This prevents a
malformed token from being coerced into a parsed numeric value by
`VariantAnnotation`. An AD value may be a single `.` when the whole vector is
missing; otherwise its width must equal REF plus every ALT.
The semantic parse then expands multiallelic records by ALT index, extracts the
matching alternate AD, counts and excludes symbolic and non-SNV alleles, and
fails on missing FORMAT/INFO definitions, malformed or negative counts,
one-sided missing DP/AD, AD greater than DP, or sample/count inconsistencies.
Partition-overlap rejection was already correct and its fixture now asserts
the expected failure reason. Header-only VCFs remain valid when their receipts
and zero counts reconcile.

The provisional mapping is:

```text
orientation_policy=legacy_provisional_v1
FWD_like -> legacy neg -> compatible + transcripts -> complement genomic REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain genomic REF/ALT
```

This is legacy compatibility behavior, not a biologically validated
orientation policy.

Successful execute mode publishes:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The sites table has fixed genomic/RNA/annotation metadata followed by
manifest-ordered `DP__<sample>`, `AD__<sample>`, and `AF__<sample>` columns.
The input receipt has one row per declared partition/orientation, in partition
manifest order with `FWD_like` then `REV_like`, and records input hashes and
observed/supported/skipped/published counts. The summary reconciles those
counts across the cohort.

Validation checklist after a future execute run:

```bash
cohort=NORAD_EV_PUM1
sites="results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv"
inputs="results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv"
summary="results/qc/vcf_preprocessing/$cohort.step08_summary.tsv"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
ls -lh "$sites" "$inputs" "$summary"
head -2 "$sites"
cat "$inputs"
cat "$summary"
```

Require all three outputs, exact schemas, the declared number/order of receipt
rows, correct sample column groups, stable hashes, globally unique candidate
IDs, and the invariants:

```text
observed ALT = supported SNV + skipped symbolic + skipped non-SNV
published candidate count = supported SNV count
each summary allele/count total = the matching input-receipt column sum
summary published candidate count = sites-table row count
```

For the approved primary manifest, require exactly `50` data rows in
`step08_inputs.tsv` (`25` partitions by two orientations) in declared
partition order with `FWD_like` then `REV_like`. Require one
`COMPLETED 0:0` job, inspected logs, all three files, and no owned lock or
run-token scratch residue.

Assert the exact partition/orientation sequence:

```bash
awk -F '\t' '
    FNR == NR {
        if (FNR > 1) {
            partition[++partition_count] = $1
        }
        next
    }
    FNR == 1 {
        for (i = 1; i <= NF; i++) {
            if ($i == "partition_id") partition_column = i
            if ($i == "orientation") orientation_column = i
        }
        if (!partition_column || !orientation_column) exit 1
        next
    }
    {
        row = FNR - 1
        expected_partition = partition[int((row + 1) / 2)]
        expected_orientation = (row % 2 ? "FWD_like" : "REV_like")
        if ($partition_column != expected_partition ||
            $orientation_column != expected_orientation) exit 1
    }
    END {
        if (partition_count != 25 || row != 50) exit 1
        print "step08_input_rows=" row
    }
' configs/step_07_partitions.primary_contigs.tsv "$inputs"
```

Execute mode owns a cohort lock, uses run-token temporary and backup paths,
validates before publication, and rolls back a prior complete set on failure.
The only valid preexisting state is all three outputs present or all three
absent. Publication order is sites table, summary, then the input receipt last
as the transaction commit marker.

## Step 09: CMH Editing-Site Calling

Status:

```text
implemented locally at implementation commit e4371de
locally tested with shell/fake-R coverage
real-R fixture suite passes locally without SKIP
PDF signature/EOF fixture scans raw bytes
cluster validation pending
not cluster-proven
```

No Step `09` cluster dry-run, execute job, log, output table, plot, or
biological candidate result has been inspected. Do not runtime-promote this
step before Step `08` is cluster-proven.

Implemented files:

```text
scripts/step_09_cmh_editing_site_calling.sh
scripts/step_09_cmh_editing_site_calling.R
jobs/step_09_cmh_editing_site_calling.slurm
tests/shell/test_step_09_cmh_editing_site_calling.sh
tests/r/run_step_09_cmh_tests.sh
tests/r/test_step_09_cmh_editing_site_calling.R
configs/step_09_pairs.NORAD_EV_PUM1.tsv
```

Runtime requirements:

```text
operator-validated Rscript
base R stats, graphics, and grDevices
sha256sum or shasum for the R engine
```

Step `09` does not install R, load a guessed module, or require Bioconductor.
The shell preflight can fall back to `python3` for SHA-256, but execute mode
still requires `sha256sum` or `shasum` because the R engine verifies hashes
independently.
The Step `08` package requirements remain separate. `Rscript` resolution is
CLI `--rscript-bin`, then `RSCRIPT_BIN_OVERRIDE`, then `Rscript` on `PATH`.
The R implementation defaults to the adjacent
`scripts/step_09_cmh_editing_site_calling.R` and may be overridden with
`--r-script` or `STEP09_R_SCRIPT`.

The full sample manifest is the only pairing source. Step `09` requires
`sample_id`, `r1_fastq`, `r2_fastq`, `strandedness`, `condition`, and
`replicate`; `notes` remains optional. Each replicate must contain exactly one
control and one treatment, both conditions must have identical replicate sets,
and at least two strata are required. Pairing is never inferred from names.

The direct production dry-run below parses and validates the production sites
table and receipt. It is an interface/reference command for an allocated
compute-node context, not a login-node command. Use the SLURM dry-run below for
cluster promotion.

Direct dry-run:

```bash
scripts/step_09_cmh_editing_site_calling.sh \
  --analysis-id NORAD_EV_vs_PUM1 \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-root results/vcf_preprocessed \
  --output-root results/editing \
  --rscript-bin /supported/path/to/Rscript
```

Dry-run is the default. It resolves the executable, validates the current
manifest/partition hashes, prints every manifest-defined pair, derives exactly:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
```

and validates the Step `08` sites table plus complete input receipt. This
includes receipt order,
cohort/sample counts, both manifest hashes, `FWD_like` then `REV_like` for
every declared partition, exact manifest-ordered `DP__`, `AD__`, and `AF__`
columns, candidate uniqueness, row counts, count/AF consistency, and
`orientation_policy=legacy_provisional_v1`. Dry-run prints the exact R command
but does not invoke R, acquire a lock, or create an output directory.

Default analysis:

```text
control: EV
treatment: PUM1
RNA change: A>G
minimum per-sample DP: 1
mean analysis DP: strictly >50
BH FDR: strictly <0.05
common OR: strictly >1.2 or <1/1.2
absolute treatment-control fraction difference: strictly >0.005
background condition: disabled
background maximum fraction when enabled: strictly <0.01
```

The optional background condition must differ from control and treatment. EV
must never be repurposed as a missing no-dox cohort.

Only after Step `08` is cluster-proven, the supported R environment passes both
real-R fixture suites, and the Step `09` dry-run is inspected, add execute mode:

The direct command below documents the shell interface. Run production-scale
execution through the SLURM wrapper; do not run it on the cluster login node.
Direct execute is limited to an explicitly allocated compute-node context or a
tiny approved fixture.

```bash
scripts/step_09_cmh_editing_site_calling.sh \
  --analysis-id NORAD_EV_vs_PUM1 \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-root results/vcf_preprocessed \
  --output-root results/editing \
  --rscript-bin /supported/path/to/Rscript \
  --execute
```

SLURM dry-run:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_09_cmh_editing_site_calling.slurm
```

SLURM execute, only after the dry-run and upstream gates are inspected:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_09_cmh_editing_site_calling.slurm
```

Wrapper variables and defaults:

```text
ANALYSIS_ID=NORAD_EV_vs_PUM1
COHORT_ID=NORAD_EV_PUM1
SAMPLE_MANIFEST=samples.tsv
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv
STEP08_ROOT=results/vcf_preprocessed
OUTPUT_ROOT=results/editing
CONTROL_CONDITION=EV
TREATMENT_CONDITION=PUM1
RNA_REF=A
RNA_ALT=G
MIN_SAMPLE_DP=1
MEAN_DP_THRESHOLD=50
FDR_THRESHOLD=0.05
COMMON_OR_THRESHOLD=1.2
ABSOLUTE_DIFFERENCE_THRESHOLD=0.005
BACKGROUND_CONDITION=<empty; disabled>
BACKGROUND_MAX_FRACTION=0.01
RSCRIPT_BIN_OVERRIDE=<unset; defaults to Rscript on PATH>
STEP09_R_SCRIPT=scripts/step_09_cmh_editing_site_calling.R
EXECUTE=0
```

The current job requests the `long` partition, eight hours, and one CPU with no
explicit memory request. Those resources are provisional and have not been
cluster-proven.

For each successfully testable target candidate, the R engine builds
treatment/control by edited/unedited tables for every manifest-defined
replicate and runs two-sided
`mantelhaen.test(..., correct=TRUE, exact=FALSE)`. The common odds ratio is
treatment relative to control. BH is applied once across all successfully
tested target candidates from every partition and orientation before
mean-depth, background, FDR, or effect call filters.

The all-sites table retains non-target, missing-count, low-coverage, and
degenerate candidates. Exact status values are:

```text
test_status:
  not_target_change | missing_counts | low_coverage | degenerate_table | tested
call_status:
  not_tested | below_mean_dp | background_not_passed | fdr_not_met |
  effect_not_met | significant_up | significant_down
background_status:
  disabled | pass | missing_counts | low_coverage | fail_fraction
```

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
39 fixed provenance/count/threshold fields. The mutation table always emits
the 12 canonical substitutions. Both plots use a fixed 7-by-5-inch base-R
device, are signature/EOF validated, and include valid empty-input plots.

Validation checklist after a future execute run:

```bash
set -euo pipefail

analysis=NORAD_EV_vs_PUM1
out_dir="results/editing/$analysis"
all="$out_dir/$analysis.cmh_all_sites.tsv"
significant="$out_dir/$analysis.cmh_significant_sites.tsv"
summary="$out_dir/$analysis.cmh_summary.tsv"
spectrum="$out_dir/$analysis.mutation_spectrum.tsv"
spectrum_pdf="$out_dir/$analysis.mutation_spectrum.pdf"
depth_pdf="$out_dir/$analysis.depth_delta.pdf"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
ls -lh "$all" "$significant" "$summary" "$spectrum" "$spectrum_pdf" "$depth_pdf"
head -2 "$all"
head -2 "$significant"
cat "$summary"
cat "$spectrum"
test "$(head -c 5 "$spectrum_pdf")" = '%PDF-'
test "$(head -c 5 "$depth_pdf")" = '%PDF-'
tail -c 2048 "$spectrum_pdf" | grep -aFq -- '%%EOF'
tail -c 2048 "$depth_pdf" | grep -aFq -- '%%EOF'
```

Require all six files, exact schemas, a single summary row, 12 mutation rows,
preserved all-sites row order, a deterministic significant subset, reconciled
status/count totals, current input hashes, and `%PDF-` signatures. A
valid PDF must also contain its `%%EOF` marker near the end. A
header-only Step `08` sites table is valid: all-sites and significant remain
header-only, the summary has one row, the spectrum has 12 zero-count rows, and
both PDFs remain valid.

Also require the all-sites data-row count to equal the Step `08` sites data-row
count; significant-sites must be the exact ordered subset with
`significant_up` or `significant_down`; summary status totals and upstream
manifest/input hashes must reconcile; the default run must record background
disabled; the job must be `COMPLETED 0:0`; and no owned lock or run-token
scratch residue may remain.

Assert the row-count and exact-subset contract:

For production tables, run this full-table scan inside an allocated
compute-node/batch context, not on the login node.

```bash
set -euo pipefail

analysis=NORAD_EV_vs_PUM1
out_dir="results/editing/$analysis"
all="$out_dir/$analysis.cmh_all_sites.tsv"
significant="$out_dir/$analysis.cmh_significant_sites.tsv"
summary="$out_dir/$analysis.cmh_summary.tsv"
spectrum="$out_dir/$analysis.mutation_spectrum.tsv"
step08_sites="results/vcf_preprocessed/NORAD_EV_PUM1/NORAD_EV_PUM1.step08_sites.tsv"
step08_rows=$(awk 'END { print NR - 1 }' "$step08_sites")
all_rows=$(awk 'END { print NR - 1 }' "$all")
summary_rows=$(awk 'END { print NR - 1 }' "$summary")
spectrum_rows=$(awk 'END { print NR - 1 }' "$spectrum")

[[ "$all_rows" -eq "$step08_rows" ]]
[[ "$summary_rows" -eq 1 ]]
[[ "$spectrum_rows" -eq 12 ]]

diff -u \
  <(awk -F '\t' '
      NR == 1 {
          for (i = 1; i <= NF; i++) {
              if ($i == "call_status") call_column = i
          }
          if (!call_column) exit 1
          print
          next
      }
      $call_column == "significant_up" ||
      $call_column == "significant_down" { print }
  ' "$all") \
  "$significant"
```

The `diff` must be empty with exit status `0`. These checks supplement, rather
than replace, schema, hash, status-total, PDF, scheduler, log, lock, and scratch
inspection.

Execute mode atomically acquires:

```text
results/editing/<analysis>/.<analysis>.step09.lock/
```

It uses run-token temporary and backup paths, requires either all six stable
outputs or none, verifies immutable inputs before and after R, validates every
temporary file, publishes five non-summary files, then publishes the summary
last as the transaction commit marker. It revalidates final content and hashes.
A failed replacement restores the previous complete set.

If a foreign lock exists, inspect its `owner` file, SLURM state, logs, stable
outputs, and run-token scratch paths; never delete or adopt it blindly. If
rollback cannot restore a complete state, the script deliberately retains its
owned lock and any recovery evidence. Inspect the reported finals/backups and
perform an explicit operator recovery before another run.

## Post-Step 09: Scientific Validation Gate

Status:

```text
approved local Step 09c evidence-package contract
not yet implemented at the Step 09b1 boundary
production evidence and scientific review remain unavailable
not a rerun of CMH and not a biological interpretation engine
```

The `step-09b1-real-r-fixes` documentation, clean-history, and push gate is
complete at docpatch `859aba2`. Create `step-09c-scientific-validation` from
that completed branch and implement a local dry-run-first Python/shell evidence
package with this public interface:

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
  --output-root OUTPUT_ROOT

# add --execute only to publish validated evidence records
```

Execute mode publishes atomically under
`results/scientific_validation/<review_id>/`:

```text
<review>.step09c_review_plan.tsv
<review>.step09c_evidence_index.tsv
<review>.step09c_orientation_locus_audit.tsv
<review>.step09c_annotation_audit.tsv
<review>.step09c_qc_funnel.tsv
<review>.step09c_replicate_effects.tsv
<review>.step09c_sensitivity_matrix.tsv
<review>.step09c_leave_one_pair_out.tsv
<review>.step09c_candidate_selection.tsv
<review>.step09c_candidate_adjudication.tsv
<review>.step09c_decisions.tsv
<review>.step09c_limitations.tsv
<review>.step09c_review_summary.tsv
```

The summary is published last as the transaction marker. The package validates
and summarizes explicit evidence; it does not rerun CMH statistics, infer
reviewer decisions, or turn synthetic fixtures into production evidence.
Only schemas, examples, and synthetic fixtures are committed.

Keep these status dimensions independent:

```text
computational status:
  implementation / local tests / runtime blocking /
  cluster dry-run / cluster proof

overall science status:
  evidence_incomplete
  science_review_complete_exploratory

evidence category:
  missing / incomplete / complete / justified not_applicable

orientation:
  provisional / validated / replacement_required
```

`biological_interpretation_ready` is reserved and Step `09c` must reject it
until a separately approved policy branch unlocks explicit exit criteria.
Background, matched-DNA, orthogonal-evidence, annotation, threshold, and
adjudication decisions remain separate explicit dimensions.

Review:

* library protocol, RSeQC, read flags, transcript strand, genomic/RNA alleles,
  and raw counts at predeclared plus-strand and minus-strand transcript loci
  under both current and inverted normalization policies;
* Novogene GTF path/identity/SHA-256 and delivery provenance, with exact
  release recorded if recoverable or explicitly accepted as unresolved, plus
  predeclared CDS, UTR, exon, intron, intergenic, overlap, and
  multi-transcript annotation semantics;
* the Step `07` -> Step `08` -> Step `09` count/status funnel by partition and
  orientation, mutation spectrum, orientation balance, and per-sample DP/AF;
* predeclared threshold sensitivity under distinct non-overwriting analysis
  IDs, per-replicate AF/delta,
  leave-one-pair-out behavior, the unweighted mean-sample-AF metric,
  replicate-direction discordance, `ABE_EV_2`, and replicate `4` duplication;
* deterministic top, discordant, and near-threshold candidate quality,
  bias, splice/repeat/multimapping/duplicate/indel, annotation, and
  polymorphism evidence;
* whether an eligible distinct background cohort exists and whether the
  strict all-sample `<0.01` rule is intended. Never use EV as no-dox.

Before inspecting concordance or rankings, freeze deterministic
locus/candidate selection, sample size, both orientations and plus/minus
transcript-strand coverage, sensitivity grid/decision thresholds, input
hashes, git commit, commands/scripts/software versions, reviewer/date/decision
owner, and current/superseded analysis IDs. Every sensitivity run preserves
the primary transaction; a testability/family change recomputes BH.

Record compact evidence tables, paths, hashes, reviewers, limitations,
matched-DNA availability, and decisions. A>G enrichment is supportive but does
not independently validate orientation. Candidate review/PI approval is not
orthogonal experimental validation. Close as
`science_review_complete_exploratory` when review is complete but results
remain provisional. Do not emit `biological_interpretation_ready` under the
current policy.

Keep production-derived audit/adjudication tables in approved results storage.
Commit only compact non-sensitive summaries, paths, hashes, and decisions
unless explicit approval permits tracking a safe fixture; never add full
biological result snapshots by default.

Rerun matrix:

```text
manifest / partition universe -> gated config/evidence package, then Steps 07-09
Step 07 filter / maximum depth
  -> contract/versioning decision plus distinct namespace or added provenance,
     then Steps 07-09
new background samples -> prove Steps 01-06 inputs, then Steps 07-09
background already in unchanged Step 08 columns -> new Step 09 analysis ID
GTF input -> Steps 08-09
orientation normalization policy
  -> Steps 08-09 contract/code/tests/docpatch, then Steps 08-09 runtime
supported Step 09 target / unchanged-manifest contrast or background /
  min-DP / defaults
  -> new analysis ID and recomputed BH over the applicable full family
CMH method/correction or testability logic
  -> Step 09 implementation/tests/docpatch, then new-ID runtime validation
FASTA or coordinates -> upstream reference/alignment impact review
manual adjudication labels -> no compute rerun
new automated filter -> separate implementation/test/docpatch package
```

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
