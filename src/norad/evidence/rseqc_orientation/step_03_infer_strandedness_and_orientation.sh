#!/usr/bin/env bash
# Step 03: infer RNA-seq library strandedness and read orientation with RSeQC.
#
# This step uses RSeQC infer_experiment.py on the canonical Step 02 sorted BAM.
# The report records mechanical paired-read orientation fractions. It does not
# infer biological strand or update the sample's declared strandedness.
#
# Dry-run mode intentionally validates the requested inputs and prints the exact
# infer_experiment.py command, but does not create the output directory or run
# RSeQC. Passing --execute runs RSeQC and validates the output file.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --bed12 BED12 \
    --output-dir OUTPUT_DIR \
    [--infer-experiment-bin INFER_EXPERIMENT_BIN] \
    [--no-clobber] \
    [--execute]

Run RSeQC infer_experiment.py on one canonical sorted BAM to infer RNA-seq
library strandedness and read orientation.

By default this script runs in dry-run mode: it validates inputs and prints the
RSeQC command without executing it. Add --execute to run infer_experiment.py.

Required arguments:
  --sample-id              Sample identifier used in output filenames.
  --input-bam              Input sorted BAM file from Step 02.
  --bed12                  BED12 annotation file for RSeQC.
  --output-dir             Directory where infer_experiment output is written.

Options:
  --infer-experiment-bin   Path or command name for infer_experiment.py.
                           Defaults to .venv/bin/infer_experiment.py when
                           present, otherwise infer_experiment.py.
  --no-clobber             Require an absent final report and stage publication.
                           Required by orchestration.
  --execute                Execute RSeQC after validation. Without this,
                           dry-run only.
  -h, --help               Show this help message and exit.
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

default_infer_experiment_bin() {
    # The CSU project environment installs RSeQC in the repo virtualenv. Falling
    # back to the command name keeps the same script usable in any environment
    # where infer_experiment.py is already on PATH.
    if [[ -e ".venv/bin/infer_experiment.py" ]]; then
        printf '.venv/bin/infer_experiment.py\n'
    else
        printf 'infer_experiment.py\n'
    fi
}

declare_required_arguments sample_id input_bam bed12 output_dir
infer_experiment_bin="$(default_infer_experiment_bin)"
execute=false
no_clobber=false

# Parse explicit file paths instead of assuming a machine-specific directory
# layout. The SLURM wrapper supplies default cluster-validation paths.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --bed12) assign_option_value "$1" "${2:-}" bed12; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --infer-experiment-bin) assign_option_value "$1" "${2:-}" infer_experiment_bin; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

# Validate all run inputs before printing a successful dry-run. This catches
# missing Step 02 outputs and missing RSeQC setup without launching compute.
[[ -f "$input_bam" ]] || die "BAM does not exist or is not a file: $input_bam"

# samtools commonly writes either sample.bam.bai or sample.bai; accept both so
# Step 03 can consume canonical BAMs from either convention.
if [[ -f "$input_bam.bai" ]]; then
    bam_index="$input_bam.bai"
elif [[ -f "${input_bam%.bam}.bai" ]]; then
    bam_index="${input_bam%.bam}.bai"
else
    die "BAM index does not exist. Expected either: $input_bam.bai or ${input_bam%.bam}.bai"
fi

[[ -f "$bed12" ]] || die "BED12 annotation does not exist or is not a file: $bed12"
requested_infer_experiment_bin="$infer_experiment_bin"
infer_experiment_bin="$(resolve_executable_value "infer_experiment.py" "$infer_experiment_bin" "infer_experiment.py")"
input_bam_sha256="not-bound"
bam_index_sha256="not-bound"
bed12_sha256="not-bound"
if [[ "$no_clobber" == true ]]; then
    validate_safe_id "--sample-id" "$sample_id"
    input_bam_sha256="$(sha256_file "$input_bam")"
    bam_index_sha256="$(sha256_file "$bam_index")"
    bed12_sha256="$(sha256_file "$bed12")"
fi

output_file="$output_dir/${sample_id}.infer_experiment.txt"
run_token="${NORAD_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "Step 03 run token" "$run_token"
tmp_output_file="$output_dir/.${sample_id}.step03.${run_token}.infer_experiment.tmp"
lock_path="$output_dir/.${sample_id}.step03.lock"
lock_owner_file="$lock_path/owner"
lock_acquired=false
publication_started=false
output_published=false

