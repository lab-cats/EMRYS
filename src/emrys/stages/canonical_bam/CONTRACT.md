# `construct_canonical_BAM` stage contract

This directory owns historical Step `02`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The private validator is grouped under `emrys validate`;
the producer remains an explicit repository-path command.

## Responsibility

Transform one explicit SAM or BAM alignment into the canonical per-sample,
coordinate-sorted, read-group-tagged BAM/BAI pair, validating the replacement
before publication and preserving a complete prior pair when publication can
be rolled back.

The separate validator observes a declared canonical pair and records its
container, sort-order, read-group, and alignment-tag contract without changing
the BAM or BAI.

## Execution dependencies

The hard data prerequisite is one samtools-readable alignment. Historical Step
`01` is the current default producer, but this stage accepts an explicit SAM or
BAM and does not consume STAR logs or require a STAR-specific filename.

After the canonical pair is published, historical Step `02b` BAM QC, Step `03`
strandedness/orientation inference, and Step `04` duplicate marking can consume
it independently. Step `03` also requires the BED12 produced by historical
Step `00b`. The current Step `04` implementation does not consume Step `02b`
or Step `03` outputs, so those three direct consumers are data-parallel once
their own additional prerequisites are satisfied.

Historical numeric order records provenance. The explicit alignment input and
canonical BAM/BAI handoff, not the numeric identifier, define required
execution.

## Inputs

The producer accepts:

- a nonempty sample identifier used for output names and read-group fields;
- one explicit input SAM or BAM file;
- one explicit output directory;
- a positive thread count; and
- an available samtools executable.

The current producer checks that the input path is a file but relies on
samtools to establish its content contract. The orchestration-safe
`--no-clobber` route validates sample-identifier path safety and binds input
stability; the legacy replaceable route does neither.

## Outputs

For `<sample-id>`, the canonical pair is:

```text
<output-dir>/<sample-id>.sorted.bam
<output-dir>/<sample-id>.sorted.bam.bai
```

The producer requires a nonempty BAM that passes `samtools quickcheck`, has
exactly one `@RG` header with `ID`, `SM`, and `LB` equal to the sample
identifier and `PL:ILLUMINA`, declares coordinate sort order, contains at least
one alignment, and tags every alignment with that read-group identifier. The
BAI must be nonempty.

The two files are published through backup and rollback attempts, but no
receipt or summary marks transaction completion.

## Orchestration-safe producer boundary

`--no-clobber` is the required local-profile mode. It refuses either existing
final before tool work and immediately before publication, pins the explicit
samtools path, hashes and rechecks the input alignment, and uses the existing
per-sample lock and staged pair validation. Because replacement is forbidden,
this path never creates or consumes backups and a failed attempt cannot damage
a predecessor. It publishes create-exclusively with staging inode anchors and
proves that both final paths still resolve to the already validated staging
inodes. When the canonical input itself supplied the staging inode, the
producer additionally hashes the published BAM after both links exist and
requires it to match the admitted input digest. The inode proof plus this
post-publication content binding carries the staged semantic validation across
publication without another `quickcheck`, header read, or two whole-BAM count
scans at the final pathname. The historical replaceable execute route retains
final-path semantic revalidation and its characterized restoration defect.

## Current execution surfaces

[`step_02_sort_index_bam.sh`](step_02_sort_index_bam.sh) is
the public producer entrypoint. It:

- is dry-run by default and keeps its own dry-run side-effect-free;
- inspects input sort order, skips a redundant sort when the admitted header
  already declares `SO:coordinate`, otherwise sorts with samtools;
- reuses a coordinate-sorted input inode when its single read group and every
  record tag already satisfy the canonical contract, otherwise replaces all
  read groups with one declared sample group;
