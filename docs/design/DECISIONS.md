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

Decision: each package descends linearly from the latest clean, docpatched
predecessor. Implementation and documentation are separate commits; a
documentation-only package uses one documentation commit.

Reason: evidence, interfaces, and current state remain reviewable at every
stage. The authoritative current lineage belongs in `PIPELINE_PLAN.md`.

### Permit isolated concurrent authoring with serialized integration

Context: the linear package gate protects evidence but currently serializes
unrelated card creation and documentation work behind long implementation or
execution. Multiple mutating agents in one worktree would contaminate status,
staging, validation, and completion claims.

Decision: preserve one authoritative linear lineage while permitting multiple
simultaneous documentation/card sidecars beside at most one active
implementation-candidate or immutable-execution lane. Every mutating lane uses
a separate branch and sibling worktree. The primary worktree is the
single-writer integration/control lane. Every candidate receives an exact base,
absolute path, unique branch, integration target, reserved IDs/paths, declared
write set, prohibited overlaps, and independent/coupled classification.

Independent documentation may land while implementation continues. A document
that changes or depends on an unsettled active contract, acceptance criterion,
architecture decision, test behavior, or evidence claim is coupled and cannot
silently land: preserve it as a draft or checkpoint and re-plan the active
task. Long execution remains attributed to its immutable commit. Only combined
canonical validation may close a package.

Rationale: parallel authoring reduces idle time and allows maintainers to keep
the task registry and unrelated documentation healthy without creating two
sources of truth. Worktree isolation plus one integrator retains the evidence
and recovery properties of the linear model.

