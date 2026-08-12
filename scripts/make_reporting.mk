DEMO_REPORT_RUN_ID := synthetic_full_run_demo
DEMO_REPORT_FIXTURE_ROOT := $(DEMO_REPORT_ROOT)/full-run-fixture
DEMO_REPORT_ARTIFACT_ROOT := $(DEMO_REPORT_FIXTURE_ROOT)/artifacts
DEMO_REPORT_OUTPUT_ROOT := $(DEMO_REPORT_ROOT)/reports
DEMO_REPORT_SCIENCE_SUMMARY := $(DEMO_REPORT_FIXTURE_ROOT)/science_fixture/step09c_fixture/output/review_fixture/review_fixture.step09c_review_summary.tsv
DEMO_REPORT_TABLE_APPROVALS := $(DEMO_REPORT_FIXTURE_ROOT)/report_table_approvals.tsv

report-test:
	"$(REPORT_PYTHON_BIN)" -m pytest \
		tests/reporting/test_artifact_run_summary.py \
		tests/reporting/test_report.py

demo-report:
	command -v "$(REPORT_PYTHON_BIN)" >/dev/null 2>&1 || { \
		printf 'ERROR: report Python is unavailable: %s\n' \
			"$(REPORT_PYTHON_BIN)" >&2; \
		exit 1; \
	}
	"$(REPORT_PYTHON_BIN)" -c \
		'import jinja2, jsonschema' || { \
		printf 'ERROR: report Python dependencies are unavailable: %s\n' \
			"$(REPORT_PYTHON_BIN)" >&2; \
		exit 1; \
		}
	"$(REPORT_PYTHON_BIN)" -m \
		tests.reporting.fixtures.artifact_run_summary_v1.build_fixture \
		--root "$(DEMO_REPORT_FIXTURE_ROOT)" \
		--full-science-demo
	SOURCE_DATE_EPOCH=1700000000 \
		"$(REPORT_PYTHON_BIN)" -I -m norad build run-summary \
		--source-checkout "$(CURDIR)" \
		--run-id "$(DEMO_REPORT_RUN_ID)" \
		--artifact-receipt \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).artifact_receipt.tsv" \
		--output-root "$(DEMO_REPORT_ARTIFACT_ROOT)" \
		--science-review-summary "$(DEMO_REPORT_SCIENCE_SUMMARY)" \
		--report-table-approvals "$(DEMO_REPORT_TABLE_APPROVALS)" \
		--execute
	SOURCE_DATE_EPOCH=1700000000 \
		"$(REPORT_PYTHON_BIN)" -I -m norad build report \
		--source-checkout "$(CURDIR)" \
		--run-summary \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.json" \
		--output-root "$(DEMO_REPORT_OUTPUT_ROOT)"
	SOURCE_DATE_EPOCH=1700000000 \
		"$(REPORT_PYTHON_BIN)" -I -m norad build report \
		--source-checkout "$(CURDIR)" \
		--run-summary \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.json" \
		--output-root "$(DEMO_REPORT_OUTPUT_ROOT)" \
		--execute
	@printf 'Demo report transaction: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)"
	@printf '  HTML: %s\n  Summary: %s\n  Receipt: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_report.html" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.tsv" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).report_outputs.tsv"
