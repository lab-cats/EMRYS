#!/usr/bin/env bash
# Purpose: future Step 05 script for running GATK SplitNCigarReads on RNA-seq
# BAMs after duplicate marking.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It performs no analysis.
#
# Expected future input:
# - results/bam/<sample_id>/<sample_id>.sorted.md.bam
#
# Expected future output:
# - results/bam/<sample_id>/<sample_id>.sorted.md.splitncigar.bam
#
# Likely tool:
# - GATK SplitNCigarReads
#
# Reference workflow note:
# - This mirrors the uploaded/reference workflow's RNA variant/editing-prep
#   stage, but will be parameterized for this repo.
set -euo pipefail

echo "Step 05 SplitNCigarReads is not implemented." >&2
echo "This script is scaffolding only and performs no work." >&2
exit 2
