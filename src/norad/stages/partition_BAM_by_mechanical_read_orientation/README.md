# `partition_BAM_by_mechanical_read_orientation` owner

This directory is the implemented native owner for semantic stage
`partition_BAM_by_mechanical_read_orientation`
(`norad.stage.partition_BAM_by_mechanical_read_orientation.v1`, historical
alias `06`). Its public assets are:

- [`step_06_split_bam_by_read_orientation.sh`](step_06_split_bam_by_read_orientation.sh),
  the mode-`0755` directly executable Bash producer;
- [`validate_step_06_orientation_outputs.py`](validate_step_06_orientation_outputs.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_06_split_bam_by_read_orientation.slurm`](step_06_split_bam_by_read_orientation.slurm),
  the mode-`0755` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/partition_BAM_by_mechanical_read_orientation/test_step_06_split_bam_by_read_orientation.sh)
  and [validator](../../../../tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer and mechanical meaning

The producer requires a sample identifier, one Step `05` split-N-cigar BAM
with its exact adjacent `<bam>.bai`, distinct output and QC directory choices,
a positive thread count, and samtools. `FWD_like` combines `samtools view -f
99` and `-f 147`; `REV_like` combines `-f 83` and `-f 163`. Because `-f`
permits additional bits, these are mechanical read-orientation groups, not
transcript strand, library strandedness, sense, or antisense labels. Reads may
remain unassigned.

From the repository root, this is a complete no-write dry run:

```bash
src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir results/orientation/ABE_EV_2 \
  --qc-dir results/qc/orientation \
  --threads 1 \
  --samtools-bin /absolute/path/to/samtools
```

Direct dry-run validates the BAM, exact BAI, positive threads, and samtools
resolution; prints the two-directory lock, run-token scratch, backup, command,
validation, publication, and rollback plans; invokes no samtools command; and
creates no directory. After inspecting that plan, repeat the command with
`--execute`.

From another working directory, make the producer, BAM, output directory, QC
directory, and samtools paths absolute:

```bash
/absolute/path/to/norad/src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam /absolute/results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir /absolute/results/orientation/ABE_EV_2 \
  --qc-dir /absolute/results/qc/orientation \
  --threads 1 \
  --samtools-bin /absolute/path/to/samtools
```

Samtools resolves from `--samtools-bin`, then `SAMTOOLS_BIN_OVERRIDE`, then
`PATH`; a value containing `/` must exist and be executable. Execute mode
invokes the selected version command, writes four flag-filter BAMs, merges the
two groups, indexes both merged BAMs, and produces:

```text
<output-dir>/<sample>.FWD_like.bam
<output-dir>/<sample>.FWD_like.bam.bai
<output-dir>/<sample>.REV_like.bam
<output-dir>/<sample>.REV_like.bam.bai
<qc-dir>/<sample>.orientation_counts.tsv
```

The eleven-column count row records input, four flag, two merged, assigned,
and unassigned counts plus a six-decimal assigned fraction. The producer
requires nonempty input and merged groups, assigned count no greater than
input, temporary and final BAM quickcheck success, nonempty BAIs, and an all-
five-or-none predecessor. It publishes the four BAM/BAI files sequentially and
the counts TSV last, then revalidates all five final paths.

These checks do not prove biological orientation or current-attempt identity.
The producer does not reconcile each flag-subcount sum against its merged-BAM
count. It does not snapshot-recheck the input BAM/BAI. The counts TSV is a
native output, not a receipt. Restoration moves are best-effort, and cleanup
can erase backups after restoration failure. The lock is under the selected
output directory while counts may be in a shared QC directory, so two runs
with distinct output directories can both succeed and last-writer-replace one
shared counts path. These are characterized defects, not guarantees.

## Validator

Invoke the mode-`0644` validator with an explicit interpreter. It reads all
five declared inputs, prints five TSV rows plus its completion line, invokes no
samtools, and writes no report in dry-run mode:

```bash
.venv/bin/python \
  src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py \
  --scope-id ABE_EV_2 \
  --fwd-bam results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam \
  --fwd-bai results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam.bai \
  --rev-bam results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam \
  --rev-bai results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam.bai \
  --counts results/qc/orientation/ABE_EV_2.orientation_counts.tsv \
  --output results/qc/validation/06/ABE_EV_2.validation.tsv
```

Create the report parent and add `--execute` to publish. Repeating the same
command deterministically replaces a valid owned report only after all five
inputs pass stable-input revalidation:

```bash
mkdir -p results/qc/validation/06
.venv/bin/python \
  src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py \
  --scope-id ABE_EV_2 \
  --fwd-bam results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam \
  --fwd-bai results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam.bai \
  --rev-bam results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam \
  --rev-bai results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam.bai \
  --counts results/qc/orientation/ABE_EV_2.orientation_counts.tsv \
  --output results/qc/validation/06/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, make the interpreter, validator, four BAM/BAI inputs,
counts, and report paths absolute. Dry-run, execute, and repeat leave no
invocation-directory residue:

```bash
/absolute/path/to/norad/.venv/bin/python \
  /absolute/path/to/norad/src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py \
  --scope-id ABE_EV_2 \
  --fwd-bam /absolute/results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam \
  --fwd-bai /absolute/results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam.bai \
  --rev-bam /absolute/results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam \
  --rev-bai /absolute/results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam.bai \
  --counts /absolute/results/qc/orientation/ABE_EV_2.orientation_counts.tsv \
  --output /absolute/results/qc/validation/06/ABE_EV_2.validation.tsv
```

The validator checks container magic, exact count-table structure, both flag-
group sums, assigned/unassigned arithmetic, and the rounded fraction. Exit `0`
means five rows were rendered or published; one or more rows may still have
`status=fail`. It does not invoke samtools, quickcheck BAMs, recount records,
inspect flags, verify BAM/BAI correspondence, or validate sorting/read groups.
Unsafe input, a stable-input mismatch, private-owner integrity failure, or
unsafe publication exits `2` without a new report and preserves a valid
predecessor when one exists.

The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py), validates the
exact owner, and preserves foreign module-cache and `sys.path` state. No
package identity, installed command, wrapper, compatibility import, ambient
`PYTHONPATH`, or global path mutation is supported.

