#!/usr/bin/env bash
# Step 02: create one canonical coordinate-sorted, read-group-tagged BAM.
#
# Dry-run mode validates inputs and prints the exact samtools, validation,
# locking, and publish actions without creating directories or files. Passing
# --execute runs the workflow and publishes the canonical BAM/BAI only after
# replacement files pass validation.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/canonical_bam/step_02_sort_index_bam.sh \
    --sample-id SAMPLE_ID \
    --input-alignment INPUT_ALIGNMENT \
    --output-dir OUTPUT_DIR \
    --threads THREADS \
    [--execute]

Sort, read-group tag, validate, index, and publish one canonical BAM.

By default this script runs in dry-run mode: it validates inputs and prints the
samtools commands and publish plan without executing them. Add --execute to run
samtools and publish outputs after validation.

Required arguments:
  --sample-id         Sample identifier used in output filenames and RG fields.
  --input-alignment  Input SAM or BAM alignment file to sort.
  --output-dir       Directory where canonical BAM and BAI outputs are written.
  --threads          Number of threads for samtools; must be a positive integer.

Options:
  --execute          Execute samtools after validation. Without this, dry-run only.
  -h, --help         Show this help message and exit.
USAGE
}

# shellcheck source=../../libraries/argument_parsing.sh
script_dir="${BASH_SOURCE[0]%/*}"
if [[ "$script_dir" == "$BASH_SOURCE[0]" ]]; then
    script_dir="."
fi
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$script_dir/../../libraries/signal_traps.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$script_dir/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"

# Defaults are empty so missing required arguments fail loudly below.
declare_required_arguments sample_id input_alignment output_dir threads
execute=false

# Keep the CLI explicit so the same script works locally and under SLURM.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-alignment) assign_option_value "$1" "${2:-}" input_alignment; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

[[ -f "$input_alignment" ]] || die "Input alignment does not exist or is not a file: $input_alignment"

samtools_bin="$(resolve_executable_value "samtools" "" "samtools")"

validate_positive_integer "--threads" "$threads"

run_token="${SLURM_JOB_ID:-$$}"

# Canonical output names are stable by design; downstream steps depend on them.
output_bam="$output_dir/${sample_id}.sorted.bam"
output_bai="$output_bam.bai"

# The per-sample lock prevents two jobs from publishing the same canonical pair.
lock_path="$output_dir/.${sample_id}.step02.lock"
lock_owner_file="$lock_path/owner"

# Temporary and backup paths include the current run token to avoid collisions.
tmp_sorted_bam="$output_dir/.${sample_id}.step02.${run_token}.sorted.tmp.bam"
tmp_rg_bam="$output_dir/.${sample_id}.step02.${run_token}.rg.tmp.bam"
tmp_rg_bai="$tmp_rg_bam.bai"

backup_bam="$output_dir/.${sample_id}.step02.${run_token}.previous.bam"
backup_bai="$output_dir/.${sample_id}.step02.${run_token}.previous.bam.bai"

# Track publish state explicitly so cleanup can rollback before deleting backups.
lock_acquired=false
previous_pair_present=false
backup_started=false
bam_backed_up=false
bai_backed_up=false
published_bam=false
published_bai=false
final_publish_complete=false

# Build tool commands as arrays to preserve argument boundaries in dry-run logs.
sort_command=(
    "$samtools_bin"
    sort
    -@ "$threads"
    -o "$tmp_sorted_bam"
    "$input_alignment"
)

addreplacerg_command=(
    "$samtools_bin"
    addreplacerg
    -@ "$threads"
    -m overwrite_all
    -w
    -r "ID:$sample_id"
    -r "SM:$sample_id"
    -r "LB:$sample_id"
    -r "PL:ILLUMINA"
    -o "$tmp_rg_bam"
    "$tmp_sorted_bam"
)

# These validation commands are printed in dry-run mode and mirrored by
# validate_bam_pair during execution.
quickcheck_command=(
    "$samtools_bin"
    quickcheck
    "$tmp_rg_bam"
)

header_command=(
    "$samtools_bin"
    view
    -H
    "$tmp_rg_bam"
)

count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_rg_bam"
)

tagged_count_command=(
    "$samtools_bin"
    view
    -c
    -d "RG:$sample_id"
    "$tmp_rg_bam"
)

