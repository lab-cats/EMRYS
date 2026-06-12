#!/bin/bash
#SBATCH --job-name=norad-validate-manifest
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp

set -euo pipefail

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"

module load python39

python --version

python scripts/validate_manifest.py \
  --manifest samples.example.tsv \
  --base-dir .

echo "Finished: $(date)"
