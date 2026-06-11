# NORAD / CSU HPC dev context

## Purpose

This repository supports RNA-seq / lncRNA / NORAD-related analysis.

The project should be developed locally on macOS in VS Code, then executed at scale on CSU's SLURM cluster.

Prioritize:

* reproducible workflows
* parameterized scripts
* clear local vs cluster execution paths
* small test-data development before full-scale cluster runs
* debuggable logs and outputs

---

## Environment

### Local development

Local environment:

* macOS
* VS Code
* Git
* local test data subset
* ChatGPT/Codex may be used for code assistance

Local workflow:

```text
1. Develop/debug locally on tiny representative data
2. Run local smoke tests
3. Commit changes to Git
4. Sync or pull code on the cluster
5. Submit full-scale jobs through SLURM
6. Inspect logs/results
7. Iterate
```

Do not assume that local paths match cluster paths.

---

## Cluster environment

Cluster:

* CSU HPC / supercomputer environment
* uses SLURM
* uses environment modules via `module load`
* real jobs should run through `jobs/*.slurm`
* do not run heavy computation on the login node

The login node is for:

* editing files
* moving data
* Git operations
* inspecting logs
* submitting jobs
* light smoke tests only

Heavy computation must happen through SLURM.

---

## Repository conventions

Expected structure:

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

Prefer adding new executable workflow steps as scripts in `scripts/` and corresponding SLURM wrappers in `jobs/`.

---

## Git and data rules

Use Git for:

* source code
* SLURM scripts
* configs
* documentation
* small safe test fixtures

Do not commit large data or generated outputs.

Never commit:

* FASTQ / FASTQ.GZ
* SAM / BAM / CRAM / BAI
* large TSV/CSV outputs
* logs
* results directories
* credentials
* tokens
* API keys
* private SSH keys
* `.env` files

Tiny synthetic or representative test fixtures may be committed only if they are small, safe, and non-sensitive.

---

## Path and configuration rules

Do not hardcode machine-specific paths inside analysis scripts.

Prefer:

* command-line arguments
* config files in `configs/`
* explicit input/output paths
* separate local and cluster configs when useful

Scripts should be able to run both locally and on the cluster by changing arguments/configs, not by editing source code.

Example local pattern:

```bash
python scripts/process_sample.py \
  --input data/test/sample.bam \
  --output results/test/
```

Example cluster pattern:

```bash
python scripts/process_sample.py \
  --input /cluster/path/to/full/sample.bam \
  --output /cluster/path/to/results/sample/
```

Avoid hidden assumptions about the current working directory unless clearly documented.

---

## SLURM job conventions

SLURM scripts should:

* live in `jobs/`
* write stdout and stderr to `logs/`
* use explicit resource requests
* use `set -euo pipefail`
* print useful debugging context
* load required modules inside the job script
* avoid relying on the interactive shell environment
* call scripts from `scripts/`
* avoid embedding large amounts of analysis logic directly in the SLURM file

Preferred log pattern:

```bash
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

Preferred job header:

```bash
#!/bin/bash
#SBATCH --job-name=norad-job
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
```

Use SLURM arrays when applying the same operation across many samples.

Example array pattern:

```bash
#SBATCH --array=1-10

