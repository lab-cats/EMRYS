#!/usr/bin/env bash
# Step 06: split one SplitNCigarReads BAM into mechanical read-orientation groups.
#
# Dry-run mode validates inputs and prints resolved paths, exact samtools
# commands, locking, temp paths, validation checks, and publish actions without
# creating output directories, locks, temp files, BAMs, indexes, or TSVs.
# Passing --execute runs samtools, validates temporary outputs, and publishes
# final BAM/BAI/TSV outputs only after validation succeeds.
set -euo pipefail
script_dir="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
helper_dir="${STEP06_HELPER_DIR:-$script_dir}"

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

for step_06_helper in \
    step_06_transaction_helpers.sh \
    step_06_output_contract.sh
do
    # shellcheck source=/dev/null
    source "$helper_dir/$step_06_helper"
done

resolve_samtools() {
    local value="${samtools_bin_arg:-}"
    if [[ -z "$value" && -n "${SAMTOOLS_BIN_OVERRIDE:-}" ]]; then
        value="$SAMTOOLS_BIN_OVERRIDE"
    fi
    resolve_executable_value "samtools" "$value" "samtools"
}

declare_required_arguments sample_id input_bam output_dir qc_dir threads
samtools_bin_arg=""
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --qc-dir) assign_option_value "$1" "${2:-}" qc_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin_arg; shift 2 ;;
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
