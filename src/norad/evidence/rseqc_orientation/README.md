# `collect_RSeQC_paired_orientation_evidence` owner

Native owner of `norad.evidence.collect_RSeQC_paired_orientation_evidence.v1`
(historical `03`). [`CONTRACT.md`](CONTRACT.md) owns exact behavior and the
mechanical-evidence boundary.

## Entry points

- producer: [`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh)
- validator: grouped route `python -I -m norad validate rseqc-orientation`,
  implemented by private [`validator.py`](validator.py)
- scheduler: [`step_03_infer_strandedness_and_orientation.slurm`](step_03_infer_strandedness_and_orientation.slurm)

The shell producer and scheduler remain repository-path interfaces.
`validator.py` is not a direct repository entrypoint.

## Operate

Invoke the mode-`0644` producer through Bash. Dry-run writes nothing:

```bash
bash src/norad/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bed12 refs/novogene_ref/genome.bed \
  --output-dir results/qc/strandedness \
  --infer-experiment-bin .venv/bin/infer_experiment.py
```

Add `--execute` after inspection. RSeQC stdout writes directly to the final
report. There is no lock, stage, backup, receipt, stable-input recheck, or
rollback; failure can replace a predecessor with partial or empty output.

Validator dry-run:

```bash
.venv/bin/python -I -m norad validate rseqc-orientation \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Exit `0` means rendering or
publication succeeded; a row may still fail.

```bash
cd /absolute/path/to/norad
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam,BED12=/absolute/refs/genome.bed,OUTPUT_DIR=/absolute/results/qc/strandedness,INFER_EXPERIMENT_BIN=/absolute/path/to/norad/.venv/bin/infer_experiment.py \
  src/norad/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.slurm
```

Change only `EXECUTE=1` after review. Stale nonempty output can make a
zero-output child look successful.

## Diagnose and verify

Preserve report, surrounding files, streams, job/accounting identity, selected
executable, BAM/BAI, and BED12 before recovery. The three fractions are
non-gating mechanical orientation evidence, not transcript strand,
sense/antisense, or approved manifest policy.

```bash
bash tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh
.venv/bin/python -m pytest -q \
  tests/evidence/rseqc_orientation/test_validate_step_03_rseqc_orientation.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_03_infer_strandedness_and_orientation
```

This is local fixture/mock and guarded-R evidence only.
