# Current architecture

This document owns the current system topology, component boundaries,
contracts, and data flow. Status and branch lineage belong in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); current evidence
belongs in [`../operations/HANDOFF.md`](../operations/HANDOFF.md).

Canonical diagrams:

- [`diagrams/pipeline.mmd`](diagrams/pipeline.mmd)
- [`diagrams/reliability.mmd`](diagrams/reliability.mmd)

## Compute pipeline

The workflow is a directed graph with a primary reference-and-read preparation
chain, parallel QC/evidence branches, and downstream cohort analysis:

```text
reference inputs
|-> 00a STAR index
|-> 00b BED12
`-> 00c FASTA sidecars

paired FASTQ + sample manifest + STAR index
-> STAR alignment
-> canonical sorted/read-group BAM
   |-> 02b BAM-QC evidence
   |-> 03 paired-orientation evidence (+ BED12)
   `-> 04 duplicate marking
       -> 05 SplitNCigarReads (+ FASTA sidecars)
       -> 06 mechanical FWD_like / REV_like BAMs
       -> 07 manifest-partitioned cohort mpileup
       -> 08 deterministic VCF preprocessing and annotation
       -> 09 paired CMH candidate ranking
       -> 09c explicit scientific-evidence review (+ declared evidence)
```

SLURM wrappers remain thin. Analysis and validation logic lives in
parameterized scripts. The login node is not a compute engine.

### Functional-owner contract index

