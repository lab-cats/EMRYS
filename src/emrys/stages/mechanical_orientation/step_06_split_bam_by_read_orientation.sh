#!/usr/bin/env bash
# Step 06: split one SplitNCigarReads BAM into mechanical read-orientation groups.
#
# Dry-run mode validates inputs and prints resolved paths, exact samtools
# commands, locking, temp paths, validation checks, and publish actions without
# creating output directories, locks, temp files, BAMs, indexes, or TSVs.
# Passing --execute runs samtools, validates temporary outputs, and publishes
# final BAM/BAI/TSV outputs only after validation succeeds.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/emrys/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --output-dir OUTPUT_DIR \
    --qc-dir QC_DIR \
    --threads THREADS \
    [--samtools-bin SAMTOOLS_BIN] \
    [--no-clobber] \
    [--execute]

Split one Step 05 split-N-cigar BAM into FWD_like and REV_like mechanical
read-orientation groups using legacy samtools flag filters.

By default this script runs in dry-run mode: it validates required existing
inputs, prints planned commands and validation checks, and writes nothing. Add
--execute to run samtools and publish outputs after validation.

Required arguments:
  --sample-id      Sample identifier used in output filenames.
  --input-bam      Split-N-cigar BAM from Step 05.
  --output-dir     Directory where orientation BAMs and BAIs are written.
  --qc-dir         Directory where orientation_counts.tsv is written.
  --threads        Number of threads for samtools view/merge; positive integer.

Options:
  --samtools-bin   samtools executable or path. Resolution order:
                   argument, SAMTOOLS_BIN_OVERRIDE, PATH.
  --no-clobber     Refuse an existing final output set. Required by orchestration.
  --execute        Execute samtools after validation. Without this, dry-run only.
  -h, --help       Show this help message and exit.

Read-orientation groups:
  FWD_like = samtools view -f 99 plus samtools view -f 147
  REV_like = samtools view -f 83 plus samtools view -f 163

These are mechanical read-orientation groups, not biological strand labels.
USAGE
}

# shellcheck source=../../libraries/executable_resolution.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/argument_parsing.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/signal_traps.sh"

declare_required_arguments sample_id input_bam output_dir qc_dir threads
requested_samtools_bin=""
execute=false
no_clobber=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --qc-dir) assign_option_value "$1" "${2:-}" qc_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" requested_samtools_bin; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

validate_positive_integer "--threads" "$threads"

# Step 05 publishes indexes as <bam>.bai. Keep Step 06 strict so stale or
# incomplete upstream split-N-cigar outputs fail before any orientation work.
input_bai="$input_bam.bai"
samtools_bin="$(resolve_overridable_executable \
    "samtools" "$requested_samtools_bin" SAMTOOLS_BIN_OVERRIDE samtools)"
run_token="${EMRYS_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "Step 06 run token" "$run_token"

# The four BAM/BAI outputs and counts TSV are a single downstream contract.
# Treat them as one publication set so reruns never leave mixed generations.
output_fwd_bam="$output_dir/${sample_id}.FWD_like.bam"
output_fwd_bai="$output_fwd_bam.bai"
output_rev_bam="$output_dir/${sample_id}.REV_like.bam"
output_rev_bai="$output_rev_bam.bai"
output_counts_tsv="$qc_dir/${sample_id}.orientation_counts.tsv"

# One sample may be retried while others are running; lock only that sample's
# orientation output directory rather than the whole results tree.
lock_path="$output_dir/.${sample_id}.step06.lock"
lock_owner_file="$lock_path/owner"

# Temp paths include both sample and run token so failed cluster attempts can be
# identified without colliding with a later rerun.
tmp_99_bam="$output_dir/.${sample_id}.step06.${run_token}.99.tmp.bam"
tmp_147_bam="$output_dir/.${sample_id}.step06.${run_token}.147.tmp.bam"
tmp_83_bam="$output_dir/.${sample_id}.step06.${run_token}.83.tmp.bam"
tmp_163_bam="$output_dir/.${sample_id}.step06.${run_token}.163.tmp.bam"
tmp_fwd_bam="$output_dir/.${sample_id}.step06.${run_token}.FWD_like.tmp.bam"
tmp_fwd_bai="$tmp_fwd_bam.bai"
tmp_rev_bam="$output_dir/.${sample_id}.step06.${run_token}.REV_like.tmp.bam"
tmp_rev_bai="$tmp_rev_bam.bai"
tmp_counts_tsv="$qc_dir/.${sample_id}.step06.${run_token}.orientation_counts.tmp.tsv"

