# PI demo evidence report

This document is a presentation snapshot of the evidence model. It is not the
live project status, command source, or roadmap. Consult
[`../operations/HANDOFF.md`](../operations/HANDOFF.md) before presenting.

## Executive summary

NORAD is a manifest-driven, local-first and SLURM-scaled reconstruction of a
Novogene RNA-seq/RNA-editing workflow. It separates:

- reproducible computation;
- local fixture and real-runtime testing;
- cluster execution evidence;
- structured scientific review;
- report rendering;
- biological interpretation.

The report layer cannot convert one category into another.

## Evidence model

| Layer | Question answered | What it does not prove |
| --- | --- | --- |
| Implementation | Does code exist for the declared contract? | That it ran on production data |
| Local fixtures | Do controlled cases behave as specified? | Real tool or cluster behavior |
| Real local runtime | Does the available runtime execute semantic fixtures? | Cluster compatibility |
| Cluster proof | Did declared computation run and reconcile on the cluster? | Scientific validity |
| Scientific review | Were evidence, decisions, and limitations recorded? | Biological causality |
| Report | Can evidence be presented deterministically? | Any new evidence state |

## Scientific caution

The cohort is paired-end and shows a reverse-stranded/first-strand-style
orientation pattern. Mechanical `FWD_like` and `REV_like` groupings remain
neutral. The legacy-compatible orientation policy is provisional.

Rows emitted by the CMH stage are “CMH-ranked candidates.” They are not
validated editing sites.

`science_review_complete_exploratory` permits only provisional reporting.
`biological_interpretation_ready` remains reserved until a separate policy and
evidence gate explicitly unlock it.

## Reporting contract

Reports consume one canonical run summary and only exact authorized
supplemental tables. They never discover inputs, invoke analysis, restore
dependencies, or change evidence state. Missing, failed, incomplete, blocked,
and unavailable evidence remains visible.

Every report must carry the applicable scientific-state banner and disclose
table truncation with the complete source path and hash.

## Discussion prompts

- Is the exact Novogene annotation release recoverable?
- What evidence is required to resolve biological orientation?
- Which sensitivity and replicate checks are mandatory?
- What is the approved production artifact retention policy?
- Which conclusions may be communicated under exploratory review?

Current answers and blockers belong in the handoff and questions documents,
not in this presentation snapshot.
