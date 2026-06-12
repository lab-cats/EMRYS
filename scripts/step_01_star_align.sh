#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  scripts/step_01_star_align.sh \
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

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

require_value() {
    local option="$1"
    local value="${2:-}"

    if [[ -z "$value" || "$value" == --* ]]; then
        die "$option requires a value."
    fi
}

is_gzip_path() {
    [[ "$1" == *.gz ]]
}

sample_id=""
r1_fastq=""
r2_fastq=""
star_index=""
output_dir=""
threads=""
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id)
            require_value "$1" "${2:-}"
            sample_id="$2"
            shift 2
            ;;
        --r1-fastq)
            require_value "$1" "${2:-}"
            r1_fastq="$2"
            shift 2
            ;;
        --r2-fastq)
            require_value "$1" "${2:-}"
            r2_fastq="$2"
            shift 2
            ;;
        --star-index)
            require_value "$1" "${2:-}"
            star_index="$2"
            shift 2
            ;;
        --output-dir)
            require_value "$1" "${2:-}"
            output_dir="$2"
            shift 2
            ;;
        --threads)
            require_value "$1" "${2:-}"
            threads="$2"
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
[[ -n "$r1_fastq" ]] || die "Missing required argument: --r1-fastq."
[[ -n "$r2_fastq" ]] || die "Missing required argument: --r2-fastq."
[[ -n "$star_index" ]] || die "Missing required argument: --star-index."
[[ -n "$output_dir" ]] || die "Missing required argument: --output-dir."
[[ -n "$threads" ]] || die "Missing required argument: --threads."

[[ -f "$r1_fastq" ]] || die "R1 FASTQ does not exist or is not a file: $r1_fastq"
[[ -f "$r2_fastq" ]] || die "R2 FASTQ does not exist or is not a file: $r2_fastq"
[[ -d "$star_index" ]] || die "STAR index directory does not exist: $star_index"
command -v STAR >/dev/null 2>&1 || die "STAR executable was not found on PATH. Load the STAR module or update PATH."

if ! [[ "$threads" =~ ^[1-9][0-9]*$ ]]; then
    die "--threads must be a positive integer; got: $threads"
fi

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

# TODO: Revisit STAR output settings before full-scale execution. STAR defaults
# may produce very large SAM files, which can be expensive on cluster storage.
star_command=(
    STAR
    --runThreadN "$threads"
    --genomeDir "$star_index"
    --readFilesIn "$r1_fastq" "$r2_fastq"
    --outFileNamePrefix "$output_dir/${sample_id}."
)

if [[ "$r1_is_gz" == true ]]; then
    star_command+=(--readFilesCommand gunzip -c)
fi

printf 'STAR command:\n'
print_command "${star_command[@]}"

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run STAR.\n'
    exit 0
fi

"${star_command[@]}"
