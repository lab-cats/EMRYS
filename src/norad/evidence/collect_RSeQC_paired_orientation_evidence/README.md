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
for dry-run, execute, and repeat. The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py); no package
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
[Step `03` troubleshooting route](../../../../docs/operations/TROUBLESHOOTING.md#step-03-producer-or-wrapper-leaves-a-partial-empty-or-stale-report).
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

Published old-path baseline `88f4994` froze direct-final partial/empty
replacement, malformed-nonempty success, arbitrary-CWD, stable-input,
virtualenv/PATH, dry-run-log, and stale-output behavior. Executable checkpoint
`24ed9b1` moved exactly five files and updated nine callers/harnesses. Final
producer mode/bytes/lines/SHA-256 is `0644` / `6,857` / `209` /
`01aa11cc60d9042ac541cfe445aec3e562a198a761c45449e82e96b7b9ab0784`;
validator is `0644` / `6,888` / `183` /
`d92eac61eeedec553b2541e446256836406f81c75e5fb8f6b12369f11bf58e67`;
and the mode-`0644` job is `4,121` bytes / `123` lines /
`d65fde6e7cb3d0ebccf76cb7101dffaf0ea42edfa49e1387d4cac3c3568d8c08`.

Final focused wiring passed `143` assertions. Serial coverage passed `1,120`
tests with `17` skips and one explicit documentation-validator deselection.
The moved validator measured `103/115` lines and `28/34` branches; global
coverage measured `9508/11677` lines and `3331/4756` branches. Every non-target
row remained exact and the standalone policy comparison passed.

The aggregate gate was not fully green. Static, shell, guarded-R, and report-
runtime lanes passed in the network-enabled rerun using the existing project
library without installing, restoring, deleting, or updating a dependency.
Python reported `1,120` passes and `17` skips before its sole documentation
assertion listed ten intentionally deferred migration links plus nine inherited
`UNREFINED` card-location findings. This documentation close repairs the ten
links; the inherited nine remain nonpassing. The initial sandboxed guarded-R
attempt stopped on Bioconductor DNS and retained the inherited malformed
`macos` warning. No result is represented as a green aggregate gate.

Artifact evidence changes only the final producer path and reviewed SHA-256
above. Rollback reverts the documentation close, executable checkpoint
`24ed9b1`, then test baseline `88f4994`; it never deletes runtime artifacts or
restores a legacy duplicate. See [`CONTRACT.md`](CONTRACT.md) and completed
[`MIG-03H`](../../../../docs/tasks/COMPLETED/MIG-03H-migrate-collect-rseqc-paired-orientation-evidence-owner.md)
for the complete boundary.

The migration added no wrapper, alias, symlink, package marker, public import
identity, descriptor, schema, transaction, receipt, recovery marker,
scheduler abstraction, strandedness classifier, or manifest mutation. Its
evidence ceiling is local fixture/mock, guarded local-R, pinned report-runtime,
and local coverage only—not new real RSeQC, scheduler, cluster, production,
scientific-review, or biological proof.
