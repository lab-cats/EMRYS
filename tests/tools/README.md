# Test tools

This directory owns test-only runners and comparators. The Python coverage
baseline tool implements the policy in the
[test baseline](../../docs/design/TEST_BASELINE.md), while `run_validation.py`
coordinates the serial static preflight and four non-overlapping owner lanes
documented by the
[operations runbook](../../docs/operations/RUNBOOK.md).

`python_test_shards.py` is the test-only CI partitioner. It uses the reviewed
duration estimates in `tests/baselines/python_test_durations.json` to build a
deterministic balanced plan, runs exact pytest node IDs with xdist work
stealing, and verifies downloaded receipts cover the current inventory once
and only once. Estimates change scheduling only, and stale estimate node IDs
fail closed.

These files support repository validation; they are not public workflow
commands or independent evidence authorities.
