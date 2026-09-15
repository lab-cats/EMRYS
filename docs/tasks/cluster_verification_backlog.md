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
| [CV-04](#cv-04-workflow-startup-readiness) | P0 | Verification pending | Readiness exercises minimal actual Snakemake startup. |
| [CV-05](#cv-05-reuse-versus-repeated-repair-work) | P0 | Open | Explain reused state, repeated checks, and new repair work. |
| [CV-06](#cv-06-actual-data-onboarding) | P0 | Verification pending | Provide a novice actual-data setup path. |
| [CV-07](#cv-07-site-and-workload-profile-selection) | P0 | Verification pending | Replace manual Viking resource-profile construction. |
| [CV-08](#cv-08-compatible-runtime-reuse) | P0 | Open | Reuse an existing compatible managed runtime across Projects. |
| [CV-09](#cv-09-qualification-scope-and-placement) | P0 | Open | Explain and enforce the qualified execution environment. |
| [CV-10](#cv-10-external-cancellation-and-recovery) | P0 | Open | Recover safely from externally cancelled jobs when possible. |
| [CV-11](#cv-11-resource-profile-compatibility) | P0 | Open | Detect and explain resource profiles that cannot fit a node. |
| [CV-12](#cv-12-unexplained-initial-runtime-qualification-failure) | P0 | Open | Establish the original runtime-qualification failure's cause. |
| [CV-13](#cv-13-expected-setup-versus-blockers) | P1 | Verification pending | Distinguish expected initial setup needs from failures. |
| [CV-14](#cv-14-project-directory-layout) | P1 | Verification pending | Give Projects a clear home outside the source checkout. |
| [CV-15](#cv-15-cross-node-active-run-status) | P1 | Open | Show remote active state without implying proven corruption. |
| [CV-16](#cv-16-monitoring-dashboard) | P1 | Open | Restore an integrated view of scheduler, progress, and logs. |
| [CV-17](#cv-17-project-creation-progress) | P1 | Verification pending | Explain lengthy input validation during Project creation. |
| [CV-18](#cv-18-safe-emrys-stop) | P1 | Open | Provide an operator stop action with safe recovery semantics. |
| [CV-19](#cv-19-verification-and-repair-vocabulary) | P1 | Verification pending | Name verification-only work accurately. |
| [CV-20](#cv-20-submission-state-before-run-creation) | P1 | Open | Show queued and preparing jobs before a Run exists. |
| [CV-21](#cv-21-reporting-in-progress-and-visibility) | P1 | Open | Distinguish unfinished report publication from failed reporting. |
| [CV-22](#cv-22-complete-submission-preview) | P1 | Verification pending | Show effective placement and computational limits before approval. |
| [CV-23](#cv-23-safe-project-or-artifact-cleanup) | P2 | Deferred | Decide and scope safe cleanup of unused owned state. |
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
clean-checkout check remain intact. Local workflow-contract and syntax checks
pass; the actual Ubuntu journey requires hosted CI.

**Coverage boundary:** Owner fixtures cover missing memory declarations, site
rejection responses, qualification faults and reporting transaction boundaries.
Real isolated processes cover Snakemake startup/login lookup and native signal
handling. These are not the corresponding institutional combinations. Existing
public failed-resume fixtures use scientific owner doubles; the separately
selected real-Slurm journey covers a pre-Task failed attempt and resume. Active
native cancellation through Snakemake, restricted Slurm export combined with
missing UID lookup, absent/rejected site memory policy, and live inspection
during execution/reporting still need complete hosted or institutional journeys.
CV-01 remains Open.

**Real-backend cancellation boundary:** The existing public materialization
harness now includes real Snakemake, Task-wrapper and separate native process
groups. A FIFO readiness handshake follows a native fixture's partial output;
only then does the test signal the isolated public Run process. Production
signal forwarding, native escalation and workflow grace periods remain in use.
The fixture checks group absence before lock release and receipt publication,
retained failed Task/start/log evidence, cleaned owned work and the current
blocked receipt. Scientific effects and readiness remain explicit test doubles.

Resume preview must refuse without writes. Execution-mode refusal may retain
its normal failed application log, while the Run and all earlier evidence stay
unchanged. The existing successful between-Task failure/resume case remains a
separate defense. Static and standalone native-gate checks pass; full integration
requires CI. This does not establish actual scientific-tool or Slurm/site
cancellation, or make a postentry Task retryable.

The existing public failed-Run/resume journey also checks real report producer
publication boundaries through separate public inspection processes, as recorded
under [CV-21](#cv-21-reporting-in-progress-and-visibility).

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
and exactly one submission. Public Control regressions run in CI. These are
simulations, not scheduler or institutional proof. Queue reasons and confirmed
cancellation remain open, so CV-03 remains Open.

**Implemented head-finalization slice:** After an accepted qualification job,
head storage errors retain that job ID and the escaped storage/OS cause with
the existing maintenance-log path. Interruptions keep their existing behavior;
published evidence is retained. The final already-admitted observation also
rejects changed Project/package/runtime bindings without another read.
Existing Doctor fixtures cover retained-probe corruption, cleanup failure after
receipt publication, and final input drift with one submission and no success
event. Static checks pass; behavioral execution requires hosted CI.

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
regressions run in CI.
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
queue time separately from work; keep performance changes under CV-26.
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
failure/interrupt behavior. Application execution requires hosted CI. CV-26's
phase timing separates observed work stages from submission-to-return waiting;
isolated queue attribution and first-setup/retry measurements remain open.

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
refusal. Static checks pass locally; application/subprocess cases run in CI.
Institutional novice walkthrough remains pending.

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
Static checks pass; application cases require hosted CI. No actual cluster
qualification or workload tuning is claimed.

Profile admission passes 32 local tests. Public authoring fixtures cover direct,
Viking, and custom placement, exact settings, no scientific reads/subprocesses,
no-write previews, invalid choices, no-clobber destinations, parent replacement,
and default/published-byte drift. Application cases and institutional novice
walkthrough remain pending; no performance optimum or actual capacity is claimed.

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
await CI. These use synthetic runtime/failed-Run fixtures, not scientific
execution. CV-08 remains Open for hosted/institutional acceptance, compute-node
accessibility and the complete managed journey.

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
and capacity regression cases; it adds no new execution or installation.
CV-09 remains Open for institutional compatible-node/incompatible-runtime
acceptance and any concrete incompatibility gaps that evidence identifies.

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
the preserved lock/no-receipt boundary; their execution awaits hosted CI.
Ruff, formatting and whitespace checks pass. These source-derived protections
do not establish E09's cause or real Snakemake/Slurm cancellation behavior.
Lost wrappers, escaped descendants and explicit safe reconciliation remain
open. No task or Run becomes recoverable solely because an outer group stopped.

**Established source constraint:** A Task with admitted entry and no verified
result remains blocked after clean native cancellation. Task re-entry refuses
its fixed start/verified paths, Snakefile admission rejects the incomplete
entered scope, and receipt validation requires every start to be verified for
a nonblocked outcome. Receipt history also permits only one start per logical
Task scope. Control and lifecycle retain these predicates before resume.
The CV-01 real-backend fixture protects this boundary; a released lock or clean
writer shutdown alone is insufficient recovery evidence.

Same-input `run` resolves to the same content-derived Run ID and refuses its
non-pristine destination. Processing reuse accepts only a complete successful
source. Neither is an implicit postentry retry route. Supporting that route
requires a versioned start/history and abort-closure model that preserves prior
references, proves owned cleanup and unchanged inputs, freezes exact retry
intent, and rechecks it under the Run lock. Existing blocked evidence must not
be silently migrated or reclassified. That recovery design remains Open.

**Retry prerequisite decision:** Do not add recovery schemas or relax these
predicates before qualifying an exact production writer boundary. Current
group quiescence proves the registered process group is empty; a detached
descendant can belong to another group. Run-local output placement alone does
not prove that every writer has stopped. The canonical BAM shell uses
foreground samtools calls and the outer launcher uses `exec`, but executable
hashes, inherited utility paths and loader/plugin dependencies do not establish
a closed set of writers. Existing fake-samtools tests and the substituted
native producer in CV-01 do not supply actual samtools containment evidence.

A future supported class needs enforceable descendant containment or an exact
audited non-detaching launcher/tool/environment contract with real cancellation
evidence. Only then should one complete change introduce immutable per-Attempt
start history, positive abort closure before any native output publication,
and exact frozen retry references. Closure must establish reaped native execution, unchanged
inputs and directory membership, owned cleanup and absent final destinations;
every entered concurrent Task must independently close or verify. Historical
admission must preserve those recorded facts after a later retry creates outputs,
while preview freshly checks retry readiness and entry repeats it under the
Run lock.
Processing reuse, reporting, receipts, backend admission and presentation must
all consume the same history. Existing blocked receipts remain ineligible.
No speculative protocol versions, new mutable state or retry action are added
by this design decision. CV-10 stays Open for this prerequisite and E09 evidence.

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
require installed Analysis entry-point metadata unavailable locally. Explicit
reservation comparison and institutional heterogeneous-node acceptance remain
separate, so CV-11 remains Open.

**Implemented reservation-fit slice:** The final effective execution profile
checks CPU and explicit memory requests before submission, Doctor repair
planning, and profile creation. It reuses the shared resource predicates with
reservation-specific diagnostics and replaces Control's duplicate CPU rule.
Placement-only resume applies retained policy first using the existing reads;
no inherited-policy loader API or fabricated capacity is introduced. Symbols
are preserved, memory omission stays unknown, and actual allocation admission
still controls execution. The final pure resource/profile suite passes 64
tests; public no-submit/no-write, Doctor, authoring, and resume cases run in CI.
Institutional heterogeneous-node acceptance remains pending.

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
pass locally; application execution requires CI. Operator acceptance is pending.

### CV-14 Project directory layout

**Finding:** The walkthrough placed a Project at the source checkout root and
later needed a separate Projects directory (E04, E07). **Acceptance:** Give the
novice a clear durable Projects home outside source checkouts and a supported
destination selection. Respect existing directories and symlink/path rules;
do not automatically move old Projects or break runtime/input references.
Cover invocation from a checkout and from the Projects parent.
**Owners/dependencies:** Onboarding, quickstart; CV-06/08.

**Selected implementation:** The quickstart and Runbook use one chosen durable
Projects parent, separate from the checkout, for synthetic and own-data setup
and reconnection. Existing `init NAME` selects its parent through the current
directory; synthetic initialization retains absolute `--output-dir` selection.
Both reuse existing canonical-parent/absent-child admission. Existing Projects
remain at their original paths. The shell variable is a walkthrough convenience,
not a new application registry or path contract; no product change is needed.

**Verification:** Existing public onboarding tests exercise synthetic creation
from the checkout and Projects parent, and own-data creation beneath the chosen
parent. They preserve no-write preview, input references and bytes, no copied
reads, and existing-destination refusal. Focused execution and documentation
checks run in the locked CI environment; operator walkthrough remains pending.

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
other labels. Static checks pass; the new task cases await hosted CI. CV-15
remains Open for institutional cross-node observations and any remaining
state distinctions established by those observations.

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

**Implemented evidence projection:** CV-15 supplies Task evidence counts;
CV-25 adds admitted terminal outcomes and exact retained logs to the same
inspection snapshot. CV-20 supplies exact selected-request scheduler state.
These are shared CLI observations for a future integrated view; the existing
dashboard remains in place until its complete replacement acceptance is met.

**Selected watch slice:** `inspect --watch` holds one exact Project/request/Run
selection and presents scheduler observations, dated scientific and reporting
evidence, elapsed context, bounded sanitized tails and next supported actions.
Shared presentation replaces duplicate milestone/Task/elapsed projection across
static and watch output. The initial and explicit refresh perform existing full
Run admission; screen painting performs no reads and automatic refresh only
checks scheduler state and the selected diagnostic tail. One daemon reader
coalesces refresh requests so quitting does not await stalled filesystem I/O.
Observation dates and historical Attempt identity remain explicit.

The existing input owner supplies bounded suffix reads with stable no-follow
identity checks. Replaced/truncated streams do not inherit previous bytes or
digest authority. No command execution, automatic resubmission or recovery
action is added. The first view does not cover full active-native-log discovery,
legacy standalone/offline parity or institutional terminal/NFS behavior.
Those gaps and complete replacement validation remain under this card and
`DASHBOARD-RETIRE-01`; no old dashboard surface or evidence is retired.

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
run in CI. The institutional large-input walkthrough remains pending.

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
no cancellation authority. Existing dashboard discovery remains compatible.
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
removed or repaired. Local fixtures and hosted CI can validate these software
boundaries; actual queued/native-task cancellation and institutional recovery
evidence remain separate and pending.

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

**Implemented scheduler-observer prerequisite:** The existing dashboard now
shares strict root-job/numeric-UID admission across discovery, accounting, and
state observation. It requests accounting duplicates rather than silently
choosing the latest reused ID, rejects ambiguous/missing/mismatched identity,
checks selected stream paths on refresh, and reports unavailable proof as
`UNKNOWN`. Exact batch-step identity controls usage display. This retires
username-environment matching and duplicate first-row accounting parsing while
preserving standalone loading and existing bounded discovery/stream handling.
Job-ID/UID/path agreement is not request/cluster identity or recovery proof;
integration with retained requests remains open. The standalone dashboard suite
passes 66 local tests; after duplicate-query changes all 50 affected cases pass.
Actual scheduler/site verification remains pending.

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
v1 remains readable as historical diagnostics. Existing dashboard discovery
accepts exact matching token-based stream pairs and preserves legacy support.
Doctor's qualification paths and isolated dashboard loading are unchanged.
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
existing dashboard and request adapter share extracted stdlib identity and
accounting mechanics while preserving isolated dashboard loading.

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
application cases passed standard CI after the fixture correction. CV-20 remains
Open for integrated monitoring and institutional scheduler acceptance.
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
context and module mutation; public early-log fixtures require hosted CI.

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
records and snapshot changes; full candidate and public fixtures require CI.
Institutional reconnect/queued/preparation observations remain pending.

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
Static checks pass; application cases require hosted CI. These cases establish
the overlap mechanism, not the historical cause of E06. That cause and actual
site visibility/finalization evidence remain unresolved, so CV-21 remains Open.

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
scientific journey. Static checks and independent review pass; full integration
requires CI. It covers producer publication boundaries, not arbitrary mid-write
timing, institutional filesystem visibility or the cause of E06.

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
pass locally; public Control and Doctor execution runs in CI. These provide
software evidence; institutional preview acceptance remains pending.

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

**Selected first action:** After the watch implementation passed its standard
CI checks, interactive Run-selected `--watch --actions` adds `p` to review the
ordinary resume plan. It captures the exact Project/Run, closes the view and
restores the terminal, then calls the existing resume handler once with its
ordinary preview/confirmation defaults. An already active read may finish but
cannot supply action authority or trigger another refresh. There is no shell
executor, action worker, stored plan or automatic return to monitoring.

Request-selected and noninteractive action modes are refused. Fresh Control
and lifecycle checks retain selection, predecessor and recovery authority.
For Slurm, the existing preview freezes the submission/profile request and
scientific admission runs on compute; a concurrent resume can still consume an
unnecessary allocation. Stop, report, new-analysis selection and complete
dashboard replacement remain separate work. This slice does not establish
institutional monitoring/action acceptance or retire the old dashboard.

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

**Implemented Task-log slice:** Normal inspection counts admitted terminal
Task attempts; verbose/debug output shows their recorded outcome, original
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
logs. Public normal/verbose/debug rendering uses one snapshot, escapes diagnostic
text, preserves evidence and retains Results/recovery refusal. Static checks
pass; application fixtures require hosted CI. Startup/application/reporting
stream association and the integrated dashboard remain open.

**Started-Task stream slice:** The admitted start already binds the exact frozen
Task dispatch. One pure Task-owned root builder replaces repeated construction
in dispatch, directory materialization, terminal admission and debug output.
One stream projection serves watch and verbose/debug inspection without new
reads, schemas or admission rules. It preserves terminal references, including
preentry failure history, and derives expected paths only when both admitted
start fields are present. Exact historical Attempt filtering and path
deduplication keep the selected request's streams distinct.

Start publication precedes stream opening; derived paths establish neither
existence nor liveness. Current tail bytes remain unverified diagnostics under
the existing ownership/stability checks. Missing or damaged starts supply no
derived path. Focused presentation tests cover these cases and no-I/O projection;
actual lifecycle/public cases require hosted CI. Institutional discovery,
standalone/offline replacement and interpretation of native liveness remain
separate acceptance.

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
execution requires hosted CI. Read/hash bytes, probe attribution, process memory,
actual scheduler timing and comparable before/after measurements remain open;
this slice establishes timing observations, not a measured speedup.

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
remain unchanged. Focused runtime tests pass; public Doctor phase, identity,
failure and observation-degradation fixtures require hosted CI. Full byte/I/O/
memory attribution and institutional before/after evidence remain Open.

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
