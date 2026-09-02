# `split_N_cigar_reads_with_GATK` owner

Native owner of `emrys.stage.split_N_cigar_reads_with_GATK.v1` (historical
`05`). [`CONTRACT.md`](CONTRACT.md) owns exact transaction, retained defects,
recovery, and evidence semantics. The lowercase directory is the physical
owner; the semantic identity, artifact names, and historical alias do not
change with that layout.

## Entry points

- producer: [`step_05_split_n_cigar_reads.sh`](step_05_split_n_cigar_reads.sh)
- validator: grouped route `emrys validate split-n-cigar`,
  implemented by private [`validator.py`](validator.py)

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Invoke the mode-`0644` producer through Bash. Dry-run writes nothing and does
not invoke tool-version commands. Execute mode requires
`EMRYS_SHA256_PYTHON` to name one absolute Python 3.11+ launcher; the Java path
must resolve to canonical `<JAVA_HOME>/bin/java`. The neutral bridge clears
ambient JVM/GATK selectors and makes that selected Java authoritative for both
the GATK version probe and SplitNCigarReads:

```bash
EMRYS_SHA256_PYTHON=/absolute/path/to/python \
bash src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /absolute/path/to/gatk \
  --samtools-bin /absolute/path/to/samtools \
  --java-bin /absolute/java-home/bin/java
```

The exact BAM index, FAI, and same-directory DICT must exist; this owner never
repairs sidecars. The orchestration-safe invocation adds `--no-clobber
--execute`. That mode uses a per-sample lock, refuses either existing final,
hashes and rechecks the BAM/BAI and FASTA/FAI/DICT set, and therefore never
enters the legacy replacement/backup path. Execute without `--no-clobber`
preserves the existing replaceable-pair transaction; failed restoration there
can still erase recovery evidence. The native pair is not an attempt receipt.

Validator dry-run:

```bash
emrys validate split-n-cigar \
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
transform or bind outputs to one input/tool attempt. Do not execute private
`validator.py` directly, add `PYTHONPATH`, or restore the retired validator
path to bypass package selection.

## Diagnose and verify

Preserve every final, temporary, backup, alternate index, GATK temp, lock,
input/reference, stream, job/accounting record, checkout, and selected tool.
Never combine attempts or infer clean state from missing recovery files. Use an
isolated directory for an authorized diagnostic retry.

```bash
bash tests/stages/split_n_cigar/test_step_05_split_n_cigar_reads.sh
.venv/bin/python -m pytest -q \
  tests/stages/split_n_cigar/test_validate_step_05_split_ncigar.py
```

This is local fixture/mock evidence only, not real GATK/Java/samtools,
scheduler, cluster, production, scientific-review, or biological proof.
