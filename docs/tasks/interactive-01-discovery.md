# INTERACTIVE-01 guided operation discovery

This working record supports [INTERACTIVE-01](backlog_matrix.md#deferred-operational-work).
The main backlog alone owns its status, priority, outcome, and acceptance. Finding
numbers below are navigation, not new backlog items or implementation approval.
The [CV-U19 record](cluster_verification_backlog.md#cv-u19-long-term-interactive-cli)
preserves the operator's eventual direction: guided setup and analysis launch by
default, with an optional manual route. It does not select a prompt sequence,
transition, or `--advanced` spelling.

## Review basis and evidence limit

The source review is pinned to [PR #304](https://github.com/lab-cats/EMRYS/pull/304)
head `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`. PR #303 is a sibling,
not part of that head. The checkout used for this document started clean at the
named commit. [PR #307](https://github.com/lab-cats/EMRYS/pull/307) head
`f32260f0408fe1826af401fc1ddce0f2478ae6ce` descends from that commit;
its two-file delta adds selected Doctor timing checks to the synthetic E2E
runner and updates the CV-26 record. It changes no product owner, Quickstart,
or INTERACTIVE-01 text cited below. [PR #316](https://github.com/lab-cats/EMRYS/pull/316)
is a separate open sibling implementing part of INIT-02; its changes are also
compared, not included in this documentation branch. Source, owner contracts,
tests, and guides were inspected; no product test, installed-command trial,
PTY walkthrough, dependency
installation, or Viking execution has been completed. The line references below
are to the pinned source revision and must be rechecked if the target changes.

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
| [1](#1-public-entry-and-manual-route) | Public entry | Bare `emrys` currently requires a command. Explicit owner commands already provide manual control. | Select the guided entry, default transition, manual route, and nonterminal behavior. |
| [2](#2-bootstrap-and-saved-settings) | Setup | Setup is checkout-bound, defaults to a dry-run, and creates one `.env` only with `--execute`; the CLI loads saved settings once before dispatch. | Decide same-invocation approval and exact propagation of newly saved values. |
| [3](#3-project-context) | Project | Named Init uses the selected Projects home or current directory; Project-aware commands use an exact Project path. | Define new versus existing selection without newest-Project or partial-root inference. |
| [4](#4-scientific-input-questions) | Scientific intent | Init already asks for reference, FASTQs, assignments, comparison, regions, target, and disclosed defaults. | Reuse its questions; review a complete prompt transcript and refusal paths. |
| [5](#5-maintained-study-selection) | Study selection | This branch still needs an explicit EV/PUM1 manifest; sibling PR #316 proposes an explicit packaged selection. | Reconcile that pending implementation and verify installed-package and novice behavior. |
| [6](#6-project-preview-and-publication) | Init approval | Init confirms after review and preserves create-absent and input-change checks. Decline and creation can both return zero. | Expose an owner outcome without parsing text or treating file presence as proof. |
| [7](#7-read-only-project-validation) | Validation | Existing validation re-admits Project inputs and scientific compatibility without writing. | Pass the exact selected Project; stop on failure without promoting it to runtime proof. |
| [8](#8-runtime-source-and-admission) | Runtime | Discovery uses an explicit donor or current environment, previews probes, then confirms and rechecks admission. Donor reuse can write in two Projects. | Keep source choice explicit, report both mutation paths, and preserve partial evidence. |
| [9](#9-doctor-readiness-and-repair) | Doctor | Diagnosis is read-only; confirmed maintenance and Slurm qualification remain Doctor-owned. | Distinguish ready, declined, blocked, and repaired outcomes; carry one exact profile. |
| [10](#10-direct-and-slurm-run-approval) | Run | Direct execution confirms a frozen Run plan. Slurm confirms a submission/resource request; its Run plan is built later on compute. | Specify truthful review language and retain duplicate-request refusal. |
| [11](#11-submission-and-watch-handoff) | Monitoring | Submission retains a request before `sbatch`. Numeric `watch JOB_ID` is scheduler-only diagnostic selection. | Hand off the exact Project request, then re-admit any later Run association. |
| [12](#12-return-recovery-and-completion) | Return | Inspection owns completion and recovery from admitted evidence, including ambiguous requests. | Define re-entry without persistent wizard state or automatic resubmission. |
| [13](#13-owner-results-and-maintenance-footprint) | Composition | Several public handlers return zero for both no-write preview and success; owners already implement admission, repair, and scheduling. | Audit private outcomes and caller-complete consolidation; quantify any product-growth exception. |
| [14](#14-presentation-documentation-and-proof) | Acceptance | The Quickstart still chains separate commands; terminal and evidence levels have distinct contracts. | Draft novice wording, terminal cases, hosted checks, and separate Viking acceptance. |

## First-pass discoveries

### 1. Public entry and manual route

**Observed.** [`__main__.py`](../../src/emrys/__main__.py) lines 224-241 and
349-384 registers owner commands and errors if `COMMAND` is absent. `--help`,
`--version`, and explicit commands already have public behavior. The installed
CLI is the interaction owner and carries no scientific semantics
([architecture](../architecture/ARCHITECTURE.md#responsibility-boundaries)).
The `emrys` console script enters the controlled Python launcher declared in
[`pyproject.toml`](../../pyproject.toml), which restarts `-m emrys` before owner
imports (`source_authority.py` lines 146-153). That launch isolation is an
adjacent contract to preserve, not a second guide entry to introduce.

**To settle.** A candidate is bare `emrys` on a TTY for guidance, retaining
explicit subcommands as the manual route. An explicit guide command or an
`--advanced` flag would change the public surface differently. Check TTY and
non-TTY invocation, help/version, unknown flags, exits, and installed-command
parity before selecting a transition. No spelling is approved here.

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

### 3. Project context

**Observed.** Named Init selects `EMRYS_PROJECTS_ROOT` or the current directory
and requires an absent child of a canonical writable parent (`onboarding.py`
lines 464-492 and 1261-1269). `project_definition_path` accepts a current
Project or one exact directory/YAML selector and rejects path aliases (lines
270-295). The existing Run selector never chooses the latest Run
([coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#public-model-and-admission)).

**To settle.** Specify a new/existing choice and retain the selected absolute
Project path across validation, Doctor, Run, and inspection. A fresh Setup starts
inside the checkout; returning use from elsewhere needs an exact Project path.
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

**Pending sibling implementation.** PR #316 head
`0e4c42245c65b1b60c2295747e8b2b39abbca33f` adds a yes/no EV/PUM1
whole-sequence offer after the user has assigned exactly those two conditions
and left partition selectors absent. Acceptance reads a packaged 25-name TSV
through the existing partition admission; refusal continues to generic regions,
explicit selectors bypass the offer, and missing nonterminal selectors still
fail. Its Quickstart uses that route and its `INIT-02` row says Verification
pending. The change is absent from this branch and has no completed installed
package or novice Viking evidence. The eventual INTERACTIVE-01 guide must
recheck the exact integrated behavior instead of copying this sibling proposal
as a current contract.

### 6. Project preview and publication

**Observed.** Init reviews the interpreted study, then explicit `y`/`yes`
confirms creation. Enter, no, EOF, `--preview`, and nonterminal omission of
`--execute` leave it uncreated; successful creation and declined preview can
both return zero (`onboarding.py` lines 1261-1398). Preview avoids FASTQ
content hashing; creation hashes each FASTQ once, rechecks inputs and reference,
and publishes `project.yaml` last. Failure preserves partial state
([contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)).

**To settle.** A composed guide must receive an explicit owner result for
`created` versus `previewed/declined`; it must not parse `Project ready`, trust
an exit code, or rely on path existence. Keep public exits and text unchanged.
Check refusal, input changes during review, one-pass hashing, partial
publication, and exact created identity (`test_onboarding.py` lines 328-558 and
1011-1044).

### 7. Read-only Project validation

**Observed.** `validate_project` returns a Project admission and reference,
annotation, sample, and partition compatibility observations without invoking
external tools (`onboarding.py` lines 1686-1815). It is a read-only input and
configuration check, not runtime qualification or scientific proof.

**To settle.** Validate the exact selected Project and stop the journey on an
invalid or changed input. Reuse its admission; do not create a second validator
or present `PASS` as readiness to submit. Check multiple Analyses, failures,
concise/plain output, and no-write behavior.

### 8. Runtime source and admission

**Observed.** Runtime discovery probes the current declared environment unless
an exact `--from-project` donor is given (`onboarding.py` lines 2268-2356).
Preview and refusal write nothing; confirmation rechecks bindings and publishes
the selected inventory. Both refusal and admission can return zero. Reusing an
unsealed donor may first publish its `runtime/shared.json`, then the borrowing
Project's `runtime.tsv`; a borrower failure can retain donor seal/claim evidence
([contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries),
lines 313-320). General compatible-donor discovery remains with CV-U22.

**To settle.** Ask for an explicit known donor or use the current-environment
route. Review both Projects' possible writes before confirmation; never promise
atomic rollback, silently replace a selection, or retry over retained partials.
Expose an exact admitted/declined owner result. Existing protection cases include
`test_onboarding.py` lines 2993, 3124, 3190, 3286, and 3338.

### 9. Doctor readiness and repair

**Observed.** [`doctor.py`](../../src/emrys/orchestration/run_coordinator/doctor.py)
lines 484-738 has a read-only diagnosis with blockers and selected-profile
readiness. A saved Viking site does not admit an implicit direct profile. The
confirmed `--repair` path alone may use established package managers and, for
Slurm placement, qualifies compute runtime/storage then finalizes on the head
node (lines 1537-1785 and 2023-2134). Head readiness alone does not skip that
site qualification. Declined or blocked repair can both return one.

**To settle.** Carry the same explicitly selected profile into Doctor and Run.
Keep diagnosis, repair approval, package installation, and qualification with
Doctor; distinguish `already ready`, `declined`, `blocked`, and `qualified` in an
owner result. Preserve one maintenance log and retained partial evidence. Check
read-only diagnosis and refusal (`test_doctor.py` lines 432, 972, 1077, 2575).
PR #307 adds a selected synthetic E2E assertion for Doctor timing records; a
retained timing measurement is still separate from a passing hosted run and
from Viking readiness or utilization proof.

### 10. Direct and Slurm Run approval

**Observed.** Interactive direct `run` without `--execute` builds and shows one
frozen plan before its execution confirmation (`control.py` lines 1766-1789).
The automation option skips that pre-execution display and builds inside the
execution path; it cannot stand in for a guide's reviewed-plan approval. For
Slurm, `_finish_control` calls
`_schedule` *before* building the Run plan (lines 1755-1765); the head node
shows the Analysis label and admitted allocation request, while the immutable
Run plan is built on the compute delegate. The retained duplicate-request
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
| Doctor | Read-only diagnosis returns 0 when ready and 1 when not ready. With `--repair`, blocked or declined preview returns 1; interrupted repair returns 130. | Confirmed repair or `--execute` can return 0 after final readiness; an already ready direct profile can return 0 without any repair prompt, while Slurm qualification still has its site path. |
| Direct Run | No/blank/EOF or nonterminal omission of `--execute` previews a frozen plan and returns 0 without executing. | Confirmation executes that plan; `--execute` bypasses its pre-execution display, and a zero result has the existing limited Run/report meaning. |
| Slurm Run | No/blank/EOF or nonterminal omission of `--execute` previews a submission request and returns 0 without submission; the duplicate guard can stop with 2. | Confirmation or `--execute` retains a request before `sbatch`; zero means accepted submission, not Run creation or completion. |

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

The smallest candidate outcome interfaces are owner-specific. Reuse
`ProjectValidation`, `validate_project`, the runtime discovery plan's
`inspection`/`admit` result, and `DoctorResult.ready`. Setup and Init need an
unambiguous private publication outcome because their public integer result
also covers a no-write preview. Runtime needs its admitted selection, and
Control needs the exact retained request and job identity from `_schedule` for
the Project inspection handoff. Doctor may be able to compose its existing
readiness result without another generic outcome type. This is an interface
proposal requiring an exact caller review before implementation. No tracked
fixture or retained evidence has been shown safe to delete.

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

**To settle.** Once a selected guide works, make Quickstart one linear head-node
journey and retain manual procedures with their owners. Use tiny local fixtures
for TTY/PTY, refusal and EOF at every approval boundary, source-bound and
installed CLI entry, `NO_COLOR`, nonterminal behavior, changed inputs, exact
runtime/profile selection, duplicate submission, and request-based watch.
Run applicable hosted checks on the exact implementation commit. A fresh
novice Viking walkthrough and site observations remain separate; no biological
interpretation follows from software or scheduler success.

**Current local test limit.** No `emrys` executable or installed distribution was
found in the available worktree and Python environments. A source-bound
`--help`, `--version`, or bare invocation exits during import because
`jsonschema` is absent, before argument parsing or interaction. This does not
verify those three public behaviors. No dependency was installed for the audit.
The selected PR #307 synthetic E2E timing assertion also needs a passing run
on its exact commit before it supports even that hosted claim.

## Proposed design and delivery order

These are review proposals, not accepted interface decisions or authority to
edit product code.

1. Set the installed starting point, guided entry, manual route, nonterminal
   behavior, and full prompt/exit transcript. Resolve the `INIT-02` dependency.
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

Stop and return for a decision if the design needs a new public command/flag,
unapproved scientific default, new persistent state/schema/dependency,
cross-owner policy, changed mutation or recovery authority, evidence deletion,
or a quantified product-code/file-growth exception. Implementation uses one
authorized worktree and branch based on a rechecked target head.

## Next discovery pass

The matrix now includes source behavior, sibling PR deltas, and a measured
candidate footprint. The next iteration should pin the then-current target,
resolve the INIT-02 sibling's disposition, and record exact public
prompt/exit behavior in an installed environment when one is available. Then
draft the full novice transcript and a bounded implementation slice with
quantified product-code change. Keep INTERACTIVE-01 status and acceptance in
the main backlog.
