# `preprocess_and_annotate_cohort_candidates` owner

Stage `08` combines the complete declared Step `07` VCF set into one
cohort-candidate table. It expands alternate alleles, keeps supported SNVs,
attaches sample depth/allele measurements and GTF overlaps, and applies the
explicitly provisional legacy orientation mapping.

Inputs include paired sample and partition manifests, all upstream receipts
and VCFs, annotation GTF, runner-supplied output paths, and the selected R runtime.
Outputs are the sites table, input receipt, and QC summary. Step `09` consumes
the sites and receipt; these are candidate inputs, not biological findings.

The [Project Run](../README.md#running-a-stage) invokes
[`step_08_vcf_preprocessing.R`](step_08_vcf_preprocessing.R) directly. To inspect validator arguments:

```bash
emrys validate cohort-candidate-preprocessing --help
```

Read the [contract](CONTRACT.md) for scientific policy, worker ordering, and
validation limits. The [runner contract](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution) owns execution and recovery. The Python validator checks the staged tables before publication; it does not repeat the R candidate construction or annotation.

## Retained optimization experiment

[PR #45](https://github.com/lab-cats/EMRYS/pull/45) narrowed Step 08 VCF-field
materialization. [Run 33090518708](https://github.com/lab-cats/EMRYS/actions/runs/33090518708)
at `195a78d1c2d7a25d2d66368d760b16b907d2e4df` retained artifact
`step08-fragments-1`; that name does not identify the separate fragment prototype
`03257218660c951daf99a2c2085c7f357dc78fe0`. Recorded artifact comparisons matched.
Each million-case comparison had only one baseline/candidate pair: wall reductions
were 0.7% and 2.4%, RSS reduction at most 5.4%, and small cases were mixed.
The selected gate (10% median wall or 15% peak RSS improvement without material
regression) was not met; no adoption or current whole-Run performance claim follows.

The [September 7 review](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/optimization_campaign.md#prior-work-and-scope-boundaries)
at `fdf76760311e6c8076320a289ef3956d754c190d` retained the distinction between these
experiments. Any newly selected bounded-memory change needs complete R producer
and Python validator parity: allele/annotation meaning, sample/row order, lexical
TSV values, skewed workloads, independent validation and publication recovery.
