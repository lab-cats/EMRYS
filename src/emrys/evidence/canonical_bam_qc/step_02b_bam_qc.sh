#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Record samtools quickcheck and flagstat evidence for one BAM.

Usage: src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
  --sample-id SAMPLE_ID \
  --bam BAM \
  --output-dir OUTPUT_DIR \
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

declare_required_arguments sample_id bam output_dir
samtools_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --bam) assign_option_value "$1" "${2:-}" bam; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

validate_safe_id "--sample-id" "$sample_id"
validate_nonempty_file "BAM" "$bam"
[[ -s "$bam.bai" || -s "${bam%.bam}.bai" ]] || die "BAM index is missing: $bam"
samtools_bin="$(resolve_executable_value "samtools" "$samtools_bin" "samtools")"
quickcheck="$output_dir/$sample_id.quickcheck.txt"
flagstat="$output_dir/$sample_id.flagstat.txt"
if ! "$samtools_bin" quickcheck -v "$bam" >"$quickcheck" 2>&1; then
    cat "$quickcheck" >&2
    die "samtools quickcheck failed: $bam"
fi
if [[ ! -s "$quickcheck" ]]; then
    printf 'PASS: samtools quickcheck completed with no errors.\n' >"$quickcheck"
fi
"$samtools_bin" flagstat "$bam" >"$flagstat"
validate_nonempty_file "quickcheck report" "$quickcheck"
validate_nonempty_file "flagstat report" "$flagstat"
