# `generate_partitioned_cohort_mpileup_VCFs` owner

Stage `07` produces one multi-sample VCF for each mechanical orientation group
in a declared cohort partition. It runs bcftools pileup and filtering, not
variant calling. These VCFs are candidate inputs, not validated editing sites.

Inputs are the ordered sample/partition manifests, both orientation BAM/BAI
pairs for every sample, FASTA/FAI, bcftools, depth/filter settings, and
runner-supplied output paths. Each partition produces two VCFs plus a receipt. Step `08` waits
for the complete declared partition set.

The private [producer](producer.py) runs through the
[Project Run](../README.md#running-a-stage). For the validator's explicit inputs:

```bash
emrys validate partitioned-cohort-mpileup --help
```

The [contract](CONTRACT.md) owns selectors, defaults, order, and receipt
limitations. The [runner contract](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution) owns execution and recovery. Validation checks declared structure and
counts without rerunning bcftools; header-only VCFs can be valid.
