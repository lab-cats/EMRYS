#!/usr/bin/env bash
# Execute GATK through the neutral selected-Java environment authority.

admit_gatk_helper_python() {
    local python_bin="${NORAD_SHA256_PYTHON:-}"

    [[ -n "$python_bin" ]] || {
        printf 'ERROR: NORAD_SHA256_PYTHON must bind an absolute Python 3.11+ launcher for controlled GATK execution.\n' >&2
        return 2
    }
    [[ "$python_bin" == /* ]] || {
        printf 'ERROR: NORAD_SHA256_PYTHON must be an absolute path: %s\n' "$python_bin" >&2
        return 2
    }
    [[ -x "$python_bin" ]] || {
        printf 'ERROR: NORAD_SHA256_PYTHON is not executable: %s\n' "$python_bin" >&2
        return 2
    }
    "$python_bin" -X pycache_prefix=/dev/null -I -c \
        'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 2)' || {
        printf 'ERROR: NORAD_SHA256_PYTHON must run Python 3.11 or newer: %s\n' "$python_bin" >&2
        return 2
    }
    export NORAD_SHA256_PYTHON="$python_bin"
    export NORAD_REQUIRE_BOUND_SHA256=1
}

invoke_gatk_with_selected_java() {
    local selected_java="$1"
    shift
    local python_bin
    local helper

    admit_gatk_helper_python || return $?
    python_bin="$NORAD_SHA256_PYTHON"
    helper="$(dirname -- "${BASH_SOURCE[0]}")/process_environment.py"
    "$python_bin" -X pycache_prefix=/dev/null -I "$helper" \
        --java-bin "$selected_java" -- "$@"
}
