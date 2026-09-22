# SIZE-01 repository-wide file responsibility audit

This working audit annex belongs to the [EMRYS polish campaign](polish-campaign.md#current-follow-up-scope). The [main findings matrix](backlog_matrix.md#maintainability-and-release) remains the sole authority for SIZE-01 status and acceptance. Observations and candidates here do not authorize implementation, evidence deletion, or a retained-file exception.

## Scope and method

Inventory snapshot: 3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d, descended from the PR #302 head. This inventory covers every tracked, non-test text file at that commit, not just files changed on the integration branch. A file qualifies when it has more than 600 physical lines; a final line without a newline counts. The 38 qualifying files contain 56,985 lines: 15 coordinator Python files, 11 other Python files, two R files, four Markdown files, three dependency locks, one CI workflow, one JSON profile, and one stylesheet.

The tables separate observed responsibility from the next question. A proposed reduction requires a caller-complete review of behavior, protection, evidence, and ownership. No path-specific size exception has been approved. If a file is retained above the limit, record its exact path, reason, explicit user approval, and a retirement condition when the exception is temporary.

This pass used source, contracts, callers, tests, and documentation. It did not run product tests, hosted CI, Slurm, scientific analysis, or report visual review.

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

## First detailed discoveries

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

No reduction in this record is counted as a saving. No test, protection, evidence, or generated lock content is proposed for deletion. Before closing the audit, every retained oversized path needs its own approved exception record or a verified reduction, and the inventory must be rerun against the final revision. At polish-campaign closure, transfer durable findings and approved exceptions to their owners; review retirement of this working annex under the applicable evidence-retention rule.

## Second pass: coordinator caller and evidence boundaries

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
