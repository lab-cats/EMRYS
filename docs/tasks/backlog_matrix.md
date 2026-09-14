# EMRYS backlog matrix

Last reconciled: **2026-09-14**

This is EMRYS's main work backlog. It owns accepted current outcomes, status,
cursory Importance and Complexity, and acceptance. The [closed compression
backlog](compression_backlog_matrix.md) retains historical CS dispositions and
proof; it is no longer an active task authority. Unfinished accepted outcomes
remain here or in their already named campaign owner. Git retains implementation
chronology.

The architectural direction is permanent rather than backlog prose. See the
[architecture rationale](../design/decisions/platform-direction.md), [current
architecture](../architecture/ARCHITECTURE.md), and [scientific pipeline
decisions](../design/decisions/scientific-pipeline.md).

## Operating rules

- A row accepts work but does not authorize implementation, publication,
  cluster use, destructive cleanup, scientific review, evidence promotion, or
  evidence deletion. Those authorities remain explicit.
- This matrix is not a fixed execution sequence. Select work from its outcome,
  acceptance, risk, value, and current context. Closed campaign cards are
  historical records, not a current execution sequence.
- **Open** means delivery remains. **In progress** means an approved bounded
  change is active. **Verification pending** means implementation appears
  complete but required evidence remains. **Deferred** means accepted work is
  intentionally retained for a later horizon. **Completed** records an accepted
  outcome at its stated evidence level. **Closed** records an explicit decision
  to end a campaign, with any unmet targets stated in its closure record.
- Mark a task Completed only when its whole outcome and acceptance pass at the claimed
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
| `HARNESS-01` | Test architecture | Verification pending | `3` | `3` | Keep simulated science entirely in test-owned seams. | The existing explicit test simulations still emit `local-science-tools` while injecting admission callbacks; reconcile that remaining naming/admission mismatch. Production dispatch, schemas, Run/Attempt, workflow, receipts, and recovery must have no test-only role or relaxed branch; current record formats are explicit; fixtures either satisfy the real runtime and storage admission contract or are named as injected simulations rather than `local-science-tools`; CI retains controlled partial-failure/resume proof without claiming scientific execution. |
| `RUN-01` | Runtime defect | Verification pending | `4` | `3` | Admit normal `renv` cache-package symlinks consistently. | Cache-package symlink handling is implemented; the retarget-after-hashing refusal test and managed restore, Doctor, and validation pass in hosted CI. Remaining evidence must identify a real restored cache-package symlink on that path, rather than infer the link representation from a successful restore. |
| `RUNTIME-CLOSURE-01` | Runtime integrity | Open | `4` | `3` | Bind the complete installed R dependency closure that can affect scientific execution. | Derive the recursive `Depends`, `Imports`, and `LinkingTo` closure from the admitted scientific namespaces; bind and re-admit that exact closure without hashing unrelated site-library packages or breaking normal `renv` cache symlinks. Every supported EMRYS R activation path forces automatic snapshots off so admission and execution cannot mutate dependency state. |
| `REFERENCE-INPUT-01` | Input diagnostic | Open | `2` | `1` | Report an empty FASTA header as a normal reference-validation error. | [The shared contig parser](../../src/emrys/libraries/references/contigs.py) indexes an empty token list for `>` or whitespace-only headers and raises `IndexError`. Correct that boundary across its callers using the existing contig tests; preserve valid names, sequence order/lengths and other rejection rules. This transferred correctness finding is not a compression saving or authorization to change scientific formats. |

