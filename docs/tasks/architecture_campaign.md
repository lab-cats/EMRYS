# EMRYS Architecture Campaign

> **INTAKE CLOSED — TEMPORARY ARCHITECTURE AUTHORITY**
>
> Intake for this campaign closed on **2026-08-24**. This document temporarily
> owns architectural context that has not yet been converted into accepted,
> bounded backlog items. The [backlog matrix](backlog_matrix.md) owns accepted
> task-level work.
> The [architecture backlog matrix](architecture_backlog_matrix.md) provides a
> provisional Architecture Priority/Indicative Complexity view of this
> campaign's candidate cards; it does not accept or authorize those cards or
> supply their final task scores.
> Where the documents overlap, the main backlog matrix owns task status and
> acceptance while this document preserves the broader rationale,
> alternatives, and ideal end state.
>
> The command names, class names, phase numbers, P0–P3 ordering, numeric targets,
> example schemas, diagrams, and filesystem layouts recorded here are proposals
> for later reconsideration unless this document explicitly labels them
> **binding**. This campaign does not authorize implementation, deletion,
> publication, dependency installation, cluster execution, scientific claims,
> or evidence promotion.

## How to read this document

This document uses the following decision-label classes:

- **Binding:** a requirement the user has explicitly made non-negotiable.
- **Preserved/Target:** the two states in the ratified constitution; Preserved
  is a scoped current contract, while Target is binding with a named current
  gap and is not an implementation claim.
- **Invariant candidate:** original source wording retained only for intake
  traceability; the qualified ratified register controls.
- **Proposed:** a concrete design suggestion retained for evaluation.
- **Open:** a decision that has deliberately not been made.
- **Observed:** behavior established at one exact audited source revision; it
  is neither a target design nor a compatibility promise.
- **Candidate compression:** a conditional reduction opportunity requiring
  owner/caller review, relevant parity, protection disposition, and explicit
  approval before any evidence deletion.

Repeated recommendations from the source material are consolidated in the
main narrative. Their variants are retained in the source, open-decision, and
nonbinding-sequencing registers so consolidation does not silently erase an
alternative.

## 1. Campaign thesis

> **The scientific core is considerably simpler than the software surrounding
> it. EMRYS's biggest opportunity is therefore not to simplify the science, but
> to compress the operational surface area while preserving the evidence and
> provenance guarantees underneath.**

EMRYS has accumulated machinery for scientific computation, evidence,
provenance, reproducibility, local and HPC execution, runtime qualification,
storage qualification, validation, transactional publication, reporting, and
recovery. Much of that machinery reflects legitimate requirements and hard-won
failure knowledge. The architectural problem is not merely that the repository
contains many mechanisms. It is that too many of their concepts are visible at
too many layers, and the same invariants can be understood or enforced in more
than one place.

The desired evolution is:

```text
CURRENT                                  TARGET

scientist                                scientist
   |                                        |
many files, identities, policies         Project / Analysis
   |                                        |
manual state transitions                 Run
   |                                        |
workflow and scheduler mechanics         Result
   |                                        |
scientific tools                         [rigorous machinery underneath]
```

The campaign should make EMRYS:

- simple at the surface;
- rigorous underneath;
- transparent when inspected;
- progressively more powerful as a user asks for more control; and
- easier to maintain because each guarantee has one clear authority.

The primary product principle is:

> Complexity should be paid for once by the implementation, rather than
> repeatedly by every scientist, operator, stage, and future maintainer.

This is a campaign to make rigor cheap to consume, not a campaign to remove
rigor.

## 2. Architectural diagnosis

### 2.1 EMRYS is several legitimate systems

EMRYS now spans at least four concerns:

| Concern | Includes |
|---|---|
| Scientific computation | Pipeline steps, alignment, BAM/VCF processing, candidate evidence, statistics, context, and scientific validation |
| Evidence and provenance | Artifact identity, validation, immutable records, receipts, evidence, reports, and reproducibility |
| Execution infrastructure | Local processes, SLURM, resources, runtimes, storage, failure behavior, and recovery |
| User-facing orchestration | Project configuration, planning, run lifecycle, status, diagnostics, inspection, and result delivery |

All four are valid. Their current boundaries are too porous. A scientific stage
should not need to understand SLURM or publication transactions. A validator
should not rediscover runtimes. A report should not own artifact publication.
The CLI should not implement scientific semantics or transaction behavior. An
ordinary scientist should not have to understand any of those internals merely
to run a valid analysis.

### 2.2 Internal concepts leak into ordinary operation

The source material identifies a normal-use surface that can expose concepts
such as:

```text
request.yaml
samples.tsv
partitions.tsv
runtime.tsv
runtime.selected.tsv
launcher.yaml
resources.yaml
workspace
run root
control directory
SLURM wrapper
owner jobs
workflow attempt IDs
task IDs
receipts
publication generations
backup generations
Snakemake commands
```

These concepts can remain valuable and inspectable. They should be generated
or nested implementation details for ordinary work, not pieces the scientist
must manually assemble into a miniature workflow operating system.

### 2.3 Complexity disposition

| Complexity | Campaign direction |
|---|---|
| Scientific workflow and statistical assumptions | Preserve and keep scientifically visible |
| Provenance and evidence generation | Preserve; expose through coherent APIs and reports |
| Artifact integrity and transactional publication | Preserve; declare class-specific authorities and share lifecycle capability only when justified |
| Runtime and storage qualification | Preserve; encapsulate behind profiles and diagnosis |
| HPC and scheduler mechanics | Preserve; strongly hide from the primary control plane |
| Repeated validators and lifecycle implementations | Consolidate, then remove superseded paths |
| Repeated owner-local infrastructure logic | Move behind owned mechanism boundaries only after inventory proves a common responsibility |
| Low-level operational configuration | Place behind profiles and explicit advanced interfaces |
| Internal state machine | Retain internally; expose a smaller run-state vocabulary |

Lines and files are not sufficient measures by themselves: moving the same
responsibility into a larger module, generated source, configuration, or an
unowned wrapper is not simplification. The primary measures are fewer
independent authorities, public concepts, call edges, and compatibility paths.
Within each implementation slice, however, net-negative maintained product
code and no product-file growth are binding defaults unless the user approves a
quantified exception.

## 3. Binding campaign requirements

The following requirements are **binding and non-negotiable** for this
campaign:

1. **Overall UX simplification.** Ordinary scientific operation must converge
   on a small, coherent surface with safe defaults and progressive disclosure.
2. **Formal architectural layering.** The architecture must define layers,
   allowed dependency direction, and ownership boundaries that prevent
   high-level workflows and low-level infrastructure from becoming mutually
   entangled.
3. **Deliberate abstractions.** The campaign must introduce coherent
   abstractions around identified operational complexity. Exact consolidation,
   ownership, API, and lightweight collaborator-extension choices remain
   just-in-time decisions under the ratified migration and retirement
   guardrails. A mandatory universal Stage hierarchy, registry, workflow
   language, or second scheduler is already prohibited.
4. **A complete golden path.** A competent computational biologist must be able
   to go from a supported fresh installation to a valid synthetic result and
   find the report without understanding EMRYS's internal architecture.
5. **Role-based development and experience.** Scientist, advanced scientist,
   operator/site administrator, automation, and developer/maintainer needs must
   be explicit in interfaces, documentation, ownership, and validation.
6. **Preservation of guarantees.** Scientific semantics, provenance, artifact
   integrity, evidence, reproducibility, validation, transactional behavior,
   runtime identity, storage qualification, HPC correctness, failure visibility,
   and safe recovery must not be weakened merely to make the surface simpler.
7. **Doctor may repair only explicitly.** The earlier categorical requirement
   that Doctor never repair anything is overridden. Diagnosis remains the
   default; any repair must be separately invoked, bounded, disclosed,
   provenance-aware where applicable, and unable to silently invent biology,
   secrets, or mutate declared scientific inputs. Dependency repair delegates
   solving and installation to an established package manager for the selected
   environment; Doctor verifies explicit operator authority and owns
   orchestration, reporting, provenance, and requalification rather than
   reimplementing a package manager.
8. **Maintenance-surface compression.** Every architecture audit must record
   concrete opportunities to retain, consolidate, retire, or defer product
   logic, wrappers and compatibility paths, configuration, scripts, schemas,
   documentation, protections, and evidence. Each implementation slice must
   make the smallest complete vertical change, migrate callers, and retire the
   responsibility it supersedes. Net-negative maintained product code and no
   product-file growth are the defaults; an exception requires the user's
   approval of quantified growth and its justification, plus an owner and
   retirement condition when the growth is temporary. Before adding owned
   machinery, evaluate the existing repository authority, standard library,
   mature maintained tools/libraries, and the relevant established package
   manager; bespoke code must record the unmet capability or prove a smaller
   total maintained surface. Every touched shell
   surface receives a `KEEP`, `CONVERT`, or `RETIRE` disposition; conversion
   must reduce total maintained and cross-language surface rather than preserve
   a second implementation. Every slice touching a retained applicable
   operation also records its `LOG-05` disposition and incorporates adoption in
   the same vertical change when output or durable diagnostics change.
9. **Immutability by default; Run is the immutable plan.** Boundary values are
   immutable unless an owning contract justifies a narrow mutable lifecycle.
   Any architecture concept named `Run` denotes the immutable plan and is never
   modified in place. A changed plan requires a new plan rather than mutation
   of the existing Run. Public nouns, nesting, identity inputs, cardinalities,
   Attempt/Result relationships, APIs, backends, policies, persistence, and
   storage remain unresolved until after audit review and a separate approved
   decision.
10. **Evidence deletion requires explicit approval.** An audit may identify
    redundant evidence and propose its deletion, but no retained evidence is
    deleted without the user's separate explicit approval of the exact
    artifact or bounded class. The proposal must state the supported claims,
    producers and consumers, redundancy basis, retention and recovery effect,
    evidence-level effect, and rollback. Approved evidence deletion is isolated
    in its own commit and never offsets product-code growth.
11. **Shared platform boundaries require demonstrated consumers.** A shared
    policy authority requires at least two production owners making the same
    decision from equivalent inputs with the same complete semantics, followed
    by one caller-complete net-negative migration; trust-boundary re-admission
    is not duplication. Local Snakemake remains the only application backend
    and Slurm remains outer placement. A generalized backend must be evaluated
    near campaign closure but is implemented only for a concrete approved
    extension or demonstrated compression, with parity and no duplicate
    authority. Compression must be net-negative; extension growth follows the
    normal quantified-exception gate. A distinct Artifact Store is deliberately
    deferred until a separately approved concrete unmet need requires it.

`ARCH-CONST-01` also ratified five binding campaign guardrails in the
[architectural invariant constitution](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails):

- every effective operational value and source is inspectable, while overrides
  exist only at explicitly supported safe owner boundaries;
- abstractions may hide operational mechanics but not the science needed for
  review;
- migration is bounded and incremental rather than an unbounded rewrite;
- a replacement completes only after caller migration and relevant parity,
  with owned, bounded, protected temporary compatibility and an explicit
  retirement condition; and
- protections at external, filesystem, concurrency, crash/recovery,
  persistence, evidence, and supported public-behavior boundaries require a
  mapped equal-or-stronger surviving defense at the same evidence level.

On **2026-08-26**, the user ratified three additional campaign guardrails for
maintenance-surface compression, immutable-by-default design with `Run` as the
immutable plan, and approval-gated evidence deletion. These extend rather
than rewrite the historical five-guardrail `ARCH-CONST-01` result. Their
canonical definitions are `AC-GUARD-006` through `AC-GUARD-008` in the same
platform-direction decision.

On **2026-08-28**, the user refined the regression-defense rule: a check and
check-only test for a proven impossible same-process state may retire without
an artificial replacement, while high-risk, ambiguous, or directly
user-facing protection removal requires explicit approval. High-risk,
directly user-facing, execution-boundary, and evidence-validation retirement,
consolidation, or conversion requires approval whether or not classified as a
protection. Evidence deletion remains governed by its separate stricter gate.
The same update made `LOG-05`
disposition mandatory for touched retained operations and required every
touched shell surface to be retained, converted, or retired based on total
maintenance-surface reduction.

On **2026-08-29**, the user ratified the existing-tool-first rule, required
explicit Doctor dependency repair to delegate to established package managers,
and deferred speculative shared policy, generalized backend, and distinct
Artifact Store boundaries behind the concrete gates in requirement 11.
Named execution profiles and a Run Bundle remain favored directions rather
than settled interfaces; the proposed runtime modes remain acquisition
journeys toward one admitted runtime authority rather than three authorities.

## 4. Invariant constitution and source trace

