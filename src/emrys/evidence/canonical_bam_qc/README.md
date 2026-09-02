# `collect_canonical_BAM_QC_evidence` owner

Native owner of `emrys.evidence.collect_canonical_BAM_QC_evidence.v1`
(historical `02b`). [`CONTRACT.md`](CONTRACT.md) owns exact behavior and
evidence meaning.

## Entry points

- producer: [`step_02b_bam_qc.sh`](step_02b_bam_qc.sh)
- validator: grouped route `emrys validate canonical-bam-qc`,
  implemented by private [`validator.py`](validator.py)

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Producer dry-run requires the BAM, an admitted adjacent BAI, and `samtools` on
`PATH`; it writes nothing:

```bash
src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam
```

The orchestration-safe invocation binds `samtools` with `--samtools-bin` and adds
`--no-clobber --execute`. That mode hashes the BAM/BAI pair, stages both
streams behind one per-sample owned lock, requires both nonempty, rechecks the
inputs, refuses a pre-existing or newly appeared final, and publishes the pair.
Publication is create-exclusive and retains staging inode anchors until the
complete pair is verified.
Execute without `--no-clobber` preserves the historical direct-write route.
The workflow verified record, not either native text file, binds the evidence
to the wider run and tool-version context.

Validator dry-run:

```bash
emrys validate canonical-bam-qc \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. The private validator is not a
direct repository entry point. Validator exit `0` means the report rendered
or published; rows may still have `status=fail`. This remains a non-gating
evidence branch.

## Diagnose and verify

Preserve both evidence files, unrelated directory bytes, whole-Run application
and scheduler streams, and job identity before deciding attempt ownership. Do
not delete, adopt, or retry because one file looks current or scheduler exit is
zero.

```bash
bash tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh
.venv/bin/python -m pytest -q \
  tests/evidence/canonical_bam_qc/test_validate_step_02b_bam_qc.py
```

Local fixture/mock evidence is not real samtools, scheduler, cluster,
production, scientific-review, or biological proof.
