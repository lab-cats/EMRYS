# `convert_GTF_to_BED12` stage contract

This document records the observed current contract of historical Step `00b`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is now the implemented native source owner for its producer, validator, and
scheduler entry point. Its Python implementation is an installed owner package;
its public Python surfaces are only the grouped routes documented below.

The adjacent [`README.md`](README.md) routes maintainers and operators to the
implemented assets, supported commands, diagnostics, and recovery boundary.

## Responsibility

Convert transcript exon models from one GTF annotation into deterministic
BED12 records suitable for RSeQC strandedness and orientation inference, then
allow the final BED12 to be checked against its source GTF without modifying
either input.

## Execution dependencies

The hard data prerequisite is one materialized GTF. Under the current default
paths, historical Step `00a` is an operational predecessor because its job
decompresses the GTF into `refs/novogene_ref/genome.gtf`. This stage does not
consume the STAR index produced by Step `00a`; that apparent stage-to-stage
dependency is caused only by the current mixed ownership of reference
materialization.

If the GTF is already materialized, BED12 conversion can run independently of
STAR-index construction and FASTA-sidecar construction. Its final BED12 must
exist before historical Step `03` runs RSeQC `infer_experiment.py`. It is not a
prerequisite for STAR alignment or the canonical-BAM stages.

Historical numeric order records the current workflow narrative. The data
dependencies above, not the numeric identifier, define required execution.

## Inputs

The converter accepts:

- one GTF annotation path;
- the selected GTF feature type, defaulting to `exon`;
- the transcript-name attribute, defaulting to `transcript_id`; and
- the gene-name attribute, defaulting to `gene_id`.

Relevant rows must have nine tab-delimited GTF fields, valid one-based closed
coordinates, a strand in `+`, `-`, or `.`, and the selected transcript
attribute. Malformed or incomplete rows are warned about and skipped. A
transcript with conflicting chromosome or strand observations is skipped as a
whole. Conversion fails when no valid transcript records remain.

The current scheduler entrypoint additionally requires a Python executable.
Its repository-relative Novogene paths are current bindings, not approved
future defaults.

## Outputs

The converter writes one BED12 row per valid transcript. It:

- converts GTF coordinates to zero-based, half-open BED coordinates;
- sorts exons within each transcript;
- derives block sizes and transcript-relative block starts;
- uses `<transcript_id>|<gene_id>` when a gene identifier is available;
- emits the BED score, thick-region, and RGB fields using the currently
  protected fixed values; and
- orders records by chromosome, start, end, and name.

The current scheduler job sends the converter output directly to the final
`genome.bed`, then requires at least one row and exactly 12 fields per row.
Deterministic ordering is owned by the converter.

## Current execution surfaces

`python -I -m norad convert gtf-to-bed12` is the public conversion route,
implemented by [`converter.py`](converter.py). It accepts explicit input/output
and GTF-selection arguments. It renders complete deterministic BED12 bytes in
memory and is dry-run by default. `--execute` acquires a create-exclusive lock,
writes and fsyncs one owner-token staging file, publishes to an absent final
path through an atomic hard link, retains that staged inode as the final's
ownership anchor while removing the lock, and removes the anchor only after no
fallible cleanup remains. Rollback deletes a final only when it is still the
same regular-file inode as that anchor. A cleanup failure or foreign replacement
fails closed with the remaining lock and/or staging residue. An existing
output, lock, or staging residue blocks the operation and is never overwritten
automatically. `--run-token` lets an orchestrator supply the safe identifier
used by the lock and staging paths; without it, the producer generates a
private random token. An unhandled interruption can leave both lock and staging
evidence; a subsequent invocation preserves and reports that ambiguous state.

[`step_00b_gtf_to_bed12.slurm`](step_00b_gtf_to_bed12.slurm)
is the scheduler entrypoint. It:

- executes implicitly and has no dry-run or explicit execute control;
- requires `SLURM_SUBMIT_DIR` and changes into that directory;
- resolves repository-owned helpers from that submitted checkout, including
  when SLURM executes a spool copy of the wrapper;
- permits environment overrides for the GTF, final BED, and Python executable;
- selects the exact producer run token from `NORAD_RUN_TOKEN`, then
  `SLURM_JOB_ID`, then the shell process ID as the direct-execution/test
  fallback, and rejects identifiers outside the producer's safe-token grammar;
