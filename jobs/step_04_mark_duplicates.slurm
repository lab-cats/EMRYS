#!/usr/bin/env bash
# Purpose: future Step 04 SLURM wrapper for marking PCR/optical duplicates on
# canonical sorted BAMs before variant/editing-style processing.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
#
# Expected future input:
# - results/bam/<sample_id>/<sample_id>.sorted.bam
#
# Expected future outputs:
# - results/bam/<sample_id>/<sample_id>.sorted.md.bam
# - results/qc/picard/<sample_id>.markduplicates.txt
#
# Likely tool:
# - Picard MarkDuplicates
#
# Reference workflow note:
# - This aligns with the uploaded/reference RNA-editing workflow's duplicate
#   marking stage, but will be rebuilt as a clean wrapper/script pair here.
#
# Future implementation should wrap:
# - scripts/step_04_mark_duplicates.sh
set -euo pipefail

echo "Step 04 duplicate marking is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
