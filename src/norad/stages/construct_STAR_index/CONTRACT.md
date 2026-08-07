# `construct_STAR_index` stage contract

This document records the observed current contract of historical Step `00a`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is now the implemented native source owner for its scheduler job and validator;
it is not a Python package and exposes no package import identity.

The adjacent [`README.md`](README.md) routes maintainers and operators to the
implemented assets and exact supported commands.

## Responsibility

Construct a STAR genome index from one reference FASTA and its matching GTF
annotation, then allow that index to be checked without modifying the native
reference or STAR outputs.

The current job also decompresses the delivered FASTA and GTF into a shared
working-reference directory. Whether reference materialization belongs inside
this stage or a separate reference-preparation owner is unresolved.

## Execution dependencies

The hard data prerequisites are the delivered compressed FASTA and GTF. This
stage does not consume BED12, FASTA sidecars, reads, or outputs from another
computational stage.

Under the current default paths, this job also materializes the uncompressed
FASTA and GTF subsequently consumed by historical Steps `00b` and `00c`.
Those two stages may run in parallel after materialization. STAR alignment may
run after the STAR index is complete and receives the index through its
explicit input.

If reference materialization becomes a separate owner, STAR-index, BED12, and
FASTA-sidecar construction can branch from that shared prerequisite. Historical
numeric order records provenance; the data dependencies above define required
execution.

## Inputs

The functional inputs are:

- one gzip-compressed reference FASTA;
- one gzip-compressed reference GTF;
- the STAR executable and runtime environment;
- a thread count; and
- the STAR splice-junction overhang value.

The current scheduler entrypoint binds these inputs to repository-relative,
Novogene-specific paths, STAR `2.7.11b`, the allocated CPU count with a default
of eight threads, and `sjdbOverhang=149`. Those bindings describe current
behavior; they are not approved future interface defaults.

## Outputs

The current producer materializes uncompressed `genome.fa` and `genome.gtf`
files and writes a STAR genome-index directory. The validator requires these
15 nonempty regular index members:

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

## Current execution surface

[`step_00a_build_novogene_star_index.slurm`](step_00a_build_novogene_star_index.slurm)
is the only current producer entrypoint. It:

- executes implicitly when invoked and has no dry-run or explicit execute
  control;
- depends on the caller's working directory and hardcoded relative paths;
- embeds decompression and STAR compute instead of delegating to a stage
  script;
- reuses existing nonempty uncompressed reference files;
- creates output directories before running STAR; and
- relies on strict shell exit propagation but performs no explicit final
  output validation or transactional publication.

These behaviors are preserved characterization, not endorsement of the target
interface.

## Validation interface

[`validate_step_00a_star_index.py`](validate_step_00a_star_index.py)
accepts explicit scope, index, FASTA, GTF, relative-parameter base, expected
overhang, and output paths. Validation is dry-run by default; `--execute`
publishes `<scope-id>.validation.tsv`.

The TSV contract is tab-delimited and uses the ordered fields `step_id`,
`scope_id`, `check_id`, `status`, `observed`, `expected`, and `detail`.

It contains exactly these five check identities:

- `index_members`;
- `fasta_identity`;
- `gtf_identity`;
- `contig_names_lengths`; and
- `sjdb_overhang`.

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

- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects the exact mixed-layout job roster, directives, mode, and generic
  scheduler boundaries.
- [`test_step_00a_build_novogene_star_index.py`](../../../../tests/stages/construct_STAR_index/test_step_00a_build_novogene_star_index.py)
  protects the embedded STAR command, module handling, caller-working-directory
  behavior, default threads, reference reuse, side effects, and exit propagation
  with local mocks.
- [`test_validate_step_00a_star_index.py`](../../../../tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py)
  protects dry-run, the five checks, mismatch reporting, repeat publication,
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

These are local fixture and mocked-wrapper contracts. They do not establish a
new cluster, production, scientific-review, or biological-evidence result.
Current evidence status remains owned by the canonical roadmap and handoff.

## Neutral publication dependency

General report rendering, validation, snapshot, locking, and publication live
in the neutral exact-file owner
[`validation_report.py`](../../libraries/validation_report.py). This validator
loads that file through its private caller-local bridge while its five checks
remain stage-local. No package marker, public import identity, compatibility
wrapper, or global `sys.path` mutation is part of that dependency.

## Deferred decisions

- Whether reference decompression is part of this stage.
- Final serialization and placement of machine-readable stage contracts.
- Whether a later descriptor, schema, or package contract is justified.
