# EMRYS backlog matrix

Last reconciled: **2026-09-09**

This is EMRYS's main work backlog. It owns accepted current outcomes, status,
cursory Importance and Complexity, and acceptance. `COMPRESS-01` delegates its
finite `CS-*` slices to the [temporary compression backlog](compression_backlog_matrix.md),
which alone owns those cards' detailed scope, status, prerequisites, and proof.
Broader parent outcomes remain here; do not duplicate CS rows or their status.
Git history retains completed implementation chronology.

The architectural direction is permanent rather than backlog prose. See the
[architecture rationale](../design/decisions/platform-direction.md), [current
architecture](../architecture/ARCHITECTURE.md), and [scientific pipeline
decisions](../design/decisions/scientific-pipeline.md).

## Operating rules

- A row accepts work but does not authorize implementation, publication,
  cluster use, destructive cleanup, scientific review, evidence promotion, or
  evidence deletion. Those authorities remain explicit.
- This matrix is not a fixed execution sequence. Select work from its outcome,
  acceptance, risk, value, and current context. The temporary compression
  cards record actual prerequisites within that campaign, not a global
  dependency graph.
- **Open** means delivery remains. **In progress** means an approved bounded
  change is active. **Verification pending** means implementation appears
  complete but required evidence remains. **Deferred** means accepted work is
  intentionally retained for a later horizon. **Completed** records an accepted
  outcome at its stated evidence level.
- A task closes only when its whole outcome and acceptance pass at the claimed
  evidence level and affected interfaces, contracts, and documentation agree.
  Local fixtures, hosted CI, disposable Slurm, institutional-site execution,
  production data, scientific review, and biological validation remain
  different claims.

### Cursory scoring

Scores estimate the **remaining** task, not historical effort. They are loose
selection aids and may be revised when scope changes; they do not grant
authority or impose ordering.

| Score | Importance | Complexity |
|---:|---|---|
| `5` | Protects scientific validity or a result's trustworthiness | Cross-cutting scientific, site, or public migration with demanding independent proof |
| `4` | Required reliability, operator, or scientist outcome | Multi-owner change with compatibility, recovery, or integration work |
| `3` | Significant usability or maintenance value | Bounded component or moderate multi-module work |
| `2` | Useful optional improvement | Localized change with focused proof |
| `1` | Exploratory convenience | Trivial mechanical change |

## Active backlog

### Reliability and qualification

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `QUAL-01` | Test performance | Open | `3` | `3` | Make qualification-test selection fast enough for routine development. | Measure duration and subprocess/NFS cost, set a justified target, and meet it without dropping coverage or fault cases. |
| `QUAL-02` | Defect verification | Verification pending | `4` | `2` | Replace the brittle resume-fixture startup deadline with bounded readiness and useful failure diagnostics. | Bounded readiness and cleanup are implemented and exercised by hosted CI. Remaining evidence is the literal early-exit/timeout diagnostic requirement; ordinary success does not exercise those fault branches. |
| `QUAL-03` | Compatibility verification | Verification pending | `4` | `2` | Admit the accepted GNU Make 3.81 and 4.3 dry-run renderings without normalizing malformed output. | The two exact renderings and rejection of mixed/malformed renderings are implemented and covered by passing hosted tests. An explicitly version-identified GNU Make 4.3 execution remains to be recorded; this is an evidence gap, not an unimplemented normalization fix. |
| `HARNESS-01` | Test architecture | Verification pending | `3` | `3` | Keep simulated science entirely in test-owned seams. | The existing explicit test simulations still emit `local-science-tools` while injecting admission callbacks; reconcile that remaining naming/admission mismatch. Production dispatch, schemas, Run/Attempt, workflow, receipts, and recovery must have no test-only role or relaxed branch; historical compatibility is explicitly bounded; fixtures either satisfy the real runtime and storage admission contract or are named as injected simulations rather than `local-science-tools`; CI retains controlled partial-failure/resume proof without claiming scientific execution. |
| `RUN-01` | Runtime defect | Verification pending | `4` | `3` | Admit normal `renv` cache-package symlinks consistently. | Cache-package symlink handling is implemented; the retarget-after-hashing refusal test and managed restore, Doctor, and validation pass in hosted CI. Remaining evidence must identify a real restored cache-package symlink on that path, rather than infer the link representation from a successful restore. |
| `RUNTIME-CLOSURE-01` | Runtime integrity | Open | `4` | `3` | Bind the complete installed R dependency closure that can affect scientific execution. | Derive the recursive `Depends`, `Imports`, and `LinkingTo` closure from the admitted scientific namespaces; bind and re-admit that exact closure without hashing unrelated site-library packages or breaking normal `renv` cache symlinks. Every supported EMRYS R activation path forces automatic snapshots off so admission and execution cannot mutate dependency state. |

