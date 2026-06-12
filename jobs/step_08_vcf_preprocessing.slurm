#!/usr/bin/env bash
# Purpose: future Step 08 SLURM wrapper for VCF preprocessing before
# downstream statistical editing-site calls.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
#
# Expected future input:
# - VCF files from Step 07
#
# Expected future outputs:
# - cleaned/annotated VCF-like TSV/table files suitable for CMH/editing-site
#   calling
#
# Likely tool:
# - R script based on/refactored from reference vcf_preprocess1.R
#
# Reference workflow note:
# - This step should remove hardcoded paths/sample groups and become
#   manifest/config driven.
#
# Future implementation should wrap:
# - scripts/step_08_vcf_preprocessing.sh
set -euo pipefail

echo "Step 08 VCF preprocessing is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
