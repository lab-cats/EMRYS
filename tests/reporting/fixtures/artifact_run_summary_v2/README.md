# Artifact run-summary fixture builder

`build_fixture.py` composes temporary computational artifact-index inputs for
run-summary, export, and rendering tests. It owns complete, failed, and missing
artifact states; generated outputs stay under the caller's temporary root.

The builder is producer-coupled support, not an independent evidence oracle.
Direct consumers include the
[run-summary suite](../../test_artifact_run_summary.py) and report suites in
the parent test directory. Production projection remains owned by the
[reporting README](../../../../src/norad/reporting/README.md).
