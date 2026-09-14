# Cohort-candidate preprocessing tests

These cases check direct R computation, exact upstream receipt/VCF bindings,
serialized output checks, and validation through the grouped command. Shared runner tests
cover publication and recovery. The
[stage contract](../../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md)
defines the provisional orientation policy. The guarded R fixture also checks
interval reduction and derived UTR ranges against explicit expected coordinates.

The guarded-R runner may skip without a suitable runtime; a skip proves no R
execution. Local candidates are not validated variants or editing sites.
