# `preprocess_and_annotate_cohort_candidates` stage contract

This directory owns historical Step `08`; the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map) owns its public
identity and alias.

## Responsibility and execution dependencies

See the [README](README.md) for purpose, inputs, outputs, and normal use.

Step `08` waits for one [Step `07`](../partitioned_cohort_mpileup/CONTRACT.md)
receipt and both VCFs for every partition in manifest order. It rejects overlaps across declared partitions,
revalidates Step `07` receipts and VCF structure, and hashes the current
receipts and VCFs into its own input receipt. The
[`rank_cohort_candidates_with_paired_CMH`](../../analyses/paired_cmh_candidate_ranking/CONTRACT.md)
analysis consumes the Step `08` sites table and input receipt, not the QC
summary.

## Inputs and provisional policy

Inputs are a safe cohort ID, an ordered paired local-CMH sample manifest,
complete nonoverlapping partition manifest, Step `07` root, nonempty
annotation GTF, and runner-supplied output paths and R runtime.
The sample header is exactly `sample_id, r1_fastq, r2_fastq, strandedness,
condition, replicate`, with optional `notes` last. Required values are
nonempty, sample and replicate IDs are safe, strandedness uses the closed
vocabulary, and sample IDs are unique. Required VCF definitions include FORMAT
DP/AD/ADF/ADR/SP and INFO AD/ADF/ADR; sample columns must match the sample
manifest exactly.

The optional positive `--threads` value defaults to `1` and bounds independent
partition/orientation VCF workers. On Unix, worker results are returned in the
declared manifest/orientation order before deterministic aggregation; Windows
direct execution falls back to one worker. Annotation import/model construction
and aggregate reconciliation remain serial in R. The division between R
computation and Python output checks is specified below.

Annotation ranges stay in `GRanges`. Existing `IRanges` reduction merges
adjacent/overlapping exon and CDS intervals; bounded gaps identify introns,
and exonic ranges outside the CDS span supply fallback UTRs. Explicit five-
and three-prime UTR annotations each take precedence over generic or derived
ranges. Transcript ordering, chromosome/strand/gene consistency checks, and
strand-dependent UTR assignment remain unchanged.

The fixed `legacy_provisional_v1` compatibility policy maps:

```text
FWD_like -> annotation_strand + and complemented genomic REF/ALT for RNA alleles
REV_like -> annotation_strand - and unchanged genomic REF/ALT for RNA alleles
```

This mapping is not validated biological strand, library-strandedness, sense,
or antisense interpretation. Symbolic and non-SNV alternate alleles are counted
but omitted from the published candidate table. Supported SNVs receive
partition-independent candidate IDs, GTF gene/transcript and CDS/UTR/exon/intron
overlaps, source QUAL/FILTER/INFO alternate depth, and per-sample DP, AD, and
derived AF fields. An exact-header sites table with no candidate rows is valid
when all input and summary counts reconcile.

Before `VariantAnnotation` parsing, the R implementation streams raw VCF
records in bounded chunks and validates the lexical values and expected widths
of every consumed `FORMAT/DP`, `FORMAT/AD`, and present `INFO/AD` field. An AD
value may be one `.` only when the whole vector is missing; otherwise its width
must equal REF plus every ALT. Semantic parsing then rejects missing required
FORMAT/INFO definitions, malformed or negative counts, one-sided missing
DP/AD, AD greater than DP, and sample/count inconsistencies. Header-only VCFs
remain valid only when their receipts and zero record counts reconcile.

## Outputs and transaction marker

The three outputs are:

```text
<cohort>/<cohort>.step08_sites.tsv
<cohort>/<cohort>.step08_inputs.tsv
<qc-root>/<cohort>.step08_summary.tsv
```

The sites header contains 22 fixed metadata fields followed by manifest-ordered
`DP__`, `AD__`, and `AF__` columns for every sample. The input receipt has one
row per partition/orientation, ordered by the partition manifest then
`FWD_like`, `REV_like`; it binds Step `07` receipt and VCF hashes, manifest
hashes, annotation path/hash, observed and skipped counts, and policy. The
one-row summary reconciles aggregate counts and identities.

The runner invokes R directly with three staged output paths, runs the Python
validator against those files, and requires every check to pass before publishing
sites, summary, then input receipt. The bytes validated must survive publication. Receipt presence alone does not prove a verified task.
Execution, input stability, publication, and recovery belong to the [runner contract](../../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).

The scientific responsibilities are:

- [The R program](step_08_vcf_preprocessing.R) owns semantic parsing,
  deterministic candidate construction, aggregation, TSV serialization,
  provisional orientation, and annotation.
- Python checks exact headers, field/row counts, receipt ordering and
  identities, basic site fields, candidate uniqueness, and policy/count
  reconciliation. It does not reparse VCFs or reconstruct candidate order
  within a VCF.

The R entrypoint loads its adjacent private input-contract, annotation, Step
`07` receipt, VCF/count, and candidate-processing modules. It resolves siblings
from Rscript's exact `--file=` path and sources them into the program environment.

## Validation interface

The grouped `emrys validate cohort-candidate-preprocessing` route,
implemented by private [`validator.py`](validator.py), accepts explicit cohort,
manifests, annotation GTF, the three outputs, and a report path. It does not
invoke R. Dry-run prints the common report; `--execute` snapshot-rechecks inputs
and uses the neutral validation-report publisher.

Exact checks are:

- `output_transaction`;
- `manifest_annotation_identity`;
- `input_receipt_reconciliation`;
- `sites_order_uniqueness`; and
- `summary_count_reconciliation`.

The validator enforces exact dynamic headers, complete ordered
partition/orientation rows, manifest and annotation identities, typed
per-input arithmetic, unique candidate IDs, sample DP/AD/AF consistency,
lexically valid carried annotation identifiers and independent overlap flags,
per-scope candidate counts, and aggregate summary reconciliation. It validates
the published tables' internal contract; it does not rerun VariantAnnotation,
GTF overlap, allele expansion, provisional complementation, or upstream VCF
filtering. Despite its check name, `sites_order_uniqueness` does not recompute
candidate IDs or prove deterministic row order.

Content mismatches publish `status=fail`; unsafe structure or report-
publication failures exit `2`.

## Consumers, protection, and evidence ceiling

- Step `09` requires exact Step `08` sites and input receipt paths, hashes and
  schemas, preserves the entire candidate order/universe in its all-sites
  output, and carries the provisional policy forward.
- Artifact adapters register all three outputs and
  `step08_validation_report_v1`; reporting consumes registered evidence
  without rerunning R.

Repository tests protect this contract under the shared
[evidence ceiling](../../../../tests/README.md). Guarded real-R fixtures compare
candidate order and bytes across worker counts; Python fault fixtures prove
structural admission, not independent candidate-order reconstruction.

When the runner supplies `--step07-root`, the validator also reopens the exact
upstream receipt/VCF set and reconciles paths, hashes, counts, selectors, and
manifest identities. Standalone inspection without that option checks the
Step `08` transaction's carried evidence. The R program carries the supplied
annotation path; the validator requires its resolved absolute spelling, which
the runner supplies. Different spellings can still fail standalone inspection.
