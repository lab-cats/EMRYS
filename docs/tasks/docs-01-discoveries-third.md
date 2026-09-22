# DOCS-01 discovery notes, third file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F62 onward. F62–F64 use PR head `b67e0eeb`; F65–F66 began at
`cf94af08`, with F66 extended at `9c4fafdc`; F67–F70 use `c0a6027a`;
F71 uses `9c4fafdc`; F72–F73 use `b3af5d9e`, all read on 2026-09-22.
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
993–997 while running filtered shards at 1023–1097. The baseline's unqualified
“complete Python inventory” exceeds the shard and nightly evidence scope;
this does not establish a failed test or broken merge gate.

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
