# `construct_FASTA_sidecars` stage contract

This directory owns historical Step `00c`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. Its only public Python surface is the grouped validator;
the producer remains an explicit repository-path command.

## Responsibility

Construct the FASTA index (`FAI`) and GATK sequence dictionary (`DICT`) for one
materialized reference FASTA, then allow the FASTA and both sidecars to be
checked for structural and contig agreement without modifying the reference.

## Execution dependencies

The hard data prerequisite is one materialized reference FASTA. Reference
materialization is outside this owner; this stage does not consume the STAR
index produced by historical Step `00a`.

Once the FASTA and GTF are materialized, FASTA-sidecar construction can run in
parallel with historical Step `00b` BED12 conversion. Both sidecars must exist
and agree with the FASTA before historical Step `05` runs GATK
`SplitNCigarReads`. They are not prerequisites for BED12 conversion or STAR
alignment.

STAR-index, BED12, and FASTA-sidecar construction can branch from their shared
materialized references. Historical numeric order records provenance; data
dependencies define execution.

## Inputs

The producer accepts:

- one explicit, nonempty regular reference FASTA;
- a `samtools` executable providing `faidx`;
- a GATK executable providing `CreateSequenceDictionary`;
- Java version 17 or newer for GATK; and
- an optional temporary-directory root and run token used for isolated staged
  files.

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
- validates the inherited run token before deriving paths, uses an owned lock
  directory and run-token temporary files, and rejects matching staging residue
  from every prior token in both dry-run and execute mode;
- reuses each existing valid sidecar and generates only a missing sidecar;
- runs `samtools faidx` and GATK `CreateSequenceDictionary` as needed; and
- hashes the reference FASTA before execute-mode tool work, rejects any byte
  change after generation or during publication, and cleans owned unpublished
  artifacts; and
- validates both sidecars and their FASTA agreement after publication.

When both sidecars are generated, the script create-exclusively hard-links the
staged `FAI` into place before doing the same for the staged `DICT`; a sidecar
that appears after the locked state check therefore blocks publication rather
than being overwritten. The staged links remain as ownership anchors through
final validation. A controlled failure removes a published final only while it
is still the same regular-file inode as its invocation-owned anchor. A missing
anchor, disappeared final, foreign replacement, or rollback-removal failure
preserves the final path, lock, and staging residue as blocking recovery
evidence. Existing and late foreign sidecars are never rollback targets.
Unhandled process death can likewise leave residue for the orchestrator to
classify as blocked; the producer never breaks or silently adopts it.
Failure to remove any owned staging path or the owned lock is also a failed
cleanup, not a clean retry boundary: the producer exits nonzero when necessary
and retains the lock plus remaining residue for operator inspection.

## Validation interface

`emrys validate fasta-sidecars`, implemented by the private
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

The validator shares reference-contig parsers with reference provenance and
Step `05`, and uses the common validation publisher. Grouped invocation binds
the selected installed `emrys` package independently of caller CWD and ambient
`PYTHONPATH`. Shared process helpers require execute mode to use absolute
Python 3.11+ in `EMRYS_SHA256_PYTHON`, canonical `<JAVA_HOME>/bin/java`, and a
JVM/GATK-selector-scrubbed environment for both the GATK probe and work. This
stage still owns tool precedence and versions, exact arguments, transaction,
validation, and sidecar policy.

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

## Protection, evidence ceiling, and related retained defect

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). The separate
[reference-provenance owner](../../evidence/reference_provenance/README.md)
records its own unresolved restoration-evidence defect; this sidecar
transaction does not inherit that defect.
