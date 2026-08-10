# `mark_BAM_duplicates_with_Picard` owner

Native owner of `norad.stage.mark_BAM_duplicates_with_Picard.v1` (historical
`04`). [`CONTRACT.md`](CONTRACT.md) owns exact transaction, defect, recovery,
and evidence semantics.

## Entry points

- producer: [`step_04_mark_duplicates.sh`](step_04_mark_duplicates.sh)
- validator: [`validate_step_04_mark_duplicates.py`](validate_step_04_mark_duplicates.py)
- scheduler: [`step_04_mark_duplicates.slurm`](step_04_mark_duplicates.slurm)

## Operate

Invoke the mode-`0644` producer through Bash. This is a no-write dry run:

```bash
TMPDIR=/tmp bash src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/markdup/ABE_EV_2 \
  --metrics-dir results/qc/markdup \
  --picard-jar /absolute/path/to/picard.jar \
  --java-bin /absolute/path/to/java \
  --samtools-bin /absolute/path/to/samtools
```

Add `--execute` after inspection. BAM, metrics, and BAI write to final names
without lock, stage, backup, no-clobber, stable-input recheck, receipt,
rollback, or all-or-none publication; mixed attempts can remain.

Validator dry-run:

```bash
.venv/bin/python src/norad/stages/mark_BAM_duplicates_with_Picard/validate_step_04_mark_duplicates.py \
  --scope-id ABE_EV_2 \
  --bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --bai results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai \
  --metrics results/qc/markdup/ABE_EV_2.markdup.metrics.txt \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/04/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Exit `0` means valid rendering or
publication; rows may still fail.

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,INPUT_BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam,OUTPUT_DIR=/absolute/results/markdup/ABE_EV_2,METRICS_DIR=/absolute/results/qc/markdup \
  src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.slurm
```

Change only `EXECUTE=1` after review. The wrapper loads Picard `3.1.1` and
samtools `1.19.2`, enforces Java 17, and checks only the named final files;
stale finals can produce false success.

## Diagnose and verify

Before recovery, preserve the triplet, input pair, all streams and job data,
selected tools/versions, `TMPDIR`, checkout, and unrelated files. Rule out Step
`05` readers. Use an isolated destination for an authorized retry; do not adopt
or delete a mixed final set.

```bash
bash tests/stages/mark_BAM_duplicates_with_Picard/test_step_04_mark_duplicates.sh
.venv/bin/python -m pytest -q \
  tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_04_mark_duplicates
```

This is local fixture/mock evidence only, not real Picard/Java/samtools,
scheduler, cluster, production, scientific-review, or biological proof.