### Platform, operation, and portability

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SITE-PARITY-01` | Site qualification | Open | `4` | `5` | Qualify the current whole-Run path on CSU Viking or another named institutional site. | A novice operator without repository-development context follows only the maintained quickstart from a fresh Viking clone through Project creation, runtime admission, Doctor, validation, Slurm execution, inspection or resume when warranted, and completed Results and reports; every undocumented prerequisite or confusing step becomes a finding. Exact site modules/tools, Project storage semantics, locking/rename/durability, failure/recovery, resource and scheduler provenance, one-log ownership, and direct/Slurm scientific parity are evidenced at one exact revision. Hosted single-node proof is not promoted to institutional, multi-node, production, scientific-review, or biological proof. |
| `SCHED-01` | Scheduler preflight | Open | `3` | `2` | Reject an explicitly undersized Slurm memory request before submission. | When both placement memory and the applicable workflow or stage minimum are explicit, admission rejects insufficient capacity before `sbatch`; unknown capacity remains unknown, the existing CPU check remains authoritative, and no generalized resource solver or duplicate scheduler policy is introduced. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `OPS-03` | Maintenance | In progress | `3` | `4` | Audit inline, generated, legacy-direct, and shell programs and keep only substantive reusable owners. | Every program receives retain/extract/migrate/retire rationale; independently useful logic has one tested owner; normal operation requires no internal helper choreography; shell-to-Python conversion occurs only when total surface falls. Retained programs receive semantic names during caller-complete migration rather than a repository-wide cosmetic rename, and standalone owner routes remain only when independently useful. Canonical BAM now has one [create-exclusive publication path](../../src/emrys/stages/canonical_bam/CONTRACT.md#producer-publication-boundary), implemented in PR #146 and covered by the passing ordinary hosted CI for PR #140; master integration remains pending. Its historical recovery record and conservative cleanup limits remain documented. [CS-06–10](compression_backlog_matrix.md#working-queue) own the bounded publication characterization and retirement proposals. CS-07 gives RSeQC one create-exclusive publication path; its shared cleanup is fully migrated across RSeQC, BAM QC, and duplicate marking, with ordinary CI passed in [PR #150](https://github.com/lab-cats/EMRYS/actions/runs/34310143034); integration remains pending. [CS-18](compression_backlog_matrix.md#cs-18-idiomatic-scientific-producer-implementation) owns the approved replacement retirement for mpileup, preprocessing, paired CMH, and scientific-context output. Remaining replacement routes across BAM QC, duplicate marking, and split-N-cigar retire only after their current orchestrated owner and failure/recovery protections demonstrably supersede them; standalone public-policy changes need explicit approval. `INLINE-OWNERS-01` is absorbed here. |
| `FUT-INDEX-01` | Data reuse | Open | `4` | `4` | Admit an externally supplied prebuilt STAR index as an explicit Project input. | Existing reuse of a successful processing Run and standalone index validation are delivered capabilities, not external-index admission. The current [reference contract](../../src/emrys/contracts/schemas/orchestration/v1/reference.schema.json) declares FASTA/GTF and construction parameters but no prebuilt-index input. Remaining work binds every required index member to exact hashes, FASTA/GTF identity, and STAR parameters/version, then plans reuse without generation, repair, merge, or mutation; directory existence alone never authorizes admission. |
| `SETUP-02` | Benchmarking | Open | `3` | `3` | Make portable advisory benchmarking available through the normal control plane. | Users need not author raw command arrays; process-by-thread trials bind dataset, node, runtime, storage, resources, equivalence checks, and raw measurements; recommendations are never silently applied. Any failed repetition makes that candidate ineligible for recommendation while every raw trial remains visible and the benchmark exits nonzero. |
| `FUT-DATA-02` | Acquisition | Deferred | `2` | `5` | Provide retryable public-reference and SRA-read acquisition. | Reference and read acquisition remain separate and record accession/version, source, hashes, cache, retry, partial-transfer, and storage identity without scraping, silent updates, or implicit trust. |
| `PERF-01` | Performance research | Deferred | `2` | `4` | Test whether cross-node execution materially improves independent-work wall time. | A bounded representative experiment uses explicit per-job resources and never treats scheduler success as production or scientific proof. |
| `PROFILE-CONTRACT-01` | Contract reduction | Deferred | `3` | `4` | Remove derivable backend adapter fields during an independently justified workflow-profile contract transition. | Audit every current/historical reader and generated profile, then determine whether the consumed `owner_tasks[].rule_name` projection and redundant scope selectors can be derived from one semantic authority; retain exact historical-v2 reads plus graph, uniqueness, scope, artifact-admission, Execution-Plan identity, and direct/Slurm parity; remove duplicate validators/tests rather than adding an adapter or compatibility writer. Do not create a version bump solely for cleanup, and dismiss the row if the fields prove independently semantic or the migration is not meaningfully net-negative. |
| `DASHBOARD-RETIRE-01` | Major retirement | Deferred | `3` | `4` | Retire the stale dashboard only after a replacement dashboard is implemented and validated. | Replacement is required before retirement; expert command access alone does not satisfy this gate. Confirm no supported caller or unique retained evidence depends on it; remove dashboard product code, text parsers, dedicated tests, targets, and stale docs together. Complete the caller-wide retirement of `emrys-local-pilot` from newly generated Slurm job/stream names while preserving exact historical reads where required. Preserve Project-local `inspect` as status authority and retain scheduler accounting and sanitized raw-stream access through existing expert surfaces or the smallest justified replacement. Evidence deletion remains separately approval-gated. |

### Scientific review and independent validation

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SCI-AUDIT-01` | Scientific review | Open | `5` | `5` | Audit the complete Steps 07–09 statistical contract. | An identified independent reviewer traces the candidate universe, raw count construction, multiallelic/symbolic filtering, manifest order and replicate pairing, CMH strata/table/direction, the exact Benjamini-Hochberg family, eligibility, thresholds, effect sizes, ranking, and interpretation limits against representative fixtures and source. Review authority, data, reference calculations, and evidence ceiling are defined first; discrepancies become characterized findings rather than presumed defects, and no software check is promoted to scientific or biological validation. |
| `SCI-ORACLE-01` | Independent validation | Open | `5` | `4` | Establish independent numerical oracles for Steps 08 and 09. | A new Step 08 reference covers allele expansion, count/order reconciliation, filtering, annotation, and provisional orientation semantics without production helpers. Audit the existing Step 09 Python/real-R oracle and extend only uncovered paired-CMH, BH, status, threshold, or ranking semantics. Record exact fixtures, tolerances, disagreements, reviewer authority, and evidence ceiling. |

