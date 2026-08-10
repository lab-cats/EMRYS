# Operator data checks

This directory owns retained operator-facing checks over existing workflow
outputs. `validate_step05_outputs.sh` performs the permanent read-only Step 05
output check described by the
[test baseline](../../docs/design/TEST_BASELINE.md); the producing stage is
routed through the
[Step 05 owner](../../src/norad/stages/split_N_cigar_reads_with_GATK/README.md).

These checks are distinct from the automated Python suite and may depend on
native tools, scheduler state, and real outputs. Their results do not by
themselves establish production, scientific, or biological validity.
