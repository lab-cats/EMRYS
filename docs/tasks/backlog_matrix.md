# EMRYS backlog matrix

Last reconciled: **2026-09-17**

This is EMRYS's main work backlog. It owns accepted current outcomes, status,
cursory Importance and Complexity, and acceptance. Unfinished accepted outcomes
remain here or in their already named campaign owner. Lasting decisions and
evidence stay with their subject owners; Git retains superseded planning and
implementation chronology.

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
| `SITE-PARITY-01` | Site qualification | Open | `4` | `5` | Qualify the current whole-Run path on CSU Viking or another named institutional site. | A novice operator without repository-development context follows only the maintained quickstart from a fresh Viking clone through one head-node path: Project creation with built-in Viking placement, Doctor-managed setup and automatic Slurm qualification, validation, submitted execution, inspection, and completed Results and reports. Normal output is concise and Doctor exposes its phases and elapsed time; every undocumented prerequisite or confusing step becomes a finding. Retain and resolve the [Viking walkthrough findings](#viking-walkthrough-findings) at their stated evidence level. Exact site modules/tools, Project storage semantics, locking/rename/durability, failure/recovery, resource and scheduler provenance, one-log ownership, and direct/Slurm scientific parity are evidenced at one exact revision. Hosted single-node proof is not promoted to institutional, multi-node, production, scientific-review, or biological proof. |
| `CLUSTER-VERIFY-01` | Cluster verification campaign | Open | `4` | `5` | Resolve the recorded cluster-walkthrough failures and operator gaps while preserving scientific and recovery authority. | The [campaign charter](cluster_verification_campaign.md) owns scope and evidence; this matrix explicitly delegates `CV-01` through `CV-27`, `CV-U01` through `CV-U33`, and `CV-UX-01` statuses and acceptance, plus assigned priorities, to the [cluster verification backlog](cluster_verification_backlog.md). Preserve operator P0–P3 priorities and unexplained observations, investigate causes only where the delegated card still requires it, extend the managed golden path and exact-revision site exercises, and reconcile each card with its production owner. Synthetic completion is operator-reported, report viewing is deferred, and the actual-data Run remains unfinished at capture. Recording this campaign does not authorize its implementation or alter the active cluster Run. Close only under the charter's disposition and evidence criteria. |
| `SCHED-01` | Scheduler preflight | Open | `3` | `2` | Reject an explicitly undersized Slurm memory request before submission. | When both placement memory and the applicable workflow or stage minimum are explicit, admission rejects insufficient capacity before `sbatch`; unknown capacity remains unknown, the existing CPU check remains authoritative, and no generalized resource solver or duplicate scheduler policy is introduced. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `OPS-03` | Maintenance | Open | `3` | `4` | Settle the remaining responsibilities of retained diagnostics and execution helpers. | The [runner migration](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution) is delivered through PR #169: producers retain science; the runner owns execution and recovery. Remaining work concerns the [FASTQ byte and diagnostic contract](../../src/emrys/ingestion/sample_manifest_admission/README.md) and surviving scripts, inline programs, and R bootstraps. R argument parsing is already shared; wrappers differ in script location, package admission, diagnostics, and error precedence. Prove equivalent behavior and caller-complete savings before sharing more. These concerns require separate selection; no compression tranche remains active. Preserve independent scientific checks and retained evidence. `INLINE-OWNERS-01` remains absorbed here. |
| `FUT-INDEX-01` | Data reuse | Open | `4` | `4` | Admit an externally supplied prebuilt STAR index as an explicit Project input. | Existing reuse of a successful processing Run and standalone index validation are delivered capabilities, not external-index admission. The current [reference contract](../../src/emrys/contracts/schemas/orchestration/v1/reference.schema.json) declares FASTA/GTF and construction parameters but no prebuilt-index input. Remaining work binds every required index member to exact hashes, FASTA/GTF identity, and STAR parameters/version, then plans reuse without generation, repair, merge, or mutation; directory existence alone never authorizes admission. |
| `SETUP-02` | Tooling retirement | Deferred | `3` | `3` | Retire standalone resource benchmarking after the optimization campaign is complete. | Approved 2026-09-10: retain `scripts/benchmark_stage_resources.py` while the [optimization campaign](optimization_campaign.md) needs it, then retire the helper, dedicated tests, CLI checks, and obsolete documentation together. This replaces the proposal to expand benchmarking into the normal control plane. Preserve raw measurements, scientific-equivalence fixtures, and retained evidence. Until retirement, experiment acceptance still requires visible raw trials, rejection of candidates with any failed repetition, and nonzero exit for a failed benchmark; recommendations remain advisory and are never automatically applied. |
| `FUT-DATA-02` | Acquisition | Deferred | `2` | `5` | Provide retryable public-reference and SRA-read acquisition. | Reference and read acquisition remain separate and record accession/version, source, hashes, cache, retry, partial-transfer, and storage identity without scraping, silent updates, or implicit trust. |
| `PERF-01` | Performance research | Deferred | `2` | `4` | Test whether cross-node execution materially improves independent-work wall time. | A bounded representative experiment uses explicit per-job resources and never treats scheduler success as production or scientific proof. |
| `PROFILE-CONTRACT-01` | Contract reduction | Deferred | `3` | `4` | Remove derivable backend adapter fields during an independently justified workflow-profile contract transition. | Audit every current reader and generated profile, then determine whether the consumed `owner_tasks[].rule_name` projection and redundant scope selectors can be derived from one semantic authority; retain graph, uniqueness, scope, artifact admission and inventory/group ordering, Execution-Plan identity, and direct/Slurm parity; remove duplicate validators/tests rather than adding an adapter or compatibility writer. Do not create a version bump solely for cleanup, and dismiss the row if the fields prove independently semantic or the migration is not meaningfully net-negative. |
| `DASHBOARD-RETIRE-01` | Major retirement | Verification pending | `3` | `4` | Finish retirement of superseded dashboard surfaces and new `emrys-local-pilot` naming. | The institutional owner accepted the [installed watch](../../src/emrys/orchestration/run_coordinator/README.md#installed-watch) as the replacement on 2026-09-17. The standalone wrapper and callers are retired; shared parsing/rendering remains for watch. New v4 Run streams use `emrys-<token>` and Doctor uses `emrys-doctor`; exact v1-v3 legacy names remain read-only. Project-local inspect, strict accounting, sanitized raw streams and focused compatibility checks remain intact. Standard CI and institutional visual verification remain. Evidence deletion is separately approval-gated. |

### Viking walkthrough findings

The following retains the earlier setup decisions and evidence. Remaining
walkthrough work is now coordinated by the
[cluster verification campaign](cluster_verification_campaign.md) and its
[delegated CV backlog](cluster_verification_backlog.md), created at the user's
request on 2026-09-14. Earlier implementation allowances below do not extend
automatically to new campaign cards.

The September 14, 2026 walkthrough selected `7c427f0c`. The user reported
successful fresh installation and synthetic Project validation. Batch job
`614786` reported 71 R packages restored in 600 seconds and the managed runtime
inventory admitted. The user then reported the job finished and supplied the
successful head-node storage finalization for qualification
`cfcf7f788fd9d949f1a23f17793ecf22ba1e05f1023bc3b49065eebc0280186f`.
Its final receipt remains in `.emrys-storage-qualification/` beneath the parent
of the `emrys-smoke` Project. This was the former manually submitted setup;
it is not evidence for the new automated Doctor path.

The walkthrough stopped before the first scientific Run to address these
operator findings together. The approved implementation permits up to 750 net
additional product lines, no new product files or receipt formats, and Rich as
the shared terminal library. Product, tests, documentation, configuration and
evidence accounting remain separate.

- **One head-node journey.** Both Project-creation commands accept `--site viking`
  and write the existing default profile with the known site settings. Run,
  resume and standalone report execution use that placement. The quickstart
  includes the complete synthetic and own-data walkthroughs, reconnecting,
  and routine recovery. The runbook retains advanced configuration and input
  options, with links to the standard guide.
- **Automatic qualification.** Head-node Doctor repair installs the managed
  runtime, submits checks of the admitted runtime and storage, and completes
  head-node finalization. Existing receipts, exact bindings and failure
  protections remain authoritative. `--compute` is an explicit advanced route.
- **Readable progress and diagnostics.** Normal output omits debug commands.
  Doctor names phases, reports elapsed time and gives a rough first-setup
  allowance of 5–15 minutes, with longer download or queue waits possible.
  Terminal color supplements text labels; redirected output remains plain.
  Complete package output is retained beside the maintenance log. Repair uses
  its own temporary directory, avoiding the observed unwritable `/local/tmp`.
- **Viking memory accounting still needs site execution.** Completed job
  `605171` used `viking-users`, `long`, `normal`, four CPUs and eight hours;
  accounting reported `ReqMem=1M` but no allocated memory entry. Scheduler
  output reported `select/cons_tres`, `CR_CORE`, unlimited default/maximum
  per-node memory and `task/cgroup`. These observations do not establish a
  process memory limit. At `c52178d2`, the capacity observer rejected missing Slurm
  memory metadata for partial-node CPU allocations; no scheduler variables
  are forged and the allocation is not enlarged to bypass admission. Retain
  the first actual Run diagnostic before choosing a correction.
  The subsequent automated repair job `618134` passed runtime inspection and
  stopped at that capacity check. Diagnostic job `618190` on `node009` exposed
  four CPUs, neither Slurm memory variable, and effectively unlimited cgroup-v1
  memory limits through the visible hierarchy. The user explicitly approved
  using the node's process-visible RAM without a separate workflow budget or
  complete-node CPU requirement. The shared capacity observer now applies that
  fallback while preserving observed cgroup limits, declared scheduler limits,
  CPU constraints, and source attribution. After the published correction the
  operator reported Doctor `READY`; complete scientific execution was still
  pending at that point. The earlier generic runtime failures are not explained
  by this memory-policy correction.
- **Batch username missing before science.** A submitted Run failed while
  Snakemake built its startup header: no login-name environment variable
  survived the explicit submission export list, and the compute node could not
  resolve the job's numeric UID. Inspection subsequently reported valid
  integrity, a failed Attempt, and recovery available, with all scientific
  milestones incomplete. The shared Doctor/run/resume/report submission owner
  now preserves Python's four login-name variables by name while retaining its
  numeric UID checks and restricted environment. The existing batch execution
  fixture exercises each variable with passwd lookup unavailable. The export
  list is rendered directly instead of through an intermediate tuple; no new
  product owner, file, dependency, or identity authority is introduced.
  The operator subsequently reported a successful synthetic resume with all
  scientific milestones and reporting complete. CV-01 retains the broader
  managed-golden and institutional evidence requirements.

The later synthetic inspection reported a valid Run, a succeeded Attempt,
complete Scientific Results and Reporting, 151 inventoried artifacts, and
an Attempt elapsed time of 3:52. Viewing the HTML reports was explicitly
deferred. An actual-data Run was subsequently cancelled through Slurm and
remained blocked without a terminal receipt; a fresh Project reused the
installed runtime and began a replacement Run. That actual-data Run was still
active at the last supplied observation. The campaign's evidence register
preserves these distinctions, the unresolved first qualification failure, and
the transient reporting/remote-inspection findings without claiming new
independent site or scientific validation.

The existing real-Slurm CI journey now uses head-node Doctor preparation in
place of its manual storage-phase commands, preserving the scientific parity
and controlled recovery checks. That [hosted journey passed on `e25b10c6`](https://github.com/lab-cats/EMRYS/actions/runs/34885186045).
Local checks and hosted disposable Slurm do not establish Viking qualification.
Continue the actual-data walkthrough and the selected campaign regressions on
an identified revision; the reported synthetic success does not close site parity.
The retained six-library Viking profile has a different resource policy and is
not a capacity requirement for this tiny fixture.

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
| `REPORT-ROSTER-01` | Reporting contract | Needs decision | `3` | `4` | Decide which scientific validation check identities and order reporting must require. | [Reporting consolidation](../../src/emrys/reporting/README.md) and [reporting-independent scientific identity](../design/decisions/execution-evidence-and-reporting.md) are delivered. The remaining CS-05 proposal is transferred here: generic artifact admission checks shape, safe unique IDs, status and count, but does not declare exact membership/order. Preserve current behavior until the scientific owners and external-provider obligations are decided. A selected change must migrate validators, artifact declarations and reporting together, retain independent expectations and malformed-input checks, and qualify meaningful product reduction or receive a quantified exception. Preserve module-specific reports, source/roster rechecks, locks, receipt-last publication, independent goldens, current-version reuse and the existing reporter entry point. |

## Completed and closed outcomes

### Repository maintenance

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `COMPRESS-01` | Compression and comprehension | Closed | — | — | Substantially reduce duplicated code and documentation; make retained implementations and explanations easy to follow. | Closed by the user on 2026-09-14 after [PR #169](https://github.com/lab-cats/EMRYS/pull/169) merged at `2ecf7d44`: 42 CS cards completed; CS-05 transferred to `REPORT-ROSTER-01`. The closure record below states the result and its limits. The temporary campaign and backlog were retired after moving unique decisions and evidence to existing owners. Existing reporting, diagnostic, dashboard, optimization and scientific/site work remains with its named owners. No further compression tranche is active or implied. |

The compression campaign ran from 2026-09-02 to 2026-09-14. Against the agreed
`cab77a26` baseline, product fell from **69,223 to 55,862 physical lines**:
**13,361 fewer lines (19.30%)**. The 20% target was **55,378 lines**;
the campaign closed **484 lines short**, by explicit user decision.
The count includes tracked product `.py`, `.R`, `.sh`, `.css`, `.j2` files
and the workflow `Snakefile`, including relocated files. Generated
`renv/activate.R` and the tooling script `restore_r_environment.R` are excluded.

Integration PR #169 preserved all 93 commits from PR #140 and PRs #148–168.
Its separate comparison against pre-integration master `446802c0` is:

| Surface | Net lines |
|---|---:|
| Product | −13,480 |
| Tests and fixtures | −12,699 |
| Documentation | +802 |
| Schemas and configuration | −2,243 |
| Tooling | +284 |
| Generated and dependency files | +106 |
| Retained evidence | 0 |
| **Total** | **−27,230** |

That integration baseline gives a 19.44% product reduction; it does not replace
the agreed campaign baseline above. Git and the linked PRs retain the card
history, individual changes and review decisions. Scientific computation,
data, provenance, current Run recovery, both reports, figures and the dashboard
remain. Dashboard retirement still requires a validated replacement.

[Ordinary hosted CI](https://github.com/lab-cats/EMRYS/actions/runs/34857271894)
and [130-pair synthetic E2E](https://github.com/lab-cats/EMRYS/actions/runs/34857300341)
passed at `fdc7cc79`; merge `2ecf7d44` has the identical source tree.
Codex completed the source and integration reviews. These are hosted software
and disposable-Slurm results, not institutional-site, scientific-review or
biological validation.

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
