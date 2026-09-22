# DOCS-01 discovery notes, third file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F62 onward. The sources below were read at PR head `b67e0eeb` on
2026-09-22. These are documentation observations, not runtime results or
accepted changes.

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
