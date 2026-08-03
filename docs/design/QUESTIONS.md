# Questions

This file contains open questions and a concise index of resolved questions.
Durable answers and rationale belong in [`DECISIONS.md`](DECISIONS.md);
current blockers belong in
[`../operations/HANDOFF.md`](../operations/HANDOFF.md).

## Open operational and scientific questions

### Production sample manifest

- Where is the immutable six-row runtime manifest stored?
- Should a safe canonical copy be tracked or remain cluster-local?
- What is its SHA-256 and retention policy?
- Have explicit replicate values been added before Steps `07`–`09` promotion?

### CSU batch runtime

- Which compute-visible R/Rscript and required namespaces are supported?
- Which hash utilities and exact tool paths are available in batch jobs?
- Is Java 17 consistently available across eligible compute nodes?

### Storage and retention

- What are the home, project-storage, and scratch quotas?
- Which location should large temporary and intermediate files use?
- What retention policy is approved for native and derived artifacts?

### Reference provenance

- What exact Novogene annotation release produced the delivered GTF?
- Do FASTA, FAI, DICT, GTF, BED, and STAR index contigs reconcile?
- Is the mitochondrial contig consistently named and included in the approved
  primary correction universe?

### Runtime promotion

- Are Step `07` resources sufficient for pilot, chromosome, and full primary
  partitions?
- Does real bcftools reproduce the locally tested VCF and receipt contracts?
- What evidence is required before downstream runtime promotion proceeds?

### Scientific policy

- What orthogonal orientation evidence is required?
- What annotation, statistical, replicate, sensitivity, and candidate
  adjudication exits are mandatory?
- What separately approved policy, if any, may unlock
  `biological_interpretation_ready`?

## Open choices

The entries below are unresolved design choices, not implementation
authorization. Each choice has one owning task and must be decided by that
task's planning deadline rather than rediscovered by an implementation agent.

### CHOICE-INTAKE-01 — Exact V1 request fields, run package, and operational directories

- **Decision state:** deliberately deferred; this does not block recovery
  integration, but it prevents selecting `INTAKE-03A` or beginning its
  implementation planning.
- **Question:** What YAML fields, schema versions, request-state directories,
  claim/promotion filenames, and internal run/attempt package layout implement
  the approved YAML+TSV lifecycle? `INTAKE-02E` owns the top-level run-request
  YAML representation; report selector and normalized reporting semantics
  remain with `RPT-02`.
- **Why it matters:** identity, duplicate prevention, resume, and operator
  navigation depend on stable names and atomic state transitions.
- **Owning card:**
  [`INTAKE-02E`](../tasks/TODO/INTAKE-02E-define-yaml-tsv-run-lifecycle.md).
- **Decision deadline:** before recovered
  [`INTAKE-03A`](../tasks/TODO/INTAKE-03A-implement-yaml-tsv-run-lifecycle.md)
  is selected or its implementation planning begins.
- **Recommendation:** use explicit versioned fields and a configured state root
  with distinct request-state and immutable `runs/<run>/attempts/<attempt>`
  packages; keep normalized contracts, status, scheduler material, logs,
  receipts, failure/recovery evidence, and report requests inspectable there,
  while referencing rather than moving raw inputs.

### CHOICE-REPORT-01 — Public report profile names and selection interface

- **Decision state:** deliberately deferred; this does not block recovery
  integration or `RPT-01` characterization.
- **Question:** What names and CLI/YAML selectors expose the science and retained
  comprehensive report profiles? Distinguish the top-level run-request YAML
  representation owned by `INTAKE-02E` from selector and normalized reporting
  semantics owned by `RPT-02`.
- **Why it matters:** profile naming is a public contract and “verbose” would be
  ambiguous with logging verbosity.
- **Owning card:**
  [`RPT-02`](../tasks/TODO/RPT-02-define-science-report-contract.md).
- **Decision deadline:** before `RPT-03` planning begins.
- **Recommendation:** use semantic names such as `science` and `comprehensive`,
  an explicit report-profile selector, and a matching YAML field; switch the
  default only in `RPT-06`.

### CHOICE-REPORT-02 — Exact science report field roster

- **Decision state:** deliberately deferred; this does not block recovery
  integration or separately selectable current-report corrections.
- **Question:** Which fields, sections, ordering, descriptions, missing states,
  and display limits form the versioned science projection? Decide authorized
  metadata and state grammar, unavailable values, joins, source authority,
  units, and display mappings explicitly.
- **Why it matters:** “minimal” is not testable and could omit scientifically
  necessary context without a closed field catalog.
