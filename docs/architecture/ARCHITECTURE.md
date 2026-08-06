# Current architecture

This document is the conceptual view of the implemented current system. Exact
semantic identities and DAG edges belong in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md); current public
surfaces and direct protection belong in the
[`functional-owner inventory`](FUNCTIONAL_OWNER_INVENTORY.md); each owner-local
`CONTRACT.md` owns its interface, consumers, evidence, and characterized
defects. Package status and current evidence remain in
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) and
[`HANDOFF.md`](../operations/HANDOFF.md).

Canonical current diagrams:

- [`diagrams/pipeline.mmd`](diagrams/pipeline.mmd) — grouped system projection;
  it does not replace the exact DAG.
- [`diagrams/reliability.mmd`](diagrams/reliability.mmd) — publication and
  recovery principles; owner-local contracts remain exact.

## Conceptual current system

All fourteen numbered workflow, analysis, and evidence owners occupy their
final functional homes under `src/norad/`. Implemented sample-manifest
admission, artifact contracts, reporting, and reference/runtime/storage
evidence also occupy their approved cross-cutting homes. Interfaces
intentionally retained at repository level, and deferred scheduler, broader
ingestion-lifecycle, orchestration, and profile work, remain classified in the
inventory; their presence is not an unfinished flat-source migration or proof
that every target capability exists.

The supported workflow is a directed graph of explicit reference and read
inputs, per-sample alignment and BAM transformations, non-gating QC and
orientation evidence, manifest-declared cohort processing, a first-class
paired-CMH analysis, and explicit scientific-review packaging. Numeric step
labels are historical aliases, not dependency order. The exact artifact edges,
typed external inputs, fan-in, barriers, and review lineage live in the stage
map.

Functional owners remain accountable for their producers, validators,
scheduler assets, mirrored tests, and local contracts. Most SLURM entry points
delegate to parameterized implementations; the historical `00a` and `00b` embedded-
compute exceptions remain explicit in their local contracts. The login node is
not a compute engine.

| Exact question | Canonical owner |
| --- | --- |
| What is each semantic owner and what directly depends on it? | [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) |
| Where are current public commands, jobs, validators, Make surfaces, and direct tests? | [`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md) |
| What does one operation consume, publish, validate, or preserve on failure? | Its adjacent `CONTRACT.md` linked from the inventory |
| What are the durable target homes and dependency directions? | [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md) |
| How does a future direct move preserve parity and rollback? | [`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md) |

## Ownership and dependency boundaries

Cross-owner data flow uses declared artifacts and neutral contracts; a
functional owner does not import another owner's private implementation.
Current shared seams are deliberately narrow:

- `validation_report.py` owns the common validator snapshot/report/publication
  implementation, while each of the thirteen validators owns its checks and
  CLI behavior;
- `bam_validation.py` and `reference_contigs.py` own only the reviewed BAM and
  reference-parsing primitives shared by their named consumers;
- the neutral artifact schemas and validator own public structured-artifact
  contracts; and
- neutral Step `08`, Step `09`, and public review-package contracts own shared
  scientific-evidence vocabularies and validation, while algorithms, review
  policy, publication, recovery, and reporting projection remain owner-local.

These files are exact-loaded through private bridges; current placement does
not establish a package import identity, installable distribution, generic
utility layer, or permission to share a larger implementation. Reporting
reads the committed public review package through a reporting-local
projection, not the private Step `09c` implementation.

Physical placement and shared identity did not repair characterized owner-
local defects or create runtime, cluster, scientific-review, or biological-
readiness evidence.

## Identity and explicit-input boundaries

Sample, condition, order, and replicate pairing come from the declared sample
manifest. The partition manifest defines Step `07` selection. Reference,
analysis, review-plan, and evidence identities are explicit inputs.

The bounded ingestion owner validates the base manifest shape, optionally
checks declared path existence, and provides a separate paired-FASTQ
diagnostic. It does not normalize or freeze a request, manage lifecycle state,
or execute the pipeline; stricter downstream manifest refinements remain with
their consuming contracts.

Owners consume declared paths, artifacts, and receipts. They do not infer
samples, partitions, report tables, or scientific evidence from filenames,
globs, neighboring source directories, or numeric step order.

## Native publication and evidence flow

Current multi-file owners have heterogeneous transaction guarantees. Many use
validation before publication, owned locks or staging, no-clobber checks,
rollback, recovery preservation, and a receipt or summary last, but no generic
transaction contract may be inferred. Some owner-specific paths can expose a
marker before final post-publication checks return; marker presence alone does
not always prove producer success. Each local contract owns the exact behavior
and known gaps.

A transaction can be structurally complete while its evidence remains
`missing`, `failed`, `incomplete`, `unavailable`, `blocked`, or `not_run`.
Publication never promotes evidence merely because files exist.

The downstream product flow is deliberately one-way:

1. Native owners publish their declared artifacts and owner-local validation
   evidence.
2. Read-only adapters inspect an explicit inventory and publish versioned
   artifact records, an ordered index, and a receipt without altering native
   outputs or executing analysis.
3. The run-summary owner consumes one exact committed adapter receipt plus
   explicitly authorized scientific-review/report-table inputs and publishes
   canonical JSON with deterministic TSV projections.
4. Static renderers consume that canonical summary and only exact, hash- and
   policy-authorized supplemental tables.

The neutral artifact schemas and validator live under
[`src/norad/contracts/`](../../src/norad/contracts/), while the indexing,
summary, templates, styles, and renderers live under
[`src/norad/reporting/`](../../src/norad/reporting/). Exact files and direct
tests are listed in the inventory.

## Reporting and scientific boundaries

Reporting is a read-only projection. It never discovers inputs, runs analysis,
installs dependencies, changes native artifacts, or promotes computational or
scientific state. The public renderer validates explicit inputs and output
identity. The report-bundle interface attempts an atomic receipt-last selected-
format/summary-TSV publication and preserves recovery evidence when rollback
or cleanup cannot be proved complete. Format-specific layout may differ, but
state banners, authorized content, and neutral terminology remain aligned.

Reports say “CMH-ranked candidates,” not validated editing sites. Mechanical
`FWD_like` and `REV_like` labels do not assert biological strand, and
`legacy_provisional_v1` preserves a compatibility mapping rather than proving
one. `science_review_complete_exploratory` is provisional;
`biological_interpretation_ready` remains locked until a separate policy
defines and authorizes its exits.

## Operational evidence boundaries

### Runtime availability

Local restoration is explicit and opt-in; compute and validation never install
software. Runtime preflight evaluates one declared profile in an explicit
context and records availability observations. Even an all-pass batch profile
is not workflow runtime validation or cluster proof.

### Reference provenance

Reference provenance hashes and reconciles one explicit declared reference
inventory. It reports missing, malformed, or inconsistent material and never
repairs or regenerates shared references.

### Storage and retention

Storage inventory measures only declared roots and records the separate
retention-policy approval state. Approval is evidence, not an executable
instruction: the boundary never deletes, moves, archives, compresses, or
cleans data.

### Validation evidence

Owner-local validators observe explicitly declared native artifacts; they do
not repair them or rerun producers. Their exact checks, evidence strengths,
consumers, and known gaps live in the local contracts. The shared publication
implementation still does not enforce report-row order.

Artifact adapters, summaries, and reports project passing and failing evidence
without raising the runtime, cluster, scientific-review, or biological-
readiness ceiling.
