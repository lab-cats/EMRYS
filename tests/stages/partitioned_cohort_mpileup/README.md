# Partitioned cohort-mpileup tests

`test_partitioned_cohort_mpileup_producer.py` checks Step 07 manifests and
selectors, both streamed bcftools processes, VCF sample order, and final-path
receipt metadata. It uses fake bcftools. Shared runner tests cover input
stability, publication, interruption, and recovery. Independent validator tests
exercise the grouped command; private `validator.py` is not a direct command.

The [stage contract](../../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
owns dataset-promotion criteria. The retired shell suite's fixed primary/pilot
configuration counts were not producer behavior and are not copied here.
Fixture VCFs are mechanical mpileup outputs, not validated variants or editing sites.
