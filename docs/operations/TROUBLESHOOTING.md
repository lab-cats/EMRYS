# Troubleshooting

Troubleshooting notes for the NORAD / Novogene Remora RNA-seq pipeline.

Use this file when something fails or behaves weirdly. For normal operation, see `docs/operations/RUNBOOK.md`.

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

This was useful partial evidence that the Step `05` inputs, tools, and reference sidecars were mostly working. It is now resolved hardening context because the later six-sample Step `05` revalidation passed final split-N-cigar BAM/BAI output inspection.

### Fix

Use a per-run project-storage GATK temp directory with all relevant GATK/Java temp controls:

```text
--java-options -Djava.io.tmpdir=<project temp dir>
--tmp-dir <project temp dir>
TMPDIR=<project temp dir> for the GATK process
```

After failure, cleanup should remove only owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks.

The later Step `05` revalidation is cluster-proven across all six samples; keep this entry as the record of why GATK temp files must stay on project storage.

## Step 00c FAI/DICT validation fails

### Symptom

Step `00c` fails with a message that the FASTA index and sequence dictionary contigs/lengths do not agree.

### Cause

`refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` are shared reference sidecars. If either file is stale, empty, partially written, or generated from a different FASTA, GATK-compatible reference validation is unsafe.

### Fix

Do not let Step `05` create or repair these files inside a per-sample job. Inspect the existing sidecars, confirm they belong to `refs/novogene_ref/genome.fa`, and rerun formal Step `00c` only after deciding how to handle the invalid shared reference files.

Step `00c` intentionally does not overwrite invalid existing sidecars by default.

## Step 07 selector does not match the FASTA index

### Symptom

Step `07` rejects a `region` selector or a contig named in a `regions_file`
before bcftools runs.

### Cause

Step `07` requires every selected contig to exist in the supplied FASTA index.
Likely causes include:

```text
chr1 in a selector while the Novogene reference uses 1
an MT/M/chrM spelling mismatch
a malformed region expression
a regions_file created for a different reference
an unapproved partition manifest that changes the declared universe
```

### Diagnose

Inspect the FASTA-index names and the declared partition selector:

```bash
cut -f1 refs/novogene_ref/genome.fa.fai
awk -F '\t' 'NR == 1 || $1 == "<partition_id>"' \
  configs/step_07_partitions.primary_contigs.tsv
```

The tracked primary-contig manifest includes `MT`, but its exact
presence/spelling in the Novogene FASTA index has not been inspected on this
workstation and must be confirmed during cluster dry-run validation.

### Fix

Use selectors that match the exact runtime FASTA index. Do not silently drop a
partition or rename the reference. If the approved correction universe must
change, update the manifest and affected documentation explicitly before
running.

This is locally tested validation behavior, not an observed cluster failure;
Step `07` has not yet completed a cluster dry-run or execute job.

## Step 07 rejects VCF sample columns

### Symptom

bcftools creates a structurally readable temporary VCF, but Step `07` rejects
its sample columns or rolls publication back.

### Cause

Step `07` requires VCF sample columns to exactly equal the sample manifest in
manifest order. bcftools derives sample names from BAM read-group `SM` values,
so missing, duplicate, or mismatched metadata can violate the cohort contract.
Supplying BAMs in a different order can also change VCF column order.

### Diagnose

Compare the manifest order with BAM read groups:

```bash
awk -F '\t' 'NR > 1 {print $1}' samples.tsv
samtools view -H \
  results/orientation/<sample_id>/<sample_id>.FWD_like.bam |
  grep '^@RG'
```

For an already published VCF, inspect the actual columns with:

```bash
/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools query -l \
  results/mpileup/<cohort>/<partition>/<cohort>.<partition>.FWD_like.mpileup.vcf
```

### Fix

Correct the manifest selection/order or regenerate the affected upstream BAM
with the expected sample metadata. Do not reorder VCF headers manually and do
not bypass Step `07` validation.

This is locally tested validation behavior, not an observed cluster failure.

## Step 07 cannot establish the runtime sample manifest or later reports a manifest hash mismatch

### Symptom

The cluster checkout has no `samples.tsv`, the manifest lacks explicit
replicate values, validation fails, or Steps `08`/`09` report a
sample-manifest hash different from the Step `07` receipts.

### Cause

`samples.tsv` is absent from the current Git checkout, so the full runtime
manifest must be deliberately provisioned on the cluster. A copy may be
missing, may still predate the approved replicate assignments, or may have
changed after Step `07`. The Step `09` pairing reference TSV is documentation,
not a runtime overlay.

### Fix

