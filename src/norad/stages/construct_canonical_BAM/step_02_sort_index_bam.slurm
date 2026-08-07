#!/bin/bash
#SBATCH --job-name=norad-sort-index-bam
#SBATCH --partition=short
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8

# SLURM wrapper for Step 02 samtools sort/index on one sample.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly for real execution.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"

export TMPDIR=/tmp

SAMPLE_ID="${SAMPLE_ID:-ABE_EV_2}"
INPUT_ALIGNMENT="${INPUT_ALIGNMENT:-results/star/${SAMPLE_ID}/${SAMPLE_ID}.Aligned.sortedByCoord.out.bam}"
OUTPUT_DIR="${OUTPUT_DIR:-results/bam/${SAMPLE_ID}}"
THREADS="${THREADS:-8}"
EXECUTE="${EXECUTE:-0}"

case "$EXECUTE" in
    0) execute_args=() ;;
    1) execute_args=(--execute) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

mkdir -p logs "$OUTPUT_DIR"

[[ -f "$INPUT_ALIGNMENT" ]] || die "Input alignment does not exist or is not a file: $INPUT_ALIGNMENT"

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: $TMPDIR"
echo "Sample ID: $SAMPLE_ID"
echo "Input alignment: $INPUT_ALIGNMENT"
echo "Output directory: $OUTPUT_DIR"
echo "Threads: $THREADS"
echo "Execute mode: $EXECUTE"

echo "Loaded modules before samtools load:"
module list 2>&1 || true

module load samtools/1.19.2

echo "Loaded modules after samtools load:"
module list 2>&1 || true

cmd=(
    bash src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh
    --sample-id "$SAMPLE_ID"
    --input-alignment "$INPUT_ALIGNMENT"
    --output-dir "$OUTPUT_DIR"
    --threads "$THREADS"
    "${execute_args[@]}"
)

echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

OUTPUT_BAM="$OUTPUT_DIR/${SAMPLE_ID}.sorted.bam"
OUTPUT_BAI="$OUTPUT_BAM.bai"

echo "Input alignment details:"
ls -lh "$INPUT_ALIGNMENT"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -f "$OUTPUT_BAM" ]] || die "Expected output BAM does not exist: $OUTPUT_BAM"
    [[ -f "$OUTPUT_BAI" ]] || die "Expected output BAI does not exist: $OUTPUT_BAI"

    echo "Output BAM details:"
    ls -lh "$OUTPUT_BAM"
    echo "Output BAI details:"
    ls -lh "$OUTPUT_BAI"
else
    echo "Dry-run completed; output BAM/BAI validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
