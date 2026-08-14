# `preprocess_and_annotate_cohort_candidates` owner

Native owner of `norad.stage.preprocess_and_annotate_cohort_candidates.v1`
(historical `08`). [`CONTRACT.md`](CONTRACT.md) owns exact input policy,
three-output transaction, retained defects, consumers, and evidence semantics.

## Entry points

- producer: [`step_08_vcf_preprocessing.sh`](step_08_vcf_preprocessing.sh)
- R implementation: [`step_08_vcf_preprocessing.R`](step_08_vcf_preprocessing.R)
- validator: grouped `python -I -m norad validate cohort-candidate-preprocessing`,
  implemented by private [`validator.py`](validator.py)
- scheduler: [`step_08_vcf_preprocessing.slurm`](step_08_vcf_preprocessing.slurm)

Private R modules split input admission, annotation, receipt reconciliation,
VCF counts, and candidate processing behind the public R coordinator; they are
not additional commands or package APIs.

## Operate

Producer no-write dry-run:

```bash
src/norad/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --rscript-bin /usr/local/bin/Rscript
```

Add `--execute` after inspecting the complete Step `07` barrier, R program,
locks, scratch, publication, and rollback. `legacy_provisional_v1` maps
mechanical orientation labels for compatibility; it does not establish
transcript strand, variants, editing sites, review, or biological readiness.
The orchestration-safe invocation also supplies `--no-clobber`, which rejects a complete
prior set without running R; direct use retains complete-set replacement
unless that option is supplied.

Execute publishes sites, cross-root summary, then the input receipt. Receipt
visibility precedes final validation; it does not hash sibling outputs or the R
program/runtime and is not immutable-input or current-attempt proof.

Validator dry-run:

```bash
cohort=NORAD_EV_PUM1
python -I -m norad validate cohort-candidate-preprocessing \
  --cohort-id "$cohort" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --sites "results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv" \
  --inputs "results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv" \
  --summary "results/qc/vcf_preprocessing/$cohort.step08_summary.tsv" \
  --output "results/qc/validation/08/$cohort.validation.tsv"
```

Create the parent and add `--execute`. Exit `0` permits failed rows. Private
`validator.py` is not a direct repository command or supported import surface.
The validator does not rerun R/annotation, recompute candidate IDs/order, or
reopen Step `07` inputs to establish scientific correctness.

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,RSCRIPT_BIN_OVERRIDE=/usr/local/bin/Rscript \
  src/norad/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.slurm
```

The wrapper requires `SLURM_SUBMIT_DIR` and enters the submitted checkout before
resolving repository-owned helpers, the producer, or its optional local R
environment; an executed spool copy does not become checkout authority.

Change only `EXECUTE=1` after review. Three stale finals can produce false
scheduler success.

## Diagnose and verify

Preserve finals, both-root scratch/backups, lock, manifests, Step `07` inputs,
GTF, R runtime/program/library, streams, job identity, and unrelated bytes.
Never combine attempts or reuse ambiguous roots; incomplete restoration
retains the owned lock and remaining backups for operator recovery.

```bash
bash tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.sh
.venv/bin/python -m pytest -q \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/stages/cohort_candidate_preprocessing/test_validate_step_08_preprocessing_outputs.py
RSCRIPT_BIN=/usr/local/bin/Rscript \
  bash tests/stages/cohort_candidate_preprocessing/run_step_08_vcf_preprocessing_tests.sh
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_08_vcf_preprocessing
```

This is local shell/R/fixture evidence only.
