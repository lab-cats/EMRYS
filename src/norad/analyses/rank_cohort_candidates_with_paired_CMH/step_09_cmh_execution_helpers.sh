# Step 09 execution and publication helpers.

append_sample_columns() {
    local base_header="$1"
    local sample_field
    local sample_id
    local appended_columns=""

    for sample_field in DP AD AF; do
        for sample_id in "${sample_ids[@]}"; do
            appended_columns+=$'\t'"${sample_field}__${sample_id}"
        done
    done
    printf '%s%s' "$base_header" "$appended_columns"
}

cleanup() {
    local status=$?
    local rollback_failed=false
    trap - EXIT HUP INT TERM
    if [[ "$scratch_owned" == true ]]; then
        for temp in "${temps[@]}"; do rm -f "$temp" || true; done
    fi
    if [[ "$publication_started" == true && "$publication_committed" != true ]]; then
        for index in "${!finals[@]}"; do
            if [[ "$previous_set" != true ]]; then
                if ! rm -f "${finals[$index]}"; then
                    printf 'ERROR: Could not remove partially published Step 09 output during rollback: %s\n' \
                        "${finals[$index]}" >&2
                    rollback_failed=true
                fi
            elif [[ -e "${backups[$index]}" ]]; then
                if ! rm -f "${finals[$index]}"; then
                    printf 'ERROR: Could not clear Step 09 output before restoring its backup: %s\n' \
                        "${finals[$index]}" >&2
                    rollback_failed=true
                elif ! mv "${backups[$index]}" "${finals[$index]}"; then
                    printf 'ERROR: Could not restore Step 09 backup during rollback: %s\n' \
                        "${backups[$index]}" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "${finals[$index]}" ]]; then
                printf 'ERROR: Step 09 rollback found neither a final output nor its backup: %s\n' \
                    "${finals[$index]}" >&2
                rollback_failed=true
            fi
        done
        if [[ "$rollback_failed" == true ]]; then
            [[ "$status" -ne 0 ]] || status=1
            printf 'ERROR: Step 09 rollback was incomplete; retaining the owned lock for operator recovery: %s\n' \
                "$lock_path" >&2
        fi
    fi
    if [[ "$scratch_owned" == true && "$publication_committed" == true ]]; then
        for backup in "${backups[@]}"; do rm -f "$backup" || true; done
    fi
    if [[ "$rollback_failed" != true &&
          "${lock_owned:-false}" == true && -d "$lock_path" ]]; then
        rm -f "$lock_owner_tmp" || true
        if [[ "${lock_owner_written:-false}" == true ]]; then
            if [[ -f "$lock_path/owner" ]] &&
               grep -Fqx $'run_token\t'"$run_token" "$lock_path/owner"; then
                rm -f "$lock_path/owner" || true
            fi
        elif [[ -f "$lock_path/owner" ]] &&
             grep -Fqx $'run_token\t'"$run_token" "$lock_path/owner"; then
            # mv may have completed immediately before an interrupt, before
            # lock_owner_written could be flipped to true.
            rm -f "$lock_path/owner" || true
        fi
        rmdir "$lock_path" 2>/dev/null || true
    fi
    exit "$status"
}

arm_signal_traps() {
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

defer_signal_traps() {
    trap 'pending_signal=129' HUP
    trap 'pending_signal=130' INT
    trap 'pending_signal=143' TERM
}

exit_for_pending_signal() {
    local signal_status="$pending_signal"
    if [[ "$signal_status" -ne 0 ]]; then
        pending_signal=0
        exit "$signal_status"
    fi
}
