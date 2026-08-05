# Decisions

This file records durable choices, rationale, alternatives, and consequences.
Current pipeline/package status belongs in
[`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), task-workflow status belongs to card
directory placement under [`../tasks/`](../tasks/), current evidence belongs in
[`../operations/HANDOFF.md`](../operations/HANDOFF.md), and commands belong in
[`../operations/RUNBOOK.md`](../operations/RUNBOOK.md).

## Development and repository

### Use TSV manifests

Decision: sample, partition, inventory, approval, and evidence manifests are
tab-separated when a table is appropriate.

Reason: TSV is easy to inspect and parse across shell, Python, and R without
CSV quoting ambiguity. Consequence: headers and row order are public
contracts and must validate exactly. This does not require a future run request
to be tabular: the approved intake direction uses one YAML request for run
policy that references one TSV sample manifest.

### Develop locally and scale through SLURM

Decision: editing, fixtures, mocks, and syntax checks happen locally; heavy
production computation runs through SLURM jobs.

Alternative rejected: executing heavy work on the login node.

### Use descendant branches and separate docpatch gates

Decision: delivery remains linear and every package descends from the latest
clean, published, documentation-patched predecessor. An executable state and
its documentation close remain separate reviewable commits; a documentation-
only package needs no artificial executable checkpoint. One approved campaign
may execute sequential cards on one branch rather than creating a branch per
card.

Reason: evidence, interfaces, and current state remain reviewable at every
boundary without turning a historical branch shape into architecture. Exact
delivery procedure belongs in
[`TASK_DELIVERY.md`](../operations/TASK_DELIVERY.md), and current lineage in
`PIPELINE_PLAN.md`.

### Keep executable programs out of Markdown

Decision: Markdown may contain short example commands and invocations, but not
extended shell, Python, or other executable programs. Substantive operational
logic belongs in parameterized files under `scripts/`, with focused tests and
normal implementation gates; the owning documentation links to those files and
explains sequence, authority, inputs, outputs, and interpretation.

Reason: embedded programs are difficult to test, inventory, reuse, review, and
keep synchronized. Separating logic from explanation keeps canonical documents
readable while making operational safeguards inspectable as code. The first
application is the fragment workflow under `scripts/git_orchestration/`.

Consequence: extracting an embedded program is an executable change, not a
documentation-only cleanup. Short snippets must not grow into shadow scripts;
move them once they encode branching, repeated validation, mutation, recovery,
or publication behavior.

### Permit isolated concurrent authoring with serialized integration

Context: parallel mutation in one worktree contaminates status, staging,
validation, and evidence, while fully serial authoring wastes independent
capacity.

Decision: preserve one authoritative linear lineage and one single-writer
integration/control worktree. Concurrent candidates use isolated branches and
worktrees with exact identities, bounded write sets, and explicit coupling;
long execution uses an immutable exact commit. Coupled work cannot silently
land across an unsettled contract or evidence boundary, and only combined
canonical validation can close the package.

Rationale: isolation permits useful parallel authoring without creating a
second source of truth or weakening rollback and evidence attribution.

Consequences: exact roles, lane packets, authority, integration, and recovery
belong in [`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md); current
lanes belong in `HANDOFF.md`. A candidate or lane packet remains a proposal,
not authorization, lineage, status, or evidence.

### Use transient integration fragments for cross-owner proposals

Context: an isolated candidate can discover facts owned elsewhere. Direct
edits would violate authority; ad hoc notes can be lost; permanent proposal
notes would create a shadow documentation system.

Decision: a candidate may publish at most one structured transient fragment
alongside its reserved deliverables. The fragment requests canonical-owner
changes but grants no authority. The integration owner verifies the frozen
source, gives every request and residual a terminal disposition, routes
accepted material, and removes the fragment before canonical publication.

Rationale: this preserves provenance and prevents silent loss without making
proposal state durable truth. A permanent preservation-ref namespace was
rejected because it would add an archive and lifecycle the protocol does not
need.

