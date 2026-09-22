# DOCS-01 repository-wide working audit

This is a temporary investigation record for [DOCS-01](backlog_matrix.md). It
records observations and questions, not accepted changes, task status, or new
completion criteria. The backlog matrix remains the authority for DOCS-01;
the [cluster verification backlog](cluster_verification_backlog.md) remains the
authority for its delegated CV cards. A proposed destination below is not
permission to change or delete the source.

## Baseline, scope, and evidence

- Initial read-only pass (2026-09-22) audited source
  `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`, the
  `codex/pr302-original-intent-corrections` revision immediately after PR
  #302's `42d02c5a` head. Branch names are provenance for this working audit,
  not a claim about the current checkout. Recheck live Git and affected text
  before selecting a correction.
- Target scope: documentation across the whole tracked repository, including root guides, operations,
  decisions, architecture, tasks, history, owner READMEs and contracts, tests,
  configuration, scripts, and CI documentation. This first source-grounded
  pass is not a completed review of every file. The initial inventory found
  170 Markdown files, three Mermaid files, and 15,834 Markdown physical lines.
  Four non-test Markdown files exceed 600 physical lines: Runbook (774),
  coordinator contract (1,248), cluster verification backlog (4,107), and
  polish campaign (1,084). [SIZE-01](backlog_matrix.md) separately owns size
  exceptions; line count alone does not justify splitting a file.
- Method: compare present-tense claims with their named authorities, production
  callers, tests, and adjacent reader paths. Source and tests below were read,
  not executed. A limited pre-draft local-link/heading scan found no missing
  target among 1,006 relative destinations and 369 anchors; that scan does not
  validate this new record and is not the repository's documentation check.
  The official check could not start here because the checkout has
  no `.venv` and the available Python lacks `markdown_it`. No dependencies were
  installed; no CI, Slurm, runtime, or scientific validation was performed.
- Line references below are for the pinned revision. Append the observed
  commit to any later audit pass or newly discovered finding; never silently
  mix revisions in one source claim. “Contradiction” means
  source-grounded disagreement at that revision. “Candidate” means that a
  transfer or reduction still needs a caller, link, and evidence review. No
  finding here establishes institutional qualification or biological meaning.

The [documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression)
guides placement: scientist journey in root guides, operator action and recovery
in operations, exact behavior beside owners, durable rationale in decisions,
and dated retained observations in history or retained artifacts. Before
closing DOCS-01, account for every finding: correct or transfer it to its
durable owner, dismiss it with a reason, or explicitly defer it to an
authoritative row or owner. Reconcile the backlog and live links, then retire
this temporary record. Exact evidence deletion needs its own proposal,
explicit approval, and separate commit.

### Coverage of this first pass

The inventory spans tracked Markdown and Mermaid files; the limited link scan
covered Markdown. Source comparisons are narrower. The following map keeps the remaining
repository-wide work visible without claiming file-by-file completion.

| Area | Compared in this pass | Further reading needed |
| --- | --- | --- |
| Scientist and operator paths | Root README, Quickstart, configuration, Runbook, Troubleshooting, engineering guide | Other operations and reference guides; end-to-end reader routes. |
| Architecture and decisions | Documentation authority, platform direction, reporting decision, logging contract, owner inventory | Other decision records, architecture maps, and all three Mermaid diagrams. |
| Task and evidence records | Main backlog, CV campaign/backlog, polish and optimization campaigns, history index/compendium | Remaining task rows, original evidence origins, and retained artifacts. |
| Product owners | Coordinator contract, runtime availability, reporting, resource defaults, stage and library samples | Every remaining owner README/contract, schemas, and adjacent production callers. |
| Tests, scripts, and CI | Golden README, selected owner tests, hook scope, workflow README, documentation-check source | Remaining test/fixture READMEs, documentation tooling, workflow/profile guides, and executable checks. |

## Findings matrix

The last column names the next investigation or possible durable home. It is
not a list of approved edits. Discovery notes below give the source references
and the boundary for each row.

