# `align_RNA_reads_with_STAR` stage contract

This directory owns historical Step `01`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The private validator is installed; the producer remains
an explicit repository-path command.

## Responsibility

The [README](README.md) explains alignment inputs, outputs, and use. Validation
reads the declared outputs without rerunning STAR or changing them.

## Execution dependencies

The hard data prerequisites are one read-1 FASTQ, its read-2 FASTQ mate, and a
STAR genome-index directory. Both FASTQs must use the same compression mode;
gzip handling is selected from their `.gz` suffixes. Historical Step `00a` is
the current producer of the required index, but this stage consumes only the
explicit index path and does not depend on how that index was constructed.

Samples are independent and may align in parallel once their reads and index
are available. Historical Step `02` consumes the STAR alignment and must
complete before later canonical-BAM consumers run. STAR's final, general, and
progress logs and splice-junction table are evidence outputs rather than
execution prerequisites for Step `02`.

## Inputs

The producer accepts:

- a nonempty sample identifier used in output-name construction;
- one read-1 and one read-2 FASTQ or FASTQ.GZ file path;
- one STAR genome-index directory;
- one explicit output directory;
- a positive thread count; and
- an available STAR executable, plus an explicitly selectable `gunzip`
  executable when both FASTQ paths end in `.gz`.

The current producer checks path types, matching compression suffixes,
sample-identifier path safety, FASTQ byte stability, and a deterministic
snapshot of every top-level STAR-index member. It does not validate FASTQ
content or biological pairing.

## Outputs

With output prefix `<output-dir>/<sample-id>.`, the protected minimum output
set is:

```text
<sample-id>.Aligned.sortedByCoord.out.bam
<sample-id>.Log.final.out
<sample-id>.Log.out
<sample-id>.Log.progress.out
<sample-id>.SJ.out.tab
```

STAR may produce additional files. The BAM is requested directly as
coordinate-sorted output with one read group whose `ID`, `SM`, and `LB` equal
the sample identifier and whose platform is `ILLUMINA`. Historical Step `02`
validates that canonical content, indexes it, and publishes the canonical
BAM/BAI pair without rewriting the BAM when a same-filesystem hard link is
available. Its generic-input fallback still sorts and/or retags noncanonical
alignments.

## Orchestration-safe producer boundary

Every invocation refuses replacement; `--no-clobber` is accepted but does not
select a different mode. Dry-run shows the plan without writing. Execute holds
a per-sample owned lock, requires all five final paths to be absent, and runs
STAR in a run-token staging directory. Every declared output must be nonempty.

The producer checks FASTQ hashes before publication. It also checks every
top-level STAR-index entry: each must be a readable, nonempty regular file.
Symlinks, directories, special files, and tab/newline-containing names are
rejected. A bytewise-name-ordered basename/SHA-256 snapshot must have identical
membership and bytes immediately before STAR and again after STAR.

Publication hard-links each staged file to its absent final path, retaining
the staged inode to prove ownership. All finals must still match their anchors
before success removes staging and then the lock. Failure before publication
removes only owned staging. During publication, rollback removes a final only
while it remains the same regular-file inode as its anchor. A late or replaced
foreign final is preserved with the lock and staging for recovery; existing or
foreign state is never adopted or deleted.

`--star-bin` selects the STAR executable. For two `.gz` mates, `--gunzip-bin`
selects the decompressor passed to `--readFilesCommand`; omission uses `gunzip`
on `PATH`. Plain mates do not resolve or validate a decompressor. Observed tool
versions and output hashes belong in the workflow verified record.

## Current execution surfaces

The [shell producer](step_01_star_align.sh) validates arguments and executable
availability before the transaction above. For two `.gz` mates, it passes the
selected decompressor to STAR as `--readFilesCommand ... -c`. Dry-run neither
invokes STAR nor creates an output directory.

## Validation interface

`emrys validate star-alignment`, implemented by private
[`validator.py`](validator.py), accepts an explicit scope, BAM, three STAR log
paths, splice-junction table, and output path. Validation is dry-run by
default; `--execute` publishes `<scope-id>.validation.tsv` using the common
seven-field step-validation contract.

The report contains exactly these five check identities:

- `output_files`;
- `bam_structure`;
- `final_log_structure`;
- `mapping_summary`; and
- `splice_junction_structure`.

The checks require five nonempty regular outputs, BAM or BGZF magic bytes,
unique nonempty key/value rows in `Log.final.out`, three required mapping
percentages in the range zero through 100, and zero or more structurally valid
nine-column splice-junction rows. These are container and report-structure
checks; they do not establish alignment correctness or scientific validity.

A content mismatch is represented by a `status=fail` row and does not repair
the STAR outputs. Missing, unreadable, or unsafe input, an invalid CLI/output
contract, or unsafe publication state exits with code `2` without publishing a
new report.

Validation publication uses the shared
[`validation`](../../libraries/validation/README.md) facade. Grouped invocation
binds the selected installed package independently of caller CWD and ambient
`PYTHONPATH`, rejecting a different installed checkout from an EMRYS worktree.

## Consumers

- Historical Step `02` consumes the STAR BAM through its explicit
  `--input-alignment`/`INPUT_ALIGNMENT` path.
- The artifact inventory registers the BAM, three logs, splice-junction table,
  and validation report through the `step01_star_bam_v1`,
  `step01_star_log_final_v1`, `step01_star_log_v1`,
  `step01_star_log_progress_v1`, `step01_star_sj_v1`, and
  `step01_validation_report_v1` adapters.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rerunning alignment.

## Protection, evidence ceiling, and retained question

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). Run materialization binds the
manifest-selected sample and mates to
the explicit arguments; this owner does not reopen the manifest. STAR already
emits the canonical sort/read-group form, so whether canonical-BAM
construction should remain a distinct validation, indexing, publication, and
recovery stage is unresolved.
