# EMRYS presenter walkthrough

This is the presenter run-of-show, not the audience handout, authoritative
status ledger, report contract, or command owner. During a live demo, verify
live Git plus checks and retained artifacts for the exact commit; run only the
exact [`README.md`](README.md) procedure.

## Narrative

1. The repository translates a legacy, path-bound workflow into explicit
   scripts, SLURM wrappers, manifests, tests, and receipts.
2. Reference preparation and BAM processing establish reproducible inputs.
3. Library-orientation evidence is preserved without equating mechanical read
   groups with biological strand.
4. Cohort mpileup, deterministic preprocessing, and paired CMH analysis retain
   every candidate with explicit status.
5. Read-only artifact adapters and a canonical run summary make missing and
   failed evidence visible.
6. Static reports project that summary without running analysis or promoting
   state.
7. Review, adjudication, and biological interpretation remain external
   work-process records and never gate the EMRYS run.

## Populated synthetic report

Before presenting, generate the local synthetic report through the
[demo procedure](README.md).
Its current implementation and evidence ceiling remain in the
reporting owner, contracts, tests, and exact checks for the selected commit.

Start in the open `Computational results` category. Show the
not-scientifically-adjudicated notice, the significant subset, the complete
candidate view, and key per-sample QC. Emphasize that the source TSVs and
provenance remain authoritative and that the report contains no review or
approval gate. Use the linked handoff and runbook for current rendering
behavior.

## Suggested inspection order

1. [`../../README.md`](../../README.md)
2. [`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)
3. [`../architecture/diagrams/pipeline.mmd`](../architecture/diagrams/pipeline.mmd)
4. [`../tasks/backlog_matrix.md`](../tasks/backlog_matrix.md)
5. [`../design/DECISIONS.md`](../design/DECISIONS.md)
6. [PI discussion guide](PI_DEMO_REPORT.md)
7. [`../operations/RUNBOOK.md`](../operations/RUNBOOK.md)

## Scientific wording

Say:

- reverse-stranded / first-strand-style libraries;
- mechanical `FWD_like` and `REV_like` groups;
- CMH-ranked candidates;
- implemented, locally tested, real-runtime tested, or cluster-proven only
  when checks and retained artifacts bound to the exact commit support that
  state;
- external review or adjudication record only when that separate work product
  actually exists.

Do not say:

- validated editing sites;
- biologically proven orientation;
- review or biological interpretation completed from fixture evidence;
- report generation validated the computation;
- cluster-proven based on a tool probe or local test.

## Cohort evidence cue

The legacy
[`HANDOFF.md`](../operations/HANDOFF.md#cohort-and-preserved-scientific-evidence)
contains one historical cohort table selected for migration under `DOC-04`.
Do not present it as current or copy its fractions or sample status into this
guide. Emphasize that orientation evidence is not biological-strand proof and
that a mapping outlier is not, by itself, a pipeline failure.
