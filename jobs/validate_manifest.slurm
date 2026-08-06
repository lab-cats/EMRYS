#!/bin/bash
#SBATCH --job-name=norad-validate-manifest
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp

# SLURM smoke check for the sample manifest validator.
#
# This validates the example manifest from the repository checkout and keeps the
# job lightweight enough for login-node-style debugging through SLURM.
set -euo pipefail

# Print job context before loading Python.
echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"

# Load Python inside the job so validation does not depend on the submit shell.
module load python39

python --version

# Run the manifest validator with repository-relative paths.
python scripts/validate_manifest.py \
  --manifest configs/samples.example.tsv \
  --base-dir .

echo "Finished: $(date)"
