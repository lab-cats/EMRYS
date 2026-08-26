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

`HANDOFF.md` and `PIPELINE_PLAN.md` therefore ceased to be current authority at
the audit cutover. Completed `DOC-03` has since reconciled and retired three of
the six legacy pages plus both future diagrams. The remaining three pages stay
visibly marked until `DOC-04`/`DOC-05` preserve their durable value.

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
| `docs/architecture/FUTURE_ARCHITECTURE.md` | Retired by completed `DOC-03` | The section trace below routes durable principles and accepted outcomes to live owners, preserves two still-open alternatives in the campaign, and leaves the final architecture-document set unsettled. |
| `docs/architecture/README.md` | Retain and refresh routes | Architecture entry point remains necessary after future-document retirement. |
| `docs/architecture/diagrams/README.md` | Retain and refresh routes | Owns the four retained current-system diagrams after the two future projections retire. |
| `docs/demo/DEMO_WALKTHROUGH.md` | Rehome or retire under `CLEAN-01` | Preserve only a neutral supported synthetic path and evidence-safe presentation guidance. |
| `docs/demo/PI_DEMO_REPORT.md` | Rehome or retire under `CLEAN-01` | Same demo-surface decision; it is not current evidence authority. |
| `docs/demo/README.md` | Rehome or retire under `CLEAN-01` | Demo terminology and public surface remain independently unsettled. |
| `docs/design/DECISIONS.md` | Retain and refresh routes | Durable rationale index; it now records this audit and no longer delegates current state to legacy sources. |
| `docs/design/LOGGING_CONTRACT.md` | Retain | Accepted logging behavior and adoption boundary remain current. |
| `docs/design/ORCHESTRATION_CONTRACT.md` | Retain and refresh routes | Durable lifecycle, safety, identity, recovery, and evidence contract remains current. |
| `docs/design/ORCHESTRATION_READINESS.md` | Consolidate, then retire under `DOC-05` | Shared admission invariants move to the orchestration contract/test policy; exact owner behavior stays owner-local and profile membership stays with the workflow/stage map/tests. |
| `docs/design/PIPELINE_PLAN.md` | Retired by completed `DOC-03` | The section trace below confirms that Git owns completed package chronology and current contracts, policy, tests, and the matrix already own every durable rule. |
| `docs/design/QUESTIONS.md` | Retired by completed `DOC-03` | The item trace below separates durable platform outcomes from obsolete mutable site/run questions so the question index cannot become another backlog. |
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
| `docs/tasks/README.md` | Retain | Compact entry point for the canonical matrix and temporary campaign/ranking. |
| `docs/tasks/architecture_backlog_matrix.md` | Retain temporarily | Provisional campaign-card ranking only; retire when campaign slicing and final matrix scoring make it unnecessary. |
| `docs/tasks/architecture_campaign.md` | Retain temporarily | Temporary source of truth for unsliced architecture context; it cannot become another backlog. |
| `docs/tasks/backlog_matrix.md` | Retain as canonical | Sole durable task/status/outcome/acceptance/disposition authority. |
| `docs/architecture/diagrams/current_user_pipeline.mmd` | Retain | Current non-authoritative user-flow projection. |
| `docs/architecture/diagrams/future_modular_pipeline.mmd` | Retired by completed `DOC-03` | Every node and edge is reconciled below to current contracts, accepted analysis/configuration/reporting outcomes, or a discarded illustrative taxonomy. |
| `docs/architecture/diagrams/future_reporting_layer.mmd` | Retired by completed `DOC-03` | Every node and edge is reconciled below; the one unresolved publication-topology choice moves to `AC-DEC-014`. |
| `docs/architecture/diagrams/local_pilot_orchestration.mmd` | Retain | Current non-authoritative local-pilot projection. |
| `docs/architecture/diagrams/pipeline.mmd` | Retain | Current non-authoritative scientific pipeline projection. |
| `docs/architecture/diagrams/reliability.mmd` | Retain | Current non-authoritative validation/publication boundary projection. |

### `DOC-03` source-to-destination trace (2026-08-25)

This trace is the durable reconciliation record for the five retired sources.
It does not make their proposed names, order, topology, or architecture-document
set binding. “Discard” means the source statement was chronology, duplicated
authority, stale implementation status, an illustrative label, or mutable
deployment state; Git retains the deleted bytes.

