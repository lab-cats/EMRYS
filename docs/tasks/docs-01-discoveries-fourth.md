# DOCS-01 discovery notes, fourth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F100–F129; [fifth notes](docs-01-discoveries-fifth.md) begin at F130.
F100–F104 use local audit head `e1771d21`; F105–F108 use
`b65e8fb8`; F109–F110 use `26898b5e`; F111 uses `cd45bd51`, F112 uses
`b62e207b`, F113 uses `ac14392e`, F114–F117 use `b72b03c0`, and F118–F119 use
`24579272`; F120 uses `dc44861b`, F121–F122 use `f538efe4`, and F123 uses
`7e7c364c`, F124 uses `663da8ed`, and F125–F126 use `54f7b756`, all read on
2026-09-22. F127–F129 use `777345b6`, read on 2026-09-23. These are
documentation observations, not runtime results, accepted changes, or
permission to alter retained evidence.

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

**Dismissed for DOCS-01 at `1db7a88d`.**
The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 845–849 owns rejection of `resources.reporting_memory_mb` and
`--reporting-memory-mb`, with removal advice. The
[profile guide](../../configs/README.md) lines 357–364 warns that retired
reporting-memory settings are rejected; current options are at 233–264. The
[polish card](polish-campaign.md) lines 429–435 records the old control's
ineffective behavior. Direct rejection tests are at
`tests/orchestration/run_coordinator/test_execution_profile.py:697–703` and
`test_resource_policy.py:529–532`. Exact recovery belongs with the rejecting
owner; moving one sentence to the guide would add prose without an identified
reduction. The historical claim was not replayed in this audit.

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

**Dismissed after recheck at `71ac2272`.**
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
admission after Scientific Results completion. The Runbook immediately says
to check completion or finish incomplete reporting, so the sentence does not
promise admitted reports after every scientific completion. No separate
reader conflict or useful DOCS-01 reduction is established.

### F105 — Retired scheduler wrapper in the stage map

