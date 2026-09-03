# EMRYS backlog matrix

Last reconciled: **2026-09-02**

This is EMRYS's only work backlog. It owns accepted current work, status,
cursory Importance and Complexity, required outcomes, and acceptance. Git
history owns completed work and implementation chronology; neither remains a
parallel planning authority.

The architectural direction is permanent rather than backlog prose. See the
[architecture rationale](../design/decisions/platform-direction.md), [current
architecture](../architecture/ARCHITECTURE.md), and [scientific pipeline
decisions](../design/decisions/scientific-pipeline.md).

## Operating rules

- A row accepts work but does not authorize implementation, publication,
  cluster use, destructive cleanup, scientific review, evidence promotion, or
  evidence deletion. Those authorities remain explicit.
- There is no blocker or dependency graph. Select work from its outcome,
  acceptance, risk, value, and current context rather than treating this table
  as a fixed sequence.
- **Open** means delivery remains. **In progress** means an approved bounded
  change is active. **Verification pending** means implementation appears
  complete but required evidence remains. **Deferred** means accepted work is
  intentionally retained for a later horizon.
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
| `CI-01` | CI usability and performance | In progress | `4` | `3` | Make exact-head validation easy to select manually and shorten routine CI feedback. | Manual dispatch independently composes the ordinary static/documentation/wheel, shell, guarded-R, managed-runtime/golden-path, Python 3.14, Python 3.11, 130-pair, and 100,000-pair groups; long lanes remain opt-in; automatic merge evidence and test semantics do not weaken. Measure the remaining critical path and remove duplicated setup or work before setting a justified duration target. |
| `QUAL-01` | Test performance | Open | `3` | `3` | Make qualification-test selection fast enough for routine development. | Measure duration and subprocess/NFS cost, set a justified target, and meet it without dropping coverage or fault cases. |
| `QUAL-02` | Defect verification | Verification pending | `4` | `2` | Replace the brittle resume-fixture startup deadline with bounded readiness and useful failure diagnostics. | The retained qualification environment proves bounded readiness, early-exit output, and guaranteed cleanup. |
| `QUAL-03` | Compatibility verification | Verification pending | `4` | `2` | Admit the accepted GNU Make 3.81 and 4.3 dry-run renderings without normalizing malformed output. | GNU Make 4.3 passes and mixed or otherwise invalid renderings still fail. |
| `QUAL-04` | Contract verification | Verification pending | `3` | `2` | Derive expected owner counts from the authoritative owner set. | Lifecycle and owner-count checks prove the current roster without stale constants. |
| `QUAL-05` | Provenance verification | Verification pending | `4` | `2` | Accept any selected clean checkout while binding Run and resume to its exact source commit. | A fresh Run records the selected commit; resume rejects incompatible source changes without requiring a predetermined external SHA. |
| `HARNESS-01` | Test architecture | Verification pending | `3` | `3` | Keep simulated science entirely in test-owned seams. | Production dispatch, schemas, Run/Attempt, workflow, receipts, and recovery have no test-only role or relaxed branch; historical compatibility is explicitly bounded; fixtures either satisfy the real runtime and storage admission contract or are named as injected simulations rather than `local-science-tools`; CI retains controlled partial-failure/resume proof without claiming scientific execution. |
| `RUN-01` | Runtime defect | Verification pending | `4` | `3` | Admit normal `renv` cache-package symlinks consistently. | A real restored library passes restore, Doctor, and validation; dangling, retargeted, or identity-changing links fail closed. |
| `RUN-02` | Runtime defect | Verification pending | `5` | `3` | Run Step 10 and reporting with default R packages disabled. | The guarded regression, namespace audit, and full Step 10/report path pass in the intended R environment. |
| `CLEAN-01` | Retirement verification | Verification pending | `3` | `3` | Finish retiring the former demo surface while retaining the neutral synthetic golden path. | Demo docs, Make ownership, public spellings, and fake fresh-clone harness stay absent; `emrys init synthetic` through Project-local `emrys inspect`, focused recovery/reporting tests, and independent HTML goldens pass exact-head CI. |

