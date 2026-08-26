# Documentation sitemap

This is the category route and canonical documentation ownership map. Each
mutable fact has one live owner. Repeat safety guidance only where a reader
acts; otherwise route rather than copy current state, commands, contracts, or
evidence. The documentation gate checks structural ownership mechanically;
the routes below explain the human boundaries.

- [Architecture](../architecture/) — current structure, contracts, owner
  inventory, diagrams, and one visibly marked legacy future source pending
  `DOC-03`.
- [Design](../design/) — decisions, application contracts, test policy, and
  visibly marked legacy planning sources pending `DOC-03`/`DOC-05`.
- [Operations](../operations/) — workflow, cross-cutting commands,
  troubleshooting, and visibly marked legacy evidence/test-plan sources
  pending `DOC-04`/`DOC-05`.
- [Reference](../reference/) — terminology that routes back to canonical
  subject owners.
- [Tasks](../tasks/README.md) — canonical planning matrix, temporary unsliced
  architecture context, provisional architecture ranking, and disposition
  rules.
- [Demonstrations](../demo/README.md) — reviewed presenter guides.
- [History](../history/) — immutable dated records maintained separately.

For task orientation and approved delivery, use
[`WORKFLOW.md`](../operations/WORKFLOW.md). For repository-wide structure, run
`make -s documentation-check`.

## Audience routes

| Audience | Start | Continue |
| --- | --- | --- |
| User | [Root README](../../README.md) | [Scientist-facing workflow](../architecture/ARCHITECTURE.md#scientist-facing-workflow) |
| Operator | [Runbook](../operations/RUNBOOK.md) | Owner README, [troubleshooting](../operations/TROUBLESHOOTING.md), and checks/artifacts for the exact commit |
| Scientist/reviewer | [Architecture index](../architecture/README.md) | Stage map, owner contracts, findings matrix, and test baseline |
| Maintainer | [Safety guard](../../AGENTS.md) | [Workflow](../operations/WORKFLOW.md), selected matrix item or approved objective, and affected owners |
| Auditor/historian | [History](../history/) | Dated evidence and test-baseline recheck routes |

## Canonical roles

| Subject | Owner |
| --- | --- |
| Product entrypoint and repository map | Root [`README.md`](../../README.md) |
| Safety, context selection, and development procedure | [`AGENTS.md`](../../AGENTS.md) and [`WORKFLOW.md`](../operations/WORKFLOW.md) |
| Checkout state and validation observations | Live Git plus checks and retained artifacts bound to the exact commit |
| Accepted work, status, and acceptance | [`backlog_matrix.md`](../tasks/backlog_matrix.md) |
| Cross-cutting commands and common recovery | [`RUNBOOK.md`](../operations/RUNBOOK.md) and [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| System-view routing and exact architecture | [Architecture index](../architecture/README.md) and its named children |
| Local-pilot lifecycle and owner admission | [`ORCHESTRATION_CONTRACT.md`](../design/ORCHESTRATION_CONTRACT.md), owner contracts, workflow profile, stage map, and tests |
| Durable rationale and unsliced campaign alternatives | [`DECISIONS.md`](../design/DECISIONS.md), its detail files, the temporary [`architecture_campaign.md`](../tasks/architecture_campaign.md), and the temporary [`performance_campaign.md`](../tasks/performance_campaign.md) |
| Exact behavior, commands, defects, and tests | Applicable colocated owner `README.md` and `CONTRACT.md` |
| Test policy and cross-cutting recheck routes | [`TEST_BASELINE.md`](../design/TEST_BASELINE.md); exact defects remain with the applicable owner `README.md` or `CONTRACT.md` |
| Current planning backlog and temporary unsliced campaign context | [Findings matrix](../tasks/backlog_matrix.md), [architecture campaign](../tasks/architecture_campaign.md), [provisional architecture ranking](../tasks/architecture_backlog_matrix.md), [performance campaign](../tasks/performance_campaign.md), [provisional performance ranking](../tasks/performance_backlog_matrix.md), and [task-planning rules](../tasks/README.md) |
| Dated planning and evidence records | Git history and [`docs/history`](../history/); neither owns current state or requirements |

Historical planning detail is not a live subject-matter owner. Before deleting
any live owner, retain its operative contract, safety rule, defect, or evidence
ceiling in the destination and update the matrix disposition in the same
package.