- **Owning card:**
  [`RPT-02`](../tasks/TODO/RPT-02-define-science-report-contract.md).
- **Decision deadline:** before projection implementation.
- **Recommendation:** begin with evidence state, CMH-ranked findings, QC/filter
  funnel, sensitivity/replicate evidence, decisions/limitations, and concise
  methods; require one authorized source and plain-language description per
  field.

### CHOICE-REPORT-03 — Profile output layout and transaction boundary

- **Decision state:** deliberately deferred; this does not block recovery
  integration or separately selectable current-report corrections.
- **Question:** How do science and comprehensive bundle paths, locks,
  profile-specific receipts, shared summary material, and a request for both
  profiles coexist transactionally? Decide profile/format selection,
  completion-marker and cache visibility, retry/supersession identity,
  implementation/tool/template/style identity, no-clobber publication,
  rollback, and one owner for every downstream interface.
- **Why it matters:** output coexistence is fixed, but ambiguous lock/receipt
  granularity could cause overwrite, partial publication, or unclear identity.
- **Owning card:**
  [`RPT-02`](../tasks/TODO/RPT-02-define-science-report-contract.md).
- **Decision deadline:** before `RPT-03` implementation planning.
- **Recommendation:** publish each profile as an explicitly named immutable
  bundle with its own owned lock and receipt published last, bind any shared
  summary by exact hash, and define an all-or-none parent transaction only when
  one request explicitly requires both profiles.

### CHOICE-GATE-REC-01 — Validation receipt contract and storage

- **Decision state:** deliberately deferred; this does not block recovery
  integration, corrected documentation-gate work, or non-receipt task views.
- **Question:** What catalog and receipt schema names and versions, storage and
  retention rules, environment/toolchain compatibility contract, and
  conservative validation-subject/manifest rules govern reusable validation
  evidence? Should the receipt extend an existing result or remain separate?
- **Why it matters:** reusable evidence must exclude credentials and private
  data, derive identity from content, contain complete successful evidence,
  invalidate deterministically, and never raise the existing evidence ceiling.
- **Owning card:**
  [`GATE-REC-01`](../tasks/TODO/GATE-REC-01-define-machine-readable-gates-and-validation-receipts.md).
- **Decision deadline:** before validation-receipt schema or persistence
  implementation.
- **Recommendation:** none until the owning card compares the complete storage,
  compatibility, invalidation, privacy, and integration tradeoffs.

### CHOICE-SKILL-01 — Documentation-health skill name and discovery location

- **Question:** What supported skill name, filesystem/install scope, and
  discovery mechanism should host the future documentation-health workflow?
- **Why it matters:** a pseudo-skill in `docs/` would not be callable, while
  hardcoding today's platform location may become stale.
- **Owning card:**
  [`DOC-SKILL-10`](../tasks/TODO/DOC-SKILL-10-build-documentation-health-skill.md).
- **Decision deadline:** before skill scaffolding.
- **Recommendation:** start with a descriptive name such as
  `norad-documentation-health`, use the then-current supported skill-creator and
  standard discovery/install location, and keep repository-specific reference
  material linked rather than inventing `docs/skills/`.

### CHOICE-SIZE-01 — Step 08 R decomposition or explicit exception

- **Question:** Can the oversized Step `08` R module be reduced through a
  demonstrably non-algorithmic seam, or must it receive a time-bounded exception?
- **Why it matters:** the mandatory size rule conflicts with the prohibition on
  unapproved scientific-algorithm refactoring.
- **Owning card:**
  [`SIZE-07E`](../tasks/TODO/SIZE-07E-resolve-step08-r-module-size.md).
- **Decision deadline:** before any Step `08` structural edit.
- **Recommendation:** extract only proven-neutral argument/I/O/publication seams
  with exact real-R parity; otherwise record an explicit exception until
  runtime/scientific evidence and authorization exist.

### CHOICE-ANALYSIS-01 — Analysis module trust and registration model

- **Question:** How should exploratory custom analyses differ from registered
  built-ins in validation, provenance, dependency, report, and evidence claims?
- **Why it matters:** easy custom R execution is useful only if it cannot
  silently acquire trusted scientific status.
- **Owning card:**
  [`FUT-ANALYSIS-01`](../tasks/TODO/FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md).
- **Decision deadline:** before an analysis registry or custom-module prototype.
- **Recommendation:** keep exploratory and registered trust levels explicit;
  require typed inputs/outputs and provenance for both, with stronger review and
  versioned policy for registered modules.

### CHOICE-DATA-01 — First public reference and read endpoints

