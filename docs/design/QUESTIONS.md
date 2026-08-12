# Open questions

This is the concise backlog of unresolved evidence and design decisions. It
does not authorize implementation. Current blockers and evidence ceilings
remain in [`HANDOFF.md`](../operations/HANDOFF.md); durable answers move to
[`DECISIONS.md`](DECISIONS.md) or the applicable contract.

## Operational and scientific evidence

| Domain | Still unresolved |
| --- | --- |
| Production manifest | Durable location and ownership of the immutable six-row runtime manifest, explicit replicate values, hash, and retention. |
| CSU runtime | Batch-visible R/namespaces, hash utilities, exact tool paths, and Java 17 availability across eligible nodes. |
| Storage | Home/project/scratch capacity, large temporary/intermediate placement, and approved native/derived retention. |
| Reference | Exact Novogene annotation release and FASTA/FAI/DICT/GTF/BED/STAR contig agreement, including mitochondrial naming. |
| Runtime promotion | Real-bcftools Step `07` parity, partition-scale resources, and required evidence before Steps `08`–`09c`. |
| Scientific policy | Orthogonal orientation evidence and the annotation, statistical, replicate, sensitivity, adjudication, and limitation exits for any biological-readiness policy. |

## Design choices

| Choice | Decision needed | Owner/deadline |
| --- | --- | --- |
| `CHOICE-REPORT-01`–`03` | Public profile names/selector, science field roster, and profile output/transaction boundary. | `RPT-02`, before `RPT-03` planning. |
| `CHOICE-GATE-REC-01` | Validation catalog/receipt schema, subject identity, storage, retention, compatibility, privacy, and invalidation. | `GATE-REC-01`, before receipt implementation. |
| `CHOICE-SITE-01` | Whether scheduler proof should begin on CSU or in a reproducible single-node Linux VM, plus the exact SLURM executor, accounting, storage, module, and recovery profile. | `FUT-SITE-01`, only after the local pilot is proven. |
| `CHOICE-SKILL-01` | Supported documentation-health skill name, scope, and discovery/install location. | [`DOC-SKILL-10`](../tasks/BACKLOG.md#doc-skill-10--build-documentation-health-skill), before scaffolding. |
| `CHOICE-ANALYSIS-01` | Trust, registration, validation, provenance, dependencies, reports, and evidence for exploratory versus built-in analyses. | `FUT-ANALYSIS-01`, before a registry/prototype. |
| `CHOICE-DATA-01` | First version-pinned NCBI reference and SRA read interfaces, cache, and resumable transfer. | `FUT-DATA-02`, before acquisition implementation. |
| `CHOICE-CONTROL-01` | Public commands/APIs, non-Python assets, immutable job materialization, packaging, and versioning. | `FUT-CLI-03`, before an installable prototype. |
| `CHOICE-SUCCESS-01` | Required/optional outcome, retry, reporting, and request-metadata archival semantics. | `FUT-SUCCESS-04`, before optional modules execute. |
| `CHOICE-EPIC-01` | Stable epic IDs and single/multiple navigation membership. | `TASK-EPIC-01`, before its planning. |

Recommendations and detailed designs belong in the owning card's approved
planning, not in this global backlog.
