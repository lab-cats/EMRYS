# Reporting template

[`run_report.html.j2`](run_report.html.j2) is the single packaged report
template shared by the scientific and operational-evidence HTML views. The
Python view builders select each document's title, banner context, introduction,
sections, and end note; this template owns their common accessible structure,
tables, figure cards, the ranked selected-candidate card index, detailed
candidate records, and block rendering. The scientific hierarchy is static and
print-oriented, with no `details` elements;
the operational-evidence categories retain their bounded disclosure controls.
Scientific SVG figures, including multi-panel candidate views, are validated
and supplied as base64 data URIs; the artifact-availability SVG is emitted only
when the evidence view supplies that block. A bounded macro section avoids
template fragments. Manifest-paired candidate evidence is emitted in bounded
four-pair batches with the candidate-specific heading inside each batch so print
page breaks never remove the record identity or split a replicate card.

The Jinja environment uses HTML autoescaping and `StrictUndefined`. Run-summary
content, identifiers, paths, computational text, issues, limitations, and table
data never cross a `safe` boundary. The only trusted raw value is the tracked,
validated packaged CSS; SVG data URIs remain autoescaped attribute values. The
template has no scripts, includes, remote assets, sidecars, or executable
analysis.

Protection lives in [`test_report.py`](../../../../tests/reporting/test_report.py)
and the isolated-wheel render smoke.
