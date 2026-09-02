# EMRYS findings matrix and backlog

Last reconciled: **2026-09-02**

This is EMRYS's only work backlog. It owns accepted IDs, status, cursory
Importance and Complexity, required outcomes, acceptance, and terminal
dispositions. Git history retains the former campaign ledger, ranking matrix,
card registry, and detailed implementation chronology; none remains a parallel
planning authority.

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
- **Complete**, **Retired**, **Absorbed**, and **Discarded** are terminal.
  Completed implementation detail belongs in code, contracts, checks, compact
  history records, and Git—not in a second live card system.
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

## Design boundary inherited by every task

> **The scientific core is considerably simpler than the software surrounding
> it. EMRYS's biggest opportunity is therefore to compress the operational
> surface while preserving the evidence and provenance guarantees underneath.**

The ordinary model is:

```text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), when operationally relevant
```

A Run is the immutable binding of one admitted Analysis revision to one
immutable internal Execution Plan. Results is read-only. Reporting runs by
default after a full scientific Attempt, can be disabled, and can be regenerated
without becoming a scientific stage or changing Run/Attempt identity. Ordinary
operation is Project-local:

```text
emrys init PROJECT_NAME
cd PROJECT_NAME
emrys validate
emrys doctor
emrys run [--analysis NAME] [--profile NAME|ABSOLUTE_PATH]
emrys inspect [RUN]
emrys resume [RUN]
emrys report [RUN]
```

Scientists author scientific intent; operators may author execution policy;
EMRYS owns evidence configuration. Low-level manifests, exact identities,
Snakemake, tasks, transactions, receipts, and scheduler detail remain
inspectable through progressive disclosure, not mandatory user concepts.

Every implementation must also follow the permanent
[compression, immutability, abstraction, protection, and evidence-deletion
guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).

## Active backlog

### Reliability and qualification

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `QUAL-01` | Test performance | Open | `3` | `3` | Make qualification-test selection fast enough for routine development. | Measure duration and subprocess/NFS cost, set a justified target, and meet it without dropping coverage or fault cases. |
| `QUAL-02` | Defect verification | Verification pending | `4` | `2` | Replace the brittle resume-fixture startup deadline with bounded readiness and useful failure diagnostics. | The retained qualification environment proves bounded readiness, early-exit output, and guaranteed cleanup. |
| `QUAL-03` | Compatibility verification | Verification pending | `4` | `2` | Admit the accepted GNU Make 3.81 and 4.3 dry-run renderings without normalizing malformed output. | GNU Make 4.3 passes and mixed or otherwise invalid renderings still fail. |
| `QUAL-04` | Contract verification | Verification pending | `3` | `2` | Derive expected owner counts from the authoritative owner set. | Lifecycle and owner-count checks prove the current roster without stale constants. |
| `QUAL-05` | Provenance verification | Verification pending | `4` | `2` | Accept any selected clean checkout while binding Run and resume to its exact source commit. | A fresh Run records the selected commit; resume rejects incompatible source changes without requiring a predetermined external SHA. |
| `HARNESS-01` | Test architecture | Verification pending | `3` | `3` | Keep simulated science entirely in test-owned seams. | Production dispatch, schemas, Run/Attempt, workflow, receipts, and recovery have no test-only role or relaxed branch; historical compatibility is explicitly bounded; CI retains controlled partial-failure/resume proof without claiming scientific execution. |
| `RUN-01` | Runtime defect | Verification pending | `4` | `3` | Admit normal `renv` cache-package symlinks consistently. | A real restored library passes restore, Doctor, and validation; dangling, retargeted, or identity-changing links fail closed. |
| `RUN-02` | Runtime defect | Verification pending | `5` | `3` | Run Step 10 and reporting with default R packages disabled. | The guarded regression, namespace audit, and full Step 10/report path pass in the intended R environment. |
| `CLEAN-01` | Retirement verification | Verification pending | `3` | `3` | Finish retiring the former demo surface while retaining the neutral synthetic golden path. | Demo docs, Make ownership, public spellings, and fake fresh-clone harness stay absent; `emrys init synthetic` through Project-local `emrys inspect`, focused recovery/reporting tests, and independent HTML goldens pass exact-head CI. |

