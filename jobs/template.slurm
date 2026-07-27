#!/bin/bash
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --job-name=norad-template
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4

# Template for future NORAD SLURM wrappers.
#
# Keep analysis logic in scripts/ and use this file as a resource/module/logging
# pattern when adding new cluster jobs.
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

# Show the inherited module state before the job loads its own requirements.
module list 2>&1 || true

# Load modules here, e.g.:
# CSU modules discovered so far.
module load star/2.7.11b
module load samtools/1.19.2
module load picard/3.1.1
module load python39
# module load gatk/...
# module load R/...

# Show the final module state and basic tool versions for debugging logs.
module list 2>&1 || true

echo "Tool versions:"
python --version
STAR --version
samtools --version | head -1
java -version
echo "PICARD: ${PICARD:-not set}"

# Run workflow step here.

echo "Finished: $(date)"
