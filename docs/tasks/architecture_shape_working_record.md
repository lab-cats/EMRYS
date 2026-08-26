# Architecture shape working record

**Status:** Temporary working decision record; approved direction as of
2026-08-26

**Scope:** `AC-SLICE-02` through `AC-SLICE-07`

**Disposition:** Absorb the durable decisions into their subject owners and
accepted backlog items, then retire this file. Git history retains the temporary
record.

## Authority and purpose

This file prevents the first implementation or the current source tree from
becoming the architecture by accident. It records the agreed semantic shape,
the decisions intentionally reserved for later slices, and the working plan for
formalizing and enforcing the architecture.

It is not:

- a second backlog or task registry;
- a replacement for the [architecture campaign](architecture_campaign.md);
- a replacement for the
  [architecture backlog matrix](architecture_backlog_matrix.md) or the
  repository [backlog matrix](backlog_matrix.md);
- a package map, class diagram, API specification, or migration order;
- authority to move code, introduce abstractions, or implement later slices.

The [platform-direction constitution](../design/decisions/platform-direction.md)
remains the durable owner of the ratified architectural invariants. The
campaign remains the temporary owner of unsliced source context. This record
narrows the next design work without silently promoting provisional mechanics
to durable architecture.

For statements explicitly marked **Approved now** or **Approved reporting
behavior**, this record contains the later user-approved resolution and
temporarily supersedes conflicting `Open` wording in the campaign until the
documents are normalized. The campaign remains authoritative for source
context, alternatives, and every portion of a question not resolved here.

Within this file:

- **Approved now** means the semantic responsibility or prohibition may be
  carried into `AC-SLICE-02`.
- **Reserved** means its owning later slice must make the decision with live
  implementation evidence.
- **Transitional** describes current implementation structure and never means
  target architecture.
- Suggested names, phases, numeric targets, detailed APIs, and migration order
  remain provisional unless this file explicitly says otherwise.

### Campaign decision reconciliation

| Campaign decision | Approved constraint recorded here | Still open |
|---|---|---|
| `AC-DEC-001` | Three semantic lifetimes and no one-to-one cardinality assumption | Public nouns, hierarchy, identity vocabulary, and nesting |
| `AC-DEC-006` | External mechanisms remain behind owned boundaries and all backends owe equivalent declared guarantees | Runtime/execution representation, profiles, and backend selection |
| `AC-DEC-008` | Any common operation boundary is thin, preserves functional ownership, and cannot become a generic framework | Name, representation, methods, granularity, schemas, discovery, and migration |
| `AC-DEC-009` | Policy is a family of owned decisions; shared abstractions require demonstrated repetition and may not become a catch-all facade | Inventory, taxonomy, final authorities, interfaces, precedence, and migration |
| `AC-DEC-010` | Logical lifecycle/admission is distinct from physical storage and storage cannot grant scientific completion | Vocabulary, states, owners, APIs, receipts, rollback, and migration |
| `AC-DEC-011` | Application coordination composes capabilities but does not absorb their authority; lower capabilities receive narrow contracts | Final Run contents, API, identity boundaries, and lifecycle coordination |
| `AC-DEC-012` | Scientific and reporting outcomes remain distinguishable | Public state vocabulary and representation of partial or recoverable outcomes |
| `AC-DEC-014` | Reporting is downstream operational work, invoked by default during a full run, disable-able, and independently regenerable; its failure does not invalidate completed science | Exact invocation interface, persisted lifecycle representation, status/exit vocabulary, receipts, location, and derived-view mechanics |
| `AC-DEC-025` | Artifact capability does not imply an Artifact Store, and storage cannot become a second completion/admission authority | Whether a Store exists and its exact logical or physical responsibilities |

## Governing approach

The campaign's five-band stack remains a target responsibility model, with
three required qualifications:

1. A band is a cluster of responsibilities, not a source directory, package,
   class hierarchy, service, import target, or one-to-one owner.
