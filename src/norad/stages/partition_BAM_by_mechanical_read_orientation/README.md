# `partition_BAM_by_mechanical_read_orientation` owner

Native owner of `norad.stage.partition_BAM_by_mechanical_read_orientation.v1`
(historical `06`). [`CONTRACT.md`](CONTRACT.md) owns exact inputs, five-output
transaction, defects, recovery, and mechanical-evidence semantics.

## Entry points

- producer: [`step_06_split_bam_by_read_orientation.sh`](step_06_split_bam_by_read_orientation.sh)
- validator: [`validate_step_06_orientation_outputs.py`](validate_step_06_orientation_outputs.py)
- scheduler: [`step_06_split_bam_by_read_orientation.slurm`](step_06_split_bam_by_read_orientation.slurm)

## Operate

Producer no-write dry-run:

```bash
src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir results/orientation/ABE_EV_2 \
  --qc-dir results/qc/orientation \
  --threads 1 \
  --samtools-bin /absolute/path/to/samtools
```

Add `--execute` after inspection. `FWD_like` combines flags 99 and 147;
`REV_like` combines 83 and 163. These are mechanical groups, not transcript
strand, strandedness, sense, or antisense, and reads may remain unassigned.

Execute publishes two BAM/BAI pairs and an orientation-count TSV last. It
requires an all-five-or-none predecessor, but does not snapshot-recheck input,
the TSV is not a receipt, failed restoration may lose backups, and distinct
output locks can race on one shared QC path.

Validator dry-run:

```bash
.venv/bin/python src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py \
  --scope-id ABE_EV_2 \
  --fwd-bam results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam \
  --fwd-bai results/orientation/ABE_EV_2/ABE_EV_2.FWD_like.bam.bai \
  --rev-bam results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam \
  --rev-bai results/orientation/ABE_EV_2/ABE_EV_2.REV_like.bam.bai \
  --counts results/qc/orientation/ABE_EV_2.orientation_counts.tsv \
  --output results/qc/validation/06/ABE_EV_2.validation.tsv
```

Create the parent and add `--execute`. Exit `0` means five rows rendered or
published; rows may fail. The validator checks table arithmetic and container
magic, not BAM quickcheck, BAM/BAI correspondence, flags, sort, or read groups.

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,INPUT_BAM=/absolute/results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam,OUTPUT_DIR=/absolute/results/orientation/ABE_EV_2,QC_DIR=/absolute/results/qc/orientation,THREADS=1 \
  src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.slurm
```

Change only `EXECUTE=1` after review. A zero-output child can rediscover stale
finals; scheduler success is not current-attempt proof.

## Diagnose and verify

Preserve all finals, scratch, backups, lock, input pair, streams, job identity,
tool version, and unrelated bytes. Do not combine attempts, delete a foreign
lock, trust the counts file as a receipt, or reuse ambiguous paths.

```bash
bash tests/stages/partition_BAM_by_mechanical_read_orientation/test_step_06_split_bam_by_read_orientation.sh
.venv/bin/python -m pytest -q \
  tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_06_split_bam_by_read_orientation
```

This is local fixture/fake-tool evidence only.
