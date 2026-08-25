# EMRYS Findings Matrix and Working Backlog

Last reconciled: **2026-08-25**

This file is the working planning backlog for EMRYS. It retains every unresolved
finding from the original NORAD E2E matrix, incorporates the selected entries
from the former repository backlog, and organizes the later architecture,
operator-experience, documentation, and maintainability findings.

The traceable architecture intake, substantive source context, proposed
alternatives, and unsliced campaign goals are preserved in the
[architecture campaign](architecture_campaign.md). The hashed source attachments
remain the verbatim record. The campaign document is the temporary source of
truth for context that has not yet been converted into accepted backlog items.
This matrix remains authoritative for task IDs, status, required outcomes,
acceptance conditions, and dispositions; the campaign document does not create
or authorize tasks by itself.

The [architecture backlog matrix](architecture_backlog_matrix.md) records only
a cursory Architecture Priority and Indicative Complexity for unsliced campaign
cards. Those provisional values neither create tasks nor supply the final
Importance and Complexity scores for accepted items in this matrix.

Names, command spellings, phase boundaries, numeric targets, and proposed
ordering quoted from the architecture intake remain suggestions unless this
matrix explicitly adopts them. They must be reconsidered during later slicing
and prioritization rather than silently treated as settled design.

Until <code>BACKLOG-01</code> completes, the repository still contains files
that describe <code>docs/tasks/BACKLOG.md</code> as backlog authority. That is
known transition state, not a second source of current planning decisions.

A row in this matrix does not itself authorize implementation, publication,
cluster execution, dependency installation, destructive cleanup, scientific
review, or evidence promotion.

## Design north star

> **The scientific core is considerably simpler than the software surrounding
> it. EMRYS's biggest opportunity is therefore not to simplify the science, but
> to compress the operational surface area while preserving the
> evidence/provenance guarantees underneath.**

The architectural problem is that too many concepts are visible at too many
layers. Ordinary users currently have to understand artifacts and mechanisms
that should normally be generated implementation details:

~~~text
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
~~~

The leading public conceptual model to evaluate is:

~~~text
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
~~~

One illustrative ordinary command surface is:

~~~text
emrys setup
emrys validate
emrys run
emrys inspect
emrys report
~~~

Project/Analysis/Run/Result vocabulary and setup/init, validate/check,
status/resume, synthetic/demo, inspect, and report spellings remain open design
choices. The binding requirement is a small coherent role-appropriate surface,
not these exact names.

Low-level files, Snakemake, owner jobs, task records, receipts, transactions,
and detailed identities may remain internal. Records required by existing
evidence and audit contracts remain accessible. Broader expert inspection and
override is a source-proposed guardrail pending ratification; ordinary
scientists must not be required to author or operate these internals.

### Configuration ownership

| Layer | Primary questions | Normal author |
|---|---|---|
| Scientific configuration | What data, reference, samples, pairing, comparison, thresholds, and regions? | Scientist |
| Execution configuration | Where does it run, with which CPUs, memory, scheduler, scratch, and tool installation? | Operator or site administrator |
| Evidence configuration | Which hashes, receipts, attempts, artifacts, and immutable identities establish provenance? | EMRYS |

The normal scientist should touch the first layer. Operators may configure the
second. EMRYS owns the third and exposes it for inspection and audit.

### Non-negotiable campaign direction

The architectural campaign must deliver all of the following without weakening
the scientific, provenance, reproducibility, execution, evidence, publication,
or recovery guarantees underneath:

- substantially simpler scientist and operator experiences;
- explicit architectural layers and dependency direction;
- coherent abstractions around identified operational complexity, with exact
  consolidation, ownership, anti-framework, and retirement guardrails ratified
  against live behavior and contracts;
- a complete supported golden path from fresh installation to a valid
  synthetic result; and
- role-based scientist, advanced-scientist, operator, and developer interfaces
  implemented through progressive disclosure.

Role-based progressive disclosure is binding, and simplification may not weaken
the underlying guarantees. The exact expert inspection/override contract and
the proposed requirement for direct scientific-implementation visibility remain
decisions to ratify rather than acceptance criteria already adopted here.

## Backlog operating rules

This matrix intentionally has **no blocker or dependency edges**. Existing
priority labels are provisional historical planning markers; they do not grant
authority, express a final sequence, or make another item unselectable.

### Status

- **Open:** the complete required outcome has not been delivered. Partial
  implementations remain Open.
- **In progress:** an explicitly approved implementation package is active.
- **Verification pending:** the intended implementation appears complete, but
  required acceptance evidence is missing.
- **Deferred:** accepted work intentionally retained for a later horizon.

Terminal states appear only in the disposition log:

- **Complete:** the outcome and every acceptance condition have current
  evidence.
- **Retired:** a formerly valid requirement was intentionally ended after
  review.
- **Absorbed:** another ID explicitly carries the complete outcome and
  acceptance criteria.
- **Discarded:** the user explicitly removed the item without a successor.

### Priority

The current P0-P3 values are **provisional**. After architecture-campaign
context has been sliced into bounded backlog items, every active item will
receive separate, rubric-backed **Importance** and **Complexity** scores. Until
that pass is complete, the retained labels must not be read as the campaign's
settled ordering.

- **P0:** blocks a complete valid run or an explicitly current committed
  deliverable.
- **P1:** required for the intended operator/scientist experience or a formal
  qualification.
- **P2:** important architecture, maintainability, portability, or usability
  improvement.
- **P3:** exploratory or safe to defer.

### Closure rule

