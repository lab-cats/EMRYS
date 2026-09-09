# `collect_canonical_BAM_QC_evidence` operation contract

This directory owns historical Step `02b`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. It is a canonical-BAM evidence
operation, not a peer data-transformation stage. The private validator is
grouped under `emrys validate`; the shell producer is an internal Run worker.

## Responsibility

The [README](README.md) explains the QC operation and use. It records native
quickcheck/flagstat evidence without transforming the BAM or gating later
computation.

## Execution dependencies

The required input is one explicit BAM plus an adjacent index found as
either `<bam>.bai` or `<bam-with-.bam-removed>.bai`. Historical Step `02` is
the normal producer, but this operation accepts any explicit BAM satisfying
the shallow path contract and does not consume a Step `02` validation report.

The index is a nonempty-file admission requirement only: neither samtools
command receives it or checks its structure or correspondence to the BAM.

After a stable canonical pair exists, this operation may run in parallel with
the Step `02` validator, historical Step `03`, and historical Step `04`.
No computational stage consumes Step `02b` outputs. The Run binds the input
pair for this attempt; it does not make concurrent external mutation safe.

## Inputs

The producer accepts:

- a nonempty sample identifier used only for output-name construction;
- one explicit BAM and one discoverable adjacent BAI;
- one explicit staging output directory; and
- an available samtools executable.

The producer does not verify that the sample identifier matches BAM read-group
metadata or reopen the manifest. It requires a path-safe sample identifier;
the Run supplies the admitted sample identity.

## Outputs

For `<sample-id>`, the native evidence files are:

```text
<output-dir>/<sample-id>.quickcheck.txt
<output-dir>/<sample-id>.flagstat.txt
```

Successful `samtools quickcheck -v` output is captured with merged standard
output and error. When that stream is empty, the producer replaces it with the
exact marker:

```text
PASS: samtools quickcheck completed with no errors.
```

A nonempty stream from a zero-exit quickcheck is preserved verbatim. A
nonzero-exit quickcheck sends its diagnostic text to the retained runner log,
exits with code `1`, and does not run flagstat. On success, native samtools
flagstat text is written to the second staging path.

No receipt binds these files to the BAM, BAI, sample identity, samtools
version, or attempt.

## Scientific worker

[`step_02b_bam_qc.sh`](step_02b_bam_qc.sh) is an internal worker of the
[Run task runner](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The worker captures quickcheck and flagstat into the runner's staging
output directory and requires both reports to be nonempty. On quickcheck
failure it copies the native diagnostic stream to standard error so the
runner's retained log explains the failure. It does not run flagstat after
quickcheck fails. The native pair has no receipt; the Run verified task record
supplies input, tool, attempt, and output identity.

The retired direct-write route could replace one file while leaving an older
sibling, producing partial or mixed evidence. It is no longer an execution
option.

## Validation interface

The grouped route `emrys validate canonical-bam-qc`, implemented
by private [`validator.py`](validator.py), accepts an explicit scope,
quickcheck file, flagstat file, and output path. It does not receive the source
BAM, BAI, samtools identity, or an attempt receipt. Validation is dry-run by
default; `--execute` publishes
`<scope-id>.validation.tsv` using the common seven-field step-validation
contract.

The report contains exactly these five check identities:

- `quickcheck_structure`;
- `flagstat_structure`;
- `total_records`;
- `mapped_records`; and
- `count_consistency`.

The validator accepts only the exact synthetic quickcheck PASS marker. It
requires unique `in total` and `mapped` flagstat rows, sums their QC-passed and
QC-failed counts, permits nonnegative values including zero, and requires
mapped records not to exceed total records. Other well-formed flagstat rows and
reported percentages are not reconciled.

This creates a protected producer/validator mismatch: the producer preserves a
nonempty zero-exit quickcheck stream as success, while the validator treats
anything except the synthetic empty-success marker as failed evidence. The
artifact adapter follows the validator's exact-marker interpretation.

A content mismatch is represented by a `status=fail` row and does not repair
the evidence. Missing, unreadable, or unsafe input, an invalid CLI/output
contract, or unsafe report publication exits with code `2` without publishing
a new validation report. General report rendering, snapshots, locking, and
publication are privately imported from neutral
[`validation/report.py`](../../libraries/validation/report.py).

## Consumers

- The Step `02b` validator consumes the two native evidence files.
- The artifact inventory registers quickcheck, flagstat, and the validation
  report through `step02b_quickcheck_v1`, `step02b_flagstat_v1`, and
  `step02b_validation_report_v1`.
- Artifact indexing promotes quickcheck status, total-read count, and mapped-
  read count into the canonical summary and reports.

No current computational stage consumes any Step `02b` output or validation
row. Requiring this evidence for a complete Step `02b` artifact scope does not
make it a prerequisite for later computation.

## Protection, evidence ceiling, and retained mismatches

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md).

The index-correspondence gap and quickcheck mismatch remain as described
above. Immutable Run task records supply wider input, tool, attempt, and
output identity.
