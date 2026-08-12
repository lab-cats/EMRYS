# Reporting projection owner

Reporting consumes explicit validated inputs. It does not discover or rerun
analysis, decide scientific validity, or promote evidence.

## Public entry points

| Interface | Responsibility |
| --- | --- |
| `python -I -m norad build artifact-index` | Reconcile one declared source checkout and inventory into a receipt-last artifact index. |
| `python -I -m norad build run-summary` | Project one admitted artifact-index receipt into the canonical run summary. |
| `python -I -m norad build report` | Render one canonical run summary under an admitted checkout authority into self-contained HTML, summary TSV, and a v2 receipt published last. |

All three build routes require `--source-checkout
ABSOLUTE_CANONICAL_CHECKOUT`. The report command is dry-run by default and
accepts only explicit inputs:

```bash
.venv/bin/python -I -m norad build report \
  --source-checkout /absolute/path/to/norad \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports
```

`--source-checkout` must name the absolute canonical NORAD Git top level whose
Python and packaged-resource bytes match the executing package. The admitted
root governs repository-relative paths in the run summary, including approved
report tables, and renderer Git identity. Reporting does not infer this
authority from the working directory or the run-summary location.

Repeat with `--execute` to publish exactly:

- `RUN_ID.run_report.html`
- `RUN_ID.run_summary.tsv`
- `RUN_ID.report_outputs.tsv`

The last file is the `norad.report_receipt` v2 receipt. Existing v1 output
directories, bare HTML predecessors, and incomplete sets are rejected; use a
fresh output root unless an explicit migration is separately approved.

[`report.py`](report.py) is the one public report owner. The private
[`_run_report/`](_run_report/README.md) package owns explicit input admission,
checkout-rooted semantic and table validation, structured view data, Jinja
rendering, static HTML validation, receipt projection, and the
lock/staging/rollback transaction. The single packaged
[`run_report.html.j2`](templates/run_report.html.j2) template owns markup and
embeds the validated packaged [`run_report.css`](styles/run_report.css). Jinja
uses HTML autoescaping and `StrictUndefined`; only the tracked CSS crosses a
trusted raw boundary. There are no scripts, remote assets, sidecars, network
access, format selection, or report PDF.

Focused protection is `make report-test`; `make demo-report` creates an ignored
synthetic HTML-only demonstration beneath `results/demo-report-jinja/`.
Recovery routes are in
[`TROUBLESHOOTING`](../../../docs/operations/TROUBLESHOOTING.md).

A rendered document or receipt reflects only its validated inputs and declared
evidence state. It does not establish production execution, completed
scientific review, validated editing sites, or biological readiness.