Before Step `07`, establish the durable six-row runtime manifest, add and
validate explicit replicate `2`, `3`, and `4` assignments, record its SHA-256,
and use the byte-identical file through Steps `07`-`09`. If the manifest must
change after upstream artifacts exist, regenerate every affected stage through
normal contracts. Never edit a receipt or summary hash to force acceptance.

This is a documented promotion risk, not an observed cluster incident.

## Step 07 finds a lock or an incomplete output set

### Symptom

Step `07` reports an existing cohort/partition lock, or refuses to continue
because only part of the expected VCF/VCF/receipt set exists.

### Cause

Another run may own:

```text
results/mpileup/<cohort>/<partition>/.<cohort>.<partition>.step07.lock
```

Alternatively, files may have been copied or changed outside the transaction,
or a prior run may have been interrupted in a way that left an incomplete
stable set. The receipt is published last and is the commit marker for the two
validated orientation VCFs.

### Fix

Inspect the lock `owner` file, SLURM state, logs, and all three stable output
paths. Do not delete a foreign lock, remove one member of a published set, or
manufacture a receipt merely to make the check pass. Resolve ownership and the
state of any active job first. If recovery is required, treat it as an explicit
operator action and preserve evidence before changing files.

The script removes only its owned run-token temporary paths and lock, restores
the prior complete output set when publication fails after backup, and refuses
to overwrite an incomplete stable set.

These are locally mocked lock/rollback guarantees; no Step `07` cluster lock or
rollback incident has been observed.

For full primary-universe validation, require 25 primary receipts and 50
primary VCFs. The separate `pilot_1` transaction adds one receipt/two VCFs
under the output root but does not satisfy, alter, or enter the primary 25/50
gate. Do not use an unfiltered directory-wide file count as proof.

## Step 07 VCF has a header but no records

### Symptom

`bcftools view -H` prints no records and the Step `07` receipt records a VCF
record count of `0`.

### Cause

A valid partition may contain no records that pass:

```text
INFO/AD[1-]>2 & MAX(FORMAT/DP)>20
```

### Fix

Do not classify the VCF as corrupt solely because it has zero data records.
Step `07` accepts a header-only VCF when the VCF structure and exact
manifest-ordered sample columns validate, and records `0` in the receipt.
Investigate only if the result is unexpected for the selected region or if
header/sample validation fails.

Header-only behavior is covered by local mocked tests; no real-bcftools or
cluster header-only output has been inspected yet.

## Step 08 or Step 09 cannot find `Rscript`

### Symptom

The Step `08` or Step `09` wrapper fails with an error such as:

```text
Rscript executable was not found on PATH
Rscript does not exist
Rscript exists but is not executable
```

Step `08` may instead reach R and report:

```text
Missing required R package(s): ...
```

### Cause

Both steps require a supported `Rscript` executable. Step `08` additionally
requires these packages:

```text
VariantAnnotation
GenomicRanges
IRanges
S4Vectors
SummarizedExperiment
GenomeInfoDb
BiocGenerics
rtracklayer
```

The local workstation now has the signed Apple-silicon CRAN R `4.6.1` runtime
and a repository-local `renv` environment locked to Bioconductor `3.23`.
Activation is deliberately opt-in. A shell that does not set
`NORAD_USE_RENV=1`, a direct wrapper invocation that does not pass the selected
Rscript, or an unsynchronized project library may therefore fail even though
local setup exists.

A supported CSU R/Rscript path and compatible package set have not yet been
established in the batch/compute environment. Local setup does not prove
cluster visibility. The workflow intentionally does not install packages
automatically.

An executable visible on the login node may also be absent from a clean batch
or compute-node environment. Separately, the Step `09` R engine requires
`sha256sum` or `shasum` for hash verification; the shell preflight's
`python3` fallback does not satisfy that execute-time R-engine requirement.

Step `09` uses base R only (`stats`, `graphics`, and `grDevices`). A Step `09`
failure to resolve `Rscript` is therefore an executable/environment issue, not
evidence that the Step `08` Bioconductor package set is also required by Step
`09`.

### Fix

For local development, use the explicit guarded targets:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

`make r-restore` is the only package-installing action in that sequence.
Analysis scripts, SLURM wrappers, validators, and renderers must never call it
or install packages. `NORAD_USE_RENV=0` intentionally leaves ordinary R
startup unchanged; any value other than exact `0` or `1` is an error.

For a direct workflow script run, pass the executable with:

```bash
--rscript-bin /usr/local/bin/Rscript
```

For a future validated SLURM environment, export its batch-visible path:

```bash
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript
```

Confirm the package set in that same environment, then run:

```bash
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript make real-r-test
```

Run this probe in the same supported batch-visible environment intended for
Steps `08` and `09`, and confirm `sha256sum` or `shasum` there.

