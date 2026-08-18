# Operator data checks

This directory owns retained operator-facing checks over existing workflow
outputs. `validate_step05_outputs.sh` optionally reads Slurm state and checks
Step `05` BAM/BAI presence, `samtools quickcheck`, coordinate-sort and read-group
headers, and scratch residue. It does not mutate the native BAM/BAI pair, but it
does create or overwrite its selected status TSV and performs a temporary write
probe in that output directory. The route is described by the
[test baseline](../../docs/design/TEST_BASELINE.md); the producing stage is
routed through the
[Step 05 owner](../../src/norad/stages/split_n_cigar/README.md).

Its default sample roster and `samtools` path are site-specific operator
configuration, not a portable fixture or general stage contract. These checks
are distinct from the automated Python suite and may depend on native tools,
scheduler state, and real outputs. Their results do not by
themselves establish production, scientific, or biological validity.
