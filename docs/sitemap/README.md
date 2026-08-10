# Documentation sitemap

This is the category route and canonical documentation ownership map. Each
mutable fact has one live owner. Repeat safety guidance only where a reader
acts; otherwise route rather than copy current state, commands, contracts, or
evidence. The documentation gate checks structural ownership mechanically;
the routes below explain the human boundaries.

- [Architecture](../architecture/) — current and future structure, contracts,
  owner inventory, and diagrams.
- [Design](../design/) — decisions, current plan, questions, audit routes, and
  test policy.
- [Operations](../operations/) — workflow, handoff, cross-cutting commands, and
  troubleshooting.
- [Tasks](../tasks/README.md) — compact actionable/proposal backlog and
  temporary JIT execution cards.
- [Demonstrations](../demo/README.md) — reviewed presenter guides.
- [History](../history/) — immutable dated records maintained separately.

For task orientation and approved delivery, use
[`WORKFLOW.md`](../operations/WORKFLOW.md). For repository-wide structure, run
`make -s documentation-check`.

## Audience routes

| Audience | Start | Continue |
| --- | --- | --- |
| User | [Root README](../../README.md) | [Scientist-facing workflow](../architecture/ARCHITECTURE.md#scientist-facing-workflow) |
| Operator | [Handoff](../operations/HANDOFF.md) | [Runbook](../operations/RUNBOOK.md), owner README, and [troubleshooting](../operations/TROUBLESHOOTING.md) |
| Scientist/reviewer | [Architecture index](../architecture/README.md) | Stage map, owner contracts, questions, and test baseline |
| Maintainer | [Safety guard](../../AGENTS.md) | [Workflow](../operations/WORKFLOW.md), selected card, and affected owners |
| Auditor/historian | [History](../history/) | Dated evidence and test-baseline recheck routes |

## Canonical roles

| Subject | Owner |
| --- | --- |
| Product entrypoint and repository map | Root [`README.md`](../../README.md) |
| Safety, context selection, and development procedure | [`AGENTS.md`](../../AGENTS.md) and [`WORKFLOW.md`](../operations/WORKFLOW.md) |
| Current evidence/blockers and roadmap/acceptance | [`HANDOFF.md`](../operations/HANDOFF.md) and [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) |
| Cross-cutting commands and common recovery | [`RUNBOOK.md`](../operations/RUNBOOK.md) and [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| System-view routing and exact architecture | [Architecture index](../architecture/README.md) and its named children |
| Durable rationale and unresolved choices | [`DECISIONS.md`](../design/DECISIONS.md), its detail files, and [`QUESTIONS.md`](../design/QUESTIONS.md) |
| Exact behavior, commands, defects, and tests | Applicable colocated owner `README.md` and `CONTRACT.md` |
| Test policy and cross-cutting recheck routes | [`TEST_BASELINE.md`](../design/TEST_BASELINE.md); exact defects remain with the applicable owner `README.md` or `CONTRACT.md` |
| Actionable work, proposals, and dated records | Compact [`BACKLOG.md`](../tasks/BACKLOG.md), selected [`cards/`](../tasks/cards/), and [`docs/history`](../history/) respectively |

JIT cards and history are not live subject-matter owners. Delete completed or
retired JIT detail, but remove or replace every dependent backlog edge in the
same package. Before deleting any live owner, retain its operative contract,
safety rule, defect, or evidence ceiling in the destination.
