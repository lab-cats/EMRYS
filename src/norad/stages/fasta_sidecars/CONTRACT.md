# `construct_FASTA_sidecars` stage contract

This document records the observed current contract of historical Step `00c`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is the lowercase physical source owner for that semantic identity. Its Python
implementation is an installed owner package; its only public Python surface is
the grouped validator route. The shell producer and scheduler remain explicit
repository-path interfaces and are not installed commands.

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

[`step_00c_prepare_gatk_reference.sh`](step_00c_prepare_gatk_reference.sh)
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

[`step_00c_prepare_gatk_reference.slurm`](step_00c_prepare_gatk_reference.slurm)
delegates to the shell entrypoint, maps `EXECUTE=0` to dry-run and `EXECUTE=1`
to `--execute`, rejects other values, resolves the current cluster tools, and
checks the two outputs after execution. Its empty-array invocation on Bash 3.2
can fail in the default dry-run path. That characterized wrapper defect is
preserved for later correction rather than normalized in this inventory.

## Validation interface

`python -I -m norad validate fasta-sidecars`, implemented by the private
[`validator.py`](validator.py) module, accepts explicit scope, FASTA, `FAI`,
`DICT`, and output paths. Validation is dry-run by default; `--execute`
publishes `<scope-id>.validation.tsv` using the common seven-field
step-validation contract.

The report contains exactly these five check identities:

- `fasta_structure`;
- `fai_structure`;
- `dict_structure`;
- `fai_contig_agreement`; and
- `dict_contig_agreement`.

A parser-recognized malformed sidecar or content mismatch is represented by
role-local `status=fail` rows and does not repair the reference or sidecars.
Input rejected by snapshot validation, an invalid CLI/output contract, or an
unsafe publication state exits with code `2` without publishing a new report.
Parser I/O, encoding, and tabular-data exceptions are translated at the parser
boundary, exit with code `2`, and publish nothing. Unexpected publication I/O
errors retain their separate hard-error boundary rather than being normalized
after report output or possible filesystem mutation.

The validator imports FASTA, `FAI`, and `DICT` parsers from the neutral
[`references/contigs.py`](../../libraries/references/contigs.py) owner and report
rendering, locking, and publication from the neutral
[`validation/report.py`](../../libraries/validation/report.py) owner. Both
lookups resolve through the installed `norad` package independently of caller
CWD. The grouped command rejects a different installed checkout when invoked
from a NORAD worktree, and isolated invocation excludes ambient `PYTHONPATH`.
Reference provenance and the final Step `05` validator share the same parser
module identity while this stage retains its per-role aggregation and
agreement rows.

The producer sources only `resolve_executable_value` from neutral
[`executable_resolution.sh`](../../libraries/executable_resolution.sh).
Samtools, GATK, and Java precedence, version checks, and commands remain owned
here.

## Consumers

- The final [`split_N_cigar_reads_with_GATK`](../split_n_cigar/README.md)
  owner consumes the FASTA and both sidecars before GATK `SplitNCigarReads`
  through explicit input paths.
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

- [`test_step_00c_prepare_gatk_reference.sh`](../../../../tests/stages/fasta_sidecars/test_step_00c_prepare_gatk_reference.sh)
  protects help and argument handling, side-effect-free dry-run, execution,
  reuse, generation of one missing sidecar, mismatch failures, Java failures,
  foreign-lock preservation, and the characterized retained-FAI state after
  final DICT publication fails.
- [`test_validate_step_00c_reference_sidecars.py`](../../../../tests/stages/fasta_sidecars/test_validate_step_00c_reference_sidecars.py)
  protects the five checks, ordered mismatch evidence, fail-closed structure,
  deterministic publication, lock handling, arbitrary-CWD repeatability, and
  the grouped package route.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects the wrapper's delegation, execution control, tool resolution, and
  characterized Bash 3.2 dry-run behavior with local mocks.
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
  creating an operational edge that is not intrinsic to sidecar construction.
- The shell producer owns sidecar generation, validation, locking, reuse, and
  publication but does not publish an atomic two-output transaction.
- The private validator module remains inside this installed stage package but
  reuses reference parsers from the neutral `reference_contigs` owner and
  publication helpers from the neutral validation-report owner through shared
  bridges.
- The scheduler wrapper owns cluster-specific tool and Java resolution around
  the parameterized shell entrypoint.

The reference-parser extraction is complete through `LIB-02K`; this inventory
does not choose a transaction redesign or scheduler abstraction.

## Deferred decisions

- Final owner of reference materialization.
- Whether the two sidecars require one atomic publication receipt.
- Final ownership of scheduler templates beyond this colocated native asset.
- Any reference-provenance transaction redesign; its physical owner home is
  already fixed separately.
