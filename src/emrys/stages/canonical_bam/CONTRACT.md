# `construct_canonical_BAM` stage contract

This directory owns historical Step `02`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The private validator is grouped under `emrys validate`;
the shell producer is an internal Run worker.

## Responsibility

The [README](README.md) explains BAM preparation and use. The worker validates
the staged pair before the runner publishes it. The separate
validator reads a declared pair without changing it.

## Execution dependencies

The input must be one samtools-readable alignment. Step `01` normally supplies
it, but any explicit SAM or BAM can be used; STAR logs and filenames are not
required.

After the canonical pair is published, historical Step `02b` BAM QC, Step `03`
strandedness/orientation inference, and Step `04` duplicate marking can consume
it independently. Step `03` also requires the BED12 produced by historical
Step `00b`. The current Step `04` implementation does not consume Step `02b`
or Step `03` outputs, so those three direct consumers are data-parallel once
their own additional prerequisites are satisfied.

## Inputs

The producer accepts:

- a sample identifier matching `[A-Za-z0-9][A-Za-z0-9._-]*`, used for output
  names and read-group fields;
- one explicit input SAM or BAM file;
- one explicit staging output directory;
- a positive thread count; and
- an available samtools executable.

The worker requires a nonempty alignment and a safe sample identifier;
samtools establishes the alignment content contract.

## Outputs

For `<sample-id>`, the canonical pair is:

```text
<output-dir>/<sample-id>.sorted.bam
<output-dir>/<sample-id>.sorted.bam.bai
```

The producer requires a nonempty BAM that passes `samtools quickcheck`, has
exactly one `@RG` header with `ID`, `SM`, and `LB` equal to the sample
identifier and `PL:ILLUMINA`, declares coordinate sort order, contains at least
one alignment, and tags every alignment with that read-group identifier. The
BAI must be nonempty.

The two files are published create-exclusively, but no receipt or summary
marks transaction completion. They are not an atomic two-file filesystem write.

## Scientific worker

[`step_02_sort_index_bam.sh`](step_02_sort_index_bam.sh) is an internal worker of the
[Run task runner](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The worker skips sorting when the input header declares `SO:coordinate`;
otherwise it sorts with samtools in runner scratch. It reuses the input inode
only when the single read group and every alignment tag already satisfy the
canonical contract and a hard link is available. Otherwise it replaces all
read groups with the declared sample group. It indexes and validates the
staged BAM/BAI pair. The runner preserves that checked byte identity through
publication, including the source binding when a canonical input is reused.

### Historical producer cleanup limits

At [revision 88522d0a](https://github.com/lab-cats/EMRYS/tree/88522d0a/tests/stages/canonical_bam),
producer-local fault tests characterized these additional cleanup limits:


- If removing both publication anchors persistently fails before either is
  removed, rollback removes both owned finals. EXIT cleanup fails to remove the
  anchors again but releases the owned lock. Both anchors remain, and the
  residue check refuses retry. Lock retention is not guaranteed for every
  cleanup failure.
- If the BAM anchor is removed before anchor cleanup fails, the final BAM is
  no longer provably owned. Rollback preserves that BAM, the remaining BAI
  anchor, and the lock, and removes the still-provably-owned final BAI.
- If unlinking lock metadata persistently fails after publication completes,
  the validated pair and owned lock remain and the command exits nonzero.

These states require operator inspection; a missing lock, present pair, or
nonzero exit alone does not authorize deletion, adoption, replacement, or retry.
No action here repairs residue from an earlier invocation.

## Historical replacement defect

The retired replacement path had a characterized data-loss defect. At
`f9c22c9a558702db62782a03be5f694fb2d04768`, the
[producer](https://github.com/lab-cats/EMRYS/blob/f9c22c9a558702db62782a03be5f694fb2d04768/src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh)
and its
[persistent-restore-failure oracle](https://github.com/lab-cats/EMRYS/blob/f9c22c9a558702db62782a03be5f694fb2d04768/tests/stages/canonical_bam/test_step_02_sort_index_bam.sh#L684)
record this exact sequence: final BAI publication fails, then restoring the
prior BAM fails persistently. Best-effort restoration ignores that second
failure, and cleanup deletes the backup. The command returns nonzero with both
diagnostics but leaves only the prior BAI at its canonical path: the canonical
BAM, both backups, owned lock, and run-token scratch are absent. This was a
lockless partial pair with a lost prior BAM, not successful rollback or
failure-atomicity. Current refusal of existing outputs prevents entering that
replacement path; it cannot recover the lost bytes or authorize cleanup of old
backups. The historical source, oracle, and this failure record are retained.

## Validation interface

The grouped route `emrys validate canonical-bam`, implemented by
private [`validator.py`](validator.py), accepts an explicit scope, BAM, BAI,
samtools executable, and output path. Validation is dry-run by default;
`--execute` publishes
`<scope-id>.validation.tsv` using the common seven-field step-validation
contract.

The report contains exactly these five check identities:

- `bam_bai_structure`;
- `samtools_quickcheck`;
- `coordinate_sorting`;
- `read_group_header`; and
- `alignment_rg_tags`.

The checks require BAM/BGZF and BAI/CSI magic bytes, a successful samtools
quickcheck, one coordinate-sorted `@HD`, one `@RG` whose `ID` and `SM` match
the scope, and equal total and matching-RG alignment counts. These checks do
not establish biological correctness.

The validator is less strict than the producer: it permits a zero-record BAM
when both counts are zero, does not require the producer's `LB` or
`PL:ILLUMINA` fields, and labels empty quickcheck diagnostics as expected while
testing only the command's exit status. Neither surface proves that the
declared BAI/CSI belongs to the declared BAM. These asymmetries are preserved
for later contract resolution, not normalized here.

A content mismatch is represented by a `status=fail` row and does not repair
the canonical pair. Missing, unreadable, or unsafe input, a failed tool call
needed to construct evidence, an invalid CLI/output contract, or unsafe
publication state exits with code `2` without publishing a new report.

The validator uses the shared validation publisher and BAM tool/header helper;
Step `04` and Step `05` share the latter rather than importing this stage.

## Consumers

- Historical Step `02b` consumes the canonical BAM and discovers either
  supported adjacent BAI naming convention for BAM QC.
- Historical Step `03` consumes the BAM/BAI together with an explicit BED12
  annotation for RSeQC inference.
- Historical Step `04` consumes the exact `<bam>.bai` pair for duplicate
  marking.
- Read-only validation and the three direct consumer branches do not acquire
  a shared producer lock. Run tasks bind their own input snapshots;
  stand-alone validation still requires stable inputs. External mutation is
  not made safe by refusing producer replacement.
- The artifact inventory registers the canonical pair and validation report
  through `step02_canonical_bam_v1`, `step02_canonical_bai_v1`, and
  `step02_validation_report_v1`.
- Artifact indexing, canonical summaries, and reports consume those registered
  artifacts and validation evidence without rebuilding the pair.

## Protection, evidence ceiling, and retained decisions

Repository tests protect current refusal, staging, publication, and recovery
behavior under the shared [evidence ceiling](../../../../tests/README.md).
The historical replacement characterization above preserves the retired
failure evidence separately from current expected behavior.

Two decisions remain open: whether this stays a distinct stage now that STAR
normally emits canonical bytes, and whether one contract should replace the
current producer/validator disagreement over empty BAMs and `LB`/`PL` fields.
Run materialization supplies the sample argument, but library and platform
remain derived here rather than admitted as manifest metadata.
