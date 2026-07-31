# NORAD / CSU HPC RNA-seq Workflow

NORAD rebuilds a legacy Novogene Remora RNA-seq / RNA-editing workflow as
maintainable, manifest-driven research software for local development and CSU
SLURM execution.

The workflow prepares the reference, aligns and normalizes BAMs, measures
library orientation, marks duplicates, applies `SplitNCigarReads`, separates
mechanical read orientations, performs cohort mpileup, preprocesses VCFs, and
runs paired CMH candidate ranking. Structured artifact, scientific-review,
run-summary, and report contracts support explicit evidence inspection without
changing native analysis outputs. Step-specific validation reports enter that
evidence path through explicit read-only adapters.

## Evidence boundary

The repository deliberately separates implementation, local fixtures,
real-runtime testing, cluster execution, scientific review, and biological
interpretation. Report generation does not promote any of those states.

Candidate rows are “CMH-ranked candidates,” not validated editing sites.
Mechanical `FWD_like` and `REV_like` labels are not biological strand claims.
`biological_interpretation_ready` remains reserved unless an approved
scientific policy explicitly unlocks it.

For the verified current status and exact resume point, read
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md). For the
authoritative step/package matrix and descendant roadmap, read
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md).

## Minimal local start

1. Apply [`AGENTS.md`](AGENTS.md), read the concise
   [`task-start router`](docs/operations/TASK_START.md), and follow the selected
   card to the applicable current-state and canonical sections.
2. Use the commands in
   [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md).
3. Start with synthetic fixtures and dry-run mode.
4. Never treat a local pass as cluster or scientific evidence.

To preview a populated synthetic HTML/PDF bundle, use the
[demo-report procedure](docs/operations/RUNBOOK.md#generate-the-populated-synthetic-demo-report).
It exercises the report path without production inputs or evidence promotion.

Dependency restoration is an explicit setup action. Workflow scripts,
validators, renderers, and tests never install R, Quarto, system packages, or
analysis dependencies.

## Repository map

```text
scripts/        workflow, validation, artifact, and report entry points
jobs/           SLURM wrappers
tests/          active Python, shell, R, and fixture tests
configs/        example manifests and explicit contracts
schemas/        versioned public artifact/report JSON Schemas
reports/        static report source and style
docs/           architecture, design, operations, and demo material
docs/tasks/     bounded future task cards organized by lifecycle status
results/        ignored generated outputs
logs/           ignored runtime logs
```

## Documentation map

| Document | Use it for |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Stable repository conduct and development gates |
| [`TODO.md`](TODO.md) | Short prioritized pending work |
| [`HANDOFF.md`](docs/operations/HANDOFF.md) | Current branch, evidence boundary, blockers, and resume point |
| [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md) | Authoritative roadmap, status matrix, and acceptance criteria |
| [`REFACTOR_AUDIT.md`](docs/design/REFACTOR_AUDIT.md) | Evidence-ranked refactor findings, risks, and retained boundaries |
| [`TEST_BASELINE.md`](docs/design/TEST_BASELINE.md) | Measured Python baseline and public-contract risk-to-test traceability |
| [`QUESTIONS.md`](docs/design/QUESTIONS.md) | Open questions and resolved-question links |
| [`RUNBOOK.md`](docs/operations/RUNBOOK.md) | Setup, validation, cluster, inspection, and recovery commands |
| [`TASK_START.md`](docs/operations/TASK_START.md) | Minimum task-start context, freshness rules, and canonical routing |
| [`CONCURRENT_WORK.md`](docs/operations/CONCURRENT_WORK.md) | Isolated lane roles, write authority, coupling, handoff, and serialized integration |
| [`DECISIONS.md`](docs/design/DECISIONS.md) | Durable decisions and rationale |
| [`TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md) | Symptom-to-fix guidance |
| [`ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Current topology, contracts, and data flow |
| [`FUTURE_ARCHITECTURE.md`](docs/architecture/FUTURE_ARCHITECTURE.md) | Target-state design and deferred constraints |
| [`docs/tasks/`](docs/tasks/) | One bounded card per future task, with scope, dependencies, and acceptance evidence |
| [`DEMO_WALKTHROUGH.md`](docs/demo/DEMO_WALKTHROUGH.md) | Presentation-oriented walkthrough |
| [`PI_DEMO_REPORT.md`](docs/demo/PI_DEMO_REPORT.md) | Dated evidence snapshot for discussion |

Canonical Mermaid sources live under
[`docs/architecture/diagrams/`](docs/architecture/diagrams/). Architecture
documents link to those files instead of maintaining inline copies.

## Data and Git policy

Commit source, tests, configs, schemas, documentation, and tiny safe fixtures.
Do not commit FASTQ, BAM, CRAM, VCF, large result tables, logs, credentials,
tokens, private keys, restored runtimes, or environment caches.

The full runtime sample manifest and production references may be
cluster-local. Their identity, persistence, and hashes must be explicitly
recorded before downstream runtime promotion; filenames are not provenance.

## Development model

Each package uses a clean descendant branch, focused and complete applicable
local validation, an implementation commit when executable behavior changes,
a separate impact-directed documentation commit, and a clean pushed gate
before another branch begins. Documentation-only packages use one
documentation commit and no computational suite when the complete diff has no
executable or test-affecting consumer.

Future work is selected from the
[`task registry`](docs/tasks/README.md). Moving a card to `IN_PROGRESS` begins
task-specific read-only planning; it does not authorize implementation. Every
card still requires live repository inspection, an approved plan, bounded
execution, and inspected acceptance evidence.

Approved work may be authored in isolated candidate worktrees, including
multiple disjoint documentation/card sidecars beside at most one
implementation or immutable-execution lane. Candidate state remains a proposal;
accepted integration and validation are serialized under
[`CONCURRENT_WORK.md`](docs/operations/CONCURRENT_WORK.md).
The required first-use strategy discussion is recorded complete; current lane
state and candidate disposition remain in
[`HANDOFF.md`](docs/operations/HANDOFF.md). That milestone does not select,
accept, or authorize candidate work.

Remote and cluster promotion remain upstream-sequential. See
[`AGENTS.md`](AGENTS.md) for the durable gate and
[`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md) for the approved current
lineage.
