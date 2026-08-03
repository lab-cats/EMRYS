# Current architecture

This document owns the current system topology, component boundaries,
contracts, and data flow. Status and branch lineage belong in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); current evidence
belongs in [`../operations/HANDOFF.md`](../operations/HANDOFF.md).

Canonical diagrams:

- [`diagrams/pipeline.mmd`](diagrams/pipeline.mmd)
- [`diagrams/reliability.mmd`](diagrams/reliability.mmd)

## Compute pipeline

Current public workflow entry points use a mixed physical layout. The neutral
validation-report library, the `construct_STAR_index` job and validator, and the
`convert_GTF_to_BED12` producer, validator, and job now live under `src/norad/`;
remaining workflow entry points stay under `scripts/` and `jobs/`. Other
colocated functional-owner documents under `src/norad/` remain contracts rather
than claims that their implementations have migrated.

The supported workflow is a directed graph of shared reference inputs,
per-sample alignment and BAM transformations, non-gating QC/orientation
evidence branches, manifest-declared cohort processing, a first-class analysis,
and explicit scientific-review packaging. The exact semantic identities,
historical aliases, direct artifact edges, typed external inputs, and barrier
semantics have one owner in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md). The current executable
diagram remains [`diagrams/pipeline.mmd`](diagrams/pipeline.mmd).

Most numbered SLURM entry points delegate functional work to parameterized
scripts; the historical `00a` and `00b` embedded-compute exceptions remain
recorded in their colocated contracts. The login node is not a compute engine.

### Functional-owner contract index

The exact public-entrypoint and cross-cutting-domain coverage roster is
[`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md).
Target source/test ownership and future direct-migration mechanics live in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md) and
[`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md),
not in this implemented-current-topology document.

### Neutral validation-report library

[`validation_report.py`](../../src/norad/libraries/validation_report.py) owns
the shared snapshot, seven-column rendering/validation, and transactional
publication protocol used by all thirteen validator entry points. The final
`construct_STAR_index` and `convert_GTF_to_BED12` validators and eleven
remaining `scripts/` validators resolve that exact file through private
caller-local loaders; no package marker, public Python import identity, install
step, compatibility wrapper, or `sys.path` mutation is part of the current
interface. Stage-specific parsing and check rosters remain with their
functional owners.

This relocation preserved the characterized snapshot, ordering, collision,
rollback, cleanup, descriptor, and lock defects. It did not correct them or
promote runtime, cluster, scientific-review, or biological evidence.

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
implementation lives in the neutral validation-report library and is loaded by
all thirteen validators through exact-file private bridges. Current shared
publication still does not enforce report-row order.

Typed adapters, artifact indexing, canonical-summary assembly, and reporting
project both passing and failing validation evidence without promoting
runtime, cluster, scientific-review, or biological-readiness state.
