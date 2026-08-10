# Test baselines

This directory owns reviewed comparator snapshots used by test policy. The
current Python coverage snapshot is `python_coverage.json`; its authority and
update rules are defined by the
[test baseline](../../docs/design/TEST_BASELINE.md).

The comparison implementation is
[`../tools/python_coverage_baseline.py`](../tools/python_coverage_baseline.py),
with direct protection in
[`../test_python_coverage_baseline.py`](../test_python_coverage_baseline.py).
Do not edit or regenerate a baseline to conceal lost protection. A coverage
snapshot is local test evidence, not runtime, scientific, or biological proof.
