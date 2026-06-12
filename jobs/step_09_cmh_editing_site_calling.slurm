#!/usr/bin/env bash
# Purpose: future Step 09 SLURM wrapper for CMH editing-site statistical
# testing, correction, and summary outputs.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
#
# Expected future input:
# - preprocessed VCF/table outputs from Step 08
#
# Expected future outputs:
# - CMH/editing-site result tables and plots
#
# Likely tool:
# - R script based on/refactored from reference Edit_call_cmh.R
#
# Reference workflow note:
# - This should become parameterized rather than hardcoded to old experiment
#   names.
#
# Future implementation should wrap:
# - scripts/step_09_cmh_editing_site_calling.sh
set -euo pipefail

echo "Step 09 CMH editing-site calling is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
