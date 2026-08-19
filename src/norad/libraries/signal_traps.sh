# Shared signal trap helpers for Bash stages and analyses.

arm_signal_traps() {
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

acquire_lock() {
    local step_id=$1
    local owner="run_token=$run_token"

    if [[ -z "$step_id" ]]; then
        die "acquire_lock requires a step id."
    fi

    # mkdir is atomic for the lock directory; never break another invocation's
    # lock by modifying and/or removing it.
    if mkdir "$lock_path" 2>/dev/null; then
        printf '%s\n' "$owner" > "$lock_owner_file"
        lock_acquired=true
        return
    fi

    if [[ -f "$lock_owner_file" ]]; then
        die "$step_id lock already exists at $lock_path; owner: $(cat "$lock_owner_file")"
    fi

    die "$step_id lock already exists at $lock_path; owner: unknown"
}

set_exit_trap() {
    local cleanup_function=$1
    if [[ -z "$cleanup_function" ]]; then
        printf 'ERROR: set_exit_trap requires a cleanup function name.\n' >&2
        exit 2
    fi
    if ! declare -f "$cleanup_function" >/dev/null; then
        printf 'ERROR: set_exit_trap cleanup function was not found: %s\n' \
            "$cleanup_function" >&2
        exit 2
    fi

    NORAD_EXIT_TRAP_CLEANUP_FN="$cleanup_function"
    trap '__norad_run_exit_trap' EXIT
    arm_signal_traps
}

remove_owned_lock() {
    local owner="run_token=$run_token"
    local unexpected

    if [[ "${lock_acquired:-false}" != true ]]; then
        return
    fi

    if [[ -f "$lock_owner_file" ]] &&
       [[ "$(cat "$lock_owner_file")" == "$owner" ]]; then
        unexpected="$(
            find "$lock_path" -mindepth 1 -maxdepth 1 \
                ! -path "$lock_owner_file" -print -quit
        )" || {
            printf 'ERROR: Could not inspect owned lock directory: %s\n' \
                "$lock_path" >&2
            return 1
        }
        if [[ -n "$unexpected" ]]; then
            printf 'ERROR: Owned lock contains unexpected residue; preserving it: %s\n' \
                "$unexpected" >&2
            return 1
        fi
        if ! rm -f "$lock_owner_file"; then
            printf 'ERROR: Could not remove owned lock metadata: %s\n' \
                "$lock_owner_file" >&2
            return 1
        fi
        if ! rmdir "$lock_path" 2>/dev/null; then
            if [[ ! -e "$lock_owner_file" && -d "$lock_path" ]]; then
                (set -o noclobber; printf '%s\n' "$owner" > "$lock_owner_file") \
                    2>/dev/null || true
            fi
            printf 'ERROR: Could not remove owned lock directory; preserving residue: %s\n' \
                "$lock_path" >&2
            return 1
        fi
        lock_acquired=false
        return 0
    fi
    printf 'ERROR: Could not prove lock ownership for removal: %s\n' "$lock_path" >&2
    return 1
}

__norad_run_exit_trap() {
    local status=$?
    trap - EXIT HUP INT TERM
    "$NORAD_EXIT_TRAP_CLEANUP_FN" "$status"
    exit "$status"
}
