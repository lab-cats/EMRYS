# Reporting fixtures

This directory owns shared reporting-test support, divided by protected
contract:

- [`artifact_adapters_v1/`](artifact_adapters_v1/README.md) builds temporary
  source artifacts for artifact-index tests.
- [`artifact_run_summary_v2/`](artifact_run_summary_v2/README.md) builds
  temporary computational artifact states for run-summary and report tests.

Generated fixture outputs belong in caller-owned temporary directories and are
not tracked evidence or independent goldens.
