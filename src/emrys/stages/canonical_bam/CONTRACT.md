# `construct_canonical_BAM` stage contract

This document records the observed current contract of historical Step `02`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is the lowercase physical owner for that frozen semantic identity. Its shell
producer remains a repository-path interface, while its private Python
validator is exposed only through the grouped package command. The
adjacent [owner README](README.md) routes supported commands, diagnostics, and
rollback; this contract remains the detailed behavior owner.

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

The validator imports neutral
[`validation/report.py`](../../libraries/validation/report.py) for report
rendering, snapshots, locking, and publication, and neutral
[`alignments/bam.py`](../../libraries/alignments/bam.py) for `run_tool` and
`parse_header`. The final Step `04` and Step `05` validators import
the same BAM helper rather than importing this owner. Normal package imports
provide one module identity; neither neutral module has a public CLI, and
stage-specific checks stay here.

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

No downstream stage depends on this stage's implementation module. The neutral
BAM helper removes the former Step `04`/`05` peer-stage import without changing
their functional ownership.

## Protected behavior and evidence

- [`test_step_02_sort_index_bam.sh`](../../../../tests/stages/canonical_bam/test_step_02_sort_index_bam.sh)
  protects the explicit CLI, side-effect-free producer dry-run, read-group and
  sort contract, locking, inconsistent-pair rejection, staged validation,
  cleanup, and legacy rollback after backup, publication, and final-validation
  faults. The no-clobber path additionally relies on the shared
  create-exclusive publication ownership helpers that require exact staging
  inode identity and exercises rollback when a reused input changes after its
  final BAM link is published.
- [`test_validate_step_02_canonical_bam.py`](../../../../tests/stages/canonical_bam/test_validate_step_02_canonical_bam.py)
  protects dry-run, the five checks, mismatch evidence, fail-closed missing
  input, publication, and foreign-lock preservation.
- [`test_validation_check_rosters.py`](../../../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
  protects the exact validator inventory and check identities.
- [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py)
  characterizes the imported shared validation-report publication behavior.
- [`test_bam_validation.py`](../../../../tests/libraries/test_bam_validation.py)
  protects helper behavior shared by the three consumers.
- [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py)
  and [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protect the recorded public-CLI and coverage boundaries.

These are local fixture contracts. They do not establish a
new real-runtime, cluster, production, scientific-review, or biological-
evidence result. Current evidence status remains owned by the canonical
roadmap and handoff.

## Observed ownership boundaries

- Step `01` now requests coordinate sorting and the canonical sample read
  group. This stage reuses those bytes through a hard link while retaining
  validation, indexing, and publication; noncanonical inputs still take the
  sort and/or read-group replacement paths.
- Sample identity arrives as a direct argument rather than a verified manifest
  row and is used in filenames and read-group metadata.
- The producer and validator disagree on zero-record, library, and platform
  requirements.
- Cross-cutting BAM parsing and validation-publication helpers live in neutral
  package modules.
This inventory records those boundaries without selecting future owners or
changing behavior.

## Deferred decisions

- Whether the target keeps a distinct canonicalization stage when STAR already
  emits a canonical BAM, beyond its remaining validation, indexing, and
  transaction ownership.
- How manifest identity supplies sample, library, and platform metadata.
- One authoritative producer/validator contract for empty BAMs and read-group
  fields.
- Receipt and recovery-marker requirements for the BAM/BAI transaction.
- Whether either private neutral helper later receives a reviewed package or
  public import identity.