#### Future-architecture sections

| Retired section | Destination or explicit disposition |
|---|---|
| Transition notice and authority links | Discarded as duplicate routing. The architecture index routes current design, the findings matrix owns accepted work, and the temporary campaign owns unsliced alternatives. |
| Principle 1: versioned requests, manifests, contracts, and deterministic identities | Preserved by `ORCHESTRATION_CONTRACT.md`, `STAGE_MAP.md`, and the artifact contracts. |
| Principle 2: owner-local, testable functional behavior with explicit source topology | Preserved by `platform-direction.md`, `FUNCTIONAL_OWNER_INVENTORY.md`, and `SOURCE_TOPOLOGY.md`. |
| Principle 3: filesystem-first inspectable run, attempt, task, recovery, and evidence state | Preserved by `ORCHESTRATION_CONTRACT.md`; public simplification remains accepted under `CONTROL-01`, `IDENTITY-01`, and `FILESYSTEM-01`. |
| Principle 4: explicit inputs, dependencies, cleanup, repair, publication, and evidence | Preserved by owner contracts, `AGENTS.md`, the workflow kernel, and the execution/evidence decision record. |
| Principle 5: distinct local, runtime, scheduler, production, scientific-review, and biological evidence | Preserved by `TEST_BASELINE.md`, the runbook's CI evidence boundary, and the execution/evidence decision record. |
| Principle 6: typed preprocessing and analysis extension rather than one universal RNA/DNA workflow | Preserved as accepted future outcomes under `ANALYSIS-01` and `ANALYSIS-02` and as unsliced context in campaign section 12; no plugin interface is selected. |
| Local YAML/TSV lifecycle capability | Implemented fixed-profile behavior and the “no inbox, watcher, queue, database, or service” boundary remain in `ORCHESTRATION_CONTRACT.md`; B2/B4/B5/B6 labels are discarded chronology. |
| Local orchestration capability | Current static graph, lifecycle, resume, reporting tail, and evidence limits remain in `ARCHITECTURE.md`, `ORCHESTRATION_CONTRACT.md`, the workflow profile, and tests; B3/B4/B5/B6 labels are discarded chronology. |
| Site-execution capability | Accepted outcomes remain under `OPS-02`, `RUNTIME-01`, `DOCTOR-01`, and `CONTAINER-01`. Exact-commit runtime/scheduler evidence remains owned by `.github/ci/README.md`, the runbook, and retained artifacts; this retirement produces no runtime or site proof. |
| Report-profile capability | Current adapter/view/publication invariants remain in the reporting owner and execution/evidence decision; audience work remains `REPORT-03`. The still-open shared-versus-profile-specific receipt topology moves to campaign `AC-DEC-014`. |
| Logging capability | The foundation is current under `LOGGING_CONTRACT.md`; production adoption remains `LOG-05`, and observability outcomes remain `OBS-01`/`OBS-02`. The legacy claim that logging was wholly unimplemented is discarded as stale. |
| Analysis-extension capability | Preserved by `ANALYSIS-01`, `ANALYSIS-02`, and campaign section 12. Loader, registry, and trust-level names remain suggestions rather than accepted interfaces. The optional-outcome-policy proposal is discarded with `FUT-SUCCESS-04` and has no successor. |
| Public-acquisition capability | The accepted provenance-safe outcome remains `FUT-DATA-02`; initial NCBI-reference/SRA adapters versus possible later ENA/GEO/BAM support moves to the campaign as a nonbinding scope choice. |
| Standalone-wheel control-plane capability | Current source-checkout and installed-control-plane limitations remain in `ORCHESTRATION_CONTRACT.md`. Discarded `FUT-CLI-03` is not revived. |
| Documentation-automation capability | The read-only documentation gate remains under `scripts/documentation/`; discarded documentation-skill, task-scan, and task-view proposals are not revived. |
| Future-projection links | Reconciled node by node below, then discarded with their targets. |
| Safety boundary: no evidence promotion or implicit restore, cleanup, repair, or recovery | Preserved by `AGENTS.md`, the workflow kernel, `ORCHESTRATION_CONTRACT.md`, and the execution/evidence decision. |

#### Future-diagram nodes and edges

