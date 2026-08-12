RSCRIPT_BIN ?= Rscript
PYTHON_BIN ?= python3
REPORT_PYTHON_BIN ?= $(CURDIR)/.venv/bin/python
PYTHON_COVERAGE_ROOT ?= $(CURDIR)/.coverage-work
PYTHON_COVERAGE_DATA ?= $(PYTHON_COVERAGE_ROOT)/.coverage
PYTHON_COVERAGE_RAW ?= $(PYTHON_COVERAGE_ROOT)/coverage.json
PYTHON_COVERAGE_CURRENT ?= $(PYTHON_COVERAGE_ROOT)/python_coverage.current.json
PYTHON_COVERAGE_BASELINE ?= $(CURDIR)/tests/baselines/python_coverage.json
PYTHON_COVERAGE_PYTEST_ARGS ?=
VALIDATION_JOBS ?= 3
VALIDATION_PYTHON_WORKERS ?= 2
VALIDATION_ARGS ?=
DEMO_REPORT_ROOT ?= $(CURDIR)/results/demo-report-jinja
VALIDATION_DIRS := \
	results/qc/validation/00a \
	results/qc/validation/00b \
	results/qc/validation/00c \
	results/qc/validation/01 \
	results/qc/validation/02 \
	results/qc/validation/03 \
	results/qc/validation/04 \
	results/qc/validation/05 \
	results/qc/validation/06 \
	results/qc/validation/07 \
	results/qc/validation/08 \
	results/qc/validation/09

.PHONY: setup test documentation-check shell-test validation-shell-contracts validation-shell-slurm validation-wheel-smoke real-r-test r-restore r-check local-real-r-test report-test demo-report python-coverage-measure python-coverage-check python-coverage-baseline-update validation-guarded-r validation-static validate smoke lint all-checks

setup:
	mkdir -p logs $(VALIDATION_DIRS)

test:
	"$(REPORT_PYTHON_BIN)" -m pytest

NORAD_MAKE_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(NORAD_MAKE_ROOT)/scripts/make_quality.mk
include $(NORAD_MAKE_ROOT)/scripts/make_reporting.mk
