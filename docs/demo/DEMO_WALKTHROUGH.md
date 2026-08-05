# NORAD presenter walkthrough

This is the presenter run-of-show, not the audience handout, authoritative
status ledger, report contract, or command owner. During a live demo, use the
current [`HANDOFF.md`](../operations/HANDOFF.md) and
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); run only the exact
[`RUNBOOK.md`](../operations/RUNBOOK.md#generate-the-populated-synthetic-demo-report)
procedure.

## Narrative

1. The repository translates a legacy, path-bound workflow into explicit
   scripts, SLURM wrappers, manifests, tests, and receipts.
2. Reference preparation and BAM processing establish reproducible inputs.
3. Library-orientation evidence is preserved without equating mechanical read
   groups with biological strand.
4. Cohort mpileup, deterministic preprocessing, and paired CMH analysis retain
   every candidate with explicit status.
5. Scientific-review tooling records evidence and limitations separately from
   computation.
6. Read-only artifact adapters and a canonical run summary make missing and
   failed evidence visible.
7. Static reports project that summary without running analysis or promoting
   state.

## Populated synthetic report

Before presenting, generate the local synthetic report through the
[runbook procedure](../operations/RUNBOOK.md#generate-the-populated-synthetic-demo-report).
Its current implementation and evidence ceiling remain in the
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md#populated-demo-report).

Start in the open Overview category: the evidence banner, status, CMH-ranked
candidates, adjudication, and limitations appear first. Then expand QC and
orientation, Replicates and sensitivity, Review decisions, and Evidence and
provenance. Use the linked plan and runbook for current rendering behavior.

## Suggested inspection order

1. [`../../README.md`](../../README.md)
2. [`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)
3. [`../architecture/diagrams/pipeline.mmd`](../architecture/diagrams/pipeline.mmd)
4. [`../operations/HANDOFF.md`](../operations/HANDOFF.md)
5. [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md)
6. [PI discussion guide](PI_DEMO_REPORT.md)
7. [`../operations/RUNBOOK.md`](../operations/RUNBOOK.md)

## Scientific wording

Say:

- reverse-stranded / first-strand-style libraries;
- mechanical `FWD_like` and `REV_like` groups;
- CMH-ranked candidates;
- implemented, locally tested, real-runtime tested, or cluster-proven only
  when the handoff supports that exact state;
- exploratory/provisional when scientific review remains non-final.

Do not say:

- validated editing sites;
- biologically proven orientation;
- production review completed from fixture evidence;
- report generation validated the computation;
- cluster-proven based on a tool probe or local test.

## Cohort evidence cue

At the cohort-evidence stop, display the current
[`HANDOFF.md`](../operations/HANDOFF.md#cohort-and-preserved-scientific-evidence)
table and caveats directly. Do not copy its fractions or sample status into
this guide. Emphasize at the action point that orientation evidence is not
biological-strand proof and that a mapping outlier is not, by itself, a
pipeline failure.
