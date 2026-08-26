# `mark_BAM_duplicates_with_Picard` stage contract

This is the observed contract of historical Step `04`, now implemented in this
native owner directory. The
exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is the capability-oriented physical owner for that identity and owns the
producer, validator, and scheduler assets.

## Responsibility and execution dependencies

Mark PCR/optical duplicates in one canonical BAM without removing reads,
produce its index and Picard metrics, and permit independent structural
validation.

The hard input is the explicit `<bam>.bai` canonical pair normally produced by
Step `02`. Step `04` does not consume Step `02b` or Step `03` evidence and may
run alongside them once the pair is stable. Step `05` consumes the marked
BAM/BAI, so successful Step `04` publication is its data prerequisite. Current
readers do not share a lock or a pinned snapshot; replacement must
not overlap downstream reads.

## Inputs and outputs

Inputs are a nonempty sample identifier, canonical BAM, exact `<bam>.bai`,
output and metrics directories, readable Picard jar, Java and samtools
executables, and an existing writable `TMPDIR`. The producer does not bind
sample identity to a manifest or validate path safety. The wrapper currently
loads Picard `3.1.1`, samtools `1.19.2`, and requires Java 17 or newer; these
are operational bindings, not future defaults.

Outputs are:

```text
<output-dir>/<sample-id>.markdup.bam
<output-dir>/<sample-id>.markdup.bam.bai
<metrics-dir>/<sample-id>.markdup.metrics.txt
```

Picard runs with `REMOVE_DUPLICATES=false`. Under `--no-clobber`, the producer
also requests `CREATE_INDEX=true` and accepts a regular, non-symlink, nonempty
index only at one of the two run-token staging paths proven absent before the
current Picard invocation. It normalizes Picard's alternate `<stem>.bai`
spelling to the stable `<bam>.bai` interface and falls back to `samtools index`
when neither staged path contains a nonempty index. Legacy replacement mode
never adopts a discovered sidecar and always runs `samtools index`, so a
predecessor BAI cannot be mistaken for current output. The producer requires
nonempty files and samtools quickcheck success for the BAM, but does not parse
metrics, verify duplicate flags, publish a receipt, or bind outputs to one
input/tool attempt.

## Orchestration-safe producer boundary

`--no-clobber` is the required local-profile mode. It hashes the input BAM/BAI
and Picard jar, refuses any existing final, holds a per-sample owned lock,
directs Picard and any samtools fallback to run-token BAM/BAI/metrics paths,
validates the complete triplet, rechecks the admitted hashes, and publishes
only the new set. Publication is create-exclusive and keeps staging inode
anchors through complete-set validation. Failure removes only still-owned new
finals; ambiguous replacement preserves lock and residue. Java and samtools
paths are explicit; observed tool versions and final hashes belong in the
workflow verified record. Execute without this option retains the historical
direct-final contract below.

## Current execution surfaces

[`step_04_mark_duplicates.sh`](step_04_mark_duplicates.sh)
is dry-run by default and creates no output directories in dry-run. Execute
without `--no-clobber` writes Picard BAM and metrics directly to final paths,
quickchecks the BAM, indexes it at the final path, then checks all three files
for nonemptiness. That historical route has no lock, staging, stable-input
recheck, rollback, or all-or-none transaction; failure may leave a partial or
cross-attempt set.

[`step_04_mark_duplicates.slurm`](step_04_mark_duplicates.slurm)
requires literal `SLURM_SUBMIT_DIR` and enters the submitted checkout before
resolving its repository-owned helper or producer, so SLURM's spool copy is
never checkout authority. It resolves modules, Picard, Java, and samtools before
delegation and checks the three outputs after execute. It creates `logs/` in
dry-run. Its empty execution-argument array has the characterized Bash 3.2
dry-run defect; an unset `JAVA_HOME` can abort at the later unguarded diagnostic,
and a stale nonempty output triplet can mask a zero-exit child that created
nothing.

## Validation interface

The grouped `python -I -m emrys validate duplicate-marking` route, implemented
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
helpers are privately imported from neutral
[`alignments/bam.py`](../../libraries/alignments/bam.py); neither helper has a
public package or CLI identity.

## Consumers and protected evidence

- The final [`split_N_cigar_reads_with_GATK`](../split_n_cigar/README.md)
  owner consumes the marked BAM/BAI.
- Artifact adapters register `step04_markdup_bam_v1`,
  `step04_markdup_bai_v1`, `step04_markdup_metrics_v1`, and
  `step04_validation_report_v1`; summary/report code consumes those artifacts
  without rerunning Picard.
- [`test_step_04_mark_duplicates.sh`](../../../../tests/stages/duplicate_marking/test_step_04_mark_duplicates.sh)
  protects CLI, side-effect-free dry-run, Picard/samtools command construction,
  both staged native-index spellings, missing/empty-index fallback, legacy
  predecessor safety, cleanup, output presence, missing inputs, and temporary-
  directory failure with mocks.
- [`test_validate_step_04_mark_duplicates.py`](../../../../tests/stages/duplicate_marking/test_validate_step_04_mark_duplicates.py),
  wrapper, roster, publication-fault, public-CLI, artifact, report, and coverage
  tests protect the recorded validation and projection boundaries.

This is local fixture/mock characterization, not new runtime, cluster,
scientific-review, or biological evidence.

## Ownership gaps and deferred decisions

- Producer validation, independent validation, and artifact interpretation are
  not one identical contract.
- Legacy direct execution lacks transactional ownership; the no-clobber route
  owns a staged three-file publication boundary.
- Sample/library/platform metadata is hardcoded or scope-derived rather than
  manifest-bound.
- The neutral BAM and report helpers remain private shared owners rather
  than installed or public package APIs.
- A native receipt, manifest-level sample binding, and wider verified-task
  tool/output identity remain deferred.
