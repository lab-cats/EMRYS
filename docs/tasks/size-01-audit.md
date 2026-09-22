# SIZE-01 repository-wide file responsibility audit

This working audit annex belongs to the [EMRYS polish campaign](polish-campaign.md#current-follow-up-scope). The [main findings matrix](backlog_matrix.md#maintainability-and-release) remains the sole authority for SIZE-01 status and acceptance. Observations and candidates here do not authorize implementation, evidence deletion, or a retained-file exception.

## Scope and method

Inventory snapshot: 3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d. This inventory covers every tracked, non-test text file at that commit, not just files changed on the integration branch. A file qualifies when it has more than 600 physical lines; a final line without a newline counts. The 38 qualifying files contain 56,985 lines: 15 coordinator Python files, 11 other Python files, two R files, four Markdown files, three dependency locks, one CI workflow, one JSON profile, and one stylesheet.

The tables separate observed responsibility from the next question. A proposed reduction requires a caller-complete review of behavior, protection, evidence, and ownership. No path-specific size exception has been approved. If a file is retained above the limit, record its exact path, reason, explicit user approval, and a retirement condition when the exception is temporary.

The audit reviewed implementation, contracts, callers, tests, and documentation. Its findings are source observations; product tests, hosted CI, Slurm, scientific analysis, and report visual review are separate evidence layers.

## File responsibility matrix

Paths are relative to the repository root. Line counts belong to the snapshot above and must be recounted after edits.

### Run coordinator source

| Path | Lines | Observed responsibility | Reduction or retention question |
|---|---:|---|---|
| src/emrys/orchestration/run_coordinator/_inspection_presentation.py | 1,368 | Watch navigation, admitted observations, stream tails, rendering, and terminal actions. | Determine whether scheduler trace and selected-tail reads can share admitted content without losing their different bounds and checks. |
| src/emrys/orchestration/run_coordinator/_submission_inspection.py | 609 | Associates requests with applications and reads Run application observations. | Check whether its narrow admission boundary is cohesive; a cosmetic trim would not establish reduction. |
| src/emrys/orchestration/run_coordinator/control.py | 3,098 | Coordinates Run planning and execution, reports, stop, inspect, and watch commands. | Trace each command's decision owner and all callers before moving or removing policy. Preserve selection and fresh action admission. |
| src/emrys/orchestration/run_coordinator/dashboard.py | 2,442 | Secure stream cache, scheduler selection, Snakemake parsing, and dashboard layout. | Test whether parsing, stream ownership, and presentation contain caller-complete separable responsibilities. |
| src/emrys/orchestration/run_coordinator/doctor.py | 2,147 | Diagnosis, explicit repair, maintenance locking, and Slurm qualification. | Compare repeated admission with adjacent owners while preserving distinct diagnosis, repair, and site evidence boundaries. |
| src/emrys/orchestration/run_coordinator/inspection.py | 721 | Projects Run status, recovery, and processing from admitted evidence. | Check whether these views are one evidence boundary before proposing retention or consolidation. |
| src/emrys/orchestration/run_coordinator/lifecycle.py | 2,447 | Signals, quiescence, locks, admission, and Attempt finalization. | Map recovery and interruption callers; assess a path-specific exception only after that boundary is established. |
| src/emrys/orchestration/run_coordinator/materialization.py | 1,801 | Builds stage commands and Task graph plans, creates Attempt material, and publishes it. | Separate any repeated planning mechanics only if immutable Run and Attempt identity remain intact. |
| src/emrys/orchestration/run_coordinator/normalization.py | 751 | Admits identity, samples, partitions, and Project inputs. | Verify whether apparent repeated validation occurs at equivalent trust boundaries. |
| src/emrys/orchestration/run_coordinator/onboarding.py | 2,398 | Handles setup, Project Init, manifest preparation, validation, and runtime discovery. | Compare creation and admission helpers across all onboarding callers; preserve create-absent publication. |
| src/emrys/orchestration/run_coordinator/reporting_boundary.py | 1,047 | Handles ledger projection, identity re-admission, and report publication. | Identify any repeated mechanics without collapsing separate admission and publication decisions. |
| src/emrys/orchestration/run_coordinator/resource_policy.py | 657 | Holds symbolic resource policy and numeric Attempt resolution. | Review the ResourcePlan compatibility view and every caller; small accessor deletion alone will not close SIZE-01. |
| src/emrys/orchestration/run_coordinator/slurm_submission.py | 1,133 | Admits requests, stop operations, rosters, batch plans, and exact scheduler identity. | Verify the safety boundary before proposing retention; do not weaken request-to-job binding. |
| src/emrys/orchestration/run_coordinator/synthetic_fixture.py | 816 | Produces deterministic installed fixtures through create-absent input handling. | Check whether generation and safe publication form one owner. |
| src/emrys/orchestration/run_coordinator/task.py | 3,053 | Loads Tasks, contains children, captures streams, publishes native products, and validates receipts. | Audit the complete transaction and recovery path before treating its size as mixed responsibility. |

### Other source

| Path | Lines | Observed responsibility | Reduction or retention question |
|---|---:|---|---|
| src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.R | 1,026 | Produces native scientific-context outputs and receipts. | Review internal repetition while preserving the independent Python validator as a separate oracle. |
| src/emrys/contracts/orchestration/api.py | 791 | Registers contracts, parses strict JSON/YAML, and validates record semantics. | Compare schema and code checks by trust boundary before deriving or deleting either. |
| src/emrys/contracts/orchestration/application_model.py | 1,290 | Defines immutable Analysis, ExecutionPlan, and Run records and pure resource resolution. | Determine whether resource resolution can be simplified without introducing a second plan authority. |
| src/emrys/contracts/scientific_evidence/scientific_context.py | 1,408 | Independently validates Step 10 scientific output, receipts, and reference context. | Preserve independent producer/validator checks; review duplication within this validator only. |
| src/emrys/contracts/scientific_evidence/step08.py | 629 | Validates neutral sample and partition evidence for Step 08. | Map public callers and mutation protections before considering a small reduction or exception. |
| src/emrys/contracts/scientific_evidence/step09.py | 1,352 | Validates Step 09 results, projections, summaries, and mutations. | Keep numerical and provenance checks while searching for genuinely repeated record mechanics. |
| src/emrys/evidence/storage_inventory/qualification.py | 929 | Qualifies direct and two-phase site storage evidence. | Shared helpers exist; verify that further consolidation would not merge distinct evidence claims. |
| src/emrys/libraries/application_logging/handler.py | 658 | Owns durable AttemptLog lifecycle and console projection. | Check whether remaining presentation code belongs beside logging ownership or warrants retention. |
| src/emrys/renv/activate.R | 1,438 | Supplies the R dependency bootstrap used by the established package manager. | Review package-manager ownership; hand trimming or splitting this input is not a valid size fix. |
| src/emrys/reporting/paired_cmh_candidate_ranking_report/candidate_display.py | 624 | Projects selected candidates and significant-table display rows. | Compare the two significant-row traversals and duplicate-ID checks without changing selection semantics. |
| src/emrys/reporting/paired_cmh_candidate_ranking_report/figures.py | 1,250 | Renders Step 09 figures. | Assess repeated palette and legend constants with the Step 10 figure owner; preserve distinct plot behavior. |
| src/emrys/reporting/paired_cmh_candidate_ranking_report/scientific_context_figures.py | 1,083 | Renders Step 10 scientific-context figures. | Review shared presentation constants; do not merge location fields whose order and case differ. |
| src/emrys/reporting/transaction_validation.py | 866 | Validates Run-summary and HTML-report transactions. | Common helpers already exist; keep distinct commit and evidence semantics. |

### Documentation, workflow, configuration, and generated inputs

| Path | Lines | Observed responsibility | Reduction or retention question |
|---|---:|---|---|
| .github/workflows/ci.yml | 1,417 | Defines 13 jobs, selected lanes, inline measurement, and evidence uploads. | Review repeated lane conditions and inline scripts against job identity, tests, gates, and retained artifacts. |
| docs/operations/RUNBOOK.md | 774 | Gives cross-cutting operator procedures. | Compare detailed Init internals with the coordinator contract; keep the usable operator journey and recovery steps. |
| docs/tasks/cluster_verification_backlog.md | 4,107 | Holds delegated acceptance and evidence for 61 CV cards. | Consider a temporary exception tied to verified evidence transfer and campaign retirement; do not trim live acceptance. |
| docs/tasks/polish-campaign.md | 1,084 | Owns repository-wide inventory, exception review, and campaign rationale. | Review historical PR tables and proposal disposition before shortening; keep SIZE-01 authority here. |
| src/emrys/orchestration/run_coordinator/CONTRACT.md | 1,248 | Records exact coordinator behavior across several subowners. | Compare repeated field and path inventories with schemas and owner source under DOCS-01. |
| src/emrys/renv.lock | 2,924 | Records the resolved R package set. | Review declared dependencies through their owner; retention requires its own explicit exception. |
| src/emrys/reporting/styles/run_report.css | 719 | Styles both self-contained HTML views, including print output. | Assess selector/token reduction with browser and print parity; splitting changes resource identity. |
| src/emrys/resources/runtime/pixi.lock | 3,881 | Records the resolved native/R base environment. | Review declared dependencies through their owner; retention requires its own explicit exception. |
| src/emrys/workflow/contracts/local_cmh_v2.json | 712 | Defines the canonical workflow profile, owners, edges, and artifact templates. | Evaluate repeated owner-key lists under SCHEMA-01 and PROFILE-CONTRACT-01 across every consumer. |
| uv.lock | 2,287 | Records the resolved Python package set. | Review declared dependencies through their owner; retention requires its own explicit exception. |

## Cross-owner discoveries

1. **Resource compatibility view.** [ResourcePlan](../../src/emrys/orchestration/run_coordinator/resource_policy.py#L213) presents one policy and one Attempt resolution through forwarding properties. Static source search found no direct production use of its declaration property; allocation is used inside policy_record. Removing those accessors would save only a few lines and leave the file above 600. The next review must trace typed callers and determine whether the compatibility view can be retired as a whole while preserving symbolic Run policy and numeric Attempt resolution.

2. **Figure constants.** The Step 09 and Step 10 figure modules contain the same eight-color pair tuple and legend limit at [figures.py](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/figures.py#L43) and [scientific_context_figures.py](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/scientific_context_figures.py#L48). The latter already imports selected helpers from the former. This is a concrete small consolidation candidate, but it does not bring either file below 600; the two legend decisions and other location fields still need semantic comparison.

3. **Watch stream reads.** [refresh_snapshot](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py#L664) reads scheduler streams for workflow and identity projection, then [read_tail](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py#L371) reads the selected stream as a bounded, sanitized tail. A selected scheduler stream can therefore be read through both paths during one refresh. Those paths have different limits and purposes. Reuse is a hypothesis pending review of stream identity, rotation, bounds, sanitization, and failure behavior; no read is marked safe to remove.

4. **CI measurement is protected code.** The [inline Doctor measurement program](../../.github/workflows/ci.yml#L440) occupies about 191 workflow lines. [test_ci_workflow.py](../../tests/test_ci_workflow.py#L602) extracts and exercises its behavior, including reads, command exit handling, and output failure. Moving the program into a new file would add a maintained path and leave the workflow above 600. Review repeated selected-lane conditions separately while preserving job names, gates, and evidence uploads.

5. **Profile key repetition.** In [local_cmh_v2.json](../../src/emrys/workflow/contracts/local_cmh_v2.json#L5), semantic_owner_keys and required_owner_keys currently equal the 12 owner_tasks machine keys in order. The profile also has 12 direct edges and 57 artifact templates. Equal values do not establish equal meaning. Derivation needs every reader, identity use, and retained-profile rule checked under the existing schema/profile decisions.

6. **Operator and owner documentation.** The [Runbook's Init detail](../operations/RUNBOOK.md#create-a-project-for-your-own-data) overlaps the [coordinator contract's admission detail](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries). A precise owner link may shorten operator prose while retaining paste-ready actions and recovery. The [polish campaign's historical PR tables](polish-campaign.md#existing-capabilities-and-overlapping-work) are another compression candidate, subject to its [disposition and transfer rule](polish-campaign.md#campaign-disposition).

7. **Delegated verification record.** The [cluster backlog](cluster_verification_backlog.md#verified-scope-and-remaining-evidence) remains the acceptance and evidence owner for its CV cards. Its stated retirement condition requires exact evidence-bearing records and lasting decisions to reach durable homes first. A temporary size exception is a candidate; immediate deletion would risk losing active acceptance or retained evidence.

## Cross-surface reduction questions

| Surface | Concrete review opportunity | Boundary to preserve |
|---|---|---|
| Product code | ResourcePlan forwarding and the two reporting palette definitions. | Complete callers, Run/Attempt meaning, report behavior. |
| Tests and protection | The extracted CI measurement driver tests and large coordinator fixtures under tests/; map repeated setup and unique failures under ASSURANCE-01. | Independent oracles, boundary faults, and existing gate evidence. Test files are outside the SIZE-01 threshold. |
| Scripts and tooling | Inline Doctor measurement and repeated selected-lane conditions in ci.yml. | Job identity, dispatch, uploads, and exact measurement semantics. |
| Schema and configuration | Equal owner-key lists in local_cmh_v2.json; dependency declarations that generate the three distinct locks. | Profile identity, consumers, package-manager ownership, and reproducibility. |
| Documentation | Init detail across Runbook and coordinator contract; campaign chronology. | Operator usability, owner-local exact behavior, and retained evidence. |
| Mutable state | Separate scheduler trace caches and selected-tail state in watch. | Stream rotation, bounded reads, sanitized output, and read-only inspection. |


## Coordinator command, recovery, and watch boundaries

These path reviews inspect committed source and direct tests at the inventory snapshot. Reading a test establishes the intended protection, not that the test passed on this audit branch.

### control.py

[Run and Resume share admission](../../src/emrys/orchestration/run_coordinator/control.py#L1962) rather than keeping separate command implementations. Watch reuses Inspect's parser and handler, and [Stop delegates its plan](../../src/emrys/orchestration/run_coordinator/control.py#L2405) to the submission owner. Watch actions call fresh public handlers with exact selectors rather than acting on a stale display observation. Run selection and submission-request selection make distinct decisions, with [direct selector tests](../../tests/orchestration/run_coordinator/test_run_locator.py#L104). Moving handlers into another file would redistribute lines without an established net reduction. Next proof: inventory every remaining command branch and its direct tests for duplicated equivalent policy before proposing retention or a caller-complete deletion.

### task.py and lifecycle.py

The Task worker imports the existing [process-group quiescer](../../src/emrys/orchestration/run_coordinator/lifecycle.py#L927), so that behavior has already been consolidated across its two callers. Task also owns descendant reaping, stream capture, and native publication; Lifecycle owns the Snakemake Attempt and receipt transaction. [Task failure tests](../../tests/orchestration/run_coordinator/test_task.py#L934) and [Lifecycle recovery tests](../../tests/orchestration/run_coordinator/test_lifecycle.py#L868) protect different failure boundaries. Extracting the shared quiescer merely to shorten either file would add a product file without demonstrated reduction. Next proof: compare the remaining child and Attempt cleanup branches for equivalent inputs and outcomes, including partial publication and lock preservation.

### onboarding.py

Guided Project creation and the separate manifest-draft command already use the same [manifest drafting helper](../../src/emrys/orchestration/run_coordinator/onboarding.py#L1073). Publication also uses the create-absent tree owner. [Onboarding tests](../../tests/orchestration/run_coordinator/test_onboarding.py#L1416) cover independent manifest drafts and runtime reuse. Setup, Project creation, validation, and runtime selection cross different mutation boundaries. The file warrants navigation review, but a split alone would not satisfy SIZE-01. Next proof: trace each public route and its create, preview, and interruption behavior before judging any route redundant.

### doctor.py

[Read-only diagnosis](../../src/emrys/orchestration/run_coordinator/doctor.py#L526), repair planning, fresh re-admission, and storage work have different mutation authority. The timing collector is an explicit observation contract and cannot direct repair. [Doctor tests](../../tests/orchestration/run_coordinator/test_doctor.py#L972) protect no-write preview, timing limits, fresh re-admission, and preserved evidence claims. No safe deletion is established by file size. Next proof: compare the complete diagnosis and repair call graph with onboarding and site qualification for truly equivalent decisions, rather than merging checks across trust boundaries.

### _inspection_presentation.py

The [full-history trace pass](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py#L664) and [bounded selected tail](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py#L371) can observe one scheduler stream twice per refresh. [Dashboard stream tests](../../tests/orchestration/run_coordinator/test_dashboard.py#L528) and [watch tail tests](../../tests/orchestration/run_coordinator/test_inspection_presentation.py#L589) protect different history, byte-bound, sanitization, and generation behavior. One admitted observation with two projections is a possible mutable-state and I/O reduction, not yet a proven code reduction. Next proof: establish identical path admission, rotation, timing, diagnostics, and selected-tail behavior before changing cache ownership.

## Scientific, reporting, and evidence boundaries

These findings are source and test inspections at the inventory snapshot. They neither change scientific meaning nor establish runtime or biological proof.

### scientific_context_projection.R and scientific_context.py

The Step 10 R producer repeats the exact safe-ID and SHA-256 argument checks already present in [Step 09's R common code](../../src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_common.R#L108). Step 10 already sources the neutral [input contract library](../../src/emrys/libraries/input_contract.R); a caller-complete move of those two small helpers there is a plausible net reduction after checking diagnostics and all R callers. It would not take the producer below 600 lines. The producer's Fisher calculation and the [Python scientific-context rederivation](../../src/emrys/contracts/scientific_evidence/scientific_context.py#L481) are independent across a producer/validator trust boundary and must stay separate. [Contract mutation tests](../../tests/contracts/scientific_evidence/test_scientific_context.py#L82) and [real-R determinism tests](../../tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/test_real_r_projection.py#L287) protect different evidence levels; their presence does not prove they ran here.

### step09.py

[Intrinsic streaming projection validation](../../src/emrys/contracts/scientific_evidence/step09.py#L665) deliberately omits upstream Step 08 identity, paired-sample CMH semantics, global BH reconciliation, and publication state. Reporting calls that intrinsic route, while the analysis validator calls [full result admission](../../src/emrys/contracts/scientific_evidence/step09.py#L804), summary validation, and semantic validation. [Direct contract tests](../../tests/contracts/scientific_evidence/test_step09.py#L233) cover streaming and mutation cases. These are distinct validation layers, so moving them to separate files would mostly relocate code. Next proof: compare their shared TSV mechanics with the neutral TSV reader without weakening either layer's diagnostics or bounded-memory behavior.

### figures.py and scientific_context_figures.py

Both renderers use the identical eight-color pair palette and legend limit, and both select colors by pair index. Step 10 already imports renderer helpers from [Step 09 figures](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/scientific_context_figures.py#L20). Sharing the two constants through that existing relationship is a plausible roughly ten-line product reduction with no new file. [Figure tests](../../tests/reporting/test_figures.py#L402) protect selected panels and paired profiles. This candidate does not settle the files' size exceptions or make their remaining plot decisions identical.

### transaction_validation.py

The owner already shares snapshot and residue checks, while [report validation](../../src/emrys/reporting/transaction_validation.py#L479) and [Run-summary validation](../../src/emrys/reporting/transaction_validation.py#L625) have different output and receipt transactions. [Mutation and race tests](../../tests/reporting/test_transaction_validation.py#L424) protect their boundaries. A split would change location, not reduce maintained behavior. Next proof: inspect repeated operations at equivalent publication boundaries across both callers; retain separate scientific-source and report admission unless equivalence is shown.

### qualification.py

The storage owner shares one [root probe](../../src/emrys/evidence/storage_inventory/qualification.py#L414), then conducts direct qualification or staged compute and final qualification with separate receipt and admission rules. [Storage tests](../../tests/evidence/storage_inventory/test_storage_inventory.py#L89) cover both modes and incomplete or failed publication. A path-specific exception is a candidate if no measured reduction preserves both authorities and recovery behavior. Local synthetic coverage is not institutional cross-node qualification.

### renv/activate.R

The bundled [renv autoloader](../../src/emrys/renv/activate.R#L5) declares renv version 1.2.3 and its MD5. An earlier product-code campaign excluded generated activate.R from its count; SIZE-01's non-test rule still includes this path. The [shell test](../../tests/shell/test_local_r_environment.sh#L64) checks presence and later uses a stub, so it does not prove the bundled bootstrap itself. Before proposing a generated-file exception, verify upstream provenance, exact selected-environment behavior, and the explicit repair route. Hand editing the generated autoloader is not a line-count reduction.

## Documentation, workflow, configuration, and generated inputs

### ci.yml

[Ordinary and selected CI lanes](../../.github/workflows/ci.yml#L1) coexist in one workflow. Selected synthetic-lane truth recurs in the job condition, seed environment, and final gate, while setup already shares YAML anchors. [Workflow tests](../../tests/test_ci_workflow.py#L72) pin selection semantics and [evidence-upload tests](../../tests/test_ci_workflow.py#L785) pin retained artifacts. A shorter selector expression is a candidate only if job names, required checks, selected-lane behavior, and failure artifacts remain equivalent. Adding a selector job or splitting workflows could increase maintained surface. The 191-line Doctor measurement program is exercised by extracted-driver tests; moving it to a new file would not itself resolve the workflow's size.

### local_cmh_v2.json

The profile repeats its 12 owner keys in semantic, task, and required-owner lists. [Contract validation](../../src/emrys/contracts/orchestration/api.py#L355) currently enforces equality. The 57 base artifact templates are the canonical workflow inventory; [profile tests](../../tests/orchestration/run_coordinator/test_profile.py#L303) pin the composed roster and native-result semantics. Deriving one repeated list is a concrete schema question, but removes fewer than the 112 lines needed to reach 600 and can change profile and immutable Run identity. It belongs to a separately approved SCHEMA-01 and PROFILE-CONTRACT-01 transition after all consumers and retained records are reviewed.

### run_report.css

One [stylesheet](../../src/emrys/reporting/styles/run_report.css#L553) is embedded in both HTML views. The print-specific candidate group and image rules have distinct media behavior from their screen counterparts. The [report receipt](../../src/emrys/reporting/_run_report/receipt.py#L100) binds the exact stylesheet path and hash; [report tests](../../tests/reporting/test_report.py#L695) check print-source tokens and embedding, not visual parity. Splitting or minifying for a line count would alter asset wiring or receipt identity. A real rule consolidation needs screen and print rendering, receipt validation, and installed-wheel review before a size disposition.

### uv.lock, pixi.lock, and renv.lock

These are separate package-manager resolutions for Python, native/R base, and R packages. Doctor reads and stages exact [Pixi lock bytes](../../src/emrys/orchestration/run_coordinator/doctor.py#L905); a [wheel test](../../tests/test_package_distribution.py#L250) parses the Python lock; [CI](../../.github/workflows/ci.yml#L1223) retains all three with runtime evidence. Each retained path requires its own reason and explicit exception approval. Dependency pruning, if useful, belongs to declared dependency owners and manager regeneration with exact runtime and CI checks. Hand editing, splitting, or deleting lock evidence is not authorized by SIZE-01.

### RUNBOOK.md, CONTRACT.md, and campaign records

The [Runbook's Project creation section](../operations/RUNBOOK.md#create-a-project-for-your-own-data) includes hashing and filesystem identity internals also explained in the coordinator [publication contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries). DOCS-01 can retain the operator choices, confirmation, and recovery cue while linking exact implementation guarantees to the owner. The [polish campaign's history](polish-campaign.md#existing-capabilities-and-overlapping-work) needs proposal disposition before shortening, and the [cluster backlog](cluster_verification_backlog.md#verified-scope-and-remaining-evidence) owns live CV acceptance until evidence transfer. Both are possible temporary exceptions with explicit retirement triggers, not immediate deletion candidates. Exact evidence deletion requires its own approval and commit.

## Coordinator planning, admission, and submission owners

### materialization.py

[Run and Attempt planning](../../src/emrys/orchestration/run_coordinator/materialization.py#L175) builds immutable identity, step commands, Task records, and create-exclusive publication. Its fixed-step and typed-module planners emit similar record shapes but use different inputs and producers. Artifact expansion already delegates to the inventory owner, and [Run binding is committed last](../../src/emrys/orchestration/run_coordinator/materialization.py#L1664) while incomplete residue is quarantined. [Plan and interruption tests](../../tests/orchestration/run_coordinator/test_materialization.py#L1470) protect direct/Slurm equality and partial publication. Replacing the command switch with another registry needs all-step argv and provenance parity plus a net-line comparison; relocation alone is not reduction.

### normalization.py

The sample manifest is parsed by [_normalize_samples](../../src/emrys/orchestration/run_coordinator/normalization.py#L345), its returned table is discarded by one admission path, and the same bytes are parsed again when projecting a selected subset. Retaining the parsed table could avoid one pass, but adds state and may save little product code. [Normalization tests](../../tests/orchestration/run_coordinator/test_normalization.py#L55) protect prepared input, Project-root, and snapshot bindings. The large-input hashing path is already shared with guided Init; ordinary admission intentionally does not parse FASTQ records. Next proof: compare exact subset bytes and interruption behavior before changing the prepared admission shape.

### inspection.py

[Inspection](../../src/emrys/orchestration/run_coordinator/inspection.py#L24) delegates immutable authority, Attempt-chain, Task, and report evidence to existing owners, then derives integrity, Results, reporting, and recovery states for read-only consumers. Prepared-finalization preview compares ordinary and prospective inspections; processing-source admission requires successful Step 00–06 evidence and subset compatibility. [Lifecycle and materialization tests](../../tests/orchestration/run_coordinator/test_lifecycle.py#L2056) cover receipt drift and source compatibility. No duplicate state authority was established. A path exception remains a proposal until approved.

### reporting_boundary.py

[reporting_kinds](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py#L214) and [inspect_reporting_ledger](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py#L251) scan the ledger roster in sequence. Combining them might remove a small repeated scan, but the second can observe a newly inserted entry and reports a different blocker; publication also calls reporting_kinds. [Unexpected-state tests](../../tests/orchestration/run_coordinator/test_reporting_boundary.py#L383) and [publication re-admission tests](../../tests/orchestration/run_coordinator/test_reporting_boundary.py#L836) protect those decisions. This is a low-confidence reduction candidate, not permission to remove fresh identity checks.

### slurm_submission.py

Submit and Stop already share [descriptor-pinned transcript handling](../../src/emrys/orchestration/run_coordinator/slurm_submission.py#L905), while their mutations, timeout, and at-most-once rules differ. The v4 writer retains v1–v3 request observation because historical records remain readable under the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#run-root-contract). [Submission tests](../../tests/orchestration/run_coordinator/test_slurm_submission.py#L422) cover both operation families. Retiring historical readers needs a separate retained-record decision; SIZE-01 alone does not authorize it.

### _submission_inspection.py

Stable snapshots and candidate Run/Attempt admission are already shared. [Selected-request inspection](../../src/emrys/orchestration/run_coordinator/_submission_inspection.py#L417) rechecks a closed request/response and binds one tokenized log; [historical Run inspection](../../src/emrys/orchestration/run_coordinator/_submission_inspection.py#L543) scans pending and Run scopes and reports incomplete scans. [Change-detection tests](../../tests/orchestration/run_coordinator/test_submission_inspection.py#L577) prevent reuse of an earlier observation as if it were fresh. The nine-line excess does not justify removing that evidence distinction.

### resource_policy.py

[ResourcePlan](../../src/emrys/orchestration/run_coordinator/resource_policy.py#L213) forwards effective numeric fields used by Materialization, Lifecycle, and the Snakefile; its record binds symbolic Run policy, numeric Attempt resolution, allocation, and source digests. Persisted policy is re-resolved and compared on admission, and CLI override fields already drive one parsing table. [Resource tests](../../tests/orchestration/run_coordinator/test_resource_policy.py#L85) pin a stable Run declaration across different allocations. The apparently unused declaration accessor is a narrow cleanup candidate, not a meaningful SIZE-01 reduction or grounds to collapse symbolic and numeric policy.

### synthetic_fixture.py

The [fixture owner](../../src/emrys/orchestration/run_coordinator/synthetic_fixture.py#L62) generates deterministic smoke and production-like inputs, metadata, and checksums for the public synthetic Init command. It already shares Project YAML, validation, and create-absent publication with onboarding. [Onboarding fixtures tests](../../tests/orchestration/run_coordinator/test_onboarding.py#L1957) pin bytes and neutral-pair geometry, while the real-tool E2E selects both profiles. Moving this module under tests would break the installed command; its metadata are expectations, not scientific proof. A profile retirement would require separate public-contract authority.

### dashboard.py

The [dashboard owner](../../src/emrys/orchestration/run_coordinator/dashboard.py#L249) contains descriptor-pinned stream caching, exact scheduler/log selection, diagnostic trace parsing, and terminal layout. Watch consumes all of these; moving sections into new files would improve navigation without reducing maintained behavior. The strongest cross-file candidate remains one admitted stream observation with full-history and bounded-tail projections. [Stream tests](../../tests/orchestration/run_coordinator/test_dashboard.py#L528) protect generation resets, path and UID admission, timeouts, and diagnostics; watch tests protect bounded escaped display. A smaller candidate is the resource fallback text stored in STAGES: for 11 known stage keys, the only production caller passes it to [stage_resource_text](../../src/emrys/orchestration/run_coordinator/dashboard.py#L903), which returns observed text or “not yet reported” without displaying that fallback. Four other known keys can still use it. Removing dormant strings needs a full consumer check and would not bring this file below 600. Scheduler ambiguity and log-derived completion claims remain separate from admitted Run inspection.

## Contracts, logging, and candidate display owners

### api.py

The [public validator](../../src/emrys/contracts/orchestration/api.py#L695) accepts a profile argument. Its cached route serializes and decodes that profile and includes it in the cache key, but the current uncached semantic validator does not read the argument. Removing only the unused internal decode and cache dimension is a concrete small candidate; the public signature remains used by coordinator callers. The review must preserve strict JSON error behavior, cache correctness, and exact validation of every record kind. This is not yet a caller-complete implementation decision and would not by itself take the file below 600.

### application_model.py

The [application model](../../src/emrys/contracts/orchestration/application_model.py#L173) binds immutable Analysis, ExecutionPlan, and Run records, processing compatibility, pure resource resolution, and successor authority. Its plan semantics enforce ordering, graph edges, and predecessor closure. [Contract tests](../../tests/contracts/orchestration/test_application_model_contracts.py#L623) exercise successor and resource drift. These duties share the immutable plan boundary; splitting them would relocate code. Next proof: compare resource-resolution callers with resource_policy.py for equivalent decisions without introducing a second Run authority.

### scientific_context.py and step09.py streaming mechanics

The Step 10 [_stream_tsv](../../src/emrys/contracts/scientific_evidence/scientific_context.py#L292) and Step 09 [_stream_projection_tsv](../../src/emrys/contracts/scientific_evidence/step09.py#L582) each implement strict bounded TSV streaming and nearly the same row-width loop. The existing neutral [TSV library](../../src/emrys/libraries/validation/tsv.py#L58) is the first possible owner for common lexing. Any shared primitive must preserve Step 09 variable-header checks, Step 10 fixed headers, error precedence, diagnostics, and bounded memory. [Step 09 streaming tests](../../tests/contracts/scientific_evidence/test_step09.py#L387) and [Step 10 mutation tests](../../tests/contracts/scientific_evidence/test_scientific_context.py#L188) are relevant parity protections. The independent Step 10 scientific rederivation and R producer remain separate.

### step08.py

[Path-based and admitted-byte manifest entrypoints](../../src/emrys/contracts/scientific_evidence/step08.py#L309) already share semantic table validators. Normalization, onboarding, and the Step 08 output validator use those distinct admission boundaries. [API fingerprint and byte-admission tests](../../tests/contracts/scientific_evidence/test_step08.py#L228) constrain removal. No caller-complete net reduction surfaced in this pass; the 29 lines above the threshold warrant a retention decision, not arbitrary trimming. Fixture checks are not cluster or scientific proof.

### handler.py

The [AttemptLog](../../src/emrys/libraries/application_logging/handler.py#L131) lifecycle methods converge on [_transition](../../src/emrys/libraries/application_logging/handler.py#L414), which serializes durable write, sync, state change, and closure. Record writing keeps durable JSON and console projection distinct. [Handler tests](../../tests/libraries/application_logging/test_handler.py#L73) cover ordering, synchronization, and failures; installed smoke exercises another layer. No duplicate state machine surfaced. Retention is more defensible than a mechanical split pending an exact path-specific exception decision.

### candidate_display.py

The [candidate display owner](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/candidate_display.py#L548) builds one immutable roster for the provider, HTML, and two figure modules. Its [fallback Step 09 scan](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/candidate_display.py#L206) and [Step 10-selected scan](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/candidate_display.py#L259) repeat snapshot and duplicate-ID checks but make different ranking and membership decisions. Sharing only the equivalent traversal mechanics may reduce code; preserve roster, fallback, and snapshot behavior covered by [display tests](../../tests/reporting/test_candidate_display.py#L284). A small helper that leaves parallel scans or adds surface without net reduction would not close SIZE-01.

## Audit decision boundary

No reduction in this record is counted as a saving. No test, protection, evidence, or generated lock content is proposed for deletion. Before closing the audit, every retained oversized path needs its own approved exception record or a verified reduction, and the inventory must be rerun against the final revision. At polish-campaign closure, transfer durable findings and approved exceptions to their owners; review retirement of this working annex under the applicable evidence-retention rule.
