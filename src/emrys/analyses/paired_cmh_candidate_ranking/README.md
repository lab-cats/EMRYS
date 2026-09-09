# `rank_cohort_candidates_with_paired_CMH` owner

Analysis `09` ranks cohort candidates using paired Cochran–Mantel–Haenszel
(CMH) tests and one global Benjamini–Hochberg correction. It compares explicitly
paired control/treatment samples under the study's declared thresholds.
Threshold-passing candidates are not validated editing sites.

It reads the Step `08` sites table and input receipt, sample/partition
manifests, and analysis policy. The six outputs include all-sites and
significant-sites tables, a summary, mutation-spectrum TSV/PDF, and depth/delta
PDF. External review may use these outputs but is not a pipeline dependency.

Normal execution uses `emrys run` or `resume` as described in the
[Runbook](../../../../docs/operations/RUNBOOK.md#project-and-run-operations).
The private [Python producer](producer.py) coordinates
[`step_09_cmh_editing_site_calling.R`](step_09_cmh_editing_site_calling.R).
For the independent validator's inputs:

```bash
emrys validate paired-cmh-candidate-ranking --help
```

The [contract](CONTRACT.md) owns pairing, numerical methods, thresholds,
publication, and recovery. The validator reconciles results but does not
independently recompute CMH statistics; a separate oracle and real-R corpus
protect that method boundary.
