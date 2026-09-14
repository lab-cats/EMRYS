# STAR-alignment tests

Native STAR arguments, both compression modes, child failure, output presence, and grouped structural validation are covered. Mocked STAR results do not establish alignment correctness.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
