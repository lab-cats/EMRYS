# `align_RNA_reads_with_STAR` owner

Native owner of `norad.stage.align_RNA_reads_with_STAR.v1` (historical `01`).
[`CONTRACT.md`](CONTRACT.md) is the exact behavior and evidence contract.

## Entry points

- producer: [`step_01_star_align.sh`](step_01_star_align.sh)
- scheduler: [`step_01_star_align.slurm`](step_01_star_align.slurm)
- validator: grouped route `python -I -m norad validate star-alignment`,
  implemented by private [`validator.py`](validator.py)

## Operate

Producer dry-run from the repository root:

```bash
src/norad/stages/star_alignment/step_01_star_align.sh \
  --sample-id ABE_EV_2 \
  --r1-fastq data/ABE_EV_2_R1.fastq.gz \
  --r2-fastq data/ABE_EV_2_R2.fastq.gz \
  --star-index refs/novogene_star_index \
  --output-dir results/star/ABE_EV_2 \
  --threads 8 \
  --gunzip-bin /usr/bin/gunzip
```

`STAR` must be on `PATH`, or bind it with `--star-bin`. When both mates end in
`.gz`, bind the admitted decompressor explicitly with `--gunzip-bin`; direct
callers that omit it retain the `gunzip`-on-`PATH` default. Uncompressed mates
do not resolve or validate a decompressor. Dry-run writes nothing.
The orchestration-safe invocation adds `--no-clobber`: that mode hashes both
FASTQs and every admitted top-level regular STAR-index file in deterministic
name order, uses a per-sample owned lock and run-token staging directory,
requires the five declared STAR outputs, rechecks FASTQ and index membership
plus bytes, refuses any pre-existing declared output, and create-exclusively
publishes each final while retaining its staged inode as an ownership anchor.
Success validates the full final set against those anchors, removes staging,
and then releases the lock. If a final appears late or replaces an owned final,
the foreign path, lock, and staging residue remain for operator recovery. Empty,
symbolic-link, nested, special, or delimiter-ambiguous index members block this
mode. The historical `--execute` route without `--no-clobber` still writes
STAR's prefix directly and retains its prior index-directory behavior. The
workflow verified record remains the wider run/output/tool binding.

Validator dry-run:

```bash
.venv/bin/python -I -m norad validate star-alignment \
  --scope-id ABE_EV_2 \
  --bam results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --log-final results/star/ABE_EV_2/ABE_EV_2.Log.final.out \
  --log-out results/star/ABE_EV_2/ABE_EV_2.Log.out \
  --log-progress results/star/ABE_EV_2/ABE_EV_2.Log.progress.out \
  --sj-out results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab \
  --output results/qc/validation/01/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute` to publish. Validation is
structural; it does not establish alignment correctness.

Submit only from the intended checkout. `EXECUTE=0` is the default and creates
placeholder inputs; `EXECUTE=1` rejects them and requires all real overrides:

```bash
cd <checkout>
SAMPLE_ID=ABE_EV_2 R1_FASTQ=/absolute/R1.fastq.gz \
R2_FASTQ=/absolute/R2.fastq.gz STAR_INDEX=/absolute/star-index \
OUTPUT_DIR=/absolute/results/star/ABE_EV_2 EXECUTE=1 \
  sbatch src/norad/stages/star_alignment/step_01_star_align.slurm
```

The wrapper strictly loads STAR `2.7.11b` and does not validate outputs.

## Diagnose and verify

Preserve scheduler streams, STAR logs, BAM, and `SJ.out.tab` as one attempt.
Do not delete or adopt partial output; use the validator dry-run as the next
safe inspection and follow [`TROUBLESHOOTING.md`](../../../../docs/operations/TROUBLESHOOTING.md).

```bash
bash tests/stages/star_alignment/test_step_01_star_align.sh
.venv/bin/python -m pytest -q \
  tests/stages/star_alignment/test_validate_step_01_star_alignment.py \
  tests/test_slurm_wrapper_contracts.py
```

These are local fixture/mock checks, not real STAR, scheduler, cluster,
production, scientific-review, or biological proof.
