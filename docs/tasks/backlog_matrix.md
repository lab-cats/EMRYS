# EMRYS backlog matrix

Last reconciled: **2026-10-01**

This is EMRYS's main work backlog. It owns accepted current outcomes, status,
cursory Importance and Complexity, and acceptance. Unfinished accepted outcomes
remain here; subject catalogs retain findings without creating new task authority. Lasting decisions and
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
- **Open** means delivery remains. **Needs decision** means the accepted outcome
  is an unresolved decision, without a selected implementation. **In progress** means an approved bounded
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

These rows retain accepted follow-up outcomes and completed owner dispositions.
Audit questions are not established defects or permission to delete code, tests,
protections or evidence. The [execution/runtime](execution-runtime-findings.md),
[scientific/reporting](scientific-reporting-findings.md) and
[contracts/engineering](contracts-engineering-findings.md) catalogs group retained
findings; this matrix alone owns status and acceptance. `SCHEMA-01`, `EXTENSION-01`
and `RELEASE-01` remain separate outcomes, not cluster closure requirements.

#### October 1, 2026 owner completion

On **2026-10-01**, the owner directed that `REDUCE-01`, `ASSURANCE-01`,
`DOCS-01`, `SIZE-01` and `QUAL-01` be marked **Completed**. This is an explicit
owner disposition of these five workstreams, not a claim that every original
acceptance target was demonstrated. Their original scope and acceptance remain
in the rows below for context; they no longer assign further audit or
implementation work.

