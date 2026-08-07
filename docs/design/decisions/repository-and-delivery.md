# Repository and delivery rationale

## Representation and execution

### Explicit manifests

Use ordered TSVs for samples, partitions, inventories, approvals, and evidence
because shell, Python, and R can inspect the same bytes. Exact headers and row
order are public contracts. A future YAML run request may carry policy while
referencing the sample TSV.

### Local development, SLURM production

Editing, fixtures, mocks, and syntax checks run locally. Heavy production
computation runs through owner-local SLURM entry points, never on the login
node.

### Programs stay out of Markdown

Markdown may show short invocations, but branching, validation, mutation,
recovery, and publication logic belongs in parameterized tested source.
Legacy scripts are protocol evidence, not authority to retain hardcoded paths,
samples, or assumptions.

### Active and future tests remain distinct

Runnable tests live in active test owners. Non-runnable ideas remain explicit
scaffolds and are never wired into the validation gate.

## Reviewable delivery

### Semantic packages and separate publication

One bounded package normally produces one semantic commit containing its
implementation, direct tests, contracts, and subject-affected documentation.
Selection and progress bookkeeping create no commits. Publication remains a
separate authorized action. The exact current procedure is the
[`workflow kernel`](../../operations/WORKFLOW.md).

### Proportional, final-state validation

Focused tests provide feedback. Run one complete applicable gate on the final
affected state and rerun only evidence invalidated by later changes. A
non-consuming documentation change needs Git and documentation checks; an
executable or consumed change needs its behavioral gate.

### Failure-first output

Routine success remains concise while failures retain attributable diagnostics.
Parallel validation must preserve exact results and coverage, bound cleanup,
pin dependencies, and retain a deterministic serial fallback. Measured tuning
thresholds are activation criteria, not permanent speed guarantees.

### Context and approval follow impact

Start from live Git state, the bounded task, affected owners, and direct
consumers. Reuse exact unchanged context; broaden for contradiction, public
contracts, science, safety, recovery, publication, ownership, dependencies, or
unbounded impact. Approval covers only its stated objective, mutation,
authority, evidence ceiling, exclusions, and stop conditions.

## Maintainability

Documentation changes when its subject changes. Exact commands and defects
stay with functional owners; current state, roadmap, and cross-cutting rules
stay with their named canonical documents. Purposeful action-point safety
repetition may remain.

Coverage measures regression but cannot replace scenario, shell, real-R,
runtime, transaction, oracle, cluster, or scientific testing. Materially
changed large files receive cohesion review; split by responsibility, never an
arbitrary line quota.

Automate a repository workflow only after repeated use stabilizes its inputs,
judgment, and safety boundary. Automation must not encode unsettled policy.
