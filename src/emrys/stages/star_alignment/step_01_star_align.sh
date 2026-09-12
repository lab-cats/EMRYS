#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Align one paired FASTQ sample with STAR.

Usage: src/emrys/stages/star_alignment/step_01_star_align.sh \
  --sample-id SAMPLE_ID \
  --r1-fastq R1_FASTQ \
  --r2-fastq R2_FASTQ \
  --star-index STAR_INDEX \
  --output-dir OUTPUT_DIR \
  --threads THREADS \
  --star-bin STAR_BIN \
  --gunzip-bin GUNZIP_BIN

Internal worker: requires an existing EMRYS_TASK_WORK_DIR supplied by the runner.
Output destinations are staging paths supplied by the runner.
  -h, --help  Show this help message and exit.
USAGE
}

script_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"

declare_required_arguments sample_id r1_fastq r2_fastq star_index output_dir threads star_bin gunzip_bin

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --r1-fastq) assign_option_value "$1" "${2:-}" r1_fastq; shift 2 ;;
        --r2-fastq) assign_option_value "$1" "${2:-}" r2_fastq; shift 2 ;;
        --star-index) assign_option_value "$1" "${2:-}" star_index; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --star-bin) assign_option_value "$1" "${2:-}" star_bin; shift 2 ;;
        --gunzip-bin) assign_option_value "$1" "${2:-}" gunzip_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

validate_safe_id "--sample-id" "$sample_id"
validate_positive_integer "--threads" "$threads"
validate_nonempty_file "R1 FASTQ" "$r1_fastq"
validate_nonempty_file "R2 FASTQ" "$r2_fastq"
[[ -d "$star_index" ]] || die "STAR index directory does not exist: $star_index"
require_executable "STAR" "$star_bin"
command=("$star_bin" --runThreadN "$threads" --genomeDir "$star_index"
    --readFilesIn "$r1_fastq" "$r2_fastq" --outFileNamePrefix "$output_dir/$sample_id."
    --outSAMtype BAM SortedByCoordinate
    --outSAMattrRGline "ID:$sample_id" "SM:$sample_id" "LB:$sample_id" PL:ILLUMINA)
if is_gzip_path "$r1_fastq" && is_gzip_path "$r2_fastq"; then
    require_executable "gunzip" "$gunzip_bin"
    command+=(--readFilesCommand "$gunzip_bin" -c)
elif is_gzip_path "$r1_fastq" || is_gzip_path "$r2_fastq"; then
    die "R1 and R2 must both be gzip-compressed or both be uncompressed."
fi
print_command "${command[@]}"
"${command[@]}"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    validate_nonempty_file "STAR output" "$output_dir/$sample_id.$suffix"
done
