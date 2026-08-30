# EMRYS Findings Matrix and Working Backlog

Last reconciled: **2026-08-29**

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

The [architecture backlog matrix](architecture_backlog_matrix.md) records the
original cursory Architecture Priority and Indicative Complexity for campaign
cards. Completed candidates may remain there for ranking traceability. Those
provisional values neither create tasks nor supply the final Importance and
Complexity scores for accepted items in this matrix.

Names, command spellings, phase boundaries, numeric targets, and proposed
ordering quoted from the architecture intake remain suggestions unless this
matrix explicitly adopts them. They must be reconsidered during later slicing
and prioritization rather than silently treated as settled design.

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
project.yaml
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

The current execution-profile cut retires `launcher.yaml`, `resources.yaml`,
and the generated Slurm wrapper from the supported Run path; the remaining
list continues to describe unresolved surface compression.

The ratified compact public conceptual model is:

~~~text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), when operationally relevant
~~~

Run is public and immutably binds one admitted Analysis revision to one
generated, immutable, inspectable internal Execution Plan. Results is a
read-only surface, and Attempt is progressively disclosed for retry, failure,
recovery, or advanced inspection. Dataset, Reference, and
ExperimentalDesign remain scientific-definition sections; Runtime/profile is
operator-facing input to Run construction; Artifact is advanced vocabulary,
Task internal, and Report a downstream Results capability.
`ARCH-MODEL-FIELDS-01` fixes the semantic fields, domain-separated Run-ID
composition, relocation/content/order rules, Attempt envelope, and logical
authorities. The first successor cutover now realizes immutable
Analysis-revision, Execution-Plan, and Run-binding records; persists the Run
binding last as the commit; and migrates current new-Run planning, execution,
resume, and inspection while retaining historical read/resume. Public Project
and Results realization, role-aware APIs/CLI, generalized backend and policy
boundaries, and remaining public/campaign migration remain Open. Workflow/task
now admit exact successor Run authority, reporting inputs are Attempt-owned,
and the temporary successor execution projection is retired.

One illustrative ordinary command surface is:

~~~text
emrys setup
emrys validate
emrys run
emrys inspect
emrys report
~~~

`Project -> Analysis -> Run -> Results`, public Run, and progressively disclosed
Attempt are ratified. The first internal successor Run records and persistence
are implemented. Exact public Project/Results types, role-aware APIs, and
setup/init, validate/check, status/resume, synthetic/demo, inspect, and report
spellings remain Open. The binding requirement is a small coherent
role-appropriate surface, not the illustrative commands above.

Low-level files, Snakemake, owner jobs, task records, receipts, transactions,
and detailed identities may remain internal. Records required by existing
evidence and audit contracts remain inspectable subject to explicit retention
and redaction policy. Every effective operational value and source is
inspectable; an override exists only where its owner defines a safe supported
boundary. Ordinary scientists must not be required to author or operate these
internals.

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
  consolidation, ownership, API, and lightweight collaborator-extension choices
  made just in time under the ratified migration and retirement guardrails;
- no mandatory universal Stage hierarchy, registry, workflow language, or
  second scheduler;
- a complete supported golden path from fresh installation to a valid
  synthetic result;
- role-based scientist, advanced-scientist, operator, and developer interfaces
  implemented through progressive disclosure;
- campaign-level maintenance-surface compression, with concrete consolidation
  and retirement opportunities recorded during every architecture audit and
  implementation slice; and
- immutable-by-default boundary design, with **Run** reserved for the immutable
  plan while every other public noun, nesting choice, API, backend, and policy
  decision remains subject to the applicable post-audit decision gate.

