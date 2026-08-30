# Synthetic report demonstration

Generate the deterministic ignored HTML demonstration with the synchronized
Python environment:

```bash
uv sync --locked
make demo-report
```

The target builds a synthetic artifact index and canonical run summary, prints
a dry-run report plan, and then publishes separate scientific and
evidence/provenance HTML views, summary TSV, and the v4 receipt last. The
default output is under
`results/demo-report-jinja/reports/synthetic_full_run_demo/`. An explicit
ignored `DEMO_REPORT_ROOT` may select another fresh root.

This target deliberately exercises private reporting builders as a developer
fixture. Those builders are not public commands or operator recovery routes;
operators use default-on reporting after `emrys run`/`emrys resume` or the
independent `emrys report --run-root ...` route for an admitted Run.

Existing pre-v4 report directories are not adopted or overwritten. The older
ignored `results/demo-report/` tree, if present, remains untouched pending
separate destructive-cleanup or migration authority.

The fixture is synthetic and provisional. The report labels its rows
`Computational results — not scientifically adjudicated` and uses
`CMH-ranked candidates`; it does not establish production execution, runtime
or cluster validation, validated editing sites, or a biological conclusion.
Any review, adjudication, or biological interpretation record is an external
research work product rather than a demo or pipeline state.
