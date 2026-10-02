#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo_root"

# shellcheck source=tests/tools/select_test_rscript.sh
source "$repo_root/tests/tools/select_test_rscript.sh" \
    "Step 08" "${STEP08_TEST_RSCRIPT_BIN:-}"

step08_engine="$repo_root/src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R"
foreign_help_cwd="$(mktemp -d "${TMPDIR:-/tmp}/emrys-step08-help.XXXXXX")"
cleanup_help_cwd() {
    rmdir "$foreign_help_cwd" 2>/dev/null || true
}
trap cleanup_help_cwd EXIT
step08_help="$(
    cd "$foreign_help_cwd"
    "$rscript_bin" "$step08_engine" --help
)"
[[ "$step08_help" == *"Usage:"* ]] || {
    printf 'ERROR: Step 08 --help output is missing its usage line.\n' >&2
    exit 1
}
[[ "$step08_help" == *"--cohort-id"* ]] || {
    printf 'ERROR: Step 08 --help output is missing --cohort-id.\n' >&2
    exit 1
}

python_bin="${REPORT_PYTHON_BIN:-$repo_root/.venv/bin/python}"
"$rscript_bin" tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R \
    "$rscript_bin" "$step08_engine" "$python_bin"
