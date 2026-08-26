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
   secrets, or mutate declared scientific inputs.
8. **Maintenance-surface compression.** Every architecture audit must record
   concrete opportunities to retain, consolidate, retire, or defer product
   logic, wrappers and compatibility paths, configuration, scripts, schemas,
   documentation, protections, and evidence. Each implementation slice must
   make the smallest complete vertical change, migrate callers, and retire the
   responsibility it supersedes. Net-negative maintained product code and no
   product-file growth are the defaults; an exception requires the user's
   approval of quantified growth and its justification, plus an owner and
   retirement condition when the growth is temporary.
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
- direct-owner, adversarial, seeded-fault, and synthetic end-to-end defenses
  require mapped equal-or-stronger replacement at the same evidence level.

On **2026-08-26**, the user ratified three additional campaign guardrails for
maintenance-surface compression, immutable-by-default design with `Run` as the
immutable plan, and approval-gated evidence deletion. These extend rather
than rewrite the historical five-guardrail `ARCH-CONST-01` result. Their
canonical definitions are `AC-GUARD-006` through `AC-GUARD-008` in the same
platform-direction decision.

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

and the even smaller:

```text
Project / Analysis -> Run -> Result
```

The binding outcome is a small vocabulary. The method notation above is intake
traceability, not an authorization for a mutable Run aggregate or a selected
application API. `Run` is now reserved for the immutable plan. Whether it is a
public type, how it is constructed or persisted, where it nests, and whether
`Project` and `Analysis` are distinct identities, aliases, or nested concepts
remain open pending the application-model audit and discussion.

### 5.2 Proposed public commands

The normal surface should express user intent rather than engine mechanics.
The following names are **proposed, not settled**:

| Intent | Suggested names retained from intake |
|---|---|
| Create or prepare a project | `emrys setup`, `emrys init` |
| Validate readiness | `emrys validate`, `emrys check`, `emrys doctor` |
| Plan and execute | `emrys run` |
| Observe current work | `emrys status` |
| Recover compatible work | `emrys resume` |
| Inspect internals or provenance | `emrys inspect`, `emrys run --explain`, `emrys diagnostics`, `emrys debug ...` |
| Read or regenerate reports | `emrys report` |
| Manage runtime modes | `emrys runtime discover`, `accept`, `define`, or `install` |
| Inspect or manage effective configuration | `emrys config` |
| Exercise a neutral synthetic path | `emrys demo` was suggested, but the name conflicts with the planned demo-surface retirement and remains open |

The interface must remain automation-friendly, including deliberate
noninteractive confirmation such as the proposed `emrys run --yes`, without
making raw engine commands the automation API.

### 5.3 Configuration ownership

| Configuration layer | Questions answered | Normal owner |
|---|---|---|
| Scientific | Which data, reference, samples, pairing, biological comparison, thresholds, regions, cohorts, and analyses? | Scientist |
| Execution | Where does it run, with which resources, scheduler, scratch, storage, and tool installation? | Operator or site administrator |
| Evidence | Which hashes, receipts, attempts, artifact identities, and immutable records establish provenance? | EMRYS, exposed for inspection |

A proposed scientist-facing form is:

```yaml
project: my-experiment

reference:
  fasta: /data/ref/genome.fa
  gtf: /data/ref/genes.gtf

samples:
  - id: control_1
    r1: /data/control_1_R1.fastq.gz
    r2: /data/control_1_R2.fastq.gz
    condition: control
    replicate: 1
  - id: treatment_1
    r1: /data/treatment_1_R1.fastq.gz
    r2: /data/treatment_1_R2.fastq.gz
    condition: treatment
    replicate: 1

analysis:
  target_change: A>G
  min_depth: 10
  fdr: 0.05
  min_effect: 0.01
```

This schema is illustrative. Embedded samples versus a separate sample TSV,
and `project.yaml` versus `analysis.yaml`, remain open. The durable requirement
is that EMRYS generates normalized requests, partition manifests, runtime and
resource configuration, launcher details, run identity, and evidence manifests
without requiring a scientist to author implementation details. Every effective
value remains inspectable.

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
`Project`, `Stage`, and whether `Run` is public remain proposals; `Run` itself
is reserved for the immutable plan. Reporting is downstream operational work
rather than a semantic scientific stage. OS, R, Python, SLURM, Snakemake, and
filesystems are external mechanisms reached through EMRYS-owned boundaries,
not an internal authority layer.

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

**Partially resolved:** the architecture distinguishes evolvable user intent
from an immutable inspectable plan and from operational attempt state when
present. The immutable plan is the `Run`; it is never modified in place, and a
changed plan requires a new plan. The exact identity and cardinality
consequences remain open. The model must permit multiple analyses over
compatible upstream artifacts. Application coordination may admit intent,
resolve a Run, invoke lower capabilities, and assemble outcomes, but it cannot
absorb scientific, execution, policy, artifact, evidence, or reporting
authority.

Lower capabilities receive explicit immutable supported information rather
than importing a broad higher-level aggregate or independently reconstructing
competing identity. Draft construction, attempt-local execution state, locks,
logs, and transactional publication may mutate only inside an explicit owner
and cannot alter or reconstruct the Run. Whether `Run` is public, how Project,
Analysis, Attempt, Result, and artifacts are named or nested, and whether any
representation is an object, record, service, facade, or functions remain
`AC-SLICE-03` and `AC-DEC-001` audit and discussion outcomes.

`ARCH-MODEL-AUDIT-01` completes the current-state audit prerequisite below;
it does not resolve the remaining `AC-DEC-001` or `AC-DEC-011` model choices.

The same slice must inventory, but not prematurely decide, whether consumers
receive one narrow shared context or multiple owner-specific capability views;
the exact operations, arguments, return types, error model, and
synchronous/asynchronous behavior; and the boundary among science-affecting
values, execution values, Run identity, and attempt identity. Analysis, Run,
attempt, artifact, and report identity inputs remain open, including whether
runtime, executor, resource, or report choices affect identity. User-authored
schemas, package/import surfaces, CLI mapping, compatibility windows, migration
order, persistence, storage, and any relationship between default reporting
and the lifecycle surrounding Run also remain unsettled until the audit is
reviewed and the user separately approves decisions.

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
  +-- init -> onboarding -> starter-set publication
  +-- validate local-pilot-request -> request admission/normalization only
  +-- doctor local-pilot -> readiness inspection
  +-- run -> control -> Doctor -> normalization -> resource/capacity policy
  |    -> AttemptPlan
  |       +-- dry-run -> print plan; no workspace write
  |       +-- --execute -> create run skeleton -> lifecycle admission
  |            -> local Snakemake executor -> functional-owner tasks
  |            -> artifact index -> run summary -> HTML reports
  |            -> terminal attempt receipt
  +-- resume -> inspection/readiness -> AttemptPlan -> optional execution
  +-- inspect local-pilot-run -> explicit read-only derived inspection
  +-- build report -> separate low-level report regeneration path