backup_fwd_bam="$output_dir/.${sample_id}.step06.${run_token}.previous.FWD_like.bam"
backup_fwd_bai="$output_dir/.${sample_id}.step06.${run_token}.previous.FWD_like.bam.bai"
backup_rev_bam="$output_dir/.${sample_id}.step06.${run_token}.previous.REV_like.bam"
backup_rev_bai="$output_dir/.${sample_id}.step06.${run_token}.previous.REV_like.bam.bai"
backup_counts_tsv="$qc_dir/.${sample_id}.step06.${run_token}.previous.orientation_counts.tsv"

# Cleanup and rollback decisions are stateful because BAM, BAI, and TSV
# publication is a multi-file operation rather than a single atomic rename.
lock_acquired=false
previous_final_set_present=false
backup_started=false
fwd_bam_backed_up=false
fwd_bai_backed_up=false
rev_bam_backed_up=false
rev_bai_backed_up=false
counts_tsv_backed_up=false
final_publish_complete=false

# Keep command construction in arrays so dry-run output is copy-pasteable and
# arguments with spaces remain safe if paths ever contain them.
view_99_command=(
    "$samtools_bin"
    view
    -@ "$threads"
    -b
    -f 99
    "$input_bam"
    -o "$tmp_99_bam"
)

view_147_command=(
    "$samtools_bin"
    view
    -@ "$threads"
    -b
    -f 147
    "$input_bam"
    -o "$tmp_147_bam"
)

view_83_command=(
    "$samtools_bin"
    view
    -@ "$threads"
    -b
    -f 83
    "$input_bam"
    -o "$tmp_83_bam"
)

view_163_command=(
    "$samtools_bin"
    view
    -@ "$threads"
    -b
    -f 163
    "$input_bam"
    -o "$tmp_163_bam"
)

merge_fwd_command=(
    "$samtools_bin"
    merge
    -@ "$threads"
    -o "$tmp_fwd_bam"
    "$tmp_99_bam"
    "$tmp_147_bam"
)

merge_rev_command=(
    "$samtools_bin"
    merge
    -@ "$threads"
    -o "$tmp_rev_bam"
    "$tmp_83_bam"
    "$tmp_163_bam"
)

index_fwd_command=(
    "$samtools_bin"
    index
    "$tmp_fwd_bam"
)

index_rev_command=(
    "$samtools_bin"
    index
    "$tmp_rev_bam"
)

input_count_command=(
    "$samtools_bin"
    view
    -c
    "$input_bam"
)

flag_99_count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_99_bam"
)

flag_147_count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_147_bam"
)

flag_83_count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_83_bam"
)

flag_163_count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_163_bam"
)

fwd_count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_fwd_bam"
)

