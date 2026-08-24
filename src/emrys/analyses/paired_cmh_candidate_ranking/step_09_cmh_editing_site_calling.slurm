#!/usr/bin/env bash
#SBATCH --job-name=emrys-cmh
#SBATCH --partition=long
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 09 paired CMH editing-site calling. R module/package
# installation is intentionally outside this job; provide an operator-validated
# Rscript through RSCRIPT_BIN_OVERRIDE.
set -euo pipefail

# Run from the submitted repository checkout rather than SLURM's spool copy.
: "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
cd "$SLURM_SUBMIT_DIR"

export TMPDIR="${TMPDIR:-/tmp}"
# shellcheck source=../../libraries/argument_parsing.sh
source "src/emrys/libraries/argument_parsing.sh"

# These frozen defaults are scientific cohort identities, not project branding.
ANALYSIS_ID="${ANALYSIS_ID:-NORAD_EV_vs_PUM1}"
COHORT_ID="${COHORT_ID:-NORAD_EV_PUM1}"
SAMPLE_MANIFEST="${SAMPLE_MANIFEST:-samples.tsv}"
PARTITION_MANIFEST="${PARTITION_MANIFEST:-configs/step_07_partitions.primary_contigs.tsv}"
STEP08_ROOT="${STEP08_ROOT:-results/vcf_preprocessed}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/editing}"
CONTROL_CONDITION="${CONTROL_CONDITION:-EV}"
TREATMENT_CONDITION="${TREATMENT_CONDITION:-PUM1}"
RNA_REF="${RNA_REF:-A}"
RNA_ALT="${RNA_ALT:-G}"
MIN_SAMPLE_DP="${MIN_SAMPLE_DP:-1}"
MEAN_DP_THRESHOLD="${MEAN_DP_THRESHOLD:-50}"
FDR_THRESHOLD="${FDR_THRESHOLD:-0.05}"
COMMON_OR_THRESHOLD="${COMMON_OR_THRESHOLD:-1.2}"
ABSOLUTE_DIFFERENCE_THRESHOLD="${ABSOLUTE_DIFFERENCE_THRESHOLD:-0.005}"
BACKGROUND_CONDITION="${BACKGROUND_CONDITION:-}"
BACKGROUND_MAX_FRACTION="${BACKGROUND_MAX_FRACTION:-0.01}"
RSCRIPT_BIN="${RSCRIPT_BIN_OVERRIDE:-Rscript}"
R_SCRIPT="${STEP09_R_SCRIPT:-src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R}"
EXECUTE="${EXECUTE:-0}"

case "$EXECUTE" in
    0|1) ;;
    *) die "EXECUTE must be 0 or 1; got: $EXECUTE" ;;
esac

mkdir -p logs
analysis_dir="$OUTPUT_ROOT/$ANALYSIS_ID"
outputs=(
    "$analysis_dir/$ANALYSIS_ID.cmh_all_sites.tsv"
    "$analysis_dir/$ANALYSIS_ID.cmh_significant_sites.tsv"
    "$analysis_dir/$ANALYSIS_ID.cmh_summary.tsv"
    "$analysis_dir/$ANALYSIS_ID.mutation_spectrum.tsv"
    "$analysis_dir/$ANALYSIS_ID.mutation_spectrum.pdf"
    "$analysis_dir/$ANALYSIS_ID.depth_delta.pdf"
)

printf 'Job ID: %s\n' "${SLURM_JOB_ID:-none}"
printf 'Job name: %s\n' "${SLURM_JOB_NAME:-none}"
printf 'Node: %s\n' "$(hostname)"
printf 'Started: %s\n' "$(date)"
printf 'Working directory: %s\n' "$PWD"
printf 'TMPDIR: %s\n' "$TMPDIR"
printf 'Analysis / cohort: %s / %s\n' "$ANALYSIS_ID" "$COHORT_ID"
printf 'Sample manifest: %s\n' "$SAMPLE_MANIFEST"
printf 'Partition manifest: %s\n' "$PARTITION_MANIFEST"
printf 'Step 08 root: %s\n' "$STEP08_ROOT"
printf 'Output root: %s\n' "$OUTPUT_ROOT"
printf 'Control / treatment: %s / %s\n' "$CONTROL_CONDITION" "$TREATMENT_CONDITION"
printf 'RNA change: %s>%s\n' "$RNA_REF" "$RNA_ALT"
printf 'Background: %s\n' "${BACKGROUND_CONDITION:-disabled}"
printf 'Rscript / R implementation: %s / %s\n' "$RSCRIPT_BIN" "$R_SCRIPT"
printf 'Execute mode: %s\n' "$EXECUTE"
printf 'Loaded modules before Step 09:\n'
module list 2>&1 || true

cmd=(
    bash src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.sh
    --analysis-id "$ANALYSIS_ID"
    --cohort-id "$COHORT_ID"
    --sample-manifest "$SAMPLE_MANIFEST"
    --partition-manifest "$PARTITION_MANIFEST"
    --step08-root "$STEP08_ROOT"
    --output-root "$OUTPUT_ROOT"
    --control-condition "$CONTROL_CONDITION"
    --treatment-condition "$TREATMENT_CONDITION"
    --rna-ref "$RNA_REF"
    --rna-alt "$RNA_ALT"
    --min-sample-dp "$MIN_SAMPLE_DP"
    --mean-dp-threshold "$MEAN_DP_THRESHOLD"
    --fdr-threshold "$FDR_THRESHOLD"
    --common-or-threshold "$COMMON_OR_THRESHOLD"
    --absolute-difference-threshold "$ABSOLUTE_DIFFERENCE_THRESHOLD"
    --background-max-fraction "$BACKGROUND_MAX_FRACTION"
    --rscript-bin "$RSCRIPT_BIN"
    --r-script "$R_SCRIPT"
)
[[ -n "$BACKGROUND_CONDITION" ]] && cmd+=(--background-condition "$BACKGROUND_CONDITION")
[[ "$EXECUTE" == "1" ]] && cmd+=(--execute)

printf 'Wrapper command:\n'
print_command "${cmd[@]}"
"${cmd[@]}"

if [[ "$EXECUTE" == "1" ]]; then
    for output in "${outputs[@]}"; do
        [[ -s "$output" ]] || die "Expected Step 09 output does not exist or is empty: $output"
    done
    printf 'Validated Step 09 output paths:\n'
    ls -lh "${outputs[@]}"
else
    printf 'Step 09 completed in dry-run mode; execute output validation skipped.\n'
fi
printf 'Finished: %s\n' "$(date)"
