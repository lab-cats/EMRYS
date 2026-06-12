#!/usr/bin/env bash
#SBATCH --job-name=norad-gtf-bed12
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"

GTF="${GTF:-refs/novogene_ref/genome.gtf}"
UNSORTED_BED="${UNSORTED_BED:-refs/novogene_ref/genome.unsorted.bed}"
BED="${BED:-refs/novogene_ref/genome.bed}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

if [[ "$UNSORTED_BED" == "$BED" ]]; then
echo "ERROR: UNSORTED_BED and BED must be different paths." >&2
exit 1
fi

if [[ ! -f "$GTF" ]]; then
echo "ERROR: GTF not found: $GTF" >&2
exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
echo "ERROR: Python executable not found or not executable: $PYTHON_BIN" >&2
exit 1
fi

mkdir -p logs
mkdir -p "$(dirname "$UNSORTED_BED")" "$(dirname "$BED")"

echo "GTF to BED12 reference prep"
echo "  Job ID:          ${SLURM_JOB_ID:-unknown}"
echo "  Job name:        ${SLURM_JOB_NAME:-unknown}"
echo "  Node:            ${SLURMD_NODENAME:-unknown}"
echo "  Working dir:     $(pwd)"
echo "  TMPDIR:          ${TMPDIR:-unset}"
echo "  GTF:             $GTF"
echo "  Unsorted BED:    $UNSORTED_BED"
echo "  Sorted BED:      $BED"
echo "  Python:          $PYTHON_BIN"
echo

echo "Loaded modules before bedtools load:"
module list 2>&1 || true
echo

module load bedtools/2.31.1

echo "Loaded modules after bedtools load:"
module list 2>&1 || true
echo

echo "Converting GTF to unsorted BED12..."
gtf_to_bed12_cmd=(
"$PYTHON_BIN"
scripts/gtf_to_bed12.py
--gtf "$GTF"
--bed "$UNSORTED_BED"
)

printf 'Command:'
printf ' %q' "${gtf_to_bed12_cmd[@]}"
printf '\n'

"${gtf_to_bed12_cmd[@]}"

echo
echo "Sorting BED12..."
bedtools_sort_cmd=(
bedtools
sort
-i "$UNSORTED_BED"
)

printf 'Command:'
printf ' %q' "${bedtools_sort_cmd[@]}"
printf ' > %q\n' "$BED"

"${bedtools_sort_cmd[@]}" > "$BED"

echo
echo "Checking BED12 field count..."
awk '
NF != 12 {
print "ERROR: bad BED12 field count at line " NR ": expected 12 fields, saw " NF
exit 1
}
END {
print "BED12 field-count check passed"
}
' "$BED"

echo
echo "Output summary:"
wc -l "$BED"
ls -lh "$UNSORTED_BED" "$BED"

echo
echo "First BED records:"
head "$BED"

echo
echo "Finished GTF to BED12 reference prep."