# `partition_BAM_by_mechanical_read_orientation` owner

Native owner of `emrys.stage.partition_BAM_by_mechanical_read_orientation.v1`
(historical `06`). [`CONTRACT.md`](CONTRACT.md) owns exact inputs, five-output
transaction, defects, recovery, and mechanical-evidence semantics. The
lowercase directory is the physical owner; the semantic identity, mechanical
labels, artifact names, and historical alias do not change with that layout.

## Entry points

- private workflow producer: [`producer.py`](producer.py)
- validator: grouped route `python -I -m emrys validate mechanical-orientation`,
  implemented by private [`validator.py`](validator.py)

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Run this owner only through the immutable Project/Analysis Run journey. The
private producer has one production mode: an admitted runtime supplies an
absolute `samtools` path, and the task executes a create-absent transaction.
It does not expose the retired standalone dry-run or replace-existing modes.
`FWD_like` combines flags 99 and 147; `REV_like` combines 83 and 163. These are
mechanical groups, not transcript strand, strandedness, sense, or antisense,
and reads may remain unassigned. The counts TSV remains native QC evidence,
not a receipt.

Validator dry-run:

```bash
.venv/bin/python -I -m emrys validate mechanical-orientation \
  --scope-id ABE_EV_2 \
  --fwd-bam results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam \
  --fwd-bai results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam.bai \
  --rev-bam results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam \
  --rev-bai results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam.bai \
  --counts results/qc/orientation/ABE_EV_2.orientation_counts.tsv \
  --output results/qc/validation/06/ABE_EV_2.validation.tsv
```

Create the parent and add `--execute`. Exit `0` means five rows rendered or
published; rows may fail. The validator checks table arithmetic and container
magic, not BAM quickcheck, BAM/BAI correspondence, flags, sort, or read groups.
Do not execute private `validator.py` directly, add `PYTHONPATH`, or restore the
retired validator path to bypass package selection.

## Diagnose and verify

Preserve all finals, scratch, lock, input pair, streams, job identity,
tool version, and unrelated bytes. Do not combine attempts, delete a foreign
lock, trust the counts file as a receipt, or reuse ambiguous paths.

```bash
.venv/bin/python -m pytest -q tests/stages/mechanical_orientation
```

This is local fixture/fake-tool evidence only.
