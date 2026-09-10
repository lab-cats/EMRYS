# Paired-CMH analysis tests

These tests cover direct R outputs and planned arguments, requested-policy
validation, an oracle calculated from counts, and a committed guarded real-R
corpus. Shared runner tests cover publication and recovery. The
[analysis contract](../../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
defines the method, inputs, and outputs; its
[README](../../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
explains the supported commands.

Validator cases use `python -I -m emrys validate paired-cmh-candidate-ranking`;
`validator.py` is private implementation. `step_09_cmh_oracle.py` must remain
independent of production statistical code. A skipped guarded-R case supplies
no real-R evidence, as explained in the [test evidence limits](../../README.md#evidence-limits).