Do not substitute a fake R executable for semantic validation and do not call a
skipped real-R test a pass. `make real-r-test` runs the Step `08` suite followed
by the Step `09` suite; either runner reports `SKIP` only when the default
`Rscript` is absent, while an explicit bad override fails.

Current evidence is deliberately narrower:

```text
local runtime/package/headless-PDF checks pass
an empty cache-disabled binary restore passes
both real-R suites pass locally without SKIP
Step 08 raw lexical count validation and partition-overlap fixtures pass
Step 09 raw-byte PDF signature/EOF fixtures pass
cluster runtime and output evidence remain pending
```

These passes establish local fixture behavior only. They do not prove CSU
batch visibility, production input behavior, or cluster outputs. The
`step-09b1-real-r-fixes` documentation, clean-history, and push gate is
complete. Step `09c` is implemented locally at `b674a31`.
`artifact-schema-v1` is implemented and locally fixture-tested at `5f4d3b4`;
`artifact-adapters-v1` is implemented and locally fixture-tested at
`4dbd32d`. After its docpatch/push gate, the next descendant is
`artifact-run-summary`.

## `renv` startup uses sustained CPU or repeatedly creates directories

### Symptom

Starting the guarded local environment hangs or consumes sustained CPU before
the requested R expression runs.

### Cause

The local R `4.6.1`/macOS combination reproduced an `renv` sandbox
directory-creation loop. This was a startup-environment issue, not evidence of
an analysis loop.

### Fix

Use the repository Make targets, which set the reviewed guard:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
```

For a direct diagnostic command, preserve the same setting:

```bash
NORAD_USE_RENV=1 RENV_CONFIG_SANDBOX_ENABLED=FALSE \
  /usr/local/bin/Rscript -e 'sessionInfo()'
```

The tracked `.Rprofile` also supplies this default during opted-in activation.
Do not enable automatic snapshots or change the lockfile as a workaround.

## Local `renv` reports lock drift or missing Step 08 namespaces

### Symptom

`make r-check` reports that `renv::status()` is not synchronized,
`BiocManager::valid()` fails, or one of the eight direct Step `08` namespaces
does not load. It may instead report that the Bioconductor version cannot be
validated while showing a DNS/download failure for the configured release
metadata.

### Cause

The ignored project library may be absent, incomplete, or inconsistent with
the tracked lockfile. The runtime may also be different from the locked R
`4.6.1` / Bioconductor `3.23` contract. A metadata DNS/download error means the
check cannot reach the configured Bioconductor release source; by itself it
does not show package drift.

### Fix

Run the explicit restore and check:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
```

Run `r-check` in a network-capable developer environment when
`BiocManager::valid()` needs current release metadata. Require a successful
rerun; do not relabel the connectivity failure as a passing offline check.

Do not edit `renv.lock`, install into the project library manually, use the
damaged Homebrew checkout, or add source-build tooling merely to silence the
check. A necessary dependency or runtime contract change requires its own
reviewed implementation and lockfile update.

## Step 08 rejects a Step 07 receipt, VCF, hash, count, or sample order

### Symptom

Step `08` stops before or during semantic processing with a receipt/path/hash
mismatch, an unexpected input count, a VCF record-count mismatch, or a message
that VCF sample columns do not exactly match manifest order.

### Cause

Step `08` consumes exactly the declared partition-manifest Cartesian product
with `FWD_like` and `REV_like`. Each partition must have its valid Step `07`
receipt commit marker, and the receipt must agree with:

```text
cohort and partition selector
orientation order
exact VCF paths
sample-manifest and partition-manifest SHA-256 hashes
manifest sample count
VCF record count
exact manifest-ordered VCF sample columns
```

A stale manifest, copied or edited receipt, moved VCF, changed VCF header,
manually changed record count, or incomplete Step `07` transaction violates
that contract.

### Diagnose

Inspect the declared partition and its committed Step `07` set:

```bash
partition=<partition_id>
cohort=<cohort_id>
dir="results/mpileup/$cohort/$partition"

ls -lh \
  "$dir/$cohort.$partition.FWD_like.mpileup.vcf" \
  "$dir/$cohort.$partition.REV_like.mpileup.vcf" \
  "$dir/$cohort.$partition.step07_outputs.tsv"
awk -F '\t' 'NR == 1 || NR <= 3 { print }' \
  "$dir/$cohort.$partition.step07_outputs.tsv"
```

With the validated cluster bcftools path, compare each VCF sample list and data
row count with the manifest and receipt:

```bash
bcftools=/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
"$bcftools" query -l "$dir/$cohort.$partition.FWD_like.mpileup.vcf"
"$bcftools" view -H "$dir/$cohort.$partition.FWD_like.mpileup.vcf" | wc -l
```

