# `rank_cohort_candidates_with_paired_CMH` owner

This directory is the implemented native owner for semantic analysis
`rank_cohort_candidates_with_paired_CMH`
(`norad.analysis.rank_cohort_candidates_with_paired_CMH.v1`, historical alias
`09`). Its public assets are:

- [`step_09_cmh_editing_site_calling.sh`](step_09_cmh_editing_site_calling.sh),
  the mode-`0755` directly executable Bash transaction owner;
- [`step_09_cmh_editing_site_calling.R`](step_09_cmh_editing_site_calling.R),
  the mode-`0644` Rscript-only statistical implementation;
- [`validate_step_09_cmh_outputs.py`](validate_step_09_cmh_outputs.py), the
  mode-`0644` explicit-interpreter validator;
- [`step_09_cmh_editing_site_calling.slurm`](step_09_cmh_editing_site_calling.slurm),
  the mode-`0755` scheduler entry point; and
- the mirrored [shell](../../../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.sh),
  [R](../../../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.R),
  [guarded-R runner](../../../../tests/analyses/rank_cohort_candidates_with_paired_CMH/run_step_09_cmh_tests.sh),
  [validator](../../../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py),
  and [independent-oracle](../../../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py)
  protection. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

No installed command, package import, compatibility wrapper, legacy path,
symlink, ambient `PYTHONPATH`, or global `sys.path` mutation is supported.

## Producer, inputs, and scientific meaning

The sample manifest is the only pairing authority. Control and treatment must
have exactly one sample for every identical replicate label and at least two
paired strata. The partition manifest, Step `08` sites table, and Step `08`
input receipt bind the candidate universe, order, samples, counts, and
`legacy_provisional_v1` orientation policy. The committed
[`step_09_pairs.NORAD_EV_PUM1.tsv`](../../../../configs/step_09_pairs.NORAD_EV_PUM1.tsv)
is reference documentation, not a runtime overlay.

The R program builds replicate-stratified edited/unedited tables, runs the
two-sided continuity-corrected `stats::mantelhaen.test`, applies one global
Benjamini-Hochberg correction, and classifies strict depth, background, FDR,
odds-ratio, and allele-fraction thresholds. Outputs are CMH-ranked cohort
candidates. They are not validated RNA-editing sites, validated strand
interpretation, completed scientific review, or biological readiness.

From the repository root, this is a no-write dry run unless `--execute` is
added:

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

Dry-run validates all declared paths, pairing, thresholds, and R choices,
prints the exact R command, invokes no R, and creates no output, lock, scratch,
backup, or final. Inspect those choices before adding `--execute`.

From another CWD, make the shell, Rscript, R program, both manifests, Step
`08` root, and output root absolute. For example:

```bash
repo=/absolute/path/to/norad
"$repo/src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.sh" \
  --analysis-id NORAD_EV_vs_PUM1 \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest "$repo/samples.tsv" \
  --partition-manifest "$repo/configs/step_07_partitions.primary_contigs.tsv" \
  --step08-root "$repo/results/vcf_preprocessed" \
  --output-root /absolute/output/editing \
  --rscript-bin /usr/local/bin/Rscript \
  --r-script "$repo/src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.R"
```

The selected R program can still change after admission without being
detected: the characterized producer may publish and exit `0`. The summary
does not record the selected Rscript/R program, R/package state, a durable
attempt identity, or hashes of its five sibling outputs. These are evidence
ceilings, not supported guarantees.

## Six-output transaction and validator

The six outputs under `<output-root>/<analysis-id>/` are:

```text
<analysis>.cmh_all_sites.tsv
<analysis>.cmh_significant_sites.tsv
<analysis>.mutation_spectrum.tsv
<analysis>.mutation_spectrum.pdf
<analysis>.depth_delta.pdf
<analysis>.cmh_summary.tsv
```

Execute mode owns `.<analysis>.step09.lock/`, uses run-token scratch/backups,
requires all six prior finals or none, validates temporaries, publishes the
five non-summary files in fixed order, and publishes the summary last. The
summary becomes visible before final content/hash checks finish, so visibility
alone is not committed-attempt proof. Failed restoration can retain the owned
lock and exact recovery backups for manual intervention.

From the repository root, validator dry-run prints seven rows, invokes no R,
and writes no report:

```bash
analysis=NORAD_EV_vs_PUM1
cohort=NORAD_EV_PUM1
analysis_dir="results/editing/$analysis"
.venv/bin/python \
  src/norad/analyses/rank_cohort_candidates_with_paired_CMH/validate_step_09_cmh_outputs.py \
  --analysis-id "$analysis" \
  --cohort-id "$cohort" \
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

For arbitrary-CWD validation, make the interpreter, validator, all ten inputs,
and report path absolute. Create the report parent and add `--execute` only
after inspecting the rows. Exit `0` means inspection/rendering or publication
succeeded; rows may still have `status=fail`.

The checks are `output_transaction`,
`upstream_identity_and_candidate_order`, `status_semantics`,
`significant_subset`, `summary_count_reconciliation`,
`mutation_spectrum_reconciliation`, and `pdf_structure`. The validator derives
BH from reported p-values but does not independently recompute count-table
estimability, CMH statistic, p-value, or common odds ratio. Its current
`status_semantics` expected text nevertheless says CMH was recomputed. The
separate real-R fixture and independent oracle protect that boundary; neither
turns the production validator into independent statistical proof.

The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py), neutral
[`step08.py`](../../contracts/scientific_evidence/step08.py) for manifests and
the Step `08` inputs/sites contract, and neutral
[`step09.py`](../../contracts/scientific_evidence/step09.py) for the public Step
`09` output contract. The validator's direct Step `08` load and neutral Step
`09`'s Step `08` dependency must resolve the same object before the validator
continues. None of these exact-file bridges creates a package API, and the
validator no longer loads the Step `09c` implementation.

After owner validation, reconcile the complete table and exact significant
subset in an allocated production compute context:

```bash
set -euo pipefail
analysis=NORAD_EV_vs_PUM1
out="results/editing/$analysis"
all="$out/$analysis.cmh_all_sites.tsv"
significant="$out/$analysis.cmh_significant_sites.tsv"
summary="$out/$analysis.cmh_summary.tsv"
spectrum="$out/$analysis.mutation_spectrum.tsv"
step08="results/vcf_preprocessed/NORAD_EV_PUM1/NORAD_EV_PUM1.step08_sites.tsv"

[[ "$(awk 'END { print NR - 1 }' "$all")" -eq \
   "$(awk 'END { print NR - 1 }' "$step08")" ]]
[[ "$(awk 'END { print NR - 1 }' "$summary")" -eq 1 ]]
[[ "$(awk 'END { print NR - 1 }' "$spectrum")" -eq 12 ]]

diff -u \
  <(awk -F '\t' '
      NR == 1 {
        for (i = 1; i <= NF; i++) if ($i == "call_status") status = i
        if (!status) exit 1
        print
        next
      }
      $status == "significant_up" || $status == "significant_down" { print }
    ' "$all") \
  "$significant"
```

The empty diff supplements schemas, hashes, reconciled totals, PDF structure,
scheduler/log inspection, and lock/run-token inspection.

## Guarded R and scheduler

The owner-specific real-R and independent-oracle diagnostics are:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/analyses/rank_cohort_candidates_with_paired_CMH/run_step_09_cmh_tests.sh
.venv/bin/python -m pytest -q \
  tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py
```

Step `09` uses base R. R restoration or dependency installation is a separate
explicit operator action. These diagnostics establish local fixture behavior,
not production-scale or cluster behavior.

SLURM opens declared log paths before the job body. Start in the checkout,
create `logs/`, and submit dry-run mode first:

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,RSCRIPT_BIN_OVERRIDE=/usr/local/bin/Rscript \
  src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.slurm
```

Change only `EXECUTE=1` after accepting the dry-run and upstream/runtime
choices. Explicit Bash execution is a local wrapper diagnostic, not the
supported scheduler journey. The wrapper does not preflight Rscript or the R
program and relies on the child. It creates `logs/` in its body, uses
`SLURM_SUBMIT_DIR` with launch-CWD fallback, and checks only that six outputs
exist after an exit-`0` child. Six stale outputs can therefore produce false
success. Scheduler exit `0` is not current-attempt, method, cluster,
scientific-review, or biological proof.

## Recovery, provenance, evidence, and rollback

Before cleanup, retry, or recovery, preserve all six finals; every matching
temporary and backup; the lock and owner; both manifests; both Step `08`
inputs; selected Rscript, R program, startup/library state, and hashes; all
streams; scheduler job/accounting/logs/CWD; environment overrides; and
unrelated bytes. Record missing expected paths. Never combine attempts,
manufacture a member or summary, delete a foreign or recovery lock, discard a
backup, trust visibility, names, hashes, timestamps, or stale scheduler
success, or reuse the same output root before ruling out every writer and
consumer. A separately authorized nonproduction diagnostic retry uses a fresh
absolute output root.

Artifact provenance changes only `STEP_PRODUCERS["09"]` to this final shell
path and its reviewed hash in
[`build_artifact_index.py`](../../reporting/build_artifact_index.py).
Artifact IDs, six native identities, validation-report identity, schemas,
ordering, consumers, and scientific meaning are unchanged.

Focused local protection is:

```bash
bash tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.sh
.venv/bin/python -m pytest -q \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/contracts/scientific_evidence/test_step09.py \
  tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py \
  tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/analyses/rank_cohort_candidates_with_paired_CMH/run_step_09_cmh_tests.sh
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_09_cmh
```

Current behavior, recovery states, and evidence limits are owned by
[`CONTRACT.md`](CONTRACT.md) and the common/owner-specific
[`troubleshooting rules`](../../../../docs/operations/TROUBLESHOOTING.md). The
owner is locally shell/R/fixture tested; this does not establish scheduler,
cluster, production, scientific-review, editing-site, or biological proof.
