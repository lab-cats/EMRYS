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

### CHOICE-STAGE-01 — Exact semantic stage identities and DAG

- **Question:** What exact display title, public slug, stable versioned key,
  historical aliases, and DAG edges apply to every functional stage?
- **Why it matters:** target paths, contracts, user documentation, and migration
  cards require identities that do not encode mutable lexical order.
- **Owning card:**
  [`ARCH-02B`](../tasks/TODO/ARCH-02B-define-semantic-stage-map.md).
- **Decision deadline:** before `ARCH-02C` planning begins.
- **Recommendation:** derive names only from the completed functional inventory;
  retain numeric IDs as historical aliases and make the explicit DAG the sole
  ordering authority.

### CHOICE-ARCH-01 — Machine stage descriptor and contract serialization

- **Question:** What exact stage-descriptor filename/format, local contract
  layout, and schema/reference mechanism represent each stage's machine-readable
  interface?
- **Why it matters:** the conceptual vertical tree fixes ownership but not the
  serialized descriptor that orchestration, documentation, and validation will
  consume.
- **Owning card:**
  [`ARCH-02C`](../tasks/TODO/ARCH-02C-define-vertical-source-contract-and-test-topology.md).
- **Decision deadline:** before `ARCH-02D` or any source migration planning.
- **Recommendation:** pair the human `README.md` with one predictable,
  versioned stage-local descriptor (prefer YAML for inspectable metadata) that
  references stage-local or central JSON Schemas according to the approved
  public/cross-stage ownership rule.

### CHOICE-INTAKE-01 — Exact V1 request fields, run package, and operational directories

- **Question:** What YAML fields, schema versions, request-state directories,
  claim/promotion filenames, and internal run/attempt package layout implement
  the approved YAML+TSV lifecycle?
- **Why it matters:** identity, duplicate prevention, resume, and operator
  navigation depend on stable names and atomic state transitions.
- **Owning card:**
  [`INTAKE-02E`](../tasks/TODO/INTAKE-02E-define-yaml-tsv-run-lifecycle.md).
- **Decision deadline:** before any ingestion implementation card is created.
- **Recommendation:** use explicit versioned fields and a configured state root
  with distinct request-state and immutable `runs/<run>/attempts/<attempt>`
  packages; keep normalized contracts, status, scheduler material, logs,
  receipts, failure/recovery evidence, and report requests inspectable there,
  while referencing rather than moving raw inputs.

### CHOICE-REPORT-01 — Public report profile names and selection interface

- **Question:** What names and CLI/YAML selectors expose the science and retained
  comprehensive report profiles?
- **Why it matters:** profile naming is a public contract and “verbose” would be
  ambiguous with logging verbosity.
- **Owning card:**
  [`RPT-02`](../tasks/TODO/RPT-02-define-science-report-contract.md).
- **Decision deadline:** before `RPT-03` planning begins.
- **Recommendation:** use semantic names such as `science` and `comprehensive`,
  an explicit report-profile selector, and a matching YAML field; switch the
  default only in `RPT-06`.

### CHOICE-REPORT-02 — Exact science report field roster

- **Question:** Which fields, sections, ordering, descriptions, missing states,
  and display limits form the versioned science projection?
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

- **Question:** How do science and comprehensive bundle paths, locks,
  profile-specific receipts, shared summary material, and a request for both
  profiles coexist transactionally?
- **Why it matters:** output coexistence is fixed, but ambiguous lock/receipt
  granularity could cause overwrite, partial publication, or unclear identity.
- **Owning card:**
  [`RPT-02`](../tasks/TODO/RPT-02-define-science-report-contract.md).
- **Decision deadline:** before `RPT-03` implementation planning.
- **Recommendation:** publish each profile as an explicitly named immutable
  bundle with its own owned lock and receipt published last, bind any shared
  summary by exact hash, and define an all-or-none parent transaction only when
  one request explicitly requires both profiles.

### CHOICE-LOG-01 — Exact public log levels and flags

- **Question:** What level enum, CLI/environment controls, precedence, and
  invalid-value behavior should every entry point expose?
- **Why it matters:** inconsistent level names would recreate per-script output
  behavior and complicate automation.
- **Owning card:**
  [`LOG-02`](../tasks/TODO/LOG-02-define-logging-contract.md).
- **Decision deadline:** before `LOG-03` planning begins.
- **Recommendation:** prefer a small semantic enum such as `normal`, `verbose`,
  and `debug`, define `normal` as the concise default, and add a separate
  `quiet` level only if characterization identifies a real user/automation need.

### CHOICE-LOG-02 — Durable log layout, retention, and failure tail

- **Question:** Where do run/attempt logs live, what files/metadata are required,
  who owns retention, and what bounded failure summary reaches the console?
- **Why it matters:** complete diagnostics and recovery must survive quiet
  output without authorizing unbounded storage or automatic deletion.
- **Owning card:**
  [`LOG-02`](../tasks/TODO/LOG-02-define-logging-contract.md).
- **Decision deadline:** before foundation implementation.
- **Recommendation:** use run/attempt-scoped paths under configured state,
  always retain complete durable logs, print a concise actionable failure tail
  to stderr, and leave deletion to explicit operator retention policy.

### CHOICE-DOC-01 — Documentation consolidation, overview, and history locations

- **Question:** Which current sections move, remain, link, or become dated
  history, and where should the user pipeline overview and preserved historical
  snapshots live?
- **Why it matters:** `RUNBOOK.md` and `TROUBLESHOOTING.md` are large, while
  unique commands, recovery cautions, and evidence snapshots must not be lost.
- **Owning card:**
  [`DOC-IA-01`](../tasks/TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md).
- **Decision deadline:** before any `DOC-CONS-08-*` card is created.
- **Recommendation:** add audience/navigation and a source-to-destination ledger
  before splitting; retain exact commands in `RUNBOOK.md`, symptom/cause/
  diagnosis/fix in `TROUBLESHOOTING.md`, and intentional safety repetition at
  the action point. Prefer a stable architecture/user-guide location for the
  conceptual overview and a clearly dated `docs/history/`-style owner for
  noncanonical snapshots, subject to the inventory.

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

## Resolved index

Durable decisions are recorded in [`DECISIONS.md`](DECISIONS.md), including:

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
  exact serial parity, and explicit failure/interruption cleanup.
- behavior-contract sufficiency rather than 100% line coverage before
  architectural mutation;
- a vertical `src/norad` target with semantic black-box stages, mirrored tests,
  and direct contract-preserving migrations;
- semantic stage title/slug/versioned-key identities with DAG-defined order and
  historical numeric aliases;
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
- a file-backed task registry with separate planning/approval for every card;
- a future proper documentation-health skill and later separate skill review,
  with no `docs/skills/` directory now.

Implementation status and remaining package order are intentionally not copied
here; see [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