index_command=(
    "$samtools_bin"
    index
    "$tmp_rg_bam"
)

validate_bam_pair() {
    local bam="$1"
    local bai="$2"
    local label="$3"
    local header
    local rg_lines
    local rg_count
    local rg_line
    local total_records
    local tagged_records

    # Validate both metadata and record-level RG tags before any publish step.
    [[ -s "$bam" ]] || die "$label BAM is missing or empty: $bam"
    "$samtools_bin" quickcheck "$bam" || die "$label BAM failed samtools quickcheck: $bam"

    header="$("$samtools_bin" view -H "$bam")"
    rg_lines="$(printf '%s\n' "$header" | grep '^@RG' || true)"
    rg_count="$(printf '%s\n' "$rg_lines" | sed '/^$/d' | wc -l | tr -d ' ')"
    [[ "$rg_count" == "1" ]] || die "$label BAM must contain exactly one @RG line; found: $rg_count"

    rg_line="$rg_lines"
    [[ "$rg_line" == *"ID:$sample_id"* ]] || die "$label @RG line is missing ID:$sample_id"
    [[ "$rg_line" == *"SM:$sample_id"* ]] || die "$label @RG line is missing SM:$sample_id"
    [[ "$rg_line" == *"LB:$sample_id"* ]] || die "$label @RG line is missing LB:$sample_id"
    [[ "$rg_line" == *"PL:ILLUMINA"* ]] || die "$label @RG line is missing PL:ILLUMINA"
    printf '%s\n' "$header" | grep -q '^@HD.*SO:coordinate' || die "$label BAM header is not coordinate sorted"

    total_records="$("$samtools_bin" view -c "$bam")"
    [[ "$total_records" =~ ^[0-9]+$ ]] || die "$label total alignment count is not numeric: $total_records"
    [[ "$total_records" -gt 0 ]] || die "$label BAM contains no alignment records"

    tagged_records="$("$samtools_bin" view -c -d "RG:$sample_id" "$bam")"
    [[ "$tagged_records" =~ ^[0-9]+$ ]] || die "$label tagged alignment count is not numeric: $tagged_records"
    [[ "$tagged_records" -eq "$total_records" ]] || die "$label BAM has $tagged_records of $total_records records tagged RG:$sample_id"

    [[ -s "$bai" ]] || die "$label BAI is missing or empty: $bai"
}

confirm_canonical_pair_state() {
    # A single existing file is unsafe: there would be no complete rollback target.
    if [[ -e "$output_bam" && -e "$output_bai" ]]; then
        previous_pair_present=true
    elif [[ ! -e "$output_bam" && ! -e "$output_bai" ]]; then
        previous_pair_present=false
    else
        die "Canonical outputs are inconsistent; expected both BAM and BAI or neither: $output_bam $output_bai"
    fi
}

rollback_publish() {
    if [[ "$backup_started" != true || "$final_publish_complete" == true ]]; then
        return
    fi

    printf 'Rolling back Step 02 canonical outputs...\n' >&2

    if [[ "$previous_pair_present" == true ]]; then
        # Restore only the files that were actually moved to backup.
        if [[ "$bam_backed_up" == true && -e "$backup_bam" ]]; then
            rm -f "$output_bam"
            mv "$backup_bam" "$output_bam" || true
            bam_backed_up=false
        fi

        if [[ "$bai_backed_up" == true && -e "$backup_bai" ]]; then
            rm -f "$output_bai"
            mv "$backup_bai" "$output_bai" || true
            bai_backed_up=false
        fi
    else
        # With no prior pair, rollback means no canonical files should remain.
        rm -f "$output_bam" "$output_bai"
    fi
}

