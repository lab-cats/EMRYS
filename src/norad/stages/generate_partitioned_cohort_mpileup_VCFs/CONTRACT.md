# `generate_partitioned_cohort_mpileup_VCFs` stage contract

This is the observed contract of historical Step `07`, now implemented in this
native owner directory. The exact public identity and historical alias are
owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug and owns the producer, validator, and scheduler assets.

## Responsibility and execution dependencies

For one declared cohort partition, generate separate `FWD_like` and
`REV_like` multi-sample VCFs from every sample's Step `06` BAM in canonical
manifest order, then publish the two VCFs and receipt as one transaction.
This is pileup generation and filtering, not a `bcftools call` operation or a
claim that variants or RNA-editing sites have been identified.

Step `07` requires the complete BAM/BAI pair for both mechanical orientation
groups of every declared sample from the final
[`partition_BAM_by_mechanical_read_orientation`](../partition_BAM_by_mechanical_read_orientation/README.md)
owner, but only checks those files' presence and nonemptiness; it does not
require Step `06` counts, validation evidence, or a native completion marker.
Distinct partitions may run
independently when they use distinct output locks and immutable shared inputs.
The
[`preprocess_and_annotate_cohort_candidates`](../preprocess_and_annotate_cohort_candidates/CONTRACT.md)
owner is the cohort barrier and consumes the complete declared partition-by-
orientation result set regardless of partition completion order.

## Inputs and selector contract

Inputs are a safe cohort ID, sample manifest, partition manifest, requested
partition ID, Step `06` orientation root, reference FASTA plus FAI, output
root, bcftools, positive maximum depth, and filter expression. Sample IDs must
be unique and nonempty. The requested partition must have exactly one manifest
row with one of these selector types:

- `region`, passed to `bcftools mpileup -r`; or
- `regions_file`, passed with `-R`, with relative paths resolved from the
  partition manifest directory.

Selectors are checked against the FAI. The FWD and REV BAM argument arrays are
built in exact sample-manifest order. `FWD_like` and `REV_like` remain
mechanical labels; they do not establish transcript strand, library
strandedness, sense, or antisense.

The default maximum depth is `10000000`; the default filter is
`INFO/AD[1-]>2 & MAX(FORMAT/DP)>20`. Each orientation runs `bcftools mpileup`
with `-Ou`, `-I`, the reference, selector, depth, and declared DP/AD/ADF/ADR/SP
annotations, then pipes to `bcftools filter -Ov`. No calling subcommand runs.

## Outputs and transaction marker

For `<cohort>` and `<partition>`, the output directory contains:

```text
<cohort>.<partition>.FWD_like.mpileup.vcf
<cohort>.<partition>.REV_like.mpileup.vcf
<cohort>.<partition>.step07_outputs.tsv
```

Header-only VCFs are valid. The receipt has exactly two rows, ordered
`FWD_like` then `REV_like`, and records cohort, partition, selector type/value,
orientation, VCF path, both manifest SHA-256 values, sample count, and VCF
record count. It is renamed last among the three outputs and is the native
completion marker, but becomes visible before post-publication validation and
the producer's in-memory committed flag; its mere presence is not independent
proof of a successfully completed immutable computation.

[`step_07_bcftools_mpileup_by_chrom_and_strand.sh`](step_07_bcftools_mpileup_by_chrom_and_strand.sh)
is side-effect-free in dry-run. Execute mode hashes and later rechecks both
manifests, uses a cohort/partition lock and run-token temporary/backup paths,
rejects stale owned paths and partial prior sets, validates temporary VCF
sample order and counts, then replaces all three outputs with the receipt last.
Final outputs are revalidated before backups are removed.

Ordinary rollback restores the prior three-file set. If restoration itself
fails, backup paths are preserved, but there is no recovery marker or automated
recovery interface. Stable-input rechecks cover the two manifests only: BAMs,
reference, FAI, regions file, tool identity, depth, and filter are not bound by
hash in the receipt. The receipt also does not hash either output VCF.