Consequences: the current serial conduct remains in force until
[`CONCURRENCY-01`](../tasks/TODO/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
operationalizes lane roles, multi-sidecar coordination, exact commands, status
ownership, integration, and validation. After that card is complete and
pushed, pause for the required user strategy discussion before using the new
workflow or selecting `PROGRAM-01`.

### Run one complete computational gate per executable state

Decision: use focused tests during implementation, then run one de-duplicated
complete computational gate against the final executable state before its
implementation commit. A subsequent documentation-only patch runs the
documentation gate and reuses that recorded computational evidence when Git
inspection proves that executable configuration, dependencies, Make targets,
schemas, fixtures, report templates, and test-harness selection and execution
semantics are unchanged. For a standalone documentation-only package with no
executable or test-affecting consumer, computational validation is not
applicable; run only Git and documentation validation.

Reason: rerunning identical multi-runtime suites before both the implementation
and documentation commits adds substantial latency without testing a new
executable state. Any executable change after the recorded gate invalidates
reuse and reopens the full implementation/docpatch sequence.

### Prefer failure-first validation output

Decision: local pytest uses quiet progress, short tracebacks, and its default
captured-output behavior. Make command echo and routine successful shell, R,
and report output are suppressed or captured; complete output is shown for a
failure or an explicit verbose run.

Reason: successful progress narration consumes operator attention and agent
context without changing evidence. Failure logs must remain complete and
diagnosable.

Decision: the complete developer gate uses a bounded orchestrator rather than
unconstrained `make -j`. Python coverage, shell contracts, sequential guarded
R, and pinned report-runtime checks are independent lanes. A parallel default
is allowed only after exact repeated serial/parallel result, file, line,
branch, and coverage equality; the measured improvement thresholds and
smallest-stable-concurrency rule in `PIPELINE_PLAN.md`; controlled failure and
interruption cleanup; and a working serial fallback. Developer-only parallel
dependencies are pinned and synchronized explicitly, never installed by tests
or workflow entry points.

Reason: this removes duplicate work and reduces feedback latency while keeping
coverage, evidence boundaries, failure provenance, process cleanup, and a
deterministic low-concurrency fallback reviewable.

### Route task context by revision and impact

Decision: [`TASK_START.md`](../operations/TASK_START.md) is the concise routing
owner. A task begins with live Git state, the selected card, its bounded local
surfaces, and applicable canonical sections. Exact content already present in
active context may be reused only when its revision is identifiable, Git proves
it unchanged, and the retained detail is sufficient. Changed content requires
the diff and affected sections; full-file or corpus reading is reserved for
unknown revisions, contradictions, ownership or structural changes, dispersed
impact, and scientific, evidence, safety, recovery, publication, public-
contract, or other risk that cannot be bounded safely.

A phase boundary requires reassessing closing evidence, new acceptance and
lineage, changed canonical owners, and the diff since the prior boundary. It
does not by itself require a complete canonical-corpus read.

Reason: the former phase-boundary corpus exceeded 9,000 lines, much of it
unrelated and unchanged. Version-aware reuse plus explicit expansion triggers
preserves the correctness boundary without paying that cost repeatedly. An
unversioned summary or another agent's statement remains orientation rather
than live proof.

### Make documentation consistency impact-directed

Decision: use the final package diff, canonical ownership, inbound references,
and repository-wide targeted searches to discover documentation and diagram
impact. Inspect affected sections, owners, consumers, and changed diagrams;
broaden semantic reading only when the impact is cross-cutting, contradictory,
ownership-changing, or not safely bounded. Keep the automated repository-wide
documentation gate because its global structural checks emit compact evidence
without loading the corpus into agent context.

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

Decision: runtime preflight consumes one exact TSV profile with closed
tool-version, R-namespace, SHA-256, and absolute-path visibility check types.
Each row declares `local`, `cluster_batch`, or `any`; the operator explicitly
declares the context in which the probes run.

Reason: login-shell availability, local development state, module names, and
path assumptions do not prove batch visibility. Context mismatches remain
`blocked` or `not_checked` rather than being silently promoted.

Consequence: preflight installs and repairs nothing. Command success means the
checks were evaluated and, in execute mode, the report was published; every
required row still must be inspected. Even an all-pass batch report is
availability evidence, not workflow runtime validation or cluster proof.

### Reconcile references without repair

Decision: reference provenance uses an explicit TSV inventory and base
directory, hashes every named physical member, retains declared annotation
source/release, and compares contig identities across FASTA, FAI, DICT, GTF,
BED12, and STAR metadata.

Reason: filenames and colocated directories are not provenance, while an
inspection tool must not silently regenerate or normalize shared references.
Consequently, missing files, hash differences, malformed metadata, and contig
disagreement are reported in a summary-last transaction and require separate
operator resolution.

### Measure storage without acting on retention policy

Decision: storage evidence comes from an exact TSV inventory of absolute roots
and a separate exact retention-policy TSV. The inventory records declared and
resolved paths, tree size, entry counts, filesystem capacity, expected quota,
and policy approval state in a three-file summary-last transaction.

Reason: capacity evidence and retention authorization must be inspectable
before large runs, but an observational foundation tool must not become an
implicit cleanup engine. Consequently, pending or rejected approvals and
missing required storage are reported without deleting, moving, archiving,
compressing, or otherwise changing data.

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

The public renderer defaults to one atomic HTML/PDF/summary-TSV bundle with a
deterministic report receipt published last. Operators may explicitly select
`html`, `pdf`, or `all`; every mode still publishes the summary and receipt.
PDF uses pinned Quarto with bundled Typst and a pinned pure-Python reader for
structural, text-order, and every-page banner validation. Format-neutral
content keeps the HTML and PDF projections aligned while allowing
format-specific validation.

The HTML projection groups broad report categories with native,
script-free disclosure elements. Overview opens first so status, CMH-ranked
candidates, adjudication, and limitations remain near the top. The page uses
a bounded reading width, while wide approved tables scroll within their own
keyboard-focusable regions instead of widening the document. The PDF remains
linear and renders wide candidate tables as compact per-candidate records.
Full approved rows and provenance remain available in the HTML and authorized
source tables.

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
Ordinary checks reject a global line/branch regression or a removed baseline
module. New shared Python modules start with a 90% line and 85% branch
threshold.

Baseline regeneration is an explicit reviewed action. Tests and runtime entry
points never install the tool or rewrite the snapshot automatically.

Reason: a measured floor makes later refactors comparable, while percentage
coverage alone cannot establish assertion independence, public-contract
completeness, transaction safety, real-R behavior, cluster execution, or
scientific correctness. The public-contract matrix and independent scenario
tests remain separate gates.

## Documentation ownership

Decision: each information category has one canonical owner:

- `AGENTS.md`: stable conduct and gates;
- `README.md`: concise entry point;
- `TODO.md`: prioritized pending work;
- `HANDOFF.md`: current takeover snapshot;
- `PIPELINE_PLAN.md`: pipeline/package/evidence status, acceptance criteria,
  and lineage;
- `QUESTIONS.md`: open questions and resolved index;
- `RUNBOOK.md`: executable commands;
- `TASK_START.md`: version-aware context routing and expansion rules;
- `DECISIONS.md`: durable choices and rationale;
- `TROUBLESHOOTING.md`: symptom, cause, diagnosis, and fix;
- `ARCHITECTURE.md`: current topology and contracts;
- `FUTURE_ARCHITECTURE.md`: target-state constraints;
- `docs/tasks/`: bounded task scope, directory-owned workflow status,
  dependencies, acceptance evidence, and historical completion records;
- demo documents: presentation material or dated snapshots;
- standalone `.mmd` files: canonical diagrams.

Reason: mutable facts otherwise drift across independently maintained copies.
Documents link to canonical owners instead of repeating branch names, commit
IDs, test totals, commands, live status, or diagrams.

## Approved architecture direction (2026-07-31)

The decisions below were approved by the repository owner on 2026-07-31. They
constrain future planning inside the already-active repository-spanning
refactor, but do not authorize any TODO task or represent target behavior as
implemented. Each task still requires live inspection, a task-specific plan,
and approval.

### Protect behavior before architectural mutation

Context: the repository has substantial local coverage, but tests vary in
independence and no percentage can prove that every behavior intended for
preservation is protected.

Decision: before production structure changes, classify every applicable
behavior row as `preserved contract`, `characterized defect`,
`undefined — decision required`, or `environment-deferred`. The Phase `01Z`
exit is 100% protection of applicable `preserved contract` rows, not 100% line
coverage. Independent goldens are small, reviewed known-good bytes or semantic
oracles that do not derive the expected rule from the producer under test.
Integrated fixtures remain valuable and are not replaced.

If the sufficiency decision is negative, create bounded `TEST-01G-*` closure
cards and a later `TEST-01Z-R*` decision card. Later migrations add focused
pre-characterization and old/new parity where feasible. An approved path or
interface change is an explicit contract migration, never a silent regression.

Rationale: this preserves intentional behavior while allowing known defects
and accidental paths to be handled honestly. The alternative—treating every
current output as correct or treating high coverage as readiness—would freeze
defects and leave shared producer/test mistakes undetected.

Consequences: no architecture root is released by a negative `01Z` decision;
defect corrections remain separate tasks. See
[`TEST-01C`](../tasks/TODO/TEST-01C-characterize-validation-check-rosters.md)
through
[`TEST-01Z`](../tasks/TODO/TEST-01Z-decide-behavior-contract-sufficiency.md).

### Govern future work through a file-backed task registry

Context: a broad roadmap cannot carry enough settled constraints for dozens of
small future agents, while putting Jira-like detail in every canonical owner
would recreate responsibility leak.

Decision: use one stable Markdown card per task under `docs/tasks/TODO`,
`IN_PROGRESS`, or `COMPLETED`; directory location is the status. Cards own
scope, dependencies, deliverables, acceptance, and completion history. Durable
rationale, current state, commands, topology, and open choices remain in their
canonical documents.

Moving a card to `IN_PROGRESS` starts task-specific read-only planning. It does
not authorize implementation. Hard blockers are direct, reciprocal, and
acyclic. `Completion unblocks` distinguishes a sole remaining blocker from one
of several blockers. Paused work may return to TODO with a reason; there is no
`BLOCKED` directory. Completed cards are historical; follow-up work receives a
new card.

Correction approved on 2026-07-31: blocker fields are reserved for genuine
technological blockers whose missing output makes meaningful progress
impossible. Preferred order belongs in `PIPELINE_PLAN.md` or `TODO.md`;
approval, environment, and repository-state conditions belong under
`Prerequisites`; useful context alone is not an unblock relationship.
Completed cards remain historical rather than being rewritten to maintain a
live graph. The existing registry and validator still implement the original
broader model until the separately planned `TASK-REG-01` evidence-based
migration; this decision does not authorize a mechanical edge rewrite.

Rationale: a file-backed registry is inspectable, reviewable with code, and
locally usable without introducing an external project system. The alternative
of expanding the roadmap into task specifications would duplicate status and
rationale across owners.

Consequences: card moves use `git mv` and update inbound links in the same
commit. The lifecycle and template are canonical in
[`docs/tasks/README.md`](../tasks/README.md). The approved semantic migration is
owned by
[`TASK-REG-01`](../tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md).

### Use an architecture runway with rolling vertical delivery

Context: the current program is iterative inside each card but waterfall-shaped
across phases: all characterization, all design, one integrated plan, three
whole-plan reviews, and then implementation. That shape can create stale plans,
speculative cards, broad context requirements, and delayed empirical feedback.

Decision: settle expensive-to-reverse cross-cutting invariants in small
coordinated planning cohorts, then plan and execute bounded vertical cards just
in time. A normal card closes its inspect, plan, approve, execute, validate,
document, integrate, and feedback loop before dependent delivery advances. A
design card executes by producing a reviewed decision; it does not absorb all
downstream implementation.

`TEST-01Z` continues to gate structural architectural mutation, not independent
read-only inventory or characterization. `PLAN-02Z` will reconcile the minimum
shared architecture and create only the next evidence-supported delivery
tranche. Architecture, reliability, and usability reviews remain independent
but attach to the risk boundaries they govern rather than one monolithic plan.
Future-only cards preserve constraints without joining the current release
gate or receiving speculative detailed plans.

Rationale: high-fan-out topology, contract, state, recovery, and evidence
decisions are cheaper and safer to reconcile before files move. Local
implementation choices are more accurate after feedback from a completed
slice. The hybrid keeps necessary architecture without front-loading the whole
refactor.

Consequences: after the required post-concurrency strategy discussion,
[`PROGRAM-01`](../tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
will classify active cards, define cohorts, revise `PLAN-02Z` and review
boundaries, and select the first tranche. It will not execute implementation or
migrate the legacy blocker graph.

### Target a vertical package with direct contract-preserving migrations

Context: `scripts/` and `jobs/` now contain application domains, but packaging
and public distribution are premature. There are no external consumers that
justify indefinite preservation of accidental repository paths.

Decision: the target is a vertical Python source tree:

```text
src/norad/
├── stages/<semantic-stage>/
├── cli/
├── orchestration/
├── scheduler/
├── contracts/
├── libraries/
├── evidence/
├── reporting/
└── ingestion/
```

Each stage owns its implementation, validator, job template, README, and
stage-only contracts. Cross-stage/public contracts are central. Stages are
black boxes and never import another stage's implementation. Root `tests/`
mirrors stages and neutral domains while retaining independent contract and
integration suites. Do not create a generic `utils` owner.

Move each concern directly to its final home. A hybrid layout is temporary
migration scaffolding only: introduce a root wrapper where required, migrate
callers/tests/docs, prove old/new parity, and remove the wrapper. Preserve
behavior, scientific meaning, output/evidence/recovery contracts, dry-run, and
publication guarantees—not paths for their own sake.

Rationale: the final vertical home provides local ownership and supports a
later installable package without forcing versioning now. A permanent hybrid
would create dual ownership; a big-bang move would exceed the behavior and
review boundary.

Consequences: the exact inventory, semantic map, topology, and migration
mechanics belong to
[`ARCH-02A`](../tasks/TODO/ARCH-02A-inventory-functional-stages-and-contracts.md)
through
[`ARCH-02D`](../tasks/TODO/ARCH-02D-define-direct-migration-mechanics.md).
Current flat-layout documentation remains current truth until migrations land.

### Identify stages semantically and order them with a DAG

Context: numeric names such as `00c`, `02b`, and `09c` convey historical order
but not user meaning. Encoding order in a new filename would repeat the same
problem and make future branches awkward.

Decision: each future stage has a display title for people, a public semantic
slug, and a stable versioned machine key. Numeric IDs remain historical
provenance/aliases. Explicit DAG edges define order and branch points.

Retain a minimal user overview with a conceptual sequence table and Mermaid
diagram explaining purpose, ordering rationale, and input/output contracts.
The current detailed technical pipeline remains separate. Exact names and DAG
edges are deferred until the functional inventory is complete.

Rationale: semantic identities improve comprehension while stable keys and a
DAG decouple identity from mutable order. The alternative of deleting all
historical identifiers would weaken provenance.

Consequences: see
[`ARCH-02B`](../tasks/TODO/ARCH-02B-define-semantic-stage-map.md) and
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

Consequences: intentional independent validation stays duplicated. Candidate
decisions belong to
[`LIB-02F`](../tasks/TODO/LIB-02F-define-shared-library-ownership.md).

### Apply risk-based source-size thresholds

Context: very large mixed-responsibility files defeat bounded review and local
context, but raw line count is not a safe decomposition plan.

Decision: a materially changed file above 600 lines receives advisory cohesion
review, and new files normally remain below 600. A file above 1,000 lines needs
a decomposition plan or explicit justification before architectural mutation.
A file above 1,500 lines must be eliminated during the current repo-spanning
refactor unless the owner approves an explicit exception. Split tests by
scenario/comprehension, not arbitrary length.

The 2026-07-31 snapshot found 15 files above 600, 10 above 1,000, and 6 above
1,500. The six mandatory families were the artifact-index builder, scientific-
validation tooling, report renderer, run-summary builder, Step `08` R module,
and artifact-contract validator. Counts must be refreshed before execution.

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
[`RPT-06`](../tasks/TODO/RPT-06-make-science-report-the-default.md). The target
implementation owner is `src/norad/reporting`; current report behavior remains
unchanged until those cards complete.

### Separate concise console output from durable detailed logs

Context: current scripts often print more context than a normal user needs, but
that detail remains valuable for debugging, audit, and recovery.

Decision: target a relatively quiet default console, explicit verbose/debug
levels, and complete durable run-scoped logs. Machine-readable output goes to
stdout; human logs go to stderr. Log level may change presentation only: it
must never change artifacts, hashes, receipts, evidence, validation, rollback,
or exit behavior.

Rationale: deleting diagnostic detail would harm maintainability; printing all
detail by default harms usability and context efficiency. Two explicit sinks
serve both audiences and protect automation.

Consequences: exact level names/flags, durable layout/retention, and failure-tail
behavior remain open in
[`LOG-01`](../tasks/TODO/LOG-01-characterize-current-output.md) and
[`LOG-02`](../tasks/TODO/LOG-02-define-logging-contract.md). Foundation, local
adoption, and default activation remain separate. Current print behavior stays
documented until implemented.

### Treat documentation and maintainer context as architecture

Context: abbreviations, opaque directories/fixtures, overlapping documents,
and undocumented module invariants make the repository expensive to inspect.
Broad mandatory reads also consume context that local ownership could avoid.

Decision: create `docs/reference/GLOSSARY.md` as the canonical abbreviation and
term owner. Use `README.md` for eligible durable directories; parents stay
shallow and children own detail. Explain TSV/JSON/schema/generated/lock/byte-
sensitive artifacts adjacently rather than inserting comments into them.

Inventory every code file as `sufficient`, `update`, `defer`, or `exclude`.
Module/header documentation explains purpose, inputs/outputs, side effects,
invariants, failure/publication, and scientific limits as applicable. Inline
comments explain why, non-obvious invariants, recovery/safety, and scientific
boundaries—not mechanics. Protect CLI help before changing any module docstring
used as an `argparse` description.

Documentation consolidation begins with an audience/navigation and source-to-
destination ledger. Unique meaning must have a destination before relocation;
intentional safety repetition may remain at the action point. Local stage/domain
context should link purpose, contracts, direct neighbors, tests, and canonical
owners so bounded work does not load the whole repository. Phase and cross-
cutting work reassesses impact and broadens according to the global task-start
triggers; correctness outranks token reduction.

The repository-root `AGENTS.md` is a concise, automatically loaded project
router, not the owner of detailed NORAD commands, topology, mutable state,
scientific policy, or coding conventions. It retains only always-needed
approval, safety, evidence, and routing guardrails plus canonical links.
Reusable cross-repository preferences belong in global agent guidance. A
rule-by-rule source-to-destination ledger must prove that slimming the root file
does not lose critical protections.

Operational documentation owns supported invocations and behavior summaries,
not substantial embedded implementations. The current documentation validator
must be behavior-locked, extracted, and tested before its dependency semantics
change; `RUNBOOK.md` will retain only the supported invocation and concise
operator-facing explanation.

Rationale: conventional local documentation makes the repository inspectable
without creating more canonical owners. A blind cleanup or blanket commenting
pass would either lose meaning or add noise.

Consequences: see
[`DOC-IA-01`](../tasks/TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md)
through
[`CONTEXT-09`](../tasks/TODO/CONTEXT-09-define-local-maintainer-context.md), plus
[`DOC-GATE-01`](../tasks/TODO/DOC-GATE-01-extract-documentation-validator.md).
Concrete consolidation/comment rollout cards are created only after inventories.

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

| Discussion theme | Durable owner above | Task owner |
| --- | --- | --- |
| Behavior coverage before mutation and independent goldens | Protect behavior before architectural mutation | `TEST-01C`–`TEST-01Z` |
| Card lifecycle, true technological blockers, and separate approvals | File-backed task registry | `ARCH-DOC-00`, `TASK-REG-01`, and `docs/tasks/README.md` |
| Multiple isolated documentation/card sidecars and one canonical integrator | Concurrent authoring with serialized integration | `CONCURRENCY-01` |
| Architecture runway, planning cohorts, rolling tranches, and just-in-time card execution | Rolling vertical delivery | `PROGRAM-01`, `PLAN-02Z`, and `REVIEW-*` |
| Vertical `src/norad`, black-box stages, mirrored tests, direct migration | Vertical package | `ARCH-02A`–`ARCH-02D` |
| Semantic names, historical numbers, DAG, user overview | Semantic stages and DAG | `ARCH-02B`, `DOC-PIPE-04` |
| Local/shared abstraction threshold and ownership | Shared-library promotion | `LIB-02F` |
| 600/1,000/1,500 thresholds and mandatory large files | Source-size thresholds | `SIZE-07*`, `RPT-05B` |
| YAML+TSV intake, atomic claim, attempts, promotion, stationary raw data | Run request and manifest | `INTAKE-02E` |
| Reference formats versus SRA reads and acquisition priority | Public acquisition priority | `FUT-DATA-02` |
| Preprocessing profiles, analysis library, custom R, trust boundary | Analysis extension path | `FUT-ANALYSIS-01` |
| Installable `norad`, non-Python assets, materialized jobs | Later control plane | `FUT-CLI-03` |
| Science default, comprehensive profile, projection, no nested scroll | Future reporting | `RPT-01`–`RPT-06` |
| Quiet default, verbose/debug, durable logs, stdout/stderr | Two-sink logging | `LOG-01`–`LOG-05` plus generated `LOG-04-*` |
| Exact-revision context reuse, selective phase boundaries, impact-directed review | Task-start routing | `CONTEXT-00` |
| Glossary, READMEs, adjacent fixture docs, comments, concise root agent router, validator extraction, consolidation, context | Documentation as architecture | `DOC-GATE-01`, `DOC-IA-01`–`CONTEXT-09` plus generated cleanup/comment cards |
| Documentation-health skill and later skill review | Deferred skills | `DOC-SKILL-10`, `SKILL-11` |
| Required/optional analyses and archival | Future success semantics | `FUT-SUCCESS-04` |

The integrated sequence and three independent reviews are owned by
[`PLAN-02Z`](../tasks/TODO/PLAN-02Z-integrate-future-task-sequence.md) and
`REVIEW-*`; final closure is owned by
[`AUDIT-99`](../tasks/TODO/AUDIT-99-final-refactor-and-documentation-audit.md).

## Deferred engineering

Decision: generic orchestration, job arrays, publishing infrastructure,
targeted reruns, automatic cleanup, biological-readiness policy, public-data
acquisition, analysis-module execution, optional-analysis archival, and public
package distribution remain deferred until their named evidence and task gates
are complete.

Future refactors preserve proven behavior, scientific meaning, outputs,
evidence, dry-run/execute semantics, and transaction/recovery contracts.
Current CLIs and paths may change only through separately approved, explicitly
tested migrations; they are not preserved indefinitely merely because they are
current.
