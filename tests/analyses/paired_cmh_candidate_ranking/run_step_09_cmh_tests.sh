#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
test_script="$repo_root/tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_editing_site_calling.R"

# shellcheck source=tests/tools/select_test_rscript.sh
source "$repo_root/tests/tools/select_test_rscript.sh" \
    "Step 09" "${STEP09_TEST_RSCRIPT_BIN:-}"

step09_help="$("$rscript_bin" "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" --help)"
[[ "$step09_help" == *"Usage:"* ]] || {
    echo "Step 09 --help output is missing its usage line." >&2
    exit 1
}
[[ "$step09_help" == *"--analysis-id"* ]] || {
    echo "Step 09 --help output is missing --analysis-id." >&2
    exit 1
}

exec "$rscript_bin" "$test_script"
