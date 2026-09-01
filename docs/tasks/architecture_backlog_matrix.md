# EMRYS Architecture Campaign Backlog Matrix

> **PROVISIONAL CAMPAIGN RANKING — NOT AN IMPLEMENTATION BACKLOG**

Last ranked: **2026-08-25**

This file is a scoped planning view of the candidate cards in the
[architecture campaign](architecture_campaign.md). It records a cursory,
provisional Architecture Priority and Indicative Complexity comparison to
support small, just-in-time slices. This preliminary scoring pass was
explicitly approved by the user on **2026-08-25**.

The [main backlog matrix](backlog_matrix.md) remains authoritative for accepted
task IDs, implementation status, required outcomes, acceptance conditions, and
dispositions. This architecture matrix does not accept a candidate into the
implementation backlog, resolve an open design decision, or authorize work.
The campaign remains authoritative for the full rationale, alternatives,
binding requirements, open decisions, and ideal end state behind each card.
The outcome and routing columns below are navigation summaries. If their
wording ever conflicts with the campaign, the campaign controls until a task is
accepted into the main backlog.

`AC-SLICE-01` completed as `ARCH-CONST-01`, and `AC-SLICE-02` completed as
`ARCH-LAYER-01`, after this ranking was recorded. Their original `5`/`3` values
and rows remain for traceability rather than implying active work or a
reranking; the main matrix owns the terminal dispositions.

`ARCH-MODEL-AUDIT-01` subsequently completed the read-only current-state
prerequisite for `AC-SLICE-03`. Per the approved recording boundary it did not
complete, accept, implement, or rerank that campaign card; the original
`5`/`4` values remain provisional.

`ARCH-MODEL-DECISION-01` subsequently selected model C, the compact public
vocabulary, and the Run-versus-Attempt semantic boundary. It also did not
rerank or complete `AC-SLICE-03`.

`ARCH-MODEL-FIELDS-01` subsequently completed the documentation-only semantic
field-and-authority package: identity fields and digest composition,
relocation/order/content rules, the symbolic resource/Attempt envelope,
logical authorities, recovery owner, direct compatibility direction, and
status-domain separation.

The first successor Run-authority cutover subsequently implemented immutable
Analysis-revision, Execution-Plan, and Run-binding records; durable Run-last
admission; zero-Attempt inspection; and new-Run planning, execution, resume,
and inspection through the current local-pilot path. Historical
`emrys.execution.v1` read/resume remains supported through a version-aware
reader. Successor workflow/task consumers now admit exact `run.json` authority,
and reporting consumes exact Attempt-owned inputs bound by the origin workflow
config; the temporary successor execution projection is retired. A subsequent
public-model cut adds closed `emrys.project.v1`, shared Dataset/Reference
sections, and named Analyses; validation admits all Analyses, while Run and
Doctor select one. New work rejects request-v3, whose exact reconstruction is
isolated to historical resume. Attempt-v1 evidence and the existing
Results/reporting authority remain unchanged. Final compression accounting and
focused verification complete `AC-SLICE-03`. Generalized storage and package
APIs remain separately Open, and
generalized-backend implementation stays conditional on concrete extension or
net-reduction evidence.

A subsequent execution-configuration cut implements one admitted
`emrys.execution-profile.v1` document and optional `--execution-profile`
selector. Omission uses packaged direct-placement defaults; current precedence
is built-in profile, explicitly selected profile, then CLI resource overrides.
Run-bound computational resources remain distinct from Attempt-local
direct/Slurm placement and runtime provisioning. Grouped `run`/`resume` now
submit whole-Run Slurm placement once through a private transport; the
generated wrapper and separate launcher/resource surfaces are retired.
Controlled planning/materialization parity remains established. Hosted
disposable single-node Slurm now also proves one successful 130-pair path:
direct and Slurm preserve identical canonical Analysis, Execution Plan, and
Run authority while producing distinct Attempts with matching common fields,
task rosters, path-neutral scientific results, and symbolic resources. Each
side separately admits a successful receipt, complete reporting, and one
ordered application log; allocation-sensitive effective resources, scheduler
streams, and job provenance differ as intended. Institutional-site/module portability,
multi-node and production execution, failure/recovery parity, and scientific
or biological validation remain Open.

A subsequent guided-setup cut completes `SETUP-03`: `emrys init project`
validates before dry-run-first, create-absent publication; owns only
`project.yaml`, `runs/`, `logs/`, and `runtime/`; references inputs in place;
and makes the Project root derivable without duplicate workspace arguments.
Runtime acquisition and repair remain separately owned.