- indexes the staged canonical BAM;
- validates the staged BAM/BAI before touching canonical paths;
- acquires an owned per-sample lock;
- requires an existing canonical state to contain both BAM and BAI or neither;
- on the orchestration-safe no-clobber path, create-exclusively publishes the
  pair, proves final/staging inode identity, and rechecks the admitted digest
  after publication when the input inode was reused, instead of semantically
  scanning the same bytes a second time;
- on the legacy replaceable path, backs up a prior pair, publishes the
  replacement files, and revalidates the final pair; and
- attempts to restore the prior pair, or remove a newly introduced partial
  pair, when a protected execution or publication step fails.

Existing complete outputs are intentionally replaceable after the replacement
passes validation. Temporary, backup, and lock paths carry the run token and
live with the canonical outputs.

Rollback restoration commands are best-effort and their failures are ignored;
cleanup can subsequently remove backup paths without publishing a recovery
marker. The characterized persistent-restore-failure oracle fails final BAI
publication and then prior-BAM restoration. It returns nonzero with both
diagnostics but leaves only the prior BAI at its canonical path: the canonical
BAM, both backups, owned lock, and run-token scratch are absent. This lockless
partial pair and lost prior BAM are an unresolved ambiguous/data-loss defect,
not failure-atomicity, successful rollback, or authority to clean or retry.

## Validation interface

The grouped route `emrys validate canonical-bam`, implemented by
private [`validator.py`](validator.py), accepts an explicit scope, BAM, BAI,
samtools executable, and output path. Validation is dry-run by default;
`--execute` publishes
`<scope-id>.validation.tsv` using the common seven-field step-validation
contract.

The report contains exactly these five check identities:

- `bam_bai_structure`;
- `samtools_quickcheck`;
- `coordinate_sorting`;
- `read_group_header`; and
- `alignment_rg_tags`.

The checks require BAM/BGZF and BAI/CSI magic bytes, a successful samtools
quickcheck, one coordinate-sorted `@HD`, one `@RG` whose `ID` and `SM` match
the scope, and equal total and matching-RG alignment counts. These checks do
not establish biological correctness.

The validator is less strict than the producer: it permits a zero-record BAM
when both counts are zero, does not require the producer's `LB` or
`PL:ILLUMINA` fields, and labels empty quickcheck diagnostics as expected while
testing only the command's exit status. Neither surface proves that the
declared BAI/CSI belongs to the declared BAM. These asymmetries are preserved
for later contract resolution, not normalized here.

A content mismatch is represented by a `status=fail` row and does not repair
the canonical pair. Missing, unreadable, or unsafe input, a failed tool call
needed to construct evidence, an invalid CLI/output contract, or unsafe
publication state exits with code `2` without publishing a new report.

The validator uses the shared validation publisher and BAM tool/header helper;
Step `04` and Step `05` share the latter rather than importing this stage.

## Consumers

- Historical Step `02b` consumes the canonical BAM and discovers either
  supported adjacent BAI naming convention for BAM QC.
- Historical Step `03` consumes the BAM/BAI together with an explicit BED12
  annotation for RSeQC inference.
- Historical Step `04` consumes the exact `<bam>.bai` pair for duplicate
  marking.
- Read-only validation and the three direct consumer branches do not acquire
  the producer lock or pin one immutable input snapshot; same-sample
  replacement must therefore not overlap them under current orchestration.
- The artifact inventory registers the canonical pair and validation report
  through `step02_canonical_bam_v1`, `step02_canonical_bai_v1`, and
  `step02_validation_report_v1`.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rebuilding the pair.

## Protection, evidence ceiling, and retained decisions

Repository tests protect this contract, including the exact legacy restore
failure, under the shared [evidence ceiling](../../../../tests/README.md).

Two decisions remain open: whether this stays a distinct stage now that STAR
normally emits canonical bytes, and whether one contract should replace the
current producer/validator disagreement over empty BAMs and `LB`/`PL` fields.
Run materialization supplies the sample argument, but library and platform
remain derived here rather than admitted as manifest metadata.
