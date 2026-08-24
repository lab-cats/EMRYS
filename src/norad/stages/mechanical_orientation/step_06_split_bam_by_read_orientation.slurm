#!/usr/bin/env bash
#SBATCH --job-name=norad-split-orientation
#SBATCH --partition=short
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 06 read-orientation BAM splitting on one sample.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly after Step 05 has
# produced split-N-cigar BAMs and indexes.
set -euo pipefail

# Run from the submitted repository checkout rather than SLURM's spool copy.
: "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
cd "$SLURM_SUBMIT_DIR"

export TMPDIR="${TMPDIR:-/tmp}"
# shellcheck source=../../libraries/argument_parsing.sh
source "src/norad/libraries/argument_parsing.sh"
# shellcheck source=../../libraries/orientation.sh
source "src/norad/libraries/orientation.sh"

SAMPLE_ID="${SAMPLE_ID:-ABE_EV_2}"
INPUT_BAM="${INPUT_BAM:-results/split_ncigar/${SAMPLE_ID}/${SAMPLE_ID}.split_ncigar.bam}"
OUTPUT_DIR="${OUTPUT_DIR:-results/orientation/${SAMPLE_ID}}"
QC_DIR="${QC_DIR:-results/qc/orientation}"
THREADS="${THREADS:-1}"
SAMTOOLS_BIN="${SAMTOOLS_BIN_OVERRIDE:-/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools}"
EXECUTE="${EXECUTE:-0}"

# Keep the SLURM execution gate narrow and explicit. The script receives
# --execute only when the job environment says EXECUTE=1.
case "$EXECUTE" in
    0) execute_args=() ;;
    1) execute_args=(--execute) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

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
echo "QC directory: $QC_DIR"
for orientation in "${ORIENTATIONS[@]}"; do
    echo "${orientation} BAM: $OUTPUT_DIR/${SAMPLE_ID}.${orientation}.bam"
    echo "${orientation} BAI: $OUTPUT_DIR/${SAMPLE_ID}.${orientation}.bam.bai"
done
echo "Counts TSV: $QC_DIR/${SAMPLE_ID}.orientation_counts.tsv"
echo "Threads: $THREADS"
echo "samtools: $SAMTOOLS_BIN"
echo "Execute mode: $EXECUTE"

echo "Loaded modules before Step 06 setup:"
module list 2>&1 || true

# Loading the module is useful log context, but the script receives the known
# direct samtools path because PATH behavior has varied on this cluster.
module load samtools/1.19.2 || true

echo "Loaded modules after Step 06 setup:"
module list 2>&1 || true

if [[ -x "$SAMTOOLS_BIN" ]]; then
    echo "samtools version:"
    "$SAMTOOLS_BIN" --version | head -n 2
else
    echo "WARNING: samtools path is not executable before script validation: $SAMTOOLS_BIN"
fi

cmd=(
    bash
    src/norad/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh
    --sample-id "$SAMPLE_ID"
    --input-bam "$INPUT_BAM"
    --output-dir "$OUTPUT_DIR"
    --qc-dir "$QC_DIR"
    --threads "$THREADS"
    --samtools-bin "$SAMTOOLS_BIN"
    "${execute_args[@]}"
)

# The script owns samtools command construction, locking, validation, and
# publication. This wrapper supplies cluster defaults and prints job context.
echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

FWD_BAM="$OUTPUT_DIR/${SAMPLE_ID}.FWD_like.bam"
FWD_BAI="$FWD_BAM.bai"
REV_BAM="$OUTPUT_DIR/${SAMPLE_ID}.REV_like.bam"
REV_BAI="$REV_BAM.bai"
COUNTS_TSV="$QC_DIR/${SAMPLE_ID}.orientation_counts.tsv"

if [[ "$EXECUTE" == "1" ]]; then
    for orientation in "${ORIENTATIONS[@]}"; do
        bam_path="$OUTPUT_DIR/${SAMPLE_ID}.${orientation}.bam"
        bai_path="$bam_path.bai"
        [[ -s "$bam_path" ]] || die "Expected ${orientation} BAM does not exist or is empty: $bam_path"
        [[ -s "$bai_path" ]] || die "Expected ${orientation} BAI does not exist or is empty: $bai_path"
    done
    [[ -s "$COUNTS_TSV" ]] || die "Expected counts TSV does not exist or is empty: $COUNTS_TSV"

    echo "Validated Step 06 read-orientation outputs:"
    ls -lh "$FWD_BAM" "$FWD_BAI" "$REV_BAM" "$REV_BAI" "$COUNTS_TSV"
else
    echo "Step 06 completed in dry-run mode; output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
