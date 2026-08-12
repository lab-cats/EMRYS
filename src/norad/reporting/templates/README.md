# Reporting template

[`run_report.html.j2`](run_report.html.j2) is the single packaged report
template. It owns document structure, sections, tables, status panels,
limitations, evidence presentation, approved-table display, and the embedded
artifact-overview SVG. A bounded macro section avoids template fragments.

The Jinja environment uses HTML autoescaping and `StrictUndefined`. Run-summary
content, identifiers, paths, scientific text, issues, limitations, and table
data never cross a `safe` boundary. The only trusted raw value is the tracked,
validated packaged CSS. The template has no scripts, includes, remote assets,
sidecars, or executable analysis.

Protection lives in [`test_report.py`](../../../../tests/reporting/test_report.py)
and the isolated-wheel render smoke.