Consequences: field syntax belongs in
[`docs/fragments/README.md`](../fragments/README.md), authority and lifecycle
in [`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md#integration-fragment-authority-and-lifecycle),
and exact commands and publication checks in
[`RUNBOOK.md`](../operations/RUNBOOK.md#manual-integration-fragment-exchange).

### Run one complete computational gate per executable state

Decision: use focused tests during implementation, then run one de-duplicated
complete computational gate against the final executable state before its
implementation commit. A documentation-only close may reuse that evidence only
when Git proves no executable, dependency, test, schema, fixture, template, or
gate semantics changed. A wholly non-consuming documentation package runs Git
and documentation validation only.

Reason: rerunning identical multi-runtime suites before both the implementation
and documentation commits adds substantial latency without testing a new
executable state. Any executable change after the recorded gate invalidates
reuse and reopens the full implementation/docpatch sequence.

### Prefer failure-first validation output

Decision: routine successful validation is quiet; complete diagnostics appear
for failure or an explicit verbose run. The complete developer gate uses a
bounded orchestrator, not unconstrained `make -j`. Parallel defaults require
repeated exact serial parity, measured benefit, controlled failure/interruption
cleanup, pinned developer dependencies, and a deterministic serial fallback.

Reason: success narration consumes attention without changing evidence, while
failures must remain complete and attributable. Exact lane and threshold
policy belongs in `PIPELINE_PLAN.md` and the gate implementation.

### Route task context by revision and impact

Resolved ID: `CHOICE-CONTEXT-01`.

Decision: [`TASK_START.md`](../operations/TASK_START.md) is the concise routing
owner. A task begins with live Git state, the selected card, its bounded local
surfaces, and applicable canonical sections. Context is reusable only when its
revision is identifiable, Git proves it unchanged, and its detail is sufficient.
Unknown revisions, contradictions, ownership/structural changes, or unbounded
scientific, evidence, safety, recovery, publication, or public-contract impact
expand inspection. A phase boundary triggers reassessment, not an automatic
full-corpus read.

Reason: the former phase-boundary corpus exceeded 9,000 lines, much of it
unrelated and unchanged. Version-aware reuse plus explicit expansion triggers
preserves the correctness boundary without paying that cost repeatedly. An
unversioned summary or another agent's statement remains orientation rather
than live proof.

### Use proportional planning categories and bounded approval envelopes

Resolved ID: `CHOICE-PROGRAM-02`.

Decision: semantic planning category and validation impact are independent;
tests follow affected contracts, risk, and acceptance rather than topic labels.
One explicit bounded approval envelope may authorize routine in-scope work,
but preserves objective, included cards, classifications, Git/lane identity,
write set, mutations, evidence boundary, exclusions, unresolved choices, and
stop conditions. Expansion requires revised approval. A lane packet projects
authority and never creates it; preferred order is not a technological blocker.

Rationale: semantic review can be broad without executable impact, and a small
consumed file can demand tests. Rejected alternatives include one-dimensional
risk classes, uniform maximum ceremony, topic-triggered computational testing,
repeated in-envelope approval, packet-as-authorization, and order-as-blocker.

Consequences: operational classification and envelope fields belong in
[`TASK_START.md`](../operations/TASK_START.md); projected lane fields belong in
[`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md). The decision creates
no metadata schema, gate, receipt, task authority, or current evidence.

### Make documentation consistency impact-directed

Decision: use the final package diff, canonical ownership, inbound references,
and repository-wide targeted searches to discover documentation and diagram
impact. Inspect affected sections, owners, consumers, and changed diagrams;
broaden only for cross-cutting, contradictory, ownership-changing, or unbounded
impact. The repository-wide structural gate remains compact global evidence.

Reason: repository-wide search and validation coverage protects consistency;
repository-wide manual line-by-line reading is not a necessary proxy for that
coverage.

### Keep active and future tests separate

Decision: active runnable shell tests live under `tests/shell/`; future plans
live under `tests/pending/` and are not wired into active targets.

### Treat legacy scripts as protocol references

Decision: translate legacy behavior into parameterized, tested interfaces.
Do not copy hardcoded paths, samples, or undocumented assumptions.

## Execution and publication

### Default to dry-run

Decision: workflow scripts require `--execute`; SLURM wrappers use
`EXECUTE=0` by default and accept only `0` or `1`.

Reason: operators should inspect resolved inputs, outputs, tools, and commands
before publication.

### Publish validated transactions

Decision: multi-file stages use owned locks, run-token staging, input rechecks,
validation before publication, rollback, cleanup, and a receipt or summary
published last.

Consequence: transaction completion describes the publication set, not the
success or existence of every underlying evidence item.

### Preserve recovery evidence

Decision: do not automatically delete locks, backups, or recovery markers when
ownership, rollback, or cleanup cannot be proved.

Alternative rejected: optimistic cleanup that can destroy the only evidence
needed for safe recovery.

### Characterize unsafe publication states before correcting them

Decision: adversarial tests freeze both protected behavior and explicitly
labeled unsafe states for the shared step-validator publisher and each
distinct ancillary publisher before any implementation is changed. A known-
gap assertion records the observed failure boundary; it does not approve that
behavior, weaken the recovery decision above, or make unlike transaction
implementations interchangeable.

Reason: publication, rollback, signal, descriptor, and cleanup paths are easy
to change in ways that improve one exception while silently deleting foreign
or recovery evidence in another. Test-only characterization gives the later
reliability review concrete states to preserve or deliberately correct without
prematurely extracting a generic publication framework.

## Reference and BAM pipeline

### Use the Novogene-provided reference

Decision: the delivered reference is the workflow reference unless a separate
migration is approved. Reference FASTA, annotation, sidecars, BED, and STAR
index identities must reconcile explicitly.

### Build STAR with the declared read-length overhang

Decision: the reference index uses `sjdbOverhang=149` for the declared
150-base reads. Validators must inspect the configured value rather than infer
it from filenames.

### Generate BED12 from GTF

Decision: RSeQC consumes a deterministic BED12 derived from the declared GTF.

### Treat FASTA sidecars as Step `00c`

Decision: FAI and sequence dictionary preparation is a formal, validated step,
not an undocumented prerequisite.

