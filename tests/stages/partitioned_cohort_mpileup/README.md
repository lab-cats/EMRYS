# Partitioned cohort-mpileup stage tests

This directory protects Step 07 manifest and selector admission, fake-bcftools
execution, three-output publication and rollback, and validator reporting. The
[stage owner](../../../src/emrys/stages/partitioned_cohort_mpileup/README.md)
owns commands, promotion criteria, recovery, and exact evidence meaning.

`test_producer.py` protects the private Python producer, including streamed
bcftools pipelines, stationary-input guards, interruption, and receipt-last
publication. Validator tests remain independent of that producer.

The retired shell suite's hard-coded primary/pilot configuration-count checks
were not producer behavior and are not copied. Dataset promotion counts remain
separate operational criteria rather than implementation-parity tests.

Validator tests exercise the grouped package route; private `validator.py` is
not a direct command.

Local fake-tool outputs are mechanical mpileup evidence, not validated
variants, editing sites, real bcftools, scheduler, cluster, or production proof.