rev_count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_rev_bam"
)

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
    if [[ "$no_clobber" == true ]]; then
        [[ "$final_count" == "0" ]] ||
            die "Step 06 --no-clobber requires all five final outputs to be absent; found: $final_count"
        previous_final_set_present=false
        return
    fi

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
        return 0
    fi

    printf 'Rolling back Step 06 read-orientation outputs...\n' >&2

    if [[ "$no_clobber" == true ]]; then
        local rollback_ok=true
        remove_owned_published_file \
            "Step 06 FWD BAM" "$tmp_fwd_bam" "$output_fwd_bam" || rollback_ok=false
        remove_owned_published_file \
            "Step 06 FWD BAI" "$tmp_fwd_bai" "$output_fwd_bai" || rollback_ok=false
        remove_owned_published_file \
            "Step 06 REV BAM" "$tmp_rev_bam" "$output_rev_bam" || rollback_ok=false
        remove_owned_published_file \
            "Step 06 REV BAI" "$tmp_rev_bai" "$output_rev_bai" || rollback_ok=false
        remove_owned_published_file \
            "Step 06 counts" "$tmp_counts_tsv" "$output_counts_tsv" || rollback_ok=false
        if [[ "$rollback_ok" == true ]]; then
            return 0
        fi
        return 1
    fi

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
    local rollback_ok=true

    set +e

    # Rollback must run before temp cleanup so backup files remain available.
    if [[ "$status" -ne 0 ]]; then
        rollback_publish || rollback_ok=false
    fi

    if [[ "$rollback_ok" == true ]]; then
        rm -f "$tmp_99_bam" "$tmp_147_bam" "$tmp_83_bam" "$tmp_163_bam"
        rm -f "$tmp_fwd_bam" "$tmp_fwd_bai" "$tmp_rev_bam" "$tmp_rev_bai"
        rm -f "$tmp_counts_tsv"

        if [[ "$status" -eq 0 || "$backup_started" == true ]]; then
            rm -f "$backup_fwd_bam" "$backup_fwd_bai"
            rm -f "$backup_rev_bam" "$backup_rev_bai"
            rm -f "$backup_counts_tsv"
        fi

        remove_owned_lock
    else
        printf 'ERROR: Step 06 no-clobber rollback was incomplete; retaining owned lock and residue: %s\n' \
            "$lock_path" >&2
    fi
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

validate_orientation_outputs() {
    local fwd_bam="$1"
    local fwd_bai="$2"
    local rev_bam="$3"
    local rev_bai="$4"
    local counts_tsv="$5"
    local label="$6"

    # quickcheck catches corrupt BAMs before downstream mpileup consumes the
    # orientation split. BAIs and TSVs are checked for nonempty publication.
    [[ -s "$fwd_bam" ]] || die "$label FWD_like BAM is missing or empty: $fwd_bam"
    "$samtools_bin" quickcheck "$fwd_bam" || die "$label FWD_like BAM failed samtools quickcheck: $fwd_bam"
    [[ -s "$fwd_bai" ]] || die "$label FWD_like BAI is missing or empty: $fwd_bai"

    [[ -s "$rev_bam" ]] || die "$label REV_like BAM is missing or empty: $rev_bam"
    "$samtools_bin" quickcheck "$rev_bam" || die "$label REV_like BAM failed samtools quickcheck: $rev_bam"
    [[ -s "$rev_bai" ]] || die "$label REV_like BAI is missing or empty: $rev_bai"

    [[ -s "$counts_tsv" ]] || die "$label orientation counts TSV is missing or empty: $counts_tsv"
}

write_counts_tsv() {
    local input_records
    local flag_99_records
    local flag_147_records
    local flag_83_records
    local flag_163_records
    local fwd_like_records
    local rev_like_records
    local assigned_records
    local unassigned_records
    local assigned_fraction

    # Count each filtered and merged temporary BAM so the QC row reflects the
    # exact records produced for publication and downstream use.
    input_records="$("${input_count_command[@]}")"
    flag_99_records="$("${flag_99_count_command[@]}")"
    flag_147_records="$("${flag_147_count_command[@]}")"
    flag_83_records="$("${flag_83_count_command[@]}")"
    flag_163_records="$("${flag_163_count_command[@]}")"
    fwd_like_records="$("${fwd_count_command[@]}")"
    rev_like_records="$("${rev_count_command[@]}")"

    validate_nonnegative_integer "input_records" "$input_records"
    validate_nonnegative_integer "flag_99_records" "$flag_99_records"
    validate_nonnegative_integer "flag_147_records" "$flag_147_records"
    validate_nonnegative_integer "flag_83_records" "$flag_83_records"
    validate_nonnegative_integer "flag_163_records" "$flag_163_records"
    validate_nonnegative_integer "fwd_like_records" "$fwd_like_records"
    validate_nonnegative_integer "rev_like_records" "$rev_like_records"

    [[ "$input_records" -gt 0 ]] || die "input_records is zero; refusing to publish empty Step 06 outputs"
    [[ "$fwd_like_records" -gt 0 ]] || die "fwd_like_records is zero; refusing to publish empty FWD_like output"
    [[ "$rev_like_records" -gt 0 ]] || die "rev_like_records is zero; refusing to publish empty REV_like output"

    assigned_records=$((fwd_like_records + rev_like_records))
    if (( assigned_records > input_records )); then
        die "assigned_records exceeds input_records: $assigned_records > $input_records"
    fi

    unassigned_records=$((input_records - assigned_records))
    # Use awk for portable floating point formatting; POSIX shell arithmetic is
    # integer-only and would silently truncate this QC fraction.
    assigned_fraction="$(awk -v assigned="$assigned_records" -v input="$input_records" 'BEGIN { printf "%.6f", assigned / input }')"

    {
        printf 'sample_id\tinput_records\tflag_99_records\tflag_147_records\tflag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\tassigned_records\tunassigned_records\tassigned_fraction\n'
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$sample_id" \
            "$input_records" \
            "$flag_99_records" \
            "$flag_147_records" \
            "$flag_83_records" \
            "$flag_163_records" \
            "$fwd_like_records" \
            "$rev_like_records" \
            "$assigned_records" \
            "$unassigned_records" \
            "$assigned_fraction"
    } > "$tmp_counts_tsv"
}

