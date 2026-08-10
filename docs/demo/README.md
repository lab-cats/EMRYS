# Demonstration guides

This directory contains two reviewed presentation consumers. Neither guide
owns current checkout state, report behavior, commands, or evidence promotion.

| Guide | Consumer and role |
| --- | --- |
| [`DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md) | Presenter run-of-show: inspection order, report tour, and action-point wording. |
| [`PI_DEMO_REPORT.md`](PI_DEMO_REPORT.md) | PI/audience discussion guide: evidence-layer table, scientific cautions, and prompts. |

Generate the deterministic ignored bundle after explicit Quarto setup:

```bash
make demo-report
```

Optional projections are `DEMO_REPORT_FORMATS=html`,
`DEMO_REPORT_FORMATS=pdf`, and an explicit ignored `DEMO_REPORT_ROOT`. The
default bundle is under `results/demo-report/reports/synthetic_full_run_demo/`.

Before presenting, use the current
[`HANDOFF.md`](../operations/HANDOFF.md) for status, cohort evidence, and
limitations. Current reporting behavior and its
evidence ceiling remain in the
[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md#publication-and-evidence-flow)
and [`HANDOFF.md`](../operations/HANDOFF.md#evidence-boundary).

Only the two guides listed above are verified current presentation consumers.
File presence does not activate later or otherwise unreviewed demo material.
Dated presentation evidence belongs under the
[`docs/history/`](../history/README.md) rules only when its date, source commit,
and unique historical value are established.
