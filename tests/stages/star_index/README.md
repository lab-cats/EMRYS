# STAR-index tests

These cases check Step 00a dry-run, execution from other working directories,
publication of the declared index files, existing-output refusal, and rollback.
Collision tests preserve files created by another process during publication
and locks owned by another attempt. The
[stage contract](../../../src/emrys/stages/star_index/CONTRACT.md) defines these
boundaries. Whole-Run Slurm placement is tested with orchestration; these mocked
cases do not prove real STAR indexing or reference readiness.
