#!/usr/bin/env bash
#SBATCH --job-name=emrys-mpileup
#SBATCH --partition=long
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 07 cohort mpileup on one declared partition.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly after Step 06 has
# produced every manifest sample's FWD_like and REV_like BAM/index pairs.
set -euo pipefail

# Run from the submitted repository checkout rather than SLURM's spool copy.
: "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
cd "$SLURM_SUBMIT_DIR"

export TMPDIR="${TMPDIR:-/tmp}"
# shellcheck source=../../libraries/argument_parsing.sh
source "src/emrys/libraries/argument_parsing.sh"

: "${COHORT_ID:?COHORT_ID is required}"
: "${SAMPLE_MANIFEST:?SAMPLE_MANIFEST is required}"
: "${PARTITION_MANIFEST:?PARTITION_MANIFEST is required}"
: "${PARTITION_ID:?PARTITION_ID is required}"
: "${ORIENTATION_ROOT:?ORIENTATION_ROOT is required}"
: "${REFERENCE_FASTA:?REFERENCE_FASTA is required}"
: "${OUTPUT_ROOT:?OUTPUT_ROOT is required}"
: "${BCFTOOLS_BIN_OVERRIDE:?BCFTOOLS_BIN_OVERRIDE is required}"

MAX_DEPTH="${MAX_DEPTH:-10000000}"
FILTER_EXPRESSION="${FILTER_EXPRESSION:-INFO/AD[1-]>2 & MAX(FORMAT/DP)>20}"
BCFTOOLS_BIN="$BCFTOOLS_BIN_OVERRIDE"
EXECUTE="${EXECUTE:-0}"

# Keep the SLURM execution gate narrow and explicit. The script receives
# --execute only when the job environment says EXECUTE=1.
case "$EXECUTE" in
    0|1) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

mkdir -p logs

PARTITION_OUTPUT_DIR="$OUTPUT_ROOT/$COHORT_ID/$PARTITION_ID"
FWD_VCF="$PARTITION_OUTPUT_DIR/${COHORT_ID}.${PARTITION_ID}.FWD_like.mpileup.vcf"
REV_VCF="$PARTITION_OUTPUT_DIR/${COHORT_ID}.${PARTITION_ID}.REV_like.mpileup.vcf"
OUTPUT_RECEIPT="$PARTITION_OUTPUT_DIR/${COHORT_ID}.${PARTITION_ID}.step07_outputs.tsv"

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"
echo "Cohort ID: $COHORT_ID"
echo "Sample manifest: $SAMPLE_MANIFEST"
echo "Partition manifest: $PARTITION_MANIFEST"
echo "Partition ID: $PARTITION_ID"
echo "Orientation root: $ORIENTATION_ROOT"
echo "Reference FASTA: $REFERENCE_FASTA"
echo "Reference FAI: $REFERENCE_FASTA.fai"
echo "Output root: $OUTPUT_ROOT"
echo "FWD_like VCF: $FWD_VCF"
echo "REV_like VCF: $REV_VCF"
echo "Output receipt: $OUTPUT_RECEIPT"
echo "Maximum depth: $MAX_DEPTH"
echo "Filter expression: $FILTER_EXPRESSION"
echo "bcftools: $BCFTOOLS_BIN"
echo "Execute mode: $EXECUTE"

echo "Loaded modules for Step 07:"
if command -v module >/dev/null 2>&1; then
    module list 2>&1 || true
else
    echo "module command unavailable; using the explicit bcftools path"
fi

if [[ -x "$BCFTOOLS_BIN" ]]; then
    echo "bcftools version:"
    "$BCFTOOLS_BIN" --version
else
    echo "WARNING: bcftools path is not executable before script validation: $BCFTOOLS_BIN"
fi

cmd=(
    bash
    src/emrys/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.sh
    --cohort-id "$COHORT_ID"
    --sample-manifest "$SAMPLE_MANIFEST"
    --partition-manifest "$PARTITION_MANIFEST"
    --partition-id "$PARTITION_ID"
    --orientation-root "$ORIENTATION_ROOT"
    --reference-fasta "$REFERENCE_FASTA"
    --output-root "$OUTPUT_ROOT"
    --max-depth "$MAX_DEPTH"
    --filter-expression "$FILTER_EXPRESSION"
    --bcftools-bin "$BCFTOOLS_BIN"
)
if [[ "$EXECUTE" == "1" ]]; then
    cmd+=(--execute)
fi

# The script owns bcftools command construction, locking, validation, and
# publication. This wrapper supplies cluster defaults and prints job context.
echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -s "$FWD_VCF" ]] || die "Expected FWD_like VCF does not exist or is empty: $FWD_VCF"
    [[ -s "$REV_VCF" ]] || die "Expected REV_like VCF does not exist or is empty: $REV_VCF"
    [[ -s "$OUTPUT_RECEIPT" ]] || die "Expected output receipt does not exist or is empty: $OUTPUT_RECEIPT"

    echo "Validated Step 07 cohort mpileup outputs:"
    ls -lh "$FWD_VCF" "$REV_VCF" "$OUTPUT_RECEIPT"
else
    echo "Step 07 completed in dry-run mode; output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