### Make Step `02` the canonical BAM boundary

Decision: downstream consumers use coordinate-sorted, indexed BAMs with
sample-specific read-group metadata. Publication is validation-first and
rollback-protected.

### Keep QC and downstream transformation as separate consumers

Decision: BAM QC, orientation inference, and duplicate marking consume the
canonical BAM independently. QC evidence does not mutate the BAM.

### Mark rather than remove duplicates

Decision: Step `04` marks duplicates and preserves reads for downstream policy
decisions.

### Validate the effective Java runtime

Decision: resolve the actual Java executable, log its version, and fail before
Picard when it is below the required major version. Module names and
`JAVA_HOME` alone are insufficient evidence.

Node pinning is a temporary operational mitigation, not architecture.

### Use project storage for large GATK temporary files

Decision: Step `05` routes large temporary files to an owned project-storage
location and cleans only paths it owns.

## Orientation and downstream analysis

### Separate mechanical orientation from biological strand

Decision: retain neutral `FWD_like` and `REV_like` labels. Do not infer
biological sense/antisense from flag groupings.

Reason: the cohort is reverse-stranded/first-strand-style, but read
orientation, transcript strand, and biological interpretation are distinct.

### Run Step `07` cohort-wide and manifest-partitioned

Decision: each declared partition processes all manifest samples together in
manifest order for both mechanical orientations. Selector type determines the
bcftools interface. Outputs and counts are committed by a receipt published
last.

No input discovery by glob and no sample-order inference are allowed.

### Consume only declared Step `07` transactions in Step `08`

Decision: Step `08` verifies the exact partition/orientation cross-product,
receipts, paths, hashes, counts, and sample order before semantic parsing.

Multiallelic records are expanded deterministically; symbolic and non-SNV
alleles are counted and excluded. Raw count lexemes are validated before
semantic coercion.

### Keep the orientation policy provisional

Decision: `legacy_provisional_v1` is a compatibility mapping, not biological
validation. Outputs and reports must retain that limitation.

### Pair Step `09` samples only through manifest replicates

Decision: pairing is explicit manifest metadata, never inferred from sample
names. The declared design requires matching treatment/control replicate sets
and at least two strata.

### Use one paired CMH and global BH family

Decision: Step `09` retains every eligible and ineligible candidate with an
explicit status, uses the declared two-sided continuity-corrected CMH
direction, and applies one BH family across successfully tested target
candidates.

Outputs are “CMH-ranked candidates,” not validated editing sites.

## Runtime environments

### Guard the repository-local R environment

Decision: repository activation occurs only when `NORAD_USE_RENV=1`; `0`
leaves normal startup unchanged and other values fail. Restoration is an
explicit operator action. Compute scripts and tests never bootstrap packages.

Reason: local reproducibility must not silently alter ordinary R startup or
cluster jobs.

### Restore report tooling explicitly

Decision: Quarto restoration is separate from rendering and testing. Installed
identity, receipt, tree, and version must validate before reuse. Rendering
never installs or repairs software.

### Probe runtime availability from explicit profiles

Decision: runtime preflight evaluates one exact declared profile in an
explicit execution context and installs or repairs nothing. Login-shell or
local availability does not prove batch visibility; context mismatches remain
blocked/not checked. Even an all-pass batch report is availability evidence,
not workflow runtime validation or cluster proof.

### Reconcile references without repair

Decision: reference provenance hashes and reconciles one explicit inventory,
including declared annotation identity and contig agreement, without repairing
or regenerating shared artifacts. Filenames and colocation are not provenance;
reported inconsistencies require separate operator resolution.

### Measure storage without acting on retention policy

Decision: storage evidence measures exact declared roots and records a separate
retention-policy approval state. Capacity evidence and authorization must be
inspectable, but the observational tool never deletes, moves, archives,
compresses, or otherwise changes data.

## Evidence and scientific state

### Separate computational proof and scientific interpretation

Decision: implementation, fixture testing, real-runtime testing, cluster
dry-run, cluster proof, scientific review, and biological readiness are
independent fields.

`cluster-proven` requires inspected scheduler, log, command, and output
evidence. Report generation is not validation.

### Preserve two post-review states

Decision:

- `science_review_complete_exploratory` records a completed but provisional
  evidence review;
- `biological_interpretation_ready` is reserved for stricter, separately
  approved exit criteria.

Current tools must reject an unauthorized ready state.

### Require explicit evidence relationships

Decision: passed, failed, or proven claims require their defined evidence
roles. Runtime and cluster roles additionally require exact underlying paths
and hashes. Blocked or not-run states are never proof.

## Structured artifacts and reporting

### Decouple reporting from computation

Decision: native compute outputs remain unchanged behind explicit, read-only
artifact adapters. Renderers consume a canonical structured summary rather
than native outputs directly.

### Use versioned closed schemas

Decision: public artifact, scientific-review, run-summary, and report-receipt
documents use explicit schema versions. A closed shape is not silently
changed; incompatible changes require a version increment.

### Inventory physical artifacts explicitly

