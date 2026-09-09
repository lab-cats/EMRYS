# Durable decisions

This is the rationale index. It records why durable boundaries exist without
copying exact owner contracts, schemas, commands, or current task status.

| Subject | Decision record | Principal boundary |
|---|---|---|
| Architecture and public model | [`platform-direction.md`](decisions/platform-direction.md) | `Project -> Analysis -> Run -> Results`; Run is immutable; responsibilities flow downward; abstractions require concrete consumers and caller-complete compression. |
| Scientific pipeline | [`scientific-pipeline.md`](decisions/scientific-pipeline.md) | Biological meaning is explicit; owner science remains visible; outputs are computational candidates, not adjudicated sites. |
| Execution, evidence, and reporting | [`execution-evidence-and-reporting.md`](decisions/execution-evidence-and-reporting.md) | Mutation is explicit and fail-closed; evidence levels do not promote; reporting is downstream and read-only over admitted science. |
| Repository and delivery | [`repository-and-delivery.md`](decisions/repository-and-delivery.md) | Review complete changes, verify the final revision, give each subject one documentation home, and remove redundant maintenance. |

Exact behavior belongs to the applicable owner `CONTRACT.md`, versioned schema,
and direct tests. [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) owns
scientific identities and DAG edges;
[`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) owns import
direction. The [`findings matrix`](../tasks/backlog_matrix.md) routes accepted
work to its authoritative backlog. Live Git owns source state; checks and
retained artifacts bound to an exact revision own validation observations.
