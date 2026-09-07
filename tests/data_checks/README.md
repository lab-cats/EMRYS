# Operator data checks

`validate_step05_outputs.sh` is a retained operator check for existing Step 05
BAM/BAI outputs. It may query Slurm, runs structural `samtools` checks, writes
the selected status TSV, and performs a temporary output-directory write probe;
it does not mutate the BAM/BAI pair. Its defaults are site-specific, and its
result is not a portable stage, production, scientific, or biological claim.
