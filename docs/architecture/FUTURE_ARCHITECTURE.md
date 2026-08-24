# Future architecture

This file records unimplemented capability boundaries. It is a backlog guard,
not current functionality, authorization, roadmap order, or evidence. The
accepted local-first design is now owned by the
[`ORCHESTRATION_CONTRACT`](../design/ORCHESTRATION_CONTRACT.md) and its
[readiness register](../design/ORCHESTRATION_READINESS.md); current system views
are organized by the [architecture index](README.md), and exact remaining open
choices remain in [`QUESTIONS.md`](../design/QUESTIONS.md).

## Principles

- Scientist-facing work should use explicit versioned requests, manifests,
  contracts, and deterministic identities.
- Functional owners remain independently understandable and testable; shared
  code follows the current dependency rules in
  [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md).
- Run, workflow-attempt, task, failure, rollback, and recovery state remains
  filesystem-first and inspectable without a special service.
- Inputs, dependencies, cleanup, repair, publication, and evidence promotion
  are never implicit.
- Local fixtures, real runtime, cluster execution, scientific review, and
  biological interpretation remain separate claims.
- A future extension model must support typed preprocessing and analyses
  without assuming one universal RNA/DNA workflow.

## Capability backlog

| Capability | Preserved boundary | Not decided or implemented |
| --- | --- | --- |
| Local YAML+TSV lifecycle | B2 implements closed request/profile/execution/lifecycle schemas plus read-only safe-YAML normalization, content identity, and deterministic reporting projection. B4 implements immutable workflow-attempt publication/finalization and read-only derived inspection. B5 adds request-to-run materialization and public dry-run-first run/resume/inspection commands. B6 adds matched structural starters and proof-matched fresh-clone onboarding. | There is no version 1 request queue or watcher. |
| Local orchestration | B3 implements the fixed local-CMH profile, fourteen-scientific-owner-rule static Snakemake graph, local executor profile, hash-bound dispatch task boundary, task-attempt publication, and content-bound verified records. B4 adds durable producer-entry ledgers, three ordered reporting rules, internal failure/interruption handling, between-task resume, and semantic completion. B5 binds the production command projection and public adapter. B6 proves separate clean-success and controlled failure/resume paths from a clean fresh clone with no-science collaborators. | Reconciliation after an entered scope fails and real science-tool execution are not implemented. |
| Site execution | Local profile semantics must remain separate from executor/site configuration and cluster evidence. | SLURM, a local VM, CSU profile, accounting, storage, modules, and scheduler-specific recovery remain deferred choices. |
| Report profiles | Preserve explicit inputs, format-neutral semantics, static deterministic rendering, transactional publication, and no evidence promotion. | Science/comprehensive names, selector, field roster, default, and multi-profile transaction. |
| Logging | Keep concise human output distinct from durable diagnostics; never alter computation, publication, recovery, evidence, or exits based on verbosity. | Controls, event schema, storage layout, stream policy, redaction, and scheduler integration. |
| Analysis extensions | Require typed inputs/outputs, dependencies, validation, provenance, failure semantics, and explicit trust level. | Profile/module schema, loader, registration, custom-analysis trust, and optional outcome policy. |
| Public acquisition | Keep reference and read acquisition separate; preserve accession/version, hashes, provenance, cache, retry, and storage identity. | Exact NCBI/SRA endpoints and later ENA/GEO/BAM scope. |
| Standalone wheel control plane | Remain thin, filesystem-first, and dependency-noninstalling; retain immutable run-bound scheduler assets. | Workflow asset distribution, source-independent execution, and release-version commitments. |
| Documentation automation | Keep owner-local context concise and mechanical checks read-only by default. | Skills, generated views, automated repair, and broader maintainer tooling. |

## Projections

- [`future_modular_pipeline.mmd`](diagrams/future_modular_pipeline.mmd)
  illustrates typed preprocessing and analysis extension.
- [`future_reporting_layer.mmd`](diagrams/future_reporting_layer.mmd)
  illustrates shared semantics across future report profiles.

These projections do not create a schema, directory, command, package,
workflow, runtime, report profile, or evidence state.

## Safety boundary

No future component may infer success or evidence promotion from output
presence, scheduler exit, logs, receipts, or rendering. Dependency restoration,
stale-lock removal, artifact/log cleanup, destructive recovery, production
publication, and biological-readiness policy remain separately authorized
capabilities.
