#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Record RSeQC strandedness evidence for one BAM.

Usage: src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
  --sample-id SAMPLE_ID \
  --input-bam INPUT_BAM \
  --bed12 BED12 \
  --output-dir OUTPUT_DIR \
  [--infer-experiment-bin INFER_EXPERIMENT_BIN]

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

declare_required_arguments sample_id input_bam bed12 output_dir
infer_experiment_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --bed12) assign_option_value "$1" "${2:-}" bed12; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --infer-experiment-bin) assign_option_value "$1" "${2:-}" infer_experiment_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

validate_safe_id "--sample-id" "$sample_id"
validate_nonempty_file "Input BAM" "$input_bam"
validate_nonempty_file "BED12" "$bed12"
[[ -s "$input_bam.bai" || -s "${input_bam%.bam}.bai" ]] || die "BAM index is missing: $input_bam"
if [[ -z "$infer_experiment_bin" && -x .venv/bin/infer_experiment.py ]]; then
    infer_experiment_bin=.venv/bin/infer_experiment.py
fi
infer_experiment_bin="$(resolve_executable_value "RSeQC infer_experiment.py" "$infer_experiment_bin" "infer_experiment.py")"
output="$output_dir/$sample_id.infer_experiment.txt"
"$infer_experiment_bin" -r "$bed12" -i "$input_bam" >"$output"
validate_nonempty_file "RSeQC orientation evidence" "$output"
