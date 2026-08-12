# Synthetic report demonstration

Generate the deterministic ignored HTML demonstration with the synchronized
Python environment:

```bash
uv sync --locked
make demo-report
```

The target builds a synthetic artifact index and canonical run summary, prints
a dry-run report plan, and then publishes HTML, summary TSV, and the v2 receipt
last. The default output is under
`results/demo-report-jinja/reports/synthetic_full_run_demo/`. An explicit
ignored `DEMO_REPORT_ROOT` may select another fresh root.

Existing v1 report directories are not adopted or overwritten. The older
ignored `results/demo-report/` tree, if present, remains untouched pending
separate destructive-cleanup or migration authority.

The fixture is synthetic and provisional. The report retains
`EXPLORATORY / PROVISIONAL — NOT BIOLOGICALLY VALIDATED.` and
`CMH-ranked candidates`; it does not establish production execution, runtime
or cluster validation, completed production scientific review, validated
editing sites, or biological readiness.