An item leaves the active matrix only when:

1. Its required outcome is fully implemented.
2. Every acceptance condition is satisfied.
3. Dated evidence is recorded at the correct level. Local engineering,
   cluster/production execution, scientific review, and biological readiness
   remain separate claims.
4. Affected public interfaces, documentation, provenance, and operational
   contracts are updated.
5. A terminal disposition is recorded.

A commit, partial implementation, policy decision, or “appears implemented”
observation is not sufficient by itself. Audit/decision tasks close when their
inventory and durable decisions exist; executing those decisions remains
separately tracked where required.

## Active backlog

### Qualification and retained runtime defects

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>QUAL-01</code> | P2 | Open | Make qualification-test selection fast enough for routine developer use. | Capture durations and subprocess/NFS costs, establish a runtime target, and demonstrate the selected suite meets it without reducing coverage or fault cases. |
| <code>QUAL-02</code> | P1 | Verification pending | Replace the brittle resume-fixture startup deadline with exact bounded readiness and useful failure diagnostics. | The targeted resume fixture passes with bounded readiness, early-exit output, and guaranteed cleanup under the retained qualification environment. |
| <code>QUAL-03</code> | P1 | Verification pending | Support the exact accepted GNU Make 3.81 and 4.3 dry-run renderings without over-normalizing malformed output. | The selected contracts pass under GNU Make 4.3 and continue to reject mixed or otherwise invalid renderings. |
| <code>QUAL-04</code> | P1 | Verification pending | Derive owner-count expectations from the authoritative owner set rather than stale hard-coded values. | The affected lifecycle and owner-count tests pass and prove the expected current owner roster. |
| <code>QUAL-05</code> | P1 | Verification pending | Accept any operator-selected clean checkout while binding each run and resume to the exact source commit actually used. | A fresh run accepts the selected clean checkout, receipts bind its commit, and resume rejects incompatible source changes without requiring an external predetermined SHA. |
| <code>RUN-01</code> | P1 | Verification pending | Admit normal <code>renv</code> cache-package symlinks consistently across restore, Doctor, and validation. | The real restored library passes focused admission and Doctor checks; dangling, retargeted, or identity-changing links still fail closed. |
| <code>RUN-02</code> | P1 | Verification pending | Complete Step 10 and report execution with default R packages disabled and eliminate similar unqualified base/default-package calls. | The guarded regression, namespace audit, and full Step 10/report path pass in the intended R environment. |