2. The proposed `Project / Run Application API` and `Stage` vocabulary is
   illustrative until `AC-SLICE-03` and `AC-SLICE-04` settle the public model
   and operation boundary.
3. OS, R, Python, SLURM, Snakemake, and filesystems are external mechanisms.
   EMRYS-owned adapters sit at the product boundary; the mechanisms themselves
   are not an ordinary internal layer or an authority over scientific meaning,
   artifact admission, or recovery.

Reporting has a special relationship to the bands: it is an automatically
invoked downstream projection by default, not a peer semantic scientific
stage. Its approved behavior is specified below.

Identity is a responsibility cluster, not a presumed service or package.
Consumers receive authoritative identity facts through explicit contracts
rather than reconstructing competing identities. Exact vocabulary, ownership,
and hash composition remain reserved.

### Two maps, not one interim stack

Architecture work will maintain two explicitly different views:

1. **Normative target responsibility map**
   - Defines responsibilities, allowed dependency direction, and forbidden
     authority transfers.
   - Does not require target packages or APIs before their owning slices.
2. **Descriptive current-owner crosswalk**
   - Maps live owners to target responsibilities.
   - Marks each mapping `aligned`, `transitional`, or `unresolved`.
   - Names the later decision owner and a retirement or resolution condition
     for every transitional mapping.

The current local-pilot control surface is evidence about present behavior and
an important behavior oracle. It is not the future package map or application
API.

### Three dependency graphs

The formal architecture must represent these separately:

1. source imports;
2. runtime and control invocation;
3. artifact and evidence flow.

An allowed downstream artifact consumption does not necessarily authorize a
source import or a reversed control dependency. Enforcement must state which
graph a rule protects instead of collapsing all three into a single vertical
stack.

### Decision filter

A decision belongs in `AC-SLICE-02` when it:

- governs responsibility or dependency direction across several later slices;
- follows the ratified invariants and current owner contracts;
- remains true whether implemented with classes, functions, protocols,
  manifests, adapters, or existing owners; and
- can be enforced without inventing a future package or API.

A decision remains reserved when it selects:

- public nouns or exact hierarchy;
- a package, class, protocol, service, method, or schema;
- state vocabulary or identity/hash composition;
- physical storage or workflow-engine integration;
- detailed defaults, precedence, retry, or recovery mechanics; or
- a representative migration and retirement order.

The controlling rule is:

> `AC-SLICE-02` may ratify responsibilities and forbidden authority transfers,
> but it must not ratify concrete positive ownership where `AC-SLICE-03`
> through `AC-SLICE-07` still own the design.

## `AC-SLICE-03`: application model

### Approved now

The architecture distinguishes three semantic lifetimes without yet assigning
their final public names:

1. evolvable, user-authored scientific intent;
2. an immutable, inspectable effective specification for a particular
   realization, with the boundary between science-affecting values, execution
   values, run identity, and attempt identity still reserved; and
3. one or more operational attempts against that immutable specification.

The model must not assume one-to-one cardinality. It must permit:

- shared datasets, references, and designs to support multiple analyses;
- separately identified downstream, cohort, subset, sensitivity, or
  differential analyses;
- compatible upstream artifact reuse;
- multiple attempts against one immutable realization; and
- independent regeneration of downstream projections such as reports.

An application-coordination role may admit intent, resolve an effective plan,
invoke lower capabilities, and assemble user-facing outcomes. It must not
implement scientific algorithms, execution backends, policy decisions,
artifact admission or publication, evidence semantics, or reporting semantics.

Lower capabilities receive an explicit immutable contract containing only
supported lower-level information. Whether this is one narrow shared context
type or multiple owner-specific capability views remains reserved. They do not
import or depend on a broad higher-level Project, Analysis, Run, or application
aggregate.

User-authored scientific intent remains distinct from site and operator
execution choices. Those inputs may be resolved into an inspectable effective
plan without making scientific intent the owner of runtime or execution policy.

### Reserved for `AC-SLICE-03` and related identity work

- Whether the public model uses Project, Analysis, Run, all three, or different
  nouns.