### Fix

Restore the exact manifests used to produce Step `07`, or rerun the affected
Step `07` partition through its validated publication path. Do not edit a VCF
header, receipt hash, path, or count merely to satisfy Step `08`, and do not
replace the declared set with a glob.

These checks are locally tested behavior. No Step `08` real-R or cluster
receipt-mismatch incident has been observed.

## Step 08 rejects partition overlap, duplicate candidates, or malformed counts

### Symptom

Step `08` reports an overlapping partition selector, duplicate candidate ID,
missing or incorrect FORMAT/INFO definition, malformed or negative count,
partial DP/AD missingness, or AD greater than DP.

### Cause

The declared partitions must not overlap, and candidate identity is global
across partitions. VCF parsing also requires the Step `07` FORMAT/INFO
definitions and integer, non-negative, internally consistent DP/AD values.
`VariantAnnotation` can coerce some malformed lexical count tokens into parsed
numeric values while parsing; the local fixture observed an invalid `x`
becoming zero. Step `08` therefore performs a bounded-memory raw VCF pass
before semantic parsing and validates the consumed `FORMAT/DP`,
`FORMAT/AD`, and present `INFO/AD` token syntax and widths. A single `.` is
valid for a wholly missing AD vector; otherwise AD width must equal REF plus
every ALT. Silently deduplicating sites, truncating multiallelic vectors, or
accepting coerced malformed counts would change the declared analysis
universe.

Symbolic and non-SNV alternate alleles are different: valid instances are
counted and excluded intentionally rather than causing failure.

### Fix

Correct the partition manifest or regenerate the malformed upstream VCF from
the approved Step `07` workflow. Preserve ALT indexing and complete DP/AD pairs.
Do not delete duplicate rows, clamp counts, convert missing values to zero, or
change AD to fit DP after the fact.

These paths are covered by committed real-R fixtures, and the complete local
suite now passes without `SKIP`. Partition-overlap rejection was already
correct; the earlier unlabeled negative-fixture failure was misdiagnosed as an
overlap defect. The fixtures now identify each negative mode, assert the
expected overlap error, and cover malformed `FORMAT/DP`, `FORMAT/AD`, and
`INFO/AD` values before parser coercion can hide them.

The raw lexical check adds one bounded-memory streaming pass over each VCF.
Its production-scale I/O cost is not yet measured. During future runtime
promotion, benchmark a representative pilot or chromosome-scale input set in
an isolated output namespace and record input size, elapsed time, and maximum
RSS before running the full declared universe. A local fixture pass is not
production or cluster performance evidence.

## Step 08 finds a lock, partial output set, or input mutation

### Symptom

Step `08` reports:

```text
Step 08 lock already exists
Existing Step 08 outputs are incomplete; expected all three or none
an input or hash changed during Step 08
```

### Cause

Another run may own:

```text
results/vcf_preprocessed/<cohort>/.<cohort>.step08.lock/
```

Alternatively, a prior/manual operation may have left only part of the sites,
summary, and input-receipt set, or a manifest, GTF, Step `07` receipt, or VCF
may have changed after preflight. `step08_inputs.tsv` is published last as the
transaction commit marker, so one or two stable files are not a committed set.

### Fix

Inspect the lock owner, scheduler state, logs, all three final paths, and the
declared inputs before changing anything. Do not delete a foreign lock,
manufacture the missing receipt, combine files from different runs, or bypass
the hash check. If an active writer exists, wait for it to finish. If recovery
is required after an interrupted/manual operation, preserve evidence and make
the operator action explicit before restoring or regenerating a complete set.

The wrapper removes only its owned run-token scratch and lock paths and restores
the prior complete three-file set when a replacement fails after backup begins.
Lock, cleanup, input-mutation, and rollback behavior is locally tested with a
fake R executable; no Step `08` cluster incident has been observed.

## Step 09 rejects the sample manifest pairing

### Symptom

Step `09` reports a missing `replicate` column, empty replicate, duplicate
sample for one condition/replicate, unequal control/treatment replicate sets,
or fewer than two paired strata.

### Cause

Step `09` pairs only from explicit metadata in the full sample manifest. It
requires exactly one control and one treatment for each replicate, identical
replicate sets, and at least two strata. The current approved relationships
are:

```text
ABE_EV_2 / ABE_PUM1_2 -> replicate 2
ABE_EV_3 / ABE_PUM1_3 -> replicate 3
ABE_EV4  / ABE_PUM1_4 -> replicate 4
```

`ABE_EV4` demonstrates why pairing must not be inferred by parsing names.

### Fix

Add the approved `replicate` values to the full sample manifest before Step
`07`, validate it with:

