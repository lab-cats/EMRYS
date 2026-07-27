#!/usr/bin/env bash
# Run STAR alignment for one paired-end RNA-seq sample.
#
# The script validates inputs and prints the STAR command in dry-run mode by
# default. Passing --execute stages, validates, and publishes STAR's five
# required outputs without leaving partial stable files after failure.
set -euo pipefail

# Print the command-line contract used by local smoke tests and SLURM wrappers.
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

# Defaults are empty so missing required arguments fail loudly below.
sample_id=""
r1_fastq=""
r2_fastq=""
star_index=""
output_dir=""
threads=""
execute=false

# Parse explicit paths and execution mode from the command line.
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

# Validate required arguments and external tool availability before any work starts.
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

if [[ -L "$output_dir" ]]; then
    die "Output directory must not be a symbolic link: $output_dir"
fi
if [[ -e "$output_dir" && ! -d "$output_dir" ]]; then
    die "Output path exists but is not a directory: $output_dir"
fi

run_token="${SLURM_JOB_ID:-manual}.$$"
stable_prefix="$output_dir/${sample_id}."
staging_dir="$output_dir/.step01.${run_token}.tmp"
staging_prefix="$staging_dir/output."

output_suffixes=(
    Aligned.sortedByCoord.out.bam
    Log.final.out
    Log.out
    Log.progress.out
    SJ.out.tab
)

stable_outputs=()
staged_outputs=()
for suffix in "${output_suffixes[@]}"; do
    stable_outputs+=("${stable_prefix}${suffix}")
    staged_outputs+=("${staging_prefix}${suffix}")
done

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
printf '  Stable output prefix: %s\n' "$stable_prefix"
printf '  Threads: %s\n' "$threads"
printf '  Mode: %s\n' "$mode"

# Write a coordinate-sorted BAM into an owned staging directory. Execute mode
# publishes the five required files only after all of them are nonempty.
star_command=(
    STAR
    --runThreadN "$threads"
    --genomeDir "$star_index"
    --readFilesIn "$r1_fastq" "$r2_fastq"
    --outFileNamePrefix "$staging_prefix"
    --outSAMtype BAM SortedByCoordinate
)

if [[ "$r1_is_gz" == true ]]; then
    star_command+=(--readFilesCommand gunzip -c)
fi

printf 'STAR command:\n'
print_command "${star_command[@]}"
printf 'Required stable outputs:\n'
printf '  %s\n' "${stable_outputs[@]}"

# Dry-run mode is the default safety path for local development and wrapper tests.
if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run STAR.\n'
    exit 0
fi

# Stable outputs are no-clobber. This prevents cleanup for a failed new attempt
# from deleting or mixing with an earlier result family.
for output in "${stable_outputs[@]}"; do
    [[ ! -e "$output" && ! -L "$output" ]] \
        || die "Refusing to overwrite existing STAR output: $output"
done

output_dir_created=false
if [[ ! -d "$output_dir" ]]; then
    output_dir_created=true
fi
mkdir -p "$output_dir"

[[ ! -e "$staging_dir" && ! -L "$staging_dir" ]] \
    || die "Refusing to reuse existing Step 01 staging path: $staging_dir"
mkdir "$staging_dir"

published_count=0
cleanup_owned_attempt() {
    local status=$?
    local index

    trap - EXIT HUP INT TERM

    if [[ "$status" -ne 0 ]]; then
        for ((index = 0; index < published_count; index++)); do
            rm -f -- "${stable_outputs[$index]}" || true
        done
    fi

    if [[ -d "$staging_dir" && ! -L "$staging_dir" ]]; then
        rm -rf -- "$staging_dir" || true
    fi

    if [[ "$status" -ne 0 && "$output_dir_created" == true ]]; then
        rmdir "$output_dir" 2>/dev/null || true
    fi

    exit "$status"
}
trap cleanup_owned_attempt EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# Execute only after validation and command logging are complete.
"${star_command[@]}"

for output in "${staged_outputs[@]}"; do
    [[ -s "$output" ]] || die "STAR required output is missing or empty: $output"
done

for ((index = 0; index < ${#stable_outputs[@]}; index++)); do
    # A same-filesystem hard link makes the no-clobber decision atomic. The
    # staging directory lives under the output directory by construction.
    ln -- "${staged_outputs[$index]}" "${stable_outputs[$index]}"
    published_count=$((published_count + 1))
    rm -f -- "${staged_outputs[$index]}"
done

for output in "${stable_outputs[@]}"; do
    [[ -s "$output" ]] || die "Published STAR output is missing or empty: $output"
done

printf 'Published STAR outputs:\n'
printf '  %s\n' "${stable_outputs[@]}"