`ARCH-CONST-01` completed the source, contract, and test reconciliation. The
[qualified 27-invariant register](../design/decisions/platform-direction.md#ratified-architectural-invariant-constitution)
is binding and distinguishes scoped current **Preserved** contracts from
binding **Target** requirements with named implementation gaps.

The statements below remain the original intake candidates for source
traceability. Their broader wording does not override the qualified register,
live owner contracts, or current evidence.

### 4.1 Scientific invariants

- Input orientation, sample relationships, cohorts, strata, conditions, and
  other biological meanings are explicit; EMRYS does not silently invent them.
- Scientific transformations are deterministic where the scientific contract
  expects determinism.
- Tools, statistical procedures, parameters, filters, thresholds, candidate
  universe, count construction, and multiple-testing family are recorded at
  sufficient precision to reproduce and audit the analysis.
- Reporting, orchestration, scheduling, and filesystem refactoring cannot
  silently alter scientific results.
- Scientific implementations remain recognizable and inspectable to a reader
  who understands the underlying biology and statistics.
- A workflow success, a computational candidate, a statistically selected
  result, and a biologically validated editing site remain distinct claims.

### 4.2 Provenance and artifact invariants

- A result is traceable to exact inputs, scientific configuration, source and
  package identity, runtime/tool identity, and the execution that produced it.
- Durable artifacts have stable, content-bound identities.
- Published artifacts cannot silently mutate.
- Generated manifests and normalized configuration remain inspectable even
  when users do not author them.
- There is one canonical path by which a candidate output becomes an admitted,
  validated, durable artifact.

### 4.3 Execution and recovery invariants

- An execution either completes according to its contract or is visibly
  incomplete or failed.
- Partial publication and provisional outputs are detectable.
- Recovery cannot silently produce a scientifically different result under the
  same identity.
- Resume reuses only compatible, admitted work and recomputes or rejects work
  when identities or contracts are incompatible.
- Local and HPC execution satisfy the same fundamental correctness and evidence
  guarantees even when their mechanisms differ.
- An immutable plan exists before execution, even when planning and execution
  form one conceptual user operation.
- Failure and repair actions remain attributable and auditable.

### 4.4 Evidence and reporting invariants

- Reported claims correspond to actual admitted artifacts and recorded
  validations.
- Validation evidence can be reproduced at its declared level.
- Scientific, evidence/provenance, and operational evidence remain
  distinguishable.
- Local engineering evidence, synthetic end-to-end evidence, cluster execution,
  scientific review, and biological validation are never promoted into one
  another without evidence.
- Receipts and low-level transaction records may be hidden from ordinary views
  but remain complete and available for forensic inspection.

### 4.5 User-boundary invariants

- Level-4 developer knowledge is never required for a Level-1 scientist task.
- Defaults, site policy, project values, and CLI overrides have one documented,
  inspectable precedence model.
- The system never prints secrets or silently creates biological meaning.
- Automatic actions are bounded, observable, and reversible or recoverable
  where the underlying operation permits it.

## 5. Target public model

### 5.1 Small conceptual vocabulary

Two compatible source models were proposed:

```text
Project
  |
  +-- Dataset
  +-- Reference
  +-- ExperimentalDesign
  +-- Runtime
          |
          v
         Run
          |
          +-- plan()
          +-- validate()
          +-- execute()
          +-- inspect()
          +-- report()
```

and the even smaller source proposal:

```text
Project / Analysis -> Run -> Result
```

`ARCH-MODEL-DECISION-01` now ratifies the compact public conceptual model as
`Project -> Analysis -> Run -> Results`, with Attempt progressively disclosed.
The method notation above remains intake traceability, not an authorization
for a mutable Run aggregate or a selected public application API. Exact
semantic fields, subordinate identity, and logical authorities are selected by
`ARCH-MODEL-FIELDS-01` in Section 8.1.3, and the first internal successor
construction and Run-last persistence are implemented. The active
`emrys.project.v1` definition now supplies shared Dataset and Reference
sections plus one or more human-named Analysis definitions. Each selected
Analysis is admitted as an immutable revision and bound to the existing
immutable Execution Plan, Run, and read-only Results machinery. Validation
admits every named Analysis; `run` and Doctor select one by `--analysis`, with
omission valid only for a single-Analysis Project. Generalized storage and a
broader package API remain Open; neither is required to use the completed
public CLI vertical.

### 5.2 Proposed public commands

The normal surface should express user intent rather than engine mechanics.
The table retains intake candidates; implemented selections are identified
explicitly and the remaining names are not settled:

| Intent | Suggested names retained from intake |
|---|---|
| Create or prepare a project | `emrys init project` is selected; a separate `setup` name remains unselected |
| Validate readiness | `emrys doctor` is selected; `validate` remains for admitted definitions rather than readiness |
| Plan and execute | `emrys run` is selected |
| Observe current work | `emrys inspect run` is selected; a separate `status` name remains unselected |
| Recover compatible work | `emrys resume` is selected |
| Inspect internals or provenance | `emrys inspect run` with progressive detail is selected; separate `explain`, `diagnostics`, and `debug` names remain unselected |
| Read or regenerate reports | `emrys report` is selected |
| Manage runtime modes | `emrys runtime discover` is selected; `accept`, `define`, and `install` remain unselected |
| Inspect or manage effective configuration | `emrys config` |
| Exercise a neutral synthetic path | `emrys init synthetic` is selected; the public `demo` name and surface are retired, with exact-head verification pending |

Noninteractive mutation uses the explicit `--execute` path; terminal journeys
may confirm before mutation. Raw engine commands are not the automation API.

### 5.3 Configuration ownership

| Configuration layer | Questions answered | Normal owner |
|---|---|---|
| Scientific | Which data, reference, samples, pairing, biological comparison, thresholds, regions, cohorts, and analyses? | Scientist |
| Execution | Where does it run, with which resources, scheduler, scratch, storage, and tool installation? | Operator or site administrator |
| Evidence | Which hashes, receipts, attempts, artifact identities, and immutable records establish provenance? | EMRYS, exposed for inspection |

A selected scientist-facing `emrys.project.v1` form is:

```yaml
schema_version: emrys.project.v1
dataset:
  samples: samples.tsv
reference:
  fasta: reference/genome.fa
  gtf: reference/genes.gtf
  star_index:
    sjdb_overhang: 149
    genome_sa_index_nbases: 14
analyses:
  primary:
    partitions: partitions.tsv
    control_condition: control
    treatment_condition: treatment
    target_change: A>G
    min_sample_dp: 1
    mean_dp_threshold: 50
    fdr_threshold: 0.05
    common_or_threshold: 1.2
    absolute_difference_threshold: 0.005
    background_condition: null
    background_max_fraction: 0.01
```

The Project file's parent is the Project root. Samples remain in one external
ordered TSV shared by the Project; each named Analysis references an external
partition TSV and owns its comparison, target change, and thresholds. FASTA,
GTF, and STAR-index parameters are shared Reference inputs. Analysis names are
human selectors rather than scientific identity inputs. EMRYS derives the
internal normalized workflow inputs, content-derived scope identities,
Execution Plan, Run identity, Attempt evidence, and reporting inputs without
requiring the scientist to author them. Every effective value remains
inspectable.

A proposed precedence model is:

```text
built-in defaults -> site/execution profile -> project values -> CLI override
```

The exact merge rules require a separately ratified contract.

### 5.4 Public identity and filesystem models

The proposed public identity hierarchy is:

```text
Analysis
  +-- Run
       +-- Attempt
       |    +-- Task
       +-- Artifacts
```

An ordinary operator should normally need only a Run ID and, when diagnosing a
retry, perhaps an Attempt ID. Commit, package, runtime, request, task, artifact,
and receipt identities remain nested metadata rather than disappearing.

A proposed public filesystem model is:

```text
emrys/
+-- project.yaml
+-- inputs/
+-- runs/
|   +-- RUN-ID/
|       +-- provenance/
|       +-- work/
|       +-- results/
|       |   +-- artifacts/
|       |   +-- reports/
|       +-- logs/
+-- runtime/
```

The exact layout remains open. The leading proposed user mental model is
project, inputs, runs, and one obvious result location. The binding requirement
is the broader outcome: no manual directory assembly and no hidden competing
report root.

## 6. Roles and progressive disclosure

Role-based design is binding. The levels below describe what each role needs;
they are not permission tiers and do not imply that one person cannot occupy
multiple roles.

| Level and role | Primary concerns | Normal surface |
|---|---|---|
| Level 1 — Scientist | Inputs, analysis intent, readiness, progress, results, and scientific limitations | Setup/init, validate/check, run, status, report |
| Level 2 — Advanced scientist | Full sample manifest, reference, regions, statistical parameters, validation details, reusable upstream data, and alternative analyses | Scientific configuration and detailed result inspection |
| Level 3 — Operator/site administrator | Runtime, scheduler, storage, resources, site policy, installation, diagnosis, and recovery | Profiles, Doctor, execution inspection, bounded repair, explicit overrides |
| Level 4 — Developer/maintainer | Contracts, stage and artifact lifecycles, transactions, identities, evidence internals, state transitions, and engine integration | Developer APIs, debug surfaces, source and architecture documentation |
| Automation | Stable noninteractive inputs, deterministic exits, machine-readable plans/status/results, and complete durable logs | Supported CLI/API contracts rather than private wrappers |

The governing rule is:

> Level 4 must never be required to perform a Level 1 task.

One source expressed the intended disclosure distribution as a nonbinding
heuristic:

```text
80%  emrys run
15%  emrys run --profile hpc
 5%  low-level policy/configuration and forensic interfaces
```

The percentages are not measured targets. They preserve the proposal that the
golden path should cover most work, profiles should cover most remaining
operational variation, and direct low-level control should be exceptional but
fully supported.

Documentation should follow the same disclosure model:

1. Scientist journey: what EMRYS does, required data, experiment definition,
   running, result interpretation, and scientific limitations.
2. Operator journey: supported installation, runtimes, storage, SLURM,
   resources, diagnosis, and recovery.
3. Developer journey: architecture, contracts, owners, lifecycles, provenance,
   evidence, tests, and migration rules.

One source suggested that the scientist layer might be approximately five pages
total. That is preserved as a candidate size target, not a documentation cap;
completeness, accessibility, and successful use remain the actual outcomes.

The same source set proposed an expert `emrys run --explain` view with this
exact illustrative plan: validate inputs; qualify the execution environment;
prepare the reference; execute scientific stages; validate artifacts; generate
evidence; publish the immutable run; generate reports. The sequence and command
remain nonbinding, but the example records the desired inspectability.

This role split must also guide code ownership and validation. A scientist-facing
change must not require operator internals; infrastructure changes must prove
scientific semantics unchanged; developer escape hatches must not become the
primary workflow by accident.

## 7. Target layering and dependency direction

`AC-SLICE-02` ratified the interpretation of this layering while leaving its
concrete APIs and package representation to later slices. The durable decision
is the
[responsibility and dependency model](../design/decisions/platform-direction.md#ratified-responsibility-and-dependency-model);
the original five-band proposal remains a useful responsibility view:

```text
+-----------------------------------------+
|                 CLI / UX                |
+-----------------------------------------+
|       Project / Run Application API     |
+-----------------------------------------+
| Scientific | Evidence | Reporting       |
+-----------------------------------------+
| Artifact | Execution | Policy | Identity|
+-----------------------------------------+
| OS / R / Python / SLURM / Filesystem    |
+-----------------------------------------+
```

The labels are not packages, classes, services, or a one-to-one owner roster.
The later `ARCH-MODEL-DECISION-01` decision makes `Project`, `Analysis`, `Run`,
and `Results` the compact public vocabulary and progressively discloses
`Attempt`; `Stage` remains only a proposal. `Run` is the immutable plan.
Reporting is downstream operational work rather than a semantic scientific
stage. OS, R, Python, SLURM, Snakemake, and filesystems are external mechanisms
reached through EMRYS-owned boundaries, not an internal authority layer.

The binding dependency rule is:

> Higher layers may request capabilities from lower layers. Lower layers must
> not depend on higher-level user workflows.

Consequences include:

- scientific stages do not implement scheduler, runtime, storage, or
  transaction behavior;
- reporting does not publish upstream artifacts or mutate upstream scientific,
  artifact, execution, or attempt state; it may publish its own derived report
  transaction;
- validators do not implement runtime discovery;
- CLI code does not implement scientific semantics;
- stages do not independently reinvent provenance or evidence;
- infrastructure does not need to understand scientific report presentation;
- Snakemake remains an execution mechanism, not scientific or application
  authority and not a required user concept.

Source imports, runtime/control invocation, and artifact/evidence flow are now
three explicitly separate graphs. Permission in one does not imply permission
in another. The current-owner crosswalk remains descriptive, and its exact
current CLI-composition seams and Python import transitions are ratcheted;
neither becomes the target stack.

One source summarized the desired internal conceptual consolidation as:

```text
Domain -> Stage -> Run
```

Here, Domain is visible scientific logic and Stage is a possible thin
operational boundary. The source used Run for possible global coordination,
but the later binding decision reserves `Run` for the immutable plan rather
than a mutable coordinator. Inventory must establish the actual mapping.
`AC-SLICE-02` did not select the remaining nouns, a Stage interface, or an
application API.

## 8. Proposed abstractions and guardrails

### 8.1 Project and Run application boundaries

**Direction resolved; public CLI realization substantially implemented:**
`ARCH-MODEL-DECISION-01` selects
model C and the compact public relationship
`Project -> Analysis -> Run -> Results`, with `Attempt` progressively disclosed
when operationally relevant. An admitted Analysis revision and the effective
Execution Plan are separate immutable values bound by the public immutable
Run. The model permits multiple Runs for one Analysis revision and multiple
analyses over compatible upstream artifacts. Application coordination may
admit intent, bind a Run, invoke lower capabilities, and assemble outcomes,
but it cannot absorb scientific, execution, policy, artifact, evidence, or
reporting authority.

Lower capabilities receive explicit immutable supported information rather
than importing a broad higher-level aggregate or independently reconstructing
competing identity. Draft construction, attempt-local execution state, locks,
logs, and transactional publication may mutate only inside an explicit owner
and cannot alter or reconstruct the Run. `ARCH-MODEL-FIELDS-01` now selects
exact semantic fields, identity composition, Attempt variation, logical
authorities, and recovery ownership. The first successor cutover now realizes
immutable canonical Analysis-revision, Execution-Plan, and Run-binding types
and schemas; durable Run-last admission; current-path new-Run planning,
execution, resume, and inspection; historical read/resume; and a temporary
one-way workflow/task/reporting projection. A subsequent bounded cutover
retired that projection: workflow/task now admit exact successor Run authority,
and reporting uses exact Attempt-owned inputs bound by the origin config. The
current public-model cut adds the closed `emrys.project.v1` source, admits all
named Analyses, selects one Analysis for Run or Doctor readiness, and connects
that immutable revision to the same Execution Plan, Run, Attempt, and Results
authorities. New work rejects request-v3; exact request-v3 reconstruction is
isolated to historical resume. Generalized storage and package APIs remain
`AC-DEC-011` work. Generalized backend and shared-policy boundaries follow the
later ratified concrete-consumer gates.

`ARCH-MODEL-AUDIT-01` completed the current-state prerequisite below.
`ARCH-MODEL-DECISION-01` then resolved `AC-DEC-001` and the model/boundary
portion of `AC-DEC-011`; `ARCH-MODEL-FIELDS-01` completes the bounded semantic
field-and-authority package in Section 8.1.3. The first caller-complete
Run-authority implementation boundary subsequently realizes that package for
the current local-pilot path without completing the broader campaign card.

Consumers now receive the narrow admitted Analysis value needed by Run
construction rather than a broad mutable Project aggregate. Exact Analysis,
Execution-Plan, Run, and Attempt semantic identity inputs are fixed;
role-tiered Run identity and expert inspection use the existing control and
read-only inspection routes. The public package/import API, generalized
storage relationships, and remaining non-CLI migration stay Open. The
semantic boundary is settled: identity-bearing effective
toolchain/backend/profile/resource-policy changes Run; actual realization
within the declared envelope belongs to
Attempt; reporting changes neither Run nor Attempt. User-authored
Project schema and current CLI mapping are selected; package/import surfaces,
compatibility duration, generalized storage relationships, and later migration
order remain unsettled. Attempt-v1 evidence field names and records remain
unchanged, and no Attempt-v2 or evidence deletion is introduced. A generalized
backend and shared policy layer are conditional on the ratified concrete
consumer/net-reduction gates, not unconditional unsettled deliverables.
Reporting itself
is already default-on for a full run,
disable-able, independently regenerable, and downstream of scientific
completion.

### 8.1.1 `ARCH-MODEL-AUDIT-01` current application-model audit

> **Observed baseline, not a design decision.** This read-only audit mapped the
> current application/control flow, representations, semantic lifetimes,
> owners, callers, identity inputs, mutable state, protections, evidence, and
> candidate compression at exact source revision
> `6524ed7967090319cf4ae62ae1b2edf31e9ca02d`. It does not select public nouns
> or nesting, plan fields, APIs, package placement, persistence, execution
> backends, state vocabulary, compatibility policy, or migration order. The
> only target-model constraint applied here is that **Run is an immutable
> plan**; changing the plan creates a different Run.

`ARCH-MODEL-AUDIT-01` is complete as the current-state audit prerequisite.
Per the approved recording boundary, `AC-SLICE-03`, `CONTROL-01`, `RUN-03`,
`IDENTITY-01`, and broad `ARCH-01` remain Open; no model decision or bounded
implementation is completed here.

#### Audit scope and reproducible method

The implementation baseline is exact source revision
`6524ed7967090319cf4ae62ae1b2edf31e9ca02d`. This record is stacked on the
later documentation-only campaign-guardrail commit
`4c3f50ced83859083127501d5e40e4c03554a833`; that commit changed no product
source in the audited roster. The audit used tracked source, contract, schema,
test, configuration, workflow, CLI, and journey-document inspection. It did
not use generated, ignored, untracked, installed-environment, workspace,
runtime, or run-output files as inventory inputs.

The bounded product/schema roster and physical-line count are reproducible
from the reviewed revision with:

```sh
git ls-files -- \
  src/emrys/contracts/orchestration \
  src/emrys/contracts/schemas/orchestration \
  src/emrys/orchestration/local_pilot
```

That command returns 43 files. Summing `wc -l` over those exact paths—where a
physical line means one newline-counted line—returns 22,395 lines. Filtering
that same roster to filenames ending in `.py` returns 19 files and 18,892
lines. The direct contract/local-pilot test and support roster is:

```sh
git ls-files -- \
  tests/contracts/orchestration \
  tests/orchestration/local_pilot
```

It returns 27 files and 17,776 physical lines, including the tracked contract
README. These totals deliberately exclude `src/emrys/__main__.py`,
`pyproject.toml`, `workflow/Snakefile`, the fixed workflow contract/profile,
`configs/`, Quickstart and other documentation, generated files, runtime
environments, and run data. Those surfaces were inspected separately where
named below; the exclusions prevent the footprint caption from implying a
larger roster than was actually counted.

#### Current control flow

The current entry and follow-up paths are separate; they do not form one
automatic pipeline:

```text
emrys
  +-- init project/manifests/synthetic -> bounded Project or draft publication
  +-- validate project -> Project/request admission only
  +-- doctor -> Project readiness and explicit managed repair
  +-- run -> control -> Doctor -> normalization -> resource/capacity policy
  |    -> AttemptPlan
  |       +-- dry-run -> print plan; no workspace write
  |       +-- --execute -> create run skeleton -> lifecycle admission
  |            -> local Snakemake executor -> functional-owner tasks
  |            -> artifact index -> run summary -> HTML reports
  |            -> terminal attempt receipt
  +-- resume -> inspection/readiness -> AttemptPlan -> optional execution
  +-- inspect run -> explicit read-only derived inspection
  +-- report -> independent dry-run-first report regeneration
```

Ordinary `emrys run` does not invoke onboarding or the explicit request-
validation command, and full `inspect_run` is an explicit command or an
internal resume/lifecycle check rather than an automatic post-receipt step.
The private Slurm transport submits one frozen plan and re-enters the same
single-host backend inside the allocation, as recorded below.

The installed entry point is [`emrys.__main__:main`](../../pyproject.toml).
The current composition root is a 534-line
[`__main__.py`](../../src/emrys/__main__.py) with ten top-level command groups:
`init`, `prepare`, `build`, `doctor`, `run`, `resume`, `reconcile`, `inspect`,
`convert`, and `validate`. This is a supported compatibility surface, not the
accepted target CLI.

Current onboarding generates seven user-visible starter members—
`request.yaml`, `emrys.launcher.yaml`, `emrys.resources.yaml`, `samples.tsv`,
`partitions.tsv`, `runtime.tsv`, and `run-in-slurm.sh`—then publishes
`starter-set.manifest.tsv` last. The repository also contains 20 tracked files
under `configs/`. These counts establish the present operational surface; they
do not by themselves authorize consolidation or removal.

The normal `run` command still requires explicit request, workspace, and
runtime-profile paths. Its primary plan output includes the run ID and root,
workflow-attempt ID, owner-job count, thread/concurrency/memory details, three
reporting transactions, the raw Snakemake command, and every pending producer
and validator command. Those details are useful expert evidence but exceed the
intended ordinary control plane.

At the audited revision, the [quickstart](../../quickstart.md) also told the
operator to create and populate the input-directory tree manually, redirect a
complete runtime profile to a new filename, copy the run root from a dry-run,
and repeat that transfer from a completed Slurm dry-run log before execution.
Section 13.12 supersedes the two-invocation Run guidance; the remaining setup
work still confirms that safe internal boundaries leak user-as-glue work.

#### Current owner and caller map

| Current owner or surface | Current responsibility | Principal callers or consumers | Audit conclusion |
|---|---|---|---|
| [`__main__.py`](../../src/emrys/__main__.py) | Parse and compose all installed command routes | Scientists, operators, automation, owner commands | Composition root, not a semantic application model; ordinary and expert capabilities are interleaved. |
| [`onboarding.py`](../../src/emrys/orchestration/local_pilot/onboarding.py) | Starter generation, request compatibility validation, and generated one-allocation Slurm wrapper | `init`, `validate local-pilot-request`, generated wrapper | Owns several setup, validation, and scheduler-launch concerns that later role journeys must repartition without weakening create-absent publication. |
| [`normalization.py`](../../src/emrys/orchestration/local_pilot/normalization.py) | Admit authored intent and construct the canonical execution identity | Onboarding validation, Doctor, control, reporting projection | Closest current semantic plan source, but it returns shallowly frozen mutable structures and is not a selected public Run API. |
| Orchestration [`api.py`](../../src/emrys/contracts/orchestration/api.py), schemas, and package exports | Validate closed records, canonicalize bytes, recompute identities, and expose the deliberate current contract API | Normalization, materialization, lifecycle, task/reporting boundaries, inspection, projection, workflow owners, packaging tests | Current contract authority and compatibility boundary; model consolidation must preserve historical admission and must not silently widen the public import surface. |
| [`doctor.py`](../../src/emrys/orchestration/local_pilot/doctor.py) | Project, input, storage, runtime, and execution readiness plus separately authorized managed-runtime repair | Top-level Doctor and internal Run/resume readiness | Composes the existing Project/runtime/storage authorities, delegates repair to established package managers, logs only confirmed mutation, and requalifies. It preserves site/user profiles and declared inputs. |
| [Runtime-availability inspector](../../src/emrys/evidence/runtime_availability/inspector.py) and [storage-qualification owner](../../src/emrys/evidence/storage_inventory/qualification.py) | Declare/admit runtime availability and final two-phase storage evidence | Direct inspect commands, Doctor readiness, materialization bindings, lifecycle re-admission, runtime/storage tests | Independent evidence authorities outside the 43-file roster. Doctor composes them and lifecycle re-admits them before execution; future capability placement must preserve that attribution and recheck. |
| [`control.py`](../../src/emrys/orchestration/local_pilot/control.py) | Compose Doctor, normalization, resources, attempt planning, execution, resume, and inspection output | `emrys run`, `resume`, `inspect local-pilot-run` | Nearest current application coordinator; it still exposes attempt, engine, owner-job, and transaction detail directly. |
| [`resource_policy.py`](../../src/emrys/orchestration/local_pilot/resource_policy.py) and [`capacity.py`](../../src/emrys/orchestration/local_pilot/capacity.py) | Resolve effective per-stage/report resources and observe/admit available allocation capacity | Control planning, materialization/workflow configuration, launcher and resource tests | These owners materially shape the effective executable plan even though their values do not enter current `run_id`; final policy/application placement remains Open. |
| [`materialization.py`](../../src/emrys/orchestration/local_pilot/materialization.py) | Build a complete no-write `AttemptPlan`, workflow config, task dispatches, and fixed/attempt files | Control and lifecycle materialization | Current attempt-planning representation, not a selected Run model. Whether any class, package, or facade is later public remains Open. |
| [`lifecycle.py`](../../src/emrys/orchestration/local_pilot/lifecycle.py) | Serialize admission, own the run lock, execute the delegated process, bind recovery evidence, and publish the terminal receipt last | Control, task/reporting boundaries, inspection | Strong operational transaction authority cannot be transferred into application coordination. Future class/package/facade placement remains Open. |
| [`task.py`](../../src/emrys/orchestration/local_pilot/task.py) and [`reporting_boundary.py`](../../src/emrys/orchestration/local_pilot/reporting_boundary.py) | Admit one owner scope or reporting transaction and publish start/attempt/verified records | Fixed Snakemake workflow and lifecycle | Retain functional and downstream transaction authority; do not move it into application coordination around Run. |
| Fixed [`Snakefile`](../../workflow/Snakefile), workflow contract, and local profile | Declare the reviewed task graph, fixed scientific-owner invocations, target, and local engine configuration | Materialization, local Snakemake execution, task/reporting boundaries, contract and end-to-end tests | Effective execution surface and current engine adapter; not application or scientific authority and not included in the 43-file footprint total. |
| [`inspection.py`](../../src/emrys/orchestration/local_pilot/inspection.py) | Derive separated Run, Attempt, Results, reporting, and recovery status from canonical contracts, records, receipts, and the owned lock | Control, lifecycle resume checks, tests | Read model only. The current `RunInspection` name is descriptive and does not select the target Run representation. |
| [`projection.py`](../../src/emrys/contracts/orchestration/projection.py) and reporting owners | Project the execution contract into reporting contracts and render admitted results | Normalization, materialization, workflow, standalone `build report` | Downstream reporting remains separate from scientific completion and is not a scientific stage. |
| `launcher_config.py` at the audited revision | Resolve outer Slurm allocation defaults/configuration/environment/overrides and submit once | Generated `run-in-slurm.sh` | Historical scheduler-transport owner later retired by Section 13.6; it was never a second application backend or scientific authority. |
| [`dashboard.py`](../../src/emrys/orchestration/local_pilot/dashboard.py) | CSU preview using scheduler queries plus parsed stdout/Snakemake stderr | `make dashboard` only; no production Python importer | Non-authoritative, stale presentation with text coupling and fixed six-sample/25-partition assumptions that disagree with the current starter. Freeze it during the campaign: do not update or extend it, implement `OBS-02` independently from persisted records, and reconsider retirement only after campaign completion and explicit approval. |

#### Representation and semantic-lifetime map

| Current representation | Lifetime and current persistence | Current authority | Relationship to the target model |
|---|---|---|---|
| Authored request YAML plus sample/partition TSVs | Evolvable external intent; an exact request copy is retained per attempt | Operator intent before admission | Possible Project/Analysis input, not a Run after admission. |
| `NormalizationBundle` | One no-write normalization result in memory | Normalization result plus non-identity admission evidence | Contains the closest current plan analogue but is only shallowly frozen. |
| `emrys.execution.v1` and `contract/normalized.json` | Deterministic canonical execution contract; published only when an execution attempt materializes the run root | Immutable local-run identity | Closest current analogue to the target immutable Run; it is not yet selected as Run and does not include the full effective execution choice. |
| Identity envelope and `run_id` | Deterministic digest of workflow profile, samples, partitions, reference, and analysis policy | Canonical execution contract | Current local-run identity, not a decision about future Run identity composition. |
| `AttemptPlan` | One in-memory execute/resume plan with time/token/host/process/resources and planned files | Control/materialization | Operational attempt plan. A frozen dataclass contains mutable mappings, so the boundary is not deeply immutable. |
| `workflow-attempt` record and workflow config | One persisted execute or resume invocation | Lifecycle and attempt schema | Current Attempt analogue; it binds source, runtime/tool, resource, executor, and command facts omitted from `run_id`. |
| Task dispatch/start/attempt/verified records | One functional-owner scope within an attempt, with reusable verified state across compatible attempts | Task boundary and owner validation | Internal operational/evidence detail; not required ordinary public vocabulary. |
| Reporting start/verified records and report receipt | One downstream report transaction/output identity | Reporting owners | Derived output that may be regenerated; not a semantic scientific stage or Run mutation. |
| Attempt receipt | Terminal outcome of one workflow attempt | Lifecycle, published last | Attempt outcome and evidence, not a general application Result. |
| `RunInspection` | Regenerated separated read-only status domains | Inspection over persisted authorities | Current status projection. It is not persisted authority and must not define target Run mutability. |
| Dashboard dictionaries and stream caches | Mutable presentation state for one stale live view | Dashboard only | Frozen transitional UI state, not application or evidence authority; it receives no architecture-campaign updates. |

There is no current application-level `Project` or `Result` representation.
`WorkflowResult` reports the delegated process exit and `LifecycleOutcome`
reports one terminal attempt; neither is the campaign's possible public
Result. At audit time, the current run root was an aggregate namespace
containing an immutable contract, evolving attempts, locks, task/report state,
native results, products including reports, attempt-local stream logs, and
disposable engine metadata. It had no top-level report surface; generated
reports lived under `products/report/<run-id>/`. `RESULTS-01` subsequently
established the current scientist-facing surface at
`results/{editing,scientific_context,reports}` and moved nonfinal/QC workflow
artifacts to `products/native`, without making the run-root directory or
`RunInspection` the target immutable Run. Exact legacy-profile report ledgers
remain readable only as historical evidence.

#### Current identity boundary

Normalization constructs an identity envelope from:

- the fixed workflow profile ID, version, and canonical digest;
- the ordered sample-manifest snapshot, normalized rows, and FASTQ path, size,
  and content identities;
- the ordered partition-manifest snapshot, normalized rows, and any selector
  file identities;
- reference ID, FASTA/GTF path, size, and content identities plus STAR-index
  parameters; and
- cohort, primary-analysis ID, normalized analysis policy, and policy digest.

The current execution record repeats profile, samples, partitions, reference,
and analysis both at its top level and inside `identity_envelope`, then requires
exact equality before hashing. That duplication is validated today and cannot
be removed without a schema/consumer migration.

| Change or fact | Current `run_id` effect | Current placement |
|---|---|---|
| Bound sample/reference/selector content, manifest order, analysis policy, or fixed workflow-profile digest | Creates a different ID | Identity envelope |
| Absolute paths embedded in admitted manifest/input/reference snapshots | Affects the digest; relocating otherwise identical bound files therefore changes the current ID | Identity envelope; this is an implementation inference from the hashed snapshots, not a target portability decision |
| Request label, YAML formatting, or omitted-versus-explicit normalized null | No change | Attempt metadata or normalized away |
| Workspace, source checkout/commit, runtime profile/tools, resources, executor, host/process, attempt time/token, or resume predecessor | No change | Workflow-attempt/configuration records |
| Reporting enabled/disabled | No current full-run option exists; no target identity rule is implied | Reporting is currently mandatory in the lifecycle tail |
| Reporting `run_contract_sha256` | Narrower five-component reporting projection only | Reporting contract; explicitly not complete orchestration identity |

The current `run_id` is consequently a deterministic digest of the current
path-sensitive identity envelope, while `AttemptPlan` contains a fuller
effective operational plan. Giving that digest a durable scientific or public
semantic label is part of the still-Open identity decision. Whether target Run
follows either boundary or composes separate immutable intent and execution-
plan records remains Open.

#### Plan, execute, and scheduler observations

At the audited revision, `plan_run` performed readiness, normalization,
resource resolution, and attempt planning without writing workspace state. In
one `emrys run --execute` invocation, the same in-memory `AttemptPlan` was
printed and then executed. A plain dry-run persisted no accepted plan. A later
`emrys run --execute` recomputed normalization/readiness and created a new
attempt time, token, owner token, process identity, and attempt paths. The user
therefore could not approve and execute the exact prior dry-run plan, and there
was no interactive confirmation between plan display and mutation.

Section 13.12 closes that audited direct-control gap: one terminal invocation
builds and displays one `AttemptPlan`, then executes that same frozen object
only after confirmation. Whole-Run Slurm constructs one frozen submission plan,
displays its placement summary, and after confirmation submits that same object
once; the compute delegate still constructs the immutable Run only after it can
bind the admitted Slurm job ID.
The submit host does not manufacture compute-allocation readiness or a Run plan
it cannot admit.

The current ordering has an important qualification. The normalized execution
contract candidate and the in-memory `AttemptPlan` exist before mutation, but
`_default_execute()` calls `initialize_run()` first, creating and syncing the
workspace/run skeleton. Only afterward does argument evaluation materialize
`plan.preparation`, whose property canonicalizes the current mutable
`attempt_record` into exact attempt-preparation bytes for lifecycle admission.
Whether that is a contract violation depends on which fields the future Run
plan contains, so the audit does not decide it. It does record a real gap: if
attempt-specific fields belong to Run, the exact immutable plan is not frozen
before the first write; if they remain Attempt facts, the normalized Run
candidate predates mutation but the shallow mutable aggregate still needs a
single immutable authority. A future journey may compose validation, plan
display, confirmation, and execution without requiring run-root transfer, but
the selected Run must be exact and immutable before its first execution
mutation.

The same order has a recovery consequence. Initial execution creates and
syncs the workspace, `runs/`, run root, and `attempts/`, `locks/`, and `state/`
directories before exact attempt-preparation admission, signal control, or
attempt-mutex acquisition. Failure in that interval can leave a create-absent
run skeleton with no attempt or terminal receipt, while a later `plan_run`
rejects the already-existing root. The audit records that unreceipted-skeleton
state and owner/recovery gap without choosing whether planning, lifecycle,
reconciliation, or another bounded capability should resolve it.

At the audited revision, the generated Slurm path was an outer single-node
allocation wrapper:

```text
submit host
  -> resolve LauncherPlan
  -> sbatch --nodes=1 --ntasks=1 ...
  -> generated wrapper inside allocation
  -> validate request
  -> emrys run
  -> Doctor readiness gate
  -> Snakemake local executor on the allocated node
```

It is not currently a separate application execution backend. Successor
Attempts derive their executor from the admitted immutable Execution Plan;
that value remains `local` for the only current scientific backend. The
Attempt's structured allocation provenance records the exact Slurm job ID, or
null for direct execution, without changing Run identity. Historical
three-field allocation records remain readable. Scheduler state and the
terminal lifecycle receipt remain separate authorities.

The generated wrapper no longer invokes a second standalone Doctor between
explicit request-compatibility validation and `emrys run`; the Run-control
readiness failure retains Doctor remediations. The remaining normalization and
re-admission points are not declared redundant: lock-time and pre-mutation
admission must remain deliberate, and any future explicit Doctor repair must
be followed by re-admission rather than carrying stale facts across mutation.
Section 13.6 records the later retirement of that wrapper and split
configuration path; this paragraph remains the exact audit baseline.

#### Status, Result, and reporting cutover

Before the first read-model cutover, `RunInspection` exposed five aggregate states:
`prepared`, `running`, `resume_available`, `blocked`, and
`local_pipeline_complete`. Attempt receipts separately expose
`succeeded`, `failed`, `interrupted`, or `blocked`.

The read model now derives Run integrity, scientific Attempt outcome,
scientific Results status, reporting status, and recovery availability
independently. Control and lifecycle recovery decisions use the separated
domains; verified report paths remain visible independently of the legacy
combined receipt status. Receipt-v1 and its `local_pipeline_complete` field
remain unchanged historical evidence. The superseded aggregate `state`,
`resume_available`, and `local_pipeline_complete` Python accessors are retired
after current callers migrated to the separated domains.

The operational cutover is now implemented. The scientific workflow stops at
`cohort_slice`, releases the Run lock, and publishes a receipt-v2 Attempt before
public control invokes reporting. `run` and `resume` report by default and
accept `--no-report`; `emrys report --run-root ...` plans or reuses without
writes and generates only with `--execute`. Reporting creates no Run or Attempt
and cannot change scientific success. The low-level build commands are retired;
one fixed Run-oriented coordinator fails closed on partial or ambiguous state.

#### Run-control boundary compression

The grouped `emrys run`, `emrys resume`, and `emrys inspect run`
routes are now the sole supported Run-control surface. Their no-write planning
and execution helpers remain private implementation details, and the grouped
CLI composes all three routes through one controlled-runtime adapter instead of
three duplicate forwarding functions. This changes no command, argument,
output, Run/Attempt authority, execution behavior, or persisted format.

The subsequent narrow Project vertical now owns active scientist intake.
Terminal confirmation and report opt-out/regeneration are implemented; broader
argument ownership, final command naming, and higher-level execution-profile
selection remain later work.

#### Request-to-Analysis intake hardening

The preceding hardening cut kept the existing authored request as a temporary
Project-source/provenance adapter and introduced no public Project type,
schema, command, or filesystem layout. Admission retained immutable authored
source bytes, canonical profile bytes, canonical construction bytes, and the
admitted Analysis revision. Compatibility mappings are reconstructed as fresh
views, so a caller cannot mutate later views, Analysis identity, historical-v1
bytes, or subsequent Run construction.

This first implemented the immutable admission boundary beneath future Project
intake. The subsequent narrow vertical directly replaces
`NormalizationBundle` with owner-local immutable `ProjectAdmission`, publishes
`project.yaml`, and makes `emrys validate project`, `emrys doctor`,
and `emrys run` accept only `--project`. `RunCandidate.project.analysis` binds
the admitted Analysis to the existing immutable Execution Plan and Run, while
the existing read-only Results surface remains unchanged. The current closed
`emrys.request.v3` shape is deliberately reused as a temporary adapter; no
second schema, storage model, registry, backend, policy abstraction, or public
root-package API is introduced.

That statement records the first vertical at its implementation boundary.
Section 13.20 now supersedes the adapter on the active path with closed
project-v1 and named Analyses; request-v3 survives only for exact historical
resume.

Doctor admission, fresh post-Doctor Project re-admission, and lifecycle's
lock-time exact-source re-read remain distinct mutation-window defenses.
Persisted workflow-attempt fields and snapshots retain their request-era names
for historical evidence compatibility. The Project nesting/schema and external
sample/partition TSV choices are now selected. Broader discovery/edit
lifecycle, configuration precedence, generalized storage, and public
package/error design remain Open.

#### Mutation inventory

The strongest current immutability is in validated canonical bytes and
create-exclusive persisted records, not in every Python aggregate:

| State | Current owner and lifetime | Writers | Readers | Why mutation exists now | Immutable-boundary disposition |
|---|---|---|---|---|---|
| Project/Analysis admission drafts and immutable admitted views | `normalization.py`; local drafts live only during one admission call, then `ProjectAdmission` retains exact source bytes and a tuple of `AnalysisAdmission` values retaining canonical profile, workflow-input, authored-path, and Analysis-revision bytes | Admission builders populate local parsed and normalized mappings; callers receive only fresh disposable mapping views from immutable bytes | Project validation, Doctor, control, projection, materialization, tests | Draft parsing and snapshot admission remain naturally incremental; no shared post-admission mapping is mutable | Implemented for project-v1 and all named Analyses. The selected `AnalysisAdmission` connects directly to Run construction; broader discovery/edit lifecycle and root-package APIs remain Open. |
| `AttemptPlan.attempt_record` and nested bundle | `materialization.py` and control; one execute or resume planning invocation through lifecycle handoff | `build_attempt_plan` constructs it; an injected control transformer may replace the plan before return; audited in-repo local-pilot callers showed no later mutation | Control display/execution, materialization publication, lifecycle admission, tests | Construction combines readiness, resources, identity, time/token/host/process, files, and command facts; later mutability is incidental | Implemented handoff: the plan projects one canonical byte payload before mutation; lifecycle admits it once and publishes those exact bytes. Whether further Attempt fields belong to Run remains Open. |
| `LifecycleRequest.attempt_record_bytes` | Planning-to-lifecycle handoff; one materialized attempt admission | `AttemptPlan.lifecycle_request` carries the already-canonical Attempt bytes; `publish_attempt` only materializes planned files and returns no second request | Lifecycle admission, identity/resource/argv rechecks, exact Attempt publication, tests | No mapping crosses the boundary and no post-handoff mutation is required | Implemented immutable admitted request value; do not conflate it with live lifecycle transaction state. |
| `LifecycleOutcome.receipt` | Lifecycle-to-control handoff; one terminal attempt return | Lifecycle builds the terminal receipt/outcome after receipt-last publication | Control result projection, verified-report display, tests | Dictionary construction mirrors the persisted schema; post-return mutation is not required | Candidate immutable terminal view over persisted evidence; receipt file remains authority. |
| `TransactionSignalController` and delegated-process state | `lifecycle.py`; from signal-handler installation through receipt commit/restore | Signal handlers and lifecycle execution update child, signal, interruption, and commit state | Lifecycle cleanup, termination, receipt publication, fault tests | Live process and signal ownership must change as execution advances and cannot be modeled truthfully as a fixed value | Retain tightly owned mutation. Expose only immutable outcome/evidence values after the transaction. |
| `_OwnedRunLock` bytes, inode, and live lock ownership | `lifecycle.py`; from exclusive lock acquisition through release/recovery publication | Lock acquisition constructs exact bytes and inode identity; lifecycle changes filesystem ownership state and publishes release evidence | Lifecycle serialization/recovery, inspection, resume, fault tests | Owned filesystem lock state must transition with attributable identity; the duplicate parsed-record mirror was not required | Implemented minimal immutable in-memory proof plus narrowly owned live lock mutation and exact release/history records. |
| `RunInspection` nested attempt, receipt, task, and report dictionaries | `inspection.py`; one read-only inspection call/result | Inspection derives the aggregate from persisted authorities | Control, resume/lifecycle checks, tests | Mutable dictionaries simplify construction; post-construction mutation is not authority or required behavior | Keep a derived non-authoritative read model and make exposed boundary values immutable when selected; never persist it as status authority. |
| `ReportingBundle` dictionaries beside exact bytes | Contract projection; one deterministic reporting projection | Projection constructs reference, policy, run-contract, and inventory documents and bytes | Materialization, workflow/reporting owners, projection tests | Incremental projection is convenient; the admitted dictionary and byte forms need no later shared mutation | Candidate one immutable projection authority with derived views; preserve deterministic exact output and separate reporting transaction authority. |
| `TaskDispatch.scope` and admitted dispatch collections | Task boundary; one functional-owner invocation | Task admission constructs the closed dispatch value from canonical bytes | Producer/validator invocation, stream capture, task publication and tests | Parsing constructs nested values; execution needs stable facts, not mutable shared ownership | Candidate deeply immutable admitted dispatch; canonical dispatch bytes and schema remain authority. |
| `TaskOutcome.task_attempt` and `verified_task` | Task boundary; one successful owner return | Task transaction builds the dictionaries after create-exclusive publication | Workflow/lifecycle caller and task tests | Dictionary form mirrors persisted records; post-return mutation is not needed | Candidate immutable result view; persisted task attempt and verified records remain evidence authority. |
| Reporting-boundary `_AdmittedIdentity` dictionaries | Reporting boundary; one report transaction admission | Reporting admission loads and validates execution, profile, attempt and references | Reporting start, semantic validation, verified publication and tests | Admission assembles related mappings; downstream mutation is not required | Candidate immutable internal admitted identity; final neutral shared admission owner remains Open and reporting ordering stays local. |
| `_TaskStreamCapture` descriptors, digests, sizes, and completion state | `task.py`; one functional-owner process invocation | Stream callbacks and cleanup update descriptor/capture state | Task attempt/log/verified publication and fault cleanup | Streaming output identities and descriptors are only known while the process runs | Retain narrowly owned mutation; publish immutable stream evidence at the boundary. |
| Dashboard `StreamCache` and presentation dictionaries | `dashboard.py`; one stale live dashboard session | Scheduler/log polling and parsing update cached state | Dashboard rendering and dashboard tests | The state exists only for a non-authoritative presentation surface and duplicates status concepts using parsed human text | **Freeze during the campaign.** Do not update, extend, or make it authoritative; reconsider whole-surface retirement only after campaign completion and explicit approval. |
| Filesystem locks, create-exclusive publications, and transaction progress | Lifecycle, task, and reporting owners; one attempt or transaction plus recovery lifetime | Owned lock/process/publication operations mutate filesystem state; receipts are committed last | Lifecycle and owner recovery, inspection, resume, audit consumers | Concurrency, crash recovery, attribution, and durable publication require controlled state transitions | Retain controlled mutation and immutable committed records. Consolidation may share primitives but cannot merge semantic owners or erase ordering/fault behavior. |

Text and caller inspection within the exact in-repo contract/local-pilot roster
found no post-return product mutation of the principal plan dictionaries. This
was not dynamic proof and does not cover unknown external callers; the type
boundaries do not enforce the observed convention.
Persisted canonical records, hash recomputation, and—after preparation is
formed—prepared-versus-materialized byte equality currently prevent several
mutation races and must remain equal or stronger through any consolidation.

#### Protections and evidence disposition

These rows are the retain/evidence portion of the mandatory Section 13.1
register. For every retained row, the directional estimate and audit actual
are zero changed product files/lines, public concepts, configuration artifacts,
call edges, and compatibility paths. A later slice that changes one must supply
its own exact category deltas and boundary/risk disposition. Boundary defenses
require equal-or-stronger surviving protection; a proven same-process
impossible-state check may retire without replacement under `AC-GUARD-005`.

| Mechanism and category | Current owners; callers and consumers | Unique retained need; redundancy evidence | Disposition and surviving authority | Estimated and audit-actual deltas | Preconditions for any future change |
|---|---|---|---|---|---|
| Closed schemas, canonical JSON, digest recomputation; protection/schema | Orchestration contract API and versioned schemas; every normalization, materialization, lifecycle, task, reporting, inspection, workflow and historical reader | Defines admitted shape and identity and independently rechecks bytes; no equivalent independent authority was found | **Retain.** Versioned contract/schema owner survives | Estimate all six zero; audit actual all six zero | A successor must prove current and historical admission, canonical bytes and digest parity before old support changes |
| Stable-file snapshots, no-follow descriptor/path binding and near-mutation rechecks; protection | Normalization, lifecycle, task, reporting and inspection; input admission, publication, recovery and adversarial tests | Prevents path replacement, symlink, inode and stale-read races; similar helpers have owner-specific semantics, not proven redundancy | **Retain; conditional primitive consolidation only.** Each current semantic owner survives | Estimate all six zero for retention; audit actual all six zero | Map large-file, inode, destination, hash, timing and error behavior and retain last-safe-boundary checks |
| Attempt mutex, owned run lock, create-exclusive publication, fsync and receipt-last ordering; protection | Lifecycle, task and reporting transaction owners; recovery, resume, inspection and fault tests | Provides serialization, attributable ownership, durability and truthful completion; repeated mechanics do not duplicate semantic ordering | **Retain.** Transaction authorities survive; only a proven low-level primitive may consolidate | Estimate all six zero for retention; audit actual all six zero | Equal-or-stronger concurrency, crash, signal, rollback, directory-durability and failure evidence required |
| Separate start, attempt, stream, verified, reporting, lock-release and terminal records; evidence | Task, reporting and lifecycle owners; inspection, recovery, audit and historical readers | Distinguishes entry, execution, validation, failure/recovery and terminal truth; record count alone is no redundancy evidence | **Retain pending itemized lifecycle/evidence audit.** Current record owners survive | Estimate all six zero; audit actual all six zero | Any proposal must name exact record class, producers/consumers, claim, recovery path, retention and rollback and receive explicit user approval if deleting evidence |
| Derived inspection independent of `.snakemake`; protection | Inspection over EMRYS contracts/records/locks; control, resume and tests | Prevents engine metadata from becoming status, recovery or completion authority; no redundant authority exists | **Retain.** Persisted EMRYS records remain authority and inspection remains derived | Estimate all six zero; audit actual all six zero | A new read model must derive the same or stronger truthful state and cannot persist a competing status |
| Direct-owner, adversarial, seeded-fault, independent-golden, recovery, fresh-clone and synthetic E2E defenses; protection/tests | Functional owners and CI; maintainers, release review and regression diagnosis | Protects distinct failure, packaging, recovery and synthetic execution claims; coverage or happy path is not equivalent. Tests aimed only at an impossible same-process injection are not automatically equivalent to these boundaries | **Retain boundary defenses or map individually to equal-or-stronger surviving protection. Retire proven check-only internal seams with their redundant check.** | Estimate all six zero; audit actual all six zero | Name invariant, trust boundary, risk, evidence level and surviving authority for each retirement; high-risk, ambiguous, or directly user-facing removal requires explicit approval; long checks remain CI-owned |
| Deliberate orchestration exports and eager-import-free local-pilot package; compatibility/protection | Contract package and local-pilot package; importers, packaging and public-contract tests | Controls supported imports and avoids import-time side effects; no redundant facade was proved | **Retain pending API/package decision.** Current boundaries survive | Estimate all six zero; audit actual all six zero | Inventory external imports and import-time behavior; do not make an interim package stack permanent |
| Packaged retired-v2 request schema; evidence/compatibility | Orchestration schema package and distribution tests; historical package readers | Preserves declared retired-format compatibility evidence and wheel contents; age is not redundancy evidence | **Retain pending approval-gated evidence review.** Packaged schema remains authority for its historical claim | Estimate all six zero; audit actual all six zero | Exact consumer/history/claim/rollback review and explicit user approval before any evidence deletion |
| `.snakemake/`; runtime metadata | Snakemake engine; engine only, never EMRYS completion/reporting readers | Supports engine operation but is deliberately excluded from EMRYS authority; no retained-evidence claim | **Disposable runtime metadata, not authority.** EMRYS contracts/records survive | Maintained-source estimate and audit actual all six zero | Cleanup must stay within the run/work policy and cannot substitute engine state for EMRYS evidence |
| `locks/acquire.mutex`; protection/runtime state | Lifecycle admission; concurrent attempts and lifecycle fault tests | Reusable synchronization point; historical attribution is carried by owned-lock/release/receipt records, not the mutex itself | **Retain as synchronization mechanism, not historical evidence by itself.** Lifecycle owns it | Estimate all six zero; audit actual all six zero | Preserve serialization and safe stale-state handling; do not delete attributable lock/release evidence by analogy |
| Retained exact evidence generally; evidence | Named producer/owner of each artifact or record; scientific, operational, recovery, audit and historical consumers | Supports claims and recovery at different levels; no blanket redundancy finding exists | **Retain. No evidence deletion is proposed.** Each current owner survives | Estimate all six zero; audit actual all six zero | Separate itemized review plus explicit user approval and separate commit for any exact evidence deletion |

#### Footprint indicators

The exact tracked roster defined in the audit method—local-pilot orchestration
plus orchestration contracts/schemas—counted 43 product/schema/owner files and
22,395 physical lines. Its 19-file Python subset totaled 18,892 lines; the
separate 27-file direct test/support roster totaled 17,776 lines. CLI
composition, fixed workflow/profile files, configurations, and documentation
were inspected but are excluded from those totals. These are audit-scope
baselines, not targets or permission to merge unlike owners.

The largest current orchestration modules are scope indicators, not automatic
deletion or splitting targets:

| Module | Physical lines at audited revision |
|---|---:|
| `lifecycle.py` | 2,628 |
| `task.py` | 2,111 |
| `inspection.py` | 2,088 |
| `dashboard.py` | 1,985 |
| `materialization.py` | 1,547 |
| `doctor.py` | 1,098 |
| `launcher_config.py` | 1,082 |
| `onboarding.py` | 1,076 |
| `reporting_boundary.py` | 1,070 |
| `__main__.py` | 711 |

Size may direct owner/caller review, but it cannot justify a god module,
forwarding facade, weakened failure behavior, or moving complexity into
configuration/generated code.

#### Candidate compression register

Every row below is conditional. None authorizes implementation or deletion.

The delta column records directional audit estimates because no design or
caller migration is selected. A promoted slice must replace them with an exact
numeric before/after roster. “Audit actual all zero” means zero changed product
files/lines, public concepts, configuration artifacts, call edges, and
compatibility paths for that candidate; documentation-only audit accounting is
reported separately below.

| Candidate | Surface/category | Current owners; callers and consumers | Unique retained responsibility | Redundancy evidence | Proposed disposition and surviving authority | Directional estimate; audit actual | Preconditions before change |
|---|---|---|---|---|---|---|---|
| `ARCH-MODEL-COMP-01` | Schema and protection | Contract API/execution schema; normalization, projection, materialization, lifecycle, task, reporting, inspection, workflow and tests | Canonical execution identity, closed shape, digest recomputation, and historical admission | Profile, samples, partitions, reference, and analysis occur both top-level and in `identity_envelope`; validation requires exact equality | **Defer; candidate consolidate.** Current versioned contract/schema remains authority until an approved successor and migration exist | Est.: files 0; lines lower; concepts/config 0; edges lower; at most one temporary compatibility path, then zero. Audit actual all zero | Complete consumer roster; select identity boundary; version/migrate schema; prove historical and current admission plus exact digest parity |
| `ARCH-MODEL-COMP-02` | Maintained product code and protection | Normalization, materialization, lifecycle, inspection and projection; control, task/reporting owners and tests | Exact admitted record bytes and immutable identity/plan facts | Frozen dataclasses wrap mutable dictionaries beside cached or recomputed canonical bytes | **Defer; candidate consolidate.** One immutable admitted-record authority is required, but its type, noun, and package remain Open | Est.: files no growth; lines and competing views lower; concepts/config/compat 0; edges no increase. Audit actual all zero | Decide Run/Attempt fields; prove no mutable caller ownership; add deep-immutability and byte-divergence protection; preserve fault checks |
| `ARCH-MODEL-COMP-03` | Maintained product code and protection | Onboarding validation, Doctor, grouped control and lifecycle; operators, CLI, planning and tests | Fresh admission at each mutation/repair/lock risk boundary | At the audited revision the generated Slurm journey normalized the same request four times before execution. The wrapper and its duplicate validation path are now retired; one allocated grouped command retains deliberate profile, request, runtime/tool, storage, and lifecycle re-admission at their real boundaries. | **Partially realized.** Section 13.6 removes the duplicate composition path while preserving boundary re-admission; any further consolidation remains conditional. | Actual execution-profile cut is recorded in Section 13.6. | Separate redundant work from TOCTOU defense; re-admit after future repair and prove changed inputs fail closed at the last safe boundary. |
| `ARCH-MODEL-COMP-04` | Maintained product code and protection | Inspection, lifecycle, task and reporting owners; recovery, validation and tests | No-follow stable canonical-record admission with owner-specific size, inode, destination, hashing and diagnostic rules | Multiple owners already call `inspection.admit_canonical_record` while retaining parallel higher-level identity binding and specialized readers | **Defer; evaluate candidate seam.** Final neutral owner/API/package remains Open; each semantic owner retains its unique checks | Est.: files no growth; lines and duplicate call edges lower; concepts/config/compat 0. Audit actual all zero | Map exact per-owner semantics and dependency cycles; share only proven intersection; preserve large-file behavior and fault/error contracts |
| `ARCH-MODEL-COMP-05` | Maintained product code and protection | Lifecycle, task and reporting publication owners; inspection, recovery and fault tests | Create-exclusive durable bytes, directory fsync, transaction ordering, rollback and truthful terminal publication | Closely related low-level publication mechanics are implemented separately in the three transaction owners | **Defer; candidate consolidate primitive only.** Lifecycle/task/reporting remain separate semantic authorities; primitive owner Open | Est.: files no growth; lines lower; concepts/config/compat 0; low-level edges may converge without new semantic edge. Audit actual all zero | Prove byte-publication equivalence; retain signal/ownership/rollback/order/fault differences and receipt-last semantics |
| `ARCH-MODEL-COMP-06` | Maintained product code and configuration | Doctor, onboarding, materialization and control; readiness, planning, validation and tests | Bind the reviewed fixed workflow profile and exact checkout identity | The same current-profile relative path is repeated in four owners | **Defer; candidate consolidate locator.** Current exact-profile and checkout checks survive; final profile-policy owner remains Open | Est.: files 0; lines and literal call edges lower; concepts/config/compat 0. Audit actual all zero | Decide profile/application policy; prove packaging and checkout behavior; avoid a facade that merely forwards the literal |
| `ARCH-MODEL-COMP-07` | Maintained product code and policy/protection | Reporting boundary, resource policy, inspection, control and `Snakefile`; workflow, status, memory planning and tests | Closed report-kind roster, deterministic order, resources, transaction schemas and independent regeneration | Report kinds/count appear as a tuple, hard-coded `3`, workflow targets and validation assumptions across several owners | **Defer; candidate consolidate catalog.** Final catalog authority/package remains Open; reporting transactions retain semantic authority | Est.: files no growth; lines and repeated edges lower; concepts/config/compat 0. Audit actual all zero | Inventory all producers/consumers and dependency direction; avoid inspection/reporting cycle; prove order, memory, schema and regeneration parity |
| `ARCH-MODEL-COMP-08` | Wrapper/compatibility path and maintained product code | Dashboard plus control/inspection and Snakemake text producers; `make dashboard` and dashboard tests | Current-user scheduler observation and sanitized raw-stream access are the only unique operational needs; persisted EMRYS records remain status authority | The 1,985-line dashboard has no production importer, parses non-authoritative human text, duplicates 986 test lines, and hard-codes a roster incompatible with the current starter | **Mark stale and freeze.** Implement `OBS-02` independently; do not update or retire the dashboard during the campaign. Reconsider whole-surface retirement afterward. Manual scheduler accounting and raw streams survive as expert routes | Post-campaign retirement opportunity: replacement budget at most 250 product and 300 test lines would permit at least 1,751 net product/script and 686 net direct-test reduction. Audit actual all zero | Campaign completion plus explicit user approval for public-route retirement; then prove the applicable status and scheduler-observation boundaries |
| `ARCH-MODEL-COMP-09` | Maintained product code | CLI composition, control, onboarding, launcher and owner commands; users, wrappers, automation and tests | Owner-specific actionable diagnostics and stable exit contracts | Similar exception-to-public-error projection patterns recur, but exact equivalence and caller dependence are not yet proved | **Defer pending inventory.** Each current owner remains authority until a genuinely shared projection is proved | Est.: files no growth; lines and edges may decrease; concepts/config/compat 0. Audit actual all zero | Inventory exact messages, exception types, exit codes and machine consumers; retain owner-specific context and failure ceilings |
| `ARCH-MODEL-COMP-10` | Configuration/script/schema/documentation and compatibility | `configs/`, onboarding starter set, grouped control, runtime and execution-profile owners; scientists, operators, examples and tests | Scientific intent, site execution policy, inspectable defaults/sources, deterministic generated artifacts and compatibility | The audited split launcher/resource surface exposed one execution decision through parallel files, defaults, schemas, wrapper, and tests. | **Partially realized.** Section 13.6 consolidates current resources and placement into one profile, shrinks the starter to six visible artifacts including its manifest, and retires the wrapper/split examples without compatibility aliases. Scientific Project input, runtime, storage, and named-profile management remain Open. | Actual execution-profile cut is recorded in Section 13.6. | Preserve scientific visibility, safe override provenance, create-absent publication, and historical record admission in each later configuration slice. |
| `ARCH-MODEL-COMP-11` | Wrapper/compatibility path | Dashboard helper/parser; dashboard callers and tests plus historical plan/log readers | No independent responsibility outside the stale dashboard | Scheduler selection and legacy parsers exist only inside that surface | **Freeze with the dashboard.** Do not update parser compatibility during the campaign; if post-campaign retirement is approved, remove it with the whole surface rather than preserving it separately | Included in `ARCH-MODEL-COMP-08`; audit actual all zero | Same post-campaign approval and proof gate as `ARCH-MODEL-COMP-08` |
| `ARCH-MODEL-COMP-12` | Maintained product code and wrapper/compatibility path | `__main__.py` grouped composition and command adapters; all CLI users, automation, docs and public-contract tests | Stable public capability routing, arguments, exits and advanced escape hatches | A 711-line root composes ten top-level groups and interleaves ordinary/expert plumbing; duplication cannot be quantified before the public model is chosen | **Defer.** Current CLI remains authority; later migrate directly to selected owners and retire superseded routes without a permanent facade | Est.: files no growth; lines, concepts and call edges lower; config 0; temporary compatibility route only with owner/retirement. Audit actual all zero | Decide public nouns/capabilities; roster every caller; preserve exact contracts; prove parity before retiring old tree |
| `ARCH-MODEL-COMP-13` | Documentation and compatibility | Quickstart, orchestration, launcher and role-journey documentation; scientists, operators, maintainers and support | Canonical safety, recovery, advanced inspection and evidence-ceiling guidance | Manual directory creation, runtime-profile redirection and dry-run-root transfer recur across local and Slurm journeys | **Defer; candidate relocate unique facts and retire superseded journey text.** Final subject owners retain exact contracts | Est.: documentation files/lines, public concepts and compatibility journeys lower; product/config/call edges 0. Audit actual all zero | Implement accepted interface first; map every unique rule and inbound link; update/retire old journeys in the same bounded migration |
| `ARCH-MODEL-COMP-14` | Wrapper/compatibility path and protection | Execution-profile admission; CLI/config callers, packaging and migration tests | Fail closed on ambiguous retired EMRYS/NORAD adjacent configuration | Split launcher/resource readers would preserve two architectures. | **Realized for current authoring.** One execution-profile owner rejects retired adjacent names; no launcher/resource compatibility reader or alias survives. Historical persisted records remain readable. | Actual compatibility reduction is recorded in Section 13.6. | Any later removal of the explicit fail-closed migration diagnostic requires a separate support-policy review. |

#### Focused reduction and shell-disposition audit

The 2026-08-28 audit at source revision `1abbf094` reviewed observability,
immutable handoffs, repeated validation, tracked shell, generated shell, and
their direct protection suites. It found 10,432 tracked product shell lines
(8,754 `.sh` and 1,678 `.slurm`). The generated-wrapper template spans 143
physical Python source lines and currently renders 121 shell lines.
The estimates below are directional implementation budgets, not authorization;
product and protection/test reductions remain separately reported.

| Surface | Disposition and surviving authority | Directional reduction | Gate |
|---|---|---:|---|
| Same-process impossible-state and test-only seams in control, materialization, lifecycle, and inspection | **Retire.** Trust the sole admitted immutable producer; retain disk re-admission, canonical bytes, schema validation, and real mutation boundaries | 90–140 product; 10–30 tests | Low risk only after the slice records sole construction, no injection/mutation path, no distinct claim, and exact surviving authority |
| Materialization-to-lifecycle handoff | **Consolidate duplicated exact handoff facts behind one admitted immutable boundary selected during implementation.** Retain mutex, filesystem re-admission, source/tool/storage checks, lock ownership, signal handling, and receipt-last publication | 110–170 product; 150–300 tests | Explicit approval because this changes an execution boundary; prove core-path and fault parity; no evidence deletion |
| Repeated inspection receipt/task validation | **Consolidate conditionally behind the smallest admitted view selected during implementation.** Derive status and receipt comparisons without repeated reads; retain cumulative receipt arrays and all evidence records | 350–470 product, with additional test/I/O reduction to be measured | Explicit approval because blocker specificity and authoritative status validation are affected |
| Dashboard and `make dashboard` | **Mark stale and freeze during the campaign.** Persisted EMRYS records remain authority, inspection owns the independent derived projection, and the dashboard receives no updates | Post-campaign opportunity of at least 1,751 net product/script and 686 net direct tests under the caps in `ARCH-MODEL-COMP-08` | Reconsider only after campaign completion; exact public-route removal still requires explicit approval |
| Sixteen stage/utility `.slurm` wrappers | **RETIRE realized in Section 13.19.** Grouped whole-Run Slurm preserves the scheduler boundary; the private batch bootstrap remains. | Audit estimate retained: 1,678 product and at least 2,402 dedicated tests. Actuals are recorded in Section 13.19. | Caller audit found no live runtime consumer; successful hosted 130-pair direct/Slurm parity gated retirement. Site/module and failure/recovery parity remain Open. |
| Generated `run-in-slurm.sh` body | **RETIRE realized in Section 13.6.** Grouped Run control and the private Python transport own submission; one private stdin batch bootstrap remains **KEEP** for module initialization, scratch cleanup, and final `exec`. | Actual product, test, configuration, and compatibility reductions are recorded in Section 13.6. | Real scheduler/site parity remains Open; preserve submitter/profile/job binding, module environment, scratch cleanup, signal/exit propagation, and Python availability. |
| Step 07, Step 08, and the Step 09 shell bundle | **Convert individually to existing Python admission/publication owners; keep the R scientific implementations.** No parallel shell compatibility owner | Respectively 600–750, 650–800, and 900–1,200 net product; direct test reductions measured per slice | Separate explicit boundary/parity approval for each; preserve exact inputs, command failure, immutable publication, validation, and terminal-record ordering |
| Steps 00c and 05 plus shared shell libraries | **Keep for now.** Reconsider only after a smaller Python owner pattern is proven; retire shared functions as their last real caller migrates | Zero now | Do not create bespoke line-for-line ports or matching Python helper APIs |
| Step 06 shell owner | **RETIRE realized in Section 13.25.** One private create-absent Python owner preserves the live transaction and validator boundary without the production-dead replacement surface or a shared helper framework. | Actual product, test, documentation, and compatibility reductions are recorded in Section 13.25 and the findings matrix. | Caller-complete materialization, transaction/fault, installed-wheel, provenance, and 130-pair gates apply. |
| Retired `scripts/git_orchestration/` namespace | **Keep absent and finish the exact history-backed disposition.** Useful documentation validation already moved to its owner; do not add a permanent return-prevention guard for an implausible invariant | Avoids new guard/test surface | `TOOLING-01` remains Open until every former file/caller is accounted for; do not revive the namespace |

The combined opportunities exceed 5,000 directional net product lines before
the approval-gated evidence-I/O consolidation candidate. This is neither a
quota nor permission to trade away guarantees: each bounded slice must replace
the estimate with actual category-separated accounting and stop if its total
surface does not fall.

#### Model options reviewed and remaining decision order

A useful first question for the bounded model discussion was:

> **Which changes create a new immutable Run, and which create only a new
> Attempt of the same Run?**

Three options were compared explicitly:

| Option | Shape | Benefit | Cost or risk |
|---|---|---|---|
| **A — promote the normalized execution contract essentially as Run** | Workflow profile + scientific inputs/design/reference/policy form the Run; runtime/resources/executor/source remain Attempt facts | Smallest migration and strongest reuse of current canonical identity | Current identity is path-sensitive and omits effective execution choices, so the object may be less than the full plan users expect. |
| **B — include effective execution selection in Run** | Add selected runtime/executor/resources and possibly source realization to the immutable plan | Run becomes the complete accepted execution plan | Changes identity, storage, migration, reuse, and compatibility semantics; may conflate scientific intent with site execution. |
| **C — separate immutable scientific intent from immutable execution plan, with Run referencing both** | One admitted scientific definition plus one immutable effective realization compose Run; Attempt executes it | Clean distinction between science and realization and supports multiple execution plans | Adds concepts and risks locking the repository into an interim stack unless old representations retire in the same bounded migration. |

`ARCH-MODEL-DECISION-01` subsequently selects option C. Mutable object state
and canonical bytes cannot be competing authorities. The remaining
**nonbinding candidate discussion order** is:

1. decide exact Analysis, Execution Plan, Run, and Attempt fields, identity
   inputs, relocation behavior, and immutable
   in-memory/persisted representation;
2. decide separate scientific, execution,
   reporting, and recovery status semantics;
3. decide persistence and storage relationships; then
4. select APIs, CLI mapping, execution-backend interfaces, policy boundaries,
   compatibility windows, and caller migration only where those decisions are
   required by a bounded implementation slice.

This list is not approved implementation sequencing. `AC-DEC-020` remains
Open, and the required decisions and their order must be reconsidered for each
bounded slice rather than used to pre-set the campaign.

The audit itself left every item above Open except Run's immutable-plan
meaning. The later decision selects only the public vocabulary, nesting,
model-C composition, and Run-versus-Attempt boundary. Neither record introduces
product code, command, API, class, schema, package, backend, policy owner,
persistence format, or evidence deletion.

#### Audit-only change accounting

The audit delta is measured from the inherited campaign-guardrail commit
`4c3f50ced83859083127501d5e40e4c03554a833`. Categories do not offset one
another:

| Category | Actual change |
|---|---|
| Maintained product implementation | 0 files; 0 physical lines |
| Protections and executable tests | 0 files; 0 physical lines; no defense retired or added |
| Configuration, scripts, schemas, generated/runtime material | 0 files; 0 physical lines; no generated or runtime artifact counted |
| Retained evidence | 0 artifacts or evidence classes added, moved, or deleted; no deletion proposed |
| Public product concepts and interfaces | 0 commands, types, methods, schemas, or accepted public nouns added or removed |
| Compatibility paths | 0 added, changed, or retired |
| Mutable product state | 0 product mutations added or removed; current exceptions are inventory only |
| Documentation | 3 files; `+485/-16` physical lines relative to the inherited guardrail commit |

#### Evidence ceiling

This audit used exact current Git/source, contract, schema, and test inspection
at the revision named above. No product tests, runtime restoration, real
scientific tools, scheduler job, Slurm allocation, cluster or production run,
scientific review, or biological validation was performed. Focused
documentation validation of the recorded audit is separate engineering
evidence and cannot promote this ceiling.

### 8.1.2 `ARCH-MODEL-DECISION-01` selected model and next decision package

> **Ratified direction, not implementation.** After reviewing the current-state
> audit and the three alternatives above, the user selected model C and the
> smallest public vocabulary below. At this decision boundary, exact fields,
> records, APIs, persistence, storage, backends, compatibility, and migration
> remained Open; Section 8.1.3 subsequently resolves the semantic fields and
> logical authorities only.

The compact public conceptual model is:

```text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), progressively disclosed
```

| Concept | Ratified meaning and visibility |
|---|---|
| Project | Mutable organizational workspace for drafts, declared inputs, references, and configuration; not execution authority. |
| Analysis | Scientist-facing scientific intent. Drafts may evolve; an admitted Analysis revision is immutable. Analysis may be human-named while retaining an internal immutable identity. |
| Execution Plan | Generated, immutable, and inspectable effective realization of an Analysis revision. It is an internal Run component, not an ordinary user-authored or separately managed public noun. |
| Run | Public immutable binding of exactly one admitted Analysis revision and one Execution Plan; owns the primary ordinary identifier. An Analysis revision may have multiple Runs. |
| Attempt | One execution occurrence of an unchanged Run. It is surfaced for retry, failure, recovery, or advanced inspection rather than required on the ordinary path. A Run may have zero or more Attempts. |
| Results | Read-only discoverable Run-bound output surface, not a mutable identity-bearing aggregate or competing completion authority. |

Dataset, Reference, and ExperimentalDesign remain scientific-definition
sections rather than independently managed top-level identities. Runtime and
execution-profile selection are operator-facing inputs to Run construction.
Artifact is advanced inspection vocabulary, Task remains internal, and Report
is a downstream regenerable output capability beneath Results rather than a
scientific stage or scientific-completion authority.

The semantic change boundary is:

| Change | New Analysis revision | New Run | New Attempt |
|---|:---:|:---:|:---:|
| Scientific intent changes | yes | yes | no |
| Identity-bearing effective toolchain, backend/profile, or permissible resource policy changes | no | yes | no |
| The same immutable Run is retried or re-executed | no | no | yes |
| Host, scheduler job ID, timestamps, or actual allocation vary inside the declared permissible envelope | no | no | yes |
| A retry requires resources outside the declared permissible envelope | no | yes | no |
| Only downstream report enablement or format changes, or a report is generated or regenerated independently | no | no | no by itself; executing the Run still creates an Attempt |

Reporting is invoked by default during a full run, can be disabled, and can be
regenerated independently with its own downstream provenance. It does not
change Run or Attempt identity and cannot define scientific completion.

At this decision boundary, exact Analysis/Execution-Plan/Run/Attempt fields,
the permissible variation envelope, Run-ID inputs, relocation/order semantics,
logical authorities, recovery ownership, status separation, persistence,
APIs, compatibility, and migration remained Open. Section 8.1.3 subsequently
resolves the semantic field, identity, authority, envelope, recovery-owner,
and status-domain questions. Product representation, persistence, APIs,
backend realization, compatibility mechanics, and caller migration remain
Open. No interim parallel model or god object is authorized.

#### Bounded `AC-SLICE-03` field-and-authority decision package

This documentation-only decision package preceded implementation. It did not
receive a new backlog identity: `AC-SLICE-03`,
`CONTROL-01`, `RUN-03`, `IDENTITY-01`, and `ARCH-01` remain its planning
owners.

The minimum representation roster at that decision boundary was
`emrys.request.v3`, `NormalizationBundle`,
`emrys.execution.v1`/`contract/normalized.json`,
`emrys.identity-envelope.v1`, `ResourcePlan`, `AttemptPlan`, the unversioned
workflow configuration, `emrys.workflow-attempt.v1`, `AttemptPreparation`,
`LifecycleRequest`, `WorkflowResult`, `LifecycleOutcome`,
`emrys.attempt-receipt.v1`, and `RunInspection`. The package must expand this
roster if source or caller inspection finds another competing or derived view.
Section 13.24 later retires `AttemptPreparation`: the surviving
`LifecycleRequest` carries the one canonical Attempt byte payload directly.

Required output:

1. Exhaustively map every field in the authored request, normalized request and
   identity envelope, `NormalizationBundle`, resource selection, `AttemptPlan`,
   workflow configuration and attempt record, lifecycle request/outcome and
   receipt, inspection projection, artifacts, and reporting records to Project,
   an immutable Analysis revision, the immutable Execution Plan, the Run
   binding, Attempt, Results, provenance-only metadata, internal derived
   material, or an explicit compatibility/retirement disposition.
2. Decide the exact Run-ID inputs and relocation, raw-formatting,
   collection-order, label/notes, and content-change semantics.
3. Decide the permissible Attempt variation envelope and publish a complete
   change-to-new-Analysis/new-Run/new-Attempt/neither table.
4. Select one logical canonical authority for each admitted boundary and name
   the surviving current records, derived views, and direct retirement or
   bounded compatibility disposition. Mutable dictionaries and canonical bytes
   cannot compete.
5. Assign zero-attempt and unreceipted-skeleton recovery ownership without
   treating a directory alone as a Run.
6. Separate Attempt execution, scientific-results completeness, and reporting
   status semantically while deferring the exact public state vocabulary.
7. Apply Section 13.1: record owner/caller, compression, mutation, protection,
   retained-evidence, compatibility, non-goal, and evidence-ceiling
   dispositions before proposing implementation.

Non-goals are product code, public API or CLI design, filenames or filesystem
layout, backend implementation, status vocabulary, reporting API, Artifact
Store, serialized schema migration, and any evidence deletion. The package is
complete only when the field map is schema/caller-backed, every remaining
choice and rationale is durable, and documentation-only evidence is reported
without implying runtime, scheduler, scientific, or biological proof. A first
vertical implementation requires separate review and approval.

### 8.1.3 `ARCH-MODEL-FIELDS-01` field and authority decision

> **Selected semantic design, not product implementation.** This package
> completes the no-code prerequisite defined above. It fixes the semantic
> fields, identity inputs, Attempt envelope, logical authorities, and recovery
> owner needed to slice the first implementation. It deliberately does not
> choose public APIs or commands, packages, storage paths, serialized schemas,
> backend implementation, public status names, or an Artifact Store.

The governing split is deliberately portable:

```text
Project aliases and locators
        |
        +--> immutable Analysis revision: what is being analyzed
        +--> immutable Execution Plan: how it is to be computed
                    |
                    v
             immutable Run binding
                    |
                    +--> Attempt(s): where and when the plan was realized
                    +--> Results: what the Run produced and proved
```

Paths locate content but do not identify it. Raw configuration sources explain
how an effective decision was reached but do not replace that decision.
Backend-specific dispatch material executes a Run but does not become another
Run authority.

#### Canonical identity records

The logical identity records below are exact. Their later Python types,
serialization, filenames, and storage remain Open.

| Record | Exact identity-bearing semantic fields | Explicit exclusions |
|---|---|---|
| Analysis revision | Identity-domain version; samples sorted by `sample_id`, each with `sample_id`, `condition`, `replicate`, `strandedness`, and R1/R2 content SHA-256; partitions sorted by `partition_id`, each with `partition_id`, `selector_type`, and either the normalized region selector or selector-file content SHA-256; reference FASTA and GTF content SHA-256; and the complete normalized scientific policy: `control_condition`, `treatment_condition`, `background_condition`, `rna_ref`, `rna_alt`, `min_sample_dp`, `mean_dp_threshold`, `fdr_threshold`, `common_or_threshold`, `absolute_difference_threshold`, and `background_max_fraction` | Project/name aliases; authored and resolved paths; file sizes; request/manifest bytes and hashes; raw formatting and collection order; notes; `label`, `analysis.id`, `cohort_id`, and `reference.id`; STAR-index settings; runtime, source, backend, resources, reporting, and storage |
| Execution Plan | Identity-domain version; normalized functional-owner/dependency/output-admission specification; declared scientific-computation target or stopping boundary; exact executable implementation content identity for scientific computation and artifact admission; exact logical toolchain and environment content identities; declared execution-backend and engine semantics; STAR-index parameters; and the canonical pre-allocation computational resource declaration, including `workflow_cores`, `stage_concurrency`, `step_threads`, `workflow_memory_mb`, and computational `stage_memory_mb` with their symbolic values preserved | Analysis fields; physical source/tool/config paths; commit labels that do not prove executable content; host, process, scheduler job, workspace, scratch, and run-root locations; allocation-resolved resource values; logging/display flags; reporting targets, implementation, templates, enablement, format, projection, and reporting memory; backend adapter files, argv, dispatch paths, and absolute output paths |
| Run binding | Identity-domain version, Analysis-revision digest, and Execution-Plan digest | Project identity/location, human labels, Attempt facts, Results/report state, and every derived adapter |

The Analysis and Execution Plan are independently content-addressed and may be
reused. A Run binds exactly one of each. Any Analysis-specific dispatch roster
is therefore a deterministic projection of the Run binding, not an additional
identity record.

Successor task and artifact scopes that currently depend on `reference.id`,
`cohort_id`, or `analysis.id` use internal content-bound scope identities;
Project aliases may still be displayed and retained as provenance. This is why
renaming one of those aliases cannot silently change the Run's task or Results
identity. `sample_id` and `partition_id` remain Analysis fields because they are
structural keys within the declared design, not top-level display aliases.

For the current CMH profile, “normalized functional-owner/dependency/output
specification” means the semantic content of `owner_tasks`, `direct_edges`,
completion/evidence-owner classification, and required artifact templates,
including the current logical `source_path_template` because it selects the
artifact admitted under an ID. Engine `rule_name` and derivable
`scope_selector` values are adapter material. Set- or graph-like lists
are canonicalized by stable semantic keys; their authored order is not
identity. Artifact adapters remain semantic where they determine how an output
is admitted.

The implementation identity is the digest of executable source, workflow,
scripts, and locked code dependencies that can affect Run-bound scientific
computation or artifact admission. Report-only rules, modules, renderers,
templates, and stylesheets have their own downstream transaction provenance
and do not enter Run identity. A
clean source commit may be retained and may locate that material, but a commit
label alone is not the portable content identity. Each tool or environment
identity contains the logical name and exact admitted executable, package, or
environment-content digest; version is retained for explanation. Install
paths are Attempt realization facts. This exact-content rule is intentionally
conservative: version-compatible substitution is not allowed inside one Run.

The identity calculation is domain-separated:

```text
analysis_revision_digest = SHA256(canonical Analysis-revision identity record)
execution_plan_digest     = SHA256(canonical Execution-Plan identity record)
run_binding               = {
  identity_domain: "emrys.run-identity.v1",
  analysis_revision_sha256: analysis_revision_digest,
  execution_plan_sha256: execution_plan_digest
}
run_id                    = "run-" + SHA256(canonical run_binding)
```

The identity-domain version changes only when identity semantics change. A
storage-schema or formatting migration alone must not change these identities.
Historical current-format Run IDs remain valid for their historical records;
they are not recomputed into the successor domain.

#### Relocation, formatting, naming, order, and content rules

| Change | Identity consequence |
|---|---|
| Move a request, manifest, FASTQ, selector file, FASTA, GTF, tool, environment, Project, workspace, or Run bundle without changing admitted content | No Analysis, Execution-Plan, or Run identity change. A later execution records the new realization in a new Attempt. |
| Change request YAML/TSV whitespace, quoting, key order, row order, or equivalent relative/absolute locator spelling while normalized semantics and bound content are unchanged | No identity change. Exact authored-source bytes remain provenance. |
| Change `label`, `analysis.id`, `cohort_id`, `reference.id`, or sample `notes` only | Project alias/annotation change only. No new Analysis revision or Run. |
| Change `sample_id`, `condition`, `replicate`, `strandedness`, `partition_id`, `selector_type`, or normalized region selector | New Analysis revision and therefore a new Run. These values are structural scientific keys, not presentation-only labels. |
| Change any bound FASTQ, selector-file, FASTA, or GTF byte content | New Analysis revision and Run, even if a higher-level parser might judge the files equivalent. A future semantic-content equivalence rule would require a new identity domain. |
| Change any scientific comparison, allele, threshold, background, or design value | New Analysis revision and Run. Omitted `background_condition` and explicit normalized `null` are equivalent. |
| Change the Run-bound workflow/method graph, scientific/evidence completion or output-admission policy, scientific stopping boundary, computational/artifact-admission implementation, exact computational tool/environment content, backend/engine semantics, STAR-index policy, or declared computational resource policy | New Execution Plan and Run. |
| Change only a raw profile/config path, formatting, source hash, default source, or override source while the canonical effective declaration is unchanged | Provenance change only; no new Run. |
| Change report enablement, format, renderer, template, output path, or reporting resource policy | No Analysis revision, Run, or Attempt by itself. The reporting transaction records the change. |

The implemented Run-bound stopping boundary is the required
scientific/evidence-owner closure exposed by `cohort_slice` and
`_all_owner_outputs()`. The former composite `local_pipeline_slice` and its
three reporting rules are retired from the workflow. Artifact indexing,
run-summary assembly, and HTML rendering are downstream default reporting
operations. A later backend may name or represent the scientific boundary
differently without changing the semantic split.

`strandedness` remains an Analysis design declaration even though the present
pipeline does not consume it computationally. That gap must stay visible until
a scientific decision either uses it or explicitly retires it; it must not be
silently dropped during architecture migration.

#### Resource declaration and permissible Attempt variation

The current `ResourcePlan` mixes two authorities. It resolves symbolic
`workflow_memory_mb: allocation` and per-job `memory: workflow` against the
observed allocation, then records both the resolved values and allocation.
Freezing that object into Run would make the same declared plan change identity
from host to host.

The Run instead owns the canonical **pre-allocation declaration**. Symbolic
`allocation` and `workflow` values remain symbolic and define the permissible
envelope. Each Attempt records `allocation.{cores,memory_mb,source}` and the
deterministic numeric resolution. The declaration is unchanged across
Attempts; insufficient capacity is inadmissible. No new min/max range policy
is introduced by this decision.

Reporting memory is outside Run because reporting is a downstream,
identity-neutral transaction. `default_sha256`, `config_path`,
`config_sha256`, and override labels explain policy provenance but do not enter
Run identity; the effective symbolic declaration does.

The complete change boundary is:

| Change or observation | New Analysis revision | New Run | New Attempt or downstream transaction |
|---|:---:|:---:|---|
| Any Analysis identity field changes | yes | yes | No Attempt until the new Run is executed |
| Any Execution-Plan identity field or symbolic resource declaration changes | no | yes | No Attempt until the new Run is executed |
| Same Run executes or resumes, including reuse of verified predecessor work | no | no | New Attempt |
| Attempt ID, predecessor, operation, time, owner token, host, PID, scheduler job, account/partition/QoS/node, walltime, workspace, scratch, run-root location, or storage location changes | no | no | New Attempt |
| Physical source/tool/runtime paths change while exact Run-bound content identities remain equal | no | no | New Attempt when execution occurs |
| Actual cores or memory change while the unchanged symbolic declaration admits the allocation and the effective computational target, threads, concurrency, and toolchain stay fixed | no | no | New Attempt; record the observation and numeric resolution |
| Allocation is insufficient for the Run declaration | no | no | Block before Attempt admission when possible; otherwise retain a truthful blocked Attempt. Changing the declaration requires a new Run. |
| Scheduler transport changes but the declared backend, implementation, toolchain, and resource declaration do not | no | no | New Attempt; current outer Slurm placement is such transport, not a second backend |
| Declared execution backend or engine semantics change | no | yes | No Attempt until the new Run is executed |
| Report is generated, regenerated, fails, or uses different report-only policy | no | no | Separate reporting transaction; never an Attempt by itself |
| Inspection or another read-only projection is regenerated | no | no | Neither |

An Attempt may vary only in realization and observation. Its effective
scientific inputs, target, implementation, tool/environment identities,
backend semantics, computational resource declaration, thread/concurrency
policy, and task semantics must still match the Run. Backend-specific argv may
contain different paths, tokens, and locators, but it may not silently change
those semantics.

#### Exhaustive current-field disposition

The tables below name every current field or closed field family required by
the package. Existing Section 8.1.1 retains the source-backed caller map;
these tables settle the target allocation.

| Current authored/normalized field | Final semantic owner or disposition |
|---|---|
| Project `schema_version` | Active serialization compatibility metadata; request-v3's value survives only in historical source evidence and resume admission |
| `analyses` mapping key | Human selection/display name; excluded from immutable Analysis identity |
| Historical request-v3 `label`, `analysis.id`, `cohort_id`, `reference.id`, and `profile` | Historical source provenance and exact execution-v1 reconstruction only; no active Project field or identity authority |
| `dataset.samples`, `analyses.*.partitions`, `reference.fasta`, and `reference.gtf` authored strings | Project locators; physical resolution is Attempt provenance |
| Sample `sample_id`, `condition`, `replicate`, `strandedness`; R1/R2 content SHA-256 | Analysis revision |
| Sample R1/R2 `path`, `size_bytes`; sample `notes`; raw sample-manifest `path`, `size_bytes`, `sha256` | Locator, validation, annotation, or exact-source provenance; no identity authority |
| Partition `partition_id`, `selector_type`, normalized region `selector_value`, or selector-file content SHA-256 | Analysis revision |
| Regions-file authored/absolute `selector_value`; selector-file `path`, `size_bytes`; raw partition-manifest `path`, `size_bytes`, `sha256` | Locator/validation/exact-source provenance; duplicate path authority retires |
| Reference FASTA/GTF content SHA-256 | Analysis revision |
| Reference FASTA/GTF `path`, `size_bytes` | Locator, validation, and Attempt realization provenance |
| `star_index.sjdb_overhang`, `star_index.genome_sa_index_nbases` | Execution Plan technical policy |
| Analysis `control_condition`, `treatment_condition`, `background_condition`, `target_change`, `min_sample_dp`, `mean_dp_threshold`, `fdr_threshold`, `common_or_threshold`, `absolute_difference_threshold`, `background_max_fraction` | Analysis revision; `target_change` is normalized to the existing RNA reference/alternate representation |
| Policy/Reference `schema_version`; `policy_sha256` | Identity-domain/compatibility metadata or derived component digest |
| Generated `primary_analysis_id`, `policy.analysis_id`, `cohort_id`, and `reference_id` | Private content-derived scope identifiers used by the fixed backend; none is scientist-authored or a separate identity authority |

| Current plan/profile field | Final semantic owner or disposition |
|---|---|
| Workflow-contract `profile_id`, `profile_version`, raw `profile_sha256` | Inspectable provenance/compatibility; the normalized semantic profile content enters Execution Plan |
| `semantic_owner_keys[]`; `owner_tasks[].{machine_key,step_id,scope_type}`; `direct_edges[].{producer,consumer,artifact,semantics}`; `required_owner_keys[]`; `evidence_owner_keys[]`; `artifact_templates[].{artifact_id_template,step_id,scope_type,adapter,source_path_template,required}` | Normalized functional and output-admission specification in Execution Plan; set/graph order is canonicalized. `source_path_template` stays bound until another bound field provably derives the same artifact selection. |
| `owner_tasks[].rule_name`; both `scope_selector` occurrences | Derived backend adapter material; derivable duplicate fields are compression candidates |
| Snakemake profile `executor`, `scheduler`, effective `cores`, `retries`, `keep-incomplete` | Normalized backend/engine/resource semantics in Execution Plan |
| Snakemake profile `printshellcmds`, `show-failed-logs` | Attempt logging/presentation policy, not identity |
| Resource declaration `workflow_cores`, `workflow_memory_mb`, `stage_concurrency`, `step_threads`, computational `stage_memory_mb` | Execution Plan in canonical pre-allocation form |
| Reporting `reporting_memory_mb` | Downstream reporting policy/provenance |
| Allocation `cores`, `memory_mb`, `source`; numeric memory resolution | Attempt observation/provenance |
| Resource source/default/config paths, hashes, and override labels | Provenance only; effective semantic declaration is authority |
| Computational `RuntimeBinding.check_id`, `sha256`, and content-bearing `observed` fact | Resolve exact Execution-Plan tool/environment content identity where semantically relevant; retained again as Attempt admission observation |
| `RuntimeBinding.path`, `resolved_path` | Attempt physical realization/provenance only |
| Raw runtime-profile identity and `storage_qualification` binding/receipt | Readiness and Attempt admission provenance only. They prove how/where the fixed plan was admitted but never enter Run identity. |
| `DoctorResult.project`, selected `analysis`, `source_root`, `source_commit`, `inspection`, `bindings`; storage/runtime readiness booleans; `blockers`, `remediations`, and derived `ready` | Readiness, selection, and provenance projection, not Run or Attempt authority. Exact executable/tool content is projected into Execution Plan, while path-bound re-observation remains Attempt admission evidence. |
| Launcher `slurm.account`, `partition`, `qos`, `cpus_per_task`, `memory`, `time`, `exclusive`, `nodelist` / `LauncherPlan` equivalents | Attempt scheduler placement and requested/observed allocation provenance. Capacity must admit the unchanged Run declaration; changing placement alone does not change Run. |
| Launcher `paths.log_dir`, `request`, `workspace`, `runtime_profile`, `scratch_parent` | Attempt locators/placement provenance only |
| Launcher `modules.mode`, `init`, `load` | Attempt environment-realization instructions and provenance. Only the exact resulting Run-bound tool/environment content identities affect Run identity; equivalent directives or module locations do not. |
| `LauncherPlan.config_path`, `dotenv_path`, `override_labels` and raw config/environment/override sources | Provenance for effective placement/realization values, never Run identity; secret values are not made evidence merely because their source participates in resolution |

| Current representation field | Final semantic owner or disposition |
|---|---|
| `ProjectAdmission.source_path`, `source_sha256`, `source_bytes`, and `analyses` | Exact authored-source locator/evidence plus the immutable admitted named-Analysis roster |
| `AnalysisAdmission` profile/workflow-input/authored-path bytes and fresh views | Private construction and Attempt-evidence adapter; canonical `AnalysisRevision` is scientific identity authority |
| Historical execution-v1 top-level `profile`, `samples`, `partitions`, `reference`, `analysis`, and duplicate `identity_envelope` | Retained only for exact historical read/resume; active successor generation persists one Analysis record, one Execution Plan record, and one Run binding |
| Historical `identity_envelope.schema_version`, `identity_envelope_sha256`, and execution-v1 `run_id` | Historical Run identity authority only; successor generation uses the domain-separated binding above |
| `reporting_projection.{reference_contract,primary_analysis_policy,reporting_run_contract,artifact_inventory}.{path,sha256}` | Derived reporting adapter/Results projection; identity-neutral |
| `ReportingBundle` dictionaries, rows, and cached bytes | Derived construction state; no public or persisted authority |

| Current Attempt/materialization field | Final semantic owner or disposition |
|---|---|
| `AttemptPlan.run` | Immutable successor Run candidate or exact historical Run reference through one Attempt plan |
| `AttemptPlan.readiness`, `workspace`; `run_root`; fixed/attempt files, directories, path properties, `dispatch_count` | Transient readiness, placement, and derived materialization |
| `operation`, `workflow_attempt_id`, `supersedes_workflow_attempt_id` | Attempt identity/chain |
| `AttemptPlan.resources` and immutable `attempt_record_bytes` with its fresh parsed view | One Attempt resolution/report-policy view and one immutable prepared Attempt record; neither competes with the Run resource declaration |
| Workflow config `run_root`, `python_executable`, `execution_path`, `profile_path`, `source_checkout`, `artifact_source_root`, `reference_contract_path`, `primary_analysis_policy_path`, `reporting_run_contract_path`, `artifact_inventory_path`, and `dispatch_paths` | Attempt-local derived backend adapter |
| Workflow config `workflow_attempt_id` | Attempt reference |
| Workflow config `resource_policy` | Split into Run declaration plus Attempt allocation/resolution; not an independent authority |
| Workflow-attempt `run_id`, `execution_contract_sha256`, `profile_sha256` | Run and historical-compatibility references |
| `workflow_attempt_id`, `supersedes_workflow_attempt_id`, `operation`, `created_at` | Attempt identity, chain, and occurrence |
| `request`, `request_label`, `authored_paths`, `workspace`, `scratch`, `host`, `process_id`, `owner_token` | Attempt provenance/realization |
| `source_checkout.{path,commit,clean}` | Executable content identity is Run-bound; path and cleanliness observation are Attempt provenance; commit is inspectable locator/provenance |
| `normalizer` and computational entries in `required_tools` `name/version/path/resolved_path/sha256` | Normalizer/implementation and actual tool/package/environment logical name plus exact content identity are Run-bound; paths and re-observation are Attempt provenance; duplicate normalizer/Python identity is a compression candidate |
| `required_tools` entries `runtime_profile` and `storage_qualification` | Raw runtime-profile and filesystem-qualification evidence are Attempt/readiness provenance, not Execution-Plan identity. `renv_project`/`renv_library` paths likewise realize a separately content-bound environment rather than identify it. |
| `executor`, `execution_mode` | Declared semantic backend/mode is Run-bound; test or physical realization detail is Attempt provenance |
| `cores` | Redundant Attempt numeric resolution; retire after resource split |
| `snakemake_argv`, `workflow_config` reference | Derived Attempt adapter and provenance, never Run authority |
| Task dispatch `schema_version`, `run_root`, `execution_path`, `profile_path`, `workflow_attempt_id`, `task_attempt_id`, `owner_run_token`, `machine_key`, `scope`, `producer_argv`, `validator_argv`, `inputs`, `outputs`, `validation_report_path`, `native_receipt_path`, `task_start_path`, `task_attempt_path`, `verified_task_path`, `stdout_path`, `stderr_path` | Logical owner/scope/I/O/command derive from Run; task/owner tokens, physical paths, logs, record locations, and retained predecessor references are Attempt/internal evidence |

| Current lifecycle/inspection field | Final semantic owner or disposition |
|---|---|
| `LifecycleRequest.run_root`, contract/config/Snakefile/Python/profile paths, authored request path | Derived Attempt invocation/placement |
| `LifecycleRequest.target` | The current fixed backend targets the Run-bound scientific closure `cohort_slice`; downstream reporting is selected by public control, not the lifecycle request. |
| `LifecycleRequest.operation`, `attempt_record_bytes` | Attempt occurrence and the one exact immutable Attempt payload; lifecycle parses and validates it once before mutation and persists the same bytes |
| `WorkflowResult.exit_code`, `termination_signal`, `message` | Attempt observation reduced into terminal evidence |
| `LifecycleOutcome.attempt_path`, `receipt_path`, lock paths, `receipt`, `workflow_result` | Derived post-science view; persisted records remain authorities and no reporting result is carried by lifecycle |
| Attempt receipt v2 `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`, `workflow_attempt_id`, `attempt_record`, `released_run_lock`, `status`, `finished_at`, `snakemake_exit_code`, `termination_signal`, `preentry_task_attempt_records`, `task_start_records`, `verified_tasks`, `blockers`, `message` | Immutable scientific Attempt terminal evidence and exact subordinate evidence references |
| Attempt receipt v1 `reporting_completion_records`, `local_pipeline_complete` | Exact historical compatibility evidence only; current receipt v2 omits both fields and neither is scientific-completion authority |
| `RunInspection.run_root`, `run_id`, latest Attempt/receipt, tasks, reporting records, domain blockers, integrity, Attempt outcome, Results status, reporting status, recovery availability, and report locations | Read-only derived projection over persisted authorities. The superseded aggregate state and duplicate booleans are retired. |
| Former `ReportingBoundaryOutcome` aggregate | Retired after callers moved to the minimum kind-specific values; persisted start, verified, and semantic receipt records remain authorities |
| `ReportingOperationOutcome.status`, `verified_report_locations` | Derived Run-oriented plan/generate/reuse view; it creates no persisted aggregate status or identity |

| Current artifact/report field family | Final semantic owner or disposition |
|---|---|
| Artifact inventory `artifact_id`, `step_id`, `scope_type`, `scope_id`, `adapter`, `source_path`, `required` | Logical expected-output identity/scope/adapter/requirement derives from Run; `source_path` is placement; the realized inventory is a read-only Results discovery projection |
| Artifact record `schema_name`, `schema_version`, `record_type`, `run_id`, `run_contract`, `artifact_id`, `scope` | Versioned Run-bound Results evidence identity |
| `adapter`, `expectation`, `availability_status`, `completion_status`, `state_reason`, `attempt_provenance_status`, `attempts`, `selected_attempt_id` | Per-artifact Results completeness and Attempt lineage |
| `implementation`, `local_testing`, `runtime_validation`, `cluster_validation`, `source`, `members`, `tools`, `parameters`, `metrics`, `warnings`, `errors`, `provenance` | Results evidence, validation ceiling, content binding, and provenance |
| Run summary `schema_name`, `schema_version`, `record_type`, `run_id`, `run_contract`, `summary_state`, `generated_at`, `inventory`, `artifact_receipt`, `attempts`, `superseded_attempt_ids`, `expected_scopes`, `artifacts`, `computational_rollup`, `tools`, `parameters`, `qc_metrics`, `limitations`, `candidate_terminology`, `interpretation_boundary`, `warnings`, `errors`, `provenance` | Read-only Results summary/projection; not Run or Attempt authority |
| Report receipt `schema_name`, `schema_version`, `record_type`, `run_id`, `attempt_id`, `generated_at`, `publication_state`, `transaction_state`, `interpretation_boundary`, `input_run_summary`, `renderer`, `template`, `stylesheet`, `outputs`, `state_banner`, `truncations`, `schema_versions`, `analysis_execution_performed`, `external_network_assets_used`, `validation_claimed`, `warnings`, `errors`, `provenance` | Downstream reporting transaction/output evidence. `attempt_id` is lineage, not report-created Attempt identity. |
| Reporting start `schema_version`, Run/execution/profile identities, `origin_workflow_attempt_id`, `kind`, workflow-attempt/config/lock references, `created_at` | Reporting transaction admission and lineage |
| Verified reporting `schema_version`, Run/execution/profile identities, `origin_workflow_attempt_id`, `kind`, start/semantic-receipt references, `created_at` | Reporting transaction commitment and lineage |
| Artifact-index receipt `run_id`, Run-contract path/hash/components, inventory path/hash/row count, artifact/index/receipt schema versions, index path/hash, record/count/status/error totals, `record_set_sha256`, adapter Attempt chain/history, producer/version/commit, start/finish times, `transaction_state` | Results-index transaction commitment, independent admission, and provenance; current narrow Run-contract components are historical compatibility, not successor Run authority |
| Run-summary receipt `run_id`, Run-contract fields, artifact-receipt and inventory/index references/counts, output schema versions and JSON/TSV/QC paths/hashes/sizes/row counts, `summary_state`, `interpretation_boundary`, output count, summary Attempt chain/history, producer/version/commit, start/finish times, `transaction_state` | Results-summary transaction commitment, independent admission, and provenance |
| Reporting-context and artifact-index/run-summary build-context objects | Mutable transaction construction state; cannot become Results authority |

Shared nested artifact fields—record/path/evidence references, scopes, attempts,
implementation/runtime/cluster status blocks, members, tools, metrics,
limitations, report outputs, truncations, and provenance—inherit the parent
Results or reporting disposition above. Their `path` fields locate exact
content; their digests bind it. Repeated identity/count fields may support
independent admission and are not authorized for mechanical deletion.

#### Canonical authorities, migration, and retirement

| Boundary | One surviving logical authority | Current-record treatment |
|---|---|---|
| Analysis revision | One deeply immutable admitted Analysis record | Parsed request/manifests are construction/provenance. Current normalized components remain readable for historical Runs but do not compete with successor records. |
| Execution Plan | One deeply immutable admitted Execution-Plan record | `ResourcePlan` and workflow/profile dictionaries become builders or projections. Allocation resolution stays with Attempt. |
| Run | One immutable binding record published only after its referenced Analysis and Execution Plan are durable | `contract/normalized.json`/`emrys.execution.v1` remains historical authority for existing Runs. If an implementation slice temporarily emits it for unmigrated current consumers, that compatibility projection has an explicit owner and must stop when those callers migrate. The duplicated identity envelope does not survive as a successor authority. |
| Attempt | One immutable admitted occurrence record plus its append-only terminal receipt and subordinate task/recovery evidence | `AttemptPlan`, the bytes-backed `LifecycleRequest`, and `LifecycleOutcome` are transient views. The unversioned workflow config remains a content-bound backend adapter only until all current consumers read Run plus Attempt authority. |
| Results | Existing per-artifact evidence and transaction commitments, with indexes/summaries as read-only discoverability projections | No new mutable Results aggregate or completion record is introduced. Existing artifact, summary, reporting, and historical evidence is retained. |

Before persistence, construction has one immutable value. After persistence,
every in-memory object is parsed from or checked against the one admitted
record; mutable dictionaries and separately cached canonical bytes cannot both
claim authority. Derived projections may be cached only when their source
identity is explicit and divergence fails closed.

Migration is direct and bounded rather than a permanent parallel stack:

1. Add successor Analysis, Execution-Plan, and Run authorities and a
   version-aware historical reader.
2. Migrate every in-repository current-format consumer in the bounded
   implementation tranche; any temporary generated current-format projection
   names its exact callers and retirement condition.
3. Stop producing current-format compatibility projections for new Runs when
   those callers migrate. Keep historical records readable; do not rewrite or
   delete them.
4. The minimal Project vertical retired `NormalizationBundle`. Retire the
   remaining mutable-dictionary and workflow-config authority in the same
   caller-complete migrations, without adding a forwarding facade or god
   object.

#### Run admission and unreceipted-skeleton recovery

One Run-admission transaction owner owns the interval from create-absent
initialization through durable publication of the immutable Run binding.
Attempt lifecycle begins only after it can admit that Run. A directory, empty
subdirectory roster, `AttemptPlan`, or workflow config is never a Run.

No separate initialization receipt is required. The Run binding is published
last after its referenced immutable records are durable; its presence and
successful admission are the Run commit. That gives zero-Attempt Runs a
truthful authority without adding another evidence class.

If publication is interrupted before that commit, the same owner may reuse or
roll back only residue proved to contain no admitted Run, Attempt, lock,
receipt, task/report record, result, log, or other retained evidence. Anything
nonempty, concurrent, partially attributable, or ambiguous is quarantined and
reported rather than silently repaired or deleted. Once an Attempt admission
or lock exists, existing lifecycle/recovery owners retain authority and their
evidence is never treated as initialization residue.

#### Status-domain separation

Exact public state names remain Open, but five semantic dimensions are now
binding and cannot collapse:

1. Run admission and immutable-plan integrity.
2. Per-Attempt execution and terminal outcome.
3. Evidence integrity, blockers, and recovery availability.
4. Scientific Results/artifact availability, completeness, and validation
   ceiling.
5. Reporting transaction/publication state.

Run existence is not Attempt success; Attempt success is not complete Results;
complete Results is not report publication; none implies scientific review or
biological validation. Report failure or disablement cannot turn a successful
scientific Attempt into a failed one. The ordinary command journey may still
surface a downstream reporting failure, but the underlying authorities remain
separate. `RunInspection` and future read models derive these dimensions and
never persist a competing mutable status.

#### Compression, protection, compatibility, and evidence boundary

The first implementation slice must be net-negative in maintained product
surface and must report category-separated actuals. The highest-confidence
required reductions are the duplicated execution/identity-envelope view,
mutable-dictionary-plus-canonical-bytes competition, six copied
`AttemptPlan` resource views, redundant normalizer/Python identities,
duplicated status booleans, and workflow-config authority. Profile fields
proved derivable (`semantic_owner_keys`, equal required-owner rosters, and
`scope_selector`) and unused convenience/outcome fields remain caller-audit
candidates rather than automatic deletions.

Closed validation, canonicalization and digest rechecks; no-follow input and
record admission; exact source/runtime re-admission; resource
oversubscription checks; create-exclusive publication, fsync and publication-
last ordering; attempt mutexes, owned locks, signal/process-group behavior;
dispatch substitution and resume-chain checks; derived inspection independent
of Snakemake metadata; and direct-owner, adversarial, seeded-fault, recovery,
fresh-clone, and synthetic end-to-end boundary defenses all survive unless an
implementation maps an equal-or-stronger replacement. This does not preserve a
redundant check whose only reachable state is a test-manufactured violation of
an already-admitted immutable same-process value.

No retained evidence deletion is proposed or authorized. Workflow attempts,
terminal receipts, task start/attempt/verified records, reporting ledgers and
semantic receipts, artifact records/indexes/summaries/reports, logs,
lock/released-lock recovery evidence, and historical schemas remain retained.
Repeated identity or count fields require schema-by-schema tamper-detection and
consumer review; duplication alone is not deletion evidence.

#### Minimal implementation design

This is the complete pre-code design for the first `AC-SLICE-03` authority
cutover. Details not fixed here are implementation choices and do not require
another planning package unless they change these boundaries.

1. **Construct once.** The application/control layer constructs the Analysis
   revision and Execution Plan after scientific inputs, implementation and
   tool/environment identity, backend/stopping boundary, and symbolic
   computational-resource policy are admitted. It binds the Run before actual
   allocation resolution, Attempt identity, run-root mutation, workflow
   configuration, or dispatch generation. Doctor and onboarding supply
   admitted inputs but do not own Run.
2. **Persist three authorities.** A new-format Run has three separate immutable
   canonical JSON records: Analysis revision, Execution Plan, and Run binding.
   They use the repository's existing canonical JSON encoding and the identity
   rules above. The Run binding is the sole Run identity and admission
   authority. Exact Python types, schema identifiers, filenames, and helper
   APIs are selected in implementation.
3. **Commit Run before Attempt.** One Run-admission transaction publishes and
   durably syncs Analysis and Execution Plan, then publishes the Run binding
   create-exclusively and last. Only an admitted Run may acquire an Attempt
   lock or publish Attempt adapters. Pre-binding residue is recovered or
   quarantined under the rules above; evidence-bearing state is never deleted
   as initialization residue.
4. **Cut over without rewriting history.** Existing
   `emrys.execution.v1` Runs keep their identifiers and remain readable through
   a version-aware reader. New Runs use only the successor authorities. The
   first tranche temporarily permitted a one-way legacy-shaped backend
   projection; the completed follow-up retires it. Workflow/task consume exact
   `run.json`, while reporting consumes identity-neutral Attempt-owned inputs
   bound by the origin workflow config.
5. **Migrate one complete boundary.** The first implementation tranche moves
   new-Run creation, Run-ID/root selection, Run admission, Attempt planning and
   admission, resume compatibility, inspection, and backend admission to the
   successor authority together. No successor execution projection remains.
   Public command redesign, Project persistence, Results layout, Run Bundle,
   Artifact Store, generalized backend/policy APIs, reporting UX, and public
   state vocabulary are outside this tranche.

Deterministic implementation-content closure and content-bound scope-ID
formulas are completed directly in implementation, frozen as versioned
identity rules before the first successor ID is persisted, and protected by
tests under the already-fixed identity semantics; they do not receive another
design gate.
The tranche must retire new-Run authority from the current identity envelope,
mutable normalization dictionaries, copied `AttemptPlan` resource views, and
workflow configuration. Historical records and retained evidence are not
deleted.

#### Decision-only change accounting and evidence ceiling

This package changes documentation only. Maintained product implementation,
protections/executable tests, configuration/scripts/schemas/runtime material,
retained evidence, compatibility code paths, and mutable product state all
change by zero. No public command, type, method, serialized schema, backend, or
storage path is introduced.

The decision is grounded in current schemas, exact constructor/consumer
inspection, and the completed Section 8.1.1 audit. Focused documentation
validation can prove internal consistency only. It cannot prove product
behavior, runtime portability, local/Slurm parity, scheduler or cluster
operation, production readiness, scientific review, or biological validity.

### 8.2 Thin Stage boundary

A source-proposed Stage contract is conceptually:

```text
Stage
  name
  version
  inputs
  outputs
  resources
  execute()
  validate()
  describe()
```

Potential recognizable operations include alignment, canonical BAM creation,
QC, orientation, duplicate handling, SplitNCigar, orientation partitioning,
mpileup, candidate selection, CMH, and context. Reporting is not a semantic
scientific Stage, though it may be scheduled as downstream operational work.
The intake also
suggested a common lifecycle:

```text
admit -> plan -> execute -> validate -> publish -> record
```

The responsibility direction is settled but the API and lifecycle vocabulary
remain proposed. Functional owners retain review-relevant semantics, declare
needs, and define semantic validity; allocation authority resolves resources;
execution enforces that resolution; lifecycle and admission remain logically
distinct. Execution may invoke and record owner validation, but it cannot
redefine scientific success.

`AC-SLICE-04` found that the minimum common representation already exists and
that another Stage/Operation API would add a second authority. Transformation
Step `00b`, scientific Step `09`, and evidence Step `02b` all map without
distortion to the private `TaskDispatch` boundary: owner command, validator,
declared inputs/outputs, resources, identity, and task-level execution evidence.
Profiles and the execution graph separately retain dependencies, semantic
identity, and scheduling. Reporting deliberately does not map: it is downstream
Run work with its own ledger and independent regeneration semantics, not a
scientific Stage. This four-owner map also proves a second and third distinct
owner against the selected denominator.

The binding decision is therefore to retain the existing private functional-
owner dispatch boundary and add no Stage class, Operation protocol, registry,
schema, lifecycle vocabulary, public noun, or universal publication framework.
The caller-complete Step `08` migration proves the boundary by replacing its
shell coordinator with one owner-local Python producer while preserving the R
scientific implementation, neutral scientific-evidence contracts, independent
validator, whole-Run scheduler placement, immutable input checks, receipt-last transaction,
rollback/recovery evidence, and task/run logging. This decision does not settle
future extension discovery, collaborator libraries, or additional backends.

### 8.3 Execution boundary

**Resolved boundary; parity remains partially open:** every supported realization owes
one declared guarantee contract covering scientific boundaries, artifact
integrity, recovery, and evidence. Mechanisms and environment-specific proof
may differ.

The first implementation boundary is now explicit: the current product has one
scientific backend, local Snakemake, while one private single-node Slurm
transport places the entire grouped Run-control operation inside an outer
allocation. The former generated wrapper and separate launcher owner are
retired. Successor Attempt executor provenance comes from the immutable
Execution Plan; structured placement provenance records the admitted profile
source and exact Slurm job identity without affecting Run identity; direct
execution records no scheduler job; and historical allocation and Attempt
records remain readable.
A controlled planning/materialization proof holds Run, Attempt context,
and effective resource resolution constant while changing only direct versus
larger admitted Slurm allocation. Canonical Analysis, Execution Plan, Run,
fixed files, dispatches, other Attempt files, and output directories remain
byte-for-byte equal; only allocation provenance and its workflow-configuration
digest differ. A subsequent hosted disposable single-node Slurm proof executes
the 130-pair real-synthetic driver through both placements: the Runs retain the
same immutable authority; distinct Attempts retain matching common fields,
task rosters, path-neutral scientific outputs, and symbolic resources. Each
side separately admits a successful receipt, complete reporting transactions,
and one ordered application log; effective resources and scheduler provenance
differ as intended. This is real hosted scheduler evidence, but not an
institutional-site/module, multi-node, production-data, failure/recovery,
scientific-review, or biological claim. One explicit
execution-profile format now combines resource declaration and placement, but
a named profile registry, discovery/acceptance lifecycle, and final profile
taxonomy remain open.

No generalized execution capability is selected. A near-closure evaluation is
required, but implementation proceeds only if a concrete approved extension
needs another application backend or if one boundary can demonstrably compress
the current app. Either case requires equivalent guarantees and no duplicate
authority. Compression requires caller-complete net reduction; a concrete
extension follows the campaign's normal quantified-growth exception.

Scientific work declares CPU, memory, wall time, inputs, outputs, and runtime
needs. Execution infrastructure owns process invocation, environment binding,
scheduler integration, allocation identity, exit state, logs, cleanup, and
recovery metadata.

The durable platform direction rejects building a second scheduler, stage
registry, scientific implementation, or recovery system. `AC-SLICE-05` owns
the remaining direct/Slurm guarantee and parity work for the current backend;
it does not need to invent request/result types or another backend to close.
EMRYS's differentiator remains evidence-bound, provenance-aware
scientific analysis with strong execution guarantees—not a new generic
workflow engine.

### 8.4 Shared policy authorities

The sources proposed policy owners such as:

```text
InputPolicy
ValidationPolicy
RuntimePolicy
StoragePolicy
PublicationPolicy
ResourcePolicy
ExecutionPolicy
```

The taxonomy is nonbinding. Every policy decision has one declared final
authority, but that does not require a central policy layer. A shared authority
is justified only when at least two production owners make the same decision
from equivalent inputs with the same defaults, precedence, overrides, errors,
and outputs; one bounded migration must move every caller and retire the
duplicates net-negatively. Re-admission at a distinct trust or mutation
boundary is not duplicate policy. `AC-INV-011` separately binds one declared
admission chain and final authority per artifact class or guarantee without
creating one global implementation or god object.

A functional owner either owns a policy decision or requests it from the
declared authority; it does not reimplement locking, rename, durability,
runtime, validation, publication, or resource semantics owned elsewhere. A
policy layer is justified only when it consolidates current repeated behavior;
generic wrappers that leave all old decisions in place do not satisfy the
campaign.

`AC-SLICE-06` inventories candidates against this gate and may close with no
shared layer. Any selected consolidation remains a bounded implementation
slice; generic policy-object families, package/service placement, and uniform
APIs are not campaign prerequisites.

### 8.5 Artifact lifecycle and storage boundary

**Partially resolved:** logical artifact lifecycle/admission is distinct from
physical storage. Storage, copying, publication, or workflow-engine success
cannot by itself grant scientific completion or artifact admission. The
following state model remains a proposal:

```text
ArtifactCandidate
      |
      v
  Validation
      |
      v
   Admission
      |
      v
  Publication
      |
      v
   Immutable Artifact
```

The exact states and generalized owner are open. `AC-INV-011` makes one
declared admission chain and final authority per artifact class or guarantee a
binding target; current class-specific authorities remain the accepted
default. Visible provisional/failure state and mutation detection remain
separately qualified in the constitution.

Two sources place a named **Artifact Store** between stages and reports. The
campaign deliberately defers that distinct boundary: no Store service,
registry, universal manifest, or second artifact authority is selected. The
decision is revisited only for a separately approved concrete unmet need that
current class-specific owners cannot handle cleanly. Cross-run reuse,
duplicated resolution, external or large artifacts, Run-Bundle portability,
caching, and garbage collection are nonbinding examples, not a settled trigger
roster. Any later proposal still applies `AC-INV-011` and must replace rather
than duplicate authority.

`AC-SLICE-07` remains open only for demonstrated artifact-class lifecycle or
admission gaps and any resulting bounded migration. A distinct Store is not a
prerequisite for that work.

### 8.6 Ratified and open abstraction guardrails

The binding constitution now requires operational mechanics to remain
encapsulatable while review-relevant science stays visible; one final authority
per artifact class or guarantee without a god object; bounded migration with
caller migration, parity, owned temporary compatibility, and eventual
retirement; and mapped equal-or-stronger protection before direct-owner,
adversarial, seeded-fault, or synthetic end-to-end defenses are removed. The
replacement defense may already survive elsewhere; removing redundancy does
not require creating a duplicate test. A proven impossible same-process state
may lose its redundant check and check-only test without replacement; high-risk,
ambiguous, or directly user-facing removal remains approval-gated. Evidence
levels remain distinct, so
neither coverage nor a scientist-facing synthetic golden path proves scheduler,
production, scientific-review, or biological readiness.

The later `AC-GUARD-006` through `AC-GUARD-008` additions also make
maintenance-surface compression and immutable-by-default boundaries binding,
reserve `Run` for the immutable plan, and require explicit user approval before
retained evidence is deleted. A protection is an executable or static defense
such as a test, validator, CI check, fixture, or oracle. Evidence is a retained
record or artifact that supports or bounds a claim, reproduction, or recovery.
A fixture, golden, or oracle may be both; in that case both the protection and
evidence guardrails apply.

Exact facade use, package order, layer APIs, the lightweight
collaborator-module extension mechanism, and integration with supported
workflow/scheduler machinery remain just-in-time design choices within the
binding prohibition on a mandatory universal Stage/workflow framework or
second scheduler. Adding a wrapper beside an existing authority without a
bounded caller migration and retirement condition cannot satisfy the ratified
guardrails.

## 9. Runtime, execution, storage, and Doctor

### 9.1 Runtime modes are distinct from execution profiles

The intake proposed three runtime modes:

| Runtime mode | Intent | Current disposition |
|---|---|---|
| Managed | Use an EMRYS-provided reproducible environment | The initial Linux x86-64 repair is implemented through Project-aware Doctor and the packaged Pixi lock; broader qualification remains Open. |
| Site | Discover and admit institution-provided modules and tools | Implemented as dry-run-first `emrys runtime discover [--execute]`. |
| Explicit | Supply advanced tool paths and identities | Required future capability; exact `define` surface remains Open. |

The accepted interpretation is acquisition/provisioning journeys that
converge on one admitted runtime authority, not three runtime object models or
authorities. The institution-provided discovery route and Project-owned
`runtime/runtime.tsv`, plus the first bounded Managed repair, are settled;
taxonomy, named-profile management, and the Explicit surface stay open.

Runtime discovery inspects Python/EMRYS, the active workflow
engine (currently Snakemake where the selected path depends on it), STAR,
samtools, GATK, Picard, bcftools, RSeQC, R, Java, and the relevant R environment,
then presents versions and readiness before `--execute` admission. Snakemake remains an
internal execution dependency, not a scientific authority or a configuration
surface ordinary scientists must author.

Execution profiles are a different axis. The implemented v1 profile combines
computational resources with direct or Slurm placement, uses a packaged direct
default when no file is selected, and accepts an explicit profile path plus
the existing admitted resource overrides. It does not select runtime
provisioning mode, storage policy, or a second application backend. Proposed
future names include `local`, `cluster`, `cluster-debug`, `development`, and
`production`; a registry, discovery/acceptance lifecycle, storage location,
and final taxonomy remain open.
Named execution profiles are likely necessary for operator usability, but
their names, registry/discovery mechanism, precedence beyond v1, and storage
remain unselected.

Managed-runtime groundwork uses Pixi with one Linux x86-64 manifest/lock and
declared glibc 2.28/Linux 4.18 virtual-package values. Those solve inputs do
not prove an actual kernel or cluster. Ordinary CI installs the unchanged lock
and invokes its tools in Rocky 8.10, Ubuntu 22.04, and Debian 12 userspaces. A
real-tool managed direct Ubuntu golden-path job is implemented; its exact-head
execution is pending. Actual Linux 4.18, broader portability, site, scheduler,
security, and update qualification remain open. A container remains an
independent `CONTAINER-01` option rather than part of guided setup.

### 9.2 Transparent execution

Ordinary users can now request a run without operating a SLURM wrapper or
assembling launcher configuration. The grouped `run` and `resume` routes use
the built-in direct profile by default or one explicitly selected profile; a
Slurm profile causes exactly one outer submission and the allocated process
runs the same local scientific backend. Automatic profile discovery or
selection, named profiles, and the eventual role-aware surface remain open.

The primary progress surface should use scientific milestones such as
preparation, alignment, QC, candidate evidence, statistical testing, and report
generation. Owner counts, workflow attempts, transactions, and engine commands
belong in durable logs, evidence, and expert inspection.

### 9.3 Doctor behavior and repair override

Doctor should derive project, reference, workspace, runtime, storage, input,
and scheduler facts from admitted configuration. A concise view should cover:

```text
Storage: workspace, sidecars, permissions, locking, rename, durability
Runtime: Python, EMRYS, active workflow engine/Snakemake, R, STAR, samtools,
         GATK, Picard, bcftools, RSeQC, Java
Inputs: FASTQs, FASTA, GTF, design
Execution: local process and/or scheduler readiness
```

Failures should explain what was detected, why it is unacceptable, and one or
more supported remediations.

The former categorical non-mutating Doctor requirement is **overridden**.
The campaign requirement is now:

- diagnosis is the default;
- repair requires an explicit action, such as the proposed `--fix` or a
  dedicated repair command;
- repair scope is previewed or otherwise made clear before execution;
- every mutation is bounded and reported;
- dependency solving and installation are delegated to the established package
  manager selected for that environment; Doctor owns the repair plan,
  verifies explicit operator authority, and owns orchestration, reporting,
  provenance, and requalification rather than package-manager mechanics;
- EMRYS-owned environments may be provisioned or replaced; user/site-owned
  environments require explicit authority and should normally be supplemented
  through an EMRYS-owned overlay rather than silently mutated;
- scientific inputs and references are never silently rewritten or adopted;
- biological relationships, secrets, and site policy are never invented;
- generated directories or EMRYS-owned configuration may be created when the
  user deliberately requests repair/setup and the ownership contract permits
  it;
- qualification probes have bounded locations, deterministic cleanup, and an
  explicit evidence ceiling;
- low-level storage/runtime qualification remains available through an
  advanced or debug interface.

The exact split among `doctor`, `validate/check`, `setup`, and repair commands
is an open UX decision.

## 10. Golden path

The golden path is a **binding capability set and successful end state**. The
current supported synthetic order is:

```text
emrys init synthetic -> emrys doctor --repair -> emrys run -> emrys inspect run
```

Reporting remains automatic by default after successful scientific work and
can be disabled or regenerated independently. The intake's three materially
different sequences remain historical suggestions rather than current
interfaces:

```text
AC-SRC-001: init -> check -> run -> reports
AC-SRC-002: repository -> doctor -> demo -> init -> run -> report
AC-SRC-003: install -> Doctor -> Demo -> Configure -> Run -> Inspect result
```

The selected synthetic initializer creates its Project, Doctor establishes
readiness, Run executes the immutable plan and automatic reporting, and
inspection admits the retained outcome. The broader real-data, site-runtime,
and Slurm journeys remain role-specific extensions. The required capabilities
remain:

```text
supported installation/runtime
readiness diagnosis
neutral synthetic execution
project creation/configuration
validation and immutable planning
execution and useful progress/status
safe recovery when possible
discoverable valid result and report
```

A proposed interaction is:

```text
emrys init my-analysis
emrys check
emrys run
emrys status
emrys report
```

The workflow must:

- create EMRYS-owned project, workspace, run, result, runtime, and log
  directories without manual assembly;
- generate structural manifests from supplied paths while asking for ambiguous
  biological meaning;
- qualify inputs, runtime, storage, and execution before expensive work;
- preserve immutable plan-before-execute safety without requiring the user to
  copy a run root between commands;
- show the effective analysis, reference, sample count, resources, and executor
  before confirmation;
- support a deliberate noninteractive path for automation;
- show scientific milestones and actionable failures;
- print one canonical result/report location on completion; and
- produce a valid synthetic result without requiring architecture documents.

One source illustrated completion with a scientific funnel—42,381 candidates
evaluated, 127 passing statistical/effect thresholds, and 18 passing the
background criterion—followed by `scientific.html` and `evidence.html`. These
counts and filenames are examples, not targets; they preserve the proposed
shape of an immediately understandable completion summary.

Local/synthetic learning and production/HPC admission are distinct experiences.
A production environment must not be required merely to learn the software,
and success in the synthetic path is not cluster, production, scientific, or
biological proof.

## 11. Status, recovery, Run Bundle, and reports

### 11.1 User-facing state and recovery

The internal state machine may remain detailed. A proposed public vocabulary
is:

```text
PENDING
RUNNING
COMPLETE
FAILED
RECOVERABLE
```

The sources also supplied this illustrative internal sequence:

```text
prepared -> validated -> executing -> committing -> published -> complete
```

Neither vocabulary is settled. The required experience is that status states
where the run stopped, why it stopped, whether resume is safe, and the next
supported action. Resume should determine internally which admitted artifacts
remain valid, which outputs are provisional, what must roll back, what can be
reused, and what must be recomputed. Recovery should be operationally boring
without weakening fail-closed behavior.

### 11.2 Canonical Run Bundle

A proposed completed-run abstraction is:

```text
run/
+-- manifest.json
+-- configuration.yaml
+-- identity.json
+-- artifacts/
+-- evidence/
+-- logs/
+-- reports/
```

The campaign leans toward a Run Bundle being useful, but whether it is a view,
export, snapshot, persisted object, or other shape remains open. The exact
layout is also open. The desired abstraction is a portable, coherent
representation of everything needed to understand a run, supporting archival,
sharing, debugging, reproducibility, support, and publication. Portability,
redaction, external references, large-data handling, regeneration, and archive
semantics require explicit decisions.

### 11.3 Three report purposes

Reporting should preserve three distinct questions:

| Surface | Primary question |
|---|---|
| Scientific report | What did the analysis find, and what are its scientific limitations? |
| Evidence/provenance report | Why should the reader trust that this result corresponds to these inputs, tools, validations, and artifacts? |
| Operational report | How did execution proceed, consume resources, fail, recover, or complete? |

The ordinary report should lead with scientific findings. Evidence and
operations remain discoverable without burying interpretation. A concise run
integrity summary may state that declared artifacts are present, hashed,
validated, and associated with the run, with receipts and transaction details
behind an inspection route.

All scientist-valued outputs should be discoverable beneath the canonical
run-relative results surface. Reporting is now resolved as downstream
operational work, not a semantic scientific Stage. A full run invokes it by
default after upstream admission, with an explicit supported opt-out, and a
report can be regenerated independently without rerunning or changing the
identity/validity of completed science. A report failure remains visible but
does not invalidate admitted upstream work.

Whether reports are immutable artifacts, derived views, or both remains open,
as do the exact persisted association between Run and report or execution
state, retry/resume and exit presentation, canonical location, and whether
multiple audience views share one receipt-last publication transaction or use
profile-specific receipts. `AC-DEC-014` now preserves only those residual
choices rather than reopening reporting's downstream classification, default
invocation, opt-out, or regeneration semantics.

## 12. Scientific modularity and audit boundary

Operational simplification must not distract from scientific architecture.

- Compatible per-sample work through Step 06 should be reusable for separately
  identified cohort, subset, sensitivity, or downstream analyses beginning at
  the cohort-dependent boundary.
- The completed `ANALYSIS-02` v1 boundary admits one explicitly selected
  installed `emrys.analysis_modules` entry point. Its closed descriptor owns
  configuration admission and one or two downstream Step 09/10 tasks with
  typed predecessor inputs, result and validation outputs, dependencies,
  planning/failure boundaries, minimum memory, admitted runtime needs, and
  one implementation package. Fixed processing through Step 08, immutable
  Analysis/Run identity, private `TaskDispatch`, the existing backend, and
  evidence admission remain EMRYS-owned.
- Each module renders its own bespoke scientific HTML from an admitted,
  read-only Run/result context and declares its interpretation boundary.
  EMRYS retains the evidence-and-operations view and the complete automatic,
  disable-able, independently regenerable report transaction. No generic
  report schema, template system, or customizable-section DSL is introduced.
  The exact provider distribution, entry point, configuration schema,
  implementation content, and trust classification are bound and re-admitted.
  An external-provider fixture proves that adding a differential analysis
  requires no edit to the built-in scientific core, workflow graph, scheduler,
  or evidence/report transaction owner.
- The algorithms, parameters, assumptions, interpretation boundaries, and
  implementation needed for scientific review must remain recognizable and
  inspectable under binding `AC-GUARD-002`; the v1 entry-point and task-centric
  module boundary is selected without a universal Stage hierarchy, workflow
  language, second scheduler, or auto-installation mechanism.

The intake separately recommends a scientific audit of Steps 07–09, with
particular attention to:

- candidate-universe selection;
- count construction;
- CMH table construction;
- the exact family over which Benjamini–Hochberg correction is performed;
- threshold and effect-size application; and
- independent numerical oracles for Steps 08 and 09.

This is not a claim that a defect exists. Audit scope, reviewers, fixtures,
reference calculations, and acceptance evidence must be defined as separate
work. Scientific review remains distinct from the architecture campaign's
software evidence.

One source further recommends pursuing this audit in parallel as the next
scientific-review focus instead of spending additional effort on the already
strong filesystem/provenance machinery. That is retained as a sequencing
suggestion—not an accepted priority—and remains subordinate to `AC-DEC-020` and
the later Importance/Complexity pass.

## 13. Incremental migration strategy

Invariant preservation, bounded incremental migration, caller migration and
relevant parity before replacement completion, and eventual retirement after
an explicit compatibility condition are binding. Facade-first sequencing is
not. One source proposed this order:

1. Inventory live owners, callers, state transitions, artifact paths,
   execution paths, duplicated policies, and user-authored configuration.
2. Apply the ratified architectural invariants to the selected slice.
3. Introduce the smallest useful Project/Run/application facades around current
   behavior.
4. Move the public CLI and documentation to those facades while retaining
   expert inspection.
5. Consolidate shared policy only when it passes the ratified duplicate-policy
   gate; evaluate other execution, artifact, and lifecycle abstractions under
   their own approved boundaries, one bounded package at a time.
6. Prove parity and failure behavior at the appropriate evidence level.
7. Remove superseded implementations, adapters, and compatibility paths rather
   than leaving permanent dual architecture.
8. Measure whether the user and maintenance surface actually became simpler.

Regardless of the selected sequence, “introduce an abstraction” is not
completion. A package closes only when its callers use the intended owner,
relevant parity is established, protected behavior and evidence remain intact,
and every old path has the disposition required by its retirement condition.
`AC-DEC-018` now owns only each migration's compatibility window, warnings,
fixtures, and removal evidence. `AC-DEC-020` owns work order and just-in-time
facade sequencing; neither reopens the binding eventual-retirement rule.

### 13.1 Mandatory per-slice compression and mutation protocol

This is the canonical protocol for every architecture audit, decision slice,
and implementation slice. Other governance documents point here rather than
creating competing templates.

Before design selection, the slice records a compression register with one row
for every concrete retention, consolidation, retirement, or deferral
opportunity it finds. Each row records:

- surface and category: maintained product code, wrapper/compatibility path,
  configuration/script/schema/documentation, protection, or evidence;
- current owner, callers, and consumers;
- the unique responsibility, invariant, claim, recovery need, or reader need;
- the evidence for redundancy;
- proposed disposition: retain, consolidate, retire, or defer;
- the surviving authority;
- for a protection, the trust boundary and risk class, whether the defended
  state is reachable outside a test seam, and whether an independent invariant
  remains;
- for shell or generated shell, `KEEP`, `CONVERT`, or `RETIRE`, including the
  shell-native responsibility and total product/test/caller/cross-language
  effect;
- for a touched retained operation, the `LOG-05` adoption, not-applicable, or
  retiring disposition;
- estimated and then actual change in files, lines, public concepts,
  configuration artifacts, call edges, and compatibility paths; and
- preconditions, including caller migration, parity, evidence review,
  retirement condition, and any explicit approval required.

The same audit inventories mutable state, its owner, lifetime, readers and
writers, why mutation is necessary, and whether it can become an immutable
boundary value. Draft construction and tightly owned attempt, lock, log, or
transaction state may remain mutable when justified. A Run is never mutable. The
audit records facts and options; it does not itself settle nouns, nesting,
APIs, backends, policies, persistence, or other application-model choices.
Those require a separate explicit decision such as
`ARCH-MODEL-DECISION-01`, and only the exact boundary named by that decision is
settled.

An implementation slice closes only when it:

1. makes the smallest complete vertical change and migrates the selected
   callers;
2. removes the superseded responsibility once parity and its retirement
   condition are satisfied;
3. is net-negative in maintained product code and adds no maintained product
   file by default, or stops for user approval of quantified growth and its
   justification, plus an owner and retirement condition when temporary;
4. reports before/after changes separately for product implementation,
   protections/tests, configuration/documentation, retained evidence, public
   concepts, and compatibility paths; and
5. reports every remaining mutable exception and its owner and justification.

If a retained applicable operation's human output or durable diagnostics
change, `LOG-05` adoption is part of that same vertical slice. The slice may not
add an interim logger, output convention, wrapper-owned attempt, or parallel
shell/Python implementation. A touched shell surface closes only when its
recorded `KEEP`, `CONVERT`, or `RETIRE` disposition is realized or explicitly
deferred with a reason and trigger.

Regardless of whether a mechanism is classified as a protection, any
high-risk, directly user-facing, execution-boundary, or evidence-validation
retirement, consolidation, or conversion requires the user's explicit
approval. This implementation gate is independent of the stricter retained-
evidence deletion gate below.

No category offsets another. Deleting tests, documentation, configuration, or
evidence cannot make product growth appear net-negative. Generated files,
runtime environments, vendored bulk, and moving logic into configuration do
not count as maintained-source reduction. File and line counts are secondary
signals: a god module, denser code, hidden generated logic, weakened protection,
or an extra facade beside the old authority fails the compression requirement
even if counts decline. Temporary growth remains growth until its owner,
retirement condition, and removal are recorded.

Protection retirement follows `AC-GUARD-005`. External-input, filesystem,
concurrency, crash, recovery, persistence, evidence, and supported
public-behavior boundaries require a mapped equal-or-stronger surviving
defense. A low-risk check and its check-only test may retire without replacement
only when the slice proves that the state is impossible outside the test seam,
has one admitted immutable producer, has no supported injection or mutation
path, and supports no distinct failure mode or claim. High-risk, ambiguous, or
directly user-facing protection removal requires explicit user approval.
Evidence retirement follows a separate gate. The proposal must name
the exact artifacts or bounded class; claims and recovery paths supported;
producers and consumers; retention requirement; redundancy basis;
discoverability, verification, and evidence-level effects; and rollback. The
user must explicitly approve that exact deletion, which is then isolated in a
separate commit. Ambiguous fixtures, goldens, oracles, receipts, logs, reports,
and dated records are treated as evidence until classified otherwise.

### 13.2 Nonbinding sequencing proposals from the sources

The sources suggested several useful but different sequences. None is adopted
by this document.

| Source proposal | Suggested sequence |
|---|---|
| UX-first seven phases | UX wrapper; unified scientific configuration; runtime abstraction; Stage abstraction; simplified identities; Steps 08/09 numerical validation; role-based documentation |
| Facade-first six phases | Freeze invariants; introduce Project/Run/Artifact/Execution/Report facades; move CLI; consolidate implementations; mark internals as operator/developer APIs; measure |
| Detailed nine phases | Inventory; domain objects; policy consolidation; execution abstraction; source-proposed “Run coordination” (now constrained to application coordination around immutable Run); high-level CLI; profiles; deletion; journey-first documentation |

The expanded source also proposed this P0–P3 order:

- **Suggested P0:** invariants, Doctor, synthetic golden path, scientific versus
  operational configuration, and Project/Run/Artifact/Execution/Report
  boundaries.
- **Suggested P1:** execution, artifact, and policy consolidation; state hiding;
  local/cluster profiles.
- **Suggested P2:** status, resume, inspect/explain, and Run Bundle.
- **Suggested P3:** duplicate-validator and lifecycle deletion, obsolete
  migration/compatibility removal, and infrastructure extraction from stages.

These labels record source recommendations only. Actual ordering will follow
task slicing, evidence review, and the later importance/complexity scoring pass.

### 13.3 Accepted LOG-05 sequencing boundary

**Binding:** `LOG-05` planning and guard work may precede production adoption.
Wiring proceeds operation by operation through separately approved bounded
slices and need not wait for unrelated campaign work. The
[matrix guard](backlog_matrix.md#log-05-adoption-and-closure-guard) owns slice
admission and closure, and the
[logging contract](../design/LOGGING_CONTRACT.md#adoption-boundary) owns exact
operation behavior. Transitional compatibility support does not satisfy final
retained-operation coverage, and retiring surfaces do not advance closure.

Every implementation slice that touches a retained applicable operation now
records its `LOG-05` disposition. A slice changing that operation's human output
or durable diagnostics adopts the foundation in the same vertical change; it
does not add an interim convention for later replacement. Operations proven
not applicable or retiring are recorded as such and do not become adopters.

This resolves only the `LOG-05` migration boundary within `AC-DEC-020`. It does
not settle any other campaign ordering or interface decision.

### 13.4 Bounded slice record: Step 07 verified input-identity reuse

**Table 13.4-1 — Compression and mutation register**

| Surface/category | Finding | Disposition and surviving authority | Delta | Preconditions or retirement condition |
|---|---|---|---:|---|
| Maintained product: repeated Step 07 full-input hashing | The local-pilot task already hashes every declared input twice before producer entry and once afterward; direct Step 07 independently performs three full roster passes. | Consolidate only the admitted local-pilot route: its entry snapshots supply one producer-lifetime aggregate, Step 07 retains one final full roster comparison before publication, and the task retains its final declared-input recheck. Normalize relative selector files from their manifest owner so the two rosters cannot bind different paths. | `+58/-11`, net `+47` lines in three existing files; `0` files | Exact ordered-roster parity; inherited-value scrubbing; nested selector-path parity; mutation failure before publication; unchanged receipt/schema |
| Direct compatibility path | A direct caller has no admitted task-entry identity. | Retain its existing three-pass `--no-clobber` behavior. | `0` paths | Retire only with direct invocation or after it receives equivalent authority. |
| Protections and evidence | Direct mutation, fail-closed publication, and task-boundary guarantees remain necessary. | Retain the existing fresh-clone cross-boundary E2E and all direct-path protections; add nested selector-authority plus valid bound-route and mutation tests; add no receipt field or persistent handoff artifact. | Test delta recorded in Table 13.4-2 | No protection or evidence deletion. |
| `ANALYSIS-01` physical realization | A Step 06 copy or snapshot may serve portability, retention, or locality but cannot establish reuse authority. | Defer storage realization to `ANALYSIS-01`/`AC-SUG-016`; implement no storage mechanism in this slice. | `0` | Separate identity, compatibility, storage, and site-measurement decision. |

The sole new boundary value is one immutable 64-character aggregate written once by the local-pilot task owner from admitted entry snapshots, read only by the Step 07 producer, scrubbed from inherited and downstream environments, and discarded with the process. It is not persisted in Run, configuration, receipt, schema, logs, or evidence; existing publication and rollback state remains unchanged.

**Table 13.4-2 — Category-separated closeout**

| Category | Estimated delta | Actual delta and disposition |
|---|---:|---|
| Product implementation | `+35–50` lines, `0` files | `+58/-11`, net `+47` lines in three existing files; approved bounded exception; no temporary owner or retirement condition |
| Protections/tests | `+60–100` lines, `0` files | `+95/-6`, net `+89` lines in two existing files; no protection deleted |
| Configuration/documentation | Approximately `+25` lines, `0` files | `+39/-9`, net `+30` lines in three existing files; contract, matrix context, suggestion, and this register only |
| Retained evidence | `0` | `0`; none added, rewritten, or deleted |
| Public concepts/interfaces | `0` | `0`; no command, option, schema, receipt field, public noun, or backend |
| Compatibility paths | `0` | `0`; direct three-pass path retained |
| Persisted mutable state | `0` | `0`; one producer-lifetime immutable value only |

### 13.5 Bounded slice record: Run status and recovery guidance

| Surface/category | Finding | Disposition and surviving authority | Preconditions or retirement condition |
|---|---|---|---|
| Maintained product: aggregate `RunInspection` projections | `state`, `resume_available`, and `local_pipeline_complete` have no production callers and duplicate the separated status domains. | **Retire.** Current callers use integrity, Attempt outcome, Results, reporting, and recovery directly. | All direct callers migrated; focused lifecycle and presentation coverage retained. |
| Maintained product: inspection guidance | The separated domains identify a safe action, but the existing public inspection leaves the operator to infer it. | **Retain one projection.** The existing inspect route prints one deterministic next action and fails closed for blockers. | No new command, schema, backend, repair operation, or persisted authority. |
| Maintained product: scientific progress | Internal Step identities are already admitted persisted facts, but exposing each task by default leaks orchestration detail. | **Project five public milestones.** Preparation, alignment/sample processing, QC evidence, candidate evidence, and statistical/context processing derive only from admitted task records. Reporting remains downstream and separate; an unmapped admitted Step fails closed. | No workflow stage, status store, schema, backend, dashboard, or mutable progress authority is added. |
| Maintained product: elapsed time | Summing resumed work or estimating completion would manufacture semantics absent from retained evidence. | **Project one bounded duration.** A running Attempt uses its creation time and the current clock; a terminal Attempt uses its own creation and receipt-finish times. Missing, mixed, or negative boundaries report unavailable. Predecessor durations are never summed and ETA is never inferred. | Attempt and receipt records remain the only persisted boundaries. |
| Public presentation | One detail level either overwhelms ordinary users or withholds useful operator evidence. | **Tier the existing route.** Normal shows public status, milestones, Results, reporting, blockers, recovery, next action, and result links; verbose adds milestone counts, Run/Attempt placement, and transaction aggregates; debug adds exact admitted receipt, engine, task, task-attempt, and stream references. | One `--detail` selector only; no new command, API, role registry, or alternate authority. |
| Compatibility/evidence | Receipt-v1 uses `local_pipeline_complete` as historical format evidence; the active CI E2E summary no longer copies that aggregate. | **Retain receipt v1 unchanged.** Its field is not status authority for current product decisions. | Any future receipt-v1 evidence deletion requires exact review and separate explicit approval. |
| Protections and redundant inspection state | Aggregate assertions obscure which authority blocked or completed a Run. Inspection also retained unused copies of records, paths, blockers, and identifiers. | **Consolidate projections, retain evidence re-admission.** Existing fault/lifecycle tests assert the owning domain. Five unused projections and one internal export retire. Independent review confirmed that the ledger's second semantic admission protects transitive evidence against concurrent mutation, so it remains alongside task-start admission, reference rechecks, exact start/origin binding, and verified-file concurrency detection. | No direct-owner, trust-boundary, fault, lifecycle, or E2E defense class is removed; retained evidence is unchanged. |
| `LOG-05` | Read-only inspection neither starts work nor owns a durable diagnostic lifecycle. | **Not applicable to this operation.** Do not create an application Attempt or log merely to read persisted state. | `LOG-05` remains Open for other retained applicable operations and parity. |

Initial next-action cut closeout: maintained product Python two existing files, `+25/-36`, net `-11`;
protections/tests three existing files, `+100/-31`; documentation five files,
`+34/-13`; configuration/schema/workflow and retained evidence zero;
one inspect output line added and three direct Python accessors retired; receipt-v1
and CI E2E summary v1 unchanged; no compatibility path or mutable state added.

`OBS-02` completion increment before commit: maintained product Python two
existing files, `+166/-56`, net `+110`; protections/tests three existing files,
`+125/-5`; documentation three existing files, `+23/-8`;
configuration/schema/workflow and retained evidence zero; one optional selector on
the existing inspect route; five unused Python projections and one internal
export retired while high-risk semantic evidence re-admission remains; no compatibility path, evidence deletion,
status store, backend, dashboard change, application log, or mutable state added.
The user approved this permanent net `+110` maintained-product exception on
2026-08-28; the existing control and inspection owners retain the surface.

### 13.6 Bounded slice record: unified execution profile and Run placement

This approved cutover replaces the split launcher/resource/wrapper surface with
one admitted execution profile and one private whole-Run Slurm transport. It
also adopts the `LOG-05` foundation for retained `run` and `resume` execution.
Local Snakemake remains the only scientific backend.

| Surface/category | Finding | Disposition and surviving authority | Preconditions or retirement condition |
|---|---|---|---|
| Maintained product: launcher, resource, and Run-control owners | A 1,081-line launcher owner, a generated wrapper, separate launcher/resource defaults, and grouped control divided one execution decision across parallel paths. | **Consolidate and retire.** `execution_profile.py` owns immutable profile admission, `slurm_submission.py` owns the private one-submission transport, and grouped control owns run/resume behavior. `launcher_config.py` and its schema/defaults are retired. | Direct and Slurm planning parity, exact profile/source binding, one scheduler submission, and current caller migration. |
| Public configuration and compatibility | Operators previously assembled two adjacent files and a wrapper. | **Replace.** A built-in direct profile is the default; `--execution-profile` selects one explicit combined profile. The starter contains `emrys.execution.yaml`. Retired adjacent launcher/resource names fail closed instead of invoking a shadow compatibility implementation. | Historical Run, Attempt, and allocation records remain readable; no alias or dual authority survives. |
| Shell | The generated `run-in-slurm.sh` made users and tests carry cross-language control logic. | **RETIRE** the generated wrapper. **KEEP** only the private minimal batch bootstrap for module initialization, private scratch cleanup, and final `exec`. The sixteen owner-local stage/utility `.slurm` scripts are untouched and **DEFERRED** to their own caller-complete slices. | Real scheduler/site behavior and the deferred scripts remain open; no dashboard change. |
| Protections/tests | Launcher-only tests repeated policy now admitted by profile, transport, control, and lifecycle owners. Some same-process re-admission and frozen-dataclass tests defended impossible states. | **Consolidate.** Preserve external-input, no-follow filesystem, environment scrubbing, scheduler-result, source/profile binding, allocation/placement, signal, recovery, receipt-last, and historical-read defenses in their final owners. Retire launcher-only and check-only tests with the removed paths. | No evidence oracle, receipt, log, recovery record, scientific protection, or supported external-boundary defense is deleted. |
| `LOG-05` | Retained run/resume execution lacked one concise application-attempt log and milestone surface. | **ADOPT.** Run/resume execution owns one protected non-authoritative application log, terminalizes preflight failures/interruption, reports owned lock/recovery paths, and cannot change receipt or exit outcome after log initialization. Scheduler submission emits only its machine receipt; the allocated Run process owns the application log. | `OBS-01` and `OBS-02` are complete for their distinct presentation surfaces; broader retained-operation adoption and parity remain open under `LOG-05`. |
| Documentation | The legacy launcher regression transcript names retired files and commands after its live safeguards moved to owner contracts, tests, CI, the runbook, and configuration guide. | **RETIRE** `LOCAL_PILOT_LAUNCHER_TEST_PLAN.md`; Git history preserves the non-authoritative transcript. `ORCHESTRATION_READINESS.md` remains the sole open `DOC-05` transition source. | This is stale-document retirement, not retained-evidence deletion. |
| Mutable state | Placement and runtime mechanics previously leaked across configuration and wrapper state. | Run remains immutable. Computational declaration remains Run-bound; profile source, realized allocation, placement, and scheduler job ID are immutable Attempt-local facts. Application-log state, lifecycle locks/transactions, external scheduler queue state, and private scratch remain tightly owned mutable exceptions. | No Attempt may alter or reconstruct Run; reporting remains default-on and downstream rather than a semantic stage. |

**Category-separated closeout from `1abbf094`:**

| Category | Actual delta and disposition |
|---|---|
| Product implementation | Twelve Python owner files, `+1496/-1704`, net `-208` lines. Two focused owners replace the launcher monolith, so the approved responsibility split adds one net maintained product file while materially reducing product lines and eliminating the parallel launcher authority. |
| Protections/tests | Twenty-one test/documentation-gate files, `+2104/-2036`, net `+68` lines. Launcher-only and impossible-state checks retire; final-owner external, filesystem, scheduler, lifecycle, recovery, persistence, and logging defenses remain. |
| Configuration/schema/workflow | Fourteen files, `+452/-584`, net `-132` lines and two fewer maintained files: five added execution-profile, default, and schema owners replace seven split examples, defaults, and launcher-schema paths; the two remaining files are updated configuration/schema guides. |
| Documentation | Eighteen files, `+700/-763`, net `-63` lines. Current owner, operator, onboarding, campaign, and matrix text replaces wrapper/config-split guidance; the stale launcher transcript retires. |
| Retained evidence | `0`; no evidence was added, rewritten, moved, or deleted. Historical persisted formats remain readable. |
| Public concepts/interfaces | One explicit execution-profile artifact/selector replaces the generated wrapper, separate launcher/resource artifacts, and launcher-specific control surface. Run/resume gain concise `LOG-05` milestones and durable log discovery; no second backend, scheduler, runtime mode, named-profile registry, or new scientific noun is added. |
| Compatibility paths | The generated wrapper and split current configuration paths retire without aliases; retired adjacent filenames fail closed. Historical Run, Attempt, allocation, and receipt formats remain admitted. |
| Mutable product state | No Run mutation is added. Attempt placement is immutable provenance; only the existing bounded lifecycle state plus the non-authoritative application log, scheduler queue, and private scratch are mutable. |

Focused local evidence is recorded in the findings matrix. Long aggregate,
fresh-clone, real-tool, and scheduler/site validation remains CI or site work;
none is inferred from the focused local checks.

### 13.7 Bounded slice record: concise Run console projection

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Normal Run control | Operation labels, split work counts, paths, resources, profiles, and scheduler streams obscured the scientific journey. | **Consolidate and tier.** Normal retains Run identity, one work summary, reporting, phases, verified Results/evidence, warnings/failures, and the durable log path. Verbose owns operational paths/resources; debug owns exact safe commands. |
| Durable application log | Opening metadata was useful evidence but redundantly projected into the normal console. | **Retain durably; narrow only the projection.** The event, message, ordering, schema, and every JSONL field remain unchanged; normal shows its discoverable log path. |
| Automation | Evidence automation parsed operational paths from normal output. | **Use the public verbose level.** Automation opts into the same production interface; no test-only production input or alternate path is introduced. |
| Contracts, evidence, mutation, and shell | Console detail is not execution authority. | Exact scheduler `JOB_ID`/`OUT`/`ERR`, receipts, exits, evidence boundaries, no-write/no-log dry runs, and mutable-state ownership remain unchanged. No evidence or protection is deleted, and no shell is touched. |

Category-separated closeout: maintained product Python two existing files, `+18/-23`, net `-5`, with no product-file growth; protections/tests five
existing files, `+101/-34`, with no defense class retired;
configuration/schema/workflow zero; retained evidence zero added, moved,
rewritten, or deleted; public surface zero commands, flags, schemas, backends,
package-root exports, or public nouns added, while redundant normal fields are
removed or tiered behind existing levels; compatibility zero paths or formats
added or removed; mutable authority zero added. Documentation actuals and
focused validation are recorded in the findings matrix. `OBS-01` is complete;
`LOG-05` remains Open for other retained applicable operations and parity.

### 13.8 Bounded slice record: existing task boundary and Step 08 migration

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Shared representation | Transformation, scientific-analysis, and evidence owners already share private `TaskDispatch`; reporting does not fit without semantic distortion. | **Retain the existing boundary.** Add no Stage/Operation type, registry, schema, public noun, lifecycle framework, or second scheduler. Profiles and the graph retain identity/dependency/resource concerns; reporting remains downstream. |
| Step `08` owner | The shell coordinator duplicated Python scientific-evidence validation and carried a large transaction harness around an R scientific core. | **Convert caller-completely.** One private owner-local Python producer replaces the shell path in materialization, Slurm, provenance, documentation, and tests. The R coordinator/modules and independent validator remain authoritative for their existing responsibilities. |
| Publication and recovery | Lock ownership, exact admitted inputs, staged validation, complete-set replacement, create-exclusive no-clobber publication, input-receipt-last commit, post-publication revalidation, rollback, signal exit, and ambiguous recovery residue are high-risk defenses. | **Retain.** Focused Python tests cover dry-run, successful receipt-last publication, no-clobber refusal, predecessor restoration, failed-restoration residue, foreign locks/incomplete sets, signals, and residue refusal. No evidence is deleted. |
| Scheduler and execution | Sixteen owner-local scheduler wrappers remain a deferred family; this slice touches only Step `08`. | **Migrate the exact caller.** Its existing wrapper invokes the Python owner with the controlled checkout interpreter; local-pilot materialization uses the same owner under the existing guarded R environment. No backend or parity claim is added. |
| `LOG-05` | Step `08` does not own a new application lifecycle. | **Use the existing lifecycle.** Within a full Run it remains a task whose streams and milestones feed the existing Run application Attempt/log; the private direct owner keeps concise human diagnostics. No parallel log, status, or evidence authority is introduced. |

Category-separated actuals and focused validation are recorded in the findings
matrix. `AC-SLICE-04` is complete; broad `ARCH-01`, `ANALYSIS-02`, `LOG-05`,
future collaborator-library design, and the other shell/scheduler candidates
remain Open.

### 13.9 Bounded slice record: minimal Project vertical

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Scientist intake | The active path exposed a request noun even though the selected public model begins at Project. | **Replace directly.** Starter and synthetic input sets publish `project.yaml`; validation, Doctor, and Run accept only `--project`. No alias or second active intake remains. |
| Application boundary | `NormalizationBundle` described a transformation rather than the admitted domain value passed into Run construction. | **Rename and narrow.** Owner-local frozen `ProjectAdmission` retains exact source/profile/construction bytes plus immutable `AnalysisRevision`; `RunCandidate.project.analysis` connects it to existing immutable Run authority and read-only Results. |
| Schema and future design | Final Project keys, nesting, embedded/tabular sample choice, persistence, discovery, defaults, and public package API are not yet selected. | **Defer.** The current closed `emrys.request.v3` record is the temporary adapter behind the Project boundary. No new schema, registry, backend, storage model, or policy abstraction is added. |
| Mutation, evidence, and compression | Doctor and lifecycle span real mutation windows; persisted request-era evidence must remain readable. The policy helper repeated two checks already owned by the policy contract. | **Retain the three temporal admissions; delete only the duplicate in-process semantic checks.** Workflow-attempt request fields/snapshots stay unchanged. No evidence is deleted, no shell is touched, and current Run/Results persistence is unchanged. |

Category-separated actuals and focused validation are recorded in the findings
matrix. `AC-SLICE-03` remains Open for final Project shape/persistence, broader
public Analysis/Results APIs and role disclosure, generalized backend/policy
boundaries, and remaining migrations.

This record preserves the first vertical's historical boundary. Section 13.20
supersedes its temporary request-v3 adapter for the active path without
rewriting the evidence from this earlier slice.

### 13.10 Bounded slice record: Step 07 Python-owner migration

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Step `07` owner and callers | The 976-line shell coordinator duplicated Python parsing and carried publication, process, and recovery state in shell. | **Convert caller-completely.** One private owner-local Python producer replaces the shell path in materialization, the retained Slurm wrapper, provenance rosters, documentation, and tests. There is no compatibility wrapper or new public command. |
| Parsing and validation | Producer and validator used adjacent manifest parsers, while the shell test repeated the same admission cases. | **Consolidate in the existing neutral Step `07` helper.** Strict physical TSV parsing and full partition-row admission now serve both producer and validator. Temporary and final VCF validation, exact sample order, input hashing, receipt-last publication, and the independent validator remain. |
| Compression and protections | PIPE-null branches, type-only assertions, repeated state bits, and shell-only test permutations defended impossible in-process states or the retired implementation. | **Retire only those copies.** Lock ownership, full scientific-input binding, manifest mutation checks, process-group signal/reap behavior, complete-set admission, create-exclusive no-clobber publication, predecessor rollback, failed-restoration residue, and post-publication revalidation remain directly covered. |
| Scheduler and `LOG-05` | Step `07` remains one private task inside the existing Run lifecycle. | **Retain the `.slurm` transport and existing Run logging authority.** The wrapper now delegates to the controlled checkout Python owner. No task-local application log, status authority, scheduler, or backend is added; broader `LOG-05` adoption/parity remains Open. |
| Compatibility and evidence | Changing the registered producer path changes current source identity. | New records identify `producer.py`. Exact historical records remain bound to their recorded producing checkout; this slice does not broaden historical admission or rewrite/delete evidence. No schema, receipt, public noun, Run/Attempt/Results authority, or mutable state changes. |

Category-separated closeout is recorded in the findings matrix. The maintained
product is net-negative with no file growth; the 1,323-line shell-only suite is
replaced by a smaller owner-focused suite plus retained independent validator,
wrapper, materialization, artifact, and public-contract coverage. No retained
evidence is deleted. `AC-SLICE-17` advances by one bounded retirement, while
the retained Step `07` Slurm wrapper and the other shell candidates remain
separate work.

### 13.11 Bounded slice record: downstream Run reporting cutover

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Scientific lifecycle and receipts | Reporting was coupled to the workflow target and terminal Attempt receipt even though it is not scientific work. | **End the Attempt at science.** `cohort_slice` is the fixed-profile stopping boundary; the lock is released and receipt v2 is published before reporting. Receipt v2 is receipt v1 minus the two reporting fields. Exact receipt-v1 reads and complete-report reuse remain supported; v1 cannot originate a new report transaction. |
| Public control and workflow | Users needed three low-level build commands and a composite workflow tail. | **Replace them caller-completely.** `run` and `resume` report by default and accept `--no-report`; `emrys report --run-root ... [--execute]` plans, generates, or reuses reports independently. Reporting creates no Run or Attempt and cannot change scientific success. The three low-level routes, their CLI-shaped adapters, and the workflow reporting rules are retired without aliases. |
| Transaction safety and reuse | Valid complete reporting can be reused, but partial, corrupt, orphaned, linked, or concurrent state is ambiguous. | **Reuse only exact complete state; generate only into empty owned locations.** Preserve artifact-index → run-summary → HTML ordering, preflight → immutable start → fresh preparation → receipt-last publication → semantic verification, no-follow admission, exclusive locks, durability, rollback/recovery, and final read-only inspection. Do not adopt, repair, replace, or delete ambiguous state. |
| Compression and evidence | Private print/int adapters and copied return state added no authority; publisher replacement/recovery branches protect higher-risk cases. | **Delete the low-risk transport copies and retain the protection owners.** One artifact-builder file, adapter-only printers, dead execute fields, a forwarding serializer, broad boundary return state, and obsolete fixture arguments retire. Publisher transactions, independent goldens, historical readers, and predecessor recovery remain; evidence changed by zero. Removing predecessor replacement support requires separate explicit approval. |
| Logging, mutation, and deferred configuration | Reporting needs diagnostics but not another semantic lifecycle. Its former workflow memory settings no longer govern execution. | **Keep logging observational and state bounded.** Automatic reporting continues in the Run application log; standalone generation opens one log only after generation begins; dry-run and reuse open none. Only existing ledgers, output transactions, and the application log may change. `reporting_memory_mb` remains a visible redundant-configuration candidate pending explicit approval; the frozen dashboard and `DOC-05` are untouched. |

Category-separated closeout is recorded in the findings matrix. At this cut,
`RUN-03` still awaited the single-invocation journey; Section 13.12 subsequently
completed that card. Real scheduler/site and outcome parity remain with
`AC-SLICE-05`/`OPS-02`, while broader public-model realization remains with
`AC-SLICE-03`/`CONTROL-01`/`ARCH-01`.

### 13.12 Bounded slice record: single-invocation Run journey

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Direct `run`/`resume` control | Separate no-write and `--execute` invocations rebuilt Attempt-specific plan fields, so the operator could not approve the object later executed. | **Consolidate.** A terminal builds and displays one frozen `AttemptPlan`, reads one confirmation, and passes that exact object into the existing lifecycle. Refusal or EOF returns without mutation; interruption propagates before mutation. Noninteractive omission of `--execute` remains the no-write path. |
| Whole-Run Slurm | Submit-host planning owns placement and transport, while immutable Run admission requires compute-allocation readiness and the scheduler job ID. | **Confirm the exact authority available.** EMRYS constructs one frozen submission plan and displays its placement summary; confirmation creates `<workspace>/logs` and passes that same object to `sbatch` once. The private `--execute` delegate remains noninteractive and constructs the Run inside the allocation. No false submit-host Run/readiness claim is added. |
| Automation and reporting | Automation needs an explicit noninteractive route, and reporting is downstream rather than a semantic stage. | **Retain `--execute`; change no reporting behavior.** Explicit automation and the private delegate never prompt. Default automatic reporting, `--no-report`, and independent `emrys report` generation/reuse retain their existing owners and semantics. |
| Compression and protections | Run/Resume duplicated execution-option definitions, no-write rendering, and identical public error rendering. Scheduler admission, lifecycle/logging, recovery, reporting, and evidence validation protect independent boundaries. | **Consolidate only the low-risk copies.** One shared execution-option owner, no-write renderer, and public control-failure renderer replace the duplicates. Explicit direct `--execute` still opens the application log before semantic preflight; accepted interactive direct execution opens it after consent. Slurm submission owns no application log. No filesystem, scheduler, lifecycle, signal, recovery, reporting, evidence, or historical-reader defense is removed. |
| `LOG-05`, mutation, shell, and evidence | A declined plan is not an adopted execution Attempt. Direct application-log and lifecycle state begin only after execution authority; Slurm transport state begins only after submission authority. | **Keep mutation bounded.** Pre-confirmation creates no workspace, log, Run, Attempt, report transaction, or scheduler submission. After direct confirmation, the existing application-log, lifecycle, and reporting owners remain unchanged. After Slurm confirmation, only scheduler transport state begins; its private delegate later owns the compute-side application log and lifecycle. No shell is touched, no mutable Run state is added, and retained evidence changes by zero. |

The current owner is `local_pilot/control.py`; its callers are the grouped CLI,
the private Slurm delegate, and their control/transport tests. The three
consolidated render/argument/error helpers had no independent invariant. The
retained scheduler, path-admission, lifecycle, logging, recovery, reporting,
and evidence protections defend reachable user-input, external-system,
failure, concurrency, and corruption boundaries; none is deleted. Their
independent checks remain in their existing owners.

The estimate was one existing product file, net nonpositive lines, and zero new
public concepts, configuration artifacts, call edges, or compatibility paths.
The actual product change is `+56/-62`, net `-6`, with zero growth in each of
those other categories. Caller migration is complete for grouped `run` and
`resume`; the duplicate paths are removed. Preconditions were approval of the
bounded behavior, exact-plan/no-write/single-submit focused parity,
documentation alignment, and clean CI. Standard CI run `33286493310` and
extended synthetic CI run `33286499044` both passed on exact implementation
commit `1adb036c9a1052b00ce71552be85300b77532750`; the hosted extended evidence
used disposable single-node Slurm and is not CSU/site or production proof.
The immutable pre-confirmation plan is transient. Accepted direct execution
owns the existing application log and bounded lifecycle state. Slurm
submission and stream state remain transport state; its compute delegate later
owns the application log and Attempt. Test, documentation, and evidence
actuals are recorded in the findings matrix.

This completes `RUN-03`: the current immutable admitted Run plan now supports
terminal confirmation, explicit automation, scientific Results, and downstream
reporting without manual planning-to-execution transfer of a run root or
internal state, while exact historical read/resume compatibility remains
supported through its version-aware path. Real
scheduler/site and outcome parity remain with `AC-SLICE-05`/`OPS-02`; broader
public-model migration remains with `AC-SLICE-03`/`CONTROL-01`/`ARCH-01`; later
Run-locator disclosure was subsequently completed by `AC-SLICE-09` and
`IDENTITY-01`.

### 13.13 Bounded slice record: role-tiered identity and expert inspection

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Ordinary identity | Normal validation and Run inspection exposed more identity concepts than ordinary operation needs. | **Use one primary Run ID.** Normal validation no longer prints the raw Analysis digest; normal planning and inspection retain the Run ID plus scientific outcome. No identity or status authority moves into presentation code. |
| Advanced identity and effective plan | Analysis, Execution Plan, Attempt, placement, and resource facts are useful for advanced operation but are not ordinary control-plane nouns. | **Use the existing verbose tier.** Verbose planning and inspection expose admitted Analysis and Execution-Plan IDs, Attempt identity when present, Run location, placement, and effective resources. Historical Runs are explicitly labeled and receive no fabricated successor identity. |
| Artifact and evidence inspection | Exact authority records, task attempts, verified outputs, receipts, commands, hashes, and evidence blockers already exist in admitted Run inspection. | **Use the existing debug tier.** Debug renders canonical authority paths and digests, effective-plan facts, verified task/output bindings, receipt evidence, and exact safe commands from admitted records. No new command, schema, status store, evidence format, or competing reader is added. |
| Compression, protections, logging, and evidence | Inspection and lifecycle repeated evidence admission, record projection, format plumbing, and impossible partial-state guards. | **Consolidate under one evidence snapshot and one successor authority.** Caller-complete migration removes the duplicate projections and redundant same-process checks while retaining boundary admission, no-follow/path checks, hash/receipt validation, historical reads, failure/recovery evidence, and independent tests. Inspection remains read-only, creates no log, touches no shell or dashboard, and deletes no retained evidence. |

The current owners remain `local_pilot/control.py` for presentation and
`local_pilot/inspection.py` for admitted read state; lifecycle consumes that
inspection authority rather than rebuilding a parallel evidence view. The
implementation changes ten existing files: maintained product Python
`+344/-782`, net `-438`; protections/tests `+114/-30`, net `+84`; whole slice
`+458/-812`, net `-354`. Configuration, schema, workflow, retained evidence,
mutable Run authority, shell, dashboard, commands, flags, backends, package
exports, compatibility paths, and public nouns change by zero. `LOG-05` is not
applicable because the read-only route opens no application log. Exact hosted
CI evidence and its ceiling are recorded in the findings matrix.

A later approved decomposition of the same admitted inspection mechanics (`0c5b7f7f` through `a82f509c`) split the 1,985-line owner by responsibility
and shared existing file-boundary mechanics across its callers. Across the
four commits, maintained product Python is `+1879/-2221`, net `-342`, with
three net-new product files; protections/tests are `+129/-88`, net `+41`;
workflow configuration is `+6/-44`, net `-38`; and the whole change is
`+2014/-2353`, net `-339`. The split adds no public surface, mutable authority,
compatibility route, or retained-evidence change.

### 13.14 Bounded slice record: Project-aware Doctor and managed repair

| Surface/category | Finding | Disposition and surviving authority |
|---|---|---|
| Public readiness | The old grouped Doctor spelling and path-heavy rendering exposed an obsolete campaign name and required operators to assemble readiness context. | **Use top-level `emrys doctor`.** It derives Project, input, storage, runtime, and execution readiness and uses normal/verbose/debug progressive disclosure. Advanced runtime and storage evidence routes remain available without becoming ordinary inputs. |
| Mutation and runtime ownership | Readiness needed actionable storage/runtime repair without making EMRYS a package solver or authorizing mutation of institutional state. | **Use one explicit repair.** `--repair` previews and terminal-confirms; noninteractive mutation requires `--repair --execute`. Doctor may publish the Project-owned direct-storage receipt and mutate only the active checkout-owned `.venv` and Project `runtime/managed`, with create-absent profile admission. `uv`, Pixi, and `renv` own solving/installation. Site/user profiles and declared scientific inputs are preserved, not migrated. Linux x86-64 is the current managed-runtime target. |
| Logging and evidence | Diagnosis is a read and does not own a durable operation; confirmed repair is an attributable maintenance action. | **Adopt `LOG-05` only for repair.** Diagnosis, detail, help, preview, refusal, EOF, and pre-authority interruption open no log. Confirmed repair owns one Project maintenance attempt and terminalizes only after complete requalification. Runtime/storage evidence authorities remain distinct and no retained evidence is deleted. |
| Compression and protections | Doctor and control carried `DoctorOps`/`ControlOps` test-only collaborator facades; materialization accepted test-only clock/token inputs; a legacy absent-workspace branch, duplicate Step `00c` checks already admitted by storage qualification, duplicate runtime/roster checks, and repeated same-process validation added further maintenance surface. | **Retire the low-value copies caller-completely.** Tests inject at real package-manager, subprocess, inspection, publication, time, and UUID boundaries rather than production test-only inputs. External-input admission, clean source identity, Project validation, final storage receipt, runtime-policy tamper checks, package-tree/no-follow identity, namespace-root checks, lifecycle temporal re-admission, confirmation, logging, and requalification survive. Storage-only repair preserves an already-ready site runtime and invokes no package manager. Final category accounting and exact-head engineering evidence belong in the findings matrix. |

`DOCTOR-01` and `AC-SLICE-19` are complete. `AC-INV-018` is preserved for the
implemented supported repair catalog. `RUNTIME-01` remains Open for Explicit
definition, named profiles, broader portability/taxonomy, and updates.
`LOG-05` remains Open for other retained operations and parity. The integrated
`AC-SLICE-13` implementation exists and awaits exact-head managed execution.
The frozen dashboard and post-campaign documentation retirement remain
untouched.

### 13.15 Bounded slice record: managed golden path and demo retirement

| Surface/category | Selected implementation and boundary |
|---|---|
| Supported journey | The current neutral synthetic path is `emrys init synthetic → emrys doctor --repair → emrys run → emrys inspect run`. Doctor-managed runtime repair and automatic reporting stay inside that journey; real-data, site-runtime, and Slurm variants remain advanced extensions. Exact-head CI execution is pending. |
| Storage and placement | Doctor can publish one receipt-last single-host qualification for direct execution. Direct Runs admit that receipt or stronger retained v1 evidence. Slurm and placement-less historical Runs still require the unchanged two-phase v1 receipt; lifecycle re-admits the exact class bound to the Attempt. |
| Retirement and compression | Demo docs/Make ownership, the fake fresh-clone harness, and the coupled public spellings retire. Focused failure/resume tests and independent report goldens remain. A shared stable no-follow reader and the existing exclusive-publication primitive replace duplicate local mechanics without widening the package API. The real Slurm driver/test pair is reduced by 1,271 lines while preserving its scheduler, storage, Step 09 oracle, reporting, retention, and failure boundaries. Maintained product is net `-74` lines and the exact tree is net `-2279`; exact category accounting lives in the findings matrix. No retained evidence is deleted. |
| Mutation and logging | The only new authority is an immutable direct-storage receipt. Synthetic initialization is bounded create-absent publication with no Attempt log; Doctor diagnosis/preview/refusal and Run inspection are read-only/no-log; confirmed repair uses one maintenance log from before mutation through requalification; Run plus automatic reporting keeps its existing single Run log. `LOG-05` remains Open elsewhere; no dashboard or mutable Run authority changes. |

### 13.16 Bounded slice record: no-science harness boundary

| Surface/category | Selected implementation and boundary |
|---|---|
| Command/effect seam | Current no-science Attempts retain `local-science-tools`, immutable Run/Attempt values, required tools, paths, and dispatch input/output rosters. Tests may replace only producer/validator argv plus the directly derived dispatch, workflow-config, and Attempt hashes. Storage/runtime effects use the existing test-owned `LifecycleOps` seams. |
| Retirement and compression | The production `test-double` storage/runtime admission branches, 34 side-manifest inputs, manifest CLI mode, dead fault selector, and duplicate artifact publisher retire. One bounded inline-payload mode remains in the existing test task double. Version-one `test-double` vocabulary remains schema-reader compatibility only; current materialization and executable harness fixtures do not emit it. Exact category accounting lives in the findings matrix. |
| Protections, evidence, mutation, and logging | Exact replacement-invariance, lifecycle re-admission, create-exclusive/fsynced publication, receipts, failure/recovery, and byte-preserving resume remain. No retained evidence is deleted. The harness mutates only isolated test workspaces, changes no public operation output or durable diagnostic, and adds no `LOG-05`, shell, mutable Run, schema, backend, or compatibility path. Its controlled proof remains no-science/no-real-runtime engineering evidence. |

### 13.17 Bounded slice record: golden-path admission compression

| Surface/category | Selected implementation and boundary |
|---|---|
| Runtime admission | Immediate noninteractive `run`/`resume --execute` reuses the runtime inspection that constructed the immutable plan, then retains the full post-workflow probe. A terminal-confirmed plan still performs a fresh execution-time probe because confirmation may introduce delay. Exact tool bytes, profile bytes and hash, fixed policy, source, storage, and Attempt identities are re-admitted before publication in every path. Public behavior, schemas, evidence, logging, and retained files change by zero. |
| Reporting admission | One reporting invocation prepares each transaction once and validates artifact index, run summary, and HTML report topologically. Each downstream step rechecks the exact predecessor receipt; independent validators and later `inspect run` calls start fresh. Duplicate recursive semantic validation, its test-only collaborator wiring, and the final same-invocation reconstruction retire while receipt-last publication, immutable snapshots, source attestation, roster closure, recovery, historical reads, and independent direct validation remain. Product Python is net `-25` lines and protections/tests are net `-45`; no public output, schema, evidence, logging, or retained file changes. |

### 13.18 Bounded slice record: Step 09 Python-owner migration

| Surface/category | Selected implementation and boundary |
|---|---|
| Owner and callers | One private [`producer.py`](../../src/emrys/analyses/paired_cmh_candidate_ranking/producer.py) replaces the seven-file shell/AWK transaction bundle in local materialization, the retained Step `09` Slurm delegate, and provenance/source rosters. The R scientific implementation, grouped validator, neutral contract, and independent numerical oracle retain their existing authorities. No compatibility wrapper or public command is added. |
| Transaction guarantees | Exact flags/defaults and R argument ordering, four hash-bound inputs, paired-stratum and threshold admission, the six-or-none rule, owner lock, process-group signals, temporary and final semantic validation, summary-last publication, create-exclusive no-clobber inode proof, predecessor rollback, and ambiguous-recovery residue remain. Focused Python cases replace shell-only mechanics; distinct scientific, real-R, validator, oracle, wrapper, materialization, artifact, and report evidence remains. |
| Compression and scope | The formatted owner is 710 lines and 25,372 bytes versus 1,484 lines and 64,318 bytes across the retired bundle: owner implementation net `-774` lines and `-38,946` bytes. The focused suite is 712 lines versus the retired 1,675-line shell suite: net `-963` test lines after adding direct scientific-role, runtime-executable, and controlled-R admission cases needed to preserve the repository-wide coverage floor. The expanded Step `09` critical-owner measurement is rebased narrowly while its existing validator coverage and the global line/branch floors remain non-regressed. The rough 900-line product estimate was not forced through packed formatting, weakened protections, or a premature shared transaction abstraction. Exact whole-slice accounting lives in the findings matrix. |
| Logging and remaining work | Step `09` remains a private task under the existing single Run application log; no task-local lifecycle or log is introduced. All sixteen owner-local `.slurm` files remain, with Steps `07`–`09` delegating to Python. Whole-Run Slurm parity and wrapper retirement remain separate, and `AC-SLICE-17` remains **Open** after this atomic cut. No retained evidence is deleted. |

### 13.19 Bounded slice record: whole-Run Slurm parity and owner-wrapper retirement

| Surface/category | Selected implementation and boundary |
|---|---|
| Parity gate | Exact revision `aad239d7` passed ordinary CI and the selected 130-pair real-synthetic step through direct and disposable single-node Slurm placement. The driver compares identical canonical Analysis, Execution Plan, and Run authority; distinct Attempts with matching common fields and task rosters; matching path-neutral scientific results and symbolic resources; and allocation-sensitive effective resources. It separately admits each successful receipt, complete reporting roster, and ordered single application log, plus one Slurm submission and stream pair with exact scheduler provenance. The later 100,000-pair step was explicitly deemed unnecessary for every architectural cut and canceled after the 130-pair evidence uploaded. |
| Retirement and surviving authority | A caller audit found no production or workflow runtime consumer for the sixteen owner-local `.slurm` files. Those 1,725 product lines, their 2,478-line dedicated harness, two entirely wrapper-only stage suites, wrapper-only STAR-index fixture guidance, and obsolete Make/CI wiring retire without aliases. Four mixed direct-owner suites lose only wrapper syntax/path assertions. Grouped `run`/`resume`, one admitted execution profile, and the small private whole-Run batch bootstrap remain the sole scheduled path. Legacy Step `00a` Novogene decompression is intentionally not ported; materialized FASTA/GTF are Project/input prerequisites. |
| Protections, evidence, and logging | Direct scientific owners, validators, independent numerical oracles, immutable Run/Attempt admission, allocation provenance, scheduler submission/stream tests, locks, no-clobber publication, signals, rollback/recovery, receipts, reports, and real-synthetic parity remain. Successful direct and Slurm Runs each own exactly one compute-side application log; submission itself owns none. Retained receipts, reports, logs, goldens, dated records, and other evidence change by zero. |
| Compression actuals | Maintained product implementation: 19 paths, `+5/-1730`, net `-1725`; protections/tests/tooling: 14 paths, `+26/-3390`, net `-3364`; configuration/workflow: four paths, `+6/-31`, net `-25`; documentation: 60 paths, `+406/-887`, net `-481`; whole slice: 97 paths, `+443/-6038`, net `-5595`. No product file, public command, flag, schema, package export, backend, noun, compatibility path, mutable Run state, or retained evidence is added. |
| Remaining work and evidence ceiling | This is hosted disposable single-node scheduler and successful synthetic engineering evidence. Institutional-site/module portability, multi-node and production-data execution, direct/Slurm failure and recovery parity, scientific review, and biological validation remain Open. `AC-SLICE-05` and `AC-SLICE-17` remain umbrella cards; generalized-backend evaluation remains near campaign closure and implementation is conditional. |

### 13.20 Bounded slice record: project-v1 and named Analysis cutover

| Surface/category | Selected implementation and boundary |
|---|---|
| Scientist-owned definition | One closed `emrys.project.v1` document owns shared Dataset and Reference inputs plus a nonempty map of human-named Analyses. Samples remain one external TSV; each Analysis references its partition TSV and owns comparison, target-change, and threshold fields. Raw TSV bytes and ordering remain source provenance, while canonical normalized rows enter Analysis identity. The Project file's parent is the Project root. Names select Analyses but do not replace content-derived immutable Analysis identity. |
| Admission and selection | `init project`, `init synthetic`, `validate project`, Doctor, direct Run, and whole-Run Slurm use project-v1. Validation admits every named Analysis. `run` and Doctor select one with `--analysis`; omission is valid only for a singleton Project. The selected immutable Analysis revision flows directly into the existing immutable Execution Plan and Run binding. |
| Compatibility and evidence | New validation, diagnosis, and Run creation reject `emrys.request.v3`. Its closed schema and exact reconstruction remain only for historical resume. New and old Attempts retain the unchanged `emrys.workflow-attempt.v1` evidence shape and request-era field names, so no Attempt-v2, evidence rewrite, or evidence deletion is introduced. Stable/no-follow reads, manifest and reference admission, scientific-policy validation, temporal re-admission, and exact historical binding remain. |
| Results and reporting | The existing read-only Results authority, `results` layout, receipts, and report transactions are unchanged. Full Runs still report by default, `--no-report` still disables downstream reporting, and `emrys report` still regenerates independently without changing Analysis, Run, or Attempt identity. No Artifact Store, Run Bundle, second report authority, or filesystem migration is introduced. |
| Compression and closeout | Active request-v3 normalization/projection, mutable normalization views, duplicate stable-file/YAML/profile admission, constructor-only invariant rechecks, user-facing request-v3 setup fields (`label`, authored reference/cohort/analysis IDs), and current-path request-v3 fixtures/instructions retire. The closed request schema, exact historical reader/resume adapter, Attempt-local `request.yaml` evidence name/fields, and exact compatibility fixtures remain. Final category-separated actuals: maintained product Python 10 paths, `+654/-714`, net `-60`; protections/tests 15 paths, `+584/-346`, net `+238`; configuration/schema one new closed schema, `+114/-0`; documentation 14 paths, `+451/-267`, net `+184`; whole slice 40 paths, `+1803/-1327`, net `+476`, with one net new file. This is a meaningful maintained-product reduction while introducing the final active model; no evidence is deleted. `AC-SLICE-03` and `CONFIG-01` are Complete. |
| Remaining scope and evidence ceiling | Broader package APIs and generalized storage/Run-Bundle work remain with `CONTROL-01`; named execution profiles, site/runtime portability, institutional Slurm evidence, and near-closure generalized-backend evaluation retain their existing cards. Focused local verification passes 512 tests with three environment skips across the public-model, onboarding, Doctor, materialization, projection, historical-resume, installed-wheel, and source/dependency boundaries; an independent final review found no actionable P1/P2 issue. Aggregate, fresh-clone/golden-path, direct/Slurm, and full-CI evidence remain required on the exact pushed revision; no institutional-site, production, scientific-review, or biological proof is claimed. |

### 13.21 Bounded slice record: processing-only Run boundary

| Surface/category | Selected implementation and boundary |
|---|---|
| Public boundary and default | `emrys run --through processing` creates a distinct immutable Run selecting the exact evidence-complete, all-sample Steps `00`–`06` closure. The fixed four-sample fixture expands that closure to 31 owner tasks. Omitting `--through processing` preserves the unchanged full Steps `00`–`10` Analysis and default reporting behavior. |
| Identity and backend binding | The scientific stopping-owner roster is a nonempty, predecessor-closed subset of the functional required owners and is part of immutable Execution-Plan identity, so the processing and full plans bind distinct Runs. The fixed Snakefile remains the single backend; its exact bytes now enter the Run-bound backend-semantics digest. No mutable Run state or second execution path is introduced. |
| Terminal state, reporting, and resume | After all 31 selected tasks verify, the lifecycle publishes the ordinary terminal successful Attempt receipt and releases the Run lock. Results are `complete` relative to that immutable plan. Reporting is `not applicable`; automatic reporting is skipped, and manual `emrys report --run-root ...` rejects the Run read-only. A successful processing Run is terminal and cannot be resumed into a fuller stopping boundary. |
| Deferred reuse and non-goals | This slice establishes only the processing/future-reuse boundary. A future cohort, subset, sensitivity, or downstream Analysis would require a separately identified Run, but compatible cross-Run admission and downstream launch remain unimplemented; `ANALYSIS-01` stays **In progress**. No Artifact Store, copy/snapshot handoff, module API, second manifest/receipt authority, or claim that the processing outputs are currently cross-Run reusable is introduced. |
| Compression, verification, and evidence | The backend target now follows the immutable plan roster, task dispatch invocation has one sequence-safe owner, the obsolete one-sample target and test-only target substitution retire, and duplicate scope projection, unused Snakefile state, redundant schema revalidation, and a 110-line synthetic inspection scaffold are removed. A caller-complete history audit also retires 205 lines of private shell manifest/header helpers whose last production callers disappeared in the completed Step `07` and Step `09` Python conversions, plus the orphaned two-line shell orientation-policy file whose sole remaining references were identity bookkeeping; only their 40-line self-test/roster block is removed, while the current Python manifest/header/orientation authorities and every live hashing, residue, publication, rollback, and lock protection remain. Category-separated actuals: maintained product implementation eight paths, `+147/-236`, net `-89` (six Python paths `+147/-29`, two shell paths `+0/-207`); protections/tests six paths, `+524/-127`, net `+397`; configuration/workflow one path, `+190/-347`, net `-157`; documentation seven paths, `+124/-45`, net `+79`; whole slice 22 paths, `+985/-755`, net `+230`, with one fewer product file. Focused local gates pass, including exact 31/35-task DAGs, direct/Slurm plan parity, partial reporting/no-write behavior, byte-preserving between-task failure/resume through the unchanged production target, stopping-roster resume preservation, backend-identity drift rejection, exact static rule/owner/scope projection, and one real 31-task public no-science Run. Independent review's fixed-graph finding is repaired by the compact exact projection and schema-valid owner-reassignment regression. Standard CI and the selected 130-pair real-synthetic lane remain required on the exact pushed revision. Existing owner-native artifacts, validation reports, task starts/attempts/verified records, workflow Attempt receipts, released-lock evidence, logs, Results authority, and report ledgers retain their owners and semantics. No evidence is deleted or weakened; no cluster/site, production-data, scientific-review, or biological proof is claimed. |

### 13.22 Bounded slice record: stationary cross-Run processing reuse

| Surface/category | Selected implementation and boundary |
|---|---|
| Public journey and identity | `emrys run --from-processing-run RUN_ID --analysis NAME` selects one explicit successful processing Run from the same Project. The new downstream Run remains a complete immutable Analysis plan and binds the source Run ID, its successful workflow-Attempt ID, and the canonical successful receipt digest. `--from-processing-run` and `--through processing` are mutually exclusive. Resume admits the relationship from the immutable target plan; Slurm transports the same selector before its single submission. |
| Compatibility and ownership | The first reuse vertical requires the exact normalized sample and Reference identities and the same complete Execution Plan identity except its stopping/source fields; Analysis partitions and scientific policy may differ. The source must be the exact terminal Steps `00`–`06` boundary with valid, complete, successful evidence. Its artifacts remain stationary and read-only. The target executes and owns only Steps `07`–`10`, with its own task/Attempt evidence, outputs, Results, default report transaction, and application log. Source verified-task records are never copied, relabeled, or adopted by the target. |
| Fail-closed temporal admission | Every reused downstream input is materialized with the source task's exact size and SHA-256 and is rechecked before producer entry and through the existing stable-input boundary. Missing bindings fail planning. The source receipt, authority, task closure, artifacts, and compatibility are re-admitted before execution, after workflow execution, and during target inspection. Reporting carries that admitted snapshot into artifact-index preparation, compares the already-hashed inputs before its start, and performs one fresh source admission immediately before artifact-index verification; downstream report transactions consume that verified predecessor without repeating full source-data passes. A missing, replaced, mutated, incomplete, incompatible, self-referential, or differently bound source blocks the target without changing the source. |
| Results, storage, and operator model | Reporting retains one target Results authority while its artifact inventory points to stationary source-Run artifacts for Steps `00`–`06`, admits content-identical relocated external Reference inputs, and uses target paths for Steps `07`–`10`. Inspection labels the admitted processing milestones as reused and shows the source Run once; an inadmissible source renders them blocked. No copy, symlink, reuse manifest, Artifact Store, generic module API, second scheduler, mutable Run field, or separate source log is introduced. This resolves the first physical realization as same-Project stationary reuse without settling later portability or archival mechanisms. |
| Compression and remaining scope | The redundant `artifact_source_root` workflow-config field and duplicate Snakefile validation of reporting-owned projections retire; reporting keeps its single semantic admission owner. The existing 31-task public processing journey becomes the source half of one processing-to-downstream failure/resume/reporting journey rather than adding a second expensive harness. Exact category accounting and CI status are recorded in the backlog dated-evidence entry. `ANALYSIS-01` remains **In progress** for authored cohort/sample subsets and the broader modular downstream-analysis launch model; `ANALYSIS-02` retains the collaborator library/interface decision. |

### 13.23 Bounded slice record: named Analysis sample subsets

| Surface/category | Selected implementation and boundary |
|---|---|
| Authored model and identity | A named project-v1 Analysis may declare a nonempty unique `sample_ids` list. Omission or an explicit complete-Dataset selection has the existing all-sample meaning. Selection order is neutral; admitted Dataset order drives the private workflow projection. The selected canonical sample rows continue to own Analysis/cohort identity and existing paired-design validation. |
| Reuse and backend realization | A target may reuse one successful processing Run when every selected sample row is identical to a source row; extra source samples are allowed, while Reference and the existing conservative Execution-Plan compatibility remain exact. Steps `07`–`09` receive one deterministic Attempt-bound selected TSV through the existing planned-file and immutable-input binding machinery. It is a backend adapter, not another scientist-authored manifest, Run authority, or evidence store. |
| Surviving protections | Source receipt, authority, task closure, artifact hashes, temporal re-admission, failure/resume, reporting, locks, and source immutability remain unchanged. The target consumes only selected Step `06` artifacts and owns its downstream evidence, Results, report, and application log. `LOG-05` is inherited through the existing Run owner; no new logging path is added. |
| Closure and non-goals | This completes `ANALYSIS-01`: processing-boundary Runs, stationary exact-subset reuse, named subset/sensitivity identity, and the public failure/resume/report journey are one vertical. No Artifact Store, copy/snapshot handoff, selector language, new CLI flag, module registry, second scheduler, or mutable Run field is added. Generalized collaborator-extensible downstream modules remain solely `ANALYSIS-02`. |
| Compression and evidence accounting | Caller-complete review found no superseded product owner to retire without unrelated scope or weaker admission. Maintained product Python is five existing paths, `+108/-30`, net `+78`; protections/tests are seven existing paths, `+274/-18`, net `+256`; configuration/schema is one existing path, `+8/-0`; documentation is six existing paths, `+46/-16`, net `+30`; whole slice is 19 existing paths, `+436/-64`, net `+372`, with no file growth. The quantified product-growth exception was explicitly approved before commit. One optional authored field is added; commands, flags, package exports, public nouns, backends, compatibility paths, shell, and retained evidence change by zero. One private post-admission mapping mutation retires and no mutable authority is added. No evidence is moved, rewritten, or deleted. |

### 13.24 Bounded slice record: immutable Attempt handoff compression

| Surface/category | Selected implementation and boundary |
|---|---|
| Surviving handoff | `AttemptPlan` projects one bytes-backed `LifecycleRequest` before lifecycle mutation. Lifecycle parses and schema-validates the canonical Attempt bytes once, then publishes and hashes those exact bytes. `publish_attempt` only materializes the already-planned files and returns nothing. |
| Retirement | The scalar-mirroring `AttemptPreparation`, production-unused direct `run_attempt` route and alternate lock-acquisition branch, materializer-return substitution checks, and duplicate `_OwnedRunLock.record` mirror retire without aliases. All in-repo tests use the sole production `run_materialized_attempt` entry. |
| Preserved boundaries | Immutable Run/Attempt identity, operation preflight, temporal Run admission, mutex and run-lock ownership, exact-byte no-clobber publication, source/runtime/resource/argv admission, signals, failure cleanup, recovery, receipt-last ordering, subordinate evidence, Results/reporting, and `LOG-05` ownership remain. No public command, schema, evidence record, backend, scientific behavior, or retained evidence changes. |
| Compression and evidence | Maintained product Python across three files is `+54/-148`, net `-94`; protections/tests are `+141/-152`, net `-11`; documentation across four files is `+22/-11`, net `+11`; whole slice is nine existing files, `+217/-311`, net `-94`, with no file growth. Focused lifecycle evidence preserves all 42 lifecycle test functions and every distinct fault/boundary case. Exact-head standard CI passed; selected 130-pair direct/Slurm evidence remains separately recorded. `AC-SLICE-17` remains Open for other separately proven reductions. |

### 13.25 Bounded slice record: Step 06 Python-owner migration

| Surface/category | Selected implementation and boundary |
|---|---|
| Owner and science | One private Python producer replaces the repository-path Step `06` shell owner. It retains the exact four flag selections, FWD/REV merges, indexing, record counts, six-decimal fraction, quickchecks, and independent validator boundary. The R and downstream scientific paths do not change. |
| Transaction and evidence | Input BAM/BAI identity, foreign-residue refusal, one owned lock, process signals, create-exclusive publication, counts-last ordering, rollback of only provably owned outputs, ambiguous-state preservation, final revalidation, task evidence, immutable Run authority, and the existing single Run log remain. No task-local log, schema, receipt, backend, or evidence authority is added. |
| Retirement | The production-dead direct dry-run, replace/backup route, implicit executable and token fallbacks, public shell path, and shell-only suite retire without a compatibility wrapper. Materialization is the sole production caller and now invokes the private module through the existing controlled Python boundary. No retained evidence is moved, rewritten, or deleted; unfinished historical Runs remain bound to their recorded checkout. |
| Compression and verification | The exact category accounting and hosted evidence are recorded in the findings matrix. One product file replaces one product file, while the 740-line shell owner and 1,216-line shell suite retire. `AC-SLICE-17` remains Open for other separately approved reductions. |

## 14. Measurement plan

Measurement is required so the campaign does not merely move complexity.
The per-slice register and closeout in Section 13.1 apply immediately;
`AC-SLICE-14` does not defer or own that accounting. Its separate purpose is to
establish reproducible campaign-wide baselines and interpretation methods
before aggregate targets are ratified.

### 14.1 New-user measures

- Time from supported fresh installation to valid synthetic result
- Number of commands required
- Number of user-authored configuration files and fields
- Number of concepts that must be understood before the first run
- Number of documentation pages required to complete the golden path
- Time and steps required to find the primary report

### 14.2 Operational measures

- Time to diagnose an invalid environment
- Percentage of readiness and runtime failures with actionable diagnostics
- Time and number of manual steps required to recover a failed run
- Number of decisions an operator can inspect and override without source edits
- Parity of correctness and evidence guarantees across local and SLURM modes

### 14.3 Architectural measures

- Number of artifact-lifecycle implementations
- Number of execution implementations and direct scheduler callers
- Number of duplicated validators or policy decisions
- Number of modules directly implementing publication or storage semantics
- Number of modules that understand mutable execution or attempt state
- Number of compatibility/migration paths after their supported window
- Maintained product files and lines, public concepts, call edges, and
  compatibility paths
- Protection files and lines, mapped invariants, and surviving defense routes
- Configuration, script, schema, and documentation files and lines
- Retained evidence artifacts, classes, claims, and retention owners

These categories are measured and interpreted independently. Counts do not
prove simplicity or safety, and one category cannot offset growth in another.
The baseline must explain inclusions, exclusions, generated/runtime material,
and how a reviewed source-coverage baseline is rebased after source retirement
without hiding its absolute numerator, denominator, or surviving routes.

The source suggested **under 30 minutes** for a supported local synthetic run
and **under one hour** in a prepared HPC environment. These are useful candidate
targets, not accepted commitments. Hardware, installation boundary, cache
state, dataset size, scheduler wait, and “prepared environment” must be defined
before any time target becomes normative.

## 15. Open decision register

`AC-SLICE-02` resolved the responsibility direction around several rows below.
Those rows now retain only their stated concrete vocabulary, API, lifecycle,
storage, or migration choices; they do not reopen the ratified constraints in
Sections 7, 8, and 11.3.

`ARCH-MODEL-DECISION-01` resolves `AC-DEC-001` and the model/change-boundary
portion of `AC-DEC-011`; `ARCH-MODEL-FIELDS-01` resolves the remaining
semantic field-and-authority portion:

| Decision ID | Resolved decision |
|---|---|
| `AC-DEC-001` | The compact public conceptual model is `Project -> Analysis -> Run -> Results`; Run is public and owns the primary ordinary identity, while Attempt is progressively disclosed. Execution Plan is internal and inspectable; Dataset, Reference, and ExperimentalDesign are scientific-definition sections; Runtime/profile is operator-facing; Artifact is advanced, Task internal, and Report a downstream Results capability. |
| `AC-DEC-004` | The scientist-authored source is one closed `emrys.project.v1` `project.yaml`: shared Dataset and Reference sections plus a nonempty map of named Analyses. Samples and per-Analysis partitions remain external TSVs. `validate project` admits all Analyses; `run` and Doctor select one by `--analysis`, with omission only for a singleton. Analysis names are selectors, while immutable scientific identity remains content-derived. |
| `AC-DEC-011` (partial) | Model C is selected. A Run immutably binds one admitted immutable Analysis revision to one immutable effective Execution Plan. Scientific-intent or declared-plan changes create a new Run; re-execution creates an Attempt; attempt-local realization may vary only inside the Run's declared envelope; reporting changes create neither. |
| `AC-DEC-011` (semantic fields and authorities) | Section 8.1.3 fixes the Analysis, Execution-Plan, and Run identity fields and digest composition; relocation/content/order rules; symbolic resource envelope; Attempt variation; logical canonical authorities and direct retirement direction; Run-admission recovery owner; and five separate status domains. |
| `AC-DEC-008` | The minimum useful common operation representation is the existing private `TaskDispatch` plus profile/graph references. Reporting remains a separate downstream boundary. No new Stage/Operation API, schema, registry, lifecycle vocabulary, or public noun is justified. |
| `AC-DEC-009` | Shared policy is conditional rather than a required layer. Centralize only when at least two production owners make the same decision from equivalent inputs with identical complete semantics and one bounded caller-complete migration retires the duplicates net-negatively. Distinct trust-boundary re-admission is not duplication; the inventory may select no shared abstraction. |
| `AC-DEC-003` | Top-level `emrys doctor` diagnoses without writing or logging. Repair is separately operator-authorized: `--repair` previews one plan and confirms on a terminal, while noninteractive mutation requires `--repair --execute`. Doctor may publish one receipt-last Project-owned direct-storage qualification and may mutate only the active checkout-owned `.venv` and Project `runtime/managed`; it delegates dependency solving/installation to `uv`, Pixi, and `renv`, owns one maintenance log, preserves site/user profiles and declared inputs, and requalifies. Storage-only repair preserves an already-ready site runtime and invokes no package manager. Direct Runs admit that local receipt or stronger v1 evidence; Slurm and placement-less historical Runs remain v1-only. Linux x86-64 is the current managed-runtime target; advanced evidence routes remain separate. |
| `AC-DEC-007` | A supported managed environment is accepted through Pixi for the initial Linux x86-64 path; containerization remains an independent option. The packaged manifest/lock declares glibc 2.28 and Linux 4.18 virtual-package values. Ordinary CI installs that unchanged lock in Rocky 8.10, Ubuntu 22.04, and Debian 12 userspaces, and the real-tool managed direct Ubuntu golden-path job is implemented with exact-head execution pending. Actual Linux 4.18, broader portability, cluster/site, scheduler, security, licensing, updates, native escape hatches, and full tool-provenance policy remain with `RUNTIME-01`/`CONTAINER-01`. |
| `AC-DEC-015` | The public demo surface is retired. The neutral supported synthetic path begins with `emrys init synthetic`; the internal fixture schema remains compatibility metadata rather than a public command or product concept. |
| `AC-DEC-024` | The current supported synthetic capability order is `emrys init synthetic -> emrys doctor --repair -> emrys run -> emrys inspect run`. The initializer creates its Project, Doctor establishes readiness, Run executes the immutable plan with reporting automatic by default, and inspection admits the retained outcome. Real-data, site-runtime, and Slurm journeys remain role-specific extensions rather than alternate ordinary orders. |
| `AC-DEC-017` | The stable advanced surface is the existing role-tiered grouped Run control and read-only Run inspection route. Normal output keeps the primary Run ID and scientific outcome; verbose adds admitted Analysis, Execution Plan, and Attempt identity plus effective placement/resources; debug adds canonical authority paths/digests, effective-plan facts, verified artifacts, task/receipt evidence, and exact safe commands. Historical Runs are labeled without successor identities. Durable records remain the machine-readable evidence surface; no separate explain, manifest, evidence, or diagnostics command is required. |

| Decision ID | Open question | Retained options or concerns |
|---|---|---|
| `AC-DEC-002` | Which names form the stable public CLI? | setup/init, validate/check/doctor, status/resume, config, inspect/explain/debug |
| `AC-DEC-005` | What broader merge semantics remain beyond the implemented execution-profile boundary? | Current execution precedence is packaged defaults, one explicitly selected closed fragment, then owner-defined CLI resource overrides, with source/effective provenance retained. Site/project/scientist configuration precedence and broader list/map/null semantics remain Open. |
| `AC-DEC-006` | How are runtime and future named execution choices represented? | One explicit file-bound direct/Slurm execution profile is implemented and runtime remains separate. Institution-provided discovery publishes one Project-owned admitted runtime authority that ordinary commands derive, and Doctor implements the first bounded Managed installation/repair. Named execution profiles are likely necessary; Explicit definition, registry/management, final taxonomy, broader portability, and persistence remain Open. External mechanisms stay behind owned boundaries and supported realizations owe equivalent declared guarantees. |
| `AC-DEC-010` | What artifact-lifecycle vocabulary and owner shape are justified? | Candidate, validation, admission, publication, commit, immutability, evidence, and rollback; generalized versus class-specific ownership; APIs, schemas, manifests, receipts, immutability mechanisms, external/large artifacts, Run Bundle/report-derived relationships, cleanup, recovery, and representative migration. Lifecycle/admission is already distinct from physical storage. |
| `AC-DEC-011` | How are the selected Analysis/Execution-Plan/Run/Attempt semantics realized beyond the current public CLI vertical? | Immutable canonical Analysis/Execution-Plan/Run records, Run-last persistence, project-v1/named-Analysis admission, current-path migration, direct workflow/task Run admission, Attempt-owned reporting inputs, exact historical request-v3 resume, and temporary-projection retirement are implemented. Broader package API placement, generalized storage relationships, compatibility duration, and the remaining implementation-retirement roster remain Open. Attempt-v1 stays the evidence shape for new and old Attempts. A generalized backend is evaluated near closure only for concrete extension or compression evidence; shared-policy migrations follow resolved `AC-DEC-009`. Mutable object state and canonical bytes cannot compete; coordination cannot absorb lower authorities or become a god object. |
| `AC-DEC-012` | What public Run, Attempt, scientific, and reporting states are useful and truthful? | Resolved for the supported read-only surface: Run integrity is `valid`/`blocked`; Attempt outcome is `not_started`/`running`/`succeeded`/`failed`/`interrupted`/`blocked`; scientific Results are `incomplete`/`complete`/`blocked`, while reporting is independently `not applicable`/`incomplete`/`complete`/`blocked`; recovery is a separate availability fact. Five scientific milestones use `not applicable`/`incomplete`/`complete`/`blocked`; source-backed processing milestones may also render `reused` only after the bound source is re-admitted. Reporting is not a milestone. A successful processing-only Run is Results-complete relative to its immutable Steps `00`–`06` plan, reporting-not-applicable, and not recoverable/resumable into a fuller boundary. Current/latest Attempt elapsed time uses only that Attempt's retained boundaries, with no resume summation or ETA. Normal/verbose/debug disclosure is presentation, not authority. The superseded aggregate Python accessors are retired; receipt-v1 remains historical schema evidence. |
| `AC-DEC-013` | What is the Run Bundle contract? | A Run Bundle is likely useful, but view/export/snapshot shape, mutability, ownership, persistence, layout, portability, large artifacts, external references, redaction, archival, regeneration, and sharing remain Open. |
| `AC-DEC-014` | How are the ratified downstream-reporting semantics represented? | Resolved for the current fixed profile: scientific Attempt/Results state, reporting state, recovery, and verified locations are independent; receipt v2 ends at science while receipt v1 remains exact historical evidence. Full `run`/`resume` report by default, `--no-report` opts out, and dry-run-first `emrys report --run-root ... [--execute]` regenerates without a Run or Attempt. For a processing-only Run, reporting is `not applicable`: automatic reporting is skipped and the manual report route rejects read-only. A downstream Run created from an admitted processing source owns its ordinary default report transaction and one target Results authority with a hybrid stationary artifact inventory. Its retained source admission is compared to artifact-index's prepared hashes before start and refreshed once before artifact-index verification; run-summary and HTML consume the verified reporting predecessor without repeating whole-source admissions. Complete applicable transactions are revalidated/reused; partial or ambiguous state is never adopted, repaired, deleted, or retried. The existing scientific and Evidence-and-operations HTML views and `results/reports/<run-id>` remain canonical for applicable full Runs. Broader Run-Bundle, format, portability, archival, and future-profile choices remain with their own cards. |
| `AC-DEC-016` | Which filesystem concepts are public? | Project/inputs/runs/results/runtime; exact internal-to-public mapping |
| `AC-DEC-018` | How is each bounded compatibility and retirement transition implemented? | Compatibility window, warnings, fixtures, and removal evidence; caller migration, relevant parity, owned temporary compatibility, and eventual retirement are already binding. Evidence deletion remains separately approval-gated. |
| `AC-DEC-019` | Which campaign metrics and targets become commitments? | Reproducible UX and operational baselines; separate product, protection, configuration/documentation, and retained-evidence methods; supported environment; time targets; coverage-rebase interpretation; qualitative acceptance. Per-slice accounting is already binding. |
| `AC-DEC-020` | How should work beyond the accepted `LOG-05` migration boundary, compression opportunities, and any just-in-time facade use be ordered? | The `AC-SLICE-03` field-and-authority prerequisite and first caller-complete successor Run-authority cutover are complete. Broader campaign ordering remains Open: three source phase models and the P0–P3 suggestion, per-slice facade need, compression/retirement opportunities, and later importance/complexity scores remain for just-in-time reconsideration. Section 13.3 settles only logging adoption sequencing. |
| `AC-DEC-021` | Which new architecture documents should remain after the campaign? | Invariants, current architecture, target architecture, or consolidation into existing durable owners |
| `AC-DEC-022` | How should the Steps 07–09 audit be bounded? | Review authority, candidate universe, count/CMH/BH contracts, oracle data, evidence ceiling |
| `AC-DEC-023` | Which historical claims from the source are accurate and useful? | Development dates, chronology, and repository-history interpretations require live Git verification before reuse |
| `AC-DEC-025` | Deferred trigger: does a distinct Artifact Store become necessary? | No Store is selected or required now. Reconsider only after a separately approved concrete unmet need that current class-specific authorities cannot handle cleanly; any Store must replace rather than duplicate admission authority. Nonbinding example needs remain in the suggestion register. |

No open decision is resolved merely because one source supplied a concrete
example. In this document, “post-audit” always means after the audit is reviewed
and a separate user-approved decision is recorded; the audit itself selects
nothing beyond already binding constraints.

### 15.1 Concrete nonbinding suggestion register

The exact suggestions below are retained for reconsideration. Their presence
does not select a name, API, schema, or implementation.

| Suggestion ID | Concrete source suggestions retained |
|---|---|
| `AC-SUG-001` | Primary commands: `emrys setup` or `init`; `validate`, `check`, or `doctor`; `run`; `status`; `resume`; `report`; `inspect`; `config`; and the disputed `demo` name |
| `AC-SUG-002` | Expert inspection forms: `emrys run --explain`, `emrys run explain`, `emrys run manifest`, `emrys run evidence`, `emrys inspect run <id>`, `emrys inspect artifact <id>`, `emrys diagnostics`, `emrys debug scheduler ...`, and the broader `emrys debug ...` namespace |
| `AC-SUG-003` | Execution forms: `emrys run --yes`, `emrys run --profile cluster`, `emrys run --executor slurm`, and `emrys run --container` |
| `AC-SUG-004` | Runtime and diagnosis forms: `emrys runtime install`, `discover`, `accept`, and `define`; `emrys doctor --fix`; `emrys doctor --storage`; and `emrys debug storage-qualification` |
| `AC-SUG-005` | Reporting forms: `emrys report`, `emrys report --evidence`, and `emrys report --operations`; scientific/evidence/operations views or separate artifacts remain alternatives, including the proposed filenames `scientific.html` and `evidence.html` |
| `AC-SUG-006` | Internal API names: `Stage.run()`, `ExecutionEngine`, `LocalExecution`, `SlurmExecution`, `execution.run(task)`, and Input/Validation/Runtime/Storage/Publication/Resource/Execution policy owners |
| `AC-SUG-007` | Proposed durable documents: `ARCHITECTURE_CURRENT.md` and `ARCHITECTURAL_INVARIANTS.md`; their content may instead be consolidated into existing owners |
| `AC-SUG-008` | Sensitivity-analysis authoring: `analysis.include_replicates: ["2", "3"]` inside a profile versus a separate first-class sensitivity-analysis definition |
| `AC-SUG-009` | Scientific configuration/layout names: `project.yaml`, `analysis.yaml`, a separate `samples.tsv`, embedded samples, and the illustrative project/run/Run-Bundle trees |
| `AC-SUG-010` | A scientist documentation layer of approximately five pages total, separate from operator and developer detail; this is a candidate size target, not a limit |
| `AC-SUG-011` | Exact illustrative `emrys run --explain` plan: validate inputs; qualify the execution environment; prepare the reference; execute scientific stages; validate artifacts; generate evidence; publish the immutable run; generate reports |
| `AC-SUG-012` | Journey-first documentation order: What is EMRYS; Install; synthetic/demo path; configure a project; run an analysis; understand results; run on HPC; recover a failed run; understand provenance; developer architecture—with architecture after successful use |
| `AC-SUG-013` | Illustrative completion funnel: 42,381 candidates evaluated; 127 passing statistical/effect thresholds; 18 passing the background criterion; then `scientific.html` and `evidence.html`. Counts and filenames are examples, not targets |
| `AC-SUG-014` | Pursue the Steps 07–09 audit in parallel as the proposed next scientific-review focus rather than further filesystem/provenance refinement; this is a sequencing suggestion, not accepted priority |
| `AC-SUG-015` | The exact `Artifact Store` name and source diagrams that place it between stages and reports are retained only for reconsideration after a separately approved concrete unmet need; example needs include cross-run reuse, duplicated resolvers, external/large artifacts, Run-Bundle portability, caching, and garbage collection, while trigger sufficiency, boundary type, and ownership remain Open |
| `AC-SUG-016` | Physical realizations for reusable scientific artifacts: stationary admitted paths with verified identities as the lowest-footprint candidate; retained full copy for portability or retention; qualified copy-to-scratch only when real-site measurements show benefit; reflink or native snapshots where semantics are qualified; and future content-addressed storage. Copying alone does not authorize reuse or replace identity and compatibility admission. Step 07 directly consumes Step 06 BAM/BAI; Steps 08–09 benefit only through their own admitted upstream outputs. Evaluate the STAR reference/index and canonical BAM as separate high-fanout candidates rather than inferring blanket duplication of raw inputs or every stage. Exact noun, backend, default, and ordering remain open. |
| `AC-SUG-017` | Favored directions: named execution profiles; institution-provided discovery plus future Managed/Explicit acquisition journeys to one runtime authority; and a likely-useful Run Bundle. The discovery route and canonical Project-owned runtime path are now implemented; exact remaining names, APIs, persistence, managers, bundle shape, layout, and ordering remain Open. Generalized-backend evaluation is a binding near-closure checkpoint, while implementation remains conditional. |

## 16. Candidate slicing ledger

These began as candidate work slices, not final backlog IDs, priority, or
implementation authorization. `AC-SLICE-01` is complete as the bounded
`ARCH-CONST-01` decision/audit slice, and `AC-SLICE-02` is complete as
`ARCH-LAYER-01`. The read-only owner/caller, representation, identity,
mutation, protection/evidence, and compression prerequisite is complete as
`ARCH-MODEL-AUDIT-01`. `ARCH-MODEL-DECISION-01` then selects model C, the
compact public vocabulary, and the Run-versus-Attempt change boundary.
`ARCH-MODEL-FIELDS-01` completes the semantic field-and-authority prerequisite.
The successor Run-authority cutover now implements immutable records, Run-last
admission, direct workflow/task Run admission, Attempt-owned reporting inputs,
historical read/resume, and retirement of the temporary execution projection.
The grouped CLI is now the sole supported Run-control surface and its duplicate
direct Python planning surface is retired. Current Project admission freezes
exact Project source plus per-Analysis profile/workflow-input/authored-path
bytes and Analysis authority, surfaces
`project.yaml` and `--project` through validation, Doctor, and Run control, and
connects directly to immutable Analysis/Execution Plan/Run and read-only
Results. The current cut replaces the temporary active request-v3 adapter with
closed project-v1, admits multiple named Analyses, and confines request-v3 to
exact historical resume without changing Attempt-v1 evidence or Results/report
authority. The historical slice record left `AC-SLICE-03` Open pending final
compression accounting and verification; Section 13.20's completed closeout
supersedes that temporary status. Every
later candidate still requires its own bounded owner/caller review,
compression register, mutation inventory, non-goals, acceptance conditions,
protection disposition, and evidence ceiling before entering the matrix. A
promoted implementation card also requires the category-separated closeout
defined in Section 13.1; evidence deletion cannot be implied by promotion.

| Candidate | Observable outcome | Likely relationship to current matrix |
|---|---|---|
| `AC-SLICE-01` | Ratified all 27 architectural invariants and five migration/test guardrails against live contracts and representative tests | Completed as `ARCH-CONST-01`; broad `ARCH-01` remains Open |
| `AC-SLICE-02` | Ratified responsibility clusters, three separate dependency graphs, forbidden authority transfers, a current-owner crosswalk, and a fast Python source-boundary ratchet for exact CLI seams and transitional imports | Completed as `ARCH-LAYER-01`; broad `ARCH-01` remains Open |
| `AC-SLICE-03` | Establish the compact public application model and introduce it only after exact fields, identity, authority, recovery, compatibility, and retirement decisions are complete | **Complete.** Closed project-v1 persists shared Dataset/Reference inputs and named Analyses; validation admits all, while Run and Doctor select one. The selected immutable Analysis flows through existing Execution Plan, Run, Attempt, and read-only Results authorities. New work rejects request-v3; its exact reconstruction is isolated to historical resume. Attempt-v1 and Results/report semantics remain unchanged. Active request-v3 intake and duplicate request-era owners retire with a meaningful maintained-product reduction. Generalized storage, broader package APIs, named execution profiles, and backend evaluation remain separately owned. |
| `AC-SLICE-04` | Decide whether a shared thin operation representation is justified and, if so, define the minimum boundary and prove it through one representative migration only after the mapping test passes | **Complete.** The four-owner map retained private `TaskDispatch`, rejected a new universal Stage/Operation representation, and proved the decision through the caller-complete Step `08` Python-owner migration. `ANALYSIS-02` and broad `ARCH-01` retain their wider outcomes. |
| `AC-SLICE-05` | Complete the declared guarantee and parity contract across direct and Slurm placement of the current backend, then evaluate the generalized-backend boundary near campaign closure | One file-bound profile and grouped `run`/`resume` route select direct or whole-Run Slurm around the same one-host Snakemake backend. Private transport submits once and records Attempt-local placement. Controlled planning/materialization parity and successful hosted disposable-Slurm outcome parity are proven at 130 pairs: immutable authority, Attempt common fields/task roster, path-neutral science, and symbolic resources match; each side separately admits successful receipt/reporting and one application log; effective resources and scheduler provenance remain placement-sensitive. Institutional-site/module, multi-node/production, and failure/recovery parity remain Open with `OPS-02`; another backend remains conditional on the near-closure evaluation. |
| `AC-SLICE-06` | Inventory duplicated policy decisions and centralize only candidates that pass the resolved two-production-owner, equivalent-semantics, caller-complete, net-negative gate | Conditional inventory; may close with no shared layer; supports `ARCH-01` |
| `AC-SLICE-07` | Define demonstrated artifact-class lifecycle/admission gaps and migrate one path only if the selected design requires a boundary change | Conditional class-specific work; a distinct Artifact Store is deferred until a separately approved concrete unmet need |
| `AC-SLICE-08` | Decide whether named execution profiles are accepted and, if so, define them independently of runtime acquisition modes | One v1 file-bound format, built-in direct default, explicit selector, current precedence, and source/effective provenance are implemented. Institution-provided runtime discovery publishes one Project-owned authority independently of execution configuration, and bounded Managed install/repair is implemented through Doctor. Named execution profiles, Explicit definition, higher-level management, and broader persistence remain Open with `OPS-01` and `RUNTIME-01`. |
| `AC-SLICE-09` | **Complete.** The existing grouped Run-control and read-only Run-inspection routes provide role-tiered identity, effective-plan, artifact, and evidence inspection without a new command, schema, status store, or authority. | Completed with `IDENTITY-01`; broader Project/Results APIs remain with `CONTROL-01` and command simplification remains with `OPS-02`. |
| `AC-SLICE-10` | Define high-level status and safe resume/recovery UX over existing fail-closed internals | **Complete.** Separated status, recovery gating, deterministic next-action guidance, five persisted-authority scientific milestones, current/latest Attempt elapsed time, and normal/verbose/debug progressive disclosure are implemented on the existing read-only inspect route. Reporting remains separate; no ETA, status store, dashboard dependency, or inspection-side write is introduced. `OBS-01` is complete; `LOG-05` remains open for broader retained-operation adoption and parity. |
| `AC-SLICE-11` | Decide whether a canonical Run Bundle is accepted and, if so, define its contract | A Run Bundle is likely useful; shape, ownership, persistence, and exact contract remain Open and coordinate with `FILESYSTEM-01` and completed `RESULTS-01` |
| `AC-SLICE-12` | Formalize scientific, evidence, and operational report purposes and navigation | **Complete.** The two receipt-bound HTML reports retain their output identities and now carry fixed sibling-relative navigation for the three accepted questions. The scientific report remains primary. The combined **Evidence and operations** report retains Run overview, folds both provenance sections into Evidence, and places Attempt lineage under Operations. No third report, schema, receipt, command, or filesystem surface was added. `RESULTS-01` subsequently co-located both reports with the admitted result tables; `REPORT-03` remains Verification pending for rendered acceptance. |
| `AC-SLICE-13` | Deliver a supported fresh-install-to-valid-synthetic-result golden path after ratifying its capability order | **Implementation complete; Verification pending.** The ordinary CI lane contains the supported managed direct journey `init synthetic -> doctor --repair -> run -> inspect run` and exact retained Project/Run/Results/report assertions. Exact-head managed execution and aggregate CI remain pending. |
| `AC-SLICE-14` | Establish reproducible UX, operational, and separate product/protection/configuration-documentation/retained-evidence baselines and ratify their interpretation methods and campaign success measures | New aggregate-measurement slice; per-slice accounting starts immediately and coordinates with `REVIEW-UX-03` and `ARCH-01` |
| `AC-SLICE-15` | Audit the Steps 07–09 statistical contract | New scientific-review slice; not architecture evidence |
| `AC-SLICE-16` | Build independent numerical oracles for Steps 08 and 09 | New scientific-validation slice |
| `AC-SLICE-17` | Retire duplicated lifecycle, validator, infrastructure, adapter, or compatibility paths after each replacement is proven; classify dual-purpose fixtures, goldens, logs, receipts, reports, and dated records before deletion | Sections 13.6, 13.8, 13.10, 13.18, 13.19, 13.24, and 13.25 retire the generated wrapper/configuration split, the Step `06`–`09` shell owners and shell-only suites, all sixteen owner-local `.slurm` paths plus their dedicated harness, and the duplicate Attempt-preparation/direct-lifecycle route after caller-complete replacement and applicable parity. The private batch bootstrap remains. This does not complete the umbrella card; further reductions remain bounded slices, and exact evidence deletion still requires separate user approval and commit. |
| `AC-SLICE-18` | Rewrite navigation and documentation around scientist/operator/developer journeys | Expansion or slicing of `DOC-01`; use the accepted `DOC-02`/`DOC-03` traces and coordinate with `DOC-04`–`DOC-05` retirements |
| `AC-SLICE-19` | **Complete.** Define Doctor repair ownership, supported mutations, preview/reporting, and safety contracts | Top-level diagnosis is no-write/no-log. Explicit confirmed repair delegates the active `.venv`, Project-managed native/R environment, and R library to `uv`, Pixi, and `renv`; Doctor owns bounded authority, one maintenance log, and complete requalification while preserving inputs and site/user profiles |

Slicing must preserve traceability to the campaign section and source IDs. A
slice should represent one observable outcome, identify affected owners and
callers, state non-goals, preserve relevant invariants, and name proportionate
acceptance evidence.

## 17. Routing into existing matrix items

The following routing is incorporated at the planning level in the
[backlog matrix](backlog_matrix.md). The matrix owns the accepted task wording;
this campaign preserves the cross-task rationale and unsettled alternatives.

| Existing ID | Context to carry into the matrix |
|---|---|
| `ARCH-CONST-01` | Completed decision/audit slice: the durable 27-invariant register and five migration/test guardrails now live in the platform-direction decision; broad implementation remains `ARCH-01` and the routed owner tasks |
| `ARCH-LAYER-01` | Completed responsibility-shape slice: the five bands are responsibility clusters rather than package topology; source imports, runtime/control invocation, and artifact/evidence flow are separate graphs; forbidden authority transfers, current owners, exact transitional imports, and a fast import ratchet now have durable owners |
| `ARCH-MODEL-AUDIT-01` | Completed current-model prerequisite: maps separate control paths, semantic lifetimes, owners/callers, identity boundaries, dry-run and write-before-attempt-admission gaps, Local/Slurm relationship, reporting/status mismatch, mutation ownership, protected evidence, reproducible footprint/change accounting, and 14 conditional compression candidates without selecting the application model |
| `ARCH-MODEL-DECISION-01` | Completed direction decision: model C; public `Project -> Analysis -> Run -> Results`; progressively disclosed Attempt; internal inspectable Execution Plan; explicit Run-versus-Attempt change boundary; reporting remains downstream and identity-neutral. |
| `ARCH-MODEL-FIELDS-01` | Completed semantic decision package: exact identity-bearing fields and digest composition; relocation, formatting, labels, order, and content rules; symbolic resource/Attempt envelope; one logical authority per admitted boundary; direct compatibility/retirement direction; Run-admission recovery ownership; and separate Attempt, Results, evidence, and reporting status domains. The first internal successor representation and current-path migration are now implemented; broader product realization remains Open. |
| `CONTROL-01` | The public CLI now realizes Project -> named Analysis -> immutable Execution Plan/Run -> read-only Results with progressive Attempt disclosure. Validation admits all Analyses; Run and Doctor select one. Shared mutable normalization views, the duplicate direct Python planning surface, the temporary execution projection, and active request-v3 intake retire. Broader package APIs and generalized storage relationships remain Open; no new Results or evidence authority is introduced. |
| `CONFIG-01` | **Complete.** One closed scientist-facing `emrys.project.v1` definition owns shared Dataset/Reference inputs and named Analyses, with samples and per-Analysis partitions retained as external TSVs. Internal workflow inputs and scope identities are generated. Execution profile, Attempt-local placement, and Project-owned runtime remain distinct and inspectable. Active request-v3 configuration retires; exact request-v3 is retained only for historical resume. |
| `OPS-01` | The current operator surface is one optional closed execution-profile file plus explicit resource overrides, with implemented current precedence and source/effective provenance. Named profiles are likely necessary; names, discovery/registry, broader site/project precedence, storage/runtime integration, and the final safe override roster remain Open. |
| `OPS-02` | Grouped `run`/`resume` select direct or whole-Run Slurm placement from the admitted profile; `run --analysis` selects one named Analysis and Doctor uses the same selection rule after whole-Project validation. Terminal control confirms one frozen plan; automation uses explicit `--execute`. Whole-Run Slurm submits once and re-enters the same one-host backend. Hosted 130-pair success-path parity and all sixteen owner-wrapper retirements remain as recorded. Institutional-site/module, multi-node/production, failure/recovery parity, the internal local-pilot source name, and broader command simplification remain Open. |
| `OPS-03` | Inline/generated program inventory, extraction of substantive reusable logic, and removal of operator dependence on helper scripts |
| `OPS-04` | Replace “local pilot” with a domain name that remains accurate beyond one execution context |
| `SETUP-01` | **Complete.** `emrys init manifests` admits canonical paired FASTQ paths plus explicit condition/replicate/strandedness, optionally admits declared partitions, and produces deterministic strict drafts through dry-run-first, absent-directory, no-clobber, completion-last publication without inspecting content or inventing biology. Guided Project setup, runtime acquisition, Doctor, and data acquisition remain separate. |
| `SETUP-02` | Portable setup-adjacent benchmarking with advisory, evidence-bound recommendations |
| `SETUP-03` | **Complete.** `emrys init project` validates the explicit scientific inputs before dry-run-first, create-absent publication; creates only Project-owned `project.yaml`, `runs/`, `logs/`, and `runtime/`; references inputs in place; and retires the local-pilot starter/manual-workspace path without coupling setup to runtime acquisition. |
| `RUNTIME-01` | Institution-provided discovery is implemented as a dry-run-first route publishing only Project-owned `runtime/runtime.tsv`, which run, resume, and Doctor derive; generic profile-driven inspection remains advanced evidence. The packaged Pixi Managed resources target Linux x86-64 with declared glibc 2.28/Linux 4.18 virtual-package values, and Doctor repair delegates locked `.venv`, native/R, and R-package provisioning to `uv`, Pixi, and `renv` under owned paths before requalification. Ordinary CI installs the unchanged lock and invokes its tools in Rocky 8.10, Ubuntu 22.04, and Debian 12 userspaces; the real-tool managed direct Ubuntu golden-path job is implemented with exact-head execution pending. Actual Linux 4.18, broader portability, cluster/site, scheduler, security, update qualification, Explicit definition, named profiles, and taxonomy remain Open; runtime stays separate from execution profiles. |
| `DOCTOR-01` | **Complete.** Top-level Project-aware diagnosis derives input, storage, runtime, and execution readiness with normal/verbose/debug disclosure. Diagnosis and preview write/log nothing. Confirmed repair may publish one receipt-last Project-owned direct-storage qualification and is otherwise bounded to the active checkout-owned `.venv` and Project `runtime/managed`; it delegates to established package managers, owns one maintenance log, preserves inputs and site/user profiles, and requalifies. Storage-only repair preserves an already-ready site runtime and invokes no package manager. Direct Runs admit the local receipt or stronger v1 evidence; Slurm and placement-less historical Runs remain v1-only. |
| `RUN-03` | **Complete.** The current path constructs and commits immutable successor Run authority, admits it through workflow/task boundaries, and supports zero-Attempt inspection, execution, and compatible resume without permitting Attempt mutation of Run. One terminal direct invocation displays and confirms the exact frozen Run plan. Slurm constructs one frozen submission plan, displays its placement summary, and submits that same object once after confirmation; its private delegate constructs the Run and opens the application log inside the allocation. `--execute` remains the explicit automation path. Refusal, EOF, or interruption precedes every applicable direct or transport mutation. The scientific Attempt ends at `cohort_slice` with a released lock and receipt v2; default reporting runs afterward, `--no-report` disables it, and `emrys report` plans/generates/reuses it independently without creating a Run or Attempt. Low-level reporting commands and the composite workflow tail are retired. Computational declaration may affect Run identity; profile location/raw bytes, placement, allocation, scheduler job ID, logging, reporting, and transport state remain Run-neutral facts. Real scheduler/site and outcome parity remain with `AC-SLICE-05`/`OPS-02`; broader public-model migration remains with `AC-SLICE-03`/`CONTROL-01`/`ARCH-01`; role-tiered Run identity and locator disclosure are complete under `AC-SLICE-09`/`IDENTITY-01`. |
| `IDENTITY-01` | **Complete.** Successor Runs use the selected domain-separated digest over relocation-independent Analysis and Execution-Plan identities, with historical Runs preserved through the version-aware reader and no successor execution projection. Normal operation uses one primary Run ID; verbose inspection adds admitted Analysis, Execution Plan, and Attempt identity; debug retains detailed authority, artifact, receipt, task, and evidence metadata. No subsystem reconstructs a competing Run identity. |
| `FILESYSTEM-01` | Completed `RESULTS-01` supplies one current discoverable result/report surface with no hidden competing report root; a Run Bundle is likely useful while its acceptance, shape, exact contract, and automatic broader directory creation remain Open; no distinct Artifact Store is currently selected |
| `CONTAINER-01` | Independent managed-container/environment decision without assuming final runtime labels; institutional/native/advanced coexistence, image contents and digest, scheduler/storage/security/licensing/update contracts |
| `REVIEW-UX-03` | Scientist, advanced scientist, operator, automation, and developer journeys; progressive disclosure; cognitive-load and golden-path baseline |
| `LOG-03` | Durable complete attempt logging remains infrastructure while concise output becomes the default role-appropriate surface |
| `LOG-05` | Grouped `run`/`resume` execution owns one protected compute-side application attempt; automatic reporting continues in that same log after the scientific receipt. Standalone executing `report` owns one reporting log. Confirmed Doctor repair owns one maintenance log from pre-mutation through requalification; diagnosis and preview own none. Hosted direct/Slurm success-path parity proves one Run log in either placement and scheduler streams only for Slurm. Logging degradation cannot change evidence, recovery, or exit; other retained operations and failure-path parity remain Open. |
| `OBS-01` | **Complete.** Grouped Run control now keeps Run/work/reporting, meaningful phases, Results/evidence, warnings/failures, and the log path normal; operational paths/resources/profile/streams are verbose; exact engine/scheduler/task commands are debug. Durable evidence and machine output are unchanged. |
| `OBS-02` | High-level scientific progress, public run status, elapsed time, completion/failure, and links to recovery/inspection |
| `ANALYSIS-01` | **Complete.** Named Analyses may select Dataset samples explicitly or default to all samples, stop at the immutable Step 06 boundary, and launch a separately identified exact-subset downstream Run from one stationary successful processing Run. The private selected TSV is Attempt-bound backend projection, not another authored/evidence authority. Generalized collaborator modules remain `ANALYSIS-02`. |
| `ANALYSIS-02` | **Implementation complete; Verification pending.** One explicitly selected installed v1 module declares configuration admission, one or two downstream Step 09/10 tasks, typed dependencies and artifacts, validation, runtime/resource needs, one implementation package, and provider provenance/trust. It owns a bespoke scientific renderer over admitted results; EMRYS owns evidence/operations rendering and report validation, publication, receipt, default invocation, opt-out, and independent regeneration. The built-in paired-CMH analysis and an external-provider fixture use the same boundary without edits to the core graph or scheduler. No universal Stage hierarchy, workflow language, second scheduler, auto-installation, generic report schema, or customizable-section DSL is introduced. Exact-head CI remains pending. |
| `ARCH-01` | Consumes the completed prerequisites and current vertical cutovers. Sections 13.6, 13.19, and 13.20 leave one execution-profile owner, one private whole-Run Slurm transport/bootstrap, one closed project-v1/named-Analysis source, and grouped control while retiring split configuration, the generated wrapper, all sixteen owner-local scheduler routes, and active request-v3 intake. Run remains immutable, placement/diagnostics remain Attempt-local, Attempt-v1 evidence and Results authority remain unchanged, and no second backend, scheduler, facade, Artifact Store, or evidence deletion is introduced. Broader package, generalized storage, remaining caller migration, and only demonstrated policy/artifact consolidations stay Open under the existing-tool-first protocol. Generalized-backend evaluation remains required near closure. |
| `REPORT-03` | Primary-scientific-findings hierarchy with evidence and operational detail progressively disclosed |
| `REPORT-04` | Preserve the requested ability to render nine A-through-I selections when the admitted result warrants them |
| `RESULTS-01` | **Complete.** Current Runs expose only editing results, scientific context, and receipt-bound reports beneath `results`; nonfinal/QC artifacts live beneath `products/native`; both reports link to admitted primary result tables; no copy, symlink, new manifest/index, or competing current report root exists. Exact legacy-profile report ledgers remain readable as historical evidence, while old-layout Runs are not automatically resumable under the changed current profile. |
| `DOC-01` | Role- and journey-based scientist/operator/developer documentation that does not assume campaign history |
| `DOC-02` | Completed repository-wide documentation disposition and authority cutover; bounded documentation migration and retirement now remain under completed `DOC-03` and open `DOC-04`–`DOC-05`; `CLEAN-01` is Verification pending and `CLEAN-02` is complete |
| `DOC-03` | Completed source reconciliation and retirement of the stale future-architecture, pipeline-plan, question-index, and future-diagram surfaces without settling the final architecture-document set; the [durable trace](../design/decisions/repository-and-delivery.md#doc-03-source-to-destination-trace-2026-08-25) lives in the repository-and-delivery decision record |
| `DOC-04` | Reconcile every handoff section, preserve unique dated evidence and durable recovery facts without promotion, discard blocker/takeover prose, and retire the rolling handoff |
| `DOC-05` | The launcher transition plan is retired after its current safeguards move to execution-profile, transport, onboarding, package, contract, test, CI, runbook, and configuration owners. `ORCHESTRATION_READINESS.md` still requires its separate consolidation and retirement, so the card remains Open. |
| `BACKLOG-01` | Matrix cutover remains a discrete task; this campaign does not silently create another permanent backlog authority |
| `DOC-TOOL-01` | Preserve useful documentation validation in a correctly named owner while removing obsolete task-registry coupling |
| `TOOLING-01` | Complete the exact former-file/caller history audit for the absent generic Git-orchestration namespace; useful validation remains with its documentation owner and no check-only return guard is required |
| `CLEAN-01` | **Implementation complete; Verification pending.** The public demo surface, docs/Make owner, and fake fresh-clone harness retire; `emrys init synthetic` and focused lifecycle/reporting evidence retain the neutral supported value. Exact-head aggregate CI remains pending. |
| `CLEAN-02` | **Complete.** Every pending Step 04 intent maps to the active duplicate-marking owner suite; the missing-input execution case explicitly proves Picard is not invoked. The two-file non-runnable planning surface, inbound routes, and inventory exception retire, and the owner suite prevents the directory from returning. |
| `FUT-DATA-02` | Preserve initial exact NCBI reference and SRA-read adapters versus possible later ENA, GEO, and BAM acquisition as an explicit nonbinding scope choice; provenance and acquisition acceptance remain matrix-owned |
| `FUT-INDEX-01` | Reuse a compatible declared index rather than regenerate it; compatibility and identity remain fail-closed |

Other retained qualification, runtime-defect, reporting-layout, acquisition, and
performance rows remain in the matrix unchanged unless later campaign slicing
demonstrates a specific architectural relationship. Inclusion here must not be
used to blur their separate acceptance evidence.

## 18. Source inventory and duplicate treatment

### 18.1 Source files

| Source ID | Source label | SHA-256 | Treatment |
|---|---|---|---|
| `AC-SRC-001` | Pasted architecture critique and redesign narrative | `ad2bd7d38e52047ea655e442e61eb5d97e304f3df026b9d1f48f7b38e61417ee` | Primary detailed UX narrative; partly duplicates the earlier inline chat passage, then adds runtime, Doctor, Stage, reporting, container, migration, and statistical-audit detail |
| `AC-SRC-002` | Concise “Architecture Revision & Usability Plan” | `e5cec5e7409721dbbf1f8ef1f02d0a8dc56e98607530bef21ddb47bce139290a` | Condensed architecture outline; preserves complexity disposition, four core abstractions, state hiding, progressive disclosure, facade migration, and measurement framing |
| `AC-SRC-003` | Expanded “Architecture Revision & Usability Plan” | `777257adf2b84954408c29e54282aec3b722b825d78cb5bcfbae1e8d6ac2ba9b` | Most comprehensive proposal; preserves invariant constitution, domain model, execution/policy/artifact abstractions, Run Bundle, recovery, layering, metrics, phase and P0–P3 suggestions |
| `AC-SRC-004` | Current external findings matrix used for routing | `a3be3d24c6e6e5a79a70c64d11fe610b706a85e095e20e8c292a7781d5f3888f` | Existing task authority at intake time; destination for accepted task-level context, not an architecture source to supersede silently |

The attachment storage paths are session-local and are intentionally not
treated as durable repository links. Hashes identify the exact reviewed bytes.

`AC-SRC-003` also supplied an unverified historical interpretation: initial
workflow work beginning on June 11, 2026; a subsequent 38-day period without
commits; resumed development on July 25; and rapid acquisition of validation,
provenance, reporting, ownership, transaction, HPC, runtime, and test machinery
during the following month. This chronology is retained as source context, not
as repository fact. `AC-DEC-023` requires live Git verification before any part
of it is reused as durable project history or campaign rationale.

The following coverage map records where every substantive source region was
consolidated. Line numbers refer to the exact hashed source bytes above; they
are provenance for this intake, not durable links to the attachment paths.

| Source region | Substantive content | Campaign destination |
|---|---|---|
| `AC-SRC-001:2-649` | Thesis, leaked concepts, public model and commands, runtime modes, Doctor, engine concealment, configuration ownership, identity/filesystem models, and combined plan/execute UX | Sections 1-3, 5, 6, 9, and 10; duplicates earlier chat intake `AC-IN-003` |
| `AC-SRC-001:651-753` | Transparent local/SLURM execution, thin Stage proposal, named stages, lifecycle, and visible-science boundary | Sections 7-9 and `AC-SLICE-04`/`05` |
| `AC-SRC-001:755-913` | Simple integrity presentation, role-based documentation including the five-page scientist-layer suggestion, actionable Doctor/repair and Snakemake-readiness examples, and container contents/digest | Sections 4, 6, 9, 11, and `AC-SUG-010` |
| `AC-SRC-001:915-1125` | Domain/Stage/Run consolidation, hide-not-delete inventory, detailed first-use transcript and completion funnel, target application architecture, and Artifact Store proposal | Sections 2, 5-8, 10, `AC-DEC-025`, and `AC-SUG-013`/`015` |
| `AC-SRC-001:1128-1263` | Suggested phases, independent Steps 08/09 oracle, preservation of evidence machinery, Steps 07-09 statistical-audit focus, and the proposed parallel/next-review emphasis | Sections 4, 12-15, `AC-SLICE-15`/`16`, and `AC-SUG-014` |
| `AC-SRC-002:1-175` | Concise diagnosis, complexity disposition, Project/Run/Result target, golden path, Artifact Store, and 80/15/5 escape-hatch heuristic | Sections 1-3, 5, 6, 8, 10, and `AC-DEC-025` |
| `AC-SRC-002:177-292` | Artifact, Execution, Policy, and Run abstractions plus hidden state/resume behavior | Sections 8 and 11 |
| `AC-SRC-002:294-449` | Alternate onboarding order, Doctor and Snakemake readiness, four disclosure levels, facade-first migration, measurement, and dual user/operator acceptance criteria | Sections 3, 6, 9, 10, 13-15, and `AC-DEC-024` |
| `AC-SRC-003:1-184` | Expanded diagnosis, complexity principle, and scientific/provenance/execution/evidence constitution | Sections 1-4 |
| `AC-SRC-003:185-373` | Project, Run, Artifact, Execution, and Report models; execution engine; policy authorities; artifact lifecycle | Sections 5, 7, and 8 |
| `AC-SRC-003:375-590` | Public/internal states, recovery, golden path, Doctor, configuration split, and execution profiles | Sections 5, 9-11 |
| `AC-SRC-003:592-816` | Progressive disclosure, exact eight-step explain example, three report purposes, Run Bundle, recovery, and dependency layering | Sections 6, 7, 11, and `AC-SUG-011` |
| `AC-SRC-003:817-990` | Anti-over-abstraction and anti-second-engine guardrails, local versus HPC learning modes, time targets, incremental refactoring/deletion strategy, and journey-first documentation order | Sections 8, 10, 13, 14, and `AC-SUG-012` |
| `AC-SRC-003:992-1167` | Proposed CLI and first-use transcript, consolidation/deletion candidates, explicit adversarial and synthetic E2E preservation, metrics, and suggested P0-P3 order | Sections 3, 4, 5, 8, 10, and 13-15 |
| `AC-SRC-003:1168-1277` | Architectural north star, target user/internal boundary, final novice and expert acceptance criteria | Sections 1-3 and 20 |

### 18.2 Chat intake ledger

| Intake ID | Intake content | Disposition |
|---|---|---|
| `AC-IN-001` | Initial unorganized findings covering Step-06 reuse, analysis modules, repo coupling, index reuse, documentation, inline scripts, operator commands/defaults, orchestrator naming, ingestion, benchmarking, container evaluation, config sprawl, guided setup, stale architecture/demo/logging/campaign language, report capacity, automatic directories/results, and Git-orchestration cleanup | Routed to existing matrix IDs in Section 17; unmatched architecture context retained here |
| `AC-IN-002` | Discard blockers; keep containerization independent of setup; retain every unimplemented matrix item; make repository documentation audit, validator relocation, and backlog retirement discrete tasks | Reflected in matrix structure and `DOC-02`, `DOC-TOOL-01`, `BACKLOG-01`, and `CONTAINER-01`; no dependency edges introduced |
| `AC-IN-003` | Architecture thesis, implementation-detail leakage, Project/Run model, small CLI, configuration ownership, identity hierarchy, filesystem model, and plan-to-execute simplification | Consolidated in Sections 1, 2, 5, 9, and 10; partly duplicated by `AC-SRC-001` |
| `AC-IN-004` | Overall UX simplification, layering, abstractions, golden path, and role-based development are non-negotiable | Binding in Section 3 |
| `AC-IN-005` | Override the categorical non-mutating Doctor requirement | Binding repair posture recorded in Sections 3 and 9; exact interface is now resolved by `AC-DEC-003`, `DOCTOR-01`, and Section 13.14 |
| `AC-IN-006` | Proposed names, phases, numeric targets, and ordering are not settled; preserve them as suggestions for later reconsideration | Enforced by status banner and Sections 13–15 |
| `AC-IN-007` | Intake complete | Intake frozen on 2026-08-24; new material requires an explicit reopened or successor intake |

### 18.3 Post-intake ratification ledger

These user decisions govern how the closed intake is audited and implemented;
they do not reopen it or promote any remaining proposal.

| Ratification | User decision | Durable disposition |
|---|---|---|
| `AC-RAT-001` | Every audit records compression opportunities; every vertical implementation slice aggressively removes redundant maintenance surface without losing essential behavior; net-negative maintained product code and no product-file growth are the defaults | Binding requirement 8, `AC-GUARD-006`, and the Section 13.1 protocol |
| `AC-RAT-002` | Immutability is preferred throughout; `Run` is the immutable plan; public nouns and nesting are decided only after audit and discussion; every other application-model, API, backend, and policy decision is deferred until then | Binding requirement 9, `AC-GUARD-007`, `AC-SLICE-03`, and `AC-DEC-001`/`011` |
| `AC-RAT-003` | Redundant evidence may be identified, but deletion requires great caution and the user's explicit approval | Binding requirement 10, `AC-GUARD-008`, and the evidence proposal and separate-commit gate in Section 13.1 |
| `AC-RAT-004` | Adopt model C and the compact public model `Project -> Analysis -> Run -> Results`, progressively disclose Attempt, keep Execution Plan internal and inspectable, and apply the ratified Run-versus-Attempt change boundary including identity-neutral downstream reporting | Durable `ARCH-MODEL-DECISION-01`, resolved `AC-DEC-001`, the semantic package in `ARCH-MODEL-FIELDS-01`, and the first successor Run-authority realization; broader `AC-DEC-011` and `AC-SLICE-03` work remains Open |
| `AC-RAT-005` | Remove redundant validation and protection against impossible same-process states when maintenance cost exceeds the nonexistent independent failure boundary; low-risk check-only seams need no artificial replacement, while high-risk, ambiguous, directly user-facing, execution-boundary, or evidence-validation change requires explicit approval | Refined `AC-GUARD-005`/`006`, Section 13.1 risk/trust-boundary protocol, and the focused reduction register; retained evidence remains separately governed by `AC-RAT-003` |
| `AC-RAT-006` | Every slice touching a retained applicable operation records and incorporates the relevant `LOG-05` work when output or durable diagnostics change, without creating an interim logging convention | Binding requirement 8, Section 13.3, the logging contract adoption boundary, and the findings-matrix closure guard |
| `AC-RAT-007` | Every touched shell or generated-shell surface is evaluated for retention, Python conversion, or retirement; conversion proceeds only when it reduces total product, protection/test, caller, and cross-language surface | `AC-GUARD-006`, Section 13.1, and the focused shell-disposition audit |
| `AC-RAT-008` | Evaluate existing repository owners, maintained tools/libraries, and established package managers before bespoke code; make explicit Doctor repair delegate dependency mechanics; require concrete duplicate consumers before shared policy; evaluate a generalized-backend boundary near closure while keeping implementation conditional; defer a distinct Artifact Store until a separately approved concrete unmet need | Binding requirements 7, 8, and 11; `AC-GUARD-006`; `AC-INV-011`/`018`; Sections 8.3–8.5 and 9; resolved `AC-DEC-009`; trigger-deferred `AC-DEC-025` |

### 18.4 Duplicate policy

The three attachments express the same central thesis at different levels of
detail. They are **overlapping sources**, not disposable duplicates:

- recurrence increases confidence that a concern was intentional and central;
- repeated wording is consolidated once in the narrative;
- unique examples, alternative commands, abstraction variants, sequences,
  metrics, and diagrams remain represented;
- agreement among the sources does not convert a suggestion into a decision;
  later explicit ratification can do so, as recorded by `AC-RAT-004`;
- source-specific chronology and repository-history assertions remain
  unverified until checked against live Git and current canonical documents.

No substantive recommendation was discarded merely because another source
made a similar recommendation.

## 19. Prioritization contract

At the user's explicit direction on **2026-08-25**, the campaign uses two
deliberately separate scoring passes:

1. The [architecture backlog matrix](architecture_backlog_matrix.md) records a
   cursory **Architecture Priority** and **Indicative Complexity** for each
   unsliced campaign card. These preliminary buckets guide just-in-time
   selection and decomposition. They do not accept work, settle sequencing, or
   become task scores automatically.
2. After campaign context has been sliced into the main matrix and traceability
   is complete, every active main-matrix item will receive separately reviewed
   **Importance** and **Complexity** scores with a short rationale.

Candidate dimensions are:

| Score | Dimensions to consider |
|---|---|
| Importance | Scientific integrity, user/operator impact, evidence or reliability risk, breadth/frequency, strategic enablement, and urgency |
| Complexity | Number of owners and callers, public-interface/schema migration, runtime/site/cluster dependencies, transaction/recovery risk, compatibility burden, and required validation |

The final accepted-task scale and rubric remain to be ratified. Preliminary
campaign-card scores must be reconsidered rather than copied into that pass.
Importance and complexity must not be collapsed into one opaque number, and
source-proposed P0–P3 ordering must not preempt final scoring. Dependencies,
risk, sequencing opportunities, and available evidence may inform later
execution order without becoming hidden blocker edges.

## 20. Campaign exit criteria

This document remains temporary authority until all of the following are true:

1. Every attachment and chat intake ID has a recorded disposition.
2. Every substantive goal, constraint, example, alternative, metric, and ideal
   end state is either:
   - durable context in an existing matrix item;
   - represented by one or more new matrix items;
   - retained as an architectural invariant or open decision in an approved
     durable owner; or
   - explicitly discarded by the user with a reason.
3. Every candidate slice has been accepted, revised, split, absorbed, or
   explicitly declined.
4. Every new matrix item has one observable outcome, bounded scope, non-goals,
   affected owners/callers, a compression register, mutation inventory,
   invariant traceability, protection and evidence dispositions, acceptance
   conditions, and evidence ceiling.
5. The completed matrix has separately reviewed Importance and Complexity
   scores and rationales.
6. The matrix, task navigation, and legacy backlog transition identify one
   unambiguous active backlog authority.
7. No proposed name, phase, target, ordering, historical claim, or example has
   been silently promoted into a binding decision.
8. A final source-to-destination audit finds no orphaned intake item,
   compression opportunity, or architectural context that exists only in an
   attachment path or temporary register.
9. The user approves the final traceability and prioritization review.
10. This document receives an explicit retain, archive, consolidate, or retire
    disposition; it does not remain a second permanent backlog by accident.
11. Every proposed evidence deletion is explicitly declined or
    approved for an exact bounded deletion; campaign completion itself never
    supplies deletion authority.

Until those conditions hold, this campaign document preserves the complete
planning context while the matrix remains the authority for accepted tasks and
their status.