- **Question:** Which exact NCBI reference and SRA acquisition interfaces,
  accession/version rules, cache, and resumable-transfer behavior are supported
  first?
- **Why it matters:** upstream interfaces and mutable records can affect
  reproducibility, storage, and provenance.
- **Owning card:**
  [`FUT-DATA-02`](../tasks/TODO/FUT-DATA-02-public-reference-and-sra-acquisition.md).
- **Decision deadline:** before a public-data prototype.
- **Recommendation:** implement one version-pinned NCBI reference registration
  path before a separate SRA-to-FASTQ read adapter; verify then-current primary
  documentation during planning.

### CHOICE-CONTROL-01 — Exact installable CLI surface and asset materialization

- **Question:** Which commands/APIs become public, how are non-Python assets
  packaged, how are immutable run-bound scheduler jobs materialized, and when
  do versioning/distribution commitments begin?
- **Why it matters:** these decisions create versioning and distribution
  commitments that should not follow accidentally from internal paths.
- **Owning card:**
  [`FUT-CLI-03`](../tasks/TODO/FUT-CLI-03-installable-norad-control-plane.md).
- **Decision deadline:** before an installable-package prototype.
- **Recommendation:** keep the control plane thin and filesystem-first; treat
  `validate`, `plan`, `run`, `status`, `resume`, `report`, and `stages` as a
  starting usability study, then package explicit assets and materialize hashed
  job copies per run. Do not publish a versioned distribution before the final
  local audit and interface review; apply semantic versioning only once public
  contracts are intentionally declared.

### CHOICE-SUCCESS-01 — Required/optional analysis success and request archival

- **Question:** How do required and optional module outcomes determine run
  completion, retry, report state, and request metadata archival?
- **Why it matters:** multiple analyses make one undifferentiated success bit
  misleading, while premature archival could hide required failure.
- **Owning card:**
  [`FUT-SUCCESS-04`](../tasks/TODO/FUT-SUCCESS-04-optional-analysis-and-archival-semantics.md).
- **Decision deadline:** before optional modules enter an executable run.
- **Recommendation:** distinguish required failure, required success with
  optional failure, and full success; archive/promote metadata only after
  required success, preserve optional failure visibly, and never move raw data
  automatically.

### CHOICE-PROGRAM-01 — First planning cohorts and delivery tranche

- **Question:** Which live cards share a genuine decision boundary, and which
  smallest low-risk vertical slice should become the first current tranche?
- **Why it matters:** excessive grouping recreates the waterfall program,
  while premature standalone work can settle cross-cutting contracts twice.
- **Owning card:**
  [`PROGRAM-01`](../tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md).
- **Decision deadline:** before `PROGRAM-01` initializes the first durable
  per-tranche artifact/current pointer or selects a post-program delivery card.
- **Recommendation:** group only expensive-to-reverse shared invariants; choose
  the smallest evidence-supported vertical slice and let integrated feedback
  shape later tranches.

### CHOICE-EPIC-01 — Initial logical epic taxonomy and membership

- **Question:** Which stable epic IDs describe the live task families, and may
  one card belong to more than one epic?
- **Why it matters:** too many epics duplicate card state and context, while a
  rigid single hierarchy makes cross-cutting work difficult to find.
- **Owning card:**
  [`PROGRAM-01`](../tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md).
- **Decision deadline:** before `TASK-EPIC-01` task-specific planning.
- **Recommendation:** derive a small stable taxonomy from durable ownership,
  use one primary membership when it is honest, and permit additional
  navigation links only when they do not imply status, order, or dependency.

## Resolved index

Durable decisions are recorded in [`DECISIONS.md`](DECISIONS.md), including:

- `CHOICE-LIFECYCLE-01`: persist `INTEGRATION_REVIEW` only for asynchronous
  candidate review that survives beyond the current unpublished integration
  package; same-package frozen handoff and integration remain in the active
  card lifecycle;
