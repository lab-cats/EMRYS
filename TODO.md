# TODO

Current tactical TODOs for the NORAD / Novogene Remora RNA-seq pipeline.

This file is for actionable next work. For broader context, see:

```text
docs/HANDOFF.md
docs/PIPELINE_PLAN.md
docs/QUESTIONS.md
docs/RUNBOOK.md
DECISIONS.md
TROUBLESHOOTING.md
```

## Current state

Implemented and cluster-proven for `ABE_EV_2`:

```text
00a  Build STAR index
00b  Convert GTF to BED12
01   STAR alignment
02   Canonical sort/index BAM
02b  BAM QC
03   RSeQC strandedness/orientation inference
```

Pending / scaffold-only:

```text
04   MarkDuplicates
05   SplitNCigarReads
06   Split BAM by read orientation
07   bcftools mpileup
08   VCF preprocessing
09   CMH editing-site calling
```

Step 03 result for `ABE_EV_2` indicates strong reverse-stranded / first-strand-style behavior.

## Immediate next TODO

### 1. Decide next development move

Choose one:

```text
A. Continue downstream development on ABE_EV_2 with Step 04 MarkDuplicates.
B. Pause and generalize/run Steps 01-03 across all six samples first.
```

Current recommendation:

```text
Continue with Step 04 on ABE_EV_2 for development speed.
Later, run Steps 01-03 across all six samples before final global assumptions.
```

### 2. Validate Step 04: Picard MarkDuplicates on cluster

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

```bash
module load picard/3.1.1
java -jar "$PICARD" MarkDuplicates ...
```

Implemented local behavior:

```text
- dry-run by default
- execute only with --execute / EXECUTE=1
- validate input BAM and BAI
- validate Picard jar through $PICARD
- write duplicate-marked BAM with REMOVE_DUPLICATES=false
- write metrics file
- validate duplicate-marked BAM with samtools quickcheck
- index output BAM
- validate output BAM, BAI, and metrics
- local shell tests use fake java/Picard and fake samtools
```

Decision already made:

```text
Mark duplicates; do not remove duplicates unless a specific reason is documented.
```

### 3. Validate Step 04 on cluster

After local implementation and commit/push:

```bash
ssh csu-hpc
norad
git pull
git status --short
mkdir -p logs
```

Dry-run:

```bash
sbatch jobs/step_04_mark_duplicates.slurm
sjcheck <JOBID>
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_04_mark_duplicates.slurm
sjcheck <JOBID>
```

Inspect expected outputs before declaring Step 04 proven.

## Near-term TODOs

### Run Steps 01-03 across all six samples

Eventually run implemented upstream steps for:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

Purpose:

```text
- produce canonical BAMs for all samples
- run BAM QC for all samples
- confirm strandedness/orientation across all samples
```

Do this before finalizing global strandedness assumptions.

### Begin designing manifest-driven execution

The next architectural piece is manifest-driven sample selection for SLURM arrays.

Eventually needed:

```bash
scripts/get_manifest_row.py \
  --manifest samples.tsv \
  --row "$SLURM_ARRAY_TASK_ID"
```

or:

```bash
scripts/get_sample_from_manifest.py \
  --manifest samples.tsv \
  --sample-id ABE_EV_2
```

Purpose:

```text
Allow SLURM array task N to select sample N from samples.tsv.
```

Do not overbuild this yet.

Recommended timing:

```text
After Step 04 is proven on ABE_EV_2, begin designing sample-selection helpers.
Before running the full six-sample workflow at scale, implement manifest-driven arrays.
```

### Decide output layout for downstream processed BAMs

Current likely layout:

```text
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt

results/splitncigar/<sample>/<sample>.splitncigar.bam
results/splitncigar/<sample>/<sample>.splitncigar.bam.bai

results/orientation/<sample>/<sample>.<orientation>.bam
results/orientation/<sample>/<sample>.<orientation>.bam.bai
```

Confirm this before implementing Step 04/05/06 too deeply.

## External blockers / unresolved items

### GATK availability

Still unresolved.

Known:

```bash
module avail gatk
```

did not show a visible GATK module.

Need to determine whether GATK should be run through:

```text
- a differently named module
- a jar
- conda/mamba
- container
- project-local install
```

Blocks:

```text
Step 05: SplitNCigarReads
```

### R / Rscript availability

Still unresolved.

Needed for:

```text
Step 08: VCF preprocessing
Step 09: CMH editing-site calling
```

Need to identify module name, environment, or project-local installation plan.

### bcftools availability

Still unresolved.

Needed for:

