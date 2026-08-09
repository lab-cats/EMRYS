# Run-report implementation owners

This private package supports the public
[`render_run_report.py`](../render_run_report.py) and
[`render_run_report_bundle.py`](../render_run_report_bundle.py) commands.
Public paths remain compatibility facades; private modules own implementation
and may change without creating another supported command surface.

| Module | Owned responsibility |
| --- | --- |
| [`dispatch.py`](dispatch.py) | Selects the public bundle coordinator without creating a renderer import cycle. |
| [`models.py`](models.py) | Shared immutable report constants, value objects, and renderer error type. |
| [`html_components.py`](html_components.py) | Escaped HTML primitives and approved-table rendering. |
| [`html_computational.py`](html_computational.py) | Computational status, provenance, attempt, artifact, tool, and issue sections. |
| [`html_science.py`](html_science.py) | Scientific-review, evidence, limitation, decision, and methods sections. |
| [`html_projection.py`](html_projection.py) | Final deterministic composition of the HTML report body. |
| [`inputs.py`](inputs.py) | Explicit path resolution, stable file snapshots, run-summary loading, and approved-table intake. |
| [`html_validation.py`](html_validation.py) | Static QMD construction plus generated-QMD, CSS, accessibility, identity, and self-containment validation. |
| [`context.py`](context.py) | Validated, immutable render-context preparation for one explicit run summary. |
| [`runtime.py`](runtime.py) | Closed Quarto environment, pinned-version check, deterministic epoch, timeout, and process-group lifecycle. |
| [`html.py`](html.py) | Current HTML transaction and publication owner; it retains compatibility bindings for moved helpers. |
| [`bundle.py`](bundle.py) | Current PDF/summary/receipt projection and multi-output publication owner. |

The bundle imports the private HTML owner directly. The HTML owner never
imports the bundle. Public facades retain direct-import compatibility while
decomposition proceeds behind them.

Exact report inputs, deterministic bytes, accessibility checks, format
selection, locks, rollback, recovery, and receipt-last publication remain
protected by `tests/reporting/` and `make report-test`.
