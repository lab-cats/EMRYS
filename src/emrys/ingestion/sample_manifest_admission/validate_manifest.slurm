#!/bin/bash
#SBATCH --job-name=emrys-validate-manifest
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --export=ALL,TMPDIR=/tmp

# SLURM smoke check for the sample manifest validator.
#
# This validates the example manifest from the repository checkout and keeps the
# job lightweight enough for login-node-style debugging through SLURM.
set -euo pipefail

# Resolve the submitted checkout before selecting its explicitly installed Python.
cd "${SLURM_SUBMIT_DIR:-$PWD}"
python_bin="${EMRYS_PYTHON_BIN:-$PWD/.venv/bin/python}"
if [[ ! -x "$python_bin" ]]; then
  printf 'ERROR: EMRYS Python is not executable: %s\n' "$python_bin" >&2
  exit 2
fi

echo "Job ID: ${SLURM_JOB_ID:-none}"
echo "Job name: ${SLURM_JOB_NAME:-none}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "Working directory: $PWD"
echo "TMPDIR: ${TMPDIR:-unset}"

"$python_bin" --version

# Isolated mode prevents an ambient PYTHONPATH from replacing the selected package.
"$python_bin" -I -m emrys validate manifest \
  --manifest configs/samples.example.tsv \
  --base-dir .

echo "Finished: $(date)"
