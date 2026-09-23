# DOCS-01 discovery notes, fourth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F100–F119. F100–F104 use local audit head `e1771d21`; F105–F108 use
`b65e8fb8`; F109–F110 use `26898b5e`; F111 uses `cd45bd51`, F112 uses
`b62e207b`, F113 uses `ac14392e`, F114–F117 use `b72b03c0`, and F118–F119 use
`24579272`, all read on 2026-09-22. These are documentation observations, not
runtime results, accepted changes, or permission to alter retained evidence.

## Discovery notes

### F100 — GTF worker detail in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1099–1104 defines runner ownership of paths, locks, streams,
publication, and recovery, then adds that the GTF-to-BED12 worker shares
normalization with Project and BED12 validation. The
[GTF owner contract](../../src/emrys/stages/gtf_to_bed12/CONTRACT.md)
lines 45–52 already states that exact worker fact and links back to runner
ownership. Current callers use `normalize_gtf` in the
[worker](../../src/emrys/stages/gtf_to_bed12/converter.py) lines 259–263 and
285–289, [validator](../../src/emrys/stages/gtf_to_bed12/validator.py) line 52,
and [Project admission](../../src/emrys/orchestration/run_coordinator/onboarding.py)
line 1719. This is a one-sentence owner-detail overlap inside a cross-owner
execution section. Runner publication and recovery rules remain distinct; no
safe saving is established by this comparison alone.

### F101 — Retired reporting-memory recovery advice in the contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 845–847 records rejection of the retired `resources.reporting_memory_mb`
field and `--reporting-memory-mb` flag, then gives the operator action of
removing the field from a selected profile. The
[profile guide](../../configs/README.md) lines 233–264 owns profile authoring
and current options; lines 357–364 warn generically that retired reporting-
memory settings are rejected, without naming this field or its removal. A
tracked guide search found no other exact operator route to that advice. The
source tests at
`tests/orchestration/run_coordinator/test_execution_profile.py:698–703` and
`test_resource_policy.py:529–532` cover the rejections. Exact rejection
behavior belongs to the coordinator owner. The removal advice has a different
operator audience and currently resides only in that contract. The historical
claim that the old control never constrained reporting was not independently
replayed in this pass.

### F102 — Historical E09 example in current lifecycle rules

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1029–1036 states current prepared-finalization eligibility, then names
the historical E09 Run and says its cause cannot be established or its state
recovered under this path. The [CV evidence register](cluster_verification_campaign.md)
line 114 retains the operator's cancellation observation; the
[CV-10 card](cluster_verification_backlog.md) lines 2732–2744 and 2810–2814
retains its accepted recovery boundary. The named example adds historical
context to the current contract, while its generic missing-evidence rule is
already stated there. Neither the E09 cause nor recovery of that old Run was
verified by this document comparison.

### F103 — Unpublished FASTQ experiment in the owner guide

The [sample-manifest owner guide](../../src/emrys/ingestion/sample_manifest_admission/README.md)
lines 20–32 mixes current helper limits with what it calls an unpublished
single-pass `awk` draft, its NUL-header counterexample, and a source-derived 21-pass
count. The [optimization campaign](optimization_campaign.md) lines 340–345
already records the deferred helper optimization and points to the owner for
the byte and diagnostic boundary. The
[current helper](../../src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh)
lines 73 and 114–151 defaults to 20 IDs, counts records, and rescans each
requested leading ID; this
supports the logical-pass count, not measured physical I/O or pipeline speed.
The current direct test module has prefix, count, mismatch, and compression
cases but no NUL-header case. The owner passage is the only current-tree
description found for the exact NUL-header pair and `awk` truncation; its
documentation commit `550b54025` does not establish the draft's execution
date or retained output. The exact counterexample and truncation detail are
unique to this current guide; the broader accepted-input boundary also appears
in the optimization campaign. This review establishes no deletable span or saving.

### F104 — Automatic reports after successful computation

