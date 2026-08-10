# `rank_cohort_candidates_with_paired_CMH` owner

Native owner of `norad.analysis.rank_cohort_candidates_with_paired_CMH.v1`
(historical `09`). [`CONTRACT.md`](CONTRACT.md) owns exact pairing, method,
six-output transaction, validation, consumer, and evidence semantics.

## Entry points

- transaction owner: [`step_09_cmh_editing_site_calling.sh`](step_09_cmh_editing_site_calling.sh)
- statistical implementation: [`step_09_cmh_editing_site_calling.R`](step_09_cmh_editing_site_calling.R)
- validator: [`validate_step_09_cmh_outputs.py`](validate_step_09_cmh_outputs.py)
- scheduler: [`step_09_cmh_editing_site_calling.slurm`](step_09_cmh_editing_site_calling.slurm)

Private R modules sit behind the public coordinator; the historical REMORA
script is an algorithm reference, not a runtime dependency or parity proof.

## Operate

The sample manifest is the only pairing authority. Dry-run writes nothing:

```bash
src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.sh \
  --analysis-id NORAD_EV_vs_PUM1 \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-root results/vcf_preprocessed \
  --output-root results/editing \
  --rscript-bin /usr/local/bin/Rscript
```

Add `--execute` after inspecting pairing, thresholds, inputs, R identity, lock,
scratch, publication, and rollback. The method is two-sided continuity-
corrected CMH with one global BH correction and fixed threshold classification.
Outputs are ranked candidates, not validated editing sites or biological proof.

Execute publishes five payloads then the summary. Summary visibility precedes
final checks and is not committed-attempt proof; the summary omits R
program/runtime identity and sibling hashes.

Validator dry-run:

```bash
analysis=NORAD_EV_vs_PUM1 cohort=NORAD_EV_PUM1
analysis_dir="results/editing/$analysis"
.venv/bin/python src/norad/analyses/rank_cohort_candidates_with_paired_CMH/validate_step_09_cmh_outputs.py \
  --analysis-id "$analysis" --cohort-id "$cohort" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-sites "results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv" \
  --step08-inputs "results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv" \
  --all-sites "$analysis_dir/$analysis.cmh_all_sites.tsv" \
  --significant-sites "$analysis_dir/$analysis.cmh_significant_sites.tsv" \
  --summary "$analysis_dir/$analysis.cmh_summary.tsv" \
  --mutation-spectrum "$analysis_dir/$analysis.mutation_spectrum.tsv" \
  --mutation-spectrum-pdf "$analysis_dir/$analysis.mutation_spectrum.pdf" \
  --depth-delta-pdf "$analysis_dir/$analysis.depth_delta.pdf" \
  --output "results/qc/validation/09/$analysis.validation.tsv"
```

Create the parent and add `--execute`. Exit `0` permits failed rows. The
validator derives BH from reported p-values but does not independently
recompute CMH statistics; the real-R fixture and independent oracle protect
that separate boundary.

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,RSCRIPT_BIN_OVERRIDE=/usr/local/bin/Rscript \
  src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.slurm
```

Change only `EXECUTE=1` after review. Six stale outputs can produce false
scheduler success.

## Diagnose and verify

Preserve all six finals, scratch/backups, lock, manifests, Step `08` inputs, R
program/runtime/library/hashes, streams, job identity, and unrelated bytes.
Never combine attempts or trust summary visibility, names, hashes, timestamps,
or stale scheduler success. Use a fresh root for an authorized diagnostic run.

```bash
bash tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.sh
.venv/bin/python -m pytest -q \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/contracts/scientific_evidence/test_step09.py \
  tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py \
  tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/analyses/rank_cohort_candidates_with_paired_CMH/run_step_09_cmh_tests.sh
.venv/bin/python -m pytest -q tests/test_slurm_wrapper_contracts.py -k step_09_cmh
```

This is local shell/R/fixture evidence only.
