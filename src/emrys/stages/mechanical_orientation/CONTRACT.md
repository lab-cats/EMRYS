# `partition_BAM_by_mechanical_read_orientation` stage contract

This directory owns historical Step `06`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The producer is workflow-private and the validator is
grouped under `emrys validate`.

## Responsibility and execution dependencies

Partition one split-N-cigar BAM into the protected legacy `FWD_like` and
`REV_like` mechanical flag groups, index both BAMs, reconcile counts, and
publish the five outputs as one rollback-protected set.

Step `05` normally supplies the required BAM plus exact `<bam>.bai`. Step `06`
does not consume Step `03` RSeQC evidence, a manifest, or biological-
orientation policy. Per-sample partitions may run independently. The final
[`generate_partitioned_cohort_mpileup_VCFs`](../partitioned_cohort_mpileup/README.md)
owner requires both BAM/BAI pairs for every declared sample before a cohort
partition can run; it does not consume the Step `06` counts or validation
report.

## Mechanical contract, inputs, and outputs

The exact group definitions are:

```text
FWD_like = samtools view -f 99 plus -f 147
REV_like = samtools view -f 83 plus -f 163
```

`-f` requires the named bits and permits additional bits. These labels are not
transcript strand, library strandedness, sense, or antisense. Unassigned reads
are allowed; exhaustive partitioning is not claimed.

Inputs are sample ID, nonempty split BAM and exact adjacent BAI, output/QC
directories, positive threads, an admitted owner token, and the absolute
samtools path selected by the Run runtime. Outputs are:

```text
<sample>.FWD_like.bam
<sample>.FWD_like.bam.bai
<sample>.REV_like.bam
<sample>.REV_like.bam.bai
<sample>.orientation_counts.tsv
```

The exact one-row TSV records input, four flag-group, two merged-group,
assigned, and unassigned counts plus a six-decimal assigned fraction. Input and
both merged groups must be nonzero; assigned may not exceed input.

## Orchestration-safe producer boundary

The private producer has one create-absent mode. It refuses any member of an
existing five-file final set before tool work, hashes and rechecks the input
BAM/BAI, and retains the per-sample owned lock, temporary-set validation,
ordered publication, and final-path validation. It never creates predecessor
backups. Finals are hard-link create-exclusive and staging inode anchors remain
through complete-set validation. The counts TSV remains native evidence rather
than a receipt; tool-version and final-set hashes belong in the workflow
verified record.

## Current execution surfaces

[`producer.py`](producer.py) is invoked only by the fixed workflow task. It
uses one per-sample owned lock and run-token temporary paths, rejects stale
owned-path candidates, validates both temporary pairs and arithmetic, publishes
the counts TSV last, and revalidates final paths. Failure removes only partial
finals still proven to share their staging inode; ambiguous mutation preserves
the final, staging anchor, and lock for operator inspection. The counts TSV is
a final native output, not a cryptographic transaction receipt.

## Validation interface

The grouped `emrys validate mechanical-orientation` route,
implemented by private [`validator.py`](validator.py), accepts the four
explicit BAM/BAI paths, counts TSV, scope, and report output. It does not invoke
samtools. Dry-run prints the common TSV; `--execute` snapshot-rechecks inputs
and uses the neutral validation-report publisher.

Exact checks are:

- `output_containers`;
- `counts_structure`;
- `fwd_count_arithmetic`;
- `rev_count_arithmetic`; and
- `assigned_count_arithmetic`.

The validator checks container magic, exact header/one scope row, nonnegative
typed counts, both flag-group sums, assigned/unassigned reconciliation,
positive input, and fraction agreement within six-decimal rounding. It does
not quickcheck BAMs, recount records, inspect flags, verify BAM/BAI
correspondence, or validate sort/read-group metadata. Producer and independent
validator therefore protect different evidence layers.

Content mismatches publish `status=fail`; unsafe input or report-publication
failures exit `2`.

## Consumers, protection, and evidence ceiling

- The final
  [`generate_partitioned_cohort_mpileup_VCFs`](../partitioned_cohort_mpileup/README.md)
  owner consumes both orientation BAM/BAI pairs for every manifest sample in
  manifest order.
- Artifact adapters register both pairs, counts, and
  `step06_validation_report_v1`; summaries/reports consume them without
  rerunning samtools.

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). The producer does not reconcile
flag-subcounts against merged-BAM counts; the independent validator may publish
failed rows with exit `0` and, as stated above, neither quickchecks nor recounts
BAM records.
