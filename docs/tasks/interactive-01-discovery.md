# INTERACTIVE-01 guided operation discovery

This working record supports [INTERACTIVE-01](backlog_matrix.md#deferred-operational-work).
The main backlog alone owns its status, priority, outcome, and acceptance. Finding
numbers below are navigation, not new backlog items or implementation approval.
The [CV-U19 record](cluster_verification_backlog.md#cv-u19-long-term-interactive-cli)
preserves the operator's eventual direction: guided setup and analysis launch by
default, with an optional manual route. It does not select a prompt sequence,
transition, or `--advanced` spelling.

**Accepted owner decision (2026-09-22).** Bare `emrys` on a terminal will start
guidance; existing named commands remain the manual route. This selects the
entry and route, not the guide's full transcript, implementation slice, or an
`--advanced` flag. The [backlog row](backlog_matrix.md#deferred-operational-work)
remains the status and acceptance authority.

## Review basis and evidence limit

The source review is pinned to [PR #304](https://github.com/lab-cats/EMRYS/pull/304)
head `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`. PR #303 is a sibling,
not part of that head. The checkout used for this document started clean at the
named commit. [PR #307](https://github.com/lab-cats/EMRYS/pull/307) head
`5ecc409c123fe34f746a61f7e92397c6978f3cab` descends from that commit;
its earlier source change adds selected Doctor timing checks to the synthetic E2E
runner. Its later commits change documentation only. It changes no product
owner, Quickstart, or INTERACTIVE-01 text cited below.
[PR #316](https://github.com/lab-cats/EMRYS/pull/316) head
`e1e802177b5333454e93e5e7c4f38d229f33f62a` and
[PR #320](https://github.com/lab-cats/EMRYS/pull/320) head
`1bb133e5fb47d82e84e8bc797c7591dcbbf4d8ae` are separate open branches
proposing INIT-02 study selection and CV-U22 runtime donor selection; their
latest commits change documentation only. Their changes are compared, not
included in this documentation branch.
PR #320 is stacked on an earlier #316 head, so its integration remains to be
reconciled. Source, owner contracts, tests, and guides were inspected. No
product test was run locally for this audit; no installed-command walkthrough,
PTY journey, dependency installation, or Viking execution has been completed.
The line references below are to the pinned source revision and must be
rechecked if the target changes.

The proposed journey begins once `emrys` is installed on the Viking head node.
The [Quickstart](../../quickstart.md) still owns the preceding uv, Pixi, clone,
and locked-environment installation because an EMRYS CLI cannot run before it
is installed. This scope boundary is a proposal to settle, not a narrowing of
the accepted backlog outcome. For the Viking path, the intended endpoint is one
confirmed Slurm submission and an exact inspection handoff, never inferred Run
creation or completion.

## Findings matrix

| No. | Boundary | Source-grounded discovery | Unsettled choice or next evidence |
| --- | --- | --- | --- |
| [1](#1-public-entry-and-manual-route) | Public entry | Bare `emrys` currently exits with usage error; marked saved settings load even before help/version parsing. Current prompting needs stdin and stderr terminals. | Accepted: bare terminal entry starts guidance, named commands remain manual. Specify the transcript and preserve nonterminal behavior. |
| [2](#2-bootstrap-and-saved-settings) | Setup | Setup is checkout-bound, defaults to a dry-run, and creates one `.env` only with `--execute`; the CLI discards the loaded settings-file path before dispatch. | Decide same-invocation approval and value propagation; skip create-absent Setup for returning users. |
| [3](#3-project-context) | Project | Named Init uses the selected Projects home or current directory; Project-aware commands use an exact Project path and never search parents for one. | Define new versus existing selection without newest-Project or partial-root inference. |
| [4](#4-scientific-input-questions) | Scientific intent | Init already asks for reference, FASTQs, assignments, comparison, regions, target, and disclosed defaults. Detected sample IDs precede mate validation. | Reuse its questions; review a complete prompt transcript, invalid inputs, and refusal paths. |
| [5](#5-maintained-study-selection) | Study selection | This branch still needs an explicit EV/PUM1 manifest; sibling PR #316 proposes an explicit packaged selection. | Reconcile that pending implementation and verify installed-package and novice behavior. |
| [6](#6-project-preview-and-publication) | Init approval | Init confirms after review and preserves create-absent and input-change checks. Decline and creation can both return zero. | Expose an owner outcome without parsing text or treating file presence as proof. |
| [7](#7-read-only-project-validation) | Validation | Existing validation re-admits Project inputs and scientific compatibility without writing, including FASTQ content rehashing. | Budget repeated reads and stop on failure without promoting it to runtime proof. |
| [8](#8-runtime-source-and-admission) | Runtime | This branch uses an exact donor or current environment; sibling PR #320 proposes a bounded donor picker. A runtime file is only a candidate, and donor preview validates two Projects. | Keep source choice explicit, report both mutation paths, and preserve partial evidence. |
| [9](#9-doctor-readiness-and-repair) | Doctor | Diagnosis is read-only; confirmed maintenance and Slurm qualification remain Doctor-owned. Readiness and public exit alone lose repair history. | Distinguish ready, declined, blocked, and repaired outcomes; carry one exact profile. |
| [10](#10-direct-and-slurm-run-approval) | Run | Interactive direct execution confirms a frozen Run plan. Slurm confirms a submission/resource request; its Run plan is built later on compute. Terminal scheduler state can pass the duplicate guard. | Bind exact Analysis and reviewed request; retain duplicate-request refusal and manual retry review. |
| [11](#11-submission-and-watch-handoff) | Monitoring | Submission retains a request before `sbatch`. Numeric `watch JOB_ID` is scheduler-only diagnostic selection. | Hand off the exact Project request, then re-admit any later Run association. |
| [12](#12-return-recovery-and-completion) | Return | Inspection owns completion and recovery from admitted evidence; multiple requests may map to one Run. | Define exact request-bound re-entry without persistent wizard state or automatic resubmission. |
| [13](#13-owner-results-and-maintenance-footprint) | Composition | Several public handlers return zero for both no-write preview and success; owners already implement admission, repair, and scheduling. | Audit private outcomes and caller-complete consolidation; quantify any product-growth exception. |
| [14](#14-presentation-documentation-and-proof) | Acceptance | The Quickstart still chains separate commands; approvals, watch, and actions use different terminal gates. | Draft novice wording, redirected terminal cases, hosted checks, and separate Viking acceptance. |

## Findings and source discoveries

### 1. Public entry and manual route

**Observed.** [`__main__.py`](../../src/emrys/__main__.py) lines 224-241 and
349-384 registers owner commands and exits with usage error 2 if `COMMAND` is
absent. It loads a marked current/ancestor `.env` *before* parsing any command,
so malformed saved settings can also block `--help` and `--version` with exit 2.
Those options and explicit commands already have public behavior. The installed
CLI is the interaction owner and carries no scientific semantics
([architecture](../architecture/ARCHITECTURE.md#responsibility-boundaries)).
The `emrys` console script enters the controlled Python launcher declared in
[`pyproject.toml`](../../pyproject.toml), which restarts `-m emrys` before owner
imports (`source_authority.py` lines 146-153). That launch isolation is an
adjacent contract to preserve, not a second guide entry to introduce.

**Accepted design choice.** The owner approved bare `emrys` on a terminal as
the guided entry and existing named commands as the manual route. Route only
the no-command interactive case after existing argv and saved-settings
admission; preserve the controlled console launcher and parser ownership. A
new `--advanced` flag is not selected. Preserve the current no-write usage
failure for nonterminal bare invocation unless separately approved, along with
help/version, unknown-option, and named-command behavior. Check clean and
malformed saved settings, both the installed console launcher and isolated
`-m emrys` path. The current prompt gate requires both stdin and stderr to be
terminals (`onboarding.py` lines 960-961); stdout redirection alone does not
make an otherwise interactive invocation nonterminal.
Existing public tests cover isolated help/version and named commands, but no
bare-command TTY journey was found (`test_public_cli_contracts.py` lines
482-532 and 713-800).

### 2. Bootstrap and saved settings

**Observed.** [`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 153-260 loads the nearest marked `.env` only from the current directory's
ancestry. Process values take precedence. Setup requires an EMRYS checkout,
shows Projects home/site/log root, returns zero on either preview or publication,
and writes an absent mode-`0600` `.env` only with `--execute`.
[`__main__.py`](../../src/emrys/__main__.py) lines 349-358 loads that environment
once before parsing. A setting published later in the same invocation has not
automatically changed the already parsed defaults.

**To settle.** Show a distinct save confirmation in the guide and carry the
admitted values explicitly to following stages. The existing Setup has no
interactive commit prompt: `--execute` is its write authority, while omission
returns a dry-run with exit zero. A guide must review the proposed `.env` before
invoking that authority; repeating the public Setup handler would ask for the
same inputs again. Do not overwrite existing
settings, search an unrelated checkout, or create global Project, profile,
runtime, or scientific defaults. Check refusal/EOF, an existing `.env`, process
precedence, and a returning user outside the checkout. Existing coverage starts
at `test_onboarding.py` lines 212 and 301.

A returning user with saved settings must skip create-absent Setup. The CLI
startup loader returns the exact marked `.env` path it found, but `main`
currently discards that result (`__main__.py` lines 349-357). Retain that
private result to show the origin and effective values, including process
overrides, without scanning for settings again. A regular unmarked nearer
`.env` is ignored by the existing loader; a malformed marked one stops before
guidance. If a process value outranks a reviewed saved value, the guide must
show the value that will actually apply in later commands rather than promise
that `.env` overrides the process.

### 3. Project context

**Observed.** Named Init selects `EMRYS_PROJECTS_ROOT` or the current directory
and requires an absent child of a canonical writable parent (`onboarding.py`
lines 464-492 and 1261-1269). `project_definition_path` accepts a current
Project or one exact directory/YAML selector and rejects path aliases (lines
270-295). Its implicit selection is only `project.yaml` in the current
directory: it does not search parents or a global Project registry. The
existing Run selector never chooses the latest Run
([coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#public-model-and-admission)).

**To settle.** Specify a new/existing choice and retain the canonical absolute
`project.yaml` path returned by admission across validation, Doctor, Run, and
inspection. A fresh Setup starts inside the checkout; returning use from
elsewhere needs an exact Project path.
Creating a new Project outside the checkout also needs an explicitly carried
Projects home, because `.env` is loaded only from the current directory's
ancestry. Do not silently fall back to the return directory as the new home.
Do not select by directory order, adopt an incomplete creation, or infer a
Project from scheduler text. Check missing, ambiguous, external, and changed
paths using the existing path admission owner.

### 4. Scientific input questions

**Observed.** Init already collects admitted reference FASTA/GTF, recognized
FASTQ pairs, study or per-sample strandedness, conditions and pairing groups,
comparison direction where it is unambiguous to offer both directions, partition
source, target change, and disclosed paired-CMH defaults (`onboarding.py` lines
654-704, 812-893, 939-1096, and 1163-1258). An explicit comparison direction
and selected reference regions are scientific intent, not site defaults.

**To settle.** Compose the existing prompts and review rather than create a
second scientific question set. Draft a complete plain-English transcript for
two-condition, mixed-strand, multi-condition, background, and invalid-input
cases. Keep color optional and every default readable with `NO_COLOR`. Inspect
the current prompt tests at `test_onboarding.py` lines 609-728 and 1092-1152.
The current `Detected FASTQ pairs` display lists candidate sample IDs before
mate validation. Discovery scans only immediate recognized filenames and
ignores other files; a sample with one mate may be listed and then refused
before preview (`onboarding.py` lines 964-1025 and 1433-1470). The guide must
not describe that display as proof of six complete libraries. Cover missing
mates and unrecognized filenames in the prompt review.

The current interactive Init path has this order; it is a source trace, not a
proposed new guide transcript:

| Step | Current question or decision | Boundary to preserve |
| --- | --- | --- |
| Before entry | `PROJECT_NAME` is a required positional argument; `--analysis-name` defaults to `primary`. | A composed guide still needs an explicit new or existing Project choice and name. |
| Reference | Missing reference FASTA, then GTF paths. | Both are admitted files; relevant FASTA contents are snapshotted before later derived settings. |
| Samples | Missing FASTQs trigger a directory question and recognized pair listing; missing sample assignments trigger study strandedness, then each sample's condition and pairing group, and per-sample strandedness only for `mixed`. | The study suggestion is `unknown`; sample assignments are scientific input. |
| Partitions | If no partition input was supplied, ask for a regions file or selected FASTA names/regions. | An empty selector is refused; the first 24 admitted FASTA names are shown when manual selectors are requested. |
| Comparison | When exactly two conditions have compatible paired strata and neither direction was supplied, offer two numbered directions without a default. Otherwise, missing control and treatment are asked later. | Direction is explicit scientific intent. |
| Analysis | Missing target change, then remaining settings in `_PROJECT_FIELDS` order; the five paired-CMH settings are offered as one disclosed default set only when all five are absent. | A supplied subset is not silently completed by that group offer. Background condition is an optional argument, not an interactive question; its maximum is shown in the default offer only when active. |
| Review | Preview destination, libraries, Analysis/site, reference, partitions, comparison/target, strandedness counts, thresholds, background, and STAR settings. | Read length dependent STAR values are marked automatic at creation; `--verbose` exposes sample paths and partition selectors. |

The exact offer depends on supplied arguments and admitted sample structure.
This trace does not establish that a novice understands each scientific choice;
the eventual transcript and walkthrough must test that separately.

### 5. Maintained study selection

**Observed.** [Quickstart](../../quickstart.md) lines 92-110 still passes
`configs/step_07_partitions.primary_contigs.tsv` explicitly. Init supports a
supplied partition manifest or generic regions, validates the selected names,
and copies normalized content (`onboarding.py` lines 685-704 and 1027-1160).
The [INIT-02 backlog row](backlog_matrix.md#novice-setup-and-operational-follow-up)
remains Open for a guided EV/PUM1 study choice that supplies the maintained
selection without a manifest path, including its installed-package supply. Its
completion cannot be assumed from a checkout file or inferred from `viking`, a
Project name, or FASTA headers.

**To settle.** Reconcile INTERACTIVE-01's journey with the separate INIT-02
outcome before proposing an automatic study route. Check the installed package,
the exact 25-name selection, missing contigs, and the existing explicit-manifest
and generic-region routes. Do not add another selector validator.

**Pending sibling implementation.** PR #316's current head
`e1e802177b5333454e93e5e7c4f38d229f33f62a` retains the code from
`bd3f1399305732e76435679e08c504ad6793010b` that adds a yes/no EV/PUM1
whole-sequence offer after the user has assigned exactly those two conditions
and left partition selectors absent. Acceptance reads a packaged 25-name TSV
through the existing partition admission; refusal continues to generic regions,
explicit selectors bypass the offer, and missing nonterminal selectors still
fail. Its Quickstart uses that route and its `INIT-02` row says Verification
pending. The change is absent from this branch and has no completed installed
guided-command or novice Viking evidence. The ordinary
[hosted run](https://github.com/lab-cats/EMRYS/actions/runs/35776280689) passed
on the older code head, including the wheel lane; selected real synthetic E2E
was skipped. That run does not validate the current documentation-only head. The
eventual INTERACTIVE-01 guide must recheck the exact integrated behavior
instead of copying this sibling proposal as a current contract.

### 6. Project preview and publication

**Observed.** Init reviews the interpreted study, then explicit `y`/`yes`
confirms creation. Enter, no, EOF, `--preview`, and nonterminal omission of
`--execute` leave it uncreated; successful creation and declined preview can
both return zero (`onboarding.py` lines 1261-1398). Preview avoids FASTQ
content hashing; creation hashes each FASTQ once, rechecks inputs and reference,
and publishes `project.yaml` last. Scientific and input refusal before
publication creates no Project. Publication reserves an absent output
directory, writes `project.yaml` last, then re-admits the tree; a failure here
retains any partial directory and even a present `project.yaml` may be invalid
([contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)).

**To settle.** A composed guide must receive an explicit owner result for
`created` versus `previewed/declined`; it must not parse `Project ready`, trust
an exit code, or rely on path existence. Keep public exits and text unchanged.
Check refusal, input changes during review, one-pass hashing, partial
publication, and exact created identity (`test_onboarding.py` lines 328-558 and
1011-1044).
Before the guarded publication body, including during reservation setup,
`KeyboardInterrupt` propagates and may still leave a reserved directory. The
`BaseException` guard around member writes and internal tree readmission wraps
an interruption as `OnboardingError` and reports exit 2 with the partial tree
preserved. After that helper returns, Init performs one final unguarded input
recheck; interruption there propagates even though a `project.yaml` may now
exist and `Project ready` has not printed (`onboarding.py` lines 619-651 and
1383-1407). Test all three boundaries; do not promise one interruption exit or
infer completion from path presence.

### 7. Read-only Project validation

**Observed.** `validate_project` returns a Project admission and reference,
annotation, sample, and partition compatibility observations without invoking
external tools (`onboarding.py` lines 1686-1815). It rehashes declared FASTQ
bytes without decoding their records, and checks reference/partitions across
all Analyses (`normalization.py` lines 238-257 and 345-365). Runtime discovery,
Doctor, and direct Run repeat relevant admission at their own boundaries. It is
a read-only input and configuration check, not a cheap metadata lookup, runtime
qualification, or scientific proof.

**To settle.** Validate the exact selected Project and stop if its current
admission fails. The resulting observation neither compares FASTQ bytes with
those at Init nor guarantees they remain unchanged after validation. Reuse this
capability while leaving later owners' fresh admission intact; budget repeated
FASTQ reads and do not add a second validator or present `PASS` as readiness to
submit. Check multiple Analyses, failures, concise/plain output, and no-write
behavior.

### 8. Runtime source and admission

**Observed.** Runtime discovery probes the current declared environment unless
an exact `--from-project` donor is given (`onboarding.py` lines 2268-2356).
Preview and refusal write nothing; confirmation rechecks bindings and publishes
the selected inventory. Current-environment admission creates an absent
`runtime.tsv`; rerunning `--execute` with an existing inventory refuses and
preserves it. Both refusal and admission can return zero. Reusing an
unsealed donor may first publish its `runtime/shared.json`, then the borrowing
Project's `runtime.tsv`; a borrower failure can retain donor seal/claim evidence
([contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries),
lines 313-320). General compatible-donor discovery remains with CV-U22.
Donor reuse refuses the same Project as donor/borrower, an unresolved donor
claim, or a borrower inventory that would be replaced without explicit
`--replace`. Replacement is limited to an existing shared selection from that
same donor (`onboarding.py` lines 2105-2151 and 2231-2251).

**To settle.** Ask for an explicit known donor or use the current-environment
route. Review both Projects' possible writes before confirmation; never promise
atomic rollback, silently replace a selection, or retry over retained partials.
An existing `runtime.tsv` is a candidate, not proof of an admitted or ready
inventory; Doctor loads and inspects it afresh (`doctor.py` lines 576-610).
An absent inventory needs discovery or Doctor preparation. Explicit donor
planning also validates both borrower and donor Projects before preview,
including their input rehashes (`onboarding.py` lines 2105-2108 and 1686-1698).
Keep `--replace` as the owner's explicit same-donor operation.

The present Quickstart skips runtime discovery when there is no smoke-test donor
and proceeds to Doctor, so the guide must settle whether discovery is needed
for each path rather than make it unconditional. Expose an exact
admitted/declined owner result. Existing protection cases include
`test_onboarding.py` lines 2993, 3124, 3190, 3286, and 3338.

**Pending sibling implementation.** PR #320's current head
`1bb133e5fb47d82e84e8bc797c7591dcbbf4d8ae` retains the code from
`62b874785b88d1edf29747bf54241461338d021a` that makes a bare
`--from-project` on a terminal list at most 256 immediate Projects under the
canonical Projects home with runtime inventories. The list is explicitly
unverified; a numbered choice still runs the existing donor admission.
Omitting a choice returns zero without a write. A bare source in a nonterminal
call, or combined with `--execute`/`--replace`, is refused. This proposal is
absent here, and its base predates PR #316's current head. The
[ordinary hosted run](https://github.com/lab-cats/EMRYS/actions/runs/35776414501)
passed on the older code head with selected real synthetic E2E skipped; that
run does not validate the current documentation-only head. Installed donor
selection and site acceptance remain separate. A future guide must recheck the
integrated result; it must not interpret a listed candidate or zero exit as
admitted reuse.

### 9. Doctor readiness and repair

**Observed.** [`doctor.py`](../../src/emrys/orchestration/run_coordinator/doctor.py)
lines 484-738 has a read-only diagnosis with blockers and selected-profile
readiness. A saved Viking site does not admit an implicit direct profile. The
confirmed `--repair` path alone may use established package managers and, for
Slurm placement, qualifies compute runtime/storage then finalizes on the head
node (lines 1537-1785 and 2023-2134). Head readiness alone does not skip that
site qualification. Declined or blocked repair can both return one. Doctor
cannot repair every blocker: an unadmitted installed package, invalid execution
profile, failed Python checks, custom analysis dependencies, and site/user-owned
inventory have their own refusal or remediation (`doctor.py` lines 518-524,
640-670, and 835-925).

**To settle.** Carry the same explicitly selected profile into Doctor and Run.
Keep diagnosis, repair approval, package installation, and qualification with
Doctor; distinguish `already ready`, `declined`, `blocked`, and `qualified` in an
owner result. Preserve one maintenance log and retained partial evidence. Check
read-only diagnosis and refusal (`test_doctor.py` lines 432, 972, 1077, 2575).
The public Doctor adapter returns only an integer; `DoctorResult.ready` cannot
by itself distinguish initial readiness from completed repair or a declined
preview (`doctor.py` lines 2007-2020 and 2089-2134). An owner-private outcome
seam remains to be designed before guide composition. `--execute` without
`--repair` returns 2, as do wrong-node invocations: a Slurm allocation without
the advanced `--compute` selection, or `--compute` without a canonical
allocation (`doctor.py` lines 2027-2040). The guide must not use either path
as a shortcut to readiness.
The guide should stop on an owner-supplied external remediation instead of
repeating `--repair`; Doctor normally runs on the head node. An already ready
direct profile can return without repair, while explicitly requested Slurm
repair may still plan qualification. Run loads the profile afresh, so any
Doctor-to-Run drift must be re-admitted rather than carried as durable readiness.
PR #307 adds a selected synthetic E2E assertion for Doctor timing records; a
retained timing measurement is still separate from a passing hosted run and
from Viking readiness or utilization proof.

### 10. Direct and Slurm Run approval

**Observed.** Interactive direct `run` without `--execute` builds and shows one
frozen plan before its execution confirmation (`control.py` lines 1766-1789).
The automation option skips that pre-execution display and builds inside the
execution path; it cannot stand in for a guide's reviewed-plan approval. For
Slurm, `_finish_control` calls `_schedule` *before* building the Run plan (lines
1755-1765); the head node shows the submitted Analysis name only if
`--analysis` was supplied. Otherwise it says selection will occur from the
Project on the compute node. It also shows the admitted allocation request,
while the immutable Run plan is built on the compute delegate. The retained duplicate-request
check refuses a matching active or unconfirmed request before `sbatch` unless
the operator explicitly supplies the advanced override (lines 1104-1165).

**To settle.** Describe the Slurm screen as a submission/resource preview,
not a frozen Run-plan review. A stronger pre-submission scientific preview would
need its own approved design without claiming head-side compute admission.
Never auto-add the duplicate override, retry, or treat an absent Run as proof
that a queued job is gone. Preserve the direct and Slurm approval boundaries;
see `test_materialization.py` lines 3048, 3158, 4692, 4783, and 5027-5218.
Direct Run's zero exit can include a completed computation with only partial
scientific output or intentionally disabled reporting; the guide must use the
existing admitted result and inspection language for any stronger claim.
Select and review the exact Analysis before approval or explicitly retain the
compute-side selection limit. `_schedule` generates its request token before
the preview; rerunning it after a separate guide preview would make a different
request. Reuse the same admitted owner plan through confirmation, just as the
interactive direct path reuses its frozen plan. The duplicate-risk scan occurs
before the interactive wait; source review found no second scan after that
wait in `_schedule`. Review the commit boundary and adjacent protections before
claiming atomic duplicate prevention. Test one approved action and exact
preview-to-commit identity without a hidden `--execute` bypass.
The guard only stops matching requests whose scheduler state is nonterminal or
unconfirmed (`control.py` lines 1104-1165). A terminal scheduler observation
can permit a new submission even when Run evidence is unresolved
(`test_materialization.py` lines 5069-5103). Passing the guard is not a guided
retry decision: require review of the exact request and any admitted Run and
Attempt, then leave any repeat submission to a separate manual approval.

### 11. Submission and watch handoff

**Observed.** Control writes an exact `submission-<uuid>` request context before
`sbatch`, then prints the request, scheduler ID/name, streams, and a
submission-only statement (`control.py` lines 1172-1225). A numeric
`emrys watch JOB_ID` selects raw scheduler diagnostics and excludes Project/Run
admission (lines 2656-2724 and 3016-3027). The Project inspection owner can
watch an exact retained request using `inspect --project PROJECT --submission
REQUEST --watch`; its later association with a Run is separately re-admitted.
The public submission output currently advertises the numeric watch shortcut,
so the composed guide needs its own request-bound handoff. The submission
selector accepts the exact `submission-<32 hex>` directory name or absolute
path, not a job ID, prefix, or newest-request guess (`slurm_submission.py`
lines 248-261 and 477-545).

**To settle.** Return the exact request identity from the submission owner to
the guide without parsing stdout. Offer watch on that Project request, not a
job-ID-only path presented as verified Run inspection. An interrupted or
unconfirmed submission retains evidence and does not trigger an automatic
second submission. Check request ambiguity, delayed Run creation, and exact
handoff (`test_run_locator.py` and `test_slurm_submission.py`).

### 12. Return, recovery, and completion

**Observed.** Project watch inventories requests and Runs without choosing the
newest (`control.py` lines 226-329 and 3033-3075). A refresh may admit a later
request-to-Run association; failed re-verification clears earlier admission.
Completion and recovery come from admitted Attempt, Results, and reporting
evidence, not a scheduler success line or file presence
([inspection owner](../../src/emrys/orchestration/run_coordinator/README.md)).
The exact request's context and response are rechecked; one token-bound
application log with matching Project, profile, and job identity is only a
candidate until Run and Attempt authority are admitted
(`_submission_inspection.py` lines 320-530). Periodic watch ticks refresh
scheduler/log diagnostics; pressing `r` requests association re-verification
(`_inspection_presentation.py` lines 538-653 and 1170-1194). A noninteractive
watch snapshot can return zero while association is still unknown.

**To settle.** Re-entry should ask for or show exact Project/request/Run choices
and then use existing Inspect/Watch and supported recovery action. Do not add
persistent last-used selection, automatic resume, or auto-reporting. A queued
submission may have no Run yet. Check reconnect, multiple submissions for one
Run, unknown scheduler state, and failed re-verification. Treat a watch exit
code as command completion, never as Run completion or recovery approval.
Several requests can point to one Run, so selecting that Run does not recover
a unique request (`control.py` lines 226-243 and 294-329). Keep the selected
request identity across refreshes. Explicit `inspect --submission REQUEST
--watch --actions` offers a request stop preview, even if a Run is later
associated. The `emrys watch` shorthand can retain an already admitted Run
alongside its selected request and then offer Run resume/report reviews; those
actions re-admit the exact Run (`control.py` lines 2593-2617, 2735-2755, and
3033-3063). The guide must keep the request identity distinct from that Run.
An inspection suggestion to repeat the original Run invocation for a Run with
no started Attempt is not sufficient by itself to resubmit: reconcile the
retained request and scheduler observation first (`control.py` lines 790-808).

### 13. Owner results and maintenance footprint

**Observed.** Setup's dry-run, Init/runtime/direct/Slurm Run's declined
no-write previews, and their successful actions can all return zero
(`onboarding.py` lines
252-257, 1313-1398, 2341-2356; `control.py` lines 1165-1225 and 1769-1789).
The CLI already owns dispatch, Init owns scientific admission/publication,
Doctor owns repair, and Control owns Run/submission. Their yes/no prompts make
different trust decisions; similar text alone does not justify one policy owner.

The public outcomes that composition must distinguish are:

| Owner path | No-write or stopped result | Approved action and remaining limit |
| --- | --- | --- |
| Setup | Omitting `--execute` previews and returns 0; a missing answer or existing `.env` returns 2. | `--execute` publishes absent `.env` and returns 0; Setup itself has no final yes/no prompt. |
| Init | `--preview`, no/blank/EOF at final confirmation, or nonterminal omission of `--execute` returns 0 without creation; missing interactive answers or EOF during a required question returns 2. | `y`/`yes` or `--execute` hashes and validates inputs before create-absent publication, returning 0 only on success. |
| Runtime discovery | Not-ready returns 1 before approval; ready but no/blank/EOF or nonterminal omission returns 0 without admission. | `y`/`yes` or `--execute` calls the existing admission plan; success also returns 0, and donor partials must be retained if later admission fails. |
| Doctor | Read-only diagnosis returns 0 when ready and 1 when not ready. With `--repair`, blocked or declined preview returns 1; interrupted repair returns 130. | Confirmed head-side repair can return 0 after final readiness; an already ready direct profile can return 0 without a repair prompt. Private delegated compute success also returns 0 but still needs head finalization. |
| Direct Run | No/blank/EOF or nonterminal omission of `--execute` previews a frozen plan and returns 0 without executing. | Confirmation executes that plan; `--execute` bypasses its pre-execution display, and a zero result has the existing limited Run/report meaning. |
| Slurm Run | No/blank/EOF or nonterminal omission of `--execute` previews a submission request and returns 0 without submission; the duplicate guard can stop with 2. | Confirmation or `--execute` retains a request before `sbatch`; zero means accepted submission, not Run creation or completion. |
| Watch or Inspect selection | Menu cancellation, EOF, or interruption returns 0; ambiguous nonterminal selection returns 2. An exact submission roster or noninteractive watch snapshot can also return 0 with no admitted Run association. | Exact Project/request/Run selection permits inspection; watch command completion still does not prove Run completion. |

If sibling PR #320 is integrated, its donor picker adds another zero-result
no-write path when no candidate is selected. It must remain distinct from an
admitted runtime outcome.

**To settle.** Evaluate private structured outcomes at each real owner boundary
while keeping the public integer adapter and output contract. Compare exact
input, EOF, stream, and exit semantics before consolidating prompt mechanics.
Inventory duplicate code, callers, compatibility, tests, docs, scripts,
configuration, and mutable state; record product lines/files separately from
tests, docs, and evidence. Existing `argparse`, `sys.stdin`, `pathlib`, Rich,
and the installed terminal-menu dependency appear sufficient. Do not add a
second validator, scheduler reader, wizard store, shell wrapper, or dependency
without a demonstrated gap. The [architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails)
default to meaningful net product-code reduction and no product-file growth;
any measured exception needs separate approval.

The pinned source footprint makes the possible implementation surface concrete.
These are candidate touchpoints, not a proposal to modify every file:

| Category | Pinned #304 baseline | Audit implication |
| --- | ---: | --- |
| Direct CLI and guide owners | 4 product files; 8,031 physical lines | `__main__.py`, onboarding, Doctor, and Control need a caller-complete design before any shared helper is added. |
| Adjacent admission and monitoring | 3 product files; 2,463 lines | Inspection, submission inspection, and Slurm submission remain separate owners to check for duplicate reads or policy. |
| Installed launcher | 1 product file; 206 lines | Preserve the controlled console entry when the public default behavior changes. |
| Direct protection candidates | 8 test files; 21,371 lines | Extend meaningful existing cases; line count does not justify dropping independent defenses. |
| Nearby owner and operator docs | 8 files; 7,248 lines | Reconcile Quickstart, owner contracts, operations, and backlog status without a second acceptance registry. |
| Config, packaging, and schema candidates | 10 files; 4,658 lines | Includes the maintained manifest, example Viking profile, and package declaration; no required edit or safe retirement is established. |
| Repository scripts | 6 files; 1,276 lines | No guide-specific script or retirement has been established. |

Within those owners, onboarding's `_prompt` has ten static call sites across
Setup/Init, `_prompt_choice` has four within Init, and `_confirm_admission` has
two across Init/runtime. Doctor's `_confirm_repair` has one; Control's
`_confirm_execution` has three across submission, prepared resume, and direct
Run/Resume. Control's existing terminal selection helper has two Run/watch
call sites. Onboarding already shares its same-owner confirmation, and Control
already shares execution confirmation. Doctor and Control print approval to
stdout while onboarding prints to stderr; their approvals also authorize
different mutations. A new common prompt policy has no demonstrated
caller-complete net reduction.

The smallest candidate handoffs remain owner-specific. CLI startup already
receives the exact marked `.env` path or `None`; retain that result and the
effective values after process precedence. Setup needs a private
published-versus-preview result with its selected values for same-invocation
use; Init needs the created `project.yaml` path or no-write result. Reuse
existing `ProjectValidation` and `validate_project` for the current read-only
observation, and the runtime discovery plan's `inspection`/`admit` result for
the admitted profile. Doctor's private path must distinguish initial readiness,
declined or blocked repair, delegated compute qualification, and completed
head-side finalization; `DoctorResult.ready` and public exit alone do not encode
that history. Control's `_schedule` has the exact retained `request_root` and
`job_id` in local scope but returns only an integer; those values are the
minimum submission-to-watch handoff. These are interface proposals requiring
exact caller review before implementation, not new generic result types or
persistent wizard state. No tracked fixture or retained evidence has been shown
safe to delete.

The compression inventory is deliberately conservative:

| Surface | Candidate or current limit |
| --- | --- |
| Product code | Reuse owner plans/admission and compare the three terminal yes/no mechanics for exact parity before consolidating; no deletion is proven yet. |
| Tests and protections | Extend current owner and public CLI cases for guide composition; do not retire independent input-change, refusal, request, or recovery defenses. No redundant test is established. |
| Scripts | Keep bootstrap installation instructions outside the installed CLI. A new shell launcher has no demonstrated need; no existing script retirement is established. |
| Schemas and configuration | Reuse `.env`, Project, runtime, and request contracts. No wizard schema or saved scientific selector is indicated; no existing field is established as dead. |
| Documentation | Replace novice copy-and-run sequencing in Quickstart only after the guide works; keep exact manual commands and recovery with their owners. |
| Mutable state and evidence | Hold only exact in-invocation selections; add no persistent last-Project or wizard checkpoint. Retain `.env`, Project/runtime records, requests, locks, logs, and partials. |

### 14. Presentation, documentation, and proof

**Observed.** The [Quickstart](../../quickstart.md) lines 54-205 still directs
separate Setup, Init, Validate, optional runtime reuse, Doctor, Run, Watch, and
Inspect commands. The [Runbook](../operations/RUNBOOK.md) owns advanced
commands; [Troubleshooting](../operations/TROUBLESHOOTING.md) owns recovery.
Current terminal output must remain understandable without color, in redirected
output, and in a dumb terminal. Source review does not prove an installed or
novice Viking journey.

Terminal gates differ: Setup/Init, Doctor confirmation, and Run confirmation
require stdin and stderr terminals (`onboarding.py` lines 960-961,
`doctor.py` lines 1480-1484, `control.py` lines 1046-1050). Interactive watch
requires stdin and stdout terminals with `TERM` other than `dumb`; otherwise
it renders one snapshot and can return zero (`_inspection_presentation.py`
lines 1117-1153). Watch `--actions` requires all three streams to be terminals
and a non-dumb `TERM` (lines 1062-1066). The guide must specify and test which
route applies under stdout or stderr redirection and avoid treating a snapshot
as continued monitoring. If watch first has to choose among multiple requests
or Runs, that picker separately requires stdin and stderr terminals; redirected
stderr can refuse selection before the watch display is reached (`control.py`
lines 177-193 and 294-329). Passing the exact request selector avoids that
ambiguity for the guided handoff. Doctor and Control write approval questions
to stdout despite using stdin/stderr for eligibility; with redirected stdout,
an approval may still read a response while its question is hidden in the
redirected stream. The proposed guide must make the question visible at its
actual approval boundary (`doctor.py` lines 1480-1484; `control.py` lines
1046-1053).

**To settle.** Once a selected guide works, make Quickstart one linear head-node
journey and retain manual procedures with their owners. Use tiny local fixtures
for TTY/PTY, refusal and EOF at every approval boundary, source-bound and
installed CLI entry, `NO_COLOR`, `TERM=dumb`, redirected input/output,
nonterminal behavior, changed inputs, exact runtime/profile selection, duplicate
submission, and request-based watch.
Cover the controlled console launcher and isolated `-m emrys` entry, clean and
malformed `.env`, bare and named commands, exact owner exits, and no writes on
refusal in their existing test owners rather than adding a second harness.
Include a terminal-scheduler request with unresolved Run evidence, menu
cancellation versus ambiguous nonterminal selection, request stop preview
versus separately admitted Run recovery, and request-to-Run re-verification.
Run applicable hosted checks on the exact implementation commit. A fresh
novice Viking walkthrough and site observations remain separate; no biological
interpretation follows from software or scheduler success.

**Current local test limit.** No `emrys` executable or installed distribution was
found in the available worktree and Python environments. A source-bound
`--help`, `--version`, or bare invocation exits during import because
`jsonschema` is absent, before argument parsing or interaction. This does not
verify those three public behaviors. No dependency was installed for the audit.
The selected PR #307 synthetic E2E timing assertion supports a hosted claim
only with a passing run on the exact head named in that claim; an earlier run
cannot validate later documentation-only commits.

## Proposed Viking/PUM1 journey

This is a candidate interaction sequence for the study in the
[Quickstart](../../quickstart.md), not accepted prompt wording or a new command
contract. The bare-terminal entry and named-command manual route are accepted;
the sibling features and guide-only exit details are implementation-time
decisions. The explicit manifest and known-donor routes are the current
baseline. Each answer with scientific meaning must be supplied or explicitly
reviewed by the operator.

| Checkpoint | Proposed visible decision | Owner boundary and stop condition |
| --- | --- | --- |
| Installed start | Follow the Quickstart's one head-node install path, then enter guidance from the checkout. | The CLI cannot perform its own uv/Pixi installation before it exists. A failed install stops before the guide. |
| Entry | Bare `emrys` on a terminal starts the guide; named commands remain manual. Show what Project and settings are in scope. | This entry is owner-approved. Preserve malformed-settings refusal before parsing, other CLI behavior, and the current nonterminal no-write error unless separately approved. |
| Saved settings | Show the Projects home, `viking` site, optional log root, value precedence, and any loaded settings file; ask before one create-absent `.env` publication only for first setup. | Setup owns the file. A returning user skips create-absent Setup; a dry-run/decline does not continue as a saved setting. Same-invocation values are carried explicitly. |
| Project context | Choose new or an exact existing `project.yaml`; show the canonical path. | No latest/parent/global lookup, adoption of a partial tree, or implicit Project switch. |
| New study | Ask for reference FASTA/GTF and the FASTQ directory; review six candidate sample IDs, the Quickstart's EV/PUM1 assignments, study-wide `reverse`, and `EV -> PUM1`. | Init owns pairing and scientific admission. The detected list precedes mate validation; a missing or incompatible input stops before Project publication. |
| Scope and thresholds | Review the maintained `1`–`22`, `X`, `Y`, `MT` selection only after an explicit study choice if INIT-02 is integrated; otherwise retain the exact manifest route. Ask for `A>G` and review the five disclosed paired-CMH values and inactive background. | A site or Project name cannot choose scientific scope. `--preview`, refusal, or input EOF must retain their distinct no-write/error outcomes. |
| Project creation | Show the complete Init preview, then ask once to create and explain FASTQ hashing time. | Init owns absent publication and completion re-admission. A declined preview is not creation; a failed partial tree requires inspection, not automatic retry. |
| Validation | Show the selected Project and a read-only compatibility check, including repeated FASTQ reads. | Validate owns a current observation. Failure stops; later owners re-admit rather than trust an earlier PASS. |
| Runtime source | If an inventory exists, show it as a candidate for fresh admission; otherwise explain the current-environment, explicit donor, or Doctor-managed path. Review donor and borrower writes when reuse is chosen. | Runtime and Doctor own admission; a listed donor or existing file is unverified, skip is no write, and retained partials or selections are never silently replaced. |
| Doctor | Show the exact Analysis/profile and diagnosis; only offer Doctor-owned repair when it has a plan. | External remediation, refused repair, or incomplete Slurm qualification stops before Run. The same profile is rechecked at Run. |
| Launch | Review the exact Analysis and direct frozen plan or Slurm submission/resource request; ask once. | Control owns duplicate-risk review and submission. Slurm approval returns an exact request and job, not a created or completed Run. |
| Watch and return | Offer request-bound Project watch, show how to recheck, then show the exact Project/request for the operator to retain for later inspection. | Inspection owns later association, completion, and supported recovery. Leaving watch, a terminal scheduler state, or a missing Run never authorizes another submission. |

### Transcript evidence boundary

The current owner prompts support only part of a continuous guided transcript.
The table quotes labels rather than inventing the guide's connective questions;
unknown absolute input paths, Doctor plan operation, and request/job IDs remain
operator- or runtime-supplied.

| Segment | Current prompt or output at pinned #304 | Still proposed or conditional |
| --- | --- | --- |
| Setup | `Projects home`, `site`, `log root (optional)`, `Saved CLI defaults`, `CLI defaults ready` (`onboarding.py` lines 214-257). | The guide must add one reviewed save decision without calling Setup twice, then carry values within the invocation. Returning users need no second create-absent Setup. |
| Project choice | Named Init requires `PROJECT_NAME`; Project-aware commands accept an exact selector (`onboarding.py` lines 270-295 and 729-759). | New/existing choice and `pum1-study` name entry are guide connective text, not current bare-CLI behavior. |
| Reference and samples | `reference fasta`, `reference gtf`, `FASTQ directory`, `Detected FASTQ pairs` (candidate IDs), `study strandedness`, then each missing `condition for SAMPLE` and `pairing group for SAMPLE` (`onboarding.py` lines 812-893, 939-961, and 981-1025). | The Quickstart supplies six EV/PUM1 assignments and study-wide `reverse`; actual input paths are not supplied by EMRYS. Sample questions follow sorted IDs, which differs from the Quickstart table order. The detected list does not yet prove mate pairing. |
| Scope | The pinned path accepts the explicit checkout manifest or asks for generic regions (`onboarding.py` lines 1027-1073 and 1100-1156). | PR #316's maintained 25-name offer is not in this branch; a continuous guide must use the explicit manifest route until it is integrated and rechecked. |
| Comparison and thresholds | Two compatible conditions offer numbered `EV -> PUM1`/`PUM1 -> EV`, then `comparison [1 / 2]`, `target change`, and `Use these paired-CMH defaults?` (`onboarding.py` lines 838-893 and 1074-1095). | The Quickstart supplies `A>G` and the disclosed `1`, `50`, `0.05`, `1.2`, `0.005`; no background cohort is selected. The guide must display, not infer, that scientific intent. |
| Publication and validation | Complete preview, `Create this Project? [y/N]`, hashing warning, `Project ready`, then a separate validation PASS (`onboarding.py` lines 1163-1258 and 1313-1398). | Guide continuation requires the exact created outcome; neither exit 0 nor path presence suffices. |
| Runtime and Doctor | A chosen donor can show `Runtime discovery: READY` and `Admit this runtime inventory? [y/N]`; Doctor asks `Apply this {operation} plan? [y/N]` when repair is available (`onboarding.py` lines 2304-2356; `doctor.py` lines 1480-1484). | Donor use is optional; PR #320's picker is not in this branch. Donor preview can rehash two Projects. The plan operation and readiness depend on fresh diagnosis. |
| Launch and return | Control asks `Execute this plan? [y/N]`, then prints the exact submission request and job; completion is unverified (`control.py` lines 1046-1050 and 1165-1225). | A `Watch now?` question is guide-only proposed text. Request-bound inspection exists, but later Run association and completion must be independently admitted. |

### Proposed guide-only connective questions

The quoted questions below are **proposed**, not current public CLI text or
approved scientific choices. The proposed save question supplies the approval
that Setup's `--execute` flag currently represents; Init, runtime, Doctor, and
Control keep their own single mutation approvals. The guide must decide its
own cancellation exit contract without changing any named command's exit or
output.

| When | Proposed question | Route and evidence limit |
| --- | --- | --- |
| After saved-settings admission | `Start a new Project, open an existing Project, or leave?` | No default or latest-Project choice. Existing Project selection skips create-absent Setup; a regular marked `.env` is loaded once with process precedence. Leave/EOF stops without mutation; its new public exit remains to decide. |
| New Project from the checkout without saved settings | `Save these defaults in <checkout>/.env? [y/N]` after Setup's current values and preview | `y` commits the same reviewed Setup plan once through its owner, without calling the public question path again, then carries effective values in this invocation. No/blank/EOF stops this proposed first-setup route without a write; an existing `.env` is never overwritten. |
| New Project outside a checkout without saved settings | Show the required checkout and exact Projects-home context | Setup currently requires a checkout. Stop with an instruction or design an explicit unsaved route before implementation; never search for a repository or home by recency. |
| Project identity | `Project name:` for new, or `Existing Project path:` for existing | New shows the canonical absent destination before Init. Existing requires an exact directory or `project.yaml` selector; refusal, EOF, alias, missing, or partial Project stops or returns to explicit choice without selecting another. |
| Optional known donor | `Reuse tools from a known Project? [y/N]` | Yes asks for one exact donor and reviews donor and borrower writes before the runtime owner's confirmation. No proceeds to Doctor's diagnosis. A subsequent owner refusal/EOF stops without admission or automatic Doctor fallback; listed candidates and existing files are not readiness proof. |
| After confirmed Slurm submission | `Watch this submission now? [y/N]` | Yes hands the exact Project and retained `submission-<32 hex>` request to request-bound inspection. No/blank/EOF prints those identities and `emrys inspect --project PROJECT --submission REQUEST --watch`; neither branch implies a Run exists. |
| Later return through an existing Project | `Inspect a retained submission request? [y/N]` | Yes requires an exact request selector and re-admits its current association. No/blank/EOF stops or returns to explicit choice without automatic submission. Leaving watch or seeing a terminal scheduler state never authorizes another submission. |

## Proposed design and delivery order

The entry choice above is accepted. The remaining steps are review proposals;
implementation must satisfy the owner and measured-footprint gates below.

1. Use the approved bare-terminal entry and named-command manual route.
   Preserve the existing nonterminal no-write usage error unless separately
   approved; settle guide cancellation exits and the full prompt transcript.
   Resolve the `INIT-02` dependency.
2. Map each existing public handler's no-write, success, blocked, and partial
   outcomes. Select the smallest private result interface that preserves public
   exits and text. Measure the affected product footprint before adding code.
3. Compose Setup and exact Project selection, then Init and Validate. Carry
   admitted settings explicitly within the invocation; do not reload into
   global state or infer a Project.
4. Compose exact runtime admission and Doctor diagnosis/confirmed maintenance.
   Review any donor and borrower writes and preserve all partial evidence.
5. Compose direct Run planning or Slurm submission preview with their existing
   confirmations and duplicate guard. Hand off the exact retained request to
   Project inspection; never label submission as completion.
6. Replace novice copy/paste sequencing only after the complete path works.
   Keep manual commands, owner contracts, and recovery instructions accurate.
   Verify with focused local checks, applicable hosted CI, and separately
   authorized institutional novice acceptance.

The first candidate owner slice is an exact Init publication outcome. A
provisional private operation in `onboarding.py` would return `Path | None`:

| Existing Init branch | Proposed private result | Preserved public result |
| --- | --- | --- |
| `--preview`, or final no/blank/EOF/nonterminal confirmation | `None` after the existing no-write message | Exit 0; no Project created. |
| Confirmed `y`/`yes` or `--execute` | Canonical `project.yaml` path only after create-absent publication and final input recheck | Exit 0 and the same `Project ready` output. |
| `OSError`, `OnboardingError`, `ValidationError`, `orchestration_contracts.ContractValidationError`, or `step08.ContractError` | Propagate to a thin public adapter | Same error message and exit 2. |
| `KeyboardInterrupt` before guarded member writes, including reservation setup | Propagate without a new catch | Same interruption behavior; a partially reserved directory may remain. |
| `KeyboardInterrupt` during guarded member writes or internal tree readmission | Existing publication guard wraps it as `OnboardingError`; preserve the partial tree | Same error message and exit 2; completion member presence is not proof. |
| `KeyboardInterrupt` during final input recheck after publication | Propagate without a new catch | Same interruption behavior; `project.yaml` may exist without a `Project ready` result. |

The public `init_project_from_args` would remain the integer adapter. Preserve
its questions and streams, `--preview`/`--execute` exclusivity, one-pass FASTQ
hashing, scientific admission, and create-absent transaction. The bounded code
owner is `onboarding.py` lines 1261-1407 and its export list; focused existing
onboarding tests and the coordinator contract would change with it. The CLI
dispatcher, Doctor, Control, schemas, scripts, fixtures, and retained evidence
have no established change for this slice. Tests must distinguish preview,
final refusal/EOF, required-answer EOF, nonterminal mode, confirmed creation,
input drift, hashing, interruption before, during, and after publication,
retained partials, and public exit/output parity.

A source-only structural estimate is about seven added product lines and zero
new product files; moving the current body into a private operation would make
the textual diff much larger than that net estimate. No caller-complete product
deletion has been identified to offset it. This is not a measured patch or an
approved growth exception. Quantify the actual delta before implementation;
any net-growth exception needs separate explicit approval. Neither tests nor
retained-evidence deletion offsets product growth.

Stop and return for a decision if the design changes bare-command behavior
beyond the approved terminal entry, needs a new public command/flag, an
unapproved scientific default, new persistent state/schema/dependency,
cross-owner policy, changed mutation or recovery authority, evidence deletion,
or a quantified product-code/file-growth exception. Implementation uses one
authorized worktree and branch based on a rechecked target head.

## Implementation-time evidence and decisions

These choices and checks belong to implementation; they do not block this
discovery draft. On the selected implementation head, refresh the findings if
sibling PRs have been integrated and recheck the literal prompt and exit
sequence in an installed environment. Review the proposed connective
questions, including first-setup refusal, outside-checkout entry, and guide
cancellation exits, when fixing the full novice transcript. The bounded Init
outcome slice above remains a proposal: measure its actual product-code delta
before seeking any growth exception or implementing it. Keep INTERACTIVE-01
status and acceptance in the main backlog.
