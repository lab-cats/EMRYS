# Cluster verification backlog

This is the delegated card-status and acceptance authority for
`CLUSTER-VERIFY-01` in the [main findings matrix](backlog_matrix.md), covering
`CV-01` through `CV-27`, the subsequently recorded `CV-U01` through `CV-U33`,
and `CV-UX-01`.
The [campaign](cluster_verification_campaign.md) defines scope, evidence
E01–E12, delivery boundaries, and closure. Created **2026-09-14** from the
operator's combined failures, usability findings, and design proposals.

P0–P3 preserve the supplied priorities. All cards began **Open**: prior fixes
and observed successes are context, not closure of these remaining outcomes.
Use the main matrix's status meanings. Recording a card accepts the finding
for tracking; it does not authorize a new command, recovery rule, installation,
cluster action, evidence promotion, or product-growth exception.

New maintenance, setup and source follow-ups live in the enduring
[main backlog](backlog_matrix.md#maintainability-and-release). In particular,
`SCHED-USAGE-01` and `SUBMISSION-PREVIEW-01` own the new source/policy acceptance
referenced below; CV-U33 and CV-22 keep their campaign status and institutional
acceptance here. The [closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
records required dispositions before this temporary document can retire.

The approved [remaining delivery scope](cluster_verification_campaign.md#remaining-delivery-scope)
includes `INIT-01` through `INIT-03` and the focused Quickstart corrections.
CV-06, CV-U07, CV-U08 and CV-U18 are **Open** for those source/documentation
prerequisites before their remaining novice acceptance can run. Their new
implementation acceptance lives in the main backlog; prior selected replay and
manual-selector behavior does not complete the newly approved requirements.
CV-U06's accounting exception is approved independently of its pending site proof.

## Verified scope and remaining evidence

The combined standard suite passed for product
`917ad7b210402dc3d17c32849d1f7bc028a08e60`
([CI 34983415214](https://github.com/lab-cats/EMRYS/actions/runs/34983415214)):
14 jobs succeeded, including all Python 3.14 shards and coverage policy, Python
3.11 compatibility, public/PTY regressions, and the managed golden path. Four
configured lanes were skipped. This includes Run-log discovery, invocation
counters, offline correction, complete dashboard functional parity, recorded
startup outcomes and Doctor setup/queue-time guidance. It supersedes their
earlier local-environment notes that application or PTY checks still required CI.
Later product changes require their own applicable checks.

CV-03's scheduler failure-phase acceptance additionally passed all 14 standard
jobs, with four configured skips, at
`45c63ca749e3ee73029cc111f79b8016ce9c772e`
([CI 34991470527](https://github.com/lab-cats/EMRYS/actions/runs/34991470527)).
This includes the public Doctor and selected-request accounting cases below.

PR [#266](https://github.com/lab-cats/EMRYS/pull/266) implementation checkpoint
`08d790a8e22edc609be0d4994fe757bbaec65ead` contains the later approved CLI,
onboarding, resource-policy, monitoring, dashboard, runtime-reuse and timeout
slices recorded below, including the allocation-aware all-stage policy merged
from PR [#271](https://github.com/lab-cats/EMRYS/pull/271). Its
[standard CI](https://github.com/lab-cats/EMRYS/actions/runs/35232897882)
passed all 14 active jobs; four configured manual/nightly lanes were skipped.
This is hosted software evidence. It is not a fresh Viking installation, an
institutional scheduler/filesystem exercise, a novice walkthrough, a new
performance benchmark, scientific review or biological validation.

The covered journey includes donor science/reporting and borrower runtime
selection/verification, actual Snakemake startup, real-backend/native-fixture
cancellation, and public inspection around real report producers. Scientific
owner doubles, simulated scheduler metadata and actual local child processes
retain their stated limits. Standard CI is neither the separately selected
real-Slurm lane nor an institutional walkthrough.

| Remaining acceptance | Current owner and required work or evidence |
| --- | --- |
| Source and documentation follow-ups | CV-U33 and CV-22 are **Open** pending `SCHED-USAGE-01` and `SUBMISSION-PREVIEW-01` in the main matrix; site evidence alone cannot close them. `VIKING-POLICY-01` and `CV-DOCS-01` own the remaining guidance/wording corrections. |
| Recently implemented outcomes awaiting verification | CV-10's prepared-finalization `resume` path and CV-18's active-native-task stop outcome are **Verification pending**. Their exact hosted checks and institutional cancellation journeys remain unverified; site execution alone cannot substitute for the hosted checks, and neither status claims a reproduced E09 cause. CV-10's equal-byte recycled-inode ownership limit is an accepted residual risk in a trusted operator-controlled workspace, not a proven defense. |
| Novice setup, qualification, resource selection and report access | CV-02/04/06/07/09/11/13/14/17/19/22/27 and CV-U28: exercise the maintained RUNBOOK on one exact installed revision; retain selected profile/runtime, resolved allocation-aware policy and report identities. Visual review is separate. |
| Scheduler, monitoring, cancellation and reuse at Viking | CV-01/03/08/15/16/18/20 and `SITE-PARITY-01`: retain exact request/Run/Attempt bindings, cross-node observations, queued/preparation/reconnect behavior and two-Project compute accessibility. |
| Historical unexplained failures | CV-12/E01 and CV-21/E06 remain unexplained historical observations whose causal reconstruction is not an acceptance requirement. CV-21 now needs only ordinary institutional execution of current reporting/inspection behavior. CV-10/E09 retains its separate current reconciliation requirement; newer successful checks cannot identify that cause. |
| Postentry Task retry and finalization | CV-10: current-version closed-abort retry has hosted acceptance evidence. The prepared-finalization path through `resume` is implemented and **Verification pending** for its exact hosted CI and institutional cancellation journey. The owner accepted the equal-byte recycled-inode residual limitation for a trusted operator-controlled workspace; existing blocked receipts and missing prepared evidence remain ineligible. |
| Doctor operation | CV-26 is Completed for exact pre-storage readmission, storage finalization and one final full diagnosis after removing the redundant intervening head diagnosis. Exact implementation CI passed; no Viking timing or speedup claim is required. Future measured tuning remains independently owned by the optimization campaign. |
| Optional interface and retirement | CV-23 keeps cleanup Deferred; CV-24 retains explicit new-analysis selection in the CLI; `DASHBOARD-RETIRE-01` owns institutional replacement validation and coordinated standalone entry-point/caller/name retirement. |

All card acceptance below remains authoritative. No institutional execution,
active-installation update, destructive cleanup, report visual review or
actual-data completion was performed by this development stack. E12 still has
no supplied terminal scientific/reporting evidence.

## Priority index

| ID | Priority | Status | Outcome |
| --- | --- | --- | --- |
| [CV-01](#cv-01-managed-golden-path-coverage) | P0 | Verification pending | Managed golden path covers the cluster-discovered cases. |
| [CV-02](#cv-02-individual-qualification-diagnostics) | P0 | Verification pending | Retain and surface each failed qualification check. |
| [CV-03](#cv-03-scheduler-and-execution-failure-messages) | P0 | Verification pending | Separate submission, queue, execution, and finalization failures. |
| [CV-04](#cv-04-workflow-startup-readiness) | P0 | Verification pending | Readiness exercises minimal actual Snakemake startup. |
| [CV-05](#cv-05-reuse-versus-repeated-repair-work) | P0 | Completed | Explain reused state, repeated checks, and new repair work. |
| [CV-06](#cv-06-actual-data-onboarding) | P0 | Open | Provide a novice actual-data setup path. |
| [CV-07](#cv-07-site-and-workload-profile-selection) | P0 | Verification pending | Replace manual Viking resource-profile construction. |
| [CV-08](#cv-08-compatible-runtime-reuse) | P0 | Verification pending | Reuse an existing compatible managed runtime across Projects. |
| [CV-09](#cv-09-qualification-scope-and-placement) | P0 | Verification pending | Explain and enforce the qualified execution environment. |
| [CV-10](#cv-10-external-cancellation-and-recovery) | P0 | Verification pending | Recover safely from externally cancelled jobs when possible. |
| [CV-11](#cv-11-resource-profile-compatibility) | P0 | Verification pending | Detect and explain resource profiles that cannot fit a node. |
| [CV-12](#cv-12-unexplained-initial-runtime-qualification-failure) | P0 | Discard | Establish the original runtime-qualification failure's cause. |
| [CV-13](#cv-13-expected-setup-versus-blockers) | P1 | Verification pending | Distinguish expected initial setup needs from failures. |
| [CV-14](#cv-14-project-directory-layout) | P1 | Verification pending | Supply the tracked Projects home inside the source checkout. |
| [CV-15](#cv-15-cross-node-active-run-status) | P1 | Verification pending | Show remote active state without implying proven corruption. |
| [CV-16](#cv-16-monitoring-dashboard) | P1 | Verification pending | Restore an integrated view of scheduler, progress, and logs. |
| [CV-17](#cv-17-project-creation-progress) | P1 | Verification pending | Explain lengthy input validation during Project creation. |
| [CV-18](#cv-18-safe-emrys-stop) | P1 | Verification pending | Provide an operator stop action with safe recovery semantics. |
| [CV-19](#cv-19-verification-and-repair-vocabulary) | P1 | Verification pending | Name verification-only work accurately. |
| [CV-20](#cv-20-submission-state-before-run-creation) | P1 | Verification pending | Show queued and preparing jobs before a Run exists. |
| [CV-21](#cv-21-reporting-in-progress-and-visibility) | P1 | Verification pending | Distinguish unfinished report publication from failed reporting. |
| [CV-22](#cv-22-complete-submission-preview) | P1 | Open | Reconcile compact resource disclosure before approval. |
| [CV-23](#cv-23-safe-project-or-artifact-cleanup) | P2 | Deferred | Decide and scope safe cleanup of unused owned state. |
| [CV-24](#cv-24-run-center-actions) | P2 | Completed | Explore a dashboard that invokes supported CLI operations. |
| [CV-25](#cv-25-log-discovery-and-readable-output) | P2 | Completed | Find the correct logs without memorizing scheduler IDs. |
| [CV-26](#cv-26-repeated-doctor-input-reads) | P2 | Completed | Remove one redundant full head diagnosis without weakening final readiness. |
| [CV-27](#cv-27-terminal-only-report-access) | P3 | Verification pending | Retrieve portable reports from a terminal-based workflow. |

## Operator findings matrix — 2026-09-15

Recorded from the operator's latest Viking/Quickstart findings and requirements.
This separate matrix belongs to this backlog; it preserves the new observations
without changing the original CV card statuses. Findings were initially **Open**
and unprioritized; the rows below track subsequent approved work and advance
only with their own implementation and verification evidence. Earlier software
acceptance does not close these findings.
Reports below have not been independently reproduced as part of recording them;
they are not established root causes or completed fixes. Proposed commands,
flags and future directions remain identified as such. This records the findings
only, without selecting implementation work or approving new interfaces.

The index links to the detailed records below. Operator quotations preserve the
reported experience; requested outcomes preserve the instructions given in this
discussion. Open questions are not filled with inferred implementation decisions.

| ID | Finding | Status |
| --- | --- | --- |
| [CV-U01](#cv-u01-cli-color-and-readability) | CLI color, readability and Inspect interpretation | Verification pending |
| [CV-U02](#cv-u02-default-cli-verbosity) | Minimal default output, optional detail | Verification pending |
| [CV-U03](#cv-u03-init-and-validate-summaries) | Init and Validate summaries | Verification pending |
| [CV-U04](#cv-u04-doctor-presentation) | Doctor categories and progress | Verification pending |
| [CV-U05](#cv-u05-doctor-first-run-expectations) | Doctor setup notice: 5–25 minutes | Verification pending |
| [CV-U06](#cv-u06-available-resources) | Use all allocated workflow CPUs and memory | Verification pending |
| [CV-U07](#cv-u07-projects-directory) | Automatic Projects-directory creation inside the repository | Open |
| [CV-U08](#cv-u08-quickstart-scope-and-language) | One complete, plain-English Viking/PUM1 Quickstart | Open |
| [CV-U09](#cv-u09-synthetic-project-explanation) | Explain the synthetic-project step | Verification pending |
| [CV-U10](#cv-u10-unnecessary-quickstart-command) | Remove unnecessary Git command | Completed |
| [CV-U11](#cv-u11-paste-ready-quickstart-commands) | Clarify paste-ready commands and supplied values | Verification pending |
| [CV-U12](#cv-u12-duplicate-submission-warning) | Warn before accidental duplicate submission | Verification pending |
| [CV-U13](#cv-u13-watching-progress) | Quickstart dashboard instructions and watch command | Verification pending |
| [CV-U14](#cv-u14-dashboard-logs) | Friendly, colored dashboard logs | Verification pending |
| [CV-U15](#cv-u15-dashboard-action-language) | Unclear “Verify/associate again” action | Verification pending |
| [CV-U16](#cv-u16-dashboard-scrolling) | Keyboard scrolling, no mouse scrolling | Verification pending |
| [CV-U17](#cv-u17-completion-communication) | Announce completion and correct stale pending steps | Verification pending |
| [CV-U18](#cv-u18-interactive-input-list-creation) | Guided creation of input lists | Open |
| [CV-U19](#cv-u19-long-term-interactive-cli) | Interactive setup and Run by default | Deferred |
| [CV-U20](#cv-u20-complete-viking-values-in-quickstart) | Supply expected Viking values inline | Verification pending |
| [CV-U21](#cv-u21-technical-parameter-assistance) | Determine technical parameters for users | Verification pending |
| [CV-U22](#cv-u22-smoke-project-tool-reuse) | Reuse smoke-project tools in the normal journey | Verification pending |
| [CV-U23](#cv-u23-repair-restriction-when-sharing-tools) | Explain and resolve the permanent repair restriction | Verification pending |
| [CV-U24](#cv-u24-persistent-cli-defaults) | Save site and other repeated CLI values | Verification pending |
| [CV-U25](#cv-u25-repeated-fastq-hashing-during-init) | One full FASTQ hashing pass across preview and creation | Verification pending |
| [CV-U26](#cv-u26-manifests-inside-the-project) | Keep manifests inside their Project directory | Verification pending |
| [CV-U27](#cv-u27-tested-smoke-to-real-resource-guidance) | Tested workload profile, Doctor checks and exact submission | Verification pending |
| [CV-U28](#cv-u28-allocation-aware-resource-policy-and-historical-provenance) | Make allocation-aware resource policy authoritative; retain fixed-policy history as provenance | Verification pending |
| [CV-U29](#cv-u29-early-inspect-and-dashboard-feedback) | Show useful information before monitoring fully populates | Verification pending |
| [CV-U30](#cv-u30-dashboard-color-and-pane-layout) | Restore dashboard colors and readable pane layout | Verification pending |
| [CV-U31](#cv-u31-dashboard-automatic-run-selection) | Select the current Run without parameters; record lost functionality | Verification pending |
| [CV-U32](#cv-u32-dashboard-independent-of-working-directory) | Open the dashboard from outside the Project directory | Verification pending |
| [CV-U33](#cv-u33-dashboard-resource-usage) | Restore resource-usage display; keep future wall-time tuning separate | Open |

### September 17 adversarial implementation audit

A read-only audit of the clean `codex/cv-u-integration-2` target at
`10f0bc9239ba879e4885fceb80a259f7356e2af0` compared each card's full requested
outcome with its current callers, tests, operator documentation and retained
evidence. Passing hosted CI establishes standard source and documentation checks;
it does not convert a remaining source or documentation gap into external
verification work. The dated findings below preserve the earlier implementation
history while returning incomplete cards to **Open**. **Verification pending** is
retained only where implementation appears complete and the card's missing
outcome is evidence at a separately identified layer. CV-U06 separately carries
an approved one-line product-growth accounting exception: its disposition no longer blocks
campaign acceptance but does not, without a separate status decision,
recategorize the functional implementation result. No Viking execution, novice
walkthrough, scientific review or biological validation was performed by this
audit.

### CV-U01 CLI color and readability

**Operator report:** “I said outputs need to be colored; output of init and
validate are not. Run also unreadable wall of monocolor text. Inspect too.”

**Requested outcome:** Meaningful color and readable output across Init,
Validate, Run and Inspect. This is a repeated requirement, not a new preference
limited to one command. Doctor's presentation is separately detailed in CV-U04;
dashboard logs are included in CV-U14. No color palette was specified.

**Additional operator report:** “Emrys inspect output is very challenging to
interpret”. Readability includes understanding the displayed information, not
only adding color or shortening the output. Delayed population is a separate
finding in CV-U29; both issues affect Inspect's usefulness.

**Implemented slice:** Init, Validate, Run and Inspect use the shared terminal
presentation owner for headings and status emphasis. Plain, redirected, dumb
terminal and `NO_COLOR` behavior remains readable. Inspect groups the Run summary
and scientific milestones before blockers and the next supported action.

**September 16 Viking acceptance failure:** The operator reported that `emrys
init`, `emrys validate` and `emrys run` were still effectively monocolored.
`runtime discover` also needs the shared color/readability treatment, and guided
prompts need clearer semantic color. In Inspect, `Run complete` remained too hard
to find. Dashboard log coloring is retained separately in CV-U14/CV-U30. These
are terminal observations, not evidence that redirected, `NO_COLOR`, or dumb
terminal behavior should become color-dependent. CV-U01 returns to **Open**.

**Approved hierarchy refinement:** The shared presentation owner now renders
field names separately from values and gives ready, complete, warning and failed
outcomes distinct semantic emphasis. Init preview, Validate, Runtime discovery,
Run and Inspect use that owner; guided prompts separately emphasize their labels
and dim `Press ENTER for ...` defaults. Exact readable plain output is preserved.
This addresses the reported indeterminate color blocks rather than treating the
finding as an absence of ANSI output. Viking visual acceptance remains pending,
so CV-U01 is **Verification pending**.

**September 17 adversarial audit:** The shared presentation migration is not
caller-complete. `emrys init synthetic` and `emrys init manifests` remain Init
routes, but neither exposes the shared Boolean `--verbose` contract nor uses the
shared terminal presentation owner; both emit unconditional raw `print`
summaries, including effectively monocolor normal output. The earlier
presentation work for Project Init, Validate, Run and Inspect remains valid, but
Viking visual acceptance cannot close missing source wiring in the other Init
callers. CV-U01 returns to **Open**.

**September 17 caller-complete correction:** Synthetic and manifest Init now use
the shared presentation owner and expose the same Boolean `--verbose` switch.
Cyan keys remain distinct from neutral or semantic values; terminal success,
pending and failure states use the shared restrained palette while redirected,
`NO_COLOR` and dumb-terminal text remains literal. Focused onboarding and
presentation checks passed locally. Standard CI and Viking visual acceptance
remain, so CV-U01 is **Verification pending**.

### CV-U02 Default CLI verbosity

The outstanding resource-disclosure conflict with CV-22 and CV-U04 is owned by
`SUBMISSION-PREVIEW-01` in the [main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up).
Its policy, affected card wording and presentation tests must agree before
CV-22 acceptance; concise output does not itself settle that policy.

**Operator report:** “Overall cli output is far too verbose by default, there
should be an option to get all that output but by default it should return only
the bare minimum, like init, validate, and doctor.”

**Requested outcome:** Normal output contains the minimum information the
operator needs. Detailed output remains available through an explicit verbose
option. Adding color alone does not address the excessive amount of text.
Command-specific expectations are recorded in CV-U03 and CV-U04. The operator
subsequently selected `--verbose` as the sole public detail switch. The former
public detail and log-level selectors are retired; durable diagnostic records
still retain their existing event detail fields.

**Implemented slice:** Init, Validate, Doctor, Run, Resume, Report, Stop and
static Inspect now expose the same Boolean `--verbose` contract. Normal output
hides identities, paths, commands, successful transaction tables and per-Task
detail while retaining progress, failures, blockers and supported next actions.

**September 16 refinement and acceptance failure:** Normal `emrys run` output
was still too verbose. Its default must retain only Run identity/location, major
phase or scheduler state, actionable warnings, final outcome, report/log location
and a recovery/resume instruction when needed. Per-Task detail, environment
diagnostics, executed commands, polling detail and low-level logs belong behind
`--verbose`. Inspect needs the same split, with Run admission, Attempt outcome,
Scientific Results, Reporting and next action prominent rather than one ambiguous
completion label. `runtime discover` also needs a concise default and the same
Boolean `--verbose` detail switch. Durable evidence and recovery detail remain
retained even when hidden from normal output. CV-U02 returns to **Open**.

**Implemented refinement:** Run planning now defaults to the Run name/location,
pending/reusable work and reporting disposition; Slurm adds only placement and
the allocation request. Inspect defaults to its four authority outcomes,
verified completion when applicable, blockers, applicable recovery, next action
and verified report paths. Runtime discovery defaults to colored readiness and
its no-write/admission outcome. The existing Boolean `--verbose` restores
profile limits, immutable identities, commands, milestones, timing, log
associations, runtime checks and per-Task/evidence detail. Focused current-source
CLI suites passed 430 tests with one skip; two scientific execution fixtures
were deselected because their controlled `-I` children loaded a different
editable EMRYS installation, a test-environment source-binding mismatch rather
than presentation evidence. CV-U02 is **Verification pending** for standard CI
and Viking terminal acceptance.

**September 17 adversarial audit:** Default-verbosity behavior is likewise
incomplete across Init. `emrys init synthetic` always prints dataset, publication
and evidence details, while `emrys init manifests` always prints output and
publication details; neither command accepts `--verbose` to separate the minimum
operator result from optional detail. The concise/default split already delivered
for Project Init, Validate, Doctor, Run, Inspect and runtime discovery remains
recorded, but the claimed common Init contract is not yet implemented across all
public Init callers. CV-U02 returns to **Open**.

**September 17 caller-complete correction:** Synthetic Init now defaults to its
destination, dataset profile, library count, publication state and evidence
boundary; read composition, reference size and publication mechanics are
verbose. Manifest Init defaults to its destination, manifest count and
publication state; exact members and policy are verbose. Both preserve errors
and no-write outcomes. Focused local checks passed; standard CI and Viking
terminal acceptance remain, so CV-U02 is **Verification pending**.

**September 21 critical-preview refinement:** Named Init's normal review now
keeps only the compact scientific choices needed to catch an incorrect immutable
plan: strand summary, comparison/target, five paired-CMH thresholds, background
state/maximum and three STAR values. Per-sample paths and assignments remain
verbose. This is deliberate critical information under AC-GUARD-002, not a
return of diagnostic narration. CV-U02 remains **Verification pending** for
hosted CI and Viking terminal acceptance.

### CV-U03 Init and Validate summaries

**Operator instruction:** “Init can give output directory libraries, and
anything else that is high value. Validate can just tell pass or fail with
specific error on failure.”

**Requested outcome:** Init reports the output directory, libraries and other
high-value information. Validate gives a clear pass/fail result and the specific
error when it fails. Routine detail belongs in the optional verbose output
described in CV-U02. The user did not supply an exhaustive list of Init fields.

**Implemented slice:** Init's normal summary reports its output directory,
library count and IDs, Analysis/site, reference, partition count, comparison and
target. Validate normally prints `PASS` or one `FAIL` line with the specific
error; `--verbose` restores hashes, counts, paths, warnings and Analysis detail.

**September 21 summary completion:** Init now also reports the compact strand
summary, five paired-CMH values, active/inactive background maximum and all three
STAR values in the normal review. These are the effective immutable study
choices; verbose still owns individual sample/mate paths and assignments.
CV-U03 remains **Verification pending** for hosted CI and Viking visual review.

### CV-U04 Doctor presentation

`SUBMISSION-PREVIEW-01` in the [main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up)
owns the outstanding preapproval resource-summary reconciliation with
CV-U02/CV-22, including Doctor submissions.

**Operator report:** “Doctor output is also just wall of text; needs to be more
user friendly.”

**Detailed instruction:** “Doctor should print each category with pass or not
with execution requirements. The info about the specific repair and validation
plan should be reserved for verbose. After that it should only print each step
with the spinner and timer (the currently green text) as it does currently; the
specific package output, runtime work, etc is unnecessary.”

**Requested outcome:** Keep the initial category results and execution
requirements visible. During subsequent work, retain the existing green step
text, spinner and elapsed timer. Detailed repair/validation plans, package
output and runtime-work narration are optional verbose information, not the
default stream. This request concerns presentation; it does not request removing
the underlying checks or repairs.

**Implemented slice:** Doctor keeps Project, Analysis, Inputs, Storage, Runtime
and Execution category results plus execution requirements in normal output.
Repair internals, package output paths, runtime narration, Slurm accounting and
precise phase/invocation timing move behind `--verbose`; the shared named-phase
spinner and elapsed timer remain visible during work.

**September 16 Viking acceptance failure:** During Doctor repair, a live progress
line and the next Slurm diagnostic were joined as
`submission-to-return wait 0:00:00Slurm submission records...`. This makes the
named phase unreadable and is tracked as the otherwise-unowned rendering defect
CV-UX-01 below. The operator also reported that Doctor repair takes too long;
at that checkpoint CV-26 owned phase attribution rather than treating shorter
output as a speedup. CV-U04 returned to **Open** at that point.

**Reconciled correction:** CV-UX-01 now serializes ordinary and verbose Doctor
diagnostics through the active Rich display, hides scheduler-record paths from
normal output, and retains them under `--verbose`. Narrow color and `NO_COLOR`
PTY fixtures cover the exact zero-duration collision, and the integrated standard
CI passed. The broader category/progress contract above is therefore implemented;
CV-U04 is **Verification pending** for a fresh Viking terminal walkthrough. This
does not claim that Doctor is faster or require a cluster performance measurement.

### CV-U05 Doctor first-run expectations

**Operator question:** “Why did we lose the message about doctor taking 5-15 mins
on first run?”

**Latest operator instruction:** “Inform user that doctor setup can take
5-25 mins”. This updates the originally requested 5–15-minute range.

**Requested outcome:** Show the **5–25-minute** setup expectation in normal
Doctor output. It is useful expectation-setting, distinct from verbose
diagnostics. The reason the notice disappeared was not established in this
discussion; the range is the user's latest requested guidance, not a new timing
measurement made while recording these findings.

**Implemented slice:** Every normal Doctor repair or verification plan now says
`First Doctor setup can take 5–25 minutes.` before confirmation. Focused local
fixtures cover both normal suppression and expanded verbose presentation. The
integrated standard CI recorded above passed; the five cards remain Verification
pending for operator terminal review.

**September 16 timing observation:** The operator reported that Doctor repair
still takes too long and that setup plus execution should not consume a full hour.
No exact phase timings or comparable cold/warm boundary were supplied in this
finding batch. The 5–25-minute notice remains expectation-setting, not performance
acceptance. CV-26 retains the attribution evidence; future measured tuning is an
independent optimization-campaign decision.

### CV-U06 Available resources

**Operator question:** “Why is workflow CPU ceiling still 4? I said we need to
be able to use all available resources”.

**Reported problem and requirement:** The operator sees a workflow CPU ceiling
of **4** despite the prior requirement to be able to use all available resources.
The retained discussion did not establish why that cap remained or which setting
produced it. No substitute CPU count, tuning result or resource-selection design
was agreed here; preserve the resource-use requirement without inventing a cause.

**Further requirement:** The operator reiterated that resource use must support
wall-time optimization and challenged the introduction of resource limits without
their instruction. The historical fixed policy and reported eight-hour versus
four-hour regression are retained as provenance in CV-U28; the allocation-aware
policy below is current authority. Resource usage must also be visible again in
the dashboard (CV-U33).

**Superseded historical restoration:** The initial implementation restored:
12 workflow cores and 524288 MiB, with concurrent sample/partition work and
the original stage allowances. Viking placement requests 256 CPUs, exclusive
allocation and 12 hours. Requested CPUs and workflow cores are separate limits;
this restored the selected historical configuration but left CV-U06's request
to use all available resources incomplete. CV-U33 remains separately owned.
See CV-U28 for the superseding decision and retained provenance.

**Allocation-aware implementation:** Workflow cores and memory resolve from the
allocation. Repeated stages resolve concurrency from admitted sample/partition
counts and CPU/memory capacity, share memory with recovered per-task minimums,
and pass CPU shares to native tools that support them. Singleton memory follows
the workflow; STAR indexing and Step 08 receive workflow CPU allowances. STAR
alignment's sorting threads, samtools additional workers, and Java helper-pool
CPU counts are now explicit. Steps 00b, 03, 07, 09 and 10 retain serial main
algorithms (03/07 parallelize across samples/partitions). Every stage's policy
and the limits of parallelism are in the
[stage resource table](../../configs/README.md#profile-document).

Viking requests all CPUs and RAM on one exclusive node without assuming a fixed
node size. Resource shares do not prove full utilization, safe peak RSS for every
dataset, or improved wall time. The
[HPC resource research](../../configs/README.md#slurm-and-tool-resource-semantics)
records primary-source behavior and the measurements needed for performance
acceptance. Static Attempt shares do not expand as sibling tasks finish.

The existing resource resolver owns profile admission, reservation checks,
Attempt resolution and retained-policy validation. Shared schema definitions
replace duplicate CPU/memory value validation, and redundant parsing is removed.
No new scheduler, dependency, product file or mutable authority is introduced.
The existing Attempt policy retains Analysis-derived workload counts.
Existing numeric policies remain valid and existing Runs retain their declaration.
The [profile guide](../../configs/README.md#profile-document) documents values;
the preceding migration procedure creates a new profile for existing Projects.
This allocation-aware workflow, memory, concurrency and native-tool policy is
authoritative for CV-U06 and CV-U28. Ordinary institutional admission and
resolution remain pending; comparative benchmarks, optimal utilization and a
speedup claim are not acceptance requirements for that policy decision.

**Earlier STAR-index slice verification:** 848 focused profile/resource/Doctor/onboarding/Slurm,
submission-inspection, application-contract and E2E-harness checks passed; the
two separately selected onboarding subprocess cases also passed. The final
Doctor/capacity run passed 154 cases, including nested cgroup v1/v2 limits, and
all four STAR producer fixtures passed. Generated-command and resource/resume
materialization checks passed 53 cases, with one Linux-only containment case
skipped on macOS. These counts describe overlapping targeted selections.
One broader resume-execution fixture failed before any Task ran: its isolated
interpreter loaded the older `/Users/elisteiger/dev/norad` installation and
could not import `coolname_hash`. That fixture remains for hosted CI; no
dependency was installed to bypass the environment mismatch. Checks used this
worktree's source, build-generated metadata and existing cached dependencies.
Ruff, documentation structure and whitespace checks passed. The historical
restoration's CI result does not cover this follow-up. Current hosted results are
recorded at the combined PR #266 implementation checkpoint above. Institutional
execution remains pending; CV-U06 remains **Verification pending**.

**All-stage follow-up verification:** 335 targeted resource, profile,
application-contract, materialization and orientation checks passed; 543
capacity, Slurm, Doctor and onboarding checks passed. All six affected shell
worker fixtures passed, including STAR sort threads above six, Java processor
counts and samtools additional-worker accounting. Ruff, documentation structure
and whitespace checks passed. The available local isolated interpreter selects
an older checkout and lacks its optional CLI dependencies, so no dependency was
installed merely to run those lanes locally. The combined implementation
checkpoint's standard CI passed the isolated subprocess/runtime lanes and the
managed golden path. No cluster jobs were started. The follow-up replaces the
existing resolver and schema mechanics rather than adding a scheduler; the
complete PR has no new product files.

**Accounting correction — September 17:** The exact first-parent resource-
tranche diff from `69223787` through merge `125cdc2b`, excluding tests and
Markdown but retaining product source, schemas and configuration, is 495
insertions and 244 deletions: **251 net added product lines**. The earlier
statement that the complete tranche remained within a 250-line allowance is
withdrawn. The user approved the one-line excess on 2026-09-22, retaining
schemas and configuration in the count. The accounting disposition is settled;
it is not Viking evidence and does not change CV-U06's functional status. These are
implementation, local-fixture and hosted software results, not Viking
utilization or speedup proof.

### CV-U07 Projects directory

**Operator instruction:** “user should not be manually creating the projects
dir - I have made that a clear rule in the past”.

**Requested outcome:** EMRYS creates the Projects directory as part of its normal
operation. The operator must not have to create it manually as a prerequisite
or be directed to a separate directory-creation command in Quickstart.

**Latest location instruction:** “Projects dir should be within parent repo not
a sibling”. The Projects home belongs inside the parent repository. This latest
requirement supersedes earlier guidance to place it outside the repository;
recording it here does not change the existing CV-14 card's status. Each Project's
own manifests must also be inside that Project, as detailed in CV-U26.

**Selected implementation:** Track `Projects/README.md` and `.gitkeep` in the
repository and ignore all Project children. Quickstart, Runbook and reconnect
instructions enter this supplied parent; no `mkdir` step remains. Existing
Projects are neither moved nor rewritten, and the existing absent-child,
canonical-parent and symlink refusals remain the creation authority.

**Verification limit:** Repository-ignore, documentation-link and onboarding
checks cover the hosted layout. A fresh Viking clone and operator walkthrough
remain required; this card is Verification pending until that evidence is
supplied.

### CV-U08 Quickstart scope and language

**Operator instruction:** “Quickstart is still too verbose; advanced info needs
to be moved, Quickstart should literally be the bare minimum necessary to get
emrys installed and run an analysis, for non-technical operators”.

The operator also asked why the language had become too technical again despite
repeated instructions. This is an audience and scope regression, not just a
request to shorten individual paragraphs.

**Requested outcome:** One minimal, plain-English path for a first-time,
non-technical Viking operator to install EMRYS and run an analysis. Move advanced
information to its appropriate documentation. Necessary explanations and concrete
values still belong in Quickstart; brevity must not require the reader to guess
what a step means or obtain missing values elsewhere (CV-U09/U11/U20).

**Expanded workflow requirement:** “Streamline the quickstart into one complete
Viking/PUM1 workflow for nontechnical users.” Each step should advance the user
toward Results without scheduler expertise, configuration authoring or detours
into other documentation. The operator specifically requires compatible-runtime
discovery and reuse, fewer repeated hashing/setup operations, manifests inside
the Project, and tested site/workload settings. Preserve necessary integrity and
readiness checks while minimizing repeated work, commands and decisions.

These details are retained in CV-U22 and CV-U24–CV-U28. They were delivered as
parts of one complete smoke-to-real journey. The latest direction below
supersedes only the requirement to run the synthetic exercise first; whichever
path the operator chooses still retains its required readiness and integrity
checks.

**Latest operator direction:** The synthetic E2E is now optional so a user can
reach their own study without first completing a second Project and Run. The
ordinary fast path should create the real Project, prepare/verify its runtime,
run, watch and inspect it. If the operator chooses the smoke exercise, its
prepared tools should still flow into the real Project under CV-U22. Skipping the
smoke exercise removes that preliminary site check; it does not remove Doctor,
scientific-input admission, storage qualification, or actual-Run evidence.

The Quickstart also still contains too many preconstructed multi-command blocks.
Distinct `emrys` commands should be separate copyable blocks so each can explain
its purpose, expected output, success condition and stop/recovery condition.
Environment setup may stay grouped only where its commands must execute together.

**Delivered implementation and documentation:** Quickstart now gives one
paste-ready synthetic path followed by one guided six-library EV/PUM1 path. The
guided initializer discovers paired FASTQs, records the six explicit biological
assignments, creates both manifests inside the Project, checks preview inputs
without full FASTQ hashing, and prints one replay command that hashes each FASTQ
once during creation. New Viking Projects inherit the current allocation-aware
placement, workflow, memory, concurrency and native-tool policy; the operator
does not author a resource profile. Quickstart supplies the sample assignments,
regions, STAR parameters, analysis thresholds and resource values inline while
moving detailed Doctor, recovery and format material to their existing owners.
The real-study path now previews and selects the compatible tools prepared by
the smoke Project before Doctor, without installing packages or detouring into
the Runbook. If the shared owner later needs repair, Doctor creates a new
generation rather than changing the generation retained by another Project.

**Verification limit:** The Quickstart still spells out `--site viking` at each
Project-creation boundary. CV-U24 owns the separate persistent-default
convenience; the current commands remain complete and require no site decision
from the operator. The integrated standard CI recorded above passed. A fresh
Viking installation and a novice smoke-to-EV/PUM1 walkthrough remain pending,
so CV-U08 is **Verification pending**. Historical values remain provenance for
the configurable per-task minima; they are not the current fixed workflow policy,
a new whole-Run cluster execution or a performance measurement.

The September 16 walkthrough rejected the mandatory smoke-to-real structure,
command grouping, region/reference language and preview-to-creation handoff.
Those are negative novice-acceptance results, so CV-U08 is **Open** rather than
Verification pending. The reported full-hour experience is not yet attributed
to setup, queueing, smoke execution, runtime checks or real analysis.

**Approved direct-to-data revision:** The real six-library EV/PUM1 journey is
now the numbered default. The synthetic exercise is a clearly optional site
confidence check with its time tradeoff stated before its commands. Every
`emrys` command has its own copyable block and adjacent purpose, expected result
and stop condition. The guide explains that the reference FASTA and GTF are
external study inputs, what to do when they are unavailable, why the regions
prompt may be empty, and how the selector list relates to the reference. It also
bridges the preview to its generated creation command and reserves `Project
ready` for successful publication. A fresh novice Viking walkthrough remains
pending, so CV-U08 is **Verification pending**.

Local integration checks pass 631 tests across every test file changed by this
tranche, with one Linux-only materialization test skipped on macOS. Six isolated
child-interpreter cases were deselected because the borrowed installed checkout
lacks `simple_term_menu` or `coolname_hash`; the corresponding current-source
paths pass in process. Documentation structure checks pass for 169 Markdown
documents and three Mermaid sources, all 13 Quickstart Bash fences pass
`bash -n`, and focused Ruff, compilation and diff checks pass. No dependency
installation, cluster execution or scientific review was performed locally.

**September 17 adversarial audit:** The maintained novice journey cannot yet be
followed literally. Quickstart tells the operator to enter STAR and analysis
values immediately after the FASTA and GTF, but current guided Init next asks for
the FASTQ directory, sample assignments and region selection; only after those
inputs does it derive STAR suggestions and collect the remaining analysis
answers. A literal first-time user can therefore enter `149` where a filesystem
path is required. The prerequisites also require delivered FASTQ checksums, but
the numbered journey provides no command or handoff that consumes or verifies
them. The direct-to-data restructuring and optional-smoke explanation remain
useful work, but these are documentation/product mismatches in the primary path,
not evidence awaiting a Viking walkthrough. CV-U08 returns to **Open**.

**September 18 approved alignment:** Quickstart now follows the implemented
questionnaire once, in its literal reference, FASTQ, sample-assignment,
partition, STAR and scientific-settings order. Provider checksums are no longer
listed as a required guided input: the guide says to retain any supplied values
with the delivery records and distinguishes them from EMRYS's own admitted-file
hashes. No checksum interface or extra FASTQ pass was added. The guide also
states the current synthetic-Project success signal and the complete built-in
Viking placement values. Focused documentation and guided-onboarding checks
pass locally; a fresh novice Viking walkthrough remains required, so CV-U08 is
**Verification pending**.

### CV-U09 Synthetic-project explanation

**Operator report:** “What ‘create the synthetic project’ is doing is NOT clear
to a first time user, it should be explained in plain language.”

**Requested outcome:** Explain what this step creates, what “synthetic” means
and why the user performs the smoke-test step. A first-time operator should
understand the purpose before running the command, without having to know the
project's internal terminology.

**Implemented documentation:** Before the creation command, Quickstart now says
that EMRYS supplies tiny made-up reads, a reference and scientific settings. It
explains that the smoke test checks installation, Viking execution and report
generation before own-data use, while explicitly excluding full-study capacity
and scientific-choice claims.

**Verification:** The explanation precedes the command and uses no internal
runtime or scheduler terminology. Bash-fence syntax and changed-document links
pass locally, and the integrated repository documentation gate recorded above
passed. CV-U09 is **Verification pending** for novice acceptance; that acceptance
does not require a new cluster run.

**September 16 direction:** Explanation alone is insufficient: the synthetic E2E
must be presented as an optional environment/site exercise, with the time and
confidence tradeoff stated plainly, rather than a mandatory prerequisite to the
real-data path. CV-U09 returns to **Open** for that revised journey and novice
acceptance.

**Approved optional-path revision:** Quickstart now places the synthetic E2E
after the ordinary real-data journey and labels it optional. It states both the
extra confidence it supplies and the setup/queue/run time it adds. Skipping it
does not skip Doctor or real-input admission. CV-U09 is **Verification pending**
for novice acceptance.

### CV-U10 Unnecessary Quickstart command

**Operator instruction:** “Git rev-parse head is not necessary in Quickstart…”

**Requested outcome:** Remove `git rev-parse HEAD` from the basic Quickstart
journey. This finding concerns an unnecessary operator step; it does not request
removing EMRYS's own source-identity or provenance records.

**Accepted disposition:** `git rev-parse HEAD` is absent from Quickstart's
installation journey. EMRYS's own Run implementation identity remains unchanged,
and the advanced Runbook retains the command where an operator intentionally
installs and records a chosen release or commit. A repository search confirms
the removal is confined to the novice guide. CV-U10 is **Completed** at static
documentation evidence; no runtime or cluster claim is made.

### CV-U11 Paste-ready Quickstart commands

**Exact command questioned:**

```bash
export EMRYS_PROJECT_ROOT="${EMRYS_PROJECTS_ROOT:?Choose a Projects home first}/emrys-smoke"
```

**Operator question:** “what is the ? Character doing? It is unclear if a user
is expected to directly paste this or replace a value before”.

**Source of confusion:** The command embeds a prerequisite check in shell syntax.
`:?` reports an error if the variable is unset or empty; it neither prompts for a
value nor marks text to replace. The command therefore assumes that the Projects
home has already been set, which the reader did not find clear.

**Requested outcome:** Clearly distinguish commands to paste unchanged from
values the user must supply, and make prerequisites understandable. Avoid
unexplained shell expressions. This also depends on supplying expected Viking
values directly in Quickstart, as requested in CV-U20.

**Implemented documentation:** Quickstart labels steps 1–5 as paste-ready and
chains dependent commands so a failure stops the block. The synthetic Project
path uses the earlier named Projects-home variable without the `:?` expression.
Own-data blocks are explicitly labelled templates and use conspicuous
`REPLACE_WITH_...` values; the surrounding text names the study-specific files
and assignments that must replace them.

**Verification:** All Quickstart Bash fences pass `bash -n`; changed-document
links and anchors pass a focused local check, and the integrated repository
documentation gate recorded above passed. CV-U11 is **Verification pending**
for novice acceptance. CV-U20 separately owns whether every knowable Viking/PUM1
value has been supplied.

**September 16 acceptance failure:** The operator requested fewer preconstructed
blocks and separate `emrys` commands with separate explanations. After the Step 7
questionnaire, the preview did not emit `Project ready` and the guide did not make
the next action sufficiently clear: the operator was expected to paste a very
large generated creation command. The no-write preview must say explicitly that
the Project does not yet exist, identify one unmistakable next action, and reserve
`Project ready` for successful publication. CV-U11 returns to **Open**; CV-U18
owns the guided product interaction.

**Approved command-handoff revision:** Distinct `emrys` invocations are now
separate blocks with local explanations. The questionnaire section says that
preview creates no Project, identifies the generated command as the next action,
and tells the operator to paste the complete command. Successful creation is the
only point labelled `Project ready`. CV-U11 is **Verification pending** for a
novice Viking walkthrough.

**September 17 adversarial audit:** The commands are syntactically paste-ready,
but the surrounding success and prompt instructions are not yet reliable enough
to satisfy the requested handoff. The guided-Init prompt order differs from the
order documented in step 3, so the supplied values cannot be entered in the
sequence the guide states. The optional smoke path also says success ends with
`Project ready:`, while `emrys init synthetic` actually reports `Published
deterministic synthetic Project (...)` followed by `Project:`. Prior improvements
to separate command blocks and the preview-to-creation handoff remain valid, but
a novice cannot use the documented prompts and expected output as literal checks.
CV-U11 returns to **Open**.

**September 18 approved alignment:** The single ordered questionnaire now puts
the FASTQ, sample and partition prompts before the supplied STAR and scientific
answers. The optional smoke path expects `Synthetic Project: ready` followed by
`Project:` and its path, matching the current initializer. Focused local checks
pass; literal novice use on Viking remains required, so CV-U11 is **Verification
pending**.

### CV-U12 Duplicate submission warning

**Scenario supplied by the operator:** A job is already running, but
`emrys inspect` has not populated yet. The user may interpret the empty or delayed
display as a failed submission and attempt to submit the work again.

**Requested safeguard:** Give a “big red warning” and tell the user to
“ONLY submit if they understand what they are doing and that inspect takes time
to populate”.

**Requested outcome:** For an earlier pending/running submission of the same
work, explain the display delay and the risk of creating duplicate jobs before
another submission. Continuing should be an intentional decision made with that
understanding. The exact enforcement, acknowledgement or override mechanism
was not decided; no new flag or automatic cancellation behavior is implied.

**Implemented safeguard:** Quickstart still says to submit once and the integrated
watch command still selects a retained pre-Run submission. Before `sbatch`,
`emrys run` now compares the requested scientific work and execution-profile
binding with retained requests. A matching active request, or one whose terminal
state cannot be confirmed, produces a prominent duplicate-risk warning that
explains display delay and stops submission. Continuing requires the explicit
`--allow-duplicate-submission` override and repeats the warning; terminal and
unrelated requests do not trigger it. No request is canceled or retried.

Focused local coverage exercises active and unknown scheduler observations,
the explicit override, distinct retained request publication and the existing
no-write confirmation path. Institutional terminal review remains required for
the requested red presentation and real delayed scheduler/Run population, so
CV-U12 is **Verification pending**.

**September 17 adversarial audit:** The duplicate-submission guard compares
near-raw delegate argument vectors after removing only `--execute`, `--no-report`
and `--verbose`; it does not compare a normalized scientific request. Equivalent
work can therefore bypass the warning when one invocation relies on the sole
default Analysis and another spells out `--analysis primary`, when only the
diagnostic `--log-root` changes, or when equivalent profile content is selected
through a different source path. Those requests are syntactically different but
do not represent distinct scientific work, so a second `sbatch` can proceed
without `--allow-duplicate-submission`. The retained-request publication,
scheduler observation and prominent warning remain useful protections, but the
card's same-work safeguard is source-incomplete. CV-U12 returns to **Open**.

**September 21 implementation correction:** Control now compares a normalized
pre-Run request projection: the resolved Analysis name, stopping boundary,
exact processing-source Run ID if any, and existing exact execution-profile
binding. Project declaration admission shares the scientific owner's
sole-or-explicit Analysis selection rule without hashing FASTQs, probing the
runtime or constructing a Run on the submit host. Diagnostic log location,
presentation/reporting choices, confirmation mode, interpreter path and
profile source path no longer distinguish work; byte-identical profiles at
different paths retain the same existing binding. Byte-different profile
sources remain distinct under the exact-binding contract.

Retained v1-v4 request formats remain unchanged. Their delegate arguments are
projected through the public Run parser, and an active or unconfirmed request
with the same profile binding fails closed to the existing warning and explicit
override when its selectors cannot be reconstructed. Public-flow coverage uses
admissible named Analyses and the real request publication, discovery and
scheduler-observation owners for default/explicit Analysis, log-root, profile
path, presentation, distinct Analysis/boundary/profile binding, terminal and
active/unknown scheduler states, override, malformed retained arguments and a
missing scheduler response; exact processing-source comparison is covered at
the normalized projection seam. The slice adds 45 net maintained product lines
across two existing product files, with no new file, schema, persistent field,
configuration, dependency or mutable state. Hosted CI and institutional review
of the red warning during real delayed scheduler/Run population remain
outstanding, so CV-U12 is **Verification pending**.

### CV-U13 Watching progress

**Operator instruction:** “Quickstart should also instruct user how to watch
progress in dashboard”. The requested command direction was
`emrys watch {JOB_ID||JOB_NAME}`, with “maybe other identifiers allowed”.

**Requested outcome:** Include the dashboard/progress-watching step in the
ordinary Quickstart journey. The desired interface accepts a job ID or job name
through `emrys watch`. The braces and alternatives express the user's proposed
interface, not a paste-ready command. Additional identifiers and final command
syntax remain unspecified.

**Implemented software outcome:** `emrys watch [RUN_OR_JOB]` now enters the
existing inspection watch owner. From a Project it automatically selects the
sole retained submission before Run creation or the sole Run afterward; an
ambiguous selection uses the existing terminal picker and fails explicitly for
noninteractive use. Numeric scheduler IDs and exact scheduler names reuse the
bounded scheduler discovery and identity checks. Run submission prints both
identifiers, labels the result submitted rather than complete, and prints the
exact job-ID watch command. Quickstart now makes the parameter-free Project
command the ordinary progress step.

**Verification and limit:** Focused selector, scheduler-name, presentation and
public-parser checks pass locally and in the integrated standard CI.
Scheduler-name selection still requires one exact current-user root allocation;
duplicate names require the numeric ID. Viking terminal use remains pending, so
the card is Verification pending.

**September 16 Viking acceptance failure:** Plain `emrys watch` did not select
the intended job or offer a selector; the operator had to find and enter the
numeric scheduler job ID manually. The exact invocation directory, candidate
roster and retained request state were not supplied, so the cause remains
uncharacterized. The ordinary path must either select the sole admissible target
or present the picker; silent failure followed by manual scheduler-ID discovery
does not satisfy this card. CV-U13 returns to **Open** and shares the unresolved
selection defect with CV-U31/CV-16.

**Approved correction:** Source audit found that no-argument watch outside a
Project delegated multiple scheduler candidates to the raw dashboard resolver,
which silently tried the newest candidate first and never opened the existing
picker. Watch now selects one bounded current-user scheduler candidate, offers
all candidates in the existing interactive picker, and fails noninteractively
with their IDs. The raw resolver now accepts only a sole discovered candidate
and refuses ambiguity rather than inferring newest. The two affected test files
pass locally (249 tests), and Ruff passes on all touched Python files. Live
Viking selection remains required, so CV-U13 is **Verification pending**.

**September 17 adversarial audit:** The corrected picker still does not inventory
retained pre-Run submissions outside the current Project. Projects-home discovery
enumerates only existing Runs and is evaluated before raw scheduler discovery.
After the optional smoke journey has created a Run, plain `emrys watch` outside
the real-data Project can therefore select that historical smoke Run while a
newer real-data submission is still awaiting Run creation. Raw discovery also
starts from all current-user scheduler jobs rather than an admitted EMRYS roster.
These are remaining source-selection defects, not merely unperformed Viking
acceptance. CV-U13 returns to **Open** and shares the required caller-complete
correction with CV-U31 and CV-U32.

**September 18 caller-complete correction:** Ordinary watch now builds one
bounded inventory from admitted Project Runs and every retained submission,
including submissions that have already produced a Run. The same immutable
target record and picker serve current-Project and declared Projects-home use.
A sole target is automatic; ambiguity is explicit; noninteractive use fails;
and no timestamp, directory order or scheduler query chooses a target. The
ordinary no-argument command no longer falls through to all current-user Slurm
jobs. Exact job IDs, exact job names and the expert raw `inspect --job-id`
surface remain available. Focused selector, request, scheduler, renderer and
watch checks pass locally; standard CI and Viking/operator use
remain required, so CV-U13 is **Verification pending**.

### CV-U14 Dashboard logs

**Operator instruction:** “Logs in dashboard should also be friendlier and not
mono colored”.

**Requested outcome:** Improve the readability and color coding of the log
content itself. Coloring dashboard headings alone would not address this finding.
No specific palette, filtering rule or log-content deletion was requested.

**Implemented software outcome:** Installed watch styles literal informational,
warning, error and completion log lines with distinct colors while preserving
every byte of text and readable plain-terminal output. Dated scheduler, Run and
stream headings are emphasized separately from unverified log interpretation.
Focused rendering tests verify the styles and unchanged literal content, and the
integrated standard CI passed. Institutional terminal and operator acceptance
were still pending.

**September 16 Viking observation:** Dashboard and other displayed logs remained
monocolored even though the surrounding dashboard rendered color. Literal log
text and retained bytes must remain unchanged, while severity and known workflow
prefixes gain useful optional styling. Timestamped or otherwise prefixed lines
must not silently evade the styling rules. Plain/redirected output and
`NO_COLOR` remain readable. This confirms CV-U14 remains **Open**.

**Approved prefix-aware refinement:** The installed dashboard now styles known
severity and workflow prefixes even when a timestamp or retained stream prefix
precedes them, and recognizes structured `level`/`severity` fields. Styling does
not rewrite literal log text. Viking/tmux visual acceptance remains pending, so
CV-U14 is **Verification pending**.

**September 17 adversarial audit:** The prefix-aware styling does not recognize
important log forms already present in repository fixtures. `Finished jobid:`
does not match the installed `finished job` word-boundary rule, and
`WorkflowError:` does not match an error token expected at the start of the
styled content. The focused styling test instead uses the invented form
`Finished job 7.`. Known Snakemake completion and failure lines can therefore
remain monocolored despite passing tests. This is remaining implementation and
fixture work; CV-U14 returns to **Open**.

**September 17 literal-form correction:** Watch now styles the actual retained
`Finished jobid:`, `WorkflowError:`, rule/checkpoint, warning/error, structured
severity and partial/complete step-count forms. Timestamps and secondary stream
metadata are dim, unclassified text remains neutral, and styling spans never
rewrite literal bytes. The log view also identifies the selected stream by label
and position. Exact-content/color tests passed locally; Viking/tmux visual
acceptance remains, so CV-U14 is **Verification pending**.

### CV-U15 Dashboard action language

**Operator question:** “What does verify/associate again mean in the dashboard?
Unclear”.

**Requested outcome:** Replace or explain the label in plain language so the
operator knows what the action does and whether it merely refreshes information
or changes anything. During the discussion, the assistant described the intended
meaning as rechecking a job and refreshing its matching Run information and logs.
That explanation was not independently verified and is not an established
description of current behavior. The unclear label is the recorded finding.

**Implemented software outcome:** The installed watch control now says
`r recheck selection/evidence (read-only)`. The label describes the read-only
action without the unexplained “verify/associate again” wording. Public terminal fixtures passed the
integrated standard CI; operator wording acceptance remains pending, so CV-U15
is **Verification pending**.

### CV-U16 Dashboard scrolling

**Operator instruction:** “Should not be able to scroll with mouse in dashboard
(logs lets you still). Scroll with up and down j/k is permitted.”

**Requested outcome:** Disable mouse scrolling throughout the dashboard,
including the log view where it reportedly remains possible. Preserve keyboard
scrolling using the up/down arrows and `j`/`k`.

**Implemented software outcome:** Installed watch captures and ignores mouse
reports, then restores terminal mouse state on
exit. Arrow, `j`/`k`, Page Up/Down and Home/`g` keyboard navigation remains.
Terminal fixtures cover mouse reports, keyboard navigation and restoration and
passed the integrated standard CI. An external terminal multiplexer can still
translate a wheel event into an ordinary arrow key before EMRYS receives it.
Institutional terminal acceptance remained pending for that narrower outcome.

**Expanded September 16 log-navigation request:** Selecting a log should begin at
its bottom/most recent retained line. New text should auto-scroll while the user
remains at the bottom; scrolling upward should pause following visibly, and a
deliberate return to the bottom should resume it. Add Vim-like counted movement
such as `99j`/`99k`, `/pattern` search with highlighted matches, and next/previous
match navigation such as `n`/`p` (or an equivalently documented pair). Line
numbers are also requested. Because the current view retains a bounded tail,
absolute-file versus tail-relative numbering must be stated rather than guessed.
These are desired interactions, not authority to weaken bounded reads, stream
identity, sanitization, or changed-generation handling. These additional
interactions remained Open at the time of the finding.

**Implemented expanded navigation:** Selecting an installed evidence/log stream
now starts at the latest retained line and follows new text while at the bottom.
Upward movement visibly changes the state to `PAUSED`; reaching the bottom or
pressing `G` resumes `FOLLOWING`. Counts apply to `j`/`k`; `/pattern` searches the
sanitized retained tail, highlights matches, and `n`/`N` moves forward/backward.
One-based displayed line numbers are explicitly tail-relative. Stream changes
reset search and resume follow. The existing 64-KiB/256-line read bound, identity
pinning, sanitization, rotation/truncation handling and ignored mouse reports are
unchanged. The standalone dashboard had no selectable evidence/log view and was
retired after the institutional owner accepted installed watch. The implementation
checkpoint's standard CI recorded above passed. CV-U16 is **Verification pending** for
Viking/tmux terminal acceptance.

**September 17 adversarial audit:** The implementation records when the selected
stream was replaced or truncated, but the interactive state does not act on that
changed generation. Search text, match state, paused-follow state and scroll
position are reset only when the operator manually switches streams. An
automatic refresh can therefore retain navigation state against unrelated
replacement bytes, contrary to the recorded claim that stream changes reset
search and resume following. CV-U16 returns to **Open** for a generation-aware
state reset and corresponding terminal coverage.

**September 17 generation-aware correction:** The shared stream owner now
exposes its existing replacement/truncation decision to installed watch. One
observed generation change clears count/search/match/scroll state and resumes
following without changing Run or stream selection. PTY coverage exercises both
replacement and truncation after paused search navigation; bounded reads,
sanitization and ignored mouse reports remain unchanged. Focused local checks
passed; Viking/tmux acceptance remains, so CV-U16 is **Verification pending**.

### CV-U17 Completion communication

**Operator report:** “Needs to communicate to the user when the job is done, in
dashboard and also just when run from cli or running inspect. I ran into a
confusing state where dashboard showed steps9/10 as pending 1/? despite the job
being completed successfully”.

**Requested outcome:** Give a clear completion message in the dashboard, Run CLI
output and Inspect. Preserve this exact discrepancy for follow-up: Steps **9/10**
remained **pending**, displaying **`1/?`**, after the operator reported successful
job completion. The step display and overall completion state must agree. The
cause and underlying scheduler/Run records were not examined during collection;
the report does not independently establish scientific or report completion.

**Implemented software outcome:** Direct execution prints completion after its
successful Attempt and applicable report verification. Slurm submission instead
prints `Submitted` and says completion is not yet verified. Static inspection
and watch share one completion projection from admitted Run evidence. When that
evidence establishes complete Results, the dashboard replaces stale log-derived
stage counts with verified Task counts, clears diagnostic active work and shows
the applicable reporting/finalization state. Scheduler state and log text alone
cannot produce the completion message.

**Verification and limit:** The reported Step 09/10 shape is covered by a fixture
whose diagnostic trace has `1/?`-equivalent missing totals while Run evidence
verifies both tasks and reporting; the dashboard renders both stages `1/1 DONE`
and announces completion. Focused checks pass locally. The original Viking Run
records were not supplied, so its historical cause remains uncharacterized and
institutional display acceptance is pending.

A later operator-supplied Viking timeout adds the failed-terminal counterpart:
when exact scheduler state is terminal and not `COMPLETED`, log-derived active,
partial, and unstarted work is displayed as `INTERRUPTED`, `INCOMPLETE`, and
`NOT REACHED`. The dashboard calls the outcome `JOB ENDED` and directs the
operator to final inspection; it does not infer completion or recovery.

The completion and failed-terminal projections passed the integrated standard
CI. Historical-cause reconstruction and institutional display acceptance remain
pending for that implementation.

**September 16 Viking acceptance failure:** A supplied dashboard view reported
`36/36 Snakemake jobs`, `0 jobs remaining`, Step FINAL `1/1 DONE`, and recent
completion entries for Steps 09, 10 and FINAL, while the same screen showed
overall `State: UNKNOWN`, Steps 09 and 10 as `1/? WAITING`, REPORT as `0/?
PENDING`, and no Run/control identity. The operator reported that static Inspect
and the logs claimed completion. The screenshot proves an internally
contradictory diagnostic display; it does not independently promote scheduler
or log text to scientific/reporting proof. When exact admitted Run evidence is
available, watch must show its verified projection. With only raw diagnostic
logs, it must distinguish “workflow log finished; Run completion unverified”
from active waiting and must not call unavailable reporting `PENDING`. CV-U17
returns to **Open**.

**Approved correction:** Raw log parsing now retains one bounded distinction
between a finished Snakemake invocation and a verified Run. When the reported
total is complete with no active or error-like record, the overview says
`Workflow log finished; Run completion unverified`, the phase repeats that
limit, observed stages are no longer called `WAITING`, and unavailable reporting
is `NOT OBSERVED` rather than `PENDING`. Admitted Run evidence continues to
replace the diagnostic projection with verified counts and completion. The
dashboard suite passes locally; Viking display acceptance remains required, so
CV-U17 is **Verification pending**.

### CV-U18 Interactive input-list creation

**Operator report:** “The command to create the input lists is fucking garbage,
what happened to the interactive process we explicitly discussed?”

**Further instruction:** “The input list creation is NOT something a
non-technical user should be expected to do”.

**Requested outcome:** EMRYS creates the input lists through the previously
agreed guided interaction. Users must not construct or format the lists
themselves, and Quickstart must lead through that guided process. This is a
functional onboarding requirement, not merely a request to explain a complex
list-generation command more thoroughly. The exact offending command was not
provided in this findings batch; whether the interactive route is missing or
simply absent from the guide was not established.

**Selected implementation:** Named `emrys init PROJECT_NAME` now discovers
recognized FASTQ pairs from one operator-selected directory, displays the
samples, asks for condition, pairing group and strandedness, and guides either
one regions file or a space-separated selector list. The same initializer asks
the existing reference and scientific questions, validates the complete study
interpretation, and prints one safely quoted creation command carrying every
answer. The specialist manifest helper remains available for advanced structural
drafting; ordinary Quickstart no longer exposes its long flag sequence.

**Verification limit:** Direct fixtures cover guided answers, generated replay,
biological pairing, selector forms and create-absent refusal. The integrated
standard CI recorded above passed. A novice Viking walkthrough remains required;
this card is **Verification pending** until that evidence is supplied.

**September 16 Viking findings:** The instruction “Leave the regions-file
prompt empty. At the selector prompt, enter this complete space-separated list;
the names must match the delivered reference” did not tell a novice what a
regions file is, what the selectors select, or how to confirm the names. The
guided sequence also asks for selectors before it collects the reference FASTA
and GTF, so it cannot show or validate the available FASTA contig names at that
point. Reorder the interaction so the admitted reference can inform the
selector prompt, explain the mutually exclusive regions-file and selector
choices in plain English, and never infer a scientific selection for the user.

Prompts need semantic color as well as clearer wording. Defaults should appear
dimmed/gray in the prompt with an explicit plain-text fallback such as `Press
ENTER for VALUE`; pressing Enter must remain unambiguous without color. After
the final question, the current no-write preview is not a created Project, yet
the large generated replay command appears without a clear transition or
`Project ready` message. The interface must state that preview is complete and
the Project does not yet exist, then present one unmistakable next action.
A candidate simplification is one interactive collect-review-confirm-publish
transaction, keeping the long replay command for verbose or automation use;
recording that candidate does not by itself approve the interface or weaken the
create-absent and input-change checks. This negative Viking acceptance keeps
CV-U18 **Open**.

**Approved correction:** Guided initialization now collects and admits the
operator-supplied reference FASTA and matching GTF before FASTQ/partition
questions. The partition prompt explains the regions-file and FASTA-name/region
alternatives and names the admitted FASTA. Prompt labels use semantic terminal
color, defaults are dimmed, and plain output says `Press ENTER for VALUE`.
No-write completion now says `Preview complete; Project not created` and labels
the complete replay command as the next action; only publication says `Project
ready`. The Quickstart explains that EMRYS does not generate the reference pair,
what each file contains, what to do when it is absent, and how FASTA selectors
relate to headers. Focused onboarding checks pass locally; novice Viking/PTY
acceptance remains required, so CV-U18 is **Verification pending**.

**September 17 adversarial audit:** The maintained Quickstart does not accurately
lead the implemented questionnaire. It says that the reference FASTA and GTF are
followed by the listed STAR and scientific answers, while the initializer next
requests the FASTQ directory, sample assignments and region selection before
collecting those answers. A novice following the guide literally can enter the
first documented value, `149`, at the FASTQ-directory prompt. Because an accurate
guided journey is part of this card's functional outcome, this is documentation
work rather than pending operator acceptance; CV-U18 returns to **Open**.

**September 18 approved alignment:** Quickstart now leads the implemented guided
interaction in its actual prompt order and retains the existing explicit sample
assignments, mutually exclusive partition choices and review-before-publication
handoff. The initializer itself did not change. Focused local checks pass; a
novice Viking/PTY walkthrough remains required, so CV-U18 is **Verification
pending**.

**September 21 guided-input compression:** For newly discovered samples, one
study-wide strand answer now fills the missing rows; `mixed` opens the existing
per-sample choice instead. Conditions and pairing groups remain explicit. When
exactly two conditions pass the existing paired-strata authority, Init shows both
directions and requires a numbered choice with no default. Ambiguous or
incompatible shapes retain the separate questions. Explicit `--sample` rows and
copied manifests are unchanged. Public preview/replay/publication tests cover the
new routing; novice Viking/PTY acceptance remains, so CV-U18 stays
**Verification pending**.

### CV-U19 Long-term interactive CLI

**Operator direction:** “Eventually the whole setup and even run process should
not be a user copy pasting commands in but an interactive cli prompt, with the
option for advanced manual usage by submitting a flag —advanced or similar”.

**Requested outcome:** Guided interactive setup and analysis launch should
eventually be the default. Advanced users retain an opt-in manual route.
`--advanced` is an illustrative flag, not a settled interface. The user explicitly
framed this as an eventual direction; no detailed prompt sequence or migration
plan was selected here.

**Current partial state:** Named Project initialization now provides the guided
input and scientific-question flow recorded under CV-U18, while the specialist
manifest command remains available. Doctor, Run and the complete setup journey
have not moved to the requested default interactive interface, and no advanced
mode transition has been selected. The operator explicitly deferred this
long-term interface direction until later; CV-U19 is **Deferred**.

### CV-U20 Complete Viking values in Quickstart

**Operator instruction:** “For the Quickstart, all of the expected values must
be provided IN THE QUICKSTART. This is explicit ‘run on viking’ instructions for
a naive user stop telling them to consult others or get info from analyst or
figure shit out just give the desired values whenever possible.”

**Requested outcome:** Provide expected values inline wherever possible for the
specific Viking journey. Do not send the reader to analysts, other people or
other documents to obtain values the guide can supply. Do not replace concrete
values with unexplained placeholders or leave the user to infer them. This
records the requirement; no new site settings or dataset-specific values were
selected during this discussion.

**Implemented values:** The Viking profile now selects:
account `viking-users`, partition `long`, QoS `normal`, one exclusive node,
all node CPUs/RAM, 12 hours, scheduler-selected node and private `/tmp` scratch.
The workflow and STAR indexing use allocation-based limits; other stages retain
the six-library EV/PUM1 settings. The packaged policy owns the full stage thread,
concurrency and memory map.

The guided EV/PUM1 continuation supplies all known study values inline: the six
`ABE_EV_2`/`ABE_PUM1_2`, `ABE_EV_3`/`ABE_PUM1_3`, and
`ABE_EV4`/`ABE_PUM1_4` assignments; pairing groups 2, 3 and 4; reverse
strandedness; primary-contig selectors 1–22, X, Y and MT; the delivered Novogene
reference decision; `sjdbOverhang=149` for the declared 150-base reads;
`genomeSAindexNbases=14`; `genomeChrBinNbits=18`; EV/PUM1 conditions; A>G; and
thresholds 1, 50, 0.05, 1.2, 0.005 and 0.01. Only the absolute FASTQ, FASTA and
GTF locations remain operator-supplied because they depend on where the delivered
files exist on Viking. The guide no longer sends this operator elsewhere to
obtain a known PUM1 value.

**Local verification:** The values reconcile to retained configuration,
scientific decisions, validation evidence and the current allocation-aware
resource policy. On the combined branch, 554 focused tests passed across onboarding,
normalization, execution profiles, resource policy, Doctor, materialization and
the hosted synthetic E2E; one platform-specific materialization case skipped.
The documentation gate passed for 169 Markdown documents and three Mermaid
sources, all 13 Quickstart Bash blocks passed `bash -n`, Ruff lint/format and
`git diff --check` passed. Existing cached dependencies and temporary package
metadata were used without installing dependencies.

Six isolated child-process cases were excluded because this machine's older
installed validation checkout lacks `simple_term_menu` or `coolname_hash`; the
current combined source passed its corresponding in-process coverage. A fresh
Viking novice walkthrough remains pending; the integrated standard CI recorded
above passed. No new cluster execution, performance benchmark, scientific review
or biological validation is claimed. CV-U20 is **Verification pending**.

**September 16 clarification and acceptance failure:** A reference FASTA and
reference GTF are external scientific inputs for a real-data Project; EMRYS does
not generate them. The synthetic Project supplies its own synthetic reference.
EMRYS may derive the STAR index and BED12 data and create or check reference
sidecars such as `.fai` and `.dict`, but those derived artifacts are not a
substitute for the matching FASTA/GTF pair. If either source file is missing,
the novice path must stop and say to obtain the correct matching reference and
annotation rather than guess or continue. Quickstart at that point named the
paths but did not explain this ownership or missing-input action adequately, so
CV-U20 returned to **Open**.

**Reconciled correction:** The current Quickstart states that the FASTA and
matching GTF are external inputs that EMRYS neither generates nor downloads,
tells the operator to stop if either is absent, and explains that selectors must
match the first words after `>` in the selected FASTA headers. It supplies the
complete PUM1 selector list while explicitly refusing to guess when a delivery
uses different names. The documented ownership and missing-input gap is fixed;
CV-U20 is **Verification pending** for a novice Viking walkthrough.

**September 17 adversarial audit:** The concrete Viking placement values recorded
as implemented are still absent from Quickstart. The account `viking-users`,
partition `long`, QoS `normal`, exclusive whole-node CPU/RAM request, 12-hour
limit and `/tmp` scratch policy exist in the packaged profile, but the guide only
says EMRYS supplies the settings. That does not satisfy the explicit requirement
to provide all known values **in the Quickstart**. CV-U20 returns to **Open** for
the promised inline values and reconciliation with the actual prompt order.

**September 18 approved alignment:** Quickstart now names account
`viking-users`, partition `long`, QoS `normal`, one scheduler-selected exclusive
node, all-node CPU and memory requests, the 12-hour limit and private `/tmp`
scratch. It labels these as supplied requests rather than measured performance,
and the questionnaire order now matches the product. Focused local checks pass;
novice Viking acceptance remains required, so CV-U20 is **Verification pending**.

**September 21 shorter concrete path:** Quickstart now directs the PUM1 operator
to enter study-wide `reverse`, explicitly choose the displayed `EV -> PUM1`
direction, enter `A>G`, and accept the disclosed values `1`, `50`, `0.05`, `1.2`
and `0.005` once. With no background cohort, `0.01` remains visible and persisted
as inactive rather than becoming another question. All known values remain in
the guide; novice Viking acceptance is still required, so CV-U20 remains
**Verification pending**.

### CV-U21 Technical parameter assistance

**Operator instruction:** “There should be a tool for determining sjdb overhang,
genome sa index nbases, etc. whenever possible”.

**Requested outcome:** Provide assistance that determines `sjdbOverhang`,
`genomeSAindexNbases` and similar technical values wherever possible. Non-technical
users should not have to calculate or choose these values themselves. The user
did not specify formulas, a new command name or a particular implementation.

**Initial implemented outcome:** The Viking/PUM1 Quickstart retains its known study
values. For other data, guided initialization now derives missing STAR settings:
`sjdbOverhang` is the largest observed first-record read length across the
declared FASTQs minus one, and `genomeSAindexNbases` follows STAR's small-genome
formula from the admitted FASTA length, floored and bounded to a positive value
through 14. The prompt reports the observed read and reference bases, offers the
values as defaults, and preserves explicit overrides. Noninteractive setup uses
the derived values when only those two flags are omitted.

Preview reads at most one complete record from each FASTQ and streams the FASTA;
it does not add a full FASTQ hash or claim that the observed records prove a
variable-length file's global maximum. Creation retains its single full FASTQ
hashing pass.

**Initial local verification:** Focused tests cover interactive defaults, noninteractive
derivation, gzip input and the bounded first-record behavior. All 115
source-bound onboarding cases pass; the two isolated replay cases reproduce the
same older-installed-package mismatch on the integration baseline. Ruff
formatting/lint, documentation checks and diff checks pass. A fresh operator
exercise with non-synthetic variable-length reads remains required for that
implemented assistance.

**September 16 extension:** The same assistance principle applies to region
selectors: after the user supplies the reference FASTA, show or validate the
contig names that the selector prompt can accept. This is technical assistance,
not authority to choose biologically appropriate regions, a reference release,
or an annotation on the user's behalf. Prompt ordering must make the selected
FASTA available before this assistance is offered.

**Implemented extension:** Guided setup now parses the admitted FASTA once,
shows its contig count and a bounded name list before the selector prompt, and
immediately rejects an entered name or interval that the selected FASTA cannot
accept. The same in-memory contig summary supplies STAR's reference-length
suggestion rather than reopening the FASTA. Publication still freshly validates
the reference, annotation and selectors at its separate mutation boundary. No
biological selector or reference release is inferred. The implementation
checkpoint's standard CI recorded above passed. CV-U21 is **Verification
pending** for a fresh operator walkthrough.

**September 17 adversarial audit:** The installed `sjdbOverhang` assistance
examines only the first FASTQ record in each file and treats the maximum of those
records as the read length. A variable-length file with a longer later record
therefore receives a value that is too small; focused coverage explicitly
requires trailing records not to be read. This is a bounded sampling heuristic,
not reliable determination of the parameter requested by the card. CV-U21
returns to **Open** pending either a sound determination method or an explicitly
approved narrower outcome with safe validation and truthful presentation.

**September 20 approved repair:** No-write preview now labels `sjdbOverhang` as
automatic without reading FASTQ contents. Creation validates every record in
every declared plain or gzip FASTQ during the existing single raw-content hash
pass, finds the global maximum sequence length and freezes maximum minus one as
the numeric Project value. Explicit numeric overrides remain available and are
reported beside the observed automatic value. Malformed or truncated records
fail before publication without exposing sequence content. Focused local tests
cover later and R2 maxima, plain and gzip input, malformed records, deterministic
numeric publication, long records across streaming fragments, concatenated and
padded gzip, gzip integrity and
explicit override preservation. CV-U21 is
**Verification pending** for hosted CI and a fresh operator walkthrough with
non-synthetic variable-length reads.

**September 20 approved STAR-default completion:** Guided initialization no
longer asks a non-technical user for `genomeSAindexNbases`; it derives and shows
the numeric value from the stable admitted FASTA summary. A third technical
setting, `genomeChrBinNbits`, is automatic at creation: references with at most
5,000 sequences retain STAR's prior value of `18`, while more fragmented
references use STAR's bounded mean-sequence/read-length rule. Creation derives
the latter during the existing FASTQ validation/hash pass and freezes all three
numeric STAR values in the new Project. Explicit advanced overrides remain
available and visibly identified.

The generated replay command preserves omission of automatic STAR flags so an
observed preview value is not converted into an override. Reference-derived
values remain bound to the device, inode, size, nanosecond modification time and
nanosecond change time observed with the FASTA summary; a change through full
admission fails before publication. Existing Projects without
`genome_chr_bin_nbits` normalize to `18` without rewriting their files. The Step
`00a` validator adds a seventh exact check for the retained native value. CV-U21
remains **Verification pending** for hosted CI and a fresh operator walkthrough
with non-synthetic variable-length reads and a representative fragmented
reference.

**September 21 novice-default boundary:** The shorter questionnaire does not
extend mechanical parameter determination. STAR values remain derived as above;
`unknown` is a conservative strandedness fallback rather than a measurement,
comparison direction is explicitly selected, and the disclosed paired-CMH
values are existing ranking policy rather than inferred study truth. An active
background maximum joins the same disclosure; without a background condition,
the persisted `0.01` is visibly inactive. CV-U21 remains **Verification pending**
at its existing evidence ceiling.

### CV-U22 Smoke-project tool reuse

**Exact instruction challenged:**

> To reuse another Project's managed tools, first follow
> [sealed runtime reuse](../operations/RUNBOOK.md#reuse-prepared-managed-tools)
> before this Project has an inventory.

**Operator response:** “If they are following the Quickstart they will have just
run the synthetic smoke project and prepared all the tools this should assume
those will be used.” The operator identified the detour as contrary to repeated
instructions.

**Requested outcome:** Make reuse of the smoke project's prepared tools the
normal continuation into the real analysis. Include any required steps and values
directly in Quickstart. The user must not need a separate advanced procedure or
understand “sealed runtimes” and inventory timing to follow that continuation.
This is a request to carry already-prepared tools through the ordinary journey,
not merely to rename the link to the separate guide.

**Additional reported failure:** After successful synthetic setup, the real-data
Quickstart still defaults to preparing another managed runtime despite an
existing installation.

**Expanded requirement:** Discover and validate a compatible existing runtime
before invoking package installation, and reuse it when compatible. Install tools
only when needed. Retain the required Project-specific readiness checks; tool
reuse must not be presented as permission to skip them. Reuse belongs in the
standard Quickstart flow, not an optional Runbook detour. This expands the
expected smoke-project reuse into an explicit discover/validate/reuse-before-install
requirement; no discovery mechanism was selected in this findings collection.

**Implemented:** The ordinary Quickstart now previews and selects the prepared
`emrys-smoke` runtime before Doctor. Selection freshly probes and content-binds
the source generation and installs nothing; Doctor retains Project, storage and
placement readiness checks. An absent inventory remains the normal first
selection. An existing inventory is preserved unless the operator explicitly
requests a same-source shared replacement.

**Verification limit:** Public preview, selection, content-binding and
verification-only Doctor cases passed the integrated standard CI. A fresh
institutional smoke-to-study reuse journey remains pending, so CV-U22 is
**Verification pending**.

**Latest journey boundary:** The synthetic E2E is optional. When it is chosen,
reuse its compatible prepared tools in the real Project as above. The direct
real-data path must also work without a smoke Project and must not require an
invented donor. Both paths retain explicit runtime discovery, compatibility and
Project-readiness checks. This changes the Quickstart routing requirement, not
the immutable-generation or explicit replacement safeguards.

**September 17 adversarial audit:** Runtime reuse remains an operator-chosen
alternate path rather than discovery before installation. The numbered
Quickstart first presents `emrys doctor --repair` as the fastest/default route
and only afterward tells a reader who completed the optional smoke test to run
runtime discovery instead. Following the ordinary sequence can therefore
prepare another managed runtime before compatibility with the smoke runtime is
checked. This does not satisfy the recorded discover/validate/reuse-before-
install requirement or make smoke reuse the normal continuation when smoke was
chosen. CV-U22 returns to **Open**.

**September 18 approved correction:** Quickstart now asks whether the optional
smoke Project was completed before presenting Doctor. When it was, runtime
discovery, compatibility checking and selection occur first; Doctor is the one
shared next step only after that admission. When smoke was skipped, the guide
does not invent a source Project and Doctor prepares the real Project directly.
The existing seal, freshness, explicit replacement and Project-readiness owners
remain unchanged. The exported `reuse_runtime_profile` programmatic boundary
was mistakenly described as test-only and retired while its implementation was
copied into the tests. The boundary and export are restored, and the runtime
reuse cases again exercise that production API directly. Focused local checks
pass; a fresh institutional smoke-to-study journey remains required, so CV-U22
is **Verification pending**.

### CV-U23 Repair restriction when sharing tools

**Exact wording challenged:** “That optional operation permanently disables
managed repair of the donor;”

**Operator questions:** “what does this mean? Why? Again with the unclear
language I told you to write in fucking English”.

**Concern recorded:** The instruction describes a significant loss of repair
functionality through unexplained jargon. In the intended Quickstart journey,
“donor” refers to the earlier smoke Project whose tools would be reused. The
assistant interpreted the sentence as preventing Doctor from repairing or
reinstalling that shared tool installation, and offered protecting other analyses
from tool changes as the intended rationale. That interpretation and rationale
were not independently verified. The original decision to make the restriction
permanent was not available in retained context.

**Requested outcome and unresolved question:** Explain the affected Project,
tools, lost capability and reason in plain English. The user's challenge to
permanence remains unresolved; this record does not establish that permanence
is necessary, approve removal of safeguards or select a replacement policy.

**Resolved policy and implementation:** Sharing no longer permanently disables
Doctor repair. Doctor never changes a sealed generation in place. It creates and
verifies a new managed generation, moves only the owning Project's current
selection, and preserves the old generation for retained Runs and Attempts.
Dependent Projects remain bound to their exact old generation and require an
explicit `runtime discover --from-project SOURCE --replace --execute`. The
replacement admits only an existing shared selector from the same source
Project and rechecks the new generation. Under the existing maintenance claim,
the shared no-clobber publication owner displaces and reverifies the admitted old
selector, creates the new selector exclusively, and refuses a competing name; it
does not use an overwrite primitive or discard a concurrent file.

**Verification:** Focused contract coverage now includes exact-file replacement,
same-source selection replacement, preserved old seals, generation planning and
stale-plan refusal. This slice adds 395 net product lines across five existing
owners, 302 net test lines across four existing test files, and 91 net lines
across eight existing documentation/owner-contract files. It adds no product
file, schema or dependency; the necessary growth replaces the permanent repair
refusal with generation creation, exact selector replacement and caller-complete
admission through the existing runtime and publication owners. Local compilation,
lint and documentation structure checks pass. A borrowed environment plus its
already-unpacked dependency cache passes 339 focused tests except for two
pre-existing isolated replay cases whose child interpreter cannot see that
borrowed cache. The integrated hosted standard CI recorded above passed. The
two-Project institutional smoke-to-study journey remains required, so CV-U23 is
**Verification pending**.

### CV-U24 Persistent CLI defaults

**Operator instruction and question:** “—site should not be a required argument,
should be able to be set in the .env or similar. What other values are currently
cli args that can but put in the .env?”

**Requested outcome:** A configured site should be usable without repeatedly
supplying `--site`. Support saved values through `.env` or a similar configuration
mechanism, and identify other repeated CLI values that can be supplied this way.
The exact file format, supported settings and precedence rules were not chosen.

**Implemented outcome:** `emrys setup` now asks for Projects home, site and an
optional application-log root. Its dry run shows the selected values;
`--execute` creates one ignored, mode-`0600`, repository-root `.env` without
overwriting an existing file. EMRYS loads the nearest marked file from the
current directory or its parents. The format accepts only
`EMRYS_PROJECTS_ROOT`, `EMRYS_SITE` and optional `EMRYS_LOG_ROOT`, plus its
version marker. Unknown, duplicate, incomplete, unsupported and unsafe values
fail before any setting is loaded.

The precedence is explicit CLI, existing process environment, `.env`, then the
built-in default. The saved site feeds existing `--site` arguments, the Projects
home feeds existing bounded cross-Project discovery, and the log root feeds the
existing logging controls. Selected Project, execution profile, runtime and
scientific values remain Project- or command-owned and are deliberately excluded
from global defaults. Quickstart performs prompted setup once and no longer
repeats `--site viking` or shell exports for Projects home.

**Local verification:** Focused tests cover prompted creation, mode and exact
closed bytes, parent discovery, optional log-root loading, process-environment
precedence, unknown-key rejection, dry-run behavior and no-clobber publication.
All 117 source-bound onboarding cases and 141 execution-profile, Run-location
and application-logging cases pass. Two isolated replay cases and one isolated
logging smoke case reproduce their older-installed-package mismatches on the
integration baseline. Ruff formatting/lint, documentation checks, all 14
Quickstart Bash blocks and diff checks pass. A fresh Viking reconnect and novice
walkthrough remain required; CV-U24 is **Verification pending**.

### CV-U25 Repeated FASTQ hashing during Init

**Operator finding:** “emrys init performs three full FASTQ hashing passes across
preview and creation, adding substantial I/O and setup latency for large
datasets.” The requested follow-up is to consolidate overlapping verification
work while preserving exact input identity, change detection and required checks
at publication boundaries.

**Explicit target:** “For preview → creation, we should aim for one full hashing
pass.” The supplied direction is that preview checks settings and paths without
scanning every FASTQ, while `--execute` hashes once and reuses that verified input
state through creation, preserving checks for input changes.

**Required boundaries:** Reducing full-file reads must retain exact input
identity and the necessary change/publication checks. This records a performance
target and the operator's proposed flow, not proof that a particular reuse method
is safe. The three-pass count and I/O impact were supplied as findings; no new
read-count or timing measurements were made during this recording task.

**Selected implementation:** No-write preview validates manifest structure,
scientific assignments, selectors and path availability without hashing FASTQ
contents. Creation admits and hashes each FASTQ once, retains its device, inode,
size and nanosecond modification time, and reuses the admitted Project through
compatibility checking and create-absent publication. The existing publication
owner verifies exact prepared manifest, profile and Project bytes. Observable
input identity must remain unchanged immediately before `project.yaml` is
published and again on return; the former second full Project admission is
retired.

**Verification limit:** A focused invocation-counter fixture requires zero
FASTQ hashes for preview and exactly one per FASTQ for creation, with a separate
mutation-boundary refusal. Comparable large-input timing and a Viking exercise
remain required; the implementation passed the integrated standard CI and the
card is **Verification pending** until that evidence is supplied.

**Interactive-flow consequence:** If onboarding becomes one
collect-review-confirm-publish transaction under CV-U18, it must retain this
same zero-full-hash preview and one-full-hash creation contract. Eliminating the
large replay-command handoff must not add another FASTQ scan or bypass the
publication-boundary identity check.

**September 17 adversarial audit:** The retained FASTQ snapshot binds device,
inode, size and nanosecond modification time, but not ctime or current content.
A same-inode, same-size rewrite whose mtime is restored can therefore change
FASTQ bytes after admission while both publication-boundary comparisons still
succeed. The focused mutation case substitutes the refusal rather than
exercising that real rewrite, so it does not protect the claimed exact input-
identity boundary. This is an implementation gap, not pending timing or Viking
evidence; CV-U25 returns to **Open**.

**September 20 approved repair:** The retained input snapshot now also binds
nanosecond change time. The publication test performs a real same-inode,
same-size FASTQ rewrite, restores mtime and verifies that the production
boundary refuses `project.yaml`; it no longer substitutes a mocked refusal.
FASTQ structure validation and maximum-read measurement observe the same raw
chunks used by the sole content hash, and the resulting immutable sample
admission is reused by full Project admission without reopening a FASTQ.
Preview still reads zero FASTQ content. Focused local tests cover exact observer
bytes, one execution hash per FASTQ, mutation during stable reads and restored-
mtime post-admission mutation. CV-U25 is **Verification pending** for hosted CI,
comparable large-input timing and a fresh Viking/operator exercise; ctime is the
accepted ordinary-filesystem post-hash mutation boundary and is not claimed as
protection against privileged tampering that can forge filesystem metadata.

### CV-U26 Manifests inside the Project

**Operator instruction:** “There should be a single directory per project, that
contains the manifests instead of having the in a sibling dir”.

**Requested outcome:** Keep a Project's manifests inside its own directory, with
the Project's other files. The ordinary setup and Quickstart flow must not require
a separate sibling directory for those manifests. This is distinct from the
Projects-home location in CV-U07: the home is inside the parent repository, and
each Project contains its own manifests. The exact internal subdirectory names
and any treatment of existing Projects were not specified.

**Selected implementation:** New named Projects publish `samples.tsv` and
`partitions.tsv` beside `project.yaml` and reference them by relative path.
Guided setup generates both in memory; advanced setup copies validated,
path-normalized content from a supplied manifest pair. FASTQs, references and
regions files remain external durable inputs. Existing Projects continue to use
their current manifest locations and receive no automatic migration.

**Verification limit:** Hosted onboarding and validation fixtures cover exact
manifest bytes, relative Project references, external input preservation and
existing-Project compatibility. Institutional operator acceptance remains
required; the integrated standard CI passed and this card is **Verification
pending** until that evidence is supplied.

### CV-U27 Tested smoke-to-real resource guidance

**Operator finding:** “The walkthrough has exposed a real quickstart gap:
getting from a successful smoke test to real data still requires expert resource
planning and manual Slurm investigation.”

**Required supported path:**

- A tested resource profile with clear workload limits.
- Doctor checks that identify missing or incompatible site settings.
- An exact submission command once those checks pass.

This guidance belongs in the Viking/PUM1 Quickstart journey. A successful smoke
test must lead into a usable real-data path without the operator becoming a
scheduler expert or authoring a resource configuration. No new resource values,
workload limits or claims of profile testing were established during collection.
CV-U28 retains the fixed historical settings as provenance while making the
current allocation-aware policy authoritative.

**Approved implementation:** Synthetic and real-data Viking initialization now
inherit the current allocation-aware policy automatically. Doctor and Run use
the existing shared admission and preview owners, and the Quickstart proceeds
through `emrys doctor --repair` then `emrys run`. Existing Projects can create a named
Viking profile and select it consistently for both commands. Explicit profiles
and frozen Run policies are preserved. The documented historical workload is
six EV/PUM1 libraries; it supplies provenance for configurable minima, not a
fixed current policy or workload-size guarantee.

**Verification limit:** The packaged/default-profile, onboarding, Doctor,
submission and hosted synthetic cases passed the integrated standard CI.
Institutional smoke-to-real execution and operator acceptance remain pending;
CV-U27 remains **Verification pending**.

**September 17 adversarial audit:** The saved `EMRYS_SITE=viking` setting
selects Viking placement when a new profile is created, but Doctor diagnoses an
existing Project from that Project's selected profile without checking
compatibility with the saved site. An existing direct-placement Project can
therefore pass direct Doctor checks and run directly while the operator's saved
site remains Viking, with no missing/incompatible-site diagnostic. Because
identifying incompatible site settings is part of this card's required path,
CV-U27 returns to **Open**. Existing hosted profile and submission checks remain
valid evidence for the behavior they cover.

**September 18 approved correction:** Doctor now checks the saved `viking` site
when the Project's default profile is implicit. A direct default produces a
no-write execution requirement with exact choices to create/select a Viking
profile or explicitly retain direct placement for both Doctor and Run. An
explicit `--profile` remains authoritative, and a matching implicit Viking
profile passes through the existing profile and storage admission. No profile is
rewritten and Run identity is unchanged. Focused local checks pass;
institutional smoke-to-real execution and operator acceptance remain required,
so CV-U27 is **Verification pending**.

### CV-U28 Allocation-aware resource policy and historical provenance

**Operator instruction:** “Stage thread caps and other configuration options are
wrong, ideal config must be recovered from past runs and the whole giant fucking
benchmarking process we did”.

**Reported regression:** The operator reports a pipeline taking **8 hours instead
of the expected 4 hours**, attributes the loss to changes in the historical
per-stage configuration, and requires retaining those historical configurations.
The operator emphasized the many hours already spent optimizing wall time and
challenged the introduction of resource limits without their instruction.

**Original requested outcome:** Recover the desired per-stage settings and other relevant
configuration from the previous runs and benchmarking work, and retain that
configuration. Preserve wall-time optimization as the objective. Replacing those
settings with newly guessed caps would not address the requirement.

**Earlier restoration decision:** The operator's observation that the historical
policy performed better is sufficient to select it as the default. Another benchmark
or controlled comparison is not a prerequisite for restoration. The reported
8-hour/4-hour timing remains operator evidence, distinct from local software
checks.

**Historical recovery:** Review covered all 78 remote `perf` branch heads and
their historical resource/configuration and benchmark paths. Seventy-two heads
retained identical EMRYS resource blobs; six older NORAD heads retained the
conservative example. The unqualified `configs/local_pilot_resources.yaml` has
no tracked history. The `.example.yaml` was the conservative four-core policy;
the desired policy was `configs/local_pilot_resources.csu_viking_ev_pum1.yaml`,
introduced by `92863824`. It moved into the execution profile in `d6e54aff`;
`5f42c8c4` retired the old filename without losing those computational values.
The current [Viking profile](../../configs/execution_profile.csu_viking_ev_pum1.yaml)
now applies CV-U06's allocation-based workflow/STAR limits; the original policy
used 12 workflow cores, 524288 MiB workflow memory, 12 STAR-index threads and
262144 MiB STAR-index memory, with 256 CPUs requested outside the workflow.
Other recovered stage values and later one-thread declarations for 09/10 remain;
the retired, inactive reporting-memory map is not reintroduced.

The 46 perf branches carrying the benchmark harness contained 11 harness
versions; their fixed per-case budgets were not an alternative whole-Run policy.
The older per-stage Slurm wrappers and the VM trial at `f054ddee` were separate
execution contexts. The restoration selected the six-library Viking policy,
including its per-stage memory and concurrency, rather than mixing those contexts.

**Approved native-memory follow-up:** Increasing an admitted stage allowance
now raises STAR index/sort limits, samtools fallback-sort buffers, and
Picard/GATK heaps. The existing
[command-construction owner](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
derives the native budget once; worker owners translate it to tool units.
The operator approved up to 40 net added product lines across seven existing
files, with focused tests and documentation and no new product file or
dependency. Existing argument validation is reused; redundant local thread
plumbing is removed. No second resource policy, schema, recovery state, or
scientific setting is introduced. This follow-up leaves `workflow_memory_mb`
for the operator's separate change. Native-limit wiring does not establish
measured speedup or institutional memory qualification.

**Native-memory local protection:** All six worker fixtures passed, including
larger native limits and invalid-budget refusal; 31 planning/identity/resume
checks and 22 shell-interface checks passed. Twelve selected task-boundary
checks passed; three more reached isolated Python subprocesses that loaded the
machine's older installed checkout and failed on missing `simple_term_menu`.
They require the normal hosted environment. Shell fixtures used the existing
Python launcher in place of this worktree's absent `.venv`; no dependency was
installed. Ruff, shell syntax, documentation structure and whitespace checks
passed. The product delta is 26 net lines in seven existing files; native-tool
execution and full regression checks remain with hosted CI.

**Historical restoration and protection:** At restoration, the packaged defaults
matched the retained profile exactly, and Viking requested 256 CPUs, exclusive
allocation and 12 hours. CV-U06 records the subsequent full-allocation change.
The existing admission, scheduler,
preview, override and immutable-resume owners are reused without new product
code paths, schemas, files or dependencies. The retained historical profile
provided the historical evidence described above. Small symbolic-admission
and hosted-E2E budgets are explicit fixtures rather than implicit product defaults.

**Local verification:** 733 checks passed: 695 across `test_execution_profile`,
`test_resource_policy`, `test_onboarding`, `test_doctor`,
`test_submission_inspection`, `test_slurm_submission` and `test_real_synthetic_e2e`;
38 materialization checks selected with `resource or slurm or standalone_report`.
Ruff lint/format, documentation structure and `git diff --check` passed.
These used this worktree's source and build-generated package metadata with
existing cached dependencies; no dependencies were installed. Two
`test_guided_project_preview_replays_exact_answers_without_new_prompts` cases
were excluded after isolated subprocesses selected the machine's older installed
checkout and failed on its missing `simple_term_menu`. Full standard CI,
including those cases and the active managed golden path, passed in the integrated
run recorded above. The configured real-synthetic E2E lane was skipped, and the
institutional walkthrough remains pending. No cluster job or new performance
benchmark was claimed; CV-U28 was **Verification pending** at that checkpoint.

**September 17 adversarial audit, conflict now resolved:** Historical recovery
established a fixed policy with 12 workflow cores, while the integrated product
subsequently replaced that workflow/STAR policy with CV-U06's allocation-aware
limits. The repository also states that the new sharing policy is not known to
be optimal and may increase wall time; no retained Viking comparison establishes
that it satisfies the original instruction to restore the benchmark-derived
policy and wall-time behavior. This was a conflict between accepted outcomes,
not merely missing external verification. CV-U28 returned to **Open** at that
checkpoint pending an explicit owner decision.

**September 21 superseding owner decision:** The current allocation-aware
workflow and memory ceilings, workload-aware concurrency and shares, and derived
native-tool controls are authoritative. Historical per-task memory minima remain
current only where the active profile declares them. The fixed 12-core policy,
its 524288 MiB envelope, and the reported eight-hour/four-hour observation remain
provenance; they are not current defaults or evidence of comparative performance.
Restoring the fixed policy and reproducing or benchmarking the historical timing
are no longer acceptance requirements.

Ordinary institutional Doctor and Run execution on one exact installed revision
must show that the current symbolic policy is admitted and resolves from the
actual allocation. That verification does not need a fixed-policy comparison and
does not establish optimality, utilization, speedup, safe peak memory for every
dataset or scientific acceptance. That ordinary institutional execution remains
pending, so CV-U28 is **Verification pending**.

### CV-U29 Early Inspect and dashboard feedback

**Operator finding and question:** “Inspect/dashboard take way too long to
populate; we need to show at least something faster. What starts logging early
that can be used?”

**Requested outcome:** Present useful early information while full inspection or
dashboard content is still being populated. The user must be able to see that
submission or preparation is progressing rather than encounter a prolonged empty
display. This complements the duplicate-submission concern in CV-U12 and is
separate from the readability of a fully populated Inspect view in CV-U01.

**Question retained for follow-up:** Which existing records become available
early enough? The discussion identified the application log opening before
“Preparing analysis,” submission records and an accepted Slurm job ID as possible
sources. These are leads from the earlier discussion, not a selected presentation
design or measured proof of the current population delay's cause. No timing
target or logging change was specified.

**Implemented software outcome:** The ordinary watch command can select a
retained submission before a Run exists and immediately presents its recorded
request, scheduler observation and dated diagnostic stream. During refresh it
keeps the dated prior observations visible and states that refresh is in progress
instead of showing an empty view. Focused pre-Run and refresh fixtures passed the
integrated standard CI. No Viking population-time measurement was made, so
institutional timing and operator acceptance remain pending and CV-U29 is
**Verification pending**.

### CV-U30 Dashboard color and pane layout

**Operator report:** “Lost a lot of color from the original dashboard, and also
formatting/pane layout.”

**Specific layout requirements:** The pane at the top must be taller so that it
can display all its fields. Information at the bottom should run horizontally
across the full screen width instead of making that portion of the display so
tall. Restore the lost color and formatting from the original dashboard.

This concerns the overall dashboard layout and information visibility. The
friendliness and color of the log content remain separately recorded in CV-U14.
No exact pane heights, color palette or terminal-size policy was specified.

**Implemented software outcome:** The job/resources/Run panel now grows to the
number of fields it must display, preserving every identity and resource row on
the tested compact layout. Distinct title, panel-title, label, value, success,
warning and failure styles restore visual structure, while the controls and
dated-status information use the full-width footer area. Wide, compact, small,
plain and colored rendering fixtures passed the integrated standard CI.
Institutional terminal-size and operator acceptance remained pending.

**September 16 repeat finding:** The dashboard and its logs were still reported
as monocolored on Viking. Colored headings alone do not satisfy the requirement;
status, severity, progress and log events need restrained semantic styling with
a readable plain/`NO_COLOR` rendering. This is negative visual acceptance for
CV-U30 and the log-specific CV-U14, not a new palette selection.

**Approved table-hierarchy refinement:** Pipeline rows now style step, stage,
count, elapsed and state as separate fields instead of painting each row one
semantic color. State remains the primary success/warning/failure signal, while
headers and identifiers remain distinguishable. This supplements the existing
pane layout without changing its plain rendering. Viking visual acceptance
remains pending, so CV-U30 is **Verification pending**.

### CV-U31 Dashboard automatic Run selection

**Operator requirement and question:** “Dashboard is supposed to be able to auto
select the current run without needing params. What else did we silently lose
from dashboard functionality?”

**Requested outcome:** The dashboard should be able to select the current Run
without requiring selection parameters. Preserve this expected convenience
alongside the explicit job-ID/job-name entry direction in CV-U13.

**Unresolved completeness question:** Record the concern that other original
dashboard functionality may have been lost. The reports identify color/layout,
automatic selection, resource-usage display and working-directory convenience;
they are not a verified complete regression inventory. No comparison was
performed during this recording task, and no new rule for ambiguous selections
was chosen.

**Implemented selection:** The ordinary watch command reuses the existing Run
locator. One Run is selected without parameters; several Runs open a picker and
automation must provide an exact human name, full ID or unique prefix. Retained
submissions use the same one-or-picker rule before Run creation. No timestamp,
directory order or scheduler text chooses a latest Run.

**Regression inventory:** Source comparison confirms that installed watch still
reuses the legacy overview/detail renderer, pipeline history, sample lanes,
timings, activity, scheduler discovery, historical accounting, offline streams,
refresh control and resource fields. The reported color/layout regression is
CV-U30, resource visibility is CV-U33, mouse behavior is CV-U16, log styling is
CV-U14 and action wording is CV-U15. No additional lost legacy behavior was
identified in this bounded source audit; Viking/operator comparison remains
required. The integrated selector, regression-inventory and rendering cases
passed standard CI, so completeness is not claimed and the card is Verification
pending.

**September 16 Viking acceptance failure:** Plain `emrys watch` did not select
the intended job or offer a selector, and the operator had to enter the numeric
Slurm job ID manually. The working directory, discovered candidate roster and
exact request state were not supplied, so this record does not infer the cause.
Ordinary no-argument watch must select the sole admissible current target or
show a picker when several targets are admissible; raw scheduler-ID entry is a
diagnostic fallback, not the novice route. CV-U31 returns to **Open**.

**Approved paired correction:** The CV-U13 scheduler fallback correction also
closes the identified no-Project selection gap for this card without creating a
second monitoring owner: sole candidate selection and multi-candidate picking
remain in `emrys watch`, while raw dashboard discovery rejects ambiguity. The
Project Run/request one-or-picker behavior is unchanged. Local focused coverage
passes (249 tests); Viking must still demonstrate the intended no-argument
selection, so CV-U31 is **Verification pending**.

**September 17 adversarial audit:** Outside a selected Project, Projects-home
discovery inventories only existing Runs, not retained pre-Run submissions. If
a historical smoke Run exists while a new real-data submission is queued or
preparing, plain `emrys watch` can select or offer the old Run and never reach
the current submission. The raw scheduler fallback is reached only when no
Project Run exists and begins from the current user's scheduler roster rather
than an admitted EMRYS request roster. The intended current-target selection is
therefore not source-complete; CV-U31 returns to **Open**.

**September 18 caller-complete correction:** One Project inventory now treats
each retained submission as the scheduler identity and carries its admitted Run
association in the same target. A Run is offered separately only when no exact
request represents it. Multiple requests for one Run remain distinct picker
choices instead of collapsing to the newest or silently becoming Run-only.
Both `emrys watch` and Run-selected `inspect --watch` use this selection path.
The focused local suite passes; standard CI and the intended Viking terminal
exercise remain pending, so CV-U31 is **Verification pending**.

### CV-U32 Dashboard independent of working directory

**Operator instruction:** “Should not need to be in the specific project dir to
run the dashboard”.

**Requested outcome:** The operator can open the dashboard from outside the
selected Project's directory. Changing into a particular Project directory must
not be an ordinary prerequisite. This requirement coexists with automatic
selection (CV-U31) and explicit selection (CV-U13); the Project-discovery
mechanism was not specified in this discussion.

**Implemented discovery:** `EMRYS_PROJECTS_ROOT`, already used by the operator
journey, now supplies a bounded read-only discovery root. Watch inspects at most
256 immediate children, admits only canonical real Project definitions and Run
directories, and then applies the same sole-selection/picker rules. It creates
no registry, selected-Project file or mutable state. `--project` remains the
exact alternative from any directory. CV-U07 still owns creation and the final
location of the Projects home; this card consumes that declared path without
creating it or moving existing Projects.

**Verification and limit:** Focused cases cover one Project, multiple Projects,
ambiguous noninteractive use and invocation without a current directory Project,
and passed the integrated standard CI. No institutional filesystem or terminal
exercise ran; the card is Verification pending.

**Tranche consolidation and accounting:** The four cards add no production
file, schema, dependency, configuration record or mutable selection state.
`watch` routes through the existing inspection/presentation owner, static and live
completion share one projection, and one terminal-selection helper replaces the
duplicated picker mechanics. The expert `inspect` surface and shared watch
parser/renderer remain necessary owners, so this bounded audit found no complete
production surface that these cards safely supersede. The current source-code
diff is 385 insertions and 42 deletions, a net increase of 343 lines; committing
that quantified exception requires the repository-owner approval recorded with
this tranche.

**September 17 adversarial audit:** The exact `--project` path remains a valid
supported subset, but automatic Projects-home discovery inventories only
existing Runs, not retained pre-Run submissions. From outside the selected
Project, a historical Run can therefore be offered while the current submission
remains invisible; with request-only state, selection falls back to raw
scheduler discovery without the Project/request binding. General no-parameter
use outside the Project is incomplete; CV-U32 returns to **Open**.

**September 18 caller-complete correction:** Projects-home discovery now
inventories retained submissions as well as Runs under each immediate admitted
Project. It applies the same 256-target refusal and picker as Project-local use,
creates no registry or current pointer, and performs no scheduler query while
enumerating candidates. Exact `--project` remains available. Focused local
selection checks pass; standard CI and institutional filesystem/terminal use
remain pending, so CV-U32 is **Verification pending**.

### CV-U33 Dashboard resource usage

**Operator requirement:** “I want resource usage back in the dashboard”. The
operator also emphasized “WE NEED TO OPTIMIZE WALL TIME” and objected to limiting
resource usage after substantial prior benchmarking work.

**Requested outcome:** Restore resource-usage information in the dashboard so
the operator can see how the running work uses resources. Preserve the established
wall-time objective for independently selected future tuning. Visibility of
usage and correctness of resource limits are related requirements, while the
allocation-aware policy decision is owned by CV-U06 and CV-U28.
The exact missing display fields were not enumerated in this batch.

**Implemented software outcome:** The visible job/resources panel retains
scheduler placement, allocated CPUs, per-task maximum RSS, bytes read/written and
average task CPU time when admitted accounting supplies them; unavailable usage
stays explicit. Its dynamic height prevents those rows from being clipped on the
tested compact layout. CV-U06/CV-U28 own the authoritative allocation-aware
resource policy separately. Resource-label, identity and layout fixtures passed
the integrated standard CI. Institutional accounting/display acceptance remains
pending, so CV-U33 is **Verification pending**.

**September 17 adversarial audit:** Once a retained submission is associated
with a Run, Project-local selection removes that request and watches the Run
alone. That Run-only path intentionally has no exact submission identity, so
scheduler state and usage become unavailable even while the work is active. The
accounting observer also invokes `sstat` only for roots still active in `squeue`,
making completed-job usage unavailable by construction. Preserving resource
rows in the renderer does not restore their data path; CV-U33 returns to
**Open**.

**September 18 identity and accounting correction:** Watch retains the exact
submission request after Run creation, so scheduler state and resource usage no
longer disappear at that transition. Active roots use the exact `sstat` batch
step; terminal roots use the exact `sacct` batch record. Both paths share metric
validation and require matching root observations before and after the usage
query. Duplicate rows, wrong ID/UID/cluster, malformed metrics and identity
drift leave the admitted root state visible while reporting usage unknown. The
shared renderer labels live samples and final accounting distinctly, and both
interactive and snapshot request watches ask for resources. Focused local fault
and rendering matrices pass; standard CI and institutional accounting/display
remain pending. Future wall-time tuning
and its measurements remain with the optimization campaign, not this card.

**Current source disposition:** CV-U33 is **Open**. The new cluster-scope
defect and its corrective acceptance are transferred to `SCHED-USAGE-01` in
the [main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up).
Resolving or explicitly narrowing that source outcome is required before this
card can become source-complete; institutional accounting/display acceptance
remains here. Canned scheduler responses do not resolve the defect.

## Additional Viking UX findings — 2026-09-16

This matrix holds findings from the same operator run only when no existing
CV/CV-U card already owns the defect. Recording them preserves the observation
and acceptance boundary; it does not authorize implementation, cluster work or
an evidence promotion. Related findings remain on their existing cards above.

| ID | Finding | Status |
| --- | --- | --- |
| [CV-UX-01](#cv-ux-01-doctor-live-progress-output-collision) | Doctor live progress collides with the next diagnostic line | Verification pending |

### CV-UX-01 Doctor live-progress output collision

**Observed Viking output:** During `emrys doctor --repair`, the live phase line
ended with `Slurm submission-to-return wait 0:00:00` and the next diagnostic
began immediately on the same terminal row as `Slurm submission records:`,
rendering `0:00:00Slurm submission...` with no separating space or newline. The
captured run then printed retained submission stdout/stderr paths and Slurm job
`621172`. This is a presentation defect; the screenshot does not establish that
the retained records or job identity were wrong.

**Acceptance:** Before ordinary stdout/stderr diagnostics are emitted, finish or
clear the live spinner/progress row and serialize the next record through the
same terminal-presentation boundary. The concise default should not emit verbose
submission-record paths, but `--verbose` must still render every retained detail
without collision, loss or reordering. Cover a real PTY with color, narrow-line
wrapping and `NO_COLOR`/plain rendering. Keep the timer and phase label readable
when the wait duration is zero. CV-U04 owns Doctor's broader presentation and
CV-26 retains its historical duration evidence; future measured tuning belongs
to the optimization campaign. CV-UX-01 remains **Open** until Viking/PTY acceptance.

**Implemented slice:** The shared live-progress owner now redirects ordinary
stdout/stderr through Rich's active display boundary, which clears and redraws
the row around diagnostics. Doctor passes its normal/verbose policy into the
submission transport: normal output hides transcript and scheduler-log paths,
while `--verbose` retains them. Real narrow-PTY checks cover color and
`NO_COLOR`, diagnostic ordering, a line boundary before `Slurm submission
records:`, and readable zero-duration timing. Focused progress, submission and
Slurm Doctor suites passed 418 tests locally. CV-UX-01 is **Verification pending**
for Viking terminal acceptance; the integrated standard CI passed.

**September 17 integrated presentation refinement:** The same serialized owner
now colors the phase key cyan, elapsed time dim, and terminal outcome separately
as success or failure. Plain output is unchanged and the narrow color/`NO_COLOR`
PTY regression remains passing. This adds no higher evidence; CV-UX-01 remains
**Verification pending** for Viking terminal acceptance.

## P0 outcomes

### CV-01 Managed golden path coverage

**Finding:** Hosted success missed conditions encountered on Viking (E01–E12).
**Acceptance:** The managed journey covers absent Slurm memory variables,
site rejection of explicit memory requests, unavailable UID lookup with
restricted environment export, Doctor qualification, real Snakemake startup,
failed-Run resume, cancellation during an active native task, inspection before
Run creation/during execution/during reporting, and compatible runtime reuse
across Projects. Exercise supported combinations and preserve distinct test,
hosted Slurm, and institutional claims. Gate new fixes with their regressions;
do not declare the suite complete from a success-only run.
**Owners/dependencies:** Existing managed golden path and real-Slurm journey;
each affected owner supplies fault cases. Depends on selected cards below;
test design begins alongside them. Coordinate `HARNESS-01` and `QUAL-02`.

**Selected coverage:** CV-02 adds native/R qualification failure and
compute-only/head requalification diagnostics to the existing focused tests.
Injected manager/scheduler faults are simulations. They do not complete the
managed golden path, establish an institutional result, or cover the remaining
cancellation, startup, reuse, and inspection outcomes.
CV-03 adds transport-failure cases that preserve a single submission, confirmed
or uncertain job identity, and the existing retained transcripts.

**Hosted reuse slice:** After the existing managed golden path verifies the
donor's scientific Run and reports, the same job creates a separate synthetic
borrower. It inspects the borrower before any Run, exercises no-write reuse
preview, seals/selects the donor through the public runtime command, and runs
the borrower's verification-only Doctor operation. The retained application
log must show readiness with no package-manager work, and the borrower must
have its own semantically admitted direct storage receipt. Its inventory must
bind the exact donor seal and selected Python; no borrower scientific Run is
created by this slice.

The comparison preserves donor non-managed file bytes and the complete
namespace/stable metadata except the explicitly created seal and directory
timestamps. Existing Doctor admission checks the fixed native/R content roster;
this does not claim a complete transitive environment hash. Explicit artifact
paths retain both Projects' diagnostics and qualification evidence without
uploading managed tools or caches. The original donor science/report oracle and
clean-checkout check remain intact. The actual Ubuntu journey passed the
combined standard CI recorded above.

**Coverage boundary:** Owner fixtures cover missing memory declarations, site
rejection responses, qualification faults and reporting transaction boundaries.
Real isolated processes cover Snakemake startup/login lookup and native signal
handling. These are not the corresponding institutional combinations. Existing
public failed-resume fixtures use scientific owner doubles; the separately
selected real-Slurm journey covers a pre-Task failed attempt and resume. Active
native cancellation through Snakemake and combined restricted export/UID lookup
now have the bounded fixtures below. Actual Slurm/site cancellation,
absent/rejected site memory policy and cross-node inspection still require
the corresponding institutional journeys. The integrated standard CI recorded
above passed the active managed golden path and all other active jobs. At that
earlier checkpoint, CV-01 was **Verification pending** for the corresponding
institutional journeys.

**Real-backend cancellation boundary:** The existing public materialization
harness now includes real Snakemake, Task-wrapper and separate native process
groups. A FIFO readiness handshake follows a native fixture's partial output;
only then does the test signal the isolated public Run process. Production
signal forwarding, native escalation and workflow grace periods remain in use.
The fixture checks group absence before lock release and receipt publication,
retained failed Task/start/log evidence and cleaned owned work. With CV-10's
current Linux abort contract, it also checks a positively closed interrupted
receipt, read-only resume preview and successful execution in a new Attempt.
Earlier records and verified outputs remain unchanged. Scientific effects and
readiness remain explicit test doubles; actual-tool descendant containment is
verified separately under CV-10.

The successful between-Task failure/resume case remains a separate defense.
Both public journeys passed the final CV-10 standard CI recorded below. Missing
prepared finalization or unclosed Task evidence still prevents resume. This
does not establish Slurm/site cancellation or recover historical interrupted
Runs.

The existing public failed-Run/resume journey also checks real report producer
publication boundaries through separate public inspection processes, as recorded
under [CV-21](#cv-21-reporting-in-progress-and-visibility).

**Combined batch-startup slice:** The real generated Bash wrapper now runs the
current capacity observer and Snakemake readiness probe together under simulated
allocation metadata. Its restricted export projection drops submitting-shell
memory values; no Slurm memory variables are supplied to the child. Capacity
uses process-visible memory while explicitly recording an unspecified scheduler
memory limit. Actual Snakemake version and empty-workflow startup run with
passwd lookup made unavailable: forwarding `USER` permits startup, while no
username produces the expected bounded failure. Both cases check private batch
and probe scratch cleanup without creating scheduler logs. The two cases pass
locally with Python 3.14.5/Snakemake 9.25.1; static checks and independent review
pass. This is real local Bash/backend evidence with simulated scheduler inputs,
not an allocation, site memory-rejection or institutional execution result.

**September 17 adversarial audit:** The hosted managed golden path remains a
successful direct-placement journey. Separate fixtures cover parts of the
required behavior, but the managed journey does not yet integrate the recorded
Slurm memory-policy rejection, actual controller cancellation, and cross-node
monitoring combinations required by this card. Those are source/journey coverage
gaps distinct from the later institutional rerun. CV-01 returns to **Open**;
existing hosted results remain valid for the narrower cases they exercised.

**Disposable Slurm prerequisite:** The separately selected real-Slurm CI lane
now configures a supported, version-matched client, controller, worker, and
accounting service and requires exact cluster-scoped observation before its
synthetic journey. That infrastructure alone does not exercise active-native-
Task cancellation or establish a Viking result.

**Selected source/journey slice (hosted CI pending):** The 130-pair real-Slurm
journey now inspects each qualified Project before a Run exists. It retains the
existing direct/Slurm pre-Task failure, public resume, final scientific oracle,
and report parity. In the Slurm Run, an additional resume enters a Task with a
test-gated, pinned real `samtools view` child: the adapter preserves that Task
invocation's options but substitutes a blocking FIFO for its input. The driver
admits the native process identity, Task start, exact recorded submission and
active Run; it exercises public submission/Run inspection, a watch snapshot,
a no-write stop preview and one public controller-filtered `stop --execute`.
It then requires the native child to exit, a terminal scheduler record, a
positively closed interrupted Attempt and Task, a no-write resume preview, and
a distinct public resume to real-tool scientific and reporting completion. The three Slurm
Attempts and their retained predecessors are checked explicitly; the direct
journey remains a separate two-Attempt parity comparator. A scheduler
`CANCELLED` state by itself never authorizes recovery. No hosted result for
this new journey is claimed until the selected exact-commit CI run passes.

Focused public-flow tests also cover an explicit-memory `sbatch` rejection
with one invocation, retained stderr and no new Run, and a real local
Snakemake/Task/native stop followed by public resume. The rejection response
and local stop's scheduler are controlled fixtures, not site memory-policy or
controller evidence. The selected hosted lane can establish only disposable,
single-node Slurm behavior. Absent/rejected Viking memory-policy combinations,
cross-node inspection, and institutional active-native cancellation remain
separate acceptance work. CV-01 is **Verification pending** for the selected
exact-commit hosted run and institutional memory-policy, cross-node, and
active-native cancellation journeys; none is claimed as passed here.

### CV-02 Individual qualification diagnostics

**Finding:** Generic qualification failure required manual reconstruction of
checks (E01, E03). **Acceptance:** Doctor retains and surfaces each failing
check's identity, phase/host context, expected and observed result, and relevant
exit/error details with a directly usable evidence path. Separate an unavailable
probe from a failed assertion. Keep normal output concise and full detail
available after exit. Reproduce a single native failure, R namespace failure,
and compute-only failure through the public flow.
**Owners/dependencies:** Doctor, runtime inspection, application logging;
coordinate CV-03, CV-04, CV-12, and CV-25.

**Selected implementation:** Preserve the existing runtime observations through
Doctor discovery, compute qualification, and head requalification, using the
existing maintenance log and scheduler stderr. Retain actual/expected process
exit status and R loader errors in the runtime probe owner. The repeated Doctor
failure projection is consolidated; probes remain read-only and the logging
library retains ownership of durable records. No new product file, dependency,
schema, receipt, or recovery rule is introduced. The approved exception permits
at most 100 net added product lines for the missing diagnostics; test and
documentation changes are accounted separately.

**Verification:** The focused runtime-probe suite passes locally (39 cases,
including an actual R 4.6.1 loader failure); changed Python files pass Ruff and
format checks. [Phase 1 CI](https://github.com/lab-cats/EMRYS/actions/runs/34914521139)
passed at `805d9abdb9ea5584dc1d1d81dfb1b71c75c8f168`, including Doctor's
public-flow regressions, the documentation validator, all Python 3.14 shards
and coverage policy, Python 3.11 compatibility, and managed golden path.
Scheduled/manual lanes retain their separate selection and evidence limits.
Institutional acceptance remains pending. CV-12's original cause remains
unresolved; these diagnostics do not reconstruct its missing observations.

### CV-03 Scheduler and execution failure messages

**Finding:** `sbatch failed` conflated scheduler rejection and a submitted job's
failure (E02, E03, E09). **Acceptance:** Identify inability to invoke the
scheduler, rejected submission, pending queue state/reason, compute-job failure,
cancellation, and head finalization failure separately. Include the known job
identity, underlying failure, and relevant logs. A nonzero waited `sbatch` exit
must not erase the distinction. Test each phase without duplicate submissions.
**Owners/dependencies:** Shared Slurm transport, Doctor, Run control, logging.

**Selected implementation:** The first slice distinguishes scheduler invocation,
submission-record failure, an unconfirmed submission response, and failure after
a canonical job ID was returned. It preserves escaped underlying diagnostics,
known job identity, and existing stream/transcript paths without retrying.
All four Control exception-translation wrappers are replaced by handling the
existing shared exception at public failure boundaries. No new scheduler
observer, command, file, schema, receipt, or recovery rule is introduced.
The approved exception permits at most 25 net added product lines across the
existing transport and Control owners; tests and documentation are separate.

**Verification and remaining scope:** Focused transport tests exercise real
tiny subprocess fixtures and injected scheduler responses, including nonzero
waited jobs, malformed responses, transcript failures, escaped diagnostics,
and exactly one submission. Public Control regressions passed CI. These are
simulations, not scheduler or institutional proof. CV-20 now supplies strictly
bound queue/accounting observations and CV-18 supplies the exact-request stop
path. Their actual queued/cancelled site acceptance remains open; the software
acceptance result is recorded below.

**Implemented head-finalization slice:** After an accepted qualification job,
head storage errors retain that job ID and the escaped storage/OS cause with
the existing maintenance-log path. Interruptions keep their existing behavior;
published evidence is retained. The final already-admitted observation also
rejects changed Project/package/runtime bindings without another read.
Existing Doctor fixtures cover retained-probe corruption, cleanup failure after
receipt publication, and final input drift with one submission and no success
event. Static checks and hosted behavioral execution pass.

**Six-phase acceptance audit:** Existing transport, selected-request inspection,
stop and Doctor owners cover the required phases through their public flows:

| Required phase | Existing path and direct protection |
| --- | --- |
| Scheduler invocation | Shared submission I/O diagnostics and tiny subprocess fixtures; public Run/resume/report failure boundaries. |
| Rejected submission | Nonzero response without confirmed job identity retains stderr and stream paths; one-submission tests. |
| Pending queue | Exact-request inspection/watch shows admitted state and escaped queue reason; no unselected scheduler query. |
| Compute failure | Accepted waited-job errors retain job/log context; public Doctor runtime/startup failures preserve qualification refusal. |
| Cancellation | Exact root accounting admits numeric cancellation states; public request inspection and stop retain their evidence limits. |
| Head finalization | Doctor reports accepted job identity and storage/OS cause; corruption, cleanup and final-input-drift cases retain receipts and failure. |

The audit found one presentation gap: Doctor retained terminal accounting state
and exit status in its existing optional timing observation but hid both from
normal output. The same summary now displays state, source and scheduler exit
status. No additional query, parser, formatter owner, command, schema or recovery
authority is needed. Public fixtures distinguish `FAILED`, `CANCELLED` and
`UNKNOWN`, and retain the original transport failure even if accounting says
`COMPLETED`. The full standard CI above passed, including the expanded public
Doctor and selected-request fixtures using the actual accounting parser.
CV-03 is Verification pending for exact-revision queued/cancelled site acceptance;
software coverage does not establish live Slurm behavior.

### CV-04 Workflow startup readiness

**Finding:** Tool probes passed before Snakemake's username lookup failed (E03).
**Acceptance:** Add or reuse a minimal, bounded Snakemake startup exercise in
the intended compute environment that traverses actual backend initialization
without running the study. Cover the restricted environment and absent passwd
entry. State the check's limits: successful startup is not complete science.
Keep package installation in explicit maintenance and avoid a second backend.
**Owners/dependencies:** Doctor, runtime inspection, workflow owner; CV-01/02.

**Selected implementation:** Extend the existing required Snakemake observation
with bounded empty-workflow startup after version admission. The selected
interpreter starts the real backend with local execution, one core, disabled
ambient profiles, and private disposable scratch. No study task, installation,
new check ID, receipt, schema, or backend is added. Existing probe diagnostics
and Doctor failure propagation retain startup failures at each host boundary.
The approved growth cap is 50 net product lines in the existing probe owner.

**Verification:** All 53 focused runtime tests pass locally, including six
actual Snakemake 9.25.1 startup cases with Python 3.14.5: ordinary startup,
unavailable UID lookup, and each supported login-name variable. Separate cases
exercise timeout, startup, and scratch failures. Public Doctor qualification
regressions passed the current integrated standard CI.
These local runtime and simulated qualification checks do not establish an
institutional result or scientific completion; those evidence limits remain.

### CV-05 Reuse versus repeated repair work

**Finding:** Doctor appeared to start over, but retry output showed native
installation reused and R restore completed quickly; verification still repeated
(E01, E08, E11). **Acceptance:** Plans and progress distinguish reused tools,
cached package work, checks that must repeat, and new install/repair actions.
Explain why repeated work is necessary and retain successful prior evidence
without claiming stale checks still pass. Cover unchanged retry, interrupted
setup, and a changed dependency/input. Show first-setup duration guidance and
queue time separately from work; retain CV-26's historical evidence while routing
future performance changes through the optimization campaign.
**Owners/dependencies:** Doctor and existing package-manager integration.

**Selected runtime-work slice:** One immutable-plan summary is reused in preview,
execution and the existing maintenance-start diagnostic. It distinguishes a
currently verified selected runtime with no package-manager work, preparation
of a missing managed inventory, and checking/updating tools selected by a
retained inventory. Missing inventory can follow interrupted setup; retained
files or caches alone do not prove usable packages. Actual package reuse and
changes remain in the manager's exact printed/recorded `package-output.log`.
No new probe, cache parser, receipt or skipped admission is introduced.

Focused public fixtures preserve no-write preview, retained cache/inventory
bytes, manager-free verification, identical manager commands and existing
failure/interrupt behavior; these passed the earlier combined standard CI.

**Queue attribution and setup guidance:** One optional terminal accounting query
extends the existing strict scheduler observer. The existing submission callback
now carries the response-recorded job ID and cluster caller-completely, without
rereading a transcript or changing submission success. Exact ownership, root ID,
cluster, planned name and maintenance streams must match. Ordered UTC dates,
zero restarts/suspension and consistent elapsed time support submitted-to-start
wait, eligible queue wait and allocation wall time. Incomplete or ambiguous
accounting stays unavailable. This is diagnostic timing, not scientific compute
time, qualification or recovery proof. Lookup has a separate bounded phase;
process-control exceptions during submission skip it. Optional observation
failures preserve the controlling outcome. The existing timing collector buffers
the result until maintenance outcome, in the same log.

Quickstart and runbook now cover unchanged retry, interrupted inventory creation,
changed tools/inputs and a planning allowance exceeding ten minutes rather than
a promised setup deadline. Actual package reuse remains the package manager's
report, and every required fresh check remains. Existing owners plus standard
library date parsing close the timing capability gap without a parallel parser,
new product file, command, dependency, persistent schema or mutable recovery state.
The complete standard CI above passed all 14 standard jobs with four configured
skips, including the expanded 22-case public Doctor fixture, all Python shards
and coverage, and donor setup/borrower verification in the managed golden path.
The optional timing cases preserve success, failure, interruption, exact stream
binding and receipt/revalidation behavior while separating query latency from
the waited submission timer. CV-05 is Completed for this hosted software
acceptance. The scheduler records in these tests are controlled fixtures, not
live Slurm measurements; comparable site setup/retry duration measurement and
performance changes remain independently selectable under the optimization
campaign. CV-26 retains the existing timing evidence.

### CV-06 Actual-data onboarding

**Finding:** Quickstart step 7 required legacy-file archaeology, many flags, and
manual translation despite recorded study settings (E07). **Acceptance:** A
novice can use a short guided path or import a supported existing study
definition, review its interpretation, and create a current Project. Preserve
explicit sample/mate assignments, biological pairing, reference and partition
identity, strandedness, and scientific thresholds; never infer pairing from
filenames. Unknown or unsupported legacy fields receive actionable diagnostics.
The normal journey stays on the head node, delegates Slurm automatically, and
places advanced paths outside the main walkthrough. Preserve old bundles.
**Owners/dependencies:** Onboarding/normalization, quickstart, configuration
guide; CV-07, CV-08, CV-14, CV-17. Import format is a design decision.

**Selected implementation:** Strengthen the existing guided path. No-write
initialization shows the admitted study interpretation and prints a safely
quoted creation command carrying every answer, exact parent, and current Python
interpreter. The novice reviews once and replays without another questionnaire.
Inputs are rechecked at creation. Existing explicit mate/biology admission and
scientific values are preserved; unsupported schemas keep their original
diagnostics with actionable current-format guidance. Existing Projects remain
supported in place. No new importer, flag, file, or automatic legacy mapping is
needed for this selected route. Product growth is 80 net lines under the user's
minimum necessary expansion approval.

**Verification:** Existing onboarding/normalization tests cover actual printed
shell replay with closed stdin, changed working directory, quoted paths,
arbitrary explicitly assigned mate names, background selection, direct/Viking
placement, exact scientific values, and preserved source bytes after schema
refusal. Static checks pass locally; application/subprocess cases passed the
current integrated standard CI. Institutional novice walkthrough remains
pending.

**Original-input manifest follow-up:** The operator's fresh-user walkthrough
exposed vendor FASTQ mates named `_1`/`_2` and 25 explicit whole-chromosome
`region` partitions that the drafting helper could not accept. The approved
bounded correction adds those mate suffixes alongside `_R1`/`_R2` and exposes
the existing selector through repeatable `--region PARTITION_ID SELECTOR`.
Existing `--regions-file` use and mixed selections remain explicit; IDs are
unique across the complete partition manifest. No study defaults are inferred.

The touched vertical is the existing onboarding CLI, its sample/partition TSV
contracts, Project normalization and reference checks, direct tests, and setup
guides. The audit found duplicated sample-path state and a separate rendering
projection in the helper; one draft row per sample replaces both. Existing
file admission, canonical mate identity, inode-reuse checks, compression and
complete-mate checks, required biological assignments, TSV validators, sorted
output and create-absent publication are preserved. The schema and downstream
scientific checks already support both selectors; no new validator, wrapper,
dependency, product file, or persisted state is needed. Scope ends at manifest
authoring and its admission into a Project. Scheduler/dashboard behavior and
scientific execution remain separate.

Regression fixtures use the public CLI for six vendor-style libraries and 25
chromosomes, existing naming forms, ambiguous mates, mixed selector forms,
duplicate IDs, no-write preview, destination preservation, and downstream
reference admission. Runtime execution of these fixtures passed the current
integrated standard CI. Institutional acceptance remains pending; the earlier
local test environment lacked their dependencies.

**September 16 novice-path acceptance failure:** The guided Viking run exposed
four unresolved onboarding gaps. First, the regions-file/selector instruction
does not explain the choice or connect selector names to the chosen reference.
Second, although Quickstart asks for a reference FASTA and GTF, it does not say
that a real-data operator must supply the matching external scientific inputs,
that EMRYS does not generate them, or that setup must stop if either is absent;
the synthetic Project is the separate case that supplies a synthetic reference.
Third, the prompt asks for selectors before collecting the FASTA/GTF, preventing
reference-informed contig assistance. Fourth, the final no-write preview emits
a large replay command without clearly saying that no Project exists yet or
making the required creation action unmistakable.

Defaults must be visible in dim/gray prompt text with a literal `Press ENTER for
VALUE` message that remains clear without color. Quickstart must use separate
copyable blocks for separate `emrys` commands and explain each command's
purpose, expected success signal and next action. The synthetic E2E is optional:
the fast novice route is real Project creation, Doctor/runtime readiness, Run,
Watch and Inspect. Choosing the smoke exercise still provides site confidence
and a compatible runtime-reuse opportunity, but skipping it does not skip the
real Project's readiness or evidence checks. These are negative institutional
onboarding observations; CV-06 remains **Open**.

**September 18 approved alignment:** The maintained Quickstart now matches the
implemented reference-first guided flow through FASTQ assignment, partition
selection and scientific settings; it also gives the exact site values and
current success signals inline. Provider checksums are retained as external
delivery records rather than presented as an unsupported initializer input.
Together with the previously implemented reference-informed selectors, visible
defaults and explicit preview-to-publication handoff, this resolves the recorded
source/documentation gaps. Focused local checks pass; institutional novice
acceptance remains required, so CV-06 is **Verification pending**.

**September 21 onboarding compression:** The actual-data flow now replaces
repeated strand and threshold questions with one disclosed study-wide strand
choice and one disclosed paired-CMH default-set confirmation. Pairing metadata
and control direction remain explicit, every effective choice stays in the
normal preview and replay, copied manifests remain literal, and decline,
noninteractive refusal, admission and no-write/publication boundaries are
preserved. Public-path fixtures cover persisted TSV/YAML and replay with closed
stdin; institutional novice acceptance remains required, so CV-06 stays
**Verification pending**.

### CV-07 Site and workload profile selection

**Finding:** Built-in site selection still required a hand-edited profile for
the actual workload (E07, E10). **Acceptance:** Provide a supported way to select
site placement and workload resources without Python snippets or hand-authored
Slurm YAML. Present the exact resulting settings, preserve explicit choices,
and distinguish a tiny fixture from a full cohort. Do not silently change
scientific parameters or promote an unbenchmarked preset as optimal. Qualification
submission size and resulting queue cost must be understandable.
**Owners/dependencies:** Execution profiles, onboarding, Doctor; CV-09/11/22.

**Implemented selector slice:** Doctor accepts the same default, named, or
absolute profile selection as Run/resume/report. Repair, private compute
qualification, and head finalization carry the admitted source and reject
binding drift through the final readiness observation. Invalid explicit
selections retain their diagnostic and never fall back. This does not change
runtime inventory selection, queue policy, or scientific settings.

**Implemented authoring slice:** `emrys profile create NAME` requires explicit
site or direct/Slurm placement, accepts existing workflow/stage resource flags,
and previews exact admitted settings before create-absent `--execute`.
Existing profile/default files are preserved. Placement-only profiles retain
resume policy; resource overrides save the complete reviewed policy. The
shared admission owner accepts bytes as well as stable files, so authoring
does not write a temporary profile or repeat scientific input reads. Guides
distinguish fixture defaults from unbenchmarked cohort choices and explain
that qualification uses the same allocation request and its queue cost.

**Verification:** Existing Doctor fixtures cover all selection forms, invalid
selection without mutation, exact private compute arguments, and selected
profile changes before submission, after the job, and during finalization.
Static checks and the integrated hosted standard CI pass. No actual cluster
qualification or workload tuning is claimed.

Profile admission passes 32 local tests. Public authoring fixtures cover direct,
Viking, and custom placement, exact settings, no scientific reads/subprocesses,
no-write previews, invalid choices, no-clobber destinations, parent replacement,
and default/published-byte drift. Application cases passed the current integrated
standard CI. The institutional novice walkthrough remains pending; no performance
optimum or actual capacity is claimed.

### CV-08 Compatible runtime reuse

**Finding:** New Projects defaulted to separate restoration; inventory copying
provided a manual verified reuse path (E08). **Acceptance:** Offer supported
selection of an existing compatible runtime, with exact version/content checks
and compute-node accessibility. Track dependencies on that runtime's location;
prevent a repair, removal, or upgrade from silently changing another Project's
execution environment. Handle incompatible or unavailable runtimes explicitly.
Prove two-Project reuse without repeating installation and reject changed tools.
Use existing admission and established package managers; no new cache/service
is assumed. Do not hard-link or copy trust receipts as a substitute for checks.
**Owners/dependencies:** Doctor, runtime discovery/inspection; CV-01/09/23.

**Implemented maintenance prerequisite:** Managed Doctor repair acquires a
durable `runtime/maintenance.lock` after diagnostic-log admission and before
plan re-admission or manager work. Existing claims block competing/retried
repair. Failure/interruption preserves acquired claims; successful completion
releases the exact owner before success logging. A release directory-sync
failure is reported even if unlink already removed the pathname. Verification
without package work does not acquire a claim. The existing reporting claim
and exclusive-writer mechanics move to their neutral publication owner with
all callers migrated and reporting's owned-partial cleanup policy preserved.

**Verification and remaining scope:** Twenty neutral tests pass locally,
covering short writes, ordered file/directory synchronization, contention,
replacement, redirected parents, failed acquisition/release and real process
termination. Doctor fixtures cover log-open failure, claim-before-manager,
retained failure/interruption, requalification, and release-before-success;
public Doctor/reporting execution requires CI in the current local environment.
Those maintenance checks alone do not establish safe sharing.

**Implemented sealed selection:** `runtime discover --from-project DONOR`
previews current probes and fixed content; `--execute` exclusively seals the
managed donor before publishing an absent borrower inventory. The closed seal
and three-column selector bind donor location, exact digest and borrower Python.
Selected native/R paths must remain inside the donor managed root. Doctor,
Run/resume and retained Attempt profiles use one runtime content-binding owner;
fresh fixed-content comparisons reject drift. Managed repair refuses a sealed
donor even with malformed/missing inventories or a stale plan. Interrupted or
failed publication preserves surviving claims/seals, and borrower failure does
not undo a seal. There is no unseal or cleanup command.

The 462 net product lines use six existing files and consolidate binding from
Doctor into runtime evidence, replacing all affected callers. Stable streaming
hashing and installed-package-tree identity reuse existing owners. New closed
seal/selector formats fill the expected-content gap that path inventories and
package managers cannot supply alone; no dependency or product file is added.
The baseline covers fixed executable/jar bytes and required R package trees,
not the entire environment, shared libraries or transitive dependencies.

**Verification:** Thirty-one focused seal/selector tests pass locally, as does
the source dependency gate. Public two-Project preview/publication, failure and
stale-repair fixtures plus planned Run/resume and direct lifecycle admission
passed the combined standard CI. The hosted donor-science/borrower-verification
journey is covered under CV-01, and the integrated standard CI recorded above
passed. CV-08 is **Verification pending** for institutional two-Project acceptance
and compute-node accessibility; no borrower scientific Run is claimed.

**September 16 discovery UX and repeated-work finding:** `runtime discover`
needs the same concise colored default and Boolean `--verbose` detail contract
as the other operator commands. Source review found that preview and
`--execute` are separate invocations that independently repeat discovery and
readiness probes; the dry run does not retain a reusable admitted plan. The
operator asked whether execution can reuse the work that preview just did.
Remove duplicate work only through a same-invocation confirmation flow or an
explicitly retained, content-bound plan with targeted freshness checks at the
mutation boundary. Execution must not blindly trust a stale preview or weaken
runtime-content, namespace, source-generation or borrower-publication checks.
This records the performance/interaction requirement and safe boundary, not an
approved persistence design. A direct real-data path must also work when no
optional smoke donor exists.

**Implemented same-invocation flow:** Interactive discovery now displays one
in-memory inspected plan and offers `Admit this runtime inventory? [y/N]`.
Decline and noninteractive omission remain no-write; `--execute` remains the
automation route. Confirmation reuses the previewed probes while rechecking the
Project, destination, exact source inventory and runtime content at the mutation
boundary. A newly published donor seal still receives its distinct post-seal
probe before borrower publication. No retained plan, cache, schema or cleanup
policy was added. The implementation checkpoint's standard CI recorded above
passed. Institutional reuse acceptance remains pending.

### CV-09 Qualification scope and placement

**Finding:** The operator could not tell what qualification covered or whether
different system-installed tools mattered; this contributed to cancelling an
already-started healthy allocation (E03, E08–E10). **Acceptance:** Explain the
selected managed/site runtime, validated environment, relevant node/platform
constraints, and checks repeated inside the actual allocation. Enforce those
constraints and reject real dependency/ABI/storage incompatibility. Permit
compatible eligible nodes; do not treat one previously successful hostname as
universal qualification or a required pin. Show user pins accurately.
**Owners/dependencies:** Doctor, runtime inspection, placement, Run preflight;
CV-04, CV-07, CV-11, CV-22.

**Implemented scope guidance:** Runtime ownership now documents the actual
diagnosis, compute, head-finalization, and execution boundaries, exact selected
tools versus system defaults, explicit pins versus scheduler eligibility, and
direct-host versus two-phase storage evidence. The guide states the x86-64
Linux managed-repair boundary and the limits of version/startup/namespace
probes; it does not claim complete binary compatibility from version strings.
Existing code rejects changed content, permissions, failed loaders/probes, and
incompatible storage at its admission boundaries. This documentation slice was
checked against those owners and existing direct/Slurm storage, runtime-change,
and capacity regression cases; it adds no new execution or installation. The
integrated standard CI recorded above passed. CV-09 is **Verification pending**
for institutional compatible-node/incompatible-runtime acceptance and any
concrete incompatibility gaps that evidence identifies.

### CV-10 External cancellation and recovery

**Finding:** Slurm cancellation left a nonterminal Run with unfinished task
state and no offered recovery (E09). **Acceptance:** Characterize normal
cancellation, TERM/KILL escalation, and lost wrapper/child processes. Account
for the delegated process tree; retain an honest terminal outcome and partial
publication evidence when possible. Use `emrys resume RUN` to complete an exact
prepared finalization after revalidating retained terminal evidence and ownership,
then apply ordinary resume admission. Process absence alone proves neither
closure nor ownership. Ambiguous state remains preserved and clearly explained.
Test interrupted native output, pre-entry state, publication boundaries, and
failure of finalization itself. Scheduler cancellation alone is insufficient
authority; never fabricate success or delete a lock to obtain resume.
**Owners/dependencies:** Slurm transport, lifecycle, task/publication owners,
inspection/control; CV-01, CV-03, CV-15, CV-18.

**Selected first slice:** Source review found that task signal handlers were
restored before terminal evidence publication. The existing task boundary now
retains its handlers through finalization and masks catchable signals only
during each exclusive terminal-record write. Hashing and revalidation remain
interruptible. A failed task stays failed; an interrupted record pair stays
incomplete and blocked. Existing caller handlers/masks are restored, and an
ambient mask that prevents task cancellation is refused before mutation.
This is 37 net product lines under the approved minimum necessary expansion,
with no new product file or recovery state.

**Implemented nested-cancellation slice:** Native execution uses the existing
signal controller from spawn through stream drain and group quiescence,
watching HUP/INT/TERM without throwing from its handlers. Children receive
watched signals unblocked; repeated signals cannot bypass cleanup. Closed
pipes do not prove process completion. The outer workflow allows native
cleanup time, but any forced or externally observed workflow SIGKILL retains
the Run lock and publishes no Attempt receipt because an independent native
session may remain. Typed native ambiguity also prevents workspace/lock
cleanup when another signal replaces the exception during handler restoration.
Only that cleanup-authority decision is masked; filesystem cleanup is not.

**Verification and remaining scope:** Eleven earlier isolated real-signal cases
cover producer interruption, successful/failed terminal-record writes, the
gap between records, mask restoration, re-entry, and SIGKILL. Execution is
covered by the passing combined standard CI at PR #198. The nested slice adds
real local process fixtures for repeated signals, the spawn/registration gap,
closed pipes, handler restoration, and lifecycle-to-Task-to-native cancellation.
They retain an actual live native PID after forced outer termination and check
the preserved lock/no-receipt boundary; their execution passed standard CI.
Ruff, formatting and whitespace checks pass. These source-derived protections
do not establish E09's cause or actual Slurm cancellation behavior. CV-01 adds
the separately bounded real-Snakemake/native-fixture observation.
Prepared-finalization and institutional cancellation acceptance remain open. No
Task or Run becomes recoverable solely because an outer group stopped.

**Wall-time observation and bounded prevention slice:** Operator-supplied
records for Viking job `621154` report `TIMEOUT` after `08:00:09` against an
`08:00:00` limit. The affected Step 06 scope had a task start without a terminal
result; final inspection retained remote lock ownership, found no terminal
Attempt receipt, reported no recovery, and instructed the operator not to
resume. The historical Run remains untouched. For future submissions, Slurm now
warns the batch shell with `TERM` five minutes before the limit; the generated
wrapper forwards that signal once to its exact EMRYS child and waits for the
child's actual exit. Existing lifecycle and Task owners remain solely
responsible for provable closure. Hard kill, missing/late warning, or finalization
without admitted prepared evidence retains the blocked ambiguity. Local wrapper
evidence is not a real Slurm timeout or institutional recovery result. Focused
local submission, dashboard, lifecycle, and Task interruption checks pass; the
full lifecycle/Task collection still requires a current installed-package test
environment for its isolated-module case.

**Supported recovery boundary:** The earlier fixed-start contract blocked every
entered Task without verified success, including clean cancellation. The
accepted Linux descendant prerequisite below now supports one complete
replacement across planning, Task entry, history inspection, backend admission,
receipts, reuse, reporting and presentation. An entered Task is retryable only
with a finalized, positively closed prepublication abort and unchanged current
inputs. Run identity and prior evidence stay immutable.

Same-input `run` still resolves to the same content-derived Run ID and refuses
its non-pristine destination. Processing reuse still requires a complete
successful source. `resume` remains the explicit recovery route. The approved
finalization extension uses immutable Attempt-local prepared receipt bytes;
it adds no public recovery command or mutable Run. Old record versions and
blocked receipts remain ineligible for retry. Lost worker evidence, missing
prepared finalization and E09 are not reconstructed from a released lock or
clean process group.

**Accepted descendant-containment prerequisite:** Use the existing fresh Linux
Task worker as a [child subreaper](https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html).
Linux reparents orphaned descendants to that
worker even after a child creates a separate session. The existing native runner,
signal controller and bounded TERM/KILL cleanup remain the owners; a dedicated
worker supplies the stronger child observation and signaling effects. Inline
callers and non-Linux workers retain their existing process-group boundary.

The standard library can call the kernel's established `prctl` interface without
a dependency. A cgroup would require a delegation contract absent from the
current launcher; a PID namespace would require separately admitted namespace
capability. A standalone init tool that exits with the main child does not by
itself prove that all adopted children have stopped. This fills the capability
gap in the existing Task owner without another supervisor executable, workflow
rule, policy schema or recovery action.

The stronger scope requires exclusive child-reaping ownership and normal
SIGCHLD handling and the required `prctl`/`waitid` capabilities. It retains the
main child's actual outcome and establishes `ECHILD` using a
[wait that includes Linux clone children](https://man7.org/linux/man-pages/man2/waitpid.2.html).
A zero nonblocking wait
result means children remain. `/proc` child lists select signal targets; neither
an empty list nor EOF establishes closure. The same bounded cleanup deadline
covers adoption and escalation. Observation, signaling or reaping uncertainty
preserves the existing ambiguity boundary.

Linux process fixtures and the unchanged canonical BAM producer with the
already-provisioned samtools supply the retained prerequisite evidence below.
The managed golden path retains their exact-revision results and tiny outputs.
The claim covers kernel descendant processes, not work delegated to a preexisting
external service or remote process. These checks do not explain E09 or supply
site cancellation evidence. Worker loss still supplies no positive closure:
native work/locks may remain with a
blocked receipt even when the outer Run lock can be released. No existing
blocked Task becomes retryable; the new protocol uses this verified capability
only in fresh Linux Task workers.

The implementation adds 162 net product lines in the existing Task owner.
Fifteen focused unit protections and the existing lightweight runner checks
passed locally, as did lint, format, documentation and dependency checks. All 32
selected cases, including the 17 Linux/native cases, then passed with no skips in
[CI 34993805649](https://github.com/lab-cats/EMRYS/actions/runs/34993805649).
All 14 standard jobs passed, with four configured skips. The native job tested
merge `f28a829ca894674f4e17d9e6f4bf618b7296ea1e`, containing PR head
`21992c732b44392cfe63528633a0e147b7979f85` and base
`94a13fbea639d769fb22b1e443ccdb78b536fdd7`.
The retained [artifact 10407865575](https://github.com/lab-cats/EMRYS/actions/runs/34993805649/artifacts/10407865575)
has SHA-256 `8e53347a597b2f6b081e9c965ab5259d6621674d2e1af3009a44ae0d1151bb3a`.
The four real samtools cases cover
one/two-thread success, canonical hard-link reuse and cancellation after an
observed real `sort` is deliberately stopped. That last fixture establishes
bounded stopped-native escalation; it does not claim ordinary unpaused site
cancellation or that output bytes existed before the stop. CI rejects skipped
real-tool cases and retains the actual output roster. Both real cancellation
rosters were empty; the synthetic descendant cases retained partial bytes.
Worker-loss evidence correctly retained no positive closure marker. This accepts
the bounded descendant-containment prerequisite, not the recovery protocol or
institutional cancellation behavior.

**Producer workspace prerequisite:** Producers now run with the existing owned
Task scratch directory as their working directory. Frozen file arguments stay
absolute; validators and semantic all-pass retain the Run-root working directory.
This contains incidental relative files in the same owned cleanup boundary.
In particular, locked STAR 2.7.11b [defaults its initial log prefix to `./`](https://github.com/alexdobin/STAR/blob/2.7.11b/source/parametersDefault)
before [genome generation moves the log into the index directory](https://github.com/alexdobin/STAR/blob/2.7.11b/source/Genome_genomeGenerate.cpp); early cancellation
could otherwise leave that file at the Run root. The central producer launch
replaces that behavior for all current owners without per-tool launch flags,
new directories or additional product lines. This is output-placement policy,
not a filesystem sandbox or new retry authority.

**Implemented closed-abort retry:** Task starts now live inside their original
Attempt's task tree (`task-start.v3`) and bind the complete original input
snapshot. A failed `task-attempt.v4` can record the single positive closure
`linux-task-prepublication.v1` only after the fresh Linux worker proves every
native descendant reaped, unchanged input bytes/identities and directory
membership, untouched publication destinations, owned cleanup and successful
directory synchronization. Publication is tracked before its first invocation;
rollback never restores retry eligibility. Expensive proof remains interruptible.
Worker loss, uncertain child state, incomplete cleanup, reused sidecars and
postpublication failures cannot earn closure.

The existing inspection owner admits all starts and terminal attempts in
supersession order. `attempt-receipt.v3` binds their cumulative exact references,
and every entered concurrent Task must close or verify before resume is offered.
`workflow-attempt.v4` freezes each new Task's exact latest abort reference;
planning, locked lifecycle admission, backend admission and Task entry reuse
the same history policy. Retained verified work keeps its original origin.
Selected-sample projections keep their original path and bytes without copying
or recreating missing historical evidence. Historical abort admission remains
valid after a successful retry publishes outputs; current retry readiness
separately checks unchanged inputs, empty destinations and absent owned residue.

The supported provider contract requires workers to keep writes in their owned
paths and work within descendant processes. Kernel closure does not cover
preexisting services or remote delegation, and structural admission is not a
sandbox. Inline/non-Linux execution retains its earlier boundary and cannot
publish this positive closure.

Local focused checks cover current record shapes, historical versus current
readiness, damaged or incomplete task trees, selected-scope receipt drift,
interruptible proof and descendant observation. At product
`79d45fb8a974d34572aca5da1ec22a4e4cdbac74`, the real-Snakemake cancellation →
read-only preview → successful resume journey passed in 238.76 seconds in
[CI job 104486782385](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/job/104486782385).
It preserves prior EMRYS records, logs, selected inputs and verified outputs
while creating a new Attempt; Snakemake's own incomplete-job metadata may change.

The managed golden job passed all 47 selected containment cases with zero skips,
including all ten abort-proof modes and four real samtools cases. Only the fully
closed abort mode earned positive closure; the nine refused modes retained null
closure. The real-tool cancellation cases retain the stopped-sort/empty-output
limits described above. This tested PR merge
`3aa865b1c42d710f40b2a698045db2eed9438bcf`, containing that product head and
base `13cd68750e4223431a594478804795905bfe9154`. The retained
[artifact 10410455801](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/artifacts/10410455801)
has SHA-256 `a8b0e166cd0d1b5f1a898cd8abb32eb91b2b418582ea2342ed7926ba1fd0f258`.

That initial complete suite failed four older fixture assumptions about Task
labels, retained origins and immutable resource policy. Their corrections keep
the refusal checks and construct valid predecessor/Run bindings; no recovery
predicate was relaxed. Final product head
`a947b8fca04eb052c3829e897f255b046b002087` passed all 14 standard jobs, with
four configured skips, in
[CI 35002451860](https://github.com/lab-cats/EMRYS/actions/runs/35002451860).
The strengthened public cancellation/resume journey passed in 282.22 seconds;
all 47 native cases passed without skips. Final
[artifact 10411245477](https://github.com/lab-cats/EMRYS/actions/runs/35002451860/artifacts/10411245477)
has SHA-256 `7f691245b22bf4b24cd479745b041adfdcc9d11b662f0455ff1ceebde6d16985`.
The later timeout-warning slice also passed the integrated standard CI recorded
above. Those results cover the earlier retry and warning behavior, not the
prepared-finalization extension. The historical interrupted Run remains
untouched and its cause unestablished.

**Approved prepared-finalization boundary:** The September 17 audit identified
the missing reconciliation path. `emrys resume RUN` now owns the selected
extension: complete the exact prepared `attempt-receipt.v3` bytes, written only
after terminal observation and the lifecycle's evidence decision, before ordinary
resume admission. The [lifecycle contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
owns preparation, exact-byte/evidence/ownership revalidation and publication.
The transition stages same-inode lock and receipt aliases before retiring their
source names; a copied file or released-only shape cannot authorize recovery.
There is no receipt reconstruction or scheduler/log/PID-derived authority.
Prepared failed/interrupted outcomes may continue only after existing admission;
prepared blocked/succeeded outcomes create no new scientific Attempt. Legacy
missing-prepared states, lost workers and unclosed Tasks stay blocked; E09 is
neither adopted nor repaired.

CV-10 is **Verification pending** for exact hosted CI of this extension,
including interrupted publication, refusal and public preview/confirmation
behavior, and for institutional cancellation acceptance. No new local, hosted
or institutional results are claimed here.

**Owner-accepted ownership limit (2026-09-22):** The cross-preview candidate
binds exact bytes and device/inode identity. If the original file is removed
and the filesystem reuses its inode number for an equal-byte replacement,
those observations alone cannot prove ownership continuity. The
path-replacement regression tests a distinct-inode atomic replacement, not
this recycled-inode case. The owner accepts that residual limitation for a
trusted, operator-controlled workspace while retaining the exact-byte,
device and inode checks. This does not claim protection against adversarial
same-UID replacement, and passing CI would not prove such protection.
The enduring [recovery contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
and [operator guidance](../operations/TROUBLESHOOTING.md#run-and-reporting-state)
retain this accepted boundary independently of campaign retirement.

### CV-11 Resource profile compatibility

**Finding:** The selected smaller-memory node could not satisfy the retained
STAR-index allowance; idle CPUs did not imply available exclusive placement or
sufficient RAM (E02, E10). **Acceptance:** Explain incompatibility as early as
available facts permit, separating physical/observed capacity, scheduler
reservation, configured stage allowances, and measured demand. Preserve unknown
capacity instead of trusting the site's placeholder memory value. Cover missing
memory metadata, explicit-memory rejection, exclusive/shared placement, and
stage/workflow limits. Shared execution must make its memory-policy implications
clear. Changing a plan creates a new Run; no automatic budget reduction or
unmeasured throughput promise. Reuse resource admission rather than adding a
second scheduler authority.
**Owners/dependencies:** Existing `SCHED-01` covers explicit undersized-memory
preflight; this card owns the broader heterogeneous-capacity and UX acceptance.
Coordinate execution profiles/capacity, CV-07/09/22, and optimization discussion 3.

**Implemented declaration-fit slice:** The existing computational-resource
owner now checks only known relationships before allocation and supplies the
same predicates to actual capacity resolution. Impossible thread/concurrency
and known memory totals fail early; symbolic memory remains retained, and
explicit correcting overrides apply first. This adds no capacity query,
reservation assumption, automatic reduction, or new policy owner. Placement-only
resume still selects its retained policy before any future reservation check.

**Verification:** Resource/profile tests pass locally (54 cases), including
early refusal, correcting overrides, symbolic retention, immutable predecessor
policy, and an allocation-dependent memory boundary. Broader contract tests
require installed Analysis entry-point metadata unavailable locally. The
reservation-fit slice below supplies explicit comparison; institutional
heterogeneous-node acceptance remains pending.

**Implemented reservation-fit slice:** The final effective execution profile
checks CPU and explicit memory requests before submission, Doctor repair
planning, and profile creation. It reuses the shared resource predicates with
reservation-specific diagnostics and replaces Control's duplicate CPU rule.
Placement-only resume applies retained policy first using the existing reads;
no inherited-policy loader API or fabricated capacity is introduced. Symbols
are preserved, memory omission stays unknown, and actual allocation admission
still controls execution. The final pure resource/profile suite passes 64
tests. Public no-submit/no-write, Doctor, authoring and resume cases passed the
integrated standard CI recorded above. CV-11 is **Verification pending** for
institutional heterogeneous-node acceptance.

### CV-12 Unexplained initial runtime qualification failure

`CV-DOCS-01` in the [main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up)
owns reconciliation of the older acceptance wording below with the current
**Discard** disposition. Recording that wording defect does not reopen causal
reconstruction or establish an explanation for E01.

**Finding:** The first repaired runtime failed qualification after successful
package installation; the failing individual check is still unknown (E01).
**Acceptance:** Recover sufficient retained diagnostics or reproduce the
failure at the identified revision/environment, establish its cause, and link
the correction and a discriminating regression. If evidence cannot establish
a cause, keep the limitation explicit for a separate disposition; do not close
it by attributing it to later memory-policy or username defects.
**Owners/dependencies:** Doctor/runtime owner; CV-02 and CV-01. No new repair
or root-cause claim is authorized by this record.

## P1 outcomes

### CV-13 Expected setup versus blockers

**Finding:** Initial expected Runtime/Storage setup needs were labelled as
blockers during the repair journey (E01, E08). **Acceptance:** Distinguish
not-yet-prepared state, repairable failed checks, and conditions preventing the
requested operation. Keep real execution refusal and check detail intact;
plain output must remain understandable without relying on color alone.
**Owners/dependencies:** Doctor presentation and quickstart; CV-05/19.

**Selected implementation:** Doctor derives domain labels from existing admitted
observations: absent default runtime inventory is `NOT PREPARED`, inspected
runtime failures are `CHECKS FAILED`, storage is `NOT QUALIFIED`, and unusable
execution profiles are `NOT ADMITTED`. Exact failure details remain execution
requirements, and actual operation refusal still reports `DOCTOR BLOCKED`.
Invalid storage evidence is not assumed to be an initial setup condition.
Four net product lines implement the change, with no new read, state, or schema.

**Verification:** Diagnosis-backed tests cover absent versus malformed/explicitly
missing inventories, failed checks, invalid retained storage evidence, plain
output, preserved no-write behavior, and unchanged refusals/exits. Static checks
and current integrated application execution pass. Operator acceptance is
pending.

### CV-14 Project directory layout

**Finding:** The walkthrough placed a Project at the source checkout root and
later needed a separate Projects directory (E04, E07). The later CV-U07 operator
decision places that home at tracked `Projects/` inside the checkout.
**Acceptance:** Give the novice that ready-to-use Projects home and a supported
destination selection. Respect existing directories and symlink/path rules;
do not automatically move old Projects or break runtime/input references.
Cover invocation from the checkout and from the Projects parent.
**Owners/dependencies:** Onboarding, quickstart; CV-06/08.

**Selected implementation:** The repository tracks `Projects/README.md` and a
`.gitkeep`, while ignore rules exclude Project children. Quickstart and Runbook
enter that parent for synthetic and own-data setup and reconnection; no manual
directory creation is required. Existing `init NAME` still selects its parent
through the current directory, and synthetic initialization retains absolute
`--output-dir` selection. Both reuse canonical-parent/absent-child admission.
Existing Projects remain at their original paths; no Project registry or move
operation is added.

**Verification:** Public onboarding tests exercise synthetic and own-data
creation beneath the tracked Projects parent. They preserve no-write preview,
external input references and bytes, ignored Project children, and
existing-destination refusal. Focused execution and documentation checks passed
in the locked integrated CI environment; operator walkthrough remains pending.

### CV-15 Cross-node active Run status

**Finding:** Head-node inspection presented unproved remote lock ownership and
unfinished task records as blocked Run/Results during active work (E05).
**Acceptance:** Distinguish remotely active or unverified ownership, work in
progress, and demonstrated invalid state. Report the limits of available proof
without authorizing unsafe resume. Cover active, completed, unreachable-host,
stale/ambiguous ownership, and terminal-without-finalization cases. Scheduler
evidence may inform display but cannot replace transaction integrity checks.
**Owners/dependencies:** Inspection/lifecycle and presentation; CV-10/16/20.

**Implemented observation slice:** Normal inspection now reports Run admission
separately from the derived lock observation and shows the recorded host/job
only for a structurally admitted owner. An exact remote lock is labeled
`remote ownership unverified`; it remains blocked and non-resumable. Invalid
namespace/binding, dead local owner, live local owner, and no lock remain
distinct. This uses the existing lock read and does not query remote hosts or
infer scheduler liveness. Unfinished task evidence retains its strict blockers.

**Implemented task-observation slice:** All inspection detail levels now count
`Verified complete`, `Verification not admitted`, `Started; completion
unverified`, and `No admitted start` from the existing typed task snapshot.
Debug rows share those labels and show admitted start paths. A start does not
prove current worker activity; missing/invalid start evidence does not prove
that work never ran. No new read, stored state or recovery permission is added.

**Verification:** Lifecycle fixtures inspect during actual admitted Attempt
execution, including remote/dead/invalid locks and terminal retained locks;
public output retains uncertainty and blockers without mutating evidence or
probing an unbound PID. Task fixtures follow the same admitted start through
local-live, remote-unverified and terminal-incomplete observations; all display
levels acquire one snapshot per render and preserve files and recovery refusal.
Existing complete, changed-verified and missing/malformed-start cases cover the
other labels. The task cases and current integrated standard CI passed. CV-15 is
**Verification pending** for institutional cross-node observations and any
remaining state distinctions established by those observations.

### CV-16 Monitoring dashboard

**Finding:** The operator needed separate scheduler panes, manual tails, and
misleading interim inspection output to monitor work (E05, E06, E12).
**Acceptance:** Provide one view of scheduler state, stage/task progress,
elapsed time, relevant logs, and next supported actions. Use current Run and
submission authorities with explicit uncertainty. Preserve the existing
diagnostic discovery/accounting behavior and sanitized stream handling; cover
missing/rotated/truncated logs and reconnecting.
**Owners/dependencies:** Run coordinator inspection/presentation and watch;
CV-15/20/21/25. The selected CLI handoffs are completed under CV-24.

**Implemented evidence projection:** CV-15 supplies Task evidence counts;
CV-25 adds admitted terminal outcomes and exact retained logs to the same
inspection snapshot. CV-20 supplies exact selected-request scheduler state.
These are shared CLI observations for the integrated watch view. The institutional
owner accepted that replacement on 2026-09-17, after which the standalone
dashboard wrapper and duplicate mechanics were retired.

**Dashboard parity implementation:** Installed `inspect --watch` now shares the
diagnostic discovery, selection, parser and overview/detail renderer.
It provides explicit/recent/historical job selection,
offline owned streams, configurable refresh and snapshots, pipeline history,
sample lanes and peer timings, stage explanations/resources, current frontier,
activity/errors, scheduler placement/usage and keyboard navigation. Exact-request
resources preserve stronger name/UID/cluster/path identity; optional batch usage
has independent dates and before/after local identity checks.

The new evidence/log view preserves Run/Attempt/Task/reporting admissions and
application-log discovery. Full retained diagnostic history reconstructs progress
on reconnect, while no-follow generation checks prevent rotation/truncation from
mixing bytes. One bounded daemon per stream and closed/start synchronization
preserve responsive exit. `o` remains overview; report preview moves to `b`.
Queued input is discarded before CLI handoff. Unknown invocation totals are
shown as unknown, replacing the legacy six-sample/25-partition assumptions.

**Consolidation and validation:** Reuse existing selection, scheduler, parser,
line projections and CLI handlers; no new product file, dependency, command,
persistent schema or recovery authority. The installed Rich view adapts the
shared layout instead of implementing another pipeline/sample presenter.
Legacy and installed public fixtures cover discovery/accounting/ownership,
full-trace reconnect, changed streams, resource identity/usage, layouts,
plain/color output, navigation and fresh action handoff. These software checks
passed the final combined standard CI above. CV-16 is Verification pending for
institutional terminal/NFS and operator walkthrough evidence. The original entry
point and generated legacy names remain under `DASHBOARD-RETIRE-01`.

**Legacy offline correction:** The existing `--offline` selector already avoided
scheduler discovery, but snapshot and interactive refresh still queried Slurm.
Both now share one selected-state owner: offline stays `UNKNOWN` and makes no
scheduler query; online observation keeps its exact prior arguments. Existing
regular-file/ownership admission and sanitized stream display remain in use.
The full standalone suite passes 182 local tests, including both public offline
modes and unchanged online refresh queries. This preserves the supported legacy
surface without establishing institutional acceptance or retiring the standalone
entry point.

**September 16 Viking acceptance failures:** Plain `emrys watch` failed to
select the intended current target or offer a selector, forcing manual numeric
job-ID entry. A supplied dashboard simultaneously showed `36/36` jobs and zero
remaining plus FINAL `1/1 DONE`, yet reported overall `UNKNOWN`, Steps 09/10 as
`1/? WAITING`, REPORT as `0/? PENDING`, and no admitted Run/control identity.
The screenshot establishes a contradictory diagnostic display, not scientific
completion. Watch must prefer admitted Run evidence and otherwise label a
finished workflow log as unverified rather than active waiting.

The log view was still reported as monocolored. It should open at the most
recent admitted line and follow new text automatically; upward navigation must
pause following visibly and returning to the bottom must resume it. Retain a
bounded reader while adding clear absolute or tail-relative line numbering,
counted `j`/`k` motion such as `99j`/`99k`, `/pattern` search with highlighting,
and `n`/`p` next/previous matches. Missing/rotated/truncated-log and reconnect
protections remain required. These operator observations return CV-16 to
**Open** despite prior hosted parity checks.

**September 18 integrated-watch correction:** The accepted color, log
navigation and evidence renderer remains intact while one watch-target model now
serves Project-local and Projects-home selection. Exact request identity survives
Run association, ordinary watch no longer enumerates unrelated scheduler jobs,
and active/final batch usage shares one validated data path. The overview and
detail panes also share one scheduler-state row renderer. No product file,
schema, dependency, persistent selection state or recovery authority was added;
the tranche is net-negative in maintained product Python. Focused local watch,
selection, scheduler-fault and renderer suites pass. Standard CI,
Viking terminal/NFS behavior and operator visual acceptance remain pending, so
CV-16 is **Verification pending**.

### CV-17 Project creation progress

**Finding:** Actual-data initialization silently read large inputs for minutes
(E07). **Acceptance:** Show the current validation phase, elapsed time, and
useful file/byte progress when measurable. Explain large-input work before it
starts; label estimates and avoid invented completion percentages. Preserve
no-write preview, interruption behavior, and content/compatibility checks.
**Owners/dependencies:** Onboarding and existing progress presentation; CV-06.

**Selected implementation:** Named initialization reuses the existing phase and
elapsed-time presenter for full input hashing, reference/partition compatibility,
and post-publication verification. An upfront explanation identifies complete
input reads. Existing admissions, hashes, publication, and interruption behavior
are preserved; no shared validation path is changed. File/byte completion is
not currently measured, so no percentage or speedup is claimed. Product growth
is nine net lines within the approved ten-line cap, with no new product file.

**Verification:** Existing public initialization tests check phase ordering and
no-write preview, then all creation phases. Failure and interruption cases
cover each validation boundary, preserving inputs and any published state.
Ruff, formatting, AST, and whitespace checks pass locally; application tests
passed the current integrated standard CI. The institutional large-input
walkthrough remains pending.

### CV-18 Safe EMRYS stop

**Finding:** There was no clear supported stop action that preserved a route
to resume (E09). `emrys stop JOB_ID` is the operator's proposed spelling.
**Acceptance:** Settle target selection for queued submissions and active Runs,
confirm exact ownership/intent, and route cancellation through the shared
lifecycle. Report progress and the actual terminal/recovery state. A successful
stop must not promise resume when task evidence is ambiguous. Cover stopping
before Run creation and during a native task. Reuse CV-10 recovery mechanics.
**Owners/dependencies:** CLI/control, Slurm transport, lifecycle; CV-10/20.

**Selected identity prerequisite:** Ordinary requests retain a token-specific
scheduler job name in closed v3 context. Planning, validation and selected
observation bind the same name alongside numeric owner, root job ID, cluster
and exact stream paths. Older v1/v2 records keep read-only inspection and gain
no cancellation authority. Shared watch discovery remains compatible.
This prepares safe target selection; it does not execute cancellation.

**Stop design boundary:** Select an exact retained request with Project context,
rather than a bare reusable job ID. Cancellation must apply owner/name/ID
filters together at the controller; observing stream paths before ID-only
cancellation leaves a reuse race. Slurm added that `scancel --ctld` behavior in
[23.11.6](https://raw.githubusercontent.com/SchedMD/slurm/slurm-23-11-10-1/NEWS).
Older or unconfirmed clients must refuse before any mutating command. Even a
successful command means only that the request was processed; independently
admitted Run receipts/locks still decide completion and recovery. Actual cluster
cancellation retains its own authority.

**Selected stop slice:** `emrys stop --submission REQUEST` with Project context
previews one exact owned v3 request. Explicit `--execute` requires fresh target
identity and an unchanged admitted client before one controller-filtered
whole-job cancellation. The existing logger synchronizes exact intent; the
shared submission transport retains raw output through pinned directory/file
identities. Errors, timeout and interruption preserve records without retry.
An already terminal target causes no cancellation; a processed request and
terminal scheduler observation remain distinct from native process absence or
Run recovery eligibility. No lock, receipt, Task output or retained evidence is
removed or repaired. Local fixtures and the integrated hosted standard CI pass
these software boundaries. CV-18 is **Verification pending** for actual
queued/native-task cancellation and institutional recovery evidence.

**September 17 adversarial audit:** `emrys stop` safely binds and submits one
controller-filtered cancellation request, then reports scheduler observations.
It does not establish native-process quiescence or integrate Run/Task evidence
to report the actual terminal and recovery state. Its principal public stop
fixture intentionally creates no Run, so stopping during an active native task—
the card's required case—is not implemented end to end. CV-18 returns to
**Open**.

**Selected outcome slice (exact CI pending):** After the single cancellation
request, re-read the same exact retained submission request, its application
association and independently admitted Run evidence. Association is diagnostic:
only an association to the Run's current Attempt can support a Run/Task outcome;
it cannot authorize cancellation or recovery. If the scheduler is terminal but
the matching Attempt has no terminal receipt yet, allow at most ten seconds of
read-only settlement checks for publication. Do not resend cancellation. Report
an admitted terminal state and recovery eligibility only from Run evidence;
otherwise report recovery unconfirmed and direct the operator to inspect/watch
the exact request or Run. A prepared finalization is a distinct `resume` next
action, not already-available recovery. Preserve transport exit-code meaning
and all uncertain records. The public active-native-Task fixture must exercise
real Snakemake, Task and native child cancellation through this path. Hosted
software checks cannot prove the Viking controller or institutional native-task
outcome. CV-18 is **Verification pending** for exact hosted CI of this outcome
and institutional queued and active-native-task cancellation; neither check
is claimed to have passed here.

### CV-19 Verification and repair vocabulary

**Finding:** Doctor printed READY, then asked to apply a repair consisting only
of verification and finalization (E08, E11). **Acceptance:** Name the plan,
confirmation, progress, and completion according to its actual actions.
Verification-only work explains what is rechecked and why; installation or
correction remains identifiable as repair. Cover already-ready, unprepared,
failed-check, and mixed-action plans without changing their authority.
**Owners/dependencies:** Doctor and shared presentation; CV-05/13.

**Selected implementation:** Doctor derives verification versus repair and
verification from the planned package-manager actions, and carries each manager
action's display label alongside its exact command/environment. Preview and
execution share those labels; duplicate plan construction is consolidated.
The quickstart explains repeated checks and retained package-manager reuse
evidence. No public command, check ID, log mode/event ID, receipt, dependency,
or recovery rule changes. CV-13 supplies setup-state classification; its operator
acceptance remains pending. CV-05 supplies tested accounting timing and
setup/retry guidance. Missing storage evidence is not assumed harmless.

**Verification:** Focused regressions cover verification-only and package-action
plans, confirmation/refusal, progress, failures, and preserved no-write preview.
Doctor regressions passed the combined standard CI above. Institutional operator
acceptance remains pending.

### CV-20 Submission state before Run creation

**Finding:** `inspect` reported no Runs while a submitted job was preparing
inputs or queued (E05). **Acceptance:** Discover and show the exact submission,
queue reason, and preparation state before a Run exists; connect it to the Run
when created. Support multiple submissions and reconnecting without assuming
the latest directory is authoritative. Distinguish startup failure and absence
of any submission. Preserve the rule against duplicate submission on uncertainty.
**Owners/dependencies:** Submission/control, inspection/presentation/logging;
CV-03/15/16/18/25.

**Implemented scheduler-observer prerequisite:** Watch uses strict
root-job/numeric-UID admission across discovery, accounting, and
state observation. It requests accounting duplicates rather than silently
choosing the latest reused ID, rejects ambiguous/missing/mismatched identity,
checks selected stream paths on refresh, and reports unavailable proof as
`UNKNOWN`. Exact batch-step identity controls usage display. This retires
username-environment matching and duplicate first-row accounting parsing while
preserving bounded discovery/stream handling.
Job-ID/UID/path agreement is not request/cluster identity or recovery proof;
the current inspection path below integrates retained requests. The institutional
owner accepted installed watch on 2026-09-17; its shared observer then replaced
the looser standalone scheduler query. Actual scheduler/site verification
remains pending.

**Selected first slice:** Ordinary Run/resume/report now retain a private,
create-absent request context and raw scheduler responses after approval,
including failures and interruption before Run creation. The context includes
exact Project/command/profile and custom application-log location for later
reconnection. Directory synchronization precedes launch; early stdin closure
retains scheduler rejection details. The existing recorded transport serves
both ordinary and waited Doctor submissions without duplicate job-ID state,
automatic retry, or a premature application Attempt. Product growth is 73 net
lines under the user's minimum necessary expansion approval; no product file
is added.

**Implemented discovery slice:** `emrys inspect` without a Run selector lists
every retained request before existing Run selection, including when no Run
exists. It shows recorded context and response job/cluster, bounded escaped
stderr, and partial/malformed/unconfirmed observations without scheduler calls
or writes. Unavailable directories are errors rather than empty rosters. The
writer and bounded reader share closed-context admission and a 64 KiB limit;
directory/file ownership, canonical paths, stable reads, strict response
parsing and immutable returned context prevent guessing from arbitrary files.
No newest-request selection, acceptance inference or Run association is added.

**Implemented stream-identity prerequisite:** Each ordinary submission freezes
one request UUID before preview/confirmation and uses it in both scheduler
stream destinations. The v2 context binds those paths to the request directory;
v1 remains readable as historical diagnostics. Watch discovery accepts exact
matching token-based stream pairs and preserves historical support. Doctor's
qualification paths are unchanged; isolated standalone loading was retired later.
The token alone does not establish a job's current state or cluster identity.
Transport/dashboard/shared-input tests pass 191 cases, with 17 affected cases
rechecked after the final naming changes. Public confirmation/decline and
repeated run/resume/report fixtures passed standard CI at PR #201.

**Implemented selected-request scheduler view:** `inspect --submission REQUEST`
selects one exact retained directory name or absolute path instead of a Run.
It checks ID, numeric UID, cluster and both frozen paths in one complete queue
record; only a successful empty queue reply permits duplicate-aware terminal
accounting. State, queue reason and exit status are escaped observations.
Legacy/incomplete requests make no queries; unsupported, malformed, mismatched,
duplicate or unavailable metadata remains `UNKNOWN`. The ordinary roster makes
no scheduler calls, keeping query cost independent of retained history. The
watch and the request adapter share extracted stdlib identity and accounting
mechanics.

**Verification and remaining scope:** Tiny real subprocess tests cover accepted,
rejected, malformed, invalid-byte, interrupted, and early-stdin-close responses;
directory/file failures prevent launch and Doctor callback ordering is retained.
The transport/shared-input suites pass 107 local tests, including exact size
boundaries, empty Analysis preservation, malformed/partial records, symlinks,
owner mismatches and changed directories. Public fixtures cover zero/multiple
requests before any Run, an existing Run, escaped output, unavailable logs,
writer-reader roundtrips, and oversized context preventing submission; these
application fixtures passed standard CI at PR #199. Strict scheduler fixtures
cover exact identity, wrong/reused IDs, clusters, streams, duplicate accounting,
failed versus empty queries and invalid metadata. The focused suites passed
266 cases before final identity/whitespace additions; all 90 affected cases
passed afterward, including array/heterogeneous IDs and exact untrimmed paths.
Public selected-request cases
cover one-request query cost, default no-query behavior, unavailable/legacy
observations, exact selection, escaped reason text and no writes; these new
application cases passed standard CI after the fixture correction. CV-20 is
Verification pending for institutional scheduler, reconnect and preparation
observations.
Neither retained context nor a terminal
scheduler record grants scientific completion, cancellation or recovery authority.

**Implemented application-log producer prerequisite:** Ordinary Run/resume/report
delegates carry the frozen request token in their existing private context and
record it with exact profile/Project binding immediately after opening their
one application log. Batch admission checks the token before modules/scratch
and preserves it through module initialization. Random application-attempt
identity, custom roots and direct/legacy/Doctor behavior remain intact. The
event is diagnostic; a later reader must still reject ambiguous or incomplete
logs and independently admit candidate Runs/Attempts before association.
Transport fixtures exercise actual safe Bash propagation, invalid/orphan
context and module mutation; public early-log fixtures passed the final
startup-outcome CI below.

**Selected application/Run association slice:** Exact-request inspection scans
only the retained command-specific application scope, with bounded directory,
log and authority reads. Stable, canonical, current-UID-owned evidence must
bind the request token, Project/profile, scheduler ID and one complete log.
Multiple matches, malformed records, drift or exhausted limits remain unknown;
the default roster scans no application logs. Public output keeps the bound log
and recorded preparation separate from admitted Run/Attempt identity and offers
the exact Run-inspection command.

Existing Run/profile/Attempt admission checks the named candidate without
walking unrelated Attempts or scientific outputs. A historical Attempt record
is association evidence only: no chain, lock, receipt, Task or Results admission
is implied. Shared directory enumeration gains an optional bound and profile
binding retains one formatter for equivalent digest inputs. Focused fixtures
cover actual log-writer compatibility, identities, limits, malformed/ambiguous
records and snapshot changes; full candidate and public fixtures passed the final
startup-outcome CI below.
Institutional reconnect/queued/preparation observations remain pending.

**Recorded startup outcomes:** Selected-request inspection and watch now preserve
the final admitted application failure or interruption and its recorded phase,
including a preflight failure before a Run exists. Run-log rows use the same
pure formatter. Open logs retain no recorded outcome; missing, ambiguous,
malformed or changing evidence remains unknown. A recorded interruption keeps
its `interrupt` phase instead of guessing that it occurred during preflight.
Preparation candidates and independently admitted Run/Attempt identities remain
separate from the application outcome, with no new reads, records or recovery
authority. Real-writer and public-handler regressions cover failure before and
after preparation, interruption, unchanged admission and escaped presentation.
The complete standard suite passed for product
`7b8db426020dd3b501ac3fdbe68aa315e68f4c69`
([CI 34977917662](https://github.com/lab-cats/EMRYS/actions/runs/34977917662)):
all 14 standard jobs succeeded, including installed-provider Run association,
all Python shards, coverage and the managed golden path; four configured lanes
were skipped. Institutional reconnect/queued/preparation evidence remains
required. Recorded application failure does not establish a scientific outcome.

### CV-21 Reporting in progress and visibility

**Finding:** Missing reporting receipts briefly appeared as failures and later
passed without intervention (E06). The event remains an unexplained historical
observation. **Acceptance:** Represent `No admitted start`, `Started; completion
unverified`, and `Verified complete` truthfully; expose report locations only
after exact verified completion; and reject truly missing or invalid committed
outputs. Exercise inspection at each report transaction boundary and controlled
finalization faults; do not add blind sleeps or turn missing evidence into
success. Reproducing E06, attributing its cause or reconstructing its historical
filesystem state is not required.
**Owners/dependencies:** Reporting publication/boundary and inspection;
CV-01/15/16. Visual report review remains separate.

**Implemented observation slice:** Normal inspection now shows the existing
reporting transaction table, with `No admitted start`, `Started; completion
unverified`, and `Verified complete`, separately from Reporting admission.
The admitted start survives the missing-completion blocker, and a start does
not prove a live reporter. The table appears once at each detail level; no new
state, reads, sleeps, completion inference, or weakened blocker is introduced.
Public and hosted output consumers use the new admission label.

**Verification:** Existing reporting-boundary coverage now inspects before
start, after start, after producer output, and after verified publication;
exact retained references/blockers and no writes are checked. Public inspection
fixtures cover pending/started/complete rows at normal and verbose levels.
Static checks and the integrated hosted standard CI pass. These cases establish
the overlap mechanism, not the historical cause of E06. Current institutional
reporting/inspection execution remains pending; causal reconstruction is no
longer required.

**Integrated public reporting slice:** The existing failed-Run/resume fixture
pauses immediately before and after each real summary/HTML producer, while its
reporting start is admitted and verified completion is still absent. Four
separate public CLI readers must preserve complete scientific Results, show
the unverified transaction and blockers, and withhold public report locations.
The exact producer receipt is absent before production and present afterward;
neither presence nor a start grants verified reporting admission. Whole-Project
namespace, file bytes and modification times remain unchanged by inspection.
The original final verified-report and byte-preserving resume assertions remain.
This reuses scientific owner doubles and real reporting owners without another
scientific journey. Full integration passed the combined standard CI after
the test reader adopted the controlled Python argv owner. It covers producer
publication boundaries, not arbitrary mid-write timing, institutional filesystem
visibility or the cause of E06. The later Run-log discovery association assertions
in this same journey also passed the final combined standard CI above.

**Controlled finalization-fault slice:** The reporting boundary now has
deterministic coverage for completion publication failing before the verified
name is visible and failing after the exact complete marker becomes visible.
Inspection follows the admitted filesystem state: the first case remains
`Started; completion unverified`, even with a producer receipt present, while
the second re-admits the visible marker as verified. No sleep, retry, missing-as-
success rule or new reporting state was added. The historical E06 cause and
actual Viking storage-visibility behavior remain unknown. Ordinary institutional
execution of the current reporting path remains pending, so CV-21 is not
established as a site result.

**September 17 adversarial audit:** The added transaction-boundary and
deterministic finalization-fault fixtures preserve useful defenses, but they
demonstrate possible mechanisms rather than establish the cause of E06. This
card's acceptance then required first distinguishing publication overlap, storage
visibility or another cause, while its own evidence record continued to say that
the historical cause and Viking visibility behavior were unresolved. CV-21
therefore returned to **Open** at that checkpoint.

**September 21 owner disposition:** Causal reconstruction is explicitly
discarded as an acceptance requirement. The truthful transaction states,
verified-location gate, fail-closed committed-output admission, real public
producer-boundary coverage and controlled finalization-fault protections are
accepted as the current implementation outcome. E06 remains unexplained
historical provenance and does not block closure. Ordinary institutional
execution of current inspection/reporting behavior on an exact revision remains
pending; no induced fault, E06 reproduction, visual review or scientific claim
is required. CV-21 is **Verification pending**.

### CV-22 Complete submission preview

**Finding:** Confirmation omitted node selection/exclusivity and obscured the
distinction between allocated CPUs and workflow/stage limits (E10, E12).
**Acceptance:** Before approval show selected node/eligibility, exclusive/shared
placement, allocation CPUs/time, workflow CPU ceiling, and memory policy with
resolved values where known. Identify unknown capacity and important stage
caps; do not imply that a larger reservation guarantees utilization. The
display must describe the frozen plan actually submitted and be clear for
Doctor verification as well as Run/report submission.
**Owners/dependencies:** Shared submission planning/presentation and profiles;
CV-03/07/09/11. Preserve ordinary concise output.

**Selected implementation:** One pure formatter on the admitted execution
profile replaces the repeated placement summary and redundant workflow-core
plumbing. Doctor, Run/resume, and report submission display requested placement,
allocation resources, workflow limits, and stage caps from that same object.
Planned report preview also admits its selected profile; already-complete
reports keep their existing no-submission path. Unknown capacity, site policy,
and configured limits remain distinct. No allocation probe or new state is
introduced. The final 51 net product lines use the user's subsequent approval
for minimum necessary expansion; no new product file is added.

**Verification:** Existing profile, Control, and Doctor tests cover omitted and
explicit placement fields, exact submitted arguments, no-write previews,
profile refusal, resume policy, and report reuse. All 30 focused profile tests
pass locally; public Control and Doctor execution passed the integrated standard
CI. These provide software evidence; institutional preview acceptance remains
pending.

**Current policy disposition:** CV-22 is **Open**. Its conflict with the later
concise-output behavior is transferred to `SUBMISSION-PREVIEW-01` in the
[main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up), which
owns reconciliation with CV-U02/U04. That source/policy follow-up blocks
acceptance; the existing institutional preview requirement remains here.

## P2 outcomes

### CV-23 Safe Project or artifact cleanup

**Finding/proposal:** Old Projects, abandoned attempts, and unused artifacts
accumulate, with no clear safe operator cleanup route.
**Acceptance:** Decide the supported scope and preview exact owned candidates,
references, and consequences before any deletion feature is approved. Protect
active/ambiguous Runs, shared inputs, reused runtimes, receipts, and recovery
evidence. Never infer deletability from age, job disappearance, or absence of
a success receipt. Any evidence deletion retains its separate explicit
authority. This is not a revival of retired storage-capacity/retention planning.
**Owners/dependencies:** Project/runtime/lifecycle owners; CV-08/10. Design
selection and product implementation remain separate from this recorded idea.

**Selected design disposition:** Defer a general cleanup preview or deletion
command. Source review identified no retained candidate class for which current
owners can establish both exclusive ownership and absence of references. Keep
the existing cleanup of temporary state owned by the executing transaction;
this decision identifies no actual storage candidate and claims no space saving.

| Candidate class | Existing authority and unresolved consequence |
| --- | --- |
| Runs, older Attempts and scientific artifacts | Run inspection admits processing reuse through an exact Run, Attempt and receipt. Removing older evidence can invalidate a later Run. |
| Native outputs, staging, locks and reporting partials | Task and reporting owners clean their own transaction state using captured ownership. Retained leftovers do not establish that ownership, native quiescence or safe rollback. |
| Managed runtimes and caches | Runtime reuse permits borrower Projects outside the donor. Permanent seals have no reverse borrower catalog or unseal operation; R package links also prevent treating caches as disposable. |
| Qualification probes and receipts | Qualification owns its immediate cleanup and explicitly retains evidence after cleanup failure. Leftover probes are not automatically abandoned. |
| Inputs, references and sidecars | Project normalization admits declared paths without establishing exclusive ownership or enumerating external consumers. |
| Submission and application records | Request and association inspection consume these records. Age, scheduler disappearance and missing success receipts do not establish disposability. |

Reopen implementation for a specific owner-backed candidate class with complete
reference and consequence rules. An incomplete search must report unknown,
never unused. Reuse existing inspection and ownership primitives instead of a
second status cache, retention registry or generic cleanup engine. Native and
reporting cleanup remain separate where their process-lifetime and publication
guarantees differ. Any later evidence deletion keeps its separate explicit
authority. No product change or deletion is part of this design disposition.

### CV-24 Run center actions

**Finding/proposal:** Monitoring could become a Run center for readiness,
launching analyses, inspection, logs, and supported resume.
**Acceptance:** Evaluate staged addition of actions to the validated monitoring
view. Every action invokes the same CLI-owned operation, frozen plan preview,
confirmation, and recovery checks. Resolve Project/Run selection and concurrent
actions without a second scheduler, shell executor, state authority, or recovery
implementation. Record the selected interface and coverage before retirement
under `DASHBOARD-RETIRE-01`.
**Owners/dependencies:** Existing CLI/control and dashboard; CV-16 first.

**Selected actions:** Interactive `--watch --actions` offers `p` for a Run's
ordinary resume plan and confirmation, `b` for its report preview, or `s` for
an exact request's stop preview. One immutable action list replaces the
resume-only callback. Each handoff captures only the exact Project/selection,
closes the view and restores the terminal, then constructs the ordinary parser
and calls its existing handler once. An already active read may finish but
cannot supply action authority or trigger another refresh. There is no shell
executor, action worker, stored plan or automatic return to monitoring.

Run handoffs use the default profile. Report and stop remain strict previews;
resume retains its explicit confirmation. No inspected `execute` value or
associated historical Run becomes a command argument. Noninteractive action
mode is refused. Fresh Control
and lifecycle checks retain selection, predecessor and recovery authority.
For Slurm, the existing preview freezes the submission/profile request and
scientific admission runs on compute; a concurrent resume can still consume an
unnecessary allocation. Public owner fixtures cover exact selections, fresh
profile/request refusal, declined direct/Slurm resume, and report/stop no-write
previews. Terminal cases preserve teardown before one callback under stalled
reads and restoration failure. Presentation, application and PTY cases passed
the final combined standard CI above. CV-24 is Completed for the selected hosted
software interface. Institutional monitoring/action use remains under CV-16;
standalone retirement remains under `DASHBOARD-RETIRE-01`.

**New-analysis interface disposition:** Keep launch in
`emrys run --project PROJECT --analysis NAME`. Project admission selects an
existing declared Analysis and requires its name when several are defined.
Control owns full/processing
scope, source-Run reuse, profile selection, plan review and confirmation.
A shortcut using the monitored historical Run or Project defaults would not
represent a new Analysis choice. The selected watch interface is therefore
the three scoped handoffs above. A future chooser remains with the same Control
owner and must specify all selections before implementation; it is not required
to replace supported explicit CLI selection or to operate the current watch.

### CV-25 Log discovery and readable output

**Finding:** Locating the relevant logs required remembering job IDs or using
an unsafe assumption about the most recently modified filename (E01–E06).
Earlier operator notes also requested color and less verbose normal output.
**Acceptance:** Expose submission, startup, workflow, and reporting streams by
explicit Project/Run/Attempt identity, including before a Run exists. Preserve
multiple-attempt history, ownership, terminal sanitization, and full durable
diagnostics. Normal output is concise; optional detail and color aid navigation
while redirected/plain output stays usable. No reliance on shell clipboard
functions or a guessed latest log. Coordinate the old Slurm-name retirement
through `DASHBOARD-RETIRE-01` instead of independently renaming streams.
**Owners/dependencies:** Application logging, submission, inspection/dashboard;
CV-02/03/16/20.

**Implemented Task-log slice:** Static inspection admits terminal Task attempts;
`--verbose` shows their count, recorded outcome, original
Attempt, and content-bound record/stdout/stderr paths. Existing Task-tree
admission supplies records without another log scan. Postentry observations
must match an already admitted start reference and originating Attempt;
preentry failures preserve the existing ordering rule across later starts.
All output uses the existing terminal escaping. Recorded success cannot replace
verified Task evidence, complete Results or authorize recovery. Earlier failed
attempts remain visible alongside later success, without a guessed latest log.
The 63 net product lines reuse the existing admission and escaping owners;
there are no new product files, schemas, commands or dependencies.

**Verification:** Fixtures cover failed preentry/postentry records, recorded
success without scientific verification, retry history, absent terminal records,
malformed scope/start references, wrong-Attempt starts, and changed/truncated
logs. Public normal and `--verbose` rendering uses one snapshot, escapes diagnostic
text, preserves evidence and retains Results/recovery refusal. Static checks
pass; application fixtures passed the combined standard CI. CV-20 supplies
request-bound startup/application/reporting association; the Run-selected slice
below adds historical discovery to static inspection and watch.

**Started-Task stream slice:** The admitted start already binds the exact frozen
Task dispatch. One pure Task-owned root builder replaces repeated construction
in dispatch, directory materialization, terminal admission and debug output.
One stream projection serves watch and `--verbose` inspection without new
reads, schemas or admission rules. It preserves terminal references, including
preentry failure history, and derives expected paths only when both admitted
start fields are present. Exact historical Attempt filtering and path
deduplication keep the selected request's streams distinct.

Start publication precedes stream opening; derived paths establish neither
existence nor liveness. Current tail bytes remain unverified diagnostics under
the existing ownership/stability checks. Missing or damaged starts supply no
derived path. Presentation, lifecycle and public fixtures passed the final
combined standard CI above. Institutional discovery and interpretation of native
liveness remain under CV-16/15; coordinated standalone retirement remains under
`DASHBOARD-RETIRE-01`.

**Run-selected application discovery:** Explicit Run inspection and watch now
share a bounded search of one default, environment-selected or explicit
`--log-root` root. The request reader's canonical enumeration, preparation
parsing and historical Run/Attempt admission serve both paths. Each scan admits
the selected Run once and each distinct Attempt once, preserving all matching
Run/resume/report logs. A standalone report is associated with the Run only.
Custom historical roots are not retained in Run contracts and must be selected;
the ordinary roster/implicit picker does not scan, and a selected request keeps
its frozen root. No writer, product file, persistent index or schema is added.

Stable global snapshots and shared aggregate limits bound both scopes. Partial
malformed evidence remains unknown; independently rechecked matches may survive,
but namespace drift clears them. Explicit watch refresh rebuilds sources and
removes revoked associations while retaining independent Task streams; timer
refresh never repeats discovery. Associations do not establish unique ownership,
native liveness, completion or recovery. Reader, presentation, real writer/public
handler and historical resume/report cases passed the final combined standard CI
above. CV-25 is Completed for hosted software log discovery and presentation.
Institutional monitoring remains under CV-16; legacy entry-point/name retirement
remains under `DASHBOARD-RETIRE-01`.

### CV-26 Repeated Doctor input reads

**Finding:** A verification-only Doctor operation repeated Project/runtime
observations and exceeded ten minutes (E11). **Original acceptance:** Measure a
complete Doctor operation and attribute phases, hashes/bytes, probes, and queue time.
Audit duplicate mechanics across callers; consolidate only observations proven
equivalent at the same trust/mutation boundary. Preserve detection of input,
package, runtime, and storage changes during repair and qualification. Report
before/after measurements and residual costs; metadata or cached hashes alone
do not justify weaker checks. Do not invent an unmeasured time target.
**Owners/dependencies:** Doctor, normalization/runtime inspection, existing
validation helpers; coordinate optimization discussions 11–13 and CV-05/17.

**Selected phase-measurement slice:** Doctor keeps an invocation-local timing
collector and uses an optional observation callback on the existing progress
owner. It reports complete invocation elapsed time, explicitly including
operator confirmation time, and the actual exit outcome. Verbose/debug output
adds precise phase seconds. Approved maintenance writes `doctor_phase_timing`
events to its existing log at the operation outcome, including initial inspection; read-only
diagnosis and delegated compute create no additional log. Head/local and
compute contexts remain distinct. Slurm waiting is labelled submission-to-return
wait, which includes launch/transport and compute work as well as queue time.

Every input read, content hash, probe and admission boundary remains in place.
Ordinary clock/callback/log observation failures cannot change the work or
replace its failure; process-control exceptions keep their cancellation meaning.
Timing writes occur after controlling work and the claim-release decision, so
a degraded diagnostic log cannot interrupt package-output handling.
Focused fixtures cover precise clocks, failed phases, observation failures,
no-write diagnosis, existing-log buffering and delegated context. Public fixture
execution passed the current integrated hosted CI. Read/hash bytes, probe
attribution, process memory, actual scheduler timing and comparable before/after
measurements were left open by this slice; they are independently selectable
future research, not the revised CV-26 acceptance gate. This slice establishes
timing observations, not a measured speedup.

**Retained hosted observation:** The managed golden path at
`2e03177747e67e8d970083e3994f3c8970d77caf`
([run 34935510824](https://github.com/lab-cats/EMRYS/actions/runs/34935510824),
artifact `emrys-managed-golden-1`, ID `10382984827`) retained one complete
direct Doctor repair invocation lasting **175.681 seconds**. Its application
log recorded these phase durations:

| Phase | Seconds |
| --- | ---: |
| Initial Project/runtime inspection | 1.727 |
| Approved-input revalidation | 0.100 |
| Single-host storage qualification | 0.068 |
| Native tools and R preparation | 43.478 |
| R package restore/check | 20.146 |
| Installed-runtime discovery and verification | 55.091 |
| Final Project readiness | 54.907 |

The unrounded phases sum to 175.517 seconds, leaving 0.164 seconds outside
the named phases. Discovery and final readiness account for 62.61% of total
elapsed time. Those phases combine probes and content/admission work; the
artifact has no complete per-probe, hash-byte, CPU, physical-I/O or RSS
attribution. R restore linked 71 packages from cache. This is one hosted direct
managed-setup observation, not a cold setup, borrower steady-state, Slurm/NFS
measurement or explanation of E11. No optimization before/after claim follows.

**Hash-reuse audit disposition:** Retain fresh content checks and defer an
invocation-local digest cache. In a fixed-roster local fixture, the Python
aliases and Java/Picard selection produced 14 executable/jar hashes for 11
distinct files. Removing three reads would still require independent current
path, descriptor and content-identity guarantees at each use. Repeated checks
across repair, qualification and final revalidation also protect different
mutation boundaries; they are not interchangeable observations.

The fixture exercised actual file and R-tree hashing with synthetic runtime
observations on a warm local filesystem. It did not run Doctor or native probes,
measure physical storage I/O, or attribute the reported institutional delay.
Its duplicate-read cost does not justify a new cache or a weaker admission
rule. The existing binding and byte-reading owners remain shared; no alternate
hasher, persistent cache or product state is added. Reconsider the candidate
only after full-operation phase/byte measurements show a material cost and an
equivalent identity-preserving replacement demonstrates a measured benefit.

**Successful-probe diagnostic slice:** Reuse the probe runner's existing elapsed
values and the invocation collector to retain passing runtime details at actual
Doctor inspection/discovery returns. One field projection serves passed and
failed diagnostics. Passing packets flush with existing phase timings after
controlling work and the claim-release decision; failures keep their immediate
diagnostics. A returned Slurm observation is not recorded again as a fresh check,
and head and delegated compute evidence remain distinct. Log timestamps date
the deferred emission. Verbose/debug diagnosis exposes escaped passing details.

Tool version and Snakemake startup durations are separate. SHA-256 utility
timing covers its tiny test payload; it does not measure executable/jar or R-tree
hashing. Existing qualification identities, reads, probes, clocks and log owners
remain unchanged. Focused runtime tests and the integrated hosted standard CI
pass the public Doctor phase, identity, failure and observation-degradation
fixtures. Full byte/I/O/memory attribution and institutional before/after
evidence remained open at this checkpoint; the September 21 disposition makes
them optional future measurement rather than CV-26 acceptance.

**Retained probe attribution:** The managed golden-path job at
`1f4171d198cada8833f59ccd5a1bfeffab3ebaff`
([run 34939155081](https://github.com/lab-cats/EMRYS/actions/runs/34939155081),
job `104283598944`) completed donor setup and borrower verification. Artifact
`emrys-managed-golden-1`, ID `10385365580`, contains 6,756,172 bytes; its downloaded
SHA-256 matches `df47f8cbc74141df8395c3efd87c6c9d14572a21ad080e6ae2a045e719151685`.
The overall workflow failed on separate display-fixture assertions, so this is
evidence from the successful managed job rather than a whole-suite success.

| Invocation / phase | Phase seconds | Timed probes | R namespace loads | Snakemake version + startup |
| --- | ---: | ---: | ---: | ---: |
| Donor discovery | 46.968 | 46.861 | 37.810 | 7.038 |
| Donor final readiness | 47.024 | 46.745 | 38.687 | 6.282 |
| Borrower diagnosis | 53.111 | 51.580 | 42.227 | 7.241 |
| Borrower final readiness | 51.887 | 51.623 | 42.159 | 7.331 |

Each qualification pass retains 26 passing observations and 24 timed child
calls. Three path checks have no child timer; Snakemake has separate version
and startup timers. The rounded probe sums account for 97.12–99.77% of their
enclosing phases. R namespace loading is the largest observed component;
VariantAnnotation, rtracklayer and SummarizedExperiment dominate those loads.

The donor invocation took 140.458590 seconds, with a 140.350734-second phase sum
and 44.889825 seconds in package-manager phases. Borrower verification took
105.179918 seconds, with a 105.161497-second phase sum and no package-manager
events. Reuse therefore still includes fresh qualification work in this case.
Probe values have millisecond precision, and JSONL timestamps date deferred
emission rather than phase chronology. Unattributed time is not measured hash
or seal cost. These single hosted observations do not measure hashed bytes,
CPU, physical I/O or RSS, explain E11, or establish an optimization comparison.

**Selected invocation-counter slice:** The existing managed golden path wraps
its donor setup and borrower verification Doctor calls with one CI-only driver.
Each invocation runs once through the controlled public module and preserves
arguments, environment, streams, exceptions and exit status. Existing scientific,
reporting, reuse and namespace assertions stay in place. The driver restores
the two shared read owners after recording completed bytes/calls, failed calls
and elapsed read time; it introduces no additional input reads or hashes.

Separate donor/borrower JSON artifacts retain the actual CI checkout SHA,
invocation wall time, self/child CPU, resource snapshots and Linux process I/O
counters. Self RSS and the largest waited child's RSS are separate high-water
values, never summed or subtracted. Logical owner bytes exclude other Python,
semantic/gzip, Pixi and child/native reads; failed partial bytes remain unknown.
`rchar` includes pipes and cached reads; `read_bytes` is block-backed accounting,
not measured physical-device or NFS traffic. These invocation totals do not
attribute individual probe CPU, memory or I/O. Unsupported counters are unknown.

The instrumented public-module scope includes imports and observer overhead,
not identical console-bootstrap timing. It supplies no cold-cache, institutional
queue or before/after optimization evidence. Twenty eligible local harness and
workflow tests pass; the controlled public-parser test and actual donor/borrower
measurements passed hosted CI, as recorded below. No product files, commands,
dependencies, runtime identity rules or product schemas change. At that
checkpoint CV-26 remained Open.

**Retained invocation counters:**
[CI 34944690812](https://github.com/lab-cats/EMRYS/actions/runs/34944690812)
passed all 14 standard jobs, with four configured skips, at PR head
`0c2759d7479ea4a33c365f5beb3bd6d48c0f7519`. Managed job `104301191364`
uploaded artifact `10387257383` (`emrys-managed-golden-1`), 6,825,885 bytes.
The downloaded archive matches SHA-256
`1ee51845e853ef983022b639b996d51cad8ec8b7beb46b1c3d382b8e521b7e44`.
Both measurement records identify actual checkout
`20897a7cb8e4b2549e4a456142af2c971744bcb7`, whose verified parents are the
base `cea7b60f1dd4164c8f8e61266f73bccbb2024caa` and that exact PR head.
Both controlled public invocations exited zero under Python 3.14.7.

| Measurement | Donor setup | Borrower verification |
| --- | ---: | ---: |
| Invocation wall seconds | 168.319256 | 110.727837 |
| Self CPU seconds | 4.209327 | 4.138431 |
| Waited-child CPU seconds | 205.620768 | 121.208439 |
| Self RSS high-water, KiB | 128,464 | 132,116 |
| Largest waited-child RSS high-water, KiB | 1,176,504 | 1,176,296 |
| Selected-owner completed bytes / calls | 237,833,169 / 2,330 | 457,049,108 / 2,779 |
| Selected-owner read seconds | 0.174186 | 0.254114 |
| Kernel `rchar` delta, bytes | 1,851,383,535 | 1,691,378,756 |
| Kernel `read_bytes` delta | 49,762,304 | 0 |
| Kernel `write_bytes` delta | 3,853,074,432 | 397,312 |

All selected-owner calls succeeded. Their timed reads cover 0.10% and 0.23% of
invocation wall time, but exclude package hashing after payload reads and the
other gaps above. Rounded child-probe wall sums are 108.180 and 106.558 seconds;
R namespace calls contribute 86.684 and 86.087 seconds. Borrower probes account
for 96.23% of its invocation wall time, without package-manager events. Donor
native/R manager phases add 35.151161 and 20.666390 seconds. These different
workloads are not an optimization before/after comparison.

The retained post-Run donor namespace has 7,686,327,159 managed regular-path
bytes, including environments and caches. This sums path sizes, counts hard
links repeatedly and does not follow symlinks; it is not allocated disk usage
or reclaimable space. The retained donor namespace and non-managed content
comparisons exclude the new permanent seal and directory timestamps; they
remain identical before preview, after preview and after borrower verification.

The borrower read substantial logical data while its block-backed read counter
stayed zero. Cache/host state is uncontrolled, and no physical-I/O absence,
per-probe CPU/RSS attribution, production latency cause or speedup follows.
This observation supports retaining the deferred digest-cache decision;
equivalent fresh-probe semantics and representative site/queue measurements
remain prerequisites to a performance change. It does not resolve E11.

**Completed steady-ready experiment and disposition:** The explicitly selected
[managed run 34995028343](https://github.com/lab-cats/EMRYS/actions/runs/34995028343)
passed on exact checkout `45bd9cd2b7b5dc98046aa7df862200b1b674c99d`.
[Artifact 10407268954](https://github.com/lab-cats/EMRYS/actions/runs/34995028343/artifacts/10407268954)
contains all four complete Doctor diagnoses, logs and comparison records;
its 9,209,702-byte archive has SHA-256
`241fc3e4308b800f0c6f09c30238bb80560b20325c8709573c8c2e1e31d6d9e7`.
Every invocation exited zero, performed one fresh admission with the same 26
ordered passing observations and ten independent R namespace checks, and
preserved borrower bytes/stable metadata and the donor comparisons. Both
parallel trials observed two active R children and ten launches, without
observation or cleanup failures. Serial launch counters were not instrumented.

| Trial | R workers | Complete diagnosis seconds | Self CPU seconds | Waited-child CPU seconds | Sampled process-tree peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 57.403428 | 7.612158 | 60.836692 | 1201.17 |
| 2 | 2 | 41.068635 | 6.975059 | 61.601436 | 1626.86 |
| 3 | 2 | 41.998423 | 7.063463 | 62.389509 | 1641.50 |
| 4 | 1 | 57.486943 | 7.482891 | 60.859327 | 1207.46 |

The two-worker mean was 41.533529 seconds versus 57.445185 serial: 15.911656
seconds (27.70%) lower in this instrumented hosted workload. Mean sampled peaks
rose by 429.86 MiB (35.69%); combined measured CPU rose by 0.91%. Each invocation
completed 1,227 selected-owner reads totaling 227,044,786 logical bytes in
0.150–0.160 seconds. Kernel read_bytes stayed zero; this is block-accounting,
not proof of absent physical-device or NFS traffic. Samples can repeat shared
pages and miss true peaks or short-lived children. Observer overhead and
uncontrolled host/cache state remain included. These are steady-ready diagnoses,
not setup, two-boundary repair, cluster or biological measurements.

**Decision: retain serial namespace checks.** Valid profiles can select one CPU
and bounded memory; diagnosis runs before allocation/resource resolution, and
the probe owner receives no admitted concurrency budget. Unconditional parallel
R loading would overcommit that supported selection and raises measured memory.
Production interruption would also need a maintained concurrent child owner;
the existing Task subreaper requires a single thread and registered command.
A future resource-aware proposal must qualify cancellation and complete-operation
benefit before adoption. The tiny measured read-time fraction does not justify
cached admission or weaker fresh checks.

The temporary scheduling, sampling and comparison apparatus and its prototype
fixtures are retired; canonical donor/borrower counters and native-containment
checks remain. No product optimization or evidence deletion occurs. The original
and follow-up automatic PR suites had a prototype-only fixture failure
(immediate SIGKILL observation, then a 0.2-second fixture startup timeout).
Those failed suites are not promoted to passing evidence; the selected real
experiment passed independently with its 600-second trial bound. Retirement
head `13cd68750e4223431a594478804795905bfe9154` then passed all 14 standard
jobs, with four configured skips, in
[CI 34998873917](https://github.com/lab-cats/EMRYS/actions/runs/34998873917).
That combined run also validates the retained producer-workspace prerequisite.
At that checkpoint CV-26 remained Open for the complete comparable
institutional operation/queue measurements and E11 attribution; this experiment
and its adoption decision are finished.

**September 16 performance report:** Doctor repair was still experienced as too
long, and the overall setup/execution walkthrough was reported to approach a
full hour. No phase-resolved Viking timings accompanied that observation, so it
does not establish whether package work, runtime discovery, repeated probes,
Slurm waiting, synthetic execution or the actual analysis dominated. Retain the
report as negative operator acceptance and capture comparable end-to-end and
per-phase Viking measurements before selecting optimizations. Making the
synthetic E2E optional shortens the novice route but is not evidence that Doctor
itself became faster. The repeated preview/execute work in `runtime discover`
is owned by CV-08; any consolidation must preserve its mutation-boundary checks.
CV-26 remained **Open** at that checkpoint.

**Approved attribution refinement:** A repair invocation now ends with one
concise default `Doctor elapsed` field naming total elapsed time, the slowest
phase and outcome; `--verbose` retains every phase duration. No admission check,
fresh read, probe or mutation-boundary verification was removed. Making the
synthetic E2E optional shortens the novice route but is not Doctor performance
evidence. CV-26 remained **Open** at that checkpoint pending comparable
phase-resolved Viking measurements and a measured optimization.

**September 21 approved structural reduction and revised acceptance:** A
successful Slurm verification now moves from compute qualification through exact
installed-package, Project and execution-profile readmission, head storage
finalization, and one full final head diagnosis. The former complete
`head_requalification` between readmission and storage was redundant: the storage
owner consumes only its admitted Project paths, compute receipt, probes, root
identity, hashes and durability state, not runtime readiness. Removing that pass
reduces the complete successful operation from five full diagnoses to four, and
the head-node share from four to three. Product code is nine net lines smaller.

The surviving readmission still refuses Project/package/profile drift before
storage mutation. The unchanged storage owner retains corruption, interruption,
receipt, finalization and durable-evidence defenses. The final full diagnosis
still verifies runtime, package, Project and profile readiness and refuses binding
drift before Doctor records success. A valid compute or final storage receipt may
survive a later Doctor failure; the terminal `repair_requalified` record may not.
The public Doctor fault matrix continues through one simulated submission and
the real storage qualification owner, including final runtime, Project, package,
inventory and profile drift plus storage corruption and interrupted finalization.

**Local protection:** 116 Doctor, 55 storage-qualification and 85 runtime-owner
tests passed, including all 17 public Slurm Doctor scenarios above. Thirteen
documentation-structure checks, Ruff lint/format and the whitespace check passed.

No cache, snapshot, weakened hash, new abstraction, persisted state or timing
target is introduced, and no speedup is claimed. Exact implementation head
`593f6e728321f535817bcde732d263c2f86079a8` passed all 14 standard jobs, with
four configured skips and no failures, in
[CI 35577392877](https://github.com/lab-cats/EMRYS/actions/runs/35577392877).
CV-26 is **Completed** for this revised structural outcome without Viking timing
data; future measured Doctor tuning remains independently selectable.

## P3 outcome

### CV-27 Terminal-only report access

`CV-DOCS-01` in the [main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up)
owns the missing direct Quickstart link claimed below. Generated-report
portability, links, rendering and institutional transfer remain unverified by
the tiny-directory fixture; their existing acceptance is preserved.

**Finding:** The terminal operator declined a suggested web-server/SSH-tunnel
workflow; visual review was deferred (E04).
**Acceptance:** Provide a short supported method to locate and retrieve a
complete portable report/results bundle using existing transfer capabilities
where adequate. Preserve relative links and distinguish copying/viewing from
scientific/reporting validation. No local web server, tunnel, or new hosting
service should be required for the normal path. Verify the copied bundle and
record visual review separately; keep original evidence accessible.
**Owners/dependencies:** Reporting, quickstart/runbook; CV-25. Coordinate
existing `REPORT-01` through `REPORT-03` visual acceptance rather than duplicating it.

**Selected implementation:** The [Runbook](../operations/RUNBOOK.md#retrieve-reports-from-a-terminal)
now gives exact Run selection, complete `results/` transfer through existing
SSH/rsync, a read-only content comparison, and local HTML navigation. The
quickstart links to this one procedure. No product code, dependency, server,
hosting service, or EMRYS command is added. Existing reporting owns portable
relative links; established transfer tools own copying and comparison.

**Verification:** The documented copy/comparison commands are exercised on a
tiny local directory fixture, including a changed file that comparison detects.
This verifies command mechanics, not a Viking transfer or a generated report.
Operator transfer and visual acceptance remain pending; `REPORT-01` through
`REPORT-03` keep their existing visual-review authority.

## Earlier observations and coverage reconciliation

| Operator note | Retained coverage |
| --- | --- |
| Color coding; normal `emrys run` output is too verbose | CV-25; color supplements plain text, with durable detail preserved. |
| Quickstart should not branch into technical Slurm setup or compute-shell login | CV-06/07/09; default head-node journey and automatic compute delegation remain required. |
| Doctor should run on the head node; Slurm qualification should be automatic | CV-04/06/09; existing implemented delegation is context, with remaining coverage tracked in CV-01. |
| Doctor needs progress and first-setup duration guidance | CV-05/19, with Project-creation progress in CV-17 and measured repeated work in CV-26. |
| Doctor starts over every time | CV-05 replaces the original hypothesis and its duplicate with the observed distinction between reuse and revalidation. |
| Manual profile setup and repeated restoration were written as one finding | CV-07 and CV-08 retain the two distinct P0 outcomes. |
| Previously successful node should be used | CV-09/11/22 capture runtime provenance, capacity, and explicit placement; a hostname alone is not a dependency or capacity guarantee. |
| Use more of an exclusive allocation | CV-07/11/22 expose resource policy and fit; measured tuning remains in the optimization campaign. No new performance promise is implied. |

Implementation links, exact checks, remaining acceptance, and explicit
dispositions belong in the relevant card when work is selected. Update the
priority index from that same change; do not create a second campaign board.