### Public model, operator interface, setup, runtime, and data

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>CONTROL-01</code> | P1 | Open | Establish a compact role-aware public conceptual model and explicitly decide the relationship among Project, Analysis, Dataset, Reference, ExperimentalDesign, Runtime, Run, Result, Attempt, Task, Artifact, and Report. | Ordinary scientific work can be explained and operated through the smallest accepted vocabulary; advanced scientists, operators, and developers can progressively inspect the deeper model; generated manifests, control files, engine state, and low-level identities remain available but are not required user-authored concepts. Exact nouns and nesting remain a later design decision. |
| <code>CONFIG-01</code> | P1 | Open | Replace configuration sprawl with one scientist-facing project definition and explicit scientific, execution, and evidence ownership. | Scientists author data/reference/design/analysis intent; operators select and define execution profiles; EMRYS owns evidence configuration and generates normalized requests, manifests, runtime/resource/launcher artifacts, identities, and records; runtime provisioning mode and execution backend/profile remain distinct inspectable choices; every effective value and its source are inspectable. |
| <code>OPS-01</code> | P1 | Open | Remove the large manually maintained export surface and define a small operator-configuration surface; evaluate named execution profiles as one candidate encapsulation. | The accepted precedence and operator-control model is documented; installation-derived facts can be discovered; backend, resources, storage, and runtime are not conflated. The task explicitly decides which effective operational values require stable inspection or override and through which interfaces. The stronger “every supported decision without modifying source” rule remains a source proposal pending ratification. |
| <code>OPS-02</code> | P1 | Open | Provide a small role-aware public CLI instead of exposing wrappers, implementation variables, scheduler mechanics, or direct engine controls. | Workstation and scheduled execution expose the same accepted high-level capabilities for project preparation, readiness/validation, execution, progress/status, inspection, and reporting with safe defaults. The task decides command partitioning and ordering, scheduler-selection behavior, and stable advanced inspection/override/debug routes. Exact command names and sequence remain open. |
| <code>OPS-03</code> | P2 | Open | Inventory inline/generated programs and extract substantive reusable scripts from Python, Make, documentation, and other owners. | Every inline program has an explicit retain/extract disposition; substantive independently testable programs have one owner and direct tests; operators do not run internal helper scripts to complete normal work. |
| <code>OPS-04</code> | P2 | Open | Replace the misleading “local pilot” orchestrator name in the primary product surface. | The stable command and domain name describe execution accurately across CLI, modules, docs, logs, and generated assets, with an explicit compatibility/retirement policy for the old name. |
| <code>SETUP-01</code> | P1 | Open | Generate required draft manifests from supplied input paths without inventing biological relationships. | EMRYS discovers structural input facts, emits deterministic validated drafts, and asks for pairing, strata, conditions, or other biological meaning when they are ambiguous. |
| <code>SETUP-03</code> | P1 | Open | Provide a guided project-creation/setup workflow that prepares a project for normal commands. | Setup collects the minimum project/site facts, creates safe workspace, results, runtime, and log locations, generates derived configuration, validates the prepared project, and never prints or silently invents secrets or biology. Its boundary is project preparation. The broader golden path also requires separately owned installation/runtime, readiness, neutral-synthetic execution, progress/status, recovery, and result-access capabilities. Their exact order, command partitioning, and setup/init spelling remain unsettled. |
| <code>RUNTIME-01</code> | P1 | Open | Evaluate and establish a tiered runtime provisioning and selection model that reduces ordinary setup burden while retaining institutional and advanced paths. | The task chooses and documents the accepted provisioning modes; it considers a reproducible managed option with <code>CONTAINER-01</code>, discovery/admission of institution-provided tools, and explicit advanced definitions without conflating provisioning with execution backend or profile. Qualification covers the complete selected runtime, including Snakemake as an internal engine dependency when applicable and the relevant R environment. Managed/Site/Explicit labels and proposed subcommands remain nonbinding. |
| <code>DOCTOR-01</code> | P1 | Open | Replace user-hostile low-level readiness commands with a project-aware readiness experience; “Doctor” remains the working label until command partitioning is decided. | The accepted readiness surface derives declared workspace/reference/input locations and reports storage, runtime, execution, and input readiness concisely with actionable failures. Runtime readiness includes internal dependencies such as the selected workflow engine without making that engine scientist-authored configuration or the primary execution interface. Default invocation does not mutate project/reference data. Any repair requires an explicit repair action, is previewed or precisely reported, is limited to owned safe state, preserves provenance, never invents secrets or biology, and cannot silently adopt or alter declared scientific inputs. Low-level probes and diagnostics remain available through an advanced route; the split among setup, readiness, validation, and repair commands remains open. |
| <code>RUN-03</code> | P1 | Open | Define a coherent run journey that preserves immutable-plan safety while eliminating manual transfer of run roots or internal state between phases. | The accepted journey presents the scientific request, effective execution choice, resources, reuse decisions, and immutable plan at the appropriate point; supports interactive and noninteractive operation; and preserves provenance plus Local/HPC correctness. A single command followed by confirmation is a source proposal, not settled command structure. Command boundaries, ordering, and executor-selection policy remain open. |
| <code>IDENTITY-01</code> | P2 | Open | Reduce public identity burden and ratify the smallest role-appropriate identity model while preserving detailed identities as evidence metadata. | Ordinary users need only the accepted primary run-level identifier and any additional identifier genuinely required for truthful retry or recovery diagnosis. No subsystem reconstructs a competing run identity; existing commit, package, runtime, request, task, artifact, receipt, and publication identities remain preserved under the accepted model. The proposed Project/Analysis → Run → Attempt/Task/Artifact hierarchy is illustrative, not acceptance. |
| <code>FILESYSTEM-01</code> | P2 | Open | Define a stable generated public storage model with one discoverable scientist-facing result surface and decide its relationship to the proposed Run Bundle. | Locations for provenance, work, results/artifacts/reports, and logs are predictable and created automatically; no manual directory assembly or competing hidden report root remains. Exact public nouns, directory names, nesting, bundle layout, portability, archival, and sharing semantics remain open. |
| <code>CONTAINER-01</code> | P2 | Open | Independently evaluate a supported managed container/environment option without coupling it to guided setup or assuming the final runtime taxonomy. | The decision covers scheduler integration, storage, architecture, security, reproducibility, tool and R-library contents, licensing, image and per-tool provenance, updates, coexistence with institutional/native/advanced runtime paths, and escape hatches; any implementation has explicit local and site acceptance evidence. |
| <code>FUT-DATA-02</code> | P3 | Deferred | Provide explicit retryable public-reference and SRA-read acquisition with provenance and content identity. | Reference and read acquisition remain separate; version/accession, source, hashes, cache, retry, partial transfer, and storage identity are recorded without scraping, silent updates, or implicit trust. |
| <code>FUT-INDEX-01</code> | P2 | Open | Safely admit and reuse an explicitly declared prebuilt STAR index instead of regenerating it. | Required index members are bound to FASTA/GTF identities, STAR parameters and version, and exact content hashes; mere directory existence never authorizes reuse, repair, merge, or mutation. |

### Usability, logging, and progress

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>REVIEW-UX-03</code> | P1 | Open | Independently review scientist, advanced-scientist, operator, developer/maintainer, and automation journeys against the non-negotiable simplified golden path. | The review covers fresh installation through valid synthetic result, findability, terminology, concepts required, configuration burden, progressive disclosure, accessibility, failure diagnosis and recovery, console/report hierarchy, intake, local/HPC context, and evaluation of the source-proposed expert inspection, override, and escape-hatch model without changing scientific meaning. It records baseline and target measures without treating source-proposed numeric targets as already accepted. |
| <code>LOG-03</code> | P1 | Open | Build a neutral two-sink logging foundation that separates concise operator output from complete durable attempt logs. | The binding logging contract is implemented across identity, records, publication, failure, redaction, retention, and scheduler streams without changing computation, artifacts, transactions, recovery, exits, or evidence meaning. |
| <code>LOG-05</code> | P1 | Open | Activate concise role-appropriate default logging across every applicable command after foundation adoption. | Routine output uses scientific and run-level milestones rather than owner jobs, transactions, scheduler commands, or receipt mechanics; failures identify the useful public state, reason, recovery guidance, and durable log path; complete forensic detail remains available; parity evidence covers each adopted domain. |
| <code>OBS-01</code> | P1 | Open | Remove low-value console noise from the default user experience. | Default output shows meaningful milestones, warnings, failures, and the durable log path; verbose/debug detail is explicitly requested. |
| <code>OBS-02</code> | P1 | Open | Provide a supported high-level progress, status, and recovery-guidance surface while hiding the internal execution/publication state machine. | Users see preparation, alignment, QC, candidate generation/testing, report generation, elapsed time, and a small truthful state vocabulary such as pending/running/complete/failed/recoverable; failure output explains the reason, whether resume is safe, and the supported next action. EMRYS determines internally what remains valid, provisional, reusable, rolled back, or recomputed; Snakemake jobs, owner counts, transactions, publication states, and attempt internals remain available in evidence/debug views. Exact states and resume command remain unsettled. |

