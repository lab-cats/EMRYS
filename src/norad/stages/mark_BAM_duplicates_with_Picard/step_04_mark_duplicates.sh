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
  src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --output-dir OUTPUT_DIR \
    --metrics-dir METRICS_DIR \
    --picard-jar PICARD_JAR \
    [--java-bin JAVA_BIN] \
    [--samtools-bin SAMTOOLS_BIN] \
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

sample_id=""
input_bam=""
output_dir=""
metrics_dir=""
picard_jar=""
java_bin_arg=""
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
        --metrics-dir)
            require_value "$1" "${2:-}"
            metrics_dir="$2"
            shift 2
            ;;
        --picard-jar)
            require_value "$1" "${2:-}"
            picard_jar="$2"
            shift 2
            ;;
        --java-bin)
            require_value "$1" "${2:-}"
            java_bin_arg="$2"
            shift 2
            ;;
        --samtools-bin)
            require_value "$1" "${2:-}"
            samtools_bin_arg="$2"
            shift 2
            ;;
        --execute)
            execute=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1. Run with --help for usage."
            ;;
    esac
done

[[ -n "$sample_id" ]] || die "Missing required argument: --sample-id."
[[ -n "$input_bam" ]] || die "Missing required argument: --input-bam."
[[ -n "$output_dir" ]] || die "Missing required argument: --output-dir."
[[ -n "$metrics_dir" ]] || die "Missing required argument: --metrics-dir."
[[ -n "$picard_jar" ]] || die "Missing required argument: --picard-jar."

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
java_bin="$(resolve_executable_value "Java" "$java_bin_arg" "java")"
samtools_bin="$(resolve_executable_value "samtools" "$samtools_bin_arg" "samtools")"

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
printf '  Output BAM: %s\n' "$output_bam"
printf '  Output BAI: %s\n' "$output_bai"
printf '  Metrics file: %s\n' "$metrics_file"
printf '  Java bin: %s\n' "$java_bin"
printf '  Picard jar: %s\n' "$picard_jar"
printf '  samtools bin: %s\n' "$samtools_bin"
printf '  TMP_DIR: %s\n' "$tmp_dir"
printf '  Mode: %s\n' "$mode"

picard_command=(
    "$java_bin"
    -jar "$picard_jar"
    MarkDuplicates
    "INPUT=$input_bam"
    "OUTPUT=$output_bam"
    "METRICS_FILE=$metrics_file"
    # Mark duplicates for downstream filtering/inspection; do not remove reads.
    REMOVE_DUPLICATES=false
    "TMP_DIR=$tmp_dir"
)

quickcheck_command=(
    "$samtools_bin"
    quickcheck
    "$output_bam"
)

index_command=(
    "$samtools_bin"
    index
    "$output_bam"
)

printf 'Picard MarkDuplicates command:\n'
print_command "${picard_command[@]}"

printf 'samtools quickcheck command:\n'
print_command "${quickcheck_command[@]}"

printf 'samtools index command:\n'
print_command "${index_command[@]}"

if [[ "$execute" != true ]]; then
    # Keep dry-runs side-effect-light so placeholder directories are not
    # mistaken for completed Step 04 outputs.
    printf 'Dry-run only. Add --execute to run Picard MarkDuplicates and samtools.\n'
    exit 0
fi

mkdir -p "$output_dir" "$metrics_dir"

"${picard_command[@]}"

# Validate the duplicate-marked BAM before creating the index expected by
# downstream steps. This gives a clearer failure when Picard writes a bad BAM.
"${quickcheck_command[@]}"
"${index_command[@]}"

[[ -s "$output_bam" ]] || die "Output BAM is missing or empty: $output_bam"
[[ -s "$output_bai" ]] || die "Output BAI is missing or empty: $output_bai"
[[ -s "$metrics_file" ]] || die "Picard metrics file is missing or empty: $metrics_file"

printf 'Picard MarkDuplicates output details:\n'
ls -lh "$output_bam" "$output_bai" "$metrics_file"
