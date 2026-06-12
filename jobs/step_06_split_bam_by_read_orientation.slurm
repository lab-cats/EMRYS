#!/usr/bin/env bash
# Purpose: future Step 06 SLURM wrapper for splitting processed BAMs into
# FWD/REV orientation-specific BAMs for strand-aware mpileup/editing analysis.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
#
# Expected future input:
# - results/bam/<sample_id>/<sample_id>.sorted.md.splitncigar.bam
#
# Expected future outputs:
# - results/bam/<sample_id>/<sample_id>.sorted.md.splitncigar.FWD.bam
# - results/bam/<sample_id>/<sample_id>.sorted.md.splitncigar.REV.bam
#
# Likely tools:
# - samtools view
# - samtools merge
# - samtools index
#
# Reference workflow note:
# - The uploaded/reference workflow used SAM flag combinations 99/147 and
#   83/163 to create FWD/REV BAMs.
#
# Future implementation should wrap:
# - scripts/step_06_split_bam_by_read_orientation.sh
set -euo pipefail

echo "Step 06 BAM orientation splitting is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