cleanup_no_clobber() {
    local status="$1"
    local rollback_failed=false

    set +e
    if [[ "$status" -ne 0 &&
          "$publication_started" == true &&
          "$output_published" == true ]]; then
        if ! remove_owned_published_file \
            "Step 03 report" "$tmp_output_file" "$output_file"; then
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" != true &&
          ( -e "$tmp_output_file" || -L "$tmp_output_file" ) ]]; then
        if ! rm -f -- "$tmp_output_file" ||
           [[ -e "$tmp_output_file" || -L "$tmp_output_file" ]]; then
            printf 'ERROR: Could not remove Step 03 staging output during cleanup: %s\n' \
                "$tmp_output_file" >&2
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" != true && "$lock_acquired" == true ]]; then
        remove_owned_lock
        if [[ -e "$lock_path" || -L "$lock_path" ]]; then
            printf 'ERROR: Could not remove the owned Step 03 lock during cleanup: %s\n' \
                "$lock_path" >&2
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" == true ]]; then
        printf 'ERROR: Step 03 no-clobber cleanup was incomplete; retaining the owned lock and recovery residue: %s\n' \
            "$lock_path" >&2
    fi
}

# Report the resolved context in the same style as earlier steps so SLURM logs
# are enough to rerun or debug the command later.
mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'RSeQC infer_experiment context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input BAM: %s\n' "$input_bam"
printf '  BAM index found: %s\n' "$bam_index"
printf '  BED12 annotation: %s\n' "$bed12"
printf '  BAM SHA-256: %s\n' "$input_bam_sha256"
printf '  BAM index SHA-256: %s\n' "$bam_index_sha256"
printf '  BED12 SHA-256: %s\n' "$bed12_sha256"
printf '  Output directory: %s\n' "$output_dir"
printf '  Output file: %s\n' "$output_file"
printf '  infer_experiment.py: %s\n' "$requested_infer_experiment_bin"
printf '  Resolved infer_experiment.py: %s\n' "$infer_experiment_bin"
printf '  No-clobber transaction: %s\n' "$no_clobber"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Run token: %s\n' "$run_token"
printf '  Temporary output: %s\n' "$tmp_output_file"
printf '  Mode: %s\n' "$mode"

infer_command=(
    "$infer_experiment_bin"
    -r "$bed12"
    -i "$input_bam"
)

printf 'RSeQC infer_experiment command:\n'
print_command "${infer_command[@]}"

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Step 03" "$output_dir" ".${sample_id}.step03.*"
fi

if [[ "$execute" != true ]]; then
    # Keep dry-runs side-effect-light: no mkdir and no placeholder output file.
    printf 'Dry-run only. Add --execute to run RSeQC infer_experiment.py.\n'
    exit 0
fi

mkdir -p "$output_dir"

capture_path="$output_file"
if [[ "$no_clobber" == true ]]; then
    [[ ! -e "$output_file" ]] || die "Step 03 --no-clobber output already exists: $output_file"
    [[ ! -e "$tmp_output_file" ]] || die "Step 03 temporary output already exists: $tmp_output_file"
    set_exit_trap cleanup_no_clobber
    acquire_lock "Step 03"
    capture_path="$tmp_output_file"
fi

# RSeQC writes its report to stdout, so redirect stdout into the stable
# downstream filename expected by the pipeline plan.
"${infer_command[@]}" >"$capture_path"

[[ -s "$capture_path" ]] || die "infer_experiment.py output is missing or empty: $capture_path"

if [[ "$no_clobber" == true ]]; then
    [[ "$(sha256_file "$input_bam")" == "$input_bam_sha256" ]] || die "BAM changed during Step 03."
    [[ "$(sha256_file "$bam_index")" == "$bam_index_sha256" ]] || die "BAM index changed during Step 03."
    [[ "$(sha256_file "$bed12")" == "$bed12_sha256" ]] || die "BED12 changed during Step 03."
    [[ ! -e "$output_file" ]] || die "Step 03 --no-clobber output appeared during execution: $output_file"
    publication_started=true
    publish_file_create_exclusive \
        "Step 03 report" "$tmp_output_file" "$output_file"
    output_published=true
    require_owned_published_file \
        "Step 03 report" "$tmp_output_file" "$output_file"
    rm -f -- "$tmp_output_file"
    [[ ! -e "$tmp_output_file" && ! -L "$tmp_output_file" ]] ||
        die "Step 03 could not remove its owned publication anchor: $tmp_output_file"
    publication_started=false
    remove_owned_lock
fi

printf 'RSeQC infer_experiment output details:\n'
ls -lh "$output_file"

printf 'RSeQC infer_experiment output preview:\n'
sed -n '1,20p' "$output_file"
