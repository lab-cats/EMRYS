# `mark_BAM_duplicates_with_Picard` stage contract

This directory owns historical Step `04`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias.

## Responsibility and execution dependencies

See the [README](README.md) for purpose, inputs, outputs, and normal use.

The input is the explicit `<bam>.bai` canonical pair normally produced by
Step `02`. Step `04` does not consume Step `02b` or Step `03` evidence and may
run alongside them once the pair is stable. Step `05` consumes the marked
BAM/BAI, so successful Step `04` publication is its data prerequisite. Current
Run tasks bind their own input snapshots; external mutation must not overlap
downstream reads.

## Inputs and outputs

Inputs are a nonempty sample identifier, canonical BAM, exact `<bam>.bai`,
output and metrics directories, readable Picard jar, Java and samtools
executables, and runner scratch. The worker requires a path-safe sample ID;
the Run supplies its admitted manifest identity.

Outputs are:

```text
<output-dir>/<sample-id>.markdup.bam
<output-dir>/<sample-id>.markdup.bam.bai
<metrics-dir>/<sample-id>.markdup.metrics.txt
```

Picard runs with `REMOVE_DUPLICATES=false`. The producer requires nonempty
files and samtools quickcheck success for the BAM, but does not parse metrics,
verify duplicate flags, publish a receipt, or bind outputs to one input/tool
attempt.

## Scientific worker

[`step_04_mark_duplicates.sh`](step_04_mark_duplicates.sh) is an internal worker of the
[Run task runner](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The worker receives separate staging directories for BAM and metrics. It
runs Picard with `REMOVE_DUPLICATES=false` and runner scratch as `TMP_DIR`,
quickchecks the BAM, creates its index with samtools, and requires the complete
three-file set to be nonempty. Metrics interpretation stays with the validator.

The retired direct-write route could leave partial or mixed output after a
Picard or samtools failure. It is no longer an execution option.

## Validation interface

The grouped `emrys validate duplicate-marking` route, implemented
by private [`validator.py`](validator.py), accepts explicit BAM, BAI, metrics,
samtools, scope, and report paths. Dry-run prints the common seven-column TSV;
`--execute` snapshot-rechecks inputs and publishes it through neutral private
[`validation/report.py`](../../libraries/validation/report.py).

Exact checks are:

- `bam_bai_structure`;
- `samtools_quickcheck`;
- `coordinate_sorting`;
- `read_group_preservation`; and
- `duplication_metrics`.

The validator checks BAM/BAI magic, quickcheck exit, coordinate order, one
`@RG` whose `ID` and `SM` match scope, and exactly one row in Picard's
duplication-metrics table with nonempty library, nonnegative pair counts,
duplicates not exceeding examined pairs, and a finite `PERCENT_DUPLICATION` in
`0..1`. Later Picard tables such as the duplicate-set histogram are ignored. It
does not prove BAI/BAM
correspondence, duplicate flags, metrics/BAM correspondence, or the producer's
`LB`/platform contract. A nonzero quickcheck becomes failed evidence even when
diagnostics are nonempty.

Content mismatches publish `status=fail` rows; unsafe inputs, evidence-building
tool failures, and publication-contract failures exit `2`. BAM tool/header
operations use the shared BAM helper.

## Consumers, protection, and evidence ceiling

- The final [`split_N_cigar_reads_with_GATK`](../split_n_cigar/README.md)
  owner consumes the marked BAM/BAI.
- Artifact adapters register `step04_markdup_bam_v1`,
  `step04_markdup_bai_v1`, `step04_markdup_metrics_v1`, and
  `step04_validation_report_v1`; summary/report code consumes those artifacts
  without rerunning Picard.

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md).

Run materialization supplies the sample argument, but library and platform remain
scope-derived or hardcoded rather than separately admitted manifest metadata.
