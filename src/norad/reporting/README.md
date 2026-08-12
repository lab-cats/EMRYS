# Reporting projection owner

Reporting consumes explicit validated inputs. It does not discover or rerun
analysis, decide scientific validity, or promote evidence.

## Public entry points

| Interface | Responsibility |
| --- | --- |
| `python -X pycache_prefix=/dev/null -I -m norad build artifact-index` | Reconcile one declared artifact root and inventory under an independent producer-checkout authority into a receipt-last artifact index. |
| `python -X pycache_prefix=/dev/null -I -m norad build run-summary` | Project one admitted artifact-index receipt into the canonical run summary. |
| `python -X pycache_prefix=/dev/null -I -m norad build report` | Render one canonical run summary under distinct code and artifact authorities into self-contained HTML, summary TSV, and a v2 receipt published last. |

All three build routes require both `--source-checkout
ABSOLUTE_CANONICAL_CHECKOUT` and `--artifact-source-root
ABSOLUTE_CANONICAL_ARTIFACT_ROOT`. The report command is dry-run by default
and accepts only explicit inputs:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad build report \
  --source-checkout /absolute/path/to/norad \
  --artifact-source-root /absolute/path/to/run-root \
  --run-summary /absolute/path/to/run-root/products/artifact-summary/RUN_ID/RUN_ID.run_summary.json \
  --output-root /absolute/path/to/run-root/products/report
```

`--source-checkout` names the absolute canonical NORAD Git top level whose
Python and packaged-resource bytes match the executing package; it owns
producer and renderer Git identity. `--artifact-source-root` independently
resolves contract-relative inventory, native artifact, science, approval, and
report-table paths. Reporting infers neither root from the working directory
or the run-summary location.

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

[`transaction_validation.py`](transaction_validation.py) is the public
read-only completion owner used by local lifecycle and inspection. Its three
specific validators and fixed-profile `validate_receipt(...)` dispatcher pin
receipt identity by no-follow descriptor before and after semantic validation,
then revalidate bound native sources, records, indexes, summaries, HTML, TSV,
and receipts. A receipt path or hash alone is never completion evidence.

This completion boundary assumes the same single-user, cooperative workspace
as the local pilot. Pre-existing symlink components, leaf substitution,
unstable bytes, and roster drift fail closed; hostile concurrent replacement
of ancestor directories or mount namespaces requires external isolation and
lies outside this local evidence claim.

A rendered document or receipt reflects only its validated inputs and declared
evidence state. It does not establish production execution, completed
scientific review, validated editing sites, or biological readiness.
