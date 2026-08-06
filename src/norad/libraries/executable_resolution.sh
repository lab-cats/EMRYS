# Neutral executable-value resolution shared by named Bash stage producers.

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
