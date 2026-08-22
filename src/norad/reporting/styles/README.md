# Reporting styles

[`run_report.css`](run_report.css) is the single packaged presentation resource
shared by the self-contained scientific and operational-evidence HTML reports.
It is validated against external resource references, then embedded by the
Jinja template. View-specific banner classes, bounded scientific-figure cards,
candidate records, and figure-guide entries distinguish the documents without
creating separate themes or evidence policy in CSS. Print rules use fixed page
margins, remove sticky positioning, prevent horizontal overflow in scientific
content, present the selected-candidate index as ranked evidence cards rather
than a wide table, keep compact evidence blocks and their four-pair candidate
batches together, preserve the two-column record and figure-guide grids, and
start the major scientific figure/guide sections on new pages. Its selectors
change with the owned template rather than defining a public styling API.

Protection lives in [`test_report.py`](../../../../tests/reporting/test_report.py)
and the installed-wheel resource/render smoke.
