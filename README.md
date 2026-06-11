# NORAD / CSU HPC RNA-seq Workflow

This repository contains code, configuration, and SLURM job scripts for RNA-seq / lncRNA / NORAD-related analysis.

The workflow is designed for **local development on macOS** and **full-scale execution on CSU's SLURM cluster**.

---

## Project goals

This project supports RNA-seq analysis involving lncRNA/NORAD-related questions.

The current high-level workflow is:

```text
FASTQ(.gz)
    ↓
STAR alignment
    ↓
SAM/BAM
    ↓
samtools preprocessing
    ↓
Picard duplicate marking
    ↓
GATK RNA preprocessing
    ↓
strand-aware BAM generation
    ↓
downstream analysis
```

The repo is structured so that scripts can be tested locally on small representative data, then run at scale on the cluster through SLURM.

---

## Development model

The intended development loop is:

```text
1. Develop and debug locally in VS Code
2. Test on tiny representative data
3. Commit code to Git
4. Sync or pull code on the cluster
5. Submit full-scale jobs with SLURM
6. Inspect logs and results
7. Iterate
```

The cluster login node should not be used for heavy computation. It is for editing, file movement, Git operations, light checks, and submitting jobs.

Full analysis should run through SLURM jobs in `jobs/`.

---

## Handoff philosophy

This repository is being developed as a maintainable research workflow, not a one-off personal script collection.

The goal is that another researcher should be able to take over this project, understand the workflow, run small tests, submit full SLURM jobs, and modify the analysis without needing undocumented context.

To support that, scripts should:

* accept explicit command-line arguments
* avoid hardcoded local or cluster paths
* document required inputs and generated outputs
* provide useful `--help` messages
* fail with clear errors
* support tiny local test runs
* be wrapped by SLURM scripts for full-scale execution

Documentation should explain not only what to run, but what each step is doing and what files it produces.

---

## Repository layout

```text
scripts/        # Python, R, or shell scripts
jobs/           # SLURM job scripts
configs/        # local and cluster config files
data/test/      # tiny local test fixtures only
data/raw/       # large/raw data; not committed
data/full/      # full cluster-scale data; not committed
results/        # generated outputs; not committed
logs/           # SLURM stdout/stderr logs; not committed
docs/           # notes and project documentation
```

Large data files and generated outputs should stay out of Git.

---

## Data and Git policy

Use Git for:

* source code
* SLURM scripts
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

Tiny test fixtures may be committed only if they are small, safe, and non-sensitive.

---

## Local setup

This project is intended to be developed locally in VS Code.

Typical local tools:

* Git
* Python
* R
* VS Code
* Codex / ChatGPT coding assistance
* `rsync` for file transfer
* small local test data

A local Python virtual environment can be created with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

Install project dependencies as needed and record them in a dependency file such as `requirements.txt`, `environment.yml`, or a project-specific setup script.

---

## Cluster usage

The CSU cluster uses SLURM.

Typical commands:

```bash
sbatch jobs/example.slurm
squeue -u <username>
scancel <job_id>
sacct
sinfo
```

SLURM scripts should live in `jobs/` and write logs to `logs/`.

Example log pattern:

```bash
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

Each job should request appropriate resources explicitly, such as runtime, memory, and CPU count.

Example:

```bash
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
```

Cluster software should be loaded inside the SLURM script using environment modules, for example:

```bash
module load python
module load R
module load samtools
```

Exact module names may vary on the CSU cluster.

---

## Running scripts

Scripts should avoid hardcoded paths when possible.

Prefer command-line arguments:

```bash
python scripts/process_sample.py \
  --input data/test/sample.bam \
  --output results/test/
```

The same script should be usable on the cluster by passing cluster paths:

```bash
python scripts/process_sample.py \
  --input /cluster/path/to/full/sample.bam \
  --output /cluster/path/to/results/sample/
```

Config files in `configs/` may be used to separate local test paths from cluster-scale paths.

---

## SLURM job pattern

A minimal SLURM job should look like:

```bash
#!/bin/bash
#SBATCH --job-name=norad-example
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

set -euo pipefail

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"

module list || true

python scripts/example.py \
  --input data/test/example.bam \
  --output results/example/

echo "Finished: $(date)"
```

For many samples, prefer SLURM arrays rather than manually submitting one job at a time.

---

## Bioinformatics tools

### STAR

STAR is a splice-aware RNA-seq aligner.

It aligns RNA-seq reads to a reference genome and handles exon-exon junctions.

Typical input:

* FASTQ

Typical output:

* SAM/BAM

### samtools

`samtools` is used to manipulate alignment files.

Common operations:

* convert SAM/BAM
* sort BAM
* index BAM
* merge BAM
* filter reads

### Picard

Picard is used for preprocessing and QC.

Current expected use:

* duplicate marking with `MarkDuplicates`

### GATK

GATK is a genomics processing toolkit.

Current expected use:

* RNA-seq preprocessing with `SplitNCigarReads`

### R

R is used for downstream analysis, statistics, visualization, and tables.

---

## File formats

### FASTQ

Raw sequencing reads, often compressed as `.fastq.gz`.

For paired-end sequencing:

* `R1` is the first read
* `R2` is the second read

### SAM

Human-readable alignment format.

### BAM

Compressed binary alignment format.

### BAI

Index file for BAM.

---

## Notes

This repo is intentionally organized around a local-first, cluster-execution workflow.

The goal is not to develop directly on the cluster. The goal is to make scripts work locally on small data, then submit reproducible jobs to SLURM for full-scale execution.