```text
Step 07: bcftools mpileup
```

Need to identify module name or installation path.

### Storage quotas

Still unresolved.

Need to document:

```text
- home quota
- /mnt/stor-pool-01/users/2609214 quota
- scratch availability
- whether temp files should use scratch or /tmp
```

### Exact annotation version

Partially unresolved.

Known:

```text
Reference came from Novogene 04.Ref delivery.
Genome is GRCh38-like.
Chromosome names are numeric-style.
```

Still need:

```text
Exact annotation release/version if recoverable from files or Novogene docs.
```

## Later TODOs

### Step 05: SplitNCigarReads

Implement after GATK availability is resolved.

Needs:

```text
- duplicate-marked BAM
- reference FASTA
- FASTA .fai
- sequence dictionary .dict
- GATK invocation method
```

### Step 06: split BAM by read orientation

Old workflow used samtools flag groupings similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Important:

```text
Do not assume old FWD/REV labels equal biological sense/antisense.
Step 03 indicates reverse-stranded / first-strand behavior for ABE_EV_2.
```

Step 06 must clearly document read orientation versus transcript strand.

### Step 07: bcftools mpileup

Needs decisions:

```text
- bcftools module/location
- chromosome/region handling
- reference FASTA path
- per-sample vs grouped mpileup strategy
- FWD/REV or orientation-specific output naming
```

### Step 08: VCF preprocessing

Port from uploaded `vcf_preprocess1.R`.

Needs:

```text
- remove hardcoded paths
- make CLI-driven
- make manifest-driven where appropriate
- document strand/orientation assumptions
- define output table format
```

### Step 09: CMH editing-site calling

Port from uploaded `Edit_call_cmh.R`.

Needs:

```text
- remove hardcoded paths
- define expected input tables
- define comparison structure
- define final output tables/plots
- document statistical assumptions
```

## Deferred roadmap: structured artifacts and reporting

This work should begin only after the core computational workflow is substantially proven. It is planned, deferred, and non-runnable for now. Do not create schema files, placeholder scripts, templates, report directories, sidecar files, or SLURM jobs until this roadmap is explicitly activated.

The future layers should remain distinct:

```text
per-step JSON sidecars: future cross-cutting pipeline capability
run_summary.json aggregation: future downstream phase
HTML/PDF/TSV rendering: separate report layer
```

Deferred phases:

```text
A. Define and version the artifact schema.
B. Add shared artifact-writing utilities.
C. Retrofit proven steps to emit sidecars.
D. Define the richer CMH/editing-site artifact schema.
E. Aggregate sidecars into run_summary.json.
F. Implement HTML reporting.
G. Add PDF and TSV renderers.
```

## Resolved items

### Step 01 STAR wrapper

Resolved.

Step 01 has been implemented and cluster-proven for `ABE_EV_2`.

### Step 02 samtools sort/index wrapper

Resolved.

Step 02 has been implemented and cluster-proven for `ABE_EV_2`.

### Step 02b BAM QC

Resolved.

Step 02b has been implemented and cluster-proven for `ABE_EV_2`.

### Step 03 strandedness/orientation inference

Resolved for `ABE_EV_2`.

RSeQC indicates strong reverse-stranded / first-strand behavior.

Still need to run on all samples before final global assumption.

### Real data location

Resolved operationally.

Raw data symlink:

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

### STAR index path

Resolved.

```text
refs/novogene_star_index/
```

### FASTA/GTF paths

Resolved.

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
```

### Genome/reference naming

Resolved enough for current workflow.

Known:

```text
GRCh38-like Novogene reference
numeric-style chromosome names such as 1, 2, 3
FASTA and GTF chromosome names match
```

### Read length

Resolved.

Reads are 150 bp.

STAR index used:

```text
sjdbOverhang=149
```

### Manifest format

Resolved.

TSV is canonical.

Current manifest:

```text
samples.tsv
```

### Cluster TMPDIR behavior

Resolved operationally.

Use:

```text
TMPDIR=/tmp
```

Submit execute jobs with:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

### Picard invocation

Resolved.

Use:

```bash
module load picard/3.1.1
java -jar "$PICARD" <PicardCommand>
```

### Stop condition from earlier TODO

Old stop condition was:

```text
Stop when Step 02 is green.
```

Resolved.

Current state is beyond that:

```text
Steps 00a, 00b, 01, 02, 02b, and 03 are green for ABE_EV_2.
```

## Development rule

Do not jump ahead.

Continue using:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> proceed
```

A TODO is not done until the relevant outputs have been inspected and the docs are updated.
