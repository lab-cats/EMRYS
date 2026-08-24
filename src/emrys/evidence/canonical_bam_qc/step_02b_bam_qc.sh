#!/usr/bin/env bash
# Run basic integrity/QC checks on one canonical sorted BAM with samtools.
#
# The script validates the BAM and index, then prints the samtools commands in
# dry-run mode by default. Passing --execute runs the same commands.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
    --sample-id SAMPLE_ID \
    --bam BAM \
    --output-dir OUTPUT_DIR \
    [--samtools-bin SAMTOOLS_BIN] \
    [--no-clobber] \
    [--execute]

Run basic BAM integrity/QC checks on a canonical sorted BAM from Step 02.

By default this script runs in dry-run mode: it validates inputs and prints the
samtools commands without executing them. Add --execute to run samtools.

Required arguments:
  --sample-id    Sample identifier used in output filenames.
  --bam          Input sorted BAM file from Step 02.
  --output-dir   Directory where BAM QC outputs will be written.

Options:
  --samtools-bin  samtools executable or path. Defaults to samtools on PATH.
  --no-clobber    Require absent final outputs and publish a staged pair.
                  Required by orchestration.
  --execute      Execute samtools after validation. Without this, dry-run only.
  -h, --help     Show this help message and exit.
USAGE
}

# shellcheck source=../../libraries/argument_parsing.sh
script_dir="${BASH_SOURCE[0]%/*}"
if [[ "$script_dir" == "$BASH_SOURCE[0]" ]]; then
    script_dir="."
fi
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$script_dir/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$script_dir/../../libraries/signal_traps.sh"

declare_required_arguments sample_id bam output_dir
execute=false
no_clobber=false
requested_samtools_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --bam) assign_option_value "$1" "${2:-}" bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" requested_samtools_bin; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

[[ -f "$bam" ]] || die "BAM does not exist or is not a file: $bam"

if [[ -f "$bam.bai" ]]; then
    bam_index="$bam.bai"
elif [[ -f "${bam%.bam}.bai" ]]; then
    bam_index="${bam%.bam}.bai"
else
    die "BAM index does not exist. Expected either: $bam.bai or ${bam%.bam}.bai"
fi

samtools_bin="$(resolve_executable_value "samtools" "$requested_samtools_bin" "samtools")"
bam_sha256="not-bound"
bam_index_sha256="not-bound"
if [[ "$no_clobber" == true ]]; then
    validate_safe_id "--sample-id" "$sample_id"
    bam_sha256="$(sha256_file "$bam")"
    bam_index_sha256="$(sha256_file "$bam_index")"
fi

QUICKCHECK_OUT="$output_dir/${sample_id}.quickcheck.txt"
FLAGSTAT_OUT="$output_dir/${sample_id}.flagstat.txt"
run_token="${EMRYS_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "Step 02b run token" "$run_token"
lock_path="$output_dir/.${sample_id}.step02b.lock"
lock_owner_file="$lock_path/owner"
tmp_quickcheck="$output_dir/.${sample_id}.step02b.${run_token}.quickcheck.tmp"
tmp_flagstat="$output_dir/.${sample_id}.step02b.${run_token}.flagstat.tmp"
lock_acquired=false
publication_started=false
quickcheck_published=false
flagstat_published=false

require_absent_outputs() {
    [[ ! -e "$QUICKCHECK_OUT" && ! -e "$FLAGSTAT_OUT" ]] ||
        die "Step 02b --no-clobber requires both final outputs to be absent: $QUICKCHECK_OUT $FLAGSTAT_OUT"
}

