# `collect_canonical_BAM_QC_evidence` operation contract

This directory owns historical Step `02b`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. It is an independently runnable canonical-BAM evidence
operation, not a peer data-transformation stage. The private validator is
grouped under `emrys validate`; the producer remains an explicit
repository-path command.

## Responsibility

Run samtools quickcheck and flagstat against one declared canonical BAM and
persist their native text evidence for validation, artifact indexing, summary,
and reporting consumers. The operation does not transform the BAM or gate a
later computational stage in the current executable graph.

## Execution dependencies

The hard data prerequisite is one explicit BAM plus an adjacent index found as
either `<bam>.bai` or `<bam-with-.bam-removed>.bai`. Historical Step `02` is
the normal producer, but this operation accepts any explicit BAM satisfying
the shallow path contract and does not consume a Step `02` validation report.

The index is an admission requirement only: neither current samtools command
receives it, and the operation does not validate its size, structure, or
correspondence to the BAM.

After a stable canonical pair exists, this operation may run in parallel with
the Step `02` validator, historical Step `03`, and historical Step `04`.
No computational stage consumes Step `02b` outputs. A same-sample Step `02`
replacement or another Step `02b` attempt must not overlap this operation
because current readers and writers share no lock or immutable snapshot.

Historical numeric order records provenance; the explicit BAM input defines
execution readiness.

## Inputs

The producer accepts:

- a nonempty sample identifier used only for output-name construction;
- one explicit BAM and one discoverable adjacent BAI;
- one explicit output directory; and
- an available samtools executable.

The producer does not verify that the sample identifier matches BAM read-group
metadata or bind the evidence to a manifest row. It also does not validate
sample-identifier path safety.

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
nonzero-exit quickcheck also preserves its diagnostic file, exits with code
`1`, and does not run flagstat. On quickcheck success, native samtools flagstat
text is written to the second final path.

No receipt binds these files to the BAM, BAI, sample identity, samtools
version, or attempt.

## Orchestration-safe producer boundary

`--no-clobber` is the required local-profile mode. It binds an explicit
samtools executable, hashes the BAM and admitted BAI, requires both finals to
be absent, holds a per-sample owned lock, captures both commands into
run-token temporary paths, requires both files to be nonempty, rechecks the
inputs, and publishes the pair create-exclusively while retaining staging
inode anchors through validation. Failure removes only still-owned finals;
ambiguous replacement preserves the lock and residue. The native pair is not a receipt; the
workflow verified record binds it to the run, attempt, and observed tool
version. Execute without this option retains the direct-write contract below.

## Current execution surfaces

[`step_02b_bam_qc.sh`](step_02b_bam_qc.sh) is the public
producer entrypoint. It:

- creates no output directory in dry-run mode;
- validates path presence and samtools availability;
- is dry-run by default and requires `--execute` to invoke samtools;
- without `--no-clobber`, writes each command's stream directly to its final
  output path;
- silently truncates or replaces an existing same-named file; and
- preserves quickcheck failure diagnostics as a final-path artifact.

That historical route has no lock, staged pair, stable-input recheck, receipt,
or output-set validation. A quickcheck or flagstat failure can leave a partial
or cross-attempt evidence set, especially when an older sibling file already
exists.

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

The adjacent BAI remains an admission prerequisite although neither command
uses or validates it. Producer zero-exit quickcheck output is preserved, but
the validator and artifact adapter accept only the synthetic empty-success
marker. The unsafe legacy direct route remains exactly as described above;
immutable Run task records supply wider input, tool, attempt, and output
identity for the no-clobber route.
