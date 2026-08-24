# `convert_GTF_to_BED12` owner

This directory is the implemented native owner for semantic stage
`convert_GTF_to_BED12` (`emrys.stage.convert_GTF_to_BED12.v1`, historical
alias `00b`). Its current public assets are:

- `python -I -m emrys convert gtf-to-bed12`, implemented by the private
  [`converter.py`](converter.py) module;
- `python -I -m emrys validate bed12`, implemented by the private
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
.venv/bin/python -I -m emrys convert gtf-to-bed12 \
  --gtf refs/novogene_ref/genome.gtf \
  --bed refs/novogene_ref/genome.bed
```

From another working directory, use the absolute path to the installed
interpreter and explicit absolute input and output paths. The default invocation
renders the deterministic BED12 bytes and prints the exact create-exclusive
publication plan without creating the output parent, lock, staging file, or
BED12. Add `--execute` only after inspection.

Execute mode writes and fsyncs one owner-token staging file, links it to an
absent final path without replacement, retains the staged inode as an ownership
anchor through lock cleanup, then removes that anchor. Rollback removes a final
only while it is still the same regular-file inode as the anchor. Lock/staging
cleanup failure or a foreign final replacement fails closed with recovery
residue. An existing output, lock, or staging residue is a blocker and is
preserved. An orchestrator may bind the transaction to its own safe identifier
with `--run-token`; omitting that option retains the private random-token
fallback.

## Validator

Invoke the validator through an explicit interpreter. Omitting `--execute` is
the no-write dry run:

```bash
.venv/bin/python -I -m emrys validate bed12 \
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
sbatch src/emrys/stages/gtf_to_bed12/step_00b_gtf_to_bed12.slurm
```

Submission executes implicitly and supplies `--execute` plus one exact safe
publication token to the producer. The job honors the existing `GTF`, `BED`,
and `PYTHON_BIN` overrides. `EMRYS_RUN_TOKEN` takes precedence when supplied;
otherwise the job uses `SLURM_JOB_ID`, with the shell process ID retained only
as a safe direct-execution/test fallback. The selected token must match the
producer's safe-identifier contract.

The job creates the log and final-output directories before conversion and
requires `PYTHON_BIN` to select an environment where this checkout is
installed. The transactional converter writes the deterministic final BED
directly; there is no intermediate BED or second bedtools sort. The wrapper
then requires at least one row and exactly 12 fields per row. A converter
failure cannot replace an existing final. A failed postcheck exits nonzero and
preserves the newly published final as explicit inspection evidence rather
than printing the completion message.

## Diagnostics, recovery, and evidence

Inspect scheduler stdout/stderr, the final BED, and its transaction-residue
paths together. Preserve ambiguous or foreign residue; do not delete or
replace it merely because a local test characterizes the state. The next safe
local action for an existing BED is the validator dry run above with the exact
source GTF. Recovery or replacement of runtime artifacts remains an explicit
operator decision.

Run the owner-focused local tests with:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/gtf_to_bed12/test_gtf_to_bed12.py \
  tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py \
  tests/stages/gtf_to_bed12/test_step_00b_gtf_to_bed12.py
```

The artifact index records the producer's final path while preserving its
implementation evidence identity and byte hash. See
[`CONTRACT.md`](CONTRACT.md) for the full behavior contract. Available
fixture/mock and coverage evidence is local only; it is not runtime, scheduler,
production, scientific-review, or biological proof.
