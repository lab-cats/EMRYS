# `construct_FASTA_sidecars` stage contract

This document records the observed current contract of historical Step `00c`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug; it is not yet a Python package or implemented source
location.

Only this contract is colocated here. The current executable files remain in
`jobs/` and `scripts/` until a separately approved migration.

## Responsibility

Construct the FASTA index (`FAI`) and GATK sequence dictionary (`DICT`) for one
materialized reference FASTA, then allow the FASTA and both sidecars to be
checked for structural and contig agreement without modifying the reference.

## Execution dependencies

The hard data prerequisite is one materialized reference FASTA. Under the
current default paths, historical Step `00a` is an operational predecessor
only because its scheduler job decompresses the FASTA into
`refs/novogene_ref/genome.fa`. This stage does not consume the STAR index
produced by Step `00a`.

Once the FASTA and GTF are materialized, FASTA-sidecar construction can run in
parallel with historical Step `00b` BED12 conversion. Both sidecars must exist
and agree with the FASTA before historical Step `05` runs GATK
`SplitNCigarReads`. They are not prerequisites for BED12 conversion or STAR
alignment.

If reference materialization becomes a separate owner, STAR-index, BED12, and
FASTA-sidecar construction can branch from that shared prerequisite.
Historical numeric order records provenance; the data dependencies above
define required execution.

## Inputs

The producer accepts:

- one explicit, nonempty regular reference FASTA;
- a `samtools` executable providing `faidx`;
- a GATK executable providing `CreateSequenceDictionary`;
- Java version 17 or newer for GATK; and
- an optional temporary-directory root and run token used for isolated staged
  files.

The current scheduler entrypoint binds the FASTA, `samtools`, GATK, Java, and
temporary-directory inputs to CSU- and repository-specific defaults while
allowing environment overrides. Those bindings describe current behavior;
they are not approved future interface defaults.

## Outputs

For `<reference-fasta>`, the producer declares:

- `<reference-fasta>.fai`; and
- `<reference-stem>.dict` in the FASTA directory.

Each output must be a nonempty regular file. The `FAI` and `DICT` must contain
unique contig names and valid lengths that agree with the FASTA. The producer's
final check compares contig-name and length pairs independent of order; the
validator separately checks each sidecar's ordered contig sequence against the
FASTA.

The current producer publishes no receipt or transaction summary. Downstream
readiness is therefore established by explicit output and validation checks,
not by the mere existence of the target paths.

## Current execution surfaces

[`step_00c_prepare_gatk_reference.sh`](../../../../scripts/step_00c_prepare_gatk_reference.sh)
is the public producer entrypoint. It:

- validates its declared inputs and tools before generation;
- is dry-run by default and requires `--execute` to publish;
- uses an owned lock directory and run-token temporary files;
- reuses each existing valid sidecar and generates only a missing sidecar;
- runs `samtools faidx` and GATK `CreateSequenceDictionary` as needed; and
- validates both sidecars and their FASTA agreement after publication.

When both sidecars are generated, the script moves the staged `FAI` into place
before moving the staged `DICT`. If the second move fails, cleanup removes
temporary files and the lock but does not restore the first predecessor or
provide all-or-none publication. This is a characterized recovery defect, not
an approved target transaction contract.

[`step_00c_prepare_gatk_reference.slurm`](../../../../jobs/step_00c_prepare_gatk_reference.slurm)
delegates to the shell entrypoint, maps `EXECUTE=0` to dry-run and `EXECUTE=1`
to `--execute`, rejects other values, resolves the current cluster tools, and
checks the two outputs after execution. Its empty-array invocation on Bash 3.2
can fail in the default dry-run path. That characterized wrapper defect is
preserved for later correction rather than normalized in this inventory.

## Validation interface

[`validate_step_00c_reference_sidecars.py`](../../../../scripts/validate_step_00c_reference_sidecars.py)
accepts explicit scope, FASTA, `FAI`, `DICT`, and output paths. Validation is
dry-run by default; `--execute` publishes `<scope-id>.validation.tsv` using the
common seven-field step-validation contract.

The report contains exactly these five check identities:

- `fasta_structure`;
- `fai_structure`;
- `dict_structure`;
- `fai_contig_agreement`; and
- `dict_contig_agreement`.

A content mismatch is represented by a `status=fail` row and does not repair
the reference or sidecars. Malformed or unsafe input, an invalid CLI/output
contract, or unsafe publication state exits with code `2` without publishing
a new report.

The validator imports FASTA, `FAI`, and `DICT` parsers from
`reference_provenance.py` and shared report rendering, locking, and publication
functions from the Step `00a` validator. These dependencies record current
cross-stage ownership; they do not assign target ownership.

## Consumers

- Historical Step `05` consumes the FASTA and both sidecars before GATK
  `SplitNCigarReads` through explicit input paths.
- Reference-provenance configuration names the `FAI` and `DICT` for hashing
  and contig reconciliation.
- The artifact inventory registers the FASTA, `FAI`, `DICT`, and validation
  report through the `step00c_reference_fasta_v1`,
  `step00c_reference_fai_v1`, `step00c_reference_dict_v1`, and
  `step00c_validation_report_v1` adapters.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rerunning this stage.

No downstream stage should depend on this stage's implementation module.

## Protected behavior and evidence

- [`test_step_00c_prepare_gatk_reference.sh`](../../../../tests/shell/test_step_00c_prepare_gatk_reference.sh)
  protects help and argument handling, side-effect-free dry-run, execution,
  reuse, generation of one missing sidecar, mismatch failures, Java failures,
  and foreign-lock preservation.
- [`test_validate_step_00c_reference_sidecars.py`](../../../../tests/test_validate_step_00c_reference_sidecars.py)
  protects the five checks, ordered mismatch evidence, fail-closed structure,
  publication, and lock handling.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects the wrapper's delegation, execution control, tool resolution, and
  characterized Bash 3.2 dry-run behavior with local mocks.
- [`test_validation_check_rosters.py`](../../../../tests/test_validation_check_rosters.py)
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
  creating an operational edge that is not intrinsic to sidecar construction.
- The shell producer owns sidecar generation, validation, locking, reuse, and
  publication but does not publish an atomic two-output transaction.
- The validator reuses cross-cutting reference parsers and publication helpers
  owned by modules outside this stage.
- The scheduler wrapper owns cluster-specific tool and Java resolution around
  the parameterized shell entrypoint.

This inventory records those boundaries without choosing an extraction,
transaction redesign, or target owner.

## Deferred decisions

- Final owner of reference materialization.
- Whether the two sidecars require one atomic publication receipt.
- Final ownership of shared reference parsers and validation-publication code.
- Final ownership of scheduler templates and non-Python assets.
- Migration order, compatibility wrappers, and shared-code extraction.
