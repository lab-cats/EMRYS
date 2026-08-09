# `preprocess_and_annotate_cohort_candidates` owner

This directory is the implemented native owner for semantic stage
`preprocess_and_annotate_cohort_candidates`
(`norad.stage.preprocess_and_annotate_cohort_candidates.v1`, historical alias
`08`). Its public assets are:

- [`step_08_vcf_preprocessing.sh`](step_08_vcf_preprocessing.sh), the
  mode-`0755` directly executable Bash transaction owner;
- [`step_08_vcf_preprocessing.R`](step_08_vcf_preprocessing.R), the
  mode-`0644` Rscript-only scientific implementation;
- [`validate_step_08_preprocessing_outputs.py`](validate_step_08_preprocessing_outputs.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_08_vcf_preprocessing.slurm`](step_08_vcf_preprocessing.slurm), the
  mode-`0644` scheduler entry point; and
- the mirrored [shell](../../../../tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.sh),
  [R](../../../../tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.R),
  [guarded-R runner](../../../../tests/stages/preprocess_and_annotate_cohort_candidates/run_step_08_vcf_preprocessing_tests.sh),
  and [validator](../../../../tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

The 401-line public R coordinator loads four owner-private modules:

- [`_step_08_input_contract.R`](_step_08_input_contract.R) owns arguments,
  paths, manifests, selectors, and partition admission;
- [`_step_08_annotation.R`](_step_08_annotation.R) owns the explicit GTF
  annotation model and overlap mechanics;
- [`_step_08_receipt_contract.R`](_step_08_receipt_contract.R) owns Step `07`
  receipt reconciliation; and
- [`_step_08_vcf_processing.R`](_step_08_vcf_processing.R) owns raw VCF/count
  validation, allele expansion, orientation mapping, and candidate assembly.

The largest private module is 570 lines. The entry point resolves these
siblings from Rscript's own `--file=` invocation path and loads them into the
existing program environment; it does not search the caller's working
directory for a sibling, change that directory, load packages, or add another
public command. The complete Step `08` R owner remains about 1,900 lines: this
is a responsibility decomposition, not a claim that production hardening made
the implementation intrinsically small.

No installed command, supported external package API, compatibility wrapper,
legacy path, symlink, or ambient `PYTHONPATH` contract is exposed. The Python
validator promotes the checkout's `src` root ahead of ambient import paths.

## Producer, inputs, and scientific meaning

The shell enumerates exactly the partition-manifest order crossed with
`FWD_like` and `REV_like`; it does not discover VCFs by glob. It requires the
complete Step `07` receipt/VCF barrier, the sample and partition manifests, a
nonempty annotation GTF, separate output and QC roots, and an explicit or
resolvable Rscript. The sibling R program performs bounded raw-VCF lexical
validation, VariantAnnotation parsing, supported-SNV selection, allele
expansion, GTF overlap, deterministic candidate construction, and exact TSV
generation.

The fixed `legacy_provisional_v1` policy maps `FWD_like` to annotation `+` with
complemented genomic alleles for the RNA representation and maps `REV_like` to
annotation `-` without complementation. These are mechanical compatibility
labels. They do not establish validated transcript strand, library
strandedness, sense/antisense interpretation, variants, RNA-editing sites,
completed scientific review, or biological readiness.

From the repository root, this is a no-write dry run unless `--execute` is
added:

```bash
src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --rscript-bin /usr/local/bin/Rscript
```

Dry-run validates identifiers, manifests, their complete nonoverlapping
partition barrier, every Step `07` receipt and VCF, annotation GTF, Rscript,
and R-program resolution. It prints the exact R command plus final, lock,
temporary, backup, validation, publication, and rollback choices without
creating a directory, lock, temporary, or final. Inspect those choices before
adding `--execute`.

From another CWD, make the producer, both manifests, Step `07` root, annotation
GTF, output/QC roots, Rscript, and any overridden R program absolute. The
default R program is the sibling final path; `STEP08_R_SCRIPT` or `--r-script`
is a diagnostic override whose identity is not recorded in the receipt.

The three outputs are:

```text
<output-root>/<cohort>/<cohort>.step08_sites.tsv
<output-root>/<cohort>/<cohort>.step08_inputs.tsv
<qc-root>/<cohort>.step08_summary.tsv
```

Execute mode owns `.<cohort>.step08.lock` and run-token scratch/backups split
across both roots. It requires all three prior finals or none, validates all
temporaries, publishes sites, cross-root summary, then input receipt, and
revalidates visible bytes and stable inputs. Receipt visibility precedes final
post-publication validation and the in-memory committed flag. The receipt
hashes upstream VCFs, receipts, manifests, and annotation, but not the sibling
sites/summary outputs or R program/runtime/packages. It is not immutable-input
or current-attempt proof.

The implemented
[`rank_cohort_candidates_with_paired_CMH`](../../analyses/rank_cohort_candidates_with_paired_CMH/README.md)
analysis consumes the sites table and input receipt together with the same
manifests. It does not consume the standalone Step `08` QC summary. Preserve
both required outputs and their path/hash context as one predecessor boundary.

## Validator and shared owners

The validator invokes no R and prints five report rows without writing in
dry-run mode:

```bash
cohort=NORAD_EV_PUM1
.venv/bin/python \
  src/norad/stages/preprocess_and_annotate_cohort_candidates/validate_step_08_preprocessing_outputs.py \
  --cohort-id "$cohort" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --sites "results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv" \
  --inputs "results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv" \
  --summary "results/qc/vcf_preprocessing/$cohort.step08_summary.tsv" \
  --output "results/qc/validation/08/$cohort.validation.tsv"
```

Create the report parent and add `--execute` only after inspecting the rows.
The exact checks are `output_transaction`, `manifest_annotation_identity`,
`input_receipt_reconciliation`, `sites_order_uniqueness`, and
`summary_count_reconciliation`. Exit `0` means the rows rendered or published;
one or more may still have `status=fail`.

The validator checks internal table contracts without rerunning
VariantAnnotation, GTF overlap, allele expansion, complementation, or upstream
filtering. It does not recompute candidate IDs or deterministic row order, and
it does not reopen Step `07` files to recompute their hashes. Equivalent
annotation spellings can fail identity evidence; arbitrary unique candidate
IDs and reversed site rows can pass.

It imports neutral
[`validation/report.py`](../../libraries/validation/report.py) and neutral
[`step08.py`](../../contracts/scientific_evidence/step08.py) through the
repository-local package. The latter owns the public Step `08` manifest/table
headers, `ContractError`/`Table` identity, and reconciliation used by this
validator, Step `09`, Step `09c`, and artifact indexing. These consumers share
the repository-local `norad` package identity; no installed package API is
exposed.

## Guarded R and scheduler

Use the repository-local guarded R route without installing or restoring
dependencies:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

Restoration is a separate explicit operator action. In this migration's local
environment, `r-check` remained blocked by an inherited ignored malformed
`macos` library entry and unavailable Bioconductor metadata, while the isolated
Step `08` and Step `09` real-R semantic suites passed against the existing
library. Neither result proves production-scale or cluster behavior.

SLURM opens declared log paths before the job body. Start in the checkout,
create `logs/`, and submit dry-run mode first:

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,RSCRIPT_BIN_OVERRIDE=/usr/local/bin/Rscript \
  src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.slurm
```

Change only `EXECUTE=1` after accepting the dry-run and input/runtime choices.
The wrapper changes to `SLURM_SUBMIT_DIR` with current-CWD fallback, creates
`logs/`, tolerates module diagnostics, probes Rscript only when usable,
delegates the final shell, and checks three nonempty outputs in execute mode.
Missing or nonexecutable Rscript is warning-only at the wrapper and remains a
producer rejection. Version-command failure is tolerated. A zero-exit child
can be falsely accepted when three stale nonempty finals already exist.
Scheduler success is not current-attempt, semantic-validation, cluster,
scientific, or biological proof.

## Recovery, evidence, and rollback

Before cleanup, retry, or recovery, preserve all three finals; output- and
QC-root scratch/backups; lock and owner; manifests; Step `07` receipts/VCFs;
annotation GTF; R program/runtime/library; stdout/stderr; scheduler job,
accounting, logs and CWD; environment overrides; and unrelated bytes. Record
missing expected paths too. Never combine attempts, reconstruct one member,
delete a foreign lock, trust receipt presence/counts/timestamps, or retry the
same output roots before ruling out every active producer and consumer.

Failed restoration may leave a prior final absent while its backup survives,
yet cleanup can remove owned scratch/lock and no durable recovery marker is
written. Controlled receipt-publication exit `67` followed by sites-restore
exit `68` preserves exactly that ambiguous state. This is preservation-first
manual recovery, not successful rollback or retry authority. Follow the
[common recovery rules](../../../../docs/operations/TROUBLESHOOTING.md)
before action.

Focused local protection is:

```bash
bash tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.sh
.venv/bin/python -m pytest -q \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/stages/preprocess_and_annotate_cohort_candidates/run_step_08_vcf_preprocessing_tests.sh
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_08_vcf_preprocessing
```

Current behavior, recovery states, and evidence limits are owned by [`CONTRACT.md`](CONTRACT.md). The owner is locally shell/R/fixture tested; this does not establish scheduler, cluster, production, scientific-review, variant/editing-site, or biological proof.
