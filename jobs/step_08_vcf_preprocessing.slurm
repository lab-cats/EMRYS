#!/usr/bin/env bash
#SBATCH --job-name=norad-vcf-preprocess
#SBATCH --partition=long
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 08 cohort VCF preprocessing.
#
# Defaults run in dry-run mode. Set EXECUTE=1 only after the complete declared
# Step 07 receipt/VCF set has been inspected and the supported Rscript runtime
# and required Bioconductor packages are available.
set -euo pipefail

export TMPDIR="${TMPDIR:-/tmp}"

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

cd "${SLURM_SUBMIT_DIR:-$PWD}"

COHORT_ID="${COHORT_ID:-NORAD_EV_PUM1}"
SAMPLE_MANIFEST="${SAMPLE_MANIFEST:-samples.tsv}"
PARTITION_MANIFEST="${PARTITION_MANIFEST:-configs/step_07_partitions.primary_contigs.tsv}"
STEP07_ROOT="${STEP07_ROOT:-results/mpileup}"
ANNOTATION_GTF="${ANNOTATION_GTF:-refs/novogene_ref/genome.gtf}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/vcf_preprocessed}"
QC_ROOT="${QC_ROOT:-results/qc/vcf_preprocessing}"
RSCRIPT_BIN="${RSCRIPT_BIN_OVERRIDE:-Rscript}"
R_SCRIPT="${STEP08_R_SCRIPT:-scripts/step_08_vcf_preprocessing.R}"
EXECUTE="${EXECUTE:-0}"

case "$EXECUTE" in
    0|1) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

mkdir -p logs

COHORT_OUTPUT_DIR="$OUTPUT_ROOT/$COHORT_ID"
SITES_OUTPUT="$COHORT_OUTPUT_DIR/$COHORT_ID.step08_sites.tsv"
INPUTS_OUTPUT="$COHORT_OUTPUT_DIR/$COHORT_ID.step08_inputs.tsv"
SUMMARY_OUTPUT="$QC_ROOT/$COHORT_ID.step08_summary.tsv"

printf 'Job ID: %s\n' "${SLURM_JOB_ID:-none}"
printf 'Job name: %s\n' "${SLURM_JOB_NAME:-none}"
printf 'Node: %s\n' "$(hostname)"
printf 'Started: %s\n' "$(date)"
printf 'Working directory: %s\n' "$PWD"
printf 'TMPDIR: %s\n' "${TMPDIR:-unset}"
printf 'Cohort ID: %s\n' "$COHORT_ID"
printf 'Sample manifest: %s\n' "$SAMPLE_MANIFEST"
printf 'Partition manifest: %s\n' "$PARTITION_MANIFEST"
printf 'Step 07 root: %s\n' "$STEP07_ROOT"
printf 'Annotation GTF: %s\n' "$ANNOTATION_GTF"
printf 'Output root: %s\n' "$OUTPUT_ROOT"
printf 'QC root: %s\n' "$QC_ROOT"
printf 'Sites table: %s\n' "$SITES_OUTPUT"
printf 'Input receipt: %s\n' "$INPUTS_OUTPUT"
printf 'QC summary: %s\n' "$SUMMARY_OUTPUT"
printf 'Rscript: %s\n' "$RSCRIPT_BIN"
printf 'R script: %s\n' "$R_SCRIPT"
printf 'Execute mode: %s\n' "$EXECUTE"
printf 'Orientation policy: legacy_provisional_v1 (provisional; not biologically validated)\n'

printf 'Loaded modules before Step 08:\n'
module list 2>&1 || true

# R/Rscript module naming remains unresolved. Do not guess a module or install
# packages here; use an operator-validated executable through RSCRIPT_BIN_OVERRIDE.
if [[ "$RSCRIPT_BIN" == */* ]]; then
    if [[ -x "$RSCRIPT_BIN" ]]; then
        printf 'Rscript version:\n'
        "$RSCRIPT_BIN" --version 2>&1 || true
    else
        printf 'WARNING: Rscript path is not executable before script validation: %s\n' "$RSCRIPT_BIN"
    fi
elif command -v "$RSCRIPT_BIN" >/dev/null 2>&1; then
    printf 'Rscript version:\n'
    "$RSCRIPT_BIN" --version 2>&1 || true
else
    printf 'WARNING: Rscript command is not available before script validation: %s\n' "$RSCRIPT_BIN"
fi

cmd=(
    bash
    scripts/step_08_vcf_preprocessing.sh
    --cohort-id "$COHORT_ID"
    --sample-manifest "$SAMPLE_MANIFEST"
    --partition-manifest "$PARTITION_MANIFEST"
    --step07-root "$STEP07_ROOT"
    --annotation-gtf "$ANNOTATION_GTF"
    --output-root "$OUTPUT_ROOT"
    --qc-root "$QC_ROOT"
    --rscript-bin "$RSCRIPT_BIN"
    --r-script "$R_SCRIPT"
)
if [[ "$EXECUTE" == "1" ]]; then
    cmd+=(--execute)
fi

# The shell script owns exact input enumeration, R command construction,
# locking, validation, publication, cleanup, and rollback.
printf 'Wrapper command:\n'
print_command "${cmd[@]}"

"${cmd[@]}"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -s "$SITES_OUTPUT" ]] ||
        die "Expected Step 08 sites table does not exist or is empty: $SITES_OUTPUT"
    [[ -s "$INPUTS_OUTPUT" ]] ||
        die "Expected Step 08 input receipt does not exist or is empty: $INPUTS_OUTPUT"
    [[ -s "$SUMMARY_OUTPUT" ]] ||
        die "Expected Step 08 summary does not exist or is empty: $SUMMARY_OUTPUT"

    printf 'Validated Step 08 VCF preprocessing outputs:\n'
    ls -lh "$SITES_OUTPUT" "$INPUTS_OUTPUT" "$SUMMARY_OUTPUT"
else
    printf 'Step 08 completed in dry-run mode; output validation skipped because EXECUTE=0.\n'
fi

printf 'Finished: %s\n' "$(date)"
