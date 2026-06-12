#!/usr/bin/env bash
# Sort and index one SAM/BAM alignment file with samtools.
#
# The script validates inputs and prints the samtools commands in dry-run mode
# by default. Passing --execute runs the same commands after validation.
set -euo pipefail

# Print the command-line contract used by local smoke tests and SLURM wrappers.
usage() {
    cat <<'USAGE'
Usage:
  scripts/step_02_sort_index_bam.sh \
    --sample-id SAMPLE_ID \
    --input-alignment INPUT_ALIGNMENT \
    --output-dir OUTPUT_DIR \
    --threads THREADS \
    [--execute]

Sort and index one SAM or BAM alignment file with samtools.

By default this script runs in dry-run mode: it validates inputs and prints the
samtools commands without executing them. Add --execute to run samtools.

Required arguments:
  --sample-id         Sample identifier used in output filenames.
  --input-alignment  Input SAM or BAM alignment file to sort.
  --output-dir       Directory where sorted BAM and BAI outputs will be written.
  --threads          Number of threads for samtools sort; must be a positive integer.

Options:
  --execute          Execute samtools after validation. Without this, dry-run only.
  -h, --help         Show this help message and exit.
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

# Defaults are empty so missing required arguments fail loudly below.
sample_id=""
input_alignment=""
output_dir=""
threads=""
execute=false

# Parse explicit input/output paths and execution mode from the command line.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id)
            require_value "$1" "${2:-}"
            sample_id="$2"
            shift 2
            ;;
        --input-alignment)
            require_value "$1" "${2:-}"
            input_alignment="$2"
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

# Validate required arguments and external tool availability before output setup.
[[ -n "$sample_id" ]] || die "Missing required argument: --sample-id."
[[ -n "$input_alignment" ]] || die "Missing required argument: --input-alignment."
[[ -n "$output_dir" ]] || die "Missing required argument: --output-dir."
[[ -n "$threads" ]] || die "Missing required argument: --threads."

[[ -f "$input_alignment" ]] || die "Input alignment does not exist or is not a file: $input_alignment"
command -v samtools >/dev/null 2>&1 || die "samtools executable was not found on PATH. Load the samtools module or update PATH."

if ! [[ "$threads" =~ ^[1-9][0-9]*$ ]]; then
    die "--threads must be a positive integer; got: $threads"
fi

mkdir -p "$output_dir"

# Use deterministic output names so downstream steps can locate sorted BAMs.
output_bam="$output_dir/${sample_id}.sorted.bam"
output_bai="$output_bam.bai"

# Report the resolved run context so cluster logs are reproducible.
mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'samtools sort/index context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input alignment: %s\n' "$input_alignment"
printf '  Output directory: %s\n' "$output_dir"
printf '  Output BAM: %s\n' "$output_bam"
printf '  Output BAI: %s\n' "$output_bai"
printf '  Threads: %s\n' "$threads"
printf '  Mode: %s\n' "$mode"

# Build commands as arrays to preserve argument boundaries and make dry-run output exact.
sort_command=(
    samtools
    sort
    -@ "$threads"
    -o "$output_bam"
    "$input_alignment"
)

index_command=(
    samtools
    index
    "$output_bam"
)

printf 'samtools sort command:\n'
print_command "${sort_command[@]}"

printf 'samtools index command:\n'
print_command "${index_command[@]}"

# Dry-run mode is the default safety path for local development and wrapper tests.
if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run samtools.\n'
    exit 0
fi

# Execute only after validation and command logging are complete.
"${sort_command[@]}"
"${index_command[@]}"