| Retired diagram element | Destination or explicit disposition |
|---|---|
| Modular nodes M1 versioned request, M3 typed sample manifest, M4 registered reference | Current fixed forms remain in `ORCHESTRATION_CONTRACT.md`; future simplification remains `CONFIG-01`. |
| Modular node M2 selected preprocessing profile | Fixed current selection remains in the orchestration contract; generalized selection remains an unsettled `CONFIG-01`/`ANALYSIS-01` concern. |
| Modular node M5 typed branch artifacts | Current edges remain in `STAGE_MAP.md` and `ARCHITECTURE.md`; generalized typed outputs remain `ANALYSIS-02`. |
| Modular nodes M6 built-in module, M7 custom module, M8 native outputs | Module trust, inputs, outputs, provenance, validation, and reporting remain `ANALYSIS-02`; the exact built-in/custom two-lane taxonomy is discarded as illustrative. |
| Modular node M9 owner-local validators | Preserved by current owner contracts/tests and future `ANALYSIS-02` validation acceptance. |
| Modular nodes M10 read-only adapters, M11 canonical summary, M12 versioned report view | Preserved by the current reporting architecture and execution/evidence decision. |
| Modular node M13 science/comprehensive reports | Audience separation remains `REPORT-03`; the old two-profile names are superseded by scientific, evidence, and operational purposes. |
| Modular edges M1/M3/M4→M2 and M2→M5 | Current intake/profile projection remains in the orchestration contract; generalized profile choice and typed artifacts remain future `CONFIG-01`/`ANALYSIS-01`/`ANALYSIS-02` work. |
| Modular edges M5→M6/M7→M8 | Preserved as the future module/input/output relationship under `ANALYSIS-02`; the exact two-lane topology is not accepted. |
| Modular edges M8→M9/M10, M9→M10, M10→M11→M12→M13 | Preserved as owner validation plus read-only reporting adaptation; future audience projection remains `REPORT-03`. |
| Reporting nodes R1 native outputs, R3 owner validation, R2 adapters, R4 canonical summary, R5 versioned view | Preserved by the current reporting owner, `ARCHITECTURE.md`, and the execution/evidence decision. |
| Reporting nodes R6 focused profile, R7 comprehensive profile, R8 scientific HTML, R9 comprehensive HTML | Audience separation remains `REPORT-03`; the old profile names and “comprehensive HTML” label are discarded as superseded. |
| Reporting node R10 deterministic summary TSV | Preserved by the current reporting contract. |
| Reporting node R11 receipt-last publication | Preserved by the current report transaction; shared versus profile-specific future receipts remain open under `AC-DEC-014`. |
| Reporting edges R1/R3→R2→R4→R5 | Preserved as the current validated adapter/view flow. |
| Reporting edges R5→R6/R7→R8/R9 | Preserved only as a future audience-projection concern under `REPORT-03`; exact names and branching are not accepted. |
| Reporting edges R4→R10 and R8/R9/R10→R11 | Deterministic TSV and receipt-last publication remain current; future transaction topology remains `AC-DEC-014`. |

#### Pipeline-plan sections

| Retired section | Destination or explicit disposition |
|---|---|
| Transition warning, navigation, and authority routing | Discarded as duplicate of `AGENTS.md`, the workflow kernel, architecture index, and findings matrix. |
| Completed B/RPT package families and package-order tables | Discarded as Git chronology. Current behavior remains in functional owners, the workflow profile, stage map, contracts, and tests. |
| RPT-05 figures, Step 10, report outputs, receipt v4, native Step 09 PDFs, and no-recalculation rule | Preserved by the reporting owner, scientific-context contracts, and reporting decisions; historical scope language is discarded. |
| B1–B6 local-pilot summary, Doctor, public adapter, resume/recovery, and fresh-clone proof | Preserved by the local-pilot contract/README, workflow profile, runbook, test baseline, and direct tests; package labels are discarded chronology. |
| Adversarial hardening and PORT-NC summary | Current no-clobber, residue, interruption, recovery, reuse, and evidence guarantees remain owner-local. Unique dated PORT-NC evidence remains assigned to `DOC-04` through `HANDOFF.md`; this duplicate summary is discarded. |
| Real-tool, SLURM, VM, and site work described as unselected | Discarded as mixed mutable status. Exact-commit runtime/scheduler evidence remains in the hosted-CI owner, runbook, and retained artifacts and is not promoted to current-head proof here. Current architecture still treats general real-tool/SLURM and CSU whole-run proof as unproved; `DOC-04` separately owns the dated manual CSU Steps 07–09 evidence. |
| Reporting-card split and unselected work families | Current reporting behavior remains owner-local and accepted work remains matrix-owned. Stale selection claims, including pre-`LOG-03` logging status, are discarded. |
| Six generic package-acceptance rules and documentation-gate/history policy | Preserved by `AGENTS.md`, the workflow kernel, engineering conventions, test policy, decision records, and `docs/history/README.md`. |
| Eight owner-admission checks plus clean/failure-resume end-to-end checks | Preserved by engineering conventions, `TEST_BASELINE.md`, the functional-owner inventory, local-pilot contract, and direct tests; no checklist item is unique. |
| Computational exit and external-interpretation boundary | Preserved by `AGENTS.md` and the execution/evidence decision. |

