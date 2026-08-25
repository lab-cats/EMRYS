# Architecture index

This is the authoritative organizer for EMRYS system documentation. It owns
only the boundary between views; implementation and scientific detail remain
with the relevant child and functional owner.

| Question | Authority |
| --- | --- |
| What system is implemented now? | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| How does a scientist understand the workflow? | [Scientist-facing workflow](ARCHITECTURE.md#scientist-facing-workflow) and [`current_user_pipeline.mmd`](diagrams/current_user_pipeline.mmd) |
| Which public programs, jobs, validators, and tests exist? | [`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md) |
| What are the semantic identities and artifact edges? | [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) |
| Which source dependencies and shared seams are allowed? | [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) |
| How is the implemented source-checkout local pilot designed? | [`ORCHESTRATION_CONTRACT.md`](../design/ORCHESTRATION_CONTRACT.md), workflow profile, stage map, owner contracts/tests, and [`local_pilot_orchestration.mmd`](diagrams/local_pilot_orchestration.mmd) |
| What accepted work remains? | [`backlog_matrix.md`](../tasks/backlog_matrix.md) |
| Where are unsliced architecture alternatives preserved? | Temporary [`architecture_campaign.md`](../tasks/architecture_campaign.md) |
| What are the exact local interfaces and defects? | The applicable owner `README.md` and `CONTRACT.md` |

The detailed current system, user pipeline, and reliability projections remain
in [`diagrams/`](diagrams/). Diagrams do not override contracts, prove
implementation, or authorize future work.