- creates log and output directories before conversion;
- tolerates a failed diagnostic `module list` without loading a stage tool;
- invokes the transactional converter with the declared final `--bed`, exact
  `--run-token`, and `--execute`; and
- rejects an empty final or a row with a field count other than 12 before
  printing the completion message.

The converter's create-exclusive transaction and no-clobber boundary therefore
cover the final BED itself. A postcheck failure occurs after that publication:
the wrapper exits nonzero and preserves the final as inspection evidence. The
surrounding verified-task orchestration remains responsible for admitting
completion evidence only after the owner command and verifier succeed.

## Validation interface

`python -I -m norad validate bed12`, implemented by
[`validator.py`](validator.py), accepts explicit scope, BED12, source-GTF, and
output paths. Validation is dry-run by default; `--execute` publishes
`<scope-id>.validation.tsv` using the common seven-field step-validation
contract.

The report contains exactly these five check identities:

- `bed12_structure`;
- `coordinate_sorting`;
- `block_structure`;
- `unique_transcript_names`; and
- `gtf_transcript_agreement`.

A validation mismatch is represented by a `status=fail` row and does not
repair the BED12 or source GTF. Malformed input, an invalid CLI/output contract,
or unsafe publication state exits with code `2` without publishing a new
report.

The GTF-agreement check imports the converter's normalization function, so it
compares reconstructed BED12 rows against the producer's normalization rather
than an independent implementation. Its report retains the historical
`BED12 bytes equal` detail label for byte compatibility. The producer is its
same-owner sibling. Snapshot, rendering, validation, locking, and publication
functions come from the neutral shared
[`validation/`](../../libraries/validation/README.md) facade. Neither dependency
creates a cross-stage scientific implementation edge.

## Consumers

- Historical Step `03` consumes the final BED12 through its explicit
  `--bed12`/`BED12` input when running RSeQC strandedness inference.
- Reference-provenance configuration registers the BED12 as a deterministic
  derivative of the declared GTF.
- The artifact inventory registers the final BED12 through
  `step00b_bed12_v1` and its validation report through
  `step00b_validation_report_v1`.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rerunning conversion.

No downstream stage should depend on this stage's implementation module.

## Protected behavior and evidence

- [`test_gtf_to_bed12.py`](../../../../tests/stages/gtf_to_bed12/test_gtf_to_bed12.py)
  protects the public route, exact exon-to-block conversion, sorting, warnings,
  configurable attributes, invalid-transcript handling, failure with no valid
  records, side-effect-free dry-run, arbitrary-CWD execution, create-exclusive
  publication, ownership-checked rollback, cleanup-failure residue, foreign
  final preservation, and interruption-residue blocking.
- [`test_validate_step_00b_bed12.py`](../../../../tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py)
  protects dry-run, the five checks, mismatch evidence, structural failures,
  and preservation of foreign locks or invalid predecessors.
- [`test_step_00b_gtf_to_bed12.py`](../../../../tests/stages/gtf_to_bed12/test_step_00b_gtf_to_bed12.py)
  protects submit-checkout and spool-copy execution, exact producer arguments,
  run-token precedence and safe fallback, success, tolerated module-list
  failure, isolated preflight failures, converter failure, bad-field and empty
  final checks, and transactional no-clobber residue.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects the exact mixed-layout job roster, directives, mode, and generic
  scheduler boundaries.
- [`test_validation_check_rosters.py`](../../../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
  protects the exact validator inventory and check identities.
- [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py)
  characterizes the imported shared publication and recovery behavior.
- [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py)
  and [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protect the recorded public-CLI and coverage boundaries.

These are local fixture and mocked-wrapper contracts. They do not establish a
new cluster, production, scientific-review, or biological-evidence result.
Current evidence status remains owned by the canonical roadmap and handoff.

## Observed ownership boundaries

- Reference materialization currently belongs incidentally to Step `00a`,
  creating an operational edge that is not intrinsic to BED12 conversion.
- The validator reuses producer normalization code for its strongest agreement
  check.
- Cross-cutting validation publication lives in the neutral shared
  [`validation/`](../../libraries/validation/README.md) owner and is imported
  through its stable facade.

This inventory records the remaining reference-materialization and oracle
boundaries without choosing an unreviewed correction.

## Deferred decisions

- Final owner of reference materialization.
- Whether GTF-agreement validation requires a producer-independent oracle.
- Whether a later descriptor or schema contract is justified.
