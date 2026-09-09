# `split_N_cigar_reads_with_GATK` stage contract

This directory owns historical Step `05`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The private validator is grouped under `emrys validate`;
the shell producer is an internal Run worker.

## Responsibility and execution dependencies

See the [README](README.md) for purpose, inputs, outputs, and normal use.

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
bound by the worker; the Run supplies the admitted sample and the worker
requires a path-safe identifier.

Outputs are:

```text
<output-dir>/<sample-id>.split_ncigar.bam
<output-dir>/<sample-id>.split_ncigar.bam.bai
```

The producer requires quickcheck success, coordinate sort order, exactly one
matching `ID`/`SM` read group, at least one alignment, all alignments tagged
with that group, and a nonempty index. It does not publish a receipt or prove
that CIGAR-N transformation semantics occurred.

## Scientific worker

[`step_05_split_n_cigar_reads.sh`](step_05_split_n_cigar_reads.sh) is an internal worker of the
[Run task runner](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The worker runs GATK with runner scratch supplied consistently as Java's
`java.io.tmpdir`, GATK `--tmp-dir`, and `TMPDIR`. It retains the selected-Java
17+ probe and isolated GATK environment, creates the canonical `.bam.bai`
index with samtools, and applies the native BAM checks above. A GATK-created
alternate `.bai` may remain in scratch; it is not a second published index.

### Historical replacement defect

The retired standalone writer used predecessor backups and best-effort
restoration. A failure during restoration could be ignored before cleanup
removed backups and the lock, losing predecessor and recovery evidence. The
old implementation and its fault characterization remain in
[revision 88522d0a](https://github.com/lab-cats/EMRYS/tree/88522d0a/src/emrys/stages/split_n_cigar).
This records the old defect; it does not authorize deleting old residue.

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
exact SplitNCigarReads arguments, validation, and output policy.

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
[evidence ceiling](../../../../tests/README.md). The historical replacement
defect is retained above. Producer and validator prove
structure, not the GATK-specific transformation.
