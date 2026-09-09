#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Mark PCR and optical duplicates with Picard without removing reads.

Usage: src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh \
  --sample-id SAMPLE_ID \
  --input-bam INPUT_BAM \
  --output-dir OUTPUT_DIR \
  --metrics-dir METRICS_DIR \
  --picard-jar PICARD_JAR \
  [--java-bin JAVA_BIN] \
  [--samtools-bin SAMTOOLS_BIN]

Internal worker: requires an existing EMRYS_TASK_WORK_DIR supplied by the runner.
Output destinations are staging paths supplied by the runner.
  -h, --help  Show this help message and exit.
USAGE
}

script_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$script_dir/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"

declare_required_arguments sample_id input_bam output_dir metrics_dir picard_jar
java_bin=""
samtools_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --metrics-dir) assign_option_value "$1" "${2:-}" metrics_dir; shift 2 ;;
        --picard-jar) assign_option_value "$1" "${2:-}" picard_jar; shift 2 ;;
        --java-bin) assign_option_value "$1" "${2:-}" java_bin; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

validate_safe_id "--sample-id" "$sample_id"
validate_nonempty_file "Input BAM" "$input_bam"
validate_nonempty_file "Input BAM index" "$input_bam.bai"
validate_nonempty_file "Picard jar" "$picard_jar"
[[ -r "$picard_jar" ]] || die "Picard jar is not readable: $picard_jar"
java_bin="$(resolve_executable_value "Java" "$java_bin" "java")"
samtools_bin="$(resolve_executable_value "samtools" "$samtools_bin" "samtools")"
output_bam="$output_dir/$sample_id.markdup.bam"
metrics="$metrics_dir/$sample_id.markdup.metrics.txt"
"$java_bin" -jar "$picard_jar" MarkDuplicates "INPUT=$input_bam" \
    "OUTPUT=$output_bam" "METRICS_FILE=$metrics" REMOVE_DUPLICATES=false \
    "TMP_DIR=$EMRYS_TASK_WORK_DIR"
"$samtools_bin" quickcheck "$output_bam"
"$samtools_bin" index "$output_bam"
validate_nonempty_file "Duplicate-marked BAM" "$output_bam"
validate_nonempty_file "Duplicate-marked BAI" "$output_bam.bai"
validate_nonempty_file "Picard metrics" "$metrics"
