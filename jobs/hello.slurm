#!/bin/bash
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --job-name=norad-hello
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1

set -euo pipefail

# Ensure TMPDIR points somewhere writable.
if [[ -z "${TMPDIR:-}" || ! -w "${TMPDIR:-}" ]]; then
    export TMPDIR="/tmp/${USER}/${SLURM_JOB_ID:-manual}"
    mkdir -p "$TMPDIR"
fi

echo "TMPDIR: $TMPDIR"
echo "Job ID: ${SLURM_JOB_ID:-local/no-slurm}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"

python scripts/hello.py

echo "Finished: $(date)"