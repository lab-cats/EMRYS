#!/usr/bin/env bash
# Step 04: mark PCR/optical duplicates on one canonical sorted BAM with Picard.
#
# Dry-run mode validates inputs and prints the exact Picard and samtools
# commands without creating output directories or final output files. Passing
# --execute runs Picard MarkDuplicates, validates the BAM with samtools
# quickcheck, indexes it, and checks the expected outputs.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/duplicate_marking/step_04_mark_duplicates.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --output-dir OUTPUT_DIR \
    --metrics-dir METRICS_DIR \
    --picard-jar PICARD_JAR \
    [--java-bin JAVA_BIN] \
    [--samtools-bin SAMTOOLS_BIN] \
    [--no-clobber] \
    [--execute]

Mark duplicates in one canonical sorted BAM with Picard MarkDuplicates.

By default this script runs in dry-run mode: it validates inputs and prints the
Picard and samtools commands without executing them. Add --execute to run the
commands and validate outputs.

Required arguments:
  --sample-id     Sample identifier used in output filenames.
  --input-bam     Input sorted BAM file from Step 02.
  --output-dir    Directory where duplicate-marked BAM and BAI are written.
  --metrics-dir   Directory where Picard MarkDuplicates metrics are written.
  --picard-jar    Path to the Picard jar, usually from the PICARD module var.

Options:
  --java-bin      Java executable or path. Defaults to java.
  --samtools-bin  samtools executable or path. Defaults to samtools.
  --no-clobber    Require an absent final output set and use staged publication.
                  Required by orchestration.
  --execute       Execute Picard and samtools after validation. Without this,
                  dry-run only.
  -h, --help      Show this help message and exit.
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

declare_required_arguments sample_id input_bam output_dir metrics_dir picard_jar
requested_java_bin=""
requested_samtools_bin=""
execute=false
no_clobber=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --metrics-dir) assign_option_value "$1" "${2:-}" metrics_dir; shift 2 ;;
        --picard-jar) assign_option_value "$1" "${2:-}" picard_jar; shift 2 ;;
        --java-bin) assign_option_value "$1" "${2:-}" requested_java_bin; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" requested_samtools_bin; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

# Step 02 writes the canonical index as sample.sorted.bam.bai. Keep Step 04
# strict here so a missing upstream index is caught before Picard starts.
input_bai="$input_bam.bai"
output_bam="$output_dir/${sample_id}.markdup.bam"
output_bai="$output_bam.bai"
metrics_file="$metrics_dir/${sample_id}.markdup.metrics.txt"

# Picard can spill temporary files during MarkDuplicates. Use the caller's
# TMPDIR when provided, but require it to already exist instead of silently
# creating an unexpected scratch location.
tmp_dir="${TMPDIR:-/tmp}"

[[ -f "$input_bam" ]] || die "Input BAM does not exist or is not a file: $input_bam"
[[ -f "$input_bai" ]] || die "Input BAM index does not exist or is not a file: $input_bai"
[[ -f "$picard_jar" ]] || die "Picard jar does not exist or is not a file: $picard_jar"
[[ -r "$picard_jar" ]] || die "Picard jar is not readable: $picard_jar"
java_bin="$(resolve_executable_value "Java" "$requested_java_bin" "java")"
samtools_bin="$(resolve_executable_value "samtools" "$requested_samtools_bin" "samtools")"
input_bam_sha256="not-bound"
input_bai_sha256="not-bound"
picard_jar_sha256="not-bound"
if [[ "$no_clobber" == true ]]; then
    validate_safe_id "--sample-id" "$sample_id"
    input_bam_sha256="$(sha256_file "$input_bam")"
    input_bai_sha256="$(sha256_file "$input_bai")"
    picard_jar_sha256="$(sha256_file "$picard_jar")"
fi

run_token="${NORAD_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "Step 04 run token" "$run_token"
tmp_bam="$output_dir/.${sample_id}.step04.${run_token}.markdup.tmp.bam"
tmp_bai="$tmp_bam.bai"
tmp_metrics="$metrics_dir/.${sample_id}.step04.${run_token}.metrics.tmp"
lock_path="$output_dir/.${sample_id}.step04.lock"
lock_owner_file="$lock_path/owner"
lock_acquired=false
publication_started=false
bam_published=false
bai_published=false
metrics_published=false

