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
scientific review, and biological interpretation remain different claims. No
new runtime, CI, site, performance, or scientific result was produced for this
draft.

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

## Findings matrix

Finding numbers identify review questions within this temporary record. They
are not backlog IDs or a second task-status list. Each row has an initial
discovery below and names the next evidence needed before changing authority.

| Finding | Baseline discovery | Next verification or disposition |
| --- | --- | --- |
| 1. Status vocabulary and placement | The matrix uses `Needs decision` without defining it; the delegated backlog uses `Discard`; two Completed rows sit under Active backlog. | Reconcile lifecycle meanings and place completed outcomes without changing their acceptance. |
| 2. `INIT-02` and dependent onboarding claims | Automatic maintained-study selection is Open, but CV summaries call `INIT-01`–`INIT-03` source-complete. Quickstart supplies a manifest path explicitly. | Correct the source-completeness summary; review CV-06, CV-U08, CV-U20, and CV-U21 against their own acceptance before any status change. |
| 3. `CV-U22` runtime reuse | The card remains Open for compatible-donor discovery before installation; the documented known-smoke route is narrower. | Retain Open and the no-silent-donor rule; distinguish known-smoke evidence from the undecided general selection design. |
| 4. `CV-26` Doctor cost | One redundant full diagnosis was removed; original complete-operation attribution and comparable measurements remain Open. | Separate exact retained measurements and the serial-probe decision from implementation checkpoints and unmeasured speedup claims. |
| 5. Dashboard retirement | The matrix says the standalone entry point and callers are retired; several CV summaries still say that retirement remains. | Correct current-sounding text while keeping shared watch code, historical readers, and pending visual verification. |
| 6. Repeated cluster closure instructions | The main checklist, cluster backlog summary, and charter repeat remaining work. | Keep one operative sequence and retain unique card acceptance and evidence limits at their owners. |
| 7. Viking walkthrough chronology | The main matrix holds dated jobs, a qualification hash, capacity observations, approvals, and a last-supplied Run state. | Map unique evidence and decisions to durable homes before shortening current-task prose. |
| 8. Compression closeout chronology | The completed section combines the user closure, quantified shortfall, exact CI, and PR chronology. | Keep the closure decision; preserve unique measurements and evidence ceiling before condensing routine integration history. |
| 9. CV card checkpoint narratives | Detailed cards repeatedly recount Open-to-implemented-to-pending transitions alongside live acceptance. | Classify each paragraph; retain original outcome, current status/acceptance, trust limits, and exact evidence pointers. |
| 10. Polish chronology and overlap | The campaign contains an old audit/PR narrative and merged-PR tables plus proposals already implemented elsewhere. | Classify PR chronology and preserve unique rationale and evidence before compression. |
| 11. Optimization source drift | The September 7 audit is correctly pinned, but most cited source blobs changed by the baseline. Candidates 8 and 12 have materially changed source premises. | Re-evaluate all 13 candidates against current owners and measurements without converting old proposals into defects. |
| 12. Time-bound campaign authority | The charter repeats earlier blanket development authority and an active-cluster-job precaution as present-tense guidance. | Date-bound historical instructions; keep current authorization and cluster safety with their authoritative owners. |
| 13. Polish proposals versus current owners | Several original findings describe capabilities now delivered; others retain a live gap. | Reconcile each numbered proposal with source, tests, accepted rows, and its original evidence ceiling. |

## Initial discoveries

### 1. Status vocabulary and placement

**Observed:** [Matrix operating rules](backlog_matrix.md) lines 24–29 define
Open, In progress, Verification pending, Deferred, Completed, and Closed.
`REPORT-ROSTER-01` uses `Needs decision` at line 295. The delegated backlog
uses `Discard` for CV-12 in its index at line 106 and detailed disposition at
line 3032, while its introduction refers readers to the matrix meanings.
`VIKING-POLICY-01` and `CV-DOCS-01` are Completed at matrix lines 90–91 under
`## Active backlog`; the completed section begins at line 297.

