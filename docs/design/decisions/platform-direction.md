# Architecture rationale

## Protect behavior before structural change

Classify affected behavior as preserved contract, characterized defect,
undefined and requiring a decision, or environment-deferred. Protect preserved
behavior independently before mutation. Structural cleanup does not silently
correct a defect or authorize a public/scientific interface change.

## Ratified architectural invariant constitution

`ARCH-CONST-01` ratified this constitution on 2026-08-26 by reconciling all 27
campaign candidates to live contracts, decisions, implementation boundaries,
and representative regression protection. These rules constrain later
architecture work; they do not select a public vocabulary, command, schema,
filesystem layout, layer map, class, facade, or abstraction.

The register uses two states:

- **Preserved** means the qualified wording is already a current contract in
  its declared scope. Exact conformance still comes from live source and tests,
  not this decision record.
- **Target** means the wording is binding for the campaign but a named current
  gap remains. A target is not evidence that the capability exists.

Characterized defects and environment-deferred behavior stay visible. A
representative test route shows existing protection, not universal proof or a
new evidence level.

### Scientific invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-001` | Orientation, pairing, cohorts, strata, conditions, and other biological meaning are explicit; structural discovery never invents them. | Preserved | The [scientific decision](scientific-pipeline.md), [current architecture](../../architecture/ARCHITECTURE.md), and [sample-manifest tests](../../../tests/ingestion/sample_manifest_admission/) own the implemented boundary. |
| `AC-INV-002` | A scientific transformation is deterministic only where its owner contract declares determinism; no universal byte-determinism claim is implied. | Preserved | Scientific owner contracts and the [independent contract goldens](../../../tests/contract_integration/independent_contract_goldens/) protect declared ordering and serialization. |
| `AC-INV-003` | Tools, procedures, parameters, filters, thresholds, candidate universe, count construction, and testing family are recorded sufficiently to reproduce or audit the analysis at its declared level. | Target | The scientific decision and Step 07–09 contracts own current declarations; native-receipt provenance gaps remain visible under `ARCH-01` and the scientific-audit boundary in `AC-DEC-022`. The [Step 09 oracle](../../../tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_oracle.py) independently protects core statistics. |
| `AC-INV-004` | Reporting, orchestration, scheduling, filesystem, and performance refactoring cannot silently alter scientific results. | Preserved | The root safety guard, owner locality, [test policy](../TEST_BASELINE.md), and scientific owner suites require behavior to be preserved or changed only under separately approved scope. |
| `AC-INV-005` | Operational abstractions may hide mechanics, but scientific algorithms, parameters, assumptions, interpretation boundaries, and implementation needed for scientific review remain recognizable and inspectable. | Target | Current scientific owners remain colocated with contracts and tests. `ANALYSIS-02` and `ARCH-01` must preserve reviewability across future module and abstraction boundaries; human recognizability requires review and cannot be proved by coverage alone. |
| `AC-INV-006` | Workflow success, a computational candidate, statistical selection, scientific review, and biological validation remain distinct claims. | Preserved | The root evidence guard, [execution/evidence decision](execution-evidence-and-reporting.md), artifact contracts, and [reporting tests](../../../tests/reporting/) protect the non-promotion boundary. |