- Exact hierarchy, nesting, and public cardinalities.
- Whether the application boundary is represented by classes, immutable
  records, use-case services, functions, a facade, or a combination.
- Exact operations, arguments, return types, error model, and synchronous or
  asynchronous behavior.
- Whether consumers receive one context type or narrower capability views.
- What contributes to analysis, run, attempt, artifact, and report identity.
- Whether runtime, executor, resource, or report choices change a run identity.
- User-authored configuration schemas and filenames.
- Package locations, stable import surfaces, CLI mapping, compatibility
  windows, and migration order.
- Whether report generation contributes to persisted Run lifecycle or
  completion state; default invocation and the separate scientific/reporting
  status relationship are already constrained below.

## `AC-SLICE-04`: operation or Stage boundary

### Approved now

`Stage` is a reserved term for a possible thin operational capability boundary.
It is not currently approved as a package, base class, registry, workflow
framework, or universal scientific owner.

Transformation stages, scientific analyses, and evidence owners retain their
distinct semantic identities. A shared execution capability must not erase
those distinctions or move review-relevant algorithms, parameters,
assumptions, interpretation limits, contracts, or direct tests away from their
recognizable functional owners.

Any future common operation representation must be able to express, directly
or by reference:

- stable owner identity;
- typed inputs and outputs;
- explicit dependencies;
- runtime and resource needs;
- semantic validation responsibility;
- failure behavior;
- provenance and trust requirements; and
- report integration where applicable.

These are representational obligations, not approved fields or methods.

Responsibility direction is approved as follows:

- functional owners declare resource needs and science-affecting constraints;
- the designated allocation authority, whether owner-local or later
  centralized after the policy inventory, resolves effective allocations;
- execution mechanisms enforce the resolved allocations;
- functional owners define semantic validity and produce owner-local
  validation evidence;
- execution may invoke and record validation but cannot redefine scientific
  success; and
- artifact admission, publication, durability, rollback, and recovery remain
  logically distinct responsibilities, without implying separate packages or
  owners.

There will be no mandatory inheritance hierarchy, universal registry,
abstract-factory tree, generic workflow language, or second scheduler. A common
abstraction must remove a demonstrated repeated responsibility without
obscuring or wrapping an existing authority.

### Reserved for `AC-SLICE-04`

- Whether the final boundary is called Stage.
- Protocol, dataclass, manifest, adapter, callable, or existing-command shape.
- Methods or fields such as `execute()`, `validate()`, `describe()`, inputs,
  outputs, and resources.
- Invocation granularity: owner, analysis, sample, partition, scoped
  invocation, or planned task.
- Lifecycle and state vocabulary.
- Input/output representation and schema evolution.
- Resource units, minima versus requests, defaults, precedence, and scheduler
  translation.
- Runtime and tool-dependency representation.
- Extension discovery, installation, trust admission, and version
  compatibility.
- Representative owner, migration mechanics, and generalization threshold.

### Provisional validation approach

Before selecting a common denominator, the design should initially paper-map a
transformation owner, a scientific analysis, an evidence owner, and reporting.
A candidate next step is one representative migration, with further
generalization dependent on demonstrated net reduction and evidence that a
second distinct owner maps without distortion. The exact number of mappings,
migrations, and their order remains unsettled.

## `AC-SLICE-05`: execution capability

### Approved now

EMRYS will define one execution guarantee contract, not prematurely define one
execution API. Every supported backend must satisfy the same declared:

- scientific-boundary guarantees;
- artifact-integrity guarantees;
- recovery guarantees; and
- evidence and attribution guarantees.

Mechanisms and the environment-specific evidence needed to prove those
guarantees may differ between local and SLURM execution.

External execution mechanisms are reached through EMRYS-owned boundaries.
Scheduler and workflow-engine observations are attributable facts; they are not
scientific-completion, artifact-admission, validation, or recovery authority.
Snakemake remains an execution mechanism, and no second scheduler will be
introduced.

### Reserved for `AC-SLICE-05`