Role-based progressive disclosure is binding, and simplification may not weaken
the underlying guarantees. The
[ratified architectural invariant constitution](../design/decisions/platform-direction.md#ratified-architectural-invariant-constitution)
also binds scientific reviewability, inspectable effective operational values,
safe owner-defined overrides, bounded migration, eventual retirement after
caller migration and parity, and equal-or-stronger surviving defense at real
external, filesystem, concurrency, crash/recovery, persistence, evidence, and
supported public-behavior boundaries. A proven low-risk impossible
same-process check may retire with its check-only test; high-risk, ambiguous,
or directly user-facing protection removal requires explicit approval.
High-risk, directly user-facing, execution-boundary, and evidence-validation
retirement, consolidation, or conversion requires approval whether or not it
is classified as a protection.
The later campaign governance extensions additionally bind maintenance-surface
compression, immutable-by-default design, and separate evidence-deletion
authority. The public conceptual vocabulary and nesting are now ratified;
semantic identity fields and logical authorities are selected, and the first
internal successor records, persistence, and current-path migration are
implemented. Exact expert/public interfaces, public Project/Results types,
generalized layers, backend and policy interfaces, storage relationships,
remaining compatibility migration, and facade use remain Open decisions.

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

### Architecture compression, immutability, and evidence authority

Architecture work follows the canonical
[guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails)
and [per-slice protocol](architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol).
Before design selection, an audit records compression opportunities and mutable
state. An implementation defaults to net-negative maintained product code and
no product-file growth; reports each surface category separately; and stops for
explicit user approval of a quantified exception. Counts cannot be gamed by
moving or weakening responsibility.

**Run is the immutable plan**, and the
[ratified application model and Run boundary](../design/decisions/platform-direction.md#ratified-application-model-and-run-boundary)
govern public vocabulary and Run-versus-Attempt semantics. The campaign's
`ARCH-MODEL-FIELDS-01` decision fixes semantic fields, logical authorities,
Run-ID composition, the symbolic Attempt envelope, and initialization recovery
ownership. The first successor Run-authority boundary now has canonical product
records, versioned schemas, durable Run-last persistence, current-path caller
migration, historical read/resume compatibility, direct workflow/task Run
admission, Attempt-owned reporting inputs, and no successor execution
projection. Public Project/Results, role-aware APIs/CLI, generalized backend
and policy interfaces, and remaining public/campaign migration remain Open. A
surviving equal-or-stronger defense may permit redundant boundary-protection
removal without a one-for-one new test. A proven impossible same-process check
may instead retire with its check-only test and no artificial replacement.
Retained evidence is a separate boundary:
deleting an exact artifact or bounded class requires its own explicit user
approval and commit and cannot offset product growth.

### Closure rule

An item leaves the active matrix only when:

1. Its required outcome is fully implemented.
2. Every acceptance condition is satisfied.
3. Dated evidence is recorded at the correct level. Local engineering,
   cluster/production execution, scientific review, and biological readiness
   remain separate claims.
4. Affected public interfaces, documentation, provenance, and operational
   contracts are updated.
5. An architecture audit or decision slice has recorded its compression and
   mutation inventory; an implementation slice has recorded actual deltas in
   each separate closeout category and the disposition of temporary paths.
6. Any evidence deletion has its exact separate approval and commit; no
   evidence deletion is required merely to satisfy a compression target.
7. A terminal disposition is recorded.

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
| <code>HARNESS-01</code> | P2 | Open | Remove test-aware inputs and test-only production behavior from the no-science orchestration harness while preserving its failure/resume evidence. | Doubles inject simulated science only through test-owned command/effect seams; production dispatch input/output rosters, Run and Attempt semantics, schema vocabulary, lifecycle admission, workflow, receipts, and recovery remain unchanged. No new dispatch has a test-only input role and no production branch is added or relaxed solely for tests. The existing <code>test_payload_manifest</code> inputs and production <code>test-double</code> admission exception are retired or reduced to explicitly owned historical-read compatibility; focused invariance checks prove exactly what the double may replace, and CI retains the controlled partial-failure/resume proof without claiming scientific or real-runtime execution. |
| <code>RUN-01</code> | P1 | Verification pending | Admit normal <code>renv</code> cache-package symlinks consistently across restore, Doctor, and validation. | The real restored library passes focused admission and Doctor checks; dangling, retargeted, or identity-changing links still fail closed. |
| <code>RUN-02</code> | P1 | Verification pending | Complete Step 10 and report execution with default R packages disabled and eliminate similar unqualified base/default-package calls. | The guarded regression, namespace audit, and full Step 10/report path pass in the intended R environment. |

### Public model, operator interface, setup, runtime, and data

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>CONTROL-01</code> | P1 | Open | Realize the ratified compact role-aware public model <code>Project -&gt; Analysis -&gt; Run -&gt; Results</code>, with Attempt progressively disclosed and generated internals hidden from ordinary operation but inspectable. | Project is mutable organizational context; an admitted Analysis revision is immutable scientific intent; public immutable Run binds exactly one Analysis revision to one internal immutable inspectable Execution Plan and owns the primary ordinary ID; Results is read-only; Attempt appears for retry, failure, recovery, or advanced inspection. The first narrow public vertical is implemented: <code>project.yaml</code> and the sole active <code>--project</code> spelling admit immutable source/profile/construction bytes and <code>ProjectAdmission.analysis</code>, then bind that Analysis through the existing Execution Plan and Run to the read-only Results surface. The three temporal admission guards remain; persisted request-era Attempt evidence remains readable. Final Project nesting/persistence, broader public Analysis/Results APIs, role disclosure, storage surface, and remaining migration remain Open. |
| <code>CONFIG-01</code> | P1 | Open | Replace configuration sprawl with one scientist-facing project definition and explicit scientific, execution, and evidence ownership. | One scientist-facing <code>project.yaml</code> is now the active validation/Doctor/Run input, using the existing closed <code>emrys.request.v3</code> shape as a temporary adapter rather than adding a second schema. The operator path collapses launcher/resource files into one optional admitted execution profile; Run-bound resources, Attempt-local placement, and runtime remain distinct. Final Project nesting, generated scientific manifests, runtime/setup generation, discovery, defaults, and precedence remain Open. |
| <code>OPS-01</code> | P1 | Open | Remove the large manually maintained export surface and define a small operator-configuration surface; evaluate named execution profiles as one candidate encapsulation. | The current operator surface is one optional closed execution-profile file plus explicit resource overrides. Its current merge precedence and source/effective provenance are implemented; four old examples plus launcher/resource defaults and the launcher schema are retired. Named profiles, discovery/registry, broader site/project precedence, storage/runtime integration, and the final safe override roster remain Open. |
| <code>OPS-02</code> | P1 | Open | Provide a small role-aware public CLI instead of exposing wrappers, implementation variables, scheduler mechanics, or direct engine controls. | Grouped <code>run</code>/<code>resume</code> now select direct or whole-Run Slurm placement from the admitted profile. On a terminal, direct control displays and confirms the exact frozen Run plan. Slurm constructs one frozen submission plan, displays its placement summary, and submits that same object once after confirmation; the delegate constructs the Run and opens its application log inside the allocation. Refusal, EOF, or interruption precedes every applicable direct or transport mutation. Noninteractive omission of <code>--execute</code> remains no-write/no-submit, while explicit automation prints exact <code>JOB_ID</code>, <code>OUT</code>, and <code>ERR</code>. The generated wrapper is retired. Real scheduler/site and allocation-sensitive outcome parity, broader command simplification, and stable expert routes remain Open. |
| <code>OPS-03</code> | P2 | Open | Inventory inline/generated programs and extract substantive reusable scripts from Python, Make, documentation, and other owners. | Every inline program has an explicit retain/extract disposition; substantive independently testable programs have one owner and direct tests; operators do not run internal helper scripts to complete normal work. |
| <code>OPS-04</code> | P2 | Open | Replace the misleading “local pilot” orchestrator name in the primary product surface. | The stable command and domain name describe execution accurately across CLI, modules, docs, logs, and generated assets, with an explicit compatibility/retirement policy for the old name. |
| <code>SETUP-01</code> | P1 | Open | Generate required draft manifests from supplied input paths without inventing biological relationships. | EMRYS discovers structural input facts, emits deterministic validated drafts, and asks for pairing, strata, conditions, or other biological meaning when they are ambiguous. |
| <code>SETUP-03</code> | P1 | Open | Provide a guided project-creation/setup workflow that prepares a project for normal commands. | Setup collects the minimum project/site facts, creates safe workspace, results, runtime, and log locations, generates derived configuration, validates the prepared project, and never prints or silently invents secrets or biology. Its boundary is project preparation. The broader golden path also requires separately owned installation/runtime, readiness, neutral-synthetic execution, progress/status, recovery, and result-access capabilities. Their exact order, command partitioning, and setup/init spelling remain unsettled. |
| <code>RUNTIME-01</code> | P1 | Open | Evaluate and establish a tiered runtime provisioning and selection model that reduces ordinary setup burden while retaining institutional and advanced paths. | The task chooses and documents the accepted provisioning modes; it considers a reproducible managed option with <code>CONTAINER-01</code>, discovery/admission of institution-provided tools, and explicit advanced definitions without conflating provisioning with execution backend or profile. Qualification covers the complete selected runtime, including Snakemake as an internal engine dependency when applicable and the relevant R environment. Managed/Site/Explicit labels and proposed subcommands remain nonbinding. |
| <code>DOCTOR-01</code> | P1 | Open | Replace user-hostile low-level readiness commands with a project-aware readiness experience; “Doctor” remains the working label until command partitioning is decided. | The accepted readiness surface derives declared workspace/reference/input locations and reports storage, runtime, execution, and input readiness concisely with actionable failures. Runtime readiness includes internal dependencies such as the selected workflow engine without making that engine scientist-authored configuration or the primary execution interface. Default invocation does not mutate project/reference data. Any repair requires an explicit repair action, is previewed or precisely reported, is limited to owned safe state, preserves provenance, never invents secrets or biology, and cannot silently adopt or alter declared scientific inputs. Low-level probes and diagnostics remain available through an advanced route; the split among setup, readiness, validation, and repair commands remains open. |
| <code>RUN-03</code> | P1 | Open | Realize a coherent journey around public Run as the immutable binding of one admitted Analysis revision and one internal immutable Execution Plan while eliminating manual transfer of run roots or internal state between phases. | Scientific-intent and identity-bearing declared-plan changes create a new Run; locator, placement, logging, and report-only changes do not. Re-execution creates an Attempt, which cannot alter or reconstruct Run. A terminal direct <code>run</code>/<code>resume</code> now displays and confirms one frozen Run plan. Slurm instead constructs one frozen submission plan, displays its placement summary, and submits that same object once after confirmation; Run construction follows inside the allocation. <code>--execute</code> remains the explicit noninteractive path. Scientific Attempts stop at <code>cohort_slice</code>, release their lock, and publish receipt v2 before default downstream reporting. <code>--no-report</code> disables only reporting; <code>emrys report</code> plans, generates, or reuses it independently; reporting creates neither Run nor Attempt and cannot change scientific success. Low-level build commands and the composite workflow tail are retired. Current Run authority, historical read/resume, separated Results/reporting, single-invocation terminal control, and controlled planning parity are implemented. Real placement/outcome parity, generalized realization, and remaining public migration remain Open. |
| <code>IDENTITY-01</code> | P2 | Open | Realize the ratified smallest role-appropriate identity model while preserving detailed identities as evidence metadata. | Ordinary users need one primary Run ID; Analysis may be human-named while retaining internal immutable identity; Attempt ID is surfaced only when truthful retry, failure, recovery, or advanced inspection requires it. Relocation-independent Analysis/Execution-Plan identities and the domain-separated Run digest over their canonical digests are now implemented for successor Runs; human aliases, raw formatting/order, paths, Attempt facts, reporting, and backend-adapter-only code are excluded. Historical-reader mechanics preserve existing Runs, and the successor execution projection is retired. Ordinary public exposure, progressive disclosure, and remaining public migration remain Open. Existing commit, package, runtime, request, task, artifact, receipt, and publication identities remain detailed evidence metadata, and no subsystem may reconstruct a competing Run identity. |
| <code>FILESYSTEM-01</code> | P2 | Open | Define a stable generated public storage model with one discoverable scientist-facing result surface and decide its relationship to the proposed Run Bundle. | Completed <code>RESULTS-01</code> provides the single current scientist-facing result/report surface with no competing current report root. The remaining outcome makes provenance, work, artifacts, logs, and all owned directories predictable and automatic, with no manual assembly; exact broader public labels, nesting, bundle layout, portability, archival, and sharing semantics remain Open. |
| <code>CONTAINER-01</code> | P2 | Open | Independently evaluate a supported managed container/environment option without coupling it to guided setup or assuming the final runtime taxonomy. | The decision covers scheduler integration, storage, architecture, security, reproducibility, tool and R-library contents, licensing, image and per-tool provenance, updates, coexistence with institutional/native/advanced runtime paths, and escape hatches; any implementation has explicit local and site acceptance evidence. |
| <code>FUT-DATA-02</code> | P3 | Deferred | Provide explicit retryable public-reference and SRA-read acquisition with provenance and content identity. | Reference and read acquisition remain separate; version/accession, source, hashes, cache, retry, partial transfer, and storage identity are recorded without scraping, silent updates, or implicit trust. |
| <code>FUT-INDEX-01</code> | P2 | Open | Safely admit and reuse an explicitly declared prebuilt STAR index instead of regenerating it. | Required index members are bound to FASTA/GTF identities, STAR parameters and version, and exact content hashes; mere directory existence never authorizes reuse, repair, merge, or mutation. |

### Usability, logging, and progress

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>REVIEW-UX-03</code> | P1 | Open | Independently review scientist, advanced-scientist, operator, developer/maintainer, and automation journeys against the non-negotiable simplified golden path. | The review covers fresh installation through valid synthetic result, findability, terminology, concepts required, configuration burden, progressive disclosure, accessibility, failure diagnosis and recovery, console/report hierarchy, intake, local/HPC context, and the ratified inspectable-effective-value and safe-override boundaries plus role-appropriate escape hatches without changing scientific meaning. It records baseline and target measures without treating source-proposed numeric targets as already accepted. |
| <code>LOG-05</code> | P1 | Open | Activate concise role-appropriate default logging using the implemented foundation, incrementally across every retained applicable operation. | Grouped <code>run</code>/<code>resume</code> execution owns one compute-side application attempt under <code>&lt;workspace&gt;/logs/application</code>; automatic reporting continues in that same log after scientific receipt publication. Standalone executing <code>report</code> owns one reporting application log, while report dry-run/reuse, valid Run dry-run, and scheduler submission own none. Normal output is concise, verbose adds allocation detail, debug adds exact safe commands, and bounded failures identify durable logs and owned recovery paths. Receipt-last evidence remains authoritative and logging degradation cannot change scientific/reporting behavior or exit. The card remains Open for other retained applicable operations and required parity. |
| <code>OBS-01</code> | P1 | Complete | Remove low-value console noise from the default user experience. | Grouped <code>run</code>/<code>resume</code> normal output now shows concise Run identity, combined pending/reusable work, automatic reporting, meaningful phases, verified Results/evidence, warnings/failures, and the durable log path. Verbose adds the Run root, resources/allocation, execution profile, and scheduler streams; debug adds exact safe engine, scheduler, and task commands. Exact scheduler <code>JOB_ID</code>/<code>OUT</code>/<code>ERR</code>, durable JSONL fields, receipts, exits, evidence boundaries, and no-write/no-log dry runs remain unchanged. |
| <code>OBS-02</code> | P1 | Complete | Provide a supported high-level progress, status, and recovery-guidance surface while hiding the internal execution/publication state machine. | The read-only inspect route independently reports Run integrity, scientific Attempt outcome, five persisted-authority scientific milestones, scientific Results, downstream reporting, recovery, domain-specific blockers, one deterministic next action, and verified report locations. Current/latest Attempt elapsed time never sums resumes or infers ETA. Normal output hides engine internals; verbose adds operational aggregates; debug exposes admitted scheduler, engine, transaction, receipt, task, stream, and record detail. Inspection writes nothing. The stale dashboard received no update and retirement remains deferred until campaign completion and separate approval. |

#### LOG-05 adoption and closure guard

Planning, retained-surface inventory, attempt-owner mapping, and reusable
conformance and parity-harness work may precede production adoption and need not
wait for unrelated campaign work. Production adoption occurs only in a
separately approved bounded slice for a retained semantic operation or an
explicitly approved transitional compatibility operation. Before or within the
slice, it must identify the operation's role, exactly one application-attempt
owner and its delegates, role-appropriate identity and entry-point
compatibility, durable log placement, truthful milestone/failure/recovery
projection, stdout contract, and applicable Local/SLURM responsibility and
parity evidence. The slice may settle those bounded decisions but may not
silently adopt a nonbinding campaign suggestion.

Every implementation slice touching a retained applicable operation records
its `LOG-05` disposition. If that slice changes human output or a durable
diagnostic path, the approved vertical includes adoption rather than adding a
temporary logger, log format, wrapper-owned attempt, or second console
convention. A proven not-applicable or retiring operation does not adopt merely
to advance closure.

A transitional compatibility adoption does not satisfy final retained-operation
coverage, and an unapproved retiring surface is out of scope. <code>LOG-05</code>
remains Open until every operation in the reviewed application surface is
either adopted when retained and applicable or explicitly dispositioned as
retired or not applicable, and every adoption has the required evidence. A
claimed complete golden-path capstone requires current <code>LOG-05</code>
closure evidence. These are slice-admission and capstone-acceptance conditions,
not blocker edges or an overall campaign order.

### Analysis modularity and overall architecture

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>ANALYSIS-01</code> | P1 | Open | Allow one project to stop after compatible per-sample processing and launch separately identified cohort, subset, sensitivity, or downstream analyses from the reusable Step 06 boundary. | Compatible Steps 00–06 artifacts are content-bound and reused without mutation; cohort-dependent Steps 07 onward receive a distinct analysis/run identity, outputs, evidence, and report; incompatible reuse fails closed. Physical realization remains unsettled: stationary admitted paths are the lowest-footprint candidate, while retained copy, qualified scratch copy, reflink/native snapshot, and future content-addressed storage remain alternatives under <code>AC-SUG-016</code>. Copying alone is neither identity nor compatibility proof. |
| <code>ANALYSIS-02</code> | P2 | Open | Provide a versioned collaborator-extensible analysis library/module interface within the binding prohibition on a mandatory universal Stage hierarchy, registry, workflow language, or second scheduler. | Modules declare typed inputs/outputs, dependencies, validation, provenance, trust level, failure semantics, resource needs, and report integration; adding a differential analysis does not require editing the scientific core or unrelated owners. Algorithms, parameters, assumptions, biological interpretation boundaries, and implementation needed for scientific review remain recognizable and inspectable across the module boundary. The task decides the lightweight extension API and may share execution, filesystem, provenance, or scheduler adapters only where a demonstrated repeated responsibility moves to one owner with bounded caller migration and net reduction. |
| <code>ARCH-01</code> | P2 | Open | Establish formal architectural layers and dependency direction, introduce deliberate application/infrastructure abstractions, and aggressively reduce maintained surface and cross-module coupling while preserving every declared invariant. | Completed prerequisites and current vertical migrations now include immutable Run authority, separated read-only status, grouped Run control, immutable request-to-Analysis intake, and one bounded execution/configuration cut: split launcher/resource configuration and the generated wrapper retire in favor of one execution-profile owner, one private Slurm transport, and grouped control. Run remains immutable, placement/diagnostics remain Attempt-local, and no second backend, scheduler, or facade is introduced. <code>ARCH-01</code> remains Open for the public application/operation surface; policy, identity, artifact/storage, Project/Results, generalized backend, package, and remaining caller migrations. The Section 13.1 compression, mutation, protection, shell, <code>LOG-05</code>, and evidence-deletion gates remain binding. |

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
| <code>REPORT-03</code> | P1 | Verification pending | Remove low-value report material and establish explicit scientific, evidence, and operational report audiences with a primary-findings-first default hierarchy. | The two receipt-bound HTML files now answer the three accepted questions through fixed relative navigation: the primary scientific report answers what was found; Evidence and provenance answers why it is trustworthy; Operations answers how execution proceeded. Run overview remains intact, both former provenance sections live under Evidence, and Attempt lineage lives under Operations. No third artifact, command, schema, or filesystem surface was added. Rendered visual/user acceptance remains pending. |
| <code>REPORT-04</code> | P1 | Open | Support an A-through-I selected-candidate/panel roster when the admitted result warrants nine items. | At least nine admitted selections render without silent truncation, label collision, inaccessible content, or print/layout failure; any larger-display limit is explicit and evidence-bound. |
| <code>RESULTS-01</code> | P1 | Complete | Publish one discoverable scientist-facing result bundle beneath the canonical run-relative results surface and make it the ordinary entry point into the broader Run Bundle. | Current Runs expose only editing results, scientific context, and both receipt-bound reports beneath <code>&lt;run-root&gt;/results</code>; 56 nonfinal/QC artifacts live beneath <code>products/native</code>, with no copy, symlink, competing report root, or new index/manifest. Both reports link portably to the admitted ranked, complete, and candidate-context tables, and Evidence and operations retains the existing inspect command. Exact legacy-profile report ledgers remain readable at <code>products/report</code> only as historical evidence. The fixed-profile change intentionally gives new Runs new identities; historical Runs remain inspectable but are not automatically resumable under the current profile. <code>FILESYSTEM-01</code> and <code>AC-SLICE-11</code> remain Open for the broader storage and portable Run Bundle contracts. |

### Documentation, backlog, demo, and maintenance tooling

| ID | Priority (provisional) | Status | Required outcome | Acceptance |
|---|---|---|---|---|
| <code>DOC-01</code> | P1 | Open | Condense retained documentation and reorganize it around scientist, operator, and developer journeys without requiring campaign history or developer-only context. | Scientist guidance covers purpose, inputs, project definition, the golden path, results, and scientific limitations; operator guidance covers runtime, profiles, storage, scheduler, diagnosis, and recovery; developer guidance retains exact architecture, contracts, evidence, and internals. Each retained document states purpose, pipeline role, when it is needed, primary interface/output, and canonical contract owner; B2/B4, campaign, phase, and similar shorthand is replaced with meaningful content. Successful ordinary use does not require reading developer architecture. After the architecture campaign closes, the documentation-compression pass evaluates replacing duplicated machine-verifiable Markdown contract material with versioned executable specifications and generated references, while retaining concise prose for intent, authority, evidence meaning, trust boundaries, non-goals, rationale, and migration; implementation code must not become its own specification, and independent conformance checks remain required. |
| <code>DOC-04</code> | P1 | Open | Reconcile every section of <code>HANDOFF.md</code>, preserve all uniquely valuable dated evidence and durable recovery constraints, discard its blockers/current-resume prose, and retire the rolling handoff surface. | A section-level source-to-destination/discard trace covers the VM, renderer/report derivative, PORT-NC-01, Viking Step 07–09, cohort/Step 03, artifact-identity, local-R-recovery, blocker, and resume material; retained history records preserve exact source commits, commands, hashes/artifacts, dates, and evidence ceilings; live recovery facts move to their owner only after verification; claims are not promoted; blockers and takeover instructions are discarded only after reconciliation; every inbound route and structure roster is updated before <code>HANDOFF.md</code> is deleted. |
| <code>DOC-05</code> | P1 | Open | Consolidate useful orchestration-admission safeguards into live owners and retire the remaining stale transition source. | The launcher transition plan is retired in the execution-profile cut: current safeguards live in execution-profile, transport, onboarding, package, contract, test, CI, runbook, and configuration owners, while obsolete <code>.env</code>, generated-wrapper, split-config, and Bash-3.2 instructions remain only in Git history. <code>ORCHESTRATION_READINESS.md</code> still requires its own consolidation and retirement, so <code>DOC-05</code> remains Open. |
| <code>TOOLING-01</code> | P2 | Open | Complete the exact history-backed disposition of the retired <code>scripts/git_orchestration/</code> namespace after <code>BACKLOG-01</code> and <code>DOC-TOOL-01</code> without adding a permanent guard against its implausible return. | Every former file and caller is accounted for; useful documentation validation remains under its live owner; no useful behavior, product caller, public route, tracked generic Git-orchestration path, or live operational reference remains. The namespace stays absent, its historical trace remains documentation, and no check-only return protection is added. |
| <code>CLEAN-01</code> | P2 | Open | Retire the historically coupled “demo” product surface without losing a neutral supported synthetic golden path or necessary reporting validation. | Demo Make targets, docs, fixtures, tests, links, and public references are inventoried and removed, renamed, or moved to neutral synthetic-example/test/preview ownership; a fresh installation can still produce a valid synthetic result through the accepted golden path; no historical “demo” state remains in the primary product surface unless that name is deliberately reconsidered and accepted later. |
| <code>CLEAN-02</code> | P2 | Open | Reconcile and retire the obsolete non-runnable Step 04 scaffold under <code>tests/pending/</code>. | Every intended check in <code>tests/pending/test_step_04_mark_duplicates.sh</code> is mapped to the active duplicate-marking owner suite or moved there if still unique; <code>tests/pending/README.md</code>, the scaffold, inbound links, and the <code>RETAIN_ROOT</code> inventory exception are removed; a retired-surface guard prevents the duplicate planning area from returning. |

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
| <code>CONTROL-01</code>, <code>REVIEW-UX-03</code> | The public surface must become substantially simpler and use progressive disclosure for scientist, advanced-scientist, operator, and developer roles. <code>ARCH-MODEL-DECISION-01</code> ratifies <code>Project -&gt; Analysis -&gt; Run -&gt; Results</code>, with Attempt progressively disclosed; Execution Plan internal/inspectable; Dataset, Reference, and ExperimentalDesign as scientific-definition sections; Runtime/profile operator-facing; Artifact advanced; Task internal; and Report downstream beneath Results. The first narrow Project vertical now exposes the selected noun through <code>project.yaml</code>, validation, Doctor, and Run without exposing generated records as the ordinary interface. | Simplification preserves guarantees. Every effective operational value and source remains inspectable, while only owner-defined safe values are overrideable. Final Project nesting/persistence, expert interface, safe override roster, broader role-aware Analysis/Results APIs, generalized storage, remaining compatibility migration, percentages, and concept-count targets remain Open. |
| <code>CONTROL-01</code>, <code>RUN-03</code>, <code>IDENTITY-01</code>, <code>ARCH-01</code> | The completed audit and decisions selected model C, the Run/Attempt boundary, exact semantic fields, domain-separated identities, symbolic resource envelope, logical authorities, recovery ownership, and separated status domains. Current Project admission freezes exact source/profile/construction bytes and immutable Analysis authority, and <code>RunCandidate.project.analysis</code> connects that value to canonical Analysis-revision, Execution-Plan, and Run-binding records committed Run-last. Workflow/task admit exact Run authority; reporting inputs are Attempt-owned and origin-bound; historical read/recovery remains; no successor execution projection remains; read-only inspection separates Run integrity, scientific Attempt outcome, Results, reporting, and recovery; grouped Run control is the only supported control surface; and successor Attempts derive executor provenance from their immutable Execution Plan while allocation placement remains Attempt-local. | The current <code>emrys.request.v3</code> record remains a temporary Project adapter. Final Project schema/persistence, broader public Analysis/Results APIs, generalized backend/policy boundaries, remaining migration, and broader logging adoption/parity remain Open. Private planning helpers are not automatically public, persisted request-era evidence remains readable, and no evidence deletion is authorized. |
| <code>CONFIG-01</code>, <code>OPS-01</code>, <code>RUNTIME-01</code> | Scientific intent, execution/site policy, and EMRYS-owned evidence configuration have different authors. One explicit file-bound execution profile now combines current resource declaration and direct/Slurm placement with deterministic precedence and provenance, while runtime provisioning remains separate. Named-profile taxonomy/registry and Managed/Site/Explicit runtime labels remain proposals. | Future taxonomy and higher-level management must preserve inspectable effective values/sources, owner-defined safe overrides, and runtime/readiness qualification of internal dependencies such as Snakemake without exposing engine configuration as an ordinary scientist task. |
| <code>OPS-02</code>, <code>SETUP-03</code>, <code>DOCTOR-01</code>, <code>RUN-03</code>, <code>OBS-02</code>, <code>LOG-05</code>, <code>RESULTS-01</code>, <code>CLEAN-01</code> | Together these rows own the required golden-path capability set: supported installation/runtime, readiness diagnosis, project creation and validation, neutral-synthetic execution, useful progress/status, safe recovery, and discoverable valid results. The ordinary path must not require manual directory creation, run-root copying, scheduler scripts, engine state, transaction states, or forensic identities. | The capability set and successful end state are binding; no exact ordering is adopted because the sources propose different sequences. No one row can claim the complete golden path from its segment alone. Diagnosis is the default while repair is explicit, bounded, safe, and provenance-aware. The active Project intake spelling is settled; remaining command partitioning and higher-level setup/discovery are not. |
| <code>ARCH-01</code>, <code>ANALYSIS-02</code> | Formal layering and deliberate abstractions are non-negotiable. The five-band proposal is ratified as responsibility clusters rather than package topology, with separate source-import, runtime/control-invocation, and artifact/evidence-flow graphs. The public model, Run/Attempt boundary, semantic identity fields, logical authorities, and recovery/status separation are selected; the first internal successor records, persistence, and current-path migration are implemented. Public/generalized storage and product realization plus candidate Stage, Artifact lifecycle/Store, and policy representations remain for bounded decisions after the recorded ownership/mutation/compression audit. | Higher-to-lower responsibility direction, forbidden authority transfers, explicit current source-owner classification, and exact stale-failing CLI-composition and transitional-import rosters are binding. Public/generalized classes/APIs, package realization, Artifact Store ownership, remaining migrations, and facade use remain Open. A mandatory universal Stage hierarchy, registry, workflow language, or second scheduler is prohibited; the lightweight collaborator-extension mechanism remains Open. Every audit records compression and mutable-state opportunities, every touched shell receives a `KEEP`/`CONVERT`/`RETIRE` disposition, and every implementation reports category-separated deltas under the default net-negative/no-product-file-growth rule. External, filesystem, concurrency, crash/recovery, persistence, evidence, and public-behavior protections require mapped equal-or-stronger surviving defense; a proven low-risk impossible same-process check may retire with its check-only test. High-risk, directly user-facing, execution-boundary, and evidence-validation retirement, consolidation, or conversion requires explicit approval whether or not classified as protection. Protections and evidence remain distinct; deleting exact evidence requires separate user approval and a separate commit. |
| <code>IDENTITY-01</code>, <code>FILESYSTEM-01</code>, <code>RESULTS-01</code> | One coherent inspectable package should associate the immutable Run plan with its configuration, identity, artifacts/results, evidence, logs, and reports without turning Run into a mutable execution container. Public identity is one ordinary Run ID with Attempt progressively disclosed; detailed identities remain evidence metadata. | “Run Bundle” and “Artifact Store” are proposed abstractions, not settled public nouns, owners, on-disk schemas, or portability guarantees. Scratch/work state is not promoted into the scientist-facing result merely for structural symmetry. |
| <code>REPORT-03</code>, <code>RESULTS-01</code> | Reporting serves three explicit questions: scientific—what was found; evidence—why the result is trustworthy; operational—how execution occurred. The current realization uses one primary scientific HTML and one combined Evidence and operations HTML, with fixed relative destinations in both. | The two receipt-bound outputs share Run identity and provenance but do not force operational/evidence detail into the primary scientific narrative. Provenance is grouped under Evidence and Attempt lineage under Operations. Completed <code>RESULTS-01</code> co-locates them with admitted scientific result tables beneath the canonical results surface; <code>REPORT-03</code> still requires rendered acceptance. |
| <code>DOC-01</code>, <code>REVIEW-UX-03</code> | Documentation and review follow the role journeys: scientists reach a result and interpretation first; operators provision, qualify, schedule, diagnose, and recover; developers inspect architecture and exact contracts. | Developer architecture remains available, but reading it cannot be a prerequisite for ordinary scientific use. |
| <code>CONTAINER-01</code>, <code>RUNTIME-01</code> | A managed image/environment may provide the easiest supported runtime and bind an image digest plus enumerated tool identities into provenance. | Containerization remains independent of guided project setup and supplements rather than automatically replacing the institutional, native, or advanced runtime paths accepted by <code>RUNTIME-01</code>. |
| <code>ARCH-01</code>, <code>DOC-04</code>, <code>DOC-05</code>, <code>TOOLING-01</code>, <code>CLEAN-01</code>, <code>CLEAN-02</code> | Cleanup is an architectural deliverable: every audit records compression opportunities across duplicate validators, lifecycle implementations, stage-specific infrastructure, migration adapters, compatibility paths, generic ownership buckets, stale documentation, superseded test scaffolds, shell/generated-shell surfaces, and retained evidence, then proposes retain, relocate, consolidate, retire, convert, or approval-required evidence-deletion dispositions. | Durable scientific, operational, provenance, recovery, testing, and documentation-validation value moves before retirement. Eventual retirement after caller migration, relevant parity, and an explicit condition is binding. Boundary protections require mapped equal-or-stronger surviving defense, while a proven impossible same-process check may retire without an artificial replacement. High-risk, ambiguous, directly user-facing, execution-boundary, and evidence-validation changes require explicit approval; exact evidence deletion separately requires explicit approval and a separate commit. <code>AC-DEC-018</code> decides each compatibility window, warnings, fixtures, and removal evidence; <code>AC-DEC-020</code> decides ordering. Completed <code>DOC-03</code> supplies an accepted retirement example; <code>TOOLING-01</code> remains a bounded history audit without a return-guard requirement. |

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
profiles, execution-profile material, run identities, and evidence
manifests internally. Generated artifacts remain inspectable and
content/provenance bound; scientists are not required to author them.

The accepted design requires one documented, inspectable precedence contract:
every effective operational value and source is inspectable, and an override
exists only at an owner-defined safe supported boundary. One proposed ordering
is:

~~~text
built-in defaults -> site/execution profile -> project request -> CLI override
~~~

Exact merge order, safe override roster, and list/map/null semantics remain
open.

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

The example labels are not settled vocabulary. Every effective operational
value and source is inspectable, but the owning contract decides which values
are safe to override and through which role-appropriate interface. Exact
override scope, terminology, and provenance presentation remain open.

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

### Ratified identity model and source-proposed filesystem example

The public conceptual hierarchy is:

~~~text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), progressively disclosed
~~~

Commit, package, runtime, request, artifact, and receipt identities remain
complete metadata under the appropriate Run/Attempt/artifact evidence
boundary. Exact field nesting, digest inputs, and subordinate identity exposure
remain Open; existing evidence identities remain preserved.

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

The conceptual model is settled, but this exact layout remains Open. The
binding general outcome is automatically prepared, predictable locations, one
discoverable scientist-facing Results surface, and no hidden competing report
root.

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

## Documentation audit decisions

The completed <code>DOC-02</code> audit covers all 170 tracked Markdown sources
and six diagrams. Its individual <code>docs/</code> roster and exhaustive
owner-partition dispositions live in the
[repository-and-delivery decision record](../design/decisions/repository-and-delivery.md#repository-documentation-audit-2026-08-25).
The named candidates have these accepted dispositions:

| Source | Accepted disposition | Execution owner |
|---|---|---|
| <code>docs/architecture/FUTURE_ARCHITECTURE.md</code> and two future diagrams | Retired after node-level reconciliation; the [durable trace](../design/decisions/repository-and-delivery.md#doc-03-source-to-destination-trace-2026-08-25) remains in the repository decision record | Completed <code>DOC-03</code> |
| <code>docs/design/PIPELINE_PLAN.md</code> and <code>docs/design/QUESTIONS.md</code> | Retired after [section/item reconciliation](../design/decisions/repository-and-delivery.md#doc-03-source-to-destination-trace-2026-08-25) to the matrix, campaign, decisions, contracts, site-state disposition, or Git history | Completed <code>DOC-03</code> |
| <code>docs/operations/HANDOFF.md</code> | Trace every section; move unique dated evidence to history and verified recovery facts to live owners, discard blockers/takeover prose after reconciliation, then retire | <code>DOC-04</code> |
| <code>docs/design/ORCHESTRATION_READINESS.md</code> | Consolidate missing safeguards into live owners, discard stale transition material, then retire | <code>DOC-05</code> |
| <code>docs/operations/LOCAL_PILOT_LAUNCHER_TEST_PLAN.md</code> | Retired after current safeguards moved to final execution-profile, transport, grouped-control, onboarding, test/CI, runbook, and configuration owners; obsolete transcript material remains in Git history | Partial <code>DOC-05</code> execution-profile cut |
| <code>docs/tasks/BACKLOG.md</code> and <code>docs/tasks/cards/README.md</code> | Retired | Completed <code>BACKLOG-01</code> |
| <code>docs/tasks/README.md</code> | Retain as compact task-planning index | Completed <code>BACKLOG-01</code> refresh |
| <code>docs/demo/</code> | Retire or rehome while preserving a neutral supported synthetic path | <code>CLEAN-01</code> |
| <code>tests/pending/README.md</code> and its Step 04 scaffold | Trace against the active owner test and retire the duplicate pending surface | <code>CLEAN-02</code> |
| <code>scripts/git_orchestration/README.md</code> | Removed after the useful validator moved to its documentation owner | Completed <code>DOC-TOOL-01</code> |

The two not-yet-retired sources are visibly marked legacy and are not current
authority. Live Git owns checkout state; exact checks and retained artifacts
own validation observations; this matrix owns accepted work and acceptance;
the temporary campaign owns unsliced alternatives; owner contracts, the
runbook, troubleshooting, and test policy own behavior, recovery, commands,
and evidence meaning. The later role-journey rewrite remains <code>DOC-01</code>.

## Dated evidence ledger

| Date | ID or scope | Observation | Evidence level |
|---|---|---|---|
| 2026-08-29 | <code>RUN-03</code> single-invocation Run journey | With terminal input and a terminal-visible plan stream, direct <code>run</code>/<code>resume</code> now displays one frozen Run plan, reads one confirmation, and executes that exact object only after consent. Refusal, EOF, interruption, noninteractive input, or redirected plan output returns before every workspace, application-log, lifecycle, or reporting mutation. Noninteractive <code>--execute</code> remains the explicit automation/private-delegate path and retains log-first semantic preflight. Whole-Run Slurm instead constructs one frozen submission plan, displays its placement summary, and after confirmation creates scheduler streams and passes that same object to <code>sbatch</code> once; immutable Run construction and application logging remain compute-side after job-ID admission. Default reporting, <code>--no-report</code>, independent report regeneration/reuse, receipts, recovery, and result discovery are unchanged. Duplicate Run/Resume option definitions, no-write rendering, and public control-error rendering consolidate without removing any scheduler, filesystem, lifecycle, signal, recovery, reporting, evidence, or historical-reader defense. Category-separated pre-commit actuals: maintained product Python one existing file <code>+56/-62</code>, net <code>-6</code>, with no product-file growth; protections/tests one existing file <code>+177/-22</code>, net <code>+155</code>; configuration/schema/workflow zero; documentation eight existing files <code>+163/-89</code>, net <code>+74</code>; retained evidence zero added, rewritten, moved, or deleted; public surface zero commands, flags, schemas, backends, package exports, compatibility paths, call edges, or nouns added; mutable Run state zero. Direct application-log/lifecycle/reporting state and Slurm submission/stream transport state retain their distinct owners. <code>RUN-03</code>, <code>OPS-02</code>, and broad <code>ARCH-01</code> remain Open for real placement/outcome parity, generalized realization, remaining command simplification, and public migration. | Focused local engineering evidence: 15 terminal/nonterminal, exact-plan, no-write/no-log, Resume, Slurm, explicit-preflight-log, and reporting cases passed; 126 public-CLI and scheduler-transport tests passed with three environment skips; all 39 documentation-structure tests passed; targeted Ruff and <code>git diff --check</code> passed. A deliberately stopped aggregate local materialization run is not acceptance evidence; clean aggregate, fresh-clone, real-tool, and extended synthetic validation remain CI work. No real <code>sbatch</code>, allocation, CSU/site/cluster execution, production data, rendered user acceptance, scientific review, or biological validation was performed or inferred locally. |
| 2026-08-28 | <code>AC-SLICE-05</code>/<code>AC-SLICE-08</code>/<code>AC-SLICE-17</code> execution-profile and whole-Run placement cut | One admitted execution-profile format now owns current resource declaration plus direct/Slurm placement; grouped <code>run</code>/<code>resume</code> use the packaged direct default or one explicit profile, submit whole-Run Slurm placement once through a private transport, and adopt <code>LOG-05</code> on the compute-side operation. The generated wrapper, launcher owner/schema/default, split resource/launcher defaults and four examples, dedicated launcher tests, and stale launcher transition plan retire. Run remains immutable; computational declaration remains Run-bound; profile source, placement, allocation, scheduler job ID, logging, queue, and scratch remain Attempt/transport facts. The private minimal batch bootstrap remains <code>KEEP</code>; sixteen owner-local <code>.slurm</code> paths and the stale dashboard remain unchanged. All routed cards remain Open for their broader outcomes. Category-separated actuals from <code>1abbf094</code>: maintained product Python 12 files, <code>+1496/-1704</code>, net <code>-208</code> lines, with the approved two-owner replacement adding one net product file while deleting the launcher monolith; protections/tests/tooling 21 files, <code>+2104/-2036</code>, net <code>+68</code>, with launcher-only/impossible-state checks retired and final-owner boundary defenses retained; configuration/schema/workflow 14 files, <code>+452/-584</code>, net <code>-132</code> and two fewer maintained files; documentation 18 files, <code>+700/-763</code>, net <code>-63</code>, including retirement of the non-authoritative launcher transcript; whole slice <code>+4752/-5087</code>, net <code>-335</code>. Retained evidence changed by zero; historical records remain readable; no evidence deletion was proposed or performed. | Focused local engineering evidence: 180 execution-profile, resource, scheduler-transport, onboarding, orchestration-contract, logging-control/adoption, and source-authority tests plus 15 selected materialization/lifecycle boundary tests passed; lint, source-dependency enforcement, documentation structure, direct documentation-owner tests, and <code>git diff --check</code> passed. Full CI remains the aggregate acceptance gate. No real <code>sbatch</code>, Slurm allocation, CSU/site run, production-data execution, scientific review, or biological validation was performed or inferred locally. |
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
| 2026-08-25 | <code>BACKLOG-01</code> | The legacy backlog, task-card guidance, status renderer, registry parser, and live callers were removed; canonical planning now routes only through this matrix, with retired surfaces and the matrix owner protected by the documentation gate. | Focused local evidence: documentation gate passed; documentation-validator and affected public-interface tests passed, 12 tests total |
| 2026-08-25 | <code>DOC-TOOL-01</code> | The retained structure checks moved from the generic Git-orchestration bucket to <code>scripts/documentation/validate_structure.py</code>; the owner now documents its exact checks and non-goals, and seeded tests cover every retired surface plus canonical, adjacency, inventory, and Mermaid failures. | Focused local evidence: relocated documentation gate passed; documentation-owner, public-interface, and Make-expansion tests passed, 32 tests total |
| 2026-08-25 | <code>DOC-02</code> | All 170 tracked Markdown sources, six Mermaid sources, named retired candidates, and inbound routes to the six stale sources received evidence-based individual or exhaustive owner-partition dispositions. Current authority now routes to live Git, exact checks/artifacts, this matrix, the temporary campaign, and subject owners; all six legacy pages and two future diagrams remain mechanically protected until <code>DOC-03</code>–<code>DOC-05</code> execute the accepted migrations. | Current Git/source/reference audit plus focused local evidence: documentation gate passed; documentation-owner, public-interface, and Make-expansion tests passed, 46 tests total; no retirement migration or scientific/runtime proof performed |
| 2026-08-25 | <code>DOC-03</code> | Every section of the future-architecture, pipeline-plan, and question-index pages and every node/edge of both future diagrams received an explicit preserve/discard destination. Two unique nonbinding choices moved to the campaign; five stale sources retired; live routes and latest-head logging status were reconciled; runtime/site claims were routed without promotion; and the gate now protects all five retired paths while retaining three pending transition pages. | Focused local documentation evidence: structure gate passed at 168 Markdown and four Mermaid sources; documentation-owner, affected public-interface, and Make-expansion tests passed, 43 tests total; Ruff and <code>git diff --check</code> passed. No long aggregate, runtime, cluster, scientific-review, or biological evidence was produced. |
| 2026-08-25 | <code>LOG-03</code> | The neutral [application-logging owner](../../src/emrys/libraries/application_logging/README.md) implements the [binding two-sink foundation](../design/LOGGING_CONTRACT.md). No production command or wrapper adopts it; that rollout remains <code>LOG-05</code>. | Hosted [Phase 1 CI run #43](https://github.com/lab-cats/EMRYS/actions/runs/32888179176) passed on exact implementation-and-documentation head [<code>c6aee017</code>](https://github.com/lab-cats/EMRYS/commit/c6aee017f0d1982627782e40f3efa01eef908ad9). Engineering evidence only; no production-command adoption, real scheduler or cluster execution, scientific review, or biological proof is claimed. |
| 2026-08-26 | <code>ARCH-CONST-01</code> | All 27 campaign invariant candidates were reconciled to live contracts, decisions, implementation boundaries, representative regression routes, and named gaps. The durable register distinguishes scoped current <strong>Preserved</strong> contracts from binding <strong>Target</strong> requirements with named current gaps, and five abstraction/migration/test guardrails are ratified. No command, API, class, schema, layer map, filesystem layout, runtime, scheduler, scientific method, or performance behavior changed; broad <code>ARCH-01</code> remains Open. | Current source/contract/test audit plus focused local documentation evidence: structure gate passed at 168 Markdown and four Mermaid sources; documentation-owner, affected public-interface, and Make-expansion tests passed, 43 tests total; <code>git diff --check</code> passed. Representative scientific, lifecycle, artifact, reporting, and onboarding tests were inspected but not executed. No long aggregate, runtime, cluster, production, scientific-review, or biological evidence was produced. |
| 2026-08-26 | <code>ARCH-LAYER-01</code> | The five campaign bands are ratified as responsibility clusters rather than package topology; source imports, runtime/control invocation, and artifact/evidence flow are distinct graphs; nine forbidden authority-transfer/classification rules and the current-owner crosswalk have durable owners. The Python source-boundary gate now fails closed on unclassified domains, forbidden declared imports and recognized literal standard-library dynamic import forms, cross-owner private access, undeclared or stale grouped-CLI composition seams, exact transitional imports, and cycles between neutral library owners. Its executable roster is 28 current CLI seams plus 13 transitional edges and is directly checked against the documented topology. Concrete application/operation/execution/policy/artifact APIs, package realization, and migrations remain Open under <code>ARCH-01</code> and later slices. | Current source/contract audit plus focused local evidence: documentation structure passed at 168 Markdown and four Mermaid sources; the read-only source gate passed over 169 Python sources and 452 EMRYS import edges with all 28 composition seams and 13 transitions observed; 44 focused source-boundary, validation-orchestrator, and affected Make/public-interface tests passed; targeted Ruff and <code>git diff --check</code> passed. The local tests used the existing sibling CI worktree environment because this worktree has no <code>.venv</code>; no dependency was installed or restored. No long aggregate, R/runtime, scheduler, cluster, production, scientific-review, or biological evidence was produced. |
| 2026-08-26 | <code>ARCH-LAYER-01</code> reduction follow-up | The source-boundary implementation and its focused tests were reduced from 1,378 to 770 physical lines without changing the ratified import projections, exact 28-seam and 13-transition ratchets, documented-successor parity, owner-level cycle scope, or diagnostics. Result/count plumbing, duplicated executable successor metadata, roster object models, custom cycle traversal, and redundant tests were removed; no product source or public interface changed. | Focused local evidence on the compact implementation: the live read-only gate passed over 169 Python sources and 452 EMRYS import edges; all 43 source-boundary and validation-orchestrator tests passed, including three-owner cycles and package-only relative dynamic imports; targeted Ruff and <code>git diff --check</code> passed. <code>uv run --offline --frozen</code> created the ignored local environment from the existing cache; no network access was used. No long aggregate, R/runtime, scheduler, cluster, production, scientific-review, or biological evidence was produced. |
| 2026-08-26 | Architecture campaign governance extension | Three later user-ratified guardrails make maintenance-surface compression and mutation auditing mandatory, make Run the immutable plan while deferring every other application-model choice until after audit and explicit decision, and separate protection retirement from exact evidence-deletion authority. Per-slice product, protection, evidence, configuration/documentation, public-concept, compatibility, and mutable-state deltas cannot offset one another. The historical five-guardrail <code>ARCH-CONST-01</code> record remains unchanged, and broad <code>ARCH-01</code> remains Open. | Governance/documentation decision only. Focused local evidence: the documentation structure gate passed at 168 Markdown and four Mermaid sources; 167 documentation-owner, affected public-interface, and validation-orchestrator tests passed with three skipped; <code>git diff --check</code> passed. Tests used an existing sibling worktree environment; no dependency was installed. No product code, executable test, or runtime artifact changed; no retained evidence was deleted. No long aggregate, scheduler, cluster, production, scientific-review, or biological evidence was produced. |
| 2026-08-26 | <code>ARCH-MODEL-AUDIT-01</code> | At exact source revision <code>6524ed7967090319cf4ae62ae1b2edf31e9ca02d</code>, the current application/control flow, representations and semantic lifetimes, owners/callers, identity inputs and omissions, dry-run/execute continuity, Local-within-Slurm relationship, reporting/status mismatch, mutation ownership, protected transaction/evidence boundaries, reproducible footprint rosters, and 14 conditional compression opportunities were recorded. The audit establishes that neither <code>contract/normalized.json</code> nor <code>AttemptPlan</code> alone is already the selected Run model. Run means immutable plan; whether it is public and every other model or migration choice remain Open. | Current Git/source/contract/schema/test inspection plus focused documentation-only validation: the structure gate passed at 168 Markdown documents and four Mermaid sources, and <code>git diff --check</code> passed. Product tests were inspected but not executed for this audit. Category-separated actuals: product, protections/tests, configuration/scripts/schemas/runtime, retained evidence, public interfaces/concepts, compatibility paths, and mutable product state all changed by zero; documentation changed three files by <code>+485/-16</code> physical lines from the inherited guardrail commit. No runtime restoration, real scientific tools, scheduler job, Slurm allocation, cluster or production run, scientific review, or biological validation was performed. No evidence deletion was proposed or performed. |
| 2026-08-26 | <code>ARCH-MODEL-DECISION-01</code> | After the completed current-state audit and explicit user review, EMRYS selects model C and the compact public conceptual model <code>Project -&gt; Analysis -&gt; Run -&gt; Results</code>, with Attempt progressively disclosed. Run is public, owns the primary ordinary identifier, and immutably binds one admitted Analysis revision to one generated internal immutable Execution Plan. The Run-versus-Attempt boundary, role placement of the remaining nouns, and downstream identity-neutral reporting semantics are ratified. The next documentation-only <code>AC-SLICE-03</code> field-and-authority package is bounded but not implemented; all exact realization choices remain Open. | User-ratified documentation decision grounded in <code>ARCH-MODEL-AUDIT-01</code> plus independent decision-consistency review. Focused local evidence: documentation structure passed at 168 Markdown documents and four Mermaid sources; <code>git diff --check</code> passed. Category-separated actuals: maintained product implementation, protections/executable tests, configuration/scripts/schemas/runtime material, retained evidence, compatibility paths, and mutable product state changed by zero; no public command, type, method, or schema implementation changed; the documentation accepts four ordinary public nouns plus progressively disclosed Attempt and classifies the existing proposed nouns by role; documentation changed five files by <code>+346/-134</code> physical lines from the audited decision base. No product test, runtime restoration, real tool, scheduler job, Slurm allocation, cluster or production run, scientific review, or biological validation was performed. No evidence deletion was proposed or performed. |
| 2026-08-26 | <code>ARCH-MODEL-FIELDS-01</code> | The source/schema/caller-backed field-and-authority package fixes exact semantic Analysis and Execution-Plan fields; domain-separated Run-ID composition; relocation, formatting, label, order, and byte-content rules; a symbolic pre-allocation resource policy with Attempt-local resolution; one logical authority for Analysis, Execution Plan, Run, Attempt, and Results boundaries; direct current-record compatibility/retirement direction; Run-admission ownership of zero-Attempt and unreceipted-skeleton recovery; and separate Run integrity, Attempt outcome, evidence/recovery, Results completeness, and reporting status domains. <code>AC-SLICE-03</code> remains Open for product types, persistence/storage, APIs/packages, backend adapters, caller migration, tests, and implementation. | Documentation-only decision grounded in the completed current-state audit plus exact active request/execution/resource/attempt/receipt/artifact/report schemas and constructor/consumer inspection. Focused local evidence: documentation structure passed at 168 Markdown documents and four Mermaid sources; independent decision-consistency review and <code>git diff --check</code> completed before commit. Category-separated actuals: maintained product implementation, protections/executable tests, configuration/scripts/schemas/runtime material, retained evidence, compatibility code paths, mutable product state, and public commands/types/methods/schemas all changed by zero; three documentation files changed. No product test, runtime restoration, real tool, scheduler job, Slurm allocation, local/Slurm parity run, cluster or production run, scientific review, or biological validation was performed. No evidence deletion was proposed or performed. |
| 2026-08-27 | <code>AC-SLICE-03</code> successor Run-authority cutover | New Runs now use deeply immutable canonical Analysis-revision, Execution-Plan, and Run-binding records and versioned identities. Planning binds Run after scientific/toolchain/backend/stopping/symbolic-resource admission but before allocation or Attempt; admission durably publishes Analysis and Plan before committing Run last; inspection admits a prepared zero-Attempt Run; lifecycle refuses locks or Attempts without admitted Run authority; current planning, root selection, execution, compatible resume, and inspection use the successor records. Existing <code>emrys.execution.v1</code> Runs remain readable and resumable; workflow/task/reporting temporarily consume a one-way <code>emrys.execution-projection.v1</code> adapter that cannot determine Run identity. New-Run authority no longer belongs to the historical identity envelope, mutable normalization mappings, copied <code>AttemptPlan</code> resource views, or workflow configuration. Reporting-only and backend-adapter-only code remain identity-neutral. Whole Python/R lock identities remain conservative exact environment identities; narrowing them requires a validated production/scientific dependency-closure projection and remains a future compression candidate. Broad <code>AC-SLICE-03</code>, <code>CONTROL-01</code>, <code>RUN-03</code>, <code>IDENTITY-01</code>, and <code>ARCH-01</code> remain Open. Category-separated actuals before commit: maintained product implementation 14 files, <code>+2795/-346</code> physical lines, two new product files and no product-file retirement; protections/executable tests 14 files, <code>+1438/-100</code>, with no whole defense retired; configuration/schema/workflow material two files, <code>+336/-2</code>; documentation three files, <code>+79/-48</code>; retained evidence zero added, moved, or deleted; public surface zero CLI commands, zero package-root exports, and zero additional ordinary nouns; compatibility one owned temporary projection while the historical reader/resume path remains; mutable authority zero added, with the three new authorities byte-backed and immutable while existing Attempt, lock, reporting, runtime-observation, and transaction mutation remains in its current owners. No evidence deletion was proposed or performed. | Focused local engineering evidence: 52 application-model/resource/materialization tests passed with the one environment-dependent Snakemake case deselected; 74 task/reporting tests passed; 42 selected contract/lifecycle/resource tests passed; two implementation-identity sensitivity tests passed; documentation structure passed at 168 Markdown documents and four Mermaid sources; targeted Ruff and <code>git diff --check</code> passed. In the broader focused run, 319 tests passed before the sole Snakemake-backed case reported that the local environment lacks an importable Snakemake module. No long aggregate, fresh-clone E2E, local/Slurm parity, scheduler job, Slurm allocation, cluster or production execution, scientific review, or biological validation was performed; those higher evidence levels remain CI/site work. |
| 2026-08-27 | <code>AC-SLICE-03</code> successor execution-projection retirement | Successor Attempts now bind exact <code>contract/run.json</code> bytes through the existing format-aware <code>execution_contract_sha256</code>; workflow and task admission consume that Run authority directly; reporting inputs are identity-neutral, Attempt-owned files beneath <code>contract/reporting-inputs/&lt;workflow-attempt-id&gt;/</code> with exact origin-config path/hash references; and same-Run compatible resume may generate a new Attempt adapter without rewriting Run authority. Successor <code>contract/normalized.json</code>, <code>emrys.execution-projection.v1</code>, its schema arm, builder, validation path, and fixed Run-wide reporting adapters are retired. Historical <code>emrys.execution.v1</code> bytes, paths, reads, task/reporting semantics, and resume remain supported. <code>AC-SLICE-03</code>, <code>CONTROL-01</code>, <code>RUN-03</code>, <code>IDENTITY-01</code>, and <code>ARCH-01</code> remain Open only for their broader public/campaign outcomes. Category-separated actuals before commit: maintained product Python 11 files, <code>+405/-416</code>, net <code>-11</code>, with no product-file growth; protections/tests 10 files, <code>+347/-283</code>, with one redundant helper-level successor reporting check absorbed by stronger materialization/boundary coverage and no defense class removed; workflow/schema material two files, <code>+36/-42</code>, net <code>-6</code>; documentation seven files, <code>+95/-64</code>; retained evidence zero added, moved, or deleted; public surface zero CLI commands, zero package-root exports, and zero new ordinary nouns, while the temporary internal schema/helper surface is removed; compatibility one successor adapter family retired while historical compatibility remains; mutable authority zero added. No evidence deletion was proposed or performed. | Focused local engineering evidence: 97 application-contract/orchestration/reporting tests passed; three successor materialization/resume tests passed; selected historical lifecycle and task admission checks passed; four real-Snakemake dry-run/resource-policy cases passed; the 31-test source-boundary gate passed; documentation structure passed at 168 Markdown documents and four Mermaid sources; targeted Ruff and <code>git diff --check</code> passed. Long aggregate, fresh-clone E2E, real-tool workflow, Local/SLURM parity, scheduler, cluster, production, scientific-review, and biological validation remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-03</code> read-only Run/Results status cutover | Read-only inspection and recovery now derive Run integrity, scientific Attempt outcome, scientific Results, downstream reporting, and recovery eligibility independently. Reporting failure cannot erase successfully completed scientific work; verified report locations remain discoverable even when the terminal receipt records a reporting failure; and unmatched historical receipt ambiguity still blocks Run integrity. Lifecycle and control recovery consume the separated read model. The persisted receipt-v1 schema and emitter are unchanged, and narrow compatibility projections retain historical Python readers while current gates use the separated dimensions. Broader <code>AC-SLICE-03</code>, <code>CONTROL-01</code>, <code>RUN-03</code>, <code>OBS-02</code>, <code>RESULTS-01</code>, and <code>ARCH-01</code> remain Open. Category-separated actuals before commit: maintained product Python four files, <code>+431/-162</code>, with no product-file growth; protections/tests four files, <code>+133/-59</code>, with the invalid completed-Run resume premise replaced by a real failed-Attempt successor-resume proof and no defense class retired; configuration/schema/workflow material zero files; documentation nine files, <code>+63/-47</code>; retained evidence zero added, moved, or deleted; public surface zero commands, flags, package-root exports, persisted schemas, or ordinary nouns added, while the inspection output replaces one aggregate state and two aggregate booleans with five separated labels; compatibility no persisted format added or removed and receipt v1 remains authoritative historical evidence; mutable authority zero added. No evidence deletion was proposed or performed. | Focused local engineering evidence: 10 selected lifecycle/status/recovery tests passed in the final cut, following passing focused groups covering the CLI seam, reporting/runtime separation, result-location formatting, successor recovery, and current synthetic/fresh-clone assertions; targeted Ruff, documentation structure at 168 Markdown documents and four Mermaid sources, and <code>git diff --check</code> passed. A broader local lifecycle/materialization run exposed four affected expectations and premises that were corrected, but it is not claimed as a passing aggregate gate. Long aggregate, complete fresh-clone E2E, real-tool workflow, Local/SLURM parity, scheduler, cluster, production, scientific-review, and biological validation remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-03</code> Run-control boundary compression | The grouped CLI is now the sole supported Run-control surface. The duplicate direct Python planning API was demoted to private implementation detail after an exact in-repository caller search, and three identical controlled-runtime forwarding functions collapsed into one adapter. No CLI command, argument, output, Run/Attempt authority, execution behavior, or persisted format changed. Public Project/Analysis/Results intake and control, command simplification, and execution-profile selection remain Open. Category-separated actuals before commit: maintained product Python two files, <code>+16/-39</code>, net <code>-23</code>, with no product-file growth; protections/tests one file, <code>+2/-2</code>, with no defense retired; configuration/schema/workflow material zero files; documentation five files, <code>+33/-16</code>; retained evidence zero added, moved, or deleted; public surface three direct Python names retired and zero CLI commands, flags, arguments, output fields, package-root exports, persisted schemas, or ordinary nouns added; compatibility no alias added for the retired direct Python planning names because no in-repository production caller exists; mutable authority zero added. No evidence deletion was proposed or performed. | Focused local engineering evidence: 117 tests passed with three environment-conditional public-CLI checks skipped; targeted Ruff, documentation structure at 168 Markdown documents and four Mermaid sources, and <code>git diff --check</code> passed. Long aggregate, fresh-clone E2E, real-tool workflow, Local/SLURM parity, scheduler, cluster, production, scientific-review, and biological validation remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-03</code> current request-to-Analysis intake hardening | The existing authored request remains a temporary Project-source/provenance adapter, while normalization now retains immutable request, canonical profile, and canonical construction bytes plus the admitted Analysis revision. Request, profile, and construction mappings are fresh disposable views; caller mutation cannot alter later views, Analysis identity, historical-v1 bytes, or subsequent Run construction. A duplicate strict JSON parser and one-use request-schema wrapper were retired in favor of the existing orchestration-contract authorities. No public Project type, schema, command, layout, precedence policy, or setup lifecycle was selected, so public Project/Analysis intake remains Open. Category-separated actuals before commit: maintained product Python one file, <code>+28/-52</code>, net <code>-24</code>, with no product-file growth; protections/tests one file, <code>+26/-0</code>, adding one mutation-adversarial boundary proof and retiring no defense class; configuration/schema/workflow material zero files; documentation five files, <code>+37/-12</code>; retained evidence zero added, moved, or deleted; public surface zero commands, flags, package-root exports, schemas, or ordinary nouns added and all existing normalization property names retained; compatibility historical execution-v1 bytes and current caller views retained, with strict profile JSON admission delegated to the shared contract parser; mutable authority two stored shared mappings retired and zero mutable authority added. No evidence deletion was proposed or performed. | Focused local engineering evidence: all 32 normalization tests and two Run-candidate/materialization smoke tests passed; targeted Ruff, documentation structure at 168 Markdown documents and four Mermaid sources, and <code>git diff --check</code> passed. Long aggregate, fresh-clone E2E, real-tool workflow, Local/SLURM parity, scheduler, cluster, production, scientific-review, and biological validation remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-05</code>/<code>AC-SLICE-08</code> execution/allocation boundary groundwork | The current topology is explicit without introducing an interim execution stack: local Snakemake remains the sole scientific backend and the generated single-node Slurm path remains outer placement. Successor Attempts derive executor provenance from the admitted immutable Execution Plan; current Attempt allocation provenance carries an exact Slurm job ID or null for direct execution without changing Run identity; and exact historical three-field allocation records remain readable. The wrapper retains request-compatibility validation but delegates readiness to grouped Run control, whose failures preserve Doctor remediations. One redundant standalone Doctor subprocess and one redundant batch CPU export were retired. Profile names, schema, storage, precedence, selection, public commands, Managed/Site/Explicit runtime modes, any additional backend, and parity acceptance remain Open. Category-separated actuals before commit: maintained product Python eight files, <code>+50/-16</code>, net <code>+34</code>, with no product-file growth; protections/tests seven files, <code>+129/-15</code>, with no defense class retired; configuration/schema/workflow files zero; documentation six files, <code>+84/-43</code>; retained evidence zero added, moved, or deleted; public surface zero commands, flags, package-root exports, public types, profile selectors, backend registries, or ordinary nouns added; compatibility one internal current Attempt-allocation field added while the historical exact shape remains admitted; mutable authority zero added because the new fact is immutable Attempt-local provenance. No evidence deletion was proposed or performed. | Focused local engineering evidence: 69 allocation/resource/application-contract tests, three selected immutable-executor/materialization tests, and five selected launcher/onboarding tests passed; targeted Ruff, documentation structure at 168 Markdown documents and four Mermaid sources, independent read-only minimality/backward-compatibility review, and <code>git diff --check</code> passed. The review's one large-decimal validation edge case was reproduced and corrected without integer conversion. Long aggregate, complete fresh-clone E2E, real-tool workflow, direct/Slurm parity, scheduler job, Slurm allocation, cluster or production execution, scientific review, and biological validation remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-05</code> controlled direct/Slurm planning parity | One existing materialization protection now constructs the same immutable Analysis, Execution Plan, Run, and Attempt context twice with equal effective resource resolution: once against direct capacity and once against a larger admitted Slurm allocation. It proves byte-identical canonical authorities, fixed files, non-configuration Attempt files including task dispatches and reporting/runtime inputs, and output directories. Workflow configuration differs only in structured allocation provenance, and the Attempt record only in the corresponding configuration digest. This introduces no executor abstraction, backend, profile model, production path, or test-only production input. Allocation-sensitive effective-resource parity, distinct-Attempt outcome parity, real scheduler/site execution, runtime/module portability, failure/recovery parity, and report-publication parity remain Open. Category-separated actuals before commit: maintained product Python zero files; protections/tests one file, <code>+86/-36</code>, strengthening one existing allocation/identity protection and consolidating repeated workflow-config reads with no defense class retired; configuration/schema/workflow material zero files; documentation four files, <code>+34/-9</code>; retained evidence zero added, moved, or deleted; public surface zero commands, flags, package-root exports, schemas, backend/profile selectors, or ordinary nouns added; compatibility zero formats or paths added, changed, or retired; mutable authority zero added. No evidence deletion was proposed or performed. | Focused local engineering evidence: three affected materialization tests passed; 71 capacity, resource-policy, application-contract, and Slurm-wrapper delegation tests passed; targeted Ruff, documentation structure at 168 Markdown documents and four Mermaid sources, independent read-only minimality/contract review, and <code>git diff --check</code> passed. No long aggregate, complete fresh-clone E2E, real-tool workflow, allocation-sensitive effective-resource comparison, distinct-Attempt result comparison, scheduler job, Slurm allocation, cluster or production execution, scientific review, or biological validation was performed; those higher evidence levels remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-10</code> safe Run next-action guidance and aggregate-projection retirement | The existing <code>emrys inspect local-pilot-run</code> route now derives one deterministic next supported action solely from separated Run integrity, Attempt outcome, scientific Results, reporting, and recovery domains. Blocked evidence is preserved and never presented as resumable; completed science is not rerun for reporting trouble; running work waits; safe failed/interrupted boundaries point to the existing dry-run-first resume route. The redundant <code>RunInspection.state</code>, <code>resume_available</code>, and <code>local_pipeline_complete</code> Python projections are retired after all current callers migrated. Receipt-v1 and the CI E2E summary v1 remain byte-format compatible historical evidence. <code>OBS-02</code> remains Open for milestones, elapsed time, and role-aware progressive disclosure. Category-separated actuals before commit: maintained product Python two existing files, <code>+25/-36</code>, net <code>-11</code>; protections/tests three existing files, <code>+100/-31</code>, with domain-owned assertions, a compact action table, and a public inspect-output assertion while no defense class was removed; configuration/schema/workflow material zero files; documentation five files, <code>+34/-13</code>; retained evidence zero added, moved, rewritten, or deleted; public surface one deterministic line added to the existing inspect output, three direct Python accessors retired, and zero commands, flags, persisted schemas, package-root exports, backends, profiles, or ordinary nouns added; compatibility receipt-v1 and CI summary v1 unchanged with no path added; mutable authority zero added. No evidence deletion was proposed or performed. | Focused local engineering evidence: eight selected status/lifecycle tests and all 31 source-boundary tests passed; targeted Ruff, documentation structure at 168 Markdown documents and four Mermaid sources, independent read-only final review, and <code>git diff --check</code> passed. The complete doubled-workflow public-adapter check and all long aggregate, fresh-clone E2E, real-tool workflow, direct/Slurm parity, scheduler, cluster, production, scientific-review, and biological-validation evidence remain CI/site work and are not claimed. |
| 2026-08-28 | <code>AC-SLICE-10</code>/<code>OBS-02</code> persisted-authority status completion | The existing read-only inspect route now projects five scientific milestones, current/latest Attempt elapsed time, and normal/verbose/debug disclosure over admitted EMRYS records. Reporting remains separate from scientific progress; resumes are not summed; ETA is never inferred; inspection creates no application Attempt, log, status store, schema, backend, dashboard dependency, or write. Normal output hides engine state, verbose adds Run/Attempt placement and transaction aggregates, and debug adds exact retained receipt, engine, task, and stream paths. Five unused inspection projections and one internal export retire. Independent review caused the proposed duplicate semantic-validation retirement to be rejected: transitive task evidence is still re-admitted and reference-checked for concurrent mutation. <code>OBS-01</code> and <code>LOG-05</code> remain Open for their broader distinct outcomes; <code>DOC-05</code> and the stale dashboard are untouched. Category-separated actuals before commit: maintained product Python two existing files, <code>+166/-56</code>, net <code>+110</code>, with no product-file growth; protections/tests three existing files, <code>+125/-5</code>, with no defense class retired; configuration/schema/workflow zero; documentation three existing files, <code>+23/-8</code>; retained evidence zero added, moved, rewritten, or deleted; public surface one optional <code>--detail</code> selector on an existing command and no new command, schema, backend, package-root export, or public noun; compatibility no path or persisted format added or removed; mutable authority zero added. The user approved the permanent quantified product-growth exception on 2026-08-28; the existing control and inspection owners retain the surface. | Focused local engineering evidence: 46 selected status, lifecycle, CLI, and source-boundary tests passed after final evidence-protection restoration; targeted Ruff and <code>git diff --check</code> passed. The exact repaired production baseline <code>211533ac</code> passed all Phase 1 CI lanes in [run 33207766071](https://github.com/lab-cats/EMRYS/actions/runs/33207766071). Exact-head aggregate CI, the complete doubled-workflow adapter, fresh-clone E2E, real-tool workflow, direct/Slurm parity, scheduler, cluster, production, scientific-review, and biological-validation evidence are not yet claimed. |
| 2026-08-28 | Architecture compression, `LOG-05`, and shell-disposition audit | Campaign governance now distinguishes real trust-boundary defenses from redundant checks of impossible same-process states; low-risk check-only seams may retire without artificial replacement, while high-risk, ambiguous, directly user-facing, execution-boundary, and evidence-validation changes remain approval-gated. Touched retained operations must disposition and, when output or durable diagnostics change, incorporate `LOG-05` without an interim convention. Touched shell is retained, converted, or retired only when total surface falls. The focused register identifies more than 5,000 directional net product lines across the stale dashboard's post-campaign retirement opportunity, sixteen stage/utility Slurm wrappers, Steps 07–09 conversion, generated-wrapper reduction, and internal validation/handoff consolidation. Persisted EMRYS records remain status authority; elapsed time is Attempt-scoped; scheduler, engine text, and logs remain observations. The dashboard is frozen with no campaign updates or retirement; `TOOLING-01` remains Open for exact former-file/caller accounting but no longer requires a return-prevention guard. No implementation or evidence deletion is authorized by this audit. Category-separated actuals: maintained product, protections/tests, configuration/schema/workflow, retained evidence, public interfaces, compatibility paths, and mutable product state all changed by zero; six existing documentation files changed, `+196/-38`; no backlog ID or document was added. | Documentation-only planning evidence: current owner/caller and source-line audit at `1abbf094`; documentation structure passed at 168 Markdown documents and four Mermaid sources; all 40 documentation-structure tests and `git diff --check` passed. No product, shell, scheduler, Slurm, local/Slurm parity, runtime, scientific-review, biological, or evidence-deletion validation was performed. |
| 2026-08-28 | <code>AC-SLICE-10</code>/<code>OBS-02</code> exact-head aggregate validation | No product, protection, configuration, evidence, public-interface, compatibility, or mutable-state change; this row records follow-up validation of the previously committed status slice. | Exact head <code>867f2e783cf62e5704757ab70c76f23e3d9a8df1</code> passed all four Python 3.11 full-suite shards and aggregate coverage, the selected 130-pair and 100,000-pair real-tool synthetic E2E lanes, exact R/runtime restoration, disposable Slurm setup, evidence upload, and clean-checkout enforcement in [CI run 33214441598](https://github.com/lab-cats/EMRYS/actions/runs/33214441598). Manual dispatch skipped the Python 3.14/static, shell-contract, guarded-R-fixture, and dedicated fresh-clone jobs. This is not real site/cluster, production, scientific-review, or biological evidence. |
| 2026-08-28 | <code>OBS-01</code> concise grouped-Run console projection | Grouped <code>run</code>/<code>resume</code> normal output now keeps one Run/work/reporting summary, meaningful phases, verified Results/evidence, warnings/failures, and the durable application-log path. Run root, resources/allocation, execution profile, and scheduler streams move behind the existing verbose level; exact safe engine/scheduler/task commands remain debug. The redundant Operation line, split work-count lines, duplicate normal Run ID, and separately projected opening-log metadata retire while all metadata remains durable. Evidence automation now requests verbose through the production interface. <code>OBS-01</code> is Complete; <code>LOG-05</code> remains Open for other retained applicable operations and parity. Category-separated actuals before commit: maintained product Python two existing files, <code>+18/-23</code>, net <code>-5</code>, with no product-file growth; protections/tests five existing files, <code>+101/-34</code>, with no defense class retired; configuration/schema/workflow zero; documentation eight existing files, <code>+73/-39</code>; retained evidence zero added, moved, rewritten, or deleted; public surface zero commands, flags, schemas, backends, package-root exports, or public nouns added while existing detail levels carry less redundant normal output; compatibility zero paths or persisted formats added or removed; mutable authority zero added; no shell touched. No evidence deletion was proposed or performed; <code>DOC-05</code> and the stale dashboard are untouched. | Focused local engineering evidence: 87 logging, grouped-control, scheduler-receipt, degradation/failure, and real-E2E parser tests passed; targeted Ruff, documentation structure at 167 Markdown documents and four Mermaid sources, the source-boundary gate, and <code>git diff --check</code> passed. Long aggregate, complete fresh-clone E2E, actual real-tool workflow, direct/Slurm execution, scheduler/site, cluster, production, scientific-review, and biological-validation evidence remain CI/site work and are not yet claimed for this exact head. |
| 2026-08-29 | <code>AC-SLICE-04</code> existing task boundary and Step <code>08</code> owner migration | A four-owner map found that transformation, scientific-analysis, and evidence work already share private <code>TaskDispatch</code>, while reporting would map only through semantic distortion. The existing boundary is retained and no universal Stage/Operation API, schema, registry, lifecycle, backend, or public noun is added. Step <code>08</code> now has one owner-local Python coordinator invoked caller-completely by materialization and its retained Slurm wrapper; native R science, neutral scientific-evidence contracts, the independent validator, exact admitted-input checks, lock ownership, receipt-last publication, create-exclusive no-clobber behavior, rollback, recovery residue, signal semantics, and Run/task logging ownership remain. The old shell owner and shell test retire without a compatibility wrapper. Broad <code>ANALYSIS-02</code>, <code>ARCH-01</code>, <code>LOG-05</code>, collaborator-library design, and the other shell/scheduler candidates remain Open. Category-separated actuals at commit: maintained product implementation six paths, <code>+835/-1040</code>, net <code>-205</code>; protections/tests ten paths, <code>+534/-1555</code>, net <code>-1021</code>; configuration/schema/workflow two existing files, <code>+19/-6</code>, net <code>+13</code>; documentation six existing files, <code>+52/-37</code>, net <code>+15</code>; whole slice <code>+1440/-2638</code>, net <code>-1198</code>, with no net file growth. Retained evidence changed by zero; the explicitly inventoried Step <code>08</code> repository command/path is replaced by the private Python-module invocation, while flags, schemas, backends, package-root exports, and public nouns change by zero; no compatibility path is retained; mutable authority changed by zero. No evidence deletion was proposed or performed. | Focused local engineering evidence: 204 Step <code>08</code> owner/contract/validator, Slurm-wrapper, materialization, reporting-roster, and affected public-interface tests passed with three skipped; after commit, all 81 reporting-adapter tests also passed against exact package identity. Targeted Ruff, Python formatting/compilation, shell syntax, source-dependency enforcement, documentation structure at 167 Markdown documents and four Mermaid sources, stale-path search, and <code>git diff --check</code> passed. No long aggregate, real R scientific run, scheduler/site/cluster execution, production-data run, scientific review, or biological validation was performed or inferred locally. |
| 2026-08-29 | <code>AC-SLICE-12</code> role-oriented report purposes and navigation | The existing scientific HTML remains the primary answer to what the analysis found. Both HTML files now expose fixed sibling-relative destinations for that scientific report, Evidence and provenance, and Operations. The second existing file is titled <strong>Evidence and operations</strong>; Run overview remains intact, both former provenance sections fold under Evidence without content loss, and Attempt lineage moves under Operations. Exactly two receipt-bound HTML outputs, their filenames/kinds, receipt v4, self-contained status, and independent hashes remain; renderer version advances to <code>5.1.0</code>. No third artifact, command, schema, runtime validator, output root, or public noun is introduced. <code>AC-SLICE-12</code> is Complete; <code>REPORT-03</code> remains Verification pending for rendered acceptance and <code>RESULTS-01</code> remains Open for canonical result co-location. Category-separated actuals before commit: maintained product implementation three existing files, <code>+30/-31</code>, net <code>-1</code>; protections/tests four existing files, <code>+62/-3</code>, with exact-byte independent goldens and no defense retired; configuration/schema/workflow zero; documentation eight existing files, <code>+32/-22</code>; whole slice <code>+124/-56</code>, net <code>+68</code>, with no file growth. Retained evidence, mutable authority, commands, flags, schemas, backends, package-root exports, output paths/kinds, and compatibility paths changed by zero. No evidence deletion was proposed or performed. | Focused local engineering evidence: 55 documentation-structure, independent-contract-golden, report-publication, role-navigation, and template-boundary tests passed; targeted Ruff, Python compilation, documentation structure at 167 Markdown documents and four Mermaid sources, and <code>git diff --check</code> passed. The installed-wheel assertion and all long aggregate, fresh-clone E2E, real-tool workflow, scheduler/site/cluster execution, production-data run, rendered visual/user acceptance, scientific review, and biological validation remain CI or review work and are not claimed locally. |
| 2026-08-29 | <code>RESULTS-01</code> canonical scientist-facing result surface | The fixed profile now keeps exactly six Step <code>09</code> result artifacts under <code>results/editing</code>, five Step <code>10</code> artifacts under <code>results/scientific_context</code>, and both existing receipt-bound reports under <code>results/reports/&lt;run-id&gt;</code>; exactly 56 nonfinal/QC artifacts move to <code>products/native</code>. Step <code>07</code>–<code>10</code> dispatch roots derive from admitted artifact paths, preventing profile/command drift. Both reports link by portable relative paths to admitted all-sites, threshold-passing, and candidate-context tables; the Evidence and operations report alone shows the existing inspect command. No artifact is copied or linked, and no new manifest, index, report, schema, command, public noun, backend, registry, or mutable authority is introduced. One profile-bound helper selects the current report root and the exact legacy-profile root; current publication cannot adopt the latter. Read-only inspection admits noncurrent legacy report bytes only through their verified ledger, exact receipt/output hashes, recorded producer identities, run-summary transaction, and full transitive artifact roster. Historical record paths derive from admitted inventory beneath the fixed records directory, validation consumes one no-follow byte generation, and fixed orchestration identities are checked before any receipt-selected path can be opened. The current checkout is admitted only as the reader, and legacy bytes are neither reconstructed nor republished as current. Receipt v4 remains unchanged and renderer version advances to <code>5.2.0</code>. The profile schema, profile ID, and declared version remain unchanged, while changed canonical profile bytes intentionally create new Run identities; old-layout Runs remain inspectable but are not automatically resumable under the current fixed profile. <code>FILESYSTEM-01</code> and <code>AC-SLICE-11</code> retain broader storage, portability, archival, and bundle work. Current publication lifecycle and application-log behavior are unchanged, so no additional <code>LOG-05</code> adoption is necessary in this slice. The user approved the quantified footprint exception before commit: maintained product implementation 15 existing files, <code>+811/-130</code>, net <code>+681</code>, with no product-file growth; protections/tests eleven existing files, <code>+1060/-87</code>, net <code>+973</code>, with exact-byte goldens, generation-race, no-follow/path-containment, fresh-clone path/link, and public historical-inspection coverage and no defense retired; configuration/workflow two existing files, <code>+58/-57</code>, net <code>+1</code>; documentation eight existing files, <code>+70/-27</code>, net <code>+43</code>; whole slice 36 existing files, <code>+1999/-301</code>, net <code>+1698</code>. The exception preserves legacy evidence validation rather than hiding growth through protection consolidation or deletion; the reporting transaction validator owns that compatibility until a separately approved <code>AC-DEC-018</code> retirement decision. Retained evidence changed by zero, the frozen dashboard is untouched, and no evidence deletion was proposed or performed. | Focused local engineering evidence on the committed implementation tree: 144 artifact-schema, reporting-transaction, report-publication, and reporting-boundary tests passed. Targeted source-dependency and documentation-structure gates, Ruff, Python compilation, and <code>git diff --check</code> passed; an independent final review found no remaining P1/P2 correctness or security issue. The new complete-workflow public historical-inspection regression and all other long aggregate, complete fresh-clone E2E, real-tool synthetic workflow, full CI, scheduler/site/cluster execution, production-data run, rendered visual/user acceptance, scientific review, and biological validation remain CI or review work and are not claimed locally. |
| 2026-08-29 | <code>RESULTS-01</code> CI-fixture repair | Full CI exposed no production relaxation: one lifecycle helper duplicated the retired report root, while the no-science owner double embedded authored cohort/analysis aliases instead of admitted successor scope identities, used reference-inconsistent candidate coordinates, and emitted a generic Step <code>10</code> validation check. The helper now reuses the existing profile-aware receipt paths; fixture payloads derive their cohort/analysis IDs from the admitted inventory, use reference-consistent coordinates, and emit the exact <code>scientific_context_transaction</code> check. Production owners and validators are unchanged. Follow-up actuals: maintained product implementation zero; protections/tests three existing files, <code>+35/-38</code>, net <code>-3</code>; configuration/schema/workflow zero; documentation one existing file, <code>+2/-1</code>, net <code>+1</code>; retained evidence, public interfaces, compatibility paths, mutable authority, shell, logging, and dashboard behavior changed by zero. Cumulative endpoint diff is 37 existing files, <code>+2035/-339</code>, net <code>+1696</code>, still within the approved exception and with no file growth or evidence deletion. | The eight exact Python 3.11/3.14 lifecycle failures now pass locally, as does the strengthened successor-scope payload regression; targeted Ruff and <code>git diff --check</code> pass. A bounded independent reconstruction admits every Step <code>09</code> artifact as present/complete and found no remaining fixture/report identity mismatch. Exact repaired head <code>53950fbf8bdd65b3e0d308a90054a30bb30465ed</code> passed all Python 3.14 shards and aggregate coverage, guarded R, shell/Slurm, fresh-clone E2E, lint/documentation/wheel lanes in [standard CI run 33248113968](https://github.com/lab-cats/EMRYS/actions/runs/33248113968), and all Python 3.11 shards and aggregate coverage plus 130-pair and 100,000-pair real-tool synthetic E2E/evidence lanes in [extended CI run 33248133537](https://github.com/lab-cats/EMRYS/actions/runs/33248133537). This is GitHub-hosted disposable single-node Slurm synthetic evidence, not CSU/distributed production execution, rendered user acceptance, scientific review, or biological validation. |
| 2026-08-29 | <code>AC-SLICE-03</code> minimal Project boundary | The sole active new-Run intake now uses <code>project.yaml</code>, <code>emrys validate project</code>, and <code>--project</code> across validation, Doctor, direct Run control, and whole-Run Slurm delegation; the old command/flag/starter names retire directly with no alias. Owner-local frozen <code>ProjectAdmission</code> replaces <code>NormalizationBundle</code>, retains exact source/profile/construction bytes and immutable <code>AnalysisRevision</code>, and reaches the existing immutable Execution Plan and Run through <code>RunCandidate.project.analysis</code>; Results authority and layout are unchanged. The current closed <code>emrys.request.v3</code> structure remains a temporary adapter, so no second schema, persistence model, registry, backend, generalized policy boundary, package-root API, or final Project nesting is selected. Doctor admission, fresh post-Doctor admission, and lifecycle's lock-time exact-source reread remain distinct; request-era Attempt fields and <code>request.yaml</code> snapshots remain historical evidence. Two redundant policy checks retire behind the surviving canonical policy validator, while no other defense is removed. Project labels are terminal-escaped, immutable Analysis identity is verbose/debug-only, and the normal view keeps Project plus the primary Run ID. Existing Run application logging remains the lifecycle authority, so this slice adds no parallel <code>LOG-05</code> path. <code>AC-SLICE-03</code>, <code>CONTROL-01</code>, <code>CONFIG-01</code>, and broad <code>ARCH-01</code> remain Open for final Project shape/persistence, broader public Analysis/Results APIs and role disclosure, generalized backend/policy boundaries, and remaining migrations. Category-separated actuals before commit: maintained product Python eight existing files, <code>+302/-283</code>, net <code>+19</code>, with no product-file growth; protections/tests sixteen existing files, <code>+419/-297</code>, net <code>+122</code>, adding post-Doctor mutation and terminal-injection coverage while retiring only the duplicate check copies; configuration one path renamed with identical bytes and zero line/file growth; documentation fourteen existing files, <code>+191/-162</code>, net <code>+29</code>; whole slice 39 paths, <code>+912/-742</code>, net <code>+170</code>, with no net file growth. Retained evidence, persisted schemas, backends, mutable authority, shell, dashboard, and evidence deletion changed by zero. | Focused local engineering evidence covers 388 passing Project-admission, onboarding, Doctor, execution-profile, materialization, projection, Slurm-delegation, public-CLI, and real-synthetic-driver tests with three environment-dependent skips; the complete 138-test materialization group passed, and its deliberate failure/resume recovery case passed again in isolation after one concurrent review run produced an unconfirmed failure. Targeted Ruff, source-dependency enforcement, documentation structure at 167 Markdown documents and four Mermaid sources, and <code>git diff --check</code> passed. Independent review found no remaining confirmed P1/P2 issue. Installed-wheel, complete fresh-clone and aggregate suites, real-tool workflow, full CI, real scheduler/site/cluster execution, production-data execution, rendered user acceptance, scientific review, and biological validation remain CI or later evidence and are not claimed locally. |
| 2026-08-29 | <code>AC-SLICE-17</code> Step <code>07</code> Python-owner conversion and compression | One private owner-local Python producer replaces the 976-line shell coordinator caller-completely in materialization, the retained Slurm wrapper, source/provenance rosters, contracts, and tests; the shell path and its 1,323-line shell-only suite retire without a compatibility wrapper. The existing neutral Step <code>07</code> helper now gives both producer and validator strict physical TSV parsing plus complete partition-row admission. The replacement retains exact commands and sample order, both selector modes, full scientific-input binding, manifest stability, copyable semantic-gate commands and owned scratch/rollback planning, temporary and final VCF validation, receipt-last publication, complete-set/no-clobber admission, inode and lock ownership, process-group signals, predecessor rollback, and failed-restoration residue while removing impossible PIPE/type/state checks and shell-only permutations. The registered current producer identity intentionally changes to <code>producer.py</code>; exact pre-migration records remain bound to their producing checkout, and historical admission is not broadened. The existing Run lifecycle remains the <code>LOG-05</code> authority; no task-local log is added and broader adoption/parity remains Open. <code>AC-SLICE-17</code> and broad <code>ARCH-01</code> remain Open for other retirements. Category-separated actuals before commit: maintained product implementation seven paths, <code>+995/-998</code>, net <code>-3</code>, with one Python owner replacing one shell owner and no file growth; protections/tests ten paths, <code>+890/-1358</code>, net <code>-468</code>, with boundary/fault coverage retained and shell-only permutations retired; configuration/workflow two existing files, <code>+2/-7</code>, net <code>-5</code>; documentation eleven existing files, <code>+60/-28</code>, net <code>+32</code>; whole slice 30 paths, <code>+1947/-2391</code>, net <code>-444</code>, with no net file growth. Retained evidence changed by zero; no evidence was added, rewritten, moved, or deleted. Grouped <code>emrys</code> commands and flags, public nouns, schemas, receipts, backends, package exports, Run/Attempt/Results authority, mutable product state, and the frozen dashboard changed by zero. One explicit repository-path producer interface retires in favor of the private Python module without an alias. The retained Step <code>07</code> <code>.slurm</code> wrapper delegates to Python; across the campaign Step <code>08</code> already delegates to its Python owner and the other fourteen owner-local wrappers retain their prior forms. | Focused local engineering evidence: 95 Step <code>07</code> owner, shared-parser/reference-helper, and independent-validator tests plus the exact materialization-caller assertion passed; targeted Ruff, source-dependency enforcement, shell syntax, documentation structure at 167 Markdown documents and four Mermaid sources, all 39 documentation-structure tests, and <code>git diff --check</code> passed. Full aggregate/fresh-clone/real-tool CI, real scheduler/site/cluster execution, production-data execution, scientific review, and biological validation are not claimed locally. |
| 2026-08-29 | <code>RUN-03</code> downstream Run reporting cutover | Scientific Attempts now stop at <code>cohort_slice</code>, release their lock, and publish receipt v2 before reporting. Receipt v2 removes only receipt-v1's reporting fields; exact v1 reads and complete-report reuse remain, while new generation requires a successful successor Run and v2 receipt. <code>run</code>/<code>resume</code> report by default, <code>--no-report</code> opts out, and dry-run-first <code>emrys report</code> regenerates independently without a Run or Attempt. Exact complete transactions are revalidated/reused; generation is fixed artifact-index → run-summary → HTML and accepts only empty owned locations. Partial, corrupt, orphaned, symlinked, or concurrent state fails closed. The three low-level public build routes, CLI-shaped private adapters/printers, one artifact-builder file, workflow reporting tail, dead context fields, broad boundary return state, forwarding serializer, and obsolete test-fixture arguments retire without aliases. No publisher transaction, lock/no-follow defense, receipt-last/durability rule, rollback/recovery path, historical reader, independent golden, or retained evidence is removed. Automatic reporting shares the Run log; standalone generation opens one observational log only after generation starts; dry-run/reuse open none. <code>reporting_memory_mb</code> remains a redundant-configuration candidate pending explicit approval; the frozen dashboard and <code>DOC-05</code> are untouched. Category-separated actuals before commit: maintained product Python 16 paths, <code>+742/-743</code>, net <code>-1</code>, with one new coordinator and one deleted builder file; protections/tests 23 paths, <code>+1368/-1388</code>, net <code>-20</code>, with adapter-only assertions retired while fault, recovery, historical-reader, and independent-golden coverage remains; configuration/schema/workflow five paths, <code>+214/-288</code>, net <code>-74</code>; documentation 21 paths, <code>+320/-218</code>, net <code>+102</code>; whole slice 65 paths, <code>+2644/-2637</code>, net <code>+7</code>, with three new files, one deleted file, and therefore two net new files. Retained evidence changed by zero; public surface adds one grouped <code>report</code> command and two <code>--no-report</code> flags while retiring the grouped <code>build</code> command and its three subjects; one receipt schema version is added while exact v1 compatibility remains; no public noun, backend, scientific stage, Run/Attempt authority, or aggregate mutable status is added. <code>RUN-03</code> remains Open for its broader outcomes. | The migrated reporting-owner suites passed 208 focused tests; the final reporting-operation, boundary, and source-dependency gate passed 66 tests in 3.07 seconds; all 13 independent contract goldens passed after direct receipt-owner migration; 156 public-CLI and receipt-contract tests passed with three skipped; and the five standalone-log cases plus three implementation-identity sensitivity cases passed. Targeted Ruff, documentation structure at 167 Markdown documents and four Mermaid sources, <code>git diff --check</code>, and an independent read-only final review passed with no remaining P1/P2 issue. The installed-wheel smoke and all long aggregate, fresh-clone/real-tool workflow, Local/Slurm parity, full CI, real scheduler/site/cluster execution, production-data run, rendered user acceptance, scientific review, and biological validation remain CI or later evidence and are not claimed locally. |

## Former repository-backlog reconciliation

The following IDs were explicitly retained; unresolved work appears in the
active matrix and completed work appears in the disposition log:

- <code>FUT-DATA-02</code>
- <code>FUT-INDEX-01</code>
- <code>LOG-03</code>
- <code>LOG-05</code>
- <code>REVIEW-UX-03</code>

No former blocker relationships were retained.

## Disposition log

| Date | ID | Disposition | Reason or successor |
|---|---|---|---|
| 2026-08-29 | <code>RESULTS-01</code> | Complete | Current Runs expose editing results, scientific context, and both reports beneath one scientist-facing <code>results</code> surface; nonfinal/QC artifacts live beneath <code>products/native</code>; portable admitted-result links and inspect guidance require no duplicate authority. <code>FILESYSTEM-01</code>, <code>AC-SLICE-11</code>, and rendered <code>REPORT-03</code> acceptance remain separate. |
| 2026-08-29 | <code>AC-SLICE-12</code> | Complete | The two existing receipt-bound HTML reports now expose the three accepted purposes through fixed relative navigation; the combined Evidence and operations document folds provenance under Evidence and moves Attempt lineage under Operations. <code>REPORT-03</code> remains Verification pending and <code>RESULTS-01</code> remains Open. |
| 2026-08-29 | <code>AC-SLICE-04</code> | Complete | Existing private <code>TaskDispatch</code> is retained as the minimum common boundary; a universal Stage/Operation abstraction is rejected; and the caller-complete Step <code>08</code> Python-owner migration is complete with native R science and independent validation retained. Broad <code>ANALYSIS-02</code>, <code>ARCH-01</code>, <code>LOG-05</code>, collaborator-library design, and the other shell candidates remain Open. |
| 2026-08-28 | <code>OBS-01</code> | Complete | Grouped <code>run</code>/<code>resume</code> now provides concise normal output with operational paths and resource detail at verbose and exact safe commands at debug. Durable logging/evidence and machine-output contracts are unchanged. <code>LOG-05</code> remains Open for other retained applicable operations and required parity; dashboard retirement remains deferred until campaign completion and separate approval. |
| 2026-08-28 | <code>OBS-02</code> | Complete | The existing read-only inspect route now provides persisted-authority scientific milestones, current/latest Attempt elapsed time, separated status and reporting, safe recovery guidance, verified result links, and normal/verbose/debug disclosure without a status store, dashboard dependency, ETA, or write. The subsequent <code>OBS-01</code> disposition completes its distinct console outcome; <code>LOG-05</code> remains Open for broader adoption/parity, and dashboard retirement remains deferred until campaign completion and separate approval. |
| 2026-08-26 | <code>ARCH-MODEL-FIELDS-01</code> | Complete | Exact semantic fields and identity composition, relocation/order/content rules, symbolic Attempt envelope, logical authorities, current-record retirement direction, Run-admission recovery ownership, and separate status domains are durable. <code>AC-SLICE-03</code>, <code>CONTROL-01</code>, <code>RUN-03</code>, <code>IDENTITY-01</code>, <code>RESULTS-01</code>, and broad <code>ARCH-01</code> remain Open for product realization and their stated wider outcomes. |
| 2026-08-26 | <code>ARCH-MODEL-DECISION-01</code> | Complete | Model C, the compact public vocabulary and nesting, primary Run identity, progressive Attempt disclosure, noun visibility, and Run-versus-Attempt/reporting semantic boundary are durable. The subsequent field-and-authority decision package completed as <code>ARCH-MODEL-FIELDS-01</code>; product realization remains Open under <code>AC-SLICE-03</code> and its routed owners. |
| 2026-08-26 | <code>ARCH-MODEL-AUDIT-01</code> | Complete | The current-state prerequisite is recorded: current-model, owner/caller, identity, mutation, protection/evidence, and conditional-compression inventories live in the temporary architecture campaign. Per the approved boundary, <code>AC-SLICE-03</code>, <code>CONTROL-01</code>, <code>IDENTITY-01</code>, <code>RUN-03</code>, and broad <code>ARCH-01</code> remain Open; no public model, API, persistence, backend, status, compatibility, migration, or deletion decision was completed. |
| 2026-08-26 | <code>ARCH-LAYER-01</code> | Complete | The responsibility/dependency model, current-owner crosswalk, exact current composition and transition rosters, and fast Python source-boundary ratchet are durable and focused evidence is recorded above. Broad <code>ARCH-01</code> and <code>AC-SLICE-03</code> through <code>AC-SLICE-07</code> retain every concrete API, ownership, lifecycle, package, and migration decision. |
| 2026-08-26 | <code>ARCH-CONST-01</code> | Complete | The qualified invariant register, current-gap classification, and five binding migration/test guardrails are recorded in the platform-direction decision. Exact layers, APIs, abstraction selection, facade use, migrations, and remaining target implementation stay Open under <code>ARCH-01</code> and the routed owner tasks. |
| 2026-08-25 | <code>DOC-03</code> | Complete | Acceptance evidence is recorded above. The five source paths are retired and guarded; the final architecture-document set remains open under <code>AC-DEC-021</code>, and no discarded task was revived. |
| 2026-08-25 | <code>LOG-03</code> | Complete | Acceptance evidence is recorded above. Production-command and real-wrapper adoption remains independently owned by <code>LOG-05</code>. |
| 2026-08-25 | <code>DOC-02</code> | Complete | The repository-wide disposition roster and authority cutover are accepted; completed <code>DOC-03</code>, open <code>DOC-04</code>/<code>DOC-05</code>, <code>CLEAN-01</code>, and <code>CLEAN-02</code> separately own the resulting migrations. |
| 2026-08-25 | <code>DOC-TOOL-01</code> | Complete | Useful documentation structure validation has one correctly named owner and direct test suite; obsolete registry coupling was removed and the validator no longer lives in a generic Git-orchestration bucket. Open <code>TOOLING-01</code> owns only the exact former-file/caller history audit and no longer requires a check-only return guard. |
| 2026-08-25 | <code>BACKLOG-01</code> | Complete | The findings matrix is the sole durable backlog; legacy registry/card/status surfaces and broken task routes were removed, while historical detail remains available through Git history. |
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
