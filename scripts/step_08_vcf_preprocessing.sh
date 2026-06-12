#!/usr/bin/env bash
# Purpose: future Step 08 script for VCF preprocessing before downstream
# statistical editing-site calls.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It performs no analysis.
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
set -euo pipefail

echo "Step 08 VCF preprocessing is not implemented." >&2
echo "This script is scaffolding only and performs no work." >&2
exit 2
