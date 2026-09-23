# DOCS-01 discovery notes, third file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F62 onward. F62–F64 use PR head `b67e0eeb`; F65–F66 began at
`cf94af08`, with F66 extended at `9c4fafdc`; F67–F70 use `c0a6027a`;
F71 uses `9c4fafdc`; F72–F73 use `b3af5d9e`; F74–F77 use `ab25ea9b`;
F78–F83 use PR head `7a07d502`; F84–F88 use `ce9a3289`;
F89 uses local head `39a21034`; F90–F93 and the F85 extension use `9c0264d3`;
F94–F96 and the F22/F53 extensions use local head `e90c85f4`,
F97–F99 and the F50/F56/F69/F86 extensions use local head `7adde22a`,
all read on 2026-09-22.
These are documentation observations, not runtime results or accepted changes.

## Discovery notes

### F62 — Benchmark value can be label only

The [scripts guide](../../scripts/README.md) line 9 says
`benchmark_stage_resources.py` measures stage commands at declared resource
values. Its [manifest loader](../../scripts/benchmark_stage_resources.py)
lines 182–198 accepts producer argv without `{value}`. Expansion at lines
203–210 substitutes only placeholders present; trial labeling at 378–405 and
timing at 445–456 can therefore use different value labels for identical
producer command lines; setup or external state can still differ. The
[test fixture](../../tests/test_benchmark_stage_resources.py)
lines 33–41 includes a valid producer without the placeholder. This limits what
the label proves about the command's actual resource setting; it is not a
measured performance discrepancy. No benchmark was executed.

### F63 — Background cohort in the scientist diagram