- Task-, owner-, run-, or workflow-level execution granularity.
- Request/result types, method names, and implementation names.
- Local and SLURM adapter or subclass design.
- Backend/profile selection and resource vocabulary.
- Workflow-engine placement and integration.
- Job states, retries, cleanup, cancellation, recovery, and resume mechanics.
- Exact local/SLURM parity tests and evidence claims.

## `AC-SLICE-06`: policy ownership

### Approved now

Policy is a family of explicitly owned decisions, not a mandatory package,
layer implementation, or central catch-all object.

Every policy decision has one declared final authority. Inventory may justify
moving repeated equivalent decisions from owner-local authorities to one shared
authority only when doing so removes real duplication. Functional owners
declare their requirements and request decisions; adapters and execution
mechanisms do not reinterpret those decisions. Empty forwarding wrappers and a
monolithic policy facade are prohibited.

### Reserved for `AC-SLICE-06`

- The final policy taxonomy and whether every proposed policy deserves an
  abstraction.
- Package or service placement.
- Exact final owners, configuration inputs, return types, and error model.
- Defaults, override semantics, and precedence.
- Consolidation order, compatibility behavior, and migrations.

## `AC-SLICE-07`: artifact lifecycle and storage

### Approved now

Logical artifact lifecycle and admission are distinct from physical storage.
An artifact capability does not imply an Artifact Store, directory, physical
collection, or one generalized lifecycle implementation.

Functional owners retain scientific production and semantic validation.
Lifecycle and admission compose explicit content-bound references with recorded
validation. Storage, copying, publication, or a workflow-engine success signal
cannot by itself grant scientific completion or artifact admission.

Reporting consumes admitted references downstream. It may publish its own
derived, content-bound report artifacts, but it cannot publish upstream
scientific artifacts or mutate upstream scientific state.

### Reserved for `AC-SLICE-07`

- Artifact classes and lifecycle state names.
- One generalized lifecycle owner versus class-specific owners.
- Whether a distinct Artifact Store exists and, if so, whether it is a logical
  API, manifest view, physical collection, or another form.
- Admission/publication APIs, schemas, manifests, and receipts.
- Physical filesystem structure, external or large artifact handling, and
  immutability mechanisms.
- Run Bundle and report-derived-artifact relationships.
- Rollback, cleanup, recovery, and representative migrations.

## Approved reporting behavior

Reporting is not a semantic scientific stage, and its success does not
determine scientific completion. It may still be represented or scheduled as
downstream operational work.

During a full run:

1. scientific and evidence owners complete their own work;
2. required upstream artifacts are admitted;
3. reporting is invoked automatically by default as a downstream projection;
   and
4. the reporting outcome is shown separately from scientific completion.

Users and operators may disable the default reporting invocation. The exact
configuration field, CLI spelling, and advanced/debug route remain reserved for
the applicable public-UX slice.

Reports can be regenerated independently from admitted artifacts and evidence
without rerunning scientific work. Disabling reporting or regenerating a report
does not change the identity or validity of the completed scientific run. A
generated report may have its own content-bound artifact and version identity.

A reporting failure must be visible. The full command may return an
unsuccessful or partial outcome because its requested default projection did
not complete, but the reporting failure does not invalidate already completed
scientific work or admitted upstream artifacts. Independent report regeneration
is a supported recovery path. Exact retry/resume mechanics, status names, exit
behavior, and UI presentation remain reserved.

## `AC-SLICE-02` working plan

The following sequence is a working plan, not a commitment to permanent phase
names, numeric targets, package boundaries, or the detailed ordering of later
implementation slices.

### 1. Preserve the approved shape

- Use this temporary record as the review artifact.
- Reconcile every approved statement with the constitution, campaign, live
  owner contracts, and current tests.
- Keep disagreements explicit; do not resolve them through incidental wording
  or source movement.

### 2. Define the normative responsibility map

- Define the target responsibility clusters and dependency direction.
- State forbidden authority transfers independently of package names.
- Mark application-model, operation-boundary, execution-API, policy-taxonomy,
  and artifact-lifecycle details as reserved for their owning slices.
