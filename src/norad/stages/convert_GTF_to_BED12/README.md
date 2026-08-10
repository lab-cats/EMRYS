# `convert_GTF_to_BED12` owner

This directory is the implemented native owner for semantic stage
`convert_GTF_to_BED12` (`norad.stage.convert_GTF_to_BED12.v1`, historical
alias `00b`). Its current public assets are:

- [`gtf_to_bed12.py`](gtf_to_bed12.py), the mode-`0755` Python producer;
- [`validate_step_00b_bed12.py`](validate_step_00b_bed12.py), the mode-`0644`
  explicit-interpreter validator;
- [`step_00b_gtf_to_bed12.slurm`](step_00b_gtf_to_bed12.slurm), the
  mode-`0755` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/convert_GTF_to_BED12/test_gtf_to_bed12.py),
  [validator](../../../../tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py),
  and [mocked-job](../../../../tests/stages/convert_GTF_to_BED12/test_step_00b_gtf_to_bed12.py)
  tests.

## Producer

From the repository root, invoke the producer directly or through the exact
repository interpreter:

```bash
src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py \
  --gtf refs/novogene_ref/genome.gtf \
  --bed refs/novogene_ref/genome.unsorted.bed

.venv/bin/python src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py \
  --gtf refs/novogene_ref/genome.gtf \
  --bed refs/novogene_ref/genome.unsorted.bed
```

From another working directory, either `cd` to the checkout first or use the
absolute checkout path for the producer and explicit absolute input and output
paths. The producer has no dry-run or transaction mode and silently replaces
the declared BED path. That replacement is a characterized defect, not an
approved safety guarantee.

## Validator

Invoke the validator through an explicit interpreter. Omitting `--execute` is
the no-write dry run:

```bash
.venv/bin/python src/norad/stages/convert_GTF_to_BED12/validate_step_00b_bed12.py \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv
```

After inspecting the dry-run evidence, create the output parent and add
`--execute` to publish the report. From another working directory, either `cd`
to the checkout or use absolute checkout paths for the interpreter and
validator plus explicit absolute input and output paths.

## Scheduler entry point

Submit only from the intended checkout so `SLURM_SUBMIT_DIR` becomes the job's
repository working directory:

```bash
cd <checkout>
sbatch src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm
```

Submission executes implicitly and has no dry-run control. The job honors the
existing `GTF`, `UNSORTED_BED`, `BED`, and `PYTHON_BIN` overrides. It creates
directories before conversion and publishes the intermediate and final BED
nontransactionally. Converter failure can leave directories, bedtools failure
can leave the intermediate plus a redirect-created final, and a bad-field
result can remain published after the existing contradictory success message.
These scheduler defects are characterized and preserved, not approved.

## Diagnostics, recovery, and evidence

Inspect scheduler stdout/stderr, the intermediate BED, the final BED, and their
paths together. Preserve ambiguous or foreign residue; do not delete or replace
it merely because a local test characterizes the state. The next safe local
action for an existing BED is the validator dry run above with the exact source
GTF. Recovery or replacement of runtime artifacts remains an explicit operator
decision.

Run the owner-focused local tests with:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/convert_GTF_to_BED12/test_gtf_to_bed12.py \
  tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py \
  tests/stages/convert_GTF_to_BED12/test_step_00b_gtf_to_bed12.py
```

The artifact index records the producer's final path while preserving its
implementation evidence identity and byte hash
`5c69dabba9139598a9c67331b3200b8db8a29793334ff80f19850eb37ad57a04`.
See [`CONTRACT.md`](CONTRACT.md) for the full behavior contract. Available
fixture/mock and coverage evidence is local only; it is not runtime, scheduler,
production, scientific-review, or biological proof.
