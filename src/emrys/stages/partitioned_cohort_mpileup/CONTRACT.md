# `generate_partitioned_cohort_mpileup_VCFs` stage contract

This directory owns historical Step `07`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The producer is workflow-private and the validator is
grouped under `emrys validate`.

## Responsibility and execution dependencies

For one declared cohort partition, generate separate `FWD_like` and
`REV_like` multi-sample VCFs from every sample's Step `06` BAM in canonical
manifest order, then publish the two VCFs and receipt as one transaction.
This is pileup generation and filtering, not a `bcftools call` operation or a
claim that variants or RNA-editing sites have been identified.

Step `07` requires the complete BAM/BAI pair for both mechanical orientation
groups of every declared sample from the final
[`partition_BAM_by_mechanical_read_orientation`](../mechanical_orientation/README.md)
owner, but only checks those files' presence and nonemptiness; it does not
require Step `06` counts, validation evidence, or a native completion marker.
Distinct partitions may run
independently when they use distinct output locks and immutable shared inputs.
The
[`preprocess_and_annotate_cohort_candidates`](../cohort_candidate_preprocessing/CONTRACT.md)
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
completion marker. Both published VCFs are structurally revalidated and
record-count checked before the receipt becomes visible. The receipt itself is
then checked inside the owned rollback boundary; its mere presence is not
independent proof of a successfully completed immutable computation.

[`producer.py`](producer.py) is side-effect-free in dry-run. Execute mode hashes
and later rechecks both
manifests, uses a cohort/partition lock and run-token temporary/backup paths,
rejects stale owned paths and partial prior sets, validates temporary VCF
sample order and counts, then replaces all three outputs with the receipt last.
Final outputs are revalidated before backups are removed.
`--no-clobber` is the orchestration-safe policy: while holding the owner lock,
it rejects a complete predecessor set without invoking bcftools or changing
stable outputs. A direct invocation hashes the exact sample and partition
manifests, reference FASTA/FAI pair, selected regions file when applicable,
and both BAM/BAI pairs for every admitted sample before bcftools, then rechecks
that roster after tool execution and again before publication. An admitted
run-coordinator task has already hashed the same declared roster twice at producer
entry. It supplies a process-lifetime aggregate only to this producer, which
reconstructs the roster without another initial full pass and rehashes the
complete roster immediately before publication. The task boundary performs
its unchanged final declared-input recheck after validation. The aggregate is
not persisted or added to the native receipt. Direct invocations retain
complete-set replacement and the legacy manifests-only stability boundary
unless `--no-clobber` is supplied.
First publication in that mode is create-exclusive; VCF and receipt staging
inode anchors remain through final validation, and ambiguous replacement
preserves the owner lock and residue.

Ordinary rollback restores the prior three-file set. If restoration itself
fails, backup paths and the owned lock are preserved for operator recovery;
there is no automated recovery interface. The receipt hash-binds the two
manifests only: BAMs, reference, FAI, regions file, tool identity, depth, and
filter are not durable receipt provenance. The receipt also does not hash
either output VCF.

## Validation interface

The grouped `emrys validate partitioned-cohort-mpileup` route,
implemented by private [`validator.py`](validator.py), accepts explicit cohort,
partition, manifests, FAI, both VCFs, receipt, and report output. It does not
invoke bcftools. Dry-run prints the common report; `--execute`
snapshot-rechecks inputs and uses the neutral validation-report publisher.

Exact checks are:

- `receipt_structure`;
- `vcf_structure`;
- `selector_reconciliation`;
- `manifest_identity_and_sample_order`; and
- `vcf_record_counts`.

The validator enforces receipt shape and row order, VCF header/data-row shape,
numeric positions, selector declarations against the FAI, manifest hashes,
exact VCF sample order, physical VCF identity, and record counts. It does not
verify that data coordinates remain inside the selector, validate REF/ALT or
FORMAT annotation semantics, rerun the filter, or bind input BAM, reference,
tool, policy, or output content identities. Producer and validator still differ
for `regions_file` detail.

Content mismatches publish `status=fail`; unsafe structure or report-
publication failures exit `2`.

Receipt TSV parsing remains permissive: some missing-field shapes can escape
as `KeyError` or `AttributeError` with a traceback and exit `1` rather than the
controlled exit-`2` boundary.

## Consumers, protection, and evidence ceiling

- The final
  [`preprocess_and_annotate_cohort_candidates`](../cohort_candidate_preprocessing/CONTRACT.md)
  contract consumes the declared Step `07` VCF/receipt transactions; it does
  not rediscover partitions or orientations from filenames.
- Artifact adapters register both VCFs, the receipt, and
  `step07_validation_report_v1`; reports consume registered evidence without
  rerunning pileup.

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). The exact receipt-provenance
limits, selector asymmetry, validation ceiling, and uncontrolled malformed-
receipt exception above remain retained defects rather than inferred
guarantees.