validate_nonempty_file "Input BAM" "$input_bam"
validate_nonempty_file "Input BAI" "$input_bai"
input_bam_sha256="not-bound"
input_bai_sha256="not-bound"
if [[ "$no_clobber" == true ]]; then
    validate_safe_id "--sample-id" "$sample_id"
    input_bam_sha256="$(sha256_file "$input_bam")"
    input_bai_sha256="$(sha256_file "$input_bai")"
fi

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'samtools read-orientation split context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input BAM: %s\n' "$input_bam"
printf '  Input BAI: %s\n' "$input_bai"
printf '  Input BAM SHA-256: %s\n' "$input_bam_sha256"
printf '  Input BAI SHA-256: %s\n' "$input_bai_sha256"
printf '  Output directory: %s\n' "$output_dir"
printf '  QC directory: %s\n' "$qc_dir"
printf '  FWD_like BAM: %s\n' "$output_fwd_bam"
printf '  FWD_like BAI: %s\n' "$output_fwd_bai"
printf '  REV_like BAM: %s\n' "$output_rev_bam"
printf '  REV_like BAI: %s\n' "$output_rev_bai"
printf '  Counts TSV: %s\n' "$output_counts_tsv"
printf '  Threads: %s\n' "$threads"
printf '  samtools bin: %s\n' "$samtools_bin"
printf '  Run token: %s\n' "$run_token"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Lock owner file: %s\n' "$lock_owner_file"
printf '  Temporary 99 BAM: %s\n' "$tmp_99_bam"
printf '  Temporary 147 BAM: %s\n' "$tmp_147_bam"
printf '  Temporary 83 BAM: %s\n' "$tmp_83_bam"
printf '  Temporary 163 BAM: %s\n' "$tmp_163_bam"
printf '  Temporary FWD_like BAM: %s\n' "$tmp_fwd_bam"
printf '  Temporary FWD_like BAI: %s\n' "$tmp_fwd_bai"
printf '  Temporary REV_like BAM: %s\n' "$tmp_rev_bam"
printf '  Temporary REV_like BAI: %s\n' "$tmp_rev_bai"
printf '  Temporary counts TSV: %s\n' "$tmp_counts_tsv"
printf '  Backup FWD_like BAM: %s\n' "$backup_fwd_bam"
printf '  Backup FWD_like BAI: %s\n' "$backup_fwd_bai"
printf '  Backup REV_like BAM: %s\n' "$backup_rev_bam"
printf '  Backup REV_like BAI: %s\n' "$backup_rev_bai"
printf '  Backup counts TSV: %s\n' "$backup_counts_tsv"
printf '  No-clobber transaction: %s\n' "$no_clobber"
printf '  Mode: %s\n' "$mode"

printf 'Read-orientation grouping note:\n'
printf '  FWD_like uses samtools view -f 99 plus -f 147.\n'
printf '  REV_like uses samtools view -f 83 plus -f 163.\n'
printf '  These are mechanical read-orientation groups, not biological strand labels.\n'

