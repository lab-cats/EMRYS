# PI demo discussion guide

This is the PI/audience discussion view, not the presenter run-of-show, live
project status, command source, report contract, or dated snapshot. Consult the
current [`HANDOFF.md`](../operations/HANDOFF.md) before presenting.

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
| Scientific review | Were evidence, decisions, and limitations recorded? | Biological causality |
| Report | Can evidence be presented deterministically? | Any new evidence state |

## Scientific caution

Use the current cohort evidence in the
[`HANDOFF.md`](../operations/HANDOFF.md#cohort-and-preserved-scientific-evidence).
Reverse-stranded/first-strand-style evidence does not make mechanical
`FWD_like` and `REV_like` groups biological strand. The legacy-compatible
orientation policy remains provisional.

Rows emitted by the CMH stage are “CMH-ranked candidates.” They are not
validated editing sites.

`science_review_complete_exploratory` permits only provisional reporting.
`biological_interpretation_ready` remains reserved until a separate policy and
evidence gate explicitly unlock it.

## Report boundary

The current conceptual reporting boundary belongs in the
[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md#publication-and-evidence-flow),
with implementation and synthetic-demo status in the
[`HANDOFF.md`](../operations/HANDOFF.md#evidence-boundary). For this
discussion, the essential boundary is that a report presents declared
evidence without creating new computational, cluster, scientific, or
biological evidence. A synthetic demo must never be presented as production
or validation evidence.

## Discussion prompts

- Is the exact Novogene annotation release recoverable?
- What evidence is required to resolve biological orientation?
- Which sensitivity and replicate checks are mandatory?
- What is the approved production artifact retention policy?
- Which conclusions may be communicated under exploratory review?

Current answers and blockers belong in the
[`HANDOFF.md`](../operations/HANDOFF.md#current-blockers) and
[`QUESTIONS.md`](../design/QUESTIONS.md#operational-and-scientific-evidence),
not in this discussion guide.
