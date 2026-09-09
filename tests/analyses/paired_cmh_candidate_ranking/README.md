# Paired-CMH analysis tests

These tests cover Step 09 publication and validation, an independent oracle
calculated from counts, and a committed guarded real-R corpus. The
[analysis contract](../../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
defines the method, inputs, outputs, and recovery behavior; its
[README](../../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
explains the supported commands.

Validator cases use `python -I -m emrys validate paired-cmh-candidate-ranking`;
`validator.py` is private implementation. `step_09_cmh_oracle.py` must remain
independent of production statistical code. A skipped guarded-R case supplies
no real-R evidence, as explained in the [test evidence limits](../../README.md#evidence-limits).
