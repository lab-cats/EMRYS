#!/usr/bin/env bash
#SBATCH --job-name=norad-infer-strandedness
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 03 RSeQC strandedness/orientation inference.
#
# This file keeps cluster-specific defaults and environment setup outside the
# analysis script. Defaults run in dry-run mode; set EXECUTE=1 explicitly for
# real execution after Step 02 has produced the canonical BAM and index.
set -euo pipefail

# CSU compute nodes can have an unwritable default local tmp path. Pin TMPDIR to
# /tmp unless the submit command intentionally overrides it.
export TMPDIR="${TMPDIR:-/tmp}"

die() {
    echo "ERROR: $*" >&2
    exit 1
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

# Resolve repo-relative defaults from the directory where sbatch was submitted.
# The fallback keeps local syntax checks and wrapper smoke tests simple.
cd "${SLURM_SUBMIT_DIR:-$PWD}"

# First cluster validation targets one known Step 02 output. These can be
# overridden with sbatch --export without editing this tracked wrapper.
SAMPLE_ID="${SAMPLE_ID:-ABE_EV_2}"
BAM="${BAM:-results/bam/${SAMPLE_ID}/${SAMPLE_ID}.sorted.bam}"
BED12="${BED12:-refs/novogene_ref/genome.bed}"
OUTPUT_DIR="${OUTPUT_DIR:-results/qc/strandedness}"
EXECUTE="${EXECUTE:-0}"

# Prefer the project virtualenv copy of RSeQC when present. If the virtualenv is
# absent, defer to PATH so the same wrapper can work with a module-provided or
# otherwise installed infer_experiment.py.
if [[ -e ".venv/bin/infer_experiment.py" ]]; then
    INFER_EXPERIMENT_BIN="${INFER_EXPERIMENT_BIN:-.venv/bin/infer_experiment.py}"
else
    INFER_EXPERIMENT_BIN="${INFER_EXPERIMENT_BIN:-infer_experiment.py}"
fi

case "$EXECUTE" in
    0) execute_args=() ;;
    1) execute_args=(--execute) ;;
    *)
        die "EXECUTE must be 0 or 1; got: $EXECUTE"
        ;;
esac

# SLURM needs the log directory before it can open stdout/stderr files. The
# Step 03 output directory is still left to the script and is only made during
# execute mode.
mkdir -p logs

if [[ -f ".venv/bin/activate" ]]; then
    # Prefer the project virtual environment when available on the cluster.
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"
echo "Sample ID: $SAMPLE_ID"
echo "BAM: $BAM"
echo "BED12 annotation: $BED12"
echo "Output directory: $OUTPUT_DIR"
echo "infer_experiment.py: $INFER_EXPERIMENT_BIN"
echo "Execute mode: $EXECUTE"
echo "PATH: $PATH"
echo "Python: $(command -v python || true)"
echo "infer_experiment.py on PATH: $(command -v infer_experiment.py || true)"

# RSeQC is expected from the project virtualenv for this step, but recording the
# module state is still useful when debugging cluster environments.
echo "Loaded modules:"
module list 2>&1 || true

# Build the script command as an array so paths with spaces remain safe and the
# printed wrapper command is copy-pasteable from logs.
cmd=(
    bash
    scripts/step_03_infer_strandedness_and_orientation.sh
    --sample-id "$SAMPLE_ID"
    --input-bam "$BAM"
    --bed12 "$BED12"
    --output-dir "$OUTPUT_DIR"
    --infer-experiment-bin "$INFER_EXPERIMENT_BIN"
    "${execute_args[@]}"
)

echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

OUTPUT_FILE="$OUTPUT_DIR/${SAMPLE_ID}.infer_experiment.txt"

if [[ "$EXECUTE" == "1" ]]; then
    # The script validates this too; the wrapper check makes the cluster log end
    # with an obvious success/failure signal for the submitted job.
    [[ -s "$OUTPUT_FILE" ]] || die "Expected infer_experiment output does not exist or is empty: $OUTPUT_FILE"

    echo "Validated Step 03 strandedness output:"
    ls -lh "$OUTPUT_FILE"
else
    echo "Step 03 completed in dry-run mode; output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
