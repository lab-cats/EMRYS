# Reporting styles

This directory contains private presentation assets owned by the
[reporting projection owner](../README.md). They are implementation inputs,
not a public theme API or evidence policy.

[`run_report.css`](run_report.css) defines the HTML report layout and visual
states. [`render_run_report.py`](../render_run_report.py) reads and embeds it
into the static HTML source so the published report remains self-contained.
CSS selectors are coupled to the renderer's generated markup and must change
with that markup rather than becoming a second semantic owner.

Direct protection lives in
[`test_report_html_v1.py`](../../../../tests/reporting/test_report_html_v1.py)
and the shell-launcher contract
[`test_render_run_report.sh`](../../../../tests/reporting/test_render_run_report.sh).
Visual styling does not validate inputs, promote evidence, or establish
scientific review or biological readiness.
