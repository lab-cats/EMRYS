# `convert_GTF_to_BED12` owner

This directory is the implemented native owner for semantic stage
`convert_GTF_to_BED12` (`emrys.stage.convert_GTF_to_BED12.v1`, historical
alias `00b`). Its current public assets are:

- `emrys convert gtf-to-bed12`, implemented by the private
  [`converter.py`](converter.py) module;
- `emrys validate bed12`, implemented by the private
  [`validator.py`](validator.py) module; and
- the mirrored [producer](../../../../tests/stages/gtf_to_bed12/test_gtf_to_bed12.py),
  and [validator](../../../../tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py)
  tests.

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Producer

From the repository root, invoke the producer through the installed repository
interpreter:

```bash
emrys convert gtf-to-bed12 \
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
emrys validate bed12 \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv
```

After inspecting the dry-run evidence, create the output parent and add
`--execute` to publish the report. From another working directory, use the
absolute installed interpreter plus explicit absolute input and output paths.

## Diagnostics, recovery, and evidence

Inspect whole-Run application and scheduler streams, the final BED, and its
transaction-residue paths together. Preserve ambiguous or foreign residue; do
not delete or replace it merely because a local test characterizes the state.
The next safe local action for an existing BED is the validator dry run above
with the exact source GTF. Recovery or replacement of runtime artifacts remains
an explicit operator decision.

Run the owner-focused local tests with:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/gtf_to_bed12/test_gtf_to_bed12.py \
  tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py
```

The artifact index records the producer's final path while preserving its
implementation evidence identity and byte hash. See
[`CONTRACT.md`](CONTRACT.md) for the full behavior contract. Available
fixture/mock and coverage evidence is local only; it is not runtime, scheduler,
production, scientific-review, or biological proof.
