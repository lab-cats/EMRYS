# Future architecture

This file records unimplemented capability boundaries. It is a backlog guard,
not current functionality, authorization, roadmap order, or evidence. Current
system views are organized by the [architecture index](README.md); exact open
choices remain in [`QUESTIONS.md`](../design/QUESTIONS.md).

## Principles

- Scientist-facing work should use explicit versioned requests, manifests,
  contracts, and deterministic identities.
- Functional owners remain independently understandable and testable; shared
  code follows the current dependency rules in
  [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).
- Run, attempt, scheduler, failure, rollback, and recovery state should remain
  inspectable without a special service.
- Inputs, dependencies, cleanup, repair, publication, and evidence promotion
  are never implicit.
- Local fixtures, real runtime, cluster execution, scientific review, and
  biological interpretation remain separate claims.
- A future extension model must support typed preprocessing and analyses
  without assuming one universal RNA/DNA workflow.

## Capability backlog

| Capability | Preserved boundary | Not decided or implemented |
| --- | --- | --- |
| YAML+TSV intake | A versioned request may reference the explicit sample TSV; changed inputs or policy create a new immutable run while retries create attempts. Raw inputs remain stationary. | Exact YAML fields, schemas, state paths, claim/promotion protocol, resume, archival, and optional-success rules. |
| Orchestration | Coordinate only declared DAGs, contracts, state, scheduler submissions, resume, and requested reports. Do not own scientific algorithms or install dependencies. | Engine, state layout, scheduler adapter, profiles, and public interface. |
| Report profiles | Preserve explicit inputs, format-neutral semantics, static deterministic rendering, transactional publication, and no evidence promotion. | Science/comprehensive names, selector, field roster, default, and multi-profile transaction. |
| Logging | Keep concise human output distinct from durable diagnostics; never alter computation, publication, recovery, evidence, or exits based on verbosity. | Controls, event schema, storage layout, stream policy, redaction, and scheduler integration. |
| Analysis extensions | Require typed inputs/outputs, dependencies, validation, provenance, failure semantics, and explicit trust level. | Profile/module schema, loader, registration, custom-analysis trust, and optional outcome policy. |
| Public acquisition | Keep reference and read acquisition separate; preserve accession/version, hashes, provenance, cache, retry, and storage identity. | Exact NCBI/SRA endpoints and later ENA/GEO/BAM scope. |
| Installable control plane | Remain thin, filesystem-first, and dependency-noninstalling; materialize immutable run-bound scheduler assets. | Commands, APIs, package metadata, asset distribution, and versioning commitments. |
| Documentation automation | Keep owner-local context concise and mechanical checks read-only by default. | Skills, generated views, automated repair, and broader maintainer tooling. |

## Projections

- [`future_manifest_config_contracts.mmd`](diagrams/future_manifest_config_contracts.mmd)
  illustrates the request/run/attempt distinction.
- [`future_modular_pipeline.mmd`](diagrams/future_modular_pipeline.mmd)
  illustrates typed preprocessing and analysis extension.
- [`future_reporting_layer.mmd`](diagrams/future_reporting_layer.mmd)
  illustrates shared semantics across future report profiles.

These projections do not create a schema, directory, command, package,
orchestrator, runtime, report profile, or evidence state.

## Safety boundary

No future component may infer success or evidence promotion from output
presence, scheduler exit, logs, receipts, or rendering. Dependency restoration,
stale-lock removal, artifact/log cleanup, destructive recovery, production
publication, and biological-readiness policy remain separately authorized
capabilities.