```bash
python scripts/validate_manifest.py --manifest samples.tsv
```

and regenerate any Step `07`/Step `08` artifacts made with the old manifest.
`configs/step_09_pairs.NORAD_EV_PUM1.tsv` is a reference mapping only; do not
pass or merge it as a runtime overlay and do not relax pairing validation.

## Step 09 rejects Step 08 hashes, receipts, rows, or sample columns

### Symptom

Step `09` reports a sample/partition manifest hash mismatch, incomplete or
misordered Step `08` input receipt, row-count mismatch, duplicate candidate,
unexpected orientation policy, or missing/misordered `DP__`, `AD__`, or `AF__`
sample columns.

### Cause

Step `09` consumes exactly:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
```

and validates the full declared partition by `{FWD_like,REV_like}` universe.
The current sample and partition hashes must match every Step `08` input row.
A common future cause is adding `replicate` to `samples.tsv` only after Step
`07` or Step `08`; even a biologically correct metadata edit changes the file
hash and invalidates the old receipt chain.

### Fix

Restore the exact manifests used upstream or, when replicate metadata is the
approved new contract, rerun Steps `07` and `08` from that full manifest.
Never edit receipt hashes, reorder sample columns, copy rows between analyses,
or bypass the validation merely to make Step `09` run.

These failures are locally fake-R/shell tested. No Step `09` cluster mismatch
incident has been observed.

## Step 09 rejects R outputs, background statuses, or plot signatures

### Symptom

The R process exits successfully, but the wrapper rejects an all-sites,
significant-sites, summary, mutation-spectrum, or PDF output. Errors may refer
to a schema/status mismatch, sample-count inconsistency, background
status/fraction mismatch, significant-subset mismatch, summary count/hash
mismatch, mutation count/fraction mismatch, or missing PDF header/EOF marker.

### Cause

Step `09` treats R output as untrusted until it independently reconciles the
six-file transaction with the current manifests and Step `08` inputs. Common
causes include:

```text
using a different or edited R implementation
writing rows or sample columns in a different order
using non-strict threshold boundaries
miscomputing enabled-background AF/status
shrinking the BH family with a call-level filter
publishing a significant table that is not the exact ordered subset
writing incomplete/corrupt PDFs
an input changing during the run
```

### Fix

Use the committed Step `09` R implementation and inspect the first reported
invariant rather than hand-editing an output. Confirm the manifests and Step
`08` transaction did not change, then rerun through the shell wrapper so all
six temporary outputs are regenerated and validated together. Do not patch a
summary count, background status, hash, subset, or PDF signature to force
publication.

These independent output checks and rollback behavior are locally tested with
a fake R executable. The real-R suite also passes locally without `SKIP`. Its
PDF fixture now searches the trailing raw bytes for the `%%EOF` marker instead
of coercing arbitrary PDF bytes through locale-sensitive text conversion.
This was a fixture-portability correction, not production output evidence.
Cluster output validation remains pending.

## Step 09 finds a lock or incomplete six-output set

### Symptom

Step `09` reports:

```text
Step 09 lock already exists
Existing Step 09 outputs are incomplete; expected all six or none
Refusing to reuse an existing Step 09 scratch path
```

### Cause

Another run may own:

```text
results/editing/<analysis>/.<analysis>.step09.lock/
```

Alternatively, a manual/interrupted operation may have left only part of the
four-TSV/two-PDF result set or a run-token temp/backup path. The summary is
published last as the commit marker; fewer than six stable files is not a
committed transaction.

### Fix

Inspect the lock `owner`, scheduler state, logs, all six final paths, and hidden
run-token temp/backup paths. Do not delete a foreign lock, combine outputs from
different runs, manufacture a summary, or adopt an incomplete set. Wait for an
active owner or perform an explicit evidence-preserving recovery before
retrying.

## Step 09 rollback is incomplete and retains its lock

### Symptom

Step `09` reports that rollback was incomplete and that its owned lock is being
retained for operator recovery.

### Cause

After a replacement began, the wrapper could not remove a partial new final or
restore one or more run-token `.previous` backups. Automatically releasing the
lock would permit another writer to overwrite the remaining recovery evidence.

### Fix

Do not delete the retained lock blindly. Inspect:

```text
lock owner run_token and PID
SLURM job state and logs
all six final outputs
all matching hidden .previous backup paths
all matching hidden temporary paths
```

Decide explicitly whether to restore the complete previous six-file set or
remove an incomplete new set, validate the recovered state, record the
operator action, and only then remove the owned lock. The normal wrapper
cleanup removes only its own paths; incomplete-rollback lock retention is an
intentional safety boundary.

## Step 09c rejects evidence, status, hashes, or row counts

### Symptom

Step `09c` stops before publication with a schema, path, SHA-256, row-count,
candidate, decision, computational-status, or scientific-status error. A
review plan requesting:

```text
biological_interpretation_ready
```

is always rejected.

### Cause

Step `09c` consumes only the explicitly named manifests, Step `08`
transaction, Step `09` analysis directory, one-row review plan, and evidence
manifest. It requires declared evidence paths, hashes, row counts, IDs,
reviewers, policy versions, dates, statuses, decisions, and cross-table
relationships to agree. Missing and incomplete evidence must be represented
explicitly rather than hidden. `science_review_complete_exploratory` has
stricter completed-evidence and decision requirements. The current policy
deliberately reserves `biological_interpretation_ready` for a separately
approved future branch.

### Fix

Correct the source evidence or its declaration and rerun the dry-run. Do not
edit a hash or row count to force acceptance, replace missing evidence with an
empty file, infer a reviewer decision, downgrade an observed error, or request
the reserved ready state. Use the tracked example review plan, evidence
manifest, and header schemas at
`configs/step_09c_review_plan.example.tsv`,
`configs/step_09c_evidence_manifest.example.tsv`, and
`configs/step_09c_evidence_schemas/` as structural references. Preserve
production evidence under approved ignored results storage.

These checks are implemented and synthetic-fixture-tested locally. A fixture
pass is not proof that a production review is complete.

## Step 09c finds a lock, partial output set, changed input, or incomplete rollback

### Symptom

Step `09c` reports that the output is locked, refuses an incomplete/partial
transaction, reports that an input changed before publication, or retains
recovery paths after an incomplete rollback. A cleanup failure instead names
owned paths it could not remove; the lock or other paths may already be gone.

### Cause

One review transaction owns:

```text
results/scientific_validation/<review_id>/
  .<review_id>.step09c.lock
  .<review_id>.step09c.<run_token>.tmp/
  .<review_id>.step09c.<run_token>.previous/
  .<review_id>.step09c.<run_token>.RECOVERY.txt
