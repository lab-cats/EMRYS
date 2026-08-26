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

This document uses four decision labels:

- **Binding:** a requirement the user has explicitly made non-negotiable.
- **Invariant candidate:** a guarantee that must be formalized and checked
  against the live implementation before it becomes authoritative wording.
- **Proposed:** a concrete design suggestion retained for evaluation.
- **Open:** a decision that has deliberately not been made.

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
| Artifact integrity and transactional publication | Preserve; centralize behind one lifecycle |
| Runtime and storage qualification | Preserve; encapsulate behind profiles and diagnosis |
| HPC and scheduler mechanics | Preserve; strongly hide from the primary control plane |
| Repeated validators and lifecycle implementations | Consolidate, then remove superseded paths |
| Stage-specific infrastructure logic | Move to infrastructure owners |
| Low-level operational configuration | Place behind profiles and explicit advanced interfaces |
| Internal state machine | Retain internally; expose a smaller run-state vocabulary |

The success measure is not necessarily fewer lines or files. It is fewer
independent places where the same guarantee can be implemented differently,
and fewer internal concepts required before a user can obtain a valid result.

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
   ownership, anti-framework, and retirement guardrails require ratification
   against live behavior and contracts.
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

The sources also recommend five strong campaign guardrails that remain
**proposed pending explicit ratification**:

- experienced operators can inspect and deliberately override every supported
  operational decision without modifying source;
- abstractions hide operational mechanics without burying scientific
  algorithms, parameters, assumptions, or interpretation;
- migration is incremental rather than an unbounded rewrite; and
- adopted facades and shared owners eventually retire their superseded paths
  instead of creating permanent parallel architecture; and
- adversarial testing and synthetic end-to-end regression coverage are
  preserved or replaced only by equal-or-stronger defenses, with evidence
  ceilings distinct from the scientist-facing synthetic golden path.

## 4. Invariant constitution to formalize

An early campaign deliverable should establish an authoritative architectural
constitution. The statements below are **invariant candidates** derived from
the intake, not a claim that their exact wording already matches every live
contract. Ratification requires source and test review.

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

The binding outcome is a small vocabulary. Whether `Project` and `Analysis`
are distinct public identities, aliases, or nested concepts is open.

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

The proposed layering is:

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

The binding dependency rule is:

> Higher layers may request capabilities from lower layers. Lower layers must
> not depend on higher-level user workflows.

Consequences include:

- scientific stages do not implement scheduler, runtime, storage, or
  transaction behavior;
- reporting does not implement artifact publication or mutate run state;
- validators do not implement runtime discovery;
- CLI code does not implement scientific semantics;
- stages do not independently reinvent provenance or evidence;
- infrastructure does not need to understand scientific report presentation;
- Snakemake remains an execution mechanism, not scientific or application
  authority and not a required user concept.

One source summarized the desired internal conceptual consolidation as:

```text
Domain -> Stage -> Run
```

Here, Domain is visible scientific logic; Stage is a thin operational boundary;
and Run is global coordination. This is a proposed model whose exact mapping to
current functional owners must be established by inventory rather than assumed.

## 8. Proposed abstractions and guardrails

### 8.1 Project and Run application boundaries

**Proposed:** `Project` owns stable scientific intent, references, inputs,
design, and selectable execution policy. `Run` owns one immutable effective
configuration and coordinates identity, execution, artifacts, evidence, status,
and reports.

Subsystems should receive a Run context rather than independently reconstructing
run identity or reading unrelated configuration files. `Run` must remain a
coordinator, not a god object containing scientific and infrastructure
implementations.

### 8.2 Thin Stage boundary

A proposed Stage contract is conceptually:

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

Potential recognizable stages include alignment, canonical BAM creation, QC,
orientation, duplicate handling, SplitNCigar, orientation partitioning,
mpileup, candidate selection, CMH, context, and reporting. The intake also
suggested a common lifecycle:

```text
admit -> plan -> execute -> validate -> publish -> record
```

Both the API and lifecycle vocabulary are proposed. A task selecting this model
must ratify whether one thin boundary is the right owner for repeated
operational mechanics and how scientific implementations remain reviewable.
The source further proposes rejecting a generic workflow framework or hierarchy
of abstract factories; that anti-framework guardrail remains pending
ratification.

### 8.3 Execution boundary

**Proposed:** one execution capability accepts a declared task and returns a
structured execution result, with Local and SLURM implementations and room for
future supported backends.

