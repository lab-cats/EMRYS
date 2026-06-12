#!/usr/bin/env bash
# Purpose: future Step 07 script for chromosome/strand-partitioned mpileup
# using orientation-specific BAMs.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It performs no analysis.
#
# Expected future inputs:
# - FWD/REV BAMs from Step 06
# - chromosome BED files
# - reference FASTA
#
# Expected future outputs:
# - per-chromosome, per-strand VCF files under an mpileup/results directory
#
# Likely tools:
# - bcftools mpileup
# - bcftools filter
#
# Reference workflow note:
# - This mirrors the uploaded/reference workflow's chromosome/strand-parallel
#   variant/editing candidate generation.
set -euo pipefail

echo "Step 07 bcftools mpileup partitioning is not implemented." >&2
echo "This script is scaffolding only and performs no work." >&2
exit 2
