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

No installed command, package import, compatibility wrapper, legacy path,
symlink, ambient `PYTHONPATH`, or global `sys.path` mutation is supported.

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

It privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py) and the unchanged
flat [`step_09c_scientific_validation.py`](../../../../scripts/step_09c_scientific_validation.py)
contract owner under separate private identities. The Step `09c` bridge exists
for shared schemas and validators and is a retained ownership inversion, not a
public package API or authority to move Step `09c`.

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
dedicated [Step `08` troubleshooting route](../../../../docs/operations/TROUBLESHOOTING.md#step-08-producer-or-wrapper-leaves-a-partial-rollback-failure-or-stale-transaction)
before action.

Focused local protection is:

```bash
bash tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.sh
.venv/bin/python -m pytest -q \
  tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/stages/preprocess_and_annotate_cohort_candidates/run_step_08_vcf_preprocessing_tests.sh
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_08_vcf_preprocessing
```

Published runtime/input, transaction/recovery, signal/concurrency, validator,
and scheduler baselines are `d29f87b`, `44e649d`, `6e2e2f6`, `3f02d19`, and
`7a667ee`. Executable checkpoint `5e51496` moved exactly eight files and
updated ten reviewed integration owners. Final shell mode/bytes/lines/SHA-256
is `0755` / `39,954` / `1,024` /
`578542fefa02aa23667bb40e582cbab215e6d3efec0a7c2fbb002290f1cfc1f3`;
R is `0644` / `69,505` / `1,939` /
`50cae0523ea68f87535866cbe9e86d38c3812f96a2c8a06ebd66a72177268699`;
validator is `0644` / `12,918` / `346` /
`57a227c478c0caec60fe2ff8d84f7feb1fce28c5248338f1369b2a186284c78f`;
and the mode-`0644` job is `4,597` bytes / `134` lines /
`e51d0df86609ca5d3d39b60f6036ee225bc17c11b6a83d68c683603842c57de6`.

The owner validator passed `17` tests; the complete shell suite passed; and the
five focused integration owners passed within a `597`-test run. Complete shell
contracts and isolated real-R semantic suites passed, and report runtime passed
`17` tests with `60` deselected. Coverage passed `1,219` tests with `17` skips
and the one intentionally stale documentation assertion deselected; Step `08`
is tracked at `162/167` lines and `42/48` branches, with global floors
`9601/11758` and `3367/4784`.

The aggregate gate was not green. Static preflight passed, but guarded
`r-check` stopped on the inherited malformed ignored library entry plus
unavailable Bioconductor DNS and cancelled the other aggregate lanes. An
untouched full Python run separately reached `1,219` passes and `17` skips
before its sole documentation assertion listed twelve deferred migration links
plus nine inherited `UNREFINED` locations. No dependency changed. Separately
passing lanes do not turn the aggregate result green.

Artifact provenance changes only Step `08`'s implementation path and reviewed
shell hash in [`build_artifact_index.py`](../../../../scripts/build_artifact_index.py).
Artifact identities, native receipt versus summary failure-marker distinction,
schemas, ordering, reconciliation, consumers, and scientific meaning are
unchanged.

Git rollback reverts the documentation close, executable `5e51496`, scheduler
`7a667ee`, validator `3f02d19`, signal/concurrency `6e2e2f6`, transaction/
recovery `44e649d`, then runtime/input `d29f87b`. Git cannot authenticate,
recover, delete, or alter runtime outputs, locks, backups, R state, or scheduler
logs. See [`CONTRACT.md`](CONTRACT.md) and completed
[`MIG-03M`](../../../../docs/tasks/COMPLETED/MIG-03M-migrate-preprocess-and-annotate-cohort-candidates-owner.md)
for the complete boundary.
