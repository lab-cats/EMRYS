#!/usr/bin/env bash
# Thin public launcher for the static NORAD run-report renderer.
#
# The adjacent Python implementation owns schema/table validation, static QMD
# generation, Quarto invocation, locking, rollback, and HTML validation. This
# wrapper only validates the public command-line shape, resolves Python, prints
# the exact delegated command, and preserves its exit status.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/reporting/render_run_report.sh \
    --run-summary RUN_SUMMARY_JSON \
    --output-root OUTPUT_ROOT \
    --quarto-bin QUARTO_BIN \
    [--formats html|pdf|all] \
    [--execute]

Render one canonical NORAD run-summary JSON as a static report bundle.
Dry-run is the default. Add --execute to publish:

  <output-root>/<run-id>/<run-id>.run_report.html   (html/all)
  <output-root>/<run-id>/<run-id>.run_report.pdf    (pdf/all)
  <output-root>/<run-id>/<run-id>.run_summary.tsv
  <output-root>/<run-id>/<run-id>.report_outputs.tsv  (published last)

The default format is all.

Environment:
  PYTHON_BIN_OVERRIDE  Explicit Python executable or command name.
                       When unset, prefers <repo>/.venv/bin/python when that
                       path is executable, then falls back to python3.
                       An explicit value is authoritative and never falls
                       back to another Python.

Options:
  -h, --help           Show this help message and exit.
USAGE
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_value() {
    local option="$1"
    local value="${2:-}"
    [[ -n "$value" && "$value" != --* ]] || die "$option requires a value."
}

resolve_executable() {
    local value="$1"
    local resolved

    if [[ "$value" == */* ]]; then
        [[ -e "$value" ]] || die "Python executable does not exist: $value"
        [[ -x "$value" ]] || die "Python path is not executable: $value"
        printf '%s\n' "$value"
        return
    fi

    resolved="$(command -v "$value" || true)"
    [[ -n "$resolved" ]] ||
        die "Python executable was not found on PATH: $value"
    printf '%s\n' "$resolved"
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

run_summary=""
output_root=""
quarto_bin=""
formats="all"
formats_seen=false
execute=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --run-summary)
            [[ -z "$run_summary" ]] ||
                die "--run-summary may be supplied only once."
            require_value "$1" "${2:-}"
            run_summary="$2"
            shift 2
            ;;
        --output-root)
            [[ -z "$output_root" ]] ||
                die "--output-root may be supplied only once."
            require_value "$1" "${2:-}"
            output_root="$2"
            shift 2
            ;;
        --quarto-bin)
            [[ -z "$quarto_bin" ]] ||
                die "--quarto-bin may be supplied only once."
            require_value "$1" "${2:-}"
            quarto_bin="$2"
            shift 2
            ;;
        --formats)
            [[ "$formats_seen" == false ]] ||
                die "--formats may be supplied only once."
            require_value "$1" "${2:-}"
            formats="$2"
            formats_seen=true
            shift 2
            ;;
        --execute)
            [[ "$execute" == false ]] ||
                die "--execute may be supplied only once."
            execute=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1. Run with --help for usage."
            ;;
    esac
done

[[ -n "$run_summary" ]] || die "Missing required argument: --run-summary."
[[ -n "$output_root" ]] || die "Missing required argument: --output-root."
[[ -n "$quarto_bin" ]] || die "Missing required argument: --quarto-bin."
[[ "$formats" == "html" || "$formats" == "pdf" || "$formats" == "all" ]] ||
    die "--formats must be html, pdf, or all; observed: $formats"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
python_script="$script_dir/render_run_report.py"
[[ -f "$python_script" && -r "$python_script" ]] ||
    die "Report Python implementation is missing or unreadable: $python_script"
artifact_contracts="$repo_root/src/norad/contracts/artifacts/validate_artifact_contracts.py"
[[ -f "$artifact_contracts" && -r "$artifact_contracts" ]] ||
    die "Artifact-contract validator is missing or unreadable: $artifact_contracts"

if [[ "${PYTHON_BIN_OVERRIDE+x}" == "x" ]]; then
    [[ -n "$PYTHON_BIN_OVERRIDE" ]] ||
        die "PYTHON_BIN_OVERRIDE was explicitly set but is empty."
    python_value="$PYTHON_BIN_OVERRIDE"
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
    python_value="$repo_root/.venv/bin/python"
else
    python_value="python3"
fi
python_bin="$(resolve_executable "$python_value")"

preflight_code='
import importlib.util
import sys
import jsonschema
import pypdf
import yaml
spec = importlib.util.spec_from_file_location(
    "_norad_artifact_contracts_preflight", sys.argv[1]
)
if spec is None or spec.loader is None:
    raise ImportError("unable to load artifact-contract validator")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
'
if ! preflight_output="$(
    "$python_bin" -c "$preflight_code" "$artifact_contracts" 2>&1
)"; then
    printf '%s\n' \
        "ERROR: Selected Python cannot import required report dependencies" \
        "       (jsonschema, pypdf, PyYAML, validate_artifact_contracts): $python_bin" \
        "       Use the repository .venv or set PYTHON_BIN_OVERRIDE to a compatible Python." \
        >&2
    if [[ -n "$preflight_output" ]]; then
        printf '       Import failure: %s\n' "$preflight_output" >&2
    fi
    exit 1
fi

command_args=(
    "$python_bin"
    "$python_script"
    --run-summary "$run_summary"
    --output-root "$output_root"
    --quarto-bin "$quarto_bin"
    --formats "$formats"
)
if [[ "$execute" == true ]]; then
    command_args+=(--execute)
fi

printf 'NORAD static run-report launcher:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Run summary: %s\n' "$run_summary"
printf '  Output root: %s\n' "$output_root"
printf '  Quarto: %s\n' "$quarto_bin"
printf '  Formats: %s\n' "$formats"
printf '  Python: %s\n' "$python_bin"
printf 'Delegated command:\n'
print_command "${command_args[@]}"

exec "${command_args[@]}"
