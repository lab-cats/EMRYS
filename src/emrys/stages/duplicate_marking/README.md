# `mark_BAM_duplicates_with_Picard` owner

Native owner of `emrys.stage.mark_BAM_duplicates_with_Picard.v1` (historical
`04`). [`CONTRACT.md`](CONTRACT.md) owns exact transaction, defect, recovery,
and evidence semantics.

## Entry points

- producer: [`step_04_mark_duplicates.sh`](step_04_mark_duplicates.sh)
- grouped validator: `python -I -m emrys validate duplicate-marking`, implemented
  by private [`validator.py`](validator.py)

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Invoke the mode-`0644` producer through Bash. This is a no-write dry run:

```bash
TMPDIR=/tmp bash src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/markdup/ABE_EV_2 \
  --metrics-dir results/qc/markdup \
  --picard-jar /absolute/path/to/picard.jar \
  --java-bin /absolute/path/to/java \
  --samtools-bin /absolute/path/to/samtools
```

The orchestration-safe invocation adds `--no-clobber --execute`. That mode hashes
the input BAM/BAI and Picard jar, directs Picard and samtools to run-token
temporary paths, holds a per-sample owned lock, validates all three files,
rechecks those identities, refuses any existing or newly appeared final, and
publishes the triplet create-exclusively while retaining staging inode anchors
through validation. Execute without `--no-clobber` preserves the historical
direct-write route. Java and samtools executable paths are explicit; the
workflow attempt records their observed versions.

Validator dry-run:

```bash
.venv/bin/python -I -m emrys validate duplicate-marking \
  --scope-id ABE_EV_2 \
  --bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --bai results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai \
  --metrics results/qc/markdup/ABE_EV_2.markdup.metrics.txt \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/04/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Exit `0` means valid rendering or
publication; rows may still fail.

## Diagnose and verify

Before recovery, preserve the triplet, input pair, all streams and job data,
selected tools/versions, `TMPDIR`, checkout, and unrelated files. Rule out Step
`05` readers. Use an isolated destination for an authorized retry; do not adopt
or delete a mixed final set.

```bash
bash tests/stages/duplicate_marking/test_step_04_mark_duplicates.sh
.venv/bin/python -m pytest -q \
  tests/stages/duplicate_marking/test_validate_step_04_mark_duplicates.py
```

This is local fixture/mock evidence only, not real Picard/Java/samtools,
scheduler, cluster, production, scientific-review, or biological proof.
