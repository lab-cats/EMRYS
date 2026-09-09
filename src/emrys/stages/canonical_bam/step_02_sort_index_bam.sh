#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Prepare a coordinate-sorted BAM with one canonical sample read group.

Usage: src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh \
  --sample-id SAMPLE_ID \
  --input-alignment INPUT_ALIGNMENT \
  --output-dir OUTPUT_DIR \
  --threads THREADS \
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

declare_required_arguments sample_id input_alignment output_dir threads
samtools_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-alignment) assign_option_value "$1" "${2:-}" input_alignment; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

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
    grep -q '^@HD.*SO:coordinate' <<< "$header" || die "$label BAM header is not coordinate sorted"

    total_records="$("$samtools_bin" view -c "$bam")"
    [[ "$total_records" =~ ^[0-9]+$ ]] || die "$label total alignment count is not numeric: $total_records"
    [[ "$total_records" -gt 0 ]] || die "$label BAM contains no alignment records"

    tagged_records="$("$samtools_bin" view -c -d "RG:$sample_id" "$bam")"
    [[ "$tagged_records" =~ ^[0-9]+$ ]] || die "$label tagged alignment count is not numeric: $tagged_records"
    [[ "$tagged_records" -eq "$total_records" ]] || die "$label BAM has $tagged_records of $total_records records tagged RG:$sample_id"

    [[ -s "$bai" ]] || die "$label BAI is missing or empty: $bai"
}

input_has_canonical_bam_contract() {
    local header="$1"
    local rg_lines
    local rg_count
    local total_records
    local tagged_records

    grep -q '^@HD.*SO:coordinate' <<< "$header" || return 1
    rg_lines="$(printf '%s\n' "$header" | grep '^@RG' || true)"
    rg_count="$(printf '%s\n' "$rg_lines" | sed '/^$/d' | wc -l | tr -d ' ')"
    [[ "$rg_count" == "1" ]] || return 1
    [[ "$rg_lines" == *"ID:$sample_id"* ]] || return 1
    [[ "$rg_lines" == *"SM:$sample_id"* ]] || return 1
    [[ "$rg_lines" == *"LB:$sample_id"* ]] || return 1
    [[ "$rg_lines" == *"PL:ILLUMINA"* ]] || return 1

    total_records="$("$samtools_bin" view -c "$input_alignment")" || return 1
    [[ "$total_records" =~ ^[0-9]+$ && "$total_records" -gt 0 ]] || return 1
    tagged_records="$("$samtools_bin" view -c -d "RG:$sample_id" "$input_alignment")" || return 1
    [[ "$tagged_records" =~ ^[0-9]+$ ]] || return 1
    [[ "$tagged_records" -eq "$total_records" ]]
}

validate_safe_id "--sample-id" "$sample_id"
validate_positive_integer "--threads" "$threads"
validate_nonempty_file "Input alignment" "$input_alignment"
samtools_bin="$(resolve_executable_value "samtools" "$samtools_bin" "samtools")"
output_bam="$output_dir/$sample_id.sorted.bam"
input_header="$("$samtools_bin" view -H "$input_alignment")" ||
    die "Could not inspect input alignment header: $input_alignment"
canonical_source="$input_alignment"
if ! grep -q '^@HD.*SO:coordinate' <<< "$input_header"; then
    canonical_source="$EMRYS_TASK_WORK_DIR/sorted.bam"
    "$samtools_bin" sort -@ "$threads" -o "$canonical_source" "$input_alignment"
fi
# Keep the no-rewrite path for an already canonical BAM when hard links work.
if ! { input_has_canonical_bam_contract "$input_header" && ln -- "$input_alignment" "$output_bam"; }; then
    "$samtools_bin" addreplacerg -@ "$threads" -m overwrite_all -w \
        -r "ID:$sample_id" -r "SM:$sample_id" -r "LB:$sample_id" -r PL:ILLUMINA \
        -o "$output_bam" "$canonical_source"
fi
"$samtools_bin" index "$output_bam"
validate_bam_pair "$output_bam" "$output_bam.bai" "Canonical"
