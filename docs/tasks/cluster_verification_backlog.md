# Cluster verification backlog

This is the delegated card-status and acceptance authority for
`CLUSTER-VERIFY-01` in the [main findings matrix](backlog_matrix.md).
The [campaign](cluster_verification_campaign.md) defines scope, evidence
E01–E12, delivery boundaries, and closure. Created **2026-09-14** from the
operator's combined failures, usability findings, and design proposals.

P0–P3 preserve the supplied priorities. All cards began **Open**: prior fixes
and observed successes are context, not closure of these remaining outcomes.
Use the main matrix's status meanings. Recording a card accepts the finding
for tracking; it does not authorize a new command, recovery rule, installation,
cluster action, evidence promotion, or product-growth exception.

## Priority index

| ID | Priority | Status | Outcome |
| --- | --- | --- | --- |
| [CV-01](#cv-01-managed-golden-path-coverage) | P0 | Open | Managed golden path covers the cluster-discovered cases. |
| [CV-02](#cv-02-individual-qualification-diagnostics) | P0 | Verification pending | Retain and surface each failed qualification check. |
| [CV-03](#cv-03-scheduler-and-execution-failure-messages) | P0 | Open | Separate submission, queue, execution, and finalization failures. |
| [CV-04](#cv-04-workflow-startup-readiness) | P0 | Open | Readiness exercises minimal actual Snakemake startup. |
| [CV-05](#cv-05-reuse-versus-repeated-repair-work) | P0 | Open | Explain reused state, repeated checks, and new repair work. |
| [CV-06](#cv-06-actual-data-onboarding) | P0 | Open | Provide a novice actual-data setup path. |
| [CV-07](#cv-07-site-and-workload-profile-selection) | P0 | Open | Replace manual Viking resource-profile construction. |
| [CV-08](#cv-08-compatible-runtime-reuse) | P0 | Open | Reuse an existing compatible managed runtime across Projects. |
| [CV-09](#cv-09-qualification-scope-and-placement) | P0 | Open | Explain and enforce the qualified execution environment. |
| [CV-10](#cv-10-external-cancellation-and-recovery) | P0 | Open | Recover safely from externally cancelled jobs when possible. |
| [CV-11](#cv-11-resource-profile-compatibility) | P0 | Open | Detect and explain resource profiles that cannot fit a node. |
| [CV-12](#cv-12-unexplained-initial-runtime-qualification-failure) | P0 | Open | Establish the original runtime-qualification failure's cause. |
| [CV-13](#cv-13-expected-setup-versus-blockers) | P1 | Open | Distinguish expected initial setup needs from failures. |
| [CV-14](#cv-14-project-directory-layout) | P1 | Open | Give Projects a clear home outside the source checkout. |
| [CV-15](#cv-15-cross-node-active-run-status) | P1 | Open | Show remote active state without implying proven corruption. |
| [CV-16](#cv-16-monitoring-dashboard) | P1 | Open | Restore an integrated view of scheduler, progress, and logs. |
| [CV-17](#cv-17-project-creation-progress) | P1 | Open | Explain lengthy input validation during Project creation. |
| [CV-18](#cv-18-safe-emrys-stop) | P1 | Open | Provide an operator stop action with safe recovery semantics. |
| [CV-19](#cv-19-verification-and-repair-vocabulary) | P1 | Verification pending | Name verification-only work accurately. |
| [CV-20](#cv-20-submission-state-before-run-creation) | P1 | Open | Show queued and preparing jobs before a Run exists. |
| [CV-21](#cv-21-reporting-in-progress-and-visibility) | P1 | Open | Distinguish unfinished report publication from failed reporting. |
| [CV-22](#cv-22-complete-submission-preview) | P1 | Open | Show effective placement and computational limits before approval. |
| [CV-23](#cv-23-safe-project-or-artifact-cleanup) | P2 | Open | Decide and scope safe cleanup of unused owned state. |
| [CV-24](#cv-24-run-center-actions) | P2 | Open | Explore a dashboard that invokes supported CLI operations. |
| [CV-25](#cv-25-log-discovery-and-readable-output) | P2 | Open | Find the correct logs without memorizing scheduler IDs. |
| [CV-26](#cv-26-repeated-doctor-input-reads) | P2 | Open | Measure and remove redundant reads within Doctor. |
| [CV-27](#cv-27-terminal-only-report-access) | P3 | Verification pending | Retrieve portable reports from a terminal-based workflow. |

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

### CV-04 Workflow startup readiness

**Finding:** Tool probes passed before Snakemake's username lookup failed (E03).
**Acceptance:** Add or reuse a minimal, bounded Snakemake startup exercise in
the intended compute environment that traverses actual backend initialization
without running the study. Cover the restricted environment and absent passwd
entry. State the check's limits: successful startup is not complete science.
Keep package installation in explicit maintenance and avoid a second backend.
**Owners/dependencies:** Doctor, runtime inspection, workflow owner; CV-01/02.

### CV-05 Reuse versus repeated repair work

**Finding:** Doctor appeared to start over, but retry output showed native
installation reused and R restore completed quickly; verification still repeated
(E01, E08, E11). **Acceptance:** Plans and progress distinguish reused tools,
cached package work, checks that must repeat, and new install/repair actions.
Explain why repeated work is necessary and retain successful prior evidence
without claiming stale checks still pass. Cover unchanged retry, interrupted
setup, and a changed dependency/input. Show first-setup duration guidance and
queue time separately from work; keep performance changes under CV-26.
**Owners/dependencies:** Doctor and existing package-manager integration.

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

### CV-07 Site and workload profile selection

**Finding:** Built-in site selection still required a hand-edited profile for
the actual workload (E07, E10). **Acceptance:** Provide a supported way to select
site placement and workload resources without Python snippets or hand-authored
Slurm YAML. Present the exact resulting settings, preserve explicit choices,
and distinguish a tiny fixture from a full cohort. Do not silently change
scientific parameters or promote an unbenchmarked preset as optimal. Qualification
submission size and resulting queue cost must be understandable.
**Owners/dependencies:** Execution profiles, onboarding, Doctor; CV-09/11/22.

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

### CV-10 External cancellation and recovery

**Finding:** Slurm cancellation left a nonterminal Run with unfinished task
state and no offered recovery (E09). **Acceptance:** Characterize normal
cancellation, TERM/KILL escalation, and lost wrapper/child processes. Account
for the delegated process tree; retain an honest terminal outcome and partial
publication evidence when possible. Provide an explicit supported reconciliation
path when finalization was interrupted, proving process absence and ownership
before safe resume. Ambiguous state remains preserved and clearly explained.
Test interrupted native output, pre-entry state, publication boundaries, and
failure of finalization itself. Scheduler cancellation alone is insufficient
authority; never fabricate success or delete a lock to obtain resume.
**Owners/dependencies:** Slurm transport, lifecycle, task/publication owners,
inspection/control; CV-01, CV-03, CV-15, CV-18.

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

### CV-12 Unexplained initial runtime qualification failure

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

### CV-14 Project directory layout

**Finding:** The walkthrough placed a Project at the source checkout root and
later needed a separate Projects directory (E04, E07). **Acceptance:** Give the
novice a clear durable Projects home outside source checkouts and a supported
destination selection. Respect existing directories and symlink/path rules;
do not automatically move old Projects or break runtime/input references.
Cover invocation from a checkout and from the Projects parent.
**Owners/dependencies:** Onboarding, quickstart; CV-06/08.

### CV-15 Cross-node active Run status

**Finding:** Head-node inspection presented unproved remote lock ownership and
unfinished task records as blocked Run/Results during active work (E05).
**Acceptance:** Distinguish remotely active or unverified ownership, work in
progress, and demonstrated invalid state. Report the limits of available proof
without authorizing unsafe resume. Cover active, completed, unreachable-host,
stale/ambiguous ownership, and terminal-without-finalization cases. Scheduler
evidence may inform display but cannot replace transaction integrity checks.
**Owners/dependencies:** Inspection/lifecycle and presentation; CV-10/16/20.

### CV-16 Monitoring dashboard

**Finding:** The operator needed separate scheduler panes, manual tails, and
misleading interim inspection output to monitor work (E05, E06, E12).
**Acceptance:** Provide one view of scheduler state, stage/task progress,
elapsed time, relevant logs, and next supported actions. Use current Run and
submission authorities with explicit uncertainty. Preserve the existing
dashboard's useful discovery/accounting behavior and sanitized stream handling;
cover missing/rotated/truncated logs and reconnecting. Retire the old dashboard
only after the replacement is validated under `DASHBOARD-RETIRE-01`.
**Owners/dependencies:** Run coordinator presentation and existing dashboard;
CV-15/20/21/25. Action execution is the separate CV-24 proposal.

### CV-17 Project creation progress

**Finding:** Actual-data initialization silently read large inputs for minutes
(E07). **Acceptance:** Show the current validation phase, elapsed time, and
useful file/byte progress when measurable. Explain large-input work before it
starts; label estimates and avoid invented completion percentages. Preserve
no-write preview, interruption behavior, and content/compatibility checks.
**Owners/dependencies:** Onboarding and existing progress presentation; CV-06.

### CV-18 Safe EMRYS stop

**Finding:** There was no clear supported stop action that preserved a route
to resume (E09). `emrys stop JOB_ID` is the operator's proposed spelling.
**Acceptance:** Settle target selection for queued submissions and active Runs,
confirm exact ownership/intent, and route cancellation through the shared
lifecycle. Report progress and the actual terminal/recovery state. A successful
stop must not promise resume when task evidence is ambiguous. Cover stopping
before Run creation and during a native task. Reuse CV-10 recovery mechanics.
**Owners/dependencies:** CLI/control, Slurm transport, lifecycle; CV-10/20.

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
or recovery rule changes. CV-05's queue-time attribution and CV-13's setup-state
classification remain open; missing storage evidence is not assumed harmless.

**Verification:** Focused regressions cover verification-only and package-action
plans, confirmation/refusal, progress, failures, and preserved no-write preview.
Doctor regressions require the locked CI environment. Institutional operator
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

### CV-21 Reporting in progress and visibility

**Finding:** Missing reporting receipts briefly appeared as failures and later
passed without intervention (E06). **Acceptance:** First establish whether
publication overlap, storage visibility, or another cause explains the case.
Represent known in-progress publication accurately while retaining rejection
of truly missing or invalid committed outputs. Exercise inspection at each
report transaction boundary and controlled visibility/finalization faults;
do not add blind sleeps or turn missing evidence into success.
**Owners/dependencies:** Reporting publication/boundary and inspection;
CV-01/15/16. Visual report review remains separate.

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

### CV-26 Repeated Doctor input reads

**Finding:** A verification-only Doctor operation repeated Project/runtime
observations and exceeded ten minutes (E11). **Acceptance:** Measure a complete
Doctor operation and attribute phases, hashes/bytes, probes, and queue time.
Audit duplicate mechanics across callers; consolidate only observations proven
equivalent at the same trust/mutation boundary. Preserve detection of input,
package, runtime, and storage changes during repair and qualification. Report
before/after measurements and residual costs; metadata or cached hashes alone
do not justify weaker checks. Do not invent an unmeasured time target.
**Owners/dependencies:** Doctor, normalization/runtime inspection, existing
validation helpers; coordinate optimization discussions 11–13 and CV-05/17.

## P3 outcome

### CV-27 Terminal-only report access

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
