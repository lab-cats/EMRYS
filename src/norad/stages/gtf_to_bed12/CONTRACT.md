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
Its repository-relative Novogene paths are current bindings,
not approved future defaults.

## Outputs

The converter writes one BED12 row per valid transcript. It:

- converts GTF coordinates to zero-based, half-open BED coordinates;
- sorts exons within each transcript;
- derives block sizes and transcript-relative block starts;
- uses `<transcript_id>|<gene_id>` when a gene identifier is available;
- emits the BED score, thick-region, and RGB fields using the currently
  protected fixed values; and
- orders records by chromosome, start, end, and name.

The current scheduler job writes the converter output directly to the final
`genome.bed` and checks that every row has exactly 12 fields. Deterministic
ordering is owned by the converter.

## Current execution surfaces

`python -I -m norad convert gtf-to-bed12` is the public conversion route,
implemented by [`converter.py`](converter.py). It accepts explicit input/output
and GTF-selection arguments, creates the output parent directory, and writes
immediately. It has no dry-run or transactional publication mode and silently
replaces the declared output when that path already exists; replacement is a
characterized defect, not an approved target behavior.

[`step_00b_gtf_to_bed12.slurm`](step_00b_gtf_to_bed12.slurm)
is the scheduler entrypoint. It:

- executes implicitly and has no dry-run or explicit execute control;
- requires `SLURM_SUBMIT_DIR` and changes into that directory;
- permits environment overrides for the GTF, final BED, and Python executable;
- creates log and output directories before conversion;
- embeds conversion and a final field-count check; and
- publishes the final file without an all-or-none transaction, receipt, or
  no-clobber boundary.

These behaviors are preserved characterization, not endorsement of the target
interface.

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
  records, and characterized output replacement.
- [`test_validate_step_00b_bed12.py`](../../../../tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py)
  protects dry-run, the five checks, mismatch evidence, structural failures,
  and preservation of foreign locks or invalid predecessors.
- [`test_step_00b_gtf_to_bed12.py`](../../../../tests/stages/gtf_to_bed12/test_step_00b_gtf_to_bed12.py)
  protects success plus the isolated missing-submit-directory, missing-GTF,
  nonexecutable-Python, converter-failure, and bad-field scheduler states and
  their exact residue.
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

This inventory records the remaining reference-materialization, duplicated-
sorting, and oracle boundaries without choosing an unreviewed correction.

## Deferred decisions

- Final owner of reference materialization.
- Whether GTF-agreement validation requires a producer-independent oracle.
- Whether a later descriptor or schema contract is justified.
