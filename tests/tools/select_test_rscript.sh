#!/usr/bin/env bash
# Source with owner label and optional owner override; success sets rscript_bin.
# Refusal/optional absence exits the wrapper, never emits a path on stdout.
rscript_owner="$1"
rscript_override="${2:-${RSCRIPT_BIN_OVERRIDE:-}}"
rscript_request="${rscript_override:-Rscript}"
if [[ "$rscript_request" == */* ]]; then
    rscript_bin="$rscript_request"
else
    rscript_bin="$(command -v "$rscript_request" 2>/dev/null || true)"
fi
if [[ -z "$rscript_bin" || ! -x "$rscript_bin" || -d "$rscript_bin" ]]; then
    if [[ -n "$rscript_override" ]]; then
        printf 'ERROR: %s real-R tests require an executable Rscript: %s\n' \
            "$rscript_owner" "$rscript_request" >&2
        exit 1
    fi
    printf 'SKIP: %s real-R tests require Rscript; no default executable is available.\n' \
        "$rscript_owner"
    exit 0
fi
