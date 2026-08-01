#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

rscript_request="${RSCRIPT_BIN_OVERRIDE:-Rscript}"
if [[ -n "${STEP08_TEST_RSCRIPT_BIN:-}" ]]; then
    rscript_request="$STEP08_TEST_RSCRIPT_BIN"
fi

if [[ "$rscript_request" == */* ]]; then
    if [[ ! -e "$rscript_request" ]]; then
        printf 'ERROR: explicitly requested Rscript does not exist: %s\n' \
            "$rscript_request" >&2
        exit 1
    fi
    if [[ ! -x "$rscript_request" ]]; then
        printf 'ERROR: explicitly requested Rscript is not executable: %s\n' \
            "$rscript_request" >&2
        exit 1
    fi
    rscript_bin="$rscript_request"
elif rscript_bin="$(command -v "$rscript_request" 2>/dev/null)"; then
    :
elif [[ -n "${RSCRIPT_BIN_OVERRIDE:-}${STEP08_TEST_RSCRIPT_BIN:-}" ]]; then
    printf 'ERROR: explicitly requested Rscript was not found on PATH: %s\n' \
        "$rscript_request" >&2
    exit 1
else
    printf 'SKIP: Step 08 real-R fixtures require Rscript; Rscript is not available.\n'
    exit 0
fi

if ! "$rscript_bin" -e '
required <- c(
    "VariantAnnotation", "GenomicRanges", "IRanges", "S4Vectors",
    "SummarizedExperiment", "GenomeInfoDb", "BiocGenerics", "rtracklayer"
)
missing <- required[
    !vapply(required, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing) > 0L) {
    message(
        "ERROR: Step 08 real-R fixtures are blocked by missing R package(s): ",
        paste(missing, collapse = ", ")
    )
    quit(status = 1L)
}
'; then
    exit 1
fi

step08_help="$("$rscript_bin" scripts/step_08_vcf_preprocessing.R --help)"
[[ "$step08_help" == *"Usage:"* ]] || {
    printf 'ERROR: Step 08 --help output is missing its usage line.\n' >&2
    exit 1
}
[[ "$step08_help" == *"--cohort-id"* ]] || {
    printf 'ERROR: Step 08 --help output is missing --cohort-id.\n' >&2
    exit 1
}

"$rscript_bin" tests/r/test_step_08_vcf_preprocessing.R "$rscript_bin"
