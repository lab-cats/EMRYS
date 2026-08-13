#!/usr/bin/env bash
#SBATCH --job-name=norad-validate
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?submit from the NORAD repo root}"

module load python314
source .venv/bin/activate
export TMPDIR=/tmp

STEP="${1:-}"
EXECUTE="${EXECUTE:-0}"

case "$EXECUTE" in
  0) execute_args=() ;;
  1) execute_args=(--execute) ;;
  *)
    echo "ERROR: EXECUTE must be 0 or 1" >&2
    exit 2
    ;;
esac

case "$STEP" in
    00a)
        mkdir -p results/qc/validation/00a

        cmd=(
        norad validate star-index
        --scope-id novogene_ref
        --index-dir refs/novogene_star_index
        --reference-fasta refs/novogene_ref/genome.fa
        --reference-gtf refs/novogene_ref/genome.gtf
        --parameter-path-base .
        --expected-sjdb-overhang 149
        --output results/qc/validation/00a/novogene_ref.validation.tsv
        "${execute_args[@]}"
        )
        ;;

    00b)
        mkdir -p results/qc/validation/00b

        cmd=(
        norad validate bed12
        --scope-id novogene_ref
        --bed12 refs/novogene_ref/genome.bed
        --source-gtf refs/novogene_ref/genome.gtf
        --output results/qc/validation/00b/novogene_ref.validation.tsv
        "${execute_args[@]}"
        )
        ;;
    00c)
        mkdir -p results/qc/validation/00c
        cmd=(
            norad validate fasta-sidecars
            --scope-id novogene_ref
            --reference-fasta refs/novogene_ref/genome.fa
            --reference-fai refs/novogene_ref/genome.fa.fai
            --reference-dict refs/novogene_ref/genome.dict
            --output results/qc/validation/00c/novogene_ref.validation.tsv
            "${execute_args[@]}"
        )
            ;;
    01)
        scope_id="${2:-}"
        [[ -n "$scope_id" ]] || {
            echo "ERROR: Step 01 requires a sample ID as the second argument." >&2
            exit 2
        }

        mkdir -p results/qc/validation/01
        cmd=(
            norad validate star-alignment
            --scope-id "$scope_id"
            --bam "results/star/$scope_id/$scope_id.Aligned.sortedByCoord.out.bam"
            --log-final "results/star/$scope_id/$scope_id.Log.final.out"
            --log-out "results/star/$scope_id/$scope_id.Log.out"
            --log-progress "results/star/$scope_id/$scope_id.Log.progress.out"
            --sj-out "results/star/$scope_id/$scope_id.SJ.out.tab"
            --output "results/qc/validation/01/$scope_id.validation.tsv"
            "${execute_args[@]}"
        )
    ;;
    *)
        echo "ERROR: unsupported validation step: $STEP" >&2
        exit 2
        ;;
esac

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Node: $(hostname)"
echo "Step: $STEP"
echo "Execute: $EXECUTE"
printf 'Command:'
printf ' %q' "${cmd[@]}"
printf '\n'

"${cmd[@]}"