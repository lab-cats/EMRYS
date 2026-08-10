# Run-report implementation owners

This private package supports the public
[`render_run_report.py`](../render_run_report.py) and
[`render_run_report_bundle.py`](../render_run_report_bundle.py) commands.
Public paths remain compatibility facades; private modules own implementation
and may change without creating another supported command surface.

| Module | Owned responsibility |
| --- | --- |
| [`models.py`](models.py) | Shared immutable report constants, value objects, and renderer error type. |
| [`html_components.py`](html_components.py) | Escaped HTML primitives and approved-table rendering. |
| [`html_computational.py`](html_computational.py) | Computational status, provenance, attempt, artifact, tool, and issue sections. |
| [`html_science.py`](html_science.py) | Scientific-review, evidence, limitation, decision, and methods sections. |
| [`html_projection.py`](html_projection.py) | Final deterministic composition of the HTML report body. |
| [`inputs.py`](inputs.py) | Explicit path resolution, stable file snapshots, run-summary loading, and approved-table intake. |
| [`html_validation.py`](html_validation.py) | Static QMD construction plus generated-QMD, CSS, accessibility, identity, and self-containment validation. |
| [`context.py`](context.py) | Validated, immutable render-context preparation for one explicit run summary. |
| [`runtime.py`](runtime.py) | Closed Quarto environment, pinned-version check, deterministic epoch, timeout, and process-group lifecycle. |
| [`transaction.py`](transaction.py) | Lock ownership, stable snapshots, atomic-file primitives, fsync, cleanup, and recovery-marker mechanics. |
| [`html_publication.py`](html_publication.py) | Quarto staging plus validated, rollback-safe publication of one HTML report. |
| [`html.py`](html.py) | Thin HTML command coordinator and compatibility owner for moved helpers. |
| [`bundle_models.py`](bundle_models.py) | Shared bundle constants and immutable multi-format render context. |
| [`pdf_projection.py`](pdf_projection.py) | Deterministic PDF view, pinned Quarto invocation, and PDF validation. |
| [`receipt_projection.py`](receipt_projection.py) | Deterministic summary TSV, receipt document/TSV, truncation disclosure, and validation. |
| [`bundle_context.py`](bundle_context.py) | Bundle predecessor/receipt validation and immutable multi-format context preparation. |
| [`bundle_publication.py`](bundle_publication.py) | Rollback-safe multi-output publication with receipt-last commit semantics. |
| [`bundle.py`](bundle.py) | Thin bundle command coordinator and compatibility owner for moved helpers. |

The bundle imports the private HTML owner directly. The HTML owner never
imports the bundle. Public facades retain direct-import compatibility while
decomposition proceeds behind them.

Exact report inputs, deterministic bytes, accessibility checks, format
selection, locks, rollback, recovery, and receipt-last publication remain
protected by `tests/reporting/` and `make report-test`.
