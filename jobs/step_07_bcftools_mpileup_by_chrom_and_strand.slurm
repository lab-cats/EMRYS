#!/usr/bin/env bash
# Purpose: future Step 07 SLURM wrapper for chromosome/strand-partitioned
# mpileup using orientation-specific BAMs.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
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
#
# Future implementation should wrap:
# - scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
set -euo pipefail

echo "Step 07 bcftools mpileup partitioning is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
