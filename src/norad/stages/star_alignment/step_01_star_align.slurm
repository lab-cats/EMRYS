#!/usr/bin/env bash
#SBATCH --job-name=norad-star-align
#SBATCH --partition=long
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=8
#SBATCH --export=ALL,TMPDIR=/tmp

# SLURM wrapper for Step 01 STAR alignment.
#
# Defaults support a dry-run smoke test. Real cluster execution should pass
# sample-specific paths through environment variables and set EXECUTE=1.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"

# Defaults support a safe dry-run smoke test.
SAMPLE_ID="${SAMPLE_ID:-sample_001}"
R1_FASTQ="${R1_FASTQ:-data/test/sample_001_R1.fastq.gz}"
R2_FASTQ="${R2_FASTQ:-data/test/sample_001_R2.fastq.gz}"
STAR_INDEX="${STAR_INDEX:-refs/test_star_index}"
OUTPUT_DIR="${OUTPUT_DIR:-results/test/sample_001/star}"
EXECUTE="${EXECUTE:-0}"

# Guard the execution flag before creating fixtures or invoking STAR.
if [[ "$EXECUTE" != "0" && "$EXECUTE" != "1" ]]; then
    die "EXECUTE must be 0 or 1."
fi

default_fixture_mode=0
if [[ "$SAMPLE_ID" == "sample_001" \
   && "$R1_FASTQ" == "data/test/sample_001_R1.fastq.gz" \
   && "$R2_FASTQ" == "data/test/sample_001_R2.fastq.gz" \
   && "$STAR_INDEX" == "refs/test_star_index" ]]; then
    default_fixture_mode=1
fi

# Prevent accidental real execution with placeholder dry-run fixture paths.
if [[ "$EXECUTE" == "1" && "$default_fixture_mode" == "1" ]]; then
    die "Refusing to execute with default dry-run fixture parameters. Pass real SAMPLE_ID/R1_FASTQ/R2_FASTQ/STAR_INDEX/OUTPUT_DIR."
fi

# Ensure TMPDIR points somewhere writable.
if [[ -z "${TMPDIR:-}" || ! -w "${TMPDIR:-}" ]]; then
    export TMPDIR="/tmp/${USER}/${SLURM_JOB_ID:-manual}"
    mkdir -p "$TMPDIR"
fi

threads="${SLURM_CPUS_PER_TASK:-8}"

# Print job context before loading modules or invoking the step script.
echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: $TMPDIR"

echo "Loaded modules before STAR load:"
module list 2>&1 || true

# Load STAR inside the job so the wrapper does not rely on an interactive shell.
module load star/2.7.11b

echo "Loaded modules after STAR load:"
module list 2>&1 || true

# Default dry-run fixture support only.
if [[ "$default_fixture_mode" == "1" && "$EXECUTE" == "0" ]]; then
    echo "Using default dry-run fixtures."
    mkdir -p "$(dirname "$R1_FASTQ")" "$STAR_INDEX"
    [[ -f "$R1_FASTQ" ]] || : > "$R1_FASTQ"
    [[ -f "$R2_FASTQ" ]] || : > "$R2_FASTQ"
fi

echo "Resolved STAR SLURM parameters:"
echo "  SAMPLE_ID:  $SAMPLE_ID"
echo "  R1_FASTQ:   $R1_FASTQ"
echo "  R2_FASTQ:   $R2_FASTQ"
echo "  STAR_INDEX: $STAR_INDEX"
echo "  OUTPUT_DIR: $OUTPUT_DIR"
echo "  THREADS:    $threads"
echo "  EXECUTE:    $EXECUTE"

# Delegate workflow logic to the final stage owner; keep SLURM as a wrapper.
cmd=(
    bash src/norad/stages/star_alignment/step_01_star_align.sh
    --sample-id "$SAMPLE_ID"
    --r1-fastq "$R1_FASTQ"
    --r2-fastq "$R2_FASTQ"
    --star-index "$STAR_INDEX"
    --output-dir "$OUTPUT_DIR"
    --threads "$threads"
)

if [[ "$EXECUTE" == "1" ]]; then
    cmd+=(--execute)
fi

echo "Wrapper command:"
print_command "${cmd[@]}"

# Run the step script after logging the exact wrapper command.
"${cmd[@]}"

echo "Finished: $(date)"
