# `construct_canonical_BAM` owner

Native owner of `norad.stage.construct_canonical_BAM.v1` (historical `02`).
[`CONTRACT.md`](CONTRACT.md) owns exact transaction, recovery, and evidence
semantics.

## Entry points

- producer: [`step_02_sort_index_bam.sh`](step_02_sort_index_bam.sh)
- validator: grouped route `python -I -m norad validate canonical-bam`,
  implemented by private [`validator.py`](validator.py)
- scheduler: [`step_02_sort_index_bam.slurm`](step_02_sort_index_bam.slurm)

## Operate

Producer dry-run resolves `samtools` from `PATH` and creates no output:

```bash
src/norad/stages/canonical_bam/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8
```

The orchestration-safe invocation binds `samtools` explicitly and adds
`--no-clobber --execute`. In that mode the producer refuses either existing
final, hashes and rechecks the input alignment, retains the per-sample owned
lock through validation and publication, and never enters the legacy
replacement/backup path. Execute without `--no-clobber` preserves the existing
replaceable-pair behavior; its rollback is not failure-atomic.

When the admitted input is already coordinate sorted and every alignment has
the exact canonical sample read group, the producer hard-links those BAM bytes
into the canonical transaction and creates only the BAI. Noncanonical inputs
retain the generic samtools sort/read-group fallback.

Validator dry-run:

```bash
.venv/bin/python -I -m norad validate canonical-bam \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. The private validator imports the
neutral validation-report and BAM helpers; do not execute `validator.py`
directly, add `PYTHONPATH`, or restore the retired validator path to bypass an
import failure.

Submit from the checkout; change `EXECUTE=0` to `1` only after dry-run review:

```bash
cd /absolute/path/to/norad
mkdir -p logs
SAMPLE_ID=ABE_EV_2 \
INPUT_ALIGNMENT=/absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
OUTPUT_DIR=/absolute/results/bam/ABE_EV_2 THREADS=8 EXECUTE=0 \
  sbatch src/norad/stages/canonical_bam/step_02_sort_index_bam.slurm
```

The wrapper forces `TMPDIR=/tmp`, strictly loads samtools `1.19.2`, and checks
only that BAM and BAI paths are files.

## Diagnose and verify

Preserve finals, streams, run-token temporaries, backups, and exact missing
paths before recovery. Absence of a lock or backup does not authorize deletion,
adoption, or retry. Follow [`TROUBLESHOOTING.md`](../../../../docs/operations/TROUBLESHOOTING.md).

```bash
bash tests/stages/canonical_bam/test_step_02_sort_index_bam.sh
.venv/bin/python -m pytest -q \
  tests/stages/canonical_bam/test_validate_step_02_canonical_bam.py \
  tests/libraries/test_bam_validation.py \
  tests/stages/duplicate_marking/test_validate_step_04_mark_duplicates.py \
  tests/stages/split_n_cigar/test_validate_step_05_split_ncigar.py \
  tests/test_slurm_wrapper_contracts.py
```

These checks are local fixture/mock evidence, not real samtools, scheduler,
cluster, production, scientific-review, or biological proof.