### Provenance and artifact invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-007` | A result is traceable to exact inputs, scientific configuration, source/package identity, runtime/tool identity, and the execution that produced it. | Target | The fixed local lifecycle binds this chain in the [orchestration contract](../ORCHESTRATION_CONTRACT.md) and [lifecycle tests](../../../tests/orchestration/local_pilot/test_lifecycle.py). Native-owner, installed-control-plane, and site provenance gaps remain under `ARCH-01`, `RUNTIME-01`, and `OPS-02`. |
| `AC-INV-008` | Every admitted durable artifact reference binds a stable semantic identity plus exact content digest; changed bytes cannot retain admission under the old binding. | Preserved | The [artifact schemas](../../../src/emrys/contracts/artifacts/) and [artifact contract tests](../../../tests/contracts/artifacts/) keep semantic identity distinct from content identity. |
| `AC-INV-009` | Mutation of a published artifact invalidates its prior admission and is detected at every required re-admission; physical write prevention is not implied. | Target | Verified-task and reporting paths recheck content identity. Rewrite-blindness and owner transaction defects remain characterized in the test baseline and must be resolved or explicitly preserved by the applicable `ARCH-01` migration. |
| `AC-INV-010` | Every generated manifest or normalized configuration artifact that affects a run remains inspectable and source-attributed even when a user does not author it. | Preserved | The orchestration materialization contract and [materialization tests](../../../tests/orchestration/local_pilot/test_materialization.py) protect current generated artifacts; `CONFIG-01` and `SETUP-03` inherit the rule. |
| `AC-INV-011` | Each artifact class and guarantee has one declared admission chain and one final authority; this must not become one global implementation or god object. | Target | The current native publication → owner validation → verified result → explicit adapter/index flow is defined by the [current architecture](../../architecture/ARCHITECTURE.md). `ARCH-01`, `AC-DEC-010`, and `AC-DEC-025` own the generalized lifecycle and boundary decisions. |

### Execution and recovery invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-012` | An execution is complete according to its contract or visibly incomplete, failed, blocked, pending, or running; engine metadata is not completion authority. | Preserved | The orchestration contract and [lifecycle state tests](../../../tests/orchestration/local_pilot/test_lifecycle.py) protect the implemented local lifecycle. |
| `AC-INV-013` | Within declared EMRYS-owned transaction and control namespaces, partial or provisional state cannot be admitted as complete; ambiguous or foreign residue fails closed. | Target | Task, lifecycle, and [reporting transaction tests](../../../tests/reporting/test_transaction_validation.py) protect current paths. Owner-local residue, rollback, and rewrite defects remain characterized until their applicable migration resolves them. |
| `AC-INV-014` | Recovery cannot produce scientifically different work under the same bound identity. | Preserved | Normalization and lifecycle compatibility checks bind scientific changes to a new run identity and reject incompatible reuse. |
| `AC-INV-015` | Resume reuses only compatible admitted work; timestamps, file presence, and workflow-engine metadata are insufficient. | Preserved | The orchestration contract and [workflow tests](../../../tests/orchestration/local_pilot/test_workflow.py) require content and contract re-admission. |
| `AC-INV-016` | Local and HPC execution must provide equivalent scientific, artifact-integrity, recovery, and evidence guarantees, not identical mechanisms; each environment requires separate proof. | Target | `OPS-02`, `RUNTIME-01`, and `DOCTOR-01` own realization. Wrapper contracts are not parity, cluster, production, or scientific proof. |
| `AC-INV-017` | An immutable plan exists internally before the first execution mutation, even when planning and execution become one conceptual user operation. | Preserved | The orchestration contract and materialization tests protect no-write planning and immutable publication; `RUN-03` may simplify the interaction without weakening the order. |
| `AC-INV-018` | Failure and every supported repair are attributable and auditable. Repair is explicit, bounded to owned safe state, precisely reported, provenance-aware where applicable, and cannot alter declared scientific inputs or invent biology or secrets. | Target | Failure attribution exists in task/lifecycle records. Supported repair does not yet exist and remains `DOCTOR-01`; production adoption of durable application logging remains `LOG-05`. |

### Evidence and reporting invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-019` | Reported claims derive from admitted artifacts and recorded validation, never discovery or recalculation inside reporting. | Preserved | The execution/evidence decision, reporting contracts, and [reporting tests](../../../tests/reporting/) protect read-only adaptation and receipt-last publication. |
| `AC-INV-020` | Validation evidence is rerunnable or independently verifiable at its declared level; missing retained inputs, runtime identity, or independent verification is disclosed rather than promoted. | Target | The test baseline, independent goldens, direct validators, and scientific oracles provide bounded protection. Native provenance and validator gaps remain visible under `ARCH-01` and `AC-DEC-022`. |
| `AC-INV-021` | Scientific, evidence/provenance, and operational evidence remain distinguishable. | Target | Existing scientific and evidence HTML views provide partial separation. The complete three-purpose presentation remains `REPORT-03` and `RESULTS-01`. |
| `AC-INV-022` | Local engineering, synthetic end-to-end, runtime, cluster, production, scientific-review, and biological evidence are never promoted into one another. | Preserved | The root evidence guard, test baseline, artifact evidence schema, and reporting boundary tests own this rule. |
| `AC-INV-023` | Receipts and low-level records required by an evidence or recovery contract may be omitted from ordinary views but remain inspectable subject to explicit retention and redaction policy; expired or unavailable records are disclosed rather than treated as complete. | Target | The logging foundation and task/attempt schemas provide bounded current pieces. `LOG-05`, `OBS-01`, `OBS-02`, `FILESYSTEM-01`, `AC-DEC-013`, and `AC-DEC-017` own adoption, access, retention, and result-bundle decisions. |

