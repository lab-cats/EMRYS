# Split-N-cigar stage tests

This directory protects Step 05 input-sidecar admission, shell staging,
BAM/BAI publication and rollback, and structural validator behavior. The
[stage owner](../../../src/norad/stages/split_n_cigar/README.md) owns commands,
recovery hazards, and exact evidence limits. Validator tests exercise the
grouped package route; private `validator.py` is not a direct command.

Fixtures and fake tools do not prove the GATK transform, real GATK, Java or
samtools behavior, scheduler or cluster execution, or production evidence.