require_absent_outputs() {
    [[ ! -e "$output_bam" && ! -e "$output_bai" && ! -e "$metrics_file" ]] ||
        die "Step 04 --no-clobber requires all final outputs to be absent: $output_bam $output_bai $metrics_file"
}

cleanup_no_clobber() {
    local status="$1"
    local rollback_failed=false

    set +e
    if [[ "$status" -ne 0 && "$publication_started" == true ]]; then
        if [[ "$bam_published" == true ]]; then
            if ! remove_owned_published_file \
                "Step 04 BAM" "$tmp_bam" "$output_bam"; then
                rollback_failed=true
            fi
        fi
        if [[ "$bai_published" == true ]]; then
            if ! remove_owned_published_file \
                "Step 04 BAI" "$tmp_bai" "$output_bai"; then
                rollback_failed=true
            fi
        fi
        if [[ "$metrics_published" == true ]]; then
            if ! remove_owned_published_file \
                "Step 04 metrics" "$tmp_metrics" "$metrics_file"; then
                rollback_failed=true
            fi
        fi
    fi

    if [[ "$rollback_failed" != true ]]; then
        if [[ -e "$tmp_bam" || -L "$tmp_bam" ]]; then
            if ! rm -f -- "$tmp_bam" ||
               [[ -e "$tmp_bam" || -L "$tmp_bam" ]]; then
                printf 'ERROR: Could not remove Step 04 staged BAM during cleanup: %s\n' \
                    "$tmp_bam" >&2
                rollback_failed=true
            fi
        fi
        if [[ -e "$tmp_bai" || -L "$tmp_bai" ]]; then
            if ! rm -f -- "$tmp_bai" ||
               [[ -e "$tmp_bai" || -L "$tmp_bai" ]]; then
                printf 'ERROR: Could not remove Step 04 staged BAI during cleanup: %s\n' \
                    "$tmp_bai" >&2
                rollback_failed=true
            fi
        fi
        if [[ -e "$tmp_metrics" || -L "$tmp_metrics" ]]; then
            if ! rm -f -- "$tmp_metrics" ||
               [[ -e "$tmp_metrics" || -L "$tmp_metrics" ]]; then
                printf 'ERROR: Could not remove Step 04 staged metrics during cleanup: %s\n' \
                    "$tmp_metrics" >&2
                rollback_failed=true
            fi
        fi
    fi

    if [[ "$rollback_failed" != true && "$lock_acquired" == true ]]; then
        remove_owned_lock
        if [[ -e "$lock_path" || -L "$lock_path" ]]; then
            printf 'ERROR: Could not remove the owned Step 04 lock during cleanup: %s\n' \
                "$lock_path" >&2
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" == true ]]; then
        printf 'ERROR: Step 04 no-clobber cleanup was incomplete; retaining the owned lock and recovery residue: %s\n' \
            "$lock_path" >&2
    fi
}

[[ -d "$tmp_dir" ]] || die2 "TMP_DIR does not exist or is not a directory: $tmp_dir"
[[ -w "$tmp_dir" ]] || die2 "TMP_DIR is not writable: $tmp_dir"

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'Picard MarkDuplicates context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input BAM: %s\n' "$input_bam"
printf '  Input BAI: %s\n' "$input_bai"
printf '  Input BAM SHA-256: %s\n' "$input_bam_sha256"
printf '  Input BAI SHA-256: %s\n' "$input_bai_sha256"
printf '  Output BAM: %s\n' "$output_bam"
printf '  Output BAI: %s\n' "$output_bai"
printf '  Metrics file: %s\n' "$metrics_file"
printf '  Java bin: %s\n' "$java_bin"
printf '  Picard jar: %s\n' "$picard_jar"
printf '  Picard jar SHA-256: %s\n' "$picard_jar_sha256"
printf '  samtools bin: %s\n' "$samtools_bin"
printf '  TMP_DIR: %s\n' "$tmp_dir"
printf '  No-clobber transaction: %s\n' "$no_clobber"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Run token: %s\n' "$run_token"
printf '  Temporary BAM: %s\n' "$tmp_bam"
printf '  Temporary BAI: %s\n' "$tmp_bai"
printf '  Temporary metrics: %s\n' "$tmp_metrics"
printf '  Mode: %s\n' "$mode"