| ID | Kind | Observation at the pinned revision | Next check or likely owner |
| --- | --- | --- | --- |
| [F01](#f01-public-stop-in-the-platform-decision) | Contradiction | Platform decision denies a public stop command; exact-request Slurm stop is public. | Reconcile decision with stop contract and CV-18 ceiling. |
| [F02](#f02-standalone-resource-floor) | Contradiction | Runbook gives a fixed 12-CPU/240-GiB standalone floor; defaults resolve against capacity and reject unmet task minima. | Check resource resolver and planning minima; correct operator capacity advice. |
| [F03](#f03-init-02-in-cluster-summaries) | Contradiction | CV summaries call INIT-01–03 source-complete while INIT-02 is Open. | Preserve explicit-manifest proof; reconcile present status with the authoritative backlog. |
| [F04](#f04-root-quickstart-description) | Reader route | Root README calls Quickstart a synthetic first Run; Quickstart leads with real EV/PUM1. | Align root journey and retain optional smoke link. |
| [F05](#f05-generic-study-versus-named-evpum1-route) | Reader route | “Own study” Runbook route points into fixed EV/PUM1 inputs and choices. | Separate generic study guidance from the named example. |
| [F06](#f06-existing-project-and-new-project-recovery) | Reader route | Troubleshooting combines existing-Project navigation with absent-child Init. | Give each failure its own recovery instruction. |
| [F07](#f07-doctor-repair-does-not-always-install) | Contradiction | Runbook says Doctor repair installs tools every time; ready runtime can be verified without installation. | Align operator wording with Doctor plan and contract. |
| [F08](#f08---version-and-local-env) | Behavior question | Runbook promises `--version` from any directory; `.env` is parsed before the version response. | Exercise malformed marked `.env` in a tiny local fixture before changing the promise. |
| [F09](#f09-runbook-entry-order) | Reader route | Advanced request/watch/stop procedures precede Runbook orientation. | Test whether moving the orientation improves entry without hiding recovery commands. |
| [F10](#f10-contract-location-claim) | Contradiction | Several indexes imply every source owner has an adjacent `CONTRACT.md`; some use a README or schema instead. | State actual owner-specific contract locations. |
| [F11](#f11-python-hook-scope) | Contradiction | Engineering guide omits root `setup.py` from hook scope. | Align the guide with `.pre-commit-config.yaml`. |
| [F12](#f12-init-preview-proposal) | Stale proposal | Polish campaign says Init preview shows only destination and directories; normal preview now shows scientific values. | Compare remaining requested fields and preview/publication protection. |
| [F13](#f13-doctor-profile-proposal) | Stale proposal | Polish campaign says Doctor has no `--profile`; the public option exists. | Reconcile proposal with accepted work and tests. |
| [F14](#f14-old-source-attestation-cost-candidate) | Recheck candidate | Old optimization Git-call finding counts a prior revision's source calls, not necessarily current execution. | Re-evaluate the current source before selecting optimization work. |
| [F15](#f15-cv-u22-interim-status-prose) | Compression candidate | CV-U22 card retains an interim “Verification pending” checkpoint before its present status. | Preserve unique cause/evidence; leave current card status with CV backlog. |
| [F16](#f16-polish-merged-pr-tables) | Compression candidate | Polish campaign repeats merged-PR chronology in two long tables. | Check unique decisions before leaving routine genealogy to Git. |
| [F17](#f17-main-backlog-chronology-and-run-repetition) | Compression candidate | Main backlog repeats PR genealogy and one exact hosted run in nearby rows. | Keep each evidence limit and accepted outcome while reducing repeat prose. |
| [F18](#f18-history-filing-rule-and-existing-compendium) | Evidence placement | History requires dated topic filenames; its indexed evidence compendium is undated. | Map links and origins before a rule exception or lossless split. |
| [F19](#f19-doctor-experiment-evidence-in-workflow-readme) | Evidence placement | CI workflow README retains a dated Doctor experiment absent from history index. | Assess a lossless evidence-home transfer and keep workflow navigation. |
| [F20](#f20-independent-golden-migration-comparisons) | Evidence placement | Independent-golden README mixes current oracle use with successive migration history. | Preserve comparison evidence before shortening owner instructions. |
| [F21](#f21-coordinator-contracts-no-write-section) | Compression candidate | Coordinator contract has a 632-line no-write section with several repeated topics. | Map distinct trust and recovery rules before restructuring. |
| [F22](#f22-coordinator-cross-owner-detail) | Compression candidate | Coordinator contract repeats Doctor, runtime-seal, and watch details also owned elsewhere. | Allocate exact semantics to the correct owner; keep necessary cross-links. |
| [F23](#f23-init-details-in-the-runbook) | Compression candidate | Runbook Init guidance mixes operator choices with hashing and file-identity internals. | Retain actionable warnings; place exact mechanics beside coordinator/config owners. |
| [F24](#f24-named-profile-procedure-placement) | Audience question | Config guide holds a long named-profile operator procedure while Runbook routes there. | Decide whether Runbook needs a concise command path and config guide the format. |
| [F25](#f25-reporting-decision-versus-migration-history) | Compression candidate | Reporting decision record includes implementation and PR migration detail beside lasting rationale. | Check unique rationale, then rely on reporting owner/Git for mechanics. |
| [F26](#f26-alpha-carrier-note-in-reporting-readme) | Compression candidate | Reporting README narrates an alpha carrier migration in a current interface guide. | Check whether the migration has a current consumer or evidence need. |
| [F27](#f27-old-fixed-resource-provenance) | Compression candidate | Resource-profile README repeats old 12-core provenance. | Retain current resource contract and historical evidence at their owners. |
| [F28](#f28-repeated-owner-boilerplate) | Compression candidate | Owner test and stage READMEs repeat near-identical generic paragraphs. | Compare exceptions, then use one shared explanation and local differences. |
| [F29](#f29-library-subowner-navigation) | Navigation candidate | Library owners are documented separately but lack a concise subowner index. | Test whether a small index improves source navigation without duplicating contracts. |

## Discovery notes

### F01 — Public stop in the platform decision

[Platform direction](../design/decisions/platform-direction.md) lines 204–206
says no public stop/cancel command exists. The [Runbook](../operations/RUNBOOK.md)
lines 139–162 gives `emrys stop --submission` preview and `--execute` for an exact
retained Slurm request. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 682–707 and [control implementation](../../src/emrys/orchestration/run_coordinator/control.py)
around line 1940 describe the same bounded interface; a source test at
`tests/orchestration/run_coordinator/test_materialization.py:3705–3725` exercises
its preview. These are current source and test claims, not a test run today.
The decision needs to acknowledge that narrow command. It must not imply a
generic Run stop or completed cluster proof: CV-18 retains queued/native-task
cancellation and recovery verification pending in the
[CV backlog](cluster_verification_backlog.md) around lines 3300–3305.

### F02 — Standalone resource floor

The [Runbook](../operations/RUNBOOK.md) lines 223–230 requires at least 12 CPUs
and 240 GiB for the default workflow. The packaged
[default profile](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml)
lines 4–14 selects allocation-based cores and automatic concurrency; the
[resource resolver](../../src/emrys/contracts/orchestration/application_model.py)
lines 842–879 admits what fits and refuses a task that cannot fit. A source
test at `tests/orchestration/run_coordinator/test_execution_profile.py:106–112`
resolves the default on an 11-CPU/65,536-MiB fixture. This disproves the fixed
floor as a rule. The profile still has per-task planning minima, including
40,960 MiB for a large repeated stage; smaller host success and real-study
capacity are not established by that test. Operator wording should direct
users to actual planned admission and workload sizing.

### F03 — INIT-02 in cluster summaries

The [CV backlog](cluster_verification_backlog.md) lines 24–30 and 72 and
[campaign](cluster_verification_campaign.md) lines 55–73 call INIT-01–03
source-complete. The authoritative [backlog](backlog_matrix.md) line 85 keeps
INIT-02 Open because automatic EV/PUM1 maintained-study selection is absent.
The [Quickstart](../../quickstart.md) lines 94–109 still passes an explicit
`--partition-manifest`; [onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 695–704 and 1104–1119 accepts that path. Thus explicit-manifest behavior
is real, while the selected automatic experience is not complete. The campaign
also acknowledges the gap at lines 149–150. Reconcile only the current summary
claim; do not change INIT-02 status or erase the explicit-manifest evidence.

### F04 — Root Quickstart description

The [root README](../../README.md) lines 65–70 says Quickstart provides a
synthetic first Run. [Quickstart](../../quickstart.md) lines 1–15 starts with
the real six-library EV/PUM1 study, and lines 74–75 offers the
[smoke test](../operations/SMOKE_TEST.md) as optional. A first-time reader is
sent to the correct link but given the wrong expectation. Correct the root
description while keeping the smoke path visible and optional.

### F05 — Generic study versus named EV/PUM1 route

The [Runbook](../operations/RUNBOOK.md) lines 280–293 calls the EV/PUM1
Quickstart the path for “your own study” and “your own data.” Quickstart lines
77–115 supplies particular sample assignments, comparison, target change,
thresholds, and a primary-contig manifest. The [configuration guide](../../configs/README.md)
lines 31–124 and 144–215 explains generic Project choices. Carrying the
named study’s choices into unrelated data is a plausible reader risk, not an
observed misuse. Investigate a concise generic route that points to config
authority and uses EV/PUM1 only when that is the actual study.

### F06 — Existing Project and new Project recovery

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 100–107 opens one
paragraph by telling readers to enter a directory containing `project.yaml`
or supply `--project`, then describes Init, whose child must be absent. Both
instructions have valid but different preconditions. Separate the existing
Project lookup from a failed new-Project preview/creation, preserving the
no-adoption and no-symlink rules.

### F07 — Doctor repair does not always install

The [Runbook](../operations/RUNBOOK.md) lines 585–587 says Doctor installs
managed tools on the head node. The same Runbook lines 700–706 and the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 217–233 distinguish a repair-and-verification plan from a
verification-only plan. A direct Doctor source test at
`tests/orchestration/run_coordinator/test_doctor.py:2956–2960,3046–3054`
expects no native/R installation when a ready Slurm runtime is rechecked.
Describe the possible work rather than guaranteed installation, and retain
where head-node and compute-side checks happen.

### F08 — `--version` and local `.env`

The [Runbook](../operations/RUNBOOK.md) lines 184–188 promises
`emrys --version` from any directory. The [CLI](../../src/emrys/__main__.py)
lines 349–368 reads `.env` before version dispatch; the
[environment loader](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 153–185 can reject a malformed marked file. This is a source-level edge
case, not a reproduced command failure. A tiny local fixture should establish
the exact failure and exit before deciding whether the promise or the CLI
ordering changes.

### F09 — Runbook entry order

The [Runbook](../operations/RUNBOOK.md) lines 9–163 starts with retained
submissions, watch, and stop. Its audience, setup routes, and command
conventions first appear at lines 164–188. The procedures are useful and must
remain findable, but a new operator meets advanced recovery terms before the
guide explains where to start. Check root and Quickstart inbound links before
moving a short orientation to the top; this is a navigation judgment, not a
behavior defect.

### F10 — Contract-location claim

[Docs index](../README.md) lines 3–4 explicitly says each component has a
`CONTRACT.md`; [owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
lines 7–8 makes a similar adjacent-file claim. The
[architecture](../architecture/ARCHITECTURE.md) lines 6–7 and
[tests index](../../tests/README.md) lines 3–4 use the broader word
“contract.” Runtime-availability and reporting owners, among others, express
current contracts in READMEs; schema owners also use schemas. Inventory actual
owner links before replacing the blanket filename claim with an accurate
route. Do not create empty contracts merely to satisfy an index sentence.

### F11 — Python hook scope

[Engineering conventions](../operations/ENGINEERING_CONVENTIONS.md) lines 71–74
lists staged Python under `scripts`, `src/emrys`, and `tests`.
[Hook configuration](../../.pre-commit-config.yaml) lines 5–16 also includes
root `setup.py` for Ruff check and format. Correct the prose after checking
whether any other documented hook exclusions are intentional. The hook file is
the executable scope; this audit did not run it.

### F12 — Init preview proposal

[Polish campaign](polish-campaign.md) lines 313–327 says Init preview shows only
destination, directories, and no-copy policy. Current
[onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py) lines
1208–1242 shows strand summary, comparison, target, thresholds, background,
and STAR values normally. GTF and per-sample detail remain behind `--verbose`
at lines 1243–1256. Re-evaluate each requested preview field and
preview/publication agreement before calling the entire proposal complete or
selecting new implementation. Preserve the scientific meaning of suggested
values; source inspection is not proof that displayed and published bytes agree.

### F13 — Doctor profile proposal

[Polish campaign](polish-campaign.md) lines 329–339 says Doctor has no profile
selector. [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py)
lines 1976–1982 accepts `--profile`, and the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 729–742 describes default, named, and absolute selection. A focused
source test at `tests/orchestration/run_coordinator/test_doctor.py:464–510`
covers the path. Reconcile the old proposal against the authoritative backlog
and actual validation before retaining any remaining acceptance gap.

### F14 — Old source-attestation cost candidate

[Optimization campaign](optimization_campaign.md) lines 17–24 explicitly pins
its audit to `fdf7676` and requires a recheck before selection. Its task-entry
candidate at lines 269–290 counted 24 Git subprocess calls per task then;
that is historical source counting, not measured latency. Current
[source authority](../../src/emrys/libraries/source_authority.py) lines 68–125
uses installed package bytes and build metadata for identity rather than that
old Git-object path. Inspect today's complete task-entry caller chain and
measure only if this candidate is selected; do not rewrite the dated audit as
though it was false at its recorded revision.

### F15 — CV-U22 interim status prose

The [CV backlog](cluster_verification_backlog.md) lines 1472–1511 includes an
interim “Verification pending” checkpoint within CV-U22 before the card's
current state. This can read like a second present status. Compare the card's
dated evidence, current status cell, and index wording; preserve the unique
reason for reopening or retaining a limit while distinguishing it from present
acceptance. The CV backlog, not this working matrix, owns the card status.

### F16 — Polish merged-PR tables

[Polish campaign](polish-campaign.md) lines 991–1025 carries two detailed
tables of merged PRs #116–147. Its live purpose is to avoid reselecting
finished work; Git already retains routine chronology. Check each row for a
unique safety rule, decision, or evidence limitation, then keep that fact in
the appropriate backlog, owner, decision, or evidence home. Removing a PR table
without that comparison could lose why a proposal was superseded.

### F17 — Main backlog chronology and run repetition

The [main backlog](backlog_matrix.md) around lines 313, 343, and 349 includes
PR genealogy, and lines 340–356 repeat hosted run `34306975901` across nearby
acceptance prose. The accepted outcomes and exact CI limit must stay visible;
the same run should not imply independent checks merely because it is cited
twice. Map which row owns the observation and which rows only need a link. Do
not compress away distinct acceptance criteria or alter any task status.

### F18 — History filing rule and existing compendium

[History index](../history/README.md) lines 18–22 requires
`YYYY-MM-DD-topic.md` and an originating immutable commit. Its only indexed
record, [validation evidence](../history/validation-evidence.md), has no date
in its filename and aggregates multiple observations; one local R anecdote at
lines 132–139 lacks an explicit source date/revision. The compendium is linked
from the docs index and backlog, and
`tests/documentation/test_validate_structure.py:29` names it. Map every inbound
link and each record's origin first. Possible outcomes are a documented legacy
exception or lossless dated records; neither a rename nor evidence deletion is
implied by the naming mismatch.

### F19 — Doctor experiment evidence in workflow README

[Workflow README](../../.github/workflows/README.md) lines 24–38 preserves a
retired two-worker Doctor namespace experiment: exact run `34995028343`, commit
`45bd9cd2`, order, times, sampled RSS, and explicit limitations. The current
workflow lane description at lines 3–22 is appropriately local to CI; the
experiment may fit [history](../history/README.md) better. First compare the
run artifact and history index, and plan a lossless destination plus link.
Do not delete or paraphrase away the measurements, donor comparison, or
uncontrolled-cache and RSS caveats.

### F20 — Independent golden migration comparisons

[Golden README](../../tests/contract_integration/independent_contract_goldens/README.md)
lines 3–10 explains current literal oracles and their evidence ceiling. Lines
12–57 then record successive schema and renderer migrations, including exact
byte-identity comparisons. The current oracle instructions should remain
beside tests. Before shortening old migration prose, identify which
comparison has lasting evidence value and where its exact predecessor,
digests, and limitations can be retained. Golden presence itself is not a
runtime or biological validation claim.

### F21 — Coordinator contract's no-write section

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
has a single `No-write and publication boundaries` section spanning lines
87–718. Init rules recur at lines 89–150 and 184–215; watch selection appears
at lines 56–67 and again through 557–683. These may be separable by trust or
mutation boundary, so repeated terms alone are not proof of duplication.
Build a topic map of command, input, exact protection, caller, test, and
recovery consequence before tightening headings or prose. Preserve each
independent refusal and evidence level; coordinate file-size disposition with
SIZE-01.

### F22 — Coordinator cross-owner detail

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 236–287 details Doctor timing and presentation also described in the
[logging contract](../design/LOGGING_CONTRACT.md) lines 172–189. Its runtime
seal and replacement discussion at lines 313–339 overlaps the
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md)
lines 59–104, and watch keys at lines 622–637 overlap the Runbook. Check which
document owns each guarantee: coordinator should retain its command boundary,
runtime owner its sealed-content admission, and Runbook the keys an operator
needs. Cross-owner summaries can remain when they explain a real handoff.

### F23 — Init details in the Runbook

The [Runbook](../operations/RUNBOOK.md) lines 303–335 mixes useful Init
choices and safe prompts with exact hashing, inode, STAR derivation, and
publication mechanics also covered by the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
and [config guide](../../configs/README.md). Retain what the operator must
choose, observe, or preserve after interruption. Compare the detailed
paragraphs with owner tests and configuration rules before replacing mechanics
with links; a shorter Runbook must still warn that preview does not hash FASTQ
contents and creation can refuse changed inputs.

### F24 — Named-profile procedure placement

[Config guide](../../configs/README.md) lines 239–305 contains a long
named-profile creation walkthrough. The [Runbook](../operations/RUNBOOK.md)
routes operators there around lines 569–576 while retaining its own site and
Doctor steps. Review actual user path and inbound anchors: a short command
route may belong in the Runbook, while field meaning and YAML examples may
remain with configuration. No relocation is selected yet.

### F25 — Reporting decision versus migration history

[Execution, evidence, and reporting decision](../design/decisions/execution-evidence-and-reporting.md)
lines 108–263 contains durable boundaries alongside exact retired callbacks,
facades, PR #146 provenance, and current publication mechanics. The
[reporting owner](../../src/emrys/reporting/README.md) holds present behavior;
Git can retain routine implementation sequence. Extract the lasting reason
for source identity and create-only publication before considering any
shortening. The retired-path characterization and recovery warning at lines
210–232 may be evidence or safety context, so its destination needs review.

### F26 — Alpha carrier note in reporting README

[Reporting README](../../src/emrys/reporting/README.md) lines 22–27 says an
approved alpha cleanup changed the carrier and retired an alias, then gives
the current field/callable shape. Check current provider consumers and direct
contract tests. If the historical sentence adds no active compatibility
instruction, retain only the current interface there and let Git or an exact
evidence record carry the transition. Do not drop the actual input/output
types while trimming chronology.

### F27 — Old fixed-resource provenance

[Resource defaults README](../../src/emrys/orchestration/run_coordinator/resources/README.md)
lines 3–12 accurately describes the allocation-aware policy. Lines 14–21
also narrate where the old fixed 12-core policy entered and moved in Git.
Check whether any current maintainer needs that provenance here or whether
the dated [CV backlog](cluster_verification_backlog.md) and Git retain it.
Keep the present admission/capacity caveat; do not turn profile minima into
measured utilization or speedup.

### F28 — Repeated owner boilerplate

Six shell-stage test READMEs, including
[STAR-index tests](../../tests/stages/star_index/README.md) and
[alignment tests](../../tests/stages/star_alignment/README.md), repeat the
runner/evidence paragraph. Six stage owner READMEs, including
[STAR index](../../src/emrys/stages/star_index/README.md) and
[alignment](../../src/emrys/stages/star_alignment/README.md), repeat a generic
execution paragraph. Compare owner-specific exceptions before proposing one
shared explanation from [tests index](../../tests/README.md) or
[stage map](../../src/emrys/contracts/STAGE_MAP.md). Each owner must retain its
distinct command, contract, oracle, and evidence limit. The possible saving
has not been measured or approved.

### F29 — Library subowner navigation

[Libraries README](../../src/emrys/libraries/README.md) can be tested as a
short index to six documented subowners. Inspect actual library directories,
imports, and existing links first; add navigation only if it reduces search
work without restating each subowner contract. This is a possible small
addition, so DOCS-01's compression aim does not make it automatic.

## Preservation boundaries for the next pass

The CV campaign's E01–E12 evidence register, CV-26 measurements, the
optimization campaign's measured PR #45 experiment, the validation-evidence
compendium, the workflow Doctor experiment, and independent-golden migration
comparisons are retained support for bounded claims. Their placement can be
reviewed, but shortening or moving adjacent guidance must not silently delete
or promote them. The [CV backlog](cluster_verification_backlog.md) also retains
an original-note crosswalk near its end; inspect that before condensing any
card history. Concise current surfaces, including the root CI index and schema
README hierarchy, need no change merely because they were audited.
