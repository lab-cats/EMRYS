# Reporting projection owner

This directory owns format-neutral run/report projections and report rendering
assets. Reporting consumes explicit, validated inputs; it does not discover or
rerun analysis, decide scientific validity, or promote evidence.

## Public entry points

| Interface | Responsibility |
| --- | --- |
| `python -I -m norad build artifact-index` | Reconciles declared workflow artifacts from an explicitly admitted source checkout into an artifact index. |
| `python -I -m norad build run-summary` | Projects declared run, artifact, validation, and science state from an explicitly admitted source checkout into a run summary. |
| [`render_run_report.sh`](render_run_report.sh) | Dry-run-by-default shell launcher for the report-bundle owner. |
| [`render_run_report.py`](render_run_report.py) | Public compatibility command that dispatches selected HTML/PDF/all rendering while preserving established direct imports. |
| [`render_run_report_bundle.py`](render_run_report_bundle.py) | Public compatibility facade for selected HTML/PDF/TSV/receipt publication, with the receipt last. |

[`_artifact_index/`](_artifact_index/README.md),
[`_run_summary/`](_run_summary/README.md), including its canonical
[`science_projection.py`](_run_summary/science_projection.py) owner,
[`_run_report/`](_run_report/README.md),
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
.venv/bin/python -I -m norad build artifact-index \
  --source-checkout /absolute/canonical/path/to/norad \
  --run-id RUN_ID \
  --run-contract RUN_CONTRACT_JSON \
  --inventory INVENTORY_TSV \
  --output-root results/artifacts
```

The source checkout must be the canonical NORAD Git top level and must match
the executing package's Python and declared resource bytes. The grouped
dispatcher keeps help and unrelated installed commands lightweight and loads
the private artifact-index builder only after this route is selected.

Build its canonical run summary from the committed adapter receipt:

```bash
.venv/bin/python -I -m norad build run-summary \
  --source-checkout /absolute/canonical/path/to/norad \
  --run-id RUN_ID \
  --artifact-receipt results/artifacts/RUN_ID/RUN_ID.artifact_receipt.tsv \
  --output-root results/artifacts
```

Append `--science-review-summary` or `--report-table-approvals` only for exact
inspected inputs. Execute by repeating with `--execute`.

The required source checkout must be the canonical NORAD Git top level and
must match the executing package's Python and declared resource bytes. The
grouped dispatcher keeps help and unrelated installed commands lightweight and
loads the private run-summary builder only after this route is selected. After
argument parsing, the builder admits the explicit checkout before reading run
inputs. The retained authority governs contract-relative artifact, science,
and approval inputs and semantic, predecessor, post-publication, and rollback
validation. Git admission and later `HEAD` resolution ignore ambient `GIT_*`
routing while preserving unrelated environment state. This command cutover
changes neither evidence meaning nor receipt-last publication and recovery
behavior.

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