printf 'Lock acquisition action:\n'
printf 'mkdir %q\n' "$lock_path"
printf 'Lock owner write action:\n'
printf 'printf %q %q %q\n' '%s\n' "run_token=$run_token" "$lock_owner_file"

printf 'samtools view -f 99 command:\n'
print_command "${view_99_command[@]}"
printf 'samtools view -f 147 command:\n'
print_command "${view_147_command[@]}"
printf 'samtools view -f 83 command:\n'
print_command "${view_83_command[@]}"
printf 'samtools view -f 163 command:\n'
print_command "${view_163_command[@]}"
printf 'samtools merge FWD_like command:\n'
print_command "${merge_fwd_command[@]}"
printf 'samtools merge REV_like command:\n'
print_command "${merge_rev_command[@]}"
printf 'samtools index FWD_like command:\n'
print_command "${index_fwd_command[@]}"
printf 'samtools index REV_like command:\n'
print_command "${index_rev_command[@]}"

printf 'Counts commands:\n'
print_command "${input_count_command[@]}"
print_command "${flag_99_count_command[@]}"
print_command "${flag_147_count_command[@]}"
print_command "${flag_83_count_command[@]}"
print_command "${flag_163_count_command[@]}"
print_command "${fwd_count_command[@]}"
print_command "${rev_count_command[@]}"

printf 'Validation plan:\n'
printf '  1. Verify Step 05 input BAM and BAI exist and are nonempty.\n'
printf '  2. Resolve samtools without invoking heavy computation.\n'
printf '  3. Refuse stale run-token temp and backup paths in execute mode.\n'
printf '  4. Write flag-filtered and merged outputs to run-token temp BAMs.\n'
printf '  5. Generate counts TSV with samtools view -c and awk-formatted assigned_fraction.\n'
printf '  6. Fail if input_records is zero, assigned_records exceeds input_records, or either merged group is empty.\n'
printf '  7. Validate temporary FWD_like and REV_like BAMs with samtools quickcheck and nonempty BAIs.\n'
printf '  8. Publish final outputs only after validation succeeds.\n'
printf '  9. Roll back previous final outputs if publication fails after backups begin.\n'

printf 'Publish plan:\n'
printf '  1. Confirm final outputs are all present or all absent.\n'
printf '  2. Back up any existing complete final output set.\n'
printf '  3. Move temp BAM/BAI/TSV outputs to final paths.\n'
printf '  4. Revalidate final outputs at their published paths.\n'
printf '  5. Remove backups and owned lock after successful final validation.\n'

printf 'Rollback plan:\n'
printf '  Restore backups before cleanup on failures after backup begins; remove new final files if no prior final set existed.\n'

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Step 06" "$output_dir" ".${sample_id}.step06.*"
    require_no_owner_residue \
        "Step 06" "$qc_dir" ".${sample_id}.step06.*"
fi

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run samtools and publish Step 06 outputs.\n'
    exit 0
fi

mkdir -p "$output_dir" "$qc_dir"

# Refuse stale paths before installing the EXIT trap. These files predate this
# invocation, so cleanup must not delete them as owned scratch.
refuse_stale_paths

on_exit() {
    local status=$?

    trap - EXIT HUP INT TERM
    cleanup "$status"
    exit "$status"
}

trap on_exit EXIT HUP INT TERM

acquire_lock "Step 06"
if [[ "$no_clobber" == true ]]; then
    confirm_final_set_state
fi

printf 'samtools version:\n'
"$samtools_bin" --version

"${view_99_command[@]}"
"${view_147_command[@]}"
"${view_83_command[@]}"
"${view_163_command[@]}"
"${merge_fwd_command[@]}"
"${merge_rev_command[@]}"
"${index_fwd_command[@]}"
"${index_rev_command[@]}"
write_counts_tsv

# Validate every replacement artifact before touching stable final paths.
validate_orientation_outputs \
    "$tmp_fwd_bam" \
    "$tmp_fwd_bai" \
    "$tmp_rev_bam" \
    "$tmp_rev_bai" \
    "$tmp_counts_tsv" \
    "Replacement"

