# Runbook

Operational guide for the NORAD / Novogene Remora RNA-seq pipeline.

This project is developed locally and executed at full scale on the CSU SLURM cluster.

Core workflow rule:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> proceed
```

Do not skip gates. Do not run future scaffold jobs. Keep the pipeline boring.

## Project locations

### Local repo

```bash
/Users/elisteiger/dev/norad
```

### Cluster repo

```bash
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

### Raw data symlink on cluster

```bash
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs are under:

```bash
data/raw/novogene_remora/01.RawData/*.fq.gz
```

### Manifest

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

## Confirmed cluster tools/modules

### STAR

```bash
module load star/2.7.11b
STAR --version
```

Executable:

```bash
STAR
```

### samtools

```bash
module load samtools/1.19.2
samtools --version
```

Executable:

```bash
samtools
```

### bedtools

```bash
module load bedtools/2.31.1
bedtools --version
```

Executable:

```bash
bedtools
```

### Picard

```bash
module load picard/3.1.1
```

Known behavior:

```text
loads java/17.0.10
sets PICARD=/cm/shared/apps/picard/picard/build/libs/picard.jar
```

Invocation:

```bash
java -jar "$PICARD" <PicardCommand>
```

Expected Step 04 tool:

```bash
java -jar "$PICARD" MarkDuplicates ...
```

### Python

Known available modules:

```bash
python39
python3
python314
```

Preferred/current project Python module unless changed later:

```bash
module load python39
```

### RSeQC

RSeQC is available through the project virtual environment on the cluster:

```bash
.venv/bin/infer_experiment.py
```

Step 03 uses:

```bash
.venv/bin/infer_experiment.py -r refs/novogene_ref/genome.bed -i results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
```

## Still unresolved tools

The following have not yet been validated in the rebuilt pipeline:

```text
GATK
R / Rscript
bcftools
```

Specific unresolved issue:

```text
module avail gatk
```

did not show a visible GATK module. Need to determine whether GATK is available through another module name, jar, conda/mamba, or container.

This matters for:

```text
Step 05: GATK SplitNCigarReads
```

## Cluster facts and quirks

### First login / fresh checkout

Confirm identity and location:

```bash
hostname
whoami
pwd
```

Check SLURM and module availability:

```bash
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

Run a lightweight manifest-validation smoke job after cloning or pulling:

```bash
mkdir -p logs
sbatch jobs/validate_manifest.slurm
```

### SLURM

Known working SLURM commands:

```bash
which sbatch
which squeue
which sinfo
squeue -u "$USER"
sinfo
```

Known partition behavior:

```text
short: about 3 hour max walltime
long: about 3 day max walltime
```

Most current development jobs use `short`.

No special account setting has been required so far.

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

This has not been fatal when the job itself logs:

```text
TMPDIR: /tmp
```

### module list

`module list` writes to stderr. In scripts, use:

```bash
module list 2>&1 || true
```

## Optional cluster shell helpers

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

## Manual job checking

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

Watch output directory while a job runs:

```bash
du -sh <output_dir>
ls -lh <output_dir>
```

## Local validation gate

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

## Cluster execution pattern

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

## Reference prep

### Reference inputs

Novogene reference source files:

```text
genome.fa.gz
genome.gtf.gz
genome_gene.fa.gz
```

Prepared reference paths:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_star_index/
```

Reference notes:

```text
Genome: GRCh38-like
Chromosome naming: numeric-style, e.g. 1, 2, 3
Not chr1, chr2, chr3
```

FASTA and GTF chromosome naming match.

### Step 00a: STAR index

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
implemented / cluster-proven
```

### Step 00b: GTF to BED12

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
implemented / cluster-proven
```

## Step 01: STAR alignment

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

Validated sample:

```text
ABE_EV_2
```

Main output:

```bash
results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam
```

Other STAR outputs:

```bash
results/star/ABE_EV_2/ABE_EV_2.Log.final.out
results/star/ABE_EV_2/ABE_EV_2.Log.out
results/star/ABE_EV_2/ABE_EV_2.Log.progress.out
results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab
```

Known STAR stats for `ABE_EV_2`:

```text
Input reads: 21,358,987
Unique mapped: 58.50%
Multi-mapped: 24.19%
Too many loci: 0.52%
Unmapped too short: 16.55%
Approximate total mapped: 83.21%
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

## Step 02: canonical sort, read-group tagging, and BAM indexing

Script:

```bash
scripts/step_02_sort_index_bam.sh
```

Job:

```bash
jobs/step_02_sort_index_bam.slurm
```

Purpose:

```text
Create the canonical downstream BAM for one sample.

The canonical BAM must:
- be coordinate sorted
- contain exactly one @RG header for the sample
- assign every alignment record to that read group
- pass samtools quickcheck
- have a valid BAM index
```

Read-group convention:

```text
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

`LB=<sample_id>` is the current provisional convention until more specific
library or lane metadata is recovered from the sequencing delivery records.

Input for `ABE_EV_2`:

```bash
results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam
```

Outputs:

```bash
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

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

Publication uses rollback protection, but the BAM/BAI pair is not a single
indivisible atomic operation. If a failure occurs after backups begin, Step 02
restores the previous complete canonical pair. If no prior pair existed, it
removes any partially published canonical outputs.

Post-run validation:

```bash
module load samtools/1.19.2

sample=ABE_EV_2
bam="results/bam/$sample/$sample.sorted.bam"

samtools quickcheck "$bam"

samtools view -H "$bam" | grep '^@RG'

total_records="$(samtools view -c "$bam")"
tagged_records="$(samtools view -c -d "RG:$sample" "$bam")"

printf 'Total records: %s\n' "$total_records"
printf 'Records tagged RG:%s: %s\n' "$sample" "$tagged_records"

test "$total_records" -gt 0
test "$tagged_records" -eq "$total_records"

ls -lh "$bam" "$bam.bai"
```

Expected read-group header for `ABE_EV_2`:

```text
@RG	ID:ABE_EV_2	SM:ABE_EV_2	LB:ABE_EV_2	PL:ILLUMINA
```

Durable history:

```text
The original Step 02 sort/index implementation was successfully exercised on
the cluster before read-group hardening. Those pre-hardening BAMs lacked
required read-group metadata and are superseded by the hardened Step 02
contract.
```

Pre-hardening resource measurements:

```text
Elapsed: about 3 minutes 46 seconds
MaxRSS: about 6.8G
Output BAM: about 3.0G
Output BAI: about 3.3M
```

Normal samtools stderr observed:

```text
[bam_sort_core] merging from 4 files and 8 in-memory blocks...
```

Status:

```text
implemented / pending cluster revalidation after read-group hardening
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

Purpose:

```text
Validate canonical BAM integrity and write samtools flagstat summary.
```

Input:

```bash
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
```

Outputs:

```bash
results/qc/bam/ABE_EV_2.quickcheck.txt
results/qc/bam/ABE_EV_2.flagstat.txt
```

Dry-run:

```bash
sbatch jobs/step_02b_bam_qc.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_02b_bam_qc.slurm
```

The execute job also completed successfully with no stderr noted.

Useful output inspection:

```bash
ls -lh results/qc/bam
cat results/qc/bam/ABE_EV_2.quickcheck.txt
head -40 results/qc/bam/ABE_EV_2.flagstat.txt
grep -E "in total|primary|secondary|mapped|properly paired|duplicates" results/qc/bam/ABE_EV_2.flagstat.txt
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

## Step 03: RSeQC strandedness/orientation inference

Script:

```bash
scripts/step_03_infer_strandedness_and_orientation.sh
```

Job:

```bash
jobs/step_03_infer_strandedness_and_orientation.slurm
```

Purpose:

```text
Run RSeQC infer_experiment.py on canonical BAM to infer library strandedness/read orientation.
```

Inputs:

```bash
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
refs/novogene_ref/genome.bed
```

Output:

```bash
results/qc/strandedness/ABE_EV_2.infer_experiment.txt
```

Dry-run:

```bash
sbatch jobs/step_03_infer_strandedness_and_orientation.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_03_infer_strandedness_and_orientation.slurm
```

Output observed:

```text
This is PairEnd Data
Fraction of reads failed to determine: 0.0828
Fraction of reads explained by "1++,1--,2+-,2-+": 0.0432
Fraction of reads explained by "1+-,1-+,2++,2--": 0.8740
```

Interpretation:

```text
ABE_EV_2 appears strongly reverse-stranded / first-strand-style.
```

Equivalent common settings:

```text
featureCounts -s 2
HTSeq stranded=reverse
fr-firststrand
```

Caution:

```text
Only ABE_EV_2 has been checked so far.
Confirm strandedness across all six samples before treating this as a global library-prep assumption.
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

## Step 04: MarkDuplicates

Status:

```text
pending / scaffold only
```

Expected next implementation target.

Expected input:

```bash
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Likely outputs:

```bash
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai
results/qc/markdup/ABE_EV_2.markdup.metrics.txt
```

Expected tool:

```bash
module load picard/3.1.1
java -jar "$PICARD" MarkDuplicates
```

Implementation notes:

```text
Mark duplicates; do not remove duplicates unless there is a documented reason.
Write metrics file.
Index output BAM.
Use dry-run-first behavior.
Use local tests with fake Picard/Java if real Picard is unavailable locally.
```

## Step 05: SplitNCigarReads

Status:

```text
pending / scaffold only
```

Expected tool:

```text
GATK SplitNCigarReads
```

Blocking question:

```text
GATK module/location not yet identified.
```

Needs:

```text
reference FASTA
FASTA .fai
sequence dictionary .dict
duplicate-marked BAM
```

## Step 06: split BAM by read orientation

Status:

```text
pending / scaffold only
```

Old reference workflow used samtools flags similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Important caution:

```text
Do not assume old FWD/REV labels directly equal biological sense/antisense.
Step 03 indicates reverse-stranded / first-strand behavior for ABE_EV_2.
Document read-orientation labels separately from biological transcript strand.
```

## Step 07: bcftools mpileup

Status:

```text
pending / scaffold only
```

Needs validation:

```text
bcftools module/location
reference FASTA path
chromosome/region strategy
sample grouping
output naming
```

## Step 08: VCF preprocessing

Status:

```text
pending / scaffold only
```

Reference source:

```text
uploaded old vcf_preprocess1.R
```

Needs:

```text
remove hardcoded paths
convert to CLI/manifest-driven behavior
document strand/orientation assumptions
```

## Step 09: CMH editing-site calling

Status:

```text
pending / scaffold only
```

Reference source:

```text
uploaded old Edit_call_cmh.R
```

Needs:

```text
remove hardcoded paths
convert to CLI/manifest-driven behavior
define expected final tables/plots
document statistical assumptions
```

## Reference workflow alignment

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

The uploaded legacy scripts should be treated as protocol references, not as runnable production scripts.
