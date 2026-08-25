# Open questions

> **Legacy transition source — not a current backlog or decision authority.**
> Accepted outcomes live in the [findings matrix](../tasks/backlog_matrix.md)
> and unsliced architecture alternatives in the temporary
> [architecture campaign](../tasks/architecture_campaign.md). This file remains
> only for the `DOC-03` preservation and retirement trace.

This legacy index does not authorize implementation. Accepted open outcomes
and evidence requirements live in the
[findings matrix](../tasks/backlog_matrix.md); durable answers move to
[`DECISIONS.md`](DECISIONS.md) or the applicable contract.

## Operational and scientific evidence

| Domain | Still unresolved |
| --- | --- |
| Production manifest | Durable location and ownership of the immutable six-row runtime manifest, explicit replicate values, hash, and retention. |
| CSU runtime | Batch-visible R/namespaces, hash utilities, exact tool paths, and Java 17 availability across eligible nodes. |
| Storage | Home/project/scratch capacity, large temporary/intermediate placement, and approved native/derived retention. |
| Reference | Exact Novogene annotation release and FASTA/FAI/DICT/GTF/BED/STAR contig agreement, including mitochondrial naming. |
| Runtime promotion | Real-bcftools Step `07` parity, partition-scale resources, and required evidence before computational Steps `08`–`09`. |
| External research process | Where researchers will keep orientation, annotation, sensitivity, replicate-consistency, candidate-adjudication, and limitation records outside EMRYS. |

## Design choices

This table lists only questions routed to active findings-matrix items.
Questions owned solely by discarded predecessor proposals remain in Git
history rather than forming a shadow backlog.

| Choice | Decision needed | Owner/deadline |
| --- | --- | --- |
| `CHOICE-SITE-01` | Exact SLURM executor, accounting, storage, module, and recovery profile for institutional runtime support. | `RUNTIME-01` and `DOCTOR-01`, before accepting the site runtime path. |
| `CHOICE-ANALYSIS-01` | Trust, registration, validation, provenance, dependencies, reports, and evidence for exploratory versus built-in analyses. | `ANALYSIS-01` and `ANALYSIS-02`, before a library or alternate cohort analysis is accepted. |
| `CHOICE-DATA-01` | First version-pinned NCBI reference and SRA read interfaces, cache, and resumable transfer. | `FUT-DATA-02`, before acquisition implementation. |
| `CHOICE-CONTROL-01` | Public commands/APIs, non-Python assets, immutable job materialization, packaging, and versioning. | `CONTROL-01`, `CONFIG-01`, `OPS-01`, and `OPS-02`, before the accepted public-control redesign. |

Recommendations and detailed designs belong with the owning matrix item and
its routed campaign context, not in this question index.