A subsequent runtime cut implements dry-run-first institution-provided runtime discovery and the one
Project-owned admitted runtime path. Managed Doctor repair now uses the packaged
Pixi resources, the active checkout-owned `.venv`, and Project-owned
`runtime/managed`, delegating to `uv`, Pixi, and `renv` before requalification.
It preserves site/user profiles and currently supports Linux x86-64. The resources
target Linux x86-64 with declared glibc 2.28 and Linux 4.18 virtual-package
values. Ordinary CI installs the unchanged lock and invokes its tools in Rocky
8.10, Ubuntu 22.04, and Debian 12 userspaces. The real-tool, managed, direct
Ubuntu golden-path job is implemented; exact-head execution is pending. Actual
Linux 4.18, broader portability, cluster/site, scheduler, security, update
qualification, Explicit definition, and named profiles remain Open under
`RUNTIME-01`.

## Scoring

Both columns use `5` as the highest value. Scores are intentionally loose and
must be reconsidered when a card is bounded or split. They help select the next
candidate for just-in-time review; they are not the final Importance and
Complexity scores later assigned to accepted tasks in the main backlog.

### Architecture Priority

| Score | Meaning in this architecture view |
|---:|---|
| `5` | Campaign-defining outcome or non-negotiable architectural direction |
| `4` | Major recurring user, operator, reliability, or strategic benefit |
| `3` | Meaningful follow-on or just-in-time enabling work |
| `2` | Useful but opportunistic work with an adequate near-term alternative |
| `1` | Retained companion work outside the architecture campaign's implementation scope |

### Indicative Complexity

Complexity estimates the remaining effort and risk needed to close the
**current card as written**, including operative realization, migration,
compatibility, and proportionate proof rather than merely drafting a design.

| Score | Meaning |
|---:|---|
| `5` | Cross-cutting public, lifecycle, runtime, recovery, scheduler, or portability migration with demanding integration evidence |
| `4` | Multi-owner interface or contract change with compatibility and integration work, or specialized high-risk review/validation requiring independent proof |
| `3` | Bounded multi-module work, architectural definition, or moderate new public surface |
| `2` | Primarily read-only or localized work with focused validation |
| `1` | Localized, straightforward change with little migration risk |

Architecture Priority and Indicative Complexity are independent. They are not
multiplied into a composite score, and neither column establishes
implementation order, dependencies, or approval.

## Campaign-card matrix

