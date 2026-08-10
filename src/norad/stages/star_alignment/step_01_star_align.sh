#!/usr/bin/env bash
# Run STAR alignment for one paired-end RNA-seq sample.
#
# The script validates inputs and prints the STAR command in dry-run mode by
# default. Passing --execute runs STAR with the same validated parameters.
set -euo pipefail

# Print the command-line contract used by local smoke tests and SLURM wrappers.
usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/star_alignment/step_01_star_align.sh \
    --sample-id SAMPLE_ID \
    --r1-fastq R1_FASTQ \
    --r2-fastq R2_FASTQ \
    --star-index STAR_INDEX_DIR \
    --output-dir OUTPUT_DIR \
    --threads THREADS \
    [--execute]

Run STAR alignment for one paired-end RNA-seq sample.

By default this script runs in dry-run mode: it validates inputs and prints the
STAR command without executing it. Add --execute to run STAR.

Required arguments:
  --sample-id     Sample identifier used in STAR output filename prefix.
  --r1-fastq      Path to read 1 FASTQ or FASTQ.GZ file.
  --r2-fastq      Path to read 2 FASTQ or FASTQ.GZ file.
  --star-index    Path to STAR genome index directory.
  --output-dir    Directory where STAR outputs will be written.
  --threads       Number of threads for STAR; must be a positive integer.

Options:
  --execute       Execute STAR after validation. Without this, dry-run only.
  -h, --help      Show this help message and exit.
USAGE
}

# shellcheck source=../../libraries/argument_parsing.sh
script_dir="${BASH_SOURCE[0]%/*}"
if [[ "$script_dir" == "$BASH_SOURCE[0]" ]]; then
    script_dir="."
fi
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"

# Defaults are empty so missing required arguments fail loudly below.
declare_required_arguments sample_id r1_fastq r2_fastq star_index output_dir threads
execute=false

# Parse explicit paths and execution mode from the command line.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --r1-fastq) assign_option_value "$1" "${2:-}" r1_fastq; shift 2 ;;
        --r2-fastq) assign_option_value "$1" "${2:-}" r2_fastq; shift 2 ;;
        --star-index) assign_option_value "$1" "${2:-}" star_index; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

# Validate required arguments and external tool availability before any work starts.
require_arguments

[[ -f "$r1_fastq" ]] || die "R1 FASTQ does not exist or is not a file: $r1_fastq"
[[ -f "$r2_fastq" ]] || die "R2 FASTQ does not exist or is not a file: $r2_fastq"
[[ -d "$star_index" ]] || die "STAR index directory does not exist: $star_index"
command -v STAR >/dev/null 2>&1 || die "STAR executable was not found on PATH. Load the STAR module or update PATH."

validate_positive_integer "--threads" "$threads"

# STAR needs --readFilesCommand only when both FASTQ inputs are gzip-compressed.
r1_is_gz=false
r2_is_gz=false
if is_gzip_path "$r1_fastq"; then
    r1_is_gz=true
fi
if is_gzip_path "$r2_fastq"; then
    r2_is_gz=true
fi

if [[ "$r1_is_gz" != "$r2_is_gz" ]]; then
    die "Mixed FASTQ compression is not supported: R1 and R2 must both be .gz or both be uncompressed."
fi

if [[ "$r1_is_gz" == true ]]; then
    command -v gunzip >/dev/null 2>&1 || die "gunzip was not found on PATH but both FASTQ files end in .gz."
fi

mkdir -p "$output_dir"

# Report the resolved run context so cluster logs are reproducible.
mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'STAR alignment context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  R1 FASTQ: %s\n' "$r1_fastq"
printf '  R2 FASTQ: %s\n' "$r2_fastq"
printf '  STAR index: %s\n' "$star_index"
printf '  Output directory: %s\n' "$output_dir"
printf '  Threads: %s\n' "$threads"
printf '  Mode: %s\n' "$mode"

# Write coordinate-sorted BAM directly to avoid large default SAM output.
star_command=(
    STAR
    --runThreadN "$threads"
    --genomeDir "$star_index"
    --readFilesIn "$r1_fastq" "$r2_fastq"
    --outFileNamePrefix "$output_dir/${sample_id}."
    --outSAMtype BAM SortedByCoordinate
)

if [[ "$r1_is_gz" == true ]]; then
    star_command+=(--readFilesCommand gunzip -c)
fi

printf 'STAR command:\n'
print_command "${star_command[@]}"

# Dry-run mode is the default safety path for local development and wrapper tests.
if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run STAR.\n'
    exit 0
fi

# Execute only after validation and command logging are complete.
"${star_command[@]}"
