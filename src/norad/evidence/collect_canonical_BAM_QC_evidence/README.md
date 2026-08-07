# `collect_canonical_BAM_QC_evidence` owner

This directory is the implemented native owner for semantic evidence operation
`collect_canonical_BAM_QC_evidence`
(`norad.evidence.collect_canonical_BAM_QC_evidence.v1`, historical alias
`02b`). Its public assets are:

- [`step_02b_bam_qc.sh`](step_02b_bam_qc.sh), the mode-`0755` producer;
- [`validate_step_02b_bam_qc.py`](validate_step_02b_bam_qc.py), the
  mode-`0644` explicit-interpreter validator;
- [`step_02b_bam_qc.slurm`](step_02b_bam_qc.slurm), the intentionally
  mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh)
  and [validator](../../../../tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

The producer requires a BAM plus either adjacent `<bam>.bai` or stem `.bai`
and resolves `samtools` only from `PATH`. From the repository root, direct and
explicit-Bash dry runs are supported:

```bash
src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam

bash src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam
```

Dry-run invokes no samtools command but does create the requested output
directory. After inspecting the printed commands, add `--execute`:

```bash
src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam \
  --execute
```

From another working directory, make the producer, BAM, and output directory
paths absolute. The selected process still supplies samtools through `PATH`:

```bash
/absolute/path/to/norad/src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam /absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir /absolute/results/qc/bam
```

The producer writes quickcheck and flagstat streams directly to final paths.
It has no lock, stage, backup, receipt, stable-input recheck, rollback, or
complete-set validation. A quickcheck child exit `42` becomes producer exit
`1`, replaces an existing quickcheck file with the combined child diagnostic,
and leaves an older flagstat sibling untouched. A flagstat exit `43` follows a
new exact quickcheck PASS marker, replaces an older flagstat with partial child
stdout, and exposes the child diagnostic on stderr. These mixed-attempt states
are characterized defects, not approved recovery or publication behavior.

## Validator

Invoke the mode-`0644` validator through an explicit interpreter. Omitting
`--execute` is the no-write dry run:

```bash
.venv/bin/python src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv
```

After inspecting the five printed rows, create the output parent and add
`--execute`. Repeating the same command deterministically replaces the owned
report after both inputs are rechecked:

```bash
mkdir -p results/qc/validation/02b
.venv/bin/python src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, use absolute interpreter, validator, input, and output
paths. Dry-run, execute, and repeat leave no invocation-directory residue.
The validator imports neutral
[`validation/report.py`](../../libraries/validation/report.py); no package
identity, `PYTHONPATH` change, wrapper, or compatibility import is supported.

Producer exit `0` does not imply a passing validation row. In particular, a
nonempty stream from a zero-exit quickcheck is successful producer output but
fails the validator's exact-marker check. Validator exit `0` means the report
was validly rendered and published; it can contain `status=fail` evidence
rows. Step `02b` remains a non-gating evidence branch.

## Scheduler entry point

Submit the exact final job from the checkout. Slurm must provide
`SLURM_SUBMIT_DIR`; the wrapper changes to it before resolving its relative
inputs and child path. Bind the sample, BAM, output directory, and execution
mode explicitly:

```bash
cd /absolute/path/to/norad
SAMPLE_ID=ABE_EV_2 \
BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
OUTPUT_DIR=/absolute/results/qc/bam \
EXECUTE=0 \
  sbatch src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm

SAMPLE_ID=ABE_EV_2 \
BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
OUTPUT_DIR=/absolute/results/qc/bam \
EXECUTE=1 \
  sbatch src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm
```

The wrapper forces `TMPDIR=/tmp`, creates `logs/` and the output directory,
strictly loads samtools `1.19.2`, and tolerates diagnostics only from
`module list`. Bash `3.2` can fail while expanding the empty dry-run argument
array before producer delegation. After execute, the wrapper checks only that
both named files exist. An exit-`0` child that emitted nothing can therefore
rediscover stale predecessors and let the job succeed. Local mocked coverage
does not prove real submission, module, scheduler, or cluster behavior.

## Diagnostics, recovery, and evidence

For any producer or wrapper fault, preserve both evidence files, unrelated
files in the directory, producer stdout/stderr, scheduler stdout/stderr, and
job/accounting identity before deciding whether a file belongs to the current
attempt. There may be no lock, stage, backup, receipt, or recovery marker to
inspect. Do not delete, adopt, or retry the same names merely because one file
looks current or the scheduler returned zero. Follow the
[common recovery rules](../../../../docs/operations/TROUBLESHOOTING.md).

Focused local protection is:

```bash
bash tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh
.venv/bin/python -m pytest -q \
  tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_02b_bam_qc
```

Current behavior and evidence limits are owned by [`CONTRACT.md`](CONTRACT.md). The owner is locally fixture/mock tested; this does not establish new real-samtools, scheduler, cluster, production, scientific-review, or biological proof.
