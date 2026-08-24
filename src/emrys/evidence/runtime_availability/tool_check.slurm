#!/bin/bash
#SBATCH --job-name=emrys-tool-check
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp

# Lightweight cluster job for confirming expected bioinformatics tools load.
#
# This does not run analysis; it records module state, paths, and versions in
# SLURM logs so environment issues are easier to diagnose.
set -euo pipefail

# Print job context before loading modules.
echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"

# Load the currently expected modules explicitly inside the job.
module load python39
module load star/2.7.11b
module load samtools/1.19.2
module load picard/3.1.1

echo
echo "Loaded modules:"
module list 2>&1

# Record resolved executables so PATH/module problems are visible.
echo
echo "Tool paths:"
command -v python
command -v STAR
command -v samtools
command -v java
echo "PICARD=${PICARD:-unset}"

# Record versions without doing any heavy computation.
echo
echo "Versions:"
python --version
STAR --version
samtools --version | head -1
java -version 2>&1 | head -1
java -jar "$PICARD" MarkDuplicates --version || true

echo
echo "Finished: $(date)"
