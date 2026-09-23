# DOCS-01 discovery notes, third file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F62–F99; [fourth notes](docs-01-discoveries-fourth.md) begin at F100.
F62–F64 use pinned revision `b67e0eeb`; F65–F66 began at
`cf94af08`, with F66 extended at `9c4fafdc`; F67–F70 use `c0a6027a`;
F71 uses `9c4fafdc`; F72–F73 use `b3af5d9e`; F74–F77 use `ab25ea9b`;
F78–F83 use pinned revision `7a07d502`; F84–F88 use `ce9a3289`;
F89 uses local head `39a21034`; F90–F93 and the F85 extension use `9c0264d3`;
F94–F96 and F22/F53 extensions use `e90c85f4`; F94 was extended at `688f7117`.
F97–F99 and the F50/F56/F69/F86 extensions use local head `7adde22a`;
F99 was extended at `b62e207b`, all read on 2026-09-22.
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
measured performance discrepancy. No benchmark was executed. The
[SETUP-02 row](backlog_matrix.md) line 176 already owns eventual helper and
documentation retirement.

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
lines 124–134 already own those current mechanics. The decision at lines
29–34 also states that validation inspects the three configured values in
`genomeParameters.txt`; the [STAR-index contract](../../src/emrys/stages/star_index/CONTRACT.md)
lines 96–99 owns that current check. The decision's original EV/PUM1 values,
STAR scaling rationale, mechanical-versus-biological boundary, and pinned
STAR manual citation remain distinct rationale and provenance. Fifteen body
lines might become nine to eleven after owner routing, a conditional four-to-six
line saving. The heading has no tracked inbound link but remains a decision
destination. No draft, link check, or STAR operation was run.

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
2600–2616 and 2788–2790 checks them for stability. The owner descriptions
omit this Run task-input and provenance role. The
[stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 58–77 inventories
direct artifact edges, not every bound task input; its roster is not shown to
be incomplete. No task or scientific analysis was executed.

### F67 — Step 09 producer language in source topology

The [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) line 49
calls the Step 09 contract consumer a “Python producer.” The
[Step 09 owner](../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
lines 13–18 identifies `step_09_cmh_editing_site_calling.R` as the result
producer. The [Python module planner](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py)
lines 88–89, 130–140, and 179–237 consumes Step 09 contract facts and builds a
guarded R command for that script. “Python producer” may mean that Python
planner, but can also read as the result producer. This is a role-label
ambiguity, not an established ownership or scientific behavior error.

### F68 — Slurm diagnostic artifact bounds

The [CI workflow guide](../../.github/workflows/README.md) lines 15–22 says
only bounded, redacted setup and terminal diagnostics enter the infrastructure
artifact. The [setup script](../../tests/tools/configure_ci_slurm.sh) lines
43 and 51–58 copies Slurm configuration, full service status, and service
journals into that directory with no byte/line cap or content-redaction step. The
[workflow](../../.github/workflows/ci.yml) lines 1344–1358 does the same for
terminal status and journals, then uploads the runtime/Slurm evidence directory
at 1371–1383. Capture has a finite service and file scope and deliberately
excludes private accounting configuration and database journals. The guide's
unqualified “bounded, redacted” description exceeds these transformations; no
CI artifact contents were inspected or sensitive-data disclosure inferred.

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

At local audit head `d18470c8`, the [Projects index](../../Projects/README.md)
lines 3–6 also says named Init from the repository root creates each Project
there. That route has the same inherited-home exception; it is accurate when
setup actually selected the checkout's `Projects` directory.

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

**Dismissed for DOCS-01 at `1db7a88d`.** The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 828–830 requires a selected built-in site or direct/Slurm placement,
not necessarily a CLI flag. The
[shared site argument](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
lines 57–62 accepts `EMRYS_SITE` as that selection; the
[parser](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 311–317 and [source test](../../tests/orchestration/run_coordinator/test_onboarding.py)
lines 285–298 confirm it. With no site default, explicit selection remains
required. There is no contract conflict or useful compression here. This was
a static source/test comparison; no profile was created.

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

**Dismissed for DOCS-01 at `27844f15`.**
The [test baseline](../design/TEST_BASELINE.md) lines 90–91 says failed,
interrupted, and peer-cancelled local validation lanes retain bounded
diagnostics. The [validation driver](../../tests/tools/run_validation.py)
limits the lane set at 21–27, retains complete failed/interrupted logs at
234–240, prints complete failed logs at 243–249 and 444–455, and retains
peer-cancelled logs at 466–485. No byte cap is shown, but “bounded” does not
claim one; finite lane/file scope is a plausible reading. The volume
question establishes no overclaim or useful reduction. This differs from
F68's Slurm uploads. No lane ran or log was inspected.

### F76 — Step 07 dataset-promotion route

The [Step 07 test guide](../../tests/stages/partitioned_cohort_mpileup/README.md)
lines 9–12 says its linked
[stage contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
owns “dataset-promotion criteria.” That contract's inputs, output, validation,
consumer, and evidence-ceiling sections (lines 24–119) state no such criteria;
a repository documentation search found the phrase only in the test guide.
The contract's lines 47–64 instead define mechanical VCF publication and
validation; passing those checks cannot promote candidates to validated
variants or editing sites. The test guide's own lines 10–12 retain that caveat.
No current dataset-promotion owner was identified by this documentation pass,
so the link does not deliver the named authority. This is a reader-route
finding, not an observed Step 07 execution or scientific defect.

### F77 — Omitted application-model test suite

**Dismissed for DOCS-01 at `71ac2272`.** The index makes no complete-roster claim.
The [orchestration contract test index](../../tests/contracts/orchestration/README.md)
lines 3–10 describes `test_orchestration_contracts.py` and
`test_reporting_ledger_contracts.py` but omits the present
[`test_application_model_contracts.py`](../../tests/contracts/orchestration/test_application_model_contracts.py).
That suite's opening identifies immutable Analysis/Plan/Run protections, with
content identity and canonicalization cases at lines 270–428 and Run authority
cases at 623–757. The index thus omits a substantial direct contract suite;
the test file exists, and no test result was inferred.

### F78 — Omitted Python shard-duration baseline

**Dismissed for DOCS-01 at `71ac2272`.** The snapshot guide makes no all-baselines claim.
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
One module may cover multiple command owners; at recheck head `2398f144`,
this concern was dismissed. No discrepancy or relocation case is established.

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

The [repository safety guard](../../AGENTS.md) lines 62–64 and
[delivery decision](../design/decisions/repository-and-delivery.md) lines
12–17 reserve heavy alignment, sorting, mpileup, and analysis for an approved
grouped whole-Run Slurm allocation. The [Runbook](../operations/RUNBOOK.md)
lines 223–230 and 267–283 offer an own-data full Run on an approved non-Slurm
compute host without limiting that route to tiny or light work. The admitted
[stage map](../../src/emrys/contracts/STAGE_MAP.md#direct-dag-edges) includes
the named heavy stages in the full workflow. This is a documentation
policy-route conflict. The [root environment summary](../../README.md) lines
44–47 and [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 3–5 and 365–375 still support direct placement and tiny synthetic
fixtures; no direct or institutional Run was exercised in this audit.

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
The delegated [CV backlog](cluster_verification_backlog.md) calls CV-12
`Discard` at line 106, but its detailed card at 3026–3037 explicitly explains
that terminal decision. It is a deliberate exception, not a target for status
normalization; its unknown original cause remains intact.

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
that marker at 2883–2920. Thus 02b cannot overlap its *corresponding sample's*
Step 02 validation in an ordinary Run; different samples may overlap. This
describes Run order, not an execution defect; standalone capability remains valid.
F99 records the related Step 01→02 and Step 06→07 data-input versus
Run-scheduling distinction.

### F87 — Step 05 scratch owner in optimization candidate

The [optimization campaign](optimization_campaign.md) lines 199–212 says
Step 05 puts GATK spill under the output directory because CSU `/tmp` can be
too small, citing pinned historical worker code at line 436. The current
[worker](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh)
lines 121–124 receives `EMRYS_TASK_WORK_DIR`; the
[runner](../../src/emrys/orchestration/run_coordinator/task.py) creates
output-adjacent scratch at 1465–1469 and 1546–1575 and binds that variable
at 2698–2704. The placement claim still holds. The campaign prose does not
assign scratch ownership to the worker, and its pinned link can serve as
historical provenance. This alleged owner-drift finding is **dismissed after
recheck**; no current documentation error or saving is established. The
institutional fast-scratch performance question remains unmeasured.

### F88 — Old Slurm memory preflight proposal

**Dismissed for DOCS-01 after recheck at `633625a7`.**
The [polish campaign](polish-campaign.md) dates its source audit to
`fdf76760` at lines 35–44; item 36 at 798–811 calls undersized Slurm-memory
preflight missing. Current [execution profile](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
lines 188–207 checks CPU and explicit memory, and
[submission](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
line 829 invokes it before scheduler request. [Focused tests](../../tests/orchestration/run_coordinator/test_execution_profile.py)
lines 260–287 cover rejection without a log write. The [SCHED-01 row](backlog_matrix.md)
line 172 and [CV-11 card](cluster_verification_backlog.md) lines 2994–3024
distinguish integrated checks from institutional heterogeneous-node acceptance.
Item 36 is an explicit historical proposal, not a present-tense guidance error.
No useful compression is established; no check or cluster work ran here.

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

**Dismissed as a separate DOCS-01 reduction after recheck at `31c54ed8`.**
The [polish campaign](polish-campaign.md) has five completed tooling and
public-CLI sections at lines 459–468, 479–488, 502–512, 537–560, and
930–951: 77 physical lines in total. Repeated hosted-CI/status clauses at 461,
481, 504, 539–540, and 935–936 also appear in the
[main matrix](backlog_matrix.md) lines 340–356. Those seven physical lines
could yield only zero to two lines after reflow. The sections retain unique
ShellCheck fixes, the 78-file/2,101-line formatting baseline, hook observations,
35-task and guarded-R preservation, timing limits, and version/parser rationale.
The [test baseline](../design/TEST_BASELINE.md) and
[Runbook](../operations/RUNBOOK.md) own current lane and version routes.
No useful independent reduction of the 77-line review span is established.

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
routes. Each contract still has a useful local alias and worker/validator role,
plus unique dependencies, consumer rules, and evidence limits. All twelve have
a three-line alias/map preamble; a two-line form might save about one line per
contract. The 24 map-authority lines and full 48-line openings are review spans,
not savings estimates. No replacement or net saving was verified.

### F92 — Python lock checks before institutional R restoration

The [Runbook](../operations/RUNBOOK.md) lines 685–694 places a ten-line Python
lock/workflow check prelude before institutional R restoration. The
[engineering guide](../operations/ENGINEERING_CONVENTIONS.md) lines 77–85
owns developer lock checks. The displayed `r-restore` and `r-check`
[Make targets](../../scripts/make_quality.mk) lines 92–110 call R without uv;
the [restore script](../../src/emrys/resources/runtime/restore_r_environment.R)
at 43–82 requires `RENV_PROJECT`, R 4.6.1, and a selected renv lock. The
[R owner](../../src/emrys/renv/README.md) lines 16–25 routes operator
restoration to the Runbook but does not name Python checks. This source path
does not establish them as direct R prerequisites. Quickstart lines 43–45
initializes the workflow environment earlier, while the R targets do not use it.
The ten-line prelude could yield roughly seven fewer local lines; a separate
institutional gate remains unverified. Preserve R commands, library/cache,
checks and recovery at 696–726. No restore ran.

### F93 — Repeated partition selector rule

The [configuration guide](../../configs/README.md) lines 191–199 says
`--region` and `--regions-file` can be combined when partition IDs are unique.
Lines 212–215 repeat that rule after the coordinate examples; line 214's
advice to declare each selector remains distinct. One physical line is a
plausible saving, not a verified edit. BED versus one-based region semantics,
examples, and supplied-manifest exclusions remain. No Init command ran.

### F94 — Dashboard retirement closeout tense

At local audit head `3cfe4eff`, the
[CV backlog](cluster_verification_backlog.md) line 79 still assigns standalone
entry-point/caller/name retirement to `DASHBOARD-RETIRE-01` in its current
“Remaining acceptance” table. The [main backlog](backlog_matrix.md) line 180
records the institutional owner's September 17 acceptance of installed watch
and wrapper/caller retirement. Main-backlog lines 327–331 and the CV-16 card
at 3173–3184 are dated older checkpoints, not current competing status.
The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 498–499 still claims direct loading under isolated system Python. Shared
scheduler mechanics remain, but [dashboard.py](../../src/emrys/orchestration/run_coordinator/dashboard.py)
line 20 uses a package-relative import, [entry points](../../pyproject.toml)
lines 39–40 expose only `emrys`, and [CV-20](cluster_verification_backlog.md)
lines 3378–3384 says isolated standalone loading was retired later. The old
account is a historical checkpoint; the current table and contract can misroute
a reader. This does not prove installed-package isolated import fails. Preserve
the contract's scheduler identity rules; standard CI and institutional visual
verification remain open. No dashboard was run.

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

**Dismissed for DOCS-01 at `27844f15`.**
The [artifact schema index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 links all four current JSON schemas directly. Its adjacent
[v1](../../src/emrys/contracts/schemas/artifacts/v1/README.md),
[v2](../../src/emrys/contracts/schemas/artifacts/v2/README.md),
[v3](../../src/emrys/contracts/schemas/artifacts/v3/README.md), and
[v5](../../src/emrys/contracts/schemas/artifacts/v5/README.md) READMEs have
no inbound non-audit Markdown link in a limited scan. Unlike the
[orchestration index](../../src/emrys/contracts/schemas/orchestration/README.md)
lines 6–11, this index routes to schema files, not version notes. The four
READMEs occupy 32 physical lines but retain distinct limits: active v1
definitions/compatibility; v2 Run versus Attempt history; v3 module policy
without historical summary/receipt readers; and v5 receipt publication, not
scientific validation. Link absence is not evidence that these rules are
duplicated or expendable. Adding routes would expand documentation; no useful
DOCS-01 reduction follows. Directory and external readers remain unverified.

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

### F99 — Stage data inputs versus Run gates

**Dismissed for DOCS-01 at `27844f15`.**
The [Step 07 contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
lines 12–18 describes Step 06 BAM/BAI as direct worker inputs, without
requiring Step 06 counts, validation evidence, or native marker. The
[Step 06 contract](../../src/emrys/stages/mechanical_orientation/CONTRACT.md)
lines 12–18 likewise describes downstream data inputs. The
[processing profile](../../src/emrys/workflow/contracts/local_cmh_v2.json)
lines 160–164 declares the edge, while the
[Run graph](../../src/emrys/workflow/Snakefile) lines 402–420 separately waits
for predecessor verified markers. At `b62e207b`, the
[Step 01 contract](../../src/emrys/stages/star_alignment/CONTRACT.md) lines
21–25 similarly calls STAR logs and the SJ table evidence outputs rather than
Step 02 worker inputs; the [profile](../../src/emrys/workflow/contracts/local_cmh_v2.json)
lines 112–116 passes BAM, while its [validator](../../src/emrys/stages/star_alignment/validator.py)
lines 49–116 checks all five Step 01 outputs. Worker input and Run scheduling
are distinct, accurate boundaries, already illustrated by F86. Adding Run
order to each stage contract would expand docs; no correction or saving is
established. No validator or Run was executed.
