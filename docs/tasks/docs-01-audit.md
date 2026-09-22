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
- The second read-only pass on 2026-09-22 checked the same `3a672fdf` source
  after the audit-only commit `8f8ac2e1`. It refined F03, F07–F08, F10,
  F12–F13, F15, F17–F22, and F25–F29, and added F30–F33. Source and tests
  were inspected, not executed.

The [documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression)
guides placement: scientist journey in root guides, operator action and recovery
in operations, exact behavior beside owners, durable rationale in decisions,
and dated retained observations in history or retained artifacts. Before
closing DOCS-01, account for every finding: correct or transfer it to its
durable owner, dismiss it with a reason, or explicitly defer it to an
authoritative row or owner. Reconcile the backlog and live links, then retire
this temporary record. Exact evidence deletion needs its own proposal,
explicit approval, and separate commit.

### Coverage so far

The inventory spans tracked Markdown and Mermaid files; the limited link scan
covered Markdown. Source comparisons are narrower. The following map keeps the
remaining repository-wide work visible without claiming file-by-file completion.

| Area | Compared to date | Further reading needed |
| --- | --- | --- |
| Scientist and operator paths | Root README, Quickstart, configuration, Runbook, Troubleshooting, engineering guide | Other operations and reference guides; end-to-end reader routes. |
| Architecture and decisions | Documentation authority, platform direction, reporting decision, logging contract, owner inventory, scientist pipeline diagram | Other decision records, architecture maps, and two remaining Mermaid diagrams. |
| Task and evidence records | Main backlog, CV campaign/backlog, polish and optimization campaigns, history index/compendium | Remaining task rows, original evidence origins, and retained artifacts. |
| Product owners | Coordinator contract, runtime availability, reporting, resource defaults, stage and library samples | Every remaining owner README/contract, schemas, and adjacent production callers. |
| Tests, scripts, and CI | Golden README, selected owner tests, hook scope, workflow README, documentation-check source/tests, workflow profile guides | Remaining test/fixture READMEs, documentation tooling, and executable checks. |

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
| [F07](#f07-doctor-repair-does-not-always-install) | Contradiction | Runbook and a decision say Doctor repair installs tools every time; a ready runtime can be verified without installation. | Align operator and decision wording with Doctor plan and contract. |
| [F08](#f08---version-and-local-env) | Behavior question | Runbook promises `--version` from any directory; `.env` is parsed before the version response. | Exercise malformed marked `.env` in a tiny local fixture before changing the promise. |
| [F09](#f09-runbook-entry-order) | Reader route | Advanced request/watch/stop procedures precede Runbook orientation. | Test whether moving the orientation improves entry without hiding recovery commands. |
| [F10](#f10-contract-location-claim) | Contradiction | Two indexes claim every source owner has an adjacent `CONTRACT.md`; many use a README or schema instead. | State actual owner-specific contract locations. |
| [F11](#f11-python-hook-scope) | Contradiction | Engineering guide omits root `setup.py` from hook scope. | Align the guide with `.pre-commit-config.yaml`. |
| [F12](#f12-init-preview-proposal) | Prior-revision proposal | Polish campaign's dated audit says Init preview shows only destination and directories; normal preview now shows scientific values. | Compare remaining requested fields and preview/publication protection. |
| [F13](#f13-doctor-profile-proposal) | Prior-revision proposal | Polish campaign's dated audit says Doctor has no `--profile`; the public option now exists. | Reconcile proposal with accepted work and tests. |
| [F14](#f14-old-source-attestation-cost-candidate) | Recheck candidate | Old optimization Git-call finding counts a prior revision's source calls, not necessarily current execution. | Re-evaluate the current source before selecting optimization work. |
| [F15](#f15-cv-u22-interim-status-prose) | Preserve chronology | CV-U22's dated checkpoints explain why the card returned to Open; compression has no demonstrated benefit yet. | Keep the causal record unless a concrete reader conflict is found. |
| [F16](#f16-polish-merged-pr-tables) | Compression candidate | Polish campaign repeats merged-PR chronology in two long tables. | Check unique decisions before leaving routine genealogy to Git. |
| [F17](#f17-main-backlog-chronology-and-run-repetition) | Preserve row evidence | One hosted run supports three distinct backlog rows; repeated row-local citations may be warranted. | Check only routine genealogy for safe compression. |
| [F18](#f18-history-filing-rule-and-existing-compendium) | Evidence placement | History requires dated topic filenames; its indexed evidence compendium is undated. | Map links and origins before a rule exception or lossless split. |
| [F19](#f19-doctor-experiment-evidence-in-workflow-readme) | Evidence placement | CI workflow README repeats a shorter Doctor experiment summary already detailed in the CV backlog. | Use the CV card as evidence source before considering a history transfer. |
| [F20](#f20-independent-golden-migration-comparisons) | Evidence placement | Independent-golden README mixes current oracle use with successive migration history. | Preserve comparison evidence before shortening owner instructions. |
| [F21](#f21-coordinator-contracts-no-write-section) | Navigation candidate | Coordinator contract has a 632-line no-write section without subheadings; similar topics guard distinct boundaries. | Map topics before restructuring; no deletion inferred. |
| [F22](#f22-coordinator-cross-owner-detail) | Ownership question | Coordinator, logging, runtime, and Runbook descriptions overlap but have different trust boundaries. | Preserve each owner's guarantee and useful cross-links. |
| [F23](#f23-init-details-in-the-runbook) | Compression candidate | Runbook Init guidance mixes operator choices with hashing and file-identity internals. | Retain actionable warnings; place exact mechanics beside coordinator/config owners. |
| [F24](#f24-named-profile-procedure-placement) | Audience question | Config guide holds a long named-profile operator procedure while Runbook routes there. | Decide whether Runbook needs a concise command path and config guide the format. |
| [F25](#f25-reporting-decision-versus-migration-history) | Compression candidate | Reporting decision record includes implementation and PR migration detail beside lasting rationale. | Check unique rationale, then rely on reporting owner/Git for mechanics. |
| [F26](#f26-alpha-carrier-note-in-reporting-readme) | Compression candidate | Reporting README narrates an alpha carrier migration alongside current collaborator API guidance. | Preserve exact current types and positional guidance if trimming history. |
| [F27](#f27-old-fixed-resource-provenance) | Compression candidate | Resource-profile README repeats old 12-core provenance. | Retain current resource contract and historical evidence at their owners. |
| [F28](#f28-repeated-owner-boilerplate) | Compression candidate | Owner test and stage READMEs repeat near-identical generic paragraphs. | Compare exceptions, then use one shared explanation and local differences. |
| [F29](#f29-library-subowner-navigation) | Navigation mismatch | Tests point to a library index that does not route readers to six documented Python subowners. | Add a concise subowner route without copying contracts. |
| [F30](#f30-dashboard-reporting-stage-text) | Product-facing text | Dashboard still describes three reporting transactions and a final workflow target after reporting. | Check current workflow/reporting owners and historical log aliases before selecting a product correction. |
| [F31](#f31-historical-slurm-username-recovery-advice) | Recovery wording | Troubleshooting gives an undated upgrade instruction for a Slurm username incident whose submission fix is already present. | Preserve incident evidence and give current-version diagnosis. |
| [F32](#f32-mermaid-checks-stated-ceiling) | Evidence ceiling | Documentation tests claim Mermaid syntax coverage; checker only checks declaration and fences. | Narrow the README claim to the actual structural check. |
| [F33](#f33-report-receipt-version-in-the-scientist-diagram) | Diagram contradiction | Scientist pipeline diagram names a v4 report receipt; current report receipt is v8. | Correct non-authoritative diagram against reporting/schema owners. |

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
itself acknowledges the gap at lines 149–150. Reconcile only the current summary
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

The [Runbook](../operations/RUNBOOK.md) lines 585–587 and 654–656, plus the
[reporting decision](../design/decisions/execution-evidence-and-reporting.md)
lines 44–53, speak of Doctor installing tools on the head node as a certainty.
The same Runbook lines 700–706 and the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 217–233 distinguish a repair-and-verification plan from a
verification-only plan. A direct Doctor source test at
`tests/orchestration/run_coordinator/test_doctor.py:2956–2960,3046–3054`
expects no native/R installation when a ready Slurm runtime is rechecked.
Align both guides and the decision on possible package-manager work, retaining
where head-node and compute-side checks happen.

### F08 — `--version` and local `.env`

The [Runbook](../operations/RUNBOOK.md) lines 184–188 promises
`emrys --version` from any directory. The [CLI](../../src/emrys/__main__.py)
lines 349–368 reads `.env` before version dispatch; the
[environment loader](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 153–185 can reject a malformed marked file. This is a source-level edge
case, not a reproduced command failure. `tests/test_public_cli_contracts.py`
lines 713–734 covers version from a clean temporary directory; the malformed
`.env` test at `tests/orchestration/run_coordinator/test_onboarding.py:267–281`
does not combine that file with `--version`. A tiny local fixture should
establish the exact failure and exit before deciding whether the promise or
CLI ordering changes.

### F09 — Runbook entry order

The [Runbook](../operations/RUNBOOK.md) lines 9–163 starts with retained
submissions, watch, and stop. Its audience, setup routes, and command
conventions first appear at lines 164–188. The procedures are useful and must
remain findable, but a new operator meets advanced recovery terms before the
guide explains where to start. The root README lines 67–70 and docs index
lines 8–9 both route operators here. Check those inbound paths before
moving a short orientation to the top; this is a navigation judgment, not a
behavior defect.

### F10 — Contract-location claim

[Docs index](../README.md) lines 3–4 explicitly says each component has a
`CONTRACT.md`; [owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
lines 7–8 makes a similar adjacent-file claim. The
[architecture](../architecture/ARCHITECTURE.md) lines 6–7 and
[tests index](../../tests/README.md) lines 3–4 use the broader word
“contract.” Runtime-availability and reporting owners, among others, express
current contracts in READMEs; schema owners also use schemas. At the pinned
revision, 62 source READMEs but only 15 adjacent `CONTRACT.md` files exist;
47 README directories have no adjacent file. The narrower stage-owner claim
is valid. Replace only the global filename promise with an accurate route;
do not create empty contracts merely to satisfy an index sentence.

### F11 — Python hook scope

[Engineering conventions](../operations/ENGINEERING_CONVENTIONS.md) lines 71–74
lists staged Python under `scripts`, `src/emrys`, and `tests`.
[Hook configuration](../../.pre-commit-config.yaml) lines 5–16 also includes
root `setup.py` for Ruff check and format. Correct the prose after checking
whether any other documented hook exclusions are intentional. The hook file is
the executable scope; this audit did not run it.

### F12 — Init preview proposal

[Polish campaign](polish-campaign.md) lines 313–327 says Init preview showed only
destination, directories, and no-copy policy at its dated September 7 audit. Current
[onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py) lines
1208–1242 shows strand summary, comparison, target, thresholds, background,
and STAR values normally. GTF and per-sample detail remain behind `--verbose`
at lines 1243–1256. Re-evaluate each requested preview field and
preview/publication agreement before calling the entire proposal complete or
selecting new implementation. Preserve the scientific meaning of suggested
values; source inspection is not proof that displayed and published bytes agree.

### F13 — Doctor profile proposal

[Polish campaign](polish-campaign.md) lines 329–339 says Doctor had no profile
selector at its dated audit. [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py)
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

The [CV backlog](cluster_verification_backlog.md) lines 1472–1511 dates a
known-smoke correction, labels “Verification pending” as that checkpoint,
then explains the unsolved general donor requirement and returns CV-U22 to
Open. The chronology preserves why the card reopened. No concrete confusion
or safe reduction was established in the second pass; keep the causal record
and the CV backlog's current status authority.

### F16 — Polish merged-PR tables

[Polish campaign](polish-campaign.md) lines 991–1025 carries two detailed
tables of merged PRs #116–147. Its live purpose is to avoid reselecting
finished work; Git already retains routine chronology. Check each row for a
unique safety rule, decision, or evidence limitation, then keep that fact in
the appropriate backlog, owner, decision, or evidence home. Removing a PR table
without that comparison could lose why a proposal was superseded.

### F17 — Main backlog chronology and run repetition

The [main backlog](backlog_matrix.md) around lines 313, 343, and 349 includes
PR genealogy. Lines 340–356 cite hosted run `34306975901` in three distinct
accepted rows. The repeated row-local citation helps each acceptance stand
alone and need not be removed. Any reduction should focus on routine PR
chronology after checking unique baseline, measurement, and evidence limits;
do not compress distinct acceptance criteria or alter task status.

### F18 — History filing rule and existing compendium

[History index](../history/README.md) lines 18–22 requires
`YYYY-MM-DD-topic.md` and an originating immutable commit. Its only indexed
record, [validation evidence](../history/validation-evidence.md), has no date
in its filename and aggregates multiple observations; one local R anecdote at
lines 132–139 lacks an explicit source date/revision. The compendium is linked
from the docs index, backlog, and coordinator contract; both
`scripts/documentation/validate_structure.py:14–34` and
`tests/documentation/test_validate_structure.py:29` name it. Map every inbound
link and each record's origin first; several entries lack a source date.
Possible outcomes are a documented legacy
exception or lossless dated records; neither a rename nor evidence deletion is
implied by the naming mismatch.

### F19 — Doctor experiment evidence in workflow README

[Workflow README](../../.github/workflows/README.md) lines 24–38 summarizes a
retired two-worker Doctor namespace experiment. The
[CV backlog](cluster_verification_backlog.md) lines 3949–3995 already preserves
the fuller record: exact run `34995028343`, artifact identity, trials, sampled
RSS, caveats, and decision. That CV card is the evidence source for any
transfer to [history](../history/README.md); the workflow guide needs only a
route to it if this topic is moved. Preserve exact measurements and the
uncontrolled-cache, shared-page, and missed-peak limits. No evidence deletion
is authorized.

### F20 — Independent golden migration comparisons

[Golden README](../../tests/contract_integration/independent_contract_goldens/README.md)
lines 3–10 explains current literal oracles and their evidence ceiling. Lines
12–57 then record successive schema and renderer migrations, including exact
byte-identity comparisons. Most comparisons at lines 12–41 do not name the
predecessor revision or old/new digests in that README; later examples at
lines 43–57 name predecessor commits. Keep current oracle instructions beside
tests. Before migrating a comparison into dated history, trace Git, tests,
exact predecessor/current revisions, and oracle values. The prose alone is
not sufficient retained proof; golden presence is not runtime or biological
validation.

### F21 — Coordinator contract's no-write section

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
has a single `No-write and publication boundaries` section spanning lines
87–718 without subheadings. The apparent Init repeats separate prompts and
publication (89–150) from hashing and input stability (184–215); watch
selection (56–67) differs from dated view, refresh, and action rules
(557–683). The second pass found navigability pressure, not proven deletable
duplication. Build a topic map before changing headings; preserve independent
refusals and evidence levels, and coordinate size disposition with SIZE-01.

### F22 — Coordinator cross-owner detail

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 236–287 owns Doctor observation and admission timing; the
[logging contract](../design/LOGGING_CONTRACT.md) lines 172–189 owns emitted
event shape and flushing. Coordinator runtime orchestration at lines 313–339
overlaps the
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md)
lines 59–104, which owns the closed seal and fixed-content boundary. Watch
keys at lines 622–637 also appear in the Runbook for operator use. These are
mostly distinct trust boundaries. Keep the coordinator command handoff,
runtime admission, logging event rules, and operator keys with their owners;
cross-owner summaries can remain when they explain a real handoff.

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
lines 119–159 gives lasting scientific-fingerprint and reporting-provenance
rationale; lines 201–209 explain create-only publication. The
[reporting owner](../../src/emrys/reporting/README.md) owns current mechanics.
The clearest chronology candidate is the PR #146 and retired callback inventory
at decision lines 210–225, plus the one-time transition at 253–257. Compare
the rest with the owner before shortening; preserve the failure/recovery limit
at 227–232 and old-Run compatibility meaning at 253–257.

### F26 — Alpha carrier note in reporting README

[Reporting README](../../src/emrys/reporting/README.md) lines 22–27 says an
approved alpha cleanup changed the carrier and retired an alias, then gives
the current field/callable shape. That is the only explicit collaborator
reporter API guidance found in this pass; the current carrier is in
`src/emrys/reporting/__init__.py:24–63`, with a built-in provider caller in
`src/emrys/analyses/paired_cmh_candidate_ranking_report/provider.py:32–33`.
Historical framing may be shortened only while retaining actionable snapshot
paths, types, and positional guidance.

### F27 — Old fixed-resource provenance

[Resource defaults README](../../src/emrys/orchestration/run_coordinator/resources/README.md)
lines 3–12 accurately describes the allocation-aware policy. Lines 14–21
also narrate where the old fixed 12-core policy entered and moved in Git.
The same origin commits are retained in the [CV backlog](cluster_verification_backlog.md)
around line 1772. Check whether a maintainer needs the duplicate here. Keep
the present admission/capacity caveat; do not turn profile minima into
measured utilization or speedup.

### F28 — Repeated owner boilerplate

Six shell-stage test READMEs, including
[STAR-index tests](../../tests/stages/star_index/README.md) and
[alignment tests](../../tests/stages/star_alignment/README.md), repeat the
same five-line runner/evidence paragraph. Their first paragraphs state
owner-specific claims. Six corresponding stage owner READMEs, including
[STAR index](../../src/emrys/stages/star_index/README.md) and
[alignment](../../src/emrys/stages/star_alignment/README.md), repeat a generic
execution paragraph. Compare owner-specific exceptions before proposing one
shared explanation from [tests index](../../tests/README.md) or
[stage map](../../src/emrys/contracts/STAGE_MAP.md). Each owner must retain its
distinct command, contract, oracle, and evidence limit. The possible saving
has not been measured or approved.

### F29 — Library subowner navigation

[Tests library index](../../tests/libraries/README.md) lines 3–6 directs
readers to the production [library index](../../src/emrys/libraries/README.md),
but that index lists only three shell helpers and a runner link. Six documented
subpackages—alignments, application logging, evidence, quality, references,
and validation—have no route from it. A short list of links could repair this
navigation gap without copying contracts; assess the added lines against the
reader benefit rather than assuming a new index is required.

### F30 — Dashboard reporting-stage text

[Dashboard source](../../src/emrys/orchestration/run_coordinator/dashboard.py)
lines 183–202 tells watch readers that reporting uses three dependent
transactions and that a final workflow target follows reporting. Its rule map
at 206–214 retains old reporting aliases; the stage table renders REPORT and
FINAL rows even when unscheduled (1573–1608). Current
[reporting](../../src/emrys/reporting/README.md) lines 3–16 and
`src/emrys/orchestration/run_coordinator/reporting_boundary.py:43–44` define
two publication operations after scientific completion. The
[Snakefile](../../src/emrys/workflow/Snakefile) lines 394–397 ends the backend
at verified scientific tasks. This is user-facing product text drift, not a
request to delete historical log aliases. Review watch projection and old-log
compatibility before selecting a separate product correction; scheduler text
still cannot prove admitted Run completion.

### F31 — Historical Slurm username recovery advice

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 65–72 tells a reader
with Snakemake's `No username set in the environment` to “Update EMRYS to the
submission fix,” without identifying a fixed revision or distinguishing a
current installation. The [backlog incident](backlog_matrix.md) lines 243–252
records the original failure and fix; current
[submission code](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 861–870 preserves four login-name variables, with direct source tests
at `tests/orchestration/run_coordinator/test_slurm_submission.py:2027–2099`.
Keep the incident and safe resume/evidence advice. Current recovery should
first identify the installed revision and actual submission diagnostic;
this audit has not reproduced a current Slurm failure.

### F32 — Mermaid check's stated ceiling

[Documentation test README](../../tests/documentation/README.md) lines 3–8
says cases cover “standalone Mermaid syntax.” The
[checker](../../scripts/documentation/validate_structure.py) lines 235–251
checks only a first nonblank `flowchart` declaration and absence of Markdown
fences; its [tests](../../tests/documentation/test_validate_structure.py)
lines 290–323 exercise those refusals. The
[tool README](../../scripts/documentation/README.md) already describes
declarations and fences. Narrow the test README wording: this check does not
parse the rest of Mermaid grammar or verify rendering.

### F33 — Report receipt version in the scientist diagram

The linked [scientist-facing diagram](../architecture/diagrams/current_user_pipeline.mmd)
line 15 says reporting ends with a validated v4 receipt.
[Reporting](../../src/emrys/reporting/README.md) lines 31–49 and the
[artifact schema index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 identify artifact entries v4, Run result manifest v8, and report
receipt v8. Correct the diagram's receipt label without conflating these
separate formats. The diagram is a non-authoritative view, but it is the
architecture's linked reader path at `docs/architecture/ARCHITECTURE.md:56`.

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