Decision: each expected-artifact row names one concrete physical path.
Artifact IDs and physical paths are unique; logical-scope rows remain
contiguous and stable. Globs, unresolved templates, traversal components, and
implicit machine substitutions are rejected.

### Bind run identity to immutable analysis inputs

Decision: run identity derives from explicit sample, reference, partition, and
primary-analysis policy identities. Changing an identity component requires a
new run ID. Inventory revisions are adapter-attempt metadata, not silent run
identity changes.

### Represent missing and failed evidence

Decision: expected scopes remain in records and summaries when missing,
failed, incomplete, externally unavailable, blocked, or not run. Absence is
not silently dropped.

### Adapt step validation reports without promotion

Decision: each step validator publishes the exact seven-column report contract
defined in the pipeline plan and receives a step-specific read-only artifact
adapter. Failed checks remain failed artifact and expected-scope states through
the canonical summary and consolidated reports.

Reason: validation evidence must be visible without hand-editing artifact
records or inferring a stronger runtime state. A published local validation
report records only its explicit checks; it does not create cluster proof,
scientific review, or biological readiness.

### Authorize supplemental report tables explicitly

Decision: a report table enters the canonical summary only through an exact,
nonempty approval manifest bound to the run contract and active scientific
review. Path, hash, row count, role, display limit, policy, approver, and time
must reconcile. Omission authorizes no tables.

Canonical summary JSON must not be hand-edited.

### Render deterministic, static reports

Decision: reports are self-contained, script-free, accessible projections of
one canonical run summary. They use exact scientific-state banners and disclose
truncation with the full source path and hash.

One format-neutral content projection keeps HTML and PDF semantically aligned
while permitting format-specific accessible layout and structural validation.
The selected static format set plus summary TSV and deterministic receipt is
published transactionally; exact modes, assets, defaults, and validation live
with the reporting owner and its tests.

Alternative deferred: a richer tab interaction model with additional
keyboard, responsive, print, and browser behavior. It requires separate
review and focused interaction coverage rather than adding script execution
to the current static report implicitly.

Rendering never discovers inputs, invokes analysis engines, installs
dependencies, or promotes evidence state.

## Measure Python coverage without replacing scenario gates

Decision: pin Python coverage as a developer-only dependency, measure line and
branch execution across the complete Python suite and configured Python
subprocesses, and compare a deterministic tracked snapshot by exact ratios.
Checks reject ratio regressions or removed baseline modules; new shared Python
modules start at 90% line and 85% branch. Baseline regeneration is reviewed;
tests and runtime never install the tool or rewrite the snapshot.

Reason: a measured floor makes later refactors comparable, while percentage
coverage alone cannot establish assertion independence, public-contract
completeness, transaction safety, real-R behavior, cluster execution, or
scientific correctness. The public-contract matrix and independent scenario
tests remain separate gates.

## Documentation ownership

Decision: every information category has one canonical owner recorded in
[`DOCUMENTATION_OWNERSHIP.md`](../sitemap/DOCUMENTATION_OWNERSHIP.md).
Documents link instead of copying mutable state, commands, identities, counts,
or diagrams; intentional action-point safety repetition remains allowed.

Reason: mutable copies drift. Unique information must be discoverable at its
destination before removal; uncertainty remains explicit, and a purposeful
historical reference may remain only with a named consumer and evidence
boundary. Preservation is not promotion.

## Approved architecture direction (2026-07-31)

These approved directions constrain future planning but do not authorize a
task or represent target behavior as implemented. Each task still requires
live inspection, bounded planning, and approval.

### Protect behavior before architectural mutation

Context: the repository has substantial local coverage, but tests vary in
independence and no percentage can prove that every behavior intended for
preservation is protected.

Decision: before structural mutation, classify applicable behavior as
`preserved contract`, `characterized defect`, `undefined — decision required`,
or `environment-deferred`. Readiness means every preserved-contract row has
appropriate protection, not 100% line coverage. Independent goldens or semantic
oracles do not derive expectations from the producer; integrated fixtures
remain complementary. Migrations add focused characterization and old/new
parity where feasible, and an approved interface change is explicit rather
than a silent regression.

Rationale: this preserves intentional behavior while allowing known defects
and accidental paths to be handled honestly. The alternative—treating every
current output as correct or treating high coverage as readiness—would freeze
defects and leave shared producer/test mistakes undetected.

Consequences: characterized defects remain defects and corrections remain
separate tasks. The evidence record lives in
[`TEST-01C`](../tasks/COMPLETED/TEST-01C-characterize-validation-check-rosters.md)
through
[`TEST-01Z`](../tasks/COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md).

### Govern future work through a file-backed task registry

Resolved IDs: `CHOICE-LIFECYCLE-01`, `CHOICE-TASK-IDENTITY-01`, and
`CHOICE-TASK-VIEW-01`.

Context: a broad roadmap cannot carry enough settled constraints for dozens of
small future agents, while putting Jira-like detail in every canonical owner
would recreate responsibility leak.

