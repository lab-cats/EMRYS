# DOCS-01 discovery notes

This companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F01–F29 source-backed observations and evidence boundaries. The
[continued notes](docs-01-discoveries-continued.md) hold F30–F61 and the
[third file](docs-01-discoveries-third.md) holds F62–F99, and the
[fourth file](docs-01-discoveries-fourth.md) begins at F100. Unless a subsection
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
The contract's line 684 still says stop admits only v3 requests. Current
`slurm_submission.py:55–59,73–84,303–313` defaults new requests to v4 and admits complete
named v3/v4 requests for stop. The cited public preview fixture builds v3
(`test_slurm_submission.py:113–123`); the later native-task stop fixture also
selects a v3 request (`test_materialization.py:6400–6417,6800–6802`). Those
tests do not establish a v4 public stop journey. This present-tense
contract conflict also appears in F50; CV-18's v3 slice remains dated.
The decision omits this narrow command, and the source does not establish a
generic Run stop or completed cluster proof: CV-18 retains queued/native-task
cancellation and recovery verification pending in the
[CV backlog](cluster_verification_backlog.md) around lines 3300–3305.
The same decision at line 206 limits resume to already interrupted or failed
Runs. [Troubleshooting](../operations/TROUBLESHOOTING.md) lines 35–50 and the
coordinator contract lines 1008–1035 also allow `emrys resume RUN` to complete
an exact prepared Attempt finalization. A prepared success starts no new
scientific work. Both decision claims differ from current behavior; not every
resume creates another Attempt, and ambiguous evidence cannot authorize finalization.
The top-level CLI help in [`__main__.py`](../../src/emrys/__main__.py) line 261
also describes resume only for failed or interrupted Runs; its short label
does not mention prepared finalization.
`tests/orchestration/run_coordinator/test_lifecycle.py:2192–2256` exercises
public preview/execute for prepared succeeded and blocked outcomes without a
new Attempt; lines 2259–2349 cover a finalization-only Slurm-profile path
without submission. These are local fixtures, not hosted or Viking proof.
The contract's trusted-workspace/equal-byte recycled-inode limit at 1021–1027
and the CV backlog's pending verification at 70–77 remain in force.

### F02 — Standalone capacity wording

The [Runbook](../operations/RUNBOOK.md) lines 223–230 says the default workflow
uses process-visible capacity, then says its “retained concurrent-stage
allowances” require at least 12 CPUs and 240 GiB. It does not name the workload
or concurrency shape those numbers preserve. The packaged
[default profile](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml)
lines 4–38 selects allocation-based budgets and automatic concurrency; the
[resource resolver](../../src/emrys/contracts/orchestration/application_model.py)
lines 842–891 fits task concurrency to workload count, cores, and memory
minimums. The [source fixture](../../tests/orchestration/run_coordinator/test_execution_profile.py)
lines 66–112 shows that direct and Viking defaults share policy; an 11-CPU,
65,536-MiB six-sample allocation resolves one concurrent STAR task. This
rules out a fixed 12/240 policy-resolution floor; it does not refute the
qualified higher-concurrency claim. Six STAR tasks at the declared 40,960-MiB
minimum need 240 GiB; 12 CPUs yield two threads each. That is a policy
calculation, not measured capacity. The [config guide](../../configs/README.md)
says fixed caps are gone (lines 281–286) and minima are planning numbers,
not dataset bounds (lines 324–328). The coordinator contract treats visible
RAM as a ceiling, not guaranteed free memory (721–727), and says Snakemake
does not enforce per-process RSS (788–789). CV-U28's institutional verification
remains pending.

### F03 — INIT-02 in cluster summaries