cleanup_no_clobber() {
    local status="$1"
    local rollback_failed=false

    set +e
    if [[ "$status" -ne 0 && "$publication_started" == true ]]; then
        if [[ "$quickcheck_published" == true ]]; then
            if ! remove_owned_published_file \
                "Step 02b quickcheck" "$tmp_quickcheck" "$QUICKCHECK_OUT"; then
                rollback_failed=true
            fi
        fi
        if [[ "$flagstat_published" == true ]]; then
            if ! remove_owned_published_file \
                "Step 02b flagstat" "$tmp_flagstat" "$FLAGSTAT_OUT"; then
                rollback_failed=true
            fi
        fi
    fi

    if [[ "$rollback_failed" != true ]]; then
        if [[ -e "$tmp_quickcheck" || -L "$tmp_quickcheck" ]]; then
            if ! rm -f -- "$tmp_quickcheck" ||
               [[ -e "$tmp_quickcheck" || -L "$tmp_quickcheck" ]]; then
                printf 'ERROR: Could not remove Step 02b quickcheck staging output: %s\n' \
                    "$tmp_quickcheck" >&2
                rollback_failed=true
            fi
        fi
        if [[ -e "$tmp_flagstat" || -L "$tmp_flagstat" ]]; then
            if ! rm -f -- "$tmp_flagstat" ||
               [[ -e "$tmp_flagstat" || -L "$tmp_flagstat" ]]; then
                printf 'ERROR: Could not remove Step 02b flagstat staging output: %s\n' \
                    "$tmp_flagstat" >&2
                rollback_failed=true
            fi
        fi
    fi

    if [[ "$rollback_failed" != true && "$lock_acquired" == true ]]; then
        remove_owned_lock
        if [[ -e "$lock_path" || -L "$lock_path" ]]; then
            printf 'ERROR: Could not remove the owned Step 02b lock during cleanup: %s\n' \
                "$lock_path" >&2
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" == true ]]; then
        printf 'ERROR: Step 02b no-clobber cleanup was incomplete; retaining the owned lock and recovery residue: %s\n' \
            "$lock_path" >&2
    fi
}

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'BAM QC context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  BAM: %s\n' "$bam"
printf '  BAM index found: %s\n' "$bam_index"
printf '  BAM SHA-256: %s\n' "$bam_sha256"
printf '  BAM index SHA-256: %s\n' "$bam_index_sha256"
printf '  samtools bin: %s\n' "$samtools_bin"
printf '  Output directory: %s\n' "$output_dir"
printf '  Quickcheck output: %s\n' "$QUICKCHECK_OUT"
printf '  Flagstat output: %s\n' "$FLAGSTAT_OUT"
printf '  No-clobber transaction: %s\n' "$no_clobber"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Run token: %s\n' "$run_token"
printf '  Temporary quickcheck: %s\n' "$tmp_quickcheck"
printf '  Temporary flagstat: %s\n' "$tmp_flagstat"
printf '  Mode: %s\n' "$mode"

quickcheck_command=(
    "$samtools_bin"
    quickcheck
    -v
    "$bam"
)

flagstat_command=(
    "$samtools_bin"
    flagstat
    "$bam"
)

printf 'samtools quickcheck command:\n'
print_command "${quickcheck_command[@]}"

printf 'samtools flagstat command:\n'
print_command "${flagstat_command[@]}"

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Step 02b" "$output_dir" ".${sample_id}.step02b.*"
fi

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run samtools.\n'
    exit 0
fi

mkdir -p "$output_dir"

quickcheck_target="$QUICKCHECK_OUT"
flagstat_target="$FLAGSTAT_OUT"
if [[ "$no_clobber" == true ]]; then
    require_absent_outputs
    [[ ! -e "$tmp_quickcheck" && ! -e "$tmp_flagstat" ]] ||
        die "Step 02b temporary output already exists: $tmp_quickcheck $tmp_flagstat"
    set_exit_trap cleanup_no_clobber
    acquire_lock "Step 02b"
    quickcheck_target="$tmp_quickcheck"
    flagstat_target="$tmp_flagstat"
fi

if ! "${quickcheck_command[@]}" >"$quickcheck_target" 2>&1; then
    printf 'ERROR: samtools quickcheck failed. Output preserved at: %s\n' "$quickcheck_target" >&2
    exit 1
fi

if [[ ! -s "$quickcheck_target" ]]; then
    printf 'PASS: samtools quickcheck completed with no errors.\n' >"$quickcheck_target"
fi

"${flagstat_command[@]}" >"$flagstat_target"
[[ -s "$quickcheck_target" ]] || die "Step 02b quickcheck evidence is missing or empty: $quickcheck_target"
[[ -s "$flagstat_target" ]] || die "Step 02b flagstat evidence is missing or empty: $flagstat_target"

if [[ "$no_clobber" == true ]]; then
    [[ "$(sha256_file "$bam")" == "$bam_sha256" ]] || die "BAM changed during Step 02b."
    [[ "$(sha256_file "$bam_index")" == "$bam_index_sha256" ]] || die "BAM index changed during Step 02b."
    require_absent_outputs
    publication_started=true
    publish_file_create_exclusive \
        "Step 02b quickcheck" "$tmp_quickcheck" "$QUICKCHECK_OUT"
    quickcheck_published=true
    publish_file_create_exclusive \
        "Step 02b flagstat" "$tmp_flagstat" "$FLAGSTAT_OUT"
    flagstat_published=true
    require_owned_published_file \
        "Step 02b quickcheck" "$tmp_quickcheck" "$QUICKCHECK_OUT"
    require_owned_published_file \
        "Step 02b flagstat" "$tmp_flagstat" "$FLAGSTAT_OUT"
    rm -f -- "$tmp_quickcheck" "$tmp_flagstat"
    [[ ! -e "$tmp_quickcheck" && ! -L "$tmp_quickcheck" &&
       ! -e "$tmp_flagstat" && ! -L "$tmp_flagstat" ]] ||
        die "Step 02b could not remove owned publication anchors."
    publication_started=false
    remove_owned_lock
fi

printf 'BAM QC output details:\n'
ls -lh "$QUICKCHECK_OUT" "$FLAGSTAT_OUT"

printf 'samtools flagstat output:\n'
cat "$FLAGSTAT_OUT"
