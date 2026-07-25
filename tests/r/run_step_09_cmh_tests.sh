#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_script="$repo_root/tests/r/test_step_09_cmh_editing_site_calling.R"

explicit_rscript="${STEP09_TEST_RSCRIPT_BIN:-${RSCRIPT_BIN_OVERRIDE:-}}"
if [[ -n "$explicit_rscript" ]]; then
    if [[ "$explicit_rscript" == */* ]]; then
        if [[ ! -x "$explicit_rscript" ]]; then
            echo "Step 09 real-R tests require an executable Rscript override: $explicit_rscript" >&2
            exit 1
        fi
        rscript_bin="$explicit_rscript"
    else
        if ! command -v "$explicit_rscript" >/dev/null 2>&1; then
            echo "Step 09 real-R tests could not resolve Rscript override: $explicit_rscript" >&2
            exit 1
        fi
        rscript_bin="$(command -v "$explicit_rscript")"
    fi
else
    if ! command -v Rscript >/dev/null 2>&1; then
        echo "SKIP: Step 09 real-R tests require Rscript; no default executable is available."
        exit 0
    fi
    rscript_bin="$(command -v Rscript)"
fi

exec "$rscript_bin" "$test_script"
