# Documentation sitemap

This is the category route and canonical documentation ownership map. Each
mutable fact has one live owner. Repeat safety guidance only where a reader
acts; otherwise route rather than copy current state, commands, contracts, or
evidence. The documentation gate checks structural ownership mechanically;
the routes below explain the human boundaries.

- [Architecture](../architecture/) — current and future structure, contracts,
  owner inventory, and diagrams.
- [Design](../design/) — decisions, current plan, questions, application
  contracts, and test policy.
- [Operations](../operations/) — workflow, handoff, cross-cutting commands, and
  troubleshooting.
- [Reference](../reference/) — terminology that routes back to canonical
  subject owners.
- [Tasks](../tasks/README.md) — current planning matrix, temporary unsliced
  architecture context, and frozen legacy registry/cards during transition.
- [Demonstrations](../demo/README.md) — reviewed presenter guides.
- [History](../history/) — immutable dated records maintained separately.

For task orientation and approved delivery, use
[`WORKFLOW.md`](../operations/WORKFLOW.md). For repository-wide structure, run
`make -s documentation-check`.

## Audience routes

| Audience | Start | Continue |
| --- | --- | --- |
| User | [Root README](../../README.md) | [Scientist-facing workflow](../architecture/ARCHITECTURE.md#scientist-facing-workflow) |
| Operator | [Runbook](../operations/RUNBOOK.md) | Owner README, [troubleshooting](../operations/TROUBLESHOOTING.md), and the legacy [handoff](../operations/HANDOFF.md) only after live verification pending `DOC-02` |
| Scientist/reviewer | [Architecture index](../architecture/README.md) | Stage map, owner contracts, questions, and test baseline |
| Maintainer | [Safety guard](../../AGENTS.md) | [Workflow](../operations/WORKFLOW.md), selected card, and affected owners |
| Auditor/historian | [History](../history/) | Dated evidence and test-baseline recheck routes |

## Canonical roles

| Subject | Owner |
| --- | --- |
| Product entrypoint and repository map | Root [`README.md`](../../README.md) |
| Safety, context selection, and development procedure | [`AGENTS.md`](../../AGENTS.md) and [`WORKFLOW.md`](../operations/WORKFLOW.md) |
| Legacy evidence/blocker and roadmap/acceptance inputs pending audit | [`HANDOFF.md`](../operations/HANDOFF.md) and [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); user-identified as stale and unverified pending `DOC-02` |
| Cross-cutting commands and common recovery | [`RUNBOOK.md`](../operations/RUNBOOK.md) and [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| System-view routing and exact architecture | [Architecture index](../architecture/README.md) and its named children |
| Future local-pilot lifecycle and owner admission | [`ORCHESTRATION_CONTRACT.md`](../design/ORCHESTRATION_CONTRACT.md) and [`ORCHESTRATION_READINESS.md`](../design/ORCHESTRATION_READINESS.md) |
| Durable rationale and unresolved choices | [`DECISIONS.md`](../design/DECISIONS.md), its detail files, and [`QUESTIONS.md`](../design/QUESTIONS.md) |
| Exact behavior, commands, defects, and tests | Applicable colocated owner `README.md` and `CONTRACT.md` |
| Test policy and cross-cutting recheck routes | [`TEST_BASELINE.md`](../design/TEST_BASELINE.md); exact defects remain with the applicable owner `README.md` or `CONTRACT.md` |
| Current planning backlog and temporary unsliced architecture context | [Findings matrix](../tasks/backlog_matrix.md), [architecture campaign](../tasks/architecture_campaign.md), and [task transition rules](../tasks/README.md) |
| Legacy task registry/cards and dated records | Frozen [`BACKLOG.md`](../tasks/BACKLOG.md), [`cards/`](../tasks/cards/), and [`docs/history`](../history/) pending the separately tracked backlog cutover |

JIT cards and history are not live subject-matter owners. Delete completed or
retired JIT detail, but remove or replace every dependent backlog edge in the
same package. Before deleting any live owner, retain its operative contract,
safety rule, defect, or evidence ceiling in the destination.
