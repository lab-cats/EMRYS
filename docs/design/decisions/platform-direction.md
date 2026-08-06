# Platform-direction decisions

These decisions constrain future architecture without claiming that deferred
capabilities exist. Current topology lives in
[`ARCHITECTURE.md`](../../architecture/ARCHITECTURE.md), target ownership in
[`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md), and
open choices in [`QUESTIONS.md`](../QUESTIONS.md).

## Safe architectural change

### Protect behavior before architectural mutation

Before structural change, classify applicable behavior as preserved contract,
characterized defect, undefined and requiring a decision, or environment-
deferred. Readiness requires appropriate independent protection for preserved
behavior, not a particular coverage percentage. Defect correction and approved
interface change remain explicit work rather than silent refactor effects.

### Govern future work through a file-backed task registry

One Markdown card owns each task's scope, technological dependencies,
deliverables, acceptance, and completion record. Lifecycle authority, approval,
priority, and evidence remain separate concepts. Lightweight proposals grant no
selection authority; completed cards are historical records and follow-up work
gets a new identity. Exact current rules live in
[`docs/tasks/README.md`](../../tasks/README.md).

### Use an architecture runway with rolling vertical delivery

Settle only expensive-to-reverse cross-cutting invariants ahead of delivery,
then plan and execute bounded vertical slices just in time. Each slice closes
its own inspection, authority, implementation, validation, documentation, and
feedback loop. Coordination never replaces task scope, lifecycle, approval, or
live evidence.

### Target a vertical package with direct contract-preserving migrations

Organize preprocessing stages, analyses, evidence operations, reporting, and
neutral domains by functional ownership. Keep implementation, validation,
native assets, local documentation, and local contracts together; mirror tests,
prohibit peer-implementation imports and generic utility buckets, and use the
narrowest neutral seam for true sharing.

Move a concern directly to its final owner. Compatibility paths are exceptional,
bounded, parity-protected, and removable. Source placement creates neither an
installable package nor new runtime or scientific evidence.

### Converge cross-cutting source without misclassifying repository surfaces

Application implementation follows the target source topology. Public operator
inputs and reference tables remain explicit root interfaces when they are not
implementation-native; Git/documentation tooling, quality gates, dependency
restoration, and project environments remain repository controls. Directory age
or root placement alone does not establish an application owner.

### Identify stages semantically and order them with a DAG

Each functional stage, analysis, or evidence owner has a human title, semantic
slug, and stable versioned machine key. Numeric identifiers remain historical
aliases. Explicit artifact edges and barriers define order; filenames and
numeric sequence do not. Exact identities and edges live in
[`STAGE_MAP.md`](../../../src/norad/contracts/STAGE_MAP.md).

### Promote shared libraries only from proven reuse

Keep the first use local. At later uses, compare behavior, failure, recovery,
determinism, and scientific meaning before extracting. Promote at two uses only
for sufficiently complex or safety-critical equivalence; otherwise prefer the
third equivalent use. Shared code uses the narrowest neutral owner, independent
API and consumer tests, and no dependency on a functional owner. Do not force
cross-language DRY or merge intentionally independent scientific validation.

## Future intake and extension

### Use YAML run requests with TSV sample manifests

A future ready YAML request carries run policy and explicit paths while
referencing one TSV sample manifest. Claim, validate, hash, and normalize it
atomically into an immutable run contract; retries create attempts, while
changed inputs or policy create a new run. Failed requests remain resumable,
raw inputs stay stationary, and computational success does not promote
scientific state. Exact fields and operational paths remain open until their
own contract is approved.

### Prioritize local FASTQ and registered references before public acquisition

First stabilize local paired FASTQ plus registered references. Add public
reference acquisition before SRA read acquisition, then consider other sources
or input types. Reference FASTA and annotation records are not reads and are
never converted to FASTQ; read acquisition uses its own adapter and lifecycle.

### Preserve an extension path for preprocessing profiles and analysis modules

Design toward typed preprocessing profiles and typed analysis-module inputs and
outputs, including scientist-authored R analyses. Do not assume one universal
preprocessing trunk or treat arbitrary file-discovering scripts as trusted
modules. Current work preserves typed branch points without inventing a generic
loader, registry, universal schema, or alternate assay.

### Keep an installable control plane as a later capability

A later thin Python control plane may expose contract validation, DAG planning,
scheduler submission, filesystem-inspectable run state, resume, and reporting.
It does not reimplement scientific tools or install dependencies during compute.
Packaging non-Python assets and materializing immutable run-bound jobs remain
explicit later distribution decisions; illustrative commands are not current
public commitments.

### Keep optional-analysis success and request archival future-only

Preserve current success semantics until multiple analysis modules establish a
real contract. Later define how required and optional failures affect run state,
retry, reporting, and request-metadata archival. Raw inputs remain stationary,
and computational success never implies scientific or biological readiness.

## Future reporting

### Make science reporting the future default and retain comprehensive reporting

Retain the comprehensive report as an explicit profile and define a smaller
science-focused projection as a future default. Both profiles derive from one
versioned, format-neutral projection, preserve semantic parity across formats,
and coexist without overwriting immutable bundles. Exact names, flags, and
field rosters remain open until characterization and approval.

### Separate concise console output from durable detailed logs

The durable logging direction is summarized in
[`execution-evidence-and-reporting.md`](execution-evidence-and-reporting.md#separate-concise-console-output-from-durable-detailed-logs)
and specified by the
[`logging target`](../../architecture/FUTURE_ARCHITECTURE.md#logging-target).

## Documentation and deferred engineering

### Treat documentation and maintainer context as architecture

The durable documentation decision is recorded in
[`repository-and-delivery.md`](repository-and-delivery.md#treat-documentation-and-maintainer-context-as-architecture).

### Defer repository skills until the underlying practice is proven

The durable automation boundary is recorded in
[`repository-and-delivery.md`](repository-and-delivery.md#defer-repository-skills-until-the-underlying-practice-is-proven).

### Decision-capture crosswalk

This record owns rationale only. Current and target topology, exact contracts,
commands, live task state, evidence, and unresolved choices remain with their
dedicated owners linked above and from [`DECISIONS.md`](../DECISIONS.md).

### Deferred engineering

Future engineering preserves public behavior, scientific meaning, evidence
ceilings, and transaction/recovery contracts. Interfaces change only through
approved, tested migrations; accidental placement is not a permanent promise.
