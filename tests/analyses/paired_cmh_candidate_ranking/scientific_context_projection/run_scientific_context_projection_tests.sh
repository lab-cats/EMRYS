#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo_root"

rscript_request="${SCIENTIFIC_CONTEXT_TEST_RSCRIPT_BIN:-${RSCRIPT_BIN_OVERRIDE:-Rscript}}"
if [[ "$rscript_request" == */* ]]; then
    if [[ ! -x "$rscript_request" ]]; then
        printf 'ERROR: scientific-context real-R tests require an executable Rscript: %s\n' \
            "$rscript_request" >&2
        exit 1
    fi
    rscript_bin="$rscript_request"
elif rscript_bin="$(command -v "$rscript_request" 2>/dev/null)"; then
    :
elif [[ -n "${SCIENTIFIC_CONTEXT_TEST_RSCRIPT_BIN:-}${RSCRIPT_BIN_OVERRIDE:-}" ]]; then
    printf 'ERROR: scientific-context real-R tests could not resolve Rscript: %s\n' \
        "$rscript_request" >&2
    exit 1
else
    printf 'SKIP: scientific-context real-R tests require Rscript.\n'
    exit 0
fi

fake_contract="${EMRYS_TEST_FAKE_SCIENTIFIC_CONTEXT_R:-0}"
case "$fake_contract" in
    0) ;;
    1)
        [[ -n "${FAKE_R_LOG:-}" ]] || {
            printf 'ERROR: fake scientific-context R contract requires FAKE_R_LOG.\n' >&2
            exit 1
        }
        "$rscript_bin" \
            src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.R \
            --help >/dev/null
        printf 'SKIP: explicit fake-R contract logged one Step 10 invocation.\n'
        exit 0
        ;;
    *)
        printf 'ERROR: EMRYS_TEST_FAKE_SCIENTIFIC_CONTEXT_R must be 0 or 1.\n' >&2
        exit 1
        ;;
esac

"$rscript_bin" -e '
required <- c("Biostrings", "GenomicRanges", "IRanges", "Rsamtools")
missing <- required[
    !vapply(required, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing) > 0L) {
    message(
        "ERROR: scientific-context real-R tests are missing package(s): ",
        paste(missing, collapse = ", ")
    )
    quit(status = 1L)
}
'

python_bin="${REPORT_PYTHON_BIN:-$repo_root/.venv/bin/python}"
[[ -x "$python_bin" ]] || {
    printf 'ERROR: scientific-context tests require Python: %s\n' "$python_bin" >&2
    exit 1
}

RSCRIPT_BIN_OVERRIDE="$rscript_bin" \
    "$python_bin" -m pytest -q \
    tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/test_real_r_projection.py
