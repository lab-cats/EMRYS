# Neutral executable-value resolution shared by named Bash consumers.

resolve_overridable_executable() {
    local label="$1"
    local value="${2:-}"
    local override_var="${3:-}"
    local default_name="$4"
    local home_relative="${5:-}"

    if [[ -z "$value" && -n "$override_var" && -n "${!override_var:-}" ]]; then
        value="${!override_var}"
    fi

    if [[ -z "$value" && -n "$home_relative" && -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}${home_relative}" ]]; then
        value="${JAVA_HOME}${home_relative}"
    fi

    resolve_executable_value "$label" "$value" "$default_name"
}

resolve_executable_value() {
    local label="$1"
    local value="$2"
    local default_name="$3"
    local resolved

    if [[ -z "$value" ]]; then
        value="$default_name"
    fi

    if [[ "$value" == */* ]]; then
        [[ -e "$value" ]] || die "$label does not exist: $value"
        [[ -x "$value" ]] || die "$label exists but is not executable: $value"
        printf '%s\n' "$value"
    else
        resolved="$(command -v "$value" || true)"
        [[ -n "$resolved" ]] || die "$label executable was not found on PATH: $value"
        printf '%s\n' "$resolved"
    fi
}