command_output_bam="$output_bam"
command_metrics_file="$metrics_file"
if [[ "$no_clobber" == true ]]; then
    command_output_bam="$tmp_bam"
    command_metrics_file="$tmp_metrics"
fi

picard_command=(
    "$java_bin"
    -jar "$picard_jar"
    MarkDuplicates
    "INPUT=$input_bam"
    "OUTPUT=$command_output_bam"
    "METRICS_FILE=$command_metrics_file"
    # Mark duplicates for downstream filtering/inspection; do not remove reads.
    REMOVE_DUPLICATES=false
    "TMP_DIR=$tmp_dir"
)

quickcheck_command=(
    "$samtools_bin"
    quickcheck
    "$command_output_bam"
)

index_command=(
    "$samtools_bin"
    index
    "$command_output_bam"
)

printf 'Picard MarkDuplicates command:\n'
print_command "${picard_command[@]}"

printf 'samtools quickcheck command:\n'
print_command "${quickcheck_command[@]}"

printf 'samtools index command:\n'
print_command "${index_command[@]}"

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Step 04" "$output_dir" ".${sample_id}.step04.*"
    require_no_owner_residue \
        "Step 04" "$metrics_dir" ".${sample_id}.step04.*"
fi

if [[ "$execute" != true ]]; then
    # Keep dry-runs side-effect-light so placeholder directories are not
    # mistaken for completed Step 04 outputs.
    printf 'Dry-run only. Add --execute to run Picard MarkDuplicates and samtools.\n'
    exit 0
fi

mkdir -p "$output_dir" "$metrics_dir"

if [[ "$no_clobber" == true ]]; then
    require_absent_outputs
    [[ ! -e "$tmp_bam" && ! -e "$tmp_bai" && ! -e "$tmp_metrics" ]] ||
        die "Step 04 temporary output already exists: $tmp_bam $tmp_bai $tmp_metrics"
    set_exit_trap cleanup_no_clobber
    acquire_lock "Step 04"
fi

"${picard_command[@]}"

# Validate the duplicate-marked BAM before creating the index expected by
# downstream steps. This gives a clearer failure when Picard writes a bad BAM.
"${quickcheck_command[@]}"
"${index_command[@]}"

command_output_bai="$command_output_bam.bai"
[[ -s "$command_output_bam" ]] || die "Output BAM is missing or empty: $command_output_bam"
[[ -s "$command_output_bai" ]] || die "Output BAI is missing or empty: $command_output_bai"
[[ -s "$command_metrics_file" ]] || die "Picard metrics file is missing or empty: $command_metrics_file"

if [[ "$no_clobber" == true ]]; then
    [[ "$(sha256_file "$input_bam")" == "$input_bam_sha256" ]] || die "Input BAM changed during Step 04."
    [[ "$(sha256_file "$input_bai")" == "$input_bai_sha256" ]] || die "Input BAI changed during Step 04."
    [[ "$(sha256_file "$picard_jar")" == "$picard_jar_sha256" ]] || die "Picard jar changed during Step 04."
    require_absent_outputs
    publication_started=true
    publish_file_create_exclusive "Step 04 BAM" "$tmp_bam" "$output_bam"
    bam_published=true
    publish_file_create_exclusive "Step 04 BAI" "$tmp_bai" "$output_bai"
    bai_published=true
    publish_file_create_exclusive \
        "Step 04 metrics" "$tmp_metrics" "$metrics_file"
    metrics_published=true
    require_owned_published_file "Step 04 BAM" "$tmp_bam" "$output_bam"
    require_owned_published_file "Step 04 BAI" "$tmp_bai" "$output_bai"
    require_owned_published_file \
        "Step 04 metrics" "$tmp_metrics" "$metrics_file"
    rm -f -- "$tmp_bam" "$tmp_bai" "$tmp_metrics"
    [[ ! -e "$tmp_bam" && ! -L "$tmp_bam" &&
       ! -e "$tmp_bai" && ! -L "$tmp_bai" &&
       ! -e "$tmp_metrics" && ! -L "$tmp_metrics" ]] ||
        die "Step 04 could not remove owned publication anchors."
    publication_started=false
    remove_owned_lock
fi

printf 'Picard MarkDuplicates output details:\n'
ls -lh "$output_bam" "$output_bai" "$metrics_file"