Decision: one Markdown card owns each task's scope, technological dependencies,
deliverables, acceptance, and completion history. Directory placement is the
current lifecycle authority. Moving a card to `IN_PROGRESS` starts read-only
planning, not implementation; blocker fields name only genuine technological
impediments, while order, approval, environment, and repository-state
conditions use their own owners. Completed cards are immutable history and
follow-up work receives a new card.

`UNREFINED` preserves lightweight proposals without granting selection,
dependency, roadmap, or implementation authority. `INTEGRATION_REVIEW` is used
only when an exact frozen candidate awaits asynchronous canonical review beyond
the current unpublished package; same-package handoff and integration remain
under the active card. Logical epics are navigation groups, never lifecycle or
blocker substitutes. Exact current lifecycle rules and card schema belong in
[`docs/tasks/README.md`](../tasks/README.md).

The future target uses permanent ID-only card paths, structured lifecycle
authority, one authored technological-dependency direction, and committed
check-regenerated views. Stable identity, separate approval, immutable history,
explicit promotion, no mixed roots, and no prose-inferred status/evidence remain
mandatory. Current directory authority stays canonical until one atomic
parity-validated migration.

Rationale: a file-backed registry is inspectable, reviewable with code, and
locally usable without introducing an external project system. The alternative
of expanding the roadmap into task specifications would duplicate status and
rationale across owners.

Consequences: the approved semantic migration is owned by
[`TASK-REG-01`](../tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md).
The rejected permanent target is directory-owned identity/status because moves
destabilize paths and mix identity with lifecycle. On-demand-only generated
views were rejected because they weaken browseability, reviewability, stale-
output detection, and deterministic recovery; a single replaceable tranche
dashboard was rejected because it loses durable history and stable links.
Committed projections accept bounded churn for exact regeneration and fail-
closed drift detection.

### Use an architecture runway with rolling vertical delivery

Resolved ID: `CHOICE-TRANCHE-VIEW-01`.

Context: a phase-wide waterfall creates stale plans, speculative cards, broad
context, and delayed empirical feedback even when each card is iterative.

Decision: settle expensive-to-reverse cross-cutting invariants in small
coordinated planning cohorts, then plan and execute bounded vertical cards just
in time. A normal card closes its inspect, plan, approve, execute, validate,
document, integrate, and feedback loop before dependent delivery advances. A
design card executes by producing a reviewed decision; it does not absorb all
downstream implementation.

`TEST-01Z` gates structural architectural mutation, not independent read-only
inventory or characterization. Planning reconciles only the minimum shared
architecture and next evidence-supported delivery tranche. Architecture,
reliability, and usability reviews remain independent but attach to the risk
boundaries they govern rather than one monolithic plan. Future-only cards
preserve constraints without joining the current release gate or receiving
speculative detailed plans.

The future target uses durable per-tranche coordination artifacts plus one
recoverable current pointer, not a replaceable dashboard. A tranche links its
approved envelope, cards, evidence boundaries, reconciliation basis, and next
trigger without becoming lifecycle, roadmap, authorization, or live-results
state. Individual cards remain the execution and approval units.

Rationale: high-fan-out topology, contract, state, recovery, and evidence
decisions are cheaper and safer to reconcile before files move. Local
implementation choices are more accurate after feedback from a completed
slice. The hybrid keeps necessary architecture without front-loading the whole
refactor.

Consequences: `PROGRAM-01` owns the remaining tranche mechanism and cohort
choices. Tranche artifacts coordinate approved cards but never replace card
scope, lifecycle, approval, validation, publication, or live status owners.

### Target a vertical package with direct contract-preserving migrations

Resolved ID: `CHOICE-ARCH-01`.

Context: the former flat application layout mixed functional ownership, while
packaging and public distribution remained premature. Accidental repository
paths did not justify indefinite compatibility surfaces.

Decision: the target is a vertical source tree with distinct preprocessing
stages, first-class analyses, evidence operations, and neutral application
domains. Functional owners keep implementation, validation, native assets,
human documentation, and local contracts together; cross-owner contracts are
neutral, tests mirror ownership, and no owner imports a peer implementation or
uses a generic `utils` bucket. Exact homes and dependency direction live in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).

