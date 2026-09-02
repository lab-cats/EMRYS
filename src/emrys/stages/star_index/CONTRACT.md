# `construct_STAR_index` stage contract

This directory owns historical Step `00a`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The grouped validator route is its only public Python
surface.

## Responsibility

Construct a STAR genome index from one reference FASTA and its matching GTF
annotation, then allow that index to be checked without modifying the native
reference or STAR outputs.

The producer consumes already materialized references. Reference materialization
is outside this owner.

## Execution dependencies

The producer's hard data prerequisites are one materialized FASTA and GTF. This
stage does not consume BED12, FASTA sidecars, reads, or outputs from another
computational stage. BED12 and FASTA-sidecar construction may run in parallel
from the same materialized references. STAR alignment may run after the STAR
index is complete and receives the index through its explicit input.

STAR-index, BED12, and FASTA-sidecar construction can branch from their shared
materialized references. Historical numeric order records provenance; data
dependencies define execution.

## Inputs

The functional inputs are:

- one materialized reference FASTA;
- one materialized reference GTF;
- the STAR executable and runtime environment;
- a thread count;
- the STAR splice-junction overhang value; and
- the STAR genome suffix-array index length (`genomeSAindexNbases`).

## Outputs

The producer writes one STAR genome-index directory. Both producer admission
and the validator require these 15 nonempty regular index members:

```text
genomeParameters.txt
Genome
SA
SAindex
chrLength.txt
chrName.txt
chrNameLength.txt
chrStart.txt
exonGeTrInfo.tab
exonInfo.tab
geneInfo.tab
sjdbInfo.txt
sjdbList.fromGTF.out.tab
sjdbList.out.tab
transcriptInfo.tab
```

STAR may produce additional files. This list is the currently protected
minimum, not a declaration that unrelated files are invalid.

## Current execution surfaces

[`step_00a_build_star_index.sh`](step_00a_build_star_index.sh) is the public
producer. It:

- accepts explicit materialized FASTA, GTF, index, thread, overhang, suffix-array length, and STAR
  executable inputs;
- is dry-run by default and requires `--execute` to mutate;
- writes the complete index into an owner-token sibling staging directory;
- holds a create-exclusive owner lock across generation and publication;
- requires all 15 declared members, publishes every staged regular member, and
  requires exact final/staged membership plus inode ownership before commit;
- reserves the absent final directory create-exclusively and refuses every
  existing or late-arriving final rather than replacing or merging it; and
- removes only pre-publication owned staging after controlled failure or a
  trapped signal. Once final publication starts, failure preserves the final,
  lock, and staging residue as a blocker rather than risking foreign bytes.

## Validation interface

`emrys validate star-index`, implemented by the private
[`validator.py`](validator.py) module, accepts explicit scope, index, FASTA,
GTF, relative-parameter base, expected overhang, expected suffix-array length,
and output paths. Validation
is dry-run by default; `--execute` publishes `<scope-id>.validation.tsv`.

The TSV contract is tab-delimited and uses the ordered fields `step_id`,
`scope_id`, `check_id`, `status`, `observed`, `expected`, and `detail`.

It contains exactly these six check identities:

- `index_members`;
- `fasta_identity`;
- `gtf_identity`;
- `contig_names_lengths`; and
- `sjdb_overhang`; and
- `genome_sa_index_nbases`.

The `genomeParameters.txt` parser ignores STAR metadata rows whose first field
is exactly `###`. Every non-metadata row retains missing-value and duplicate-key
admission, and the validator still checks the exact declared overhang and
suffix-array length.

A validation mismatch is represented by a `status=fail` row and does not
repair inputs or native outputs. Unsafe input structure, an invalid
CLI/output contract, or unsafe publication state exits with code `2` and does
not publish a new report. Successful execution publishes through an owned lock
and staged replacement with predecessor restoration where the characterized
implementation supports it.

## Consumers

- STAR alignment consumes the index directory through its explicit
  `--star-index`/`STAR_INDEX` input.
- Reference-provenance configuration names selected index members for hashing
  and contig reconciliation.
- The artifact inventory registers the 15 required members through the
  `step00a_star_index_v1` adapter and the report through
  `step00a_validation_report_v1`.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rerunning this stage.

## Protection and evidence ceiling

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md).
