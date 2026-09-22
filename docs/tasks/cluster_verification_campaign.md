# Cluster verification campaign

Created: **2026-09-14**. Campaign: **CLUSTER-VERIFY-01**.

Make EMRYS's managed head-node journey usable and reliable on CSU Viking,
from Project creation through scientific execution, inspection, recovery,
and access to reports. This campaign records failures, usability gaps, and
design proposals exposed by the operator's cluster walkthrough. It includes
the synthetic study and the subsequent six-library actual-data exercise.

The [main findings matrix](backlog_matrix.md) owns the campaign outcome and
its relationship to `SITE-PARITY-01`. It delegates the finite `CV-01` through
`CV-27`, `CV-U01` through `CV-U33`, and `CV-UX-01` cards, including their
statuses and acceptance and their priorities where assigned, to the [cluster
verification backlog](cluster_verification_backlog.md). This charter owns scope,
the evidence register, and campaign completion criteria; it is not a second
card-status list.

## Scope and authority

The user approved implementing this backlog as bounded slices, with a separate
stacked PR for each slice, and approved the minimum product expansion necessary
without repeated approval pauses. Follow the
[development workflow](../operations/WORKFLOW.md): audit existing owners,
document each selected outcome and its accounting, and preserve its evidence
limits. This development authority does not authorize merging, cluster
execution, changing the active installation, or deleting retained evidence.

Priorities are the operator's P0 through P3 ordering. The duplicate question
about Doctor starting over is consolidated into CV-05: a retry reused native
installation and restored R quickly, while still repeating verification.
The record retains that correction instead of treating every retry as a
fresh installation. Within the original `CV-01` through `CV-27` priority
sequence, the three subsequently accepted additions are submission preview,
resource-profile compatibility, and the unexplained initial runtime
qualification failure. The later `CV-U` and `CV-UX` observations remain
unprioritized unless a priority is explicitly assigned; their statuses and
acceptance live in the delegated backlog.

The selected public interfaces and their limits live with the existing CLI
and coordinator owners. Deferred cleanup and broader guided operation retain
their own scope in the main backlog. Snakemake remains the execution backend;
Slurm provides placement. A Run remains immutable. Scheduler state and display
convenience do not authorize lock removal, output adoption, or evidence
fabrication.

Implementation on the active cluster installation must not be updated beneath
the running scientific job. Keep changes in the development checkout and
qualify a selected revision through an explicitly scheduled site exercise.
The earlier walkthrough's product-growth allowance in the main matrix belongs
to that earlier approved slice; it is not a blanket allowance for this campaign.

## Remaining delivery scope

The selected source and documentation corrections are implemented:

- Viking allocation and scratch guidance now describe the current owners.
- `SCHED-USAGE-01` preserves selected-cluster terminal accounting and explicitly
  bounds live sampling; `SUBMISSION-PREVIEW-01` provides compact resource
  disclosure for every Slurm approval, including Doctor.
- `INIT-01` through `INIT-03` honor the selected Projects home, read the
  explicitly selected maintained study manifest, and confirm Project creation
  after review in the same invocation.
- The focused Quickstart includes output orientation and links the separate
  optional smoke guide. CV-12/CV-27 wording and report-transfer navigation are
  reconciled, and Deferred work has named enduring owners.