The [scientist diagram](../architecture/diagrams/current_user_pipeline.mmd)
lines 4 and 33 shows an “Independent background cohort” entering only candidate
ranking; its legend at line 39 calls arrows data or contract dependencies. Run
[normalization](../../src/emrys/orchestration/run_coordinator/normalization.py)
lines 554–582 selects the Analysis sample rows, passes them to scientific
policy admission at 614–639, and uses the same rows in workflow inputs at
680–685.
[Step 07](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
lines 12–16 and 37–40 consumes every declared sample's orientation BAMs in
manifest order. [Step 09](../../src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R)
lines 73–97 identifies background samples in that manifest. Selected background
libraries thus use the upstream sample path; the optional background filter
acts during ranking. This is diagram ambiguity, not a demonstrated scientific
behavior defect.

### F64 — STAR mechanics in a scientific decision

The [scientific pipeline decision](../design/decisions/scientific-pipeline.md)
lines 17–34 restates how named Init derives three STAR index settings, handles
the >5,000-sequence case, freezes overrides, and normalizes an absent legacy
`genome_chr_bin_nbits`. The [configuration guide](../../configs/README.md)
lines 62–75 and [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 124–134 already own those current mechanics. The decision also records
the original EV/PUM1 values, the mechanical-versus-biological boundary, and a
pinned STAR manual citation. This is a narrow duplication observation; those
distinct rationale and provenance elements remain relevant. No STAR operation
was run.

### F65 — Report template owner description

The [template README](../../src/emrys/reporting/templates/README.md) lines 3–7
credits Python view builders with each view's title, introduction, sections,
and end note. The packaged
[template](../../src/emrys/reporting/templates/run_report.html.j2) sets the
title at line 2, introductory and boundary text at 172–180, section headings
throughout, and both end notes at 443–445. The
[scientific view builder](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/view.py)
lines 115–143 and [core report context](../../src/emrys/reporting/_run_report/context.py)
lines 474–484 provide the view selection, banners, data, and related labels.
The README assigns static presentation ownership to Python too broadly. This
is a source comparison, not an observed output discrepancy; no report was
rendered.

### F66 — Step 09 QC summary input scope

The [Step 08 contract](../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md)
lines 11–17 and [Step 09 contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
lines 12–18 say Step 09 consumes the Step 08 sites and input receipt, not the
QC summary. The [analysis module](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py)
lines 364–374 requires `step08_summary_v1`, and its task planner at 191–195 and
280–289 includes that file in `TaskInputV1`. The producer and validator argv
at 196–278 do not pass it; the computation claim is accurate in that narrower
sense. [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 1195–1202 requires declared inputs, and the
[task runner](../../src/emrys/orchestration/run_coordinator/task.py) lines
2600–2616 and 2788–2790 checks them for stability. The guides omit this Run
dependency and provenance role. The [stage map](../../src/emrys/contracts/STAGE_MAP.md)
lines 58–77 calls its edge roster complete but names only sites and receipt
for Step 08→09, reflecting the narrower computational dependency. It does not
describe the additional task input. No task or scientific analysis was executed.

### F67 — Step 09 producer language in source topology

The [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) line 49
calls the Step 09 contract consumer a “Python producer.” The
[Step 09 owner](../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
lines 13–18 identifies `step_09_cmh_editing_site_calling.R` as the result
producer. The [Python module planner](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py)
lines 179 and 191–237 builds a guarded R command for that script. The topology
wording misnames the production owner; the Python planner and validator retain
their own roles. This is static source comparison, not a runtime or scientific
behavior finding.

### F68 — Slurm diagnostic artifact bounds

The [CI workflow guide](../../.github/workflows/README.md) lines 15–22 says
only bounded, redacted setup and terminal diagnostics enter the infrastructure
artifact. The [setup script](../../tests/tools/configure_ci_slurm.sh) lines
43 and 51–58 copies Slurm configuration, full service status, and service
journals into that directory with no line limit or redaction step. The
[workflow](../../.github/workflows/ci.yml) lines 1344–1358 does the same for
terminal status and journals, then uploads the runtime/Slurm evidence directory
at 1371–1383. The commands deliberately exclude private accounting
configuration and database journals. This contradicts the guide's general
“bounded, redacted” description; no CI artifact contents were inspected, and
no sensitive-data disclosure is inferred.

### F69 — Python shard inventory scope

The [test baseline](../design/TEST_BASELINE.md) lines 48–51 says CI shards the
complete Python inventory and requires complete receipts. The
[shard planner](../../tests/tools/python_test_shards.py) lines 18–23 and 93–98
excludes `test_package_distribution.py` and `test_python_test_shards.py` from
collection; receipt verification at 299–355 proves completeness only against
that filtered set. Ordinary CI runs those tests separately through
[Make targets](../../scripts/make_quality.mk) lines 83–85 and 211–219 and
[static/wheel jobs](../../.github/workflows/ci.yml) lines 164–186. Scheduled
Python 3.11 runs skip those ordinary jobs at workflow lines 164–169 and
993–997 while running filtered shards at 1023–1097. Manually selected
Python 3.14 or 3.11 shards can likewise run without `static-wheel` because
its dispatch flag at 164–169 is independent. The [test-tool guide](../../tests/tools/README.md)
lines 7–8 also calls the receipts the “exact test inventory” without stating
the two-file filter. The baseline's unqualified “complete Python inventory”
exceeds these shard-only evidence scopes; this does not establish a failed
test or broken merge gate.

### F70 — Omitted site does not always mean direct

The [Runbook](../operations/RUNBOOK.md) lines 238–248 says synthetic Init
without `--site` writes a direct execution profile; lines 280–284 advise
omitting `--site viking` for a direct-host study. The
[shared parser](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
lines 57–62 instead defaults `--site` from `EMRYS_SITE`, and lines 66–82 map
`viking` to Slurm placement. Both the
[synthetic](../../src/emrys/orchestration/run_coordinator/synthetic_fixture.py)
line 705 and [own-study](../../src/emrys/orchestration/run_coordinator/onboarding.py)
line 685 Init parsers use it; synthetic publication passes the selected site
into its profile at synthetic-fixture lines 654–666 and 773. The
[CLI](../../src/emrys/__main__.py) lines 349–358 loads a saved `.env` before
argument parsing, and [onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 153–189 can populate `EMRYS_SITE=viking`. A
[source test](../../tests/orchestration/run_coordinator/test_onboarding.py)
lines 285–298 pins the synthetic default. The mismatch is conditional on an
inherited or saved site default; no CLI or host command was run.

### F71 — Quickstart Projects home default and later path

The [Quickstart](../../quickstart.md) lines 54–61 says pressing Enter accepts
the default `Projects` home and later commands use those defaults. Guided Init
at lines 92–100 uses that saved home, but validation at lines 126–132 and
reconnection at 260–269 hard-code `$EMRYS_SOURCE_ROOT/Projects/pum1-study`.
[Setup](../../src/emrys/orchestration/run_coordinator/onboarding.py) lines
214–255 offers an inherited `EMRYS_PROJECTS_ROOT` ahead of the repository's
`Projects` directory and saves the selected path; named Init at 1261–1269
creates under it. With an inherited alternate home, pressing Enter makes the
documented later `cd` miss the Project, although Init prints the actual path.
The same Quickstart lines say to leave the optional log root empty, while an
inherited `EMRYS_LOG_ROOT` is saved without prompting at onboarding lines
237–250. These are conditional reader-route mismatches, not failures in a
fresh environment with no such process defaults. No command was run.

### F72 — Automatic reporting scope for processing-only Runs

The [reporting owner](../../src/emrys/reporting/README.md) lines 3–5 says
`emrys run` and `resume` report automatically unless `--no-report` is set and
describes `emrys report [RUN]` without a Run-scope qualification. A supported
[processing-only route](../operations/RUNBOOK.md) lines 510–521 creates a
successful Steps 00–06 Run with no report. In
[control](../../src/emrys/orchestration/run_coordinator/control.py) lines
1489–1516 and 1569–1570, reporting is not applicable to a partial scientific
Run and returns before invoking the report operation. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1200–1205 states this distinction, and a
[direct fixture](../../tests/orchestration/run_coordinator/test_reporting_operation.py)
lines 187–214 checks that explicit reporting refuses processing-only Runs
without writes. The owner README's automatic-reporting description lacks
the full-Run condition. This is a static source/test comparison; no Run or
report was executed.

### F73 — Profile create explicit placement requirement

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 828–830 says `emrys profile create NAME` requires an explicit built-in
site or direct/Slurm placement. Its [parser](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 311–317 makes the choice optional when `EMRYS_SITE` is set, and the
[shared site argument](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
lines 57–62 defaults from that environment. Profile creation at onboarding
lines 349–375 uses the resulting site when `--placement` is absent. The
[source test](../../tests/orchestration/run_coordinator/test_onboarding.py)
lines 285–298 confirms `profile create cluster` selects `viking` without a
placement flag when `EMRYS_SITE=viking`. The requirement is conditional:
explicit selection is still required with no site default. This is a parser
and source-test comparison; no profile was created.

### F74 — Final-check command omits R library prerequisite

The [engineering guide](../operations/ENGINEERING_CONVENTIONS.md) lines
87–91 presents `RSCRIPT_BIN=/absolute/path/to/Rscript make -s all-checks` as
the assembled final gate. The [Make target](../../scripts/make_quality.mk)
lines 238–244 starts `run_validation.py`, whose
[guarded-R lane](../../tests/tools/run_validation.py) lines 207–215 invokes
`validation-guarded-r`. That target runs `r-check` and `local-real-r-test`
at Make lines 195–197; both require `RENV_LIBRARY` to name an existing
directory at lines 101–124. The validation driver inherits the ambient
environment rather than supplying the library itself (lines 281–293).
The displayed command needs an already exported `RENV_LIBRARY` to pass this
lane; the guide does not state that prerequisite. No gate was run.

### F75 — Validation lane diagnostic bounds

The [test baseline](../design/TEST_BASELINE.md) lines 90–91 says failed,
interrupted, and peer-cancelled local validation lanes retain bounded
diagnostics. The [validation driver](../../tests/tools/run_validation.py)
copies each failed or interrupted lane's entire log at lines 234–240 and
prints the entire failed log at 243–249 and 444–455. Peer-cancelled logs are
also retained at 466–485. These paths show no byte or line limit, so the
unqualified “bounded” claim exceeds the source behavior. This is separate
from F68's uploaded Slurm diagnostic wording. No lane ran and no log contents
were inspected.

### F76 — Step 07 dataset-promotion route

The [Step 07 test guide](../../tests/stages/partitioned_cohort_mpileup/README.md)
lines 9–12 says its linked
[stage contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
owns “dataset-promotion criteria.” That contract's inputs, output, validation,
consumer, and evidence-ceiling sections (lines 24–119) state no such criteria;
a repository documentation search found the phrase only in the test guide.
The link therefore does not deliver the named authority. This is a reader-route
finding, not an observed Step 07 execution or scientific defect.

### F77 — Omitted application-model test suite

The [orchestration contract test index](../../tests/contracts/orchestration/README.md)
lines 3–10 describes `test_orchestration_contracts.py` and
`test_reporting_ledger_contracts.py` but omits the present
[`test_application_model_contracts.py`](../../tests/contracts/orchestration/test_application_model_contracts.py).
That suite's opening identifies immutable Analysis/Plan/Run protections, with
content identity and canonicalization cases at lines 270–428 and Run authority
cases at 623–757. The index thus omits a substantial direct contract suite;
the test file exists, and no test result was inferred.

### F78 — Omitted Python shard-duration baseline

The [test-baselines index](../../tests/baselines/README.md) lines 1–9
describes only `python_coverage.json`. Its sibling
[`python_test_durations.json`](../../tests/baselines/python_test_durations.json)
has default and selected node-duration values (lines 1–9).
The [shard planner](../../tests/tools/python_test_shards.py) names that file
at line 19, validates it at 66–90, and uses it to weight assignments at
139–164; the [Make lane](../../scripts/make_quality.mk) passes it at 134–140.
The index omits an active tracked baseline with a different purpose. Those
values are scheduling estimates, not test outcomes or coverage; no shard ran.

### F79 — Shared fixture consumer count

The [fixtures index](../../tests/fixtures/README.md) lines 3–5 says the
directory holds tracked inputs used by more than one test owner. The tracked
inventory at this revision contains one data fixture,
[`make_target_expansions.json`](../../tests/fixtures/public_cli_contracts/make_target_expansions.json),
and [one test module](../../tests/test_public_cli_contracts.py) names it at
lines 22–27. A repository reference search found no second test consumer.
This is a current tracked-use discrepancy; it does not rule out future shared
fixtures or imply that the existing fixture should move.

### F80 — Alignment helper tool boundary

The [alignment-library guide](../../src/emrys/libraries/alignments/README.md)
lines 3–14 describes parsers and says they run no scientific tools.
[`bam.py`](../../src/emrys/libraries/alignments/bam.py) lines 32–53 invokes a
supplied `samtools` executable for `quickcheck -v` and `view -H` through
`subprocess.run`. The [canonical BAM validator](../../src/emrys/stages/canonical_bam/validator.py)
calls that helper at lines 55–70, as do the duplicate-marking and split-N-Cigar
validators. These are read-only validation calls, and the guide's no-tool
boundary does not describe them. No output mutation or runtime result is inferred.

### F81 — Terminal task result versus verified marker

The [orchestration contract index](../../src/emrys/contracts/orchestration/README.md)
lines 24–30 says each task has a terminal result and a verified marker binding
it. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 966–976 publishes the marker only after producer success, output
admission, validator completion, and semantic all-pass; interruption may leave
neither record. A [task test](../../tests/orchestration/run_coordinator/test_task.py)
lines 768–776 asserts a failed terminal result without a verified marker.
The index therefore applies a success-only evidence form to failed tasks.
This is a wording discrepancy, not an observed execution defect.

### F82 — Reference-provenance private test calls

The [test guide](../../tests/evidence/reference_provenance/README.md) lines
3–8 says the suite calls the public reconciliation command and uses private
`reconciler.py` functions only to inject failures. Its
[test module](../../tests/evidence/reference_provenance/test_reference_provenance.py)
directly calls `load_inventory`, `observe`, and `render` to build report data
at 181–184, uses that path for a parser-row assertion at 268–287, and calls
`publish` directly in publication-fault cases at 438 and 474. The private
calls have more than failure-injection scope. This static comparison does not
establish test independence or a runtime result; no test ran.

### F83 — Direct-host study versus allocation-only rule

The [delivery decision](../design/decisions/repository-and-delivery.md) lines
12–17 says heavy scientific work runs only in an approved whole-Run Slurm
allocation. The [root environment summary](../../README.md) lines 44–47
supports direct execution on one host, and the [Runbook](../operations/RUNBOOK.md)
lines 223–230 and 267–283 describes an own-data Run on an approved non-Slurm
compute host. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 3–5 and 365–375 also defines direct placement. The decision does not
state where a direct study ceases to be local development and becomes the
“heavy” work it reserves for Slurm. This is an operator scope question, not
a claim that direct execution is unsafe or that either route was exercised.

### F84 — Copied Init manifest path fields

The [configuration guide](../../configs/README.md) lines 20–22 says named
Init copies validated manifest content into the Project, and lines 80–85
says copied manifests retain supplied content. For a supplied sample manifest,
[Init](../../src/emrys/orchestration/run_coordinator/onboarding.py) lines
1125–1139 resolves relative FASTQ paths from that manifest's directory and
serializes absolute paths into the Project copy. It similarly resolves a
partition `regions_file` at 1141–1158; a
[focused test](../../tests/orchestration/run_coordinator/test_onboarding.py)
lines 1561–1592 asserts the resulting absolute regions-file path. The guide's
Project-relative path rule at lines 24–29 and 229–231 describes persisted
Project use, while supplied external manifests cross an Init boundary.
“Copy” preserves the referenced inputs but can change path fields and bytes.
No Init or Run was executed in this audit.

### F85 — Status vocabulary exceptions

The [main backlog](backlog_matrix.md) lines 24–29 defines Open, In progress,
Verification pending, Deferred, Completed, and Closed. Its active
`REPORT-ROSTER-01` row at line 295 instead uses `Needs decision`, the only
undefined status among 51 ID rows in a static count. The
[polish campaign](polish-campaign.md) line 435 calls that outcome open. The
decision itself remains unresolved; this finding concerns the matrix's
status vocabulary and assigns no new authority or acceptance state.
The delegated [CV backlog](cluster_verification_backlog.md) line 13 imports
those status meanings, yet its Status column calls CV-12 `Discard` at line
106. The detailed card at 3026–3037 records a deliberate terminal
disposition to stop causal reconstruction, and the
[campaign charter](cluster_verification_campaign.md) lines 173–177 permits
rejection by decision. This is a label-vocabulary distinction; the disposition
and its unknown original cause remain intact.

### F86 — Step 02b parallel-validation claim

The [Step 02b contract](../../src/emrys/evidence/canonical_bam_qc/CONTRACT.md)
lines 25–28 says the operation may run in parallel with the Step 02 validator
once a stable canonical pair exists. The current
[processing profile](../../src/emrys/workflow/contracts/local_cmh_v2.json)
lines 118–123 makes Step 02 a direct predecessor of 02b. The
[task loader](../../src/emrys/contracts/orchestration/artifact_inventory.py)
lines 42–57 carries that edge into `predecessors`, and the
[Snakefile](../../src/emrys/workflow/Snakefile) lines 402–424 waits for the
predecessor's verified marker. The [task runner](../../src/emrys/orchestration/run_coordinator/task.py)
validates and checks semantic all-pass at lines 2763–2779 before publishing
that marker at 2883–2920. Thus an ordinary Run cannot overlap 02b with Step
02 validation. This is a timing statement about the admitted Run graph, not
an observed execution defect or a claim about a standalone worker invocation.
F99 records the related Step 06→07 data-input versus Run-scheduling distinction.

### F87 — Step 05 scratch owner in optimization candidate

The [optimization campaign](optimization_campaign.md) lines 199–212 says
Step 05 deliberately puts GATK spill under the output directory because CSU
`/tmp` can be too small, citing an earlier pinned Step 05 revision. The
current [worker](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh)
lines 121–124 passes `EMRYS_TASK_WORK_DIR` to both Java and GATK temporary
options. The [stage contract](../../src/emrys/stages/split_n_cigar/CONTRACT.md)
lines 56–60 calls it runner scratch. The
[runner](../../src/emrys/orchestration/run_coordinator/task.py) derives an
output-staging-adjacent scratch path at 1465–1469, creates it at 1546–1575,
and binds both `EMRYS_TASK_WORK_DIR` and `TMPDIR` at 2698–2704. Thus the
candidate's present-tense ownership explanation has drifted, while the
scratch remains output-adjacent. The institutional fast-scratch performance
question was not measured or decided in this audit.

### F88 — Old Slurm memory preflight proposal

The [polish campaign](polish-campaign.md) dates its source audit to
`fdf76760` at lines 35–44, then item 36 at 798–811 calls explicitly
undersized Slurm-memory preflight missing and describes rejection as the
remaining outcome. The current [main backlog](backlog_matrix.md) line 172
marks `SCHED-01` Verification pending and records the effective-profile CPU
and explicit-memory check before submission, Doctor repair planning, and
profile creation. The [CV-11 card](cluster_verification_backlog.md) lines
2994–2996 and 3014–3024 records that implemented slice and integrated CI
checks while retaining institutional heterogeneous-node acceptance. Item
36 is a dated proposal, not the current software status. This audit did not
rerun the checks or establish institutional behavior.

### F89 — One-Run wording before Run creation

The [Runbook](../operations/RUNBOOK.md) lines 385–394 introduces the
`emrys validate`, `doctor`, `run`, `inspect` sequence as applying to a ready
Project “with one Analysis and one Run.” The phrase can describe an already
existing Run, while [`_plan_run`](../../src/emrys/orchestration/run_coordinator/control.py)
lines 357–367 plans a new one and validates its destination at line 424.
[Run admission](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 1566–1617 permits a matching pristine committed Run with no Attempt,
but refuses an existing Run with Attempt entries at 1588–1597 and directs the
reader to inspect or resume it. The Runbook may intend the post-command
cardinality; it does not state that precondition. No command was exercised.

### F90 — Completed tooling history in polish campaign

The [polish campaign](polish-campaign.md) has five completed tooling and
public-CLI sections at lines 459–468, 479–488, 502–512, 537–560, and
930–951: 77 physical lines in total. Their repeated disposition and hosted-CI
facts for `DEV-01`, `CI-01`, and `CLI-VERSION-01` also appear in the current
[main matrix](backlog_matrix.md) lines 340–356. The [test baseline](../design/TEST_BASELINE.md)
lines 73–85 owns current validation-lane policy, while the
[Runbook](../operations/RUNBOOK.md) lines 184–188 owns the public version
route. The polish sections also retain unique facts: seven ShellCheck fixes,
the 78-file/2,101-line formatting baseline, staged-hook observations,
35-task and guarded-R test preservation, timing limits, and version/parser
rationale. The 77 lines are a review surface, not a demonstrated saving or
permission to remove evidence.

### F91 — Repeated stage and evidence contract openings

The first paragraphs of all ten stage and both evidence `CONTRACT.md` files
span 48 physical lines: seven four-line and three three-line stage openings
(37), plus five- and six-line evidence openings (11). For example,
[canonical BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md) lines 3–6
and [Step 02b QC](../../src/emrys/evidence/canonical_bam_qc/CONTRACT.md)
lines 3–7 restate historical aliases and
[STAGE_MAP](../../src/emrys/contracts/STAGE_MAP.md) ownership, while
[RSeQC](../../src/emrys/evidence/rseqc_orientation/CONTRACT.md) lines 3–8
also names its repository-path producer command. The map already gives
all identities at lines 19–34, and adjacent owner READMEs identify their
routes. Each contract still has local worker/validator classification and
unique dependencies, consumer rules, and evidence limits. Retaining two to
three local opening lines per contract suggests only an illustrative 12–24
net-line opportunity; no edit or saving was verified.

### F92 — Python lock checks before institutional R restoration

The [Runbook](../operations/RUNBOOK.md) lines 685–694 places Python lock and
workflow-environment checks before its institutional R restore procedure.
The [engineering guide](../operations/ENGINEERING_CONVENTIONS.md) lines 77–85
already lists developer lock checks. The displayed `r-restore` and `r-check`
[Make targets](../../scripts/make_quality.mk) lines 92–110 invoke R without
uv; this source path does not establish the Python checks as direct command
prerequisites. The Runbook's R 4.6.1, external `RENV_PROJECT`, library/cache,
check, and recovery instructions at lines 696–726 serve a separate operator
need. Whether the preceding Python checks are an independent institutional
policy gate is unverified; no restoration was run.

### F93 — Repeated partition selector rule

The [configuration guide](../../configs/README.md) lines 191–199 says
`--region` and `--regions-file` can be combined when partition IDs are unique.
Lines 212–215 repeat the same combination and uniqueness rule after the
coordinate examples. The repeated statement spans about two physical lines;
the intervening BED versus one-based region semantics, examples, and the
separate supplied-manifest exclusions remain distinct. No Init command ran.

### F94 — Dashboard retirement closeout tense

The [main backlog](backlog_matrix.md) lines 327–331 ends the PR #169
integration account in present tense: dashboard retirement “still requires a
validated replacement.” Git attributes that paragraph to `550b54025` on
2026-09-14. The same backlog at line 180 records the institutional owner's
2026-09-17 acceptance of installed watch as the replacement and retirement of
the standalone wrapper/callers. The [CV campaign](cluster_verification_campaign.md)
lines 198–201 and [polish account](polish-campaign.md) lines 437–446 corroborate
that later disposition. The old sentence can describe its earlier checkpoint,
but without a date cue a current reader can take it as the remaining task.
Standard CI and institutional visual verification remain open in the later row;
acceptance of the replacement is not those proofs. No dashboard was run.

### F95 — Executed stop missing from logging adopter roster

The [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) line 57
calls its application-logging adopter list complete and names executing
`run`/`resume`, automatic and standalone reporting, and confirmed Doctor
repair, but no `stop`. The [logging contract](../design/LOGGING_CONTRACT.md)
lines 12–23, 88–90, and 193–200 owns an executed exact-request stop's single
maintenance attempt. The [current stop path](../../src/emrys/orchestration/run_coordinator/control.py)
lines 2441–2466 returns without a new log for an already-terminal target or
preview, then opens the attempt for admitted execution. This is index drift,
not evidence of a runtime logging defect. No stop was issued.

### F96 — Unrouted artifact schema version notes

The [artifact schema index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 links four current JSON schemas directly. Its adjacent
[v1](../../src/emrys/contracts/schemas/artifacts/v1/README.md),
[v2](../../src/emrys/contracts/schemas/artifacts/v2/README.md),
[v3](../../src/emrys/contracts/schemas/artifacts/v3/README.md), and
[v5](../../src/emrys/contracts/schemas/artifacts/v5/README.md) READMEs have
no inbound Markdown link outside this temporary audit in a repository link
scan, including directory links to their README targets. By comparison, the
[orchestration schema index](../../src/emrys/contracts/schemas/orchestration/README.md)
lines 6–11 routes through each of its three version READMEs. The four artifact files
occupy 32 physical lines and partly repeat the index. They also record
distinct shared-definition compatibility and test routes, Run/Attempt
separation, module-policy and historical-reader bounds, and rendering
provenance versus scientific validation. Thirty-two lines describe the review
surface, not a verified saving or grounds to delete those caveats.

### F97 — Past audit priority order in polish campaign

The [polish campaign](polish-campaign.md) lines 122–130 narrates second- and
third-pass priorities in present tense: installed-package and runtime identity,
report review, merge checks, FASTQ parity, command checks, and output discovery.
Its detailed proposals at lines 393–427, 620–711, 735–756, 775–834, and
874–911 retain the underlying subjects; the [main backlog](backlog_matrix.md)
lines 52–71 owns current accepted priorities and status. The
[documentation decision](../design/decisions/repository-and-delivery.md)
lines 91–94 places routine progress chronology in Git. These nine physical
lines are a review surface rather than a verified saving: the complete-command
measurement prerequisite and the boundary against parallel initiatives still
need to remain intelligible. No task status or performance claim changed.

### F98 — Worker prerequisites inside validation sections

The [Step 00c contract](../../src/emrys/stages/fasta_sidecars/CONTRACT.md)
lines 101–108 and [Step 05 contract](../../src/emrys/stages/split_n_cigar/CONTRACT.md)
lines 87–95 place similar absolute hash-Python, selected Java, and scrubbed
GATK-environment requirements inside their validation-interface sections.
The grouped [00c validator](../../src/emrys/stages/fasta_sidecars/validator.py)
lines 47–108 parses FASTA/FAI/DICT; the [05 validator](../../src/emrys/stages/split_n_cigar/validator.py)
lines 39–100 adds BAM/BAI and samtools checks. Their internal shell workers
probe and invoke Java/GATK at [00c](../../src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh)
lines 153–168 and [05](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh)
lines 113–124. The requirements describe worker execution, while placement
under validator prose can blur the public validator's prerequisites. This is
a repeated contract-placement issue, not evidence that a validator ran GATK.
The worker environment and each validator's independent checks remain distinct.

### F99 — Step 07 data inputs versus Run gate

The [Step 07 contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
lines 12–18 says it checks only Step 06 BAM/BAI presence and nonemptiness and
does not require Step 06 counts, validation evidence, or native marker. The
[Step 06 contract](../../src/emrys/stages/mechanical_orientation/CONTRACT.md)
lines 12–18 likewise describes the pairs as downstream data inputs. The
[processing profile](../../src/emrys/workflow/contracts/local_cmh_v2.json)
lines 160–164 declares the 06→07 edge; the [Run graph](../../src/emrys/workflow/Snakefile)
lines 402–420 waits for each predecessor's verified marker. Thus Step 07's
worker data admission is narrower than its scheduling prerequisite in an
ordinary Run. This extends F86's input-versus-order distinction to a separate
stage; no worker or Run was executed.
