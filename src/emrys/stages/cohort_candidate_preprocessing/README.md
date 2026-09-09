# `preprocess_and_annotate_cohort_candidates` owner

Stage `08` combines the complete declared Step `07` VCF set into one
cohort-candidate table. It expands alternate alleles, keeps supported SNVs,
attaches sample depth/allele measurements and GTF overlaps, and applies the
explicitly provisional legacy orientation mapping.

Inputs include paired sample and partition manifests, all upstream receipts
and VCFs, annotation GTF, runner-supplied output paths, and the selected R runtime.
Outputs are the sites table, input receipt, and QC summary. Step `09` consumes
the sites and receipt; these are candidate inputs, not biological findings.

The private [Python producer](producer.py) invokes
[`step_08_vcf_preprocessing.R`](step_08_vcf_preprocessing.R) through the
[Project Run](../README.md#running-a-stage). To inspect validator arguments:

```bash
emrys validate cohort-candidate-preprocessing --help
```

Read the [contract](CONTRACT.md) for scientific policy, worker ordering, and
validation limits. The [runner contract](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution) owns execution and recovery. The Python validator checks the published
tables; it does not repeat the R candidate construction or annotation.
