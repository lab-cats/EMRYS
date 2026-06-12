#!/usr/bin/env bash
# Purpose: future Step 03 SLURM wrapper for inferring library strandedness and
# read orientation before strand-sensitive downstream analysis.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
#
# Expected future inputs:
# - results/bam/<sample_id>/<sample_id>.sorted.bam
# - refs/novogene_ref/genome.bed
#
# Expected future outputs:
# - results/qc/strandedness/<sample_id>.infer_experiment.txt
#
# Likely tool:
# - infer_experiment.py from RSeQC
#
# Reference workflow note:
# - This step records whether later strand/orientation handling should treat
#   reads as forward, reverse, or unstranded.
#
# Future implementation should wrap:
# - scripts/step_03_infer_strandedness_and_orientation.sh
set -euo pipefail

echo "Step 03 strandedness/orientation inference is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
