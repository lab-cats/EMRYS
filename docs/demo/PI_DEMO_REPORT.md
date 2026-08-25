# PI demo discussion guide

This is the PI/audience discussion view, not the presenter run-of-show, live
project status, command source, report contract, or dated snapshot. Before
presenting, verify live Git plus checks and retained artifacts for the exact
commit; this guide cannot establish current evidence.

## Discussion context

Use the root [`README.md`](../../README.md) for product identity and the current
[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) for system structure. The
discussion here separates evidence layers that must not be promoted into one
another.

## Evidence model

| Layer | Question answered | What it does not prove |
| --- | --- | --- |
| Implementation | Does code exist for the declared contract? | That it ran on production data |
| Local fixtures | Do controlled cases behave as specified? | Real tool or cluster behavior |
| Real local runtime | Does the available runtime execute semantic fixtures? | Cluster compatibility |
| Cluster proof | Did declared computation run and reconcile on the cluster? | Scientific validity |
| External research process | Were review, adjudication, and limitation records kept outside EMRYS? | Pipeline completion or biological causality |
| Report | Can evidence be presented deterministically? | Any new evidence state |

## Scientific caution

The legacy
[`HANDOFF.md`](../operations/HANDOFF.md#cohort-and-preserved-scientific-evidence)
contains one historical cohort snapshot selected for migration under `DOC-04`;
do not present it as current evidence. Reverse-stranded/first-strand-style
evidence does not make mechanical
`FWD_like` and `REV_like` groups biological strand. The legacy-compatible
orientation policy remains provisional.

Rows emitted by the CMH stage are “CMH-ranked candidates.” They are not
validated editing sites.

EMRYS produces CMH-ranked computational candidates and provenance. Review,
adjudication, and biological interpretation are external work-process records,
not pipeline steps, gates, artifacts, or completion states.

## Report boundary

The current conceptual reporting boundary belongs in the
[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md#publication-and-evidence-flow),
with implementation behavior in the reporting owner and tests. For this
discussion, the essential boundary is that a report presents declared evidence
without creating new computational, cluster, scientific, or biological
evidence. A synthetic demo must never be presented as production or validation
evidence.

## Discussion prompts

- Is the exact Novogene annotation release recoverable?
- What evidence is required to resolve biological orientation?
- Which sensitivity and replicate checks are mandatory?
- What is the approved production artifact retention policy?
- Which conclusions may be communicated under exploratory review?

Accepted open outcomes belong in the
[findings matrix](../tasks/backlog_matrix.md), not in this discussion guide.
