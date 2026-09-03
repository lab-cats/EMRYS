# Architecture rationale

The scientific core is considerably simpler than the software surrounding it.
EMRYS therefore compresses its operational surface while preserving scientific
reviewability, provenance, recovery, and honest evidence claims.

## Protect behavior before structural change

Before changing structure, classify affected behavior as a preserved contract,
a characterized defect, an unresolved decision, or environment-deferred. Add
or identify protection for preserved behavior before mutation. A refactor does
not silently change science or a public contract.

## Ratified architectural invariant constitution

These invariants are permanent design constraints. Exact behavior lives in the
applicable owner contract, schema, and tests.

- **Scientific meaning is explicit.** Pairing, cohorts, strata, conditions,
  orientation, algorithms, parameters, thresholds, candidate universes, and
  interpretation boundaries are never inferred from filenames or hidden by an
  operational abstraction. Determinism is claimed only where an owner defines
  it. Computational success, ranked candidates, scientific review, and
  biological validation remain different claims.
- **Identity and provenance are content-bound.** A result is traceable to its
  exact scientific inputs and configuration, source and package identity,
  admitted toolchain, and execution. Durable artifact references bind semantic
  identity and exact content; changed bytes require re-admission. Generated
  manifests and normalized configuration remain inspectable and attributed.
- **Completion and recovery fail closed.** Partial, foreign, or ambiguous state
  is not complete. Resume reuses only independently re-admitted compatible
  work and cannot change the immutable plan. File presence, timestamps,
  scheduler state, and workflow-engine metadata are never completion
  authority. Local and HPC guarantees require separate evidence even when
  their scientific result is expected to match.
- **Evidence is not promoted.** Reports derive from admitted artifacts and
  validations without rediscovering or recalculating science. Scientific,
  provenance, operational, local, synthetic, runtime, cluster, production,
  review, and biological evidence remain distinguishable. Required low-level
  records may be hidden from normal views but remain inspectable under their
  retention and redaction policy.
- **Ordinary operation hides implementation detail.** Scientists do not need
  developer-only knowledge, raw engine controls, task records, transaction
  states, or forensic identities. Effective supported values and their source
  remain inspectable. EMRYS neither prints secrets nor invents biological
  meaning. Automatic mutation is bounded, attributable, and recoverable where
  the operation permits it.

## Ratified abstraction, migration, and test guardrails

1. **Inspectable control (`AC-GUARD-001`).** An override exists only where its
   owner declares a safe supported boundary; implementation-only values need
   not be overrideable.
2. **Scientific visibility (`AC-GUARD-002`).** Operational abstractions may hide
   mechanics, never the scientific logic, assumptions, parameters, or code
   needed for review.
3. **Bounded migration (`AC-GUARD-003`).** Migrate in reviewable vertical
   slices. A replacement is complete only after all intended callers move,
   relevant parity passes, and the superseded path retires. Any compatibility
   path has an owner and retirement condition (`AC-GUARD-004`).
4. **Risk-aware protection (`AC-GUARD-005`).** External-input, filesystem,
   concurrency, crash/recovery, persistence, evidence, and supported-public-
   behavior defenses require an equal-or-stronger surviving defense at the
   same evidence level. A check against an impossible same-process state may
   retire when an audit proves one immutable producer, no supported mutation or
   injection path, and no distinct failure mode. High-risk, ambiguous, user-
   facing, execution-boundary, or evidence-validation retirement,
   consolidation, conversion, or removal requires explicit user approval.
5. **Maintenance compression (`AC-GUARD-006`).** Every audit identifies
   concrete consolidation and deletion opportunities across product code,
   tests, scripts, schemas, configuration, documentation, compatibility, and
   mutable state. Implementation defaults to a meaningful net reduction in
   maintained product code and no product-file growth. A quantified exception
   needs explicit approval and, if temporary, an owner and retirement trigger.
   Counts are reported separately and cannot be improved by deleting evidence,
   tests, or documentation unrelated to the implementation.
6. **Use existing tools first.** Before writing owned machinery, evaluate the
   existing owner, standard library, mature maintained libraries, and relevant
   package manager. Bespoke code must close a concrete capability gap or reduce
   the total maintained surface. Touched shell programs are retained,
   converted, or retired explicitly; a line-for-line language port is not
   compression.
7. **Immutable by default (`AC-GUARD-007`).** Boundary values are immutable
   unless a narrow owner lifecycle requires mutation. A Run is the immutable
   plan. Draft and Attempt-local state cannot alter or reconstruct it.
8. **Evidence deletion is separate (`AC-GUARD-008`).** Removing exact retained
   evidence requires explicit user approval and its own commit. Evidence
   deletion never offsets implementation growth. The proposal must name the
   exact artifact or class, producers and consumers, claims and recovery paths,
   retention need, redundancy basis, effects on discoverability, verification,
   and evidence level, and rollback. Ambiguous fixtures, goldens, oracles,
   receipts, logs, reports, and dated records remain evidence until classified.

