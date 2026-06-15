# NORAD / CSU HPC RNA-seq Workflow

This repository contains code, tests, documentation, and SLURM job wrappers for a NORAD / PUM1 / rABE-related Novogene Remora RNA-seq workflow.

The project is being rebuilt as a maintainable, manifest-driven, dry-run-first pipeline for:

* local development on macOS
* full-scale execution on CSU's SLURM cluster
* RNA-seq preprocessing
* strandedness/orientation inference
* downstream RNA-editing / variant-like site calling

The uploaded legacy workflow is treated as a protocol reference, not as production code.

A future decoupled reporting layer is planned to consume structured pipeline artifacts and render reusable HTML, PDF, and TSV outputs without rerunning computation. That layer is roadmap-only and not implemented.

## Current Status

The upstream preprocessing workflow is now proven through duplicate marking across the six-sample cohort. Step `05` SplitNCigarReads is implemented locally and awaits cluster validation; later editing-prep steps remain scaffolded until implemented.

| Step | Purpose | Status |
| ---- | ------- | ------ |
| `00a` | Build Novogene STAR index | cluster-proven |
| `00b` | Convert GTF to BED12 for RSeQC | cluster-proven |
| `00c` | GATK reference sidecars / reference FASTA index and sequence dictionary | implemented locally; pending formal cluster validation |
| `01` | STAR alignment | complete and cluster-proven across all six samples |
| `02` | Canonical sorted/read-group/indexed BAM | hardened and cluster-proven across all six samples |
| `02b` | BAM QC with samtools | implemented and refreshed across all six final hardened Step 02 BAMs |
| `03` | Infer strandedness/orientation with RSeQC | cluster-proven across all six samples |
| `04` | Picard MarkDuplicates | cluster-proven across all six samples |
| `05` | GATK SplitNCigarReads | implemented locally; pending cluster validation |
| `06` | Split BAMs by read orientation | scaffolded / not implemented / not cluster-proven |
| `07` | bcftools mpileup by chromosome and orientation/strand | scaffolded / not implemented / not cluster-proven |
| `08` | VCF preprocessing | scaffolded / not implemented / not cluster-proven |
| `09` | CMH editing-site calling | scaffolded / not implemented / not cluster-proven |

Step `02b` currently creates its output directory before dry-run exit, so do not describe that dry-run as side-effect-free. Its final cohort refresh succeeded after prepending the known samtools bin directory to `PATH`; the first failed attempt was a cluster environment/PATH issue, not a BAM/QC failure.

## Cohort And Key Results

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

All six libraries are paired-end and reverse-stranded / first-strand-style by Step `03`. Tool-specific examples that often correspond to this orientation are:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

Do not treat those options as universally interchangeable without naming the tool.

## Biological And Computational Goal

This repository supports RNA-seq / RNA-editing workflow reconstruction for NORAD / PUM1 / rABE-related analysis.

The intended workflow is:

```text
FASTQ(.gz)
    ->
STAR alignment
    ->
canonical sorted/read-group/indexed BAM
    ->
BAM QC
    ->
RSeQC strandedness/orientation inference
    ->
Picard duplicate marking
    ->
GATK reference sidecar validation
    ->
GATK SplitNCigarReads
    ->
read-orientation BAM splitting
    ->
bcftools mpileup
    ->
VCF preprocessing
    ->
CMH/editing-site calling
```

This is not currently a simple gene-count differential-expression workflow. The downstream reference workflow points toward RNA-editing / variant-like site analysis.

## Development Model

The intended development loop is:

```text
implement locally
    ->
run local tests
    ->
commit and push
    ->
pull on cluster
    ->
submit SLURM dry-run
    ->
inspect logs
    ->
submit SLURM execute job
    ->
inspect outputs
    ->
update docs
    ->
proceed to next step
```

The cluster login node should not be used for heavy computation. It is for editing, Git operations, small file transfers, light checks, file inspection, and submitting jobs.

Full analysis should run through SLURM jobs in `jobs/`.

## Quick Start: Local Development

Clone the repo:

```bash
git clone https://github.com/Glen-Cocoa/norad.git
cd norad
```

Create and activate a local Python environment if needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Record dependency or tooling changes in `requirements.txt`, `environment.yml`, or another project setup document rather than leaving them implicit.

Run the local validation gate:

```bash
git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
```

Shortcut for the Makefile-covered checks:

```bash
make all-checks
```

Validate the example manifest:

```bash
python scripts/validate_manifest.py \
  --manifest samples.example.tsv
```

To also check file existence:

```bash
python scripts/validate_manifest.py \
  --manifest samples.example.tsv \
  --base-dir . \
  --check-files
```

