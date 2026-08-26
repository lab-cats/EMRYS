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
stay with functional owners; live Git owns checkout state, exact checks and
retained artifacts own validation observations, and the findings matrix owns
accepted work and acceptance. Purposeful action-point safety repetition may
remain.

Coverage measures regression but cannot replace scenario, shell, real-R,
runtime, transaction, oracle, cluster, or scientific testing. Materially
changed large files receive cohesion review; split by responsibility, never an
arbitrary line quota.

Automate a repository workflow only after repeated use stabilizes its inputs,
judgment, and safety boundary. Automation must not encode unsettled policy.

## Repository documentation audit (2026-08-25)

### Scope and authority correction

The `DOC-02` audit used the Git inventory to inspect all 170 tracked Markdown
sources and six standalone Mermaid sources present after the backlog and
documentation-tool cutovers. The 38 Markdown sources under `docs/` and all six
diagrams receive individual dispositions below; the other 132 Markdown sources
receive exhaustive owner-partition dispositions. The audit also inspected every
named candidate already removed by the two preceding tasks.

Before the authority cutover, a targeted Markdown-only inbound-reference scan
found 15 files naming `HANDOFF.md`, 12 naming `PIPELINE_PLAN.md`, seven each
naming `ORCHESTRATION_READINESS.md` and `QUESTIONS.md`, five naming
`FUTURE_ARCHITECTURE.md`, and one naming
`LOCAL_PILOT_LAUNCHER_TEST_PLAN.md`, excluding the campaign and matrix that
record the audit requirement itself. The documentation validator and its
mirrored Python test were separately audited as mechanical consumers rather
than counted as Markdown callers.

The audit establishes these current authority routes:

- live Git is the authority for checkout identity and source state;
- checks and retained artifacts bound to one exact commit are the authority for
  validation observations and their evidence ceilings;
- [the findings matrix](../../tasks/backlog_matrix.md) owns accepted work,
  status, required outcomes, acceptance, and terminal dispositions;
- the temporary [architecture campaign](../../tasks/architecture_campaign.md)
  owns unsliced architecture context and unsettled alternatives only;
- the [runbook](../../operations/RUNBOOK.md),
  [troubleshooting guide](../../operations/TROUBLESHOOTING.md), test policy,
  and owner-local contracts own commands, recovery, exact behavior, and
  evidence meaning;
- dated records under [`docs/history`](../../history/) may preserve unique
  historical evidence after source reconciliation, but never current state.

`HANDOFF.md` and `PIPELINE_PLAN.md` therefore cease to be current authority
immediately. The six stale sources remain in place only as visibly marked
legacy inputs until the bounded migrations below preserve their durable value.

### Owner-local and repository-support disposition

The following partitions exhaust the 132 tracked Markdown sources outside
`docs/`. Each source was reviewed within its named ownership class; an exception
is called out rather than hidden inside a group disposition.

| Source partition | Count | Disposition and evidence |
|---|---:|---|
| Root safety, product, and onboarding (`AGENTS.md`, `README.md`, `quickstart.md`) | 3 | Retain. They own repository safety and current entry journeys; `DOC-01` may condense and reorganize the user routes without weakening safety. |
| Hosted CI contract (`.github/ci/README.md`) | 1 | Retain as the current hosted-lane runtime, artifact, and evidence-ceiling owner. |
| Configuration (`configs/README.md`) | 1 | Retain as the current configuration/input contract; accepted setup and configuration simplification must update it. |
| Operational workspace roots (`data/`, `logs/`, `refs/`, `renv/`, `results/`) | 7 | Retain as current storage, fixture, runtime, logging, and result-location conventions. Accepted setup, filesystem, results, logging, and runtime work owns later changes. |
| Repository tooling (`scripts/README.md`, `scripts/documentation/README.md`) | 2 | Retain as the current tooling index and documentation-gate owner. |
| Source implementation and contract documentation (`src/`) | 68 | Retain the 51 owner/index/resource/schema READMEs, 15 adjacent contracts, `STAGE_MAP.md`, and `SOURCE_TOPOLOGY.md`. Exact behavior remains owner-local; `DOC-01` and `OPS-04` own later journey and terminology refreshes. |
| Test documentation (`tests/`) | 46 | Retain 45 active owner, fixture, oracle, baseline, and support READMEs. `tests/pending/README.md` and its duplicate non-runnable Step 04 scaffold are selected for trace-and-retirement under `CLEAN-02`. |
| Workflow documentation (`workflow/`) | 4 | Retain as the current workflow, profile, and contract owner set; accepted architecture and naming changes must update these owners with their behavior. |

