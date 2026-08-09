#!/usr/bin/env bash
# Shared argument parsing helpers for Bash stage wrappers.

: "${DIE_PREFIX:=ERROR}"

die() {
    printf '%s: %s\n' "$DIE_PREFIX" "$*" >&2
    exit 1
}

die2() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

require_java() {
    local java_bin_ref=$1
    local java_version_ref=$2
    local tool_name=$3
    local min_java_major=${4:-17}
    local override_hint=${5:-"Set JAVA_BIN_OVERRIDE to a Java ${min_java_major} executable."}
    local preferred_java_bin="${6:-}"

    local java_bin="${preferred_java_bin}"

    if [[ -z "$java_bin" ]]; then
        java_bin="${JAVA_BIN_OVERRIDE:-}"
    fi
    if [[ -z "$java_bin" && -n "${JAVA_HOME:-}" && -x "$JAVA_HOME/bin/java" ]]; then
        java_bin="$JAVA_HOME/bin/java"
    fi

    if [[ -z "$java_bin" ]]; then
        java_bin="$(command -v java || true)"
    fi

    if [[ -z "$java_bin" || ! -x "$java_bin" ]]; then
        echo "ERROR: No usable Java executable was found." >&2
        echo "$override_hint" >&2
        exit 2
    fi

    local java_version_output=""
    local java_version_status=0
    if java_version_output="$("$java_bin" -version 2>&1)"; then
        local java_version_line="$(printf '%s\n' "$java_version_output" | head -n 1)"
    else
        java_version_status=$?
        echo "ERROR: Could not determine Java version from: $java_version_output" >&2
        exit "$java_version_status"
    fi

    local java_major=""
    if [[ "$java_version_line" =~ version\ \"1\.([0-9]+) ]]; then
        java_major="${BASH_REMATCH[1]}"
    elif [[ "$java_version_line" =~ version\ \"([0-9]+) ]]; then
        java_major="${BASH_REMATCH[1]}"
    else
        echo "ERROR: Could not determine Java version from: $java_version_line" >&2
        exit 2
    fi

    if (( java_major < min_java_major )); then
        echo "ERROR: ${tool_name} requires Java ${min_java_major} or newer; found Java ${java_major} at ${java_bin}" >&2
        echo "Set JAVA_BIN_OVERRIDE to a Java ${min_java_major} executable available on compute nodes." >&2
        exit 2
    fi

    printf -v "$java_bin_ref" '%s' "$java_bin"
    printf -v "$java_version_ref" '%s\n' "$java_version_output"
}

validate_and_print_java() {
    local tool_name=$1
    local java_bin_ref=$2
    local java_version_ref=$3
    local heading=${4:-}
    local min_java_major=${5:-17}
    local override_hint=${6:-"Set JAVA_BIN_OVERRIDE to a Java ${min_java_major} executable."}
    local preferred_java_bin=${7:-}
    local strict_java_home=${8:-false}
    local java_bin
    local java_version_output

    require_java \
        "$java_bin_ref" \
        "$java_version_ref" \
        "$tool_name" \
        "$min_java_major" \
        "$override_hint" \
        "$preferred_java_bin"

    printf -v java_bin '%s' "${!java_bin_ref}"
    printf -v java_version_output '%s' "${!java_version_ref}"

    if [[ -n "$heading" ]]; then
        printf '%s\n' "$heading"
    fi
    if [[ "$strict_java_home" == true ]]; then
        printf 'JAVA_HOME: %s\n' "${JAVA_HOME}"
    else
        printf 'JAVA_HOME: %s\n' "${JAVA_HOME:-<unset>}"
    fi
    printf 'Java: %s\n' "$java_bin"
    printf '%s\n' "$java_version_output"
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

# Assign a validated option value to the owner-selected global variable.
assign_option_value() {
    local option="$1"
    local value="${2:-}"
    local target="$3"
    require_value "$option" "$value"
    printf -v "$target" '%s' "$value"
}

# One ordered roster owns both initialization and missing-argument diagnostics.
declare_required_arguments() {
    NORAD_REQUIRED_ARGUMENTS=("$@")
    local argument
    for argument in "$@"; do
        printf -v "$argument" '%s' ""
    done
}

require_arguments() {
    local argument
    for argument in "${NORAD_REQUIRED_ARGUMENTS[@]}"; do
        [[ -n "${!argument}" ]] ||
            die "Missing required argument: --${argument//_/-}."
    done
}

# Owner parsers call this from their catch-all branch. It deliberately updates
# their shared execute flag; help exits before the caller advances argv.
handle_execute_or_help() {
    case "${1:-}" in
        --execute)
            execute=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: ${1:-}. Run with --help for usage."
            ;;
    esac
}
