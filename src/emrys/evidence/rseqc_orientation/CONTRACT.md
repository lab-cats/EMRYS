# `collect_RSeQC_paired_orientation_evidence` operation contract

This directory owns historical Step `03`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. It is an independently runnable scientific-evidence
operation, not a primary-data transformation or control-policy stage. The
private validator is grouped under `emrys validate`; the producer remains an
explicit repository-path command.

## Responsibility

The [README](README.md) explains RSeQC inputs and use. Fractions are mechanical
read-orientation evidence; they do not classify samples, establish biological
strand/sense, or select a forward/reverse policy.

## Execution dependencies

The required inputs are one BAM with an adjacent index and one BED12
annotation. Historical Step `02` is the normal BAM/BAI producer, and historical
Step `00b` is the normal BED12 producer. Neither branch depends on the other;
this operation becomes ready only when both explicit inputs exist.

After a stable BAM/BAI and BED12 are available, Step `03` may run in parallel
with historical Step `02b` and Step `04`. No current computational stage reads
the native RSeQC report or Step `03` validation report. In particular, the
sample manifest's `strandedness` field is an independent declared input; the
current code does not automatically derive or update it from this report.
The Run binds input snapshots for each task. This does not make concurrent
external mutation safe.

## Inputs

The producer accepts:

- a sample identifier matching `[A-Za-z0-9][A-Za-z0-9._-]*`;
- one explicit BAM;
- an adjacent index discovered as `<bam>.bai` or
  `<bam-with-.bam-removed>.bai`;
- one explicit BED12 annotation;
- one explicit staging output directory; and
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

RSeQC standard output is captured in staging and published only when nonempty;
the separate validator owns the three-fraction structural contract.

## Scientific worker

[`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh) is an internal worker of the
[Run task runner](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The worker passes BED12 as `-r` and BAM as `-i`, captures RSeQC standard
output in the staging directory, and requires a nonempty report. RSeQC's exit
status and standard-error diagnostics propagate. The separate validator owns
the three-fraction interpretation.

The retired direct route truncated existing reports before invoking RSeQC;
partial child failure could leave partial bytes, and empty success could erase
a prior report. The runner now owns the common publication boundary.

## Validation interface

The grouped route `emrys validate rseqc-orientation`, implemented
by private [`validator.py`](validator.py), accepts an explicit scope, native
report, sum tolerance, and output path. It does not receive the BAM, index,
BED12, RSeQC identity, or attempt receipt. Validation is dry-run by default;
`--execute` publishes
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
locking, and publication are privately imported from neutral
[`validation/report.py`](../../libraries/validation/report.py).

## Consumers

- The Step `03` validator consumes the native RSeQC report.
- The artifact inventory registers the native report and validation report
  through `step03_rseqc_infer_v1` and `step03_validation_report_v1`.
- Artifact indexing, canonical summaries, and reports project the mechanical
  fractions and evidence state without rerunning RSeQC.

No current computational stage consumes these outputs. Any future policy that
turns orientation fractions into library-strandedness metadata must be defined
by an external assay-design and interpretation process. EMRYS does not turn
that process into a computational gate.

## Protection, evidence ceiling, and retained questions

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md).

The producer's historical name claims strandedness inference, while its
machine-checked output remains only mechanical paired-read orientation. No
implemented conversion updates the manifest's independently declared
strandedness. The configurable `0.1` maximum sum tolerance also lacks a
recorded scientific rationale. Immutable Run task records supply wider input,
tool, attempt, and output identity.
