# Reporting projection owner

This directory owns format-neutral run/report projections and report rendering
assets. Reporting consumes explicit, validated inputs; it does not discover or
rerun analysis, decide scientific validity, or promote evidence.

## Public entry points

| Interface | Responsibility |
| --- | --- |
| [`build_artifact_index.py`](build_artifact_index.py) | Reconciles declared workflow artifacts into an explicit artifact index. |
| [`build_run_summary.py`](build_run_summary.py) | Projects declared run, artifact, validation, and science state into a run summary. |
| [`render_run_report.sh`](render_run_report.sh) | Dry-run-by-default shell launcher for the report-bundle owner. |
| [`render_run_report.py`](render_run_report.py) | Provides the public Python bundle entry point and the internal self-contained HTML core used by the bundle coordinator; it consumes one canonical summary and only its authorized supplemental tables. |
| [`render_run_report_bundle.py`](render_run_report_bundle.py) | Publishes a selected HTML/PDF/TSV/receipt bundle, with the receipt last. |

[`_artifact_index/`](_artifact_index/README.md),
[`_run_summary/`](_run_summary/README.md),
[`_run_summary_science.py`](_run_summary_science.py),
[`templates/`](templates/README.md), and [`styles/`](styles/README.md) are
private implementation assets, not additional public interfaces. Structural
input starters live in
[`artifact_inventory.example.tsv`](../../../configs/artifact_inventory.example.tsv),
[`artifact_run_contract.example.json`](../../../configs/artifact_run_contract.example.json),
and
[`report_table_approvals.example.tsv`](../../../configs/report_table_approvals.example.tsv).
They require run-specific paths, identities, approvals, and provenance and are
not production evidence.

Direct protection lives in [`tests/reporting/`](../../../tests/reporting/).

Build an artifact index in dry-run mode, then repeat with `--execute`:

```bash
.venv/bin/python src/norad/reporting/build_artifact_index.py \
  --run-id RUN_ID \
  --run-contract RUN_CONTRACT_JSON \
  --inventory INVENTORY_TSV \
  --output-root results/artifacts
```

Build its canonical run summary from the committed adapter receipt:

```bash
.venv/bin/python src/norad/reporting/build_run_summary.py \
  --run-id RUN_ID \
  --artifact-receipt results/artifacts/RUN_ID/RUN_ID.artifact_receipt.tsv \
  --output-root results/artifacts
```

Append `--science-review-summary` or `--report-table-approvals` only for exact
inspected inputs. Execute by repeating with `--execute`.

After the separately authorized `make quarto-restore`, render in dry-run mode
and then repeat with `--execute`:

```bash
src/norad/reporting/render_run_report.sh \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto
```

Use `--formats html`, `--formats pdf`, or `--formats all`. Focused protection is
`make report-test`. Recovery routes are in
[`TROUBLESHOOTING`](../../../docs/operations/TROUBLESHOOTING.md).

Outputs belong under the caller's declared ignored results/report root. A
rendered document, summary, artifact row, or publication receipt reflects only
its validated inputs and declared evidence state. The synthetic demo remains
provisional; reporting does not establish production execution, completed
scientific review, validated editing sites, or biological readiness.