## Scheduler

SLURM opens declared log paths before the job body. Start in the checkout,
create `logs/`, and submit the exact final mode-`0755` job. The default is dry-
run:

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,INPUT_BAM=/absolute/results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam,OUTPUT_DIR=/absolute/results/orientation/ABE_EV_2,QC_DIR=/absolute/results/qc/orientation,THREADS=1 \
  src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.slurm
```

Change only `EXECUTE=1` after accepting the dry-run evidence. Use
`SAMTOOLS_BIN_OVERRIDE` for an explicit executable. The wrapper changes to
`SLURM_SUBMIT_DIR` with current-CWD fallback, exports `/tmp`, tolerates module
diagnostics and module-load failure, uses a fixed site samtools path unless
overridden, and invokes a version probe before delegation.

Scheduler dry-run differs from direct dry-run: `logs/` exists before `sbatch`,
the body also creates `logs/`, and module/version probes run before delegation.
The job requests one CPU while `THREADS` is independently configurable. Bash
`3.2` can fail on the empty dry-run argument array. Missing or nonexecutable
samtools is warning-only at the wrapper probe but rejected by the producer. In
execute mode, a zero-exit child that creates nothing can rediscover five stale
nonempty final files and let the wrapper succeed. Scheduler success is not
current-attempt, producer-validation, or independent-validator proof.

## Diagnostics, recovery, evidence, and rollback

Before cleanup, same-name retry, or recovery, preserve all five finals;
run-token filter/merged BAMs, BAIs, counts, and predecessor backups across both
output and QC directories; every relevant lock directory and owner file; the
input BAM/BAI; unrelated files; producer stdout/stderr; scheduler stdout/
stderr, job ID/accounting and logs; checkout and submit CWD; environment
overrides; thread count; and selected samtools path/version. Record expected
paths that are absent: absence does not prove a clean state or attempt
identity.

Rule out every active producer and
[`generate_partitioned_cohort_mpileup_VCFs`](../generate_partitioned_cohort_mpileup_VCFs/README.md)
reader. Never combine members
from different attempts, infer identity from counts or timestamps, remove a
foreign lock, reconstruct a missing file, or adopt stale wrapper success. A
separately authorized diagnostic retry must use both an isolated output
directory and an isolated QC directory. Git rollback changes tracked files
only; it cannot recover, delete, or authenticate runtime artifacts. Follow the
[`Step 06` recovery route](../../../../docs/operations/TROUBLESHOOTING.md#step-06-producer-or-wrapper-leaves-a-partial-rollback-failure-collision-or-stale-set).

Focused local protection is:

```bash
bash tests/stages/partition_BAM_by_mechanical_read_orientation/test_step_06_split_bam_by_read_orientation.sh
.venv/bin/python -m pytest -q \
  tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_06_split_bam_by_read_orientation
```

Current behavior, recovery states, and evidence limits are owned by [`CONTRACT.md`](CONTRACT.md). The owner is locally fixture/fake-tool tested; this does not establish new scheduler, cluster, production, scientific-review, or biological proof.