**Next:** Specify whether `Needs decision` is an accepted nonterminal state and
whether `Discard` is a card disposition rather than a work status. Preserve the
reason and evidence boundary for CV-12 and move or clearly distinguish the two
Completed rows. Do not infer a new status from their section placement.

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

**Next:** Inspect the public Init owner and direct tests at this commit, then
separate the delivered no-paste route from automatic study selection. Review
CV-06, CV-U08, CV-U20, and CV-U21 acceptance as whole outcomes; correct summaries
without changing their statuses solely because one linked `INIT` row is Open.

**Source comparison:** The public Init owner in
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 1027–1055 offers a regions file or manually entered FASTA names when no
partition manifest is given; it does not choose the maintained EV/PUM1 study.
The direct test at `tests/orchestration/run_coordinator/test_onboarding.py`
lines 1505–1510 supplies the manifest path. CV-06's original acceptance at
cluster backlog lines 2474–2484 permits either a short guided path or a
supported import, so an Open `INIT-02` does not mechanically reopen CV-06.
CV-U20 lines 1323–1329 describe the Quickstart's explicit manifest, not
automatic Init selection. CV-U08's delivered-journey claim at lines 605–619
needs the same original-intent review.

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

**Next:** Map existing Project discovery and compatibility helpers before
proposing a general donor-selection design. Preserve the known-smoke
implementation and its pending institutional acceptance while keeping the
expanded before-install requirement visible. Doctor must not silently select
another Project's tools.

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

### 6. Repeated cluster closure instructions

**Observed:** The [main closure checklist](backlog_matrix.md) lines 103–152
calls itself the single remaining verification and handoff sequence. The
[CV backlog](cluster_verification_backlog.md) lines 33–89 has a second
remaining-acceptance table, and the [charter](cluster_verification_campaign.md)
lines 53–86 and 152–190 repeat delivery and closure instructions. Each also
contains some distinct evidence limits.

**Next:** Compare each sentence with the operative checklist and detailed
cards. Replace only verified duplicate guidance with links; keep unique
conditions, evidence ceilings, and card-specific acceptance at their owners.

### 7. Viking walkthrough chronology

**Observed:** [Main matrix](backlog_matrix.md) lines 182–276 keeps the
September 14 walkthrough, including job `614786`, storage qualification hash,
jobs `618134` and `618190`, memory/cgroup observations, a bounded product
allowance, and reported synthetic/actual-data states. The
[charter register](cluster_verification_campaign.md) lines 104–117 summarizes
E01–E12 but does not replace every exact identifier or approval in the matrix.

**Next:** Make an identity-by-identity retention map. Keep current site
acceptance in `SITE-PARITY-01`/`CLUSTER-VERIFY-01`, lasting policy with its
owner, and exact dated observations with their source and ceiling in
[validation history](../history/validation-evidence.md) if a transfer is
approved. Do not infer actual-data completion from a last-supplied state.

### 8. Compression closeout chronology

**Observed:** [Main matrix](backlog_matrix.md) lines 303–350 contains the
explicit user closure of `COMPRESS-01`, its 484-line shortfall against the
agreed 20% target, two different comparison baselines, a seven-surface net
table, exact CI links, and PR integration chronology. The closure decision and
measurement definitions remain material; Git already keeps routine PR order.

**Next:** Preserve the user decision in the row and place exact counts,
baselines, checks, and evidence ceilings in a dated record before shortening
the closeout narrative. Date-bound the old dashboard statement rather than
letting it override the current retirement row.

### 9. CV card checkpoint narratives

**Observed:** The [cluster backlog](cluster_verification_backlog.md) is 4,107
lines. CV-U06, CV-U22, CV-U28, CV-10, and CV-26 include dated implementation,
adversarial-review, and verification checkpoints before their current
disposition. The CV-26 record after line 3785 and CV-U28 historical resource
reconstruction after line 1760 contain unique evidence or decisions. A simple
deletion by age would lose that support.

