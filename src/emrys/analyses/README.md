# Analysis modules

An Analysis selected in `project.yaml` consumes admitted processing artifacts
inside the immutable Run machinery; it is not a second workflow engine. The
built-in [`paired_cmh_candidate_ranking/`](paired_cmh_candidate_ranking/README.md)
owner includes the bounded
[`scientific_context_projection/`](paired_cmh_candidate_ranking/scientific_context_projection/README.md).

External computation providers use the standard `emrys.analysis_modules`
Python entry-point group. EMRYS admits the exact provider ID, version,
configuration schema and normalized scientific configuration, implementation
bytes, declared inputs/outputs, resource minimums, dependencies, planner,
producer, and independent validator. Missing, ambiguous, or changed providers
fail closed; EMRYS neither discovers substitutes nor runs provider-supplied
installation logic.

The v1 interface occupies the existing downstream `09` and optional `10` task
slots and inherits task, publication, recovery, provenance, and logging policy.
It deliberately provides no arbitrary stage graph, installer, failure-policy
language, registry service, or second scheduler. Compatible Steps `00`–`06`
artifacts may be reused by a distinct downstream Analysis without sharing its
Run, Results, reporting, or evidence identity.

When reporting is enabled, a matching `emrys.analysis_reporters` entry point
owns bespoke scientific HTML. Reporter identity belongs to the report receipt,
not Analysis or Run identity; EMRYS retains the fixed evidence/operations view
and report transaction. Existing flat paired-CMH Projects remain the v1
compatibility form, while explicit modules use Analysis revision v2.