| Card | Track | Architecture Priority | Indicative Complexity | Campaign outcome | Likely routing | Sizing note |
|---|---|---:|---:|---|---|---|
| `AC-SLICE-01` | Foundations | `5` | `3` | Ratified an architectural-invariants constitution against live contracts and representative tests | Completed as `ARCH-CONST-01`; broad `ARCH-01` remains Open | Original provisional ranking retained for traceability |
| `AC-SLICE-02` | Foundations | `5` | `3` | Ratified responsibility clusters, three graph semantics, forbidden authority transfers, and fast source-boundary enforcement over exact current CLI seams and transitional imports | Completed as `ARCH-LAYER-01`; broad `ARCH-01` remains Open | Original provisional ranking retained for traceability |
| `AC-SLICE-03` | Public model | `5` | `4` | **Complete.** Closed project-v1 persists shared Dataset/Reference inputs and named Analyses; validation admits all, while Run and Doctor select one. The selected immutable Analysis flows through the existing Execution Plan, Run, Attempt, and read-only Results authorities. New work rejects request-v3; exact historical resume retains it. | Attempt-v1 and Results/report semantics are unchanged; no evidence is deleted. Active request-v3 intake, duplicate readers/projections, and user-facing request-era setup retire with a meaningful maintained-product reduction. Generalized storage, package APIs, named execution profiles, and near-closure backend evaluation remain separately owned. |
| `AC-SLICE-04` | Scientific boundary | `3` | `4` | **Complete.** Retain private `TaskDispatch`; do not add a universal Stage/Operation representation. Step `08` now uses one owner-local Python coordinator while native R science and independent validation remain. | Completed; broad `ANALYSIS-02` and `ARCH-01` remain Open | Transformation, scientific-analysis, and evidence owners mapped; reporting correctly remained separate. Caller, Slurm, provenance, docs, and tests migrated without a compatibility wrapper. |
| `AC-SLICE-05` | Execution | `4` | `5` | Complete the declared guarantee and parity contract across direct and Slurm placement of the current backend, then evaluate the generalized-backend boundary near campaign closure | One file-bound profile and grouped `run`/`resume` route select direct or whole-Run Slurm around the same one-host Snakemake backend. The private transport submits once and records Attempt-local placement. Controlled planning/materialization parity and successful hosted disposable-Slurm outcome parity are proven at 130 pairs: immutable authority, Attempt common fields/task roster, path-neutral science, and symbolic resources match; each side separately admits successful receipt/reporting and one application log; effective resources and scheduler provenance remain placement-sensitive. Institutional-site/module, multi-node/production, and failure/recovery parity remain Open with `OPS-02`. | Evaluation is required; implementation remains conditional on a concrete extension or compression case, parity, and no duplicate authority |
| `AC-SLICE-06` | Policy ownership | `3` | `3` | Inventory duplicated policy decisions and centralize only candidates that pass the resolved equivalent-two-production-owner, caller-complete, net-negative gate | Conditional inventory; supports `ARCH-01` | May close with no shared layer; distinct trust-boundary re-admission is not duplication |
| `AC-SLICE-07` | Artifact lifecycle | `4` | `5` | Define demonstrated artifact-class lifecycle/admission gaps and migrate one path only if the selected design requires a boundary change | Conditional class-specific work; supports `ARCH-01` | A distinct Artifact Store is deferred until a separately approved concrete unmet need |
| `AC-SLICE-08` | Execution configuration | `4` | `4` | Decide whether named execution profiles are accepted and, if so, define them independently of runtime acquisition modes | One v1 file-bound format, built-in direct default, explicit selector, current precedence, and source/effective provenance are implemented. Run-bound resources, Attempt-local placement, and runtime provisioning remain distinct. Institution-provided runtime discovery publishes one Project-owned authority; bounded managed installation/repair is implemented through Doctor. Named execution profiles, Explicit definition, and broader management remain Open with `OPS-01` and `RUNTIME-01` | Discovery, canonical authority, and the first Managed repair are settled; remaining acquisition names and APIs are unselected |
| `AC-SLICE-09` | Inspection | `3` | `3` | **Complete.** Existing grouped Run control and read-only inspection provide normal Run identity, verbose Analysis/Execution-Plan/Attempt identity and effective execution facts, and debug authority, artifact, receipt, task, and evidence detail. | Completed with `IDENTITY-01`; broader Project/Results APIs remain with `CONTROL-01`, and command simplification remains with `OPS-02`. | No new command, flag, schema, status store, backend, evidence format, or identity authority; one consolidated evidence snapshot replaces duplicate inspection/lifecycle projections. |
| `AC-SLICE-10` | Operations | `4` | `4` | Define high-level status and safe resume/recovery UX over existing fail-closed internals | **Complete.** The existing inspect route derives separated status, recovery gating, a deterministic next action, five scientific milestones, and current/latest Attempt elapsed time from persisted EMRYS records. Normal output hides engine state; verbose adds operational aggregates; debug exposes admitted task, transaction, receipt, engine, scheduler, and record detail. Reporting remains downstream rather than a scientific milestone, no ETA is inferred, and inspection writes nothing. Broader console-noise work is complete under `OBS-01`; retained-operation logging adoption and parity remain Open under `LOG-05`. | The stale dashboard is frozen outside this slice and its retirement is deferred until campaign completion; focused fault/lifecycle coverage and aggregate CI protect closure. |
| `AC-SLICE-11` | Results | `3` | `5` | Decide whether a canonical Run Bundle is accepted and, if so, define its contract | A Run Bundle is likely useful; shape, ownership, persistence, and exact contract remain Open with `FILESYSTEM-01` and completed `RESULTS-01` | Do not reopen the current result layout without evidence or imply a distinct Artifact Store. |
| `AC-SLICE-12` | Results | `4` | `3` | **Complete.** The two existing receipt-bound HTML reports now expose fixed relative destinations for the scientific, evidence/provenance, and operational questions. | Completed; `RESULTS-01` is Complete and `REPORT-03` remains Verification pending | The scientific report remains primary; the combined Evidence and operations report folds provenance under Evidence and moves Attempt lineage under Operations without adding an artifact, schema, command, or filesystem surface. |
| `AC-SLICE-13` | Golden path | `5` | `5` | Deliver a supported fresh-install-to-valid-synthetic-result golden path after ratifying its capability order | Implementation complete: the supported managed direct journey and exact retained assertions are configured in the ordinary CI lane; exact-head verification is pending | Capstone acceptance outcome, not an atomic implementation package |
| `AC-SLICE-14` | Measurement | `3` | `2` | Establish reproducible UX and architecture baselines plus separately interpreted product-implementation, protection/test, configuration/documentation, and retained-evidence baselines | New slice; coordinates with `REVIEW-UX-03` and `ARCH-01` | Establishes aggregate methods; mandatory category-separated accounting begins with every slice now and is not deferred to this card |
| `AC-SLICE-15` | Scientific companion | `1` | `4` | Audit the Steps 07–09 statistical contract | New scientific-review slice; not architecture evidence | Parallel scientific-review work |
| `AC-SLICE-16` | Scientific companion | `1` | `4` | Build independent numerical oracles for Steps 08 and 09 | New scientific-validation slice | Parallel scientific-validation work |
| `AC-SLICE-17` | Retirement | `3` | `5` | Retire duplicated lifecycle, validator, infrastructure, adapter, shell, or compatibility paths after each replacement is proven; retained evidence may be deleted only after an exact scoped proposal and the user's explicit approval | Completed cuts retire the generated wrapper/configuration split, the Step `06`–`09` shell owners and shell-only suites, all sixteen owner-local `.slurm` paths and their dedicated harness, and the duplicate Attempt-preparation/direct-lifecycle route. The surviving lifecycle accepts one canonical Attempt byte payload through its sole production entry; the small private whole-Run batch bootstrap remains. Other registered reductions remain deferred, so this umbrella card stays **Open**. No retained evidence is deleted. | Low-risk impossible-state protections need no artificial replacement; high-risk, ambiguous, user-facing, execution-boundary, or evidence-validation changes require explicit approval; any approved evidence deletion stays isolated and never offsets product growth |
| `AC-SLICE-18` | Documentation | `4` | `3` | Rewrite navigation and documentation around scientist/operator/developer journeys | Expansion or slicing of `DOC-01`; uses the accepted `DOC-02`/`DOC-03` traces and coordinates with `DOC-04`–`DOC-05` retirements | Scope follows the settled role journeys |
| `AC-SLICE-19` | Doctor | `4` | `5` | **Complete.** Top-level Doctor diagnosis is no-write/no-log; explicit managed repair is previewed and confirmed, may publish the Project-owned direct-storage receipt, is otherwise bounded to the active checkout-owned `.venv` and Project `runtime/managed`, and is followed by complete requalification | Completed with `DOCTOR-01`; direct execution admits the local receipt or stronger v1 evidence, while Slurm and placement-less historical execution remain v1-only. Storage-only repair preserves an already-ready site runtime and invokes no package manager; otherwise `uv`, Pixi, and `renv` own solving/installation while Doctor owns authority, one maintenance log, and requalification | Site/user profiles and declared inputs are preserved; Linux x86-64 is the current managed target. Broader runtime modes/profiles remain `RUNTIME-01`, broader logging adoption remains `LOG-05`, and integrated exact-head verification remains with `AC-SLICE-13` |