### Reporting and Results

Every reporting row inherits the [shared report acceptance](#shared-report-acceptance).

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `REPORT-01` | Visual verification | Verification pending | `5` | `3` | Produce readable locus-centered figures aligned with the supplied Figures 4b and 6b references. | Rendered output makes editing rate, location, local sequence, nearby motifs, significant candidates, and replicate behavior immediately readable and passes visual comparison. |
| `REPORT-02` | UX verification | Verification pending | `5` | `3` | Replace wide human tables with a narrow ranked summary, comparison views, and vertical detail. | Exact facts remain printable and visible; complete data is linked as machine-readable output rather than rendered as wide appendices. |
| `REPORT-03` | Audience verification | Verification pending | `4` | `2` | Confirm the primary-findings-first scientific, evidence, and operational hierarchy. | The scientific report answers what was found; the combined Evidence and operations report answers why it is trustworthy and how execution proceeded. Fixed relative navigation, Run overview, Evidence provenance, and Operations Attempt lineage pass rendered user review without adding a third artifact. |
| `REPORT-04` | Report capability | Open | `4` | `3` | Render an A-through-I candidate/panel roster when warranted. | At least nine admitted selections render without silent truncation, label collision, inaccessible detail, or print/layout failure; any higher display limit is explicit and evidence-bound. |
| `REPORT-ROSTER-01` | Architecture reduction | In progress | `3` | `4` | Remove duplicated reporting declarations while preserving module-specific reports. | CS-02–05 and CS-11 in the [compression backlog](compression_backlog_matrix.md#working-queue) own the remaining implementation and decisions. The [fixed-output](../design/decisions/execution-evidence-and-reporting.md#fixed-report-output-consolidation) and [publication](../design/decisions/execution-evidence-and-reporting.md#reporting-lifecycle-compression) changes preserve current identity and historical behavior; they do not close this outcome. Derive equivalent declarations from existing records, migrate every applicable caller, and avoid an inspection/reporting dependency cycle. Separate report-only implementation from the scientific Run identity so compatible scientific resume survives reporting changes. Preserve report ordering, independent regeneration, historical readers, source/roster rechecks, locks and receipt-last publication, independent goldens, module-derived indexing, the `emrys.analysis_reporters` extension point, and the fixed Evidence/operations renderer. Different roster, status, historical, or trust semantics require explicit decisions; add no generic report language or catalog service. |

### Repository maintenance

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `COMPRESS-01` | Compression and comprehension | In progress | `4` | `4` | Substantially reduce duplicated code and documentation; make retained implementations and explanations easy to follow. | The [campaign](compression_campaign.md) owns scope and retirement; its [temporary backlog](compression_backlog_matrix.md) owns CS-01–19. Documentation reduction, plain language, and idiomatic code are primary outcomes with separate accounting. Complete whole responsibilities and all equivalent callers; small cleanups do not lead primary tranches. Keep independent science/recovery checks, useful decisions, and evidence limits. A completed example never closes its family. Record remaining accepted work and obtain final user disposition before retiring the temporary documents. |

## Completed outcomes reconciled in this tranche

CI-01, DEV-01, and CLI-VERSION-01 passed the complete ordinary hosted suite in
[run 34306975901](https://github.com/lab-cats/EMRYS/actions/runs/34306975901)
at `b491aac5`, including Python coverage, guarded R, managed golden path,
static/wheel, shell, and userspace checks. PR #148 awaits master integration.

The other implemented outcomes below passed their applicable Python,
guarded-R, managed-golden, and independent-contract checks in
[ordinary hosted CI 34301289787](https://github.com/lab-cats/EMRYS/actions/runs/34301289787)
on PR #140's integrated tree. This closes their hosted software-verification
scope; PR #140 still awaits master integration. It does not establish
institutional-site execution, scientific review, or biological validation.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `CI-01` | CI usability and performance | Completed | `4` | `3` | Remove repeated workflow execution and shorten guarded-R fixture scheduling while preserving every distinct check. | Manual lane selection and balanced long-test estimates are delivered through PR #139; automatic stacked-PR checks and shared sharder self-tests are implemented and passed ordinary hosted CI in [PR #140](https://github.com/lab-cats/EMRYS/pull/140), awaiting master integration. The implemented fixture change combines the full-output assertions with the resume fixture's identical initial 35-task run, schedules the 16 independent negative R cases at most two at a time with explicit child-failure propagation, and removes the wrapper's duplicate package probe while retaining the production check. Preserve complete test selection, coverage enforcement, scientific comparisons, separate processes, and existing long lanes. Focused local checks pass; ordinary hosted CI passed on `b491aac5` in [PR #148](https://github.com/lab-cats/EMRYS/actions/runs/34306975901); master integration remains pending; no additional benchmark campaign or speculative duration target is required. |
| `DEV-01` | Developer feedback | Completed | `3` | `2` | Add ShellCheck, consistent Python formatting, and fast local pre-commit hooks through existing tool owners. | The existing lint gate now runs locked ShellCheck on every tracked shell file and Ruff formatting checks; actionlint also checks embedded workflow shell. Three pre-commit hooks check applicable staged files using the same locked tools, with no workflow, R, or full-suite execution. The formatting baseline is a separate mechanical commit with unchanged parsed Python code. Local static, shell-owner, workflow-lint, and hook checks pass; ordinary hosted CI passed on `b491aac5` in [PR #148](https://github.com/lab-cats/EMRYS/actions/runs/34306975901); master integration remains pending. These additions are the approved tooling exception, not product compression. |
| `CLI-VERSION-01` | Public CLI | Completed | `2` | `1` | Show installed EMRYS version information with `emrys --version [-v]`. | Implemented through the existing package version and public parser: the ordinary flag reports the version; `-v` adds loaded-package path and Python version/executable. The display works without a Project or scientific runtime, writes no logs, and retains checkout admission for ordinary commands. Focused CLI and source-policy checks pass; ordinary hosted CI passed on `b491aac5` in [PR #148](https://github.com/lab-cats/EMRYS/actions/runs/34306975901); master integration remains pending. No new product file or version registry was introduced. |
| `QUAL-04` | Contract verification | Completed | `3` | `2` | Derive expected owner counts from the authoritative owner set. | Lifecycle and owner-count checks prove the current roster without stale constants. |
| `QUAL-05` | Provenance verification | Completed | `4` | `2` | Accept any selected clean checkout while binding Run and resume to its exact source commit. | A fresh Run records the selected commit; resume rejects incompatible source changes without requiring a predetermined external SHA. |
| `RUN-02` | Runtime defect | Completed | `5` | `3` | Run Step 10 and reporting with default R packages disabled. | The guarded regression, namespace audit, and full Step 10/report path pass in the intended R environment. |
| `CLEAN-01` | Retirement verification | Completed | `3` | `3` | Finish retiring the former demo surface while retaining the neutral synthetic golden path. | Demo docs, Make ownership, public spellings, and fake fresh-clone harness stay absent; `emrys init synthetic` through Project-local `emrys inspect`, focused recovery/reporting tests, and independent HTML goldens pass exact-head CI. |

## Shared report acceptance

Reports project admitted data; they do not recalculate science. A successful
full Run reports by default, `--no-report` opts out, and `emrys report` can
regenerate independently without creating or mutating a Run or Attempt.

- **Editing rate:** show exact control and treatment percentages, percentage-
  point difference and direction, each replicate/stratum, the informative-read
  denominator, one stated rate definition, and explicit missing or zero-
  denominator rendering. Never silently aggregate or substitute zero.
- **Location:** show genomic coordinate, edited/reference/alternate base or
  target change, orientation/strand terminology without overstating biological
  strand, assembly/contig, gene/transcript/region when available, and the edited
  base anchored in centered local sequence.
- **Motifs:** show every qualifying match in the declared window with exact
  motif ID and sequence, highlighted bases, and signed/directional distance to
  the candidate. Absence says `none detected within the configured window`;
  methods define the motif models, window, strand handling, scanning, and
  coordinate convention.
- **Views:** provide a narrow ranked overview, comparison view, and one vertical
  detail record per candidate. The summary includes site ID, compact location,
  rates/difference, motif/distance, and confidence; detail includes replicate
  values, read support, annotations, QC limitations, and interpretation.
  Information cannot depend only on hover, color, or horizontal scrolling.
  HTML/PDF print or export remains usable and links complete TSV/CSV tables.
- **Scale:** the primary view supports at least A–I when nine selections are
  admitted; presentation limits never truncate the underlying result silently.
- **Audience:** scientific findings are primary. Evidence/provenance and
  operations remain directly reachable but do not crowd the scientific story.
  Limitations state that outputs are CMH-ranked candidates, not validated
  editing sites or biological conclusions.
