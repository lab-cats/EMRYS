#!/usr/bin/env bash
#SBATCH --job-name=norad-split-n-cigar
#SBATCH --partition=short
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 05 GATK SplitNCigarReads on one sample.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly after Step 04 has
# produced duplicate-marked BAMs and Step 00c sidecars exist.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"

export TMPDIR="${TMPDIR:-/tmp}"

cd "${SLURM_SUBMIT_DIR:-$PWD}"

SAMPLE_ID="${SAMPLE_ID:-ABE_EV_2}"
INPUT_BAM="${INPUT_BAM:-results/markdup/${SAMPLE_ID}/${SAMPLE_ID}.markdup.bam}"
REFERENCE_FASTA="${REFERENCE_FASTA:-refs/novogene_ref/genome.fa}"
OUTPUT_DIR="${OUTPUT_DIR:-results/split_ncigar/${SAMPLE_ID}}"
GATK_BIN="${GATK_BIN_OVERRIDE:-/cm/shared/apps/gatk/gatk-4.6.1.0/gatk}"
SAMTOOLS_BIN="${SAMTOOLS_BIN_OVERRIDE:-/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools}"
EXECUTE="${EXECUTE:-0}"

# Keep the wrapper's execution gate narrow and explicit; the script receives
# --execute only when the SLURM environment says EXECUTE=1.
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
echo "Reference FASTA: $REFERENCE_FASTA"
echo "Reference FAI: $REFERENCE_FASTA.fai"
echo "Reference DICT: $(dirname "$REFERENCE_FASTA")/$(basename "${REFERENCE_FASTA%.*}").dict"
echo "Output directory: $OUTPUT_DIR"
echo "Output BAM: $OUTPUT_DIR/${SAMPLE_ID}.split_ncigar.bam"
echo "Output BAI: $OUTPUT_DIR/${SAMPLE_ID}.split_ncigar.bam.bai"
echo "GATK: $GATK_BIN"
echo "samtools: $SAMTOOLS_BIN"
echo "Execute mode: $EXECUTE"

echo "Loaded modules before Step 05 setup:"
module list 2>&1 || true

# Direct ADAM paths are passed to the script because module PATH behavior has
# been inconsistent; loading samtools is only for log context when available.
module load samtools/1.19.2 || true

# Do not trust JAVA_HOME or module names alone. Resolve an actual executable and
# validate its runtime version before the GATK wrapper can start Java.
validate_and_print_java "GATK SplitNCigarReads" JAVA_BIN JAVA_VERSION_OUTPUT "" 17 "Set JAVA_BIN_OVERRIDE to a Java 17 executable." "" true

echo "Loaded modules after Step 05 setup:"
module list 2>&1 || true

if [[ -x "$SAMTOOLS_BIN" ]]; then
    echo "samtools version:"
    "$SAMTOOLS_BIN" --version | head -n 2
else
    echo "WARNING: samtools path is not executable before script validation: $SAMTOOLS_BIN"
fi

if [[ -x "$GATK_BIN" ]]; then
    echo "GATK version:"
    "$GATK_BIN" --version
else
    echo "WARNING: GATK path is not executable before script validation: $GATK_BIN"
fi

cmd=(
    bash
    src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh
    --sample-id "$SAMPLE_ID"
    --input-bam "$INPUT_BAM"
    --reference-fasta "$REFERENCE_FASTA"
    --output-dir "$OUTPUT_DIR"
    --gatk-bin "$GATK_BIN"
    --samtools-bin "$SAMTOOLS_BIN"
    --java-bin "$JAVA_BIN"
    "${execute_args[@]}"
)

# The script owns GATK/samtools command construction, validation, locking, and
# final BAM/BAI publication. This wrapper supplies cluster defaults only.
echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

OUTPUT_BAM="$OUTPUT_DIR/${SAMPLE_ID}.split_ncigar.bam"
OUTPUT_BAI="$OUTPUT_BAM.bai"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -s "$OUTPUT_BAM" ]] || die "Expected output BAM does not exist or is empty: $OUTPUT_BAM"
    [[ -s "$OUTPUT_BAI" ]] || die "Expected output BAI does not exist or is empty: $OUTPUT_BAI"

    echo "Validated Step 05 SplitNCigarReads outputs:"
    ls -lh "$OUTPUT_BAM" "$OUTPUT_BAI"
else
    echo "Step 05 completed in dry-run mode; output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
