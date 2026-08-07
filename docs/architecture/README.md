# Architecture index

This is the authoritative organizer for NORAD system documentation. It owns
only the boundary between views; implementation and scientific detail remain
with the relevant child and functional owner.

| Question | Authority |
| --- | --- |
| What system is implemented now? | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| How does a scientist understand the workflow? | [`PIPELINE_OVERVIEW.md`](PIPELINE_OVERVIEW.md) and [`current_user_pipeline.mmd`](diagrams/current_user_pipeline.mmd) |
| Which public programs, jobs, validators, and tests exist? | [`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md) |
| What are the semantic identities and artifact edges? | [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) |
| Which source dependencies and shared seams are allowed? | [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md) |
| What remains unimplemented? | [`FUTURE_ARCHITECTURE.md`](FUTURE_ARCHITECTURE.md) and its three future diagrams |
| What are the exact local interfaces and defects? | The applicable owner `README.md` and `CONTRACT.md` |

The detailed current system, user pipeline, reliability, and future projections
remain in [`diagrams/`](diagrams/). Diagrams explain their named view; they do
not override contracts, prove implementation, or authorize future work.