```

Ordinary `emrys run` does not invoke onboarding or the explicit request-
validation command, and full `inspect_run` is an explicit command or an
internal resume/lifecycle check rather than an automatic post-receipt step.
The generated Slurm wrapper composes validation, Doctor, and `run` separately,
as recorded below.

The installed entry point is [`emrys.__main__:main`](../../pyproject.toml).
The current composition root is a 711-line
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

The current [quickstart](../../quickstart.md) also tells the operator to create
and populate the input-directory tree manually, redirect a complete runtime
profile to a new filename, copy the run root from a dry-run, and repeat that
transfer from a completed Slurm dry-run log before execution. This confirms
that safe internal boundaries still leak user-as-glue work into both local and
scheduled journeys.

#### Current owner and caller map

| Current owner or surface | Current responsibility | Principal callers or consumers | Audit conclusion |
|---|---|---|---|
| [`__main__.py`](../../src/emrys/__main__.py) | Parse and compose all installed command routes | Scientists, operators, automation, owner commands | Composition root, not a semantic application model; ordinary and expert capabilities are interleaved. |
| [`onboarding.py`](../../src/emrys/orchestration/local_pilot/onboarding.py) | Starter generation, request compatibility validation, and generated one-allocation Slurm wrapper | `init`, `validate local-pilot-request`, generated wrapper | Owns several setup, validation, and scheduler-launch concerns that later role journeys must repartition without weakening create-absent publication. |
| [`normalization.py`](../../src/emrys/orchestration/local_pilot/normalization.py) | Admit authored intent and construct the canonical execution identity | Onboarding validation, Doctor, control, reporting projection | Closest current semantic plan source, but it returns shallowly frozen mutable structures and is not a selected public Run API. |
| Orchestration [`api.py`](../../src/emrys/contracts/orchestration/api.py), schemas, and package exports | Validate closed records, canonicalize bytes, recompute identities, and expose the deliberate current contract API | Normalization, materialization, lifecycle, task/reporting boundaries, inspection, projection, workflow owners, packaging tests | Current contract authority and compatibility boundary; model consolidation must preserve historical admission and must not silently widen the public import surface. |
| [`doctor.py`](../../src/emrys/orchestration/local_pilot/doctor.py) | Read-only source, storage, runtime, tool, and request readiness | Standalone Doctor and `plan_run`/`plan_resume` | Produces readiness facts; it currently normalizes the request internally. |
| [Runtime-availability inspector](../../src/emrys/evidence/runtime_availability/inspector.py) and [storage-qualification owner](../../src/emrys/evidence/storage_inventory/qualification.py) | Declare/admit runtime availability and final two-phase storage evidence | Direct inspect commands, Doctor readiness, materialization bindings, lifecycle re-admission, runtime/storage tests | Independent evidence authorities outside the 43-file roster. Doctor composes them and lifecycle re-admits them before execution; future capability placement must preserve that attribution and recheck. |
| [`control.py`](../../src/emrys/orchestration/local_pilot/control.py) | Compose Doctor, normalization, resources, attempt planning, execution, resume, and inspection output | `emrys run`, `resume`, `inspect local-pilot-run` | Nearest current application coordinator; it still exposes attempt, engine, owner-job, and transaction detail directly. |
| [`resource_policy.py`](../../src/emrys/orchestration/local_pilot/resource_policy.py) and [`capacity.py`](../../src/emrys/orchestration/local_pilot/capacity.py) | Resolve effective per-stage/report resources and observe/admit available allocation capacity | Control planning, materialization/workflow configuration, launcher and resource tests | These owners materially shape the effective executable plan even though their values do not enter current `run_id`; final policy/application placement remains Open. |
| [`materialization.py`](../../src/emrys/orchestration/local_pilot/materialization.py) | Build a complete no-write `AttemptPlan`, workflow config, task dispatches, and fixed/attempt files | Control and lifecycle materialization | Current attempt-planning representation, not a selected Run model. Whether any class, package, or facade is later public remains Open. |
| [`lifecycle.py`](../../src/emrys/orchestration/local_pilot/lifecycle.py) | Serialize admission, own the run lock, execute the delegated process, bind recovery evidence, and publish the terminal receipt last | Control, task/reporting boundaries, inspection | Strong operational transaction authority cannot be transferred into application coordination. Future class/package/facade placement remains Open. |
| [`task.py`](../../src/emrys/orchestration/local_pilot/task.py) and [`reporting_boundary.py`](../../src/emrys/orchestration/local_pilot/reporting_boundary.py) | Admit one owner scope or reporting transaction and publish start/attempt/verified records | Fixed Snakemake workflow and lifecycle | Retain functional and downstream transaction authority; do not move it into application coordination around Run. |
| Fixed [`Snakefile`](../../workflow/Snakefile), workflow contract, and local profile | Declare the reviewed task graph, fixed scientific-owner invocations, target, and local engine configuration | Materialization, local Snakemake execution, task/reporting boundaries, contract and end-to-end tests | Effective execution surface and current engine adapter; not application or scientific authority and not included in the 43-file footprint total. |
| [`inspection.py`](../../src/emrys/orchestration/local_pilot/inspection.py) | Derive current aggregate state from canonical contracts, records, receipts, and the owned lock | Control, lifecycle resume checks, tests | Read model only. The current `RunInspection` name is descriptive and does not select the target Run representation. |
| [`projection.py`](../../src/emrys/contracts/orchestration/projection.py) and reporting owners | Project the execution contract into reporting contracts and render admitted results | Normalization, materialization, workflow, standalone `build report` | Downstream reporting remains separate from scientific completion and is not a scientific stage. |
| [`launcher_config.py`](../../src/emrys/orchestration/local_pilot/launcher_config.py) | Resolve outer Slurm allocation defaults/configuration/environment/overrides and submit once | Generated `run-in-slurm.sh` | Scheduler transport only; not a second application backend or scientific authority. |
| [`dashboard.py`](../../src/emrys/orchestration/local_pilot/dashboard.py) | CSU preview using scheduler queries plus parsed stdout/Snakemake stderr | `make dashboard` | Non-authoritative presentation with text coupling and fixed six-sample/25-partition display assumptions; eventual structured input is a candidate, not an approved rewrite. |

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
| `RunInspection` | Regenerated read-only aggregate state | Inspection over persisted authorities | Current state projection. It is not persisted authority and must not define target Run mutability. |
| Dashboard dictionaries and stream caches | Mutable presentation state for one live view | Dashboard only | Necessary local UI state, not application or evidence authority. |

There is no current application-level `Project` or `Result` representation.
`WorkflowResult` reports the delegated process exit and `LifecycleOutcome`
reports one terminal attempt; neither is the campaign's possible public
Result. The current run root is an aggregate namespace containing an immutable
contract, evolving attempts, locks, task/report state, native results,
products including reports, attempt-local stream logs, and disposable engine
metadata. It has no top-level report surface; generated reports live under
`products/report/<run-id>/`. Treating that entire directory or `RunInspection`
as the target Run would therefore contradict the settled immutable-plan
meaning.

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

`plan_run` performs readiness, normalization, resource resolution, and attempt
planning without writing workspace state. In one `emrys run --execute`
invocation, the same in-memory `AttemptPlan` is printed and then executed. A
plain dry-run persists no accepted plan. If the user later invokes
`emrys run --execute` separately, EMRYS recomputes normalization/readiness and
creates a new attempt time, token, owner token, process identity, and attempt
paths. The user therefore cannot currently approve and execute the exact prior
dry-run plan. There is also no built-in interactive confirmation between plan
display and mutation.

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

The generated Slurm path is an outer single-node allocation wrapper:

```text
submit host
  -> resolve LauncherPlan
  -> sbatch --nodes=1 --ntasks=1 ...
  -> generated wrapper inside allocation
  -> validate request
  -> Doctor
  -> emrys run
  -> Snakemake local executor on the allocated node