if [[ "$no_clobber" == true ]]; then
    [[ "$(sha256_file "$input_bam")" == "$input_bam_sha256" ]] || die "Input BAM changed during Step 06."
    [[ "$(sha256_file "$input_bai")" == "$input_bai_sha256" ]] || die "Input BAI changed during Step 06."
fi

confirm_final_set_state

# Backups begin the rollback-protected region. From here until final validation,
# cleanup restores the previous complete set or removes partial new finals.
if [[ "$previous_final_set_present" == true ]]; then
    backup_started=true
    mv "$output_fwd_bam" "$backup_fwd_bam"
    fwd_bam_backed_up=true
    mv "$output_fwd_bai" "$backup_fwd_bai"
    fwd_bai_backed_up=true
    mv "$output_rev_bam" "$backup_rev_bam"
    rev_bam_backed_up=true
    mv "$output_rev_bai" "$backup_rev_bai"
    rev_bai_backed_up=true
    mv "$output_counts_tsv" "$backup_counts_tsv"
    counts_tsv_backed_up=true
else
    backup_started=true
fi

if [[ "$no_clobber" == true ]]; then
    publish_file_create_exclusive \
        "Step 06 FWD BAM" "$tmp_fwd_bam" "$output_fwd_bam"
    publish_file_create_exclusive \
        "Step 06 FWD BAI" "$tmp_fwd_bai" "$output_fwd_bai"
    publish_file_create_exclusive \
        "Step 06 REV BAM" "$tmp_rev_bam" "$output_rev_bam"
    publish_file_create_exclusive \
        "Step 06 REV BAI" "$tmp_rev_bai" "$output_rev_bai"
    publish_file_create_exclusive \
        "Step 06 counts" "$tmp_counts_tsv" "$output_counts_tsv"
else
    mv "$tmp_fwd_bam" "$output_fwd_bam"
    mv "$tmp_fwd_bai" "$output_fwd_bai"
    mv "$tmp_rev_bam" "$output_rev_bam"
    mv "$tmp_rev_bai" "$output_rev_bai"
    mv "$tmp_counts_tsv" "$output_counts_tsv"
fi

# Revalidate at final paths so downstream steps consume only a complete,
# readable BAM/BAI/TSV set.
validate_orientation_outputs \
    "$output_fwd_bam" \
    "$output_fwd_bai" \
    "$output_rev_bam" \
    "$output_rev_bai" \
    "$output_counts_tsv" \
    "Published"

if [[ "$no_clobber" == true ]]; then
    require_owned_published_file \
        "Step 06 FWD BAM" "$tmp_fwd_bam" "$output_fwd_bam"
    require_owned_published_file \
        "Step 06 FWD BAI" "$tmp_fwd_bai" "$output_fwd_bai"
    require_owned_published_file \
        "Step 06 REV BAM" "$tmp_rev_bam" "$output_rev_bam"
    require_owned_published_file \
        "Step 06 REV BAI" "$tmp_rev_bai" "$output_rev_bai"
    require_owned_published_file \
        "Step 06 counts" "$tmp_counts_tsv" "$output_counts_tsv"
    rm -f -- \
        "$tmp_fwd_bam" "$tmp_fwd_bai" "$tmp_rev_bam" "$tmp_rev_bai" \
        "$tmp_counts_tsv"
    [[ ! -e "$tmp_fwd_bam" && ! -L "$tmp_fwd_bam" &&
       ! -e "$tmp_fwd_bai" && ! -L "$tmp_fwd_bai" &&
       ! -e "$tmp_rev_bam" && ! -L "$tmp_rev_bam" &&
       ! -e "$tmp_rev_bai" && ! -L "$tmp_rev_bai" &&
       ! -e "$tmp_counts_tsv" && ! -L "$tmp_counts_tsv" ]] ||
        die "Step 06 could not remove owned publication anchors."
fi

final_publish_complete=true

rm -f "$backup_fwd_bam" "$backup_fwd_bai"
rm -f "$backup_rev_bam" "$backup_rev_bai"
rm -f "$backup_counts_tsv"
remove_owned_lock

printf 'Step 06 read-orientation output details:\n'
ls -lh "$output_fwd_bam" "$output_fwd_bai" "$output_rev_bam" "$output_rev_bai" "$output_counts_tsv"
