#!/usr/bin/env bash
# Purpose: future Step 06 script for splitting processed BAMs into FWD/REV
# orientation-specific BAMs for strand-aware mpileup/editing analysis.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It performs no analysis.
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
set -euo pipefail

echo "Step 06 BAM orientation splitting is not implemented." >&2
echo "This script is scaffolding only and performs no work." >&2
exit 2
