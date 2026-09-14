# `generate_partitioned_cohort_mpileup_VCFs` stage contract

This directory owns historical Step `07`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias. The producer is workflow-private and the validator is
grouped under `emrys validate`.

## Responsibility and execution dependencies

See the [README](README.md) for purpose, inputs, outputs, and normal use.

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
partition ID, Step `06` orientation root, reference FASTA plus FAI, staged
output paths and final VCF paths for the receipt, the runner's admitted absolute
bcftools path, positive maximum depth, and filter expression. Sample IDs must
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
record count. The worker checks both staged VCFs for structure, sample order,
and record counts, then writes and checks the receipt using the supplied final
VCF paths. The runner publishes both VCFs before the receipt and verifies that
publication preserves the checked bytes. The independent validator then checks
the visible set. Receipt presence alone is not proof of a verified task.

[`producer.py`](producer.py) runs only through the existing runner. Its
scientific work is the two bcftools pipelines and their output checks;
input stability, publication, and recovery belong to the [runner contract](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The receipt hashes only the two manifests. BAMs, reference, FAI, regions file,
tool identity, depth, filter, and output VCF hashes are not durable receipt
provenance.

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
