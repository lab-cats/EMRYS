# Split-N-cigar tests

Native GATK/samtools arguments, selected Java, coordinate order, index nonemptiness, and grouped validation are covered. Fake tools do not establish the GATK transformation.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