[`step_07_bcftools_mpileup_by_chrom_and_strand.slurm`](step_07_bcftools_mpileup_by_chrom_and_strand.slurm)
owns cluster defaults, module loading, execution gating, delegation, and final
path checks; it does not own pileup or publication logic.

## Validation interface

[`validate_step_07_mpileup_outputs.py`](validate_step_07_mpileup_outputs.py)
accepts explicit cohort, partition, manifests, FAI, both VCFs, receipt, and
report output. It does not invoke bcftools. Dry-run prints the common report;
`--execute` snapshot-rechecks inputs and uses the neutral validation-report
publisher.

Exact checks are:

- `receipt_structure`;
- `vcf_structure`;
- `selector_reconciliation`;
- `manifest_identity_and_sample_order`; and
- `vcf_record_counts`.

The validator enforces receipt shape and row order, VCF header/data-row shape,
numeric positions, selector declarations against the FAI, manifest hashes,
exact VCF sample order, explicit VCF paths, and record counts. It does not
verify that data coordinates remain inside the selector, validate REF/ALT or
FORMAT annotation semantics, rerun the filter, or bind input BAM, reference,
tool, policy, or output content identities. Producer and validator also differ
for `regions_file` detail, and a receipt written from a relative output root
may not match the validator's resolved absolute VCF arguments.

Content mismatches publish `status=fail`; unsafe structure or report-
publication failures exit `2`.

## Consumers and protected evidence

- The final
  [`preprocess_and_annotate_cohort_candidates`](../preprocess_and_annotate_cohort_candidates/CONTRACT.md)
  contract consumes the declared Step `07` VCF/receipt transactions; it does
  not rediscover partitions or orientations from filenames.
- Artifact adapters register both VCFs, the receipt, and
  `step07_validation_report_v1`; reports consume registered evidence without
  rerunning pileup.
- [`test_step_07_bcftools_mpileup_by_chrom_and_strand.sh`](../../../../tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh)
  protects selector modes, manifest order, commands, dry-run, publication,
  locking, stale paths, child failures, transaction ordering, replacement,
  rollback failures, signals, mutation gaps, and provenance omissions.
- [`test_validate_step_07_mpileup_outputs.py`](../../../../tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_validate_step_07_mpileup_outputs.py)
  plus wrapper, roster, publication-fault, public-CLI, artifact, report, and
  coverage tests protect the independent evidence boundary.

This is local mocked-runtime/fixture characterization, not real-runtime,
cluster, scientific-review, or biological evidence.

## Current ownership boundaries and retained defects

- Receipt, manifest, selector, and VCF reconciliation logic spans producer,
  validator, downstream preprocessing, and artifact adapters; this owner keeps
  its native receipt and five-check roster.
- Shared report publication remains in neutral
  [`validation/report.py`](../../libraries/validation/report.py), imported
  through `norad.libraries.validation`.
- The producer sources only `resolve_executable_value` from neutral
  [`executable_resolution.sh`](../../libraries/executable_resolution.sh);
  bcftools precedence, checks, and commands remain owned here.
- Attempt identity, complete provenance, output hashes, and an automated
  recovery interface remain absent. Only manifests are hash-bound and stable-
  rechecked; restoration is best-effort and receipt visibility precedes final
  validation and the committed flag.
- Producer/validator selector detail and relative-path semantics remain
  asymmetric. The validator may publish failed rows with exit `0`, does not
  invoke bcftools, and does not prove selector-bound coordinates, VCF semantic
  fields, filter compliance, immutable inputs, or current-attempt identity.
- The scheduler retains warning-only unusable-tool preflight, submit-CWD and
  body-level log mutations, version-command failure, one-CPU defaults, and
  stale-three-file false success as characterized defects rather than
  guarantees.
