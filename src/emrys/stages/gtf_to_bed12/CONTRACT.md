# `convert_GTF_to_BED12` stage contract

This directory owns historical Step `00b`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The grouped routes below are its public Python surfaces.

## Responsibility

Convert transcript exon models from one GTF annotation into deterministic
BED12 records suitable for RSeQC strandedness and orientation inference, then
allow the final BED12 to be checked against its source GTF without modifying
either input.

## Execution dependencies

The hard data prerequisite is one materialized GTF. Reference materialization
is outside this owner; this stage does not consume the STAR index produced by
historical Step `00a`.

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

## Outputs

The converter writes one BED12 row per valid transcript. It:

- converts GTF coordinates to zero-based, half-open BED coordinates;
- sorts exons within each transcript;
- derives block sizes and transcript-relative block starts;
- uses `<transcript_id>|<gene_id>` when a gene identifier is available;
- emits the BED score, thick-region, and RGB fields using the currently
  protected fixed values; and
- orders records by chromosome, start, end, and name.

Deterministic ordering is owned by the converter.

## Current execution surfaces

`emrys convert gtf-to-bed12` is the public conversion route,
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

## Validation interface

`emrys validate bed12`, implemented by
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
same-owner sibling; publication uses the shared
[`validation`](../../libraries/validation/README.md) facade.

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

## Protection, evidence ceiling, and retained gap

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). As stated under validation,
`gtf_transcript_agreement` reuses the producer's normalization and is not a
producer-independent oracle.
