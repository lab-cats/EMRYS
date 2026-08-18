# Reporting styles

[`run_report.css`](run_report.css) is the single packaged presentation resource
shared by the self-contained scientific and operational-evidence HTML reports.
It is validated against external resource references, then embedded by the
Jinja template. View-specific banner classes distinguish the documents without
creating separate themes or evidence policy in CSS. Its selectors change with
the owned template rather than defining a public styling API.

Protection lives in [`test_report.py`](../../../../tests/reporting/test_report.py)
and the installed-wheel resource/render smoke.