```

The `.step09c.lock` path is a regular metadata file, not a directory. It is
created atomically with mode `0600` and records the review ID, PID, run token,
and creation date. The `.RECOVERY.txt` marker is a best-effort record created
only when rollback is incomplete, so it may be absent even when the error
reports retained recovery state.

The 13 stable TSVs must be all present or all absent. The review summary is
published last. A concurrent writer, interrupted/manual copy, changed input,
publication/rollback failure, or cleanup error can leave evidence that must be
inspected before another writer proceeds.

### Fix

Inspect any remaining lock metadata, all 13 stable outputs, the named input
hashes, matching run-token temporary/previous paths, and any best-effort
recovery marker. Do not delete a foreign lock, combine files from different
attempts, manufacture the summary, or discard a retained backup. Wait for an
active owner or perform an explicit, evidence-preserving recovery to either the
complete previous 13-file set or no set, validate the result, record the
operator action, and only then remove the owned lock when appropriate. For a
cleanup-only error, inspect exactly the paths named in the error because the
lock may already have been removed.

Lock, mutation, rollback, and cleanup paths are synthetic-fixture-tested only;
no production Step `09c` recovery incident has been observed.

## Step 09c fixture output is mistaken for a completed scientific review

### Symptom

A local test transaction is described as production evidence,
`science_review_complete_exploratory`, cluster proof, or biological
interpretation readiness.

### Cause

The committed fixtures are synthetic and exist to test validation and
publication contracts. Reported implementation/local-test statuses are
independent from production evidence-category and overall-science status.

### Fix

Describe the current state as:

```text
implemented and fixture-tested locally
production Step 09c evidence unavailable
production science remains evidence_incomplete
biological_interpretation_ready rejected
```

Only an inspected production evidence package and the applicable approved
policy can change those statements. Report generation will not do so.

## Artifact contract validation cannot import `jsonschema`

### Symptom

Running `scripts/validate_artifact_contracts.py` fails before validation with
an import error naming `jsonschema`, `referencing`, or another pinned Python
dependency.

### Cause

`artifact-schema-v1` added the JSON Schema Draft 2020-12 validator dependency
closure to `requirements.txt`. The selected Python environment is absent or
has not been synchronized with the current branch.

### Fix

Use the project virtual environment and install the tracked requirements as an
explicit local setup action:

```bash
cd /Users/elisteiger/dev/norad
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/validate_artifact_contracts.py --check-schemas
```

Do not add package installation to pipeline compute wrappers, SLURM jobs,
artifact adapters, run-summary builders, or report renderers.

## Artifact JSON or inventory validation fails

### Symptom

The read-only validator rejects a schema, record, or inventory with an error
about one of these contracts:

```text
duplicate JSON object key or non-standard NaN/Infinity value
schema name/version or record type
canonical run_contract_sha256
attempt supersession or selected-attempt state
implementation/local/runtime/cluster evidence coherence
scientific status or reserved biological_interpretation_ready
unresolved, globbed, redundant, or traversing path
inventory header, identifier, required value, ordering, or duplicate path
unsupported document/inventory reconciliation
```

### Cause

The v1 contracts fail closed. JSON must be strict; paths must already be
explicit and normalized; computational/scientific claims require their
declared evidence; and the inventory header must contain these tab-separated
fields in exactly this order:

```text
artifact_id
step_id
scope_type
scope_id
adapter
source_path
required
```

`required` is lowercase `true` or `false`. Each artifact ID and physical
source path must be unique, including after path normalization. Rows belonging
to one logical `(step_id, scope_type, scope_id)` must be contiguous.
`biological_interpretation_ready` and non-null readiness authorization are
intentionally rejected by v1.

Combining `--inventory` with a document performs reconciliation only for an
`artifact-record` or `run-summary`. A `scientific-review-record` or
`report-receipt` should be validated without `--inventory`.

### Diagnose

First validate the tracked contracts and inventory independently:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --check-schemas

.venv/bin/python scripts/validate_artifact_contracts.py \
  --inventory configs/artifact_inventory.example.tsv
```