The exact public-entrypoint and cross-cutting-domain coverage roster is
[`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md).

- Historical Step `00a`, working name `construct_STAR_index`:
  [`CONTRACT.md`](../../src/norad/stages/construct_STAR_index/CONTRACT.md)
- Historical Step `00b`, working name `convert_GTF_to_BED12`:
  [`CONTRACT.md`](../../src/norad/stages/convert_GTF_to_BED12/CONTRACT.md)
- Historical Step `00c`, working name `construct_FASTA_sidecars`:
  [`CONTRACT.md`](../../src/norad/stages/construct_FASTA_sidecars/CONTRACT.md)
- Historical Step `01`, working name `align_RNA_reads_with_STAR`:
  [`CONTRACT.md`](../../src/norad/stages/align_RNA_reads_with_STAR/CONTRACT.md)
- Historical Step `02`, working name `construct_canonical_BAM`:
  [`CONTRACT.md`](../../src/norad/stages/construct_canonical_BAM/CONTRACT.md)
- Historical Step `02b`, evidence operation `collect_canonical_BAM_QC_evidence`:
  [`CONTRACT.md`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/CONTRACT.md)
- Historical Step `03`, evidence operation `collect_RSeQC_paired_orientation_evidence`:
  [`CONTRACT.md`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/CONTRACT.md)
- Historical Step `04`, working name `mark_BAM_duplicates_with_Picard`:
  [`CONTRACT.md`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/CONTRACT.md)
- Historical Step `05`, working name `split_N_cigar_reads_with_GATK`:
  [`CONTRACT.md`](../../src/norad/stages/split_N_cigar_reads_with_GATK/CONTRACT.md)
- Historical Step `06`, working name `partition_BAM_by_mechanical_read_orientation`:
  [`CONTRACT.md`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/CONTRACT.md)
- Historical Step `07`, working name `generate_partitioned_cohort_mpileup_VCFs`:
  [`CONTRACT.md`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md)
- Historical Step `08`, working name `preprocess_and_annotate_cohort_candidates`:
  [`CONTRACT.md`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md)
- Historical Step `09`, analysis operation `rank_cohort_candidates_with_paired_CMH`:
  [`CONTRACT.md`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md)
- Historical Step `09c`, evidence operation `assemble_scientific_review_evidence_package`:
  [`CONTRACT.md`](../../src/norad/evidence/assemble_scientific_review_evidence_package/CONTRACT.md)

## Identity and explicit-input boundaries

The sample manifest is the source of sample identity, order, condition, and
replicate pairing. The partition manifest defines Step `07` selection.
Reference and analysis policy identities are explicit contracts.

Downstream stages consume declared paths and receipts. They do not infer
samples, partitions, report tables, or scientific evidence from filenames or
globs.

## Native artifact transactions

Current multi-file owners use several publication patterns. Many attempt
validation before publication, marker-last completion, owned locks or staging,
no-clobber checks, rollback, and retained recovery evidence, but those
properties are not uniform. Some markers become visible before final
post-publication checks, so marker presence alone does not always prove that
the producer returned success. Each functional-owner contract records its
exact guarantees and characterized defects.

A transaction may be structurally complete while its evidence records still
say missing, failed, incomplete, unavailable, blocked, or not run.

## Artifact contracts and indexing

Versioned schemas under `schemas/artifacts/v1/` define:

- artifact records;
- scientific-review records;
- canonical run summaries;
- report receipts;
- shared identifiers and evidence fields.

An explicit artifact inventory drives read-only adapters. Adapters inspect
declared native outputs and publish records, an ordered index, and a receipt
last. They do not alter native outputs or execute analysis.

## Canonical run-summary assembly

The run-summary builder consumes one exact committed adapter receipt and
optional exact scientific-review and report-table approval inputs. It
publishes canonical JSON plus deterministic artifact and QC TSV views, with
its receipt last.

The canonical JSON is the sole structured report input. Missing and failed
expected scopes remain visible.

## Reporting boundary

Report renderers:

- validate one explicit canonical run summary;
- read only supplemental tables authorized by exact path, hash, row count,
  role, policy, and approval provenance;
- never discover report inputs;
- never execute analysis code;
- never install dependencies;
- never promote computational or scientific state;
- validate accessibility, self-containment, banners, and output identity
  before publication.

Reports use “CMH-ranked candidates.” Scientific-state banners remain visible.
The public renderer accepts explicit `html`, `pdf`, or `all` formats and
defaults to `all`. It publishes the selected static report formats, one
deterministic per-scope summary TSV, and a deterministic report-output receipt
last as a single recoverable transaction. PDF rendering uses pinned Quarto
with bundled Typst; a pinned pure-Python reader validates the PDF signature,
EOF, extractable section order, page count, and exact banner on every page.
A valid predecessor containing only the former HTML output may be upgraded
without weakening identity or no-clobber checks.

The HTML view uses a bounded reading column and broad native disclosure
categories. Overview is initially open and places computational/scientific
status, CMH-ranked candidates, adjudication, and limitations before detailed
QC, sensitivity, review, and provenance material. Wide tables scroll inside
their category rather than expanding the page. The PDF remains a linear
projection and uses compact candidate records where a full-width table would
be unreadable.

## Scientific boundary

Mechanical `FWD_like` and `REV_like` labels are intentionally neutral.
`legacy_provisional_v1` preserves legacy-compatible behavior without asserting
biological strand validity.

Scientific review consumes explicit evidence for orientation, annotation,
quality funnels, replicate effects, sensitivity analyses, candidate selection
and adjudication, decisions, and limitations.

`science_review_complete_exploratory` is provisional.
`biological_interpretation_ready` is reserved until a separate policy defines
and unlocks its exits.

## Runtime and dependency boundaries

Local runtime restoration is explicit and opt-in. R activation is guarded;
Quarto restoration is separate from rendering. Compute and validation entry
points never install software.

Cluster tool modules and paths are operational profiles, not hardcoded
scientific identity. Effective executable versions must be observed in the
runtime where work occurs.

The runtime preflight consumes one exact TSV profile and records tool-version,
R-namespace, functional SHA-256, and absolute-path visibility probes in one
deterministic TSV. Each row declares its required execution context. A check
declared for `cluster_batch` is `blocked` or `not_checked` when the tool
actually runs in `local` context; the program never infers scheduler context.
It installs and repairs nothing, and its report is not connected to the
artifact/run-summary evidence graph. Availability evidence remains distinct
from workflow runtime validation and cluster proof.

## Reference provenance evidence

Reference provenance similarly consumes one explicit inventory and base
directory. It hashes regular FASTA, FAI, DICT, GTF, BED12, and named STAR index
members; records annotation source/release declarations; compares
FASTA/FAI/DICT/STAR ordered names and lengths; and verifies that GTF/BED12
contigs belong to the FASTA universe. It publishes artifact and contig TSVs
with a summary last, reports inconsistencies, and never repairs references.

## Storage evidence

Storage inventory consumes one exact root contract and one exact retention
policy. It measures only the named absolute directory trees without following
symlinks, records filesystem capacity and declared quota, and publishes the
inventory and normalized policy with a summary last. Approval state is
evidence, not an executable instruction: this boundary never deletes, moves,
archives, compresses, or cleans data.

## Validation evidence protocol

Numbered validators observe explicitly declared native artifacts and never
repair them or rerun their producers. The functional-owner
[`CONTRACT.md`](#functional-owner-contract-index) files own each
operation's exact check roster, evidence strength, consumers, and known gaps;
the [ownership inventory](FUNCTIONAL_OWNER_INVENTORY.md) maps every public
validator to one owner.

The common snapshot, seven-column report, lock, rollback, and publication
implementation currently lives in the Step `00a` validator and is imported by
later validators. That reverse dependency is a recorded ownership leak, not a
target-architecture decision, and current shared publication does not enforce
report-row order.

Typed adapters, artifact indexing, canonical-summary assembly, and reporting
project both passing and failing validation evidence without promoting
runtime, cluster, scientific-review, or biological-readiness state.
