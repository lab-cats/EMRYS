# Reporting styles

[`run_report.css`](run_report.css) is the single packaged presentation resource
for the self-contained HTML report. It is validated against external resource
references, then embedded by the Jinja template. Its selectors change with the
owned template rather than defining a separate theme API or evidence policy.

Protection lives in [`test_report.py`](../../../../tests/reporting/test_report.py)
and the installed-wheel resource/render smoke.
