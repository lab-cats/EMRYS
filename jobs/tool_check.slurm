#!/bin/bash
#SBATCH --job-name=norad-tool-check
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp

set -euo pipefail

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"

module load python39
module load star/2.7.11b
module load samtools/1.19.2
module load picard/3.1.1

echo
echo "Loaded modules:"
module list 2>&1

echo
echo "Tool paths:"
command -v python
command -v STAR
command -v samtools
command -v java
echo "PICARD=${PICARD:-unset}"

echo
echo "Versions:"
python --version
STAR --version
samtools --version | head -1
java -version 2>&1 | head -1
java -jar "$PICARD" MarkDuplicates --version || true

echo
echo "Finished: $(date)"
