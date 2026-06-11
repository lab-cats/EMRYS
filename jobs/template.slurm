#!/bin/bash
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --job-name=norad-template
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4

set -euo pipefail

# Ensure TMPDIR points somewhere writable.
if [[ -z "${TMPDIR:-}" || ! -w "${TMPDIR:-}" ]]; then
    export TMPDIR="/tmp/${USER}/${SLURM_JOB_ID:-manual}"
    mkdir -p "$TMPDIR"
fi

echo "TMPDIR: $TMPDIR"
echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"

module list || true

# Load modules here, e.g.:
# module load python
# module load R
# module load samtools

# Run workflow step here.

echo "Finished: $(date)"