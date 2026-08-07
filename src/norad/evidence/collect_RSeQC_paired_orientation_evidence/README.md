# `collect_RSeQC_paired_orientation_evidence` owner

This directory is the implemented native owner for semantic evidence operation
`collect_RSeQC_paired_orientation_evidence`
(`norad.evidence.collect_RSeQC_paired_orientation_evidence.v1`, historical
alias `03`). Its public assets are:

- [`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh),
  the mode-`0644` Bash producer;
- [`validate_step_03_rseqc_orientation.py`](validate_step_03_rseqc_orientation.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_03_infer_strandedness_and_orientation.slurm`](step_03_infer_strandedness_and_orientation.slurm),
  the mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/evidence/collect_RSeQC_paired_orientation_evidence/test_step_03_infer_strandedness_and_orientation.sh)
  and [validator](../../../../tests/evidence/collect_RSeQC_paired_orientation_evidence/test_validate_step_03_rseqc_orientation.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

The producer requires an explicit sample identifier, BAM, adjacent BAM index,
BED12 annotation, output directory, and executable RSeQC
`infer_experiment.py`. Invoke the mode-`0644` file through Bash. From the
repository root, this is a complete dry run:

```bash
bash src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bed12 refs/novogene_ref/genome.bed \
  --output-dir results/qc/strandedness \
  --infer-experiment-bin .venv/bin/infer_experiment.py
```

Dry-run validates the BAM, either admitted BAI name, BED12, and selected
executable and prints the exact RSeQC command. It creates neither the output
directory nor the native report. After inspection, add `--execute`:

```bash
bash src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bed12 refs/novogene_ref/genome.bed \
  --output-dir results/qc/strandedness \
  --infer-experiment-bin .venv/bin/infer_experiment.py \
  --execute
```

From another working directory, make the Bash script, BAM, BED12, output, and
RSeQC executable paths absolute:

```bash
bash /absolute/path/to/norad/src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam /absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bed12 /absolute/refs/novogene_ref/genome.bed \
  --output-dir /absolute/results/qc/strandedness \
  --infer-experiment-bin /absolute/path/to/norad/.venv/bin/infer_experiment.py
```

Without `--infer-experiment-bin`, selection first checks
`.venv/bin/infer_experiment.py` relative to the invocation CWD and otherwise
resolves `infer_experiment.py` through `PATH`. That default does not follow the
checkout when invoked elsewhere.

RSeQC stdout is redirected directly to
`<output-dir>/<sample-id>.infer_experiment.txt`. There is no lock, stage,
backup, no-clobber rule, receipt, stable-input recheck, or rollback. A child
exit `42` can replace a predecessor with partial stdout; an exit-`0` empty
result makes the producer exit `1` after truncating the predecessor to zero
bytes. Any nonempty output, including a structurally malformed report, passes
the producer's only final check. These are characterized defects, not approved
publication or recovery behavior.

## Validator

Invoke the mode-`0644` validator through an explicit interpreter. Omitting
`--execute` renders the five rows without writing a report:

```bash
.venv/bin/python src/norad/evidence/collect_RSeQC_paired_orientation_evidence/validate_step_03_rseqc_orientation.py \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Repeating the same command
deterministically replaces the owned report only after the input is rechecked:

```bash
mkdir -p results/qc/validation/03
.venv/bin/python src/norad/evidence/collect_RSeQC_paired_orientation_evidence/validate_step_03_rseqc_orientation.py \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, use absolute interpreter, validator, input, and output paths
for dry-run, execute, and repeat. The validator imports neutral
[`validation/report.py`](../../libraries/validation/report.py); no package
identity, `PYTHONPATH` change, wrapper, or compatibility import is supported.

Validator exit `0` means the evidence was validly rendered or published; one
or more rows may still have `status=fail`. Unsafe or unreadable input, invalid
arguments, a stable-input mismatch after rendering, or unsafe publication
exits `2` without a new report and preserves a valid predecessor when one
exists. Producer exit `0` therefore does not imply validator pass.

## Scheduler and demos

Submit the exact final mode-`0644` job from the checkout. Bind its six public
overrides—`SAMPLE_ID`, `BAM`, `BED12`, `OUTPUT_DIR`,
`INFER_EXPERIMENT_BIN`, and `EXECUTE`—without editing the tracked wrapper:

```bash
cd /absolute/path/to/norad
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam,BED12=/absolute/refs/novogene_ref/genome.bed,OUTPUT_DIR=/absolute/results/qc/strandedness,INFER_EXPERIMENT_BIN=/absolute/path/to/norad/.venv/bin/infer_experiment.py \
  src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.slurm
```

Change only `EXECUTE=1` after dry-run evidence is accepted. Slurm supplies
`SLURM_SUBMIT_DIR`; the local fallback is the wrapper's current CWD. The
wrapper exports `/tmp`, optionally sources `.venv/bin/activate`, prefers the
repository `.venv` RSeQC executable and otherwise delegates its command name
through `PATH`, and tolerates `module list` diagnostics. Dry-run creates
`logs/` but no scientific output. Bash `3.2` can fail while expanding the
empty dry-run argument array before producer delegation. In execute mode, a
zero-exit child that emits nothing can rediscover a stale nonempty named report
and let the wrapper succeed. Preserve those states; do not interpret wrapper
success as current evidence.

`make demo-step03-dry-run` and `make demo-step03` call `sbatch` with local
defaults and create `logs/`. Test coverage uses local mocks. Neither target is
proof of real scheduler, module, cluster, or RSeQC execution.

## Diagnostics, evidence meaning, and recovery

Before retry, cleanup, or same-name reuse, preserve the native report,
unrelated directory files, producer stdout/stderr, scheduler stdout/stderr,
job ID/accounting and logs, selected executable and path, BAM plus admitted
BAI, and BED12. There is no producer lock, stage, backup, receipt, or recovery
artifact to inspect. Follow the
[common recovery rules](../../../../docs/operations/TROUBLESHOOTING.md).
Git rollback changes tracked implementation only; it never recovers, removes,
or authenticates runtime evidence.

The three fractions are non-gating mechanical paired-read orientation
evidence. They do not establish transcript strand, biological sense/antisense,
an approved forward/reverse mapping, or a sample-manifest `strandedness`
policy. Historical operational observations remain separate from migration
evidence.

Focused local protection is:

```bash
bash tests/evidence/collect_RSeQC_paired_orientation_evidence/test_step_03_infer_strandedness_and_orientation.sh
.venv/bin/python -m pytest -q \
  tests/evidence/collect_RSeQC_paired_orientation_evidence/test_validate_step_03_rseqc_orientation.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_03_infer_strandedness_and_orientation
```

Current behavior and evidence limits are owned by [`CONTRACT.md`](CONTRACT.md). The owner is locally fixture/mock and guarded-R tested; this does not establish new real-RSeQC, scheduler, cluster, production, scientific-review, or biological proof.
