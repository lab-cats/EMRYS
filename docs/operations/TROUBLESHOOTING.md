# Troubleshooting

Troubleshooting notes for the NORAD / Novogene Remora RNA-seq pipeline.

Use this file when something fails or behaves unexpectedly. Exact supported
commands remain in [`RUNBOOK.md`](RUNBOOK.md); each fix links there when the
runbook already owns the identical invocation.

## Issue index

- [Cluster environment, tools, submission, and early-stage symptoms](#tmpdir-localtmp-is-not-writeable)
- [Structured stage-validation and recovery symptoms](#structured-validation-response)
- [Preflight, provenance, storage, local validation, and R symptoms](#runtime-preflight-profile-or-output-contract-is-rejected)
- [Step `08`, Step `09`, and scientific-evidence symptoms](#step-08-structured-validation-reports-transaction-disagreement)
- [Artifact, run-summary, dependency-restore, and report symptoms](#artifact-contract-validation-cannot-import-jsonschema)
- [Logs, Picard read groups, and concurrent-lane symptoms](#wrong-log-interpretation-empty-err-file)
- [Future taxonomy](#future-troubleshooting-taxonomy) and
  [general success checklist](#general-success-checklist)

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

Use the exact [runbook `TMPDIR` submission pattern](RUNBOOK.md#tmpdir).

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

The wrapper also has a characterized unguarded later `JAVA_HOME` diagnostic.
If `JAVA_HOME` is completely unset, a usable `JAVA_BIN_OVERRIDE` or `PATH`
selection can still be followed by an unbound-variable abort before producer
delegation. Preserve the job streams and environment; do not interpret that
abort as a Picard, samtools, or input failure and do not repair it during the
physical migration.

If CSU HPC provides a supported Java 17 executable, use the exact
[Step `04` override command](RUNBOOK.md#step-04-markduplicates).

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

SLURM does not create the parent directory for the output and error paths
shown in the [runbook logging contract](RUNBOOK.md#logs).

### Fix

Create the log directory with the exact [runbook command](RUNBOOK.md#logs)
before submitting jobs.

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

Find the actual log name with the
[manual job-checking command](RUNBOOK.md#manual-job-checking), then tail the
matching files:

```bash
tail -120 logs/<actual-prefix>-<JOBID>.out
tail -120 logs/<actual-prefix>-<JOBID>.err
```

If the cluster shell helpers are installed, use the exact
[helper sequence](RUNBOOK.md#optional-cluster-shell-helpers).

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
The current producer is
`src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh`;
do not recreate the removed flat path as a workaround.

## RSeQC `infer_experiment.py` not found

### Symptom

Step 03 fails because `infer_experiment.py` cannot be found.

### Cause

RSeQC is not currently known as a global module. Step `03` first looks for
`.venv/bin/infer_experiment.py` relative to its invocation CWD and otherwise
resolves the command name through `PATH`.

### Fix

Use the project executable and fallback described in the
[Python and RSeQC runbook section](RUNBOOK.md#python-and-rseqc).

The final SLURM wrapper optionally sources `.venv/bin/activate` from the
checkout selected by `SLURM_SUBMIT_DIR`. For a direct invocation outside the
checkout root, pass an explicit absolute `--infer-experiment-bin`; do not rely
on the CWD-relative default to follow the repository.

## RSeQC `infer_experiment.py` path exists but is not executable

### Symptom

Step 03 fails tool validation even though the path exists.

### Cause

Path-style tool arguments are required to be executable.

### Fix

Inspect why the selected environment supplied a non-executable file. If that
environment is intentionally operator-owned, make it executable there:

```bash
chmod +x .venv/bin/infer_experiment.py
```

Otherwise preserve it and pass a separately established executable path with:

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

These are historical mechanical paired-read orientation fractions. A prior
operational note described the dominant second group as reverse/first-strand-
style, but the current evidence contract does not validate that biological or
tool-policy mapping.

If another sample is ambiguous, compare:

```bash
cat results/qc/strandedness/<sample>.infer_experiment.txt
```

and check that the BAM, either adjacent BAI, BED12, sample, selected RSeQC
executable, job ID, and logs all belong to the same intended attempt. Preserve
the three group labels as mechanical evidence. Do not update manifest
`strandedness`, choose a downstream tool option, or call the sample biologically
stranded from this route.

## Step 03 producer or wrapper leaves a partial, empty, or stale report

### Symptom

The producer exits nonzero after changing the named native report, a zero-exit
producer leaves structurally malformed nonempty bytes, or the scheduler exits
zero even though the named report predates the apparent attempt. A failing
RSeQC child can leave partial stdout; an empty successful child can leave a
zero-byte report.

### Cause

The producer redirects RSeQC stdout directly to the final report before the
child outcome is known. It has no lock, staging path, no-clobber rule, backup,
receipt, stable-input recheck, rollback, or recovery marker, and it checks only
that successful child output is nonempty. The wrapper's execute post-check
also tests only that the named final report is nonempty, so an exit-`0` child
that emits nothing can rediscover stale predecessor bytes and let the job
succeed. These are characterized defects, not valid publication or recovery.

### Fix

Before retry, deletion, or same-name reuse, preserve the native report and its
filesystem metadata, unrelated files in the output directory, producer stdout
and stderr, scheduler stdout and stderr, job ID/accounting and logs, selected
tool identity/path, BAM plus the admitted BAI, and BED12. Absence of a lock,
stage, backup, receipt, or recovery artifact is not cleanup or adoption
authority. Git rollback changes tracked implementation only and cannot restore
runtime evidence.

Inspect the persisted bytes with the final validator in dry-run mode; this does
not rerun RSeQC or publish a report:

```bash
.venv/bin/python \
  src/norad/evidence/collect_RSeQC_paired_orientation_evidence/validate_step_03_rseqc_orientation.py \
  --scope-id <sample_id> \
  --infer-report results/qc/strandedness/<sample_id>.infer_experiment.txt \
  --output results/qc/validation/03/<sample_id>.validation.tsv
```

Producer or scheduler exit `0` proves neither current-attempt identity nor
validator pass. Validator exit `0` can render `status=fail` rows. Validator
exit `2` publishes nothing new for unreadable/unsafe input, invalid arguments,
stable-input mismatch, or unsafe publication and preserves an existing valid
report. Record an operator recovery decision before any rerun or cleanup.

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

## Structured validation response

For every step-validation TSV, command/publication success is distinct from
the check rows: a successfully published `status=fail` row is valid evidence,
not a passing check. Unsafe input, tool, CLI, or publication state remains a
process failure.

For any failed row, inspect the exact declared artifacts, producing job and
logs, explicit tool path/version when applicable, and the linked
[functional contract](RUNBOOK.md#workflow-contract-and-validation-convention).
Regenerate only through the separately authorized functional owner. Never edit
a report or native artifact into agreement, substitute a sibling or globbed
path, run repair/analysis inside the validator, or promote local validation to
runtime, cluster, scientific-review, or biological evidence. Owner-specific
differences follow; transaction recovery remains in its separate entries.

## Step 00a structured validation reports failed checks

### Symptom

`novogene_ref.validation.tsv` contains `status=fail` for index members, FASTA
or GTF identity, ordered contig names/lengths, or `sjdbOverhang`.

### Cause

The explicit index may be incomplete or disagree with the declared FASTA, GTF,
ordered contigs, parameter-path base, or approved overhang.

### Fix

Follow the [common response](#structured-validation-response). Resolve relative
`genomeParameters.txt` paths only against `--parameter-path-base`; never
reinterpret them automatically relative to the index.

## Step 00a validation report lock or predecessor blocks publication

### Symptom

Execute mode rejects a lock, unsafe output parent, invalid previous report, or
replacement/rollback state.

### Cause

One scope owns one exact `.validation.tsv` and its adjacent lock/run-token
paths. A concurrent writer, foreign lock, symlink, hand edit, partial copy, or
interrupted replacement prevents safe publication.

### Fix

Inspect the lock metadata, stable report, and matching `.tmp`/`.previous`
paths. Do not delete a foreign lock or manufacture a passing TSV. Establish
ownership, recover the validated predecessor or clean first-publication state,
record the operator action, and rerun dry-run before execute mode.

An absent lock does not by itself prove a clean state: Phase `01b` fault
injection confirmed that an incomplete restoration can leave `.previous`
bytes after the shared publisher has removed its lock.

## Validation publication leaves ambiguous recovery state

### Symptom

After an injected or real publication exception, a run-token `.previous` or
`.tmp` survives without its expected lock or recovery marker; a late-created
foreign final is missing; or runtime preflight returns success while its owned
lock remains. A lock-fsync failure may also leave a preflight lock and open
descriptor until the process exits.

### Cause

Phase `01b` characterization confirms that the current publishers do not all
have the same exception boundary. The shared step-validator publisher can
remove lock protection after failed restoration and can unlink a final that
appears during its publication move. Reference and storage multi-file
publishers can leave backups without a lock/marker after incomplete rollback.
Runtime preflight can fail before descriptor ownership enters its cleanup
block or swallow lock-unlink failure after publishing successfully.

### Diagnose

Stop retries and inspect the exact final, run-token `.tmp`/`.previous`, lock,
process, filesystem identity, and command log together. Treat surviving bytes
as recovery evidence even when no lock or marker remains. Establish whether a
late final belongs to another process; do not infer ownership from its name
alone.

### Fix

There is no automatic recovery fix in Phase `01b`. Preserve the affected
directory and logs, establish ownership, and choose an explicit operator
recovery or a new output path. Do not delete a lock, backup, stage, or foreign
final merely because a characterization test reproduces the state. Production
corrections require the later reliability review and a bounded Phase `03`
package.

## Step 00b structured validation reports BED12 or GTF disagreement

### Symptom

The Step `00b` validation TSV reports failed structure, sorting, block,
uniqueness, or GTF-agreement checks.

### Cause

The BED may be malformed or unsorted, contain invalid block sizes/offsets or
duplicate transcript names, or no longer equal deterministic normalization of
the explicit GTF exon models.

### Fix

Follow the [common response](#structured-validation-response), comparing the
BED with deterministic exon normalization of the exact GTF. Regenerate only
through
`src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py` after confirming that
conversion contract. Preserve scheduler logs, the intermediate BED, and the
final BED together when failure residue or ownership is ambiguous.

## Step 00c FAI/DICT validation fails

### Symptom

Step `00c` fails with a message that the FASTA index and sequence dictionary
contigs/lengths do not agree, or a nonzero producer attempt leaves a final FAI
while the final DICT is absent.

### Cause

`refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` are shared
reference sidecars. Either can be stale, empty, malformed, or generated from a
different FASTA. Separately, the characterized producer can publish the final
FAI before final DICT publication fails; that retained FAI is incomplete-attempt
evidence, not successful transaction output.

### Fix

Do not let Step `05` create or repair these files inside a per-sample job. Use
the exact final producer commands in the [runbook](RUNBOOK.md#step-00c-gatk-reference-sidecars)
only after confirming the FASTA/FAI/DICT provenance and ownership. Preserve the
producer context, scheduler stdout/stderr, lock state, run-token temporary
paths, and final FAI/DICT state before any cleanup or rerun decision. Step `00c`
does not overwrite invalid existing sidecars by default. After provenance and
ownership are established, a separately authorized rerun may reuse a valid FAI
and generate only the missing DICT; relocation neither fixes nor blesses the
partial-publication defect.

## Step 00c structured validation reports FASTA/FAI/DICT disagreement

### Symptom

The Step `00c` validation TSV reports failed FASTA, FAI, or DICT structure, or
failed ordered contig-name/length agreement.

### Cause

One explicit input is malformed, truncated, or belongs to a different
reference. The validator reports disagreement but does not infer, regenerate,
or repair shared reference inputs.

### Fix

Follow the [common response](#structured-validation-response) and resolve the
FASTA/FAI/DICT provenance before using the exact final
[validator command](RUNBOOK.md#step-00c-gatk-reference-sidecars) or producer for
a missing sidecar. Preserve the explicit inputs and report together. A private
reference-owner loader failure is a checkout-integrity diagnostic; do not mask
it with a `PYTHONPATH` workaround. Failed current validation does not rewrite
historical cluster evidence or authorize input repair.

## Step 01 structured validation reports STAR output disagreement

### Symptom

The Step `01` validation TSV reports a missing/empty output, invalid BAM
container, malformed final log, missing or invalid mapping percentage, or
malformed splice-junction row.

### Cause

The five explicit paths may not belong to one complete STAR attempt, an output
may be truncated, or the STAR log/table shape may not satisfy the declared
contract.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact BAM, three STAR logs, SJ table, scheduler evidence, and native logs before
deciding whether a separately authorized alignment rerun is required. Local
validation does not replace historical cluster evidence. Preserve partial
direct-final artifacts and follow the final-path
[Step `01` commands](RUNBOOK.md#step-01-star-alignment) and
[owner diagnostics](../../src/norad/stages/align_RNA_reads_with_STAR/README.md#diagnostics-recovery-and-evidence);
the characterized producer and scheduler residue is not authority to clean or
rerun automatically.

## Step 02 canonical BAM rollback leaves a prior-BAI-only lockless pair

### Symptom

Step `02` returns nonzero after a publication fault and reports both rollback
and restoration failure. The canonical BAM is absent, the prior BAI remains,
and no owned lock, backup, run-token scratch, receipt, or recovery marker is
present.

### Cause

The producer moves the prior pair to run-token backups, then publishes the new
BAM and BAI separately. Restoration moves are best-effort and their failures
are ignored before cleanup removes the backup paths. The characterized oracle
fails final BAI publication and then restoration of the prior BAM, producing
exactly this prior-BAI-only state and losing the prior BAM bytes. Relocation
preserves this ambiguous/data-loss defect; it does not approve or repair it.

### Fix

Stop retries. Preserve the complete pair directory, producer and scheduler
stdout/stderr, any still-visible run-token temporary and backup paths, and the
exact bytes and metadata of every final or backup path. Record the checkout,
job/run token, tool identity, and filesystem context. Absence of a lock,
backup, receipt, or marker does not prove clean state and does not authorize
deletion, adoption, reconstruction, or retry. Make a separately reviewed and
authorized recovery decision only after ownership and available evidence are
established; the characterization test is not recovery authority.

## Step 02 BAM-validation helper cannot load

### Symptom

The Step `02`, Step `04`, or Step `05` validator exits `2` before report
publication with:

```text
ERROR: unable to load NORAD BAM-validation owner at <path>: <type>: <reason>
```

### Cause

The caller could not exact-load or validate private
`src/norad/libraries/bam_validation.py`. The file may be missing, resolve to a
foreign cached path, be only partially initialized, or lack callable
`run_tool`/`parse_header`. This is a checkout-integrity failure, not a tool or
input mismatch.

### Fix

Inspect the exact named file, Git checkout, and process module-cache context.
Use the focused helper suite in the
[Step `02` runbook](RUNBOOK.md#step-02-canonical-sort-read-group-tagging-and-bam-indexing).
Do not add `PYTHONPATH`, install a package, invoke a public helper CLI, copy the
helper into a stage, or restore a legacy validator path.

## Step 02 structured validation reports canonical BAM disagreement

### Symptom

The Step `02` validation TSV reports an invalid BAM/BAI container, quickcheck
diagnostic, non-coordinate sort order, missing or mismatched read-group
header, or alignments without the sample RG tag.

### Cause

The pair may be incomplete or may not come from the hardened Step `02`
transaction. The selected samtools executable may also fail to inspect the
file in the current runtime context.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact BAM/BAI, samtools path/version, header, and count evidence; any sorting,
indexing, or read-group regeneration belongs to separately authorized Step
`02` execution. Use only the final producer/validator paths in the
[Step `02` runbook](RUNBOOK.md#step-02-canonical-sort-read-group-tagging-and-bam-indexing).

## Step 02b producer or wrapper leaves a partial, mixed, or stale evidence pair

### Symptom

The producer exits nonzero after changing one named evidence file, or the
scheduler exits zero even though the quickcheck and flagstat bytes appear to
come from different attempts. An older sibling or both stale named files may
remain in place.

### Cause

The producer writes quickcheck and flagstat directly to final paths without a
lock, stage, backup, receipt, rollback, stable-input recheck, or output-set
commit marker. Quickcheck failure is normalized to producer exit `1` after its
combined child diagnostic replaces that final; flagstat failure can follow a
new quickcheck PASS marker and leave partial flagstat stdout. The wrapper checks
only that both named files exist, so an exit-`0` child that emits nothing can
rediscover stale predecessors and report success. These are characterized
defects, not valid mixed-attempt publication.

### Fix

Preserve both evidence files, unrelated directory entries, producer stdout and
stderr, scheduler stdout and stderr, job/accounting identity, BAM/BAI identity,
and available filesystem metadata. There may be no lock, attempt directory,
backup, receipt, or recovery marker; absence of those paths is not cleanup,
adoption, or retry authority. Do not delete or rerun the same names until the
operator establishes which attempt owns each file and records a recovery
decision.

Use the final validator in dry-run mode to inspect the persisted bytes without
rerunning samtools:

```bash
.venv/bin/python \
  src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py \
  --scope-id <sample_id> \
  --quickcheck results/qc/bam/<sample_id>.quickcheck.txt \
  --flagstat results/qc/bam/<sample_id>.flagstat.txt \
  --output results/qc/validation/02b/<sample_id>.validation.tsv
```

Producer or scheduler exit `0` does not prove validator pass. Validator exit
`0` can print or publish `status=fail` evidence rows; it records disagreement
and does not repair or gate the workflow.

## Step 02b structured validation reports BAM-QC disagreement

### Symptom

The Step `02b` validation TSV reports a noncanonical quickcheck marker,
malformed or duplicate flagstat rows, invalid counts, or mapped records
greater than total records.

### Cause

The persisted QC files may be incomplete, manually altered, or drawn from
different attempts. This validator intentionally reads the evidence rather
than rerunning samtools.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
persisted quickcheck and flagstat files plus their producing job/log. This
validator reads persisted evidence and does not rerun samtools. Use only the
final producer/validator paths in the
[Step `02b` runbook](RUNBOOK.md#step-02b-bam-qc), and follow the
[mixed/stale-pair route](#step-02b-producer-or-wrapper-leaves-a-partial-mixed-or-stale-evidence-pair)
before any same-name retry.

## Step 03 structured validation reports RSeQC fraction disagreement

### Symptom

The Step `03` validation TSV reports missing/duplicate labels, a nonnumeric or
out-of-range fraction, or three fractions that do not sum to one within the
declared tolerance.

### Cause

The persisted RSeQC output may be malformed, truncated, manually changed, or
from an unexpected report version.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact RSeQC report and producing job/log. Preserve the paired-orientation
groups as mechanical labels; do not rename them as biological strands. Use
only the final validator and commands in the
[Step `03` runbook](RUNBOOK.md#step-03-rseqc-strandedness--orientation-inference),
and follow the
[partial/empty/stale route](#step-03-producer-or-wrapper-leaves-a-partial-empty-or-stale-report)
before same-name reuse. Validator exit `0` may publish failed evidence rows;
exit `2` publishes nothing new and is not a failed-row synonym.

## Step 04 producer or wrapper leaves a partial, mixed, or stale output triplet

### Symptom

Step `04` exits nonzero after Picard, quickcheck, index, or final checks and
the final BAM, BAI, and metrics do not share one attempt. Or the scheduler exits
zero even though the delegated child created no current output. There may be a
partial new BAM or BAI, empty/new metrics, predecessor bytes, or an entirely
stale nonempty triplet. No lock, stage, backup, receipt, or recovery marker is
present.

### Cause

The producer writes Picard BAM and metrics directly to final paths, then
quickchecks and indexes the BAM directly at the final BAI path. It has no lock,
stage, no-clobber rule, stable-input recheck, rollback, or all-or-none
transaction. Characterized failures include Picard exit `42`, quickcheck exit
`43`, index exit `44`, and a final empty-metrics rejection; each can leave a
different new/partial/prior triplet. Controlled admitted-input mutation also
goes undetected. The wrapper only checks that all three final names are
nonempty after a zero-exit child, so an unchanged stale triplet can satisfy its
post-check. These are preserved defects, not valid recovery states.

### Fix

Stop same-name retries and downstream Step `05` reads. Preserve exact BAM/BAI/
metrics bytes and metadata, the canonical input pair, unrelated files,
producer and scheduler stdout/stderr, job ID/accounting and logs, checkout,
Picard jar, selected Java path and actual version, samtools path/version, and
`TMPDIR`. Absence of a lock or recovery artifact does not prove clean state and
does not authorize deleting, adopting, or reconstructing any final.

Rule out every downstream reader before a separately reviewed retry. Use an
isolated output and metrics destination so the questioned triplet remains
unchanged, then validate the new explicit triplet with the final command in the
[Step `04` runbook](RUNBOOK.md#step-04-markduplicates). Validator exit `0`
may still contain `status=fail`; exit `2` publishes nothing new and is not a
failed-row synonym. Git rollback changes tracked implementation only and
cannot recover or authenticate runtime artifacts.

## Step 04 structured validation reports BAM or duplication-metrics disagreement

### Symptom

The Step `04` validation TSV reports an invalid BAM/BAI pair, quickcheck or
sort/read-group failure, or malformed/out-of-range Picard duplication metrics.

### Cause

The three explicit outputs may be incomplete or from different attempts, or
the selected samtools runtime cannot inspect the BAM. Picard metrics may lack
the required single data row or contain inconsistent counts/fraction.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact BAM/BAI/metrics triplet, samtools path/version, producing job, and logs.
Use only the final validator and commands in the
[Step `04` runbook](RUNBOOK.md#step-04-markduplicates), and follow the
[partial/mixed/stale triplet route](#step-04-producer-or-wrapper-leaves-a-partial-mixed-or-stale-output-triplet)
before any same-name retry. Duplicate marking or BAM repair belongs to
separately authorized Step `04`. Validator exit `0` may publish failed evidence
rows; exit `2` publishes nothing new and is not a failed-row synonym.

## Step 05 producer or wrapper leaves a partial rollback failure or stale pair

### Symptom

Step `05` returns nonzero after staging, backup, publication, final
revalidation, restoration, signal handling, or cleanup, and the final BAM/BAI
pair is absent, partial, mixed, or ambiguous. A particularly severe state has
the prior BAM missing and the prior BAI restored while no backup, lock,
scratch, or recovery marker remains. Alternatively, the scheduler exits zero
even though the delegated child created nothing and two stale nonempty final
files were already present.

### Cause

The producer validates a staged pair, moves a complete predecessor to two
run-token backups, publishes BAM and BAI sequentially, and revalidates the
final paths. Its restoration moves are best-effort. Cleanup can then erase the
backups, output-directory lock, run-token scratch, GATK temp directory, and all
recovery evidence after a restoration failure. Inputs are not snapshot-
rechecked, the lock covers the whole output directory, and successful
publication has no receipt. The characterized injected BAI-publication exit
`67` followed by prior-BAM-restoration exit `68` propagates `67`, leaves only
the prior BAI at its final name, preserves unrelated bytes, and erases the
remaining owned recovery paths. This is an ambiguous/data-loss defect, not a
successful rollback.

The wrapper checks only that both final names are nonempty after a zero-exit
child, so unchanged stale files can satisfy it. Its Bash `3.2` empty-array
dry-run defect, submit-CWD fallback, body-level `logs/` mutation, tolerated
module diagnostics, warning-only GATK/samtools preflight, and Java/GATK/
samtools version-command failures are separate preserved states. The delegated
producer still rejects unusable tools. None of these paths proves that a final
pair belongs to the current job.

### Fix

Stop same-name retries, the lock owner, and downstream Step `06` reads. Before
cleanup or recovery, preserve every surviving final BAM/BAI, run-token BAM/
BAI, alternate GATK index, predecessor backup, GATK-temp directory, lock and
owner file, all five input/reference files, unrelated directory entries,
producer stdout/stderr, scheduler stdout/stderr, job ID/accounting and logs,
checkout, submit CWD, environment overrides, selected GATK/Java/samtools
paths, and exact version diagnostics. Record which expected recovery paths are
absent; absence is not proof of cleanliness.

Do not combine pair members from different attempts, infer ownership from
timestamps, remove a foreign lock, reconstruct a missing BAM, adopt stale
wrapper success, or rerun into the questioned output directory. Rule out every
active producer and reader first. Any separately authorized diagnostic retry
uses an isolated output directory so the questioned evidence remains
unchanged. Git rollback changes tracked implementation only and cannot recover,
remove, or authenticate runtime artifacts.

Use the final validator in dry-run mode to inspect a complete surviving pair;
this may print `status=fail` rows and does not establish attempt identity or
repair anything:

```bash
.venv/bin/python \
  src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py \
  --scope-id <sample_id> \
  --bam results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam \
  --bai results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --samtools-bin /absolute/path/to/samtools \
  --output results/qc/validation/05/<sample_id>.validation.tsv
```

## Reference-contig owner cannot load

### Symptom

Reference provenance or the final Step `00c`/`05` validator exits `2` before
publication with:

```text
ERROR: unable to load NORAD reference-contig owner at <path>: <type>: <reason>
```

### Cause

The caller could not exact-load or validate final neutral
`src/norad/libraries/reference_contigs.py`. The file may be missing, resolve to
a foreign cached path, be partially initialized, lack its readiness marker,
expose an invalid `ReferenceContigError`, or lack callable `parse_fasta`,
`parse_fai`, or `parse_dict`. This is a checkout-integrity failure, not a
reference-content mismatch and not authority to package the neutral owner.

### Fix

Inspect the exact named file, Git checkout, and process module-cache context.
Use `tests/libraries/test_reference_contigs.py`, the final owner-local validator
tests, and public
`tests/evidence/reference_provenance/test_reference_provenance.py`. Do not add
`PYTHONPATH`, install a package, replace the private module cache, copy the
parser into a consumer, or restore a legacy bridge. Content disagreement after
a successful load belongs to the applicable consumer-specific evidence or
validation route; the Step `05` route follows below.

## Step 05 structured validation reports output or reference disagreement

### Symptom

The Step `05` validation TSV reports a BAM/BAI, quickcheck, sort/read-group,
or FASTA/FAI/DICT agreement failure.

### Cause

The split output pair may be incomplete or from another attempt, or one shared
reference sidecar may not match the explicit FASTA.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact output pair, reference triplet, samtools path/version, and producing
job/log. Reference repair belongs to Step `00c`; split-output regeneration
belongs to Step `05`. Use only the final commands in the
[Step `05` runbook](RUNBOOK.md#step-05-splitncigarreads), and follow the
[partial/rollback/stale-pair route](#step-05-producer-or-wrapper-leaves-a-partial-rollback-failure-or-stale-pair)
before any same-name retry. Validator exit `0` may publish failed evidence;
exit `2` publishes nothing new and is not a failed-row synonym.

## Step 06 producer or wrapper leaves a partial rollback failure, collision, or stale set

### Symptom

Step `06` returns nonzero after filtering, merging, indexing, counting,
publication, final revalidation, restoration, signal handling, or cleanup, and
the two BAM/BAI pairs plus counts TSV are absent, partial, mixed, or ambiguous.
A severe controlled state leaves the prior FWD BAM missing while the other
four predecessor files are restored and no backup, scratch, lock, or recovery
marker remains. Alternatively, two same-sample attempts with distinct output
directories both succeed but one shared QC counts path contains only the last
writer, or the scheduler exits zero after a zero-output child rediscovered five
stale nonempty files.

### Cause

The producer stages four filter BAMs, two merged BAM/BAI pairs, and a counts
TSV across the selected output and QC directories. It locks only the selected
output directory, backs up an all-five predecessor, publishes four BAM/BAI
members sequentially and counts last, then revalidates the final paths.
Restoration moves are best-effort and cleanup can erase the remaining backups,
scratch, lock, and recovery evidence after a restoration failure. The
characterized injected counts-publication exit `67` followed by prior-FWD-BAM
restoration exit `68` propagates `67`, leaves that predecessor BAM missing,
restores the other four prior files, preserves unrelated bytes, and erases all
owned recovery paths. This is an ambiguous/data-loss defect, not successful
rollback.

The input BAM/BAI is not snapshot-rechecked. The count row is not an attempt
receipt, and producer success does not require each flag-subcount sum to equal
the corresponding merged-BAM count. Distinct output-directory locks do not
serialize a shared QC path; the last successful writer replaces its counts
TSV. The wrapper checks only that five final names are nonempty after a zero-
exit child. Its submit-CWD fallback, body-level `logs/` mutation, tolerated
module calls, warning-only samtools probe, version-command behavior, one CPU
independent of `THREADS`, Bash `3.2` empty-array failure, and stale-five-file
success are separate preserved states. None proves current-attempt identity.

### Fix

Stop same-name retries, every relevant lock owner and producer, and downstream
Step `07` reads. Before cleanup or recovery, preserve all five surviving
finals; four flag-filter BAMs; merged BAM/BAI and counts scratch; all five
predecessor backups across both directories; every output-directory lock and
owner file; the input BAM/BAI; unrelated directory entries; producer stdout/
stderr; scheduler stdout/stderr, job ID/accounting and logs; checkout and
submit CWD; environment overrides; selected thread count; and exact samtools
path/version diagnostics. Record expected paths that are absent; absence is
not proof of clean state.

Do not combine members from different attempts, infer attempt identity from
counts or timestamps, remove a foreign lock, reconstruct a missing BAM or TSV,
or adopt stale wrapper success. Rule out every active producer and Step `07`
reader first. Any separately authorized diagnostic retry uses both an isolated
output directory and an isolated QC directory so the questioned evidence
remains unchanged. Git rollback changes tracked implementation only and cannot
recover, remove, or authenticate runtime artifacts.

Use the final validator in dry-run mode only to inspect one complete surviving
five-file set. It may print `status=fail` rows with exit `0`; it does not
quickcheck, recount, inspect flags, prove BAM/BAI correspondence, establish
attempt identity, or repair anything:

```bash
.venv/bin/python \
  src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py \
  --scope-id <sample_id> \
  --fwd-bam results/orientation/<sample_id>/<sample_id>.FWD_like.bam \
  --fwd-bai results/orientation/<sample_id>/<sample_id>.FWD_like.bam.bai \
  --rev-bam results/orientation/<sample_id>/<sample_id>.REV_like.bam \
  --rev-bai results/orientation/<sample_id>/<sample_id>.REV_like.bam.bai \
  --counts results/qc/orientation/<sample_id>.orientation_counts.tsv \
  --output results/qc/validation/06/<sample_id>.validation.tsv
```

## Step 06 structured validation reports output or count disagreement

### Symptom

The Step `06` validation TSV reports an invalid orientation BAM/index
container, malformed counts row, per-flag group-sum disagreement, incomplete
assigned/unassigned total, or inconsistent assigned fraction.

### Cause

The two declared BAM/BAI pairs and counts TSV may be incomplete, malformed, or
from different Step `06` attempts. The counts row may not match the declared
sample, or its `99 + 147`, `83 + 163`, assigned, unassigned, and fraction
values may not reconcile.

### Fix

Follow the [common response](#structured-validation-response). Confirm that
the two BAM/BAI pairs and counts row are declared as one Step `06` set, but do
not infer that fact from filenames, counts, timestamps, or validator exit `0`.
Inspect the final producer/validator paths, input pair, samtools selection,
producing job, logs, output/QC directories, and locks. Use only the final
commands in the [Step `06` runbook](RUNBOOK.md#step-06-split-bam-by-read-orientation),
and follow the
[partial/rollback/collision/stale-set route](#step-06-producer-or-wrapper-leaves-a-partial-rollback-failure-collision-or-stale-set)
before any same-name retry. Preserve `FWD_like` and `REV_like` as mechanical,
not biological, labels. Validator exit `0` may publish failed evidence; exit
`2` publishes nothing new and is not a failed-row synonym.

## Step 07 structured validation reports transaction disagreement

### Symptom

The Step `07` validation TSV reports a receipt, VCF, selector, manifest
identity/sample-order, path, or record-count failure.

### Cause

The declared receipt and VCFs may not be one completed transaction, the
manifests may have changed, the VCF sample columns may differ from manifest
order, or the selector may not reconcile with the declared FAI. A valid
header-only VCF has zero records and is not itself a failure.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact receipt, two VCFs, manifests, FAI, producing job, and logs. A header-only
VCF remains valid when its declared zero record count reconciles. Use only the
final producer/validator paths and commands in the
[Step `07` runbook](RUNBOOK.md#step-07-bcftools-mpileup), and follow the
[partial/rollback/stale-transaction route](#step-07-producer-or-wrapper-leaves-a-partial-rollback-failure-or-stale-transaction)
before cleanup or same-name retry. Validator exit `0` may publish failed rows;
exit `2` publishes nothing new and is not a failed-row synonym.

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

## Step 07 producer or wrapper leaves a partial rollback failure or stale transaction

### Symptom

Step `07` reports an existing cohort/partition lock, stale run-token path, or
incomplete VCF/VCF/receipt predecessor; a child or publication fails; a signal
interrupts execution; a receipt is visible although the producer did not
commit; a prior FWD VCF disappears during failed restoration; or the wrapper
returns success although the child created no current outputs.

### Cause

The final owner uses a cohort/partition lock, run-token temporary/backups,
all-three-or-none predecessor admission, sequential FWD/REV/receipt
publication, receipt-last ordering, final revalidation, best-effort
restoration, and cleanup. Another run may own:

```text
results/mpileup/<cohort>/<partition>/.<cohort>.<partition>.step07.lock
```

The receipt becomes visible before post-publication validation and the in-
memory committed flag. There is no durable attempt or recovery marker. Only
the two manifests are hash-bound and snapshot-rechecked; BAM/BAI, FASTA/FAI,
regions file, bcftools identity, depth, filter, and VCF bytes are not. A
controlled receipt-publication exit `67` followed by prior-FWD restoration
exit `68` propagates `67`, leaves the prior FWD final absent while its backup
survives, restores prior REV and receipt bytes, removes owned temps/lock, and
creates no marker. This is ambiguous manual recovery, not successful rollback.

The scheduler checks only three nonempty final paths after a zero-exit child.
It can therefore rediscover a stale complete set and return success without a
current producer transaction. Missing/nonexecutable bcftools is warning-only
at the wrapper; a version-command failure happens before delegation. Scheduler
dry-run changes CWD, creates `logs/`, and performs module/tool diagnostics.

### Diagnose

Before changing anything, preserve:

- all three stable finals and every run-token temp/backup;
- the lock directory and owner file, including paths that are unexpectedly
  absent;
- sample and partition manifests plus hashes;
- every selected Step `06` BAM/BAI, the FASTA/FAI, and regions file;
- unrelated bytes in the output directory;
- producer and wrapper stdout/stderr, job ID/accounting, and scheduler logs;
- checkout, invocation, and submit CWD plus environment overrides; and
- exact bcftools path/version, maximum depth, and filter expression.

Compare final, temp, and backup bytes without moving them. Inspect lock
ownership and every potentially active local or scheduled producer. Do not use
receipt presence, counts, timestamps, empty residue, or wrapper exit `0` to
infer current-attempt identity. A relative producer output root can also place
relative VCF paths in the receipt that disagree with the validator's resolved
arguments; preserve the exact original invocation before diagnosing this as a
data-content failure.

### Fix

Rule out every producer and Step `08` reader before action. Never combine files
from different attempts, reconstruct a missing member, manufacture or edit a
receipt, remove a foreign lock, discard a surviving backup, or adopt stale
wrapper success. Escalate the exact preserved state for manual recovery. Any
separately authorized diagnostic retry must use an isolated absolute output
root and must not be treated as production evidence.

Use the final owner paths and supported commands in the
[Step `07` runbook](RUNBOOK.md#step-07-bcftools-mpileup). Direct producer dry-
run is side-effect-free; validator dry-run reads six inputs and writes nothing;
scheduler dry-run is not side-effect-free. Git rollback changes tracked files
only and cannot authenticate, restore, delete, or alter runtime outputs,
backups, locks, logs, or recovery evidence.

These are locally mocked failure and preservation states. No real bcftools,
Step `07` cluster lock, rollback incident, scheduler recovery, production,
scientific-review, or biological evidence was created by MIG-03L.

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

## Runtime preflight profile or output contract is rejected

### Symptom

`src/norad/evidence/runtime_preflight/runtime_preflight.py` exits before
probing or publication with an
error about the profile header, row shape, duplicate ID, check type, context,
boolean, JSON probe arguments, regular expression, relative path, output
suffix, symlink, or invalid previous report.

### Cause

The preflight accepts one exact, nonempty TSV profile. Check IDs are unique
safe IDs; contexts, required values, check types, and probe adapters are
closed; path-visibility targets are absolute; and each check type has matching
argument and expectation rules. Profiles and previous reports must be regular,
byte-stable files. Execute mode requires an existing real output parent and a
`.tsv` filename.

### Fix

Compare the profile with `configs/runtime_preflight.example.tsv` and the exact
contract in the runbook. Correct the declaration at its source. Do not relax a
regular expression, change a required row, substitute local paths for cluster
paths, or hand-edit a previous result merely to obtain a pass. Rerun dry-run
before execute mode.

## Runtime preflight reports fail, blocked, or not_checked but exits zero

### Symptom

The command exits zero and may publish a TSV even though one or more result
rows have `status=fail`, `blocked`, or `not_checked`.

### Cause

Command success means the explicit probes completed and publication, when
requested, succeeded. It is intentionally separate from the per-row result.
A `cluster_batch` row evaluated with `--runtime-context local` is `blocked`
when required and `not_checked` when optional. A context-applicable probe that
cannot satisfy its expectation is `fail`.

### Fix

Inspect every required row. Run cluster-declared checks only inside the actual
approved batch/compute context and declare that context explicitly. Correct
the environment or profile through normal operator action; the preflight never
loads modules, installs packages, repairs paths, or changes statuses. Do not
call an all-pass report workflow runtime validation or cluster proof.

## Runtime preflight lock or previous report blocks publication

### Symptom

Execute mode reports an existing `.<output_name>.lock`, an invalid prior TSV,
an unsafe output parent, or a replacement/rollback failure.

### Cause

One output path has one owned publication transaction. A concurrent writer,
foreign lock, hand-edited result, changed profile/context, symlinked parent,
or interrupted replacement can make safe deterministic replacement
impossible.

### Fix

Inspect the lock, owning process, exact profile hash/context, current report,
and matching run-token `.tmp` and `.previous` paths. Do not delete a foreign
lock, overwrite an invalid report, or manufacture statuses. Resolve ownership
and preserve the prior report before an explicit recovery or a new output
path. A passing local fixture test is not evidence that a cluster-side
recovery or availability check occurred.

## Reference provenance reports missing, malformed, hash, or contig failures

### Symptom

The reference summary records `overall_status=fail`, or dry-run/execute rejects
the inventory, base directory, source type, prior transaction, or lock.

### Cause

The explicit inventory may name a missing/non-regular source, an incorrect
expected hash, malformed FASTA/FAI/DICT/GTF/BED12/STAR metadata, different
ordered names or lengths across FASTA/FAI/DICT/STAR, or annotation contigs
outside the FASTA universe. A partial or hand-edited three-file predecessor is
also unsafe to replace.

### Fix

Inspect the exact inventory row, observed digest, per-source contig rows,
summary agreement fields, current files, and any owned/foreign lock or
run-token paths. Correct provenance declarations or regenerate artifacts
through their formal upstream stage only after review. Never make this
read-only tool rebuild sidecars/indexes, rename contigs, edit hashes, discard
an unresolved annotation release, or delete a foreign lock.

## Storage inventory reports missing roots, measurement failures, or unapproved policy

### Symptom

`storage_retention_summary.tsv` records `overall_status=fail`, a root is
`missing_required`, `invalid`, or `measurement_error`, or
`unapproved_storage_count` is nonzero.

### Cause

An explicit required directory may be absent or unreadable, a declared root
may resolve to a non-directory or duplicate, filesystem metadata may be
unavailable, or no approved policy row covers that storage ID. Pending and
rejected approvals intentionally do not authorize retention handling.

### Fix

Inspect the exact root and policy rows, resolved path, observed capacity, quota
declaration, approval fields, and summary counts in the intended CSU execution
context. Correct the source contracts or storage environment through an
explicit operator action, then rerun dry-run. Do not change a status, invent a
quota or approval, or treat a local path measurement as cluster evidence. The
tool never executes retention actions.

## Storage inventory lock or prior transaction blocks publication

### Symptom

Execute mode reports an existing `.storage-inventory-retention.lock`, a
partial or invalid three-file predecessor, an unsafe output root, or a
publication/rollback failure.

### Cause

The inventory, normalized policy, and summary are one summary-last
transaction. A concurrent writer, foreign lock, manual edit, interrupted
replacement, symlink, or partial copy makes safe replacement impossible.

### Fix

Inspect the lock owner metadata, all three stable files, and matching
run-token `.tmp` and `.previous` paths. Do not delete a foreign lock, combine
attempts, manufacture a summary, or use this reporting tool to alter storage
content. Resolve ownership, recover either the complete prior transaction or
a clean first-publication state, validate it, and record any operator action
before retrying.

## Quiet local validation reports a failure or appears silent

### Symptom

A failure-first local gate prints only a `PASS` line for each successful
component, appears quiet while a long component is running, prints one or more
`FAIL` records with retained temporary-log paths and failed output, or prints
`INTERRUPTED` records with retained-log paths but no automatic replay.

### Cause

Pytest captures test output by default, Make command echo is suppressed, and,
in default or serial quiet mode, the validation orchestrator redirects each
shell, R, coverage, or report lane to its own temporary log. This is
intentional output control, not evidence that the lane was skipped. The gate
prints elapsed `PASS` lines and a final timing summary when lanes finish.

### Fix

For a failure, use every retained failed-lane log and the complete output
already replayed by the orchestrator. Multiple lanes completed in the same
polling batch can fail and be retained before the first failure triggers
cancellation of still-running lanes. For an interruption, inspect each
retained running-lane log at its printed path; those logs are retained but not
replayed. Re-run the gate with `--verbose` or use the serial fallback when
additional live detail is required. Verbose mode streams merged child output
and does not create per-lane temporary logs to retain. The gate returns the
first observed failure status, while an interruption returns `130`; both paths
terminate and reap remaining descendants. Do not rerun every successful
component merely to obtain progress narration, and do not delete retained
evidence before the failure or interruption is understood.

The quiet and verbose invocations are owned by the local-validation section of
the runbook. The measured bounded default and serial fallback exercise the same
lanes and result checks.

## Python coverage baseline cannot run or reports a regression

### Symptom

The coverage target reports a missing or wrong `coverage.py` version, missing
subprocess data, a disappeared source module, a lower global line or branch
rate, or a new shared module below the declared threshold.

### Cause

The selected project virtual environment may not be synchronized with the
tracked requirements, the exact developer-only `pytest-xdist` or `execnet`
version may be absent for a parallel run, a subprocess may no longer start
under coverage, source or test behavior may have changed, or a new shared
module may lack sufficient characterization. A rounded percentage can also
look unchanged while the exact covered/total ratio has decreased.

### Fix

Use the explicit dependency synchronization and coverage commands in the
runbook. Inspect the current and baseline JSON, the named module, the complete
test output, and any subprocess warning. Correct the source or test gap and
rerun the full gate. If only the parallel dependency identity is wrong,
explicitly synchronize the project virtual environment from
`requirements.txt` or use the supported serial fallback; do not install
packages globally or from the test command.

Do not update the baseline merely to make the command pass. A deliberate
baseline change requires review of the exact JSON diff and the
public-contract matrix. Numerical coverage is local developer evidence; it
does not replace shell, real-R, report-runtime, transaction, independent
oracle, or cluster tests.

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

For local development, use the exact
[guarded local-R sequence](RUNBOOK.md#guarded-local-r-environment).

`make r-restore` is the only package-installing action in that sequence.
Analysis scripts, SLURM wrappers, validators, and renderers must never call it
or install packages. `NORAD_USE_RENV=0` intentionally leaves ordinary R
startup unchanged; any value other than exact `0` or `1` is an error.

For a direct workflow script run, pass the executable with:

```bash
--rscript-bin /usr/local/bin/Rscript
```

The implemented Step `09` producer and sibling R program now live together
under
[`src/norad/analyses/rank_cohort_candidates_with_paired_CMH/`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md).
From another CWD, make both paths and every input/output path absolute rather
than relying on the launch directory.

For a future validated SLURM environment, export its batch-visible path:

```bash
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript
```

Confirm the package set in that same environment with the exact
[Step `08` real-R gate](RUNBOOK.md#step-08-vcf-preprocessing).

Run this probe in the same supported batch-visible environment intended for
Steps `08` and `09`, and confirm `sha256sum` or `shasum` there.

Do not substitute a fake R executable for semantic validation and do not call a
skipped real-R test a pass. `make real-r-test` runs the Step `08` suite followed
by the Step `09` suite; either runner reports `SKIP` only when the default
`Rscript` is absent, while an explicit bad override fails.

A passing local suite establishes local fixture behavior only. It does not
prove CSU batch visibility, production input behavior, or cluster outputs.
Consult the handoff for the current evidence boundary.

## `renv` startup uses sustained CPU or repeatedly creates directories

### Symptom

Starting the guarded local environment hangs or consumes sustained CPU before
the requested R expression runs.

### Cause

The local R `4.6.1`/macOS combination reproduced an `renv` sandbox
directory-creation loop. This was a startup-environment issue, not evidence of
an analysis loop.

### Fix

Use the repository Make target in the
[guarded local-R sequence](RUNBOOK.md#guarded-local-r-environment), which sets
the reviewed guard.

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

Run the explicit restore and check from the
[guarded local-R sequence](RUNBOOK.md#guarded-local-r-environment).

Run `r-check` in a network-capable developer environment when
`BiocManager::valid()` needs current release metadata. Require a successful
rerun; do not relabel the connectivity failure as a passing offline check.

Do not edit `renv.lock`, install into the project library manually, use the
damaged Homebrew checkout, or add source-build tooling merely to silence the
check. A necessary dependency or runtime contract change requires its own
reviewed implementation and lockfile update.

## Step 08 structured validation reports transaction disagreement

### Symptom

The Step `08` validation TSV reports a transaction-header, manifest/annotation
identity, input-receipt, sites schema/uniqueness, or summary-count failure.

### Cause

The sites, input receipt, and summary may not be one completed publication;
manifests or annotation may have changed; the partition-orientation universe
may be incomplete; or candidate/sample/count fields may not reconcile. The
producer preserves the supplied annotation path spelling while the validator
compares resolved paths, so equivalent relative spellings can also publish
failed annotation-identity evidence.

### Fix

Follow the [common response](#structured-validation-response). Inspect the
exact three-output set, complete partition/orientation universe, manifests,
and annotation. Invoke the final validator from any CWD with absolute input and
output paths when diagnosing spelling differences; do not edit report rows or
source receipts. Regeneration belongs to separately authorized Step `08`.

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

## Step 08 producer or wrapper leaves a partial rollback failure or stale transaction

### Symptom

The producer exits after one or more finals became visible; a prior sites,
input-receipt, or cross-root summary final is absent while a corresponding
`previous` backup survives; run-token scratch remains; the lock disappeared;
or the scheduler reports success against three nonempty files that may predate
the current attempt. Receipt presence may coexist with a failed final
post-publication validation.

### Cause

Step `08` publishes sites, QC summary, then input receipt. Receipt visibility
precedes final validation and the in-memory committed flag. Restoration is
best-effort across separate output and QC roots, has no durable recovery
marker, and cleanup may release the lock after incomplete restoration. A
controlled receipt-publication exit `67` followed by sites-restoration exit
`68` leaves the prior sites final absent with its backup retained while prior
summary and receipt are restored. The wrapper independently checks only that
three nonempty finals exist after a zero-exit child, so stale files can satisfy
it.

### Diagnose

Preserve and inventory both roots before action:

```bash
cohort=<cohort_id>
find "results/vcf_preprocessed/$cohort" -maxdepth 2 -name ".${cohort}.step08*" -print
find results/qc/vcf_preprocessing -maxdepth 1 -name ".${cohort}.step08*" -print
ls -la "results/vcf_preprocessed/$cohort" results/qc/vcf_preprocessing
```

Also preserve the lock owner if present, all three finals, both manifests,
Step `07` receipts/VCFs, annotation GTF, R program/runtime/library identity,
stdout/stderr, scheduler job/accounting/logs, checkout and submit CWD, and every
environment override. Record expected paths that are missing. Rule out every
active producer and Step `09`/`09c` reader.

### Fix

Do not combine attempts, reconstruct a member, manufacture or edit the receipt,
delete a foreign lock, discard a surviving backup, trust timestamps/counts,
or rerun against the same roots. Escalate the preserved state for explicit
manual recovery. Any separately authorized diagnostic retry uses isolated
absolute output and QC roots and remains nonproduction. Git rollback cannot
recover or authenticate runtime files.

The final-path shell, validator, guarded-real-R, and scheduler tests characterize
these states; they do not approve them or establish cluster recovery.

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
`07`, then use the exact
[manifest-validation command](RUNBOOK.md#step-07-bcftools-mpileup) and
regenerate any Step `07`/Step `08` artifacts made with the old manifest.
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

Preserve the selected Rscript, R-program bytes/path, startup and package state,
and all streams before action. The producer currently detects manifest and
Step `08` mutations after admission, but a selected-R-program mutation can go
undetected and still publish with exit `0`. The summary omits Rscript/R-program
and package identity, a durable attempt identity, and hashes of its five
sibling outputs. Treat this as an evidence ceiling, not permission to accept
the result.

These independent output checks and rollback behavior are locally tested with
a fake R executable. The real-R suite also passes locally without `SKIP`. Its
PDF fixture now searches the trailing raw bytes for the `%%EOF` marker instead
of coercing arbitrary PDF bytes through locale-sensitive text conversion.
This was a fixture-portability correction, not production output evidence.
Cluster output validation remains pending.

## Step 09 structured validation reports transaction or semantic disagreement

### Symptom

`<analysis_id>.validation.tsv` contains `status=fail` for one or more of:

```text
output_transaction
upstream_identity_and_candidate_order
status_semantics
significant_subset
summary_count_reconciliation
mutation_spectrum_reconciliation
pdf_structure
```

The validator may exit zero because successful inspection/publication is
separate from the seven row statuses. Missing, empty, symlinked, or nonregular
inputs instead exit nonzero and publish nothing.

### Cause

The six readable native outputs may have wrong headers or analysis-bound
names, span multiple directories, alias the same physical file, omit or
reorder a Step `08` candidate, use a different cohort or orientation policy,
or disagree with immutable counts and declared thresholds. The validator also
recomputes enabled-background status/maximum AF and one global BH family, then
reconciles the exact significant subset, summary provenance/counts, canonical
mutation spectrum, and both PDF structures.

It does not independently recompute count-table estimability, CMH statistic,
p-value, or common odds ratio. The current `status_semantics` expected text
nevertheless says CMH was recomputed and overstates that evidence. Preserve
the validator rows together with the separate independent-oracle and real-R
results; do not rewrite the row text as proof or bless the defect here.

### Fix

Follow the [common response](#structured-validation-response). Inspect every
explicit manifest, Step `08`, and Step `09` path, treating the six native
outputs as one transaction. Preserve the seven reported statuses and the
nonregular-input/process-failure distinction; regeneration belongs to
separately authorized Step `09`.

Producer-recorded relative paths are later interpreted from the consumer's
CWD. Preserve the producer CWD and resolved paths, and rerun inspection with
the original path context or explicit absolute paths. Do not edit a summary to
make a path resolve from a new directory.

The structured validator is read-only and locally fixture-tested. Its report
does not establish production execution, cluster proof, scientific review, or
biological validity.

## Step 09 scheduler succeeds with stale outputs or an unusable R selection

### Symptom

The Step `09` job exits `0` and finds all six expected names even though the
current child produced nothing, or the child reports a missing/nonexecutable
Rscript or missing R program.

### Cause

The mode-`0755` final job delegates runtime validation to the child. It does
not preflight Rscript, the selected R program, R version, or packages. After an
exit-`0` child it checks only that six output files exist, so a stale complete
set can satisfy the wrapper without a current-attempt identity. Body-level
`logs/` creation also occurs too late to satisfy SLURM's pre-body output-file
opening; the checkout `logs/` directory must already exist.

### Fix

Preserve the job ID, accounting, stdout/stderr paths, submit and launch CWD,
environment overrides, child command/streams, all six outputs and hashes,
lock/owner, and matching temporary/backup paths. Compare them with a known
current child attempt; do not infer current production from job exit or file
presence. Create `logs/` before a later submission, correct the batch-visible
absolute R selection, and use a fresh absolute output root for any separately
authorized nonproduction diagnostic. Never delete or overwrite the stale set
while its writers or consumers remain unresolved.

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

Even when all six and the summary are briefly visible, final content/hash
checks may still be in progress. The summary contains no durable attempt or
five-sibling hash identity, so visibility is not proof that the producer
returned success or that the visible set belongs to one current attempt.

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
approved future branch. Complete/incomplete source evidence requires dates;
analysis sets must be disjoint and category ownership must agree; pending
decisions cannot cite support; recorded decisions require
complete/not-applicable support; rerun booleans/scopes must agree; and
passed/failed/proven computational claims require their defined complete
evidence roles. Runtime and cluster roles additionally require explicit
underlying paths/hashes; blocked/not-run states are not proof. The tracked
example's `local_test_status=not_run` is intentional because it attaches no
local-test evidence.

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

When invoking from another CWD, make the launcher or Python file, interpreter,
both manifests, all three Step `08` files, Step `09` analysis directory, review
plan, evidence manifest and every payload it declares, and output root absolute.
Relative producer-recorded paths can later resolve from a consumer's CWD;
preserve the original CWD and resolved identities rather than editing a
published table into agreement.

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
published last, but becomes visible before final table/hash validation and the
second check of all 32 inputs. It does not hash its twelve siblings. A
concurrent writer, interrupted/manual copy, changed input, publication/rollback
failure, or cleanup error can leave evidence that must be inspected before
another writer proceeds.

`TERM` after summary visibility has no handler and can leave thirteen
unvalidated new finals, thirteen predecessor backups, the lock, and an empty
transaction directory without a recovery notice. `KeyboardInterrupt` can
bypass rollback but run `finally`, leaving new finals while deleting the
predecessor backups, transaction directory, and lock. These are severe
characterized defects, not approved cleanup or retry behavior.

### Fix

Inspect any remaining lock metadata, all 13 stable outputs, all 32 bound
inputs, matching run-token temporary/previous paths, any best-effort recovery
marker, streams, environment, process/signal evidence, and unrelated bytes.
Do not delete a foreign lock, combine files from different attempts,
manufacture the summary, or discard a retained backup. Do not treat a visible
summary or an absent lock as committed-attempt proof. Wait for an active owner
or perform an explicit, evidence-preserving recovery to either the complete
previous 13-file set or no set, validate the result, record the operator
action, and only then remove the owned lock when appropriate. If one restore
failed, retain the absent final's backup, the lock, empty transaction directory,
backup directory, and recovery notice exactly as found. For a cleanup-only
error, inspect exactly the paths named in the error because the lock may already
have been removed. A separately authorized nonproduction diagnostic retry uses
a new isolated absolute output root after every writer and reader is ruled out.

Lock, mutation, rollback, and cleanup paths are synthetic-fixture-tested only;
no production Step `09c` recovery incident has been observed.

## A Step 08, Step 09, artifact, or Step 09c consumer cannot load the neutral Step 08 contract

### Symptom

The final Step `08` or Step `09` validator, neutral Step `09` owner, artifact
index, or Step `09c` Python owner exits `2` with a sanitized one-line diagnostic
such as:

```text
ERROR: unable to load Step 08 scientific-evidence contract at <path>: <type>: <reason>
```

### Cause

These five repository-owned consumers exact-load the neutral public contract
at
`src/norad/contracts/scientific_evidence/step08.py` under the single internal
name `_norad_step08_scientific_evidence_contract`. Each loader requires the
exact cached-file path and completed readiness marker, inserts the module
before execution, cleans only an owned partial cache entry, and fails closed
for a missing file, foreign cache entry, partial initialization, unreadable
path, or execution error. The Step `09` validator, artifact index, and Step
`09c` owner additionally require their neutral Step `09` module to resolve the
same Step `08` object.

This is exact-file loading from the tracked checkout. It does not use package
discovery, `PYTHONPATH`, an installed distribution, or `sys.path` mutation.

### Fix

Preserve the diagnostic and inspect the exact neutral file, current Git state,
cached module identity when debugging in-process, and the invoking consumer.
Restore the reviewed neutral owner through Git if the tracked file is missing
or changed. Do not recreate the extracted Step `08` surface in Step `09c`, add
a wrapper, copy the contract into a stage, install a package, alter
`PYTHONPATH`, or inject a search path. Use the neutral direct suite and
consumer-focused commands in the
[Step `08` runbook](RUNBOOK.md#step-08-vcf-preprocessing).

## A Step 09, artifact, or Step 09c consumer cannot load the neutral Step 09 contract

### Symptom

The final Step `09` validator, artifact index, or Step `09c` owner exits `2`
with a sanitized one-line diagnostic such as:

```text
ERROR: unable to load Step 09 scientific-evidence contract at <path>: <type>: <reason>
```

### Cause

These three repository-owned consumers exact-load the neutral public contract
at `src/norad/contracts/scientific_evidence/step09.py` under the single internal
name `_norad_step09_scientific_evidence_contract`. Each loader requires the
exact cached-file path and completed readiness marker, inserts before execution,
cleans only an owned partial cache entry, and fails closed for a missing file,
foreign cache entry, partial initialization, unreadable path, or execution
error. The neutral Step `09` owner exact-loads Step `08`; every higher-level
consumer rejects a split Step `08` or Step `09` owner identity. If the
diagnostic names Step `08`, use the preceding route.

This is exact-file loading from the tracked checkout, with no package
discovery, `PYTHONPATH`, installed distribution, or `sys.path` mutation.

### Fix

Preserve the diagnostic and inspect both neutral files, current Git state,
cached identities when debugging in-process, and the invoking consumer. Restore
the reviewed neutral owner through Git if it is missing or changed. Do not
recreate the extracted Step `09` surface in Step `09c`, add a wrapper, copy it
into the analysis owner, install a package, alter `PYTHONPATH`, or inject a
search path. Use the neutral direct suite and consumer-focused commands in the
[Step `09` runbook](RUNBOOK.md#step-09-cmh-editing-site-calling).

## A Step 09c, artifact, or run-summary consumer cannot load the neutral review-package contract

### Symptom

The final Step `09c` owner, artifact index, or run-summary science normalization
exits `2` with a sanitized one-line diagnostic such as:

```text
ERROR: unable to load review-package scientific-evidence contract at <path>: <type>: <reason>
```

### Cause

These three repository-owned consumers exact-load the neutral public contract
at `src/norad/contracts/scientific_evidence/review_package.py` under the single
internal name `_norad_review_package_scientific_evidence_contract`. Each loader
requires the exact cached-file path and completed readiness marker, inserts the
module before execution, cleans only an owned partial cache entry, and fails
closed for a missing file, foreign cache entry, partial initialization,
unreadable path, or execution error. Run-summary science reads the committed
public package locally and does not load the private Step `09c` implementation.

This is exact-file loading from the tracked checkout. The neutral owner is
standard-library-only, and the load does not use package discovery,
`PYTHONPATH`, an installed distribution, or `sys.path` mutation.

### Fix

Preserve the diagnostic and inspect the exact neutral file, current Git state,
cached module identity when debugging in-process, and the invoking consumer.
Restore the reviewed neutral owner through Git if the tracked file is missing
or changed. Do not recreate the extracted public surface in Step `09c`, add a
wrapper or compatibility alias, copy the contract into reporting, install a
package, alter `PYTHONPATH`, or inject a search path. Recheck
`tests/contracts/scientific_evidence/test_review_package.py` and the affected
consumer suite.

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

Describe the evidence boundary as:

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

Running
`src/norad/contracts/artifacts/validate_artifact_contracts.py` fails before
validation with
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
.venv/bin/python \
  src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --check-schemas
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
The common schema retains its `v1` URN. Artifact records remain `1.0.0`;
scientific-review, run-summary, and report-receipt documents are `1.1.0`.
`biological_interpretation_ready` and non-null readiness authorization are
intentionally rejected by the current contracts.

Combining `--inventory` with a document performs reconciliation only for an
`artifact-record` or `run-summary`. A `scientific-review-record` or
`report-receipt` should be validated without `--inventory`.

### Diagnose

First validate the tracked contracts and inventory independently:

```bash
.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --check-schemas

.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --inventory configs/artifact_inventory.example.tsv
```

Then validate the explicit record with the matching public schema:

```bash
.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
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

Use the focused regression command under
[`artifact-schema-v1` validation](RUNBOOK.md#validate-artifact-schema-v1).

A passing focused suite is schema/fixture evidence, not production artifact
validation.

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
implemented run-summary package aggregates existing evidence but never infers
or promotes it. If Step `09c` science propagation was expected, correct its
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

`artifact-schema-v1` defines and validates declarations. Its 81-row inventory
and valid JSON records are synthetic fixtures. The validator is read-only and
does not discover pipeline outputs, build adapter records, inspect production
source contents, publish files, render reports, or run analysis. Within a
record it validates the canonical run-contract hash. The implemented
`artifact-adapters-v1` layer additionally validates an existing output-root
receipt before allowing the same `run_id` to be rebuilt.

### Fix

Describe the evidence boundary as:

```text
shared common schema plus four public Draft 2020-12 schemas
synthetic explicit physical inventory and read-only validator
explicit read-only artifact adapters
canonical JSON, deterministic TSV/QC views, exact Step 09c table approvals,
  and receipt-last publication
one atomic static HTML/PDF/summary-TSV bundle with its report receipt last
no production artifact index, run summary, approval manifest, report, or evidence
```

Keep production and cluster status unchanged. Keep production science
`evidence_incomplete`, and continue rejecting
`biological_interpretation_ready`.

## Run-summary input transaction or immutable run contract is rejected

### Symptom

`build_run_summary.py` reports a receipt path/run-ID mismatch, changed
immutable contract field, invalid inventory/index/record hash, record-set
count mismatch, disconnected attempt history, or non-canonical/unsafe input.

### Cause

The builder accepts only the exact complete adapter receipt under the declared
`OUTPUT_ROOT/<run_id>/` transaction. Moving, editing, copying, manufacturing,
or mixing receipt/index/inventory/record members breaks their path, hash,
ordering, identity, and attempt relationships.

### Fix

Point `--artifact-receipt` at the exact committed receipt and use the output
root that directly contains its `<run_id>/` directory. Validate or regenerate
the complete adapter transaction from its explicit run contract and inventory.
Never edit hashes, row counts, run IDs, attempt IDs, or receipts to force a
match.

## Explicit Step 09c summary is rejected by the run-summary builder

### Symptom

The optional `--science-review-summary` path exists, but identity, hashes,
counts, evidence categories/records, decisions, computational claims, or
science state do not reconcile.

### Cause

The optional input must be the exact summary marker of one committed 13-file
Step `09c` transaction. Complete/incomplete source evidence requires dates;
analysis sets and category ownership must agree; pending decisions cannot cite
support; recorded decisions require complete/not-applicable support; and
passed/failed/proven claims require their defined complete computational
evidence roles. Runtime and cluster roles additionally require explicit
underlying paths/hashes; blocked/not-run states are not proof.

### Fix

Correct and republish the Step `09c` evidence transaction from its explicit
inputs. If no committed review exists, omit `--science-review-summary`; the
run summary will retain `evidence_incomplete` and an explicit warning. Do not
point at a copied summary, decoy, incomplete directory, or hand-edited table.

## Report-table approvals are rejected by the run-summary builder

### Symptom

`--report-table-approvals` fails on its header, an empty manifest, run ID,
run-contract hash, role, artifact ID, review scope, path, SHA-256, row count,
display limit, approval status/policy, approver, timestamp, duplicate, symlink,
or input mutation.

### Cause

The option accepts one explicit nonempty TSV with this exact header:

```text
run_id	run_contract_sha256	table_id	artifact_id	role	title	path	sha256	row_count	display_row_limit	approval_status	approval_policy_version	approved_by	approved_at
```

Approvals require the exact committed Step `09c` science-review summary.
Every row must bind to the current run and immutable contract, use a supported
closed Step `09c` table role and `approval_status=approved`, and name one exact
complete TSV artifact in that active review scope. The path, hash, row count,
media type, size, current file, display limit, policy, approver, and canonical
non-future UTC timestamp must all reconcile. Duplicate table IDs, duplicate
physical sources, globs/templates, traversal or redundant paths, symlinks,
decoys, and changed files fail closed.

### Fix

Start from `configs/report_table_approvals.example.tsv`, but replace every
synthetic value with values from the exact current adapter transaction and
Step `09c` review. Recompute the declaration from the actual source; never edit
a hash, count, run binding, artifact record, or canonical JSON to force a
match. If no table is approved, omit the option entirely; a supplied
header-only approvals file is intentionally invalid. An approval authorizes
display of an exact table—it is not scientific review completion, biological
validation, or a computational-status promotion.

## Run-summary lock, partial output set, or recovery state remains

### Symptom

Execute mode reports a foreign lock, partial four-file set, changed output
directory identity, unsafe symlink, input mutation, rollback failure, or
cleanup failure. Relevant paths may include:

```text
results/artifacts/<run_id>/.<run_id>.run-summary.lock
results/artifacts/<run_id>/.<output-name>.<run_token>.tmp
results/artifacts/<run_id>/.<output-name>.<run_token>.previous
results/artifacts/<run_id>/.<run_id>.run-summary.<run_token>.RECOVERY.txt
```

### Cause

The canonical JSON, two TSV views, and receipt are one transaction, with the
receipt published last. A concurrent writer, adapter transaction-member,
optional Step `09c`, approval-manifest, or approved-table input mutation,
output-directory replacement, signal, publication failure, incomplete
rollback, or incomplete cleanup can leave evidence that must be inspected
before another writer runs. Native Step `00`-`09` source hashes are carried
from adapter records rather than rehashed by the summary builder.

### Fix

Inspect the regular lock metadata, owning process, current four outputs, all
reported temporary/backup/recovery paths, and exact adapter, Step `09c`,
approval-manifest, and approved-table inputs. Do not delete a foreign lock or
recovery evidence, combine attempts, or manufacture a receipt. If
output-directory identity changed, resolve and verify that identity before
touching any contained path. First validate the current new four-file
transaction: a post-commit cleanup failure may leave it complete and it should
then be retained. If it is not complete, restore the validated prior
transaction or a clean first-publication state as appropriate. Validate the
chosen state, record the operator action, then remove only proven-owned residue
and a lock whose ownership is proven.

## Run-summary receipt is complete but evidence is missing or failed

### Symptom

`<run_id>.run_summary_receipt.tsv` and `summary_state=complete` coexist with
missing, failed, incomplete, or externally unavailable artifacts,
`evidence_incomplete`, or `not_run` validation fields.

### Cause

Summary completion describes the validated four-file publication transaction,
not completion or promotion of the evidence it summarizes.

### Fix

Use the explicit computational rollups, per-scope statuses, science state,
warnings, errors, and limitations as the result. Do not edit or promote them.
Later evidence/validator packages may supply new typed inputs, after which the
adapter and summary can be regenerated through their normal contracts.

## A record is validated against the wrong 1.0 or 1.1 schema

### Symptom

Validation reports an unexpected `$id`, `schema_version`, missing retained
review/decision/limitation field, or a report receipt that expects the wrong
run-summary version.

### Cause

The common schema retains its `v1` URN and artifact records remain `1.0.0`.
Scientific-review, run-summary, and report-receipt documents are `1.1.0`.
Run-summary TSV, QC TSV, and run-summary receipt TSV producer contracts remain
`1.0.0`.

### Fix

Regenerate the record with the implemented producer and validate it against
the matching tracked schema. Do not change only a version string or `$id`;
the closed shapes differ intentionally.

## A synthetic run summary is mistaken for production evidence or a report

### Symptom

A run-summary fixture or passing test is described as a production run,
HTML/PDF report, runtime/cluster proof, completed scientific review, or
biological validation.

### Cause

The current implementation evidence uses synthetic adapter and Step `09c`
fixtures. The summary builder records existing evidence and runs no analysis
or renderer.

### Fix

Describe the boundary as synthetic-fixture behavior and local renderer
execution only. Do not claim a production adapter transaction, run summary,
approval manifest, report, pipeline runtime or cluster proof, completed
production science review, or biological readiness. Rendering does not
promote validation.

## Quarto restore rejects the archive, installed tree, version, or lock

### Symptom

`make quarto-restore` or `make report-test` fails with an archive SHA-256
mismatch, invalid install receipt/tree, wrong executable version, unsupported
platform, existing restore lock, or retained recovery-state message.

### Cause

The local report runtime is deliberately closed to one official macOS archive:

```text
Quarto version: 1.9.38
archive: quarto-1.9.38-macos.tar.gz
SHA-256: 47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a
installation: .tools/quarto/1.9.38
receipt: .tools/quarto/1.9.38/.norad-quarto-install.json
```

The earlier roadmap checksum was corrected after both the official GitHub
release metadata and an independently downloaded official archive agreed on
the value above. The restore safely validates archive members, the exact
executable version, the receipt, and a deterministic hash of the complete
installed tree. An edited receipt, mutated tree, wrong archive, stale partial
installation, foreign lock, interrupted cleanup, or non-macOS host must fail
closed.

Owned or recovery paths may include:

```text
.tools/quarto/.restore-1.9.38.lock
.tools/quarto/.restore-1.9.38.<run_token>.tmp
.tools/quarto/.restore-1.9.38.<run_token>.RECOVERY.txt
.tools/.quarto-download-<run_token>.tmp
```

### Fix

For a normal first restore, use the exact
[Quarto restore and report commands](RUNBOOK.md#restore-quarto-and-render-the-static-report-bundle).

An already-downloaded official archive may be supplied explicitly while
retaining the same checksum gate:

```bash
python3 scripts/restore_quarto.py \
  --install-root .tools/quarto \
  --archive /explicit/path/to/quarto-1.9.38-macos.tar.gz
```

Do not weaken the checksum, edit the receipt, install through Homebrew, or
make a renderer download its own dependency. If an existing version tree is
invalid, the restore intentionally refuses to overwrite it. Inspect and
record the tree, receipt, lock owner, and any recovery paths first; then use an
explicit operator-reviewed relocation or removal of only the proven ignored
tooling target before restoring again. Never delete a foreign lock or retained
recovery evidence merely to make the command pass.

`make report-test` requires the executable to exist, revalidates the installed
receipt/tree/version, and then exercises the real pinned executable. A fake
Quarto fixture is useful for wrapper behavior but is not local renderer-runtime
evidence.

## `make demo-report` cannot find tools or the HTML still widens the page

### Symptom

The demo target reports that pinned Quarto, the selected Python executable, or
report dependencies are unavailable. Alternatively, an opened demo appears to
be an older layout, or a wide approved table seems to expand the full page.

### Cause

The demo deliberately does not restore Quarto or install Python packages.
Its generated HTML is self-contained, so an already-open file does not receive
new renderer or CSS changes automatically. In the current layout, the document
column is bounded and tables with more than six columns scroll inside a
keyboard-focusable table region; the complete table itself remains wider than
that local viewport by design.

### Fix

Follow the explicit dependency setup and populated-demo procedure in
[`RUNBOOK.md`](RUNBOOK.md#generate-the-populated-synthetic-demo-report).
Regenerate the bundle and reopen the exact printed HTML path. Scroll within
the table region, not the document. Do not edit the ignored generated HTML,
install dependencies from the renderer, remove columns from an authorized
source table, or treat the synthetic exploratory content as production
evidence.

## Report bundle rendering rejects the run summary, approved table, or output

### Symptom

`src/norad/reporting/render_run_report.sh` fails during dry-run or execute mode with a
run-summary schema/identity error, approved-table path/hash/row-count error,
report-tool identity error, input mutation, static HTML validation error, PDF
signature/EOF/text/page-order error, missing per-page banner, or invalid
summary/receipt error. Messages may also identify a script, remote active
resource, sidecar resource directory, inaccessible table/image/figure,
duplicate ID, or invalid heading structure.

### Cause

The bundle renderer accepts one explicit canonical run-summary document and no
discovered inputs:

```bash
src/norad/reporting/render_run_report.sh \
  --run-summary results/artifacts/<run_id>/<run_id>.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto \
  --formats all
```

Dry-run is the default and creates no stable output, lock, or scratch path.
Add `--execute` to publish the selected report formats and always publish the
summary TSV and receipt. The default `all` set is:

```text
results/reports/<run_id>/<run_id>.run_report.html
results/reports/<run_id>/<run_id>.run_report.pdf
results/reports/<run_id>/<run_id>.run_summary.tsv
results/reports/<run_id>/<run_id>.report_outputs.tsv
```

The run summary, QMD/CSS templates, Quarto executable, and every explicitly
approved table must remain byte-stable. Approved table records must supply
the exact normalized path, SHA-256, row count, role, and display limit. The
rendered HTML must be script-free, self-contained, and accessible. The PDF
must have valid boundaries, extractable ordered section text, and the exact
applicable scientific-state banner on every page. Summary and receipt TSVs
must reconcile with the canonical summary and selected outputs.

The implemented normal run-summary producer emits an empty
`approved_report_tables` list when its optional approval manifest is omitted.
When the exact nonempty manifest passes the run/contract/Step `09c` artifact
checks documented above, the producer emits those authorized records in
manifest order. A missing row-level table after omission is not a renderer
failure and must not be bypassed by editing canonical JSON.

### Fix

Correct or regenerate the canonical run summary and approved table
through their normal validated producers. Use the exact pinned Quarto
executable. Do not edit a run ID, schema version, receipt, path, hash, row
count, banner, template, rendered report, summary TSV, or report receipt merely
to force acceptance; do not glob for candidate tables or add external
assets/scripts. Rerun dry-run first, then execute only after all printed
inputs and hashes are correct.

## Report bundle lock, rollback, cleanup, or recovery state remains

### Symptom

Execute mode reports a foreign lock, invalid prior report bundle, changed output
directory identity, late foreign replacement, failed Quarto child, signal,
timeout, incomplete rollback, or incomplete cleanup. Relevant paths may
include:

```text
results/reports/<run_id>/.<run_id>.report-bundle.lock
results/reports/<run_id>/.run-report-bundle.<run_token>.tmp
results/reports/<run_id>/.<output_name>.<run_token>.previous
results/reports/<run_id>/.<run_id>.report-bundle.<run_token>.RECOVERY.txt
```

### Cause

The selected reports, summary TSV, and receipt-last TSV are one
`report-exports-v1` publication. The renderer validates any prior bundle or
valid HTML-only predecessor, snapshots every input, acquires an owned lock,
renders into a run-token stage, and replaces only exact predecessors it
inspected. Symlinked, mutated, late-appearing, or identity-changed files and
directories are never clobbered.

Quarto runs in a dedicated process group. HUP, INT, TERM, launch errors, and
the render timeout terminate and reap that complete group before publication
cleanup continues. If publication fails, the renderer restores each validated
prior member when it can prove ownership and identity. If rollback or cleanup
cannot be proved, it retains the lock and best-effort recovery marker. If the
output directory itself changed identity, path-based rollback is skipped to
avoid modifying the replacement directory.

### Fix

Inspect the lock metadata, owning process, current bundle members, run-summary and
approved-table hashes, Quarto process state, output-directory identity, and
all named stage/backup/recovery paths. Do not delete a foreign lock, kill an
unrelated process, overwrite a late foreign report, combine attempts, or
discard recovery evidence. Determine whether the validated new report is
already committed or whether the exact prior bundle must be restored. Validate
the chosen bundle state, record the operator action, and only then remove
residue and a lock whose ownership is proven.

## A synthetic report bundle is mistaken for production or validation evidence

### Symptom

A locally rendered fixture report is described as a production report,
pipeline runtime/cluster proof, completed scientific review, or biological
validation.

### Cause

The report tests use synthetic or incomplete fixtures. Rendering accurately
presents their declared states but creates no new computational or scientific
evidence.

### Fix

Describe the boundary as:

```text
HTML/PDF/summary-TSV/report-receipt renderer implemented and fixture-tested locally
real pinned local Quarto/Typst runtime and PDF reader exercised
one synthetic atomic report-bundle contract validated
no production report or pipeline runtime/cluster validation
no completed production science review or biological readiness
```

Retain the report's state banner and limitations. Report generation is never
validation evidence, even after production inputs eventually become
available.

## Wrong log interpretation: empty `.err` file

### Symptom

The `.err` file exists but is empty.

### Cause

For many successful jobs, stderr is empty. This is fine.

### Fix

Use the exact [`sacct` command](RUNBOOK.md#manual-job-checking) and output
validation to decide success.

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

## Concurrent lane is in the wrong worktree, overlaps, or cannot integrate

### Symptom

An agent sees another lane's changes, the resolved worktree/branch/`HEAD` does
not match its packet, a reserved card ID or path overlaps, a candidate handoff
moved after review, or serialized integration reports a conflict.

### Cause

Agent identity was mistaken for filesystem isolation; the lane packet is
missing or stale; a pre-existing worktree was reused without proof; candidate
state changed after handoff; or documentation classified as independent now
depends on an active contract, result, or canonical owner.

### Diagnose

Stop mutation and use the inspection commands under
[`Concurrent Worktrees And Serialized Integration`](RUNBOOK.md#concurrent-worktrees-and-serialized-integration).
Compare the assigned absolute path, branch, base, candidate SHA, worktree list,
write set, untracked files, and coupling assumptions with the live lane table
in [`HANDOFF.md`](HANDOFF.md#active-concurrent-lanes). Preserve conflict status
and the candidate branch before taking recovery action.

### Fix

Do not add, stash, switch, reset, clean, force-remove, merge, rebase, or resolve
the overlap opportunistically. The integration owner stops affected paths,
aborts only an in-progress cherry-pick using the runbook sequence, preserves
candidate commits and execution evidence, and then repairs the packet or
returns the governing task to planning. A candidate with changed `HEAD` needs
a fresh immutable handoff.

If worktree metadata is stale but the intended checkout and branch are proved,
inspect repair options without pruning unique state. Cleanup remains optional,
explicitly authorized, and post-publication; candidate branches are preserved
by default. When executable-tree identity or non-consuming documentation
classification cannot be proved, rerun the applicable computational gate on
the integrated state.

## Future Troubleshooting Taxonomy

A future troubleshooting index may summarize repeated failure patterns as
symptom, likely cause, confirmation command, and fix. Keep the generic index as
a deferred roadmap idea until enough real failures exist. The artifact-schema
validator, inventory, and explicit artifact adapter indexer are now
implemented, as is the run-summary builder, so their concrete failure modes
are documented above. Static HTML/PDF/summary-TSV bundle reporting is also
implemented, so its concrete restore, validation, publication, and recovery
failures are documented above. Do not add entries that imply general cleanup
tools, reference/storage foundation tools, or per-step validators exist before
their branches implement them.

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
