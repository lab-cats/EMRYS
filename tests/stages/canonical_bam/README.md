# Canonical-BAM tests

Native samtools sorting and read-group construction, canonical-input hard-link reuse, malformed headers, incomplete tagging, and grouped validation are covered. The [historical replacement defect](../../../src/emrys/stages/canonical_bam/CONTRACT.md#historical-replacement-defect) retains the restore-loss sequence and exact source/test revision.

Shell cases invoke the internal worker with runner-style scratch and staging.
The [common runner suite](../../orchestration/run_coordinator/test_task.py) owns
publication, input stability, interruption, and recovery checks. Python
validator cases retain the public grouped command. The
[shared evidence limits](../../README.md#evidence-limits) apply.