**Next:** For every CV-01–27, CV-U01–33, and CV-UX-01 card, record the
original outcome, current status, current behavior, remaining acceptance,
owner, and exact evidence that must survive. Remove or link only superseded
non-evidence narration after this comparison; keep unknown causes unknown.

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
| CV-10, lines 2928–2979 | Exact CI/artifact hashes, the failed first-suite distinction, prepared recovery boundary, and accepted equal-byte recycled-inode limitation. |
| CV-26, lines 3785–3808 and 3949–4056 | The bounded 175.681-second hosted setup, four trial measurements, artifact identity/hash, failed prototype-suite distinction, serial-probe decision, and five-to-four structural reduction without a measured whole-operation or Viking speedup. |
| CV-U06, lines 512–533; CV-U28, lines 1749–1785 and 1847–1861 | Product-growth exception, historical resource provenance, operator-reported eight/four-hour comparison, superseding allocation policy, and explicit lack of utilization proof. |
| CV-23, lines 3601–3625; CV-21, lines 3537–3545 | No presently provable deletable candidate class, and the decision to stop causal reconstruction of E06 while preserving truthful current reporting. |
| [Charter](cluster_verification_campaign.md), lines 104–117 | E01–E12 observations and their limits, including unknown E01/E06 causes, E09's missing terminal recovery evidence, and E12's missing terminal actual-data result. |

CV-01's selected 130-pair disposable-Slurm journey still needs the exact
hosted and site proof named in its card (cluster backlog lines 2259–2295).
CV-10 and CV-18 also keep hosted checks and institutional cancellation
acceptance separate. The older resource coverage map at cluster backlog line
4103 should identify CV-U06/CV-U28 as the current allocation-policy owners;
CV-07/11/22 retain selection, fit, and disclosure responsibilities.

### 10. Polish chronology and overlap

**Observed:** [Polish campaign](polish-campaign.md) lines 35–131 details its
September 7–14 audit/PR sequence. Lines 974–1040 enumerate merged PRs, while
the main matrix owns seven current follow-ups (`DOCS-01`, `REDUCE-01`,
`SIZE-01`, `ASSURANCE-01`, `SCHEMA-01`, `EXTENSION-01`, `RELEASE-01`). Some
numbered findings also document completed implementation, such as item 43's
`emrys --version`. The campaign says its numbers are not backlog IDs.

**Next:** Reconcile every finding and option with a current accepted row,
owner-local contract, still-useful proposal, or dismissal. Preserve unique
constraints and dated evidence; then condense PR chronology that Git already
records. Do not re-open completed work from an old proposal heading.

The five architecture options at polish lines 132–225 are unselected
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
| 6 | Each partition binds cohort BAM/BAI inputs in [materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) lines 695–704; [Task](../../src/emrys/orchestration/run_coordinator/task.py) lines 2605–2790 has multiple pre-producer, publication, and final hashing windows. | Rebuild the old `3 × P × B`/75-traversal example per branch; preserve mutation detection. Physical I/O remains unmeasured. |
| 7 | Stage/native budgets are now derived by [materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) lines 371–378 and applied to Picard/GATK heaps. | Old unbounded-heap premise is historical; spill/RSS tuning remains unmeasured. |
| 8 | [Step 05](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh) lines 121–124 sends Java/GATK temporary files to runner-owned `EMRYS_TASK_WORK_DIR`, described by its [contract](../../src/emrys/stages/split_n_cigar/CONTRACT.md) lines 50–60. | Replace the output-directory-spill premise. Faster site scratch remains an unselected, unmeasured question; do not assume current scratch is `/tmp`. |
| 9 | [Step 09](../../src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R) lines 227–278 retains a dense AF matrix; evaluation consumes DP/AD, and Python validation retains row tables. | Mechanism survives; retain AF rejection and global statistical checks. RSS benefit unmeasured. |
| 10 | [Step 07](../../src/emrys/stages/partitioned_cohort_mpileup/producer.py) lines 284–293 still emits text VCF. | Representation proposal survives; no approved output-format migration or measured disk/I/O result. |
| 11 | [Inspection](../../src/emrys/orchestration/run_coordinator/inspection.py) and the current [Snakefile](../../src/emrys/workflow/Snakefile) each traverse Task evidence; resume/report use inspection. | Repeated-work mechanism survives, but exact bytes and latency need measurement; preserve verification boundaries. |
| 12 | [Installed-package authority](../../src/emrys/libraries/source_authority.py) lines 68–125 no longer performs execution-time Git checkout attestation, while [Task](../../src/emrys/orchestration/run_coordinator/task.py) lines 1861–1910 re-admits package identity. | Retire the current-sounding four-attestation/24-Git-subprocess count; rebuild startup trace and retain source-change detection. |
| 13 | [Runtime policy](../../src/emrys/resources/runtime/runtime_policy.tsv) lines 18–27 has ten R namespace checks, and [probe dispatch](../../src/emrys/evidence/runtime_availability/_probes.py) lines 383–418 runs them serially. | Mechanism survives; CV-26's Doctor reduction is separate. Startup benefit unmeasured. |

