# `align_RNA_reads_with_STAR` stage contract

This document records the observed current contract of historical Step `01`.
The exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is now the implemented native owner and an installed Python package for its
private validator. The shell producer and scheduler remain exact
repository-path surfaces. Supported commands and diagnostics are adjacent in
the [owner README](README.md).

## Responsibility

Align one explicitly paired RNA-seq sample to a declared STAR genome index and
produce a coordinate-sorted alignment plus STAR's run and splice-junction
evidence. Validation inspects the declared outputs without rerunning STAR or
changing native artifacts.

## Execution dependencies

The hard data prerequisites are one read-1 FASTQ, its read-2 FASTQ mate, and a
STAR genome-index directory. Both FASTQs must use the same compression mode;
gzip handling is selected from their `.gz` suffixes. Historical Step `00a` is
the current producer of the required index, but this stage consumes only the
explicit index path and does not depend on how that index was constructed.

Samples are independent and may align in parallel once their reads and index
are available. Historical Step `02` consumes the STAR alignment and must
complete before later canonical-BAM consumers run. STAR's final, general, and
progress logs and splice-junction table are evidence outputs rather than
execution prerequisites for Step `02`.

Historical numeric order records provenance. The explicit FASTQ/index inputs
and BAM handoff, not the numeric identifier, define required execution.

## Inputs

The producer accepts:

- a nonempty sample identifier used in output-name construction;
- one read-1 and one read-2 FASTQ or FASTQ.GZ file path;
- one STAR genome-index directory;
- one explicit output directory;
- a positive thread count; and
- an available STAR executable, plus `gunzip` when both FASTQ paths end in
  `.gz`.

The current producer checks path types and matching compression suffixes but
does not validate FASTQ content, index members, sample-identifier path safety,
or biological pairing. The current scheduler entrypoint supplies test-fixture
defaults and loads STAR `2.7.11b`; those are current bindings, not approved
future interface defaults.

## Outputs

With output prefix `<output-dir>/<sample-id>.`, the protected minimum output
set is:

```text
<sample-id>.Aligned.sortedByCoord.out.bam
<sample-id>.Log.final.out
<sample-id>.Log.out
<sample-id>.Log.progress.out
<sample-id>.SJ.out.tab
```

STAR may produce additional files. The BAM is requested directly as
coordinate-sorted output. Historical Step `02` nevertheless sorts the
alignment again while adding a read group, validating it, indexing it, and
publishing the canonical BAM/BAI pair; that stage is therefore not merely an
alias for this output.

The current producer writes STAR artifacts directly into the final directory.
It does not declare a receipt, lock, no-clobber rule, staged transaction, or
post-execution output validation.

## Current execution surfaces

[`step_01_star_align.sh`](step_01_star_align.sh) is the
public producer entrypoint. It:

- validates explicit arguments and executable availability;
- is dry-run by default and requires `--execute` to invoke STAR;
- creates the output directory even in dry-run mode;
- rejects mixed compressed and uncompressed mate paths;
- adds `--readFilesCommand gunzip -c` when both inputs end in `.gz`;
- asks STAR for a coordinate-sorted BAM; and
- returns STAR's exit status but does not validate or transactionally publish
  the declared outputs after STAR exits.

The output-directory creation is a protected current dry-run side effect, not
an endorsement of the target dry-run contract.

[`step_01_star_align.slurm`](step_01_star_align.slurm) is the
scheduler entrypoint. It delegates to the shell producer, maps `EXECUTE=0` to
dry-run and `EXECUTE=1` to `--execute`, rejects other values, loads the STAR
module, and derives threads from the allocation. Its default dry-run mode
creates placeholder FASTQ files and an index directory before delegation and
refuses execution with those placeholder bindings. It relies on the caller's
working directory for repository-relative paths and performs no independent
output validation after delegation.

## Validation interface

`python -I -m norad validate star-alignment`, implemented by private
[`validator.py`](validator.py), accepts an explicit scope, BAM, three STAR log
paths, splice-junction table, and output path. Validation is dry-run by
default; `--execute` publishes `<scope-id>.validation.tsv` using the common
seven-field step-validation contract.

