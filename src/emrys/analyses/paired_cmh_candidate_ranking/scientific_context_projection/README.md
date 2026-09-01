# Scientific-context projection owner

This directory owns the post-CMH scientific projection used to explain where
ranked candidates occur and what known sequence context surrounds them. It
turns the exact Step `09` candidate tables, reference FASTA/FAI, and the fixed
PUM `UGUANA`/DNA `TGTANA` hypothesis into validated figure-ready tables. It is
an analysis owner, not a report renderer or biological adjudication step.

[`CONTRACT.md`](CONTRACT.md) defines the exact inputs, five-output transaction,
sequence orientation, population, matching, enrichment, publication, and
failure semantics.

## Entry points

- producer: [`scientific_context_projection.sh`](scientific_context_projection.sh)
- R computation: [`scientific_context_projection.R`](scientific_context_projection.R)
- known-motif policy: [`resources/pum_motifs_v1.tsv`](resources/pum_motifs_v1.tsv)
- grouped validator: `python -I -m emrys validate scientific-context-projection`

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Dry-run validates and hashes inputs, prints the exact R command and stable
publication roster, and writes nothing:

```bash
: "${EMRYS_RSCRIPT_BIN:?export the admitted Rscript executable path}"
src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh \
  --analysis-id NORAD_EV_vs_PUM1 \
  --step09-all-sites results/editing/NORAD_EV_vs_PUM1/NORAD_EV_vs_PUM1.cmh_all_sites.tsv \
  --step09-significant-sites results/editing/NORAD_EV_vs_PUM1/NORAD_EV_vs_PUM1.cmh_significant_sites.tsv \
  --step09-summary results/editing/NORAD_EV_vs_PUM1/NORAD_EV_vs_PUM1.cmh_summary.tsv \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --output-root results/scientific_context \
  --rscript-bin "$EMRYS_RSCRIPT_BIN" \
  --no-clobber
```

Add `--execute` only after inspecting the Step `09` transaction, exact
reference pair, R environment, lock, scratch, and publication plan. The owner
extracts continuous genomic `-100..+100` windows and mechanically orients each
window so its center equals the declared RNA reference base. This compatibility
policy is provisional; it does not establish transcript direction, sense,
antisense, an RNA-binding event, or a validated editing site.

When the registered-motif enrichment row is available, its effect is Fisher's
conditional maximum-likelihood odds-ratio estimate with an exact two-sided 95%
confidence interval. It remains a context comparison, not a binding or editing
adjudication.

Validate a completed receipt:

```bash
.venv/bin/python -I -m emrys validate scientific-context-projection \
  --receipt results/scientific_context/NORAD_EV_vs_PUM1/NORAD_EV_vs_PUM1.context_receipt.tsv \
  --output results/qc/validation/10/NORAD_EV_vs_PUM1.validation.tsv
```

Create the report parent and add `--execute` to publish the one-row validation
report. Exit `0` permits a reported `fail`; the common `all-pass` gate owns the
semantic pass requirement.

## Diagnose and verify

Preserve the three Step `09` inputs, FASTA/FAI, motif catalog, all five finals,
lock, staging anchors, backups, R program/runtime/library, streams, and job
identity. Do not combine attempts or treat the receipt pathname, scheduler
success, or output presence as proof of a current complete transaction.

```bash
bash tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/test_scientific_context_projection.sh
.venv/bin/python -m pytest -q \
  tests/contracts/scientific_evidence/test_scientific_context.py \
  tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/test_validator.py
bash tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/run_scientific_context_projection_tests.sh
```

These are deterministic tiny-fixture and local-runtime checks, not production,
cluster, scientific-review, or biological evidence.