The old `workflow/Snakefile` link in the optimization campaign is a valid
citation to the pinned September 7 tree, but cannot establish the current
path or behavior without the comparison above. The dated PR45 experiment at
lines 329–339 remains bounded evidence; it does not prove an adopted current
whole-Run optimization.

### 12. Time-bound campaign authority

**Observed:** [Cluster charter](cluster_verification_campaign.md) lines
21–27 records earlier implementation/stacked-PR approval, while lines 47–49
instruct against updating an installation under a running scientific job.
These are dated campaign circumstances. Current work authority comes from
[AGENTS.md](../../AGENTS.md), the [workflow](../operations/WORKFLOW.md), and
the present user instruction; a prior campaign approval is not a blanket
authorization for new implementation, site work, or evidence deletion.

**Next:** Keep the reason for the live-installation safety boundary, but
date-bound the original job and approval so readers do not mistake them for
current state. Recheck all instructions and links before changing the charter.

### 13. Polish proposals versus current owners

**Observed:** Several original premises in the [polish campaign](polish-campaign.md)
have changed at the audit baseline. Item 7 (lines 313–327) says Init preview
shows only output locations, but the current public preview in
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 1163–1258 includes libraries, Analysis/site, reference, scientific
choices, and defaults, with detailed manifests behind verbose output. Item 8
(lines 329–339) says Doctor lacks a profile selector, but
[`doctor.py`](../../src/emrys/orchestration/run_coordinator/doctor.py) lines
1976–1982 offers `--profile` and lines 484–510 select it. Item 9's old
direct-storage-plan premise (lines 341–358) is narrowed by Doctor's current
Slurm branch at lines 835–857; site behavior still needs review. Item 36
(lines 798–811) describes explicit-memory preflight as missing, while the
[current `SCHED-01` row](backlog_matrix.md) line 172 says its source is
implemented and verification remains.

**Still live or undecided:** Item 11's environment-parity question persists:
[Quickstart](../../quickstart.md) line 44 uses
`--no-default-groups --group workflow`, while the managed golden CI lane in
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) lines 632–638
lacks `--no-default-groups`. Item 12's draft versus admitted FASTQ identity
question also remains: the draft rejects reused physical files by device and
inode (`onboarding.py` lines 1441–1457), while Project normalization checks
path equality and caches by path
([`normalization.py`](../../src/emrys/orchestration/run_coordinator/normalization.py)
lines 359–385). This is a policy comparison, not an established defect.

**Next:** Continue through the remaining numbered findings and options; for
each, distinguish delivered behavior, a still-live gap, a decision, and a
dated observation. Update the campaign's current-sounding premise only after
checking the accepted row and owner tests.

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
