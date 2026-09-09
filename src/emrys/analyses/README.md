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

The v2 execution interface occupies the existing downstream `09` and optional `10` task
slots and inherits task, publication, recovery, provenance, and logging policy.
It provides no arbitrary stage graph, installer, failure-policy language,
registry service, or second scheduler. A distinct downstream Analysis can reuse
compatible Steps `00`–`06` artifacts, while keeping its own Run, Results,
reporting, and evidence identity.

A planner receives `TaskPlanningContextV2`: `working_outputs` gives the exact
files its worker must create; `outputs` gives canonical final identities for
provenance and the independent validator. It returns `TaskCommandPlanV2` with
fixed worker argv, validator argv, and all consumed inputs. Artifact declarations
specify native publication order; put the terminal native receipt last. The
runner creates working space and supervises execution. Providers must migrate
their complete worker path to this interface; there is no legacy execution
adapter. Persisted v1 provider metadata remains readable for historical Runs.

## Scientific reports and compatibility

When reporting is enabled, a matching `emrys.analysis_reporters` entry point
produces the method's scientific HTML. Reporter identity belongs to the report receipt,
not Analysis or Run identity; EMRYS retains the fixed evidence/operations view
and report transaction. Existing flat paired-CMH Projects remain the v1
compatibility form, while explicit modules use Analysis revision v2.
