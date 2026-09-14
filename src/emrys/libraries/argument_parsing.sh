#!/usr/bin/env bash
# shellcheck disable=SC2154
# Shared argument parsing helpers for Bash stage owners.

: "${DIE_PREFIX:=ERROR}"

die() {
    printf '%s: %s\n' "$DIE_PREFIX" "$*" >&2
    exit 1
}

die2() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

validate_and_print_java() {
    local java_bin="$1"
    local java_version_output=""
    local java_version_status=0
    if java_version_output="$("$java_bin" -version 2>&1)"; then
        local java_version_line="${java_version_output%%$'\n'*}"
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

    if (( java_major < 17 )); then
        echo "ERROR: GATK requires Java 17 or newer; found Java ${java_major} at ${java_bin}" >&2
        exit 2
    fi

    printf 'Java version:\nJAVA_HOME: %s\nJava: %s\n%s\n' \
        "${JAVA_HOME:-<unset>}" "$java_bin" "$java_version_output"
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
    EMRYS_REQUIRED_ARGUMENTS=("$@")
    local argument
    for argument in "$@"; do
        printf -v "$argument" '%s' ""
    done
}

require_arguments() {
    local argument
    for argument in "${EMRYS_REQUIRED_ARGUMENTS[@]}"; do
        [[ -n "${!argument}" ]] ||
            die "Missing required argument: --${argument//_/-}."
    done
}

# Workers receive scratch and staging ownership from the task runner.
require_task_work_dir() {
    [[ -n "${EMRYS_TASK_WORK_DIR:-}" && -d "$EMRYS_TASK_WORK_DIR" ]] ||
        die "This internal worker requires EMRYS_TASK_WORK_DIR from the Run task runner."
}
