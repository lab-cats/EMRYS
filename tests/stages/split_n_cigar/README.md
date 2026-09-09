# Split-N-cigar tests

These cases check Step 05 input sidecars, shell staging, BAM/BAI publication
and rollback, and structural validation through the grouped command. Private
`validator.py` is not a direct command. The
[stage contract](../../../src/emrys/stages/split_n_cigar/CONTRACT.md)
defines recovery hazards. Fake tools do not establish the GATK transform.