Then validate the explicit record with the matching public schema:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --schema artifact-record \
  --document /explicit/path/to/artifact-record.json
```

Allowed schema names are:

```text
artifact-record
scientific-review-record
run-summary
report-receipt
```

### Fix

Correct the declaring inventory or JSON producer at the first reported
invariant. Do not edit a hash, status, evidence role, attempt link, source
path, or readiness value merely to force acceptance. A change to one of the
five canonical run-identity components requires a new `run_id`; an
identical-contract retry requires a distinct attempt ID. An inventory-only
revision is adapter-attempt metadata and does not by itself change run
identity.

The focused regression command is:

```bash
.venv/bin/python -m pytest -q tests/test_artifact_schema_contracts.py
```

Current local focused evidence is `54 passed`. This is schema/fixture evidence,
not production artifact validation.

## Artifact adapter rejects `--run-contract` or an existing run ID

### Symptom

`build_artifact_index.py` reports a missing/invalid `--run-contract`, an
invalid canonical contract hash, or:

```text
Existing run_id is bound to a different immutable run contract field
```

### Cause

The adapter CLI requires a strict JSON document containing exactly the
declared run-contract hash plus the sample-manifest, reference-contract,
partition-manifest, primary-analysis ID, and primary-analysis-policy identity
components. An existing output-root receipt binds that local `run_id` to
those values only within the selected output root while the committed receipt
is retained. This is not a global or permanent run registry.
The expected-artifact inventory is not one of those identity components.

### Fix

Correct an invalid declaration at its source. If an immutable identity value
changed, choose a new `run_id`; never edit the old receipt or run-contract hash
to conceal the change. If only the explicit inventory changed, retain the same
run ID and rerun with the revised inventory. Execute mode will validate the
prior complete transaction and publish a new superseding
`adapter_attempt_id`.

## Artifact adapter finds a lock, partial transaction, or incomplete rollback

### Symptom

The adapter reports an existing lock, invalid/incomplete prior receipt,
changed source, unsafe symlink, rollback failure, cleanup failure, or retained
recovery paths.

### Cause

Possible owned or recovery paths for one run include:

```text
results/artifacts/<run_id>/.<run_id>.artifact-index.lock
results/artifacts/<run_id>/.artifact-index.<run_token>.tmp.*
results/artifacts/<run_id>/.artifact-index.<run_token>.previous.*
results/artifacts/<run_id>/.artifact-receipt.<run_token>.tmp.tsv
results/artifacts/<run_id>/.artifact-receipt.<run_token>.previous.tsv
results/artifacts/<run_id>/.artifact-index.<run_token>.RECOVERY.txt
```

The records directory, ordered index, and receipt are one transaction, with
the receipt published last. A concurrent writer, source mutation, interrupted
manual copy, publication failure, or incomplete restoration can leave state
that must be inspected before another writer runs. A receipt is
re-quarantined only if restored-transaction validation fails;
first-publication rollback has no prior receipt; and the recovery marker is
best-effort, so not every failure leaves every listed path.

### Fix

Inspect lock metadata, current records/index/receipt, every reported or
remaining temporary, backup, quarantine, or recovery-marker path that is
present, source paths, and any active process before changing anything. Do
not delete a foreign lock, combine files from different attempts, manufacture
a receipt, or discard recovery evidence. Recover either the complete prior
transaction or a clean first-publication state, validate it, record the
operator action, and only then remove a lock whose ownership is proven.

## Artifact receipt is complete but evidence records are not

### Symptom

`<run_id>.artifact_receipt.tsv` records `transaction_state=complete`, while the
index contains missing, failed, incomplete, externally unavailable, or
unknown artifacts; runtime/cluster statuses remain `not_run`; or no Step
`09c` science state is propagated.

### Cause

Transaction completion means the adapter records, index, and receipt were
validated and committed together. It does not mean every expected artifact
exists or that computation/science was validated. Adapter v1 populates
implementation evidence but deliberately leaves each generated record's
local-testing, runtime-validation, cluster-dry-run, and cluster-proof fields
at `not_run`; it has no native-validation import path.

Step `09c` science propagation is separate. Both permitted science states
require its complete 13-output summary-last scope, plan/summary identity, all
ten required published category declarations, and exact
evidence-ID/payload/count reconciliation. `evidence_incomplete` may retain
missing or incomplete categories, pending decisions/adjudication, and no
completion date. `science_review_complete_exploratory` additionally requires
complete or justified `not_applicable` categories, all required decisions
complete and recorded, exact equality between the selected and adjudicated
`(analysis_id, candidate_id)` identity sets, and a completion date.
Non-provisional orientation and a source declaration of cluster proof have
their additional orientation-decision and optional `computational_validation`
gates.

### Fix

Treat the explicit record statuses as the result. Do not try to promote them
manually or by adding undeclared native evidence. Later validator packages
may publish typed validation evidence through their own contracts; the
run-summary package may aggregate that evidence but must never infer or
promote it. If Step `09c` science propagation was expected, correct its
declared transaction or evidence relationships and rerun the adapter. Keep
production science `evidence_incomplete` when reconciliation does not pass,
and continue rejecting `biological_interpretation_ready`.

## A passing artifact-schema fixture is mistaken for an artifact index, report, or validation evidence

### Symptom

A passing schema/inventory command or committed example JSON is described as:

```text
a generated results/artifacts transaction
a canonical production run summary
an HTML/PDF report
proof that declared source files exist or match their hashes
production or cluster validation
a completed scientific review or biological-readiness result
```

### Cause

`artifact-schema-v1` defines and validates declarations. Its 67-row inventory
and valid JSON records are synthetic fixtures. The validator is read-only and
does not discover pipeline outputs, build adapter records, inspect production
source contents, publish files, render reports, or run analysis. Within a
record it validates the canonical run-contract hash. The implemented
`artifact-adapters-v1` layer additionally validates an existing output-root
receipt before allowing the same `run_id` to be rebuilt.

### Fix

Describe the current boundary as:

```text
artifact-schema-v1 implemented at 5f4d3b4
shared common schema plus four public Draft 2020-12 schemas
67-row synthetic explicit physical inventory
read-only validator and 54 focused tests pass locally
artifact-adapters-v1 implemented at 4dbd32d
49 read-only adapters and 50 focused tests pass locally
no production artifact index, run summary, report, or production evidence
artifact-run-summary is next
```

Keep production and cluster status unchanged. Keep production science
`evidence_incomplete`, and continue rejecting
`biological_interpretation_ready`.

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

A future troubleshooting index may summarize repeated failure patterns as
symptom, likely cause, confirmation command, and fix. Keep the generic index as
a deferred roadmap idea until enough real failures exist. The artifact-schema
validator, inventory, and explicit artifact adapter indexer are now
implemented, so their concrete failure modes are documented above; do not add
entries that imply generated run summaries, general cleanup tools, reports,
foundation tools, or per-step validators exist before their branches
implement them.

## General success checklist

A computational stage is only `cluster-proven` when all of these are true:

```text
1. Dry-run completed 0:0.
2. Dry-run command/context looked correct.
3. Execute job completed 0:0.
4. stderr is empty or contains only known harmless messages.
5. Expected output files exist.
6. Expected output files are non-empty where appropriate.
7. Stage-specific schemas, hashes, counts, sample order, and cleanup contracts
   reconcile.
```

Do not promote a downstream step to cluster execution until its upstream
dependency passes this checklist. Local implementation of later steps may
proceed on the required descendant branches after each implementation/docpatch
gate is complete.

This checklist proves runtime execution, not biological interpretation.
Orientation policy, annotation semantics, statistical robustness, candidate
adjudication, and limitations require the separate post-Step-09 scientific
evidence-and-decision gate. Do not call CMH-ranked candidates biologically
validated solely because the files pass this checklist.
`science_review_complete_exploratory` still requires provisional labeling;
`biological_interpretation_ready` is currently reserved and must be rejected
until a separately approved scientific-policy branch unlocks its exit
criteria.