#### Question-index items

| Retired question | Destination or explicit disposition |
|---|---|
| Production six-row manifest location, ownership, hash, and retention | Ordered manifests, required replicates, SHA-256 binding, snapshots, and run ownership remain in `ORCHESTRATION_CONTRACT.md`; future generation remains `CONFIG-01`/`SETUP-01`. The fixed six-row location/retention question is discarded as obsolete run-specific state. |
| CSU runtime availability and eligible-node checks | General complete-runtime and batch-visible admission remains `RUNTIME-01`/`DOCTOR-01` and the runtime decision. Exact mutable site availability is discarded as deployment state, not architecture policy. |
| Home/project/scratch capacity, retention, and approval | General readiness, storage, capacity, location, and retention ownership remains `DOCTOR-01`, `OPS-01`, `FILESYSTEM-01`, and the storage evidence owner. Exact capacities and approval state are discarded as mutable site observations. |
| Novogene reference release and mitochondrial naming | Declared-reference identity and FASTA/FAI/DICT/GTF/BED/STAR coherence remain in the scientific-pipeline decision and reference-provenance owner. The unanswered release/name facts are discarded as project-input questions, not backlog outcomes. |
| Runtime promotion, real Step 07, Viking Steps 07–09, resources, and evidence | General promotion remains `RUNTIME-01`, `DOCTOR-01`, and `OPS-02`. Unique dated Viking/Step evidence remains in `HANDOFF.md` for exact migration under `DOC-04`; this question index adds no evidence. |
| External research process | Preserved by `EXTERNAL_SCIENTIFIC_EVALUATION.md` and the execution/evidence decision; it remains outside computational completion. |
| `CHOICE-SITE-01` | Preserved by `RUNTIME-01`, `DOCTOR-01`, `CONFIG-01`, `OPS-01`, and `OPS-02`, with unsettled runtime/execution alternatives in the campaign. |
| `CHOICE-ANALYSIS-01` | Preserved by `ANALYSIS-01` and `ANALYSIS-02`, including scientific trust, reviewability, validation, provenance, dependencies, reports, and separately identified alternate analyses. |
| `CHOICE-DATA-01` | Preserved by `FUT-DATA-02` and its nonbinding campaign scope note. |
| `CHOICE-CONTROL-01` | Preserved by `CONTROL-01`, `CONFIG-01`, `OPS-01`, and `OPS-02`; immutable materialization/versioned contracts remain in `ORCHESTRATION_CONTRACT.md`, and discarded `FUT-CLI-03` is not revived. |

### Named candidates already disposed

| Source | Disposition |
|---|---|
| `docs/tasks/BACKLOG.md` | Retired by completed `BACKLOG-01`; available only through Git history. |
| `docs/tasks/cards/README.md` | Retired by completed `BACKLOG-01`; the task-card operating system must not return. |
| `scripts/git_orchestration/README.md` | Removed by completed `DOC-TOOL-01`; retained structure validation now lives under `scripts/documentation/`. |

This audit performs the bounded authority and routing cutover, records
dispositions, marks transition sources, and guards them against premature
deletion. Completed `DOC-03` owns the trace and retirement recorded above;
`DOC-04`, `DOC-05`, `CLEAN-01`, and `CLEAN-02` own the remaining separately
reviewable migrations and deletions. `DOC-01` owns the later
scientist/operator/developer journey rewrite.
