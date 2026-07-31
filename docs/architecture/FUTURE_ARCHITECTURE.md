# Future architecture

This document describes target-state architecture and future constraints. It
does not track current branch, test, runtime, or validation status. See
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) for the approved
roadmap.

Canonical future diagrams:

- [`diagrams/future_roadmap_sequence.mmd`](diagrams/future_roadmap_sequence.mmd)
- [`diagrams/future_modular_pipeline.mmd`](diagrams/future_modular_pipeline.mmd)
- [`diagrams/future_manifest_config_contracts.mmd`](diagrams/future_manifest_config_contracts.mmd)
- [`diagrams/future_reporting_layer.mmd`](diagrams/future_reporting_layer.mmd)

## Target qualities

- explicit configuration and immutable identities;
- native compute outputs preserved behind read-only adapters;
- deterministic validation records for every pipeline step;
- reports generated only from canonical structured summaries;
- local fixtures and real-runtime evidence represented separately;
- cluster proof and scientific review represented separately;
- safe recovery without automatic deletion or repair.

## Configuration separation

A future analysis configuration may separate:

- sample metadata: what data exist;
- reference contract: which immutable reference set applies;
- partition contract: which declared loci are processed;
- analysis policy: which contrast, thresholds, orientation policy, and
  background rules apply.

This separation must preserve current CLIs and output paths until evidence
justifies migration. Filenames must not become identity.

## Validator evolution

Each current pipeline stage has one explicit validator that emits a stable
tabular record. Future validator revisions remain read-only, dry-run-first,
and stage-specific. They report failure and inconsistency rather than
repairing outputs.

A generic dispatcher or job array is not part of the target until individual
validators are proven and a concrete operational need exists.

## Reporting layer

Current stage-specific validators feed the canonical summary and report bundle
through explicit adapters. Future validator revisions and projections must not
bypass the explicit-input, table-authorization, deterministic publication, or
receipt-last contracts described in
[`ARCHITECTURE.md`](ARCHITECTURE.md).

New report projections remain projections of evidence, never evidence
generation, and require their own closed contract and transaction tests.

## Potential analysis modules

Only after stable evidence gates may Steps `07`–`09` be wrapped as a thin
RNA-editing/CMH module. Such a module must preserve:

- explicit manifests and run identity;
- existing entry-point behavior and output paths;
- dry-run and execute semantics;
- transaction and recovery contracts;
- provisional orientation language;
- independent computational and scientific states.

General core refactoring requires evidence from another real cohort.

## Deferred capabilities

The following remain intentionally deferred:

- broad shared shell or SLURM helper extraction;
- generic dispatchers and job arrays;
- targeted-rerun orchestration;
- public SRA/GEO/ENA ingestion;
- publication infrastructure;
- automatic dependency restoration;
- automatic stale-lock deletion or artifact cleanup;
- policy capable of unlocking biological readiness.

Any future capability must enter through explicit contracts and preserve
auditable evidence boundaries.
