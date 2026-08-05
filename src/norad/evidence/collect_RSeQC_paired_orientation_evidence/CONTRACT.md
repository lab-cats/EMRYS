# `collect_RSeQC_paired_orientation_evidence` operation contract

This document records the observed current contract of historical Step `03`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug and is now the implemented source location. It remains a
plain functional-owner directory, not a Python package or public import API.

Step `03` is classified as an independently runnable scientific-evidence
operation, not as a primary-data transformation or an implemented control-
policy stage. The producer, validator, scheduler asset, owner README, and
direct tests are colocated with this contract.

## Responsibility

Run RSeQC `infer_experiment.py` for one declared BAM and BED12 annotation and
record the fractions assigned to RSeQC's two paired-read orientation groups or
left undetermined. The operation produces mechanical read-orientation
evidence; it does not classify the sample, establish transcript strand or
biological sense/antisense, or select an approved forward/reverse policy.

## Execution dependencies

The hard data prerequisites are one BAM with an adjacent index and one BED12
annotation. Historical Step `02` is the normal BAM/BAI producer, and historical
Step `00b` is the normal BED12 producer. Neither branch depends on the other;
this operation becomes ready only when both explicit inputs exist.

After a stable BAM/BAI and BED12 are available, Step `03` may run in parallel
with historical Step `02b` and Step `04`. No current computational stage reads
the native RSeQC report or Step `03` validation report. In particular, the
sample manifest's `strandedness` field is an independent declared input; the
current code does not automatically derive or update it from this report.
Current readers do not acquire the Step `02` producer lock or pin one input
snapshot, so same-sample canonical-pair replacement must not overlap them.

Historical numeric order records provenance. The two converging data
prerequisites above define required execution.

## Inputs

The producer accepts:

- a nonempty sample identifier used for output-name construction;
- one explicit BAM;
- an adjacent index discovered as `<bam>.bai` or
  `<bam-with-.bam-removed>.bai`;
- one explicit BED12 annotation;
- one explicit output directory; and
- an executable `infer_experiment.py`, supplied as a path or command name.

The current operation validates path presence and tool executability but does not
validate BAM, index, or BED12 content before invoking RSeQC. It does not bind
the sample identifier to BAM metadata or a manifest row. By default it selects
`.venv/bin/infer_experiment.py` relative to the working directory when that
path exists, otherwise it resolves `infer_experiment.py` through `PATH`.

## Outputs

The producer writes one native report:

```text
<output-dir>/<sample-id>.infer_experiment.txt
```

RSeQC standard output is redirected directly to this final path. The producer
requires only that the result be nonempty; the separate validator owns the
three-fraction structural contract.

There is no lock, staging path, no-clobber rule, receipt, stable-input recheck,
or rollback. Re-execution truncates an existing path before RSeQC runs, and a
tool failure or empty-success result can leave an empty or partial final file.

## Current execution surfaces

