# DOCS-01 discovery notes

This companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F01–F29 source-backed observations and next checks. The
[continued notes](docs-01-discoveries-continued.md) hold F30 onward. Unless a subsection
names another revision, all source line references are pinned to
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`. These are audit
observations, not accepted changes or a task-status registry.

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
The same decision at line 206 limits resume to already interrupted or failed
Runs. [Troubleshooting](../operations/TROUBLESHOOTING.md) lines 35–50 and the
coordinator contract lines 1008–1035 also allow `emrys resume RUN` to complete
an exact prepared Attempt finalization. A prepared success starts no new
scientific work. Correct both decision claims without implying every resume
creates another Attempt or that ambiguous evidence authorizes finalization.

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

The [Runbook](../operations/RUNBOOK.md) lines 585–587 and 654–656, the
[reporting decision](../design/decisions/execution-evidence-and-reporting.md)
lines 44–53, and the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 164–166 speak of Doctor installing tools on the head node as a certainty.
The same Runbook lines 700–706 and the
coordinator contract lines 217–233 distinguish a repair-and-verification plan from a
verification-only plan. A direct Doctor source test at
`tests/orchestration/run_coordinator/test_doctor.py:2956–2960,3046–3054`
expects no native/R installation when a ready Slurm runtime is rechecked.
Align both guides and the decision on possible package-manager work, retaining
where head-node and compute-side checks happen.
The decision at lines 44–50 additionally names `uv` among Doctor's
installation delegates. The [root README](../../README.md) lines 53–56 and
[Runbook](../operations/RUNBOOK.md) lines 258–263 assign Doctor Project-owned
native/R work through Pixi and `renv`, with Python dependencies left to
separate package-manager setup. The Doctor implementation's manager commands
in `doctor.py` lines 1235–1265 call Pixi and Rscript, not `uv`. Correct the
decision's owner list without suggesting Doctor repairs Python itself.

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
source test at `tests/orchestration/run_coordinator/test_doctor.py:464–515`
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
The [backlog's CV retirement condition](backlog_matrix.md) lines 145–150
explicitly names this undated compendium as the future destination for
E01–E12 and hosted/artifact records. That conflicts with the history index's
dated-file and unchanged-record rules, rather than being only a filename
oddity. Decide whether the legacy compendium is a documented exception or
whether new dated records and updated backlog/index/checker links are the
intended route before any transfer. No evidence is moved by this audit.

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
`src/emrys/reporting/paired_cmh_candidate_ranking_report/provider.py:32–33`.
This is a five-line passage; deleting its historical opening alone saves little.
Retain its actionable snapshot paths, types, and positional guidance unless a
larger owner-document edit provides an equally clear home. No standalone
compression is selected by this observation.

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
