# Picard duplicate-marking tests

Native Picard arguments, complete BAM/BAI/metrics output, failed quickcheck, empty metrics, and grouped validation are covered. Fixtures do not establish duplicate-marking accuracy.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
