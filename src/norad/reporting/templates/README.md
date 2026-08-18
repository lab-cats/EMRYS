# Reporting template

[`run_report.html.j2`](run_report.html.j2) is the single packaged report
template shared by the scientific and operational-evidence HTML views. The
Python view builders select each document's title, banner context, introduction,
sections, and end note; this template owns their common accessible structure,
tables, and block rendering. The artifact-availability SVG is emitted only when
the evidence view supplies that block. A bounded macro section avoids template
fragments.

The Jinja environment uses HTML autoescaping and `StrictUndefined`. Run-summary
content, identifiers, paths, computational text, issues, limitations, and table
data never cross a `safe` boundary. The only trusted raw value is the tracked,
validated packaged CSS. The template has no scripts, includes, remote assets,
sidecars, or executable analysis.

Protection lives in [`test_report.py`](../../../../tests/reporting/test_report.py)
and the isolated-wheel render smoke.
