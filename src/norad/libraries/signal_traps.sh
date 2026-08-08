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
    if [[ "${lock_acquired:-false}" != true ]]; then
        return
    fi

    if [[ -f "$lock_owner_file" ]] &&
       [[ "$(cat "$lock_owner_file")" == "run_token=$run_token" ]]; then
        rm -f "$lock_owner_file"
        rmdir "$lock_path" 2>/dev/null || true
        lock_acquired=false
    fi
}

__norad_run_exit_trap() {
    local status=$?
    trap - EXIT HUP INT TERM
    "$NORAD_EXIT_TRAP_CLEANUP_FN" "$status"
    exit "$status"
}
