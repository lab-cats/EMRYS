#!/usr/bin/env bash
# Shared argument parsing helpers for Bash stage wrappers.

: "${DIE_PREFIX:=ERROR}"

die() {
    printf '%s: %s\n' "$DIE_PREFIX" "$*" >&2
    exit 1
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

require_value() {
    local option="$1"
    local value="${2:-}"
    if [[ -z "$value" || "$value" == --* ]]; then
        die "$option requires a value."
    fi
}
