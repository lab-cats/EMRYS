# `construct_canonical_BAM` stage contract

This document records the observed current contract of historical Step `02`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug and is now the implemented native source owner. It is not
a Python package. The adjacent [owner README](README.md) routes supported
commands, diagnostics, migration evidence, and rollback; this contract remains
the detailed behavior owner.

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
samtools to establish its content contract. It does not validate sample-
identifier path safety or recheck input stability before final publication.
The scheduler entrypoint supplies repository- and sample-specific defaults and
loads samtools `1.19.2`; those are current bindings, not approved future
interface defaults.

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

## Current execution surfaces

[`step_02_sort_index_bam.sh`](step_02_sort_index_bam.sh) is
the public producer entrypoint. It:

- is dry-run by default and keeps its own dry-run side-effect-free;
- sorts the input with samtools, replaces all read groups with one declared
  sample group, and indexes the staged BAM;
- validates the staged BAM/BAI before touching canonical paths;
- acquires an owned per-sample lock;
- requires an existing canonical state to contain both BAM and BAI or neither;
- backs up a prior pair, publishes the replacement files, and revalidates the
  final pair; and
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

[`step_02_sort_index_bam.slurm`](step_02_sort_index_bam.slurm)
delegates to the shell producer, maps `EXECUTE=0` to dry-run and `EXECUTE=1` to
`--execute`, rejects other values, and checks the pair after execution. The
wrapper creates its log and output directories even in dry-run mode. On Bash
3.2, expansion of its empty execution-argument array can prevent the default
dry-run from reaching the producer. It also relies on the caller's working
directory rather than resolving `SLURM_SUBMIT_DIR`. These behaviors are
preserved current contracts, not target behavior.

## Validation interface

[`validate_step_02_canonical_bam.py`](validate_step_02_canonical_bam.py)
accepts an explicit scope, BAM, BAI, samtools executable, and output path.
Validation is dry-run by default; `--execute` publishes
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

The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py) for report
rendering, snapshots, locking, and publication, and neutral
[`bam_validation.py`](../../libraries/bam_validation.py) for `run_tool` and
`parse_header`. The final Step `04` and Step `05` validators exact-load
the same BAM helper rather than importing this owner. Each BAM-helper loader verifies
the cached path, readiness, and callable API, preserves foreign cache state and
`sys.path`, removes only a loader-owned partial after execution failure, and
fails closed before report publication. Neither neutral file is a package or
public CLI; stage-specific checks stay here.

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

- [`test_step_02_sort_index_bam.sh`](../../../../tests/stages/construct_canonical_BAM/test_step_02_sort_index_bam.sh)
  protects the explicit CLI, side-effect-free producer dry-run, read-group and
  sort contract, locking, inconsistent-pair rejection, staged validation,
  cleanup, and rollback after backup, publication, and final-validation faults.
- [`test_validate_step_02_canonical_bam.py`](../../../../tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py)
  protects dry-run, the five checks, mismatch evidence, fail-closed missing
  input, publication, and foreign-lock preservation.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects delegation, execution control, module behavior, current dry-run
  directory creation, the Bash 3.2 defect, and exit propagation with mocks.
- [`test_validation_check_rosters.py`](../../../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
  protects the exact validator inventory and check identities.
- [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py)
  characterizes the imported shared validation-report publication behavior.
- [`test_bam_validation.py`](../../../../tests/libraries/test_bam_validation.py)
  protects exact helper behavior and the three-caller loader matrix.
- [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py)
  and [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protect the recorded public-CLI and coverage boundaries.

These are local fixture and mocked-wrapper contracts. They do not establish a
new real-runtime, cluster, production, scientific-review, or biological-
evidence result. Current evidence status remains owned by the canonical
roadmap and handoff.

## Observed ownership boundaries

- Step `01` already requests coordinate sorting, while this stage sorts again
  as part of a broader canonicalization, read-group, validation, and
  publication transaction.
- Sample identity arrives as a direct argument rather than a verified manifest
  row and is used in filenames and read-group metadata.
- The producer and validator disagree on zero-record, library, and platform
  requirements.
- Cross-cutting BAM parsing and validation-publication helpers live in neutral
  exact-loaded source owners without package identity.
- The scheduler wrapper owns cluster module loading and dry-run directory side
  effects around a side-effect-free producer.

This inventory records those boundaries without selecting future owners or
changing behavior.

## Deferred decisions

- Whether the target keeps a distinct canonicalization stage when STAR already
  emits coordinate-sorted BAM.
- How manifest identity supplies sample, library, and platform metadata.
- One authoritative producer/validator contract for empty BAMs and read-group
  fields.
- Receipt and recovery-marker requirements for the BAM/BAI transaction.
- Whether either private neutral helper later receives a reviewed package or
  public import identity.
