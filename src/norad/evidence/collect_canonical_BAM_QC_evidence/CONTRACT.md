# `collect_canonical_BAM_QC_evidence` operation contract

This document records the observed current contract of historical Step `02b`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug; it is not yet a Python package or implemented source
location.

Historical Step `02b` is classified as an independently runnable evidence
operation associated with the canonical-BAM stage, not as a peer scientific
data-transformation stage. Only its contract is colocated here. The current
executable files remain in `jobs/` and `scripts/` until a separately approved
migration.

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
sample-identifier path safety. The scheduler entrypoint supplies historical
sample/path defaults and loads samtools `1.19.2`; those are current bindings,
not approved future interface defaults.

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

## Current execution surfaces

[`step_02b_bam_qc.sh`](../../../../scripts/step_02b_bam_qc.sh) is the public
producer entrypoint. It:

- creates the output directory before deciding between dry-run and execute;
- validates path presence and samtools availability;
- is dry-run by default and requires `--execute` to invoke samtools;
- writes each command's stream directly to its final output path;
- silently truncates or replaces an existing same-named file; and
- preserves quickcheck failure diagnostics as a final-path artifact.

There is no lock, staged pair, no-clobber rule, rollback, stable-input recheck,
receipt, or output-set validation. A quickcheck or flagstat failure can leave a
partial or cross-attempt evidence set, especially when an older sibling file
already exists. These are preserved current semantics, not a target
publication design.

[`step_02b_bam_qc.slurm`](../../../../jobs/step_02b_bam_qc.slurm) requires and
changes to `SLURM_SUBMIT_DIR`, creates log and output directories, loads the
samtools module, delegates to the shell producer, maps `EXECUTE=0` to dry-run
and `EXECUTE=1` to `--execute`, and rejects other values. After execution it
checks only that both paths exist. On Bash 3.2, expansion of its empty
execution-argument array can prevent the default dry-run from reaching the
producer.

## Validation interface

[`validate_step_02b_bam_qc.py`](../../../../scripts/validate_step_02b_bam_qc.py)
accepts an explicit scope, quickcheck file, flagstat file, and output path. It
does not receive the source BAM, BAI, samtools identity, or an attempt receipt.
Validation is dry-run by default; `--execute` publishes
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
publication are imported from the Step `00a` validator.

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

## Protected behavior and evidence

- [`test_step_02b_bam_qc.sh`](../../../../tests/shell/test_step_02b_bam_qc.sh)
  protects the public CLI, both index-name conventions, dry-run directory side
  effect, exact paths, silent and nonempty quickcheck success, native flagstat
  capture, and quickcheck-failure preservation.
- [`test_validate_step_02b_bam_qc.py`](../../../../tests/test_validate_step_02b_bam_qc.py)
  protects dry-run, the five checks, malformed/count mismatch evidence, fail-
  closed missing input, publication, and foreign-lock preservation.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects wrapper execution control, module/CWD/delegation behavior,
  directory creation, the Bash 3.2 defect, and child failure propagation.
- [`test_validation_check_rosters.py`](../../../../tests/test_validation_check_rosters.py),
  [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py),
  [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py),
  and [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protect the validator roster, shared publication, public surfaces, and
  coverage boundary.
- Artifact-adapter, run-summary, and report tests protect downstream Step `02b`
  evidence projection without rerunning samtools.

These are local fixture and mocked-wrapper contracts. They do not establish a
new real-runtime, cluster, production, scientific-review, or biological-
evidence result. Current evidence status remains owned by the canonical
roadmap and handoff.

## Observed ownership boundaries

- BAM/BAI completeness is checked even though the index is not consumed or
  validated by the evidence operation.
- Sample identity controls output paths but is not checked against the BAM.
- Execution and native serialization live in a numbered shell step; semantic
  interpretation lives in a separate validator and artifact adapter.
- Producer success, validator success, and artifact-adapter success are not
  one identical quickcheck contract.
- Cross-cutting validation-publication code remains owned by the Step `00a`
  validator, while scheduler runtime bindings remain in the wrapper.

This inventory assigns the operation to the neutral evidence domain without
settling its final submodule shape or changing behavior.

## Deferred decisions

- Whether the unused BAI admission requirement remains part of the operation.
- One authoritative quickcheck-success serialization.
- Binding of native evidence to BAM/BAI identity, manifest sample, tool
  identity, and attempt.
- Transaction, collision, and failure-artifact policy for the evidence pair.
- Final separation of evidence execution, interpretation, and publication.
- Migration order, compatibility wrappers, and scheduler-asset ownership.
