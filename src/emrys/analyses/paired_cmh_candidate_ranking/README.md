# `rank_cohort_candidates_with_paired_CMH` owner

Analysis `09` consumes admitted Step 08 candidates and the sample/partition
manifests, performs paired CMH testing with global BH correction, and publishes
the six declared result, summary, and figure artifacts. Private
[`producer.py`](producer.py) coordinates
[`step_09_cmh_editing_site_calling.R`](step_09_cmh_editing_site_calling.R);
validation is `emrys validate paired-cmh-candidate-ranking`.

[`CONTRACT.md`](CONTRACT.md) owns pairing, method, thresholds, inputs, outputs,
transaction, validation, and evidence meaning. Ranked or threshold-passing
candidates are not adjudicated editing sites or biological findings.
