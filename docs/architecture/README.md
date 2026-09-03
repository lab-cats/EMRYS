# Architecture index

This directory explains the implemented system. It does not override source,
schemas, owner contracts, or validation evidence.

| Question | Authority |
| --- | --- |
| What is the current Project-to-Results system? | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| What are the scientific identities and dependency edges? | [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) |
| Which package owns each responsibility? | [`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md) |
| Which dependencies and shared seams are allowed? | [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) |
| What is the exact Run lifecycle? | [Run-coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md) |
| Which cross-cutting decisions constrain changes? | [Decision index](../design/DECISIONS.md) |
| What accepted architecture work remains? | [Findings matrix](../tasks/backlog_matrix.md) |

[`diagrams/`](diagrams/) contains supporting views. Diagrams are explanatory;
they do not prove implementation or authorize future work.
