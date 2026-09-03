# `split_N_cigar_reads_with_GATK` stage contract

This directory owns historical Step `05`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The private validator is grouped under `emrys validate`;
the producer remains an explicit repository-path command.

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

## Validation interface

The grouped `emrys validate split-n-cigar` route, implemented by
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
marked input, or GATK split-n-cigar semantics. It uses the shared validation,
BAM, and reference-contig helpers. Shared process helpers require execute mode
to use absolute Python 3.11+ in `EMRYS_SHA256_PYTHON`, canonical
`<JAVA_HOME>/bin/java`, and a JVM/GATK-selector-scrubbed environment for both
the GATK probe and work. This stage still owns tool precedence and versions,
exact SplitNCigarReads arguments, transaction, validation, and output policy.

Content mismatches publish `status=fail`; unsafe inputs, required tool-call
failures, and report-publication failures exit `2`.

## Consumers, protection, and evidence ceiling

- The final
  [`partition_BAM_by_mechanical_read_orientation`](../mechanical_orientation/README.md)
  owner consumes the split BAM/BAI.
- Artifact adapters register `step05_split_bam_v1`, `step05_split_bai_v1`, and
  `step05_validation_report_v1`; summary/report code consumes them without
  rerunning GATK.

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). The legacy replacement route
retains the restoration defect described above. Producer and validator prove
structure, not the GATK-specific transformation.