Move each concern directly to its final home. A hybrid layout is temporary
migration scaffolding only, and any legacy wrapper is named, parity-tested,
bounded, and removed. Exact caller order, parity evidence, rollback, and
removal rules live in
[`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md).

Rationale: the final vertical home provides local ownership and supports a
later installable package without forcing versioning now. A permanent hybrid
would create dual ownership; a big-bang move would exceed the behavior and
review boundary.

Consequences: exact current placement belongs in
[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) and the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md);
exact target homes and movement procedure remain in `SOURCE_TOPOLOGY.md` and
`MIGRATION_MECHANICS.md`. Physical convergence does not create packaging or
distribution commitments.

### Converge cross-cutting source without misclassifying repository surfaces

Context: directory age and root placement do not distinguish application
implementation from intentional public inputs or repository controls.

Decision: cross-cutting application concerns use the exact contract,
reporting, and evidence homes in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#cross-cutting-implemented-target-homes).
Explicit operator starter configurations and reference tables remain under
root `configs/`; Git/documentation orchestration, quality tooling, dependency
restoration, and project environments remain repository interfaces. Deferred
scheduler, ingestion, and runtime-orchestration/profile work is not inferred
from those retained paths. A prohibited peer-implementation dependency must be
resolved through the narrowest separately reviewed neutral seam.

Rationale: application ownership converges without moving public inputs or
repository controls into invented runtime domains. The explicit provenance
delta is narrower and more truthful than either indefinite compatibility paths
or a simultaneous report-interface redesign.

Consequences: the functional-owner inventory owns current retained/deferred
root surfaces; `SOURCE_TOPOLOGY.md` owns durable dependency direction. Source
placement alone neither changes public provenance semantics nor promotes
runtime or scientific evidence.

### Identify stages semantically and order them with a DAG

Resolved ID: `CHOICE-STAGE-01`.

Context: numeric names such as `00c`, `02b`, and `09c` convey historical order
but not user meaning. Encoding order in a new filename would repeat the same
problem and make future branches awkward.

Decision: each functional stage, analysis, or evidence owner has a display
title for people, a public semantic slug, and a stable versioned machine key.
Numeric IDs remain historical provenance/aliases. Explicit DAG edges define
order and branch points.

Retain a minimal user overview with a conceptual sequence table and Mermaid
diagram explaining purpose, ordering rationale, and input/output contracts.
The current detailed technical pipeline remains separate. Exact identities,
typed external inputs, edges, and barrier semantics live in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md).

Rationale: semantic identities improve comprehension while stable keys and a
DAG decouple identity from mutable order. The alternative of deleting all
historical identifiers would weaken provenance.

Consequences: see
[`ARCH-02B`](../tasks/COMPLETED/ARCH-02B-define-semantic-stage-map.md) and
[`DOC-PIPE-04`](../tasks/TODO/DOC-PIPE-04-create-user-pipeline-overview.md).

### Promote shared libraries only from proven reuse

Context: repeated code exists, but similar parsing, transaction, and scientific
checks can have different semantics or be intentionally independent.

Decision: keep the first use local. At the second use, compare full behavior,
failure, recovery, determinism, and scientific meaning. Extract at two uses
only when the code is safety-critical or sufficiently complex; otherwise the
normal promotion point is a third equivalent use. Choose the narrowest neutral
owner, prohibit shared-to-stage dependencies, require independent API and
consumer tests, and do not force cross-language DRY.

Rationale: this captures real reuse without converting lexical similarity into
repository-wide coupling or a shared defect. The alternatives of never sharing
or extracting on sight both impose avoidable maintenance risk.

Consequences: intentional independent validation, scientific algorithms,
review policy, reporting projection, and heterogeneous transactions remain
local. Neutral ownership does not establish a public import name, package
marker, build metadata, or installable distribution. The reviewed shared
surfaces, consumers, and prohibited scope are owned once in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#approved-neutral-shared-seams);
historical selection evidence remains in `MIG-03A` and `LIB-02F`.

### Apply risk-based source-size thresholds

Context: very large mixed-responsibility files defeat bounded review and local
context, but raw line count is not a safe decomposition plan.

Decision: a materially changed file above 600 lines receives advisory cohesion
review, and new files normally remain below 600. A file above 1,000 lines needs
a decomposition plan or explicit justification before architectural mutation.
A file above 1,500 lines must be eliminated during the current repo-spanning
refactor unless the owner approves an explicit exception. Split tests by
scenario/comprehension, not arbitrary length.

Rationale: thresholds force a cohesion decision without rewarding mechanical
fragmentation. A single low limit would create a massive low-value rewrite; no
limit would preserve the current cognitive bottlenecks.

Consequences: report rendering is owned by `RPT-05B`; the remaining families
are owned by `SIZE-07*`. Step `08` requires a proven non-algorithmic seam or an
explicit time-bounded exception because scientific refactoring is not already
authorized. See
[`SIZE-07`](../tasks/TODO/SIZE-07-refresh-large-file-inventory.md).

### Use YAML run requests with TSV sample manifests

Context: a scientist-facing autonomous run needs structured policy and repeated
sample rows. One YAML document containing every row would be awkward to inspect
and transform across shell, Python, and R; TSV alone cannot express nested run
policy clearly.

Decision: one ready YAML request references one TSV manifest. YAML owns run
policy and explicit paths; TSV owns repeated sample metadata. V1 accepts paired
FASTQ/FASTQ.GZ and registered FASTA/GTF inputs. Claim a request atomically,
resolve/validate/hash/normalize it into an immutable run contract, and represent
execution retries as attempts.

The same normalized request identifies the same run; a retry creates a new
attempt; changed input or policy creates a new run. Failed requests remain
resumable. Promote only request/run metadata after all currently required
tasks, validators, evidence assembly, and requested report succeed. Raw data
remains stationary. `data/raw` is storage, not the ingestion state machine.

Rationale: YAML plus TSV gives each data shape a natural, inspectable owner.
Atomic claim and immutable identity prevent duplicate runs and ambiguous
resume. Moving raw data on success would couple compute state to storage and
make recovery/destructive behavior harder to reason about.

Consequences: exact fields and operational directory names remain open in
[`INTAKE-02E`](../tasks/TODO/INTAKE-02E-define-yaml-tsv-run-lifecycle.md).
Future required/optional success and archival semantics are separate.

### Prioritize local FASTQ and registered references before public acquisition

Context: NCBI resources expose both reference records and sequencing reads,
which are not interchangeable formats or lifecycle concerns.

Decision: first stabilize local paired FASTQ plus explicit registered
references. Next add NCBI reference acquisition/registration, then SRA read
acquisition, then consider ENA, GEO, or BAM inputs. Reference FASTA/FNA and
annotation GTF/GFF3/GBFF remain reference artifacts and are never converted to
FASTQ. SRA read records may materialize FASTQ through a separate read adapter.

Rationale: reference provenance/versioning and read download/conversion have
different validation, identity, storage, and retry risks. A single “GenBank to
FASTQ” adapter would make a category error.

Consequences: public acquisition is future-only in
[`FUT-DATA-02`](../tasks/TODO/FUT-DATA-02-public-reference-and-sra-acquisition.md)
and does not expand current V1 intake.

### Preserve an extension path for preprocessing profiles and analysis modules

Context: the long-term scientific goal is a reusable preprocessing system with
a library of analyses and a straightforward custom R boundary. Different DNA
or RNA assays may require different upstream transformations.

Decision: design toward typed preprocessing profiles and typed analysis-module
inputs/outputs, including scientist-authored R analyses. Do not assume one
universal preprocessing trunk. The current CMH workflow may become the first
built-in module. Future trust can distinguish exploratory custom modules from
registered modules, with explicit provenance and report/evidence limits.

Rationale: this goal is feasible when modules consume typed artifacts and
declare dependencies, outputs, failure, and evidence semantics. It becomes
unsafe if “any R script” means untyped file discovery, hidden working
directories, or automatic trust promotion.

Consequences: current work may preserve clean branch points and contracts but
must not build a generic loader, registry, universal schema, or alternate assay.
See
[`FUT-ANALYSIS-01`](../tasks/TODO/FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md).

### Keep an installable control plane as a later capability

Context: a future `norad` package could provide one operational interface, but
packaging/versioning now would freeze unstable internal paths and non-Python
asset decisions.

Decision: later build a thin Python control plane for contracts, DAG planning,
scheduler submission, filesystem-inspectable run state, resume, and reporting.
Illustrative commands are `validate`, `plan`, `run`, `status`, `resume`,
`report`, and `stages`; they are not yet public commitments. The control plane
does not reimplement scientific tools or install dependencies during compute.

Packaged non-Python assets means explicitly including schemas, templates,
styles, R/shell resources, or other runtime data in a distribution. Materialized
jobs means writing an immutable, run-bound copy of a resolved scheduler script
rather than submitting a mutable package resource directly. Both are later
packaging concerns.

Rationale: the vertical source target enables installation later without
forcing premature distribution design. Filesystem state preserves recovery and
inspection when the CLI is absent.

Consequences: see
[`FUT-CLI-03`](../tasks/TODO/FUT-CLI-03-installable-norad-control-plane.md).

### Make science reporting the future default and retain comprehensive reporting

Context: the current report provides valuable complete diagnostics but its
density and wide local scroll regions overwhelm the default scientist journey.

Decision: characterize and retain the current comprehensive report as an
explicit profile. Define a smaller science profile that becomes the future
default. Its starting field families are evidence state, CMH-ranked findings,
QC/filter funnel, sensitivity/replicates, decisions/limitations, and concise
methods. Every field receives a useful title and description.

Use one versioned, format-neutral projection so HTML and PDF have semantic
parity. The science view must not use horizontal scrolling inside panels;
responsive records or format-appropriate layouts must preserve meaning. Profile
outputs coexist and never overwrite existing immutable bundles. Exact public
profile names/flags and the final field roster remain open until report
characterization.

Rationale: a projection-first split reduces cognitive load without deleting
diagnostic evidence or entangling content with one renderer. Replacing the
current report in one change would risk silent information loss.

Consequences: report work is deliberately split across
[`RPT-01`](../tasks/TODO/RPT-01-characterize-comprehensive-report.md) through
[`RPT-06`](../tasks/TODO/RPT-06-make-science-report-the-default.md). This
decision changes no report behavior; any profile or default change requires
the linked card. The target implementation owner is `src/norad/reporting`.

### Separate concise console output from durable detailed logs

Resolved IDs: `CHOICE-LOG-01` and `CHOICE-LOG-02`.

Context: the
[`LOG-01` inventory](TEST_BASELINE.md#log-01-current-output-and-log-inventory)
found valuable recovery detail mixed with repetitive human output, thirteen
validators mixing machine TSV rows with human stdout, only conditional
scheduler-level complete capture, and no general local application log.

Decision: separate concise operator-facing console output from complete durable
diagnostic logs under the versioned target contract in
[`FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md#logging-target).
Declared machine responses remain on stdout and human events on stderr. A log
level changes projection only, never computation, validation, publication,
recovery, evidence, or exit behavior. One operation owns one no-clobber log;
delegated components never append concurrently.

The receipt remains the authoritative transaction marker. Pre-receipt logging
faults follow the owner's existing failure/recovery path, while protected
partial logs and bounded sanitized failure guidance remain inspectable.
Application logs are operator-owned protected data: no automatic rotation,
upload, truncation, or deletion, and no evidence promotion without a separately
authorized immutable role/path/hash relationship.

Rationale: deleting diagnostic detail would harm maintainability; printing all
detail by default harms usability and context efficiency. Stable stream,
identity, and publication ownership protects automation and recovery without
confusing scheduler capture, application state, or scientific evidence.

Consequences: exact controls, event schema, stream rules, failure bounds,
scheduler relationship, and adoption obligations live once in the target
contract. Implementation and default activation remain separately reviewed
work; this decision alone changes no current output or evidence.

### Treat documentation and maintainer context as architecture

Resolved IDs: `CHOICE-DOC-01` and `CHOICE-DOC-GATE-01`.

Context: abbreviations, opaque directories/fixtures, overlapping documents,
and undocumented module invariants make the repository expensive to inspect.
Broad mandatory reads also consume context that local ownership could avoid.

Decision: documentation has explicit audience and responsibility owners.
Eligible directories receive shallow parent and detailed local READMEs; opaque
or byte-sensitive artifacts are documented adjacently. Module/header text owns
purpose and interfaces, while comments explain non-obvious rationale,
scientific limits, safety, and recovery rather than mechanics.

Consolidation begins with an audience map and source-to-destination ledger.
Unique meaning moves before its old copy disappears; intentional safety
repetition may remain at the action point. Local owner context links purpose,
contracts, direct neighbors, tests, and canonical cross-cutting owners so
routine work stays bounded, while contradictions and high-risk impact broaden
inspection. Correctness outranks compression.

The exact owner map and no-loss ledger live in
[`DOCUMENTATION_OWNERSHIP.md`](../sitemap/DOCUMENTATION_OWNERSHIP.md). Root
`AGENTS.md` remains a concise automatically loaded safety/router surface, exact
commands remain in `RUNBOOK.md`, diagnostics in `TROUBLESHOOTING.md`, and
neutral cross-language conventions in `ENGINEERING_CONVENTIONS.md`.
Operational prose links tested programs instead of embedding them; the
documentation gate remains one stable logic-free Make route to its tested
explicit-root engine.

Rationale: conventional local documentation makes the repository inspectable
without creating more canonical owners. A blind cleanup or blanket commenting
pass would either lose meaning or add noise.

Consequences: exact destinations and bounded follow-up owners are indexed in
the ownership map. A planned destination never becomes authoritative before
its owning card creates it and proves the old copy removable.

### Defer repository skills until the underlying practice is proven

Context: recurring documentation review is a strong skill candidate, but
creating several skills now would divert the refactor and encode unsettled rules.

Decision: do not create `docs/skills` or `DOC_CLEANUP.md`. After glossary,
README, code-documentation, consolidation, and review practices are proven,
create a proper documentation-health skill with `SKILL.md`. It is read-only by
default, combines deterministic checks with semantic responsibility-drift
review, requires approval before mutation, and is forward-tested. Evaluate any
other skill ideas in a later separate card.

Rationale: a skill should automate stable repeated judgment, not become another
unowned Markdown checklist. The documentation-health skill is high-value; a
broader skill program is not yet justified.

Consequences: see
[`DOC-SKILL-10`](../tasks/TODO/DOC-SKILL-10-build-documentation-health-skill.md)
and
[`SKILL-11`](../tasks/TODO/SKILL-11-evaluate-repository-skill-opportunities.md).

### Keep optional-analysis success and request archival future-only

Context: current computational success can require all current requested tasks,
validators, evidence assembly, and report. Multiple future analysis modules
will need explicit required/optional semantics.

Decision: preserve current success semantics during the active program. Later,
define how required and optional module failures affect run state, retry,
reporting, and request metadata archival. Raw inputs remain stationary and
computational success never promotes scientific or biological state.

Rationale: designing around a future branch point prevents a dead end, while
implementing optional states now would invent contracts without real modules.

Consequences: see
[`FUT-SUCCESS-04`](../tasks/TODO/FUT-SUCCESS-04-optional-analysis-and-archival-semantics.md).

### Decision-capture crosswalk

The headings above are the rationale index. Exact contracts route to
`STAGE_MAP.md`, `SOURCE_TOPOLOGY.md`, and `MIGRATION_MECHANICS.md`; live task
state to the registry, plan, and handoff; commands to `RUNBOOK.md`; and open or
resolved-choice navigation to [`QUESTIONS.md`](QUESTIONS.md).

## Deferred engineering

Decision: future engineering preserves behavior, scientific meaning, evidence ceilings, and transaction/recovery contracts. Current interfaces may
change only through approved, tested migrations; accidental placement is not a
permanent promise. Live backlog belongs in `PIPELINE_PLAN.md` and `TODO.md`.
