#!/usr/bin/env bash
#SBATCH --job-name=emrys-gtf-bed12
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# Convert the reference GTF to deterministically sorted BED12 for downstream
# strandedness checks.
#
# Environment variables can override the input GTF, final BED, and Python
# executable without editing this SLURM wrapper.
set -euo pipefail

# Run from the submitted repository checkout so relative paths are predictable.
: "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
cd "$SLURM_SUBMIT_DIR"

# Resolve repository-owned helpers from the submitted checkout rather than the
# SLURM spool copy of this script.
source "src/emrys/libraries/argument_parsing.sh"

# Resolve configurable paths and keep defaults suitable for the prepared reference.
GTF="${GTF:-refs/novogene_ref/genome.gtf}"
BED="${BED:-refs/novogene_ref/genome.bed}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

if [[ ! -f "$GTF" ]]; then
    die "GTF not found: $GTF"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    die "Python executable not found or not executable: $PYTHON_BIN"
fi

RUN_TOKEN="${EMRYS_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
case "$RUN_TOKEN" in
    [!A-Za-z0-9]* | *[!A-Za-z0-9._-]*)
        die "Unsafe Step 00b publication token: $RUN_TOKEN"
        ;;
esac

mkdir -p logs
mkdir -p "$(dirname "$BED")"

# Print the resolved job context for reproducible cluster logs.
echo "GTF to BED12 reference prep"
echo "  Job ID:      ${SLURM_JOB_ID:-unknown}"
echo "  Job name:    ${SLURM_JOB_NAME:-unknown}"
echo "  Node:        ${SLURMD_NODENAME:-unknown}"
echo "  Working dir: $(pwd)"
echo "  TMPDIR:      ${TMPDIR:-unset}"
echo "  GTF:         $GTF"
echo "  BED:         $BED"
echo "  Python:      $PYTHON_BIN"
echo "  Run token:   $RUN_TOKEN"
echo

echo "Loaded modules:"
module list 2>&1 || true
echo

echo "Converting GTF to deterministic BED12..."
# Build the Python command as an array so paths stay quoted safely.
cmd=(
    "$PYTHON_BIN"
    -I
    -m
    emrys
    convert
    gtf-to-bed12
    --gtf "$GTF"
    --bed "$BED"
    --run-token "$RUN_TOKEN"
    --execute
)

printf 'Command:'
print_command "${cmd[@]}"
"${cmd[@]}"

echo
echo "Checking BED12 field count..."
# Confirm the deterministic BED12 output has the shape expected by RSeQC.
awk '
NF != 12 {
    print "ERROR: bad BED12 field count at line " NR \
          ": expected 12 fields, saw " NF > "/dev/stderr"
    exit 1
}
END {
    if (NR == 0) {
        print "ERROR: BED12 output is empty" > "/dev/stderr"
        exit 1
    }
}
' "$BED"

echo "BED12 field-count check passed"

echo
echo "Output summary:"
wc -l "$BED"
ls -lh "$BED"

# Show a small preview in the SLURM log for quick sanity checks.
echo
echo "First BED records:"
head "$BED"

echo
echo "Finished GTF to BED12 reference prep."