`AC-SLICE-15` and `AC-SLICE-16` remain visible so the campaign does not lose
its parallel scientific-review commitments. Their `1` score is only an
Architecture Priority classification within this view; it is not a statement
about their scientific importance.

## Interpretation notes

- `AC-SLICE-13` is a high-priority capstone acceptance outcome, not an atomic
  implementation package. Its supporting capabilities require smaller bounded
  slices and separate sequencing decisions.
- The Sizing note column flags broad cards without assigning a campaign
  disposition. Candidate acceptance, revision, splitting, absorption, or
  decline remains a later explicit decision.
- A card should be promoted only after a read-only owner/caller review defines
  one observable outcome, non-goals, preserved invariants, open decisions,
  acceptance evidence, and an honest evidence ceiling; records its compression
  opportunities and proposed dispositions; classifies affected protections and
  retained evidence; and identifies every mutable exception and temporary
  compatibility path with its owner and retirement condition.
- Use the campaign's canonical
  [per-slice compression and mutation protocol](architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol)
  for the register and category-separated closeout. Promotion never implies
  authority to delete retained evidence; that requires an exact proposal,
  explicit user approval, and a separate commit.
- One provisional working method is to revisit ranking just in time rather
  than require complete campaign sequencing up front. This does not resolve
  the selected golden-path capability order or settle any remaining task sequence.
