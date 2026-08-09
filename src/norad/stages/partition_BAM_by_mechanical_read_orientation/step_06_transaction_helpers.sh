#!/usr/bin/env bash
# Step 06 final-set state, rollback, cleanup, and stale-path helpers.

count_existing_final_outputs() {
    local count=0

    [[ -e "$output_fwd_bam" ]] && count=$((count + 1))
    [[ -e "$output_fwd_bai" ]] && count=$((count + 1))
    [[ -e "$output_rev_bam" ]] && count=$((count + 1))
    [[ -e "$output_rev_bai" ]] && count=$((count + 1))
    [[ -e "$output_counts_tsv" ]] && count=$((count + 1))
    printf '%s\n' "$count"
}

confirm_final_set_state() {
    local final_count

    final_count="$(count_existing_final_outputs)"
    if [[ "$final_count" == "5" ]]; then
        previous_final_set_present=true
    elif [[ "$final_count" == "0" ]]; then
        previous_final_set_present=false
    else
        die "Step 06 final outputs are inconsistent; expected all five outputs or none."
    fi
}

rollback_publish() {
    if [[ "$backup_started" != true || "$final_publish_complete" == true ]]; then
        return
    fi

    printf 'Rolling back Step 06 read-orientation outputs...\n' >&2

    if [[ "$previous_final_set_present" == true ]]; then
        # Restore only files this invocation actually moved to backup; this
        # protects against compounding a partial publish failure.
        if [[ "$fwd_bam_backed_up" == true && -e "$backup_fwd_bam" ]]; then
            rm -f "$output_fwd_bam"
            mv "$backup_fwd_bam" "$output_fwd_bam" || true
            fwd_bam_backed_up=false
        fi

        if [[ "$fwd_bai_backed_up" == true && -e "$backup_fwd_bai" ]]; then
            rm -f "$output_fwd_bai"
            mv "$backup_fwd_bai" "$output_fwd_bai" || true
            fwd_bai_backed_up=false
        fi

        if [[ "$rev_bam_backed_up" == true && -e "$backup_rev_bam" ]]; then
            rm -f "$output_rev_bam"
            mv "$backup_rev_bam" "$output_rev_bam" || true
            rev_bam_backed_up=false
        fi

        if [[ "$rev_bai_backed_up" == true && -e "$backup_rev_bai" ]]; then
            rm -f "$output_rev_bai"
            mv "$backup_rev_bai" "$output_rev_bai" || true
            rev_bai_backed_up=false
        fi

        if [[ "$counts_tsv_backed_up" == true && -e "$backup_counts_tsv" ]]; then
            rm -f "$output_counts_tsv"
            mv "$backup_counts_tsv" "$output_counts_tsv" || true
            counts_tsv_backed_up=false
        fi
    else
        rm -f "$output_fwd_bam" "$output_fwd_bai"
        rm -f "$output_rev_bam" "$output_rev_bai"
        rm -f "$output_counts_tsv"
    fi
}

cleanup() {
    local status="$1"

    set +e

    # Rollback must run before temp cleanup so backup files remain available.
    if [[ "$status" -ne 0 ]]; then
        rollback_publish
    fi

    rm -f "$tmp_99_bam" "$tmp_147_bam" "$tmp_83_bam" "$tmp_163_bam"
    rm -f "$tmp_fwd_bam" "$tmp_fwd_bai" "$tmp_rev_bam" "$tmp_rev_bai"
    rm -f "$tmp_counts_tsv"

    if [[ "$status" -eq 0 || "$backup_started" == true ]]; then
        rm -f "$backup_fwd_bam" "$backup_fwd_bai"
        rm -f "$backup_rev_bam" "$backup_rev_bai"
        rm -f "$backup_counts_tsv"
    fi

    remove_owned_lock
}

refuse_stale_paths() {
    local path

    for path in \
        "$tmp_99_bam" \
        "$tmp_147_bam" \
        "$tmp_83_bam" \
        "$tmp_163_bam" \
        "$tmp_fwd_bam" \
        "$tmp_fwd_bai" \
        "$tmp_rev_bam" \
        "$tmp_rev_bai" \
        "$tmp_counts_tsv" \
        "$backup_fwd_bam" \
        "$backup_fwd_bai" \
        "$backup_rev_bam" \
        "$backup_rev_bai" \
        "$backup_counts_tsv"
    do
        # A matching run-token temp/backup path means a prior attempt may need
        # human inspection; do not adopt or delete it as if it were ours.
        [[ ! -e "$path" ]] || die "Refusing to reuse stale Step 06 path: $path"
    done
}
