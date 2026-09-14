# Test baselines

`python_coverage.json` is the reviewed Python coverage comparison snapshot.
The [test baseline policy](../../docs/design/TEST_BASELINE.md) defines when and
how it may change. Do not update it to conceal lost protection.

[`python_coverage_baseline.py`](../tools/python_coverage_baseline.py) compares
results against it; [`test_python_coverage_baseline.py`](../test_python_coverage_baseline.py)
checks that comparison. This snapshot measures test coverage, not runtime success.
