#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Split reads spanning introns with GATK SplitNCigarReads.

Usage: src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh \
  --sample-id SAMPLE_ID \
  --input-bam INPUT_BAM \
  --reference-fasta REFERENCE_FASTA \
  --output-dir OUTPUT_DIR \
  [--gatk-bin GATK_BIN] \
  [--samtools-bin SAMTOOLS_BIN] \
  [--java-bin JAVA_BIN]

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
# shellcheck source=../../libraries/gatk_invocation.sh
source "$script_dir/../../libraries/gatk_invocation.sh"

declare_required_arguments sample_id input_bam reference_fasta output_dir
gatk_bin=""
samtools_bin=""
java_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --gatk-bin) assign_option_value "$1" "${2:-}" gatk_bin; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin; shift 2 ;;
        --java-bin) assign_option_value "$1" "${2:-}" java_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

validate_reference_sidecar() {
    local label="$1"
    local path="$2"

    if [[ ! -s "$path" ]]; then
        die "$label is missing or empty: $path. Run Step 00c before Step 05; Step 05 does not create reference sidecars."
    fi
}

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

    # GATK should preserve the coordinate sort and sample read group from the
    # Step 04 input. Validate those properties before anything becomes final.
    [[ -s "$bam" ]] || die "$label BAM is missing or empty: $bam"
    "$samtools_bin" quickcheck "$bam" || die "$label BAM failed samtools quickcheck: $bam"

    header="$("$samtools_bin" view -H "$bam")"
    grep -q '^@HD.*SO:coordinate' <<< "$header" || die "$label BAM header is not coordinate sorted"

    rg_lines="$(printf '%s\n' "$header" | grep '^@RG' || true)"
    rg_count="$(printf '%s\n' "$rg_lines" | sed '/^$/d' | wc -l | tr -d ' ')"
    [[ "$rg_count" == "1" ]] || die "$label BAM must contain exactly one @RG line; found: $rg_count"

    rg_line="$rg_lines"
    [[ "$rg_line" == *"ID:$sample_id"* ]] || die "$label @RG line is missing ID:$sample_id"
    [[ "$rg_line" == *"SM:$sample_id"* ]] || die "$label @RG line is missing SM:$sample_id"

    total_records="$("$samtools_bin" view -c "$bam")"
    [[ "$total_records" =~ ^[0-9]+$ ]] || die "$label total alignment count is not numeric: $total_records"
    [[ "$total_records" -gt 0 ]] || die "$label BAM contains no alignment records"

    tagged_records="$("$samtools_bin" view -c -d "RG:$sample_id" "$bam")"
    [[ "$tagged_records" =~ ^[0-9]+$ ]] || die "$label tagged alignment count is not numeric: $tagged_records"
    [[ "$tagged_records" -eq "$total_records" ]] || die "$label BAM has $tagged_records of $total_records records tagged RG:$sample_id"

    [[ -s "$bai" ]] || die "$label BAI is missing or empty: $bai"
}

validate_safe_id "--sample-id" "$sample_id"
validate_nonempty_file "Input BAM" "$input_bam"
validate_nonempty_file "Input BAM index" "$input_bam.bai"
validate_nonempty_file "Reference FASTA" "$reference_fasta"
validate_reference_sidecar "Reference FAI" "$reference_fasta.fai"
reference_name="$(basename -- "$reference_fasta")"
validate_reference_sidecar "Reference DICT" "$(dirname -- "$reference_fasta")/${reference_name%.*}.dict"
java_bin="$(resolve_overridable_executable "Java" "$java_bin" "JAVA_BIN_OVERRIDE" "java" "/bin/java")"
gatk_bin="$(resolve_overridable_executable "GATK" "$gatk_bin" "GATK_BIN_OVERRIDE" "gatk")"
samtools_bin="$(resolve_overridable_executable "samtools" "$samtools_bin" "SAMTOOLS_BIN_OVERRIDE" "samtools")"
validate_and_print_java "GATK" JAVA_BIN JAVA_VERSION_OUTPUT "Java version:" 17 \
    "Set JAVA_BIN_OVERRIDE to a Java 17 executable." "$java_bin"
printf 'GATK version:\n'
invoke_gatk_with_selected_java "$java_bin" "$gatk_bin" --version 2>&1 ||
    die2 "GATK version check failed: $gatk_bin"

output_bam="$output_dir/$sample_id.split_ncigar.bam"
invoke_gatk_with_selected_java "$java_bin" "$gatk_bin" \
    --java-options "-Djava.io.tmpdir=$EMRYS_TASK_WORK_DIR" SplitNCigarReads \
    --tmp-dir "$EMRYS_TASK_WORK_DIR" -R "$reference_fasta" -I "$input_bam" -O "$output_bam"
# GATK may also leave sample.split_ncigar.bai; samtools supplies the canonical suffix.
"$samtools_bin" index "$output_bam"
validate_bam_pair "$output_bam" "$output_bam.bai" "SplitNCigarReads"
