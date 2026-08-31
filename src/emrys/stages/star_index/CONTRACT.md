# `construct_STAR_index` stage contract

This document records the observed current contract of historical Step `00a`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is now the implemented native source owner for its producer and validator.
Its Python implementation is an installed owner package; its public Python
surface is only the grouped validator route documented below.

The adjacent [`README.md`](README.md) routes maintainers and operators to the
implemented assets and exact supported commands.

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

If reference materialization becomes a separate owner, STAR-index, BED12, and
FASTA-sidecar construction can branch from that shared prerequisite. Historical
numeric order records provenance; the data dependencies above define required
execution.

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

`python -I -m emrys validate star-index`, implemented by the private
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

No downstream stage should depend on this stage's implementation module.

## Protected behavior and evidence

- [`test_step_00a_build_star_index.py`](../../../../tests/stages/star_index/test_step_00a_build_star_index.py)
  protects public producer help, dry-run, arbitrary-CWD execution, exact STAR
  arguments, declared-member publication, no-clobber, controlled rollback,
  and late-final and foreign-lock preservation with local mocks.
- [`test_validate_step_00a_star_index.py`](../../../../tests/stages/star_index/test_validate_step_00a_star_index.py)
  protects dry-run, the six checks, STAR metadata admission, mismatch reporting,
  repeat publication,
  contract failures, and preservation of foreign locks or invalid
  predecessors.
- [`test_validation_check_rosters.py`](../../../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
  protects the exact validator inventory and check identities.
- [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py)
  characterizes shared publication, rollback, cleanup, and recovery behavior.
- [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py)
  protects the public validator CLI, and
  [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protects its recorded coverage boundary.

These are local fixture contracts. They do not establish a
new cluster, production, scientific-review, or biological-evidence result.
Current evidence status remains owned by the canonical roadmap and handoff.

## Neutral publication dependency

General report rendering, validation, snapshot, locking, and publication live
in the neutral shared owner
[`validation/report.py`](../../libraries/validation/report.py). This validator
imports the validation facade while its five checks remain stage-local. The
shared module has no public CLI.

## Deferred decisions

- Whether EMRYS later adds a separate reference-materialization route.
- Final serialization and placement of machine-readable stage contracts.
- Whether a later descriptor, schema, or package contract is justified.