## Quick Start: Cluster Execution

On the cluster:

```bash
cd ~/norad
git pull
git status --short
mkdir -p logs
```

Run a dry-run job first:

```bash
sbatch jobs/<step>.slurm
```

Inspect the job:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

If the dry-run looks correct, run execute mode:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Then inspect outputs before proceeding.

## Operator Checklist

- **Default dry-run:** Workflow shell scripts and SLURM wrappers default to dry-run. Submit a dry-run first to verify resolved inputs, printed commands, and logs.
- **Submit execute jobs explicitly:** Use `EXECUTE=1` when ready, e.g.:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

- **Script-level execution flag:** Workflow shell scripts use `--execute` to run tool commands; include all required step arguments when invoking a script directly.
- **Validation locations:** Use `docs/RUNBOOK.md` for per-step dry-run/execute checks, `docs/PIPELINE_PLAN.md` for step status, and `DECISIONS.md` for execution policy.
- **Quick checks after execute:** Confirm expected outputs under `results/`, inspect SLURM logs under `logs/`, and use `sacct` for job state.

## Repository Layout

```text
scripts/        # Python, shell, and later R scripts
jobs/           # SLURM job wrappers
tests/          # local tests and pending test plans
configs/        # optional config files
data/test/      # tiny local test fixtures only
data/raw/       # large/raw data symlinks; not committed
data/full/      # optional full-scale data paths; not committed
results/        # generated outputs; not committed
logs/           # SLURM stdout/stderr logs; not committed
docs/           # project documentation
```

Large data files and generated outputs should stay out of Git.

## Important Documentation Files

```text
docs/HANDOFF.md        big project-state handoff
docs/PIPELINE_PLAN.md  tactical step map and validation status
docs/QUESTIONS.md      answered/open project questions
docs/RUNBOOK.md        operational commands and cluster procedure
TROUBLESHOOTING.md     symptom -> cause -> fix
DECISIONS.md           decisions and reasons
TODO.md                tactical next work
README.md              entrypoint / overview
```

## Data And Reference Locations

### Local repo

```text
/Users/elisteiger/dev/norad
```

### Cluster repo

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

### Raw data symlink on cluster

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs live under:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

### Reference files

Prepared reference files:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

Reference notes:

* Novogene-provided GRCh38-like reference.
* Chromosome names are numeric-style, for example `1`, `2`, `3`, not `chr1`, `chr2`, `chr3`.
* FASTA and GTF chromosome names match.
* STAR index was built with `sjdbOverhang=149` for 150 bp reads.
* BED12 annotation was generated from the GTF for RSeQC.
* Step `00c` now formalizes GATK sidecar prep with `scripts/step_00c_prepare_gatk_reference.sh` and `jobs/step_00c_prepare_gatk_reference.slurm`; the formal job is pending cluster validation.

## Confirmed Tools On CSU

Known modules/tools:

```text
star/2.7.11b
samtools/1.19.2
bedtools/2.31.1
picard/3.1.1
python39
java/17.0.10
GATK 4.6.1.0: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
bcftools 1.21: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
```

Picard is exposed through the jar path set by the module. Step `04` validates the selected Java executable and actual runtime version before Picard starts.

RSeQC is available through the project virtual environment:

```text
.venv/bin/infer_experiment.py
```

GATK and bcftools were validated on compute node `node002`; the tool probe completed successfully with exit code `0:0`.

Still unresolved:

```text
R / Rscript
```

## Beginner Glossary

`FASTQ` / `.fastq.gz`: raw sequencing reads. For paired-end data, `R1` is the first read and `R2` is the second read.

`SAM`: human-readable alignment format.

`BAM`: compressed binary alignment format.

`BAI`: BAM index file.

`STAR`: splice-aware RNA-seq aligner used here to align FASTQs to the reference.

`samtools`: alignment-file toolkit used for sorting, indexing, filtering, and inspecting BAMs.

`Picard`: preprocessing/QC toolkit; current use here is duplicate marking with `MarkDuplicates`.

`GATK`: genomics toolkit; Step `05` uses `SplitNCigarReads` for RNA-seq preprocessing after duplicate marking.

`R`: downstream analysis, statistics, visualization, and tables.

## Git And Data Policy

Use Git for:

* source code
* SLURM job wrappers
* configuration files
* documentation
* small safe test fixtures

Do not commit:

* FASTQ / FASTQ.GZ
* SAM / BAM / CRAM / BAI
* large TSV/CSV outputs
* logs
* results directories
* credentials or tokens
* `.env` files
* private SSH keys
* large raw reference/data files

Tiny test fixtures may be committed only if they are small, safe, and non-sensitive.
