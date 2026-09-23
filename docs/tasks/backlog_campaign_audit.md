# Backlog and campaign audit — working draft

Baseline: `codex/pr302-original-intent-corrections` at
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d` (2026-09-22).

This is a source-bound review record for finding stale claims, duplicate
planning, and historical material in EMRYS's task documents. It is not another
backlog or an approval to change a card. The [main matrix](backlog_matrix.md)
owns accepted outcomes, statuses, and acceptance; it delegates the CV cards to
the [cluster backlog](cluster_verification_backlog.md). The
[cluster charter](cluster_verification_campaign.md) owns campaign scope and
E01–E12. The [polish](polish-campaign.md) and
[optimization](optimization_campaign.md) campaigns contain proposals and
audit observations, not additional task-status authorities.

The review compares wording at the named commit with its original outcome,
current source and tests, operator guidance, and retained evidence. A changed
source blob flags a question to recheck; it does not invalidate a dated
observation. Hosted checks, disposable Slurm, institutional Viking execution,
scientific review, and biological interpretation remain different claims.
Documentation-only changes here supply no new runtime, site, performance, or
scientific evidence for campaign acceptance.

## Coverage and method

| Document | Scope at baseline | Role in this audit |
| --- | --- | --- |
| [Main matrix](backlog_matrix.md) | 392 lines; 51 rows | Accepted outcomes, current status, acceptance, and closure. |
| [Cluster backlog](cluster_verification_backlog.md) | 4,107 lines; 61 CV/CV-U/CV-UX cards | Delegated card status and acceptance. |
| [Cluster charter](cluster_verification_campaign.md) | 210 lines | Scope, E01–E12, and closure criteria. |
| [Optimization campaign](optimization_campaign.md) | 458 lines; 13 candidate discussions | Measurements and proposals to recheck against current source. |
| [Polish campaign](polish-campaign.md) | 1,084 lines; 44 numbered findings and five architecture options | Proposals and earlier audit rationale to reconcile with accepted rows. |
| [Task index](README.md) | 21 lines | Navigation and owner boundaries. |

The six files total 6,272 lines. These counts describe review scope, not
completion or quality. For every accepted row or proposal, record its original
outcome, current owner, live behavior, direct checks, evidence ceiling, and
whether the text is a current obligation, lasting decision, exact evidence,
useful proposal, or Git-only chronology. Inspect affected links in the rest of
the repository before changing a destination or heading. A completed audit
must reconcile the matrix, both CV indexes, detailed cards, charter, owner
guidance, and any transferred acceptance; it cannot infer completeness from a
status label or a passing suite alone.
Line numbers in this working record refer to the named baseline unless an
entry explicitly says otherwise; later wording corrections can shift them.

The 51 main-matrix rows are accounted for across maintainability/release
(seven), novice follow-up (nine), deferred operation (two), reliability
(seven), platform/portability (eleven), science (two), reporting (five), and
completed/closed outcomes (eight). Their index labels total 19 Open, 15
Verification pending, nine Completed, six Deferred, one Closed, and one Needs
decision. The following source spot checks support retaining the rows; they
do not constitute complete implementation or site acceptance.

| Row | Source and direct-check discovery | Next boundary |
| --- | --- | --- |
| `REFERENCE-INPUT-01` | The shared [FASTA parser](../../src/emrys/libraries/references/contigs.py) line 31 indexes an empty header token; its [test](../../tests/libraries/test_reference_contigs.py) lines 98–102 expects the resulting raw `IndexError`, while onboarding, alignment, and stage callers catch `ReferenceContigError`. | Correct the parser and characterized test together if implementation is selected; retain valid names/order and normal diagnostics. |
| `FUT-INDEX-01` | The [reference schema](../../src/emrys/contracts/schemas/orchestration/v1/reference.schema.json) admits FASTA/GTF and construction parameters, not an external index. The standalone [index validator](../../src/emrys/stages/star_index/validator.py) checks required members, reference identity, and parameters but is not Project admission. | Keep Open; bind exact member hashes, STAR identity, and immutable planning before claiming reuse. |
| `REPORT-ROSTER-01` | The generic [artifact inspector](../../src/emrys/reporting/_artifact_index/inspection.py) checks safe, unique IDs but not exact order/membership. Its [mutation test](../../tests/reporting/test_artifact_adapters.py) lines 585–604 documents that reordered or wrong unique IDs still mark an artifact complete. Step 09's module-specific reporter and an independent roster oracle provide narrower protections. | Preserve `Needs decision` pending its definition and owner choice; do not call every report validator defective or delete independent oracles. |
| `SCRATCH-01` | Quickstart requests Viking `/tmp`; the [Runbook](../operations/RUNBOOK.md#temporary-files) distinguishes batch, Doctor, and Task scratch and requires actual-host permissions/capacity/lifetime verification. The batch wrapper has source-level parent checks. | Keep Verification pending for site evidence; do not infer suitability from the configured path or a local fixture. |

## Findings matrix

Finding numbers identify review questions within this temporary record. They
are not backlog IDs or a second task-status list. Each row has an initial
discovery below and names the next evidence needed before changing authority.

| Finding | Baseline discovery | Next verification or disposition |
| --- | --- | --- |
| 1. Status vocabulary and placement | The baseline matrix left `Needs decision` undefined, the delegated backlog used `Discard`, and two Completed rows sat under Active backlog. | Both terms are now defined narrowly; the completed rows moved without status or acceptance changes. |
| 2. `INIT-02` and dependent onboarding claims | Automatic maintained-study selection is Open, but CV summaries call `INIT-01`–`INIT-03` source-complete. Quickstart supplies a manifest path explicitly. | Present-tense summaries are corrected in this branch. Review CV-06, CV-U08, CV-U20, and CV-U21 against their own acceptance before any status change. |
| 3. `CV-U22` runtime reuse | The card remains Open for compatible-donor discovery before installation; the documented known-smoke route is narrower. | Retain Open and the no-silent-donor rule; distinguish known-smoke evidence from the undecided general selection design. |
| 4. `CV-26` Doctor cost | One redundant full diagnosis was removed; original complete-operation attribution and comparable measurements remain Open. | Separate exact retained measurements and the serial-probe decision from implementation checkpoints and unmeasured speedup claims. |
| 5. Dashboard retirement | The matrix says the standalone entry point and callers are retired; several CV summaries still say that retirement remains. | Current-sounding text is corrected in this branch; keep shared watch code, historical readers, and pending visual verification. |
| 6. Repeated cluster closure instructions | The main checklist, cluster backlog summary, and charter repeat remaining work. | The charter now links to the operative sequence while retaining its unique disposition, site-combination, and evidence custody rules. |
| 7. Viking walkthrough chronology | The main matrix holds dated jobs, a qualification identity, capacity observations, approvals, and a last-supplied Run state. | The [dated record](../history/2026-09-14-viking-walkthrough.md) now preserves source-only journey and safety details; settle the allocation-account evidence need and owner homes before any shortening. |
| 8. Compression closeout chronology | The completed section combines the user closure, quantified shortfall, exact CI, and PR chronology. | The [dated record](../history/2026-09-14-compression-closeout.md) matches material source decisions and evidence limits; retain the closure decision and request separate authority before shortening source evidence. |
| 9. CV card checkpoint narratives | Detailed cards repeatedly recount Open-to-implemented-to-pending transitions alongside live acceptance. | The 61-card first pass and CI wording correction are recorded below; transfer exact observations and decisions before any shortening. |
| 10. Polish chronology and overlap | The campaign contains an old audit/PR narrative and merged-PR tables plus proposals already implemented elsewhere. | The [retention map](polish_finding_disposition_review.md#polish-audit-and-pr-chronology-retention-map) separates Git-only chronology candidates from unique decisions and evidence; transfer checks remain before compression. |
| 11. Optimization source drift | The September 7 audit is correctly pinned, but most cited source blobs changed by the baseline. Candidates 8 and 12 have materially changed source premises. | Re-evaluate all 13 candidates against current owners and measurements without converting old proposals into defects. |
| 12. Time-bound campaign authority | The charter repeated earlier development authority and a then-running job as present-tense guidance. | The grant and job observation are now dated; current authority and active-installation safety retain their owners. |
| 13. Polish proposals versus current owners | Several original findings describe capabilities now delivered; others retain a live gap. | The [per-item review](polish_finding_disposition_review.md) maps all 44 findings and five architecture options; item 6 is reproduced locally, item 11 has a confirmed group mismatch, and remaining decisions stay unselected. |
| 14. `HARNESS-01` status versus source gap | The row is Verification pending, yet its acceptance names a remaining test-simulation admission mismatch also visible in fixtures and production records. | Recommend Open under the matrix vocabulary, subject to fixture and retained-reader review; keep controlled simulation proof distinct from scientific execution. |

## Initial discoveries

### 1. Status vocabulary and placement

**Observed at the pinned baseline:** [Matrix operating rules](backlog_matrix.md)
at lines 24–29 defined Open, In progress, Verification pending, Deferred,
Completed, and Closed. `REPORT-ROSTER-01` used `Needs decision` at line 295.
The delegated backlog used `Discard` for CV-12 in its index at line 106 and
detailed disposition at line 3032, while its introduction referred readers to
the matrix meanings. `VIKING-POLICY-01` and `CV-DOCS-01` were Completed at
matrix lines 90–91 under `## Active backlog`; the completed section began at
line 297.

