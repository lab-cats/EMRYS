# `construct_canonical_BAM` owner

This directory is the implemented native owner for semantic stage
`construct_canonical_BAM` (`norad.stage.construct_canonical_BAM.v1`, historical
alias `02`). Its current public assets are:

- [`step_02_sort_index_bam.sh`](step_02_sort_index_bam.sh), the mode-`0755`
  shell producer;
- [`validate_step_02_canonical_bam.py`](validate_step_02_canonical_bam.py), the
  mode-`0644` explicit-interpreter validator;
- [`step_02_sort_index_bam.slurm`](step_02_sort_index_bam.slurm), the
  intentionally mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/construct_canonical_BAM/test_step_02_sort_index_bam.sh)
  and [validator](../../../../tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

The producer resolves `samtools` only from `PATH`. From the repository root,
both the direct and explicit-Bash forms are dry-run by default:

```bash
src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8

bash src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8
```

Dry-run verifies the input and that `samtools` is on `PATH`, but invokes no
samtools command and creates no output directory, lock, scratch path, backup,
BAM, or BAI. After inspecting the printed plan, execute through either form:

```bash
src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8 \
  --execute

bash src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8 \
  --execute
```

From another working directory, use absolute producer, input, and output
paths. The samtools executable still comes only from that process's `PATH`:

```bash
/absolute/path/to/norad/src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment /absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir /absolute/results/bam/ABE_EV_2 \
  --threads 8
```

The producer stages and validates a replacement pair before backing up and
publishing over a complete predecessor. Its rollback is not failure-atomic.
If final BAI publication fails and restoration of the prior BAM also fails,
the characterized result is nonzero with only the prior BAI retained at its
canonical path. The canonical BAM, backups, owned lock, and run-token scratch
can all be absent. This lockless partial pair and lost prior BAM are an
ambiguous/data-loss defect, not a successful rollback or cleanup authority.

## Validator

Invoke the mode-`0644` validator through an explicit interpreter and provide an
explicit samtools executable. Omitting `--execute` is the no-write dry run:

```bash
.venv/bin/python src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv
```

After inspecting the exact five rows, create the output parent and add
`--execute`. Repeating the same command deterministically replaces the owned
report after the inputs are rechecked:

```bash
mkdir -p results/qc/validation/02
.venv/bin/python src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv \
  --execute

.venv/bin/python src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, make the interpreter, validator, BAM, BAI, samtools, and
output paths absolute. Dry-run, execute, and repeat are supported from that
location; validation creates no invocation-directory residue.

The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py) and
[`bam_validation.py`](../../libraries/bam_validation.py). The latter owns only
`run_tool` and `parse_header` and is shared with the final Step `04` and flat
Step `05` validators. An exact-loader diagnostic is a checkout-integrity failure:
inspect the named private file and checkout. Do not add `PYTHONPATH`, install a
package, invoke the helper as a CLI, or restore a legacy Step `02` path.

## Scheduler entry point

The wrapper delegates relative to the caller's working directory and ignores
`SLURM_SUBMIT_DIR`. Change to the checkout, create `logs/`, and submit the exact
final job. Omitting `EXECUTE` keeps the default dry run:

```bash
cd /absolute/path/to/norad
mkdir -p logs
SAMPLE_ID=ABE_EV_2 \
INPUT_ALIGNMENT=/absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
OUTPUT_DIR=/absolute/results/bam/ABE_EV_2 \
THREADS=8 \
EXECUTE=0 \
  sbatch src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm
```

Real work changes only the explicit execute binding:

```bash
cd /absolute/path/to/norad
mkdir -p logs
SAMPLE_ID=ABE_EV_2 \
INPUT_ALIGNMENT=/absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
OUTPUT_DIR=/absolute/results/bam/ABE_EV_2 \
THREADS=8 \
EXECUTE=1 \
  sbatch src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm
```

The wrapper forces `TMPDIR=/tmp`, creates `logs/` and the output directory even
in dry-run, strictly loads samtools `1.19.2`, and tolerates diagnostics only
from its two `module list` calls. Bash `3.2` can fail while expanding the empty
dry-run argument array before producer delegation. Its post-execute check tests
only that the two output paths are files. Local mocked coverage does not prove
real submission, scheduler, module, or cluster behavior.

## Diagnostics, recovery, and evidence

For a producer or scheduler fault, preserve the complete pair directory,
producer and scheduler stdout/stderr, any run-token temporary and backup paths,
and the exact bytes of every final and backup path before a separately
authorized recovery decision. In particular, a prior-BAI-only state can remain
without a BAM, lock, backup, receipt, or recovery marker. Absence of any of
those paths does not authorize deletion, adoption, or retry. The exact response
route is in [troubleshooting](../../../../docs/operations/TROUBLESHOOTING.md#step-02-canonical-bam-rollback-leaves-a-prior-bai-only-lockless-pair).

Run the focused local migration surface with:

```bash
bash tests/stages/construct_canonical_BAM/test_step_02_sort_index_bam.sh
.venv/bin/python -m pytest -q \
  tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py \
  tests/libraries/test_bam_validation.py \
  tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py \
  tests/test_validate_step_05_split_ncigar.py \
  tests/test_slurm_wrapper_contracts.py
```

The helper boundary passed `40` affected validator tests. The final moved
validator/helper set passed `31` tests, the Step `02` scheduler subset passed
`9`, and the moved shell suite passed including the persistent restore-failure
oracle. Deterministic serial coverage passed `1,109` tests with `17` skips and
one explicit documentation-validator deselection. It measured Step `02` at
`137/149` lines and `32/42` branches, Step `04` at `144/155` and `33/42`, Step
`05` at `138/149` and `31/38`, the helper at `12/12`, and the global surface at
`9504/11677` lines and `3327/4756` branches. Every non-target row stayed exact
and the standalone policy comparison passed.

The aggregate gate was not fully green. Static preflight, shell contracts,
guarded R, and report runtime passed; Python reported `1,109` passes and `17`
skips before its sole failure identified ten intentionally deferred MIG-03F
documentation links plus nine inherited `UNREFINED` card-location findings.
This close repairs the ten migration links; the nine inherited findings remain
nonpassing. No result is represented as a green aggregate gate.

The artifact index records the producer's final path and reviewed SHA-256
`602c9b6f71d7fb38533e29e294fcdd3685339614daa6efa264ba413669dd0cd3`
without changing public artifact identities, schemas, contents, ordering, or
consumers. Rollback reverts this documentation close before executable/test
checkpoint `13a2748`, then helper checkpoint `4726ad1`, then the published
pre-card parent `fa79883`; preserve runtime artifacts and restore no duplicate
legacy source.

The migration added no wrapper, symlink, package marker, public import
identity, descriptor, schema, receipt, recovery marker, scheduler abstraction,
or transaction redesign. See [`CONTRACT.md`](CONTRACT.md) for the full current
behavior and characterized defects. Migration evidence is local fixture/mock,
guarded local-R, pinned report-runtime, and local coverage evidence only; it is
not real samtools runtime, scheduler, cluster, production, scientific-review,
or biological proof.
