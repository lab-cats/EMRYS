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
-> STAR index, BED12, FASTA sidecars

paired FASTQ + sample manifest
-> STAR alignment
-> canonical sorted/read-group BAM
-> BAM QC and library-orientation inference
-> duplicate marking
-> SplitNCigarReads
-> mechanical FWD_like / REV_like BAMs
-> manifest-partitioned cohort mpileup
-> deterministic VCF preprocessing and annotation
-> paired CMH candidate ranking
-> explicit scientific-evidence review
```

SLURM wrappers remain thin. Analysis and validation logic lives in
parameterized scripts. The login node is not a compute engine.

### Incremental functional-owner contract index

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

## Identity and explicit-input boundaries

The sample manifest is the source of sample identity, order, condition, and
replicate pairing. The partition manifest defines Step `07` selection.
Reference and analysis policy identities are explicit contracts.

Downstream stages consume declared paths and receipts. They do not infer
samples, partitions, report tables, or scientific evidence from filenames or
globs.

## Native artifact transactions

Multi-file stages publish a validated set with a receipt or summary last.
Owned locks, run-token staging, stable input hashes, validation before
publication, rollback, cleanup, and retained recovery evidence protect stable
outputs.

A transaction may be structurally complete while its evidence records still
say missing, failed, incomplete, unavailable, blocked, or not run.

## Artifact and summary layer

Versioned schemas under `schemas/artifacts/v1/` define:

- artifact records;
- scientific-review records;
- canonical run summaries;
- report receipts;
- shared identifiers and evidence fields.

An explicit artifact inventory drives read-only adapters. Adapters inspect
declared native outputs and publish records, an ordered index, and a receipt
last. They do not alter native outputs or execute analysis.

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

## Runtime boundaries

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

Reference provenance similarly consumes one explicit inventory and base
directory. It hashes regular FASTA, FAI, DICT, GTF, BED12, and named STAR index
members; records annotation source/release declarations; compares
FASTA/FAI/DICT/STAR ordered names and lengths; and verifies that GTF/BED12
contigs belong to the FASTA universe. It publishes artifact and contig TSVs
with a summary last, reports inconsistencies, and never repairs references.

Storage inventory consumes one exact root contract and one exact retention
policy. It measures only the named absolute directory trees without following
symlinks, records filesystem capacity and declared quota, and publishes the
inventory and normalized policy with a summary last. Approval state is
evidence, not an executable instruction: this boundary never deletes, moves,
archives, compresses, or cleans data.

Step-specific validators sit beside native outputs and never mutate them. The
first implemented validator reads the explicit Step `00a` STAR index and its
FASTA/GTF sources, then publishes the common seven-column validation TSV. Its
typed adapter keeps passing and failing check evidence in the artifact graph;
the canonical summary and both report formats project the resulting expected-
scope state without promoting runtime or cluster evidence.

Step `00b` applies the same boundary to the explicit BED12 and source GTF. It
separately reports structural, ordering, block, uniqueness, and deterministic
normalization agreement, then uses its own typed adapter rather than a generic
dispatcher.

Step `00c` reads the explicit FASTA, FAI, and DICT and reports their individual
structure plus exact ordered contig-name/length agreement. Its typed adapter
uses the same evidence-only path; it never creates or repairs reference
sidecars.

Step `01` validates the five explicit STAR outputs for one sample, including
the BAM container, final-log mapping percentages, and splice-junction table.
The per-sample typed adapter exposes those checks to the same summary and
report path without rerunning alignment.

Step `02` uses an explicit samtools executable to validate one canonical
BAM/BAI pair, coordinate sort order, the matching read-group header, and RG
coverage across all alignments. It observes the pair without sorting,
indexing, or changing tags.

Step `02b` separately validates the persisted quickcheck marker and flagstat
counts. It does not invoke samtools; its typed adapter exposes the recorded QC
evidence and count reconciliation.

Step `03` validates the three required RSeQC fractions and their sum while
retaining RSeQC's mechanical paired-orientation labels. Its adapter never
translates those labels into biological strand claims.

Step `04` validates one marked BAM/BAI pair, its preserved sample read group,
and one bounded Picard duplication-metrics row. It observes duplicate-marking
evidence without marking or removing reads.

Step `05` validates one split-N-cigar BAM/BAI pair against explicit
FASTA/FAI/DICT prerequisites. It never invokes GATK or repairs shared
reference sidecars.

Step `06` validates the two explicit mechanical-orientation BAM/BAI pairs and
the exact one-row orientation counts contract. It reconciles the flag-group,
assigned/unassigned, and fraction arithmetic without invoking samtools,
changing outputs, or inferring biological strand.

Step `07` validates one explicit cohort-partition receipt and its two VCFs
against the declared sample manifest, partition manifest, and FAI. It
reconciles selector membership, immutable hashes, sample order, paths, and
record counts without invoking bcftools. Failed expected scopes are projected
as a compact named list in both report formats so late matrix rows remain
visible in PDF text.

Step `08` validates the explicit sites, input-receipt, and summary TSV
transaction against the declared manifests and annotation. It reuses the
native semantic contracts for ordered inputs, candidate uniqueness, sample
fields, AF arithmetic, provenance hashes, and aggregate counts without
invoking R or rediscovering upstream artifacts.

Step `09` validates the six explicit native CMH outputs as one analysis-bound
transaction. It requires exact TSV headers and basenames, one shared parent,
distinct physical files, explicit cohort/provisional-policy identity, and the
complete ordered Step `08` candidate universe. It independently recomputes
target/test/call, depth, AF, and enabled-background semantics and recomputes
global BH values from the reported p-values. It type/range-checks the reported
CMH fields but does not independently derive the CMH statistic, p-value,
common odds ratio, or table estimability from DP/AD counts. It then reconciles
the significant subset, summary provenance/counts, mutation spectrum, and PDF
containers. Its seven-row typed report enters the artifact, summary, and
report graph without invoking R, changing native outputs, or promoting
evidence state.
