#!/bin/bash
#SBATCH --job-name=norad-hello
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G

set -euo pipefail

echo "Job ID: ${SLURM_JOB_ID:-local/no-slurm}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Directory: $PWD"

python scripts/hello.py

echo "Finished: $(date)"