### Platform, operation, and portability

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SITE-PARITY-01` | Site qualification | Open | `4` | `5` | Qualify the current whole-Run path on CSU Viking or another named institutional site. | Exact site modules/tools, Project storage semantics, locking/rename/durability, runtime discovery, Doctor, submission, failure/resume, resource and scheduler provenance, one-log ownership, Results, and direct/Slurm scientific parity are evidenced at one exact revision. Hosted single-node proof is not promoted to institutional, multi-node, production, scientific-review, or biological proof. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `OPS-03` | Maintenance | Open | `3` | `4` | Audit inline, generated, legacy-direct, and shell programs and keep only substantive reusable owners. | Every program receives retain/extract/migrate/retire rationale; independently useful logic has one tested owner; normal operation requires no internal helper choreography; shell-to-Python conversion occurs only when total surface falls. Legacy replacement routes across canonical BAM, BAM QC, RSeQC, duplicate marking, split-N-cigar, and paired CMH retire only after their current orchestrated owner and failure/recovery protections demonstrably supersede them. `INLINE-OWNERS-01` is absorbed here. |
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
| `REPORT-ROSTER-01` | Architecture reduction | Open | `3` | `4` | Remove duplicated reporting declarations while preserving bespoke module reports. | One admitted module/profile authority derives expected kinds, counts, order, outputs, command inputs, validation roster, paths, and implementation identity without creating an inspection/reporting cycle. Delete `reporting_memory_mb` from active configuration if no execution consumes it, otherwise move it to its real execution owner. Retire fixed paired-CMH/output tables, pseudo-whitelists, and repeated shape/status validation. Preserve artifact-index -> run-summary -> HTML ordering, independent regeneration, transaction schemas, locks, receipt-last publication, source/roster rechecks, historical reads, independent goldens, module-derived indexing, the minimal `emrys.analysis_reporters` extension point, and EMRYS's fixed Evidence/operations renderer; add no generic report DSL or catalog service. |

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

Owner contracts may record a current limitation or evidence ceiling without
thereby creating approved work. The documentation audit retained such exact
facts—including producer/validator disagreements and native transaction limits—
beside their owners, removed stale future-design prose, and routed only already
accepted work here. A future change to an unscored owner limitation first needs
an explicit matrix disposition; it must not be inferred from the contract.

## Documentation audit closeout

The repository-wide audit completed these rows after verifying the replacement
authorities, retained evidence, owner routing, and local document structure.

| ID | Kind | Status | Importance | Complexity | Delivered outcome |
|---|---|---|---:|---:|---|
| `DOC-01` | Documentation | Complete | `4` | `4` | Every tracked Markdown file was audited; role journeys, owner routing, exact contracts, and durable rationale remain while duplicate indexes, routine test READMEs, temporary campaign prose, and stale context retire. Exact non-derivable contracts remain prose; machine-derived duplication was removed, and any future executable-spec replacement requires a concrete smaller owner rather than another standing campaign. |
| `DOC-04` | Evidence migration | Complete | `4` | `3` | Unique PORT-NC, VM Slurm, renderer, Viking, cohort/orientation, and local-R observations live in `docs/history/validation-evidence.md` with exact revisions, hashes, job IDs, and evidence ceilings; blocker/takeover prose and the rolling handoff retire. |
| `DOC-05` | Documentation retirement | Complete | `4` | `3` | Useful orchestration safeguards now live in current contracts, decisions, runbook, checks, and configuration; the duplicate global orchestration contract and stale readiness source retire. |
| `TOOLING-01` | Tooling retirement | Complete | `3` | `2` | The former generic Git-orchestration namespace has no caller or public route; useful documentation validation remains as `scripts/documentation/validate_structure.py`; obsolete status, fragment, and delivery helpers remain absent without a check-only return guard. |

## Architecture campaign completion record

The architecture campaign is implementation-complete. Its durable result is:

- the public `Project -> Analysis -> Run -> Results` model and immutable Run;
- one Project definition with named Analyses and external scientific manifests;
- Project-local named execution profiles and one Project-owned runtime inventory;
- managed repair through existing package managers, with Site and Explicit
  acquisition converging on the same admission authority;
- one Snakemake backend shared by direct and whole-Run Slurm placement;
- processing-only Runs, stationary compatible Steps 00–06 reuse, and versioned
  collaborator computation/reporter providers without a universal Stage model;
- read-only inspection, safe retry, concise logs/output, and one discoverable
  Results authority; and
- caller-complete retirement of active request-v3 intake, split launcher and
  resource configuration, generated and owner-local Slurm wrappers, duplicate
  lifecycle preparation, stale private ownership names, and qualified dead
  mirrors. Exact historical request/execution readers and Attempt evidence
  remain.

Exact hosted engineering evidence:

| Tranche | Exact revision and evidence | Ceiling |
|---|---|---|
| `ARCH-CLOSE-01` | `f85379edef0440266c1e97e97be5324e364812cb`; [ordinary CI 33630887395](https://github.com/lab-cats/EMRYS/actions/runs/33630887395); [selected 130-pair CI 33630899403](https://github.com/lab-cats/EMRYS/actions/runs/33630899403) | Managed real-tool direct journey, Rocky/Ubuntu/Debian lock installation, Python 3.11 shards, and hosted direct/disposable-Slurm success; not site, multi-node, production, scientific, or biological proof. |
| `ARCH-CLOSE-02` | `4a165038b3d164d6ace59b9e9bb21add086d07df`; [ordinary CI 33640599154](https://github.com/lab-cats/EMRYS/actions/runs/33640599154); [selected recovery CI 33640622974](https://github.com/lab-cats/EMRYS/actions/runs/33640622974) | Hosted direct/disposable-Slurm controlled failure, resume, provenance, Results, and logging parity at 130 pairs; not institutional or scientific proof. |
| `ARCH-CLOSE-03` | `f3622f791e90fd6ed15079abcbcbe9b7003cbb6a`; [ordinary CI 33653717181](https://github.com/lab-cats/EMRYS/actions/runs/33653717181); [CodeQL 33653716112](https://github.com/lab-cats/EMRYS/actions/runs/33653716112) | Role, ownership, baseline, closeout, ordinary CI, and static-security evidence; long lanes were not selected. |

Completed architecture and delivery IDs are retained compactly to prevent
accidental revival:

| Area | Complete or absorbed IDs |
|---|---|
| Foundations and model | `ARCH-CONST-01`, `ARCH-LAYER-01`, `ARCH-MODEL-AUDIT-01`, `ARCH-MODEL-DECISION-01`, `ARCH-MODEL-FIELDS-01`, `ARCH-01`, `CONTROL-01`, `CONFIG-01`, `IDENTITY-01` |
| Public journey and runtime | `SETUP-01`, `SETUP-03`, `OPS-01`, `OPS-02`, `OPS-04`, `RUNTIME-01`, `DOCTOR-01`, `RUN-03`, `OBS-01`, `OBS-02`, `REVIEW-UX-03`, `LOG-03`, `LOG-05` |
| Scientific modularity and Results | `ANALYSIS-01`, `ANALYSIS-02`, `FILESYSTEM-01`, `RESULTS-01`, `AC-SLICE-04`, `AC-SLICE-12` |
| Delivery and cleanup | `BACKLOG-01`, `DOC-02`, `DOC-03`, `DOC-TOOL-01`, `CLEAN-02` |
| Campaign envelopes | `ARCH-CLOSE-01`, `ARCH-CLOSE-02`, `ARCH-CLOSE-03`; `AC-SLICE-01`–`14` and `17`–`19` are complete or absorbed. `AC-SLICE-15`/`16` continue only as `SCI-AUDIT-01`/`SCI-ORACLE-01`. |

The former `DOC-COMPRESS-01`, `INLINE-OWNERS-01`, and
`MANAGED-CONTAINER-01` proposals are absorbed by `DOC-01`, `OPS-03`, and
`CONTAINER-01`. The explicitly retained original backlog IDs were
`FUT-DATA-02`, `FUT-INDEX-01`, `LOG-03`, `LOG-05`, and `REVIEW-UX-03`; the
latter three are complete. Former blocker relationships were discarded.

## Ratified no-op decisions and future triggers

These are not open tasks. Reconsideration requires the stated concrete need and
a separately accepted backlog row.

| Do not add now | Reconsider only when |
|---|---|
| Generalized execution backend or second scheduler | A concrete approved backend or caller-complete net reduction exists and parity can be proved. |
| Shared policy object | At least two production owners make the same decision from equivalent inputs and one migration removes all duplicate callers net-negatively. |
| Universal artifact lifecycle or Artifact Store | A demonstrated artifact class cannot be served by current class-specific admission/transactions; any replacement has one authority. |
| Run Bundle | A concrete portability, archive, or sharing requirement cannot be met by the current Project/Run/Results layout. |
| Site/global profile registry | A demonstrated multi-Project or multi-site need cannot use Project-local names or an exact absolute profile path. |
| Generic Stage hierarchy, workflow language, module installer, or report DSL | A concrete collaborator need cannot be met by the bounded provider interfaces and the addition simplifies rather than duplicates authority. |
| Public stop/cancel | Durable queued/running submission ownership and a safe terminal interrupted-state contract can be defined across supported placements. |
| Broader package API or generalized storage facade | A concrete extension or measured compression benefit exists. |

## Explicitly discarded legacy IDs

Do not revive these names implicitly: `AUDIT-99`, `CODEDOC-05`,
`DOC-SKILL-10`, `DOC-TASK-SCAN-01`, `FUT-ANALYSIS-01`, `FUT-CLI-03`,
`FUT-DASH-01`, `FUT-SUCCESS-04`, `GATE-REC-01`, `SKILL-11`, `FUT-AGENT-01`,
`FUT-AIDEV-01`, `FUT-SITE-01`, `FUT-SITE-02`, `TASK-INTAKE-01`,
`TASK-VIEW-01`, and `TEST-E2E-01`. Any similar future need must be stated and
accepted on its current merits under a new or explicitly re-authored row.
