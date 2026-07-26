#!/usr/bin/env bash
# Thin public launcher for the Step 09c scientific-validation evidence package.
#
# The adjacent Python implementation owns input validation, dry-run behavior,
# output generation, locking, and atomic publication. This wrapper only
# validates the public command-line shape, resolves Python, prints the exact
# delegated command, and preserves the implementation's exit status.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  scripts/step_09c_scientific_validation.sh \
    --review-id REVIEW_ID \
    --sample-manifest SAMPLE_MANIFEST \
    --partition-manifest PARTITION_MANIFEST \
    --step08-sites STEP08_SITES \
    --step08-inputs STEP08_INPUTS \
    --step08-summary STEP08_SUMMARY \
    --step09-analysis-dir STEP09_ANALYSIS_DIR \
    --review-plan REVIEW_PLAN \
    --evidence-manifest EVIDENCE_MANIFEST \
    --output-root OUTPUT_ROOT \
    [--execute]

Validate and summarize the explicitly declared Step 09c scientific-review
evidence package. Dry-run is the default. Add --execute to publish the
validated output transaction.

Environment:
  PYTHON_BIN_OVERRIDE  Explicit Python executable or command name.
                       Defaults to python3.

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

review_id=""
sample_manifest=""
partition_manifest=""
step08_sites=""
step08_inputs=""
step08_summary=""
step09_analysis_dir=""
review_plan=""
evidence_manifest=""
output_root=""
execute=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --review-id)
            require_value "$1" "${2:-}"
            review_id="$2"
            shift 2
            ;;
        --sample-manifest)
            require_value "$1" "${2:-}"
            sample_manifest="$2"
            shift 2
            ;;
        --partition-manifest)
            require_value "$1" "${2:-}"
            partition_manifest="$2"
            shift 2
            ;;
        --step08-sites)
            require_value "$1" "${2:-}"
            step08_sites="$2"
            shift 2
            ;;
        --step08-inputs)
            require_value "$1" "${2:-}"
            step08_inputs="$2"
            shift 2
            ;;
        --step08-summary)
            require_value "$1" "${2:-}"
            step08_summary="$2"
            shift 2
            ;;
        --step09-analysis-dir)
            require_value "$1" "${2:-}"
            step09_analysis_dir="$2"
            shift 2
            ;;
        --review-plan)
            require_value "$1" "${2:-}"
            review_plan="$2"
            shift 2
            ;;
        --evidence-manifest)
            require_value "$1" "${2:-}"
            evidence_manifest="$2"
            shift 2
            ;;
        --output-root)
            require_value "$1" "${2:-}"
            output_root="$2"
            shift 2
            ;;
        --execute)
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

for required_name in \
    review_id \
    sample_manifest \
    partition_manifest \
    step08_sites \
    step08_inputs \
    step08_summary \
    step09_analysis_dir \
    review_plan \
    evidence_manifest \
    output_root
do
    [[ -n "${!required_name}" ]] ||
        die "Missing required argument: --${required_name//_/-}."
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python_script="$script_dir/step_09c_scientific_validation.py"
[[ -f "$python_script" && -r "$python_script" ]] ||
    die "Step 09c Python implementation does not exist or is not readable: $python_script"

python_value="${PYTHON_BIN_OVERRIDE:-python3}"
python_bin="$(resolve_executable "$python_value")"

command_args=(
    "$python_bin"
    "$python_script"
    --review-id "$review_id"
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --step08-sites "$step08_sites"
    --step08-inputs "$step08_inputs"
    --step08-summary "$step08_summary"
    --step09-analysis-dir "$step09_analysis_dir"
    --review-plan "$review_plan"
    --evidence-manifest "$evidence_manifest"
    --output-root "$output_root"
)
if [[ "$execute" == true ]]; then
    command_args+=(--execute)
fi

printf 'Step 09c scientific-validation launcher:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Review ID: %s\n' "$review_id"
printf '  Python: %s\n' "$python_bin"
printf '  Python implementation: %s\n' "$python_script"
printf 'Delegated command:\n'
print_command "${command_args[@]}"

exec "${command_args[@]}"
