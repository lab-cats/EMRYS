#!/usr/bin/env bash
#SBATCH --job-name=norad-build-star-index
#SBATCH --partition=long
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=8
#SBATCH --export=ALL,TMPDIR=/tmp

set -euo pipefail

echo "Job ID: ${SLURM_JOB_ID:-NA}"
echo "Node: ${SLURMD_NODENAME:-NA}"
echo "Working dir: $(pwd)"
echo "TMPDIR: ${TMPDIR:-NA}"

module load star/2.7.11b
module list 2>&1

REF_DIR="data/raw/novogene_remora/04.Ref"
WORK_REF="refs/novogene_ref"
STAR_INDEX="refs/novogene_star_index"
THREADS="${SLURM_CPUS_PER_TASK:-8}"

SJDB_OVERHANG=149

mkdir -p "$WORK_REF" "$STAR_INDEX"

echo "Preparing uncompressed reference files..."

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

STAR \
  --runThreadN "$THREADS" \
  --runMode genomeGenerate \
  --genomeDir "$STAR_INDEX" \
  --genomeFastaFiles "$WORK_REF/genome.fa" \
  --sjdbGTFfile "$WORK_REF/genome.gtf" \
  --sjdbOverhang "$SJDB_OVERHANG"

echo "STAR index build complete."
ls -lah "$STAR_INDEX"