The [Runbook](../operations/RUNBOOK.md) lines 274–278 says successful
computation generates both reports automatically. For a full Run, the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1200–1208 promises a default reporting invocation unless `--no-report`
was selected; a reporting failure does not invalidate completed science.
The [control path](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1514–1536 handles reporting failure after scientific Results complete.
The Runbook's own [recovery route](../operations/RUNBOOK.md#inspect-and-open-reports)
at lines 437–447 handles skipped, partial, and blocked reporting, while
[Quickstart](../../quickstart.md) lines 188–205 requires separate Reporting
admission after Scientific Results completion. “Generates both reports” can read as a
completion guarantee stronger than these independent checks. This is an
operator-wording question, not evidence of a reporting behavior defect.

### F105 — Retired scheduler wrapper in the stage map

The [stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 81–86 explains
the absence of `00a -> 00b` and `00a -> 00c` edges through a retired Step 00a
scheduler wrapper. Its current [edge semantics](../../src/emrys/contracts/STAGE_MAP.md#edge-semantics)
at lines 36–43, external FASTA/GTF declarations at 45–56, and complete
direct-edge table at 58–79 already describe the present relationship. The
[admitted profile](../../src/emrys/workflow/contracts/local_cmh_v2.json)
lists no 00a-to-00b/00c edge, and the [Snakefile](../../src/emrys/workflow/Snakefile)
lines 400–424 schedules profile predecessors. The paragraph combines a
retired-wrapper explanation with the durable fact that 00b/00c do not consume
the STAR index and that their current references are external. This mixture
raises a documentation-placement question; no safe saving or graph behavior
was established here.

### F106 — Doctor storage-plan proposal after Slurm routing changed

The [polish campaign](polish-campaign.md) item 9 at lines 341–358 says Doctor
constructs a direct storage-qualification plan for an unready Slurm Project,
that PR #136 did not change the plan, and that the defect investigation remains
proposed. Current [`_build_repair_plan`](../../src/emrys/orchestration/run_coordinator/doctor.py)
at lines 847–867 sets direct storage planning to `None` for selected Slurm
placement even when storage is unready. Execution selects `_qualify_slurm` at
1902–1908; its compute path calls storage qualification at 1550–1568. Git
attributes the Slurm exclusion to `7f4396f8` on 2026-09-14, after the
campaign's dated audit. Item 9 also recommends retaining a direct default
then selecting a separate Slurm profile at lines 347–349; current
[Runbook](../operations/RUNBOOK.md#slurm-setup-and-submission) lines 534–548
uses a Viking default and head-node Doctor route. The original concern remains
historical context, but its present-tense plan, proposed investigation, and
operator route no longer match these current sources.
No Doctor operation or institutional qualification was run, and a direct test
of this exact plan shape was not identified in this pass.

### F107 — Retired shell-publication tests in a current test guide

The [shared-library test guide](../../tests/libraries/README.md) lines 9–20
explains a TERM/link and inode-check cleanup gap in retired RSeQC, BAM-QC,
and duplicate-marking shell writers, then points to the current runner suite.
The cited `88522d0a` commit and `tests/libraries/` path survive in local Git;
that revision's guide describes the old shared shell cleanup. The current
guide's validation-recovery section at lines 22–30 instead describes live
tests and known current limits. The shell passage is historical defect
characterization inside a present test index, with a unique pointer to its
original test tree. No current runner test was executed here; a lossless
evidence home and any saving remain unverified.

### F108 — Scientific completion in the run-summary guide

The [run-summary guide](../../src/emrys/reporting/_run_summary/README.md)
lines 28–29 says candidate review, adjudication, biological interpretation,
and “scientific completion” are external processes. The
[architecture](../architecture/ARCHITECTURE.md) line 45 says scientific
completion and recovery belong to the runner; the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1157–1164 defines `Scientific Results: complete`, and public
[inspection](../../src/emrys/orchestration/run_coordinator/control.py)
lines 2833–2837 displays that state. External scientific review and biological
interpretation remain outside EMRYS. The unqualified phrase “scientific
completion” can conflate that external work with computational Results
completion; no report or runtime behavior defect is inferred.

### F109 — Runtime discovery's interactive publication

The [runtime owner guide](../../src/emrys/evidence/runtime_availability/README.md)
lines 61–63 says `runtime discover --from-project` probes without writing and
that `--execute` publishes the seal and dependent inventory. Current
[parser help and confirmation](../../src/emrys/orchestration/run_coordinator/onboarding.py)
at lines 2276–2301 say omission previews and offers a terminal confirmation;
the command calls `plan.admit()` after an affirmative answer at 2341–2350.
The direct [test](../../tests/orchestration/run_coordinator/test_onboarding.py)
lines 3161–3187 supplies `execute=False` and `y`, then observes a borrower
inventory. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 313–320 and [Runbook](../operations/RUNBOOK.md#reuse-prepared-managed-tools)
lines 623–631 already describe preview and confirmed publication. A declined
or noninteractive preview remains no-write. This is owner-guide wording drift;
no runtime command was executed in the audit.

### F110 — Unrouted study-pairs configuration file

The tracked [three-column pairing roster](../../configs/step_09_pairs.NORAD_EV_PUM1.tsv)
at lines 1–7 is absent from the [config inventory](../../configs/README.md#what-belongs-here)
at lines 7–16 and had no non-audit reader or caller reference in a tracked-text
search before this finding was recorded.
Its six assignments match the [Quickstart table](../../quickstart.md#2-gather-the-study-inputs-and-scientific-choices)
at lines 83–90. Current [Step 09 contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
lines 22–24 makes the sample manifest the sole pairing authority, and its
[validator](../../src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R)
lines 1–17 requires six columns absent from this file. Local Git places the
file at `e4371de5` on 2026-07-25, but its historical use is unverified.
This is an unrouted, apparently legacy study artifact; neither safe deletion
nor executable current Step 09 input follows from the comparison.

### F111 — Current resource claim with old profile citations

The [optimization campaign](optimization_campaign.md#audit-basis-and-evidence-limits)
lines 19–24 says its source citations are pinned to `fdf7676` on 2026-09-07.
Candidate 3 at lines 105–117 now describes the current allocation-aware
CV-U06/CV-U28 policy and cites `[default-profile]` and `[viking-profile]`,
whose definitions at lines 426–427 still point to that old revision. Local
`git show` of those cited files gives fixed `workflow_cores: 4` or `12`,
numeric stage concurrency, and Viking `cpus_per_task: 256` with
`memory_mb: null`. The [current default](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml)
lines 4–15 uses `allocation` and `auto`; the [current Viking example](../../configs/execution_profile.csu_viking_ev_pum1.yaml)
lines 46–55 requests `node` CPUs and all node memory. Git attributes the
candidate's current-policy paragraph to `593f6e728` on 2026-09-21, after the
audit snapshot. The old links remain valid for historical claims, but do not
support this later current-policy description. This is citation provenance,
not a measured resource or runtime result.

### F112 — R environment check's report-support claim

The [scripts index](../../scripts/README.md) line 10 says
`check_r_environment.R` checks the selected R library against the lock and
“verifies report support.” The [script](../../scripts/check_r_environment.R)
lines 48–125 checks R packages, versions, library selection, and lock status;
lines 128–159 create and inspect a tiny headless PDF. It invokes no reporting
provider, HTML renderer, or report publication path. Current
[report rendering](../../src/emrys/reporting/_run_report/validation.py)
lines 85–159 uses Python/Jinja HTML, and the built-in
[figure renderer](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/figures.py)
lines 208–231 uses Python/Matplotlib SVG. The R PDF device is relevant to
[Step 09's scientific PDF outputs](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md#inputs-and-six-output-transaction),
but this check alone does not verify current
report support. This is a guide-scope overclaim, not evidence that rendering
fails; neither the R check nor a report ran in this audit.

### F113 — CV-26 mixed current rules and measurement history

The [delegated CV-26 card](cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads)
spans lines 3748–4056: its original full-operation measurement acceptance is
at 3750–3759 and the current Open disposition at 4053–4056. Current Doctor
timing, fresh-read, and logging rules recur at 3761–3775, 3827–3844, and
4016–4039; the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 220–287 owns related current timing and logging behavior, while the
[campaign summary](cluster_verification_campaign.md) lines 203–206 and
[main matrix](backlog_matrix.md) lines 104–110 state the structural reduction's
current limit. Earlier Open checkpoint labels also recur at CV-26 lines 3900,
4000–4002, 4014, and 4021–4022. This mixes live acceptance with dated progress
inside a 309-physical-line card; the count is a review scope, not a saving.

The hosted phase timings at 3785–3808, probe attribution at 3846–3875,
invocation counters at 3902–3947, and four-trial serial/two-worker comparison
at 3949–3977 each retain distinct revisions, artifacts, numbers, and evidence
limits. The local hash-reuse fixture and cache decision at 3810–3825, failed
prototype suites and retirement CI at 3989–4002, September 16 operator report
at 4004–4014, and September 21 source/check results at 4044–4052 also retain
distinct context. The [closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
requires exact CV-26 evidence and limits before temporary-card retirement.
No evidence was moved, no net reduction was established, and no Doctor or CI
operation ran in this audit.

### F114 — Older novice route in SITE-PARITY item

[Polish item 10](polish-campaign.md) lines 360–376 says the maintained novice
walkthrough includes site modules, explicit profile selection, and both storage
qualification phases. The current [Quickstart](../../quickstart.md) lines 1–5,
54–61, 92–103, and 142–174 instead gives one Viking head-node route: `emrys
setup` saves the Viking site, guided Init creates the Project, and Doctor
coordinates readiness before Run submission. The [Runbook](../operations/RUNBOOK.md)
lines 532–548 says Doctor handles compute-side runtime/storage checks and head
finalization. The current [`SITE-PARITY-01` row](backlog_matrix.md) line 170
requires a novice to follow only that Quickstart path. Item 10's named manual
steps describe an older reader route while its open institutional proof and
exact-revision requirement remain valid. No novice or site walkthrough ran.

### F115 — Current resource policy repeated in optimization candidate

[Optimization candidate 3](optimization_campaign.md) lines 107–117 restates
allocation-aware CPU/RAM resolution, automatic repeated-stage shares, native
allowances, the retired fixed 12-core policy, and the CV-U28 evidence limit.
The current [resource owner](../../src/emrys/orchestration/run_coordinator/resources/README.md)
lines 3–26 already owns the defaults, provenance, and capacity-versus-utilization
boundary. The [CV-U28 card](cluster_verification_backlog.md#cv-u28-allocation-aware-resource-policy-and-historical-provenance)
lines 1847–1861 retains the superseding policy decision and pending institutional
acceptance. Candidate lines 119–126 uniquely propose future concurrency,
reservation, queue, and storage measurements; those are not current-policy
restatement. The 11 physical lines at 107–117 are a review span, not a verified
saving. F111 separately records that this paragraph's linked old-profile
citations do not support its newer current-policy wording. No resources were
measured.

### F116 — CV-10 current protocol beside cancellation evidence

The [CV-10 card](cluster_verification_backlog.md#cv-10-external-cancellation-and-recovery)
lines 2732–2979 retains original E09 cancellation acceptance at 2734–2746.
Its current retry and prepared-finalization protocol at 2799–2814, 2886–2912,
and 2949–2961 also belongs to the
[coordinator lifecycle contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
lines 957–1036. The card separately retains Viking timeout job `621154` at
2783–2797, exact hosted revisions/artifacts and failed-suite limits at
2853–2873 and 2914–2947, pending hosted/site acceptance at 2963–2966, and the
owner-accepted recycled-inode trust limit at 2968–2979. F102 concerns the E09
example inside the current contract, not this card's mixed roles. The
[closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
requires exact evidence and limits to survive any temporary-card retirement.
No evidence was moved and no safe reduction was established.

### F117 — CV-20 current inspection beside submission history

The [CV-20 card](cluster_verification_backlog.md#cv-20-submission-state-before-run-creation)
lines 3332–3469 keeps original pre-Run submission, queue, reconnect, and
duplicate-risk acceptance at 3334–3341. Its current request and inspection
mechanics at 3357–3398 and 3422–3462 overlap the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)
lines 420–520. The card also preserves the installed-watch prerequisite at
3343–3355; product-size and test checkpoints at 3357–3366, 3385–3387, and
3400–3418; and exact hosted CI `34977917662` with pending institutional
observations at 3463–3469. A scheduler record remains observational and does
not grant scientific or recovery authority. This is a placement question, not
proof that any of those dated results can be discarded or that a line saving
exists. No scheduler, Run, test, or CI command ran.

### F118 — CV-21 reporting table detail level

The [CV-21 card](cluster_verification_backlog.md#cv-21-reporting-in-progress-and-visibility)
lines 3485–3497 says normal inspection shows the reporting transaction table,
that it appears at each detail level, and that public fixtures cover normal and
verbose rows. The current [inspection source](../../src/emrys/orchestration/run_coordinator/control.py)
lines 2862–2881 prints `Reporting transactions:` only inside `if verbose`.
The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1190–1195 and 1210–1215 assigns the three rows to verbose inspection;
normal output retains Reporting admission, blockers, and admitted report
locations. Direct [test assertions](../../tests/orchestration/run_coordinator/test_materialization.py)
at 2208–2222 and 2251–2262 require that split. The card's normal-output claim
is stale relative to current source and tests. Its E06 observation, verified-
location gate, finalization-fault cases, and pending institutional execution
remain separate evidence. No inspection command or test ran in this audit.

### F119 — CV-U20 inline study-value claim after automatic defaults

The [CV-U20 card](cluster_verification_backlog.md#cv-u20-complete-viking-values-in-quickstart)
lines 1253–1262 says Quickstart supplies fixed `sjdbOverhang=149`,
`genomeSAindexNbases=14`, `genomeChrBinNbits=18`, and background maximum `0.01`
inline. Its later checkpoint at 1315–1320 still says all known values remain in
the guide. The current [Quickstart](../../quickstart.md) lines 102–124 gives
sample assignments and five active paired-CMH values, but none of those four
numbers. [Configuration guidance](../../configs/README.md) lines 62–92 and the
[CV-U21 card](cluster_verification_backlog.md#cv-u21-technical-parameter-assistance)
lines 1389–1430 explain that Init now derives the STAR values from admitted
inputs and displays the persisted `0.01` as inactive when there is no background
condition. This is outdated guide-description wording in a dated card, not
evidence that Quickstart omits an input the novice must choose. Preserve the
original inline-values requirement, historical selected values, and pending
novice/site acceptance. No Init or Viking journey ran.

## Reviewed overlaps without a saving claim

The [test-tool guide](../../tests/tools/README.md) lines 25–30,
[main matrix](backlog_matrix.md) lines 114–123, and
[CV backlog](cluster_verification_backlog.md) lines 505–521 and 2276–2284
repeat the 130-pair fixture's 2048-MiB floor, whole-node Slurm request, and
evidence limits. These serve current test ownership, acceptance, and dated
verification respectively. The adjacent FIFO, stop, and Attempt details in
the test guide are owner-local and preserve unique safety mechanics; no safe
saving was established from the overlapping resource summary.

The [scientific-pipeline decision](../design/decisions/scientific-pipeline.md)
lines 80–92 states lasting cohort, selector, receipt, and count/exclusion
safety choices. Step 07 and Step 08 owner contracts give their detailed
mechanics. This concise decision-to-owner overlap establishes no saving.

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 52–56 repeats the
coordinator's exact byte/device/inode and same-UID limitation at contract
1021–1027. Its trusted-workspace warning is relevant to the recovery reader;
the comparison established no safe reduction. Troubleshooting lines 222–230
also names the old unwritable `/local/tmp` incident. [SCRATCH-01](backlog_matrix.md)
line 87 retains that observation and distinguishes it from Viking `/tmp`,
whose suitability remains unverified. The distinction is an active operator
safety boundary, not routine chronology to discard.
