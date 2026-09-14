# Canonical-BAM QC tests

Native quickcheck and flagstat capture, both successful quickcheck forms, retained child diagnostics, and grouped validation are covered. The existing exact-marker producer/validator mismatch remains protected.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
