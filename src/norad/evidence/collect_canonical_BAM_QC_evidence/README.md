# `collect_canonical_BAM_QC_evidence` owner

Native owner of `norad.evidence.collect_canonical_BAM_QC_evidence.v1`
(historical `02b`). [`CONTRACT.md`](CONTRACT.md) owns exact behavior and
evidence meaning.

## Entry points

- producer: [`step_02b_bam_qc.sh`](step_02b_bam_qc.sh)
- validator: [`validate_step_02b_bam_qc.py`](validate_step_02b_bam_qc.py)
- scheduler: [`step_02b_bam_qc.slurm`](step_02b_bam_qc.slurm)

## Operate

Producer dry-run requires the BAM, an admitted adjacent BAI, and `samtools` on
`PATH`; it creates the output directory:

```bash
src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam
```

Add `--execute` after inspection. Quickcheck and flagstat write directly to
final names without lock, staging, backup, receipt, stable-input recheck,
rollback, or complete-set validation; mixed-attempt files can remain.

Validator dry-run:

```bash
.venv/bin/python src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Validator exit `0` means the
report rendered or published; rows may still have `status=fail`. This remains
a non-gating evidence branch.

```bash
cd /absolute/path/to/norad
SAMPLE_ID=ABE_EV_2 BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
OUTPUT_DIR=/absolute/results/qc/bam EXECUTE=0 \
  sbatch src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm
```

Change only `EXECUTE=1` after dry-run review. The wrapper strictly loads
samtools `1.19.2` and checks only that both named files exist; stale files can
make a zero-output child look successful.

## Diagnose and verify

Preserve both evidence files, unrelated directory bytes, producer/scheduler
streams, and job identity before deciding attempt ownership. Do not delete,
adopt, or retry because one file looks current or scheduler exit is zero.

```bash
bash tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh
.venv/bin/python -m pytest -q \
  tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_02b_bam_qc
```

Local fixture/mock evidence is not real samtools, scheduler, cluster,
production, scientific-review, or biological proof.
