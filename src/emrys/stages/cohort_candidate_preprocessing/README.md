# `preprocess_and_annotate_cohort_candidates` owner

Native owner of `emrys.stage.preprocess_and_annotate_cohort_candidates.v1`
(historical `08`). [`CONTRACT.md`](CONTRACT.md) owns exact input policy,
three-output transaction, retained defects, consumers, and evidence semantics.

## Entry points

- producer: private Python module [`producer.py`](producer.py)
- R implementation: [`step_08_vcf_preprocessing.R`](step_08_vcf_preprocessing.R)
- validator: grouped `python -I -m emrys validate cohort-candidate-preprocessing`,
  implemented by private [`validator.py`](validator.py)

Private R modules split input admission, annotation, receipt reconciliation,
VCF counts, and candidate processing behind the public R coordinator; they are
not additional commands or package APIs.
For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Producer no-write dry-run:

```bash
: "${EMRYS_RSCRIPT_BIN:?export the admitted Rscript executable path}"
.venv/bin/python -I -m emrys.stages.cohort_candidate_preprocessing.producer \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest data/raw/samples.paired.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --threads 1 \
  --rscript-bin "$EMRYS_RSCRIPT_BIN"
```

The sample manifest must use the exact paired local-CMH header:
`sample_id, r1_fastq, r2_fastq, strandedness, condition, replicate`, with
optional `notes` as the final column. The producer dry-run and independent
validator enforce the same admission contract.

Add `--execute` after inspecting the complete Step `07` barrier, R program,
locks, scratch, publication, and rollback. `legacy_provisional_v1` maps
mechanical orientation labels for compatibility; it does not establish
transcript strand, variants, editing sites, review, or biological readiness.
The orchestration-safe invocation also supplies `--no-clobber`, which rejects a complete
prior set without running R; direct use retains complete-set replacement
unless that option is supplied.

`--threads` bounds independent partition/orientation VCF workers. The owner
builds the annotation model once, returns worker results in manifest then
`FWD_like`, `REV_like` order, and retains one deterministic validation and
publication transaction. It defaults to `1`; Windows direct execution falls
back to one worker because the implementation uses Unix process forking.
Each execution logs assigned job count and cumulative job seconds per worker.

For a site qualification, use the existing
`scripts/benchmark_stage_resources.py` utility with values `1, 2, 4`,
identical inputs, and the three trial-local outputs declared as
`artifact_paths`. It records wall/CPU time, peak RSS, block I/O, and an
artifact-set SHA-256; any byte or row-order change fails artifact parity.
Keep manifests and results outside the repository. The default remains one
worker unless retained site measurements show a material improvement within
the admitted memory limit.

Execute publishes sites, cross-root summary, then the input receipt. Receipt
visibility precedes final validation; it does not hash sibling outputs or the R
program/runtime and is not immutable-input or current-attempt proof.

The producer prints the exact post-execution validator command using its bound
paths, followed by the exact `emrys validate all-pass` command. Run both after
the owner succeeds. The validator may exit `0` while publishing `fail` rows;
`all-pass` is the semantic gate. Private `validator.py` is not a direct
repository command or supported import surface. The validator does not rerun
R/annotation, recompute candidate IDs/order, or reopen Step `07` inputs to
establish scientific correctness.

## Diagnose and verify

Preserve finals, both-root scratch/backups, lock, manifests, Step `07` inputs,
GTF, R runtime/program/library, streams, job identity, and unrelated bytes.
Never combine attempts or reuse ambiguous roots; incomplete restoration
retains the owned lock and remaining backups for operator recovery.

```bash
.venv/bin/python -m pytest -q \
  tests/stages/cohort_candidate_preprocessing/test_producer.py \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/stages/cohort_candidate_preprocessing/test_validate_step_08_preprocessing_outputs.py
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/stages/cohort_candidate_preprocessing/run_step_08_vcf_preprocessing_tests.sh
```

This is local Python/R/fixture evidence only.
