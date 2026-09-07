# `align_RNA_reads_with_STAR` stage contract

This directory owns historical Step `01`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The private validator is installed; the producer remains
an explicit repository-path command.

## Responsibility

Align one explicitly paired RNA-seq sample to a declared STAR genome index and
produce a coordinate-sorted alignment plus STAR's run and splice-junction
evidence. Validation inspects the declared outputs without rerunning STAR or
changing native artifacts.

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

Historical numeric order records provenance. The explicit FASTQ/index inputs
and BAM handoff, not the numeric identifier, define required execution.

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

Every producer invocation uses the no-clobber transaction. `--no-clobber`
remains an accepted explicit spelling of that invariant, but omitting it does
not select a direct-final or overwrite path. The transaction is dry-run-visible
and side-effect-free until paired with `--execute`. Execute requires all five
declared outputs to be absent, holds an owned per-sample lock, directs STAR to
a run-token staging directory, requires every declared artifact to be nonempty,
and rechecks the admitted FASTQ hashes before create-exclusive publication. It
also admits every top-level STAR-index entry as one nonempty readable regular
file: symbolic links, subdirectories, special files, empty files, and names
containing tab/newline delimiters fail closed. The bytewise-name-ordered
basename/SHA-256 snapshot must have identical membership and bytes immediately
before STAR and again after STAR before publication. Each final is created as a
hard link without replacement while the corresponding staged inode remains as
an ownership anchor. The complete final set must still match those anchors
before success removes staging and then the owned lock. A failure before
publication removes only invocation-owned staging. During publication, rollback
removes a final only while it remains the same regular-file inode as its staged
anchor. A late or replaced foreign final is preserved with the lock and staging
residue for operator recovery. Existing or foreign state is never adopted or
deleted. `--star-bin` binds the STAR executable path. `--gunzip-bin` binds the
decompressor used by `--readFilesCommand` for paired `.gz` inputs; direct
callers that omit it retain the `gunzip`-on-`PATH` default, and uncompressed
mates do not resolve or validate it. Tool versions and final-output hashes
remain workflow verified-record responsibilities.

## Current execution surfaces

[`step_01_star_align.sh`](step_01_star_align.sh) is the
public producer entrypoint. It:

- validates explicit arguments and executable availability;
- is dry-run by default and requires `--execute` to invoke STAR;
- creates no output directory in dry-run mode;
- rejects mixed compressed and uncompressed mate paths;
- resolves the selected `--gunzip-bin` only when both mates end in `.gz` and
  passes that executable to `--readFilesCommand ... -c`;
- asks STAR for a coordinate-sorted BAM; and
- always uses the staged create-exclusive transaction above.

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
