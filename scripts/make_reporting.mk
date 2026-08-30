DEMO_REPORT_RUN_ID := synthetic_run
DEMO_REPORT_FIXTURE_ROOT := $(DEMO_REPORT_ROOT)/full-run-fixture
DEMO_REPORT_ARTIFACT_ROOT := $(DEMO_REPORT_FIXTURE_ROOT)/adapter_fixture/artifacts
DEMO_REPORT_OUTPUT_ROOT := $(DEMO_REPORT_ROOT)/reports

report-test:
	"$(REPORT_PYTHON_BIN)" -m pytest \
		tests/reporting/test_artifact_run_summary.py \
		tests/reporting/test_candidate_display.py \
		tests/reporting/test_figures.py \
		tests/reporting/test_report.py \
		tests/reporting/test_transaction_validation.py

demo-report:
	command -v "$(REPORT_PYTHON_BIN)" >/dev/null 2>&1 || { \
		printf 'ERROR: report Python is unavailable: %s\n' \
			"$(REPORT_PYTHON_BIN)" >&2; \
		exit 1; \
	}
	"$(REPORT_PYTHON_BIN)" -c \
		'import importlib.metadata, jinja2, jsonschema; assert importlib.metadata.version("matplotlib") == "3.11.1"; assert importlib.metadata.version("logomaker") == "0.8.7"' || { \
		printf 'ERROR: report Python dependencies are unavailable: %s\n' \
			"$(REPORT_PYTHON_BIN)" >&2; \
		exit 1; \
		}
	"$(REPORT_PYTHON_BIN)" -m \
		tests.reporting.fixtures.artifact_run_summary_v2.build_fixture \
		--root "$(DEMO_REPORT_FIXTURE_ROOT)" \
		--run-id "$(DEMO_REPORT_RUN_ID)" \
		--report-output-root "$(DEMO_REPORT_OUTPUT_ROOT)"
	@printf 'Demo report transaction: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)"
	@printf '  Scientific HTML: %s\n  Evidence HTML: %s\n  Summary: %s\n  Receipt: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).scientific_report.html" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).evidence_report.html" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.tsv" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).report_outputs.tsv"
