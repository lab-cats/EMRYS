# NORAD / CSU HPC RNA-seq Workflow

NORAD rebuilds a legacy Novogene Remora RNA-seq / RNA-editing workflow as
maintainable, manifest-driven research software for local development and CSU
SLURM execution.

It prepares the reference, aligns and normalizes BAMs, measures library
orientation, marks duplicates, applies `SplitNCigarReads`, separates mechanical
read orientations, performs cohort mpileup, preprocesses VCFs, and runs paired
CMH candidate ranking. See the
[current architecture](docs/architecture/ARCHITECTURE.md) for conceptual flow
and contract routes. Structured artifact, scientific-review, run-summary, and
report contracts support evidence inspection without changing native analysis
outputs; step-specific validation reports enter through explicit read-only
adapters.

## Evidence boundary

Implementation, local fixtures, real-runtime testing, cluster execution,
scientific review, and biological interpretation are distinct. Report
generation does not promote any of those states.

Candidate rows are “CMH-ranked candidates,” not validated editing sites.
Mechanical `FWD_like` and `REV_like` labels are not biological strand claims.
`biological_interpretation_ready` remains reserved unless an approved
scientific policy explicitly unlocks it.

For current status and the exact resume point, read
[`HANDOFF.md`](docs/operations/HANDOFF.md); for the package matrix, roadmap, and
lineage, read [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md).

## Minimal local start

1. Apply [`AGENTS.md`](AGENTS.md), read the
   [`task-start router`](docs/operations/TASK_START.md), and follow the selected
   card or bounded package.
2. Use the applicable [owner-local contract](src/norad/) for exact current
   behavior, the
   [engineering conventions](docs/operations/ENGINEERING_CONVENTIONS.md) for
   new or changed implementation, and
   [`RUNBOOK.md`](docs/operations/RUNBOOK.md) for supported commands.
3. Start with tiny synthetic fixtures and a supported dry-run; never treat a
   local pass as cluster or scientific evidence.

Preview a populated synthetic HTML/PDF bundle with the
[demo-report procedure](docs/operations/RUNBOOK.md#generate-the-populated-synthetic-demo-report).
It uses synthetic inputs and does not promote evidence.

Dependency restoration is an explicit setup action. Workflow scripts,
validators, renderers, and tests never install R, Quarto, system packages, or
analysis dependencies.

## Repository map

```text
scripts/        legacy workflow, validation, artifact, and report entry points
jobs/           SLURM jobs and wrapper interfaces
src/norad/      implemented neutral libraries plus colocated contracts/descriptors
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
and the [ownership map](docs/sitemap/DOCUMENTATION_OWNERSHIP.md) for audience
routes and canonical responsibility boundaries.

## Data and Git policy

Commit source, tests, configs, schemas, documentation, and tiny safe fixtures.
Do not commit FASTQ, BAM, CRAM, VCF, large result tables, logs, credentials,
tokens, private keys, restored runtimes, or environment caches.

The full runtime sample manifest and production references may be cluster-local.
Record their identity, persistence, and hashes before downstream runtime
promotion; filenames are not provenance.

## Development model

Select future work through the [`task registry`](docs/tasks/README.md).
Selection starts read-only planning and does not authorize implementation;
every task still requires live repository inspection and an approved
task-specific plan. `UNREFINED` proposals are nonselectable, while
`INTEGRATION_REVIEW` contains complete cards frozen for asynchronous canonical
integration and permits no candidate mutation.

[`TASK_DELIVERY.md`](docs/operations/TASK_DELIVERY.md#package-delivery) owns
package delivery and documentation-impact procedure; exact validation commands
remain in the [`RUNBOOK.md`](docs/operations/RUNBOOK.md#local-validation-gate).

Concurrent candidates remain isolated proposals. Accepted integration and final
validation are serialized under
[`CONCURRENT_WORK.md`](docs/operations/CONCURRENT_WORK.md); live lanes remain in
[`HANDOFF.md`](docs/operations/HANDOFF.md).

Remote and cluster promotion remain upstream-sequential under the
[delivery procedure](docs/operations/TASK_DELIVERY.md#package-delivery) and
current [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md) lineage.