SAMPLE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.txt)
python scripts/process_sample.py --sample "$SAMPLE"
```

---

## Code expectations

When writing or modifying scripts:

* use clear command-line interfaces
* prefer `argparse` for Python scripts
* validate input paths before expensive operations
* fail loudly with useful error messages
* write outputs to explicit output directories
* make scripts runnable on tiny local test data
* avoid hidden global state
* avoid hardcoded sample names
* avoid unnecessary cleverness
* keep functions small enough to debug
* print or log enough context to reproduce failures

For Python scripts:

* prefer `pathlib.Path`
* use `if __name__ == "__main__":`
* keep parsing, computation, and file writing separable when reasonable
* use type hints where helpful, but do not over-engineer

For R scripts:

* use `commandArgs(trailingOnly = TRUE)` for script arguments
* document argument order clearly
* remember that `<-` is assignment in R
* avoid hardcoded working directories
* write outputs to explicit paths

---



---

## Self-documenting script expectations

Build scripts as if another researcher will eventually run, debug, and modify them without the original author present.

Every substantial script should be self-documenting from the command line.

For Python scripts:

* use `argparse`
* include a clear `description`
* make required inputs explicit
* provide helpful `help=` text for every argument
* use meaningful argument names like `--input-bam`, `--output-dir`, `--sample-id`
* validate that input files/directories exist before expensive processing
* create output directories intentionally
* print or log enough context to reproduce the run
* expose a useful `--help` interface

A future user should be able to run:

```bash
python scripts/some_step.py --help
```

and understand:

* what the script does
* what inputs it expects
* what outputs it writes
* which arguments are required
* how to run it on test data

Example pattern:

```python
import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process a single RNA-seq BAM file for downstream NORAD analysis."
    )

    parser.add_argument(
        "--input-bam",
        required=True,
        type=Path,
        help="Input BAM file to process.",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where processed outputs will be written.",
    )

    parser.add_argument(
        "--sample-id",
        required=True,
        help="Sample identifier used in output filenames.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input_bam.exists():
        raise FileNotFoundError(f"Input BAM does not exist: {args.input_bam}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Sample ID: {args.sample_id}")
    print(f"Input BAM: {args.input_bam}")
    print(f"Output directory: {args.output_dir}")

    # Analysis logic goes here.


if __name__ == "__main__":
    main()
```

Prefer this kind of self-documenting interface over relying only on README instructions, because README examples can drift out of date.

For R scripts:

* use `commandArgs(trailingOnly = TRUE)`
* validate the expected number of arguments
* document argument order in a header comment
* print the resolved input/output paths at runtime
* fail with clear messages when inputs are missing

General rule:

```text
A script is not handoff-ready until a new user can run its --help or read its header and know how to execute it safely.
```

---

## Local testing expectations

Before writing or modifying a full cluster job, prefer creating a tiny representative test case.

Good test data should include:

* a small number of reads/records
* representative file naming
* paired-end structure when relevant
* edge cases if known
* enough data to exercise the code path without requiring cluster resources

Local testing should verify:

* argument parsing works
* input files are found
* output directories are created
* expected output files are written
* failure messages are understandable

When adding or modifying scripts, add or update committed regression tests where practical.
Prefer tests that can run locally on tiny synthetic fixtures without cluster access.

---

## Bioinformatics context

This project processes RNA-seq data.

High-level pipeline:

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

---

## File formats

### FASTQ (`.fastq`, `.fastq.gz`)

Raw sequencing reads.

Contains:

* read identifier
* nucleotide sequence
* per-base quality scores

For paired-end sequencing:

* `R1` = first read
* `R2` = second read

### SAM (`.sam`)

Human-readable alignment format.

### BAM (`.bam`)

Compressed binary alignment format.

### BAI (`.bai`)

Index for BAM files.

---

## Tooling

### STAR

Purpose:

* splice-aware RNA-seq aligner

Role:

* aligns RNA-seq reads to a reference genome
* handles exon-exon junctions

Input:

* FASTQ

Output:

* SAM/BAM

### samtools

Purpose:

* manipulate alignment files

Common operations:

* convert SAM ↔ BAM
* sort BAM
* index BAM
* merge BAM
* filter reads by flags

### Picard

Purpose:

* preprocessing / QC

Common use:

* `MarkDuplicates`

### GATK

Purpose:

* genomics processing toolkit

Current use:

* `SplitNCigarReads` for RNA-seq preprocessing

### R

Purpose:

* downstream analysis
* statistics
* visualization
* tables

---

---

## Handoff and maintainability expectations

Develop this repository as if another researcher will take over and run or modify the workflow later.

Prioritize:

* clear project structure
* readable code over clever code
* explicit inputs and outputs
* documented assumptions
* reproducible commands
* useful error messages
* small test examples
* version-controlled configs
* minimal hidden state

A future user should be able to understand:

* what each script does
* what inputs it expects
* what outputs it creates
* whether it is meant to run locally or through SLURM
* what modules/software it requires
* how to run a tiny test
* how to run the full cluster workflow
* where logs and results are written

When adding or modifying a script, include:

* a short module/script docstring or header comment
* command-line arguments with `--help`
* an example command in the README or relevant docs
* validation for required input files/directories
* clear output naming
* failure messages that explain what went wrong and how to fix it

Avoid:

* hardcoded user-specific paths
* unexplained magic numbers
* silent overwrites
* assumptions about current working directory
* analysis logic hidden inside SLURM files
* one-off scripts with unclear purpose
* undocumented manual steps

Prefer workflows where a new user can run:

```bash
python scripts/example_step.py --help
```
and

```bash
sbatch jobs/example_step.slurm
```
without needing private context.

## Development assistance expectations

When helping with code in this repository:

* preserve cluster compatibility
* distinguish local vs cluster paths
* prefer small local test subsets first
* assume final execution happens through SLURM
* avoid login-node heavy compute
* explain genomics tooling when useful
* favor debuggable, reproducible workflows
* prefer parameterized scripts over hardcoded paths
* do not commit or suggest committing large biological data
* do not assume software is available unless loaded via module or documented
* when uncertain about cluster-specific behavior, make the uncertainty explicit
* When choosing between a clever compact solution and a boring explicit solution, prefer the boring explicit solution unless performance requires otherwise.

Default preference:

```text
Make it simple.
Make it runnable locally.
Make it scalable through SLURM.
Make failures easy to debug.
```