Scientific work declares CPU, memory, wall time, inputs, outputs, and runtime
needs. Execution infrastructure owns process invocation, environment binding,
scheduler integration, allocation identity, exit state, logs, cleanup, and
recovery metadata.

The source proposes that this abstraction use appropriate workflow machinery
rather than building a second scheduler. The task must explicitly ratify that
anti-second-engine guardrail and its boundary. The proposed rationale is that
EMRYS's differentiator is evidence-bound, provenance-aware scientific analysis
with strong execution guarantees—not a new generic workflow engine.

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

The taxonomy is open. A proposed abstraction guardrail, pending explicit
ratification, is:

> One invariant has one final implementation authority.

A stage requests a policy decision rather than reimplementing locking, rename,
durability, runtime, validation, publication, or resource semantics. A policy
layer is justified only when it consolidates current repeated behavior; generic
wrappers that leave all old decisions in place do not satisfy the campaign.

### 8.5 Canonical artifact lifecycle

**Proposed:** artifact identity, validation, admission, publication,
immutability, and evidence become phases of one coherent lifecycle:

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

The exact states are open. The proposed property is one canonical path for
creating a durable artifact, with visible provisional and failure states and no
silent mutation; ratification must reconcile it with live artifact contracts.

Two sources also place a named **Artifact Store** between stages and reports.
That is a proposed boundary, not a selected service or directory. It could be a
logical API, a manifest-backed view, the owner of the canonical artifact
lifecycle, or a physical collection. Its relationship to Run coordination, the
Run Bundle, filesystem layout, external or large artifacts, scientist-facing
results, and reporting remains open. A source-proposed constraint is that it not
become a second artifact authority beside an accepted lifecycle owner;
`AC-DEC-025` preserves that constraint for ratification with the boundary.

### 8.6 Abstraction guardrails

These source-proposed guardrails require explicit ratification with the
applicable live contracts:

- Hide execution, filesystem, provenance, scheduler, and transaction mechanics.
- Keep scientific algorithms, statistical assumptions, and biological meaning
  visible.
- Introduce facades around proven behavior before changing behavior.
- Do not add a second authority beside the current one and call that
  consolidation.
- Pair every adopted abstraction with a caller migration and eventual deletion
  package for superseded paths.
- Preserve adversarial tests, direct tests, and seeded fault cases for the
  invariant being moved.
- Preserve synthetic end-to-end regression coverage independently of the
  user-facing synthetic golden path; neither proves cluster, production,
  scientific-review, or biological readiness.
- Reject generic framework work that is not required by an identified EMRYS
  lifecycle or policy duplication.

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
run-relative results surface. Report regeneration semantics and whether reports
are immutable artifacts, derived views, or both remain open.

The sources also disagree about lifecycle ownership: one proposal includes a
`ReportStage` within the run lifecycle, while another makes Report a downstream
consumer of a completed Run so reporting cannot become workflow state.
`AC-DEC-014` preserves this choice for explicit resolution. Future profile
design must also decide whether multiple audience views share one receipt-last
publication transaction or publish profile-specific receipts; neither topology
is accepted yet.

## 12. Scientific modularity and audit boundary

Operational simplification must not distract from scientific architecture.

- Compatible per-sample work through Step 06 should be reusable for separately
  identified cohort, subset, sensitivity, or downstream analyses beginning at
  the cohort-dependent boundary.
- A collaborator-extensible analysis library may support differential or other
  analyses through typed inputs/outputs, provenance, validation, trust level,
  resources, failure semantics, and report integration.
- Proposed guardrail: scientific modules should not require editing unrelated
  owners or turn EMRYS into a generic workflow framework; the module task must
  ratify this boundary.
- Proposed guardrail: the specific R/shell/Python scientific implementation and
  its assumptions should remain reviewable within the operational boundary;
  the task must ratify what visibility is required.

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

The leading source proposal is a facade-first, invariant-preserving,
incremental, deletion-complete strategy:

1. Inventory live owners, callers, state transitions, artifact paths,
   execution paths, duplicated policies, and user-authored configuration.
2. Ratify the architectural invariants against current contracts and tests.
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

Under this proposal, “introduce an abstraction” is not completion. A package
would close only when its callers use the intended owner, old paths have
explicit dispositions, protected behavior and evidence remain intact, and
maintained surface is reduced or one final owner is established. The exact
migration and deletion policy remains open under `AC-DEC-018` and
`AC-DEC-020`.

