# `preprocess_and_annotate_cohort_candidates` owner

Stage `08` reconciles the admitted partitioned mpileup outputs with the
reference and annotation policy, then publishes the three cohort-candidate
artifacts consumed by downstream analyses. Private [`producer.py`](producer.py)
coordinates [`step_08_vcf_preprocessing.R`](step_08_vcf_preprocessing.R);
validation is `emrys validate cohort-candidate-preprocessing`.

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, provisional policy, outputs,
transaction, recovery, validation, and evidence meaning. These are candidate
inputs, not called variants, adjudicated editing sites, or biological proof.
