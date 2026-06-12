#!/usr/bin/env bash
# Purpose: future Step 03 script for inferring library strandedness and read
# orientation before strand-sensitive downstream analysis.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It performs no analysis.
#
# Expected future inputs:
# - results/bam/<sample_id>/<sample_id>.sorted.bam
# - refs/novogene_ref/genome.bed
#
# Expected future output:
# - results/qc/strandedness/<sample_id>.infer_experiment.txt
#
# Likely tool:
# - infer_experiment.py from RSeQC
#
# Reference workflow note:
# - This informs whether later strand/orientation handling should treat reads
#   as forward, reverse, or unstranded.
set -euo pipefail

echo "Step 03 strandedness/orientation inference is not implemented." >&2
echo "This script is scaffolding only and performs no work." >&2
exit 2