### 13.1 Nonbinding sequencing proposals from the sources

The sources suggested several useful but different sequences. None is adopted
by this document.

| Source proposal | Suggested sequence |
|---|---|
| UX-first seven phases | UX wrapper; unified scientific configuration; runtime abstraction; Stage abstraction; simplified identities; Steps 08/09 numerical validation; role-based documentation |
| Facade-first six phases | Freeze invariants; introduce Project/Run/Artifact/Execution/Report facades; move CLI; consolidate implementations; mark internals as operator/developer APIs; measure |
| Detailed nine phases | Inventory; domain objects; policy consolidation; execution abstraction; Run coordination; high-level CLI; profiles; deletion; journey-first documentation |

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

## 14. Measurement plan

Measurement is required so the campaign does not merely move complexity.
Baselines should be captured before targets are ratified.

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
- Number of modules that understand internal Run state
- Number of compatibility/migration paths after their supported window
- Net maintained surface and call-edge change for each consolidation package

The source suggested **under 30 minutes** for a supported local synthetic run
and **under one hour** in a prepared HPC environment. These are useful candidate
targets, not accepted commitments. Hardware, installation boundary, cache
state, dataset size, scheduler wait, and “prepared environment” must be defined
before any time target becomes normative.

## 15. Open decision register

| Decision ID | Open question | Retained options or concerns |
|---|---|---|
| `AC-DEC-001` | What is the canonical public identity vocabulary? | Project, Analysis, or both; Run and Result nesting |
| `AC-DEC-002` | Which names form the stable public CLI? | setup/init, validate/check/doctor, status/resume, config, inspect/explain/debug |
| `AC-DEC-003` | How are Doctor diagnosis and repair divided? | default read-only diagnosis plus explicit `--fix`, dedicated repair command, or setup-owned mutations; repair provenance and safety |
| `AC-DEC-004` | What is the user-authored scientific schema? | project.yaml versus analysis.yaml; embedded samples versus TSV; configuration evolution |
| `AC-DEC-005` | How are effective values merged? | defaults, site/execution profile, project request, and CLI override precedence; list/map/null semantics |
| `AC-DEC-006` | How are runtime and execution choices represented? | Managed/Site/Explicit runtimes; local/cluster profiles; explicit versus automatic backend selection |
| `AC-DEC-007` | Is a supported managed container/environment accepted? | Scheduler, storage, architecture, security, licensing, updates, native escape hatch, image and tool provenance |
| `AC-DEC-008` | What is the minimum useful Stage boundary? | Methods, lifecycle states, typed contracts, current-owner mapping, avoiding a generic framework |
| `AC-DEC-009` | Which shared policies deserve explicit owners? | Input, validation, runtime, storage, publication, resource, execution; avoid empty wrappers |
| `AC-DEC-010` | What is the canonical artifact lifecycle vocabulary? | Candidate, validation, admission, publication, commit, immutability, evidence, rollback |
| `AC-DEC-011` | What belongs in Run coordination? | Identity, configuration, execution, status, artifacts, evidence, reports; avoid a god object |
| `AC-DEC-012` | What public run states are useful and truthful? | Pending/running/complete/failed/recoverable and representation of partial or blocked states |
| `AC-DEC-013` | What is the Run Bundle contract? | Layout, portability, large artifacts, external references, redaction, archival, regeneration, sharing |
| `AC-DEC-014` | What are report lifecycle semantics? | `ReportStage` inside the run lifecycle versus Report as a downstream consumer of a completed Run; automatic generation versus explicit regeneration; scientific/evidence/operations commands or views; one shared receipt-last transaction versus profile-specific receipts; immutable artifacts versus derived views; canonical location |
| `AC-DEC-015` | What replaces the current “demo” surface? | Neutral synthetic golden path; whether “demo” remains a command, test-only term, or is retired completely |
| `AC-DEC-016` | Which filesystem concepts are public? | Project/inputs/runs/results/runtime; exact internal-to-public mapping |
| `AC-DEC-017` | Which advanced interfaces are stable? | inspect run/artifact, manifest, evidence, diagnostics, debug, machine-readable outputs |
| `AC-DEC-018` | What deprecation and deletion policy applies? | Compatibility window, caller migration, warnings, fixtures, removal evidence |
| `AC-DEC-019` | Which campaign metrics and targets become commitments? | Baseline method, supported environment, time targets, qualitative acceptance |
| `AC-DEC-020` | How should work be ordered? | Three source phase models and P0–P3 suggestion; later importance and complexity scores |
| `AC-DEC-021` | Which new architecture documents should remain after the campaign? | Invariants, current architecture, target architecture, or consolidation into existing durable owners |
| `AC-DEC-022` | How should the Steps 07–09 audit be bounded? | Review authority, candidate universe, count/CMH/BH contracts, oracle data, evidence ceiling |
| `AC-DEC-023` | Which historical claims from the source are accurate and useful? | Development dates, chronology, and repository-history interpretations require live Git verification before reuse |
| `AC-DEC-024` | What is the canonical golden-path capability order? | `init -> check -> run`; repository/doctor/demo/init/run/report; Install/Doctor/Demo/Configure/Run/Inspect; placement of synthetic execution relative to project creation; interactive and automation journeys |
| `AC-DEC-025` | Is Artifact Store a distinct boundary, and what does it own? | Logical API, manifest-backed view, lifecycle owner, or physical collection; relationship to Run, Run Bundle, filesystem, external artifacts, results, reports, and the rule against a second artifact authority |

