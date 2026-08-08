#!/usr/bin/env bash
#SBATCH --job-name=norad-gtf-bed12
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# Convert the reference GTF to sorted BED12 for downstream strandness checks.
#
# Environment variables can override the input GTF, intermediate BED, final BED,
# and Python executable without editing this SLURM wrapper.
set -euo pipefail
script_dir="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../libraries/argument_parsing.sh"

# Run from the submitted repository checkout so relative paths are predictable.
cd "$SLURM_SUBMIT_DIR"

# Resolve configurable paths and keep defaults suitable for the prepared reference.
GTF="${GTF:-refs/novogene_ref/genome.gtf}"
UNSORTED_BED="${UNSORTED_BED:-refs/novogene_ref/genome.unsorted.bed}"
BED="${BED:-refs/novogene_ref/genome.bed}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

# Validate paths before running conversion or sorting.
if [[ "$UNSORTED_BED" == "$BED" ]]; then
    die "UNSORTED_BED and BED must be different paths."
fi

if [[ ! -f "$GTF" ]]; then
    die "GTF not found: $GTF"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    die "Python executable not found or not executable: $PYTHON_BIN"
fi

mkdir -p logs
mkdir -p "$(dirname "$UNSORTED_BED")" "$(dirname "$BED")"

# Print the resolved job context for reproducible cluster logs.
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

# bedtools is used only for the final BED sort after Python conversion.
module load bedtools/2.31.1

echo "Loaded modules after bedtools load:"
module list 2>&1 || true
echo

echo "Converting GTF to unsorted BED12..."
# Build the Python command as an array so paths stay quoted safely.
gtf_to_bed12_cmd=(
"$PYTHON_BIN"
src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py
--gtf "$GTF"
--bed "$UNSORTED_BED"
)

printf 'Command:'
print_command "${gtf_to_bed12_cmd[@]}"

"${gtf_to_bed12_cmd[@]}"

echo
echo "Sorting BED12..."
# Sort the BED12 records with bedtools before downstream tools consume them.
bedtools_sort_cmd=(
bedtools
sort
-i "$UNSORTED_BED"
)

printf 'Command:'
print_command "${bedtools_sort_cmd[@]}"
printf ' > %q\n' "$BED"

"${bedtools_sort_cmd[@]}" > "$BED"

echo
echo "Checking BED12 field count..."
# Confirm the sorted output still has the BED12 shape expected by RSeQC.
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

# Show a small preview in the SLURM log for quick sanity checks.
echo
echo "First BED records:"
head "$BED"

echo
echo "Finished GTF to BED12 reference prep."