cleanup() {
    local status="$1"

    # Cleanup should be best-effort and must not mask the original failure.
    set +e

    # Rollback must run before backup cleanup so prior canonical files are usable.
    if [[ "$status" -ne 0 ]]; then
        rollback_publish
    fi

    rm -f "$tmp_sorted_bam" "$tmp_rg_bam" "$tmp_rg_bai"
    rm -f "$tmp_sorted_bam.bai" "$tmp_rg_bam.bai"

    if [[ "$status" -eq 0 || "$backup_started" == true ]]; then
        rm -f "$backup_bam" "$backup_bai"
    fi

    remove_owned_lock
}

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'samtools canonical BAM context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input alignment: %s\n' "$input_alignment"
printf '  Output directory: %s\n' "$output_dir"
printf '  Output BAM: %s\n' "$output_bam"
printf '  Output BAI: %s\n' "$output_bai"
printf '  Threads: %s\n' "$threads"
printf '  Run token: %s\n' "$run_token"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Lock owner file: %s\n' "$lock_owner_file"
printf '  Temporary sorted BAM: %s\n' "$tmp_sorted_bam"
printf '  Temporary read-group BAM: %s\n' "$tmp_rg_bam"
printf '  Temporary read-group BAI: %s\n' "$tmp_rg_bai"
printf '  Backup BAM: %s\n' "$backup_bam"
printf '  Backup BAI: %s\n' "$backup_bai"
printf '  Read group: ID=%s SM=%s LB=%s PL=ILLUMINA\n' "$sample_id" "$sample_id" "$sample_id"
printf '  Mode: %s\n' "$mode"

printf 'Lock acquisition action:\n'
printf 'mkdir %q\n' "$lock_path"
printf 'Lock owner write action:\n'
printf 'printf %q %q %q\n' '%s\n' "run_token=$run_token" "$lock_owner_file"

printf 'samtools sort command:\n'
print_command "${sort_command[@]}"

printf 'samtools addreplacerg command:\n'
print_command "${addreplacerg_command[@]}"

printf 'samtools quickcheck validation command:\n'
print_command "${quickcheck_command[@]}"

printf 'samtools header validation command:\n'
print_command "${header_command[@]}"

printf 'samtools total-record validation command:\n'
print_command "${count_command[@]}"

printf 'samtools read-group-tag validation command:\n'
print_command "${tagged_count_command[@]}"

printf 'samtools index command:\n'
print_command "${index_command[@]}"

printf 'Publish plan:\n'
printf '  1. Validate replacement BAM and BAI: %s %s\n' "$tmp_rg_bam" "$tmp_rg_bai"
printf '  2. Confirm canonical outputs are a complete pair or both absent.\n'
printf '  3. Back up existing pair to: %s %s\n' "$backup_bam" "$backup_bai"
printf '  4. Move replacement BAM to: %s\n' "$output_bam"
printf '  5. Move replacement BAI to: %s\n' "$output_bai"
printf '  6. Revalidate published canonical BAM and BAI.\n'
printf '  7. Remove backups and owned lock after successful final validation.\n'
printf 'Rollback plan:\n'
printf '  Restore backups before cleanup on failures after backup begins; remove new canonical files if no prior pair existed.\n'

if [[ "$execute" != true ]]; then
    # Dry-runs are intentionally side-effect-free: no output directory or lock.
    printf 'Dry-run only. Add --execute to run samtools and publish canonical outputs.\n'
    exit 0
fi

mkdir -p "$output_dir"

set_exit_trap cleanup
acquire_lock "Step 02"

# Build and validate the replacement completely before touching canonical paths.
"${sort_command[@]}"
"${addreplacerg_command[@]}"
[[ -s "$tmp_rg_bam" ]] || die "Temporary read-group BAM is missing or empty: $tmp_rg_bam"
"${index_command[@]}"
validate_bam_pair "$tmp_rg_bam" "$tmp_rg_bai" "Replacement"

confirm_canonical_pair_state

# Backups begin the rollback-protected region.
if [[ "$previous_pair_present" == true ]]; then
    backup_started=true
    mv "$output_bam" "$backup_bam"
    bam_backed_up=true
    mv "$output_bai" "$backup_bai"
    bai_backed_up=true
else
    backup_started=true
fi

mv "$tmp_rg_bam" "$output_bam"
published_bam=true
mv "$tmp_rg_bai" "$output_bai"
published_bai=true

# Revalidate after publish so a copied/moved pair is known-good at final paths.
validate_bam_pair "$output_bam" "$output_bai" "Canonical"
final_publish_complete=true

rm -f "$backup_bam" "$backup_bai"
bam_backed_up=false
bai_backed_up=false

printf 'Canonical Step 02 output details:\n'
ls -lh "$output_bam" "$output_bai"
