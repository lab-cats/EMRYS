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
2. Apply the neutral
   [`engineering conventions`](docs/operations/ENGINEERING_CONVENTIONS.md) for
   new or changed implementation and the applicable owner-local contract for
   exact current behavior.
3. Use the commands in
   [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md).
4. Start with synthetic fixtures and dry-run mode.
5. Never treat a local pass as cluster or scientific evidence.

To preview a populated synthetic HTML/PDF bundle, use the
[demo-report procedure](docs/operations/RUNBOOK.md#generate-the-populated-synthetic-demo-report).
It exercises the report path without production inputs or evidence promotion.

Dependency restoration is an explicit setup action. Workflow scripts,
validators, renderers, and tests never install R, Quarto, system packages, or
analysis dependencies.

## Repository map

```text
scripts/        workflow, validation, artifact, and report entry points
  git_orchestration/  tested operator safeguards for exact Git integration
jobs/           SLURM jobs and wrapper interfaces
tests/          active Python, shell, R, and fixture tests
tests/pending/  non-runnable future test plans
configs/        example manifests and explicit contracts
schemas/        versioned public artifact/report JSON Schemas
reports/        static report source and style
docs/           architecture, design, operations, and demo material
docs/tasks/     bounded future task cards organized by lifecycle status
results/        ignored generated outputs
logs/           ignored runtime logs
```

## Documentation map

Use the [documentation sitemap](docs/sitemap/README.md) for top-level categories
and the [ownership map](docs/sitemap/DOCUMENTATION_OWNERSHIP.md) for short user,
operator, scientist, maintainer, and historical routes. Those maps link the
canonical documents and Mermaid sources without reproducing their contents.

## Data and Git policy

Commit source, tests, configs, schemas, documentation, and tiny safe fixtures.
Do not commit FASTQ, BAM, CRAM, VCF, large result tables, logs, credentials,
tokens, private keys, restored runtimes, or environment caches.

The full runtime sample manifest and production references may be
cluster-local. Their identity, persistence, and hashes must be explicitly
recorded before downstream runtime promotion; filenames are not provenance.

## Development model

The [`task-delivery procedure`](docs/operations/TASK_DELIVERY.md#package-delivery)
owns branch, implementation, validation, documentation-impact, commit, and
publication order. Exact validation commands remain in the
[`runbook`](docs/operations/RUNBOOK.md#local-validation-gate).

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

Remote and cluster promotion remain upstream-sequential. See the
[`task-delivery procedure`](docs/operations/TASK_DELIVERY.md#package-delivery)
for the durable gate and
[`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md) for the approved current
lineage.
