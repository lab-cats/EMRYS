# `split_N_cigar_reads_with_GATK` stage contract

This is the observed contract of historical Step `05`, now implemented in this
native owner directory. The exact public identity and historical alias are
owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
is the lowercase physical owner for that public slug and owns the producer,
validator, and scheduler assets. Its Python validator is installed only
through the grouped command; the shell producer and scheduler remain explicit
repository-path interfaces.

## Responsibility and execution dependencies

Run GATK `SplitNCigarReads` on one duplicate-marked RNA-seq BAM, validate and
index the result, and publish a rollback-protected BAM/BAI pair.

Two independent branches converge here: Step `04` normally supplies the marked
`<bam>.bai` pair, while Step `00c` supplies the explicit FASTA, `<fasta>.fai`,
and `<stem>.dict`. Step `05` neither creates nor repairs reference sidecars.
The final
[`partition_BAM_by_mechanical_read_orientation`](../mechanical_orientation/README.md)
owner consumes the published split BAM/BAI. Historical numbering is provenance;
these data edges define required order.

## Inputs and outputs

Inputs are sample ID, marked BAM and exact `<bam>.bai`, reference FASTA/FAI/
DICT, output directory, GATK, samtools, Java 17 or newer, and project-storage
temporary space. Tool values resolve through explicit arguments, approved
environment overrides, or PATH/JAVA_HOME. Sample identity is not manifest-
bound or path-safety checked.

Outputs are:

```text
<output-dir>/<sample-id>.split_ncigar.bam
<output-dir>/<sample-id>.split_ncigar.bam.bai
```

The producer requires quickcheck success, coordinate sort order, exactly one
matching `ID`/`SM` read group, at least one alignment, all alignments tagged
with that group, and a nonempty index. It does not publish a receipt or prove
that CIGAR-N transformation semantics occurred.

## Orchestration-safe producer boundary

`--no-clobber` is the required local-profile mode. It changes lock scope from
the output directory to the declared sample, refuses either existing final,
hashes and rechecks the input BAM/BAI plus reference FASTA/FAI/DICT, and uses
the existing staged validation and final-path revalidation. This path never
creates predecessor backups; it publishes create-exclusively with staging
inode anchors, so an interruption cannot enter the retained
restoration-failure defect. Tool paths are explicit; observed GATK, samtools,
and Java versions and output hashes belong in the workflow verified record.
Execute without this option preserves the replacement transaction below.

## Current execution surfaces

[`step_05_split_n_cigar_reads.sh`](step_05_split_n_cigar_reads.sh)
is side-effect-free in dry-run. Historical execute mode uses run-token BAM,
BAI, GATK temp, and backup paths; an owned output-directory lock;
pre-publication validation; complete-pair predecessor checks; sequential final
moves; final revalidation; and rollback to a prior pair or removal of a new
partial pair. Existing valid pairs are replaceable. That route does not
snapshot-recheck inputs, and neither route publishes a native attempt receipt.

Rollback restoration moves are best-effort (`|| true`), after which cleanup
can remove backups and the lock. Ordinary backup/publication rollback is
tested, but a failure inside restoration can lose predecessor and recovery
evidence. The lock is output-directory-wide rather than sample-scoped.

[`step_05_split_n_cigar_reads.slurm`](step_05_split_n_cigar_reads.slurm)
owns cluster defaults, module/tool/Java resolution, delegation, and final
existence checks. The shell entrypoint is currently interpreter-only, and the
wrapper has the characterized Bash 3.2 empty-array dry-run defect.

## Validation interface

The grouped `python -I -m norad validate split-n-cigar` route, implemented by
private [`validator.py`](validator.py), accepts explicit BAM, BAI, FASTA, FAI,
DICT, samtools, scope, and report paths. Dry-run prints the common TSV;
`--execute` snapshot-rechecks inputs and uses the neutral validation-report
publisher.

Exact checks are:

- `bam_bai_structure`;
- `samtools_quickcheck`;
- `coordinate_sorting`;
- `read_group_preservation`; and
- `reference_sidecars`.

The validator checks BAM/BAI magic, quickcheck exit, coordinate order, one
matching `ID`/`SM` read group, and exact ordered FASTA/FAI/DICT contig/length
agreement. It does not prove BAM/BAI correspondence, output relation to the
marked input, or GATK split-N-cigar semantics. It imports
report/BAM helpers from neutral
[`validation/report.py`](../../libraries/validation/report.py) and
[`alignments/bam.py`](../../libraries/alignments/bam.py), and reference parsers
from neutral [`references/contigs.py`](../../libraries/references/contigs.py).
Package selection is owned by the grouped command; direct execution of private
`validator.py`, ambient `PYTHONPATH` injection, compatibility imports, and
peer-stage implementation dependencies are not supported interfaces.

The producer shares executable-value resolution through neutral
[`executable_resolution.sh`](../../libraries/executable_resolution.sh) and the
bound-Python selected-Java handoff through neutral
[`gatk_invocation.sh`](../../libraries/gatk_invocation.sh) and
[`process_environment.py`](../../libraries/process_environment.py). Execute
mode requires absolute Python 3.11+ in `NORAD_SHA256_PYTHON`, requires Java to
resolve to canonical `<JAVA_HOME>/bin/java`, and removes ambient JVM/GATK
selectors before both the GATK version probe and work. This stage retains
GATK/samtools/Java precedence, minimum versions, exact SplitNCigarReads
arguments, transaction, validation, and output policy.

Content mismatches publish `status=fail`; unsafe inputs, required tool-call
failures, and report-publication failures exit `2`.

## Consumers and protected evidence

- The final
  [`partition_BAM_by_mechanical_read_orientation`](../mechanical_orientation/README.md)
  owner consumes the split BAM/BAI.
- Artifact adapters register `step05_split_bam_v1`, `step05_split_bai_v1`, and
  `step05_validation_report_v1`; summary/report code consumes them without
  rerunning GATK.
- [`test_step_05_split_n_cigar_reads.sh`](../../../../tests/stages/split_n_cigar/test_step_05_split_n_cigar_reads.sh)
  protects dry-run, tools/Java, reference prerequisites, locks, temp cleanup,
  staged validation, complete-pair rules, and ordinary rollback fault paths.
- [`test_validate_step_05_split_ncigar.py`](../../../../tests/stages/split_n_cigar/test_validate_step_05_split_ncigar.py),
  wrapper, roster, publication-fault, public-CLI, artifact, report, data-check,
  and coverage tests protect the recorded boundaries.

This is local fixture/mock characterization, not new runtime, cluster,
scientific-review, or biological evidence.

## Current ownership boundaries and retained defects

- Reference-contig parsing, BAM validation, and report publication remain
  neutral private libraries. Reference provenance remains a separate public
  cross-cutting evidence owner. This stage owns its three caller-local exact-
  file loaders, check roster, CLI, and transformation journey.
- The legacy replacement transaction lacks stable-input identity and robust
  rollback-failure recovery evidence. The no-clobber path hash-rechecks its
  admitted BAM, BAI, FASTA, FAI, and DICT but still lacks a native receipt and
  wider verified-task binding.
- Producer and validator prove structure but not the GATK-specific transform.
- Scheduler Bash `3.2`, warning-only tool preflight, dry-run log mutation, and
  stale-pair success remain characterized defects rather than guarantees.