### Analysis modularity and overall architecture

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>ANALYSIS-01</code> | P1 | Open | Allow one project to stop after compatible per-sample processing and launch separately identified cohort, subset, sensitivity, or downstream analyses from the reusable Step 06 boundary. | Compatible Steps 00–06 artifacts are content-bound and reused without mutation; cohort-dependent Steps 07 onward receive a distinct analysis/run identity, outputs, evidence, and report; incompatible reuse fails closed. |
| <code>ANALYSIS-02</code> | P2 | Open | Provide a versioned collaborator-extensible analysis library/module interface and explicitly decide whether and how the source-proposed anti-framework guardrail applies. | Modules declare typed inputs/outputs, dependencies, validation, provenance, trust level, failure semantics, resource needs, and report integration; adding a differential analysis does not require editing the scientific core or unrelated owners. The task explicitly decides whether and how algorithms, assumptions, biological interpretation, and implementation visibility remain reviewable across the module boundary. Candidate shared abstractions may own execution, filesystem, provenance, and scheduler mechanics only after that boundary is accepted. |
| <code>ARCH-01</code> | P2 | Open | Establish formal architectural layers and dependency direction, introduce deliberate application/infrastructure abstractions, and reduce maintained surface and cross-module coupling while preserving every declared invariant. | The task ratifies the inventory, invariant, sequencing, layer, dependency, ownership, and migration policies before applying any source-proposed order or consolidation rule. For each adopted abstraction it records the ratified purpose, authority relationship, and guarantee-preservation contract. The source-proposed exact layer map, one-final-authority rule, facade-first sequence, direct-scientific-visibility guardrail, and deletion-complete retirement rule are evaluated explicitly rather than presumed. The task also ratifies whether existing adversarial/seeded-fault and synthetic end-to-end coverage must be preserved or may be replaced by equal-or-stronger defenses, then applies the accepted contract with explicit evidence ceilings distinct from the user-facing neutral-synthetic golden path. |

### Performance and benchmarking

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>SETUP-02</code> | P2 | Open | Integrate portable optional benchmarking into the normal setup/control plane and support process-by-thread trials. | Users can run an advisory benchmark without authoring raw command arrays; results bind dataset, node, runtime, storage, resources, equivalence checks, and raw measurements; recommendations are never silently applied. |
| <code>PERF-01</code> | P3 | Deferred | Evaluate whether cross-node execution materially improves independent-work wall time. | A bounded experiment follows explicit per-job resource modeling and compares representative workloads without treating scheduler success as production or scientific proof. |

### Scientific reporting and result delivery

