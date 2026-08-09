#!/usr/bin/env bash
# Thin public launcher for the Step 09c scientific-validation evidence package.
#
# The adjacent Python implementation owns input validation, dry-run behavior,
# output generation, locking, and atomic publication. This wrapper only
# validates the public command-line shape, resolves Python, prints the exact
# delegated command, and preserves the implementation's exit status.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'USAGE'
Usage:
  src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.sh \
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

# shellcheck source=../../libraries/executable_resolution.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/argument_parsing.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/argument_parsing.sh"


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
        --review-id) assign_option_value "$1" "${2:-}" review_id; shift 2 ;;
        --sample-manifest) assign_option_value "$1" "${2:-}" sample_manifest; shift 2 ;;
        --partition-manifest) assign_option_value "$1" "${2:-}" partition_manifest; shift 2 ;;
        --step08-sites) assign_option_value "$1" "${2:-}" step08_sites; shift 2 ;;
        --step08-inputs) assign_option_value "$1" "${2:-}" step08_inputs; shift 2 ;;
        --step08-summary) assign_option_value "$1" "${2:-}" step08_summary; shift 2 ;;
        --step09-analysis-dir) assign_option_value "$1" "${2:-}" step09_analysis_dir; shift 2 ;;
        --review-plan) assign_option_value "$1" "${2:-}" review_plan; shift 2 ;;
        --evidence-manifest) assign_option_value "$1" "${2:-}" evidence_manifest; shift 2 ;;
        --output-root) assign_option_value "$1" "${2:-}" output_root; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
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

python_script="$script_dir/step_09c_scientific_validation.py"
[[ -f "$python_script" && -r "$python_script" ]] ||
    die "Step 09c Python implementation does not exist or is not readable: $python_script"

python_value="${PYTHON_BIN_OVERRIDE:-python3}"
if [[ "$python_value" == */* ]]; then
    [[ -e "$python_value" ]] || die "Python executable does not exist: $python_value"
    [[ -x "$python_value" ]] || die "Python path is not executable: $python_value"
    python_bin="$python_value"
else
    python_bin="$(command -v "$python_value")" ||
        die "Python executable was not found on PATH: $python_value"
    [[ -n "$python_bin" ]] || die "Python executable was not found on PATH: $python_value"
fi

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
