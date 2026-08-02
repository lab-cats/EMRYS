# `split_N_cigar_reads_with_GATK` stage contract

This is the observed contract of historical Step `05` for `ARCH-02A`. The
exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug; it is not yet an implemented source location.
Executables remain in `scripts/` and `jobs/`.

## Responsibility and execution dependencies

Run GATK `SplitNCigarReads` on one duplicate-marked RNA-seq BAM, validate and
index the result, and publish a rollback-protected BAM/BAI pair.

Two independent branches converge here: Step `04` normally supplies the marked
`<bam>.bai` pair, while Step `00c` supplies the explicit FASTA, `<fasta>.fai`,
and `<stem>.dict`. Step `05` neither creates nor repairs reference sidecars.
Step `06` consumes the published split BAM/BAI. Historical numbering is
provenance; these data edges define required order.

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

## Current execution surfaces

[`step_05_split_n_cigar_reads.sh`](../../../../scripts/step_05_split_n_cigar_reads.sh)
is side-effect-free in dry-run. Execute mode uses run-token BAM, BAI, GATK temp,
and backup paths; an owned output-directory lock; pre-publication validation;
complete-pair predecessor checks; sequential final moves; final revalidation;
and rollback to a prior pair or removal of a new partial pair. Existing valid
pairs are replaceable. Inputs are not snapshot-rechecked before publication,
and no receipt marks the completed attempt.

Rollback restoration moves are best-effort (`|| true`), after which cleanup
can remove backups and the lock. Ordinary backup/publication rollback is
tested, but a failure inside restoration can lose predecessor and recovery
evidence. The lock is output-directory-wide rather than sample-scoped.

[`step_05_split_n_cigar_reads.slurm`](../../../../jobs/step_05_split_n_cigar_reads.slurm)
owns cluster defaults, module/tool/Java resolution, delegation, and final
existence checks. The shell entrypoint is currently interpreter-only, and the
wrapper has the characterized Bash 3.2 empty-array dry-run defect.

## Validation interface

[`validate_step_05_split_ncigar.py`](../../../../scripts/validate_step_05_split_ncigar.py)
accepts explicit BAM, BAI, FASTA, FAI, DICT, samtools, scope, and report paths.
Dry-run prints the common TSV; `--execute` snapshot-rechecks inputs and uses the
shared Step `00a` report publisher.

Exact checks are:

- `bam_bai_structure`;
- `samtools_quickcheck`;
- `coordinate_sorting`;
- `read_group_preservation`; and
- `reference_sidecars`.

The validator checks BAM/BAI magic, quickcheck exit, coordinate order, one
matching `ID`/`SM` read group, and exact ordered FASTA/FAI/DICT contig/length
agreement. It does not prove BAM/BAI correspondence, output relation to the
marked input, or GATK split-N-cigar semantics. It imports reference parsers and
Step `02` BAM helpers as well as Step `00a` publication, exposing three neutral
concerns through stage-named modules.

Content mismatches publish `status=fail`; unsafe inputs, required tool-call
failures, and report-publication failures exit `2`.

## Consumers and protected evidence

- Step `06` consumes the split BAM/BAI.
- Artifact adapters register `step05_split_bam_v1`, `step05_split_bai_v1`, and
  `step05_validation_report_v1`; summary/report code consumes them without
  rerunning GATK.
- [`test_step_05_split_n_cigar_reads.sh`](../../../../tests/shell/test_step_05_split_n_cigar_reads.sh)
  protects dry-run, tools/Java, reference prerequisites, locks, temp cleanup,
  staged validation, complete-pair rules, and ordinary rollback fault paths.
- [`test_validate_step_05_split_ncigar.py`](../../../../tests/test_validate_step_05_split_ncigar.py),
  wrapper, roster, publication-fault, public-CLI, artifact, report, data-check,
  and coverage tests protect the recorded boundaries.

This is local fixture/mock characterization, not new runtime, cluster,
scientific-review, or biological evidence.

## Ownership gaps and deferred decisions

- Reference validation, BAM validation, report publication, scheduler binding,
  and transformation ownership span several stage-named modules.
- The native pair transaction lacks stable-input identity, receipt, and robust
  rollback-failure recovery evidence.
- Producer and validator prove structure but not the GATK-specific transform.
- Target files, helper ownership, transaction policy, and
  migration mechanics remain deferred.
