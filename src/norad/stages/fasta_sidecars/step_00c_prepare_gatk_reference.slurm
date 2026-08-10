#!/usr/bin/env bash
#SBATCH --job-name=norad-gatk-ref
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# SLURM wrapper for Step 00c GATK reference sidecar preparation.
#
# Defaults run in dry-run mode. Set EXECUTE=1 explicitly after inspecting the
# dry-run log to create missing shared reference sidecars.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"

export TMPDIR="${TMPDIR:-/tmp}"

cd "${SLURM_SUBMIT_DIR:-$PWD}"

REFERENCE_FASTA="${REFERENCE_FASTA:-refs/novogene_ref/genome.fa}"
SAMTOOLS_BIN="${SAMTOOLS_BIN_OVERRIDE:-/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools}"
GATK_BIN="${GATK_BIN_OVERRIDE:-/cm/shared/apps/gatk/gatk-4.6.1.0/gatk}"
EXECUTE="${EXECUTE:-0}"
REFERENCE_DIR="$(dirname "$REFERENCE_FASTA")"
REFERENCE_BASE="$(basename "$REFERENCE_FASTA")"
REFERENCE_STEM="${REFERENCE_BASE%.*}"
DICT_PATH="${REFERENCE_DIR}/${REFERENCE_STEM}.dict"

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
echo "Reference FASTA: $REFERENCE_FASTA"
echo "FASTA index: $REFERENCE_FASTA.fai"
echo "Sequence dictionary: $DICT_PATH"
echo "samtools: $SAMTOOLS_BIN"
echo "GATK: $GATK_BIN"
echo "Execute mode: $EXECUTE"

echo "Loaded modules before reference-prep setup:"
module list 2>&1 || true

# Direct ADAM paths are passed to the script, but loading samtools keeps the
# module context visible in logs when the module system is available.
module load samtools/1.19.2 || true

echo "Loaded modules after reference-prep setup:"
module list 2>&1 || true

# CSU modules can expose stale runtime metadata; resolve and validate Java explicitly
# before handoff to the helper script.
validate_and_print_java "GATK reference prep" JAVA_BIN JAVA_VERSION_OUTPUT

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
    src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh
    --reference-fasta "$REFERENCE_FASTA"
    --samtools-bin "$SAMTOOLS_BIN"
    --gatk-bin "$GATK_BIN"
    --java-bin "$JAVA_BIN"
    "${execute_args[@]}"
)

# The script owns sidecar generation, validation, locking, and publication.
echo "Wrapper command:"
print_command "${cmd[@]}"

"${cmd[@]}"

if [[ "$EXECUTE" == "1" ]]; then
    [[ -s "$REFERENCE_FASTA.fai" ]] || die "Expected FASTA index does not exist or is empty: $REFERENCE_FASTA.fai"
    [[ -s "$DICT_PATH" ]] || die "Expected sequence dictionary does not exist or is empty: $DICT_PATH"

    echo "Validated Step 00c reference sidecars:"
    ls -lh "$REFERENCE_FASTA.fai" "$DICT_PATH"
else
    echo "Step 00c completed in dry-run mode; output validation skipped because EXECUTE=0."
fi

echo "Finished: $(date)"
