# `align_RNA_reads_with_STAR` owner

This directory is the implemented native owner for semantic stage
`align_RNA_reads_with_STAR` (`norad.stage.align_RNA_reads_with_STAR.v1`,
historical alias `01`). Its current public assets are:

- [`step_01_star_align.sh`](step_01_star_align.sh), the mode-`0755` shell
  producer;
- [`validate_step_01_star_alignment.py`](validate_step_01_star_alignment.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_01_star_align.slurm`](step_01_star_align.slurm), the intentionally
  mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/align_RNA_reads_with_STAR/test_step_01_star_align.sh)
  and [validator](../../../../tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

From the repository root, invoke the producer directly or through Bash. Both
forms are dry-run by default:

```bash
src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh \
  --sample-id ABE_EV_2 \
  --r1-fastq data/ABE_EV_2_R1.fastq.gz \
  --r2-fastq data/ABE_EV_2_R2.fastq.gz \
  --star-index refs/novogene_star_index \
  --output-dir results/star/ABE_EV_2 \
  --threads 8

bash src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh \
  --sample-id ABE_EV_2 \
  --r1-fastq data/ABE_EV_2_R1.fastq.gz \
  --r2-fastq data/ABE_EV_2_R2.fastq.gz \
  --star-index refs/novogene_star_index \
  --output-dir results/star/ABE_EV_2 \
  --threads 8
```

The producer requires `STAR` on `PATH` even for dry-run, and dry-run creates
the declared output directory. Add `--execute` only after inspecting the
printed command. From another working directory, use the absolute checkout
path for the producer and explicit absolute FASTQ, index, and output paths.

STAR writes directly into the final output directory. A failed child can leave
that directory and any artifacts the real child created; there is no receipt,
lock, staging transaction, cleanup, no-clobber rule, or post-STAR validation.
Preserve partial or ambiguous output for inspection instead of treating the
characterized residue as safe to delete.

## Validator

Invoke the validator through an explicit interpreter. Omitting `--execute` is
the no-write dry run:

```bash
.venv/bin/python src/norad/stages/align_RNA_reads_with_STAR/validate_step_01_star_alignment.py \
  --scope-id ABE_EV_2 \
  --bam results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --log-final results/star/ABE_EV_2/ABE_EV_2.Log.final.out \
  --log-out results/star/ABE_EV_2/ABE_EV_2.Log.out \
  --log-progress results/star/ABE_EV_2/ABE_EV_2.Log.progress.out \
  --sj-out results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab \
  --output results/qc/validation/01/ABE_EV_2.validation.tsv
```

After inspecting the five structural checks, create the output parent and add
`--execute` to publish the report. From another working directory, use absolute
paths for the interpreter, validator, five inputs, and output. Validation does
not establish alignment correctness or repair STAR artifacts.

## Scheduler entry point

The job delegates by caller working directory, so submit only after changing to
the intended checkout:

```bash
cd <checkout>
sbatch src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm
```

`EXECUTE=0` is the default, but the default bindings create placeholder FASTQ
files and an index directory before producer dry-run. `EXECUTE=1` refuses those
placeholder bindings. Real work supplies all five overrides; threads come from
the scheduler allocation:

```bash
cd <checkout>
SAMPLE_ID=ABE_EV_2 \
R1_FASTQ=/absolute/data/ABE_EV_2_R1.fastq.gz \
R2_FASTQ=/absolute/data/ABE_EV_2_R2.fastq.gz \
STAR_INDEX=/absolute/refs/novogene_star_index \
OUTPUT_DIR=/absolute/results/star/ABE_EV_2 \
EXECUTE=1 \
  sbatch src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm
```

The wrapper strictly loads STAR `2.7.11b`, may redirect `TMPDIR`, and performs
no independent output validation. Mocked wrapper tests do not prove scheduler,
module, or cluster behavior.

## Diagnostics, recovery, and evidence

Inspect scheduler stdout/stderr, STAR's `Log.out`, `Log.progress.out`, and
`Log.final.out`, the coordinate-sorted BAM, and `SJ.out.tab` as one attempt.
The next safe local action for a complete-looking set is the validator dry run
above. Preserve partial artifacts and native logs before any separately
authorized rerun or rollback.

Run the focused local migration surface with:

```bash
bash tests/stages/align_RNA_reads_with_STAR/test_step_01_star_align.sh
.venv/bin/python -m pytest -q \
  tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py \
  tests/test_slurm_wrapper_contracts.py
```

The artifact index records the producer's final path and reviewed SHA-256
`718625e101a700b4da56b8e30249b1b42f8dea81546a763fc9db246be9a3edaf`
without changing public artifact identities or schemas. Rollback reverts the
documentation close before executable checkpoint `12f9be5`; repository history
restores the legacy layout without a duplicate or compatibility path.

The migration added no wrapper, symlink, package marker, import identity,
descriptor, schema, transaction, or scientific alignment policy. See
[`CONTRACT.md`](CONTRACT.md) for the full current behavior and characterized
defects. Migration evidence is local fixture/mock, guarded local-R, pinned
report-runtime, and local coverage evidence only; it is not real STAR runtime,
scheduler, cluster, production, scientific-review, or biological proof.
