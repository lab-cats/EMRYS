#!/usr/bin/env bash
#SBATCH --job-name=norad-scientific-context
#SBATCH --partition=long
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# Owner-local scheduler entry point for the post-Step09 scientific-context
# projection. Defaults to a no-write preflight; set EXECUTE=1 explicitly.
set -euo pipefail

: "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
cd "$SLURM_SUBMIT_DIR"

source "src/norad/libraries/argument_parsing.sh"

: "${ANALYSIS_ID:?ANALYSIS_ID is required}"
: "${STEP09_ALL_SITES:?STEP09_ALL_SITES is required}"
: "${STEP09_SIGNIFICANT_SITES:?STEP09_SIGNIFICANT_SITES is required}"
: "${STEP09_SUMMARY:?STEP09_SUMMARY is required}"
: "${REFERENCE_FASTA:?REFERENCE_FASTA is required}"
: "${REFERENCE_FAI:?REFERENCE_FAI is required}"
: "${OUTPUT_ROOT:?OUTPUT_ROOT is required}"
: "${RSCRIPT_BIN_OVERRIDE:?RSCRIPT_BIN_OVERRIDE is required}"

EXECUTE="${EXECUTE:-0}"
case "$EXECUTE" in
    0|1) ;;
    *) die "EXECUTE must be 0 or 1; got: $EXECUTE" ;;
esac

R_SCRIPT="${SCIENTIFIC_CONTEXT_R_SCRIPT:-src/norad/analyses/scientific_context_projection/scientific_context_projection.R}"
MOTIF_CATALOG="${MOTIF_CATALOG:-src/norad/analyses/scientific_context_projection/resources/pum_motifs_v1.tsv}"
analysis_dir="$OUTPUT_ROOT/$ANALYSIS_ID"
outputs=(
    "$analysis_dir/$ANALYSIS_ID.candidate_context.tsv"
    "$analysis_dir/$ANALYSIS_ID.motif_hits.tsv"
    "$analysis_dir/$ANALYSIS_ID.sequence_logo.tsv"
    "$analysis_dir/$ANALYSIS_ID.motif_statistics.tsv"
    "$analysis_dir/$ANALYSIS_ID.context_receipt.tsv"
)

mkdir -p logs
printf 'Job ID: %s\n' "${SLURM_JOB_ID:-none}"
printf 'Job name: %s\n' "${SLURM_JOB_NAME:-none}"
printf 'Node: %s\n' "$(hostname)"
printf 'Started: %s\n' "$(date)"
printf 'Working directory: %s\n' "$PWD"
printf 'TMPDIR: %s\n' "${TMPDIR:-unset}"
printf 'Analysis ID: %s\n' "$ANALYSIS_ID"
printf 'Step 09 all-sites: %s\n' "$STEP09_ALL_SITES"
printf 'Step 09 significant-sites: %s\n' "$STEP09_SIGNIFICANT_SITES"
printf 'Step 09 summary: %s\n' "$STEP09_SUMMARY"
printf 'Reference FASTA / FAI: %s / %s\n' "$REFERENCE_FASTA" "$REFERENCE_FAI"
printf 'Motif catalog: %s\n' "$MOTIF_CATALOG"
printf 'Output root: %s\n' "$OUTPUT_ROOT"
printf 'Rscript: %s\n' "$RSCRIPT_BIN_OVERRIDE"
printf 'R program: %s\n' "$R_SCRIPT"
printf 'Execute mode: %s\n' "$EXECUTE"
printf 'Sequence policy: legacy_rna_change_oriented_genomic_v1 (mechanical; provisional)\n'

printf 'Loaded modules before scientific-context projection:\n'
module list 2>&1 || true
if [[ "$RSCRIPT_BIN_OVERRIDE" == */* && -x "$RSCRIPT_BIN_OVERRIDE" ]] ||
   command -v "$RSCRIPT_BIN_OVERRIDE" >/dev/null 2>&1; then
    printf 'Rscript version:\n'
    "$RSCRIPT_BIN_OVERRIDE" --version 2>&1 || true
else
    printf 'WARNING: Rscript is not available before owner validation: %s\n' \
        "$RSCRIPT_BIN_OVERRIDE"
fi

cmd=(
    bash
    src/norad/analyses/scientific_context_projection/scientific_context_projection.sh
    --analysis-id "$ANALYSIS_ID"
    --step09-all-sites "$STEP09_ALL_SITES"
    --step09-significant-sites "$STEP09_SIGNIFICANT_SITES"
    --step09-summary "$STEP09_SUMMARY"
    --reference-fasta "$REFERENCE_FASTA"
    --reference-fai "$REFERENCE_FAI"
    --output-root "$OUTPUT_ROOT"
    --motif-catalog "$MOTIF_CATALOG"
    --rscript-bin "$RSCRIPT_BIN_OVERRIDE"
    --r-script "$R_SCRIPT"
    --no-clobber
)
if [[ "$EXECUTE" == 1 ]]; then
    cmd+=(--execute)
fi
printf 'Wrapper command:\n'
print_command "${cmd[@]}"
"${cmd[@]}"

if [[ "$EXECUTE" == 1 ]]; then
    for output in "${outputs[@]}"; do
        [[ -s "$output" ]] || die "Expected scientific-context output is missing: $output"
    done
    printf 'Published scientific-context output paths:\n'
    printf '  %s\n' "${outputs[@]}"
else
    printf 'Scientific-context projection completed in dry-run mode; output validation skipped.\n'
fi
printf 'Finished: %s\n' "$(date)"
