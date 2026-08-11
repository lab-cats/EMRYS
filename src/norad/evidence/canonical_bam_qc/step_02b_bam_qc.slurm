#!/usr/bin/env bash
#SBATCH --job-name=norad-bam-qc
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 02b BAM integrity/QC checks on one sorted BAM.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly for real execution.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"

SAMPLE_ID="${SAMPLE_ID:-ABE_EV_2}"
BAM="${BAM:-results/bam/${SAMPLE_ID}/${SAMPLE_ID}.sorted.bam}"
OUTPUT_DIR="${OUTPUT_DIR:-results/qc/bam}"
EXECUTE="${EXECUTE:-0}"

case "$EXECUTE" in
    0) execute_args=() ;;
    1) execute_args=(--execute) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

cd "$SLURM_SUBMIT_DIR"

mkdir -p logs "$OUTPUT_DIR"

module load samtools/1.19.2

[[ -f "$BAM" ]] || die "BAM does not exist or is not a file: $BAM"

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"
echo "Sample ID: $SAMPLE_ID"
echo "BAM: $BAM"
echo "Output directory: $OUTPUT_DIR"
echo "Execute mode: $EXECUTE"

echo "Loaded modules:"
module list 2>&1 || true

cmd=(
    bash
    src/norad/evidence/canonical_bam_qc/step_02b_bam_qc.sh
    --sample-id "$SAMPLE_ID"
    --bam "$BAM"
    --output-dir "$OUTPUT_DIR"
    "${execute_args[@]}"
)

echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

QUICKCHECK_OUT="$OUTPUT_DIR/${SAMPLE_ID}.quickcheck.txt"
FLAGSTAT_OUT="$OUTPUT_DIR/${SAMPLE_ID}.flagstat.txt"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -f "$QUICKCHECK_OUT" ]] || die "Expected quickcheck output does not exist: $QUICKCHECK_OUT"
    [[ -f "$FLAGSTAT_OUT" ]] || die "Expected flagstat output does not exist: $FLAGSTAT_OUT"

    echo "Validated Step 02b QC outputs:"
    ls -lh "$QUICKCHECK_OUT" "$FLAGSTAT_OUT"
else
    echo "Step 02b completed in dry-run mode; QC output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