### Platform, operation, and portability

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SITE-PARITY-01` | Site qualification | Open | `4` | `5` | Qualify the current whole-Run path on CSU Viking or another named institutional site. | Exact site modules/tools, Project storage semantics, locking/rename/durability, runtime discovery, Doctor, submission, failure/resume, resource and scheduler provenance, one-log ownership, Results, and direct/Slurm scientific parity are evidenced at one exact revision. Hosted single-node proof is not promoted to institutional, multi-node, production, scientific-review, or biological proof. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `OPS-03` | Maintenance | Open | `3` | `4` | Audit inline, generated, legacy-direct, and shell programs and keep only substantive reusable owners. | Every program receives retain/extract/migrate/retire rationale; independently useful logic has one tested owner; normal operation requires no internal helper choreography; shell-to-Python conversion occurs only when total surface falls. Retained programs receive semantic names during caller-complete migration rather than a repository-wide cosmetic rename, and standalone owner routes remain only when independently useful. Legacy replacement routes across canonical BAM, BAM QC, RSeQC, duplicate marking, split-N-cigar, and paired CMH retire only after their current orchestrated owner and failure/recovery protections demonstrably supersede them. `INLINE-OWNERS-01` is absorbed here. |
| `FUT-INDEX-01` | Data reuse | Open | `4` | `4` | Admit and reuse an explicitly declared prebuilt STAR index. | Required members bind to FASTA/GTF identity, STAR parameters/version, and exact hashes; directory existence never authorizes reuse, repair, merge, or mutation. |
| `SETUP-02` | Benchmarking | Open | `3` | `3` | Make portable advisory benchmarking available through the normal control plane. | Users need not author raw command arrays; process-by-thread trials bind dataset, node, runtime, storage, resources, equivalence checks, and raw measurements; recommendations are never silently applied. |
| `FUT-DATA-02` | Acquisition | Deferred | `2` | `5` | Provide retryable public-reference and SRA-read acquisition. | Reference and read acquisition remain separate and record accession/version, source, hashes, cache, retry, partial-transfer, and storage identity without scraping, silent updates, or implicit trust. |
| `PERF-01` | Performance research | Deferred | `2` | `4` | Test whether cross-node execution materially improves independent-work wall time. | A bounded representative experiment uses explicit per-job resources and never treats scheduler success as production or scientific proof. |
| `PROFILE-CONTRACT-01` | Contract reduction | Deferred | `3` | `4` | Remove derivable backend adapter fields from the next versioned execution-profile contract. | Audit every current/historical reader and generated profile, then derive `owner_tasks[].rule_name` and redundant scope selectors from one semantic authority; retain exact historical-v2 reads plus graph, uniqueness, scope, artifact-admission, Execution-Plan identity, and direct/Slurm parity; remove duplicate validators/tests rather than adding an adapter or compatibility writer. Do not create a version bump solely for cleanup, and dismiss the row if the fields prove independently semantic or the migration is not meaningfully net-negative. |
| `DASHBOARD-RETIRE-01` | Major retirement | Deferred | `3` | `4` | Retire the stale dashboard after the architecture stack is integrated. | Confirm no supported caller or unique retained evidence depends on it; remove dashboard product code, text parsers, dedicated tests, targets, and stale docs together. Complete the caller-wide retirement of `emrys-local-pilot` from newly generated Slurm job/stream names while preserving exact historical reads where required. Preserve Project-local `inspect` as status authority and retain scheduler accounting and sanitized raw-stream access through existing expert surfaces or the smallest justified replacement. Evidence deletion remains separately approval-gated. |

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
| `REPORT-ROSTER-01` | Architecture reduction | Open | `3` | `4` | Remove duplicated reporting declarations while preserving bespoke module reports. | One admitted module/profile authority derives expected kinds, counts, order, outputs, command inputs, validation roster, paths, and implementation identity without creating an inspection/reporting cycle. Report-only materialization must live outside the Run-bound implementation closure so a reporting-only change cannot alter Run identity or prevent a scientifically compatible resume. Delete `reporting_memory_mb` from active configuration if no execution consumes it, otherwise move it to its real execution owner. Retire fixed paired-CMH/output tables, pseudo-whitelists, and repeated shape/status validation. Preserve artifact-index -> run-summary -> HTML ordering, independent regeneration, transaction schemas, locks, receipt-last publication, source/roster rechecks, historical reads, independent goldens, module-derived indexing, the minimal `emrys.analysis_reporters` extension point, and EMRYS's fixed Evidence/operations renderer; add no generic report DSL or catalog service. |

### Repository maintenance

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `CONTRACT-API-01` | Contract reduction | Open | `3` | `2` | Make versioned orchestration-record admission use one coherent public authority. | Public validator selection and high-level record validation accept and reject the same supported Attempt-receipt versions; historical v1 and current v2 remain explicit; remove the private v2 special case and duplicated registry logic rather than adding another caller-specific adapter. |
| `COMPRESS-01` | Campaign intake | In progress | `4` | `3` | Complete the repository review and turn recurring comprehension and maintenance problems into finite post-architecture work. | Review all 393 files; classify every finding as addressed, current defect, accepted follow-on, or dismissed with rationale; group examples by root cause rather than treating them as isolated fixes; transfer accepted implementation work into scored matrix rows; then delete the temporary [compression campaign intake](compression_campaign.md). No broad product refactor begins before architecture closure. |

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
