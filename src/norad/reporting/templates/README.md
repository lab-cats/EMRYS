# Reporting templates

This directory contains private, static document sources owned by the
[reporting projection owner](../README.md). They are renderer inputs, not
public configuration, report requests, or independently supported entry
points.

- [`run_report.qmd`](run_report.qmd) is the HTML source. The renderer inserts
  the owned CSS and prepared report body into its placeholders; it contains no
  executable analysis cells.
- [`run_report_pdf.qmd`](run_report_pdf.qmd) is the Typst/PDF source. The bundle
  renderer inserts the prepared PDF body; it also contains no executable
  analysis cells.

Placeholder and format behavior is owned by
[`render_run_report.py`](../render_run_report.py) and
[`render_run_report_bundle.py`](../render_run_report_bundle.py). Direct
protection lives in
[`test_report_html_v1.py`](../../../../tests/reporting/test_report_html_v1.py),
[`test_report_exports_v1.py`](../../../../tests/reporting/test_report_exports_v1.py),
and the shell-launcher contract
[`test_render_run_report.sh`](../../../../tests/reporting/test_render_run_report.sh).
A rendered template reflects only its declared inputs and does not establish
scientific review or biological readiness.