### Platform, operation, and portability

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SITE-PARITY-01` | Site qualification | Open | `4` | `5` | Qualify the current whole-Run path on CSU Viking or another named institutional site. | A novice operator without repository-development context follows only the maintained quickstart from a fresh Viking clone through Project creation, runtime admission, Doctor, validation, Slurm execution, inspection or resume when warranted, and completed Results and reports; every undocumented prerequisite or confusing step becomes a finding. Exact site modules/tools, Project storage semantics, locking/rename/durability, failure/recovery, resource and scheduler provenance, one-log ownership, and direct/Slurm scientific parity are evidenced at one exact revision. Hosted single-node proof is not promoted to institutional, multi-node, production, scientific-review, or biological proof. |
| `SCHED-01` | Scheduler preflight | Open | `3` | `2` | Reject an explicitly undersized Slurm memory request before submission. | When both placement memory and the applicable workflow or stage minimum are explicit, admission rejects insufficient capacity before `sbatch`; unknown capacity remains unknown, the existing CPU check remains authoritative, and no generalized resource solver or duplicate scheduler policy is introduced. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `OPS-03` | Maintenance | Open | `3` | `4` | Settle the remaining responsibilities of retained diagnostics and execution helpers. | The caller-complete runner migration in [CS-18](compression_backlog_matrix.md#cs-18-idiomatic-scientific-producer-implementation) is delivered and merged through PR #169: producers retain science; the runner owns execution and recovery. Remaining retained concerns are the FASTQ byte/diagnostic contract and surviving script, inline-program and R-bootstrap responsibilities already recorded in the [dispositions](compression_backlog_matrix.md#broader-finding-families). They require separate selection; no approved compression implementation remains active here. Independent scientific checks and retained evidence survive. `INLINE-OWNERS-01` remains absorbed here. |
| `FUT-INDEX-01` | Data reuse | Open | `4` | `4` | Admit an externally supplied prebuilt STAR index as an explicit Project input. | Existing reuse of a successful processing Run and standalone index validation are delivered capabilities, not external-index admission. The current [reference contract](../../src/emrys/contracts/schemas/orchestration/v1/reference.schema.json) declares FASTA/GTF and construction parameters but no prebuilt-index input. Remaining work binds every required index member to exact hashes, FASTA/GTF identity, and STAR parameters/version, then plans reuse without generation, repair, merge, or mutation; directory existence alone never authorizes admission. |
| `SETUP-02` | Tooling retirement | Deferred | `3` | `3` | Retire standalone resource benchmarking after the optimization campaign is complete. | Approved 2026-09-10: retain `scripts/benchmark_stage_resources.py` while the [optimization campaign](optimization_campaign.md) needs it, then retire the helper, dedicated tests, CLI checks, and obsolete documentation together. This replaces the proposal to expand benchmarking into the normal control plane. Preserve raw measurements, scientific-equivalence fixtures, and retained evidence. Until retirement, experiment acceptance still requires visible raw trials, rejection of candidates with any failed repetition, and nonzero exit for a failed benchmark; recommendations remain advisory and are never automatically applied. |
| `FUT-DATA-02` | Acquisition | Deferred | `2` | `5` | Provide retryable public-reference and SRA-read acquisition. | Reference and read acquisition remain separate and record accession/version, source, hashes, cache, retry, partial-transfer, and storage identity without scraping, silent updates, or implicit trust. |
| `PERF-01` | Performance research | Deferred | `2` | `4` | Test whether cross-node execution materially improves independent-work wall time. | A bounded representative experiment uses explicit per-job resources and never treats scheduler success as production or scientific proof. |
| `PROFILE-CONTRACT-01` | Contract reduction | Deferred | `3` | `4` | Remove derivable backend adapter fields during an independently justified workflow-profile contract transition. | Audit every current reader and generated profile, then determine whether the consumed `owner_tasks[].rule_name` projection and redundant scope selectors can be derived from one semantic authority; retain graph, uniqueness, scope, artifact admission and inventory/group ordering, Execution-Plan identity, and direct/Slurm parity; remove duplicate validators/tests rather than adding an adapter or compatibility writer. Do not create a version bump solely for cleanup, and dismiss the row if the fields prove independently semantic or the migration is not meaningfully net-negative. |
| `DASHBOARD-RETIRE-01` | Major retirement | Deferred | `3` | `4` | Retire the stale dashboard only after a replacement dashboard is implemented and validated. | Replacement is required before retirement; expert command access alone does not satisfy this gate. Confirm no supported caller or unique retained evidence depends on it; remove dashboard product code, text parsers, dedicated tests, targets, and stale docs together. Complete the caller-wide retirement of `emrys-local-pilot` from newly generated Slurm job/stream names under the current version-support policy. Preserve Project-local `inspect` as status authority and retain scheduler accounting and sanitized raw-stream access through existing expert surfaces or the smallest justified replacement. Evidence deletion remains separately approval-gated. |

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
| `REPORT-ROSTER-01` | Reporting contract | Needs decision | `3` | `4` | Decide which scientific validation check identities and order reporting must require. | Declaration/publication consolidation and reporting-independent scientific identity are delivered in [CS-02–04/11/20](compression_backlog_matrix.md#working-queue). The remaining CS-05 proposal is transferred here: generic artifact admission checks shape, safe unique IDs, status and count, but does not declare exact membership/order. Preserve current behavior until the scientific owners and external-provider obligations are decided. A selected change must migrate validators, artifact declarations and reporting together, retain independent expectations and malformed-input checks, and qualify meaningful product reduction or receive a quantified exception. Preserve module-specific reports, source/roster rechecks, locks, receipt-last publication, independent goldens, current-version reuse and the existing reporter entry point. |

## Completed and closed outcomes

### Repository maintenance

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `COMPRESS-01` | Compression and comprehension | Closed | — | — | Substantially reduce duplicated code and documentation; make retained implementations and explanations easy to follow. | Closed by the user on 2026-09-14 after [PR #169](https://github.com/lab-cats/EMRYS/pull/169) merged at `2ecf7d44`. The [campaign](compression_campaign.md) and [closed backlog](compression_backlog_matrix.md) retain scope, 42 completed CS cards, the CS-05 transfer, decisions and exact evidence. Product reduction against the agreed baseline is 19.30%; the 20% target was not met (484 lines short). Ordinary hosted CI and the 130-pair synthetic lane passed. Existing reporting, diagnostic, dashboard, optimization and scientific/site work remains with its named owners. No further compression tranche is active or implied. |

CI-01, DEV-01, and CLI-VERSION-01 passed the complete ordinary hosted suite in
[run 34306975901](https://github.com/lab-cats/EMRYS/actions/runs/34306975901)
at `b491aac5`, including Python coverage, guarded R, managed golden path,
static/wheel, shell, and userspace checks. PR #148 merged through PR #169.

The other implemented outcomes below passed their applicable Python,
guarded-R, managed-golden, and independent-contract checks in
[ordinary hosted CI 34301289787](https://github.com/lab-cats/EMRYS/actions/runs/34301289787)
on PR #140's integrated tree. This closes their hosted software-verification
scope; PR #140 merged through PR #169. It does not establish
institutional-site execution, scientific review, or biological validation.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `CI-01` | CI usability and performance | Completed | `4` | `3` | Remove repeated workflow execution and shorten guarded-R fixture scheduling while preserving every distinct check. | Manual lane selection and balanced long-test estimates are delivered through PR #139; automatic stacked-PR checks and shared sharder self-tests are implemented and passed ordinary hosted CI in [PR #140](https://github.com/lab-cats/EMRYS/pull/140). The implemented fixture change combines the full-output assertions with the resume fixture's identical initial 35-task run, schedules the 16 independent negative R cases at most two at a time with explicit child-failure propagation, and removes the wrapper's duplicate package probe while retaining the production check. Preserve complete test selection, coverage enforcement, scientific comparisons, separate processes, and existing long lanes. Focused local checks pass; ordinary hosted CI passed on `b491aac5` in [PR #148](https://github.com/lab-cats/EMRYS/actions/runs/34306975901); no additional benchmark campaign or speculative duration target is required. |
| `DEV-01` | Developer feedback | Completed | `3` | `2` | Add ShellCheck, consistent Python formatting, and fast local pre-commit hooks through existing tool owners. | The existing lint gate now runs locked ShellCheck on every tracked shell file and Ruff formatting checks; actionlint also checks embedded workflow shell. Three pre-commit hooks check applicable staged files using the same locked tools, with no workflow, R, or full-suite execution. The formatting baseline is a separate mechanical commit with unchanged parsed Python code. Local static, shell-owner, workflow-lint, and hook checks pass; ordinary hosted CI passed on `b491aac5` in [PR #148](https://github.com/lab-cats/EMRYS/actions/runs/34306975901). These additions are the approved tooling exception, not product compression. |
| `CLI-VERSION-01` | Public CLI | Completed | `2` | `1` | Show installed EMRYS version information with `emrys --version [-v]`. | Implemented through the existing package version and public parser: the ordinary flag reports the version; `-v` adds loaded-package path and Python version/executable. The display works without a Project or scientific runtime, writes no logs, and leaves controlled-command runtime admission intact. Focused CLI and source-policy checks pass; ordinary hosted CI passed on `b491aac5` in [PR #148](https://github.com/lab-cats/EMRYS/actions/runs/34306975901). No new product file or version registry was introduced. |
| `QUAL-04` | Contract verification | Completed | `3` | `2` | Derive expected owner counts from the authoritative owner set. | Lifecycle and owner-count checks prove the current roster without stale constants. |
| `QUAL-05` | Provenance verification | Completed | `4` | `2` | Bind execution and resume to installed code, retaining exact bytes and build origin. | CS-26 replaces the checkout requirement with installed-package identity; separate Run implementation and Processing compatibility hashes still reject incompatible code. |
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
