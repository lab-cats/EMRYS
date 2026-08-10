# `split_N_cigar_reads_with_GATK` owner

Native owner of `norad.stage.split_N_cigar_reads_with_GATK.v1` (historical
`05`). [`CONTRACT.md`](CONTRACT.md) owns exact transaction, retained defects,
recovery, and evidence semantics.

## Entry points

- producer: [`step_05_split_n_cigar_reads.sh`](step_05_split_n_cigar_reads.sh)
- validator: [`validate_step_05_split_ncigar.py`](validate_step_05_split_ncigar.py)
- scheduler: [`step_05_split_n_cigar_reads.slurm`](step_05_split_n_cigar_reads.slurm)

## Operate

Invoke the mode-`0644` producer through Bash. Dry-run writes nothing and does
not invoke tool-version commands:

```bash
bash src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /absolute/path/to/gatk \
  --samtools-bin /absolute/path/to/samtools \
  --java-bin /absolute/path/to/java
```

The exact BAM index, FAI, and same-directory DICT must exist; this owner never
repairs sidecars. Add `--execute` after inspection. Execute requires Java 17,
uses a directory-wide lock and project-storage GATK temp, stages the pair, and
publishes BAM then BAI. Inputs are not snapshot-rechecked, there is no receipt,
and failed restoration cleanup can erase the only recovery evidence.

Validator dry-run:

```bash
.venv/bin/python src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py \
  --scope-id ABE_EV_2 \
  --bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --bai results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam.bai \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/05/ABE_EV_2.validation.tsv
```

Create the parent and add `--execute`. Exit `0` means five rows rendered or
published; rows may still fail. Structural validation does not prove the GATK
transform or bind outputs to one input/tool attempt.

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,INPUT_BAM=/absolute/results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam,REFERENCE_FASTA=/absolute/refs/novogene_ref/genome.fa,OUTPUT_DIR=/absolute/results/split_ncigar/ABE_EV_2 \
  src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.slurm
```

Change only `EXECUTE=1` after review. Use explicit tool overrides when needed.
Stale finals can make a zero-output child look successful.

## Diagnose and verify

Preserve every final, temporary, backup, alternate index, GATK temp, lock,
input/reference, stream, job/accounting record, checkout, and selected tool.
Never combine attempts or infer clean state from missing recovery files. Use an
isolated directory for an authorized diagnostic retry.

```bash
bash tests/stages/split_N_cigar_reads_with_GATK/test_step_05_split_n_cigar_reads.sh
.venv/bin/python -m pytest -q \
  tests/stages/split_N_cigar_reads_with_GATK/test_validate_step_05_split_ncigar.py
.venv/bin/python -m pytest -q tests/test_slurm_wrapper_contracts.py -k step_05
```

This is local fixture/mock evidence only, not real GATK/Java/samtools,
scheduler, cluster, production, scientific-review, or biological proof.