### User-boundary invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-024` | Developer-only knowledge is never required for an ordinary scientist task. | Target | Current onboarding still exposes checkout, configuration, wrapper, and run-root mechanics. `CONTROL-01`, `OPS-02`, `SETUP-03`, `RUNTIME-01`, `DOCTOR-01`, `RUN-03`, `OBS-02`, `RESULTS-01`, `DOC-01`, and `REVIEW-UX-03` own the role-level journey. |
| `AC-INV-025` | Defaults, site policy, project values, and CLI overrides use one documented, inspectable precedence model. Every effective operational value and source is inspectable; an override exists only where its owner defines a safe supported admission boundary. | Target | Current resource and launcher policy implement bounded precedence. `CONFIG-01`, `OPS-01`, `OPS-02`, and `AC-DEC-005` own the complete model and exact merge semantics. |
| `AC-INV-026` | The system never prints secrets or silently invents biological meaning. | Target | Biological admission is already fail-closed, and the logging foundation redacts admitted secrets. Production paths without logging adoption have no system-wide redaction promise; `SETUP-01`, `SETUP-03`, `DOCTOR-01`, and `LOG-05` own the remaining gap. |
| `AC-INV-027` | Automatic actions are bounded, observable, and reversible or recoverable where the operation permits it; irreversibility is explicit before mutation. | Preserved | Current dry-run-first publication/recovery contracts and [onboarding tests](../../../tests/orchestration/local_pilot/test_onboarding.py) protect supported mutations. `SETUP-03`, `DOCTOR-01`, `RUN-03`, and every future mutating owner inherit the rule. |

### Ratified abstraction, migration, and test guardrails

The following guardrails are binding. `AC-GUARD-001` through `005` are the
original set; `AC-GUARD-006` through `008` are later campaign-level extensions.
They do not ratify facade-first sequencing, an exact layer map, the campaign
phase order, or a concrete public API. The later application-model section
settles conceptual vocabulary and semantics, not an API realization.

1. **Inspectable, bounded operational control (`AC-GUARD-001`).** Every
   effective operational value and its source is inspectable. An override
   exists only where the owning contract explicitly supports it and defines a
   safe admission boundary; unsafe or implementation-only values are not
   promised an override.
2. **Scientific visibility (`AC-GUARD-002`).** Operational abstractions may
   hide execution, filesystem, scheduler, provenance, and transaction
   mechanics from ordinary views, but must not conceal the algorithms,
   parameters, assumptions, interpretation boundaries, or implementation
   needed for scientific review.
3. **Bounded migration (`AC-GUARD-003`).** Migration proceeds through bounded,
   independently reviewable slices rather than an unbounded rewrite. Exact
   facade use and package order remain just-in-time decisions.
4. **Replacement completion (`AC-GUARD-004`).** A replacement is not complete
   until affected callers use the intended owner and parity is established at
   the relevant behavior, fault, and evidence boundaries. Any temporary
   compatibility path has a named owner, bounded scope, parity protection, and
   explicit retirement condition; the superseded path retires when that
   condition is met.
