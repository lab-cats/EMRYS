#!/usr/bin/env bash
#SBATCH --job-name=norad-markdup
#SBATCH --partition=short
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 04 Picard MarkDuplicates on one sample.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly for real execution
# after Step 02 has produced the canonical sorted BAM and index.
set -euo pipefail

# Run from the submitted repository checkout rather than SLURM's spool copy.
: "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
cd "$SLURM_SUBMIT_DIR"

# shellcheck source=../../libraries/argument_parsing.sh
source "src/norad/libraries/argument_parsing.sh"

export TMPDIR="${TMPDIR:-/tmp}"

SAMPLE_ID="${SAMPLE_ID:-ABE_EV_2}"
INPUT_BAM="${INPUT_BAM:-results/bam/${SAMPLE_ID}/${SAMPLE_ID}.sorted.bam}"
OUTPUT_DIR="${OUTPUT_DIR:-results/markdup/${SAMPLE_ID}}"
METRICS_DIR="${METRICS_DIR:-results/qc/markdup}"
EXECUTE="${EXECUTE:-0}"

case "$EXECUTE" in
    0) execute_args=() ;;
    1) execute_args=(--execute) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

# SLURM opens logs/%x-%j.out and logs/%x-%j.err before this script body runs.
# Keep the runbook's pre-submit `mkdir -p logs` gate; this is only defensive.
mkdir -p logs

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"
echo "Sample ID: $SAMPLE_ID"
echo "Input BAM: $INPUT_BAM"
echo "Input BAI: $INPUT_BAM.bai"
echo "Output directory: $OUTPUT_DIR"
echo "Output BAM: $OUTPUT_DIR/${SAMPLE_ID}.markdup.bam"
echo "Output BAI: $OUTPUT_DIR/${SAMPLE_ID}.markdup.bam.bai"
echo "Metrics directory: $METRICS_DIR"
echo "Metrics file: $METRICS_DIR/${SAMPLE_ID}.markdup.metrics.txt"
echo "Execute mode: $EXECUTE"

echo "Loaded modules before Picard/samtools load:"
module list 2>&1 || true

module load picard/3.1.1

# CSU's Picard module exposes the jar through PICARD. Fail here rather than
# passing an empty --picard-jar into the script and obscuring the module problem.
if [[ -z "${PICARD:-}" ]]; then
    echo "ERROR: PICARD is not set after loading picard/3.1.1" >&2
    exit 2
fi

module load samtools/1.19.2

echo "Loaded modules after Picard/samtools load:"
module list 2>&1 || true

# Resolve Java explicitly. The CSU Java module may set JAVA_HOME to a path that
# is unavailable on compute nodes, so allow a caller-provided override.
validate_and_print_java "Picard" JAVA_BIN JAVA_VERSION_OUTPUT "" 17 "Set JAVA_BIN_OVERRIDE to a Java 17 executable." "" true

echo "PICARD: $PICARD"
echo "samtools: $(command -v samtools || true)"

cmd=(
    bash
    src/norad/stages/duplicate_marking/step_04_mark_duplicates.sh
    --sample-id "$SAMPLE_ID"
    --input-bam "$INPUT_BAM"
    --output-dir "$OUTPUT_DIR"
    --metrics-dir "$METRICS_DIR"
    --picard-jar "$PICARD"
    --java-bin "$JAVA_BIN"
    "${execute_args[@]}"
)

# The script owns Picard/samtools command construction; this wrapper only
# supplies cluster defaults, modules, and the dry-run/execute gate.
echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

OUTPUT_BAM="$OUTPUT_DIR/${SAMPLE_ID}.markdup.bam"
OUTPUT_BAI="$OUTPUT_BAM.bai"
METRICS_FILE="$METRICS_DIR/${SAMPLE_ID}.markdup.metrics.txt"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -s "$OUTPUT_BAM" ]] || die "Expected output BAM does not exist or is empty: $OUTPUT_BAM"
    [[ -s "$OUTPUT_BAI" ]] || die "Expected output BAI does not exist or is empty: $OUTPUT_BAI"
    [[ -s "$METRICS_FILE" ]] || die "Expected metrics file does not exist or is empty: $METRICS_FILE"

    echo "Validated Step 04 MarkDuplicates outputs:"
    ls -lh "$OUTPUT_BAM" "$OUTPUT_BAI" "$METRICS_FILE"
else
    echo "Step 04 completed in dry-run mode; output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
