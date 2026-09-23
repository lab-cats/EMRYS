# EMRYS backlog matrix

Last reconciled: **2026-09-22**

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

### Maintainability and release

These rows record accepted follow-up work. Audit questions are not established
defects or permission to delete code, tests, protections, or evidence. Select
each implementation separately under the workflow. Existing CV cards retain
their delegated status and site acceptance until explicitly transferred.
The [polish campaign](polish-campaign.md#current-follow-up-scope) coordinates
these seven outcomes, including the repository-wide 600-line audit. They are
not cluster-campaign closure requirements; this matrix retains their status
and acceptance.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `DOCS-01` | Documentation audit | Open | `3` | `4` | Trim documentation to its audience and enduring responsibility. | Audit the Runbook, Troubleshooting, root/owner READMEs, contracts, main matrix and other guides for duplication, unnecessary detail and developer history. Use plain reader-friendly language. Keep current commands and recovery in operator guides, exact behavior beside its owner, lasting rationale in decisions and necessary dated evidence in its evidence home; Git retains routine commit/PR chronology. Review the large coordinator `CONTRACT.md` explicitly. Transfer useful context and check links before removing superseded prose; evidence deletion remains separately authorized. [Documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression) governs placement. |
| `REDUCE-01` | Product audit and reduction | Open | `4` | `5` | Find dead, redundant and unnecessarily complex code and cut additions by 25% without losing essential behavior. | Before implementation, define the exact integration comparison refs, counted surfaces and whether additions means gross added lines or net growth; the 25% target is not yet a measured saving. Audit the complete touched paths and adjacent owners, including compatibility, scripts, configuration and mutable state. Explain and review [`_inspection_presentation.py`](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py), its terminal interaction/inspection projection/action handoff, and overlap with inspection and dashboard owners. Classify preserved, defective, undecided and environment-deferred behavior; prefer caller-complete deletion/consolidation. Preserve scientific meaning, provenance, recovery and legitimate protections. Report product, tests, docs, configuration and evidence separately; deleting non-product material cannot manufacture product savings. Coordinate `OPS-03` and existing polish proposals; do not reopen the closed compression campaign implicitly. |
| `SIZE-01` | File responsibility audit | Open | `3` | `4` | Account for every non-test file over 600 physical lines. | Inventory all non-test files, including documentation, contracts, schemas, configuration and tooling. Reduce mixed responsibility or obtain an explicit user-authorized exception for each retained large file under the [maintainability rule](../design/decisions/repository-and-delivery.md#maintainability). Record path, reason and approval, with a retirement condition for temporary exceptions. Existing size grants no exception. Do not split files mechanically or create an automated size gate solely to satisfy this record. |
| `ASSURANCE-01` | Test and protection audit | Open | `4` | `4` | Identify excessive, redundant or obsolete tests, protections and automated gates for the supported local-development and institutional-Slurm use. | Map each candidate to real supported behavior, a distinct failure and an evidence level; identify tests of nonexistent/retired behavior and fixtures that hide production defects. Review documentary filename/heading gates in [documentation tooling](../../scripts/documentation/README.md) for actual maintenance value. Use the [test baseline](../design/TEST_BASELINE.md) and its owner evidence limits; retain independent oracles and necessary boundary/fault coverage. Propose surviving defenses before removing protection; high-risk removal still needs explicit approval. This is not authority to weaken coverage baselines or delete retained evidence. Coordinate `QUAL-01` and `HARNESS-01` without duplicating them. |
| `SCHEMA-01` | Contract audit and decision | Open | `4` | `4` | Decide whether prerelease JSON schemas should start at v1, and identify dead or derivable fields. | Assess the stated alpha/no-external-consumer premise against actual readers, writers, registries, packaged paths, fixtures and retained Runs. Inventory every candidate field and its semantic, identity, provenance and recovery use. Coordinate `PROFILE-CONTRACT-01`. Decide identifiers/version reset separately from product 1.0; current [schema rules](../../src/emrys/contracts/schemas/README.md) remain until a migration is approved. Any selected reset must migrate all current callers together, reject incompatible records without modifying evidence, and avoid unnecessary aliases or historical readers. |
| `EXTENSION-01` | Collaborator usability | Open | `4` | `4` | Give collaborators a practical way to add their own analyses. | Build on the existing [provider and reporter entry points](../../src/emrys/analyses/README.md#collaborator-providers), adopting the earlier polish proposal. Demonstrate a minimal independently installable Analysis and reporter through real discovery, configuration admission, planning, execution, independent validation and reporting without substituting the loader. Explain declared inputs/outputs, dependencies, resources and identity/version refusal; retain literal expected results. Establish whether the existing Step 09/optional Step 10 boundary meets the intended analysis before proposing extensions; add no parallel plugin framework. |
| `RELEASE-01` | Release planning | Open | `4` | `4` | Define a concrete path from prerelease EMRYS to a v1 release. | Turn the prior alpha-release proposal into a concise readiness checklist: promised workflows/platforms, distributed artifact, installation and dependency policy, public/schema support policy, documentation, known limitations and exact-revision software/site evidence. Exercise promised installed operations outside the checkout through documented resources; do not infer compatibility across dependency ranges from locked tests. Assign blockers to existing owners, distinguish prerelease from 1.0 criteria and keep scientific review/biological interpretation separate. Define versioning and release-note requirements without publishing a release or inventing unsupported platform promises. |

### Novice setup and operational follow-up

These outcomes use the existing onboarding, submission, runtime and
documentation owners. The [approved pre-closure tranche](cluster_verification_campaign.md#remaining-delivery-scope)
includes all nine outcomes below, including `INIT-01` through `INIT-03`.
Its stopping point is source/documentation completion with required hosted
and institutional verification still explicit.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `QUICKSTART-01` | Reader journey | Verification pending | `4` | `3` | Make the Quickstart a short, actionable path from inputs to understood Results. | The guide now follows delivered INIT-01–03 behavior, retains the explicit study assignments/comparison/target/thresholds and inline Viking requests, and removes historical and internal-mechanics narration. An output map explains the scientific tables, plots, reports and retained provenance. The optional synthetic exercise has its own linked guide before the reuse/Doctor decision, and terminal report retrieval has one direct Runbook link. Exact hosted documentation checks and a fresh novice walkthrough remain; site memory/scratch acceptance stays with its existing owners. |
| `INIT-01` | Onboarding usability | Verification pending | `3` | `2` | Initialize a Project from the repository root as well as other supported working directories. | Named Init now uses `EMRYS_PROJECTS_ROOT` when selected, including the repository `.env` loaded by the public CLI; otherwise it uses the current directory. Preview shows the exact destination. The existing absent-child, canonical/writable-parent and no-write guards remain, as do explicit outputs for specialist Init commands. Public source and installed-command cases cover repository-root use, an unrelated directory with an explicit process setting, and the unsaved fallback. Exact hosted regression and fresh Viking novice acceptance remain under CV-U07; unrelated directories do not discover another checkout's `.env`. |
| `INIT-02` | Study selection usability | Verification pending | `4` | `3` | Read the Viking study's reference selection without making users paste 25 sequence names. | Guided sample setup now accepts the existing maintained [`step_07_partitions.primary_contigs.tsv`](../../configs/step_07_partitions.primary_contigs.tsv) through `--partition-manifest`. Quickstart selects it explicitly; EMRYS reads and validates all 25 names against the admitted FASTA, preserves their order, excludes extra contigs, and copies normalized inputs into the Project. Placement does not infer scientific selection. Partition-manifest conflicts and sample-input conflicts remain explicit, with original relative source bases; copied samples still require a partition manifest. Existing fully guided and copied-manifest routes remain supported. Current public cases cover the maintained file, missing selectors and preview/creation; exact hosted regression and novice Viking acceptance remain under CV-06/U20/U21. |
| `INIT-03` | Confirmation usability | Verification pending | `3` | `3` | Let the user confirm Project creation directly after the interactive preview. | Named Init now asks for yes/no approval after the complete preview and continues through the existing creation owner using its collected answers, manifest bytes and reference snapshot. The replay command/serializer is retired. Blank/no/EOF and noninteractive omission of execution remain nonmutating; `--preview` explicitly stops after review, and `--execute` remains automation. Existing one-pass FASTQ hashing, scientific admission, reference freshness and create-absent completion-last publication remain. Public confirmation/refusal/input-change cases replace replay-specific tests; exact hosted regression and novice acceptance remain under CV-06/U18. |
| `SCRATCH-01` | Site decision and verification | Verification pending | `4` | `3` | Decide whether `/tmp` is the appropriate scratch default for this Viking journey. | The [temporary-file guide](../operations/RUNBOOK.md#temporary-files) traces initializer/profile, Doctor package repair/probes, native-task scratch and environment overrides; the earlier unwritable `/local/tmp` failure does not identify a current source defect. Verify permissions, capacity, lifetime and head/compute-node availability at the named site before accepting a default; do not assume `/tmp` and `/local/tmp` share the same failure. Reconcile Quickstart and Troubleshooting and retain explicit errors rather than an unqualified fallback. Source review alone is not institutional evidence. |
| `SCHED-USAGE-01` | P2 production defect | Verification pending | `4` | `3` | Preserve selected-cluster terminal usage and explicitly bound live sampling. | Terminal `sacct` root rechecks and batch accounting now select the admitted root cluster. Live `sstat` supports only the locally configured cluster and must independently match that exact root; nonlocal live usage stays unavailable without erasing selected request state. Argument-sensitive transport cases cover implicit local, named local and remote requests, including identical job numbers across clusters. Preserve root/batch/UID identity brackets and honest unknown values. Exact hosted regression and institutional accounting/display evidence remain required under CV-U33. |
| `SUBMISSION-PREVIEW-01` | P2 policy reconciliation | Verification pending | `4` | `3` | Reconcile CV-22 resource disclosure with CV-U02/U04 concise output. | One admitted-profile formatter now supplies a compact summary before every Slurm approval, including Doctor: requested CPUs/memory, exclusivity and maximum runtime; explicit hosts and numeric workflow ceilings when restrictive or capacity is unknown. Stage limits, site settings and diagnostics remain behind `--verbose`. Contract, cards and presentation cases use this same policy; the frozen profile still binds submission. Exact hosted regressions and institutional preview acceptance remain under CV-22/U02/U04. |
| `VIKING-POLICY-01` | P2 documentation defect | Completed | `4` | `2` | Align Viking recovery guidance with the current allocation policy. | Troubleshooting now identifies [`execution_profile.py`](../../src/emrys/orchestration/run_coordinator/execution_profile.py) as the current `memory_mb: 0`, whole-node CPU and exclusive policy; the earlier null-memory workaround is explicitly historical. Source and guidance agree without changing allocation policy. Earlier rejection of other explicit memory requests establishes neither acceptance nor rejection of `--mem=0`; institutional verification remains required. |
| `CV-DOCS-01` | Acceptance consistency | Completed | `3` | `2` | Correct the remaining CV-12/CV-27 wording and navigation conflicts. | CV-12 now directly records its Discard disposition and unknown E01 cause, with no causal-reconstruction requirement. Quickstart directly links the Runbook terminal-transfer procedure. CV-27 still requires actual generated-bundle contents, relative links, rendering and institutional transfer; its tiny copy fixture proves command mechanics only. These wording/navigation corrections neither promote evidence nor close institutional or visual acceptance. |

### Deferred operational work

These accepted outcomes have enduring owners after the temporary CV records retire.
They are outside the selected pre-closure implementation tranche.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `CLEANUP-01` | Ownership design | Deferred | `3` | `4` | Select a safe owner-backed cleanup scope before implementing deletion. | Retains CV-23. Current owners establish no retained candidate class with both exclusive ownership and absence of references. Select a specific class, then preview exact candidates, references and consequences. Protect active/ambiguous Runs, older Attempts and reused outputs, shared inputs/sidecars, runtime borrowers and linked caches, receipts, locks, partials and recovery evidence. Unknown is not unused; age, scheduler disappearance and missing success receipts prove no deletability. Keep transaction-owned temporary cleanup at its existing boundary; reuse existing inspection and ownership rather than adding a generic registry or cleanup engine. Any evidence deletion requires separate explicit authority. |
| `INTERACTIVE-01` | Guided operation | Deferred | `3` | `4` | Extend guidance through the complete setup and analysis-launch journey. | Retains CV-U19's eventual default guided interaction with an optional manual route. Existing named Init, runtime admission, Doctor and Run confirmations are implemented partial behavior. No full prompt sequence, migration, default-mode transition or `--advanced` spelling is selected. Audit the existing CLI owners before selecting a bounded extension; preserve scientific choices, approval, no-write previews, provenance and recovery. |

### Cluster verification closure checklist

`CLUSTER-VERIFY-01` is **Verification pending**. The selected source and guide
corrections are implemented; CV-U06's one-line accounting exception is approved.
CV-10's accepted trust boundary remains in the
[recovery contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
and [operator guidance](../operations/TROUBLESHOOTING.md#run-and-reporting-state).
Broad audits, including the >600-line inventory, remain with polish; Deferred
work has the named owners above. The selected final-source resource follow-up
uses one test-owned profile derived from packaged allocation-aware defaults for
the managed golden and real synthetic journeys. It preserves allocation-derived
workflow CPU/memory and automatic repeatable-stage sharing, with a fixture-only
2048 MiB repeatable minimum; disposable Slurm requests node CPU, all scheduler-
available memory and exclusivity. Safely parallelizable lanes use all process-
visible CPUs, while ordered recovery and end-to-end boundaries remain serial.
This is still pending hosted verification and can establish mechanics on the
free-tier runner, not utilization, performance, Viking memory safety or
institutional qualification. Required verification is:

- [ ] **Final-source software evidence:** applicable hosted regressions and the
  explicitly selected, exact-revision **130-pair disposable-Slurm scenarios**:
  clean direct/Slurm parity, controlled failure/resume parity, and fresh active
  Slurm stop/resume. Ordinary PR CI does not select them. Retain the pinned real
  samtools child, stop target/current Task/Attempt, public stop and native exit,
  positive interrupted closure, unchanged predecessors, distinct resume, and
  final scientific/reporting oracles. Local stop fixtures and direct golden
  paths cannot substitute.
- [ ] **One institutional campaign:** fresh novice setup using the
  [Quickstart](../../quickstart.md), required synthetic and representative
  actual-data terminal outcomes, runtime reuse, resolved resources/memory and
  scratch, pre-Run/active/reporting/reconnect inspection, queued/native
  cancellation and recovery, cross-node combinations, and generated-report
  transfer. Cover each card's required combinations, timing and operator
  acceptance. Retain exact package/Run/Attempt/profile/input/runtime identities.
  The optional novice smoke guide waives no card's required synthetic evidence;
  disposable-node results establish no institutional memory or cross-node policy.
- [ ] **Separate review records:** report visual/link review and required
  scientific review with their reporting/scientific owners. Scheduler success
  and computational receipts do not establish either. Biological interpretation
  remains external work, never a pipeline completion gate.
- [ ] **Verified closure and retirement:** give every delegated card a terminal
  disposition or named transfer, reconcile live references, and preserve lasting
  decisions/evidence before retiring the backlog and charter together. Transfer
  E01–E12 and exact hosted/artifact records, including CV-10/CV-26 evidence, to
  [validation history](../history/validation-evidence.md); retain optimization
  decisions with their current owner. Preserve all limits and failed-suite
  distinctions. Retirement, evidence deletion and merge retain their separate
  authority; merge follows verified closure.

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
| `CLUSTER-VERIFY-01` | Cluster verification campaign | Verification pending | `4` | `5` | Resolve the recorded cluster-walkthrough failures and operator gaps while preserving scientific and recovery authority. | The [campaign charter](cluster_verification_campaign.md) owns scope and evidence; this matrix explicitly delegates `CV-01` through `CV-27`, `CV-U01` through `CV-U33`, and `CV-UX-01` statuses and acceptance, plus assigned priorities, to the [cluster verification backlog](cluster_verification_backlog.md). Selected source and guide corrections are implemented, including INIT-01–03. Preserve operator priorities, accepted trust limits and unexplained historical observations. Remaining acceptance is exact final-source hosted/disposable-Slurm evidence, coordinated institutional execution, separate review records and verified dispositions; Deferred work remains with `CLEANUP-01` and `INTERACTIVE-01`. Follow the [closure checklist](#cluster-verification-closure-checklist), retaining transferred source follow-ups and distinct institutional/review evidence. Close only under the charter's disposition and evidence criteria. |
| `SCHED-01` | Scheduler preflight | Verification pending | `3` | `2` | Reject an explicitly undersized Slurm memory request before submission. | The effective-profile check is implemented before submission, Doctor repair planning and profile creation, using the shared resource predicates. Explicit insufficient CPU or memory is rejected; symbolic or omitted capacity stays unknown, and placement-only resume retains its policy before checking. Verify the public no-submit/no-write, Doctor, authoring and resume cases on the final source. CV-11 retains the broader institutional heterogeneous-node acceptance. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `CI-IMAGE-01` | CI infrastructure decision | Open | `3` | `4` | Decide whether a shared immutable CI image should replace repeated real-E2E provisioning. | Measure cold and warm wall time, runner-minutes, transfer, and storage for checkout, Pixi, uv, renv, apt, and disposable Slurm provisioning. Run `35797246853` is the initial hosted baseline: an approximately 1.4 GiB Pixi cache and 239 MiB renv cache were restored, but the image-blind renv key produced a false hit after the move to `ubuntu-26.04`, and two scenarios rebuilt 71 R packages for 780–840 seconds each. Compare the corrected prerequisite immutable-cache job, a job container, and an ephemeral maintained runner image. Any adopted image is reproducibly built, digest-pinned, Node 24 compatible, supports disposable Slurm, contains no secrets, data, Project state, or retained evidence, and preserves independent controllers, databases, workspaces, evidence, exact provenance, patch ownership, and rollback. Adopt only for meaningful net savings. This CI-only decision does not replace product runtime authority or `CONTAINER-01`; implementation requires separate approval, otherwise close with the rejection evidence. |
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
