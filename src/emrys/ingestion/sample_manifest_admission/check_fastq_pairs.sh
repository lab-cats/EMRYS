#!/usr/bin/env bash
# Real-data execution is operator-run; default regression uses generated fixtures.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh \
    --r1-fastq R1_FASTQ \
    --r2-fastq R2_FASTQ \
    [--sample-id SAMPLE_ID] \
    [--num-reads NUM_READS]

Validate that paired FASTQ files have matching read IDs and read counts.

Real-data execution is operator-run; default regression uses generated fixtures.

Required arguments:
  --r1-fastq    Path to read 1 FASTQ or FASTQ.GZ file.
  --r2-fastq    Path to read 2 FASTQ or FASTQ.GZ file.

Options:
  --sample-id   Optional sample identifier to include in output.
  --num-reads   Number of leading FASTQ records to compare; default: 20.
  -h, --help    Show this help message and exit.
USAGE
}

# shellcheck source=../../libraries/argument_parsing.sh
DIE_PREFIX="FAIL"
script_dir="${BASH_SOURCE[0]%/*}"
if [[ "$script_dir" == "$BASH_SOURCE[0]" ]]; then
    script_dir="."
fi
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"

fastq_stream() {
    local file="$1"

    if is_gzip_path "$file"; then
        gunzip -c "$file"
    else
        cat "$file"
    fi
}

sample_label() {
    if [[ -n "$sample_id" ]]; then
        printf 'Sample ID: %s\n' "$sample_id"
    fi
}

scan_fastq() {
    local file="$1"
    local limit="$2"
    local stream_status

    {
        set +e
        fastq_stream "$file"
        stream_status=$?
        printf '\n'
        exit "$stream_status"
    } | awk -v limit="$limit" '
        NR % 4 == 1 && captured < limit {
            read_id = $0
            sub(/^@/, "", read_id)
            sub(/ .*/, "", read_id)
            sub(/\/1$/, "", read_id)
            sub(/\/2$/, "", read_id)
            ids[++captured] = read_id
        }
        END {
            line_count = NR - 1
            printf "COUNT\t%.0f\n", line_count
            complete_records = int(line_count / 4)
            output_count = captured < complete_records ? captured : complete_records
            for (ordinal = 1; ordinal <= output_count; ordinal++) {
                printf "ID\t%s\n", ids[ordinal]
            }
        }
    '
}

declare_required_arguments r1_fastq r2_fastq
sample_id=""
num_reads=20

while [[ $# -gt 0 ]]; do
    case "$1" in
        --r1-fastq) assign_option_value "$1" "${2:-}" r1_fastq; shift 2 ;;
        --r2-fastq) assign_option_value "$1" "${2:-}" r2_fastq; shift 2 ;;
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --num-reads) assign_option_value "$1" "${2:-}" num_reads; shift 2 ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1. Run with --help for usage."
            ;;
    esac
done

require_arguments

[[ -f "$r1_fastq" ]] || die "R1 FASTQ does not exist or is not a file: $r1_fastq"
[[ -f "$r2_fastq" ]] || die "R2 FASTQ does not exist or is not a file: $r2_fastq"

validate_positive_integer "--num-reads" "$num_reads"

if is_gzip_path "$r1_fastq" || is_gzip_path "$r2_fastq"; then
    command -v gunzip >/dev/null 2>&1 || die "gunzip was not found on PATH but at least one FASTQ file ends in .gz."
fi

printf 'FASTQ pair check context\n'
if [[ -n "$sample_id" ]]; then
    printf '  Sample ID: %s\n' "$sample_id"
else
    printf '  Sample ID: none\n'
fi
printf '  R1 FASTQ: %s\n' "$r1_fastq"
printf '  R2 FASTQ: %s\n' "$r2_fastq"
printf '  Read IDs checked: %s\n' "$num_reads"

r1_scan="$(scan_fastq "$r1_fastq" "$num_reads")"
r2_scan="$(scan_fastq "$r2_fastq" "$num_reads")"

r1_ids=()
while IFS= read -r summary_line; do
    case "$summary_line" in
        COUNT$'\t'*) r1_line_count="${summary_line#*$'\t'}" ;;
        ID$'\t'*) r1_ids+=("${summary_line#*$'\t'}") ;;
    esac
done <<< "$r1_scan"

r2_ids=()
while IFS= read -r summary_line; do
    case "$summary_line" in
        COUNT$'\t'*) r2_line_count="${summary_line#*$'\t'}" ;;
        ID$'\t'*) r2_ids+=("${summary_line#*$'\t'}") ;;
    esac
done <<< "$r2_scan"

if (( r1_line_count % 4 != 0 )); then
    sample_label >&2
    die "R1 FASTQ line count is not divisible by 4: $r1_line_count"
fi

if (( r2_line_count % 4 != 0 )); then
    sample_label >&2
    die "R2 FASTQ line count is not divisible by 4: $r2_line_count"
fi

r1_read_count=$((r1_line_count / 4))
r2_read_count=$((r2_line_count / 4))

printf '  R1 total reads: %s\n' "$r1_read_count"
printf '  R2 total reads: %s\n' "$r2_read_count"

if (( r1_read_count < num_reads )); then
    sample_label >&2
    die "R1 FASTQ contains fewer than --num-reads records: have $r1_read_count, need $num_reads"
fi

if (( r2_read_count < num_reads )); then
    sample_label >&2
    die "R2 FASTQ contains fewer than --num-reads records: have $r2_read_count, need $num_reads"
fi

if (( r1_read_count != r2_read_count )); then
    sample_label >&2
    die "FASTQ read counts differ: R1=$r1_read_count R2=$r2_read_count"
fi

for ((record_number = 1; record_number <= num_reads; record_number++)); do
    r1_id="${r1_ids[record_number - 1]}"
    r2_id="${r2_ids[record_number - 1]}"

    if [[ "$r1_id" != "$r2_id" ]]; then
        {
            printf 'FAIL: FASTQ read IDs mismatch\n'
            if [[ -n "$sample_id" ]]; then
                printf 'Sample ID: %s\n' "$sample_id"
            fi
            printf 'Record number: %s\n' "$record_number"
            printf 'R1 normalized ID: %s\n' "$r1_id"
            printf 'R2 normalized ID: %s\n' "$r2_id"
        } >&2
        exit 1
    fi
done

printf 'PASS: FASTQ pair check succeeded for %s read IDs and matching total read counts.\n' "$num_reads"
