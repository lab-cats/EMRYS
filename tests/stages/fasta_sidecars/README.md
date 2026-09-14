# FASTA-sidecar tests

Native samtools/GATK sidecar generation, selected Java, contig checks, and grouped validation are covered. Complete-pair reuse belongs to the Run task runner.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