5. **Boundary- and risk-aware regression defense (`AC-GUARD-005`).** A
   protection at an external-input, filesystem, concurrency, crash, recovery,
   persistence, evidence, or supported public-behavior boundary may be removed
   only through an explicit invariant-to-test mapping that establishes an
   equal-or-stronger surviving defense at the same declared evidence level.
   Coverage or the scientist-facing synthetic golden path alone is
   insufficient. A redundant check or test aimed only at an impossible
   same-process state may instead retire without replacement when the audit
   proves one admitted immutable producer, no supported injection or mutation
   path, no distinct failure mode or claim, and the exact surviving authority.
   High-risk, ambiguous, or directly user-facing protection retirement requires
   the user's explicit approval.
6. **Maintenance-surface compression (`AC-GUARD-006`).** Every architecture
   audit records concrete compression opportunities across implementation,
   compatibility paths, configuration, scripts, schemas, documentation,
   protections, and retained evidence. Each implementation slice migrates
   callers, establishes parity, and retires superseded responsibility where
   safe. The default is net-negative maintained product code with no
   product-file growth; an exception requires the user's explicit approval of
   quantified growth and its justification, plus an owner and retirement
   condition when temporary.
   The full category-separated closeout in the campaign's
   [per-slice protocol](../../tasks/architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol)
   is binding; categories never offset one another. File and line counts are
   indicators, not authority to create god modules, displace logic into
   generated/configured form, or weaken a guarantee. Temporary growth remains
   counted until retired.
   Every touched shell or generated-shell surface is classified `KEEP`,
   `CONVERT`, or `RETIRE`. Conversion is permitted only when the same slice
   removes more total product, protection/test, caller, and cross-language
   surface than it adds; a line-for-line port or parallel shell/Python owner is
   not compression. `KEEP` is correct when conversion would increase total
   surface, even if the retained implementation is not intrinsically
   shell-native; the audit records the reason and reconsideration trigger.
   Any high-risk, directly user-facing, execution-boundary, or
   evidence-validation retirement, consolidation, or conversion requires the
   user's explicit approval whether or not it is classified as a protection.
