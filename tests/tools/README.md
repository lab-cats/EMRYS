# Test tools

This directory owns test-only runners and comparators. The Python coverage
baseline tool implements the policy in the
[test baseline](../../docs/design/TEST_BASELINE.md), while `run_validation.py`
coordinates the local validation lanes documented by the
[operations runbook](../../docs/operations/RUNBOOK.md).

These files support repository validation; they are not public workflow
commands or independent evidence authorities.
