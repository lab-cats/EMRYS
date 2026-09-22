# DOCS-01 discovery notes, third file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F62 onward. F62–F64 use PR head `b67e0eeb`; F65–F66 use `cf94af08`,
all read on 2026-09-22. These are documentation observations, not runtime
results or accepted changes.

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
dependency and provenance role. No task or scientific analysis was executed.
