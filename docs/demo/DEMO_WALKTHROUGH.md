# NORAD demo walkthrough

This is presentation-oriented material, not an authoritative status ledger.
Use the current [`../operations/HANDOFF.md`](../operations/HANDOFF.md) and
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) during a live demo.

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

## Suggested inspection order

1. [`../../README.md`](../../README.md)
2. [`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)
3. [`../architecture/diagrams/pipeline.mmd`](../architecture/diagrams/pipeline.mmd)
4. [`../operations/HANDOFF.md`](../operations/HANDOFF.md)
5. [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md)
6. [`PI_DEMO_REPORT.md`](PI_DEMO_REPORT.md)
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

## Preserved cohort observation

All six paired-end libraries show the reverse-stranded/first-strand-style
RSeQC pattern. The exact fractions and evidence boundary are retained in the
handoff. `ABE_EV_2` is a mapping outlier but not, by that fact alone, a
pipeline failure.
