# Cohort-candidate preprocessing tests

These cases check Step 08 Python/R input rules, candidate processing, serialized
output checks, and validation through the grouped command. Shared runner tests
cover publication and recovery. The
[stage contract](../../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md)
defines the provisional orientation policy.

The guarded-R runner may skip without a suitable runtime; a skip proves no R
execution. Local candidates are not validated variants or editing sites.
