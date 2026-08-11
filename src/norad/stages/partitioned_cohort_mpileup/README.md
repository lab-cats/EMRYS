# `generate_partitioned_cohort_mpileup_VCFs` owner

Native owner of `norad.stage.generate_partitioned_cohort_mpileup_VCFs.v1`
(historical `07`). [`CONTRACT.md`](CONTRACT.md) owns exact selector, output,
transaction, retained-defect, and evidence semantics. The lowercase directory
is the physical owner; the semantic identity, artifact names, and historical
alias do not change with that layout.

## Entry points

- producer: [`step_07_bcftools_mpileup_by_chrom_and_strand.sh`](step_07_bcftools_mpileup_by_chrom_and_strand.sh)
- validator: grouped route
  `python -I -m norad validate partitioned-cohort-mpileup`, implemented by
  private [`validator.py`](validator.py)
- scheduler: [`step_07_bcftools_mpileup_by_chrom_and_strand.slurm`](step_07_bcftools_mpileup_by_chrom_and_strand.slurm)

## Operate

Use an absolute output root so receipt and validator paths agree. Dry-run is
no-write:

```bash
output_root="$(pwd)/results/mpileup"
src/norad/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.pilot.tsv \
  --partition-id pilot_1 \
  --orientation-root results/orientation \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-root "$output_root" \
  --bcftools-bin /absolute/path/to/bcftools
```

Add `--execute` after inspecting sample order, partition selector, BAM/BAI and
FASTA/FAI inputs, tool, depth, filter, lock, scratch, and rollback paths. The
producer runs mpileup and filter, not `bcftools call`; `FWD_like`/`REV_like` are
mechanical labels and outputs are not validated variants or editing sites.

Execute requires all three predecessors or none and publishes FWD VCF, REV
VCF, then the two-row receipt. Only manifests are hash-bound and rechecked;
receipt visibility is not immutable-input or current-attempt proof.

Validator dry-run:

```bash
cohort=NORAD_EV_PUM1 partition=pilot_1
partition_dir="$(pwd)/results/mpileup/$cohort/$partition"
.venv/bin/python -I -m norad validate partitioned-cohort-mpileup \
  --cohort-id "$cohort" --partition-id "$partition" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.pilot.tsv \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --fwd-vcf "$partition_dir/$cohort.$partition.FWD_like.mpileup.vcf" \
  --rev-vcf "$partition_dir/$cohort.$partition.REV_like.mpileup.vcf" \
  --receipt "$partition_dir/$cohort.$partition.step07_outputs.tsv" \
  --output "results/qc/validation/07/${cohort}__${partition}.validation.tsv"
```

Create the parent and add `--execute`. Exit `0` permits failed rows. The five
checks do not prove coordinate bounds, VCF semantics, filter compliance, tool
or input identity, biological meaning, or publication attempt.

Do not execute private `validator.py` directly, add `PYTHONPATH`, or restore the
retired validator path to bypass package selection.

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,PARTITION_MANIFEST=configs/step_07_partitions.pilot.tsv,PARTITION_ID=pilot_1 \
  src/norad/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

Change only `EXECUTE=1` after review. Scheduler checks three nonempty paths;
stale finals can produce false success.

## Promote, diagnose, and verify

Primary promotion additionally requires the admitted sample manifest to match
the approved pair reference and exactly 25 declared receipts plus 50 VCFs.
Counts supplement per-partition validation; they never prove semantics alone.

Preserve all finals, temp/backups, lock, manifests, BAM/BAI, FASTA/FAI,
regions, streams, job identity, environment, and tool/depth/filter identity.
Never combine attempts, trust receipt presence or counts, or delete a foreign
lock. Use a fresh root for an authorized diagnostic retry.

```bash
bash tests/stages/partitioned_cohort_mpileup/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
.venv/bin/python -m pytest -q \
  tests/stages/partitioned_cohort_mpileup/test_validate_step_07_mpileup_outputs.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_07_bcftools_mpileup
```

This is local fixture/fake-tool evidence only.
