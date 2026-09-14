# `construct_FASTA_sidecars` stage contract

This directory owns historical Step `00c`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. Its only public Python surface is the grouped validator;
the shell producer is an internal Run worker.

## Responsibility

The [README](README.md) explains sidecar construction and use. The producer
and validator check the FASTA/FAI/dictionary set without modifying the FASTA.

## Execution dependencies

The reference FASTA must already exist. This owner neither materializes it nor
consumes the Step `00a` STAR index.

Once the FASTA and GTF are materialized, FASTA-sidecar construction can run in
parallel with historical Step `00b` BED12 conversion. Both sidecars must exist
and agree with the FASTA before historical Step `05` runs GATK
`SplitNCigarReads`. They are not prerequisites for BED12 conversion or STAR
alignment.

## Inputs

The producer accepts:

- one explicit, nonempty regular reference FASTA;
- a `samtools` executable providing `faidx`;
- a GATK executable providing `CreateSequenceDictionary`;
- Java version 17 or newer for GATK; and
- explicit staging destinations and runner-owned scratch space.

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

## Scientific worker

[`step_00c_prepare_gatk_reference.sh`](step_00c_prepare_gatk_reference.sh) is an internal worker of the
[Run task runner](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The worker runs samtools `faidx` and GATK `CreateSequenceDictionary`, writing
`--reference-fai-output` and `--reference-dict-output` staging files. A FASTA
symlink in runner scratch accommodates samtools' output naming without writing
beside the input. It checks each sidecar's format and compares their contig
names and lengths before returning. The independent validator then checks
ordered agreement with the FASTA.

A Run may reuse a complete admitted sidecar pair without starting the worker.
A partial pre-existing pair remains an error. The retired standalone script
could create only a missing sidecar; that is not the Run execution contract.

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
`PYTHONPATH`. Shared process helpers require absolute
Python 3.11+ in `EMRYS_SHA256_PYTHON`, canonical `<JAVA_HOME>/bin/java`, and a
JVM/GATK-selector-scrubbed environment for both the GATK probe and work. This
stage still owns tool precedence and versions, exact arguments,
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
