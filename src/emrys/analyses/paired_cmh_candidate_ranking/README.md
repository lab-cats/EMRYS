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
The runner invokes
[`step_09_cmh_editing_site_calling.R`](step_09_cmh_editing_site_calling.R)
directly with working paths, then requires the existing validator and semantic
all-pass gate to accept its scientific outputs before publication.
For the independent validator's inputs:

```bash
emrys validate paired-cmh-candidate-ranking --help
```

The [contract](CONTRACT.md) owns pairing, numerical methods, and thresholds.
The [runner contract](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution) owns execution and recovery. The validator reconciles results but does not
independently recompute CMH statistics; a separate oracle and real-R corpus
protect that method boundary.

## Retained manual Steps 07–09 observation

The former NORAD handoff gained these operator-supplied records at
[`e69076f1`](https://github.com/lab-cats/EMRYS/blob/e69076f1a35c4ccb54d8b29fddf0a57efda053be/docs/operations/HANDOFF.md).
That document revision is not the execution date. These are historical
standalone-stage results, not evidence for the current complete Run path.

These standalone-stage observations came from branch
`codex/license-and-retire-step09c` at exact NORAD commit
`64b14a11bf2b2371a3b8ef32ebbb642154a77b66`.

| Input | Retained identity |
|---|---|
| Paired sample manifest | `data/raw/samples.paired.tsv`; SHA-256 `b7e42c8ecc8c8202b5c3647dd84c9096780d7db19765b9c1935f11bfbd1fc126` |
| Step 07 partition manifest | `configs/step_07_partitions.primary_contigs.tsv`; SHA-256 `4346cefc23cb695aa653f2cc9c14e9ebc40f2bd09454bb5894ad0eb5f4879b6b` |
| Step 08 annotation | `refs/novogene_ref/genome.gtf`; SHA-256 `3b502426b9605a5afd433bbc69694e782221e62f7c39563323934540d70e3b07` |

| Stage | Retained execution and validation observation |
|---|---|
| Step 07 | The 25-partition paired set is under `results/mpileup-paired/NORAD_EV_PUM1`. Validator array `605174_[1-25]` recorded 25/25 `COMPLETED/0:0`; the aggregate reported `REPORT_COUNT=25` and `FAILED_CHECK_COUNT=0`. |
| Step 08 | Job `605171` completed `0:0` in `00:30:03` with four workers and `MaxRSS=27437560K` (about 27 GiB). Logs `logs/norad-vcf-preprocess-605171.out` and `.err` record 50 VCF inputs and 357,637 supported SNV candidates. Sites and input-receipt SHA-256 values are `81f061b66364ad82a4a2755f48b00ef131fa4fe4e0b566417524f618c06f9f2a` and `ba7c377a7674ff2c8935f47b5d77c49ddde00cad528f8756925711678fa58dac`. `results/qc/validation/08-paired/NORAD_EV_PUM1.validation.tsv` passed all five checks. |
| Step 09 | Job `605173` completed `0:0` in `00:00:49`. Logs `logs/norad-cmh-605173.out` and `.err` record 357,637 candidates, 30,816 tested candidates, and 65 significant sites. The six-output transaction is under `results/editing-paired/NORAD_EV_vs_PUM1`; `results/qc/validation/09-paired/NORAD_EV_vs_PUM1.validation.tsv` passed all seven checks. |

This establishes only manual Steps 07–09 completion and owner validation for
the declared inputs. It does not establish `emrys run` or resume, automatic
reporting, Steps 00–06 in the same Attempt, distributed or multi-node behavior,
full-site qualification, scientific adjudication, or biological validation.
