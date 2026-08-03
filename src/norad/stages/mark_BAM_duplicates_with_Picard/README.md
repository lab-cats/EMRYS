# `mark_BAM_duplicates_with_Picard` owner

This directory is the implemented native owner for semantic stage
`mark_BAM_duplicates_with_Picard`
(`norad.stage.mark_BAM_duplicates_with_Picard.v1`, historical alias `04`). Its
public assets are:

- [`step_04_mark_duplicates.sh`](step_04_mark_duplicates.sh), the mode-`0644`
  Bash producer;
- [`validate_step_04_mark_duplicates.py`](validate_step_04_mark_duplicates.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_04_mark_duplicates.slurm`](step_04_mark_duplicates.slurm), the
  mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/mark_BAM_duplicates_with_Picard/test_step_04_mark_duplicates.sh)
  and [validator](../../../../tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

The producer requires a sample identifier, canonical BAM with the exact
adjacent `<bam>.bai`, output and metrics directories, a readable Picard jar,
Java, samtools, and an existing writable `TMPDIR`. Invoke the mode-`0644` file
through Bash. From the repository root, this is a complete no-write dry run:

```bash
TMPDIR=/tmp \
bash src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/markdup/ABE_EV_2 \
  --metrics-dir results/qc/markdup \
  --picard-jar /absolute/path/to/picard.jar \
  --java-bin /absolute/path/to/java \
  --samtools-bin /absolute/path/to/samtools
```

Dry-run validates all declared inputs and tools and prints the exact Picard,
quickcheck, and index commands. It creates neither output directory. After
inspection, repeat the command with `--execute`:

```bash
TMPDIR=/tmp \
bash src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/markdup/ABE_EV_2 \
  --metrics-dir results/qc/markdup \
  --picard-jar /absolute/path/to/picard.jar \
  --java-bin /absolute/path/to/java \
  --samtools-bin /absolute/path/to/samtools \
  --execute
```

From another working directory, make `TMPDIR`, producer, BAM, output,
metrics, Picard, Java, and samtools paths absolute. A command name without `/`
is resolved through `PATH`; a value containing `/` must exist and be
executable. The producer defaults Java to `java`, samtools to `samtools`, and
`TMPDIR` to `/tmp`, but an explicit absolute selection makes the execution
identity inspectable.

Picard writes the BAM and metrics directly to their final names with
`REMOVE_DUPLICATES=false`; samtools quickchecks the BAM and then writes its
index at the final name. There is no lock, stage, backup, no-clobber rule,
stable-input recheck, receipt, rollback, or all-or-none transaction. A Picard
failure can leave a new partial BAM and metrics with an older BAI; quickcheck
or index failure can leave another mixed triplet; the final nonempty check can
fail after new BAM/BAI publication; and admitted input mutation can go
undetected. These are characterized defects, not approved publication or
recovery behavior.

## Validator

Invoke the mode-`0644` validator with an explicit interpreter. Omitting
`--execute` renders five TSV rows to stdout and writes no report:

```bash
.venv/bin/python \
  src/norad/stages/mark_BAM_duplicates_with_Picard/validate_step_04_mark_duplicates.py \
  --scope-id ABE_EV_2 \
  --bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --bai results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai \
  --metrics results/qc/markdup/ABE_EV_2.markdup.metrics.txt \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/04/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Repeating the same command
deterministically replaces a valid owned report only after stable-input
revalidation:

```bash
mkdir -p results/qc/validation/04
.venv/bin/python \
  src/norad/stages/mark_BAM_duplicates_with_Picard/validate_step_04_mark_duplicates.py \
  --scope-id ABE_EV_2 \
  --bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --bai results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai \
  --metrics results/qc/markdup/ABE_EV_2.markdup.metrics.txt \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/04/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, use absolute interpreter, validator, BAM, BAI, metrics,
samtools, and output paths for dry-run, execute, and repeat. The validator
privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py) and
[`bam_validation.py`](../../libraries/bam_validation.py); no package identity,
public helper CLI, `PYTHONPATH`, wrapper, or compatibility import is supported.

Validator exit `0` means five rows were validly rendered or published; one or
more rows may still have `status=fail`. Unsafe input, a header-tool failure,
stable-input mismatch, or unsafe publication exits `2` without publishing a
new report and preserves a valid predecessor when one exists. Producer or
scheduler exit `0` therefore does not imply validator pass.

## Scheduler

SLURM opens declared log paths before the script body. Start in the checkout,
create `logs/`, and submit the exact final job. A dry-run submission is:

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,INPUT_BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam,OUTPUT_DIR=/absolute/results/markdup/ABE_EV_2,METRICS_DIR=/absolute/results/qc/markdup \
  src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.slurm
```

Change only `EXECUTE=1` after accepting the dry-run evidence. If needed, add
`JAVA_BIN_OVERRIDE=/absolute/path/to/java17`. The wrapper changes to
`SLURM_SUBMIT_DIR` with a current-CWD fallback, exports `/tmp`, loads Picard
`3.1.1` and samtools `1.19.2`, requires `PICARD`, selects Java from the
override, usable `$JAVA_HOME/bin/java`, then `PATH`, and rejects an actual
major version below 17. The delegated producer resolves samtools from `PATH`.
Module-list diagnostics are tolerated.

Scheduler dry-run can create `logs/` in the body but no BAM, BAI, or metrics.
On Bash `3.2`, expanding the empty dry-run argument array can abort before
delegation. A missing `JAVA_HOME` can also trigger the characterized unguarded
expansion after tool selection. In execute mode, a zero-exit child that creates
nothing can rediscover a stale nonempty three-file set and let the wrapper
succeed. Preserve these defects; wrapper success is not proof that the files
belong to the current attempt.

## Diagnostics, recovery, evidence, and rollback

Before retry, cleanup, or same-name reuse, preserve the exact BAM/BAI/metrics
bytes and metadata, canonical input pair, producer and scheduler streams,
scheduler job/accounting and logs, Picard jar, selected Java and actual version,
samtools path/version, `TMPDIR`, checkout, and unrelated directory files. Rule
out active downstream Step `05` or other readers. There are no producer lock,
stage, backup, receipt, or recovery artifacts whose absence proves clean state.
Use an isolated output/metrics destination for a separately authorized retry;
do not delete or adopt a mixed or stale final triplet as recovery. Follow the
[Step `04` troubleshooting route](../../../../docs/operations/TROUBLESHOOTING.md#step-04-producer-or-wrapper-leaves-a-partial-mixed-or-stale-output-triplet).
Git rollback changes tracked implementation only; it cannot recover, remove,
or authenticate runtime artifacts.

Focused local protection is:

```bash
bash tests/stages/mark_BAM_duplicates_with_Picard/test_step_04_mark_duplicates.sh
.venv/bin/python -m pytest -q \
  tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_04_mark_duplicates
```

Published producer, validator, and scheduler baselines are `de52e93`,
`3d73d52`, and `3e805ac`; executable checkpoint `803fcc4` moved exactly five
files and updated ten reviewed integration owners. Final producer mode/bytes/
lines/SHA-256 is `0644` / `7,232` / `241` /
`b845aa910ccabaf8799e000dc62e8939b0203c7848511524fadf51c79292eb2d`;
validator is `0644` / `10,275` / `277` /
`17a541e7b9d9822df5de0721747187621035f0dae7aaa0f1a35995f727bfb178`;
and the mode-`0644` job is `4,911` bytes / `161` lines /
`4e41c4cd7ee1ec36169797bfc4897968e38010e78aec35d16c6921dfd55217fc`.

The final direct shell suite, `9` validator tests, `18` selected scheduler
tests with `108` unrelated cases deselected, and `68` focused integration
assertions passed. Coverage passed `1,134` tests with `17` skips and one
explicit documentation-validator deselection. The moved validator measured
`146/155` lines and `35/42` branches; global coverage measured `9510/11677`
lines and `3333/4756` branches. Every non-target row remained exact and the
standalone comparison passed.

The aggregate gate was not fully green. Its first sandboxed attempt passed
static preflight and stopped when guarded R could not resolve Bioconductor
metadata, retaining the inherited malformed `macos` warning. The exact
network-enabled rerun used the existing project library and changed no
dependency. Static, shell, guarded-R, and report-runtime lanes passed. Python
ran `1,134` passes and `17` skips before its sole documentation assertion
listed ten intentionally deferred migration links plus nine inherited
`UNREFINED` locations. This close repairs the ten links; the inherited nine
remain nonpassing. No result is represented as a green aggregate gate.

Artifact evidence changes only the final producer path and reviewed hash.
Historical cluster and Picard metrics in the runbook remain historical; this
migration created no real Picard, Java, samtools, scheduler, cluster,
production, scientific-review, or biological evidence. Rollback reverts the
documentation close, executable checkpoint `803fcc4`, scheduler baseline
`3e805ac`, validator baseline `3d73d52`, then producer baseline `de52e93`; it
never alters runtime evidence. See [`CONTRACT.md`](CONTRACT.md) and completed
[`MIG-03I`](../../../../docs/tasks/COMPLETED/MIG-03I-migrate-mark-bam-duplicates-with-picard-owner.md)
for the complete boundary.

The migration added no wrapper, alias, symlink, package marker, public import
identity, descriptor, schema, transaction, receipt, recovery marker, scheduler
abstraction, duplicate-classification policy, or manifest mutation. Its
evidence ceiling is local fixtures/mocks, guarded local R, pinned report
runtime, and local coverage only.
