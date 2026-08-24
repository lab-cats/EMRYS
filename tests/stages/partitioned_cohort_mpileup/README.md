# Partitioned cohort-mpileup stage tests

This directory protects Step 07 manifest and selector admission, fake-bcftools
execution, three-output publication and rollback, and validator reporting. The
[stage owner](../../../src/emrys/stages/partitioned_cohort_mpileup/README.md)
owns commands, promotion criteria, recovery, and exact evidence meaning.

Validator tests exercise the grouped package route; private `validator.py` is
not a direct command.

Local fake-tool outputs are mechanical mpileup evidence, not validated
variants, editing sites, real bcftools, scheduler, cluster, or production proof.