The [main backlog](backlog_matrix.md#novice-setup-and-operational-follow-up)
owns these outcomes and their remaining acceptance. Its
[closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
is the single remaining verification and handoff sequence. Applicable hosted
checks and institutional observations remain required on the selected revision;
this source-completeness disposition claims no new execution evidence.

CV-U06's one-line accounting exception is approved and settled; it proves
neither functional behavior nor institutional resource policy. CV-10's accepted
trusted-workspace limitation remains with its recovery owner. Broader
documentation, 25% code reduction, the explicit >600-line exception audit,
assurance, schema, collaborator and release work remains accepted under the
[polish campaign](polish-campaign.md#current-follow-up-scope). Deferred cleanup
and complete guided operation transfer to `CLEANUP-01` and `INTERACTIVE-01` in
the [main backlog](backlog_matrix.md#deferred-operational-work).

The development tranche authorizes neither institutional execution nor evidence
deletion, campaign retirement, merge or changes to the active scientific
installation. Verification and any later retirement retain their own authority.

## Evidence register

The initial record combines operator-supplied terminal output from the
September 14 walkthrough with source review. Raw cluster logs and artifacts
remain with the operator. This document does not copy user paths, account
identifiers, or production data into the repository.

Source review for campaign creation used master `f2c0149`, which merged the
[username fix, PR #173](https://github.com/lab-cats/EMRYS/pull/173), after the
[memory-policy fix, PR #172](https://github.com/lab-cats/EMRYS/pull/172).
This identifies the reviewed code, not the exact package identity of every
operator observation. Bind site acceptance to the actual package, Run,
Attempt, profile, input, and runtime identities retained in their receipts.
Earlier exact evidence remains in the
[Viking walkthrough record](backlog_matrix.md#viking-walkthrough-findings).

| Evidence | Observation and established limit |
| --- | --- |
| E01 — First repair | Native tools and R installation completed; 71 R packages restored successfully. Repair then reported that the repaired runtime did not pass qualification, without the individual failing checks in the supplied output. Later successful probes do not identify that original cause. |
| E02 — Memory and scheduler | Viking omitted both Slurm memory variables; observed cgroup limits did not supply a finite usable bound. An explicit Slurm memory request was rejected. A later capacity-policy correction permitted Doctor to complete. Slurm's reported node memory value of `1` was not a meaningful physical-RAM measurement. |
| E03 — Username startup | Snakemake failed while building its startup header because login-name variables were absent and compute-node UID lookup failed. The shared export fix was followed by a successful synthetic resume. Its regression coverage is narrower than the complete managed golden-path requirements. |
| E04 — Synthetic completion | Operator inspection reported valid Run integrity, succeeded Attempt, all scientific milestones complete, Scientific Results complete, and Reporting complete; the latest Attempt elapsed was 3:52 and the inventory reported 151 artifacts. Visual review of both HTML reports was explicitly deferred. This is reported synthetic execution evidence, not actual-data completion or biological validation. |
| E05 — Observing active work | A running Slurm submission initially had no discoverable Run. After creation, head-node inspection reported foreign-host lock and incomplete-task blockers during reference preparation and other active tasks. These displays did not by themselves establish execution failure. |
| E06 — Reporting visibility | Synthetic inspection temporarily reported missing report transaction directories/receipts. A later inspection completed without operator repair, while the job log printed report locations. Publication overlap and shared-storage visibility delay remain competing explanations; neither is established as the cause. This remains unexplained historical provenance; CV-21 no longer requires causal reconstruction or reproduction for current acceptance. |
| E07 — Actual-data onboarding | Reusing the recorded six-library, three-pair study and 25 partitions required inspection of legacy bundles, a long initialization command, and a manual resource-profile edit. Project creation was quiet for several minutes while admission read substantial inputs. The source performs full input hashing and reference compatibility checks; their individual runtime costs were not measured. |
| E08 — Runtime reuse and verification | A new Project normally selected its own managed installation. A manual fresh-Project workaround reused the existing runtime inventory and installed tool paths; Doctor passed without a package-install action. This demonstrates a manually verified path, not a complete public managed-runtime reuse lifecycle. An already-ready Project still presented a repair plan and repeated compute checks and head finalization. |
| E09 — Cancellation | The operator cancelled an active actual-data job through Slurm during reference preparation. Accounting confirmed batch termination by SIGTERM, while EMRYS retained no terminal Attempt receipt and offered no recovery. A fresh Project was used while preserving the blocked Run. Queue removal or scheduler exit alone does not close EMRYS transactions. |
| E10 — Heterogeneous resources | One node exposed 128,544 MiB total RAM and 111,749 MiB available at a point in time; another exposed a 386,627 MiB workflow ceiling. The retained index-building allowance was 262,144 MiB. A 256-CPU exclusive request waited while 16 CPUs were occupied and 240 idle. The retained workflow used 12 cores despite the larger placement request. These are capacity/configuration observations, not measured stage demand or an optimal resource plan. |
| E11 — Doctor latency | A verification-only repair performed initial inspection, approved-input verification, readiness checking, compute qualification, another runtime/Project verification, head storage checks, and final readiness. Supplied phase times exceeded ten minutes without package installation. Repeated full-input observations exist in source; the fraction of elapsed time attributable to hashing, probes, storage, or queue waits remains unmeasured. |
| E12 — Actual-data continuation | The replacement Project's Run was active at the latest supplied observation, after compute qualification and new reference-task starts. No successful terminal scientific or reporting receipt has been supplied for that Run. Do not close actual-data acceptance from its scheduler state, nickname, or task-start records. |

The initial node-change concern was partly an interpretation failure: the
first actual-data allocation had passed its required runtime checks and
started work using selected managed tools. Different system-installed Java
versions alone did not prove that allocation unsuitable. Qualification work
must explain runtime provenance and hardware eligibility; it must not assume
that one previously successful hostname is the only valid placement.

## Delivery approach

Follow the enduring closure checklist for final-source checks, the selected
130-pair disposable-Slurm journey and the coordinated institutional campaign.
Ordinary PR CI does not select that journey. Retain the exact stop target,
current Task/Attempt, real native child exit, positively closed interruption,
unchanged predecessors, distinct resume and final scientific/reporting oracles.
Local stop fixtures or a direct managed golden path cannot supply that proof.

CV-01 remains a continuing integration obligation, not a success-only test.
Label scheduler simulations and injected faults honestly; retain real Slurm
and institutional evidence separately. The institutional combinations include
missing memory metadata plus unavailable UID lookup, reused runtimes plus
node placement, and cancellation during native-output publication. A disposable
single-node result establishes neither Viking memory policy nor cross-node
behavior. The optional novice smoke guide does not waive required synthetic
acceptance.

The current CV-12 and CV-21 dispositions retain E01 and E06 as unexplained
historical observations; neither requires causal reconstruction. New failures
found during verification belong with their existing source or operational
owner. Doctor validation, runtime inspection, CLI planning, application logging,
lifecycle recovery and reporting publication retain their existing authorities.
`INIT-02` passed exact branch-head hosted CI and still needs novice acceptance
of its explicit guided study choice. CV-U22's donor picker passed exact
branch-head hosted CI and still needs institutional acceptance; its listed
inventories are not compatibility proof until the selected reuse plan passes.

## Completion and handoff

The enduring main backlog owns the
[remaining closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
and named follow-up owners. This charter retains scope and historical evidence;
recording the handoff neither closes this campaign nor retires its backlog.

For each card, retain the selected scope, implementation revision, applicable
local/CI checks, site observations, and remaining limits. A statement that
code appears fixed is insufficient for Completed status. Record report visual
and link review separately from receipt-based reporting completion, and record
required scientific review with its scientific owner. Biological interpretation
remains external work, never a pipeline completion gate.

A read-only adversarial audit on **2026-09-17** returned affected cards to
**Open** at that checkpoint because source, journey, documentation or acceptance
gaps remained. Those historical checkpoint labels do not override each card's
current disposition. Passing hosted CI remains valid evidence for the behavior
it exercised; neither hosted success nor additional site evidence closes an
unresolved source-completeness gap.

Campaign closure requires:

- Every card has an explicit terminal disposition: accepted at its stated
  evidence level, rejected by decision, or transferred/deferred to a named
  current owner with the remaining acceptance preserved.
- The maintained novice journey is exercised from the head node through
  synthetic completion and a representative actual-data outcome, including
  the selected runtime reuse, resource placement, monitoring, cancellation,
  recovery, and report-access behavior. Outstanding failures remain findings.
- Required CI fault cases and real-site observations are tied to exact
  revisions; scheduler completion, file presence, and elapsed time are never
  promoted to scientific acceptance.
- The main matrix, delegated backlog, owner contracts, quickstart, runbook,
  and troubleshooting agree. Preserve evidence and lasting decisions with
  their owners before retiring the temporary campaign documents. The complete
  E01–E12 register and all retained exact-revision results remain here until
  that authorized transfer; retirement and evidence deletion are separate
  actions requiring their own authority.

## Related work

- `SITE-PARITY-01` retains institutional qualification and direct/Slurm parity
  acceptance; this campaign supplies the walkthrough-driven improvements.
- `SCHED-01` retains final-source verification of its implemented explicit-memory
  preflight; CV-11 owns the broader institutional heterogeneous-node acceptance.
- The institutional owner accepted CV-16/CV-24's installed watch replacement on
  2026-09-17. `DASHBOARD-RETIRE-01` has implemented new scheduler-stream naming
  with legacy read compatibility; institutional verification and the separate
  evidence-deletion boundary remain.
- The [optimization campaign](optimization_campaign.md) owns future tuning
  candidates. CV-26's source reduction removed one full head diagnosis while
  retaining exact readmission, storage finalization and final readiness.
  The owner superseded CV-26's original full-attribution and institutional E11
  timing criteria on 2026-09-22. CV-26 is Completed to its structural outcome
  and exact hosted checks; E11 remains historical and unexplained. The
  structural change alone establishes no speedup.
- The [polish campaign](polish-campaign.md) retains earlier audit observations.
  Its overlap is reconciled through the existing main-matrix owners, not a
  parallel implementation queue.
