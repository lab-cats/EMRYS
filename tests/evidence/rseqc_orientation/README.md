# RSeQC orientation tests

Native RSeQC arguments, empty or failed output, and grouped fraction validation are covered. Fixture fractions do not establish transcript strand, sense/antisense assignment, or an approved manifest policy.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
