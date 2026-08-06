# Questions

This file contains open questions and a concise index of resolved questions.
Durable answers and rationale belong in [`DECISIONS.md`](DECISIONS.md);
current blockers belong in
[`../operations/HANDOFF.md`](../operations/HANDOFF.md).

## Open operational and scientific questions

| Domain | Unresolved evidence or decision |
| --- | --- |
| Production sample manifest | Location of the immutable six-row runtime manifest; tracked-safe versus cluster-local ownership; SHA-256 and retention; explicit replicate values before Steps `07`–`09` promotion. |
| CSU batch runtime | Compute-visible R/Rscript and namespaces; hash utilities and exact tool paths; Java 17 availability across eligible nodes. |
| Storage and retention | Home, project, and scratch quotas; large temporary/intermediate placement; approved native/derived retention policy. |
| Reference provenance | Exact Novogene annotation release; FASTA/FAI/DICT/GTF/BED/STAR contig agreement; mitochondrial-contig naming and approved primary correction universe. |
| Runtime promotion | Step `07` resources by partition scale; real-bcftools VCF/receipt parity; required evidence before downstream promotion. |
| Scientific policy | Orthogonal orientation evidence; mandatory annotation/statistical/replicate/sensitivity/adjudication exits; any separately approved policy capable of unlocking `biological_interpretation_ready`. |

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

### CHOICE-EPIC-01 — Initial logical epic taxonomy and membership

- **Question:** Which stable epic IDs describe the live task families, and may
  one card belong to more than one epic?
- **Why it matters:** too many epics duplicate card state and context, while a
  rigid single hierarchy makes cross-cutting work difficult to find.
- **Owning card:**
  [`TASK-EPIC-01`](../tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md).
- **Decision deadline:** before `TASK-EPIC-01` task-specific planning.
- **Recommendation:** derive a small stable taxonomy from durable ownership,
  use one primary membership when it is honest, and permit additional
  navigation links only when they do not imply status, order, or dependency.

## Resolved index

Durable rationale lives in [`DECISIONS.md`](DECISIONS.md). This table is only a
discoverability index; exact contracts and implementation evidence stay with
the linked owner.

| Resolved ID or topic | Durable decision | Exact owner |
| --- | --- | --- |
| `CHOICE-LIFECYCLE-01`; `CHOICE-TASK-IDENTITY-01`; `CHOICE-TASK-VIEW-01` | [File-backed task registry](DECISIONS.md#govern-future-work-through-a-file-backed-task-registry) | [`docs/tasks/README.md`](../tasks/README.md) and `TASK-REG-01` |
| `CHOICE-CONTEXT-01` | [Revision- and impact-routed context](DECISIONS.md#route-task-context-by-revision-and-impact) | [`TASK_START.md`](../operations/TASK_START.md) |
| `CHOICE-PROGRAM-02` | [Bounded approval and proportional validation](DECISIONS.md#use-bounded-approval-envelopes-and-proportional-validation) | [`TASK_START.md`](../operations/TASK_START.md) |
| `CHOICE-STAGE-01` | [Semantic identities and DAG order](DECISIONS.md#identify-stages-semantically-and-order-them-with-a-dag) | [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) |
| `CHOICE-ARCH-01` | [Vertical ownership and direct migration](DECISIONS.md#target-a-vertical-package-with-direct-contract-preserving-migrations) | [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md) |
| `CHOICE-SIZE-01` | Non-algorithmic Step `08` input/admission extraction; no size exception | [`TEST_BASELINE.md`](TEST_BASELINE.md) |
| `CHOICE-LOG-01`; `CHOICE-LOG-02` | [Concise console plus durable logs](DECISIONS.md#separate-concise-console-output-from-durable-detailed-logs) | [Logging target](../architecture/FUTURE_ARCHITECTURE.md#logging-target) |
| `CHOICE-DOC-01`; `CHOICE-DOC-GATE-01` | [Documentation as architecture](DECISIONS.md#treat-documentation-and-maintainer-context-as-architecture) | [Ownership map](../sitemap/DOCUMENTATION_OWNERSHIP.md) |
| Scientific workflow and evidence | [Reference/BAM](DECISIONS.md#reference-and-bam-pipeline), [orientation/analysis](DECISIONS.md#orientation-and-downstream-analysis), and [evidence state](DECISIONS.md#evidence-and-scientific-state) | `STAGE_MAP.md` and local contracts |
| Structured artifacts and current reporting | [Artifact/reporting decisions](DECISIONS.md#structured-artifacts-and-reporting) | Neutral schemas and current reporting owner |
| YAML+TSV intake direction | [Run request and manifest](DECISIONS.md#use-yaml-run-requests-with-tsv-sample-manifests) | `INTAKE-02E`; exact fields/paths remain open in `CHOICE-INTAKE-01` |
| Future reporting, analysis extensions, control plane, and optional-analysis success | [Future reporting](DECISIONS.md#make-science-reporting-the-future-default-and-retain-comprehensive-reporting), [analysis extensions](DECISIONS.md#preserve-an-extension-path-for-preprocessing-profiles-and-analysis-modules), [control plane](DECISIONS.md#keep-an-installable-control-plane-as-a-later-capability), and [success boundary](DECISIONS.md#keep-optional-analysis-success-and-request-archival-future-only) | Exact report interfaces remain open in `CHOICE-REPORT-01`–`03`; analysis trust/registration in `CHOICE-ANALYSIS-01`; CLI/packaging in `CHOICE-CONTROL-01`; success/archive semantics in `CHOICE-SUCCESS-01` |

Implementation status and remaining package order are intentionally not copied
here; see [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
