# `collect_RSeQC_paired_orientation_evidence` owner

Native owner of `emrys.evidence.collect_RSeQC_paired_orientation_evidence.v1`
(historical `03`). [`CONTRACT.md`](CONTRACT.md) owns exact behavior and the
mechanical-evidence boundary.

## Entry points

- producer: [`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh)
- validator: grouped route `emrys validate rseqc-orientation`,
  implemented by private [`validator.py`](validator.py)

The shell producer remains a repository-path interface. `validator.py` is not
a direct repository entrypoint. For Slurm execution, use the complete immutable
Run through `emrys run` or `emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Invoke the mode-`0644` producer through Bash. Dry-run writes nothing:

```bash
bash src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bed12 refs/novogene_ref/genome.bed \
  --output-dir results/qc/strandedness \
  --infer-experiment-bin .venv/bin/infer_experiment.py
```

The orchestration-safe invocation adds `--no-clobber --execute`. That mode hashes
the BAM, admitted BAI, and BED12, captures RSeQC stdout to a run-token temporary
file behind a per-sample owned lock, requires nonempty output, rechecks all
three inputs, refuses an existing or newly appeared final, and publishes
create-exclusively with an ownership anchor. Execute without `--no-clobber`
preserves the historical direct-write
route. The native report is evidence, not an attempt receipt.

Validator dry-run:

```bash
emrys validate rseqc-orientation \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Exit `0` means rendering or
publication succeeded; a row may still fail.

## Diagnose and verify

Preserve report, surrounding files, streams, job/accounting identity, selected
executable, BAM/BAI, and BED12 before recovery. The three fractions are
non-gating mechanical orientation evidence, not transcript strand,
sense/antisense, or approved manifest policy.

```bash
bash tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh
.venv/bin/python -m pytest -q \
  tests/evidence/rseqc_orientation/test_validate_step_03_rseqc_orientation.py
```

This is local fixture/mock and guarded-R evidence only.
