# Troubleshooting

This is NORAD's canonical symptom-to-recovery guide. Use it to identify a
failure, preserve evidence, and choose the owning recovery path. Exact supported
commands belong in [`RUNBOOK.md`](RUNBOOK.md) or the linked owner README; this
guide does not duplicate full operating procedures.

## Issue index

- [Recovery rules for any ambiguous transaction](#recovery-rules-for-any-ambiguous-transaction)
- [Cluster environment, tools, logs, and early stages](#cluster-environment-tools-logs-and-early-stages)
- [Structured validation and stage recovery](#structured-validation-response)
- [Preflight, provenance, storage, and local gates](#runtime-preflight-profile-or-output-contract-is-rejected)
- [R, Step `08`, Step `09`, and scientific review](#step-08-or-step-09-cannot-find-rscript)
- [Neutral contracts, artifacts, summaries, and reports](#neutral-contract-load-failures)
- [Evidence ceilings and success criteria](#evidence-ceilings-and-success-criteria)

## Recovery rules for any ambiguous transaction

Apply these rules before a same-name retry, deletion, restoration, or adoption
of output whose attempt identity is uncertain.

1. Stop new writers and downstream readers. Check the scheduler, process table,
   lock owner, and declared output root before changing anything.
2. Preserve the exact stable outputs; hidden run-token stage, temporary,
   backup, quarantine, and recovery paths; lock metadata; stdout/stderr; job ID
   and accounting; invocation and working directory; checkout; environment and
   tool identities; admitted inputs and hashes; filesystem identity; and
   unrelated directory entries.
3. Treat absent locks, backups, receipts, or recovery markers as missing
   evidence, not proof of a clean state. Recovery markers are often best-effort.
4. Never delete a foreign lock, mix files from different attempts, manufacture
   a receipt or summary, infer ownership from names/timestamps/visibility, or
   overwrite a late or identity-changed path.
5. A receipt-last or summary-last file is a commit marker only after the whole
   transaction validates. Several owners expose that file before their final
   checks complete.
6. Choose an explicit recovery target: a validated complete predecessor, a
   validated complete new transaction, or a clean first-publication state.
   Record the decision, then remove only residue and locks whose ownership is
   proved.
7. Run diagnostics in isolated absolute output roots when the questioned state
   must remain untouched. A diagnostic retry is not production evidence.

Git rollback changes tracked implementation only. It cannot restore, remove,
or authenticate runtime outputs, locks, backups, logs, or evidence.

For validators, process success and check success are different:

- Exit `0` can publish or print `status=fail` rows.
- Exit `2` is an unsafe input, CLI, tool, or publication failure and publishes
  nothing new.
- A passing local fixture is not runtime, cluster, production, scientific-
  review, or biological evidence.

## Cluster environment, tools, logs, and early stages

### `TMPDIR [/local/tmp] is not writeable`

The cluster default can name an unwritable node-local directory and fall back
to `/tmp`. Use the exact [runbook `TMPDIR` pattern](RUNBOOK.md#tmpdir), including
the scheduler export and an explicit shell default. The warning is harmless
only when the job records a writable effective `TMPDIR`; stages with large
spill files may require project storage instead.

### `picard: command not found`

The CSU Picard module exposes a jar through `$PICARD`, not necessarily a
`picard` command. Load the declared module and invoke `java -jar "$PICARD"` as
shown in the [Step `04` procedure](RUNBOOK.md#step-04-markduplicates). Log the
selected Java executable and actual version; the module name and `JAVA_HOME`
do not prove the effective runtime.

### Picard `UnsupportedClassVersionError`

Picard `3.1.1` requires Java `17` (class-file version `61`). Some compute-node
contexts have exposed Java `11` or a nonexistent module-advertised Java path.
Step `04` resolves `JAVA_BIN_OVERRIDE`, then an executable
`$JAVA_HOME/bin/java`, then `PATH`, and rejects runtimes below Java `17` before
Picard starts.

Use the exact [Step `04` override](RUNBOOK.md#step-04-markduplicates) only with
a supported batch-visible Java `17`. Preserve the environment if the known
later unguarded `JAVA_HOME` diagnostic aborts after a valid override; that is a
characterized wrapper defect, not a Picard or input failure. Node pinning may
be a temporary diagnostic workaround, never a permanent architecture rule.

### `#SBATCH --mem=1G` fails

The selected CSU partition may reject that memory form. Use the proven
resource request for the owner in the runbook and omit explicit `--mem` until
partition policy is confirmed; do not infer a pipeline memory requirement from
the submission error.

### `logs/...out: No such file or directory` at submit time

SLURM opens output paths before the job body and does not create their parent.
Create `logs/` before submission using the [logging procedure](RUNBOOK.md#logs).
Body-level directory creation is too late.

### Tailing the wrong log file

Log prefixes differ by owner. Locate the job's actual files with the
[manual-check procedure](RUNBOOK.md#manual-job-checking), then inspect both
matching `.out` and `.err`; do not guess a prefix from a different step.

### Wrong log interpretation: empty `.err` file

Empty stderr is normal for many successful jobs, but is not proof of success.
Require scheduler state/exit `COMPLETED 0:0` plus the owner's output and
validation checks from the [manual-check procedure](RUNBOOK.md#manual-job-checking).

### STAR BAM flagstat counts look larger than input reads

`samtools flagstat` counts alignment records, including STAR secondary
alignments. Use STAR `Log.final.out` for input-read mapping rates and flagstat
for BAM-level QC; do not compare its total-record count directly with input
reads.

### Step 02b `samtools: command not found` despite loaded module

This is a batch `PATH` inconsistency, not a BAM-QC failure. Establish the
supported batch-visible samtools executable/path, record it, and rerun through
the [Step `02b` owner](RUNBOOK.md#step-02b-bam-qc). Do not recreate a removed
flat script path as a workaround.

### RSeQC `infer_experiment.py` not found

Step `03` prefers the checkout's `.venv/bin/infer_experiment.py` relative to
its invocation CWD and otherwise resolves `PATH`. Use the
[Python/RSeQC procedure](RUNBOOK.md#python-and-rseqc); from another CWD, pass an
absolute `--infer-experiment-bin`.

### RSeQC `infer_experiment.py` path exists but is not executable

Path-style tool arguments must be executable; command-style arguments must be
resolvable on `PATH`. Repair permissions only in an intentionally operator-
owned environment, otherwise pass a separately established executable path.

### Step 03 strandedness result looks ambiguous

Verify that the BAM and admitted BAI, BED12, sample, selected RSeQC executable,
job, and logs belong to one attempt. High failed fraction or no dominant group
can reflect the wrong input/annotation, an unstranded library, incompatible
annotation, or a sample-specific issue. Preserve the three groups as
mechanical paired-read-orientation evidence. This route does not authorize a
manifest `strandedness` edit, downstream policy choice, or biological label.

### `module avail gatk` shows nothing

GATK may be available only through a direct cluster installation. Use the
owner's validated path from the [Step `05` procedure](RUNBOOK.md#step-05-splitncigarreads)
and still validate the actual GATK and Java executables in the intended batch
context. Login-node or module visibility is not compute-node proof.

### Step 05 GATK `No space left on device` from `/tmp`

HTSJDK `SortingCollection` spill can exhaust node-local `/tmp`. Use one owned
project-storage temp directory consistently for Java `-Djava.io.tmpdir`, GATK
`--tmp-dir`, and the child `TMPDIR`. After failure, preserve the job evidence
and remove only proven-owned temporary BAM/index and GATK temp paths; never
generalize cleanup to the output directory.

### Picard `SAMRecord.getReadGroup() is null`

The canonical BAM is missing the expected single `@RG` declaration, record
tags, or both. Inspect the header and count records carrying
`RG:<sample_id>`, then regenerate through hardened
[Step `02`](RUNBOOK.md#step-02-canonical-sort-read-group-tagging-and-bam-indexing).
Do not patch around missing read groups in Step `04`.

## Structured validation response

For a failed structured-validation row, inspect the exact declared artifacts,
producer job and logs, and explicit tool identity. Regenerate only through the
functional owner. Never edit a report or native artifact into agreement,
substitute a sibling/globbed path, run repair inside a validator, or promote
local validation beyond its evidence level. The command convention is in the
[runbook](RUNBOOK.md#workflow-contract-and-validation-convention).

### Step 00a structured validation reports failed checks

The explicit STAR index disagrees with the declared FASTA, GTF, ordered
contigs, parameter-path base, or `sjdbOverhang`, or is incomplete. Resolve
relative `genomeParameters.txt` paths only against `--parameter-path-base` and
follow the [common response](#structured-validation-response).

### Step 00a validation report lock or predecessor blocks publication

One scope owns one validation TSV plus adjacent lock/run-token paths. Preserve
the current report, lock owner, and matching `.tmp`/`.previous` files. Recover
a validated predecessor or clean first-publication state before execute mode;
an absent lock can coexist with a surviving `.previous` after failed restore.

## Validation publication leaves ambiguous recovery state

Shared step-validator, runtime-preflight, reference-provenance, and storage
publishers do not have identical exception boundaries. Characterized failures
can remove lock protection after an incomplete restore, leave backups without
a marker, retain a preflight lock, or unlink a final that appeared late.

Stop retries and apply the [recovery rules](#recovery-rules-for-any-ambiguous-transaction)
to the exact final, run-token `.tmp`/`.previous`, lock, process, filesystem
identity, and command log. There is no generic automatic recovery. Do not
delete or adopt a path merely because a characterization test reproduces it.

### Step 00b structured validation reports BED12 or GTF disagreement

The BED12 is malformed, unsorted, duplicated, block-invalid, or differs from
deterministic exon normalization of the explicit GTF. Preserve the final and
intermediate BED plus logs; regeneration belongs only to
[`convert_GTF_to_BED12`](../../src/norad/stages/convert_GTF_to_BED12/README.md).

## Step 00c FAI/DICT validation fails

The shared FAI or DICT is missing, malformed, stale, or from another FASTA.
The characterized producer can publish the FAI before DICT publication fails,
leaving incomplete-attempt evidence. Preserve both sidecars, producer context,
logs, locks, and run-token paths. Step `05` must not create or repair them.
After provenance and ownership are established, use only the
[Step `00c` owner](RUNBOOK.md#step-00c-gatk-reference-sidecars); it may reuse a
valid FAI when a separately authorized run creates the missing DICT.

### Step 00c structured validation reports FASTA/FAI/DICT disagreement

One explicit reference input is malformed, truncated, or from a different
reference. Resolve provenance; the validator never infers or repairs sidecars.
A private owner-load failure is checkout integrity, not authority to use a
`PYTHONPATH` workaround.

### Step 01 structured validation reports STAR output disagreement

The BAM, three STAR logs, and splice-junction table may be incomplete,
truncated, malformed, or from different attempts. Preserve all five plus the
scheduler evidence. Use the final
[Step `01` owner diagnostics](../../src/norad/stages/align_RNA_reads_with_STAR/README.md#diagnostics-recovery-and-evidence);
local validation does not replace cluster evidence.

## Step 02 canonical BAM rollback leaves a prior-BAI-only lockless pair

A characterized publication-plus-restoration failure can remove the prior BAM,
leave the prior BAI, and erase locks, backups, scratch, receipts, and recovery
markers. This is an ambiguous data-loss state, not successful rollback.

Stop retries. Preserve the complete pair directory, all surviving finals and
run-token paths, streams, job/run token, tools, and filesystem context. Absence
of recovery artifacts is not cleanup authority. Recovery or reconstruction
requires separate review after ownership and evidence are established.

### Step 02 BAM-validation helper cannot load

Step `02`, `04`, or `05` could not exact-load private
`src/norad/libraries/bam_validation.py`. Inspect the named file, checkout, and
in-process module cache. Do not add `PYTHONPATH`, install a package, copy the
helper, expose a public CLI, or restore a legacy validator path.

### Step 02 structured validation reports canonical BAM disagreement

The pair fails container/index, quickcheck, coordinate-sort, read-group header,
or record-tag checks, or the selected samtools cannot inspect it. Sorting,
indexing, and read-group regeneration belong to the
[Step `02` owner](RUNBOOK.md#step-02-canonical-sort-read-group-tagging-and-bam-indexing).

## Step 02b producer or wrapper leaves a partial, mixed, or stale evidence pair

The producer writes quickcheck and flagstat directly to final paths without a
lock, stage, backup, receipt, rollback, stable-input recheck, or set-level
commit. A failed child can leave one new/partial file beside predecessor bytes;
the wrapper's existence checks can accept a stale pair after a zero-output
child.

Preserve both files, directory entries, BAM/BAI identity, streams, job, tools,
and metadata. Establish which attempt owns each before any same-name retry.
The final validator can inspect persisted bytes but does not rerun samtools,
establish attempt identity, repair output, or gate downstream work.

### Step 02b structured validation reports BAM-QC disagreement

Quickcheck or flagstat is malformed, duplicated, count-invalid, or drawn from
another attempt. Inspect persisted evidence and its producer, then use the
[Step `02b` owner](RUNBOOK.md#step-02b-bam-qc) after resolving any
[mixed pair](#step-02b-producer-or-wrapper-leaves-a-partial-mixed-or-stale-evidence-pair).

## Step 03 producer or wrapper leaves a partial, empty, or stale report

RSeQC stdout is redirected directly to the final report. There is no lock,
stage, backup, receipt, stable-input recheck, or rollback; a failed child may
leave partial bytes, and a zero-output child can let the wrapper rediscover a
stale nonempty report.

Preserve the report and metadata, unrelated files, both stream sets, job/tool
identity, BAM/BAI, and BED12. The final validator inspects persisted bytes only;
it neither reruns RSeQC nor proves current-attempt identity. Record a recovery
decision before deletion or same-name reuse.

### Step 03 structured validation reports RSeQC fraction disagreement

The report has missing/duplicate labels, invalid fractions, or a sum outside
tolerance. Inspect the exact persisted report/job and preserve group labels as
mechanical evidence. Follow the [Step `03` owner](RUNBOOK.md#step-03-rseqc-strandedness--orientation-inference)
after resolving any [stale report](#step-03-producer-or-wrapper-leaves-a-partial-empty-or-stale-report).

## Step 04 producer or wrapper leaves a partial, mixed, or stale output triplet

Picard BAM, metrics, quickcheck, and index are written to final paths without a
lock, stage, all-or-none transaction, stable-input recheck, or rollback. A
failure can leave a new/partial/prior BAM, BAI, and metrics mix; a zero-output
child can let the wrapper accept a stale nonempty triplet.

Stop downstream Step `05` reads. Preserve the triplet and canonical input,
streams, job, checkout, Picard jar, Java/samtools identities, `TMPDIR`, and
directory metadata. Any reviewed diagnostic retry must use isolated output and
metrics paths. Use the [Step `04` owner](RUNBOOK.md#step-04-markduplicates) only
after attempt ownership is resolved.

### Step 04 structured validation reports BAM or duplication-metrics disagreement

The pair fails BAM/BAI checks or the metrics lack one valid reconciled data
row. Inspect the exact triplet, tools, job, and logs. Duplicate marking or BAM
repair belongs only to Step `04`; resolve the
[mixed triplet](#step-04-producer-or-wrapper-leaves-a-partial-mixed-or-stale-output-triplet)
before same-name reuse.

## Step 05 producer or wrapper leaves a partial rollback failure or stale pair

Step `05` stages and validates a pair, backs up a complete predecessor, then
publishes BAM and BAI sequentially. Restoration is best-effort and cleanup can
erase backups, scratch, lock, GATK temp, and recovery evidence after a restore
failure. A characterized severe state loses the prior BAM while restoring only
the prior BAI. Inputs are not snapshot-rechecked, publication has no receipt,
and wrapper existence checks can accept a stale pair.

Stop Step `06` readers. Preserve every final/staged/alternate index/backup/temp
path, lock owner, all five input/reference files, unrelated bytes, streams,
job/accounting, CWD, overrides, and exact GATK/Java/samtools diagnostics. Never
combine pair members or rerun into the questioned directory. A diagnostic retry
uses an isolated output directory. The validator can inspect a complete pair
but cannot establish attempt identity or repair it. See the
[Step `05` owner](RUNBOOK.md#step-05-splitncigarreads).

### Reference-contig owner cannot load

Reference provenance or Step `00c`/`05` could not exact-load
`src/norad/libraries/reference_contigs.py`. Inspect the exact file, checkout,
and module cache. Do not alter `PYTHONPATH`, install/copy the parser, replace
the cache, or restore a bridge. Successful loading followed by content
disagreement belongs to the relevant validator route.

### Step 05 structured validation reports output or reference disagreement

The split BAM/BAI is incomplete or the FASTA/FAI/DICT do not agree. Reference
repair belongs to Step `00c`; split-output regeneration belongs to Step `05`.
Resolve any [partial or stale pair](#step-05-producer-or-wrapper-leaves-a-partial-rollback-failure-or-stale-pair)
first.

## Step 06 producer or wrapper leaves a partial rollback failure, collision, or stale set

The owner publishes two BAM/BAI pairs plus a counts TSV across output and QC
roots, but locks only the selected output directory. Best-effort restoration
and cleanup can erase recovery evidence; a characterized severe state loses
the prior FWD BAM while restoring the other four files. Distinct output locks
can race on the shared QC counts path, and wrapper existence checks can accept
five stale files. The input pair is not snapshot-rechecked and the counts row
is not an attempt receipt.

Stop Step `07` readers and every writer to both roots. Preserve all finals,
filter/stage files, backups, locks, input pair, unrelated bytes, streams,
scheduler evidence, CWD, threads, and samtools identity. A diagnostic retry
must isolate both output and QC directories. Do not infer one attempt from
counts or timestamps. The final validator reconciles declared counts but does
not quickcheck/recount BAMs, prove BAM/BAI correspondence, or establish attempt
identity. See the [Step `06` owner](RUNBOOK.md#step-06-split-bam-by-read-orientation).

### Step 06 structured validation reports output or count disagreement

The two pairs and counts row are malformed, incomplete, or from different
attempts, or group sums/fractions do not reconcile. Preserve `FWD_like` and
`REV_like` as mechanical labels. Resolve the
[cross-root transaction](#step-06-producer-or-wrapper-leaves-a-partial-rollback-failure-collision-or-stale-set)
before regeneration.

### Step 07 structured validation reports transaction disagreement

The receipt, VCFs, selectors, manifest identities/order, paths, or record counts
do not form one complete transaction. A header-only VCF is valid when its zero
record count and sample columns reconcile. Use the
[Step `07` owner](RUNBOOK.md#step-07-bcftools-mpileup) after resolving any
ambiguous transaction.

### Step 07 selector does not match the FASTA index

Every `region` or `regions_file` contig must exactly match the supplied FAI.
Inspect the runtime FAI and declared partition selector; do not silently rename
contigs, drop a partition, or alter the declared universe. Correcting that
universe requires explicit manifest review.

### Step 07 rejects VCF sample columns

VCF samples must exactly equal manifest order; bcftools derives them from BAM
read-group `SM` values. Compare the manifest with each BAM header and VCF sample
list. Correct metadata/order upstream and regenerate; never hand-edit or reorder
a VCF header.

### Step 07 cannot establish the runtime sample manifest or later reports a manifest hash mismatch

Provision one durable runtime manifest with approved explicit replicate values,
record its SHA-256, and use byte-identical bytes through Steps `07`-`09`. A
pairing reference TSV is not a runtime overlay. Any later manifest change
invalidates affected receipt chains and requires normal regeneration; never edit
stored hashes to force acceptance.

## Step 07 producer or wrapper leaves a partial rollback failure or stale transaction

Step `07` uses a cohort/partition lock, run-token temporary/backups, all-three-
or-none predecessor admission, sequential FWD/REV/receipt publication, and
receipt-last ordering. The receipt can be visible before final validation and
there is no durable attempt marker. Restoration is best-effort; a severe
characterized state can leave the prior FWD final absent while its backup
survives. Only manifest inputs are hash-bound and snapshot-rechecked; wrapper
existence checks can accept a stale three-file set.

Preserve all stable/temp/backup files, lock owner, manifests and hashes,
selected Step `06` pairs, reference/regions inputs, directory bytes, streams,
job/accounting, CWD/overrides, and bcftools/filter/depth identity. Never edit a
receipt, remove a foreign lock, combine attempts, or infer identity from
visibility/counts. A diagnostic retry uses an isolated absolute root. The
primary-universe gate requires 25 primary receipts and 50 primary VCFs; the
separate pilot transaction does not enter that count. Current failure/recovery
characterization is local/mock evidence unless an inspected runtime record says
otherwise.

### Step 07 VCF has a header but no records

Zero records can be a valid filter result. Accept it only when VCF structure,
manifest-ordered samples, and the receipt's zero count reconcile. Investigate
only an unexpected biological/region result or failed header/sample contract.

## Runtime preflight profile or output contract is rejected

The preflight accepts one exact nonempty TSV with closed IDs, contexts, check
types, arguments, expectations, and absolute visibility paths. Execute output
must be a safe existing parent and `.tsv` filename. Compare with
[`configs/runtime_preflight.example.tsv`](../../configs/runtime_preflight.example.tsv),
correct the declaration, and rerun dry-run. Never weaken a required check or
substitute local paths for cluster paths to obtain a pass.

### Runtime preflight reports fail, blocked, or not_checked but exits zero

Exit `0` means probes/publication completed, not that rows passed. A required
`cluster_batch` check run in local context is `blocked`; optional is
`not_checked`. Run cluster checks only in the approved batch context. The tool
does not load modules, install packages, repair paths, or promote statuses.

### Runtime preflight lock or previous report blocks publication

Inspect the lock owner, profile hash/context, current report, and run-token
`.tmp`/`.previous`. Preserve invalid predecessors and foreign locks; recover a
validated prior report or use a new output path. Local fixture success is not
cluster availability or recovery evidence.

### Reference provenance reports missing, malformed, hash, or contig failures

Inspect the exact inventory row, digest, contig rows, agreement fields, source
files, locks, and run-token paths. Correct declarations or regenerate through
the formal upstream owner after review. This read-only tool must never rebuild
sidecars/indexes, rename contigs, edit hashes, or discard an unresolved source.

### Storage inventory reports missing roots, measurement failures, or unapproved policy

Inspect the explicit root/policy rows, resolved path, capacity/quota evidence,
approval state, and summary in the intended CSU context. Correct the contract
or environment explicitly. The tool never executes retention actions; local
measurements are not cluster evidence and pending/rejected policy is not
approval.

### Storage inventory lock or prior transaction blocks publication

Inventory, normalized policy, and summary form one summary-last transaction.
Preserve the lock owner, all three stable files, and run-token
`.tmp`/`.previous`. Recover a validated complete predecessor or clean first
publication; never combine attempts or use this tool to alter storage content.

### Quiet local validation reports a failure or appears silent

Quiet validation redirects each lane to a temporary log and prints completion
or failure records; silence while a child runs is expected. Inspect every
retained failed or interrupted log before rerunning. Verbose mode streams merged
output and serial mode is the supported fallback. Failure cancels/reaps pending
children; interruption returns `130`. Do not delete retained logs or rerun
successful lanes merely for progress output. Commands are in the
[local-validation runbook](RUNBOOK.md#local-validation-gate).

### Python coverage baseline cannot run or reports a regression

Verify the project environment, exact pinned coverage/parallel dependencies,
subprocess data, current JSON, baseline JSON, and named module. Use the tracked
environment and [coverage procedure](RUNBOOK.md#python-coverage-baseline); do
not install globally or update the baseline merely to pass. A deliberate
baseline change requires exact JSON and contract review. Coverage remains local
developer evidence and cannot replace shell, real-R, runtime, transaction,
oracle, or cluster testing.

## Step 08 or Step 09 cannot find `Rscript`

Both owners require an explicit executable. Step `08` additionally requires
its declared Bioconductor namespaces; Step `09` uses base R but its R engine
requires `sha256sum` or `shasum`. Repository-local `renv` activation is opt-in,
and local availability does not prove batch visibility.

Use the [guarded local-R procedure](RUNBOOK.md#guarded-local-r-environment) for
development and pass an absolute `--rscript-bin` or batch-visible
`RSCRIPT_BIN_OVERRIDE` for workflow execution. Only `make r-restore` installs
packages; analysis, validation, SLURM, and rendering code must not. Use absolute
program and data paths from another CWD. A skipped real-R test is not a pass,
and local real-R success is not CSU or production proof.

### `renv` startup uses sustained CPU or repeatedly creates directories

The guarded macOS runtime has reproduced an `renv` sandbox directory loop. Use
the reviewed setting from the [local-R procedure](RUNBOOK.md#guarded-local-r-environment),
which disables the sandbox during opted-in activation. Do not enable automatic
snapshots or edit the lockfile as a workaround.

### Local `renv` reports lock drift or missing Step 08 namespaces

The ignored project library may be absent/drifted, the runtime may differ from
the lock, or release metadata may be unreachable. Use explicit restore/check
commands in a network-capable developer environment. A DNS/download error is
not proof of package drift and is not a passing offline check. Do not hand-edit
`renv.lock`, install directly into the library, or change the dependency/runtime
contract without separate review.

### Step 08 structured validation reports transaction disagreement

Sites, input receipt, and summary may not form one transaction; identities,
partition/orientation universe, candidate order, or counts may disagree. Use
absolute paths when diagnosing relative annotation spelling. Preserve source
receipts and regenerate only through the
[Step `08` owner](RUNBOOK.md#step-08-vcf-preprocessing).

### Step 08 rejects a Step 07 receipt, VCF, hash, count, or sample order

Step `08` consumes the declared partition-by-orientation product and requires
each Step `07` receipt to agree with cohort/selector, exact VCF paths, manifest
hashes/count/order, and VCF row counts. Restore the exact upstream manifests or
regenerate the affected Step `07` transaction. Never edit headers, hashes,
paths, or counts, and never replace the declared set with a glob.

### Step 08 rejects partition overlap, duplicate candidates, or malformed counts

Partitions must not overlap and candidate identity is global. DP/AD fields must
be integer, nonnegative, width-correct, and internally consistent; raw lexical
validation runs before parser coercion. A single `.` can represent a wholly
missing AD vector. Valid symbolic/non-SNV alternates are counted and excluded,
not errors. Correct the manifest or upstream VCF; never deduplicate, clamp,
truncate, or rewrite counts. Production-scale cost of the extra streaming pass
remains unproven and should be benchmarked in an isolated pilot before full
promotion.

### Step 08 finds a lock, partial output set, or input mutation

Another writer may own the cohort lock, a prior operation may have left fewer
than the three stable files, or a bound input changed after admission. The
input receipt is published last; one or two files are not a transaction. Wait
for an active owner or apply the common recovery rules to both output and QC
roots. Never manufacture the receipt or bypass hash checks.

## Step 08 producer or wrapper leaves a partial rollback failure or stale transaction

Step `08` publishes sites, cross-root QC summary, then input receipt. Receipt
visibility precedes final validation. Best-effort restoration spans two roots
without a durable recovery marker; a severe characterized state leaves the
prior sites final absent while its backup survives. Wrapper existence checks
can accept three stale files.

Preserve both roots, locks, all finals/temp/backups, manifests, Step `07`
transactions, annotation, R program/runtime/library, streams, scheduler
evidence, CWD, and overrides. Rule out Step `09`/`09c` readers. Never combine
attempts or retry the same roots; isolate both output and QC roots for a
separately authorized diagnostic. Characterization is local shell/fake-R/
real-R test evidence unless an inspected runtime record says otherwise.

### Step 09 rejects the sample manifest pairing

Step `09` requires explicit replicate metadata: exactly one control and one
treatment per replicate, equal replicate sets, and at least two strata. Do not
infer pairing from sample names or merge the reference pairing TSV as a runtime
overlay. Add approved metadata before Step `07`, validate the manifest, and
regenerate artifacts whose hashes bind older bytes.

### Step 09 rejects Step 08 hashes, receipts, rows, or sample columns

The two Step `08` tables and full partition-by-orientation universe must match
current manifests, input receipts, candidate order, orientation policy, and
sample columns. Restore the exact upstream manifests or regenerate Steps `07`
and `08`; never edit receipts or reorder rows/columns to force Step `09`.

### Step 09 rejects R outputs, background statuses, or plot signatures

The wrapper independently reconciles all-sites, significant-sites, summary,
mutation spectrum, and two PDFs. A successful R child is insufficient when
schemas, sample counts, strict thresholds, background status/fraction, one
global BH family, exact significant subset, hashes/counts, mutation fractions,
or PDF boundaries disagree. Regenerate all six through the committed owner;
never patch outputs.

Preserve the selected Rscript, R-program bytes/path, startup/library state, and
streams. The producer detects admitted data mutation but not every selected
R-program mutation, and its summary omits durable attempt, runtime/package,
and sibling-output hashes. That is an evidence ceiling, not acceptance
authority.

### Step 09 structured validation reports transaction or semantic disagreement

The validator checks one six-file transaction, upstream identity/order,
background/status semantics, exact significant subset, summary/mutation
reconciliation, and PDF structure. It does **not** independently recompute
estimability, CMH statistic, p-value, or common odds ratio; existing row text
that suggests full CMH recomputation overstates the evidence. Preserve its rows
with the separate oracle and real-R results. Relative producer paths require
the original CWD or explicit absolute paths.

### Step 09 scheduler succeeds with stale outputs or an unusable R selection

The scheduler delegates R validation to the child and checks only that six
names exist after exit `0`; stale outputs can satisfy it. Preserve scheduler
identity, CWDs, overrides, child streams, all outputs/hashes, lock, and
temp/backups. Create `logs/` before later submission, establish an absolute
batch-visible R selection, and use a fresh root for diagnostics. Do not treat
job exit plus file presence as current production.

## Step 09 finds a lock or incomplete six-output set

One analysis lock protects four TSVs and two PDFs. The summary is published
last, but visibility can precede final checks and it carries no durable attempt
or five-sibling hash identity. Inspect lock owner, scheduler state, all six
finals, and hidden run-token paths. Wait for an active owner or make an explicit
evidence-preserving recovery; never combine or manufacture members.

### Step 09 rollback is incomplete and retains its lock

Lock retention is intentional when partial new files cannot be removed or a
predecessor cannot be restored. Preserve the owner/run token/PID, scheduler
state, all six finals, `.previous` backups, and temporary paths. Restore one
complete validated predecessor or remove an incomplete new set, record the
action, then remove only the proved-owned lock. Do not clear it merely to
retry.

### Step 09c rejects evidence, status, hashes, or row counts

Step `09c` requires explicit manifests, the Step `08` transaction, Step `09`
analysis, review plan, evidence manifest, and their identities/hashes/counts/
statuses/decisions to reconcile. Missing evidence must remain explicit.
`science_review_complete_exploratory` requires its stricter completed-evidence
and decision set; `biological_interpretation_ready` is reserved and rejected.
Runtime/cluster claims require their defined underlying evidence, while
blocked/not-run states prove nothing.

Correct source evidence or declarations and rerun dry-run. Never edit a hash,
count, status, or decision to force acceptance, replace missing evidence with
an empty file, or infer a reviewer choice. From another CWD, use absolute paths
for every declared input/payload and preserve original path resolution. Fixture
success is not a completed production review.

## Step 09c finds a lock, partial output set, changed input, or incomplete rollback

One review transaction owns 13 stable TSVs, a regular mode-`0600` lock file,
run-token temporary/previous directories, and an optional best-effort recovery
marker. All 13 outputs must be present or absent. The summary is published last
but can be visible before final validation and the second check of 32 inputs;
it does not hash twelve siblings.

Characterized signal paths are severe: `TERM` after summary visibility can
leave unvalidated finals, backups, and lock without a marker; an interrupt can
leave new finals while cleanup removes backups and lock. An absent lock or
visible summary is therefore not commit proof.

Preserve all stable outputs and bound inputs, lock metadata, run-token paths,
marker, streams, environment, process/signal evidence, and unrelated bytes.
Recover explicitly to a complete previous 13-file set or no set, validate,
record the action, and remove only proved-owned residue. For cleanup-only errors
inspect exactly the named paths; some may already be gone. Diagnostics use a
new isolated absolute root. These recovery states are characterized with
synthetic fixtures unless an inspected production incident says otherwise.

## Neutral contract load failures

Neutral scientific-evidence contracts are exact-loaded from the tracked
checkout under fixed internal module names. A missing/unreadable file, foreign
cache entry, partial initialization, readiness-marker failure, or split owner
identity is checkout integrity—not content disagreement.

### A Step 08, Step 09, artifact, or Step 09c consumer cannot load the neutral Step 08 contract

Inspect `src/norad/contracts/scientific_evidence/step08.py`, Git state, cached
module identity, and the invoking consumer. Restore the reviewed file through
Git. Do not copy the surface into a consumer, add a bridge, install a package,
or alter `PYTHONPATH`/`sys.path`. Use the
[Step `08` checks](RUNBOOK.md#step-08-vcf-preprocessing).

### A Step 09, artifact, or Step 09c consumer cannot load the neutral Step 09 contract

Inspect both `step09.py` and its exact Step `08` owner plus their cached
identities. Apply the same no-copy/no-search-path rule and use the
[Step `09` checks](RUNBOOK.md#step-09-cmh-editing-site-calling).

### A Step 09c, artifact, or run-summary consumer cannot load the neutral review-package contract

Inspect `review_package.py`, Git state, cached identity, and the consumer. The
run summary reads this public standard-library-only contract, not the private
Step `09c` implementation. Do not recreate it in reporting or add a compatibility
alias/search path; recheck the neutral and affected consumer suites.

### Step 09c fixture output is mistaken for a completed scientific review

Fixtures establish local contract behavior only. Unless production evidence
has been inspected, report: implementation/fixture testing exists; production
Step `09c` evidence is unavailable; production science remains
`evidence_incomplete`; `biological_interpretation_ready` remains rejected.

## Artifact contract validation cannot import `jsonschema`

The selected Python environment is absent or unsynchronized with tracked
requirements. Use the project virtual environment and the explicit dependency
setup in the [artifact-schema procedure](RUNBOOK.md#validate-artifact-schema-v1).
Never install dependencies from compute wrappers, SLURM jobs, adapters,
summary builders, or renderers.

### Artifact JSON or inventory validation fails

Contracts fail closed on non-strict JSON, wrong schema/version/type, invalid
canonical run hash, incoherent attempt/evidence/science state, unresolved or
unsafe paths, and malformed/duplicated/noncontiguous inventory rows. Inventory
paths and IDs must be explicit and unique; `required` is lowercase Boolean.
Inventory reconciliation applies only to artifact records and run summaries.

Correct the declaring producer/inventory at the first invariant. Never edit a
hash, status, evidence role, attempt link, path, or readiness value to pass. A
canonical run-identity change requires a new `run_id`; an identical-contract
retry needs a distinct attempt ID. Use the focused
[schema checks](RUNBOOK.md#validate-artifact-schema-v1). Fixture success is not
production artifact validation.

### Artifact adapter rejects `--run-contract` or an existing run ID

The immutable contract binds the sample manifest, reference contract,
partition manifest, primary analysis ID/policy, and canonical hash. While its
receipt remains in one output root, a `run_id` is locally bound to those values;
this is not a global registry. If an immutable field changes, choose a new run
ID. An inventory-only revision may retain it and creates a superseding adapter
attempt. Never edit an old receipt/hash to conceal change.

### Artifact adapter finds a lock, partial transaction, or incomplete rollback

Records directory, ordered index, and receipt form one receipt-last
transaction. Inspect lock metadata, current transaction, sources, and every
reported temp/backup/quarantine/recovery path. The marker is best-effort and a
restored invalid receipt may be quarantined. Recover a validated complete prior
transaction or clean first publication before removing a proved-owned lock;
never combine attempts or discard evidence.

### Artifact receipt is complete but evidence records are not

Transaction completion means records/index/receipt committed together, not
that expected artifacts exist or computation/science passed. Adapter v1 records
implementation evidence and leaves native local/runtime/cluster fields at
their declared states. Step `09c` science propagation has separate complete-
transaction and evidence/decision requirements. Treat explicit statuses as the
result; never promote them manually. Keep production science
`evidence_incomplete` unless the declared reconciliation passes.

### A passing artifact-schema fixture is mistaken for an artifact index, report, or validation evidence

Schema fixtures validate declarations; they do not discover sources, build a
production transaction, inspect hashes, run analysis, or render a report.
Describe only the exact implemented and locally tested contract. Do not claim
production/cluster validation, completed science review, or biological
readiness.

### Run-summary input transaction or immutable run contract is rejected

The builder accepts only the exact complete adapter receipt under its declared
`OUTPUT_ROOT/<run_id>/`. Moving, copying, editing, or mixing receipt/index/
inventory/record members breaks identity and attempt relationships. Point to
the committed receipt or regenerate the complete adapter transaction; never
edit IDs, hashes, counts, or receipts.

### Explicit Step 09c summary is rejected by the run-summary builder

The optional summary must be the exact marker of a committed 13-file review
transaction with coherent evidence, decisions, identities, and computational
claims. Correct and republish that transaction. If none exists, omit the option
and retain `evidence_incomplete`; do not point to a copy, decoy, or hand-edited
table.

### Report-table approvals are rejected by the run-summary builder

Approvals are one explicit nonempty TSV bound to the current run/contract and
exact committed Step `09c` table artifacts. Path, hash, row count, role,
display limit, policy, approver, and nonfuture UTC timestamp must reconcile;
duplicates, globs, traversal, symlinks, decoys, and mutations fail closed.
Populate the tracked example from actual current artifacts. Omit the option
when no table is approved; a header-only file is invalid. Approval authorizes
display, not scientific completion or status promotion.

### Run-summary lock, partial output set, or recovery state remains

Canonical JSON, two TSV views, and receipt form one receipt-last transaction.
Inspect the regular lock, process, four outputs, adapter/review/approval/table
inputs, output-directory identity, and all temp/backup/recovery paths. If the
directory identity changed, do not perform path-based recovery until resolved.
A post-commit cleanup failure may leave a valid new transaction: validate it
first, otherwise restore a validated predecessor or clean first publication.

### Run-summary receipt is complete but evidence is missing or failed

`summary_state=complete` describes four-file publication only. Missing, failed,
incomplete, externally unavailable, `not_run`, or `evidence_incomplete` states
remain the result. Do not promote or edit them; regenerate only after a later
owner supplies valid typed evidence.

### A record is validated against the wrong 1.0 or 1.1 schema

The common schema retains its `v1` URN; artifact records are `1.0.0`;
scientific-review, run-summary, and report-receipt JSON are `1.1.0`; producer
TSV contracts remain `1.0.0`. Regenerate with the matching producer/schema.
Changing only `$id` or a version string is invalid because shapes differ.

### A synthetic run summary is mistaken for production evidence or a report

The summary builder records supplied evidence and performs no analysis or
rendering. Synthetic fixtures establish local behavior only. Do not claim a
production transaction/report, runtime or cluster proof, completed production
review, or biological validation.

### Quarto restore rejects the archive, installed tree, version, or lock

The report runtime is pinned to the reviewed Quarto archive/version/checksum
and a deterministic installed-tree receipt. Wrong platform/archive/hash,
mutated tree/receipt, foreign lock, partial install, or cleanup residue fails
closed. Use the exact [restore procedure](RUNBOOK.md#restore-quarto-and-render-the-static-report-bundle),
including its checksum gate. Never weaken the hash, edit the receipt, use an
unreviewed package manager install, or let a renderer download dependencies.
Inspect lock/temporary/recovery paths before an operator-reviewed relocation or
removal of only the proved ignored tooling target.

### `make demo-report` cannot find tools or the HTML still widens the page

The demo does not restore Quarto or install Python packages. Generated HTML is
self-contained, so regenerate and reopen the exact new path. Wide approved
tables scroll within their focusable region by design. Follow the
[demo procedure](RUNBOOK.md#generate-the-populated-synthetic-demo-report);
never edit ignored HTML, remove authorized columns, or call synthetic content
production evidence.

### Report bundle rendering rejects the run summary, approved table, or output

The renderer accepts one explicit canonical run summary plus its explicitly
approved tables. It validates stable inputs/tool identity, script-free
self-contained accessible HTML, PDF boundaries/text/order/banner, summary TSV,
and receipt. Dry-run publishes nothing; execute publishes only the selected
formats plus summary and receipt. Correct inputs through their validated
producers, use the pinned Quarto, rerun dry-run, and never edit identities,
hashes, counts, banners, templates, outputs, or receipts to force acceptance.
See the [report procedure](RUNBOOK.md#restore-quarto-and-render-the-static-report-bundle).

### Report bundle lock, rollback, cleanup, or recovery state remains

Selected reports, summary TSV, and receipt form one receipt-last transaction.
The owner stages output, snapshots inputs, validates predecessors, and runs
Quarto in a process group. Signals/timeouts terminate the group before cleanup;
identity-changed directories or late foreign files are not clobbered. Inspect
the lock/process, bundle, all input hashes, directory identity, and stage/
backup/marker paths. Determine whether a validated new bundle committed or the
exact predecessor must be restored, then remove only proved-owned residue.

### A synthetic report bundle is mistaken for production or validation evidence

Rendering presents the declared input state but creates no computational or
scientific evidence. Local fixtures and the pinned local renderer prove only
local report-contract behavior. Preserve the state banner and limitations; do
not claim production pipeline execution, cluster proof, completed production
science review, or biological readiness.

## Concurrent lane is in the wrong worktree, overlaps, or cannot integrate

Stop mutation when worktree, branch, base, candidate SHA, reserved paths, or
coupling differs from the lane packet. Use the read-only inspection steps under
[concurrent worktrees](RUNBOOK.md#concurrent-worktrees-and-serialized-integration).
Do not stash, switch, reset, clean, prune, merge, rebase, or resolve overlap
opportunistically. Preserve candidate commits and conflict evidence; the
integration owner repairs the packet or returns the governing task to planning.

## Evidence ceilings and success criteria

A computational owner is `cluster-proven` only when its declared dry-run and
execute jobs complete successfully, their commands/context are correct,
stderr is empty or understood, expected outputs exist, and owner-specific
schemas, hashes, counts, sample order, and cleanup contracts reconcile. Do not
advance downstream cluster execution until the required upstream owner meets
that boundary.

This proves runtime execution, not biological interpretation. Mechanical
orientation labels, annotation semantics, statistical robustness, candidate
adjudication, and limitations require their scientific evidence and decision
owners. `science_review_complete_exploratory` retains its policy constraints;
`biological_interpretation_ready` remains reserved until a separately approved
scientific-policy change establishes and satisfies its exit criteria.