The retained findings, unresolved questions, source snapshots and evidence
limits remain available. Completion establishes no unmeasured 25% product-code
reduction, test-runtime improvement, exhaustive defect resolution, or new
runtime, institutional or scientific proof. It grants no blanket size exception,
protection retirement, evidence deletion, or implementation of an audit proposal.
Permanent architecture and maintenance rules remain in force. Other accepted
backlog items retain their own scope and status.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `DOCS-01` | Documentation audit | Completed | `3` | `4` | Trim documentation to its audience and enduring responsibility. | Completed by [owner direction on 2026-10-01](#october-1-2026-owner-completion). Original acceptance: Audit the Runbook, Troubleshooting, root/owner READMEs, contracts, main matrix and other guides for duplication, unnecessary detail and developer history. Use plain reader-friendly language. Keep current commands and recovery in operator guides, exact behavior beside its owner, lasting rationale in decisions and necessary dated evidence in its evidence home; Git retains routine commit/PR chronology. Review the large coordinator `CONTRACT.md` explicitly. Transfer useful context and check links before removing superseded prose; evidence deletion remains separately authorized. [Documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression) governs placement. The subject catalogs retain the audit findings without reopening this completed workstream. |
| `REDUCE-01` | Product audit and reduction | Completed | `4` | `5` | Audit dead code, duplication, and whether even valid checks, recovery paths, and supported workflows justify their complexity for EMRYS; record simpler policies and what each would lose. Reduce net product-code growth by 25% without losing essential behavior; any decision to narrow a currently ratified protection needs explicit approval. | Completed by [owner direction on 2026-10-01](#october-1-2026-owner-completion). Original acceptance: The owner selected net product-code growth as the primary 25% measure; exact integration comparison refs, counted extensions and move treatment remain to be fixed before implementation or scorekeeping. The target is not yet a measured saving. Audit the entire repository, including complete touched paths and adjacent owners, compatibility, scripts, configuration and mutable state. Explain and review [`_inspection_presentation.py`](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py), its terminal interaction/inspection projection/action handoff, and overlap with inspection and dashboard owners. Classify preserved, defective, undecided and environment-deferred behavior; prefer caller-complete deletion/consolidation. Preserve scientific meaning and retained evidence. For provenance, recovery and protections, record current benefit and exactly what a smaller policy would lose; implementation that narrows a ratified guarantee needs a separate explicit owner decision and any required guardrail change. Also identify and pursue redundant or excessive tests and documentation as separately measured reductions coordinated with `ASSURANCE-01` and `DOCS-01`; their removal cannot offset product growth or delete retained evidence. Report product, tests, docs, configuration and evidence separately. Coordinate `OPS-03` and existing polish proposals; do not reopen the closed compression campaign implicitly. The subject catalogs preserve the revision-bound audit findings; they are not a new source review. |
| `SIZE-01` | File responsibility audit | Completed | `3` | `4` | Account for every non-test file over 600 physical lines. | Completed by [owner direction on 2026-10-01](#october-1-2026-owner-completion). Original acceptance: Inventory all non-test files, including documentation, contracts, schemas, configuration and tooling. Reduce mixed responsibility or obtain an explicit user-authorized exception for each retained large file under the [maintainability rule](../design/decisions/repository-and-delivery.md#maintainability). Record path, reason and approval, with a retirement condition for temporary exceptions. Existing size grants no exception. Do not split files mechanically or create an automated size gate solely to satisfy this record. |
| `ASSURANCE-01` | Test and protection audit | Completed | `4` | `4` | Identify excessive, redundant or obsolete tests, protections and automated gates for the supported local-development and institutional-Slurm use. | Completed by [owner direction on 2026-10-01](#october-1-2026-owner-completion). Original acceptance: Map each candidate to real supported behavior, a distinct failure and an evidence level; identify tests of nonexistent/retired behavior and fixtures that hide production defects. Review documentary filename/heading gates in [documentation tooling](../../scripts/documentation/README.md) for actual maintenance value. Use the [test baseline](../design/TEST_BASELINE.md) and its owner evidence limits; retain independent oracles and necessary boundary/fault coverage. Propose surviving defenses before removing protection; high-risk removal still needs explicit approval. This is not authority to weaken coverage baselines or delete retained evidence. Coordinate `QUAL-01` and `HARNESS-01` without duplicating them. |
| `SCHEMA-01` | Contract audit and decision | Completed | `4` | `4` | Decide whether prerelease JSON schemas should start at v1, and identify dead or derivable fields. | The independently reviewed [retention decision and complete field screen](schema_01_contract_audit.md#retention-decision-at-a3309dbf) cover all 20 registered resources and 120 declared property groups, their readers/writers and semantic, identity, provenance and recovery uses. Retain current IDs, labels, packaged paths and fields; no dead-field deletion or beneficial blanket v1 reset was established. Eleven field candidates remain unselected hypotheses, with `PROFILE-CONTRACT-01` deferred. Unknown collaborators, private installs and retained site Runs remain unknown; keeping current contracts does not depend on proving their absence. This closes the audit/decision, implements no migration, and makes no runtime-parity or scientific claim. A future incompatible transition still requires a complete consumer and retained-record inventory. |
| `EXTENSION-01` | Collaborator usability | Open | `4` | `4` | Give collaborators a practical way to add their own analyses. | Build on the existing [provider and reporter entry points](../../src/emrys/analyses/README.md#collaborator-providers), adopting the earlier polish proposal. Demonstrate a minimal independently installable Analysis and reporter through real discovery, configuration admission, planning, execution, independent validation and reporting without substituting the loader. Explain declared inputs/outputs, dependencies, resources and identity/version refusal; retain literal expected results. Establish whether the existing Step 09/optional Step 10 boundary meets the intended analysis before proposing extensions; add no parallel plugin framework. |
| `RELEASE-01` | Release planning | Open | `4` | `4` | Define a concrete path from prerelease EMRYS to a v1 release. | Turn the prior alpha-release proposal into a concise readiness checklist: promised workflows/platforms, distributed artifact, installation and dependency policy, public/schema support policy, documentation, known limitations and exact-revision software/site evidence. Exercise promised installed operations outside the checkout through documented resources; do not infer compatibility across dependency ranges from locked tests. Assign blockers to existing owners, distinguish prerelease from 1.0 criteria and keep scientific review/biological interpretation separate. Define versioning and release-note requirements without publishing a release or inventing unsupported platform promises. |

The [RELEASE-01 readiness investigation](release-readiness.md) and
[contracts/engineering findings](contracts-engineering-findings.md) retain revision-bound
findings and open evidence questions. This matrix owns their status and acceptance.

### Novice setup and operational follow-up

These outcomes use existing functional owners. The owner closed the selected
source/guide sequence on 2026-09-22; remaining evidence is preserved in the
[cluster checklist and card groups](#cluster-verification-closure-checklist).
Related IDs below describe one criterion, not additional implementations.

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
They are outside the closed cluster source-development sequence.

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `CLEANUP-01` | Ownership design | Deferred | `3` | `4` | Select a safe owner-backed cleanup scope before implementing deletion. | Retains CV-23. The [ownership decision brief](cleanup-01-ownership-audit.md) retains the six-class no-go finding and open proof questions. Current owners establish no retained candidate class with both exclusive ownership and absence of references. Select a specific class, then preview exact candidates, references and consequences. Protect active/ambiguous Runs, older Attempts and reused outputs, shared inputs/sidecars, runtime borrowers and linked caches, receipts, locks, partials and recovery evidence. Unknown is not unused; age, scheduler disappearance and missing success receipts prove no deletability. Keep transaction-owned temporary cleanup at its existing boundary; reuse existing inspection and ownership rather than adding a generic registry or cleanup engine. Any evidence deletion requires separate explicit authority. |
| `INTERACTIVE-01` | Guided operation | Deferred | `3` | `4` | Extend guidance through the complete setup and analysis-launch journey. | Retains CV-U19's eventual default guided interaction with an optional manual route. The owner selected bare `emrys` on a terminal as the guided entry and existing named commands as the manual route. Existing named Init, runtime admission, Doctor and Run confirmations are implemented partial behavior. The complete prompt sequence and migration remain open; no `--advanced` spelling is selected. Audit the existing CLI owners before selecting a bounded implementation; preserve scientific choices, approval, no-write previews, provenance and recovery. |

The [INTERACTIVE-01 decision brief](interactive-01-discovery.md) traces the
current owner path and unresolved design choices. Its selected bare-terminal
entry is a design decision; implementation remains deferred under the row above.

### Cluster verification closure checklist

`CLUSTER-VERIFY-01` remains **Verification pending**. The September 22 owner
decision closed the selected source/guide and stacked-PR sequence, including
INIT-01–03 and CV-U06's one-line accounting exception. No new CV source tranche
is selected. A newly verified defect returns to its functional owner. The five
[owner-completed audits](#october-1-2026-owner-completion) stay Completed.

- **Hosted scope:** retain applicable exact-revision ordinary checks and selected
  130-pair clean direct/Slurm parity, failure/resume parity and active native
  stop/resume. Their evidence includes pinned native child, exact request/Task/
  Attempt, public stop and exit, positive closure, unchanged predecessors,
  distinct resume and independent scientific/reporting oracles. Ordinary CI
  alone does not select these lanes; direct golden paths cannot substitute.
- **Institutional scope remains pending:** one fresh novice Quickstart journey,
  required synthetic and representative actual-data terminal outcomes, two-Project
  runtime reuse, resolved memory/scratch, pre-Run/active/reporting/reconnect
  inspection, queued/native cancellation/recovery, cross-node combinations and
  generated-report transfer. Retain each card's timing/operator criteria and
  exact package/Run/Attempt/profile/input/runtime identities. Optional novice
  smoke does not waive the required synthetic evidence.
- **Separate review records remain pending:** generated-report visual/link review
  and required scientific review with those owners. Receipts, scheduler success
  and hosted parity establish neither; biological interpretation stays external.
- **Evidence and document transfer:** all 61 original IDs, priorities, statuses and
  remaining criteria now live below. Retiring their temporary documents does not
  close institutional acceptance. Permanent owners retain decisions and bounded
  evidence; exact prior implementations, observations and approvals remain linked
  through the [frozen card record](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/cluster_verification_backlog.md)
  and [E01–E12 register](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/cluster_verification_campaign.md#evidence-register).
  Historical growth approvals are not standing allowances. Merge, site execution
  and evidence deletion retain their separately stated authority.

The current hosted resource fixture derives from packaged allocation-aware defaults,
with a fixture-only 2048 MiB repeatable minimum, whole-node exclusive placement,
all scheduler-available memory and resolved task sharing. Ordered recovery stays
serial. Passing that fixture establishes no utilization, speedup, Viking memory
safety, institutional qualification or cross-node policy. Current exact-run results
belong with the [CI evidence owner](../../.github/workflows/README.md).
CV-10's accepted trusted-workspace limit remains in the
[recovery contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
and [operator guidance](../operations/TROUBLESHOOTING.md#run-and-reporting-state).

### Cluster card dispositions

This is the complete transferred authority: **53 Verification pending, five
Completed, two Deferred and one Discard**. VP below means Verification pending;
C means Completed, D Deferred and X Discard. P0–P3 preserve operator priorities;
“—” means none was assigned. Earlier Open checkpoints in frozen records are
historical. VP retains applicable hosted proof and the stated institutional/operator
acceptance; the shared checklist applies without duplicating it in every row.
Current mechanics live in the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md).

#### Project creation and input admission

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-06` | VP | P0 | Named guided creation preserves explicit study assignments, comparison, target and thresholds; verify fresh novice creation and supported existing-manifest import. INIT-02 uses the explicit maintained 25-name manifest, with full FASTA validation; no automatic study/legacy-bundle inference. |
| `CV-14` | VP | P1 | Same selected Projects-home outcome as INIT-01/CV-U07: canonical writable parent, absent child, no moving/adopting existing Projects; verify fresh-clone placement. |
| `CV-17` | VP | P1 | Creation reports phase and elapsed progress without invented byte percentages or extra admission reads; retain large-input/operator visibility acceptance. |
| `CV-U03` | VP | — | Normal Init/Validate shows destination/libraries, explicit strand/comparison/target, all five CMH thresholds, background state and three STAR values, with specific PASS/FAIL diagnosis; verify operator readability. |
| `CV-U07` | VP | — | INIT-01 governs the Projects home: ignored generated children inside the tracked home, saved selection or current-directory fallback, no implicit existing-Project move. Verify repository and unrelated-directory use. |
| `CV-U18` | VP | — | INIT-03 governs same-invocation review/approval; explicit sample/strand assignments, reference before selectors and two-condition direction without a default remain. Preview/no/blank/EOF do not create; preserve freshness and one-hash creation. |
| `CV-U21` | VP | — | Derive the global maximum read length in the sole FASTQ hash pass and STAR settings from admitted FASTA; preview reads no FASTQ content. Preserve explicit overrides and old omitted chromosome-bin value 18 without rewriting records; verify variable-length and fragmented-reference cases. |
| `CV-U24` | VP | — | Saved create-absent mode-0600 repository `.env` has closed CLI-default keys and CLI/process/saved/default precedence; no global Project or scientific defaults. Verify reconnect and effective-value disclosure. |
| `CV-U25` | VP | — | Preview hashes no FASTQ content; creation hashes each once and checks device/inode/size/mtime/ctime around publication. Preserve comparable large-input timing and Viking operator acceptance; no protection against privileged metadata forgery is claimed. |
| `CV-U26` | VP | — | New Projects contain normalized samples/partitions with correct relative bases and external FASTQ references; existing Projects are not migrated. Verify the novice/operator path. |

#### Novice guide

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-U08` | VP | — | QUICKSTART-01 owns one short actual-data path and an optional linked synthetic exercise before reuse/Doctor selection; preserve known scientific settings and explain outputs. Required campaign synthetic evidence remains separate. |
| `CV-U09` | VP | — | Explain invented tiny reads/reference/settings, optional confidence and time tradeoff plainly; novice comprehension acceptance itself requires no new cluster Run. |
| `CV-U10` | C | — | Removed the Git-revision command from the novice path; advanced provenance remains available. This static guide correction is complete. |
| `CV-U11` | VP | — | Guide commands are separately paste-ready and match actual prompt order/literal outcomes; creation uses the current same-invocation confirmation, not the retired replay command. Verify the fresh novice journey. |
| `CV-U20` | VP | — | QUICKSTART-01 retains inline selected Viking placement/time/scratch and explicit EV/PUM1 assignments, reverse strand, EV→PUM1, A>G, five CMH values and inactive background. External references are operator-provided; verify the complete guide against current prompts. |

#### Doctor qualification and presentation

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-02` | VP | P0 | Fault diagnostics retain check ID, phase, host, expected/observed result, exit and usable loader/tool logs; distinguish unavailable from failed assertions. Verify native/R/compute-only public failures. |
| `CV-04` | VP | P0 | Use the bounded empty one-core Snakemake startup probe with ambient options disabled, temporary scratch and preserved login-name export; verify missing UID lookup and each supported login variable at the institutional boundary. |
| `CV-05` | C | P0 | Repair planning distinguishes retained native/R work from actual manager actions while preserving fresh qualification. Hosted software outcome is complete; optional accounting is not compute/site performance proof. |
| `CV-09` | VP | P0 | Explain selected managed runtime versus PATH and compatible node eligibility; version/ABI/startup qualification does not pin one successful hostname. Verify compatible/incompatible site placement. |
| `CV-13` | VP | P1 | Use specific not-prepared/checks-failed/not-qualified/not-admitted states; BLOCKED denotes refusal of invalid work. Verify understandable operator diagnosis. |
| `CV-19` | VP | P1 | Verification versus installation/repair follows actual package-manager actions and fresh readiness; verify operator wording without creating another readiness authority. |
| `CV-26` | C | P2 | Accepted structural correction removed one intervening head diagnosis (five total became four) while preserving independent storage finalization, exact pre-storage readmission and final readiness. No measured speedup; serial R checks retained and digest caching deferred. |
| `CV-U04` | VP | — | Doctor shows requirement domains and actual phases/elapsed progress; detailed plans/paths stay verbose. Resource disclosure follows SUBMISSION-PREVIEW-01; terminal readability/collision acceptance remains separate from latency. |
| `CV-U05` | VP | — | Present the rough 5–25-minute setup allowance with download/queue uncertainty; verify terminal wording, not a promised or measured completion deadline. |
| `CV-UX-01` | VP | — | Shared live-progress output preserves diagnostic order, separating lines and readable zero-duration text in color/plain/narrow terminals. Retain the reported job 621172 collision and verify a fresh Viking terminal. |

#### Managed runtime reuse

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-08` | VP | P0 | Explicit two-Project reuse binds canonical donor identity, UID, selector, fixed content seal and generation; fresh qualification and retained failure claims remain. Verify site accessibility and lifecycle; no unsealing/adoption or general donor discovery. |
| `CV-U22` | VP | — | The selected guide offers a known smoke donor before Doctor, otherwise skips that reuse step. Verify exact donor/borrower review and installed/site use; an unselected general donor browser is not remaining acceptance. |
| `CV-U23` | VP | — | Donor repair publishes a new generation; borrowers and old Attempts keep the old one until explicit same-source replacement. Verify successful repair/replacement and failure preservation. Fixed-roster sealing does not establish transitive dependency closure. |

#### Resource selection and observation

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-07` | VP | P0 | One effective default/named/absolute profile drives Doctor, Run, resume and report. Verify authoring preview/create-absent, explicit-invalid refusal and drift readmission across boundaries; no silent fallback or optimum-performance claim. |
| `CV-11` | VP | P0 | SCHED-01 owns early rejection of undersized explicit requests; omitted/symbolic capacity stays unknown. Verify heterogeneous/missing-memory/shared/exclusive site combinations and placement-only resume without changing the immutable Run. |
| `CV-22` | VP | P1 | SUBMISSION-PREVIEW-01 owns compact preapproval CPU/memory/exclusivity/runtime, explicit hosts and restrictive/unknown-capacity numeric ceilings for every Slurm owner. Verify consistent site display; stage/site diagnostics remain verbose, capacity is not utilization. |
| `CV-U06` | VP | — | Allocation-aware CPU/RAM, automatic repeated-stage concurrency/shares and native arguments agree; ordered phases remain serial and shares do not rebalance dynamically. Verify institutional resolution; fixture-only minima are not production policy. The 251-line accounting exception is settled. |
| `CV-U27` | VP | — | Selected Viking placement and effective workflow policy agree between guide, Doctor and submission. Diagnose implicit saved-site/direct-profile mismatch without rewriting; explicit profile wins. Verify smoke-to-real operator selection. |
| `CV-U28` | VP | — | Current allocation-aware policy supersedes fixed 12-core/524288-MiB restoration; retain original provenance and task minima only where current declarations use them. Historical eight/four-hour reports prove no causality; restored fixed settings or benchmark comparisons are no longer acceptance. |
| `CV-U33` | VP | — | SCHED-USAGE-01 owns selected-cluster terminal accounting and local-only live sampling, exact root/batch/UID/path identity brackets and honest unknowns. Retain the selected request after Run association; verify institutional observations, not a timing optimization. |

#### Monitoring and presentation

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-15` | VP | P1 | Inspection distinguishes live-local, dead-local, foreign-host and invalid ownership; verified Tasks, starts and diagnostics are not liveness. Verify active/completed/unreachable/stale and terminal-without-final-receipt site cases. |
| `CV-16` | VP | P1 | Installed watch owns one fixed selection, shared overview/detail, bounded single-worker refresh and full-history generation-aware streams. Offline/no-scheduler stays unknown; verify reconnect, NFS and terminal behavior with explicit recovery handoff. |
| `CV-20` | VP | P1 | Retained bounded canonical requests exist before a Run; explicit inspection binds scheduler/accounting cluster, UID and paths. Run association is diagnostic until independently admitted, custom roots are frozen and ambiguity stays unknown. Verify early/late and reconnect cases. |
| `CV-24` | C | P2 | Watch resume/report/stop hands off to existing owners after teardown and fresh preview/admission, without shell execution or automatic Run/Analysis selection. The selected action surface is complete; a future Analysis chooser is not its gate. |
| `CV-25` | C | P2 | Explicit request/Run/Attempt log access preserves Task/start/terminal stream provenance, bounded history and custom-root uncertainty without newest selection. Delivered log access is complete; association alone grants no recovery or liveness. |
| `CV-U01` | VP | — | Semantic color covers Init (including synthetic/manifests), Validate, Run, Inspect and runtime output; readable plain/NO_COLOR/dumb-terminal output remains. Verify the operator-facing surfaces. |
| `CV-U02` | VP | — | One verbose boolean keeps low-level detail optional while normal output retains critical scientific review, Run/Results/reporting/outcomes/recovery and compact submission resources. Verify consistent operator display. |
| `CV-U13` | VP | — | One bounded inventory includes Runs and every retained submission with association, without collapsing multiple requests. Sole-target selection may be automatic; ambiguity requires a picker or nonterminal refusal, never newest/raw-scheduler fallback. |
| `CV-U14` | VP | — | Style recognized real log prefixes without changing literal bytes, including timestamps/Finished jobid/WorkflowError; verify site and tmux rendering. |
| `CV-U15` | VP | — | Refresh wording truthfully requests read-only rechecking; verify operator understanding and preserve admission ownership. |
| `CV-U16` | VP | — | Preserve follow/pause, counted navigation, search, tail-relative bounded search and generation/truncation reset. Mouse input is ignored except multiplexer wheel-to-arrow translation; verify tmux/terminal behavior. |
| `CV-U17` | VP | — | Admitted Run state overrides diagnostic counts; raw finished logs remain unverified and unobserved reporting stays NOT OBSERVED. Terminal jobs without proof remain incomplete/interrupted/not-reached. Original display inconsistency remains unexplained; verify current truthful presentation. |
| `CV-U29` | VP | — | Expose retained requests early and date the latest observation. Institutional population-time measurement and operator acceptance remain required; no invented latency target or inference from scheduler state. |
| `CV-U30` | VP | — | Overview grows from the top with a stable horizontal footer and semantic fields; narrow/plain terminals stay readable. Verify site visual behavior. |
| `CV-U31` | VP | — | Uses the same CV-U13 roster/picker: exact Project requests remain distinct from Runs across refresh and action selection. Verify sole/multiple/nonterminal and retained historical targets; no separate inventory authority. |
| `CV-U32` | VP | — | Extend that same bounded discovery to an explicit Project from any directory or immediate children of the declared Projects home (bound 256). No recursive/global/latest search; verify outside-Project and partial-discovery handling. Legacy inventory parity is bounded, not full behavior parity. |

#### Submission failure and recovery

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-03` | VP | P0 | Keep invocation, scheduler rejection, pending queue, compute failure, cancellation and head finalization distinct. Preserve uncertain submissions/logs and avoid automatic resubmission; accounting COMPLETED cannot erase transport failure. Verify queued/cancelled institutional phases. |
| `CV-10` | VP | P0 | Require positive native descendant closure before recovery; preserve unknown/old blocked Runs. Bound timeout warning, Linux child ownership, closed-abort historical admission and exact prepared-finalization names/bytes/inodes; same-inode recycled-byte substitution remains an accepted trusted-workspace limit. Verify queued/native TERM/KILL, lost-worker and publication-fault boundaries separately. |
| `CV-18` | VP | P1 | Stop the exact retained request with controller-side identity filtering, known profile/logging and bounded fresh settlement. Old request versions without authority remain read-only; diagnostic Run association is insufficient. Verify queued/native site stop and no retry after ambiguous outcome. |
| `CV-U12` | VP | — | Warn/refuse equivalent active or unconfirmed Analysis/boundary/source/profile work before submission; compare exact profile content, reject unknown retained arguments and require explicit override without auto-cancel. Verify early requests and delayed association; no atomicity claim beyond the admitted boundary. |

#### Reporting and integrated proof

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-21` | VP | P1 | Inspect truthful reporting transaction states and only admitted locations/completion. Fixtures use real publication/readers with doubled science. E06 cause reconstruction/induced reproduction is waived; verify ordinary institutional behavior, leaving visual/scientific review with separate owners. |
| `CV-27` | VP | P3 | Retrieve an actually generated Results/report bundle via the Runbook SSH/rsync path, preserving contents and relative links; review locally without adding a server/tunnel/command. Tiny-copy mechanics do not prove generated-bundle rendering or institutional transfer; coordinate REPORT-01–03. |
| `CV-01` | VP | P0 | Retain integrated missing-memory plus unavailable-UID startup, shared-runtime plus node-placement, native-publication cancellation, failure/resume, inspection and reporting combinations. Selected hosted scenarios and cross-node/institutional proof remain distinct; success-only or local simulated cases cannot close the broader obligation. |

#### Transferred and discarded scope

| ID | Status | Priority | Retained outcome and remaining acceptance |
| --- | --- | --- | --- |
| `CV-23` | D | P2 | CLEANUP-01 owns the six retained artifact classes and exact-subtype ownership/reference/quiescence proof; no class is selected for deletion. Existing transaction cleanup is a different boundary. |
| `CV-U19` | D | — | INTERACTIVE-01 owns eventual full guided operation: bare terminal entry and named-command manual route are accepted; complete transcript/migration and cancellation exits remain unselected, with no approved advanced flag. |
| `CV-12` | X | P0 | Discard only causal reconstruction of the original E01 qualification failure. Preserve the unexplained observation; later successes do not identify its cause. |

### Reliability and qualification

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `QUAL-01` | Test performance | Completed | `3` | `3` | Make qualification-test selection fast enough for routine development. | Completed by [owner direction on 2026-10-01](#october-1-2026-owner-completion). Original acceptance: Measure duration and subprocess/NFS cost, set a justified target, and meet it without dropping coverage or fault cases. |
| `QUAL-02` | Defect verification | Completed | `4` | `2` | Replace the brittle resume-fixture startup deadline with bounded readiness and useful failure diagnostics. | The existing readiness wait is shared within its test owner without changing its native success path or 300-second bound. Two tiny real-child fault cases now verify early exit 23 and a missing-readiness timeout, literal diagnostic/log content, retained logs and bounded cleanup; focused local checks pass. Both cases passed unskipped in retained JUnit on `6336a6d5`; managed-native and all 14 selected jobs also passed. The workflow itself was cancelled during the subsequent push; [exact job evidence](#october-2-2026-bounded-hosted-verification) is controlling. The [test owner](../../tests/orchestration/run_coordinator/README.md#what-the-checks-establish) keeps these diagnostic cases distinct from real-backend native containment and institutional proof. |
| `QUAL-03` | Compatibility verification | Completed | `4` | `2` | Admit the accepted GNU Make 3.81 and 4.3 dry-run renderings without normalizing malformed output. | The two exact renderings and rejection of mixed/malformed renderings are implemented and covered by passing hosted tests. Python 3.14 shard logs now record the actual Make path/version in the same shell immediately before execution; all four shard logs on `6336a6d5` record `/usr/bin/make` and GNU Make 4.3; across those shards all 31 public-Make cases passed. [Exact job evidence](#october-2-2026-bounded-hosted-verification) closes this bounded compatibility check. Local Make is 3.81; the runner image alone is not version evidence. |
| `PICARD-METRICS-01` | Defect repair | Verification pending | `4` | `2` | Refuse ambiguous Picard metric columns and reconcile both readers. | Both callers now use the existing [Picard owner](../../src/emrys/libraries/quality/README.md): unique literal columns, required columns in any order and exactly one first-table row, with bounded retained rows and complete text admission. Local owner, public-validator and reporting fixtures cover duplicate/missing/reordered columns, extra rows, trailing corruption, unchanged numeric policy and `not_assessed` projection. This retires the separate reporting scanner with two net additional product lines in two existing files under delegated scope; no new files or dependencies. Hosted verification remains. Metrics-gate retirement and normalized-name collision policy are unselected; no complete Run or scientific claim. |
| `RECOVERY-ORACLE-01` | Protection repair | Verification pending | `4` | `2` | Make foreign-runtime-child and predecessor-log preservation tests independent. | A01-303 now exercises the real Doctor repair executor with a foreign ordinary file, preserving bytes/inode and the child roster before manager planning/execution while retaining its diagnostic and maintenance claim. A01-284 now uses a separate application log outside the Attempt tree and independently mutates Attempt, log, stdout and stderr. Eight focused local cases and independent review pass; hosted verification remains. Production is unchanged. Synthetic setup and literal evidence files are not actual dependency repair, scheduler resume or institutional proof. |
| `HARNESS-01` | Test architecture | Verification pending | `3` | `3` | Keep simulated science entirely in test-owned seams. | Explicit injected workflow/owner fixtures now declare the existing `test-double` mode, retaining Run/source/required-tool/storage identities and literal predecessor/successor labels; see [fixture ownership](../../tests/orchestration/run_coordinator/fixtures/README.md). Production plans and real managed E2E remain `local-science-tools`; default runtime/storage admission is unchanged. Local fixture/contract checks cover declaration semantics; controlled partial-failure/resume and native cancellation remain CI proof without claiming scientific execution. Remaining acceptance: production dispatch, schemas, Run/Attempt, workflow, receipts and recovery must have no test-only role or relaxed branch. The active workflow-attempt.v4 schema still admits `test-double`, with mode-dependent required-tool checks; this is not merely a historical reader. Retiring that public compatibility and preserving immutable resume modes need a separate decision. Verification pending remains; the current-fixture correction does not close this compatibility gap. |
| `RUN-01` | Runtime defect | Completed | `4` | `3` | Admit normal `renv` cache-package symlinks consistently. | [Retained real-runtime evidence](../../tests/evidence/runtime_availability/README.md#restored-cache-symlink-verification) identifies an actual restored VariantAnnotation cache symlink, passing Doctor discovery/readiness observations, and the identical resolved package root and digest in the successful Attempt and donor seal. Hosted CI 36956303545 passed on source `06f88dbc`; its merge checkout has the identical tree. Existing retarget-after-hashing and managed-containment refusals remain. This closes the normal-cache-link evidence gap, not institutional qualification or R dependency closure. |
| `RUNTIME-CLOSURE-01` | Runtime integrity | Open | `4` | `3` | Bind the complete installed R dependency closure that can affect scientific execution. | Derive the recursive `Depends`, `Imports`, and `LinkingTo` closure from the admitted scientific namespaces; bind and re-admit that exact closure without hashing unrelated site-library packages or breaking normal `renv` cache symlinks. The [automatic-snapshot guard](../../src/emrys/evidence/runtime_availability/README.md#automatic-snapshot-guard) now forces both environment and R-option settings off before either supported enabled profile path; tiny real-R/configuration checks pass, with managed-runtime CI tracked separately. That bounded startup repair does not implement dependency identity. The [closure proposal](../../src/emrys/evidence/runtime_availability/README.md#proposed-r-dependency-closure) retains open binding/seal/migration decisions and required graph, drift, reuse and recovery checks. |
| `REFERENCE-INPUT-01` | Input diagnostic | Completed | `2` | `1` | Report an empty FASTA header as a normal reference-validation error. | [The shared contig parser](../../src/emrys/libraries/references/contigs.py) now rejects bare, whitespace-only and later empty headers with `ReferenceContigError`, using callers’ existing validation-error handling. Local boundary and caller checks passed; full [Python 3.14](https://github.com/lab-cats/EMRYS/actions/runs/36820951934) and [Python 3.11](https://github.com/lab-cats/EMRYS/actions/runs/36820988652) regressions passed on `f4eaaa41`. The separate managed-R restoration failure does not invalidate this input-diagnostic evidence. Valid names, sequence order/lengths and other rejection rules are preserved. This input-diagnostic repair is not a scientific-format change or measured compression saving. |

### Platform, operation, and portability

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SITE-PARITY-01` | Site qualification | Open | `4` | `5` | Qualify the current whole-Run path on CSU Viking or another named institutional site. | A novice operator without repository-development context follows only the maintained quickstart from a fresh Viking clone through one head-node path: Project creation with built-in Viking placement, Doctor-managed setup and automatic Slurm qualification, validation, submitted execution, inspection, and completed Results and reports. Normal output is concise and Doctor exposes its phases and elapsed time; every undocumented prerequisite or confusing step becomes a finding. Retain and resolve the [Viking walkthrough findings](#viking-walkthrough-findings) at their stated evidence level. Exact site modules/tools, Project storage semantics, locking/rename/durability, failure/recovery, resource and scheduler provenance, one-log ownership, and direct/Slurm scientific parity are evidenced at one exact revision. Hosted single-node proof is not promoted to institutional, multi-node, production, scientific-review, or biological proof. |
| `CLUSTER-VERIFY-01` | Cluster verification campaign | Verification pending | `4` | `5` | Resolve the recorded cluster-walkthrough failures and operator gaps while preserving scientific and recovery authority. | This matrix owns all 61 [original CV IDs, statuses, priorities and criteria](#cluster-card-dispositions) after their transfer from the temporary campaign. Selected source and guide corrections are implemented, including INIT-01–03. Preserve operator priorities, accepted trust limits and unexplained historical observations. Remaining acceptance is exact final-source hosted/disposable-Slurm evidence, coordinated institutional execution, separate review records and verified dispositions; Deferred work remains with `CLEANUP-01` and `INTERACTIVE-01`. Follow the [closure checklist](#cluster-verification-closure-checklist), retaining transferred source follow-ups and distinct institutional/review evidence. Document retirement does not complete the transferred institutional or review criteria. |
| `SCHED-01` | Scheduler preflight | Completed | `3` | `2` | Reject an explicitly undersized Slurm memory request before submission. | The effective-profile check is implemented before submission, Doctor repair planning and profile creation, using the shared resource predicates. Explicit insufficient CPU or memory is rejected; symbolic or omitted capacity stays unknown, and placement-only resume retains its policy before checking. Independent source review and focused local checks cover all four callers; the Doctor and prepared/finalized resume cases now directly exercise memory shortfalls, exact-fit resume and unchanged state before refusal. All 37 selected cases passed unskipped on `6336a6d5`, with successful aggregate coverage/completeness verification; see [exact job evidence](#october-2-2026-bounded-hosted-verification). CV-11 retains the broader institutional heterogeneous-node acceptance. |
| `CONTAINER-01` | Managed platform | Open | `3` | `5` | Evaluate and, if justified, provide a supported broadly compatible Linux container without coupling it to project setup. | Compare against the existing Pixi-managed path; cover architecture/ABI support, Slurm and storage integration, security, reproducibility, licenses, tool and R identities, updates, provenance, site coexistence, and escape hatches. Any implementation has explicit local and site evidence and replaces rather than duplicates setup/runtime authority. |
| `CI-IMAGE-01` | CI infrastructure decision | Open | `3` | `4` | Decide whether a shared immutable CI image should replace repeated real-E2E provisioning. | Measure cold and warm wall time, runner-minutes, transfer, and storage for checkout, Pixi, uv, renv, apt, and disposable Slurm provisioning. Compare the current hosted runner plus lock-keyed caches, a job container, and an ephemeral maintained runner image. Any adopted image is reproducibly built, digest-pinned, Node 24 compatible, supports disposable Slurm, contains no secrets, data, Project state, or retained evidence, and preserves independent controllers, databases, workspaces, evidence, exact provenance, patch ownership, and rollback. Adopt only for meaningful net savings. This CI-only decision does not replace product runtime authority or `CONTAINER-01`; implementation requires separate approval, otherwise close with the rejection evidence. |
| `OPS-03` | Maintenance | Open | `3` | `4` | Settle the remaining responsibilities of retained diagnostics and execution helpers. | The [runner migration](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution) is delivered through PR #169: producers retain science; the runner owns execution and recovery. Remaining work concerns the [FASTQ byte and diagnostic contract](../../src/emrys/ingestion/sample_manifest_admission/README.md) and surviving scripts, inline programs, and R bootstraps. R argument parsing is already shared. The three test-owned Rscript selectors now use one [bounded helper](../../tests/tools/README.md), reducing wrapper-plus-helper implementation from 164 to 127 lines. Owner/global/default precedence, explicit-refusal versus optional-skip behavior and owner handoffs pass under Bash 3.2; private selector diagnostics are standardized and directory overrides refused before execution. Package admission and scientific checks stay with each owner. This delivered sub-slice does not settle production bootstraps or FASTQ behavior; prove caller-complete savings before sharing more. These concerns require separate selection; no compression tranche remains active. Preserve independent scientific checks and retained evidence. `INLINE-OWNERS-01` remains absorbed here. |
| [FUT-INDEX-01](fut_index_01_plan.md) | Data reuse | Open | `4` | `4` | Admit an externally supplied prebuilt STAR index as an explicit Project input. | Existing reuse of a successful processing Run and standalone index validation are delivered capabilities, not external-index admission. The current [reference contract](../../src/emrys/contracts/schemas/orchestration/v1/reference.schema.json) declares FASTA/GTF and construction parameters but no prebuilt-index input. Remaining work binds every required index member to exact hashes, FASTA/GTF identity, and STAR parameters/version, then plans reuse without generation, repair, merge, or mutation; directory existence alone never authorizes admission. |
| `SETUP-02` | Tooling retirement | Deferred | `3` | `3` | Retire standalone resource benchmarking when the remaining selected investigations no longer need it. | Approved 2026-09-10: retain `scripts/benchmark_stage_resources.py` while work under the [resource-measurement disposition](execution-runtime-findings.md#resource-measurement) needs it, then retire the helper, dedicated tests, CLI checks, and obsolete documentation together. This replaces the proposal to expand benchmarking into the normal control plane. Preserve raw measurements, scientific-equivalence fixtures, and retained evidence. Until retirement, experiment acceptance still requires visible raw trials, rejection of candidates with any failed repetition, and nonzero exit for a failed benchmark; recommendations remain advisory and are never automatically applied. |
| `FUT-DATA-02` | Acquisition | Deferred | `2` | `5` | Provide retryable public-reference and SRA-read acquisition. | Reference and read acquisition remain separate and record accession/version, source, hashes, cache, retry, partial-transfer, and storage identity without scraping, silent updates, or implicit trust. |
| `PERF-01` | Performance research | Deferred | `2` | `4` | Test whether cross-node execution materially improves independent-work wall time. | A bounded representative experiment uses explicit per-job resources and never treats scheduler success as production or scientific proof. |
| `PROFILE-CONTRACT-01` | Contract reduction | Deferred | `3` | `4` | Remove derivable backend adapter fields during an independently justified workflow-profile contract transition. | Audit every current reader and generated profile, then determine whether the consumed `owner_tasks[].rule_name` projection and redundant scope selectors can be derived from one semantic authority; retain graph, uniqueness, scope, artifact admission and inventory/group ordering, Execution-Plan identity, and direct/Slurm parity; remove duplicate validators/tests rather than adding an adapter or compatibility writer. Do not create a version bump solely for cleanup, and dismiss the row if the fields prove independently semantic or the migration is not meaningfully net-negative. |
| `DASHBOARD-RETIRE-01` | Major retirement | Verification pending | `3` | `4` | Finish retirement of superseded dashboard surfaces and new `emrys-local-pilot` naming. | The institutional owner accepted the [installed watch](../../src/emrys/orchestration/run_coordinator/README.md#installed-watch) as the replacement on 2026-09-17. The standalone wrapper and callers are retired; shared parsing/rendering remains for watch. New v4 Run streams use `emrys-<token>` and Doctor uses `emrys-doctor`; exact v1-v3 legacy names remain read-only. Project-local inspect, strict accounting, sanitized raw streams and focused compatibility checks remain intact. Standard CI and institutional visual verification remain. Evidence deletion is separately approval-gated. |

### Viking walkthrough findings

The [coordinator qualification record](../../src/emrys/orchestration/run_coordinator/README.md#qualification-evidence-and-limits)
and [resource provenance](../../src/emrys/orchestration/run_coordinator/resources/README.md#resource-policy-provenance)
retain the exact jobs, qualification identity, memory observations, unexplained
failures and actual-data outcome limits. The earlier 750-line/Rich allowance is
dated authority, not a current grant. [Frozen original decisions](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/backlog_matrix.md#viking-walkthrough-findings)
retain exact context; the cluster groups and SITE-PARITY-01 own remaining acceptance.

### Scientific review and independent validation

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `SCI-AUDIT-01` | Scientific review | Open | `5` | `5` | Audit the complete Steps 07–09 statistical contract. | An identified independent reviewer traces the candidate universe, raw count construction, multiallelic/symbolic filtering, manifest order and replicate pairing, CMH strata/table/direction, the exact Benjamini-Hochberg family, eligibility, thresholds, effect sizes, ranking, and interpretation limits against representative fixtures and source. Review authority, data, reference calculations, and evidence ceiling are defined first; discrepancies become characterized findings rather than presumed defects, and no software check is promoted to scientific or biological validation. |
| `SCI-ORACLE-01` | Independent validation | Completed | `5` | `4` | Establish independent numerical oracles for Steps 08 and 09. | [Step 08 reference](../../tests/stages/cohort_candidate_preprocessing/README.md#independent-computational-reference) derives complete scientific rows and counts from tiny raw inputs using independent point-set annotation, with literal and corruption cases plus actual-R/public-validator wiring. [Step 09 review](../../tests/analyses/paired_cmh_candidate_ranking/README.md#sci-oracle-01-coverage-review) preserves the existing numerical corpus and adds positive sample-pairing/order coverage only. The Step 08 reference/validator and Step 09 oracle/validator tests passed on `6336a6d5`; guarded R actually ran all three raw-input/public-validator cases and native Step 09 fixtures. [Exact job evidence](#october-2-2026-bounded-hosted-verification) includes the successful assembled gate. Expectations and tolerances received independent computational review, not scientific endorsement; characterize any disagreement before changing algorithms or expectations. SCI-AUDIT-01 remains separate. |

### Reporting and Results

Every reporting row inherits the [shared report acceptance](#shared-report-acceptance).

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `REPORT-01` | Visual verification | Verification pending | `5` | `3` | Produce readable locus-centered figures aligned with the supplied Figures 4b and 6b references. | Rendered output makes editing rate, location, local sequence, nearby motifs, significant candidates, and replicate behavior immediately readable and passes visual comparison. |
| `REPORT-02` | UX verification | Verification pending | `5` | `3` | Replace wide human tables with a narrow ranked summary, comparison views, and vertical detail. | Exact facts remain printable and visible; complete data is linked as machine-readable output rather than rendered as wide appendices. |
| `REPORT-03` | Audience verification | Verification pending | `4` | `2` | Confirm the primary-findings-first scientific, evidence, and operational hierarchy. | The scientific report answers what was found; the combined Evidence and operations report answers why it is trustworthy and how execution proceeded. Fixed relative navigation, Run overview, Evidence provenance, and Operations Attempt lineage pass rendered user review without adding a third artifact. |
| `REPORT-04` | Report capability | Verification pending | `4` | `3` | Render an A-through-I candidate/panel roster when warranted. | [Nine-candidate implementation](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/README.md) uses native context/receipt v2, explicit limit 9 and figure policy v5, retaining full tables, ordering and numeric links. Independent literals cover all nine selections and old-receipt refusal; [model visual review](../../tests/reporting/README.md#nine-candidate-presentation-review) covers long content at narrow/desktop sizes and corrected figure print layout. The final 43-page model PDF also passes the bounded print review; locked native-R execution and shared report acceptance remain due. The model fixture is not a complete Run or scientific proof; no higher display limit is implied. |
| `REPORT-ROSTER-01` | Reporting contract | Needs decision | `3` | `4` | Decide which scientific validation check identities and order reporting must require. | [Reporting consolidation](../../src/emrys/reporting/README.md) and [reporting-independent scientific identity](../design/decisions/execution-evidence-and-reporting.md) are delivered. The remaining CS-05 proposal is transferred here: generic artifact admission checks shape, safe unique IDs, status and count, but does not declare exact membership/order. Preserve current behavior until the scientific owners and external-provider obligations are decided. A selected change must migrate validators, artifact declarations and reporting together, retain independent expectations and malformed-input checks, and qualify meaningful product reduction or receive a quantified exception. Preserve module-specific reports, source/roster rechecks, locks, receipt-last publication, independent goldens, current-version reuse and the existing reporter entry point. |

## Completed and closed outcomes

### Repository maintenance

| ID | Kind | Status | Importance | Complexity | Required outcome | Acceptance |
|---|---|---|---:|---:|---|---|
| `COMPRESS-01` | Compression and comprehension | Closed | — | — | Substantially reduce duplicated code and documentation; make retained implementations and explanations easy to follow. | Closed by the user on 2026-09-14 after [PR #169](https://github.com/lab-cats/EMRYS/pull/169) merged at `2ecf7d44`: 42 CS cards completed; CS-05 transferred to `REPORT-ROSTER-01`. The closure record below states the result and its limits. The temporary campaign and backlog were retired after moving unique decisions and evidence to existing owners. Existing reporting, diagnostic, dashboard, optimization and scientific/site work remains with its named owners. No further compression tranche is active or implied. |

The compression campaign ran from 2026-09-02 to 2026-09-14. Against the agreed
`cab77a2610cecbefaaf0fb463fa7ebe1c500767c` baseline, product fell from
**69,223 to 55,862 physical lines**:
**13,361 fewer lines (19.30%)**. The 20% target was **55,378 lines**;
the campaign closed **484 lines short**, by explicit user decision.
The count includes tracked product `.py`, `.R`, `.sh`, `.css`, `.j2` files
and the workflow `Snakefile`, including relocated files. Generated
`renv/activate.R` and the tooling script `restore_r_environment.R` are excluded.

Integration PR #169 preserved all 93 commits from PR #140 and PRs #148–168.
Its separate comparison against pre-integration master
`446802c06ebceee8328a5cb4b542eea9fb2ed398` is:

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
remain. At this September 14 integration checkpoint, dashboard retirement still
required a validated replacement; `DASHBOARD-RETIRE-01` later completed the
caller-complete transition to installed watch with legacy read compatibility.

[Ordinary hosted CI](https://github.com/lab-cats/EMRYS/actions/runs/34857271894)
and [130-pair synthetic E2E](https://github.com/lab-cats/EMRYS/actions/runs/34857300341)
passed at `fdc7cc79a3cf8637bb1c591c95a82020816fe863`; merge
`2ecf7d449188ebd2e6d8b2e64a714ba269e5124b` has the identical source tree,
`6e1c67e3bf74b317e727bcd9c051cdccaa095236`. The closeout recorded completed
source and integration reviews. The September 22 review checked arithmetic,
tree equality and run-level success/head metadata; it did not rerun the count
inventory, reconstruct those reviews or inspect every job/artifact. These are
hosted software and disposable-Slurm results, not institutional-site,
production-data, scientific-review or biological validation.

CI-01, DEV-01, and CLI-VERSION-01 passed the complete ordinary hosted suite in
[run 34306975901](https://github.com/lab-cats/EMRYS/actions/runs/34306975901)
at `b491aac5f198584475ba72de2cfe0894f8be81df`, including Python coverage,
guarded R, managed golden path,
static/wheel, shell, and userspace checks. PR #148 merged through PR #169.

The other implemented outcomes below passed their applicable Python,
guarded-R, managed-golden, and independent-contract checks in
[ordinary hosted CI 34301289787](https://github.com/lab-cats/EMRYS/actions/runs/34301289787)
at `2fb8f5ef5a297f3778fd2dd7a5046eec0ab21fa5`, PR #140's integrated tree.
These source-recorded suite scopes are not independently established by the
later run-metadata check. This closes their hosted software-verification scope;
PR #140 merged through PR #169. It does not establish institutional-site
execution, scientific review, or biological validation.

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

### October 2, 2026 bounded hosted verification

On `6336a6d5aa2ff024b0e6939557135c75c77abd33`, all 14 selected jobs in
[CI 36962111205](https://github.com/lab-cats/EMRYS/actions/runs/36962111205)
finished successfully. GitHub nevertheless records the overall workflow as
**cancelled** during the subsequent push; it is not an overall green-run claim.
The [aggregate job](https://github.com/lab-cats/EMRYS/actions/runs/36962111205/job/110702205438)
verified exact membership of 3,399 tests (3,391 passed, eight declared skips),
25 isolated checks and coverage of 91.0692% lines / 82.8846% branches.

Retained JUnit confirms 37 SCHED-01 cases, 31 public-Make cases and both QUAL-02
fault cases passed without skips. All four shard logs name `/usr/bin/make` and
GNU Make 4.3. Artifacts `11208557533`, `11208741755`, `11208382007` and
`11208416864` are reconciled in the retained local target index
`emrys-ci-36962111205-targeted-junit.json`, SHA-256
`fb88c95b36fa038a7e661d7ad85b41b77fbd3c19d5138a7e92420124898336ab`.
The [guarded-R job](https://github.com/lab-cats/EMRYS/actions/runs/36962111205/job/110698029909)
ran the three Step 08 reference/public-validator fixtures and native Step 09
fixtures. Python reference, numerical-oracle and validator cases also passed.
The [managed-native job](https://github.com/lab-cats/EMRYS/actions/runs/36962111205/job/110698029783)
passed its Run/report, separate borrower and 53 containment cases, including
explicitly required non-skipped native samtools cases.

Independent source comparison shows these owners, tests and CI wiring unchanged
by REPORT-04 at `ab0119d3`; its Step 10/native-v2 and report changes require their
own verification. These observations close the named bounded checks only.
CV-11 institutional acceptance, full runtime closure, shared report acceptance,
SCI-AUDIT-01 and biological interpretation remain separate.
