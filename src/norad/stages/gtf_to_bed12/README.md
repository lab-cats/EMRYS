# `convert_GTF_to_BED12` owner

This directory is the implemented native owner for semantic stage
`convert_GTF_to_BED12` (`norad.stage.convert_GTF_to_BED12.v1`, historical
alias `00b`). Its current public assets are:

- `python -I -m norad convert gtf-to-bed12`, implemented by the private
  [`converter.py`](converter.py) module;
- `python -I -m norad validate bed12`, implemented by the private
  [`validator.py`](validator.py) module;
- [`step_00b_gtf_to_bed12.slurm`](step_00b_gtf_to_bed12.slurm), the
  mode-`0755` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/gtf_to_bed12/test_gtf_to_bed12.py),
  [validator](../../../../tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py),
  and [mocked-job](../../../../tests/stages/gtf_to_bed12/test_step_00b_gtf_to_bed12.py)
  tests.

## Producer

From the repository root, invoke the producer through the installed repository
interpreter:

```bash
.venv/bin/python -I -m norad convert gtf-to-bed12 \
  --gtf refs/novogene_ref/genome.gtf \
  --bed refs/novogene_ref/genome.bed
```

From another working directory, use the absolute path to the installed
interpreter and explicit absolute input and output paths. The producer has no
dry-run or transaction mode and silently replaces the declared BED path. That
replacement is a characterized defect, not an approved safety guarantee.

## Validator

Invoke the validator through an explicit interpreter. Omitting `--execute` is
the no-write dry run:

```bash
.venv/bin/python -I -m norad validate bed12 \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv
```

After inspecting the dry-run evidence, create the output parent and add
`--execute` to publish the report. From another working directory, use the
absolute installed interpreter plus explicit absolute input and output paths.

## Scheduler entry point

Submit only from the intended checkout so `SLURM_SUBMIT_DIR` becomes the job's
repository working directory:

```bash
cd <checkout>
sbatch src/norad/stages/gtf_to_bed12/step_00b_gtf_to_bed12.slurm
```

Submission executes implicitly and has no dry-run control. The job honors the
existing `GTF`, `BED`, and `PYTHON_BIN` overrides. It creates directories
before conversion and requires `PYTHON_BIN` to select an environment where
this checkout is installed. The converter writes the deterministic final BED
directly, after which the wrapper checks that every row has exactly 12 fields.
Publication remains nontransactional: converter failure can leave directories,
and a failed field-count check can leave the produced BED in place.

## Diagnostics, recovery, and evidence

Inspect scheduler stdout/stderr, the final BED, and its path together.
Preserve ambiguous or foreign residue; do not delete or replace
it merely because a local test characterizes the state. The next safe local
action for an existing BED is the validator dry run above with the exact source
GTF. Recovery or replacement of runtime artifacts remains an explicit operator
decision.

Run the owner-focused local tests with:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/gtf_to_bed12/test_gtf_to_bed12.py \
  tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py \
  tests/stages/gtf_to_bed12/test_step_00b_gtf_to_bed12.py
```

The artifact index records the producer's final path while preserving its
implementation evidence identity and byte hash
`b97e35fdb9b60e008f80897c9014dd3f38e2e38c0ba14b1a62c641cc4b8feaab`.
See [`CONTRACT.md`](CONTRACT.md) for the full behavior contract. Available
fixture/mock and coverage evidence is local only; it is not runtime, scheduler,
production, scientific-review, or biological proof.
