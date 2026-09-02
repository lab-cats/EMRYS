RSCRIPT_BIN ?= Rscript
PYTHON_BIN ?= python3
REPORT_PYTHON_BIN ?= $(CURDIR)/.venv/bin/python
PYTHON_COVERAGE_ROOT ?= $(CURDIR)/.coverage-work
PYTHON_COVERAGE_DATA ?= $(PYTHON_COVERAGE_ROOT)/.coverage
PYTHON_COVERAGE_RAW ?= $(PYTHON_COVERAGE_ROOT)/coverage.json
PYTHON_COVERAGE_CURRENT ?= $(PYTHON_COVERAGE_ROOT)/python_coverage.current.json
PYTHON_COVERAGE_BASELINE ?= $(CURDIR)/tests/baselines/python_coverage.json
PYTHON_COVERAGE_WORKERS ?= 2
PYTHON_TEST_SHARD_INDEX ?= 0
PYTHON_TEST_SHARD_COUNT ?= 1
PYTHON_TEST_DURATION_BASELINE ?= $(CURDIR)/tests/baselines/python_test_durations.json
PYTHON_TEST_SHARD_RECEIPT ?= $(PYTHON_COVERAGE_ROOT)/python-test-shard-$(PYTHON_TEST_SHARD_INDEX)-of-$(PYTHON_TEST_SHARD_COUNT).json
VALIDATION_JOBS ?= 3
VALIDATION_PYTHON_WORKERS ?= 2
VALIDATION_ARGS ?=
.PHONY: test documentation-check shell-test validation-shell-contracts validation-wheel-smoke real-r-test r-restore r-check local-real-r-test report-test dashboard python-coverage-shard python-coverage-finalize python-coverage-measure python-coverage-enforce python-coverage-check python-coverage-baseline-update validation-guarded-r validation-static validate smoke lint all-checks

test:
	"$(REPORT_PYTHON_BIN)" -m pytest

EMRYS_MAKE_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(EMRYS_MAKE_ROOT)/scripts/make_quality.mk
include $(EMRYS_MAKE_ROOT)/scripts/make_operations.mk
