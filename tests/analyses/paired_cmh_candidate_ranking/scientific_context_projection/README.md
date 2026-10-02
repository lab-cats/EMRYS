# Scientific-context projection tests

The shell test covers staged payload/receipt reconciliation and one captured-argv
oracle for the selected R script, six literal input path/SHA-256 pairs and four
final output roles. Expected digests come from fixture bytes through Python
standard-library hashing. Fake R establishes argument handoff and staging only;
it does not establish native R semantics or a complete canonical receipt.
Real-R fixtures and grouped validation independently protect the
[scientific computation](../../../../src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/README.md).
The [common runner suite](../../../orchestration/run_coordinator/test_task.py)
owns publication and recovery. The
[shared evidence limits](../../../README.md#evidence-limits) apply.