```

It is not currently a separate application execution backend. `AttemptPlan`
records `executor: local`, and no scheduler job ID is stored in the workflow
attempt or terminal lifecycle receipt. Scheduler association is reconstructed
from wrapper/log context and by the dashboard. The generated wrapper also
normalizes the same request four times along its validate → Doctor → run path:
once for explicit request validation, once for standalone Doctor, once for the
Doctor invoked by `run`, and once after that Doctor in control. Any reduction
must retain deliberate lock-time and pre-mutation re-admission and must
re-admit after any future explicit Doctor repair that changes owned state,
rather than equate every repeated check with waste or carry stale facts across
a mutating repair.

#### Current status, Result, and reporting gap

Current `RunInspection` exposes five derived states:
`prepared`, `running`, `resume_available`, `blocked`, and
`local_pipeline_complete`. Attempt receipts separately expose
`succeeded`, `failed`, `interrupted`, or `blocked`.

Today a successful attempt receipt sets `local_pipeline_complete=true`, and
inspection requires all three reporting transactions before admitting that
success. This conflicts with the already accepted target semantics: reporting
is downstream operational work, invoked by default for a full run, explicitly
disableable, and independently regenerable; report failure must not invalidate
completed science. The standalone `emrys build report` capability exists, but
requires implementation-level input and output paths rather than a compact
Run-oriented reference, and its output does not adopt or repair the
orchestration reporting ledger. The audit records this gap without selecting
new status names, persistence, command structure, or retry policy.

#### Mutation inventory

The strongest current immutability is in validated canonical bytes and
create-exclusive persisted records, not in every Python aggregate:

| State | Current owner and lifetime | Writers | Readers | Why mutation exists now | Immutable-boundary disposition |
|---|---|---|---|---|---|
| Normalization drafts and `NormalizationBundle` mappings | `normalization.py`; one normalization call, then the returned bundle's in-memory lifetime | Normalization builders populate request, profile, and execution dictionaries | Onboarding validation, Doctor, control, projection, materialization, tests | Draft parsing, defaulting, snapshot admission, and canonical construction are naturally incremental; post-admission mutability is not required | Retain mutable local drafts; candidate one immutable admitted result whose canonical bytes and views cannot diverge. Final public type and owner remain Open. |
| `AttemptPlan.attempt_record` and nested bundle | `materialization.py` and control; one execute or resume planning invocation through lifecycle handoff | `build_attempt_plan` constructs it; an injected control transformer may replace the plan before return; audited in-repo local-pilot callers showed no later mutation | Control display/execution, materialization publication, lifecycle admission, tests | Construction combines readiness, resources, identity, time/token/host/process, files, and command facts; later mutability is incidental | Exact admitted plan boundary is required. Preserve prepared-versus-materialized byte equality; whether Attempt fields belong to Run remains Open. |
| `LifecycleRequest.attempt_record` | Materialization-to-lifecycle handoff; one materialized attempt admission | `publish_attempt` constructs the request from the plan | Lifecycle admission, identity/resource/argv rechecks, tests | Mapping shape is inherited from construction; no mutation after handoff is necessary | Candidate immutable admitted request value; do not conflate it with live lifecycle transaction state. |
| `LifecycleOutcome.receipt` | Lifecycle-to-control handoff; one terminal attempt return | Lifecycle builds the terminal receipt/outcome after receipt-last publication | Control result projection, verified-report display, tests | Dictionary construction mirrors the persisted schema; post-return mutation is not required | Candidate immutable terminal view over persisted evidence; receipt file remains authority. |
| `TransactionSignalController` and delegated-process state | `lifecycle.py`; from signal-handler installation through receipt commit/restore | Signal handlers and lifecycle execution update child, signal, interruption, and commit state | Lifecycle cleanup, termination, receipt publication, fault tests | Live process and signal ownership must change as execution advances and cannot be modeled truthfully as a fixed value | Retain tightly owned mutation. Expose only immutable outcome/evidence values after the transaction. |
| `_OwnedRunLock.record`, bytes, inode, and live lock ownership | `lifecycle.py`; from exclusive lock acquisition through release/recovery publication | Lock acquisition constructs identity fields; lifecycle changes filesystem ownership state and publishes release evidence | Lifecycle serialization/recovery, inspection, resume, fault tests | The Python record need not mutate, but owned filesystem lock state must transition with attributable identity | Make the in-memory value deeply immutable if consolidated; retain narrowly owned live lock mutation and exact release/history records. |
| `RunInspection` nested attempt, receipt, task, and report dictionaries | `inspection.py`; one read-only inspection call/result | Inspection derives the aggregate from persisted authorities | Control, resume/lifecycle checks, dashboard/tests | Mutable dictionaries simplify construction; post-construction mutation is not authority or required behavior | Keep a derived non-authoritative read model and make exposed boundary values immutable when selected; never persist it as status authority. |
| `ReportingBundle` dictionaries beside exact bytes | Contract projection; one deterministic reporting projection | Projection constructs reference, policy, run-contract, and inventory documents and bytes | Materialization, workflow/reporting owners, projection tests | Incremental projection is convenient; the admitted dictionary and byte forms need no later shared mutation | Candidate one immutable projection authority with derived views; preserve deterministic exact output and separate reporting transaction authority. |
| `TaskDispatch.scope` and admitted dispatch collections | Task boundary; one functional-owner invocation | Task admission constructs the closed dispatch value from canonical bytes | Producer/validator invocation, stream capture, task publication and tests | Parsing constructs nested values; execution needs stable facts, not mutable shared ownership | Candidate deeply immutable admitted dispatch; canonical dispatch bytes and schema remain authority. |
| `TaskOutcome.task_attempt` and `verified_task` | Task boundary; one successful owner return | Task transaction builds the dictionaries after create-exclusive publication | Workflow/lifecycle caller and task tests | Dictionary form mirrors persisted records; post-return mutation is not needed | Candidate immutable result view; persisted task attempt and verified records remain evidence authority. |
| Reporting-boundary `_AdmittedIdentity` dictionaries | Reporting boundary; one report transaction admission | Reporting admission loads and validates execution, profile, attempt and references | Reporting start, semantic validation, verified publication and tests | Admission assembles related mappings; downstream mutation is not required | Candidate immutable internal admitted identity; final neutral shared admission owner remains Open and reporting ordering stays local. |
| `_TaskStreamCapture` descriptors, digests, sizes, and completion state | `task.py`; one functional-owner process invocation | Stream callbacks and cleanup update descriptor/capture state | Task attempt/log/verified publication and fault cleanup | Streaming output identities and descriptors are only known while the process runs | Retain narrowly owned mutation; publish immutable stream evidence at the boundary. |
| Dashboard `StreamCache` and presentation dictionaries | `dashboard.py`; one live dashboard session | Scheduler/log polling and parsing update cached state | Dashboard rendering and dashboard tests | A live view necessarily tracks changing non-authoritative presentation state | Retain as presentation-only mutation pending dashboard decisions; it cannot become Run, Attempt, or completion authority. |
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
its own exact category deltas and equal-or-stronger replacement proof.

| Mechanism and category | Current owners; callers and consumers | Unique retained need; redundancy evidence | Disposition and surviving authority | Estimated and audit-actual deltas | Preconditions for any future change |
|---|---|---|---|---|---|
| Closed schemas, canonical JSON, digest recomputation; protection/schema | Orchestration contract API and versioned schemas; every normalization, materialization, lifecycle, task, reporting, inspection, workflow and historical reader | Defines admitted shape and identity and independently rechecks bytes; no equivalent independent authority was found | **Retain.** Versioned contract/schema owner survives | Estimate all six zero; audit actual all six zero | A successor must prove current and historical admission, canonical bytes and digest parity before old support changes |
| Stable-file snapshots, no-follow descriptor/path binding and near-mutation rechecks; protection | Normalization, lifecycle, task, reporting and inspection; input admission, publication, recovery and adversarial tests | Prevents path replacement, symlink, inode and stale-read races; similar helpers have owner-specific semantics, not proven redundancy | **Retain; conditional primitive consolidation only.** Each current semantic owner survives | Estimate all six zero for retention; audit actual all six zero | Map large-file, inode, destination, hash, timing and error behavior and retain last-safe-boundary checks |
| Attempt mutex, owned run lock, create-exclusive publication, fsync and receipt-last ordering; protection | Lifecycle, task and reporting transaction owners; recovery, resume, inspection and fault tests | Provides serialization, attributable ownership, durability and truthful completion; repeated mechanics do not duplicate semantic ordering | **Retain.** Transaction authorities survive; only a proven low-level primitive may consolidate | Estimate all six zero for retention; audit actual all six zero | Equal-or-stronger concurrency, crash, signal, rollback, directory-durability and failure evidence required |
| Separate start, attempt, stream, verified, reporting, lock-release and terminal records; evidence | Task, reporting and lifecycle owners; inspection, recovery, audit and historical readers | Distinguishes entry, execution, validation, failure/recovery and terminal truth; record count alone is no redundancy evidence | **Retain pending itemized lifecycle/evidence audit.** Current record owners survive | Estimate all six zero; audit actual all six zero | Any proposal must name exact record class, producers/consumers, claim, recovery path, retention and rollback and receive explicit user approval if deleting evidence |
| Derived inspection independent of `.snakemake`; protection | Inspection over EMRYS contracts/records/locks; control, resume, dashboard and tests | Prevents engine metadata from becoming status, recovery or completion authority; no redundant authority exists | **Retain.** Persisted EMRYS records remain authority and inspection remains derived | Estimate all six zero; audit actual all six zero | A new read model must derive the same or stronger truthful state and cannot persist a competing status |
| Direct-owner, adversarial, seeded-fault, independent-golden, recovery, fresh-clone and synthetic E2E defenses; protection/tests | Functional owners and CI; maintainers, release review and regression diagnosis | Protects distinct failure, packaging, recovery and synthetic execution claims; coverage or happy path is not equivalent | **Retain or map individually to equal-or-stronger defense.** Existing test/evidence owner survives until mapped replacement | Estimate all six zero; audit actual all six zero | Name invariant, evidence level and surviving test for each retirement; long checks remain CI-owned |
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
| `dashboard.py` | 1,984 |
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
| `ARCH-MODEL-COMP-03` | Maintained product code and protection | Onboarding validation, Doctor, generated wrapper and control; operators, CLI, planning and tests | Fresh admission at each mutation/repair/lock risk boundary | Generated Slurm journey normalizes the same request four times before execution; ordinary run normalizes in Doctor and again in control. Wrapper validate, Doctor, and run are separate subprocesses, so one in-memory result cannot simply cross all boundaries | **Defer; candidate consolidate reusable admission only.** Current normalization/schema authority and deliberate re-admission survive | Est.: files no growth; lines and repeated call edges lower; concepts/config/compat 0. Audit actual all zero | Separate redundant work from TOCTOU defense; either collapse an approved command boundary or use one admitted transport that cannot become a second authority; re-admit after future repair and prove changed inputs fail closed at the last safe boundary |
| `ARCH-MODEL-COMP-04` | Maintained product code and protection | Inspection, lifecycle, task and reporting owners; recovery, validation and tests | No-follow stable canonical-record admission with owner-specific size, inode, destination, hashing and diagnostic rules | Multiple owners already call `inspection.admit_canonical_record` while retaining parallel higher-level identity binding and specialized readers | **Defer; evaluate candidate seam.** Final neutral owner/API/package remains Open; each semantic owner retains its unique checks | Est.: files no growth; lines and duplicate call edges lower; concepts/config/compat 0. Audit actual all zero | Map exact per-owner semantics and dependency cycles; share only proven intersection; preserve large-file behavior and fault/error contracts |
| `ARCH-MODEL-COMP-05` | Maintained product code and protection | Lifecycle, task and reporting publication owners; inspection, recovery and fault tests | Create-exclusive durable bytes, directory fsync, transaction ordering, rollback and truthful terminal publication | Closely related low-level publication mechanics are implemented separately in the three transaction owners | **Defer; candidate consolidate primitive only.** Lifecycle/task/reporting remain separate semantic authorities; primitive owner Open | Est.: files no growth; lines lower; concepts/config/compat 0; low-level edges may converge without new semantic edge. Audit actual all zero | Prove byte-publication equivalence; retain signal/ownership/rollback/order/fault differences and receipt-last semantics |
| `ARCH-MODEL-COMP-06` | Maintained product code and configuration | Doctor, onboarding, materialization and control; readiness, planning, validation and tests | Bind the reviewed fixed workflow profile and exact checkout identity | The same current-profile relative path is repeated in four owners | **Defer; candidate consolidate locator.** Current exact-profile and checkout checks survive; final profile-policy owner remains Open | Est.: files 0; lines and literal call edges lower; concepts/config/compat 0. Audit actual all zero | Decide profile/application policy; prove packaging and checkout behavior; avoid a facade that merely forwards the literal |
| `ARCH-MODEL-COMP-07` | Maintained product code and policy/protection | Reporting boundary, resource policy, inspection, control and `Snakefile`; workflow, status, memory planning and tests | Closed report-kind roster, deterministic order, resources, transaction schemas and independent regeneration | Report kinds/count appear as a tuple, hard-coded `3`, workflow targets and validation assumptions across several owners | **Defer; candidate consolidate catalog.** Final catalog authority/package remains Open; reporting transactions retain semantic authority | Est.: files no growth; lines and repeated edges lower; concepts/config/compat 0. Audit actual all zero | Inventory all producers/consumers and dependency direction; avoid inspection/reporting cycle; prove order, memory, schema and regeneration parity |
| `ARCH-MODEL-COMP-08` | Wrapper/compatibility path and maintained product code | Dashboard plus control/inspection and Snakemake text producers; operators and dashboard tests | Safe non-authoritative live presentation, scheduler selection, bounded reads, and historical log support | Dashboard parses human plan stdout, Snakemake stderr and legacy `sample_concurrency` text instead of a structured projection | **Defer; candidate replace then retire parsers.** Structured read-model owner remains Open; inspection-derived non-authority survives | Est.: files no growth; lines, call edges and at least one compatibility parser lower; concepts/config 0. Audit actual all zero | Decide advanced status boundary and historical support window; migrate callers/tests; prove Local/Slurm distinction and bounded-read behavior |
| `ARCH-MODEL-COMP-09` | Maintained product code | CLI composition, control, onboarding, launcher and owner commands; users, wrappers, automation and tests | Owner-specific actionable diagnostics and stable exit contracts | Similar exception-to-public-error projection patterns recur, but exact equivalence and caller dependence are not yet proved | **Defer pending inventory.** Each current owner remains authority until a genuinely shared projection is proved | Est.: files no growth; lines and edges may decrease; concepts/config/compat 0. Audit actual all zero | Inventory exact messages, exception types, exit codes and machine consumers; retain owner-specific context and failure ceilings |
| `ARCH-MODEL-COMP-10` | Configuration/script/schema/documentation and compatibility | `configs/`, onboarding starter set, control/runtime/resource/launcher owners; scientists, operators, examples and tests | Scientific intent, site execution policy, inspectable defaults/sources, deterministic generated artifacts and compatibility | Twenty tracked config files and eight visible starter artifacts expose overlapping user, operator, generated, example and compatibility concerns without one classification | **Defer; classify then retain/consolidate/retire individually.** Existing owners survive until `CONFIG-01` and `OPS-01` decide authority | Est.: product files no growth; config files and public concepts lower; lines/edges likely lower; temporary compatibility path possible then retired. Audit actual all zero | Complete ownership/classification and external-caller review; preserve scientific visibility, safe override provenance and create-absent publication |
| `ARCH-MODEL-COMP-11` | Wrapper/compatibility path | Dashboard helper/parser; dashboard callers and tests plus historical plan/log readers | Scheduler-candidate selection and explicitly supported historical dashboard input | `scheduler_candidate_ids()` is a three-line compatibility view; legacy `sample_concurrency` parsing duplicates newer text interpretation | **Defer; candidate retire after support review.** Current dashboard behavior survives until a structured replacement and retirement condition exist | Est.: files no growth; lines lower; concepts/config 0; edges lower; at least one compatibility path retired. Audit actual all zero | Search external callers; define history window; migrate tests/consumers; prove scheduler safety and rollback route |
| `ARCH-MODEL-COMP-12` | Maintained product code and wrapper/compatibility path | `__main__.py` grouped composition and command adapters; all CLI users, automation, docs and public-contract tests | Stable public capability routing, arguments, exits and advanced escape hatches | A 711-line root composes ten top-level groups and interleaves ordinary/expert plumbing; duplication cannot be quantified before the public model is chosen | **Defer.** Current CLI remains authority; later migrate directly to selected owners and retire superseded routes without a permanent facade | Est.: files no growth; lines, concepts and call edges lower; config 0; temporary compatibility route only with owner/retirement. Audit actual all zero | Decide public nouns/capabilities; roster every caller; preserve exact contracts; prove parity before retiring old tree |
| `ARCH-MODEL-COMP-13` | Documentation and compatibility | Quickstart, orchestration, launcher and role-journey documentation; scientists, operators, maintainers and support | Canonical safety, recovery, advanced inspection and evidence-ceiling guidance | Manual directory creation, runtime-profile redirection and dry-run-root transfer recur across local and Slurm journeys | **Defer; candidate relocate unique facts and retire superseded journey text.** Final subject owners retain exact contracts | Est.: documentation files/lines, public concepts and compatibility journeys lower; product/config/call edges 0. Audit actual all zero | Implement accepted interface first; map every unique rule and inbound link; update/retire old journeys in the same bounded migration |
| `ARCH-MODEL-COMP-14` | Wrapper/compatibility path and protection | Resource policy and launcher configuration; CLI/config callers, packaging and migration tests | Fail closed on ambiguous retired `NORAD` filenames during rename compatibility | Equivalent legacy-filename guards occur in both owners | **Defer; candidate consolidate or retire only by migration policy.** Both guards survive until one final owner or proven end of support | Est.: files no growth; lines and duplicate edges lower; concepts/config 0; compatibility support unchanged until separately retired. Audit actual all zero | Decide rename/support policy; inventory distributions/callers; preserve rejection behavior; require explicit retirement evidence before deletion |

#### Open model options and decision order

A useful first question for the next bounded discussion—not a settled campaign
order—is:

> **Which changes create a new immutable Run, and which create only a new
> Attempt of the same Run?**

Three current options remain for explicit comparison:

| Option | Shape | Benefit | Cost or risk |
|---|---|---|---|
| **A — promote the normalized execution contract essentially as Run** | Workflow profile + scientific inputs/design/reference/policy form the Run; runtime/resources/executor/source remain Attempt facts | Smallest migration and strongest reuse of current canonical identity | Current identity is path-sensitive and omits effective execution choices, so the object may be less than the full plan users expect. |
| **B — include effective execution selection in Run** | Add selected runtime/executor/resources and possibly source realization to the immutable plan | Run becomes the complete accepted execution plan | Changes identity, storage, migration, reuse, and compatibility semantics; may conflate scientific intent with site execution. |
| **C — separate immutable scientific intent from immutable execution plan, with Run referencing both** | One admitted scientific definition plus one immutable effective realization compose Run; Attempt executes it | Clean distinction between science and realization and supports multiple execution plans | Adds concepts and risks locking the repository into an interim stack unless old representations retire in the same bounded migration. |

Whichever option is selected, mutable object state and canonical bytes cannot
be competing authorities. One **nonbinding candidate discussion order** is:

1. decide the Run-versus-Attempt change boundary;
2. decide the minimum public nouns, nesting, and cardinalities around Run;
3. decide exact Run fields, identity inputs, relocation behavior, and immutable
   in-memory/persisted representation;
4. decide Attempt/Result relationships and separate scientific, execution,
   reporting, and recovery status semantics;
5. decide persistence and storage relationships; then
6. select APIs, CLI mapping, execution-backend interfaces, policy boundaries,
   compatibility windows, and caller migration only where those decisions are
   required by a bounded implementation slice.

This list is not approved implementation sequencing. `AC-DEC-020` remains
Open, and the required decisions and their order must be reconsidered for each
bounded slice rather than used to pre-set the campaign.

The audit deliberately leaves every item above Open except Run's immutable-plan
meaning. It introduces no product code, command, API, class, schema, package,
backend, policy owner, persistence format, or evidence deletion.

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

Whatever it is called, a common operation representation must be able to
express, directly or by reference, stable owner identity; typed inputs and
outputs; explicit dependencies; runtime and resource needs; semantic
validation authority; failure behavior; provenance and trust requirements;
and report integration where applicable. These are representation obligations,
not approved fields or methods.

A common boundary must remove demonstrated repetition without becoming a
mandatory inheritance hierarchy, universal registry, generic workflow
language, abstract-factory tree, or second scheduler. Before selecting a common
denominator, `AC-SLICE-04` should paper-map a transformation owner, a scientific
analysis, an evidence owner, and reporting. One representative migration is a
candidate only after that mapping; generalization requires demonstrated net
reduction and evidence that a second distinct owner maps without distortion.
The exact mapping count and migration order remain unsettled.

`AC-SLICE-04` still decides the name and representation; operation granularity;
methods or fields; lifecycle vocabulary; input/output representation and schema
evolution; resource units, minima, defaults, precedence, and scheduler
translation; runtime/tool representation; extension discovery, installation,
trust admission, and version compatibility; and the representative owner and
generalization threshold.

### 8.3 Execution boundary

**Partially resolved:** supported backends owe one declared guarantee contract
covering scientific boundaries, artifact integrity, recovery, and evidence.
Mechanisms and environment-specific proof may differ.

One execution capability accepting a declared task and returning a structured
result, with Local and SLURM implementations, remains a concrete proposal.

Scientific work declares CPU, memory, wall time, inputs, outputs, and runtime
needs. Execution infrastructure owns process invocation, environment binding,
scheduler integration, allocation identity, exit state, logs, cleanup, and
recovery metadata.

The durable platform direction rejects building a second scheduler,
stage registry, scientific implementation, or recovery system. The source
reinforces that constraint. The open task must decide how the proposed
execution abstraction integrates appropriate workflow machinery and where its
supported backend boundary belongs; it does not reopen the no-second-scheduler
authority. `AC-SLICE-05` still decides granularity, request/result types,
backend selection, engine integration, resource vocabulary, job states,
retries, cleanup, and recovery mechanics. EMRYS's differentiator remains evidence-bound, provenance-aware
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

The taxonomy is open. Every policy decision has one declared final authority,
but that does not require a central policy layer. Repeated equivalent
owner-local decisions move to a shared authority only after inventory proves
real net reduction. `AC-INV-011` separately binds one declared admission chain
and final authority per artifact class or guarantee without creating one global
implementation or god object.

A functional owner either owns a policy decision or requests it from the
declared authority; it does not reimplement locking, rename, durability,
runtime, validation, publication, or resource semantics owned elsewhere. A
policy layer is justified only when it consolidates current repeated behavior;
generic wrappers that leave all old decisions in place do not satisfy the
campaign.

Still open are whether each proposed policy deserves an abstraction;
package/service placement; exact final owners, configuration inputs, return
types, and error models; defaults, safe override semantics, and precedence; and
consolidation order, compatibility behavior, and migration.

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

The exact states and generalized owner are open. `AC-INV-011` makes one declared admission chain and
final authority per artifact class or guarantee a binding target; it does not
claim that the generalized lifecycle exists or preselect its owner. Visible
provisional/failure state and mutation detection remain separately qualified in
the constitution.

Two sources also place a named **Artifact Store** between stages and reports.
That is a proposed boundary, not a selected service or directory. It could be a
logical API, a manifest-backed view, the owner of the canonical artifact
lifecycle, or a physical collection. Its relationship to application
coordination around Run, the Run Bundle, filesystem layout, external or large
artifacts, scientist-facing results, and reporting remains open. A
source-proposed constraint is that it not
become a second artifact authority beside an accepted lifecycle owner;
`AC-DEC-025` preserves the boundary choice and must apply binding
`AC-INV-011` rather than reopening the one-authority requirement.

Still open are artifact classes and lifecycle vocabulary; one generalized
lifecycle owner versus class-specific owners; admission/publication APIs,
schemas, manifests, and receipts; physical layout, immutability mechanisms, and
external or large-artifact handling; Run Bundle and report-derived-artifact
relationships; and rollback, cleanup, recovery, and representative migration.

### 8.6 Ratified and open abstraction guardrails

The binding constitution now requires operational mechanics to remain
encapsulatable while review-relevant science stays visible; one final authority
per artifact class or guarantee without a god object; bounded migration with
caller migration, parity, owned temporary compatibility, and eventual
retirement; and mapped equal-or-stronger protection before direct-owner,
adversarial, seeded-fault, or synthetic end-to-end defenses are removed. The
replacement defense may already survive elsewhere; removing redundancy does
not require creating a duplicate test. Evidence levels remain distinct, so
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

| Runtime mode | Intent | Proposed surface |
|---|---|---|
| Managed | Use an EMRYS-provided reproducible container or environment | `emrys runtime install` or an explicitly selected managed mode |
| Site | Discover and select institution-provided modules and tools | `emrys runtime discover`, then `accept` |
| Explicit | Supply advanced tool paths and identities | `emrys runtime define ...` |

Runtime discovery should inspect at least Python/EMRYS, the active workflow
engine (currently Snakemake where the selected path depends on it), STAR,
samtools, GATK, Picard, bcftools, RSeQC, R, Java, and the relevant R environment,
then present versions and readiness before selection. Snakemake remains an
internal execution dependency, not a scientific authority or a configuration
surface ordinary scientists must author.

Execution profiles are a different axis. Proposed profiles include `local`,
`cluster`, `cluster-debug`, `development`, and `production`. A profile may bind
backend, resources, storage, and runtime selection. The exact profile taxonomy
is open.

Containerization is an independent architecture decision, not part of guided
setup. A managed image could contain Python, Snakemake, scientific tools, R,
and the restored R environment, with its digest recorded in run provenance.
Native/site execution remains necessary as an escape hatch. Licensing,
architecture, scheduler, storage, security, update, and reproducibility
requirements require a separate decision.

### 9.2 Transparent execution

Ordinary users should be able to request a run without operating a SLURM
wrapper or selecting submission mechanics. EMRYS may choose an admitted default
from the execution profile, while an advanced user can explicitly select or
inspect the backend. Automatic local-versus-SLURM selection versus explicit
profile selection remains open.

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

The golden path is a **binding capability set and successful end state**. Its
exact command names, command partitioning, ordering, and whether the synthetic
path is called “demo” are open.

The intake supplied three materially different nonbinding sequences:

```text
AC-SRC-001: init -> check -> run -> reports
AC-SRC-002: repository -> doctor -> demo -> init -> run -> report
AC-SRC-003: install -> Doctor -> Demo -> Configure -> Run -> Inspect result
```

In particular, the sources do not settle whether neutral synthetic execution
precedes project creation, uses a generated project, or follows project setup.
`AC-DEC-024` preserves that choice. The required capabilities, shown without
selecting an order, are:

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

The exact layout is open. The desired abstraction is a portable, coherent
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
- A collaborator-extensible analysis library may support differential or other
  analyses through typed inputs/outputs, provenance, validation, trust level,
  resources, failure semantics, and report integration.
- The proposal that scientific modules should not require editing unrelated
  owners or turn EMRYS into a generic workflow framework remains an exact
  module-design choice for `ANALYSIS-02` and `ARCH-01`.
- The algorithms, parameters, assumptions, interpretation boundaries, and
  implementation needed for scientific review must remain recognizable and
  inspectable under binding `AC-GUARD-002`; the exact module API and placement
  remain open.

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
5. Consolidate shared policy, execution, artifact, and lifecycle authorities
   one bounded package at a time.
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
- estimated and then actual change in files, lines, public concepts,
  configuration artifacts, call edges, and compatibility paths; and
- preconditions, including caller migration, parity, evidence review,
  retirement condition, and any explicit approval required.

The same audit inventories mutable state, its owner, lifetime, readers and
writers, why mutation is necessary, and whether it can become an immutable
boundary value. Draft construction and tightly owned attempt, lock, log, or
transaction state may remain mutable when justified. A Run is never mutable. The
audit records facts and options; it does not settle nouns, nesting, APIs,
backends, policies, persistence, or other application-model choices beyond the
binding Run decision.

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

No category offsets another. Deleting tests, documentation, configuration, or
evidence cannot make product growth appear net-negative. Generated files,
runtime environments, vendored bulk, and moving logic into configuration do
not count as maintained-source reduction. File and line counts are secondary
signals: a god module, denser code, hidden generated logic, weakened protection,
or an extra facade beside the old authority fails the compression requirement
even if counts decline. Temporary growth remains growth until its owner,
retirement condition, and removal are recorded.

Protection retirement follows `AC-GUARD-005`: the slice maps the invariant and
shows the equal-or-stronger defense that survives, which need not be newly
created. Evidence retirement follows a separate gate. The proposal must name
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

This resolves only the `LOG-05` migration boundary within `AC-DEC-020`. It does
not settle any other campaign ordering or interface decision.

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

| Decision ID | Open question | Retained options or concerns |
|---|---|---|
| `AC-DEC-001` | What is the canonical public identity vocabulary and nesting around Run? | `Run` is already reserved for the immutable plan. Whether it is public and how Project, Analysis, Attempt, Result, and artifacts are named, exposed, and nested remain post-audit decisions; current `run_id` and run-root terminology are not thereby reinterpreted. |
| `AC-DEC-002` | Which names form the stable public CLI? | setup/init, validate/check/doctor, status/resume, config, inspect/explain/debug |
| `AC-DEC-003` | How are Doctor diagnosis and repair divided? | default read-only diagnosis plus explicit `--fix`, dedicated repair command, or setup-owned mutations; repair provenance and safety |
| `AC-DEC-004` | What is the user-authored scientific schema? | project.yaml versus analysis.yaml; embedded samples versus TSV; configuration evolution |
| `AC-DEC-005` | What are the exact merge semantics within the ratified inspectable effective-value model? | Exact defaults/site/project/CLI order and list/map/null semantics; every effective value and source remains inspectable, and only owner-defined safe values are overrideable |
| `AC-DEC-006` | How are runtime and execution choices represented? | Managed/Site/Explicit runtimes; local/cluster profiles; explicit versus automatic backend selection. External mechanisms remain behind owned boundaries and supported backends owe equivalent declared guarantees. |
| `AC-DEC-007` | Is a supported managed container/environment accepted? | Scheduler, storage, architecture, security, licensing, updates, native escape hatch, image and tool provenance |
| `AC-DEC-008` | What is the minimum useful operation/Stage representation? | Name, methods, lifecycle states, typed contracts, granularity, discovery, and migration. The boundary is already constrained to remain thin, preserve functional/scientific ownership, and avoid a generic framework. |
| `AC-DEC-009` | Which repeated policy decisions deserve shared authorities? | Inventory input, validation, runtime, storage, publication, resource, and execution decisions; decide final authorities, package/service placement, configuration inputs, return/error contracts, defaults, safe overrides, precedence, compatibility, consolidation order, and migration. Every decision already requires one authority, but shared centralization must prove net reduction and avoid empty wrappers. |
| `AC-DEC-010` | What artifact-lifecycle vocabulary and owner shape are justified? | Candidate, validation, admission, publication, commit, immutability, evidence, and rollback; generalized versus class-specific ownership; APIs, schemas, manifests, receipts, immutability mechanisms, external/large artifacts, Run Bundle/report-derived relationships, cleanup, recovery, and representative migration. Lifecycle/admission is already distinct from physical storage. |
| `AC-DEC-011` | Which changes create a new immutable Run rather than a new Attempt, and what concrete model belongs in application coordination? | `ARCH-MODEL-AUDIT-01` retains three options: promote the normalized execution contract essentially as Run; add effective execution selection/resources to Run; or compose Run from separate immutable scientific-intent and execution-plan records. Exact fields, relocation behavior, identity/configuration/execution/status/artifact/evidence/report views, persistence, and API remain Open. Current initial execution creates a run skeleton before exact attempt-preparation admission, so the selected model must also assign recovery ownership for an unreceipted skeleton. Mutable object state and canonical bytes cannot become competing authorities; coordination cannot absorb lower authorities or become a god object. |
| `AC-DEC-012` | What public Run, Attempt, scientific, and reporting states are useful and truthful? | Current `RunInspection` states and attempt-receipt statuses are Observed implementation vocabulary only. Current `local_pipeline_complete` requires reporting, contrary to accepted downstream-reporting semantics. Pending/running/complete/failed/recoverable and representation of partial or blocked states remain options; scientific and reporting outcomes must remain distinguishable. |
| `AC-DEC-013` | What is the Run Bundle contract? | Layout, portability, large artifacts, external references, redaction, archival, regeneration, sharing |
| `AC-DEC-014` | How are the ratified downstream-reporting semantics represented? | The current lifecycle conflates report completion with `local_pipeline_complete`; standalone regeneration exists but requires low-level roots and does not adopt or repair the orchestration reporting ledger. Exact opt-out/regeneration interfaces, persisted Run/report states, retry/resume and exit presentation, scientific/evidence/operations commands or views, one shared receipt-last transaction versus profile-specific receipts, immutable artifacts versus derived views, and canonical location remain Open. Reporting is already downstream, invoked by default for a full run, able to be disabled, and independently regenerable without invalidating science. |
| `AC-DEC-015` | What replaces the current “demo” surface? | Neutral synthetic golden path; whether “demo” remains a command, test-only term, or is retired completely |
| `AC-DEC-016` | Which filesystem concepts are public? | Project/inputs/runs/results/runtime; exact internal-to-public mapping |
| `AC-DEC-017` | Which advanced interfaces are stable? | inspect run/artifact, manifest, evidence, diagnostics, debug, machine-readable outputs |
| `AC-DEC-018` | How is each bounded compatibility and retirement transition implemented? | Compatibility window, warnings, fixtures, and removal evidence; caller migration, relevant parity, owned temporary compatibility, and eventual retirement are already binding. Evidence deletion remains separately approval-gated. |
| `AC-DEC-019` | Which campaign metrics and targets become commitments? | Reproducible UX and operational baselines; separate product, protection, configuration/documentation, and retained-evidence methods; supported environment; time targets; coverage-rebase interpretation; qualitative acceptance. Per-slice accounting is already binding. |
| `AC-DEC-020` | How should work beyond the accepted `LOG-05` migration boundary, compression opportunities, and any just-in-time facade use be ordered? | Three source phase models and P0–P3 suggestion; per-slice facade need; compression and retirement opportunities from each audit; later importance and complexity scores. The audit must precede selection; Section 13.3 settles only logging adoption sequencing. |
| `AC-DEC-021` | Which new architecture documents should remain after the campaign? | Invariants, current architecture, target architecture, or consolidation into existing durable owners |
| `AC-DEC-022` | How should the Steps 07–09 audit be bounded? | Review authority, candidate universe, count/CMH/BH contracts, oracle data, evidence ceiling |
| `AC-DEC-023` | Which historical claims from the source are accurate and useful? | Development dates, chronology, and repository-history interpretations require live Git verification before reuse |
| `AC-DEC-024` | What is the canonical golden-path capability order? | `init -> check -> run`; repository/doctor/demo/init/run/report; Install/Doctor/Demo/Configure/Run/Inspect; placement of synthetic execution relative to project creation; interactive and automation journeys |
| `AC-DEC-025` | Is Artifact Store a distinct boundary, and what does it own? | Logical API, manifest-backed view, lifecycle owner, or physical collection; relationship to Run, Run Bundle, filesystem, external/large artifacts, immutability mechanisms, results, and report-derived artifacts. Artifact capability does not imply a Store, and storage cannot become a second admission/completion authority. |

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
| `AC-SUG-015` | The exact `Artifact Store` name and the source diagrams that place it between stages and reports; boundary type and ownership remain open |

## 16. Candidate slicing ledger

These began as candidate work slices, not final backlog IDs, priority, or
implementation authorization. `AC-SLICE-01` is complete as the bounded
`ARCH-CONST-01` decision/audit slice, and `AC-SLICE-02` is complete as
`ARCH-LAYER-01`. The read-only owner/caller, representation, identity,
mutation, protection/evidence, and compression prerequisite is complete as
`ARCH-MODEL-AUDIT-01`; `AC-SLICE-03` remains Open under the approved recording
boundary, and model selection/introduction are separate future work. Every
later candidate still requires its own bounded owner/caller review,
compression register, mutation inventory, non-goals, acceptance conditions,
protection disposition, and evidence ceiling before entering the matrix. A
promoted implementation card also requires the category-separated closeout
defined in Section 13.1; evidence deletion cannot be implied by promotion.

| Candidate | Observable outcome | Likely relationship to current matrix |
|---|---|---|
| `AC-SLICE-01` | Ratified all 27 architectural invariants and five migration/test guardrails against live contracts and representative tests | Completed as `ARCH-CONST-01`; broad `ARCH-01` remains Open |
| `AC-SLICE-02` | Ratified responsibility clusters, three separate dependency graphs, forbidden authority transfers, a current-owner crosswalk, and a fast Python source-boundary ratchet for exact CLI seams and transitional imports | Completed as `ARCH-LAYER-01`; broad `ARCH-01` remains Open |
| `AC-SLICE-03` | Audit current user-intent, plan, identity, attempt, result, mutation, persistence, API, owner, caller, protection, evidence, and compression representations; record facts and options without selecting anything beyond `Run` as the immutable plan | Current-state prerequisite recorded as completed `ARCH-MODEL-AUDIT-01`; this campaign card remains Open per the approved boundary, and model selection/implementation require later discussion and separate approval |
| `AC-SLICE-04` | Decide whether a shared thin operation representation is justified and, if so, define the minimum boundary and prove it through one representative migration only after the mapping test passes | New slice; coordinate with `ANALYSIS-02` and `ARCH-01` |
| `AC-SLICE-05` | Ratify the execution guarantee contract, select the minimum justified capability boundary, and prove equivalent declared guarantees across supported local and SLURM backends | New slice; enriches `OPS-02` |
| `AC-SLICE-06` | Inventory duplicated policy decisions, declare their final authorities, and centralize only a selected repeated decision whose migration proves net reduction | New per-policy slices after inventory; supports `ARCH-01` |
| `AC-SLICE-07` | Define artifact-class lifecycle/admission requirements, decide whether any shared lifecycle or distinct Artifact Store is justified, and migrate one path only if the selected design requires a boundary change | New slice; supports `ARCH-01` |
| `AC-SLICE-08` | Define named execution profiles independently of Managed/Site/Explicit runtime modes | New slice; coordinates with `OPS-01` and `RUNTIME-01` |
| `AC-SLICE-09` | Provide expert explain/inspect interfaces for effective plan, run, artifact, and evidence | New slice or expansion of `OPS-02`/`CONTROL-01` |
| `AC-SLICE-10` | Define high-level status and safe resume/recovery UX over existing fail-closed internals | New slice; coordinates with `OBS-02` |
| `AC-SLICE-11` | Define a portable canonical Run Bundle contract | New slice; coordinates with `FILESYSTEM-01` and `RESULTS-01` |
| `AC-SLICE-12` | Formalize scientific, evidence, and operational report purposes and navigation | New slice or expansion of `REPORT-03` and `RESULTS-01` |
| `AC-SLICE-13` | Deliver a supported fresh-install-to-valid-synthetic-result golden path after ratifying its capability order | New cross-cutting outcome; coordinates with setup, runtime, Doctor, run, results, and `CLEAN-01` |
| `AC-SLICE-14` | Establish reproducible UX, operational, and separate product/protection/configuration-documentation/retained-evidence baselines and ratify their interpretation methods and campaign success measures | New aggregate-measurement slice; per-slice accounting starts immediately and coordinates with `REVIEW-UX-03` and `ARCH-01` |
| `AC-SLICE-15` | Audit the Steps 07–09 statistical contract | New scientific-review slice; not architecture evidence |
| `AC-SLICE-16` | Build independent numerical oracles for Steps 08 and 09 | New scientific-validation slice |
| `AC-SLICE-17` | Retire duplicated lifecycle, validator, infrastructure, adapter, or compatibility paths after each replacement is proven; classify dual-purpose fixtures, goldens, logs, receipts, reports, and dated records before deletion | Multiple bounded deletion slices; never one unbounded cleanup task, and exact evidence deletion requires separate user approval and commit |
| `AC-SLICE-18` | Rewrite navigation and documentation around scientist/operator/developer journeys | Expansion or slicing of `DOC-01`; use the accepted `DOC-02`/`DOC-03` traces and coordinate with `DOC-04`–`DOC-05` retirements |
| `AC-SLICE-19` | Define Doctor repair ownership, supported mutations, preview/reporting, and safety contracts | Expansion of `DOCTOR-01` reflecting the explicit override |

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
| `CONTROL-01` | Audit-first compact application model and progressive disclosure. `Run` is the immutable plan; whether it is public, the explicit Run-versus-Attempt change boundary, and every other noun, nesting, identity, cardinality, API, persistence, and storage choice remain post-audit decisions. Generated internals remain inspectable. |
| `CONFIG-01` | Scientific versus execution versus evidence ownership; one scientist-facing definition; generated normalized artifacts; schema alternatives remain open |
| `OPS-01` | Small operator-configuration surface; every effective value and source is inspectable and only explicitly safe owner-defined values are overrideable; exact interfaces, merge semantics, and named-profile model remain open |
| `OPS-02` | Small role-aware CLI with the required capabilities; command partitioning/order, scheduler-selection behavior, and stable advanced inspection/override/debug routes remain open |
| `OPS-03` | Inline/generated program inventory, extraction of substantive reusable logic, and removal of operator dependence on helper scripts |
| `OPS-04` | Replace “local pilot” with a domain name that remains accurate beyond one execution context |
| `SETUP-01` | Generate structural input manifests while refusing to invent pairing, strata, conditions, cohorts, or other biological meaning |
| `SETUP-02` | Portable setup-adjacent benchmarking with advisory, evidence-bound recommendations |
| `SETUP-03` | Guided project creation, safe owned directories, generated configuration, validation, and no secret or biological invention; not containerization |
| `RUNTIME-01` | Tiered runtime provisioning and admission; Managed/Site/Explicit are proposed labels; complete qualification includes the active internal workflow engine/Snakemake where applicable and remains separate from execution profiles |
| `DOCTOR-01` | Project-aware readiness capabilities, actionable failures, qualified internal workflow-engine dependency, debug escape hatch, and the explicit-repair override with bounded mutation rules; exact command partitioning remains open |
| `RUN-03` | Preserve `Run` as the immutable plan while eliminating run-root copying; the one-command validate/plan/confirm/execute interaction and exact ordering remain proposals, and execution/attempt state cannot mutate Run |
| `IDENTITY-01` | Ratify the smallest role-appropriate identity model while preserving detailed identities as evidence metadata; Run/Attempt nesting remains illustrative |
| `FILESYSTEM-01` | Automatic predictable directory creation, one discoverable result surface, and no hidden report root; Project/inputs/runs and Run-Bundle layouts remain proposed |
| `CONTAINER-01` | Independent managed-container/environment decision without assuming final runtime labels; institutional/native/advanced coexistence, image contents and digest, scheduler/storage/security/licensing/update contracts |
| `REVIEW-UX-03` | Scientist, advanced scientist, operator, automation, and developer journeys; progressive disclosure; cognitive-load and golden-path baseline |
| `LOG-03` | Durable complete attempt logging remains infrastructure while concise output becomes the default role-appropriate surface |
| `LOG-05` | Scientific milestone language, actionable failures, and normal-command adoption |
| `OBS-01` | Remove engine, owner, transaction, and low-value noise from the primary view while retaining durable detail |
| `OBS-02` | High-level scientific progress, public run status, elapsed time, completion/failure, and links to recovery/inspection |
| `ANALYSIS-01` | Stop/reuse through the Step 06 boundary and launch separately identified cohort, subset, sensitivity, or downstream work |
| `ANALYSIS-02` | Collaborator-extensible modules with typed scientific contracts; scientific algorithms, assumptions, interpretation, and review-relevant implementation remain visible. The lightweight extension mechanism is open within the binding prohibition on a mandatory universal Stage hierarchy, registry, workflow language, or second scheduler |
| `ARCH-01` | Consumes the completed invariant constitution, responsibility/dependency model, and `ARCH-MODEL-AUDIT-01` current application-model/compression baseline. Every slice performs the owner/caller/compression/mutation audit and category-separated closeout in Section 13.1. Run means the immutable plan; concrete application, operation, execution, policy, identity, and artifact APIs; individual authority migrations; Artifact Store decision; package realization; and facade use remain post-audit choices. Bounded migration, default net-negative maintained product code with no product-file growth, immutable-by-default boundaries, eventual retirement, equal-or-stronger mapped protection, and separate approval for exact evidence deletion are binding. |
| `REPORT-03` | Primary-scientific-findings hierarchy with evidence and operational detail progressively disclosed |
| `REPORT-04` | Preserve the requested ability to render nine A-through-I selections when the admitted result warrants them |
| `RESULTS-01` | One discoverable results surface and coordination with the proposed Run Bundle and Artifact Store concepts without preselecting their ownership or layouts |
| `DOC-01` | Role- and journey-based scientist/operator/developer documentation that does not assume campaign history |
| `DOC-02` | Completed repository-wide documentation disposition and authority cutover; bounded migration and retirement now remain under completed `DOC-03`, open `DOC-04`–`DOC-05`, `CLEAN-01`, and `CLEAN-02` |
| `DOC-03` | Completed source reconciliation and retirement of the stale future-architecture, pipeline-plan, question-index, and future-diagram surfaces without settling the final architecture-document set; the [durable trace](../design/decisions/repository-and-delivery.md#doc-03-source-to-destination-trace-2026-08-25) lives in the repository-and-delivery decision record |
| `DOC-04` | Reconcile every handoff section, preserve unique dated evidence and durable recovery facts without promotion, discard blocker/takeover prose, and retire the rolling handoff |
| `DOC-05` | Consolidate useful orchestration-admission and launcher safeguards into live owners, discard stale transcripts, and retire both transition sources |
| `BACKLOG-01` | Matrix cutover remains a discrete task; this campaign does not silently create another permanent backlog authority |
| `DOC-TOOL-01` | Preserve useful documentation validation in a correctly named owner while removing obsolete task-registry coupling |
| `TOOLING-01` | Verify the now-empty generic Git-orchestration namespace against history and callers, then guard its retired paths from returning |
| `CLEAN-01` | Retire the old demo product surface without losing a neutral synthetic golden path and its validation value; final terminology is open |
| `CLEAN-02` | Reconcile the obsolete pending Step 04 scaffold against the active owner test, then retire the duplicate test-planning surface |
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
| `AC-IN-005` | Override the categorical non-mutating Doctor requirement | Binding repair posture recorded in Sections 3 and 9; exact interface remains open |
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

### 18.4 Duplicate policy

The three attachments express the same central thesis at different levels of
detail. They are **overlapping sources**, not disposable duplicates:

- recurrence increases confidence that a concern was intentional and central;
- repeated wording is consolidated once in the narrative;
- unique examples, alternative commands, abstraction variants, sequences,
  metrics, and diagrams remain represented;
- agreement among the sources does not convert a suggestion into a decision;
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
