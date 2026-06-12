#!/bin/bash
#SBATCH --job-name=norad-star-dry-run
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=4
#SBATCH --export=ALL,TMPDIR=/tmp

set -euo pipefail

# Ensure TMPDIR points somewhere writable.
if [[ -z "${TMPDIR:-}" || ! -w "${TMPDIR:-}" ]]; then
    export TMPDIR="/tmp/${USER}/${SLURM_JOB_ID:-manual}"
    mkdir -p "$TMPDIR"
fi

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: $TMPDIR"

echo "Loaded modules before STAR load:"
module list 2>&1 || true

module load star/2.7.11b

echo "Loaded modules after STAR load:"
module list 2>&1 || true

sample_id="sample_001"
r1_fastq="data/test/sample_001_R1.fastq.gz"
r2_fastq="data/test/sample_001_R2.fastq.gz"
star_index="refs/test_star_index"
output_dir="results/test/sample_001/star"
threads="${SLURM_CPUS_PER_TASK:-4}"

# Dry-run fixtures only: create placeholders if absent so validation can pass
# without committing real FASTQ or STAR reference data.
mkdir -p "$(dirname "$r1_fastq")" "$star_index"
if [[ ! -f "$r1_fastq" ]]; then
    : > "$r1_fastq"
fi
if [[ ! -f "$r2_fastq" ]]; then
    : > "$r2_fastq"
fi

bash scripts/step_01_star_align.sh \
    --sample-id "$sample_id" \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$output_dir" \
    --threads "$threads"

echo "Finished: $(date)"