The [stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 81–86 explains
the absence of `00a -> 00b` and `00a -> 00c` edges through a retired Step 00a
scheduler wrapper under a “Current operational coupling” heading. Its current
[edge semantics](../../src/emrys/contracts/STAGE_MAP.md#edge-semantics)
at lines 36–43, external FASTA/GTF declarations at 45–56, and complete
direct-edge table at 58–79 already describe the present relationship. The
[admitted profile](../../src/emrys/workflow/contracts/local_cmh_v2.json)
lists no 00a-to-00b/00c edge, and the [Snakefile](../../src/emrys/workflow/Snakefile)
lines 400–424 schedules profile predecessors. The paragraph combines a
retired-wrapper explanation with the durable fact that 00b/00c do not consume
the STAR index and that their current references are external. The
[00b contract](../../src/emrys/stages/gtf_to_bed12/CONTRACT.md) lines 12–20 and
[00c contract](../../src/emrys/stages/fasta_sidecars/CONTRACT.md) lines 13–21
independently preserve that live rule. The heading/history mixture raises a
placement question; no safe saving or graph behavior was established here.

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
that revision's [Step 02b shell test](https://github.com/lab-cats/EMRYS/blob/88522d0a/tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh#L331-L355)
injects a dropped second hard link and asserts retained staging anchors and
lock. The [current runner test](../../tests/orchestration/run_coordinator/test_task.py)
at 810–845 covers analogous link, ownership, residue and input faults in a
different publisher. That current case does not by itself reproduce the old
TERM probe or prove one-to-one test equivalence. The current guide's
validation-recovery section at lines 22–30 describes live tests and known
limits. This shell passage is historical defect characterization inside a
present test index; a lossless
evidence home and any saving remain unverified. No test ran in this audit.

The same retired-writer history remains in current scientific-worker contracts:
[BAM QC](../../src/emrys/evidence/canonical_bam_qc/CONTRACT.md) lines 80–82
describes mixed evidence, [RSeQC](../../src/emrys/evidence/rseqc_orientation/CONTRACT.md)
lines 68–70 describes truncation and empty success, and
[duplicate marking](../../src/emrys/stages/duplicate_marking/CONTRACT.md) lines
58–59 describes partial or mixed outputs. Their current workers use runner
staging. The shared [publication decision](../design/decisions/execution-evidence-and-reporting.md#publish-validated-transactions)
states the lasting runner boundary but not these distinct old failure modes.
This expands the placement review, not the authority to remove evidence.

At local audit head `d18470c8`, three more current contracts retain distinct
retired-writer history: [scientific context](../../src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/CONTRACT.md)
lines 107–112 record a link/anchor interruption gap;
[SplitNCigarReads](../../src/emrys/stages/split_n_cigar/CONTRACT.md) lines 62–69
record ignored restoration failure; and
[canonical BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md) lines 82–120
record cleanup limits and a characterized lost-predecessor sequence. Their
current refusal and residue guidance remains owner-specific; the canonical
loss has retained old source and a fault oracle. No safe saving follows.

### F108 — Scientific completion in the run-summary guide

**Dismissed for DOCS-01 at `1db7a88d`.**
The [run-summary guide](../../src/emrys/reporting/_run_summary/README.md)
lines 28–29 explicitly describes computational manifest state before naming
external candidate review, adjudication, biological interpretation, and
scientific completion. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1157–1164 defines the named computational `Scientific Results: complete`
state, displayed by public
[inspection](../../src/emrys/orchestration/run_coordinator/control.py)
lines 2833–2837. The two meanings are already distinguished; no useful
correction or compression is shown. No report or runtime behavior was run.

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

**Dismissed for DOCS-01 at `27844f15`.**
The tracked [three-column pairing roster](../../configs/step_09_pairs.NORAD_EV_PUM1.tsv)
at lines 1–7 has no filename-specific link in the
[config inventory](../../configs/README.md#what-belongs-here) at lines 7–16
or tracked caller; the guide generically mentions pairing at 391–394. Its
six assignments match the [Quickstart table](../../quickstart.md#2-gather-the-study-inputs-and-scientific-choices)
at lines 83–90. Named Init creates the Project `samples.tsv` through the
[onboarding owner](../../src/emrys/orchestration/run_coordinator/onboarding.py)
at lines 1114–1159 and 1376–1387. Current
[Step 09 contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
lines 22–24 makes the sample manifest the sole pairing authority, and its
[validator](../../src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R)
lines 1–17 requires six columns absent from this file. Local Git places the
file at `e4371de5` on 2026-07-25, but its historical use is unverified.
This is a configuration artifact, not duplicate guide prose. Adding inventory
text would expand the guide; retiring the file has separate authority and
unverified external use. It is not a current Step 09 input.

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
but this check alone does not verify HTML report rendering or publication.
This is a guide-scope overclaim, not evidence that rendering
fails; neither the R check nor a report ran in this audit.

### F113 — CV-26 mixed current rules and measurement history

The [delegated CV-26 card](cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads)
spans lines 3748–4056 (309 lines). It owns original acceptance at 3750–3759
and the current Open disposition at 4053–4056. Earlier Open labels at 3900,
4000–4002, 4014, and 4021–4022 are dated checkpoints, not competing status.
The hosted phase timings at 3785–3808, probe attribution at 3846–3875,
invocation counters at 3902–3947, and four-trial comparison at 3949–3977
retain distinct revisions, artifacts, numbers, and limits. The hash/cache
decision at 3810–3825, failed-suite limits at 3989–4002, operator report at
4004–4014, and September 21 source/check record at 4024–4052 also remain.

The optional synthetic E2E caveat at 4019–4021 repeats 4011–4012, but that
sentence shares physical lines with unique admission and checkpoint context.
The September 21 record explains a five-to-four diagnosis reduction, the
preserved readmission and final checks, and its exact software evidence. The
[closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
requires the card's evidence and limits before retirement. This concern is
dismissed as a compression candidate: 309 lines are card scope, not a saving,
and no useful reduction or transfer was established. No Doctor or CI ran here.

### F114 — Older novice route in SITE-PARITY item

[Polish item 10](polish-campaign.md) lines 360–376 says the maintained novice
walkthrough includes site modules, explicit profile selection, and both storage
qualification phases. It does not say the operator manually runs the storage
checks. The current [Quickstart](../../quickstart.md) lines 1–5,
54–61, 92–103, and 142–174 instead gives one Viking head-node route: `emrys
setup` saves the Viking site, guided Init creates the Project, and Doctor
coordinates readiness before Run submission. The [Runbook](../operations/RUNBOOK.md)
lines 532–548 says Doctor handles compute-side runtime/storage checks and head
finalization. The current [`SITE-PARITY-01` row](backlog_matrix.md) line 170
requires a novice to follow only that Quickstart path. Item 10's named site
module and profile steps describe an older reader route; the storage checks
remain required under Doctor. Its open institutional proof and exact-revision
requirement remain valid. No novice or site walkthrough ran.

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

**Dismissed after recheck at `71ac2272`.** The delegated card needs its protocol beside acceptance evidence.
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
[contract's Linux subreaper rules](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 1068–1078 overlap CV-10 at 2816–2840. Keep the coordinator's positive
descendant-closure criteria, non-Linux fallback, and external-service limit;
CV-10 retains the accepted rationale, tests, dates, and exact evidence. The
[closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
requires exact evidence and limits to survive any temporary-card retirement.
No evidence was moved and no safe reduction was established.

### F117 — CV-20 current inspection beside submission history

**Dismissed after recheck at `71ac2272`.** The delegated card needs request and reconnect context.
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

### F120 — Superseded Init replay in the active CV backlog

The [CV-U18 card](cluster_verification_backlog.md#cv-u18-interactive-input-list-creation)
lines 1129–1140 calls a generated, safely quoted creation command the selected
implementation and says direct fixtures cover that replay. Its later
“Current confirmation correction” at lines 1204–1210 says `INIT-03` replaced
the command with a yes/no prompt and explicitly classes those replay fixtures
as historical evidence. The [main matrix](backlog_matrix.md) line 86 also
records the serializer's retirement. The [current Init owner](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 1302–1322 previews, then prompts `Create this Project?` unless execution
or explicit preview selects another path; lines 1391–1397 print `Project ready`
only after publication. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 147–151 and direct [onboarding assertions](../../tests/orchestration/run_coordinator/test_onboarding.py)
at 364–365 and 460–461 agree on that current boundary. CV-U21's dated
September 20 explanation at lines 1413–1415 also describes omission of
automatic STAR flags from the retired replay command; its automatic-value
and reference-freshness reasoning remains distinct. The CV chronology does
record the supersession, so this is a current-reader framing and compression
candidate, not evidence of an Init behavior defect or permission to discard
the older fixtures and observations. No Init command or test ran in this pass.

### F121 — renv activation path in the root notice

The root [`NOTICE`](../../NOTICE) lines 7–11 says the source repository includes
`renv/activate.R`. Git tracks the activation script at
[`src/emrys/renv/activate.R`](../../src/emrys/renv/activate.R), with no tracked
root `renv/activate.R`. The [package-data roster](../../pyproject.toml)
lines 74–80 names `renv/activate.R` relative to the `emrys` package, while
the [distribution test source](../../tests/test_package_distribution.py)
lines 46–51 expects wheel member `emrys/renv/activate.R` and lines 238–242
compare packaged bytes with the `src/` resource. The [renv owner guide](../../src/emrys/renv/README.md)
lines 1–5 also uses `renv/` relative to that package. In the root notice,
“source repository” makes the shorter path read as a repository location;
the relative package meaning is not stated there. This is a path-clarity
finding only. The copyright, attribution, and licensing terms were not
assessed or changed, and the distribution test was read rather than run.

### F122 — Step 06 optimization source after publication moved to the runner

**Dismissed after recheck at `71ac2272`.** The campaign pins all cited source to its dated audit.
[Optimization candidate 1](optimization_campaign.md#1-consolidate-step-06-scans-and-subgroup-materialization)
lines 72–88 cites a pinned producer for both “Extraction and publication” and
asks to preserve the five-file publication/recovery transaction. Its audit
basis at lines 19–24 explicitly identifies the 2026-09-07 source snapshot and
asks for rechecking before selection. That historical
[`fdf7676` producer](https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/mechanical_orientation/producer.py#L390-L449)
does acquire, publish, and recover its own transaction. The current
[Step 06 producer](../../src/emrys/stages/mechanical_orientation/producer.py)
lines 140–208 still performs the flag-selected extraction, merge, index, count,
and output checks, while its [contract](../../src/emrys/stages/mechanical_orientation/CONTRACT.md)
lines 49–57 assigns execution, publication, and recovery to the
[runner](../../src/emrys/orchestration/run_coordinator/task.py) lines 1491–1629.
The campaign's dated comparison is valid, makes no current-owner or current
performance claim, and explicitly requires rechecking before selection. The
five declared outputs, transaction safety, and historical cost observation
remain distinct; no DOCS-01 correction, saving, or speedup follows.

### F123 — Repeated stage resource defaults in the configuration guide

**Dismissed for DOCS-01 at `27844f15`.**
The [profile document guide](../../configs/README.md#profile-document)
lines 330–344 gives a 15-physical-line table of stage CPU use and task memory,
including eight numeric repeated-stage minimums. The current
[packaged default](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml)
lines 6–41 and [Viking example](../../configs/execution_profile.csu_viking_ev_pum1.yaml)
lines 8–43 serialize those same resource-policy values. Direct
[test source](../../tests/orchestration/run_coordinator/test_execution_profile.py)
lines 90–96 checks resource-policy equality between the built-in Viking
selection and example profile; it does not check this Markdown table. The
[resource owner guide](../../src/emrys/orchestration/run_coordinator/resources/README.md)
lines 22–24 links readers to the table for stage meanings and serial phases.
CPU descriptions also include tool behavior that is not just a YAML value.
The table's current values match the serialized policy and its owner
deliberately links it for stage meanings. Repeated numbers remain a drift
surface, but removing them shows no useful physical-line saving. The 15-line
table is not a savings estimate or capacity result.

### F124 — Reliability diagram collapses two validation orders

The [reliability diagram](../architecture/diagrams/reliability.mmd) lines 7–10
routes every task through staging, output validation, publication, and a
verified-task record in that order. Its line 18 sends validation failure to
“Owner rollback or retained recovery evidence.” The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1099–1104 gives publication and recovery to the runner; lines 1117–1130
distinguish Steps 08/09, which validate working files before publication, from
other owners, which publish native finals before validation. The
[runner](../../src/emrys/orchestration/run_coordinator/task.py) lines 1742–1747
and 2732–2782 implements those two orders. A direct
[test](../../tests/orchestration/run_coordinator/test_task.py) lines 3102–3135
asserts that a Step 08 fixture's finals do not exist during validation or after
a validation failure. The diagram collapses the two orders and leaves the
runner's recovery ownership ambiguous. It is a non-authoritative schematic:
after native commit, a validation failure preserves native outputs and failed
evidence; both paths still require semantic all-pass and publish verification
last. Source and tests were read, not executed; rendering was not checked.

### F125 — Producer publication claim in the shared-contract index

The [shared-contract index](../../src/emrys/contracts/README.md) line 12 says
producers own computation and publication. For first-party scientific tasks,
the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1099–1103 assigns computation and native checks to producers but paths,
publication, and recovery to the runner. The
[source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) lines 45 and
49–50 repeats runner publication ownership for Steps 07, 09, and 10, and
the [runner](../../src/emrys/orchestration/run_coordinator/task.py) lines
1490–1492 and 1625–1629 contains native publication. This present-tense
overview claim obscures the scientific producer/runner boundary. F122 concerns
a dated optimization citation; F124 concerns validation order. Reporting and
other record publishers have separate owners, and no runtime defect follows
from the index wording. Source was read, not executed.

### F126 — Doctor plan detail and timing display in the Runbook

The [Runbook](../operations/RUNBOOK.md) lines 660–666 says a `Runtime work`
line distinguishes three managed-runtime states, and lines 678–680 say Doctor
prints full invocation elapsed time and exit outcome. Neither sentence scopes
the display mode. The [Doctor source](../../src/emrys/orchestration/run_coordinator/doctor.py)
lines 1433–1444 prints `Runtime work` only for a verbose repair plan; lines
2023–2026 enable the normal elapsed summary only for `--repair`, while verbose
diagnosis can print detailed invocation timing (lines 207–266). Direct
[tests](../../tests/orchestration/run_coordinator/test_doctor.py) lines 947–1074
assert the field is absent in normal plan previews for all three states and
that normal elapsed output follows `--repair`. Lines 2064–2079 also assert
approved normal repair omits `Runtime work` while retaining its value in the
maintenance log. The normal plan heading still distinguishes repair from
verification; only package-manager output establishes actual package reuse.
This is a guide display-scope observation, not a Doctor or cluster result.

### F127 — Older local checks inside active CV acceptance cards

The [CV-U08 card](cluster_verification_backlog.md) lines 638–645 retains a
local-check ledger of 631 tests, 169 Markdown documents, 13 Quickstart Bash
blocks, one macOS skip, and six excluded isolated child cases. The
[CV-U20 card](cluster_verification_backlog.md) lines 1264–1279 records 554
focused tests but repeats the 169/13 snapshot and six-case environment limit.
Both cards continue with later acceptance wording at lines
659–668 and 1315–1329. At audit head `777345b6`, the tree had 175 tracked
Markdown files and 14 Quickstart Bash fences. Git blame dates the 169/13 and
six-case text to September 16 commits `1dcc0ce4b` and `024bd5dbc`, while
CV-U20's adjacent policy and test-count wording changed September 21. A
prose-introduction commit does not establish the checked revision. Neither
card names one beside its local totals. This is routine validation chronology
beside active acceptance, not evidence that those historical checks failed.
The skipped-case, installed-environment, no-cluster, and no-scientific-proof
limits remain material evidence; their deletion is not authorized by this
finding.

### F128 — Tool-specific thread effects in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 781–785 repeats STAR sorting threads, samtools worker counts and sort
memory, and Java helper-pool behavior already specified in the
[STAR](../../src/emrys/stages/star_alignment/CONTRACT.md) lines 67–77,
[canonical BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md) lines 61–71,
and [duplicate-marking](../../src/emrys/stages/duplicate_marking/CONTRACT.md)
lines 40–51 owner contracts. The same samtools worker rule sits with
[orientation](../../src/emrys/stages/mechanical_orientation/CONTRACT.md) lines
101–103 and [BAM QC](../../src/emrys/evidence/canonical_bam_qc/CONTRACT.md)
lines 142–144; [FASTA sidecars](../../src/emrys/stages/fasta_sidecars/CONTRACT.md)
lines 53–63 and [split-N-cigar](../../src/emrys/stages/split_n_cigar/CONTRACT.md)
lines 42–53 own the other Java-worker detail. Current
[materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 371–379 derives the native allowance and rejects impossible budgets.
This is a bounded five-line coordinator detail overlap, not a demonstrated
deletion: the central allowance, refusal, immutable policy, and owner-specific
tool behavior remain distinct. The stage map assigns tool details to owner
contracts but does not link each one; a reader-safe replacement may need
enough links to erase the nominal saving. Source and tests were read, not
executed.

### F129 — Unrouted workflow-profile index

**Dismissed for DOCS-01 at `1db7a88d`.** At `f347216d`, a limited scan
over 170 non-audit Markdown files found no inbound local link to the 11-line
[profile index](../../src/emrys/workflow/profiles/README.md). The
[workflow overview](../../src/emrys/workflow/README.md) lines 3–4 and 16–19
links directly to the
[local profile](../../src/emrys/workflow/profiles/local/README.md), whose
lines 3–13 explain YAML and package binding. The intermediate index keeps
the unique rule that a new selectable engine profile requires approval.
At `60ec53e1`, 41 of 170 non-audit Markdown files lacked an inbound Markdown
link, all `README.md` indexes. Thus link absence is weak evidence and the
shared orientation offers no useful reduction. Filesystem and non-Markdown
reader routes remain unverified.

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

The [polish campaign](polish-campaign.md) lines 1027–1028 says the immediately
preceding PR #140–147 implementations do not close recovery defects in items
1–4. Items 2 and 4 later record publisher retirement, closing those repair
proposals without claiming repair; items 1 and 3 remain proposed. Because
“these implementations” is scoped to the earlier PR list, the sentence is
historically accurate and does not establish a separate contradiction.

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 52–56 repeats the
coordinator's exact byte/device/inode and same-UID limitation at contract
1021–1027. Its trusted-workspace warning is relevant to the recovery reader;
the comparison established no safe reduction. Troubleshooting lines 222–230
also names the old unwritable `/local/tmp` incident. [SCRATCH-01](backlog_matrix.md)
line 87 retains that observation and distinguishes it from Viking `/tmp`,
whose suitability remains unverified. The distinction is an active operator
safety boundary, not routine chronology to discard.
