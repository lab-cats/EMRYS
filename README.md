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

1. Read [`AGENTS.md`](AGENTS.md) and the handoff.
2. Use the commands in
   [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md).
3. Start with synthetic fixtures and dry-run mode.
4. Never treat a local pass as cluster or scientific evidence.

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
| [`QUESTIONS.md`](docs/design/QUESTIONS.md) | Open questions and resolved-question links |
| [`RUNBOOK.md`](docs/operations/RUNBOOK.md) | Setup, validation, cluster, inspection, and recovery commands |
| [`DECISIONS.md`](docs/design/DECISIONS.md) | Durable decisions and rationale |
| [`TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md) | Symptom-to-fix guidance |
| [`ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Current topology, contracts, and data flow |
| [`FUTURE_ARCHITECTURE.md`](docs/architecture/FUTURE_ARCHITECTURE.md) | Target-state design and deferred constraints |
| [`FUTURE_IMPLEMENTATION_ROADMAP.md`](docs/design/FUTURE_IMPLEMENTATION_ROADMAP.md) | Evidence-ranked refactor opportunities, prerequisites, and exit gates |
| [`DEMO_WALKTHROUGH.md`](docs/demo/DEMO_WALKTHROUGH.md) | Presentation-oriented walkthrough |
| [`PI_DEMO_REPORT.md`](docs/demo/PI_DEMO_REPORT.md) | Presentation-oriented evidence-model snapshot |

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

Each package uses a clean descendant branch, focused and complete local
validation, an implementation commit when executable behavior changes, a
separate repository-wide documentation commit, and a clean pushed gate before
another branch begins. Documentation-only packages use one documentation
commit.

Remote and cluster promotion remain upstream-sequential. See
[`AGENTS.md`](AGENTS.md) for the durable gate and
[`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md) for the approved current
lineage.