The [CV backlog](cluster_verification_backlog.md) lines 24–30 and 72 and
[campaign](cluster_verification_campaign.md) lines 55–73 call INIT-01–03
source-complete. The authoritative [backlog](backlog_matrix.md) line 85 keeps
INIT-02 Open because automatic EV/PUM1 maintained-study selection is absent.
The [Quickstart](../../quickstart.md) lines 94–109 still passes an explicit
`--partition-manifest`; [onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 695–704 and 1104–1119 accepts that path. Thus explicit-manifest behavior
is real, while the selected automatic experience is not complete. The campaign
itself acknowledges the gap at lines 149–150. The current summary claim is
the mismatch; INIT-02 status and explicit-manifest evidence remain distinct.
Without that flag, onboarding lines 1027–1061 asks for regions/FASTA names or
refuses missing noninteractive input; lines 1114–1143 load a partition file
only when its path was supplied. The direct guided source test at
`tests/orchestration/run_coordinator/test_onboarding.py:1492–1530` passes the
flag and checks preview, so it establishes explicit admission, not automatic
study selection. CV-U20 at CV backlog 1323–1329 and CV-06 at 2505–2511
accurately describe the *selected* Quickstart file. The overclaim is the
grouped source-complete/Verification-pending summary, not every dated CV card.

### F04 — Root Quickstart description

The [root README](../../README.md) lines 65–70 says Quickstart provides a
synthetic first Run. [Quickstart](../../quickstart.md) lines 1–15 starts with
the real six-library EV/PUM1 study, and lines 74–75 offers the
[smoke test](../operations/SMOKE_TEST.md) as optional. A first-time reader is
sent to the correct link but given the wrong expectation. The real-study
journey and optional smoke path are distinct reader routes.
The rest of the Quickstart checks a real EV/PUM1 Run and reports at lines
188–251. The [documentation index](../README.md) lines 8 and 18 also routes
first-time readers there. The named EV/PUM1 choices are the selected real
study, not universal defaults; synthetic practice has a separate optional
smoke guide.

### F05 — Generic study versus named EV/PUM1 route

At baseline `3a672fdf`, the [Runbook](../operations/RUNBOOK.md) lines 280–293
called the EV/PUM1 Quickstart the path for “your own study” and “your own data.” Quickstart lines
77–115 supplies particular sample assignments, comparison, target change,
thresholds, and a primary-contig manifest. The [configuration guide](../../configs/README.md)
lines 31–124 and 144–215 explains generic Project choices. Carrying the
named study’s choices into unrelated data is a plausible reader risk, not an
observed misuse. Generic choice guidance is in the configuration guide;
EV/PUM1 is a named-study example.
That handoff occurred in both baseline Runbook routes: standalone host (280–286)
and “own data” (289–301). Quickstart lines 83–115 fixes six
sample assignments, `reverse` strand, `EV -> PUM1`, `A>G`, thresholds, and
the primary-contig manifest; its title and opening identify the named study.
The [configuration guide](../../configs/README.md) lines 62–63 explicitly
says to replace example paths, conditions, reference, and thresholds, and
lines 144–215 defines generic sample/partition manifests. The authored study
choices and generic manifest contracts remain distinct from the named
Quickstart command. No generic scientific defaults or completed
new-study journey are established by these documents alone.

At pinned revision `0cb5d507`, the Runbook distinguishes generic choices at
lines 288–294, but lines 295–296 direct every new study to Quickstart steps
4–7. Those steps use `Projects/pum1-study` (Quickstart lines 126–132) and
describe Slurm submission (lines 161–174). The Runbook's direct-host route at
lines 280–284 and general Project commands at 385–418 show why this is not a
literal continuation for every study. The finding remains a reader-route
ambiguity; no user journey or command was exercised.

### F06 — Existing Project and new Project recovery

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 100–107 opens one
paragraph by telling readers to enter a directory containing `project.yaml`
or supply `--project`, then describes Init, whose child must be absent. Both
instructions have valid but different preconditions. Existing-Project lookup
and failed new-Project preview/creation remain distinct, as do the
no-adoption and no-symlink rules.
The [selector](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 270–285 reads the current directory or one supplied Project path;
named Init at lines 1261–1269 instead chooses an absent child beneath the
saved Projects home or current directory. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 135–149 says a failed publication preserves a partial root and never
adopts it. “Enter the Project” applies to existing-Project lookup, not
missing-child Init recovery.

### F07 — Doctor repair does not always install

The [Runbook](../operations/RUNBOOK.md) lines 545–547 uses installation
shorthand in a first Slurm setup route, then explicitly distinguishes
verification-only plans at 660–665. The
[reporting decision](../design/decisions/execution-evidence-and-reporting.md)
lines 44–53 and [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 164–166 describe Slurm repair as installation without that qualifier.
The coordinator contract at 217–233 distinguishes a repair plan from a
verification-only plan. A direct Doctor source test at
`tests/orchestration/run_coordinator/test_doctor.py:2956–2960,3046–3054`
expects no native/R installation when a ready Slurm runtime is rechecked.
Possible package-manager work, preview, and head-node versus compute-side
checks remain distinct effects across these guides and the decision.
The decision at lines 44–50 additionally names `uv` among Doctor's
installation delegates. The [root README](../../README.md) lines 53–56 and
[Runbook](../operations/RUNBOOK.md) lines 258–263 assign Doctor Project-owned
native/R work through Pixi and `renv`, with Python dependencies left to
separate package-manager setup. Doctor's manager calls (`doctor.py:1235–1265`)
use Pixi and Rscript, not `uv`; the decision overstates its Python authority.
Verification-only means no package-manager work, not necessarily a read-only
operation. A ready runtime produces a plan with `runtime=None`
(`doctor.py:835–870`), but confirmed Slurm repair/verification opens a
maintenance log (`doctor.py:1657–1676`) and calls compute-side qualification
(`doctor.py:1902–1908`). The source test at `test_doctor.py:2956–2963,3046–3054`
expects a submitted qualification job while asserting no native/R installation.
The [Troubleshooting](../operations/TROUBLESHOOTING.md) heading at 171 labels
qualification failure “after installation,” obscuring the verification-only route.
Plain diagnosis and declined preview remain no-write (`doctor.py:2089–2119`);
ready direct execution returns without a repair plan. Describe both the
possible Pixi/renv work and separate verification effects; manager output
establishes whether packages were reused or changed. Neither readiness nor
this fixture proves real-study performance or scientific validity.

### F08 — `--version` and local `.env`

The [Runbook](../operations/RUNBOOK.md) lines 184–188 promises
`emrys --version` from any directory. The [CLI](../../src/emrys/__main__.py)
lines 349–368 reads `.env` before version dispatch; the
[environment loader](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 153–185 can reject a malformed marked file or non-regular `.env` in the
working directory or an ancestor before its marker check. This is source
inference, not a reproduced failure.
`main` returns exit 2 at lines 352–356 before building the parser; the version
branch cannot run for that input if the package imports successfully. An unmarked
regular `.env` is skipped at loader lines 168–169.
`tests/test_public_cli_contracts.py`
lines 713–734 covers version from a clean temporary directory; the malformed
`.env` test at `tests/orchestration/run_coordinator/test_onboarding.py:267–281`
does not combine that file with `--version`. Source order identifies the
guard, while exact installed-command output remains unobserved.
At audit-only commit `d977e055`, a local attempt bound `PYTHONPATH` to this
source and compared clean and malformed marked `.env` directories. Both
commands failed during import because the available Python lacks `jsonschema`;
the CLI/environment branch was never reached. This is an environment limit,
not confirmation or refutation of the documented behavior.

### F09 — Runbook entry order

**Dismissed for DOCS-01 at `d84a8c41`.** The
[Runbook](../operations/RUNBOOK.md) opens with its evidence and owner boundary
at 1–7, then puts request/watch/stop procedures at 9–163 before setup at
164–188. The [root README](../../README.md) lines 67–70 and
[docs index](../README.md) lines 8–9 route operators here. The procedures
serve returning operators; no reader failure or useful reduction from changing
their order is established.

### F10 — Contract-location claim

[Docs index](../README.md) lines 3–4 says each component has a `CONTRACT.md`;
[owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md) lines 7–8
makes a similar adjacent-file claim. [DECISIONS](../design/DECISIONS.md) lines
13–14 routes exact behavior to the applicable owner `CONTRACT.md`, schema and
tests; “applicable” is less categorical but overlooks README-only owners.
The [architecture](../architecture/ARCHITECTURE.md) lines 6–7 and
[tests index](../../tests/README.md) lines 3–4 use “contract” more broadly.
Runtime-availability and reporting owners use READMEs; schema owners use
schemas. At the pinned revision, 62 source README locations had only 15
adjacent `CONTRACT.md` files; 47 README directories lack one, although not all
62 are functional owners. The narrower [stage-owner index](../../src/emrys/stages/README.md)
lines 3–5 correctly points its ten owners to adjacent contracts. The two
explicit filename promises conflict with mixed owner forms; the decision route
is incomplete, but no empty contract is implied. The inventory's later
generic “adjacent contract” and the architecture/test conceptual usage do not
promise that filename.

### F11 — Python hook scope

[Engineering conventions](../operations/ENGINEERING_CONVENTIONS.md) lines 71–74
lists staged Python under `scripts`, `src/emrys`, and `tests`.
[Hook configuration](../../.pre-commit-config.yaml) lines 5–16 also includes
root `setup.py` for Ruff check and format. The prose omits that file; other
possible exclusions were not assessed. The hook file is the executable scope;
this audit did not run it.

### F12 — Init preview proposal

[Polish campaign](polish-campaign.md) lines 313–327 says the September 7 Init
preview showed only destination, directories and no-copy policy. Current
[onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py) lines
1208–1256 shows strand summary, comparison, target, thresholds, background and
STAR values normally; GTF and per-sample detail need `--verbose`. Direct
[source tests](../../tests/orchestration/run_coordinator/test_onboarding.py)
at 327–375 check no-write preview and selected fields; 558–664 compare reviewed
comparison, target, thresholds and background with published values. The full
requested field set and full agreement are not established by those fixtures:
onboarding previews automatic `sjdb_overhang` at 1302–1312, then resolves STAR
values after FASTQ reading at 1332–1347 before publication at 1383–1391.
Those values intentionally differ between preview and created bytes. The dated
proposal is partly addressed; suggestions are not universal scientific truth.

### F13 — Doctor profile proposal

[Polish campaign](polish-campaign.md) lines 329–339 says Doctor had no profile
selector at its dated audit. [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py)
lines 1976–1982 accepts `--profile`, and the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 729–742 describes default, named, and absolute selection. A focused
source test at `tests/orchestration/run_coordinator/test_doctor.py:464–515`
covers the path. The old proposal predates current selection; remaining
acceptance is governed by the backlog and exact validation evidence.

### F14 — Old source-attestation cost candidate

[Optimization campaign](optimization_campaign.md) lines 17–24 pins its audit
to `fdf7676` and requires recheck. Its task-entry candidate at 269–290
counted 24 Git subprocess calls per task then; lines 280–287 also ask a future
selector to measure Git invocations and preserve changed-HEAD detection.
Those are revision-bound prompts, not measured latency or current requirements.
At local audit head `1eb562f0`, [source authority](../../src/emrys/libraries/source_authority.py)
lines 68–125 uses installed package bytes and build metadata, not Git. The
normal [task-entry path](../../src/emrys/orchestration/run_coordinator/task.py)
calls `admit_origins()` at 2561, 2651, 2662, and 2676 before producer entry.
The shared helper at 1861–1898 observes the installed package; its identity
routine uses [`installed_python_package_identity`](../../src/emrys/libraries/installed_package_identity.py)
at 286–293 to traverse package bytes. No current task-entry attestation
invokes Git. [Build metadata](../../setup.py) at 17–40 and source authority
91–123 allow absent Git commits; the old exact-commit/HEAD rule is not policy.
Keep the dated 24-call observation. A private six-line sketch of the
11-line future-selection paragraph suggests five local lines after removing
stale Git advice; no net saving is verified. Four package observations have
unmeasured cost/necessity; preserve installed-byte and build-origin guards.

### F15 — CV-U22 interim status prose

**Dismissed for DOCS-01 at `1db7a88d`.** The
[CV backlog](cluster_verification_backlog.md) lines 1472–1511 retains the
September 17 reopening, September 18 known-smoke correction, and still-open
general donor requirement. That sequence explains CV-U22's Open status. No reader
conflict or useful reduction was found; retain the causal record and status.

### F16 — Polish merged-PR tables

[Polish campaign](polish-campaign.md) lines 991–1025 has two merged-PR tables
spanning about 35 lines. Its first table at 998–1012 retains PR-to-slice
mappings otherwise absent from current docs; Git retains chronology but not
that convenient selection map. Four second-table rows at 1019–1022 repeat
items 22, 15, 17, and 21 at 525–535, 450–457, 469–477, and 514–523.
Those four physical lines are a review target, not verified savings. Keep the
unique #144–147 rows, CodeQL caveat at 984–989, recovery/CS-18 distinction at
1027–1032, excluded PR #44/#45 experiments at 1034–1039, and the campaign's
evidence ceiling at 35–85. The link at line 76 needs its heading preserved.

### F17 — Main backlog chronology and run repetition

**Dismissed for DOCS-01 after recheck at `31c54ed8`.**
The [main backlog](backlog_matrix.md) line 313 records 93-commit PR ancestry;
lines 343 and 349 repeat integration genealogy. These brief clauses do not
establish useful compression. Lines 305–325 retain the agreed baseline
and totals; 333–350 bind hosted evidence to revisions. Rows 354–356 cite run
`34306975901` for three distinct accepted outcomes, whose row-local proof helps
each stand alone. No useful reduction or removal of exact evidence is shown.

### F18 — History filing rule and existing compendium

[History index](../history/README.md) lines 18–22 requires
`YYYY-MM-DD-topic.md` and an originating immutable commit. Its only indexed
record, [validation evidence](../history/validation-evidence.md), has no date
in its filename and combines seven topics: PORT-NC replay (10–25), synthetic
VM/reporting (27–79), manual Viking Steps 07–09 (81–103), cohort/orientation
(104–130), local R recovery (132–139), architecture hosted CI (141–151), and
the Attempt scale probe (153–174). Several sections name exact revisions or
jobs without an explicit observation date; only the scale probe states a date
and pinned origin. The local R anecdote does not state its date or source in
the current file. Do not infer these identities from the “Dated” title.
Git traces the assembled compendium to the frozen pre-compression tree
`b9cf4767` and later additions; these commits establish document provenance,
not the date or exact installed package of a reported observation:

| Current section | Recoverable source or remaining gap |
| --- | --- |
| PORT-NC | `8901c61a:docs/history/testing/2026-08-14-port-nc-01-no-clobber-replay.md` is a frozen record dated 2026-08-14 with the integrated candidate, source-branch head, gate timings, and exclusions. It was removed from the live tree by `049dda285` but survives in Git. The compendium retains less detail. |
| Synthetic VM/report | `b9cf4767:docs/operations/HANDOFF.md` derives from `c728b593` and later report updates; it names source science and renderer revisions but no explicit VM execution date. |
| Manual Viking Steps 07–09 | The former handoff gained these records at `e69076f1` and names NORAD code `64b14a11` and jobs; its document commit date is not a job date. |
| Cohort/orientation | Earlier `docs/HANDOFF.md` at `2d5c426b` and `ec4d9d93` retains the first observation and six-value table; the former explicitly says its Step 03 job ID was not recorded. |
| Local R recovery | Former handoff text at `c239ed023` gives no exact encounter date, command transcript, or retained artifact. |
| Architecture hosted CI | `b9cf4767:docs/tasks/architecture_backlog_matrix.md` retains the ARCH-CLOSE records. The current summary omits the ARCH-CLOSE-02 CodeQL run `33640595166` and the explicit limit that the 100,000-pair lane was not selected for ARCH-CLOSE-01/02. |
| Attempt scale probe | `5511a752:docs/tasks/compression_backlog_matrix.md` is the source dated 2026-09-10; that date identifies the record, not independently the probe execution. |

The current file was created at `fe9f99a5d` and appended with architecture
CI at `13983b0f` before the current record rule was restored; the scale-probe
append at `550b5402` followed that rule. The live file still conflicts with
the unchanged-record rule. Recoverable Git
sources do not make the compendium a lossless replacement: each source has
unique limits relevant to any future split or transfer.
The compendium has file-level inbound links from the docs and history indexes
and backlog (`docs/README.md:29`, `history/README.md:9`,
`backlog_matrix.md:145–150`); the coordinator contract 950–955 links the
scale-probe anchor. These four document routes plus
`scripts/documentation/validate_structure.py:14–34` and
`tests/documentation/test_validate_structure.py:17–36` are six tracked
consumers outside this audit. The path, sole fragment anchor, and all six
consumers form a coupled boundary for any authorized transfer.
Remaining observation dates, artifact identities, and semantic losses are
unresolved for a legacy exception or lossless dated records;
neither a rename nor evidence deletion is implied by the naming mismatch.
The [backlog's CV retirement condition](backlog_matrix.md) lines 145–150
explicitly names this undated compendium as the future destination for
E01–E12 and hosted/artifact records. That conflicts with the history index's
dated-file and unchanged-record rules, rather than being only a filename
oddity. Whether the legacy compendium is a documented exception or dated
records are the intended route remains undecided. No evidence is moved by
this audit.
The [campaign evidence register](cluster_verification_campaign.md) lines
90–100 says E01–E12 combine operator-supplied output with source review; raw
logs and artifacts remain with the operator. Its `f2c0149` identifies reviewed
code, not the exact installed package for every observation. Any future history
record must retain that attribution and identity gap rather than presenting
these as independently reproduced or commit-bound Viking proof. The charter's
closure conditions at lines 173–190 preserve distinct cross-document agreement
and evidence-retention requirements; the main backlog checklist supplies the
procedural sequence. Their overlap does not justify deleting either wholesale.

### F19 — Doctor experiment evidence in workflow README

[Workflow README](../../.github/workflows/README.md) lines 24–39 spends 16
physical lines on a completed Doctor experiment. [CV-26](cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads)
3949–4002 owns its artifact, trials, limits, serial decision and retirement;
the [optimization campaign](optimization_campaign.md) 302–315 retains serial
policy. Workflow lines 3–22 own current lanes, and [CI](../../.github/workflows/ci.yml)
still uploads donor/borrower measurements. No tracked Markdown link targets
the experiment heading. A six-to-eight-line route keeping that heading and
driver fact might save eight to ten local lines. The [closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
requires CV-26's exact artifact record in validation history before backlog
retirement. [Archive inspection](docs-01-discoveries-seventh.md#retained-hosted-archive-inspection-at-496846d5)
matched bytes and selected trials, but not worker checkout or site behavior.
Repository net saving and post-expiry availability remain unverified.

### F20 — Independent golden migration comparisons

**Dismissed after recheck at `65397ad9`.** [Golden README](../../tests/contract_integration/independent_contract_goldens/README.md)
lines 3–10 explains current literal oracles and their evidence ceiling. Lines
12–57 then record successive schema and renderer migrations, including exact
byte-identity comparisons. Most comparisons at lines 12–41 do not name the
predecessor revision or old/new digests in that README; later examples at
lines 43–57 name predecessor commits. Current oracle instructions and active
tests are coupled; a date-qualified comparison also needs Git, tests, exact
predecessor/current revisions, and oracle values. The prose alone is
not sufficient retained proof; golden presence is not runtime or biological
validation.
The current [golden test](../../tests/contract_integration/independent_contract_goldens/test_independent_contract_goldens.py)
lines 178–273 consumes the literal schema, header, canonical JSON, receipt,
and two HTML-digest oracles; those active checks stay beside the tests.
`git blame` at the pinned source identifies the introduction commits for the
dated prose blocks: `2fc9e68e` (lines 12–17), `ef321aa1` (19–27),
`8499b75e` (29–32), `8a75f588` (34–41), `f4435527` (43–49), and
`4c67b371` (51–57). An introduction commit is not itself the predecessor
oracle or proof of a byte comparison; old/new literal values and retained
check results remain missing from a qualified history transfer.
At pinned audit revision `b3af5d9e`, a read-only Git comparison of the literal
`report_html.sha256` file with each introduction commit's parent found the
scientific digest unchanged across `2fc9e68e`, `8499b75e`, `f4435527`, and
`4c67b371`, and changed at `ef321aa1` and `8a75f588` where the prose describes
rendering or link changes. This supports the stated fixture lineage, not an
independent renderer replay or proof of the original HTML comparison. No useful DOCS-01 reduction is established.

### F21 — Coordinator contract's no-write section

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
has one 632-line `No-write and publication boundaries` section (87–718)
without subheadings. Init prompts/publication (89–150) differ from hashing and
input stability (184–215); watch selection (56–67) differs from dated view,
refresh, and action (557–681). This is navigation pressure, not proven
deletable duplication; any size disposition remains with SIZE-01.

Section map: Init preview/publication 89–151; Validate/Doctor 153–182; Init
continuity 184–215; Doctor plans/timing 217–287; managed runtime 299–339;
Run/Slurm planning 365–409; submission request 410–468; request/Run inspection
470–556; watch diagnostics 557–681; exact-request stop 682–717. These rules
have distinct refusals and evidence levels. The coordinator
[README](../../src/emrys/orchestration/run_coordinator/README.md) 68–71 and
[Runbook](../operations/RUNBOOK.md) 34–37, 117–119, and 420–423 send
request/watch readers to the later Results/recovery section (1141–1223).
Stop and Init links at Runbook 161 and 310–312 correctly target no-write.
The later section is a separate Run/Task/Results authority; sentences about
both boundaries need both routes. No safe deletion is established.

At local audit head `db2d2b0b`, the [configuration guide](../../configs/README.md)
346–350 calls its link a “command-construction contract” for native controls,
derivation, and minimum budgets. It resolves to planning at line 719, about
140 lines before those rules at 859, with no nearer heading. This is a valid
link with imprecise routing, not a saving. Retain limits, overhead caveat, and
the immutable-plan boundary.

### F22 — Coordinator cross-owner detail

**Dismissed after recheck at `a3b741bb`.**
The [coordinator README](../../src/emrys/orchestration/run_coordinator/README.md)
lines 45–56 summarizes setup/site, repair, shared-generation, Slurm
qualification, and profile rules already held by the contract at 69–99,
153–174, 313–339, and 729–749. Its responsibility table at 31–41 and owner
links remain distinct; 12 lines are a review span, not a saving. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 236–287 owns Doctor timing; the
[logging contract](../design/LOGGING_CONTRACT.md) lines 172–189 owns event
shape and flushing. Coordinator runtime orchestration at 326–339 overlaps the
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md)
lines 85–104 on replacement, selectors, and fixed-content limits. The
[Runbook](../operations/RUNBOOK.md) lines 643–654 repeats that lifecycle but
owns operator commands; coordinator 313–325 owns cross-Project publication,
prompts and output, while runtime owner 70–83 owns seal/selector formats.
Watch keys at contract 622–624 also appear in Runbook 96–104; presentation
289–297 overlaps the [logging owner](../../src/emrys/libraries/application_logging/README.md)
at 13–17. The contract adds prompt/default hints, `NAME=value`, mouse and
sanitized evidence-view rules. These summaries serve distinct command,
runtime-admission, logging, and operator boundaries; no saving is established.
At pinned revision `b65e8fb8`, the [logging contract](../design/LOGGING_CONTRACT.md)
lines 191–235 also repeats current/legacy Slurm request and stream names and
stop-intent details from coordinator lines 410–429, 461–468, and 691–698.
The logging contract describes pre-mutation log sync, event fields, redaction,
and association event and diagnostic limits; the coordinator owns request
admission, the association reader, scheduler transport, and cancellation.
The compatibility names and diagnostic limits have distinct readers, so this
additional overlap establishes no safe saving.

### F23 — Init details in the Runbook

At baseline `3a672fdf`, [Runbook](../operations/RUNBOOK.md) lines 303–335 mixed useful Init
choices and safe prompts with exact hashing, inode, STAR derivation, and
publication mechanics also covered by the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
and [config guide](../../configs/README.md). Operator choices, observations,
and interruption cautions remain distinct from exact mechanics. In particular,
preview does not hash FASTQ contents and creation can refuse changed inputs.

At pinned revision `0cb5d507`, the approved Runbook slice removed 75 lines and added
35. Its shorter own-study section retains preview, confirmation, changed-input
and destination cautions while linking exact mechanics to the config guide and
coordinator contract. This records a PR-local documentation change, not audit
closure or proof of a generic end-to-end reader journey; F05 remains open.

### F24 — Named-profile procedure placement

**Dismissed for DOCS-01 at `1db7a88d`.** The
[config guide](../../configs/README.md) lines 239–279 owns named-profile
preview, creation and selection; lines 281–340 explain its fields. The
[Runbook](../operations/RUNBOOK.md) links that route at 532–536 and retains
the separate head-node Doctor/Run and advanced placement paths at 557–565.
The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 828–837 owns exact admission and no-write behavior. Both Runbook
anchors serve distinct readers. No duplicate procedure or useful saving was
found; preserve the inbound link.

### F25 — Reporting decision versus migration history

**Whole-section reduction dismissed at `35cbe2a1`; lines 216–225 reopened
at `99fe2d5a`.** The [targeted rescreen](docs-01-discoveries-seventh.md#reporting-history-rescreen-for-f25)
is conditional; the surrounding compatibility and recovery rules remain.

[Execution, evidence, and reporting decision](../design/decisions/execution-evidence-and-reporting.md)
lines 119–209 and 227–257 retains scientific-fingerprint, independent-test,
create-only, recovery and old-Run compatibility decisions; the
[reporting owner](../../src/emrys/reporting/README.md) owns mechanics. Lines
210–214 cite PR #146's `0ece377ca2b285d6ec2a46f7d2441c78f16409e1`
predecessor tree, which still contains `report.py`; later `053f4130` removes
the facade. The failure and nondeletion limit matter to [history's](../history/README.md)
rules. Retired symbols at 216–218 and 223–225, including
`ReceiptValidationOps` and `RunSummaryBuildDeps`, occur only here in current
Markdown. The logical `emrys.reporting.report` producer still has compatibility
meaning in `_run_report/README.md:31–36` and `models.py:19`; surviving callbacks
and combined index/summary publication have current owners. No inbound Markdown
link targets this heading, but that does not establish a safe deletion.

### F26 — Alpha carrier note in reporting README

**Dismissed after recheck at `a3b741bb`.**
[Reporting README](../../src/emrys/reporting/README.md) lines 22–27 says an
approved alpha cleanup changed the carrier and retired an alias, then gives
the current field/callable shape. That is the only explicit collaborator
reporter API guidance found in this pass; the current carrier is in
`src/emrys/reporting/__init__.py:24–63`, with a built-in provider caller in
`src/emrys/reporting/paired_cmh_candidate_ranking_report/provider.py:32–33`.
This is a five-line passage; deleting its historical opening alone saves little.
Its actionable snapshot paths, types, and positional guidance are current API
content. No standalone compression is selected by this observation.

### F27 — Old fixed-resource provenance

**Dismissed after recheck at `f67410cb`.** The
[resource defaults owner](../../src/emrys/orchestration/run_coordinator/resources/README.md)
lines 14–17 names the old fixed-policy commits `92863824` and `d6e54aff`
and says that policy is neither current, a restoration target, nor a required
benchmark baseline. The [CV-U28 card](cluster_verification_backlog.md#cv-u28-allocation-aware-resource-policy-and-historical-provenance)
at 1766–1779 has richer origin history; 1847–1861 records supersession with
institutional admission pending. That temporary card cannot replace the
durable owner's current negative boundary. Its other resource rules and
capacity-versus-utilization limit remain at 3–12 and 18–26. Four lines of
overlap establish no useful DOCS-01 net reduction or speedup conclusion.

### F28 — Repeated owner boilerplate

At `ca31d41f`, six stage test READMEs (`canonical_bam`,
`duplicate_marking`, `fasta_sidecars`, `split_n_cigar`, `star_alignment`,
`star_index`) and two evidence guides ([BAM QC](../../tests/evidence/canonical_bam_qc/README.md)
and [RSeQC](../../tests/evidence/rseqc_orientation/README.md)) each repeat the
same five lines at 5–9: 40 physical lines. Their first paragraphs retain
distinct native checks, mocked-tool limits, and historical defects.
The [test root](../../tests/README.md#evidence-limits) and
[stage index](../../tests/stages/README.md) give general limits, but omit shared
scratch/staging, publication/recovery tests, and the public validator split.
An eight-to-nine-line tests-root account plus eight two-line routes suggests
15–16 repository lines while keeping that split visible. The
[later recheck](docs-01-discoveries-seventh.md#repository-net-recheck-for-f28) includes shared text and links.

The matching six [production stage guides](../../src/emrys/stages/README.md)
repeat three execution lines each: `duplicate_marking` 10–12,
`split_n_cigar` 11–13, and the other four 12–14. The stage index at 28–40
already owns normal Run, internal workers, and grouped specialist validators;
it lacks the warning that shell `--help` describes runner-only arguments.
One to two shared index lines and six one-line owner routes suggest 10–11
repository lines, conditional on keeping both local help commands and limits.

Twelve stage/evidence/analysis contracts have a separate 24-line test-ceiling
opening. Four stand alone and might each shrink one line; eight flow into
distinct owner limits, oracles, or recovery. [Canonical BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md)
177–178 and Step 10's scientific boundary are separate. The four gross lines
are low-value and establish no useful net reduction. No guide edit, replacement
link check, or net saving occurred.

### F29 — Library subowner navigation

**Dismissed for DOCS-01 at `1db7a88d`.** The
[test library index](../../tests/libraries/README.md) lines 3–6 points to the
[production index](../../src/emrys/libraries/README.md), which lists three
shell helpers but does not route to six documented Python subowners. That is
an added-navigation question, with no duplicate prose or reduction identified.
Preserve the source-topology boundary and existing subowner guides.
