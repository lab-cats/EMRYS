# `partition_BAM_by_mechanical_read_orientation` stage contract

This is the observed contract of historical Step `06`, now implemented in this
native owner directory. The exact public identity and historical alias are
owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug and owns the producer, validator, and scheduler assets.
Supported journeys and migration evidence are in the adjacent
[`README.md`](README.md).

## Responsibility and execution dependencies

Partition one split-N-cigar BAM into the protected legacy `FWD_like` and
`REV_like` mechanical flag groups, index both BAMs, reconcile counts, and
publish the five outputs as one rollback-protected set.

Step `05` normally supplies the required BAM plus exact `<bam>.bai`. Step `06`
does not consume Step `03` RSeQC evidence, a manifest, or biological-
orientation policy. Per-sample partitions may run independently. The final
[`generate_partitioned_cohort_mpileup_VCFs`](../generate_partitioned_cohort_mpileup_VCFs/README.md)
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
directories, positive threads, and samtools resolved from argument, approved
override, or PATH. Outputs are:

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

## Current execution surfaces

[`step_06_split_bam_by_read_orientation.sh`](step_06_split_bam_by_read_orientation.sh)
is side-effect-free in dry-run. Execute mode uses a per-sample owned lock,
run-token temporary and backup paths, rejects stale owned-path candidates,
validates both temporary pairs and arithmetic, requires an existing final set
to contain all five files or none, publishes the counts TSV last, and
revalidates final paths. Failures restore a prior set or remove new partial
finals.

No stable-input recheck or receipt binds the set to its source/tool/attempt;
the counts TSV is a final native output, not a cryptographic transaction
receipt. Rollback restore moves are best-effort and cleanup can delete backups
after a failed restoration, leaving the same unprotected recovery boundary as
other BAM transactions.

[`step_06_split_bam_by_read_orientation.slurm`](step_06_split_bam_by_read_orientation.slurm)
owns cluster defaults, samtools loading, execution gating, delegation, and
post-execute path checks. It has the characterized Bash 3.2 empty-array dry-run
defect.

## Validation interface

[`validate_step_06_orientation_outputs.py`](validate_step_06_orientation_outputs.py)
accepts the four explicit BAM/BAI paths, counts TSV, scope, and report output.
It does not invoke samtools. Dry-run prints the common TSV; `--execute`
snapshot-rechecks inputs and uses the neutral validation-report publisher.

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

## Consumers and protected evidence

- The final
  [`generate_partitioned_cohort_mpileup_VCFs`](../generate_partitioned_cohort_mpileup_VCFs/README.md)
  owner consumes both orientation BAM/BAI pairs for every manifest sample in
  manifest order.
- Artifact adapters register both pairs, counts, and
  `step06_validation_report_v1`; summaries/reports consume them without
  rerunning samtools.
- [`test_step_06_split_bam_by_read_orientation.sh`](../../../../tests/stages/partition_BAM_by_mechanical_read_orientation/test_step_06_split_bam_by_read_orientation.sh)
  protects flags, counts, dry-run, locks, stale paths, validation, zero-group
  failures, cleanup, complete-set replacement, and ordinary rollback.
- [`test_validate_step_06_orientation_outputs.py`](../../../../tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py),
  wrapper, roster, publication-fault, public-CLI, artifact, report, and coverage
  tests protect the recorded independent evidence boundary.

This is local fixture/mock characterization, not new runtime, cluster,
scientific-review, or biological evidence.

## Current ownership boundaries and retained defects

- Counts schema/arithmetic remains repeated in producer, validator, and artifact
  reconciliation code; this stage owns its native schema and check roster.
- Shared report publication remains in neutral
  [`validation/report.py`](../../libraries/validation/report.py), imported
  through `norad.libraries.validation`.
- The producer sources only `resolve_executable_value` from neutral
  [`executable_resolution.sh`](../../libraries/executable_resolution.sh);
  samtools precedence, checks, and commands remain owned here.
- Native completion and transaction semantics lack attempt and input identity.
  Restoration is best-effort, cleanup can erase recovery evidence, and the
  output-directory lock does not serialize writers to a shared QC directory.
- The producer does not reconcile flag-subcounts against merged-BAM counts;
  the independent validator may publish failed rows with exit `0` and neither
  quickchecks nor recounts BAM records.
- Scheduler Bash `3.2`, warning-only samtools preflight, one-CPU versus
  independently configured threads, dry-run log mutation, version-command,
  and stale-five-file success remain characterized defects rather than
  guarantees.
