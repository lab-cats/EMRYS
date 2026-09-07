# `collect_RSeQC_paired_orientation_evidence` operation contract

This directory owns historical Step `03`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. It is an independently runnable scientific-evidence
operation, not a primary-data transformation or control-policy stage. The
private validator is grouped under `emrys validate`; the producer remains an
explicit repository-path command.

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

The historical direct execute route has no lock, staging path, receipt,
stable-input recheck, or rollback. Re-execution truncates an existing path
before RSeQC runs, and a tool failure or empty-success result can leave an
empty or partial final file.

## Orchestration-safe producer boundary

`--no-clobber` is the required local-profile mode. It hashes the BAM, admitted
BAI, and BED12; refuses an existing final; holds a per-sample owned lock;
captures RSeQC stdout into a run-token temporary file; requires nonempty
output; rechecks all three inputs; and publishes create-exclusively while
retaining a staging inode anchor through validation. Failure removes only a
still-owned final; ambiguous replacement preserves lock and residue. The
explicit resolved RSeQC executable path is printed; its observed version and
the resulting report hash belong in the workflow verified record. Execute
without this option retains historical direct redirection.

## Current execution surfaces

[`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh)
is the public producer entrypoint. It:

- validates explicit input paths and the selected executable;
- is dry-run by default and keeps dry-run free of output-directory and output-
  file creation;
- passes the BED12 with `-r` and BAM with `-i` to RSeQC;
- creates the output directory only in execute mode;
- without `--no-clobber`, writes RSeQC output directly to the final report
  path; and
- checks only that the final file is nonempty before previewing it.

The file has a shell shebang but is not executable in the current tree; public
tests and orchestration invoke it explicitly through Bash.

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
recorded scientific rationale. The unsafe legacy direct route remains exactly
as described above; immutable Run task records supply wider input, tool,
attempt, and output identity for the no-clobber route.
