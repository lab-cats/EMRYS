# Partitioned cohort-mpileup tests

`test_producer.py` checks Step 07 manifests and selectors, streamed bcftools
pipelines, unchanged inputs, interruption, and three-output publication with
the receipt written last. It uses fake bcftools. Independent validator tests
exercise the grouped command; private `validator.py` is not a direct command.

The [stage contract](../../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
owns dataset-promotion criteria. The retired shell suite's fixed primary/pilot
configuration counts were not producer behavior and are not copied here.
Fixture VCFs are mechanical mpileup outputs, not validated variants or editing sites.
