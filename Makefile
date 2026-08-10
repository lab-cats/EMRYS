RSCRIPT_BIN ?= Rscript
PYTHON_BIN ?= python3
REPORT_PYTHON_BIN ?= $(CURDIR)/.venv/bin/python
PYTHON_COVERAGE_ROOT ?= $(CURDIR)/.coverage-work
PYTHON_COVERAGE_DATA ?= $(PYTHON_COVERAGE_ROOT)/.coverage
PYTHON_COVERAGE_RAW ?= $(PYTHON_COVERAGE_ROOT)/coverage.json
PYTHON_COVERAGE_CURRENT ?= $(PYTHON_COVERAGE_ROOT)/python_coverage.current.json
PYTHON_COVERAGE_BASELINE ?= $(CURDIR)/tests/baselines/python_coverage.json
PYTHON_COVERAGE_PYTEST_ARGS ?=
QUARTO_TOOLS_ROOT ?= $(CURDIR)/.tools/quarto
QUARTO_BIN ?= $(QUARTO_TOOLS_ROOT)/$(QUARTO_VERSION)/bin/quarto
VALIDATION_JOBS ?= 3
VALIDATION_PYTHON_WORKERS ?= 2
VALIDATION_ARGS ?=
REPORT_TEST_RESULT ?=
DEMO_REPORT_ROOT ?= $(CURDIR)/results/demo-report
DEMO_REPORT_FORMATS ?= all

.PHONY: test documentation-check shell-test validation-shell-contracts real-r-test r-restore r-check local-real-r-test quarto-restore report-test validation-report-runtime demo-report python-coverage-measure python-coverage-check python-coverage-baseline-update validation-python-coverage validation-guarded-r validation-static validate smoke lint all-checks

test:
	"$(REPORT_PYTHON_BIN)" -m pytest

NORAD_MAKE_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(NORAD_MAKE_ROOT)/scripts/make_quality.mk
include $(NORAD_MAKE_ROOT)/scripts/make_reporting.mk
