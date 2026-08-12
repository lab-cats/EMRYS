# Reporting fixtures

This directory owns shared reporting-test support, divided by protected
contract:

- [`artifact_adapters_v1/`](artifact_adapters_v1/README.md) builds temporary
  source artifacts for artifact-index tests.
- [`artifact_run_summary_v1/`](artifact_run_summary_v1/README.md) builds
  temporary artifact and science states for run-summary and report tests.

Generated fixture outputs belong in caller-owned temporary directories and are
not tracked evidence or independent goldens.
