# Troubleshooting

Troubleshooting notes for the NORAD / Novogene Remora RNA-seq pipeline.

Use this file when something fails or behaves weirdly. For normal operation, see `docs/RUNBOOK.md`.

## `TMPDIR [/local/tmp] is not writeable`

### Symptom

SLURM stderr contains:

```text
slurmstepd: error: TMPDIR [/local/tmp] is not writeable
slurmstepd: error: Setting TMPDIR to /tmp
```

### Cause

The cluster default temporary directory may point to `/local/tmp`, which is not writable on some compute nodes.

### Fix

Submit execute jobs with:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

SLURM wrappers should include:

```bash
#SBATCH --export=ALL,TMPDIR=/tmp
```

and should also explicitly set:

```bash
export TMPDIR="${TMPDIR:-/tmp}"
```

### Notes

This warning has not been fatal when the job logs show:

```text
TMPDIR: /tmp
```

## `picard: command not found`

### Symptom

Running `picard` directly fails:

```text
picard: command not found
```

### Cause

On CSU, Picard is exposed through a jar path set by the `picard/3.1.1` module, not necessarily as a standalone `picard` executable.

### Fix

Use:

```bash
module load picard/3.1.1
java -jar "$PICARD" MarkDuplicates ...
```

Known module behavior:

```text
picard/3.1.1 loads java/17.0.10
PICARD=/cm/shared/apps/picard/picard/build/libs/picard.jar
```

The module name alone does not prove the effective Java runtime. For Step `04`,
inspect the selected Java executable and its actual `java -version` output.

## Picard `UnsupportedClassVersionError`

### Symptom

Step `04` fails before or during Picard startup with an error like:

```text
UnsupportedClassVersionError
```

The observed Java class-file mismatch was:

```text
Picard requires class-file version 61
selected runtime supports class-file version 55
```

Class-file version 61 corresponds to Java 17. Class-file version 55 corresponds
to Java 11.

### Cause

Picard 3.1.1 requires Java 17, but the selected runtime on the compute node was
Java 11. This is not a Picard algorithm defect and not a pipeline-logic defect;
it exposes inconsistent Java availability across compute nodes.

Observed node-specific behavior:

```text
node003:
  selected executable: /usr/bin/java
  actual runtime: OpenJDK 17.0.15
  Picard 3.1.1 launched successfully
  ABE_EV_2 MarkDuplicates completed successfully

node007:
  /usr/bin/java reported OpenJDK 11.0.24
  Java 11 could not run Picard classes compiled for Java 17
  the Java 17 module's advertised JAVA_HOME path did not exist
```

The Java module advertised:

```text
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-17.0.10.0.7-2.el9.x86_64
```

That path was missing on `node007`. On the successful `node003` run,
`JAVA_HOME` still referred to the advertised Java 17.0.10 path, but the selected
executable was `/usr/bin/java` and its actual runtime was Java 17.0.15.

### Fix

Do not infer the effective Java runtime from the module name or `JAVA_HOME`
alone. The selected executable and actual `java -version` output must be logged
and validated.

Step `04` resolves Java in this order:

```text
1. JAVA_BIN_OVERRIDE, when explicitly provided
2. $JAVA_HOME/bin/java, only if it exists and is executable
3. command -v java
```

The wrapper then fails before Picard starts if the selected runtime is below
Java 17.

If CSU HPC provides a supported Java 17 executable, pass it explicitly:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,JAVA_BIN_OVERRIDE=/path/to/java \
  jobs/step_04_mark_duplicates.slurm
```

Temporary workaround:

```text
--nodelist=node003
```

This is only an operational workaround while Java 17 availability is clarified.
Do not embed `node003` as a permanent default, describe node pinning as a
pipeline architecture requirement, assume node003 will remain the solution, or
recommend copying a JDK from the head node or another compute node.

## `#SBATCH --mem=1G` fails

### Symptom

Submitting a job with explicit memory such as `#SBATCH --mem=1G` fails:

```text
Memory specification can not be satisfied
Batch job submission failed: Requested node configuration is not available
```

### Cause

CSU partition/memory rules may not allow the requested memory specification, or the partition may require memory requests in a different form.

### Fix

Avoid explicit `--mem` until CSU memory rules are confirmed.

Prefer known-working resource requests from existing jobs:

```bash
#SBATCH --partition=short
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
```

or use the resource pattern already proven for the relevant step.

### Notes

Observed working jobs so far did not require explicit memory requests.

## `logs/...out: No such file or directory` at submit time

### Symptom

SLURM job fails or logs are missing because the `logs/` directory does not exist.

### Cause

SLURM does not create parent directories for:

```bash
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

### Fix

Before submitting jobs:

```bash
mkdir -p logs
```

## Tailing the wrong log file

### Symptom

A job completed, but tailing the expected log fails:

```text
tail: cannot open 'logs/norad-sort-index-bam-<JOBID>.out' for reading: No such file or directory
```

### Cause

Different jobs have different log prefixes. For example:

```text
Step 02:  norad-sort-index-bam-<JOBID>.out
Step 02b: norad-bam-qc-<JOBID>.out
Step 03:  norad-infer-strandedness-<JOBID>.out
```

### Fix

Find the actual log name first:

```bash
ls -ltr logs | tail
```

Then tail the matching files:

```bash
tail -120 logs/<actual-prefix>-<JOBID>.out
tail -120 logs/<actual-prefix>-<JOBID>.err
```

If the cluster shell helpers are installed:

```bash
sjcheck <JOBID>
sjtail <JOBID>
```

## STAR BAM flagstat counts look larger than input reads

### Symptom

`samtools flagstat` shows many more total records than STAR input reads.

Example from `ABE_EV_2` STAR BAM:

```text
77,561,040 total records
35,326,360 primary
42,234,680 secondary
```

### Cause

STAR outputs secondary alignments for multimapping reads. `flagstat` counts alignment records, not original input reads.

### Fix

Use STAR `Log.final.out` for input-level mapping rates.

For `ABE_EV_2`, STAR reported:

```text
Input reads: 21,358,987
Unique mapped: 58.50%
Multi-mapped: 24.19%
Too many loci: 0.52%
Unmapped too short: 16.55%
Approximate total mapped: 83.21%
```

`flagstat` is still useful for BAM-level QC, but interpret total records carefully when secondary alignments are present.

## Step 02b `samtools: command not found` despite loaded module

### Symptom

Step `02b` fails immediately because `samtools` is not found on `PATH`, even though module output lists:

```text
samtools/1.19.2
```

### Cause

This is a cluster environment/PATH inconsistency, not a BAM/QC failure.

### Fix

Prepend the known samtools bin directory to `PATH` before rerunning:

```bash
export PATH="/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin:$PATH"
```

The Step `02b` cohort rerun succeeded across all six final hardened Step `02` BAMs with that path available.

## RSeQC `infer_experiment.py` not found

### Symptom

Step 03 fails because `infer_experiment.py` cannot be found.

### Cause

RSeQC is not currently known as a global module; it is available through the project virtual environment.

### Fix

Use the project executable:

```bash
.venv/bin/infer_experiment.py
```

Step 03 should prefer:

```text
.venv/bin/infer_experiment.py
```

if present, otherwise fall back to:

```text
infer_experiment.py
```

The SLURM wrapper should source `.venv/bin/activate` if available.

## RSeQC `infer_experiment.py` path exists but is not executable

### Symptom

Step 03 fails tool validation even though the path exists.

### Cause

Path-style tool arguments are required to be executable.

### Fix

Make it executable if appropriate:

```bash
chmod +x .venv/bin/infer_experiment.py
```

or pass a valid executable path with:

```bash
--infer-experiment-bin <path>
```

Step 03 validation rule:

```text
If the binary contains '/', require [[ -x "$bin" ]].
If it is command-name style, require command -v "$bin".
```

## Step 03 strandedness result looks ambiguous

### Symptom

RSeQC output has high failed fraction or no dominant strandedness group.

### Cause

Possible causes include:

* wrong annotation BED12
* wrong BAM
* unstranded library
* poor/incompatible annotation
* sample-specific issue

### Fix

For `ABE_EV_2`, the result was not ambiguous:

```text
Fraction failed: 0.0828
Group 1: 0.0432
Group 2: 0.8740
```

This strongly supports reverse-stranded / first-strand behavior.

If another sample is ambiguous, compare:

```bash
cat results/qc/strandedness/<sample>.infer_experiment.txt
```

and check that the BAM and BED12 paths are correct.

## `module avail gatk` shows nothing

### Symptom

No visible GATK module appears with:

```bash
module avail gatk
```

### Cause

GATK may not be exposed through `module avail gatk`, even though a direct cluster installation exists.

### Fix

Use the validated direct path used by the Step `05` SLURM wrapper:

```text
/cm/shared/apps/gatk/gatk-4.6.1.0/gatk
```

Confirmed probe evidence:

```text
node: node002
Java: OpenJDK 17.0.14
GATK: 4.6.1.0
tool probe exit code: 0:0
```

Still log and validate the actual Java runtime. The historical Java inconsistency remains relevant: `node002` and `node003` have provided Java 17, while `node007` previously exposed Java 11 / a missing Java 17 path.

Step `05` still validates the actual Java runtime before execute-mode GATK use.

## Step 05 GATK `No space left on device` from `/tmp`

### Symptom

Step `05` `GATK SplitNCigarReads` starts successfully, completes traversal pass 1, enters traversal pass 2, then fails during HTSJDK temporary spill/write/close behavior with a message like:

```text
htsjdk.samtools.util.RuntimeIOException: Problem writing temporary file file:///tmp/sortingcollection...
No space left on device
```

The failure may mention `SortingCollection` temporary spill files under `/tmp`.

### Cause

GATK/HTSJDK used node-local `/tmp` for internal `SortingCollection` spill files; node-local `/tmp` was too small.

This is useful partial evidence that the Step `05` inputs, tools, and reference sidecars were mostly working, but it is not Step `05` cluster proof because final split-N-cigar BAM/BAI outputs were not validated.

### Fix

Use a per-run project-storage GATK temp directory with all relevant GATK/Java temp controls:

```text
--java-options -Djava.io.tmpdir=<project temp dir>
--tmp-dir <project temp dir>
TMPDIR=<project temp dir> for the GATK process
```

After failure, cleanup should remove only owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks.

Do not call Step `05` cluster-proven until a rerun completes and final `results/split_ncigar/<sample>/<sample>.split_ncigar.bam` plus `.bai` outputs pass validation.

## Step 00c FAI/DICT validation fails

### Symptom

Step `00c` fails with a message that the FASTA index and sequence dictionary contigs/lengths do not agree.

### Cause

`refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` are shared reference sidecars. If either file is stale, empty, partially written, or generated from a different FASTA, GATK-compatible reference validation is unsafe.

### Fix

Do not let Step `05` create or repair these files inside a per-sample job. Inspect the existing sidecars, confirm they belong to `refs/novogene_ref/genome.fa`, and rerun formal Step `00c` only after deciding how to handle the invalid shared reference files.

Step `00c` intentionally does not overwrite invalid existing sidecars by default.

## Scaffolded downstream job accidentally submitted

### Symptom

A downstream job like Step `06`-`09` is submitted but exits immediately, says `not implemented`, or exits with code `2`.

### Cause

Steps `06`-`09` are scaffolded and intentionally non-runnable until
implemented.

Step `05` is implemented and locally tested, with cluster revalidation submitted/running but final outputs not yet inspected. If Step `05` exits as a scaffold, the cluster checkout is stale and should be updated before submission.

Current scaffolded files include:

```text
jobs/step_06_split_bam_by_read_orientation.slurm
scripts/step_06_split_bam_by_read_orientation.sh
```

### Fix

Do not run scaffolded downstream jobs.

Current scaffolded steps:

```text
06 split BAM by read orientation
07 bcftools mpileup
08 VCF preprocessing
09 CMH editing-site calling
```

Implement locally, test, commit/push, pull on cluster, then dry-run/execute only
after the step is active.

Step `05` outputs now use `results/split_ncigar/<sample_id>/` and consume Step `04` outputs under `results/markdup/<sample_id>/`.

## Wrong log interpretation: empty `.err` file

### Symptom

The `.err` file exists but is empty.

### Cause

For many successful jobs, stderr is empty. This is fine.

### Fix

Use `sacct` and output validation to decide success:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Success means:

```text
COMPLETED 0:0
```

and expected output files exist and are non-empty where appropriate.

## Picard `SAMRecord.getReadGroup() is null`

### Symptom

Picard MarkDuplicates fails immediately with:

```text
SAMRecord.getReadGroup() is null
```

### Cause

The canonical BAM lacks valid read-group metadata. Either the header has no
matching `@RG` line, records lack `RG` tags, or both.

### Diagnose

```bash
samtools view -H <bam> | grep '^@RG'
samtools view -c <bam>
samtools view -c -d "RG:<sample_id>" <bam>
```

The current one-sample-per-BAM contract expects exactly one `@RG` line and all
alignment records tagged with `RG:<sample_id>`.

### Fix

Regenerate the canonical BAM through hardened Step 02. Do not patch around
missing read groups in Step 04.

## Future Troubleshooting Taxonomy

A future troubleshooting index may summarize repeated failure patterns as symptom, likely cause, confirmation command, and fix. Keep this as a deferred roadmap idea until enough real failures exist; do not add entries for helpers, validators, cleanup tools, reports, or config files that are not implemented.

## General success checklist

A job is only “proven” when all of these are true:

```text
1. Dry-run completed 0:0.
2. Dry-run command/context looked correct.
3. Execute job completed 0:0.
4. stderr is empty or contains only known harmless messages.
5. Expected output files exist.
6. Expected output files are non-empty where appropriate.
7. Output content makes biological/computational sense.
```

Do not proceed to the next step until this checklist passes.
