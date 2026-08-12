#!/usr/bin/env bash
#SBATCH --job-name=norad-build-star-index
#SBATCH --partition=long
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=8
#SBATCH --export=ALL,TMPDIR=/tmp

# Build the Novogene STAR genome index on a compute node.
#
# Inputs are the compressed reference FASTA/GTF under data/raw; outputs are the
# uncompressed working reference and STAR index under refs/.
set -euo pipefail
script_dir="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
producer="$script_dir/step_00a_build_star_index.sh"

# Print cluster context early so SLURM logs show where the job ran.
echo "Job ID: ${SLURM_JOB_ID:-NA}"
echo "Node: ${SLURMD_NODENAME:-NA}"
echo "Working dir: $(pwd)"
echo "TMPDIR: ${TMPDIR:-NA}"

module load star/2.7.11b
module list 2>&1

# Keep reference and index paths together for easier cluster handoff.
REF_DIR="data/raw/novogene_remora/04.Ref"
WORK_REF="refs/novogene_ref"
STAR_INDEX="refs/novogene_star_index"
THREADS="${SLURM_CPUS_PER_TASK:-8}"

SJDB_OVERHANG=149

# Materialize the legacy wrapper-owned references before invoking the explicit
# scheduler-independent STAR-index producer.
mkdir -p "$WORK_REF"

echo "Preparing uncompressed reference files..."

# Reuse already-prepared reference files so reruns do not decompress needlessly.
if [[ ! -s "$WORK_REF/genome.fa" ]]; then
  gunzip -c "$REF_DIR/genome.fa.gz" > "$WORK_REF/genome.fa"
fi

if [[ ! -s "$WORK_REF/genome.gtf" ]]; then
  gunzip -c "$REF_DIR/genome.gtf.gz" > "$WORK_REF/genome.gtf"
fi

echo "Building STAR index..."
echo "Reference FASTA: $WORK_REF/genome.fa"
echo "Reference GTF:   $WORK_REF/genome.gtf"
echo "STAR index dir:  $STAR_INDEX"
echo "Threads:         $THREADS"
echo "sjdbOverhang:    $SJDB_OVERHANG"

# The public producer owns dry-run/execute, complete-member validation, locking,
# no-clobber publication, and controlled-failure cleanup.
producer_command=(
  bash "$producer"
  --reference-fasta "$WORK_REF/genome.fa"
  --reference-gtf "$WORK_REF/genome.gtf"
  --index-dir "$STAR_INDEX"
  --threads "$THREADS"
  --sjdb-overhang "$SJDB_OVERHANG"
  --star-bin STAR
  --execute
)

printf 'Producer command:'
printf ' %q' "${producer_command[@]}"
printf '\n'
"${producer_command[@]}"

echo "STAR index build complete."
ls -lah "$STAR_INDEX"