**Documentation correction:** The matrix now defines `Needs decision` as an
accepted nonterminal decision stage, with no implementation choice implied.
The delegated introduction defines `Discard` as CV-12's terminal decision to
abandon E01 causal reconstruction, not an explanation of the original failure.
The two Completed novice documentation rows moved byte-for-byte into the
completed section; their inbound links and the active-section count were
updated. No row status or acceptance changed.

### 2. `INIT-02` and dependent onboarding claims

**Observed:** [Main matrix](backlog_matrix.md) line 85 calls `INIT-02` Open:
guided Init still needs automatic selection of the maintained 25-name study
without a manifest argument. [Quickstart](../../quickstart.md) lines 97–100
explicitly pass `--partition-manifest`. The
[CV backlog](cluster_verification_backlog.md) lines 24–30 and 72 and
[charter](cluster_verification_campaign.md) lines 55–63 say all three `INIT`
source outcomes are implemented. The charter's lines 149–150 acknowledge
`INIT-02` remains incomplete. CV-06's dated correction at cluster backlog
lines 2505–2511 calls its narrower explicit-manifest route Verification pending.

**Next:** Resolve how guided Init selects and distributes the maintained study
file without a manifest path. Check no-argument selection, preserved explicit
and generic routes, missing-reference refusal, installed-package access,
exact hosted behavior, and a fresh novice Viking journey. CV-06/U08/U20/U21
retain their own acceptance and statuses.

