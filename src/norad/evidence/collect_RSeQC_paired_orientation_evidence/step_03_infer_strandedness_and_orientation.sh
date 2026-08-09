#!/usr/bin/env bash
# Step 03: infer RNA-seq library strandedness and read orientation with RSeQC.
#
# This step uses RSeQC infer_experiment.py on the canonical Step 02 sorted BAM.
# The result tells later strand-aware workflow steps whether the library behaves
# like forward-stranded, reverse-stranded, or unstranded RNA-seq data.
#
# Dry-run mode intentionally validates the requested inputs and prints the exact
# infer_experiment.py command, but does not create the output directory or run
# RSeQC. Passing --execute runs RSeQC and validates the output file.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --bed12 BED12 \
    --output-dir OUTPUT_DIR \
    [--infer-experiment-bin INFER_EXPERIMENT_BIN] \
    [--execute]

Run RSeQC infer_experiment.py on one canonical sorted BAM to infer RNA-seq
library strandedness and read orientation.

By default this script runs in dry-run mode: it validates inputs and prints the
RSeQC command without executing it. Add --execute to run infer_experiment.py.

Required arguments:
  --sample-id              Sample identifier used in output filenames.
  --input-bam              Input sorted BAM file from Step 02.
  --bed12                  BED12 annotation file for RSeQC.
  --output-dir             Directory where infer_experiment output is written.

Options:
  --infer-experiment-bin   Path or command name for infer_experiment.py.
                           Defaults to .venv/bin/infer_experiment.py when
                           present, otherwise infer_experiment.py.
  --execute                Execute RSeQC after validation. Without this,
                           dry-run only.
  -h, --help               Show this help message and exit.
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

default_infer_experiment_bin() {
    # The CSU project environment installs RSeQC in the repo virtualenv. Falling
    # back to the command name keeps the same script usable in any environment
    # where infer_experiment.py is already on PATH.
    if [[ -e ".venv/bin/infer_experiment.py" ]]; then
        printf '.venv/bin/infer_experiment.py\n'
    else
        printf 'infer_experiment.py\n'
    fi
}

sample_id=""
input_bam=""
bed12=""
output_dir=""
infer_experiment_bin="$(default_infer_experiment_bin)"
execute=false

# Parse explicit file paths instead of assuming a machine-specific directory
# layout. The SLURM wrapper supplies default cluster-validation paths.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --input-bam) assign_option_value "$1" "${2:-}" input_bam; shift 2 ;;
        --bed12) assign_option_value "$1" "${2:-}" bed12; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --infer-experiment-bin) assign_option_value "$1" "${2:-}" infer_experiment_bin; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

[[ -n "$sample_id" ]] || die "Missing required argument: --sample-id."
[[ -n "$input_bam" ]] || die "Missing required argument: --input-bam."
[[ -n "$bed12" ]] || die "Missing required argument: --bed12."
[[ -n "$output_dir" ]] || die "Missing required argument: --output-dir."

# Validate all run inputs before printing a successful dry-run. This catches
# missing Step 02 outputs and missing RSeQC setup without launching compute.
[[ -f "$input_bam" ]] || die "BAM does not exist or is not a file: $input_bam"

bam_index=""
# samtools commonly writes either sample.bam.bai or sample.bai; accept both so
# Step 03 can consume canonical BAMs from either convention.
if [[ -f "$input_bam.bai" ]]; then
    bam_index="$input_bam.bai"
elif [[ -f "${input_bam%.bam}.bai" ]]; then
    bam_index="${input_bam%.bam}.bai"
else
    die "BAM index does not exist. Expected either: $input_bam.bai or ${input_bam%.bam}.bai"
fi

[[ -f "$bed12" ]] || die "BED12 annotation does not exist or is not a file: $bed12"
infer_experiment_bin_print="$infer_experiment_bin"
infer_experiment_bin="$(resolve_executable_value "infer_experiment.py" "$infer_experiment_bin" "infer_experiment.py")"

output_file="$output_dir/${sample_id}.infer_experiment.txt"

# Report the resolved context in the same style as earlier steps so SLURM logs
# are enough to rerun or debug the command later.
mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'RSeQC infer_experiment context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input BAM: %s\n' "$input_bam"
printf '  BAM index found: %s\n' "$bam_index"
printf '  BED12 annotation: %s\n' "$bed12"
printf '  Output directory: %s\n' "$output_dir"
printf '  Output file: %s\n' "$output_file"
printf '  infer_experiment.py: %s\n' "$infer_experiment_bin_print"
printf '  Mode: %s\n' "$mode"

infer_command=(
    "$infer_experiment_bin"
    -r "$bed12"
    -i "$input_bam"
)

printf 'RSeQC infer_experiment command:\n'
print_command "${infer_command[@]}"

if [[ "$execute" != true ]]; then
    # Keep dry-runs side-effect-light: no mkdir and no placeholder output file.
    printf 'Dry-run only. Add --execute to run RSeQC infer_experiment.py.\n'
    exit 0
fi

mkdir -p "$output_dir"

# RSeQC writes its report to stdout, so redirect stdout into the stable
# downstream filename expected by the pipeline plan.
"${infer_command[@]}" >"$output_file"

[[ -s "$output_file" ]] || die "infer_experiment.py output is missing or empty: $output_file"

printf 'RSeQC infer_experiment output details:\n'
ls -lh "$output_file"

printf 'RSeQC infer_experiment output preview:\n'
sed -n '1,20p' "$output_file"