No retained source in these partitions acts as a second backlog, rolling
handoff, or stale roadmap authority.

### Per-source disposition

| Source | Disposition | Evidence and execution boundary |
|---|---|---|
| `docs/README.md` | Retain and refresh routes | Necessary tree index; current routes are updated with each completed migration. |
| `docs/architecture/ARCHITECTURE.md` | Retain | Current system view; implementation detail remains subordinate to live owners and contracts. |
| `docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md` | Retain | Current source/interface/test routing; mechanically adjacent owners remain checked. |
| `docs/architecture/FUTURE_ARCHITECTURE.md` | Retire under `DOC-03` | B-series summaries and proposals duplicate newer matrix/campaign context; compare every node before deletion without settling the final architecture-document set. |
| `docs/architecture/README.md` | Retain and refresh routes | Architecture entry point remains necessary after future-document retirement. |
| `docs/architecture/diagrams/README.md` | Retain and refresh routes | Owns diagram status and must remove retired future-diagram entries with `DOC-03`. |
| `docs/demo/DEMO_WALKTHROUGH.md` | Rehome or retire under `CLEAN-01` | Preserve only a neutral supported synthetic path and evidence-safe presentation guidance. |
| `docs/demo/PI_DEMO_REPORT.md` | Rehome or retire under `CLEAN-01` | Same demo-surface decision; it is not current evidence authority. |
| `docs/demo/README.md` | Rehome or retire under `CLEAN-01` | Demo terminology and public surface remain independently unsettled. |
| `docs/design/DECISIONS.md` | Retain and refresh routes | Durable rationale index; it now records this audit and no longer delegates current state to legacy sources. |
| `docs/design/LOGGING_CONTRACT.md` | Retain | Accepted logging behavior and adoption boundary remain current. |
| `docs/design/ORCHESTRATION_CONTRACT.md` | Retain and refresh routes | Durable lifecycle, safety, identity, recovery, and evidence contract remains current. |
| `docs/design/ORCHESTRATION_READINESS.md` | Consolidate, then retire under `DOC-05` | Shared admission invariants move to the orchestration contract/test policy; exact owner behavior stays owner-local and profile membership stays with the workflow/stage map/tests. |
| `docs/design/PIPELINE_PLAN.md` | Retire under `DOC-03` | The matrix owns accepted outcomes; Git owns completed package chronology; contracts and policy docs already own durable boundaries. |
| `docs/design/QUESTIONS.md` | Retire under `DOC-03` | Accepted open outcomes live in the matrix and unsettled architecture alternatives live temporarily in the campaign; discarded-task questions must not form another backlog. |
| `docs/design/README.md` | Retain and refresh routes | Necessary design index; legacy-source authority claims are removed now. |
| `docs/design/TEST_BASELINE.md` | Retain | Current test policy, evidence vocabulary, risk index, and recheck routes. |
| `docs/design/decisions/README.md` | Retain and refresh routes | Necessary rationale index; current acceptance now routes to the matrix. |
| `docs/design/decisions/execution-evidence-and-reporting.md` | Retain | Durable execution, recovery, evidence, and reporting rationale. |
| `docs/design/decisions/platform-direction.md` | Retain | Durable architecture rationale; unsettled campaign alternatives remain separately marked. |
| `docs/design/decisions/repository-and-delivery.md` | Retain | Durable repository/delivery rationale and this accepted audit record. |
| `docs/design/decisions/scientific-pipeline.md` | Retain | Durable scientific-method and artifact-policy rationale. |
| `docs/history/README.md` | Retain and refresh routes | Dated evidence policy and future index for unique handoff evidence selected for migration. |
| `docs/operations/ENGINEERING_CONVENTIONS.md` | Retain | Stable repository dependency, tooling, and implementation conventions. |
| `docs/operations/HANDOFF.md` | Reconcile durable content, then retire under `DOC-04` | Trace every section. Preserve unique VM, renderer, PORT-NC-01, Viking Step 07–09, cohort/Step 03, artifact-identity, and recovery facts in dated history or live owners with exact provenance and evidence ceilings; discard blockers and immediate-resume prose only after the trace; never promote historical claims to current proof. |
| `docs/operations/LOCAL_PILOT_LAUNCHER_TEST_PLAN.md` | Consolidate, then retire under `DOC-05` | Active behavior stays in tests/CI; delivery safety stays in `AGENTS.md`/workflow; commands stay in the runbook; discard the stale transcript and unverifiable short references. |
| `docs/operations/README.md` | Retain and refresh routes | Necessary operations index; current-evidence routing is corrected now. |
| `docs/operations/RUNBOOK.md` | Retain | Supported cross-cutting commands and operator procedures. |
| `docs/operations/TROUBLESHOOTING.md` | Retain and refresh routes | Common diagnosis and evidence-preserving recovery; exact current evidence no longer routes to the handoff. |
| `docs/operations/WORKFLOW.md` | Retain and refresh routes | Development authority, context selection, delivery, validation, and publication procedure. |
| `docs/reference/EXTERNAL_SCIENTIFIC_EVALUATION.md` | Retain | Optional external research-process checklist, explicitly outside pipeline completion. |
| `docs/reference/GLOSSARY.md` | Retain | Shared terminology routed to canonical subject owners. |
| `docs/reference/README.md` | Retain | Necessary reference index. |
| `docs/sitemap/README.md` | Retain and refresh routes | Canonical audience/owner map; legacy authorities are removed now and later journey redesign remains `DOC-01`. |
| `docs/tasks/README.md` | Retain | Compact entry point for the canonical matrix and temporary campaign/ranking views. |
| `docs/tasks/architecture_backlog_matrix.md` | Retain temporarily | Provisional campaign-card ranking only; retire when campaign slicing and final matrix scoring make it unnecessary. |
| `docs/tasks/architecture_campaign.md` | Retain temporarily | Temporary source of truth for unsliced architecture context; it cannot become another backlog. |
| `docs/tasks/backlog_matrix.md` | Retain as canonical | Sole durable task/status/outcome/acceptance/disposition authority. |
| `docs/tasks/performance_backlog_matrix.md` | Retain temporarily | Provisional performance-card ranking and experiment routing only; it cannot own status or acceptance. |
| `docs/tasks/performance_campaign.md` | Retain temporarily | Temporary source of truth for unsliced computational-scaling context and experiment rules; it cannot become another backlog. |
| `docs/architecture/diagrams/current_user_pipeline.mmd` | Retain | Current non-authoritative user-flow projection. |
| `docs/architecture/diagrams/future_modular_pipeline.mmd` | Retire with `DOC-03` | Future proposal duplicates campaign context and must be traced node by node before deletion. |
| `docs/architecture/diagrams/future_reporting_layer.mmd` | Retire with `DOC-03` | Future proposal duplicates campaign context and must be traced node by node before deletion. |
| `docs/architecture/diagrams/local_pilot_orchestration.mmd` | Retain | Current non-authoritative local-pilot projection. |
| `docs/architecture/diagrams/pipeline.mmd` | Retain | Current non-authoritative scientific pipeline projection. |
| `docs/architecture/diagrams/reliability.mmd` | Retain | Current non-authoritative validation/publication boundary projection. |

### Named candidates already disposed

| Source | Disposition |
|---|---|
| `docs/tasks/BACKLOG.md` | Retired by completed `BACKLOG-01`; available only through Git history. |
| `docs/tasks/cards/README.md` | Retired by completed `BACKLOG-01`; the task-card operating system must not return. |
| `scripts/git_orchestration/README.md` | Removed by completed `DOC-TOOL-01`; retained structure validation now lives under `scripts/documentation/`. |

This audit performs the bounded authority and routing cutover, records
dispositions, marks transition sources, and guards them against premature
deletion. `DOC-03`, `DOC-04`, `DOC-05`, `CLEAN-01`, and `CLEAN-02` own the
separately reviewable content migrations and deletions; `DOC-01` owns the later
scientist/operator/developer journey rewrite.