- Keep reporting downstream and external mechanisms outside the owned product
  graph.

### 3. Build the current-owner crosswalk

For each relevant current owner, record:

- current source owner;
- target responsibility or responsibilities;
- whether the relationship concerns imports, invocation, or artifact flow;
- `aligned`, `transitional`, or `unresolved` status;
- current authority and protected behavior;
- owning later decision slice;
- interim exception or protection, if needed; and
- retirement or resolution condition.

The crosswalk must expose current contradictions without treating them as
permission for a mass package migration.

### 4. Define enforcement against durable rules only

Candidate fast checks may prohibit:

- scientific semantics in CLI or generic orchestration code;
- scientific owners acquiring scheduler, storage, or publication authority;
- reporting mutating upstream run state or publishing upstream artifacts;
- lower capabilities depending on a higher application aggregate;
- direct acquisition of external-system authority outside owned boundaries;
- peer owners importing one another's private implementations; and
- introduction of a second scheduler or generic workflow framework.

Checks must not require imports from nonexistent `project`, `run`, `stage`,
`execution`, `policy`, or `artifact_store` packages. Any rule depending on a
future request/result schema, policy taxonomy, lifecycle state model, or backend
API remains documented and unenforced until its owning slice settles it.

Where the live tree does not yet satisfy a durable rule, record and protect the
known exception with an owner, rationale, successor slice, and retirement
condition. Do not weaken the target rule or silently declare the current edge
permanent.

### 5. Validate the enforcement design

- Keep the architecture check fast and deterministic locally.
- Use focused fixtures for the check itself.
- Route long or broad repository checks through CI.
- Confirm that the enforcement protects stable responsibility boundaries
  without requiring any `AC-SLICE-03` through `AC-SLICE-07` implementation.
- Demonstrate that an intentionally forbidden edge fails with an actionable
  diagnostic.

### 6. Hand off concrete design to the owning slices

- `AC-SLICE-03` settles the public application model and narrow context views.
- `AC-SLICE-04` maps diverse functional owners and selects the minimum common
  operation representation.
- `AC-SLICE-05` designs execution request/result behavior and proves backend
  guarantees.
- `AC-SLICE-06` inventories repeated decisions before selecting policy
  abstractions.
- `AC-SLICE-07` designs lifecycle and admission before deciding whether an
  Artifact Store exists.

Each slice should prefer one representative migration and prove net reduction
before generalizing. No slice may use the current crosswalk as authority to
preserve accidental coupling.

### 7. Normalize and retire this record

After review and slicing:

- move durable cross-cutting decisions to the platform-direction or other
  directly affected subject owners;
- preserve unsliced rationale and alternatives in the architecture campaign;
- put accepted implementation outcomes and acceptance criteria in the one
  backlog matrix;
- update the architecture campaign ranking only where its provisional scoring
  or slice description needs reconciliation; and
- delete this temporary file once no unique context remains.

Retirement is not complete until every approved decision, deferred decision,
rationale, and intended end state has a durable owner or an explicit disposition.

## Deliberately open decisions

The following remain open after this record:

- final public conceptual nouns and hierarchy;
- exact application and operation APIs;
- final identity vocabulary and hash composition;
- operation granularity and extension mechanism;
- execution request/result and backend design;
- policy inventory and taxonomy;
- artifact states, lifecycle owner, and Artifact Store decision;
- physical run and result layout;
- exact report opt-out, regeneration, status, and exit-code interfaces;
- package mapping, compatibility windows, and source migration order; and
- final names, numbered phases, numeric targets, and detailed campaign ordering.

## Review anchors

- [Architecture campaign](architecture_campaign.md)
- [Architecture campaign ranking](architecture_backlog_matrix.md)
- [Repository backlog](backlog_matrix.md)
- [Platform-direction constitution](../design/decisions/platform-direction.md)
- [Current source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md)
- [Current semantic owner map](../../src/emrys/contracts/STAGE_MAP.md)
