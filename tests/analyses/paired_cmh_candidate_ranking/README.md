# Paired-CMH analysis tests

This directory protects the Step 09 paired-CMH analysis through shell
transaction cases, Python validator cases, an independent count-derived
oracle, and a committed guarded real-R corpus. The
[analysis owner](../../../src/norad/analyses/paired_cmh_candidate_ranking/README.md)
owns supported commands, while its
[contract](../../../src/norad/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
owns method, inputs, outputs, publication, and evidence meaning.

Validator cases exercise the grouped
`python -I -m norad validate paired-cmh-candidate-ranking` route; the owner's
`validator.py` is private package implementation rather than a direct command.

`step_09_cmh_oracle.py` must remain independent of production statistical
implementation. The guarded-R runner may skip when no acceptable R runtime is
available; a skip supplies no real-R evidence. These tests do not establish
cluster execution, completed scientific review, or biological interpretation.
