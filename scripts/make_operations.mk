# Read-only operator utilities. Values are exported by make so user-provided
# overrides are not interpolated into the recipe shell command.
DASHBOARD_PYTHON_BIN ?= /usr/bin/python3
DASHBOARD_REFRESH ?= 30
JOB_ID ?=
LOG_DIR ?=

export EMRYS_DASHBOARD_JOB_ID := $(JOB_ID)
export EMRYS_DASHBOARD_LOG_DIR := $(LOG_DIR)
export EMRYS_DASHBOARD_REFRESH := $(DASHBOARD_REFRESH)

.PHONY: dashboard
dashboard:
	@"$(DASHBOARD_PYTHON_BIN)" -I -B \
		"$(EMRYS_MAKE_ROOT)/src/emrys/orchestration/local_pilot/dashboard.py" \
		--refresh "$$EMRYS_DASHBOARD_REFRESH"
