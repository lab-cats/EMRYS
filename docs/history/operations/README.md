# Operations history

This mutable index links immutable dated delivery and coordination records.
Historical operations records preserve observed branch lineage, completed
handoffs, and frozen lane identities. Current checkout, lanes, blockers,
evidence, and resume state remain in
[`HANDOFF.md`](../../operations/HANDOFF.md); current roadmap, status,
acceptance, and required delivery lineage remain in
[`PIPELINE_PLAN.md`](../../design/PIPELINE_PLAN.md).

## Records

| Frozen date | Record | Provenance and boundary |
| --- | --- | --- |
| 2026-08-03 | [Refactor delivery and branch lineage](2026-08-03-refactor-delivery-and-branch-lineage.md) | Exact source snapshot `9cb4bb8`; completed delivery, recovery, synthetic-exchange, and legacy branch-lineage facts only. Current state remains in the live owners above. |
