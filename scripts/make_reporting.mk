QUARTO_VERSION := 1.9.38
QUARTO_SHA256 := 47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a

DEMO_REPORT_RUN_ID := synthetic_full_run_demo
DEMO_REPORT_FIXTURE_ROOT := $(DEMO_REPORT_ROOT)/full-run-fixture
DEMO_REPORT_ARTIFACT_ROOT := $(DEMO_REPORT_FIXTURE_ROOT)/artifacts
DEMO_REPORT_OUTPUT_ROOT := $(DEMO_REPORT_ROOT)/reports
DEMO_REPORT_SCIENCE_SUMMARY := $(DEMO_REPORT_FIXTURE_ROOT)/science_fixture/step09c_fixture/output/review_fixture/review_fixture.step09c_review_summary.tsv
DEMO_REPORT_TABLE_APPROVALS := $(DEMO_REPORT_FIXTURE_ROOT)/report_table_approvals.tsv

quarto-restore:
	"$(PYTHON_BIN)" scripts/restore_quarto.py \
		--install-root "$(QUARTO_TOOLS_ROOT)"

report-test:
	test -x "$(QUARTO_BIN)" || { \
		printf 'ERROR: pinned Quarto is unavailable: %s\nRun make quarto-restore first.\n' \
			"$(QUARTO_BIN)" >&2; \
			exit 1; \
	}
	"$(PYTHON_BIN)" scripts/restore_quarto.py \
		--install-root "$(QUARTO_TOOLS_ROOT)"
	NORAD_REQUIRE_QUARTO=1 QUARTO_BIN="$(QUARTO_BIN)" \
		"$(REPORT_PYTHON_BIN)" -m pytest \
		tests/test_quarto_restore.py \
		tests/reporting/test_artifact_run_summary.py \
		tests/reporting/test_report_html_v1.py \
		tests/reporting/test_report_exports_v1.py
	QUARTO_BIN="$(QUARTO_BIN)" REPORT_PYTHON_BIN="$(REPORT_PYTHON_BIN)" \
		bash tests/reporting/test_render_run_report.sh

validation-report-runtime:
	test -n "$(REPORT_TEST_RESULT)" || { \
		printf 'ERROR: REPORT_TEST_RESULT is required\n' >&2; \
		exit 1; \
	}
	test -x "$(QUARTO_BIN)" || { \
		printf 'ERROR: pinned Quarto is unavailable: %s\nRun make quarto-restore first.\n' \
			"$(QUARTO_BIN)" >&2; \
			exit 1; \
	}
	"$(PYTHON_BIN)" scripts/restore_quarto.py \
		--install-root "$(QUARTO_TOOLS_ROOT)"
	NORAD_REQUIRE_QUARTO=1 QUARTO_BIN="$(QUARTO_BIN)" \
		"$(REPORT_PYTHON_BIN)" -m pytest -q --tb=short \
		-m report_runtime --junitxml="$(REPORT_TEST_RESULT)" \
		tests/reporting/test_report_html_v1.py \
		tests/reporting/test_report_exports_v1.py

demo-report:
	test -x "$(QUARTO_BIN)" || { \
		printf 'ERROR: pinned Quarto is unavailable: %s\nRun make quarto-restore first.\n' \
			"$(QUARTO_BIN)" >&2; \
			exit 1; \
	}
	command -v "$(REPORT_PYTHON_BIN)" >/dev/null 2>&1 || { \
		printf 'ERROR: report Python is unavailable: %s\n' \
			"$(REPORT_PYTHON_BIN)" >&2; \
		exit 1; \
	}
	"$(REPORT_PYTHON_BIN)" -c \
		'import jsonschema, pypdf, yaml' || { \
			printf 'ERROR: report Python dependencies are unavailable: %s\n' \
				"$(REPORT_PYTHON_BIN)" >&2; \
			exit 1; \
		}
	case "$(DEMO_REPORT_FORMATS)" in \
		html|pdf|all) ;; \
		*) \
			printf 'ERROR: DEMO_REPORT_FORMATS must be html, pdf, or all; observed: %s\n' \
				"$(DEMO_REPORT_FORMATS)" >&2; \
			exit 1; \
			;; \
	esac
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
		PYTHON_BIN_OVERRIDE="$(REPORT_PYTHON_BIN)" \
		src/norad/reporting/render_run_report.sh \
		--run-summary \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.json" \
		--output-root "$(DEMO_REPORT_OUTPUT_ROOT)" \
		--quarto-bin "$(QUARTO_BIN)" \
		--formats "$(DEMO_REPORT_FORMATS)"
	SOURCE_DATE_EPOCH=1700000000 \
		PYTHON_BIN_OVERRIDE="$(REPORT_PYTHON_BIN)" \
		src/norad/reporting/render_run_report.sh \
		--run-summary \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.json" \
		--output-root "$(DEMO_REPORT_OUTPUT_ROOT)" \
		--quarto-bin "$(QUARTO_BIN)" \
		--formats "$(DEMO_REPORT_FORMATS)" \
		--execute
	@printf 'Demo report bundle: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)"
	@case "$(DEMO_REPORT_FORMATS)" in \
		html|all) \
			printf '  HTML: %s\n' \
				"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_report.html" \
			;; \
	esac
	@case "$(DEMO_REPORT_FORMATS)" in \
		pdf|all) \
			printf '  PDF: %s\n' \
				"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_report.pdf" \
			;; \
	esac
	@printf '  Summary: %s\n  Receipt: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.tsv" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).report_outputs.tsv"
