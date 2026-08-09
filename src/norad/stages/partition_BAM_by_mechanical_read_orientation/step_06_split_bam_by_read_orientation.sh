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
  src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --output-dir OUTPUT_DIR \
    --qc-dir QC_DIR \
    --threads THREADS \
    [--samtools-bin SAMTOOLS_BIN] \
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

resolve_samtools() {
    local value="${samtools_bin_arg:-}"
    if [[ -z "$value" && -n "${SAMTOOLS_BIN_OVERRIDE:-}" ]]; then
        value="$SAMTOOLS_BIN_OVERRIDE"
    fi
    resolve_executable_value "samtools" "$value" "samtools"
}

sample_id=""
input_bam=""
output_dir=""
qc_dir=""
threads=""
samtools_bin_arg=""
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id)
            require_value "$1" "${2:-}"
            sample_id="$2"
            shift 2
            ;;
        --input-bam)
            require_value "$1" "${2:-}"
            input_bam="$2"
            shift 2
            ;;
        --output-dir)
            require_value "$1" "${2:-}"
            output_dir="$2"
            shift 2
            ;;
        --qc-dir)
            require_value "$1" "${2:-}"
            qc_dir="$2"
            shift 2
            ;;
        --threads)
            require_value "$1" "${2:-}"
            threads="$2"
            shift 2
            ;;
        --samtools-bin)
            require_value "$1" "${2:-}"
            samtools_bin_arg="$2"
            shift 2
            ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

[[ -n "$sample_id" ]] || die "Missing required argument: --sample-id."
[[ -n "$input_bam" ]] || die "Missing required argument: --input-bam."
[[ -n "$output_dir" ]] || die "Missing required argument: --output-dir."
[[ -n "$qc_dir" ]] || die "Missing required argument: --qc-dir."
[[ -n "$threads" ]] || die "Missing required argument: --threads."

validate_positive_integer "--threads" "$threads"

# Step 05 publishes indexes as <bam>.bai. Keep Step 06 strict so stale or
# incomplete upstream split-N-cigar outputs fail before any orientation work.
input_bai="$input_bam.bai"
samtools_bin="$(resolve_samtools)"
run_token="${SLURM_JOB_ID:-$$}"

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
    -f 99
    "$input_bam"
)

flag_147_count_command=(
    "$samtools_bin"
    view
    -c
    -f 147
    "$input_bam"
)

flag_83_count_command=(
    "$samtools_bin"
    view
    -c
    -f 83
    "$input_bam"
)

flag_163_count_command=(
    "$samtools_bin"
    view
    -c
    -f 163
    "$input_bam"
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

quickcheck_fwd_command=(
    "$samtools_bin"
    quickcheck
    "$tmp_fwd_bam"
)

quickcheck_rev_command=(
    "$samtools_bin"
    quickcheck
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

    # Counts come from samtools view -c rather than the filter temp files alone,
    # so the QC row reflects the BAM records that downstream tools will see.
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

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'samtools read-orientation split context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input BAM: %s\n' "$input_bam"
printf '  Input BAI: %s\n' "$input_bai"
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

mv "$tmp_fwd_bam" "$output_fwd_bam"
mv "$tmp_fwd_bai" "$output_fwd_bai"
mv "$tmp_rev_bam" "$output_rev_bam"
mv "$tmp_rev_bai" "$output_rev_bai"
mv "$tmp_counts_tsv" "$output_counts_tsv"

# Revalidate at final paths so downstream steps consume only a complete,
# readable BAM/BAI/TSV set.
validate_orientation_outputs \
    "$output_fwd_bam" \
    "$output_fwd_bai" \
    "$output_rev_bam" \
    "$output_rev_bai" \
    "$output_counts_tsv" \
    "Published"

final_publish_complete=true

rm -f "$backup_fwd_bam" "$backup_fwd_bai"
rm -f "$backup_rev_bam" "$backup_rev_bai"
rm -f "$backup_counts_tsv"
fwd_bam_backed_up=false
fwd_bai_backed_up=false
rev_bam_backed_up=false
rev_bai_backed_up=false
counts_tsv_backed_up=false

printf 'Step 06 read-orientation output details:\n'
ls -lh "$output_fwd_bam" "$output_fwd_bai" "$output_rev_bam" "$output_rev_bai" "$output_counts_tsv"