A shared policy owner is justified only when at least two production owners
make the same decision from equivalent inputs with the same defaults,
precedence, errors, and outputs, and one caller-complete migration produces a
net reduction. Re-admission at a different trust or mutation boundary is not
duplicate policy.

## Ratified responsibility and dependency model

The five bands are responsibilities, not packages or mandatory abstractions:

```text
+-----------------------------------------+
|                 CLI / UX                |
+-----------------------------------------+
|       Project / Run application         |
+-----------------------------------------+
| Scientific | Evidence | Reporting       |
+-----------------------------------------+
| Artifact | Execution | Policy | Identity|
+-----------------------------------------+
| OS / R / Python / SLURM / Filesystem    |
+-----------------------------------------+
```

Higher responsibilities may request declared lower capabilities. Lower
capabilities do not depend on a higher-level user workflow or reconstruct its
state. In particular:

- scientific owners do not implement scheduler, runtime, storage, reporting,
  or application policy;
- reporting consumes admitted results and may publish only its own downstream
  transaction; it cannot rerun or admit upstream science;
- input admission validates declarations without acquiring execution or
  scientific authority;
- neutral contracts have no implementation dependencies; neutral libraries
  remain acyclic and do not import functional or application owners;
- cross-owner data travels through explicit contracts and admitted artifacts,
  never a peer's private implementation; and
- filesystems, processes, workflow engines, runtimes, and schedulers provide
  attributable effects and observations, not scientific, admission, recovery,
  or evidence authority.

Source imports, runtime/control invocation, and artifact/evidence flow are
three distinct graphs. Permission in one grants no permission in another.
[`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md) owns the
import graph; [`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md) owns
the scientific artifact DAG; current owner contracts own runtime and remaining
artifact/evidence relationships.

## Ratified application model and Run boundary

The ordinary public model is:

```text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), when operationally relevant
```

- **Project** is the mutable organizational root for declared inputs,
  references, configuration, runs, logs, and runtime material. It is not
  execution authority.
- **Analysis** is scientist-authored intent. A draft may change; an admitted
  Analysis revision is immutable. Multiple named Analyses may share compatible
  processing.
- **Run** publicly and immutably binds one admitted Analysis revision to one
  generated internal Execution Plan. A plan change creates a new Run.
- **Attempt** records execution or retry of the same Run. Host, scheduler ID,
  timestamps, and allocation within the declared envelope are Attempt facts.
  A retry outside that envelope requires a new Run.
- **Results** is the read-only, discoverable Run-bound output surface. It is
  not another mutable completion authority.

Dataset, Reference, and experimental design are sections of scientific intent.
Runtime and execution profiles are operator inputs to Run construction.
Execution Plan and Artifact are advanced inspectable vocabulary; Task is
internal. Report is a regenerable Results capability, not a scientific stage.
A full Run invokes reporting by default, supports an explicit opt-out, and can
regenerate reports independently without changing Run or Attempt identity.

One content-derived Run ID remains authoritative. The deterministic two-word
name is presentation and selection metadata only. The Project root owns
`project.yaml`, `runs/`, `logs/`, and `runtime/`; Results remain beneath the
Run. There is no parent/global Project search, mutable alias registry, inferred
latest Run, second Results root, or Run Bundle.

## Current platform choices and reconsideration triggers

- Snakemake is the sole execution backend. Direct execution and whole-Run
  single-node Slurm placement share it. Add a backend abstraction only for an
  approved concrete backend or a demonstrated caller-complete net reduction.
- Artifact classes retain their separate admission and transaction owners.
  Add neither a universal lifecycle nor an Artifact Store without a concrete
  unmet class-level need.
- There is no public stop/cancel command until queued and running submission
  ownership plus a safe terminal interruption contract exist across supported
  placements. Resume remains bounded to an already interrupted or failed Run.
- Execution profiles resolve from `runtime/profiles/NAME.yaml`, with an exact
  absolute path allowed. There is no site/global registry; reconsider only for
  a demonstrated cross-Project/site need.
- Runtime acquisition may be Managed, Site, or Explicit, but all modes converge
  on the same Project-owned admitted inventory. Doctor diagnosis is read-only.
  Explicit repair is previewed, delegates solving and installation to existing
  package managers, mutates only EMRYS-owned environments, and requalifies.
- Collaborator analysis providers declare closed configuration, typed
  artifacts, dependencies, minimum resources, one Step 09 and optional Step 10,
  plus a bespoke scientific reporter. This is not a universal Stage model,
  workflow language, installer DSL, report DSL, or mutable registry.
- Candidate review and biological interpretation remain outside EMRYS. A
  future Steps 07–09 scientific audit and independent-oracle expansion are
  backlog work, not evidence that a defect exists.
- Add no broader package API or generalized storage facade without a concrete
  extension need or a measured caller-complete reduction in maintained code.

Current package ownership and public routes are summarized in the
[`architecture index`](../../architecture/README.md). The
[`findings matrix`](../../tasks/backlog_matrix.md) is the only work backlog.