**Source comparison:** The public Init owner in
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 1027–1055 offers a regions file or manually entered FASTA names when no
partition manifest is given; it does not choose the maintained EV/PUM1 study.
The direct test at `tests/orchestration/run_coordinator/test_onboarding.py`
lines 1505–1510 supplies the manifest path. The installed-distribution test
uses a fixture manifest. [`pyproject.toml`](../../pyproject.toml) disables
implicit package-data inclusion and lists other resources explicitly, but not
the repo-level study manifest; neither path proves its installed availability.
CV-06's original acceptance at
cluster backlog lines 2474–2484 permits either a short guided path or a
supported import, so an Open `INIT-02` does not mechanically reopen CV-06.
CV-U20 lines 1323–1329 describe the Quickstart's explicit manifest, not
automatic Init selection. CV-U08's delivered-journey claim at lines 605–619
needs the same original-intent review. CV-U21's STAR-parameter assistance is
separate from study selection; its status does not follow `INIT-02`.

**Documentation correction:** The CV backlog introduction, remaining-work
table, CV-06/CV-U08/CV-U20 passages, and charter delivery summary now name
the delivered *explicit* Quickstart `--partition-manifest` route separately
from `INIT-02`'s Open automatic-selection outcome. They retain `INIT-01` and
`INIT-03` implementation and each CV card's own remaining novice/site or
selected real-Slurm acceptance. Ordinary software checks later passed
[ordinary baseline CI 35770811692](https://github.com/lab-cats/EMRYS/actions/runs/35770811692); no card status changed.
CV-U21's generated-replay description is now historical; `INIT-03` confirms
and publishes in the same invocation.

### 3. `CV-U22` runtime reuse

**Observed:** The [CV-U22 card](cluster_verification_backlog.md) lines
1457–1463 requires discovery and validation of a compatible existing runtime
before installing. Its lines 1494–1505 record a known-smoke-project route;
lines 1507–1512 say general donor discovery remains unimplemented and retain
Open status. [Quickstart](../../quickstart.md) lines 144–158 presents reuse of
the named smoke Project when it was run, then skips the discovery command when
it was not. The public [`runtime discover`
owner](../../src/emrys/orchestration/run_coordinator/onboarding.py) lines
2268–2322 requires an explicit `--from-project` for donor reuse; without that
argument it plans discovery of the current Project's own runtime.

**Source comparison:** `_plan_runtime_reuse` validates one named donor. Without
`--from-project`, discovery inspects only the current Project; Doctor does not
search others. CV-08's named-donor reuse awaits site proof, while CV-U22 stays
Open for general compatible-donor discovery before installation.

**Next:** Resolve explicit donor choice without silently selecting tools;
retain the known-smoke route and its pending institutional acceptance.

### 4. `CV-26` Doctor cost

**Observed:** The [CV-26 card](cluster_verification_backlog.md) lines
3750–3759 requires complete Doctor attribution across phases, reads, hashes,
probes, and queue time, plus comparable before/after measurements. The main
matrix line 107 and charter lines 202–207 distinguish the completed structural
reduction from the Open original measurement outcome. The card holds exact
hosted artifacts and timing observations after line 3785; those are retained
evidence, not routine progress to delete.

**Next:** Inventory the exact revisions, artifacts, raw counters, failure
distinctions, and accepted serial-probe decision. Keep them source-bound if
later moved to [validation history](../history/validation-evidence.md). State
the remaining experiment without implying a measured speedup.

**Evidence boundary:** The card's lines 3785–3808 retain one hosted
complete-setup timing with its artifact identity and limits. Lines 4024–4056
record the five-to-four diagnosis reduction and exact CI, but neither
comparable complete-operation before/after data nor Viking speedup. The
[GitHub workflow guide](../../.github/workflows/README.md) lines 24–39 also
summarizes a serial/concurrent probe experiment whose fuller evidence and
failed-suite distinction remain in the CV card at lines 3949–3998. Use one
durable evidence record if this material moves.

### 5. Dashboard retirement

**Observed:** [Main matrix](backlog_matrix.md) line 180 says the institutional
owner accepted installed watch and the standalone wrapper/callers were retired;
new v4 streams use the current names while older names remain readable. The
[CV backlog](cluster_verification_backlog.md) line 79 and later CV-16/CV-25
checkpoint text still assign standalone retirement as future work. The
matrix's dated compression closeout at lines 330–331 says replacement still
requires validation, which described its earlier checkpoint.

**Next:** Check console entry points, current submission names, and historical
readers at the baseline. Then update current-sounding summaries while retaining
legacy-reading compatibility and the remaining standard-CI/institutional
visual verification.

**Source comparison:** [`pyproject.toml`](../../pyproject.toml) lines 39–40
exports only `emrys`; the tree contains no standalone dashboard wrapper or
Make target. [`slurm_submission.py`](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 72–78 generates `emrys-<token>` or `emrys-doctor` for current v4 requests
and retains old names for older records. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 426–435 explicitly preserves historical stream reads. Shared
`dashboard.py` remains part of installed watch, so its presence is not proof
that the old standalone entry point survives.

**Documentation correction:** The CV backlog remaining-work row and
current-sounding CV-16/CV-24/CV-25 summaries now agree with
`DASHBOARD-RETIRE-01`: standalone entry point/callers and new-name transition
are implemented. Ordinary software checks passed [ordinary baseline CI 35770811692](https://github.com/lab-cats/EMRYS/actions/runs/35770811692);
institutional visual verification remains. The matrix's compression closeout sentence is bound to September 14.
The earlier local-test limit, v1–v3 stream reads, and shared watch
parsing/rendering remain explicit. No evidence or card status changed.

### 6. Repeated cluster closure instructions

**Observed:** The [main closure checklist](backlog_matrix.md) lines 103–152
calls itself the single remaining verification and handoff sequence. The
[CV backlog](cluster_verification_backlog.md) lines 33–89 has a second
remaining-acceptance table, and the [charter](cluster_verification_campaign.md)
lines 53–86 and 152–190 repeat delivery and closure instructions. Each also
contains some distinct evidence limits.

**Documentation correction:** The [main checklist](backlog_matrix.md#cluster-verification-closure-checklist)
remains the ordered final-source, site, review and retirement sequence. The
charter's Delivery approach now links to it and CV-01 instead of restating the
selected stop/native/resume oracles; its Completion section retains the
accepted/rejected/transferred disposition rule, per-card evidence limits and
E01–E12 custody.
The three named institutional combinations and new-failure owner rule remain.
The CV backlog already links to the operative checklist and retains its exact
hosted limits, card-to-owner table, and detailed card acceptance. No evidence
record or status was removed.

### 7. Viking walkthrough chronology

**Observed:** [Main matrix](backlog_matrix.md) lines 182–276 keeps the
September 14 walkthrough, including job `614786`, storage qualification hash,
jobs `618134` and `618190`, memory/cgroup observations, a bounded product
allowance, and reported synthetic/actual-data states. The
[charter register](cluster_verification_campaign.md) lines 104–117 summarizes
E01–E12 but does not replace every exact identifier or approval in the matrix.

**Source comparison:** A read-only comparison of the
[additive dated record](../history/2026-09-14-viking-walkthrough.md) with the
matrix and charter found source-only setup, interface, output, and memory-safety
details, now added to the record above. The record names the source commits
and exact identities below; it is a preservation draft, not a completed removal
gate. Keep current site acceptance in
`SITE-PARITY-01`/`CLUSTER-VERIFY-01`, lasting policy with its owner, and exact
observations with their evidence ceiling. Do not infer actual-data completion
from a last-supplied state.

**Preservation map:** Before shortening either source, an additive dated record
must retain these distinct facts and their original source commits:

| Current source | Unique identity, decision, or limit to retain |
| --- | --- |
| Matrix walkthrough opening | Selected `7c427f0c`; job `614786`, 71 restored R packages/600 seconds, qualification identity `cfcf7f788fd9d949f1a23f17793ecf22ba1e05f1023bc3b49065eebc0280186f`, receipt location, and manually submitted setup limit. |
| Matrix opening and journey decisions | Initial operator report of successful fresh installation and synthetic Project validation; both `--site viking` Project-creation commands write the default profile used by Run/resume/standalone reporting. Preserve Quickstart reconnect/recovery, phase timing, plain redirected output, and complete package output beside the maintenance log. The dated record now states these details; current behavior still belongs to its owners. |
| Matrix implementation allowance | Earlier 750-net-product-line ceiling, no new product files/receipt formats, Rich selection, and separate surface accounting; this is dated authority, not a current grant. |
| Matrix memory sequence | Job `605171` request/accounting, observer `c52178d2`, repair job `618134`, diagnostic job `618190` on `node009`, missing Slurm memory fields/cgroup limit, approved process-visible-RAM fallback, and science-pending limit. Preserve the no-forged-scheduler-values/no-enlarged-allocation guard and the initial request for an actual Run diagnostic; the later fallback followed Doctor diagnostics without proving an actual Run. The existing history entry for job `605171` concerns NORAD manual Step 08 and does not transfer this E02 observation. |
| Matrix execution sequence | Username-lookup failure and failed Attempt; reported synthetic resume with 151 artifacts/3:52 and deferred HTML review; cancelled actual-data Run without terminal receipt; replacement Run active at last observation. Keep charter E03/E04/E08/E09/E12 distinctions. |
| Matrix hosted journey | `e25b10c6` and CI `34885186045` cover a disposable-Slurm Doctor preparation path, not Viking qualification; the six-library profile is no requirement for that tiny fixture. |
| Charter E register | E05 pre-Run/foreign-host observations, E06 unknown report-publication cause, E07 unmeasured hashing cost, E10 heterogeneous capacity figures, E11 unattributed Doctor time, plus E01/E09/E12 unknown or absent outcomes. The additive history record now preserves these with their source limits for review. |

The [history rules](../history/README.md) require source provenance and one
topic-index link; [validation history](../history/validation-evidence.md)
now links the dated record. The source matrix's allocation account identifier
is deliberately not repeated; any later source reduction must settle whether
it is required evidence. The new record does not transfer authority or delete
exact evidence from the original matrix and charter.

### 8. Compression closeout chronology

**Observed:** The [main matrix closeout](backlog_matrix.md#completed-and-closed-outcomes)
contains the explicit user closure of `COMPRESS-01`, its 484-line shortfall
against the agreed 20% target, two different comparison baselines, a seven-surface net
table, exact CI links, and PR integration chronology. The closure decision and
measurement definitions remain material; Git already keeps routine PR order.

**Source comparison:** The [additive dated record](../history/2026-09-14-compression-closeout.md)
preserves the material closure decision, counts, comparison definitions, exact
CI heads, and evidence limits from the matrix snapshot. A read-only comparison
found no material omission. Keep the user decision in the row. The old dashboard
statement is now date-bound to its September 14 checkpoint; the matrix's
original evidence remains in place. Any source-evidence removal remains a
separate approval and commit decision.

**Preservation check:** The Closed row records 42 completed CS cards, with
CS-05 transferred to `REPORT-ROSTER-01`, after PR #169 merged as `2ecf7d44`.
The agreed `cab77a2610cecbefaaf0fb463fa7ebe1c500767c` campaign baseline
counts tracked `.py`, `.R`, `.sh`, `.css`, `.j2`, and `Snakefile` product lines,
including relocations but excluding generated `renv/activate.R` and tooling
`restore_r_environment.R`. It fell from 69,223 to 55,862 lines: 13,361 fewer,
or 19.30%, versus a 55,378-line target. The explicit closure was 484 lines
short. The separate pre-integration-master comparison at
`446802c06ebceee8328a5cb4b542eea9fb2ed398` found product −13,480
(19.44%), tests/fixtures −12,699, docs +802, schemas/config −2,243,
tooling +284, generated/dependency +106, retained evidence 0, and total
−27,230. These baselines answer different questions and must remain labeled.

The matrix records ordinary hosted CI run `34857271894` and 130-pair synthetic
E2E run `34857300341` at `fdc7cc79a3cf8637bb1c591c95a82020816fe863`;
that commit and merge `2ecf7d44` have equal Git trees. Earlier ordinary runs
`34306975901` at `b491aac5` and `34301289787` on PR #140's integrated tree
support narrower hosted claims. This audit verified the Git identities/tree
relationship, arithmetic, and GitHub's run-level success/head metadata, not
every selected job or artifact independently. None of
those results establishes institutional execution, scientific review, or
biological interpretation. Routine sequencing of 93 commits across PR #140,
PRs #148–168, and merge #169 is held by Git; the user closure, count rules,
exact checks, and evidence ceiling require a durable evidence home before any
closeout shortening. The closeout figures entered the matrix in
`550b5402506730e8605dc96db48aaa86c400e3ed` on 2026-09-14.

### 9. CV card checkpoint narratives

**Observed:** The [cluster backlog](cluster_verification_backlog.md) held 4,107
lines at the named baseline. CV-U06, CV-U22, CV-U28, CV-10, and CV-26 include dated implementation,
adversarial-review, and verification checkpoints before their current
disposition. The CV-26 record after line 3785 and CV-U28 historical resource
reconstruction after line 1760 contain unique evidence or decisions. A simple
deletion by age would lose that support.

**Next:** Use the [61-card retention ledger](cv_card_retention_review.md) to
transfer exact observations and decisions before proposing specific reductions.
Keep current acceptance with each card and unknown causes unknown. This first
pass authorizes no removal.

**Index sweep:** All 61 card IDs occur once in both indexes and once as a
detailed heading. The current index labels are 52 Verification pending, four
Completed, two Open, two Deferred, and one Discard. Comparing each index label
with the card's final disposition found no additional status conflict; dated
earlier Open checkpoints must not be mistaken for the last disposition. This
is a coverage check, not independent proof that the 52 implementations satisfy
their original outcomes. In particular, `CV-U22` and `CV-26` intentionally
remain Open, and CV-12's Discard preserves E01 as unexplained. CV-21 dropped
E06 causal reconstruction while retaining current reporting truthfulness and
site acceptance. The four Completed cards are scoped outcomes, not campaign
closure or Viking qualification.

| Evidence-bearing region in the [CV backlog](cluster_verification_backlog.md) | Preserve before shortening |
| --- | --- |
| CV-10, lines 2740–2752, 2789–2803, and 2920–2985 | Strict prepared-finalization acceptance; job `621154` TIMEOUT, lock/no-receipt/no-recovery observation; exact CI/artifact hashes; the failed first-suite distinction; prepared recovery boundary; and accepted equal-byte recycled-inode limitation. |
| CV-26, lines 3754–3763, 3789–3829, and 3949–4056 | Original complete-operation attribution and comparable-measurement acceptance; bounded 175.681-second hosted setup; four trial measurements and artifact identity/hash; failed prototype-suite distinction; serial-probe decision; and five-to-four structural reduction without a measured whole-operation or Viking speedup. |
| CV-U06, lines 512–533; CV-U28, lines 1749–1785 and 1847–1861 | Product-growth exception, historical resource provenance, operator-reported eight/four-hour comparison, superseding allocation policy, and explicit lack of utilization proof. |
| CV-U22, lines 1446–1517 | Original general compatible-donor discovery and reuse-before-install outcome; the September 17 source-gap finding; the narrower known-smoke repair and restored API; and final Open/no-silent-choice boundary. Its earlier implemented/Verification-pending checkpoint does not set current status. |
| CV-UX-01, lines 2122–2154 | Operator-observed terminal collision on job `621172`, current color/plain/narrow-PTY acceptance, and later Viking visual limit. Preserve the reported observation separately from local terminal-helper checks. |
| CV-23, lines 3601–3625; CV-21, lines 3537–3545 | No presently provable deletable candidate class, and the decision to stop causal reconstruction of E06 while preserving truthful current reporting. |
| [Charter](cluster_verification_campaign.md), lines 104–117 | E01–E12 observations and their limits, including unknown E01/E06 causes, E09's missing terminal recovery evidence, and E12's missing terminal actual-data result. |

CV-01's selected 130-pair disposable-Slurm journey still needs the exact
hosted and site proof named in its card (cluster backlog lines 2259–2295).
CV-10 and CV-18 now cite ordinary hosted software checks at
`2f4a0313050ba254c273b480d9913e0b82fa7a7e` and the integrated baseline;
the selected real synthetic E2E job was skipped in both runs. Their selected
real-Slurm and institutional cancellation/recovery acceptance remains separate.
CV-14 and CV-22 now distinguish baseline ordinary CI from novice/site
acceptance. The [resource coverage map](cluster_verification_backlog.md#earlier-observations-and-coverage-reconciliation)
now identifies CV-U06/CV-U28 as the current allocation-policy owners;
CV-07/11/22 retain selection, fit, and disclosure responsibilities.
The linked retention ledger records the further ordinary-CI wording sweep
across CV-06 and twelve CV-U cards, while CV-01/CV-U06 keep selected
real-Slurm acceptance. No current card status changed.

**Additive evidence transfer:** Dated records now preserve
[CV-10 containment/retry](../history/2026-09-15-cv10-containment-retry.md),
the separate [job 621154 timeout](../history/2026-09-16-cv10-timeout.md),
[CV-26 hosted measurements](../history/2026-09-15-cv26-doctor-measurements.md),
and [CV-U28 fixed-policy provenance](../history/2026-09-15-cv-u28-resource-provenance.md).
The separate [CV-UX-01 job 621172 collision](../history/2026-09-16-cvux01-doctor-collision.md)
now has an indexed dated record with its ordinary-CI limit. The card's original
Open checkpoint is date-bound against its final Verification pending status.
Their original cards remain intact. These records do not transfer the later
prepared-finalization, structural Doctor, or allocation-aware decisions in
full, and they authorize no source evidence deletion.

**Checkpoint classification sample:** In the six reviewed cards (CV-10,
CV-26, CV-U06, CV-U22, CV-U28, and CV-UX-01), each final disposition agrees
with its index. Earlier implementation paragraphs, local pass-count sequences,
and refinement narration may be condensed only after the evidence and decisions
above are retained. Specific candidates are CV-U22 lines 1470–1480, CV-U06
lines 476–504, CV-U28 lines 1805–1840, and CV-UX-01 lines 2150–2154.
CV-U06's selected hosted follow-up at lines 506–522 and CV-26's trial
artifacts/counters at lines 3850–3951 contain distinct limits and are not
covered by a generic passing-CI summary. The linked ledger extends this
first-pass classification to the remaining 55 cards; none is approved for
shortening by that classification.

### 10. Polish chronology and overlap

**Observed:** The [polish campaign](polish-campaign.md#evidence-and-selection)
details its September 7–14 audit/PR sequence. Its
[overlap tables](polish-campaign.md#existing-capabilities-and-overlapping-work)
enumerate merged PRs, while
the main matrix owns seven current follow-ups (`DOCS-01`, `REDUCE-01`,
`SIZE-01`, `ASSURANCE-01`, `SCHEMA-01`, `EXTENSION-01`, `RELEASE-01`). Some
numbered findings also document completed implementation, such as item 43's
`emrys --version`. The campaign says its numbers are not backlog IDs.

**Documentation discovery:** The [44-item disposition table and chronology
retention map](polish_finding_disposition_review.md) now distinguish completed
implementation, live gaps, dated evidence, five unselected architecture
options, and possible Git-only PR sequencing. Verify each proposed durable
owner and any unmatched rationale before shortening the campaign. This review
does not approve source-evidence removal or reopen completed implementation.

The [five architecture options](polish-campaign.md#integration-scale-architecture-reduction-options) are unselected
`REDUCE-01`-adjacent hypotheses. Their withdrawn 6,400–9,200-line estimate is
not an accepted saving. Keep distinct trust and verification constraints while
separating them from the PR ledger.

### 11. Optimization source drift

**Observed:** [Optimization campaign](optimization_campaign.md) lines 17–36
pins its September 7 source audit to `fdf76760`. At this baseline, 17 of its
23 pinned source blobs differ and one cited `workflow/Snakefile` path moved to
`src/emrys/workflow/Snakefile`. The old links still document the original
audit. The PR45 experiment at lines 329–339 states limited observed gains and
an unmet experiment gate; that evidence must not be presented as a current
whole-Run speedup.

**Next:** Recheck candidates 1–13 against the current production owner,
callers, resources, and retained measurements. Mark observations as surviving,
superseded, or unresolved only after that comparison. Keep scientific and
recovery constraints even where an optimization proposal is retired.

**Candidate-by-candidate source pass:** The comparison below checks mechanism
only. No new benchmark, representative workload, physical-I/O measurement,
or scientific-equivalence result was produced. Numbers refer to the
[campaign discussions](optimization_campaign.md#candidate-observations).

| Candidate | Baseline source discovery | Disposition for the campaign text |
| ---: | --- | --- |
| 1 | [Step 06](../../src/emrys/stages/mechanical_orientation/producer.py) lines 140–149 and 172–207 still perform five input count scans, four flag extractions, and subgroup merge. | Mechanism survives; retain overlap/multiplicity and publication requirements. Benefit unmeasured. |
| 2 | [Reference observation](../../src/emrys/evidence/reference_provenance/_reference_contigs.py) lines 20–47 reads complete members; the [FASTA parser](../../src/emrys/libraries/references/contigs.py) lines 18–45 reads full text. | Mechanism survives; preserve independent observations and malformed-input behavior. Memory benefit unmeasured. |
| 3 | [Default policy](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml) and [Viking profile](../../configs/execution_profile.csu_viking_ev_pum1.yaml) now use allocation-aware sharing. | Treat the older fixed-core model as history; current tuning requires comparable Run measurements. |
| 4 | [Step 04](../../src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh) lines 64–72 and [Step 05](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh) lines 121–127 still run separate indexing. | Mechanism survives; verify native write-time capability and PR44 outcome before selecting a change. |
| 5 | [Step 08 processing](../../src/emrys/stages/cohort_candidate_preprocessing/_step_08_vcf_processing.R) lines 46–168 materializes VCF/allele/DP/AD/AF data; [aggregation](../../src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R) lines 175–215 retains worker results and binds rows. | Mechanism survives; retain order, TSV, recovery, and prototype evidence. RSS benefit unmeasured. |
| 6 | Each partition binds cohort BAM/BAI inputs in [materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) lines 695–704; the current successful, nonreused [Task](../../src/emrys/orchestration/run_coordinator/task.py) path hashes shared inputs at initial binding, entry, before/after native publication, and final admission. | The campaign now dates its `3 × P × B`/75 estimate and gives a source-derived lower bound of `5 × P × B`/125 for that path. Preserve mutation detection; physical I/O, elapsed cost, and savings remain unmeasured. |
| 7 | Stage/native budgets are now derived by [materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) lines 371–378 and applied to Picard/GATK heaps. | Old unbounded-heap premise is historical; spill/RSS tuning remains unmeasured. |
| 8 | [Step 05](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh) lines 121–124 sends Java/GATK temporary files to runner-owned `EMRYS_TASK_WORK_DIR`, described by its [contract](../../src/emrys/stages/split_n_cigar/CONTRACT.md) lines 50–60. | Replace the output-directory-spill premise. Faster site scratch remains an unselected, unmeasured question; do not assume current scratch is `/tmp`. |
| 9 | [Step 09](../../src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R) lines 227–278 retains a dense AF matrix; evaluation consumes DP/AD, and Python validation retains row tables. | Mechanism survives; retain AF rejection and global statistical checks. RSS benefit unmeasured. |
| 10 | [Step 07](../../src/emrys/stages/partitioned_cohort_mpileup/producer.py) lines 284–293 still emits text VCF. | Representation proposal survives; no approved output-format migration or measured disk/I/O result. |
| 11 | [Inspection](../../src/emrys/orchestration/run_coordinator/inspection.py) and the current [Snakefile](../../src/emrys/workflow/Snakefile) each traverse Task evidence; resume/report use inspection. | Repeated-work mechanism survives, but exact bytes and latency need measurement; preserve verification boundaries. |
| 12 | [Installed-package authority](../../src/emrys/libraries/source_authority.py) lines 68–125 reads build provenance and hashes executing package bytes without execution-time Git; [Task](../../src/emrys/orchestration/run_coordinator/task.py) lines 1861–1910 re-admits that identity at distinct boundaries. | The campaign now dates the four-attestation/24-Git-subprocess count. Rebuild the startup trace and retain installed-package, Attempt, and publication integrity. |
| 13 | [Runtime policy](../../src/emrys/resources/runtime/runtime_policy.tsv) lines 18–27 has ten R namespace checks, and [probe dispatch](../../src/emrys/evidence/runtime_availability/_probes.py) lines 383–418 runs them serially. | Mechanism survives; CV-26's Doctor reduction is separate. Startup benefit unmeasured. |

The old `workflow/Snakefile` link in the optimization campaign is a valid
citation to the pinned September 7 tree, but cannot establish the current
path or behavior without the comparison above. The dated PR45 experiment at
lines 329–339 remains bounded evidence; it does not prove an adopted current
whole-Run optimization.
Candidate 8's campaign text now dates the former output-directory spill path
and names current runner-owned Step 05 scratch; it retains the unmeasured
qualified fast-scratch question.
The campaign now also dates its candidate 1/2 priority ranking and candidate
6/12 numeric premises. Neither source-derived repeat count establishes
physical I/O, elapsed cost, or an approved optimization.

### 12. Time-bound campaign authority

**Observed:** [Cluster charter](cluster_verification_campaign.md) lines
21–27 records earlier implementation/stacked-PR approval, while lines 47–49
instruct against updating an installation under a running scientific job.
These are dated campaign circumstances. Current work authority comes from
[AGENTS.md](../../AGENTS.md), the [workflow](../operations/WORKFLOW.md), and
the present user instruction; a prior campaign approval is not a blanket
authorization for new implementation, site work, or evidence deletion.

**Documentation correction and provenance:** The approval summary was recorded in
`4d3ba00c41c6b13759d06b691d31cdcee20a1117` on 2026-09-14. The earlier
charter creation at `1ea21855a4e6db8bc54268e9c6869fa362d424eb` said an
actual-data Run was continuing and required separately selected bounded
implementation slices. It does not establish a job running now; E12 gives
only an active last-supplied observation. The later recorded approval covered
then-selected slices and stacked PRs, while excluding merge, cluster
execution, active-installation changes, and evidence deletion. It is a
repository summary, not the raw approval transcript. The charter now dates the
grant and running-job observation, disclaims current work or size authority,
and links the enduring fresh-installation rule to the
[Runbook](../operations/RUNBOOK.md#install-a-chosen-release-or-commit).
[AGENTS.md](../../AGENTS.md) and the [workflow](../operations/WORKFLOW.md)
govern current authorization. No card status changed.

### 13. Polish proposals versus current owners

**Observed:** The [per-item polish review](polish_finding_disposition_review.md)
maps all 44 numbered findings and five architecture options to current
source, accepted owners, and remaining evidence. Several old missing-feature
premises are superseded. Item 6's malformed timestamp admission is locally
reproduced; item 11's locked dependency graph confirms a CI/operator group
gap. Items 7, 9, 12 and 35 still need direct checks or policy decisions, while
item 33's current rules were read but its policy remains unselected. Delivered
source capability does not by itself close a larger backlog outcome or
institutional acceptance.
The companion and source campaign now distinguish baseline CI from the
remaining visual review for polish item 14, and date item 36's former missing
Slurm preflight while retaining CV-11's institutional capacity limit.
Item 33 now includes a dated read-only ruleset check for `master` and this
PR's distinct correction-branch base, without changing hosted settings.
Further source tracing separates item 7's explicitly deferred STAR values,
item 12's per-Dataset physical-file reuse policy, and item 35's unbound
Snakemake module content from demonstrated Run or site failures. Item 6's
artifact timestamp exposure is source-indicated and awaits its own probe.

**Next:** Resolve items 7, 9, 12 and 35 against direct tests or policy; select
separate corrections for 6 and 11 and a hosted decision for 33 if approved.
Transfer unique decisions and dated evidence before shortening campaign
chronology. The companion review proposes no deletion.

### 14. `HARNESS-01` status versus source gap

**Observed:** The [main matrix](backlog_matrix.md) line 161 marks
`HARNESS-01` Verification pending while its acceptance explicitly requires
reconciling a remaining `local-science-tools` naming/admission mismatch.
The [workflow fixture](../../tests/orchestration/run_coordinator/fixtures/workflow.py)
line 1015 emits that mode; a
[test callback](../../tests/orchestration/run_coordinator/test_materialization.py)
at lines 6350–6371 injects storage/runtime admission. The mode remains in the
production [Attempt schema](../../src/emrys/contracts/schemas/orchestration/v1/workflow_attempt.schema.json)
line 146 and [materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
line 1499. The matrix defines Verification pending as implementation
appearing complete with evidence outstanding, which does not plainly describe
this named source/contract mismatch.

**Disposition recommendation:** Under the matrix's stated vocabulary,
`HARNESS-01` should be Open at this baseline: the fixture still emits the
production execution mode while bypassing the admission that mode names.
Before changing the accepted row, trace every fixture and retained-record
reader. A selected correction must either perform real admission or name the
injected simulation explicitly while preserving partial-failure/resume tests.
Do not rename the production mode or remove the schema's `test-double` value
without a separate compatibility review. This review changes no status.

**Boundary check:** The production [contract](../../src/emrys/contracts/orchestration/api.py)
lines 483–494 requires Python and storage qualification for local science
mode, and [lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
lines 1343–1366 uses actual admission callbacks. The fixture emits the same
mode while its test callback checks the name without doing that admission.
The schema also accepts `test-double` at line 145, but this checkout has no
production writer for it; its observed uses are a contract fixture and test
diagnostics. This makes it a contract-retirement *candidate*, not proof that
retained Attempts or compatible readers permit removal. The partial-failure
and resume tests remain useful at their stated fixture level.

## Retention boundary for later edits

The [documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression)
puts current work in the matrix, exact behavior beside its owner, operating
commands in the Runbook/Troubleshooting, and dated validation observations in
history. Git retains routine progress and superseded wording. Exact evidence
deletion requires its own explicit approval and commit. An evidence transfer
must keep the originating commit, run date, job/artifact/hash identity,
observation, and its limits before removing the old location. This working
record should be retired or reduced to durable findings once the authoritative
documents and evidence homes are reconciled.

The [validation history](../history/validation-evidence.md) now indexes an
[additive E01–E12 record](../history/2026-09-14-viking-walkthrough.md). The
charter remains the original bounded E register; the matrix's Viking
walkthrough also holds exact jobs, a qualification identity, approvals, and
limits not reproduced by that register. The dated record copies those facts
and their source commits for review, including unknown E01/E06 causes, absent
E09 terminal recovery evidence, and E12's active-only observation. The
originals remain intact; the draft does not itself authorize shortening them.

| Candidate content | Proposed treatment | Gate before shortening or removal |
| --- | --- | --- |
| Current `INIT-02` and dashboard summaries | Corrected present-tense claims at their existing owners; card acceptance and dated test limits remain. | Confirm the exact documentation diff and hosted structure check; no evidence transfer is involved. |
| Charter's earlier development grant and running-job reference | Date-bound the original authorization and job circumstance; keep the enduring active-installation safety rule. | Confirm the historical approval wording and current workflow authority. |
| Roughly 205 lines across the three cluster closure regions | Link secondary delivery prose to the matrix's operative checklist. | Compare each condition with card acceptance and the E register; the region size is not a duplicate-line count. |
| Matrix walkthrough and charter E01–E12 | Additive dated record drafted and indexed; source records remain intact. | Verify source completeness, exact identities, unknown causes, absent receipts, limits, and inbound links before any separately approved reduction. |
| `COMPRESS-01` closeout counts and hosted checks | Additive dated record drafted and indexed; the matrix remains authoritative for the Closed decision. | Verify both baselines, count scope, exact run heads, evidence limits, and inbound links before any separately approved evidence reduction. |
| Polish audit/PR chronology and CV checkpoint narratives | Condense routine sequence after proposal and card-by-card disposition. | Keep unique rationale, exact CI/artifact identity, measurements, approvals, and recovery decisions. |
| Optimization old priority and traversal/attestation counts | Frame the counts as the pinned September 7 observation; re-evaluate priority against current source. | Retain raw PR45 measurements and obtain comparable new data before claiming benefit. |

Inbound links constrain later placement changes: the matrix's
`#viking-walkthrough-findings` heading is referenced by `SITE-PARITY-01` and
the charter; `#cluster-verification-closure-checklist` is referenced by the
campaign row, delegated backlog, and charter; the polish campaign's
`#current-follow-up-scope` is referenced by the design decision, main matrix,
and charter. [Validation history](../history/validation-evidence.md) also has
inbound guides and a required-document check. If a heading or evidence home
moves, update its inbound links and checker ownership in the same change.
