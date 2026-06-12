#!/usr/bin/env bash
# Purpose: future Step 05 SLURM wrapper for GATK SplitNCigarReads on RNA-seq
# BAMs after duplicate marking.
#
# Status: intentionally pending / not implemented.
# Warning: this file is scaffolding only. It is not ready to submit.
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
#
# Future implementation should wrap:
# - scripts/step_05_split_n_cigar_reads.sh
set -euo pipefail

echo "Step 05 SplitNCigarReads is not implemented." >&2
echo "This SLURM file is scaffolding only and should not be submitted yet." >&2
exit 2
