# Paired-CMH analysis tests

This directory protects the Step 09 paired-CMH analysis through shell
transaction cases, Python validator cases, an independent count-derived
oracle, and a committed guarded real-R corpus. The
[analysis owner](../../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md)
owns supported commands, while its
[contract](../../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md)
owns method, inputs, outputs, publication, and evidence meaning.

`step_09_cmh_oracle.py` must remain independent of production statistical
implementation. The guarded-R runner may skip when no acceptable R runtime is
available; a skip supplies no real-R evidence. These tests do not establish
cluster execution, completed scientific review, or biological interpretation.
