#!/usr/bin/env bash
# Run basic integrity/QC checks on one canonical sorted BAM with samtools.
#
# The script validates the BAM and index, then prints the samtools commands in
# dry-run mode by default. Passing --execute runs the same commands.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
    --sample-id SAMPLE_ID \
    --bam BAM \
    --output-dir OUTPUT_DIR \
    [--execute]

Run basic BAM integrity/QC checks on a canonical sorted BAM from Step 02.

By default this script runs in dry-run mode: it validates inputs and prints the
samtools commands without executing them. Add --execute to run samtools.

Required arguments:
  --sample-id    Sample identifier used in output filenames.
  --bam          Input sorted BAM file from Step 02.
  --output-dir   Directory where BAM QC outputs will be written.

Options:
  --execute      Execute samtools after validation. Without this, dry-run only.
  -h, --help     Show this help message and exit.
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

declare_required_arguments sample_id bam output_dir
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --bam) assign_option_value "$1" "${2:-}" bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

[[ -f "$bam" ]] || die "BAM does not exist or is not a file: $bam"

if [[ -f "$bam.bai" ]]; then
    bam_index="$bam.bai"
elif [[ -f "${bam%.bam}.bai" ]]; then
    bam_index="${bam%.bam}.bai"
else
    die "BAM index does not exist. Expected either: $bam.bai or ${bam%.bam}.bai"
fi

samtools_bin="$(resolve_executable_value "samtools" "" "samtools")"

mkdir -p "$output_dir"

QUICKCHECK_OUT="$output_dir/${sample_id}.quickcheck.txt"
FLAGSTAT_OUT="$output_dir/${sample_id}.flagstat.txt"

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'BAM QC context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  BAM: %s\n' "$bam"
printf '  BAM index found: %s\n' "$bam_index"
printf '  Output directory: %s\n' "$output_dir"
printf '  Quickcheck output: %s\n' "$QUICKCHECK_OUT"
printf '  Flagstat output: %s\n' "$FLAGSTAT_OUT"
printf '  Mode: %s\n' "$mode"

quickcheck_command=(
    "$samtools_bin"
    quickcheck
    -v
    "$bam"
)

flagstat_command=(
    "$samtools_bin"
    flagstat
    "$bam"
)

printf 'samtools quickcheck command:\n'
print_command "${quickcheck_command[@]}"

printf 'samtools flagstat command:\n'
print_command "${flagstat_command[@]}"

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to run samtools.\n'
    exit 0
fi

if ! "${quickcheck_command[@]}" >"$QUICKCHECK_OUT" 2>&1; then
    printf 'ERROR: samtools quickcheck failed. Output preserved at: %s\n' "$QUICKCHECK_OUT" >&2
    exit 1
fi

if [[ ! -s "$QUICKCHECK_OUT" ]]; then
    printf 'PASS: samtools quickcheck completed with no errors.\n' >"$QUICKCHECK_OUT"
fi

"${flagstat_command[@]}" >"$FLAGSTAT_OUT"

printf 'BAM QC output details:\n'
ls -lh "$QUICKCHECK_OUT" "$FLAGSTAT_OUT"

printf 'samtools flagstat output:\n'
cat "$FLAGSTAT_OUT"
