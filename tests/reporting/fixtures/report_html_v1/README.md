# Report HTML v1 fixtures

This directory supplies the established HTML-core runner and one approved
synthetic candidate table used by report model, security, export, and render
tests. `run_html_core.py` delegates to the production HTML core; it is not a
second renderer.

The [HTML report suite](../../test_report_html_v1.py) owns interpretation of
these inputs. Synthetic approval and rendered output do not establish a
production approval, completed scientific review, or biological readiness.
