# Analysis modules

Select an Analysis in `project.yaml` to apply a scientific method to checked
processing outputs. EMRYS keeps its plan and execution records in the same
immutable Run. The built-in
[`paired-CMH analysis`](paired_cmh_candidate_ranking/README.md) includes the
[`scientific_context_projection/`](paired_cmh_candidate_ranking/scientific_context_projection/README.md).

## Collaborator providers

External computation providers use the standard `emrys.analysis_modules`
Python entry-point group. EMRYS checks the selected provider's exact ID and
version, configuration schema and normalized scientific settings, implementation
bytes, declared inputs/outputs, minimum resources, dependencies, planner,
producer, and independent validator. A missing, ambiguous, or changed provider
is rejected; EMRYS does not select substitutes or run a provider's installer.

A module can declare additional executables, R packages, files or package
directories. Doctor checks these requirements and the runner records their
content identities. The module's package manager supplies them; managed runtime
repair does not install custom dependencies.

The v2 interface uses the existing `09` and optional `10` task slots and the
runner's publication, recovery, provenance, and logging rules. It adds no arbitrary
task graph, installer, failure-policy language, registry service, or second scheduler.
A downstream Analysis can reuse compatible Steps `00`–`06` artifacts while
keeping its own Run, Results, reporting, and evidence identity.

A planner receives `TaskPlanningContextV2`: `working_outputs` gives the exact
files its worker must create; `outputs` gives canonical final identities for
provenance and the independent validator. It returns `TaskCommandPlanV2` with
fixed worker argv, validator argv, and all consumed inputs. Planning configuration
is strict admitted JSON recursively frozen into read-only mappings and tuples.
The record decoder instead returns fresh mutable dictionaries and lists; it
cannot replace freezing without changing the provider boundary. Artifact declarations
specify native publication order; put the terminal native receipt last. The
runner creates working space and supervises execution. All workers use v2.
Current record schemas also accept v1 provider metadata; that does not authorize
v1 execution or reading obsolete Runs. The [version policy](../../../docs/design/decisions/platform-direction.md#version-support)
defines current-format support.

## Scientific reports and compatibility

When reporting is enabled, a matching `emrys.analysis_reporters` entry point
produces the method's scientific HTML. Reporter identity belongs to the report receipt,
not Analysis or Run identity; EMRYS retains the fixed evidence/operations view
and report transaction. Existing flat paired-CMH Projects remain the v1
compatibility form, while explicit modules use Analysis revision v2.
