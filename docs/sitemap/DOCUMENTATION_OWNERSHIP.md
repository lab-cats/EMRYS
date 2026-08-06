# Documentation ownership

Each mutable fact has one canonical live owner. Documents may repeat a safety
warning where a reader acts, but otherwise link instead of copying state,
commands, contracts, or evidence.

## Audience routes

| Audience | Start | Continue |
| --- | --- | --- |
| User | [Root README](../../README.md) | [Pipeline overview](../architecture/PIPELINE_OVERVIEW.md) |
| Operator | [Handoff](../operations/HANDOFF.md) | [Runbook](../operations/RUNBOOK.md) and [troubleshooting](../operations/TROUBLESHOOTING.md) |
| Scientist or reviewer | [Current architecture](../architecture/ARCHITECTURE.md) | [Stage map](../../src/norad/contracts/STAGE_MAP.md), owner-local contracts, [questions](../design/QUESTIONS.md), and [test baseline](../design/TEST_BASELINE.md) |
| Maintainer | [Agent rules](../../AGENTS.md) | [Task start](../operations/TASK_START.md), the selected [card](../tasks/README.md), and directly affected owners |
| Auditor or historian | [History index](../history/) | [Refactor audit](../design/REFACTOR_AUDIT.md) and [test baseline](../design/TEST_BASELINE.md) for current recheck routes |

## Canonical owners

| Information | Owner |
| --- | --- |
| Automatically loaded approval, safety, evidence, and routing rules | [`AGENTS.md`](../../AGENTS.md) |
| Product identity, configured-environment start, and repository map | [`README.md`](../../README.md) |
| Immediate priorities | [`TODO.md`](../../TODO.md) |
| Documentation categories and ownership | [`TOP_LEVEL.md`](TOP_LEVEL.md) and this file |
| Current blockers, evidence ceilings, and non-reconstructable takeover facts | [`HANDOFF.md`](../operations/HANDOFF.md) |
| Supported commands and operator procedures | [`RUNBOOK.md`](../operations/RUNBOOK.md) |
| Symptom diagnosis and recovery | [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| Task orientation and delivery | [`TASK_START.md`](../operations/TASK_START.md), [`TASK_DELIVERY.md`](../operations/TASK_DELIVERY.md), and the [task registry](../tasks/README.md) |
| Durable rationale | [`DECISIONS.md`](../design/DECISIONS.md) and its topic files |
| Open choices | [`QUESTIONS.md`](../design/QUESTIONS.md) |
| Pipeline status and package acceptance | [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) |
| Implemented conceptual topology | [`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) |
| Target architecture | [`FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md) |
| Exact functional surfaces | [`FUNCTIONAL_OWNER_INVENTORY.md`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md) |
| Exact semantic identities and DAG edges | [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) |
| Allowed source homes and dependency direction | [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md) |
| Exact runtime, evidence, and scientific contracts | The applicable colocated `CONTRACT.md` |
| Current test policy and recheck routes | [`TEST_BASELINE.md`](../design/TEST_BASELINE.md) |
| Current refactor defects and recheck triggers | [`REFACTOR_AUDIT.md`](../design/REFACTOR_AUDIT.md) |
| Immutable dated records | [`docs/history/`](../history/) |
| Actionable work and preserved rough proposals | [`docs/tasks/`](../tasks/README.md) |

## Boundaries

Live canonical documents must have valid local links and one current owner per
fact. Before deleting a live owner, retain any still-operative contract,
defect, safety rule, or evidence ceiling in its destination.

Task cards are temporary and are deleted on completion; their old contents and
paths remain recoverable from Git. Surviving cards are not rewritten merely
because a referenced completed card disappeared. `docs/history` is immutable
archive material and is maintained in a separate task, so its old local links
are not repaired during live-document compression.
