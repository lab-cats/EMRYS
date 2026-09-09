# STAR-index tests

Native STAR arguments, complete staged index membership, incomplete native output, and grouped validation are covered. Mocked tools do not prove real STAR indexing or reference readiness.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