No open decision is resolved merely because one source supplied a concrete
example.

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

These are candidate work slices, not final backlog IDs, priority, or
implementation authorization. Each will require a bounded owner/caller review,
non-goals, acceptance conditions, and evidence ceiling before entering the
matrix.

| Candidate | Observable outcome | Likely relationship to current matrix |
|---|---|---|
| `AC-SLICE-01` | Ratify an architectural-invariants constitution against live contracts and tests | New slice; supports `ARCH-01` |
| `AC-SLICE-02` | Define formal layers, dependency direction, forbidden edges, and enforcement strategy | New slice; supports `ARCH-01` |
| `AC-SLICE-03` | Define and introduce the Project/Analysis/Run application model without behavior change | New slice or expansion of `CONTROL-01` |
| `AC-SLICE-04` | Define the minimum thin Stage boundary and migrate one representative lifecycle | New slice; coordinate with `ANALYSIS-02` and `ARCH-01` |
| `AC-SLICE-05` | Establish one execution interface for local and SLURM behavior with parity evidence | New slice; enriches `OPS-02` |
| `AC-SLICE-06` | Inventory duplicated policy decisions and centralize one selected authority | New per-policy slices after inventory; supports `ARCH-01` |
| `AC-SLICE-07` | Establish one canonical artifact lifecycle, decide whether a distinct Artifact Store boundary is needed, and migrate one end-to-end artifact path | New slice; supports `ARCH-01` |
| `AC-SLICE-08` | Define named execution profiles independently of Managed/Site/Explicit runtime modes | New slice; coordinates with `OPS-01` and `RUNTIME-01` |
| `AC-SLICE-09` | Provide expert explain/inspect interfaces for effective plan, run, artifact, and evidence | New slice or expansion of `OPS-02`/`CONTROL-01` |
| `AC-SLICE-10` | Define high-level status and safe resume/recovery UX over existing fail-closed internals | New slice; coordinates with `OBS-02` |
| `AC-SLICE-11` | Define a portable canonical Run Bundle contract | New slice; coordinates with `FILESYSTEM-01` and `RESULTS-01` |
| `AC-SLICE-12` | Formalize scientific, evidence, and operational report purposes and navigation | New slice or expansion of `REPORT-03` and `RESULTS-01` |
| `AC-SLICE-13` | Deliver a supported fresh-install-to-valid-synthetic-result golden path after ratifying its capability order | New cross-cutting outcome; coordinates with setup, runtime, Doctor, run, results, and `CLEAN-01` |
| `AC-SLICE-14` | Capture UX/architecture baselines and ratify campaign success measures | New slice; coordinates with `REVIEW-UX-03` and `ARCH-01` |
| `AC-SLICE-15` | Audit the Steps 07–09 statistical contract | New scientific-review slice; not architecture evidence |
| `AC-SLICE-16` | Build independent numerical oracles for Steps 08 and 09 | New scientific-validation slice |
| `AC-SLICE-17` | Retire duplicated lifecycle, validator, infrastructure, adapter, or compatibility paths after each replacement is proven | Multiple bounded deletion slices; never one unbounded cleanup task |
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
| `CONTROL-01` | Compact Project/Analysis/Run/Result model, progressive disclosure, public identity vocabulary, and generated internals remaining inspectable |
| `CONFIG-01` | Scientific versus execution versus evidence ownership; one scientist-facing definition; generated normalized artifacts; schema alternatives remain open |
| `OPS-01` | Small operator-configuration surface; proposed precedence and named-profile models remain choices to ratify; installation facts and accepted effective values remain discoverable |
| `OPS-02` | Small role-aware CLI with the required capabilities; command partitioning/order, scheduler-selection behavior, and stable advanced inspection/override/debug routes remain open |
| `OPS-03` | Inline/generated program inventory, extraction of substantive reusable logic, and removal of operator dependence on helper scripts |
| `OPS-04` | Replace “local pilot” with a domain name that remains accurate beyond one execution context |
| `SETUP-01` | Generate structural input manifests while refusing to invent pairing, strata, conditions, cohorts, or other biological meaning |
| `SETUP-02` | Portable setup-adjacent benchmarking with advisory, evidence-bound recommendations |
| `SETUP-03` | Guided project creation, safe owned directories, generated configuration, validation, and no secret or biological invention; not containerization |
| `RUNTIME-01` | Tiered runtime provisioning and admission; Managed/Site/Explicit are proposed labels; complete qualification includes the active internal workflow engine/Snakemake where applicable and remains separate from execution profiles |
| `DOCTOR-01` | Project-aware readiness capabilities, actionable failures, qualified internal workflow-engine dependency, debug escape hatch, and the explicit-repair override with bounded mutation rules; exact command partitioning remains open |
| `RUN-03` | Preserve immutable-plan safety while eliminating run-root copying; the one-command validate/plan/confirm/execute interaction and exact ordering remain proposals |
| `IDENTITY-01` | Ratify the smallest role-appropriate identity model while preserving detailed identities as evidence metadata; Run/Attempt nesting remains illustrative |
| `FILESYSTEM-01` | Automatic predictable directory creation, one discoverable result surface, and no hidden report root; Project/inputs/runs and Run-Bundle layouts remain proposed |
| `CONTAINER-01` | Independent managed-container/environment decision without assuming final runtime labels; institutional/native/advanced coexistence, image contents and digest, scheduler/storage/security/licensing/update contracts |
| `REVIEW-UX-03` | Scientist, advanced scientist, operator, automation, and developer journeys; progressive disclosure; cognitive-load and golden-path baseline |
| `LOG-03` | Durable complete attempt logging remains infrastructure while concise output becomes the default role-appropriate surface |
| `LOG-05` | Scientific milestone language, actionable failures, and normal-command adoption |
| `OBS-01` | Remove engine, owner, transaction, and low-value noise from the primary view while retaining durable detail |
| `OBS-02` | High-level scientific progress, public run status, elapsed time, completion/failure, and links to recovery/inspection |
| `ANALYSIS-01` | Stop/reuse through the Step 06 boundary and launch separately identified cohort, subset, sensitivity, or downstream work |
| `ANALYSIS-02` | Collaborator-extensible modules with typed scientific contracts; explicitly ratify how scientific algorithms, assumptions, interpretation, and implementation visibility remain reviewable across the module boundary |
| `ARCH-01` | Binding formal layering and deliberate abstractions; explicitly evaluate proposed one-authority, facade-first, scientific-visibility, deletion-complete, Artifact Store, and migration guardrails; ratify preservation versus equal-or-stronger replacement of adversarial/seeded-fault and synthetic E2E regression defenses with honest evidence ceilings |
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

### 18.3 Duplicate policy

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
   affected owners/callers, invariant traceability, acceptance conditions, and
   evidence ceiling.
5. The completed matrix has separately reviewed Importance and Complexity
   scores and rationales.
6. The matrix, task navigation, and legacy backlog transition identify one
   unambiguous active backlog authority.
7. No proposed name, phase, target, ordering, historical claim, or example has
   been silently promoted into a binding decision.
8. A final source-to-destination audit finds no orphaned intake item and no
   architectural context that exists only in an attachment path.
9. The user approves the final traceability and prioritization review.
10. This document receives an explicit retain, archive, consolidate, or retire
    disposition; it does not remain a second permanent backlog by accident.

Until those conditions hold, this campaign document preserves the complete
planning context while the matrix remains the authority for accepted tasks and
their status.