[`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh)
is the public producer entrypoint. It:

- validates explicit input paths and the selected executable;
- is dry-run by default and keeps dry-run free of output-directory and output-
  file creation;
- passes the BED12 with `-r` and BAM with `-i` to RSeQC;
- creates the output directory only in execute mode;
- writes RSeQC output directly to the final report path; and
- checks only that the final file is nonempty before previewing it.

The file has a shell shebang but is not executable in the current tree; public
tests and the scheduler invoke it explicitly through Bash.

[`step_03_infer_strandedness_and_orientation.slurm`](step_03_infer_strandedness_and_orientation.slurm)
resolves repository-relative defaults from `SLURM_SUBMIT_DIR` with a current-
directory fallback, optionally activates the repository virtual environment,
selects the RSeQC executable, and delegates to the shell producer. It creates
the scheduler log directory in dry-run mode but leaves the scientific output
directory to the producer. On Bash 3.2, expansion of its empty execution-
argument array can prevent the default dry-run from reaching the producer.

## Validation interface

[`validate_step_03_rseqc_orientation.py`](validate_step_03_rseqc_orientation.py)
accepts an explicit scope, native report, sum tolerance, and output path. It
does not receive the BAM, index, BED12, RSeQC identity, or attempt receipt.
Validation is dry-run by default; `--execute` publishes
`<scope-id>.validation.tsv` using the common seven-field step-validation
contract.

The report contains exactly these five check identities:

- `report_structure`;
- `failed_fraction`;
- `paired_orientation_fraction_a`;
- `paired_orientation_fraction_b`; and
- `fraction_sum`.

The required native labels are:

```text
Fraction of reads failed to determine
Fraction of reads explained by "1++,1--,2+-,2-+"
Fraction of reads explained by "1+-,1-+,2++,2--"
```

Each label must occur once with a finite value between zero and one. Their sum
must equal one within the configurable finite tolerance, which defaults to
`0.001` and may range from zero through `0.1`. Unrecognized report lines are
ignored, including RSeQC's declaration that the input is paired-end data.

The group labels are retained exactly as mechanical paired-read orientations.
The validator does not translate them into biological strand claims or select
a manifest `strandedness` value.

A content mismatch is represented by a `status=fail` row and does not repair
the native report. Missing, unreadable, or unsafe input, an invalid tolerance
or CLI/output contract, or unsafe report publication exits with code `2`
without publishing a new validation report. General rendering, snapshots,
locking, and publication are privately exact-loaded from neutral
[`validation_report.py`](../../libraries/validation_report.py).

## Consumers

- The Step `03` validator consumes the native RSeQC report.
- The artifact inventory registers the native report and validation report
  through `step03_rseqc_infer_v1` and `step03_validation_report_v1`.
- Artifact indexing, canonical summaries, and reports project the mechanical
  fractions and evidence state without rerunning RSeQC.

No current computational stage consumes these outputs. Any future policy that
turns orientation fractions into library-strandedness metadata requires its
own scientifically approved contract and evidence gate.

## Protected behavior and evidence

- [`test_step_03_infer_strandedness_and_orientation.sh`](../../../../tests/evidence/collect_RSeQC_paired_orientation_evidence/test_step_03_infer_strandedness_and_orientation.sh)
  protects the public CLI, both executable-resolution paths, both BAI naming
  conventions, side-effect-free dry-run, exact RSeQC arguments, successful
  capture, missing-input failures, and empty-output rejection with local mocks.
- [`test_validate_step_03_rseqc_orientation.py`](../../../../tests/evidence/collect_RSeQC_paired_orientation_evidence/test_validate_step_03_rseqc_orientation.py)
  protects dry-run, the five checks, fraction/range/sum failures, fail-closed
  missing input, publication, and foreign-lock preservation.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects wrapper execution control, virtual-environment/tool selection,
  CWD/delegation behavior, the Bash 3.2 defect, and child failure propagation.
- [`test_validation_check_rosters.py`](../../../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py),
  [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py),
  [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py),
  and [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protect the validator roster, shared publication, public surfaces, and
  coverage boundary.
- Artifact-adapter, run-summary, and report tests protect downstream Step `03`
  evidence projection without interpreting biological strand.

These are local fixture and mocked-wrapper contracts. They do not establish a
new real-runtime, cluster, production, scientific-review, or biological-
evidence result. Current evidence status remains owned by the canonical
roadmap and handoff.

## Observed ownership boundaries

- The producer labels the operation as strandedness inference, while its
  machine-checked output remains mechanical paired-read orientation fractions.
- Producer comments say the result tells later steps whether a library is
  forward, reverse, or unstranded, but no implemented threshold or conversion
  performs that classification.
- BAM/BAI identity, BED12 identity, tool identity, sample identity, and attempt
  are not bound into the native report or its validation interface.
- Native report production and semantic validation are separate, and the
  producer checks only nonemptiness.
- The manifest owns declared strandedness but no approved conversion owner
  connects this evidence to that field.
- Cross-cutting validation-publication code remains owned by neutral
  `src/norad/libraries/validation_report.py`; scheduler environment selection
  remains in the wrapper.

This inventory preserves the neutral evidence boundary without selecting a
biological interpretation policy or changing behavior.

## Deferred decisions

- Scientifically approved mapping, if any, from RSeQC orientation groups to
  declared library strandedness.
- Whether the configurable `0.1` maximum sum tolerance is appropriate for the
  durable evidence contract.
- Binding of native evidence to BAM/BAI, BED12, sample, tool, and attempt
  identity.
- Transaction, collision, and failure-artifact policy for the native report.
- Whether this scientific-evidence operation remains separate from a future
  ingestion/manifest review workflow.
- Any future compatibility surface or scheduler abstraction; this migration
  added neither.