The report contains exactly these five check identities:

- `output_files`;
- `bam_structure`;
- `final_log_structure`;
- `mapping_summary`; and
- `splice_junction_structure`.

The checks require five nonempty regular outputs, BAM or BGZF magic bytes,
unique nonempty key/value rows in `Log.final.out`, three required mapping
percentages in the range zero through 100, and zero or more structurally valid
nine-column splice-junction rows. These are container and report-structure
checks; they do not establish alignment correctness or scientific validity.

A content mismatch is represented by a `status=fail` row and does not repair
the STAR outputs. Missing, unreadable, or unsafe input, an invalid CLI/output
contract, or unsafe publication state exits with code `2` without publishing a
new report.

The validator imports general report rendering, snapshot, validation,
locking, and publication functions from the neutral
[`validation/report.py`](../../libraries/validation/report.py) owner through the
installed `norad` package. The grouped command resolves independently of caller
CWD, rejects a different installed checkout when invoked from a NORAD worktree,
and excludes ambient `PYTHONPATH` under isolated invocation.

## Consumers

- Historical Step `02` consumes the STAR BAM through its explicit
  `--input-alignment`/`INPUT_ALIGNMENT` path.
- The artifact inventory registers the BAM, three logs, splice-junction table,
  and validation report through the `step01_star_bam_v1`,
  `step01_star_log_final_v1`, `step01_star_log_v1`,
  `step01_star_log_progress_v1`, `step01_star_sj_v1`, and
  `step01_validation_report_v1` adapters.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rerunning alignment.

No downstream stage should depend on this stage's implementation module.

## Protected behavior and evidence

- [`test_step_01_star_align.sh`](../../../../tests/stages/star_alignment/test_step_01_star_align.sh)
  protects the public CLI, command construction, current dry-run directory
  side effect, execute invocation, compression handling, thread validation,
  missing-input failures, and exact child-exit/output-directory residue with
  local tool mocks.
- [`test_validate_step_01_star_alignment.py`](../../../../tests/stages/star_alignment/test_validate_step_01_star_alignment.py)
  protects dry-run, the five checks, failed mapping and splice-junction
  evidence, fail-closed missing inputs, publication, and foreign-lock
  preservation, including deterministic execute/repeat behavior from a
  non-repository CWD.
- [`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py)
  protects wrapper delegation, execution control, module behavior, current
  default-fixture mutation, and exit propagation with local mocks.
- [`test_validation_check_rosters.py`](../../../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
  protects the exact validator inventory and check identities.
- [`test_validation_report.py`](../../../../tests/libraries/test_validation_report.py)
  characterizes the imported shared publication and recovery behavior.
- [`test_public_cli_contracts.py`](../../../../tests/test_public_cli_contracts.py)
  and [`test_python_coverage_baseline.py`](../../../../tests/test_python_coverage_baseline.py)
  protect the recorded public-CLI and coverage boundaries.

These are local fixture and mocked-wrapper contracts. They do not establish a
new real-runtime, cluster, production, scientific-review, or biological-
evidence result. Current evidence status remains owned by the canonical
roadmap and handoff.

## Observed ownership boundaries

- Sample and mate identity arrive as direct arguments; the producer does not
  consume or verify the manifest that canonically owns sample metadata.
- STAR writes final-path artifacts directly, while the separate validator owns
  the only explicit structural output checks.
- Coordinate sorting occurs in STAR and again inside the canonical-BAM stage,
  where the second operation is coupled to read-group tagging and publication.
- Cross-cutting validation-publication code is owned by the neutral shared
  library under `src/norad/libraries/`.
- The scheduler wrapper owns cluster module loading and mutable local fixture
  setup around the parameterized producer.

This inventory records those current boundaries without changing behavior.

## Deferred decisions

- How the future run request and manifest bind sample/mate identity to this
  stage without filename inference.
- Whether STAR output publication requires an atomic receipt or staging layer.
- Whether canonical-BAM construction can avoid redundant sorting while
  retaining read-group, validation, and recovery guarantees.
- Whether a later scheduler package changes caller-CWD dependence, mutable
  placeholder setup, module policy, or delegate-only output validation.