- TSV manifests and explicit manifest-defined sample pairing;
- local-first development with SLURM scaling;
- descendant branches and separate docpatch gates;
- dry-run-first scripts and wrappers;
- Novogene reference use and STAR overhang;
- canonical BAM/read-group and rollback-protected publication rules;
- reverse-stranded/first-strand-style cohort evidence;
- separation of mechanical orientation from biological interpretation;
- Java/Picard, TMPDIR, and module-output handling;
- Step `07` cohort/partition and receipt contracts;
- Step `08` declared-input transaction and provisional orientation policy;
- Step `09` paired CMH, global BH family, and six-output transaction;
- guarded local R and explicit dependency restoration;
- separation of computational proof, scientific review, and biological state;
- structured artifact/reporting decoupling;
- documentation ownership and task-bounded canonical reading;
- `CHOICE-CONTEXT-01`: version-aware task-start routing, exact-revision context
  reuse, selective phase-boundary inspection, explicit expansion triggers, and
  impact-directed documentation review; see
  [`TASK_START.md`](../operations/TASK_START.md) and the
  [context-routing decision](DECISIONS.md#route-task-context-by-revision-and-impact);
- one complete computational gate per executable state and failure-first local
  validation output;
- de-duplicated validation lanes with measured bounded parallel defaults,
  exact serial parity, and explicit failure/interruption cleanup;
- `CHOICE-LOG-01` and `CHOICE-LOG-02`: `normal|verbose|debug`, direct-command
  flags plus Make/SLURM environment controls, machine stdout and human stderr,
  one-writer operation-attempt JSONL, dry-run command visibility, receipt-safe
  logging, bounded failure tails, protected operator-owned retention, distinct
  scheduler capture, and explicit evidence-role authorization; see the
  [logging decision](DECISIONS.md#separate-concise-console-output-from-durable-detailed-logs)
  and [target contract](../architecture/FUTURE_ARCHITECTURE.md#logging-target);
- behavior-contract sufficiency rather than 100% line coverage before
  architectural mutation;
- `CHOICE-STAGE-01`: exact display titles, public slugs, frozen machine keys,
  historical aliases, typed external inputs, and direct DAG/barrier semantics;
  see [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md);
- `CHOICE-ARCH-01`: a vertical `src/norad` target with first-class stages,
  analyses, and evidence owners; predictable versioned YAML descriptors;
  owner-local or neutral JSON Schemas; mirrored tests; and explicit dependency
  direction; see
  [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md);
- direct, reversible, contract-preserving migrations with bounded wrapper
  criteria and parity/removal gates; see
  [`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md);
- evidence-based shared-library promotion and risk-based source-size thresholds;
- YAML run requests plus TSV sample manifests, atomic claim, immutable run/
  attempt identity, success-only metadata promotion, and stationary raw data;
- local FASTQ/reference priority before separate future reference and SRA
  adapters;
- future typed preprocessing profiles/analysis modules and thin installable
  control plane, without implementing them in the current refactor;
- future science-default/comprehensive report profiles and two-sink logging;
- glossary, directory README, adjacent opaque-file documentation,
  code-header/comment inventory, no-loss consolidation, and local context;
- `CHOICE-DOC-01`: audience routes, exact owner boundaries, move-before-delete
  ledger, action-point safety repetition, a planned architecture pipeline
  overview, neutral engineering-conventions owner, and dated history index; see
  the [documentation decision](DECISIONS.md#treat-documentation-and-maintainer-context-as-architecture)
  and [ownership map](../sitemap/DOCUMENTATION_OWNERSHIP.md); this remains
  resolved and is not reopened by the recovery source;
- `CHOICE-PROGRAM-02`: two independently machine-readable future fields, one
  for semantic planning category and one for validation impact; see the
  [proportional-planning decision](DECISIONS.md#use-proportional-planning-categories-and-bounded-approval-envelopes)
  and [`TASK_START.md`](../operations/TASK_START.md#proportional-planning-categories-and-validation-impact);
- `CHOICE-TASK-IDENTITY-01`: permanent ID-only canonical card paths with
  reviewed structured lifecycle metadata after an atomic parity-validated
  migration; see the
  [task-registry decision](DECISIONS.md#govern-future-work-through-a-file-backed-task-registry);
- `CHOICE-TASK-VIEW-01`: committed lifecycle, dependency, epic, and tranche
  Markdown views that are byte-for-byte check-regenerated with deterministic
  recovery and fail-closed stale-output detection; see the
  [task-registry decision](DECISIONS.md#govern-future-work-through-a-file-backed-task-registry);
- `CHOICE-TRANCHE-VIEW-01`: durable
  `docs/operations/tranches/<TRANCHE-ID>.md` artifacts plus one recoverable
  current pointer; see the
  [rolling-delivery decision](DECISIONS.md#use-an-architecture-runway-with-rolling-vertical-delivery);
- `CHOICE-DOC-GATE-01`: a stable, logic-free Make wrapper over the same
  explicit-root validator engine, owned for implementation by
  completed [`DOC-GATE-01`](../tasks/COMPLETED/DOC-GATE-01-extract-documentation-validator.md);
- a file-backed task registry with separate planning/approval for every card;
- a future proper documentation-health skill and later separate skill review,
  with no `docs/skills/` directory now.

Implementation status and remaining package order are intentionally not copied
here; see [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