7. **Immutable by default; `Run` is the plan (`AC-GUARD-007`).** Boundary
   values are immutable unless the owning contract justifies a narrow mutable
   lifecycle. A `Run` is an immutable plan and is never modified in place; a
   plan change creates a distinct `Run`. Draft and attempt-local state may
   mutate only within their owners and cannot alter the `Run` or reconstruct a
   competing plan from mutable state.
   This guardrail did not itself settle other public nouns or nesting,
   identity composition or cardinality, Attempt/Results relationships, APIs,
   backends, policy, persistence, or storage. The later
   [application-model decision](#ratified-application-model-and-run-boundary)
   settles only the named vocabulary, nesting, and Run-versus-Attempt boundary;
   its explicit deferrals remain open.
8. **Explicit evidence-deletion authority (`AC-GUARD-008`).** Identifying
   apparently redundant evidence in an audit, campaign, task, or compression
   proposal does not authorize deletion. Deletion requires separate explicit
   user approval for the exact artifacts or class after a proposal identifies
   supported claims and recovery, producers and consumers, retention and
   redundancy, evidence-level effects, and rollback. Approved deletion is
   isolated in its own commit and never offsets implementation growth.
   Ambiguous dual-purpose material is treated as evidence.

For these guardrails, a **protection** is an executable or static defense such
as a test, validator, fixture, or oracle. **Evidence** is a retained record or
artifact that supports or bounds a claim, reproduction, or recovery. A test
definition is not evidence merely because it can produce a result; a retained
result may be. Fixtures, goldens, and oracles can be both, so both guardrails
apply. An existing surviving defense may satisfy `AC-GUARD-005` when the
mapping establishes equal-or-stronger coverage; replacement does not require a
new one-for-one test. Conversely, a proven impossible internal state has no
independent invariant to re-protect: its redundant check and check-only test
may retire together under the recorded low-risk disposition.

## Ratified responsibility and dependency model

`AC-SLICE-02` ratified this model on 2026-08-26. It defines responsibility
direction and forbidden authority transfers without selecting the public
Project/Analysis/Run vocabulary, a Stage API, package layout, class hierarchy,
service roster, policy taxonomy, artifact state vocabulary, or migration order.

The campaign's proposed five bands are responsibility clusters, not source
containers or a promise of one implementation object per band:

| Responsibility cluster | Owns | Does not become |
|---|---|---|
| Interaction and composition | Role-appropriate CLI/UX composition and projection of supported application or advanced-owner capabilities | Scientific implementation, evidence authority, or a second copy of application policy |
| Intent admission and application coordination | Admission of user intent, resolution of an inspectable effective plan, invocation of lower capabilities, and assembly of user-facing outcomes | A Project/Run god object or owner of scientific algorithms, execution backends, policy decisions, artifact admission, evidence meaning, or reporting semantics |
| Functional and downstream product owners | Recognizable transformation, analysis, and evidence owners retain review-relevant semantics; reporting consumes admitted results as downstream operational work | A generic Stage framework; reporting is not a semantic scientific stage and cannot mutate or admit upstream science |
| Neutral contracts and capabilities | Explicit identity facts and contracts plus deliberately selected execution, policy, artifact-lifecycle, and narrow shared capabilities | A mandatory package for every concept, a catch-all policy object, a universal artifact store, or an authority facade that merely forwards existing owners |
| Owned mechanism boundaries | EMRYS adapters contain filesystem, process, runtime, workflow-engine, and scheduler mechanics | Scientific, validation, artifact-admission, recovery, or evidence-promotion authority |

OS, R, Python, filesystems, Snakemake, and SLURM are external mechanisms outside
the owned product graph. An EMRYS adapter may bind and observe them, but a
mechanism's success or metadata cannot decide scientific completion, artifact
admission, recovery safety, or evidence level.

Identity is a responsibility cluster, not a presumed service or package.
Consumers receive authoritative identity facts through explicit contracts
rather than reconstructing competing identities. Public nouns and hierarchy
are settled by the application-model decision below; exact field ownership,
hash composition, persistence, and subordinate exposure remain `AC-DEC-011`
and the applicable identity/application slice.

### Three separate dependency graphs

Architecture decisions and checks keep three graphs distinct:

| Graph | Meaning | Current authority |
|---|---|---|
| Source imports | One source module loads and can directly depend on another source module | [`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md) and its fast Python import ratchet |
| Runtime and control invocation | A coordinator, workflow engine, process, or public entry point requests a capability | The [current architecture](../../architecture/ARCHITECTURE.md), orchestration contract, and affected owner contracts/tests |
| Artifact and evidence flow | An owner consumes an explicitly admitted artifact, record, or evidence relationship | [`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md) for the functional-owner semantic DAG; artifact, orchestration, lifecycle, reporting, and owner contracts plus producer/consumer tests for the remaining flows |

Permission in one graph grants no automatic permission in another. Invoking a
public owner command does not authorize importing its private implementation;
consuming an admitted artifact does not authorize either an import or a reverse
control edge. Numeric order, filenames, validators, and colocated paths create
none of these relationships.

Higher interaction and coordination responsibilities may request declared
capabilities from lower responsibilities. Lower capabilities must not depend on
the application aggregate or reconstruct higher-level state. Until
`AC-SLICE-03` and `AC-SLICE-04` settle the application and operation
interfaces, current calls are descriptive behavior rather than the target API.

### Decision scope filter

A cross-slice architecture decision belongs in this responsibility model only
when it remains true across reasonable class, function, protocol, manifest,
adapter, and existing-owner representations and can be enforced without
inventing a future package or API. Public nouns, package/class/service shape,
methods and schemas, lifecycle states, identity hash composition, physical
storage, workflow-engine integration, defaults and precedence, recovery
mechanics, and migration order remain with their owning just-in-time slices.

`AC-SLICE-02` therefore ratifies representation-independent responsibilities
and forbidden authority transfers, but it does not ratify concrete positive
ownership reserved for `AC-SLICE-03` through `AC-SLICE-07`. Later slices may
select or reject a proposed abstraction only inside the binding responsibility
direction and migration guardrails.

### Forbidden authority transfers

The stable rules below bind later design even where the first automated check
covers only their Python-import projection:

1. **Neutral-contract independence (`AC-DEP-001`).** Neutral contracts do not
   acquire implementation dependencies. Exact current exceptions are bounded,
   ratcheted, and routed to successor decisions; they grant no new permission.
2. **Neutral-library direction (`AC-DEP-002`).** Neutral libraries depend only
   on contracts and lower neutral libraries in an acyclic graph. They never
   import functional, ingestion, application, or reporting owners.
3. **Functional-owner locality (`AC-DEP-003`).** Transformation, analysis, and
   evidence owners retain their semantics and do not import peer owners or
   ingestion, application, or reporting implementation. Cross-owner data uses
   contracts and admitted artifacts.
4. **Input-admission boundary (`AC-DEP-004`).** Ingestion validates and emits
   declarations; it does not acquire functional science, execution, reporting,
   or lifecycle authority.
5. **Downstream-reporting boundary (`AC-DEP-005`).** Reporting consumes admitted
   artifacts, never functional or application implementation, never reruns
   science, and never mutates upstream state or grants upstream completion.
6. **Application non-authority (`AC-DEP-006`).** Application coordination may
   request declared public capabilities but does not import peer-private
   implementation or absorb their semantics. Every current direct capability
   edge is either an approved current seam or a named transition, not a blanket
   domain permission.
7. **Private-owner isolation (`AC-DEP-007`).** A private module is owner-local.
   The grouped composition root may use only the exact owner-declared current
   composition seams; those seams do not become general import APIs. Every
   other cross-owner or composition-root access requires one exact bounded
   transition with a successor and exit condition.
8. **Mechanism non-authority (`AC-DEP-008`).** Scheduler, workflow-engine,
   runtime, process, and storage mechanisms provide attributable facts and
   effects only; adapters cannot reinterpret scientific, policy, validation,
   admission, reporting, or recovery decisions.
9. **Source-domain classification (`AC-DEP-009`).** Every EMRYS product source
   domain has an explicit current responsibility classification before it may
   enter the import graph. Package metadata cannot become an undeclared
   composition root. This is a review gate for new source ownership, not a
   permanent target-package map.

### Cross-slice shape constraints

The following semantic constraints are settled; their representations remain
with the named later slices:

- Application design must distinguish evolvable user intent from an immutable
  inspectable effective plan called `Run` and from operational attempt state
  when present. It must permit multiple analyses over compatible upstream
  work, pass lower owners an explicit immutable contract rather than a broad
  aggregate, and prevent mutable attempt state from altering or reconstructing
  the Run. The later application-model decision settles the public nesting and
  minimum cardinalities without choosing representation.
- A possible Stage boundary stays thin and cannot obscure the distinct
  transformation, analysis, and evidence identities or move review-relevant
  science away from its owner. Functional owners declare needs and semantic
  validity; allocation authority resolves resources; execution enforces the
  result; lifecycle/admission remains logically distinct.
- Supported execution backends owe equivalent declared scientific,
  artifact-integrity, recovery, and evidence guarantees, while mechanisms and
  environment-specific proof may differ. This guarantee contract does not
  select a request/result API or Local/SLURM class design.
- Every policy decision has one declared final authority. Repeated equivalent
  owner-local decisions may move to one shared authority only after inventory
  demonstrates real net reduction; policy is not a mandatory central layer.
- Logical artifact lifecycle/admission is distinct from physical storage.
  Storage, copying, publication, or engine success cannot by itself grant
  scientific completion or admission, and the requirement does not presume a
  distinct Artifact Store.

The public application vocabulary, nesting, and Run-versus-Attempt boundary are
now settled below. Exact field and identity composition, persisted authorities,
recovery ownership, compatibility, and migration remain in `AC-SLICE-03`; the
minimum operation representation remains `AC-SLICE-04`; execution
request/result and backend design remain `AC-SLICE-05`; policy inventory and
owners remain `AC-SLICE-06`; and artifact states, lifecycle API, and Artifact
Store decision remain `AC-SLICE-07`.

### Enforcement strategy

The static preflight scans statically declared Python imports and recognized
literal standard-library dynamic import forms. It enforces the import
projections of `AC-DEP-001` through `AC-DEP-007` plus source-domain
classification under `AC-DEP-009` that can be determined without inventing
future APIs. Exact live composition seams and transitions fail when broadened
and also fail when stale, forcing current-boundary or retirement metadata to
change with the source. The checker does not perform general dynamic-import
data-flow inference, infer semantics from filenames, enforce a future package
map, or treat the current local-pilot topology as the target.

Runtime/control invocation and artifact/evidence flow remain protected by
their explicit contracts, rosters, fixtures, and producer/consumer tests.
Shell, R, workflow, and scheduler relationships are not falsely inferred from
the Python graph. Authority rules that require semantic review—such as no
scientific logic in the CLI, reporting's read-only behavior, and mechanism
non-authority—remain decision and contract obligations until an equally direct
automated oracle exists.

## Ratified application model and Run boundary

`ARCH-MODEL-DECISION-01` ratified this boundary on 2026-08-26 after the
read-only `ARCH-MODEL-AUDIT-01` review. It selects the campaign's option C
without selecting a class hierarchy, serialized schema, package map, storage
layout, command tree, backend interface, or permanent compatibility facade.

The smallest ordinary public model is:

```text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), when operationally relevant
```

- **Project** is the mutable organizational workspace for drafts, declared
  inputs, references, and configuration. It is not execution authority.
- **Analysis** expresses scientist-facing scientific intent. Drafts may evolve;
  an admitted Analysis revision is immutable. Analysis may use a human-facing
  name while retaining its internal immutable identity.
- **Run** is public, has the primary ordinary identifier, and immutably binds
  exactly one admitted Analysis revision to exactly one internal immutable
  Execution Plan. An Analysis revision may have multiple Runs when its
  effective realization differs.
- **Attempt** is progressively disclosed operational history for executing the
  same Run. A Run may have zero or more Attempts; Attempt state and metadata
  cannot alter or reconstruct the Run.
- **Results** is the read-only discoverable surface of Run-bound committed
  outputs. It is not a second mutable completion authority or initially a
  separately managed identity-bearing aggregate.

The internal Execution Plan remains inspectable but is not an ordinary
user-authored or user-managed public noun. Dataset, Reference, and
ExperimentalDesign remain meaningful scientific-definition sections rather
than independent top-level commands or identities by default. Runtime and
execution-profile selection are operator-facing inputs to Run construction and
stay out of the ordinary scientist path unless inspected. Artifact is advanced
inspection vocabulary, Task is an internal implementation detail, and Report
is a regenerable output capability beneath Results rather than a scientific
stage or completion authority.

The Run-versus-Attempt boundary is semantic:

| Change | Consequence |
|---|---|
| Scientific intent changes | Admit a new Analysis revision and create a new Run. |
| The declared Execution Plan changes, including selected toolchain, backend, execution profile, or permissible resource policy | Create a new Run. |
| The same immutable plan is retried or re-executed | Create a new Attempt of the existing Run. |
| Host, scheduler job identifier, timestamps, or actual allocation vary within the Run's declared permissible envelope | Record Attempt metadata; the Run is unchanged. |
| A retry requires resources outside that declared envelope | Create a new Run. |
| Only downstream report enablement or format changes, or a report is generated or regenerated independently | The reporting choice itself creates neither a new Run nor a new Attempt; executing the Run still creates an Attempt. |

Reporting is invoked by default for a full run, can be disabled, and can be
regenerated independently. Reporting failure or regeneration does not rewrite
scientific completion semantics.

Each admitted boundary will have one immutable canonical authority; mutable
dictionaries and cached canonical bytes cannot compete. The application model
also cannot become a god object: application coordination may bind intent and
plan and invoke lower capabilities, but scientific, execution, policy,
artifact, evidence, and reporting authorities remain with their owners.

Still open are the exact fields, identity digest inputs and relocation
semantics, permissible-envelope representation, serialized and in-memory
forms, persistence and storage, recovery ownership for an unreceipted run
skeleton, status vocabulary, APIs and operation signatures, CLI mapping,
backend and policy interfaces, and bounded compatibility/migration details.
Those choices require the next `AC-SLICE-03` field-and-authority decision
package before any model implementation.

## Organize by functional owner

Keep each stage, analysis, evidence operation, reporting component, or neutral
domain with its implementation, native assets, commands, contract, diagnostics,
recovery behavior, and mirrored tests. Public starter inputs and repository
development controls remain outside runtime domains when they are not
implementation-native.

A source move goes directly to its final current owner. Compatibility paths are
exceptional, bounded, parity-protected, and removable. Placement creates no
installed package, new runtime behavior, or evidence.

## Use semantic identities and artifact edges

Each functional owner has a semantic slug and stable versioned machine key;
numeric identifiers remain historical aliases. Required produced artifacts and
declared barriers create DAG edges. Filenames, narrative order, shared
directories, validators, or one wrapper's materialization behavior do not.

Exact identities and edges live in
[`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md). Current source and
dependency rules live in
[`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md).

## Share only proven equivalence

Keep the first use owner-local. Compare behavior, failure, recovery,
determinism, and scientific meaning before extraction. Promote only sufficiently
complex or safety-relevant equivalent reuse, with independent API and consumer
tests, into the narrowest neutral owner. Never create a generic utility bucket,
force cross-language DRY, or let neutral code depend on a functional owner.

## Preserve inspectable boundaries

Cross-owner data passes through explicit contracts; owners do not import peer
private implementation. Reporting remains downstream of computation and
evidence. Dependency restoration, Git/documentation tooling, quality gates,
and project environments remain repository controls rather than scientific
workflow domains.

## Select a local-first orchestration boundary

The first workflow control plane uses Snakemake's local executor because the
existing semantic owners already expose the scientific operations and artifact
edges that a general-purpose workflow engine should schedule. EMRYS therefore
does not build a second scheduler, stage registry, scientific implementation,
or recovery system. One fixed profile is easier to inspect and prove than a
generic extension surface before a second real workflow exists.

Human YAML remains concise while ordered scientific records stay in TSV. A
normalizer resolves and hashes explicit inputs into canonical JSON so formatting
and caller working directory cannot determine run identity. The complete
execution contract remains distinct from the existing reporting run contract:
reporting is a downstream projection and cannot silently become lifecycle
authority.

Owner validation is evidence production rather than a process-level Boolean;
several validators intentionally publish `status=fail` with exit zero. Each
workflow task must consequently parse the persisted report and publish its own
content-bound verified record only after every row passes. This record is a
local scheduling/reuse boundary, not a scientific or cluster promotion.

Local execution precedes site execution so workflow semantics can be proven
without mixing CSU modules, storage, accounting, or scheduler policy into the
scientific graph. SLURM and the possible Linux VM remain deferred rather than
rejected. The decision-complete lifecycle and resume rules are in
[`ORCHESTRATION_CONTRACT.md`](../ORCHESTRATION_CONTRACT.md); accepted remaining
work is tracked in the [findings matrix](../../tasks/backlog_matrix.md).

The public control plane remains thin: it reruns read-only admission, prints an
exact no-write plan by default, materializes only the fixed profile under the
aggregate run lock, and delegates scientific work to public owners. It exposes
no raw Snakemake flags or automatic owner recovery.

The application-logging foundation is implemented under
[`LOGGING_CONTRACT.md`](../LOGGING_CONTRACT.md), while production-command
adoption remains `LOG-05`. Report profiles, analysis modules, public
acquisition, standalone workflow packaging, and site profiles remain designs,
not current architecture. Accepted outcomes are in the
[findings matrix](../../tasks/backlog_matrix.md); unsliced alternatives remain
in the temporary
[architecture campaign](../../tasks/architecture_campaign.md).

## Adopt application logging through accepted operations

Application logging migrates incrementally through separately approved semantic
application-operation slices, not through blanket instrumentation of the
current command and wrapper surface. This prevents transport and compatibility
layers from becoming competing lifecycle or logging authorities while allowing
accepted facades to adopt logging as they land. Planning and conformance work
may precede production adoption, and unrelated campaign work need not finish
first. An explicitly approved transitional compatibility operation is eligible
for bounded support but does not satisfy final retained-operation coverage. The
broader realization choices—fields, execution, identity composition, status,
filesystem, APIs, compatibility, and overall order—remain open.