All reporting rows also inherit the
[shared report acceptance contract](#shared-report-acceptance-contract).

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>REPORT-01</code> | P1 | Verification pending | Produce readable locus-centered figures aligned with the supplied Figures 4b and 6b references. | Rendered output makes editing rate, location, local sequence, nearby motifs, significant candidates, and replicate behavior immediately readable and passes visual comparison plus the shared report contract. |
| <code>REPORT-02</code> | P1 | Verification pending | Replace wide human-facing tables with a narrow ranked summary, comparison views, and vertical detail records. | Exact scientific facts remain printable and visible; complete data is linked as machine-readable artifacts rather than rendered as wide appendices; the shared report contract passes. |
| <code>REPORT-03</code> | P1 | Verification pending | Remove low-value report material and establish explicit scientific, evidence, and operational report audiences with a primary-findings-first default hierarchy. | The ordinary scientific view answers what the analysis found and leads with primary results, then actionable QC and necessary methods/limitations; an evidence view answers why the result is trustworthy; an operational view explains how execution occurred. All remain traceable to the same run without forcing filesystem, scheduler, transaction, or durability detail into scientific interpretation. Exact commands and whether these are views or separate artifacts remain unsettled. |
| <code>REPORT-04</code> | P1 | Open | Support an A-through-I selected-candidate/panel roster when the admitted result warrants nine items. | At least nine admitted selections render without silent truncation, label collision, inaccessible content, or print/layout failure; any larger-display limit is explicit and evidence-bound. |
| <code>RESULTS-01</code> | P1 | Open | Publish one discoverable scientist-facing result bundle beneath the canonical run-relative results surface and make it the ordinary entry point into the broader Run Bundle. | Run completion and status print the canonical result/report location; primary scientific reports, ranked results, complete tables, and links to evidence and operational views are collected under <code>&lt;run-root&gt;/results</code>; <code>FILESYSTEM-01</code> leaves no competing hidden report root, duplicate authority, or scratch/intermediate content there. The result remains bound to its run identity and provenance without requiring the scientist to navigate forensic internals. |

### Documentation, backlog, demo, and maintenance tooling

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>DOC-01</code> | P1 | Open | Condense retained documentation and reorganize it around scientist, operator, and developer journeys without requiring campaign history or developer-only context. | Scientist guidance covers purpose, inputs, project definition, the golden path, results, and scientific limitations; operator guidance covers runtime, profiles, storage, scheduler, diagnosis, and recovery; developer guidance retains exact architecture, contracts, evidence, and internals. Each retained document states purpose, pipeline role, when it is needed, primary interface/output, and canonical contract owner; B2/B4, campaign, phase, and similar shorthand is replaced with meaningful content. Successful ordinary use does not require reading developer architecture. |
| <code>DOC-02</code> | P1 | Open | Audit repository documentation and decide independently for each source whether to retain, refresh, consolidate, move durable information, or retire it. | The audit covers all inbound references and named candidates; each disposition is evidence-based; durable safety, operations, science, evidence ceilings, and recovery content move before deletion; execution of separately scoped decisions remains separately tracked. |
| <code>BACKLOG-01</code> | P1 | Open | Retire the repository backlog/task-card operating system and establish one durable canonical location for this matrix. | <code>docs/tasks/BACKLOG.md</code>, registry/card guidance, task-specific navigation, and <code>task_status.py</code> receive explicit dispositions; every caller is updated; no second backlog authority or broken task reference remains. |
| <code>DOC-TOOL-01</code> | P1 | Open | Preserve, narrow, relocate, and revalidate the useful non-backlog behavior of <code>validate_documentation.py</code>. | Existing checks are inventoried; retained canonical-owner, retired-document, owner-adjacency, topology/diagram, and other intended checks move to a correctly named owner; obsolete task-registry logic is removed; Make, docs, fixtures, and tests are updated; seeded failures prove the replacement is not weaker. |
| <code>TOOLING-01</code> | P2 | Open | Independently audit the remainder of <code>scripts/git_orchestration/</code> and remove the misleading ownership bucket. | Every file and caller receives a retain, relocate, replace, or retire decision; useful tools move beside their real owner; no generic Git-orchestration directory remains solely as historical taxonomy. |
| <code>CLEAN-01</code> | P2 | Open | Retire the historically coupled “demo” product surface without losing a neutral supported synthetic golden path or necessary reporting validation. | Demo Make targets, docs, fixtures, tests, links, and public references are inventoried and removed, renamed, or moved to neutral synthetic-example/test/preview ownership; a fresh installation can still produce a valid synthetic result through the accepted golden path; no historical “demo” state remains in the primary product surface unless that name is deliberately reconsidered and accepted later. |

## Routed architecture context for existing IDs

This section routes architecture-intake context to existing task rows without
adding candidate task slices. Binding status follows the explicit
non-negotiables and each task row's accepted general outcome. A source proposal
remains nonbinding when routed here unless the matrix explicitly says otherwise.
Task creation, final interface decisions, importance/complexity scoring, and
sequencing remain later passes. The campaign preserves source traceability,
substantive context, and alternatives; the hashed source attachments remain the
verbatim record.

| Existing ID or IDs | Routed campaign context | Scope boundary retained |
|---|---|---|
| <code>CONTROL-01</code>, <code>REVIEW-UX-03</code> | The public surface must become substantially simpler and use progressive disclosure for scientist, advanced-scientist, operator, and developer roles. Project/Run/Result is a leading source proposal; Project/Analysis/Run/Result and the placement of Dataset, Reference, Design, Runtime, Attempt, Task, Artifact, and Report remain alternatives to evaluate. | Simplification preserves guarantees and uses binding role-based progressive disclosure. The exact stable expert inspection and override surface, source-proposed nouns, command names, percentages, and concept counts require explicit decision. |
| <code>CONFIG-01</code>, <code>OPS-01</code>, <code>RUNTIME-01</code> | Scientific intent, execution/site policy, and EMRYS-owned evidence configuration have different authors. Named execution profiles and Managed/Site/Explicit are source-proposed ways to represent distinct concerns; the tasks must choose terminology and taxonomy without conflating runtime provisioning, execution backend, or profile. | Whatever taxonomy is accepted, generated configuration retains precedence and provenance, and runtime/readiness qualification includes internal engine dependencies such as Snakemake without exposing engine invocation or configuration as an ordinary scientist task. |
| <code>OPS-02</code>, <code>SETUP-03</code>, <code>DOCTOR-01</code>, <code>RUN-03</code>, <code>OBS-02</code>, <code>LOG-05</code>, <code>RESULTS-01</code>, <code>CLEAN-01</code> | Together these rows own the required golden-path capability set: supported installation/runtime, readiness diagnosis, project creation and validation, neutral-synthetic execution, useful progress/status, safe recovery, and discoverable valid results. The ordinary path must not require manual directory creation, run-root copying, scheduler scripts, engine state, transaction states, or forensic identities. | The capability set and successful end state are binding; no exact ordering is adopted because the sources propose different sequences. No one row can claim the complete golden path from its segment alone. Diagnosis is the default while repair is explicit, bounded, safe, and provenance-aware. Command spellings and partitioning remain unsettled. |
| <code>ARCH-01</code>, <code>ANALYSIS-02</code> | Formal layering and deliberate abstractions are non-negotiable. The leading layer model and candidate Run, Execution, Stage, Artifact lifecycle/Store, and policy boundaries are proposals to evaluate. | Higher-to-lower dependency direction is binding. Exact classes/APIs, direct scientific-code visibility, facade-first migration, one-final-authority wording, deletion-complete retirement, and the preservation-versus-equal/stronger-replacement rule for adversarial/seeded-fault and synthetic E2E tests all require ratification before migration; their evidence labels remain distinct. |
| <code>IDENTITY-01</code>, <code>FILESYSTEM-01</code>, <code>RESULTS-01</code> | A run should be understandable as one coherent package containing its configuration, identity, artifacts/results, evidence, logs, and reports. Detailed identities remain metadata under whatever public identity model is accepted. | “Run Bundle” and “Artifact Store” are proposed abstractions, not settled owners, on-disk schemas, or portability guarantees. Scratch/work state is not promoted into the scientist-facing result merely for structural symmetry. |
| <code>REPORT-03</code>, <code>RESULTS-01</code> | Reporting must serve three explicit questions: scientific—what was found; evidence—why the result is trustworthy; operational—how execution occurred. | The views share run identity and provenance but do not force operational/evidence detail into the primary scientific narrative. Separate commands versus report views/files remain undecided. |
| <code>DOC-01</code>, <code>REVIEW-UX-03</code> | Documentation and review follow the role journeys: scientists reach a result and interpretation first; operators provision, qualify, schedule, diagnose, and recover; developers inspect architecture and exact contracts. | Developer architecture remains available, but reading it cannot be a prerequisite for ordinary scientific use. |
| <code>CONTAINER-01</code>, <code>RUNTIME-01</code> | A managed image/environment may provide the easiest supported runtime and bind an image digest plus enumerated tool identities into provenance. | Containerization remains independent of guided project setup and supplements rather than automatically replacing the institutional, native, or advanced runtime paths accepted by <code>RUNTIME-01</code>. |
| <code>ARCH-01</code>, <code>DOC-02</code>, <code>TOOLING-01</code>, <code>DOC-TOOL-01</code>, <code>CLEAN-01</code> | Cleanup is an architectural deliverable: inventory duplicate validators, lifecycle implementations, stage-specific infrastructure, migration adapters, compatibility paths, generic ownership buckets, and stale documentation, then retain, relocate, consolidate, or retire each deliberately. | Durable scientific, operational, provenance, recovery, testing, and documentation-validation value moves before any retirement. Whether each abstraction package must immediately delete all superseded paths is the proposed migration policy tracked by <code>AC-DEC-018</code>/<code>020</code>; every compatibility path still receives an explicit disposition. |

## Illustrative architecture reference models

The following source-proposed schemas, labels, commands, hierarchies, and
layouts preserve concrete options for later decisions. They are nonbinding
unless an active task row separately adopts a general outcome. Exact vocabulary,
command partitioning, ordering, runtime taxonomy, identity nesting, and
filesystem shape remain open.

### Scientific project configuration

One source-proposed user-authored scientific schema resembles:

~~~yaml
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
~~~

EMRYS may generate normalized requests, sample and partition manifests, runtime
profiles, launcher/resource configuration, run identities, and evidence
manifests internally. Generated artifacts remain inspectable and
content/provenance bound; scientists are not required to author them.

The accepted design requires an explicit precedence contract. One proposed
ordering is:

~~~text
built-in defaults -> site/execution profile -> project request -> CLI override
~~~

Exact merge order and list/map/null semantics remain open.

### Source-proposed runtime modes

| Mode | User intent | Expected primary interface |
|---|---|---|
| Managed | Use an EMRYS-provided reproducible container or environment. | <code>emrys runtime install</code>, only if <code>CONTAINER-01</code> accepts and defines it |
| Site | Discover and select institution-provided modules and tools. | <code>emrys runtime discover</code>, then <code>emrys runtime accept</code> |
| Explicit | Supply advanced paths and identities manually. | <code>emrys runtime define ...</code> |

One source-proposed discovery scope includes Python/EMRYS, STAR, samtools, GATK,
Picard, bcftools, RSeQC, R, Java, Snakemake, and the relevant R environment.
Whatever model is accepted, readiness must qualify the complete selected
toolchain. Snakemake remains an internal execution dependency: ordinary
scientists do not author its commands or configuration, while operator/debug
detail may expose its exact version and readiness. Discovery observes; it does
not install, repair, or silently select a runtime.

Runtime modes answer **how the required tools are provisioned and selected**.
They are independent of execution backends and named execution profiles:

| Concept | Question answered | Examples under consideration |
|---|---|---|
| Runtime mode | How are tools supplied and identified? | Managed, Site, Explicit |
| Execution backend | How is work launched? | Local, SLURM |
| Execution profile | Which site-approved backend, resources, storage, and runtime selection apply? | Local, cluster, development, production |

The example labels are not settled vocabulary. The accepted design must decide
which operational choices are visible and overrideable for each role and how
their provenance is reported. The stronger proposal that every important choice
be overrideable without source modification is not yet ratified.

### Illustrative readiness/Doctor surface

The primary readiness surface should report:

~~~text
Storage
  workspace             pass/fail
  reference sidecars    pass/fail
  locking               pass/fail
  atomic rename         pass/fail
  durability            pass/fail

Runtime
  Python                pass/fail
  workflow engine       pass/fail
  STAR                  pass/fail
  samtools              pass/fail
  GATK                  pass/fail
  ...

Inputs
  FASTQs                pass/fail
  FASTA                 pass/fail
  GTF                   pass/fail
  experimental design   pass/fail
~~~

Detailed output identifies Snakemake and its version when it is the selected
workflow engine, without making Snakemake part of the ordinary scientific
control model.

Doctor derives paths from the admitted project/site configuration and diagnoses
without mutation by default. It may offer an explicitly selected repair action,
but every repair must be bounded to EMRYS-owned safe state, previewed or
precisely reported, provenance-aware, and prohibited from silently inventing or
altering secrets, biological relationships, declared inputs, or reference
content. Qualification writes remain explicit bounded owned probes with
deterministic cleanup and a reported evidence ceiling. Detailed low-level
storage and runtime checks stay available through advanced/debug interfaces.
The exact repair command spelling and catalogue of permitted repairs remain a
later design decision.

### Source-proposed identity and filesystem examples

One proposed public identity hierarchy is:

~~~text
Analysis
  +-- Run
       +-- Attempt
       |    +-- Task
       +-- Artifacts
~~~

Commit, package, runtime, request, artifact, and receipt identities remain
complete metadata under the appropriate run/attempt/task/artifact boundary.
Exact hierarchy, nesting, and public identity vocabulary remain open; existing
evidence identities remain preserved.

One proposed public filesystem example is:

~~~text
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
~~~

Exact layout and public mental model remain open. The binding general outcome is
automatically prepared, predictable locations, one discoverable
scientist-facing result surface, and no hidden competing report root.

## Shared report acceptance contract

This section remains normative until <code>REPORT-01</code> through
<code>REPORT-04</code> and <code>RESULTS-01</code> satisfy it with current
rendered evidence.

The primary scientific surface must let a reader answer three questions for
every prioritized editing site without consulting a machine-readable artifact:

1. **Editing rate:** How much editing was observed?
2. **Location:** Where is the edited base biologically and genomically?
3. **Nearby motifs:** Which relevant motifs occur nearby, and where are they
   relative to the edited base?

These are required result fields, not optional annotations.

### Editing rate

- Show the exact control and treatment editing percentages and the change in
  percentage points.
- Preserve replicate behavior rather than presenting only a pooled value; use
  aligned replicate markers or tracks when space permits.
- Show the informative read denominator alongside the rate, or in the same
  vertical detail record, so shallow and well-supported percentages are not
  visually equivalent.
- Define the rate calculation once and represent missing or zero-denominator
  values explicitly rather than as zero editing.

### Location

- Show genomic coordinate, strand, and reference assembly/contig naming
  context.
- Show gene or transcript identifiers and transcript-region annotation, such
  as 5-prime UTR, CDS, 3-prime UTR, intron, or intergenic, when available.
- Keep the edited base visibly anchored to local sequence in each locus view.

### Nearby motifs

- Display exact matched motif sequence, motif identity, and signed or
  directionally clear distance from the edited base.
- Show all qualifying motifs within the documented sequence window, not only
  the nearest match, and highlight their exact bases in the locus view.
- State “none detected within the configured window” when appropriate; motif
  absence must not disappear as a blank field.
- Declare motif definitions, search window, strand handling, and coordinate
  convention once in methods or the figure legend.

### Coordinated report views

The printable report should use:

1. A narrow ranked summary with stable site identifier, compact location,
   control/treatment editing rates and difference, nearby motif/distance, and
   statistical confidence.
2. A Figure 4b/6b-style locus view showing position-by-position editing, local
   sequence, edited sites, and motif placement.
3. A vertical detail record for exact replicate values, read support,
   annotations, QC limitations, and interpretation.

Exact rates, coordinates, and motif annotations must remain visible in exported
HTML/PDF and must not depend on hover interactions. Complete site-level data
remains available as linked TSV/CSV output rather than a rendered wide
appendix. Nine admitted A-through-I selections must render without silent
truncation or degraded print/accessibility behavior.

## Documentation audit candidates

<code>DOC-02</code> must at minimum inspect:

- <code>docs/architecture/FUTURE_ARCHITECTURE.md</code>
- <code>docs/design/ORCHESTRATION_READINESS.md</code>
- <code>docs/design/PIPELINE_PLAN.md</code>
- <code>docs/design/QUESTIONS.md</code>
- <code>docs/operations/LOCAL_PILOT_LAUNCHER_TEST_PLAN.md</code>
- <code>docs/operations/HANDOFF.md</code>
- <code>docs/tasks/BACKLOG.md</code>
- <code>docs/tasks/README.md</code>
- <code>docs/tasks/cards/README.md</code>
- <code>docs/demo/</code>
- <code>scripts/git_orchestration/README.md</code>

The audit decides retain, refresh, consolidate, move, or retire. It does not
perform the independently tracked backlog, validator, or demo migrations merely
by recording a disposition.

<code>docs/operations/HANDOFF.md</code> and
<code>docs/design/PIPELINE_PLAN.md</code> are user-identified stale, unverified
transition sources even though existing repository guards, navigation, and
cross-links still route to them. <code>DOC-02</code> must reconcile useful
content against live Git, source, tests, this matrix, and applicable durable
owners, then update every inbound authority claim before either document is
retained, refreshed, replaced, or retired. Current planning or evidence must not
be added solely to either file on the assumption that it remains reliable.

## Dated evidence ledger

| Date | ID or scope | Observation | Evidence level |
|---|---|---|---|
| 2026-08-20 | Original 19 findings | The predecessor matrix assessed <code>fix/viking-local-pilot-e2e</code> at <code>ce9d1c4</code>, recorded five verification-pending fixes, four partially addressed items, nine open items, and one policy-closeout item. | Historical branch/source review; not current execution proof |
| 2026-08-24 | Repository snapshot | <code>/Users/elisteiger/dev/norad</code> was clean on <code>ci/extended-synthetic-e2e</code> at <code>d7929f302b962b7cf0e30ce741565fb03f97d305</code>, with cached upstream relation <code>0/0</code>. No fetch, test, benchmark, R check, Slurm execution, or scientific review was performed for this matrix rewrite. | Current local Git/source observation only |
| 2026-08-24 | <code>QUAL-02</code>, <code>QUAL-03</code>, <code>QUAL-04</code>, <code>RUN-01</code>, <code>RUN-02</code> | Their cited implementation commits are ancestors of the current checkout, but the predecessor matrix's required retained gates were not re-established in this documentation task. | Implementation presence; verification pending |
| 2026-08-24 | <code>QUAL-01</code> | Duration-aware sharding and slow-test reporting now exist, but no accepted latency target or current proof closes the original qualification-runtime problem. | Current source review; outcome remains Open |
| 2026-08-24 | <code>QUAL-04</code>, <code>QUAL-05</code>, <code>RUN-02</code> | Current implementation and regression surfaces appear to satisfy the intended code changes, but this matrix rewrite did not execute their final acceptance gates. They remain Verification pending. | Current source/test review; no new execution evidence |
| 2026-08-24 | <code>OPS-02</code>, <code>OBS-02</code>, <code>SETUP-01</code>, <code>SETUP-02</code> | Partial commands/helpers exist, but the complete outcomes stated in this matrix do not. They therefore remain Open under the closure rule. | Current source/documentation review |
| 2026-08-24 | <code>REPORT-01</code>, <code>REPORT-02</code>, <code>REPORT-03</code> | Current reporting implements candidate-centered figures, narrow ranked/vertical records, linked complete tables, and separate scientific/evidence hierarchies. Current rendered visual/user acceptance against the retained contract was not performed, so the rows remain Verification pending. | Current source/test review; rendered acceptance absent |
| 2026-08-24 | <code>REPORT-04</code> | The current scientific-context/report selection contract uses a fixed display limit of eight. The requested A-through-I surface requires nine when warranted. | Current source observation |
| 2026-08-24 | Configuration/setup | The repository contains 20 files under <code>configs/</code>; Quickstart still exposes manual configuration and directory preparation. | Current source/documentation observation |
| 2026-08-24 | Documentation/task tooling | The repository still declares <code>docs/tasks/BACKLOG.md</code> as live authority; <code>task_status.py</code> renders that registry; <code>validate_documentation.py</code> combines useful documentation checks with task-registry enforcement. | Current source/documentation observation |

## Former repository-backlog reconciliation

The following IDs were explicitly retained and now appear in the active matrix:

- <code>FUT-DATA-02</code>
- <code>FUT-INDEX-01</code>
- <code>LOG-03</code>
- <code>LOG-05</code>
- <code>REVIEW-UX-03</code>

No former blocker relationships were retained.

## Disposition log

| Date | ID | Disposition | Reason or successor |
|---|---|---|---|
| 2026-08-24 | <code>AUDIT-99</code> | Discarded | Explicitly excluded from the retained backlog. Current architecture/documentation concerns are re-authored under <code>ARCH-01</code> and <code>DOC-02</code>. |
| 2026-08-24 | <code>CODEDOC-05</code> | Discarded | Explicitly excluded; current reader-facing documentation outcome is owned by <code>DOC-01</code>. |
| 2026-08-24 | <code>DOC-SKILL-10</code> | Discarded | Explicitly excluded without retaining the former skill proposal. |
| 2026-08-24 | <code>DOC-TASK-SCAN-01</code> | Discarded | Explicitly excluded; the new bounded repository documentation audit is <code>DOC-02</code>. |
| 2026-08-24 | <code>FUT-ANALYSIS-01</code> | Discarded | The former item is not revived; current analysis requirements are re-authored as <code>ANALYSIS-01</code> and <code>ANALYSIS-02</code>. |
| 2026-08-24 | <code>FUT-CLI-03</code> | Discarded | The former proposal is not revived; current public-control outcomes are owned by <code>CONTROL-01</code>, <code>CONFIG-01</code>, <code>OPS-01</code>, and <code>OPS-02</code>. |
| 2026-08-24 | <code>FUT-DASH-01</code> | Discarded | Explicitly excluded; <code>OBS-02</code> retains only the supported progress/status requirement. |
| 2026-08-24 | <code>FUT-SUCCESS-04</code> | Discarded | Explicitly excluded without a successor task. |
| 2026-08-24 | <code>GATE-REC-01</code> | Discarded | Explicitly excluded; current tasks still preserve existing evidence/provenance guarantees. |
| 2026-08-24 | <code>SKILL-11</code> | Discarded | Explicitly excluded without a successor task. |
| 2026-08-24 | <code>FUT-AGENT-01</code> | Discarded | Explicitly excluded without a successor task. |
| 2026-08-24 | <code>FUT-AIDEV-01</code> | Discarded | Explicitly excluded without a successor task. |
| 2026-08-24 | <code>FUT-SITE-01</code> | Discarded | Explicitly excluded; current runtime/site simplification is re-authored under <code>RUNTIME-01</code> and <code>DOCTOR-01</code>. |
| 2026-08-24 | <code>FUT-SITE-02</code> | Discarded | The former proposal is not revived; containerization is independently re-authored as <code>CONTAINER-01</code>. |
| 2026-08-24 | <code>TASK-INTAKE-01</code> | Discarded | Explicitly excluded without a successor task. |
| 2026-08-24 | <code>TASK-VIEW-01</code> | Discarded | Explicitly excluded; the matrix itself is the intended working view. |
| 2026-08-24 | <code>TEST-E2E-01</code> | Discarded | Explicitly excluded from the retained backlog. Existing qualification findings remain independently tracked. |
