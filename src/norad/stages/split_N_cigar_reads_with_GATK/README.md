# `split_N_cigar_reads_with_GATK` owner

This directory is the implemented native owner for semantic stage
`split_N_cigar_reads_with_GATK`
(`norad.stage.split_N_cigar_reads_with_GATK.v1`, historical alias `05`). Its
public assets are:

- [`step_05_split_n_cigar_reads.sh`](step_05_split_n_cigar_reads.sh), the
  mode-`0644` Bash producer;
- [`validate_step_05_split_ncigar.py`](validate_step_05_split_ncigar.py), the
  mode-`0644` explicit-interpreter validator;
- [`step_05_split_n_cigar_reads.slurm`](step_05_split_n_cigar_reads.slurm), the
  mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/split_N_cigar_reads_with_GATK/test_step_05_split_n_cigar_reads.sh)
  and [validator](../../../../tests/stages/split_N_cigar_reads_with_GATK/test_validate_step_05_split_ncigar.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

The producer requires a sample identifier, one duplicate-marked BAM with the
exact adjacent `<bam>.bai`, a reference FASTA with exact `<fasta>.fai` and
same-directory `<stem>.dict` sidecars, an output directory, GATK, samtools,
and Java 17 or newer. It never creates or repairs reference sidecars. Invoke
the mode-`0644` file through Bash. From the repository root, this is a complete
no-write dry run:

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

Direct dry-run checks all five input/reference files and executable paths,
prints the exact lock, run-token scratch, backup, project-storage GATK-temp,
GATK, and samtools plan, and writes nothing. It invokes no version or data
tool. After inspection, repeat the command with `--execute`:

```bash
bash src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /absolute/path/to/gatk \
  --samtools-bin /absolute/path/to/samtools \
  --java-bin /absolute/path/to/java \
  --execute
```

From another working directory, make the producer, BAM, reference FASTA,
output directory, GATK, samtools, and Java paths absolute. The derived BAM
index, FAI, and DICT then remain bound to those absolute inputs:

```bash
bash /absolute/path/to/norad/src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam /absolute/results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta /absolute/refs/novogene_ref/genome.fa \
  --output-dir /absolute/results/split_ncigar/ABE_EV_2 \
  --gatk-bin /absolute/path/to/gatk \
  --samtools-bin /absolute/path/to/samtools \
  --java-bin /absolute/path/to/java
```

GATK and samtools resolve from explicit arguments, then their corresponding
`*_BIN_OVERRIDE`, then `PATH`. Java resolves from its explicit argument,
`JAVA_BIN_OVERRIDE`, a usable `$JAVA_HOME/bin/java`, then `PATH`. A value with
`/` must exist and be executable. Execute mode invokes the selected Java and
GATK version commands and rejects Java below 17; direct dry-run deliberately
does not invoke them.

Execute mode creates the output directory, takes the output-directory-wide
lock, creates a run-token GATK temp directory on project storage, runs
`SplitNCigarReads`, indexes and validates the staged pair, backs up a complete
predecessor when present, moves the two replacement files sequentially, and
revalidates their final paths. The structural checks require a nonempty BAM,
quickcheck success, coordinate order, exactly one sample-matching read group,
at least one alignment, every alignment tagged with that group, and a nonempty
BAI. They do not prove the GATK split-N-cigar transform or bind outputs to one
input/tool attempt.

Inputs are not snapshot-rechecked. Successful publication has no receipt. The
lock is shared by all samples in one output directory. Restoration moves are
best-effort, and cleanup can erase backups, scratch, the lock, and the only
recovery evidence after a restoration failure. A controlled GATK-time change
to the admitted BAM, BAI, FASTA, FAI, or DICT can therefore go undetected.
These are characterized defects, not approved transaction guarantees.

## Validator

Invoke the mode-`0644` validator with an explicit interpreter. Dry-run performs
the declared samtools/header/reference checks, prints five TSV rows plus the
completion line, and writes no report:

```bash
.venv/bin/python \
  src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py \
  --scope-id ABE_EV_2 \
  --bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --bai results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam.bai \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/05/ABE_EV_2.validation.tsv
```

Create the output parent and add `--execute`. Repeating the same command
deterministically replaces a valid owned report only after all six declared
input/tool files pass stable-input revalidation:

```bash
mkdir -p results/qc/validation/05
.venv/bin/python \
  src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py \
  --scope-id ABE_EV_2 \
  --bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --bai results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam.bai \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/05/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, make the interpreter, validator, BAM, BAI, FASTA, FAI,
DICT, samtools, and report paths absolute. Dry-run, execute, and repeat leave
no invocation-directory residue:

```bash
/absolute/path/to/norad/.venv/bin/python \
  /absolute/path/to/norad/src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py \
  --scope-id ABE_EV_2 \
  --bam /absolute/results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --bai /absolute/results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam.bai \
  --reference-fasta /absolute/refs/novogene_ref/genome.fa \
  --reference-fai /absolute/refs/novogene_ref/genome.fa.fai \
  --reference-dict /absolute/refs/novogene_ref/genome.dict \
  --samtools-bin /absolute/path/to/samtools \
  --output /absolute/results/qc/validation/05/ABE_EV_2.validation.tsv
```

The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py), neutral
[`bam_validation.py`](../../libraries/bam_validation.py), and neutral
[`reference_contigs.py`](../../libraries/reference_contigs.py).
Each bridge validates the exact owner and preserves foreign cache state without
changing `sys.path`; no package identity, `PYTHONPATH`, wrapper, compatibility
import, or public helper CLI is supported.

Validator exit `0` means five rows were validly rendered or published; one or
more rows may still have `status=fail`. Quickcheck nonzero is published as a
failed row. Unsafe input, a required header-tool failure, a stable-input
mismatch, an exact-owner integrity failure, or unsafe publication exits `2`
without a new report and preserves a valid predecessor when one exists.
Neither producer nor scheduler exit `0` implies validator pass.

## Scheduler

SLURM opens declared log paths before the script body. Start in the checkout,
create `logs/`, and submit the exact final job. The default is dry-run:

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=ABE_EV_2,INPUT_BAM=/absolute/results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam,REFERENCE_FASTA=/absolute/refs/novogene_ref/genome.fa,OUTPUT_DIR=/absolute/results/split_ncigar/ABE_EV_2 \
  src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.slurm
```

Change only `EXECUTE=1` after accepting the dry-run evidence. Use
`GATK_BIN_OVERRIDE`, `SAMTOOLS_BIN_OVERRIDE`, and `JAVA_BIN_OVERRIDE` for
explicit tool paths. The wrapper changes to `SLURM_SUBMIT_DIR` with a current-
CWD fallback, exports `/tmp`, tolerates samtools module-list/load diagnostics,
uses fixed site paths for GATK and samtools unless overridden, selects Java
from the override, usable `$JAVA_HOME/bin/java`, then `PATH`, and enforces the
actual Java-17 floor. Its GATK and samtools version commands can fail before
delegation. Missing/unusable GATK or samtools paths are warning-only at the
wrapper probe but are rejected by the delegated producer.

Scheduler dry-run creates `logs/` in the body and invokes runtime/tool version
probes before the direct producer's no-write dry-run. Bash `3.2` can fail while
expanding the empty dry-run argument array. In execute mode, a zero-exit child
that creates nothing can rediscover a stale nonempty final pair and let the
wrapper succeed. Preserve these defects; scheduler success is not proof of
current-attempt output identity.

## Diagnostics, recovery, evidence, and rollback

Before cleanup, same-name retry, or recovery, preserve every surviving final,
temporary, backup, alternate-index, GATK-temp, lock/owner, input/reference,
unrelated, stdout/stderr, scheduler job/accounting/log, checkout, and selected
tool/version artifact. Rule out the lock owner, an active producer, and Step
`06` or other readers. Do not combine BAM and BAI members from different
attempts, infer attempt identity from timestamps, remove a foreign lock, or
adopt a stale scheduler success.

The characterized worst rollback state propagates injected BAI-publication
exit `67` after injected prior-BAM-restoration exit `68`. It leaves the prior
BAM missing and prior BAI restored, preserves unrelated bytes, and erases
backups, lock, scratch, and any recovery marker. Their absence does not prove
clean state. Use an isolated output directory for any separately authorized
diagnostic retry. Git rollback changes tracked implementation only; it cannot
restore, remove, or authenticate runtime artifacts. Follow the
[Step `05` recovery route](../../../../docs/operations/TROUBLESHOOTING.md#step-05-producer-or-wrapper-leaves-a-partial-rollback-failure-or-stale-pair).

Focused local protection is:

```bash
bash tests/stages/split_N_cigar_reads_with_GATK/test_step_05_split_n_cigar_reads.sh
.venv/bin/python -m pytest -q \
  tests/stages/split_N_cigar_reads_with_GATK/test_validate_step_05_split_ncigar.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_05
```

Current behavior, recovery states, and evidence limits are owned by [`CONTRACT.md`](CONTRACT.md). The owner is locally fixture/mock tested; this does not establish new GATK, Java, samtools, scheduler, cluster, production, scientific-review, or biological proof.
