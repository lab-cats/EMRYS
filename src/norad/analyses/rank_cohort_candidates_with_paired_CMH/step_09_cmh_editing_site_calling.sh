#!/usr/bin/env bash
# Step 09: paired CMH editing-site calling from the committed Step 08 tables.
#
# Dry-run validates the complete declared input contract and prints the exact R
# command without creating output paths or invoking R. Execute mode writes six
# run-token outputs, validates them, and publishes the summary last as the
# transaction commit marker.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bootstrap_args=("$@")
bootstrap_r_script="${STEP09_R_SCRIPT:-$script_dir/step_09_cmh_editing_site_calling.R}"
for ((i = 0; i < ${#bootstrap_args[@]}; i++)); do
    if [[ "${bootstrap_args[i]}" == --r-script && $((i + 1)) -lt "${#bootstrap_args[@]}" ]]; then
        bootstrap_r_script="${bootstrap_args[i + 1]}"
        break
    fi
done
library_dir="$script_dir/../../libraries"
if [[ ! -f "$library_dir/orientation.sh" ]] &&
    [[ -f "$bootstrap_r_script" ]]; then
    library_dir="$(cd "$(dirname "$bootstrap_r_script")/../../libraries" && pwd)"
fi
helper_dir="$script_dir"
if [[ ! -f "$helper_dir/step_09_cmh_input_parsing.sh" ]] &&
   [[ -f "$bootstrap_r_script" ]]; then
    helper_dir="$(cd "$(dirname "$bootstrap_r_script")" && pwd)"
fi

# shellcheck source=../../libraries/orientation.sh
source "$library_dir/orientation.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$library_dir/file_checks.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$library_dir/executable_resolution.sh"

for step_09_helper in \
    step_09_cmh_input_parsing.sh \
    step_09_cmh_step08_validation.sh \
    step_09_cmh_output_validation.sh \
    step_09_cmh_output_summary_validation.sh \
    step_09_cmh_execution_helpers.sh
do
    source "${helper_dir}/${step_09_helper}"
done

analysis_id=""
cohort_id=""
sample_manifest=""
partition_manifest=""
step08_root=""
output_root=""
control_condition="EV"
treatment_condition="PUM1"
rna_ref="A"
rna_alt="G"
min_sample_dp="1"
mean_dp_threshold="50"
fdr_threshold="0.05"
common_or_threshold="1.2"
absolute_difference_threshold="0.005"
background_condition=""
background_max_fraction="0.01"
rscript_bin_arg=""
r_script="${STEP09_R_SCRIPT:-$script_dir/step_09_cmh_editing_site_calling.R}"
execute=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --analysis-id) require_value "$1" "${2:-}"; analysis_id="$2"; shift 2 ;;
        --cohort-id) require_value "$1" "${2:-}"; cohort_id="$2"; shift 2 ;;
        --sample-manifest) require_value "$1" "${2:-}"; sample_manifest="$2"; shift 2 ;;
        --partition-manifest) require_value "$1" "${2:-}"; partition_manifest="$2"; shift 2 ;;
        --step08-root) require_value "$1" "${2:-}"; step08_root="$2"; shift 2 ;;
        --output-root) require_value "$1" "${2:-}"; output_root="$2"; shift 2 ;;
        --control-condition) require_value "$1" "${2:-}"; control_condition="$2"; shift 2 ;;
        --treatment-condition) require_value "$1" "${2:-}"; treatment_condition="$2"; shift 2 ;;
        --rna-ref) require_value "$1" "${2:-}"; rna_ref="$2"; shift 2 ;;
        --rna-alt) require_value "$1" "${2:-}"; rna_alt="$2"; shift 2 ;;
        --min-sample-dp) require_value "$1" "${2:-}"; min_sample_dp="$2"; shift 2 ;;
        --mean-dp-threshold) require_value "$1" "${2:-}"; mean_dp_threshold="$2"; shift 2 ;;
        --fdr-threshold) require_value "$1" "${2:-}"; fdr_threshold="$2"; shift 2 ;;
        --common-or-threshold) require_value "$1" "${2:-}"; common_or_threshold="$2"; shift 2 ;;
        --absolute-difference-threshold) require_value "$1" "${2:-}"; absolute_difference_threshold="$2"; shift 2 ;;
        --background-condition) require_value "$1" "${2:-}"; background_condition="$2"; shift 2 ;;
        --background-max-fraction) require_value "$1" "${2:-}"; background_max_fraction="$2"; shift 2 ;;
        --rscript-bin) require_value "$1" "${2:-}"; rscript_bin_arg="$2"; shift 2 ;;
        --r-script) require_value "$1" "${2:-}"; r_script="$2"; shift 2 ;;
        --execute) execute=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done

for required in analysis_id cohort_id sample_manifest partition_manifest step08_root output_root; do
    [[ -n "${!required}" ]] || die "Missing required argument: --${required//_/-}"
done
validate_safe_id "analysis_id" "$analysis_id"
validate_safe_id "cohort_id" "$cohort_id"
validate_safe_id "control_condition" "$control_condition"
validate_safe_id "treatment_condition" "$treatment_condition"
[[ "$control_condition" != "$treatment_condition" ]] ||
    die "Control and treatment conditions must differ."
if [[ -n "$background_condition" ]]; then
    validate_safe_id "background_condition" "$background_condition"
    [[ "$background_condition" != "$control_condition" &&
       "$background_condition" != "$treatment_condition" ]] ||
        die "Background condition must differ from control and treatment; EV must not be repurposed as a missing no-dox cohort."
fi
validate_base "rna_ref" "$rna_ref"
validate_base "rna_alt" "$rna_alt"
[[ "$rna_ref" != "$rna_alt" ]] || die "rna_ref and rna_alt must differ."
validate_positive_integer "min_sample_dp" "$min_sample_dp"
validate_nonnegative_number "mean_dp_threshold" "$mean_dp_threshold"
validate_probability "fdr_threshold" "$fdr_threshold"
validate_positive_number "common_or_threshold" "$common_or_threshold"
awk -v value="$common_or_threshold" 'BEGIN { exit !(value + 0 > 1) }' ||
    die "common_or_threshold must be greater than 1."
validate_closed_unit_fraction "absolute_difference_threshold" "$absolute_difference_threshold"
validate_unit_fraction "background_max_fraction" "$background_max_fraction"

validate_nonempty_file "Sample manifest" "$sample_manifest"
validate_nonempty_file "Partition manifest" "$partition_manifest"
[[ -d "$step08_root" ]] || die "Step 08 root does not exist or is not a directory: $step08_root"
validate_nonempty_file "Step 09 R script" "$r_script"

rscript_value="${rscript_bin_arg:-${RSCRIPT_BIN_OVERRIDE:-Rscript}}"
rscript_bin="$(resolve_executable_value "Rscript" "$rscript_value" "Rscript")"
sample_manifest_sha256="$(sha256_file "$sample_manifest")"
partition_manifest_sha256="$(sha256_file "$partition_manifest")"

sample_output="$(read_samples_and_validate_pairs "$sample_manifest")" ||
    die "Sample manifest pairing validation failed: $sample_manifest"
sample_ids=()
background_sample_ids=()
pair_lines=()
sample_count=""
replicate_count=""
background_sample_count=""
while IFS=$'\t' read -r kind one two three; do
    if [[ "$kind" == "S" ]]; then
        validate_safe_id "sample_id" "$one"
        sample_ids+=("$one")
    elif [[ "$kind" == "B" ]]; then
        background_sample_ids+=("$one")
    elif [[ "$kind" == "P" ]]; then
        pair_lines+=("replicate=$one control=$two treatment=$three")
    elif [[ "$kind" == "M" ]]; then
        sample_count="$one"
        replicate_count="$two"
        background_sample_count="$three"
    fi
done <<< "$sample_output"
[[ -n "$sample_count" && "${#sample_ids[@]}" -eq "$sample_count" ]] ||
    die "Could not reconcile sample manifest rows."
background_indices_csv=""
if [[ "$background_sample_count" -gt 0 ]]; then
    [[ "${#background_sample_ids[@]}" -eq "$background_sample_count" ]] ||
        die "Could not reconcile background-condition sample rows."
    for background_sample_id in "${background_sample_ids[@]}"; do
        background_index=""
        for sample_index in "${!sample_ids[@]}"; do
            if [[ "${sample_ids[$sample_index]}" == "$background_sample_id" ]]; then
                background_index=$((sample_index + 1))
                break
            fi
        done
        [[ -n "$background_index" ]] ||
            die "Could not locate background sample in manifest order: $background_sample_id"
        [[ -z "$background_indices_csv" ]] || background_indices_csv+=","
        background_indices_csv+="$background_index"
    done
fi

partition_output="$(read_partitions "$partition_manifest")" ||
    die "Partition manifest validation failed: $partition_manifest"
partition_ids=()
partition_types=()
partition_values=()
partition_rows_csv=""
partition_ids_csv=""
while IFS=$'\t' read -r partition_id selector_type selector_value; do
    validate_safe_id "partition_id" "$partition_id"
    partition_ids+=("$partition_id")
    partition_types+=("$selector_type")
    partition_values+=("$selector_value")
    [[ -z "$partition_rows_csv" ]] || partition_rows_csv+=$'\034'
    partition_rows_csv+="$partition_id"$'\035'"$selector_type"$'\035'"$selector_value"
    [[ -z "$partition_ids_csv" ]] || partition_ids_csv+=","
    partition_ids_csv+="$partition_id"
done <<< "$partition_output"
partition_count="${#partition_ids[@]}"

step08_cohort_dir="$step08_root/$cohort_id"
step08_sites="$step08_cohort_dir/$cohort_id.step08_sites.tsv"
step08_inputs="$step08_cohort_dir/$cohort_id.step08_inputs.tsv"
validate_nonempty_file "Step 08 sites table" "$step08_sites"
validate_nonempty_file "Step 08 input receipt" "$step08_inputs"
step08_sites_sha256="$(sha256_file "$step08_sites")"
step08_inputs_sha256="$(sha256_file "$step08_inputs")"

step08_sites_header='partition_id	candidate_id	orientation	chromosome	position	alt_index	genomic_ref	genomic_alt	rna_ref	rna_alt	annotation_strand	gene_ids	transcript_ids	is_cds	is_five_prime_utr	is_three_prime_utr	is_exon	is_intron	qual	filter	info_alt_depth	orientation_policy'
step08_sites_header="$(append_sample_columns "$step08_sites_header")"
step08_site_field_count=$((22 + sample_count * 3))

step08_published_count="$(validate_step08_inputs "$step08_inputs")" ||
    die "Step 08 input receipt validation failed."
validate_step08_sites "$step08_sites" "$step08_inputs"
confirm_inputs_unchanged

result_header='analysis_id	partition_id	candidate_id	orientation	chromosome	position	alt_index	genomic_ref	genomic_alt	rna_ref	rna_alt	annotation_strand	gene_ids	transcript_ids	is_cds	is_five_prime_utr	is_three_prime_utr	is_exon	is_intron	qual	filter	info_alt_depth	orientation_policy	control_condition	treatment_condition	target_rna_change	replicate_count	test_status	call_status	background_condition	background_status	min_analysis_dp	mean_analysis_dp	mean_control_af	mean_treatment_af	treatment_control_difference	max_background_af	cmh_statistic	cmh_degrees_freedom	cmh_p_value	cmh_fdr_bh	common_odds_ratio'
result_header="$(append_sample_columns "$result_header")"
result_field_count=$((42 + sample_count * 3))
summary_header='analysis_id	cohort_id	control_condition	treatment_condition	background_condition	target_rna_change	replicate_count	sample_count	candidate_count	target_candidate_count	successfully_tested_count	not_target_change_count	missing_counts_count	low_coverage_count	degenerate_table_count	below_mean_dp_count	background_not_passed_count	fdr_not_met_count	effect_not_met_count	significant_up_count	significant_down_count	sample_manifest_path	sample_manifest_sha256	partition_manifest_path	partition_manifest_sha256	step08_sites_path	step08_sites_sha256	step08_inputs_path	step08_inputs_sha256	min_sample_dp	mean_dp_threshold	fdr_threshold	common_or_threshold	absolute_difference_threshold	background_max_fraction	multiple_testing_method	cmh_alternative	continuity_correction	orientation_policy'
summary_field_count=39
mutation_header='analysis_id	rna_ref	rna_alt	mutation_type	candidate_count	candidate_fraction	successfully_tested_count	significant_up_count	significant_down_count'

analysis_dir="$output_root/$analysis_id"
final_all="$analysis_dir/$analysis_id.cmh_all_sites.tsv"
final_significant="$analysis_dir/$analysis_id.cmh_significant_sites.tsv"
final_summary="$analysis_dir/$analysis_id.cmh_summary.tsv"
final_mutation="$analysis_dir/$analysis_id.mutation_spectrum.tsv"
final_mutation_pdf="$analysis_dir/$analysis_id.mutation_spectrum.pdf"
final_depth_pdf="$analysis_dir/$analysis_id.depth_delta.pdf"
finals=("$final_all" "$final_significant" "$final_mutation" "$final_mutation_pdf" "$final_depth_pdf" "$final_summary")

run_token="${SLURM_JOB_ID:-$$}"
validate_safe_id "run token" "$run_token"
tmp_all="$analysis_dir/.$analysis_id.step09.$run_token.all.tmp.tsv"
tmp_significant="$analysis_dir/.$analysis_id.step09.$run_token.significant.tmp.tsv"
tmp_summary="$analysis_dir/.$analysis_id.step09.$run_token.summary.tmp.tsv"
tmp_mutation="$analysis_dir/.$analysis_id.step09.$run_token.mutation.tmp.tsv"
tmp_mutation_pdf="$analysis_dir/.$analysis_id.step09.$run_token.mutation.tmp.pdf"
tmp_depth_pdf="$analysis_dir/.$analysis_id.step09.$run_token.depth.tmp.pdf"
temps=("$tmp_all" "$tmp_significant" "$tmp_mutation" "$tmp_mutation_pdf" "$tmp_depth_pdf" "$tmp_summary")
backups=()
for final in "${finals[@]}"; do
    backups+=("$analysis_dir/.$(basename "$final").$run_token.previous")
done
lock_path="$analysis_dir/.$analysis_id.step09.lock"

r_command=(
    "$rscript_bin" "$r_script"
    --analysis-id "$analysis_id"
    --cohort-id "$cohort_id"
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --sample-manifest-sha256 "$sample_manifest_sha256"
    --partition-manifest-sha256 "$partition_manifest_sha256"
    --step08-sites "$step08_sites"
    --step08-inputs "$step08_inputs"
    --step08-sites-sha256 "$step08_sites_sha256"
    --step08-inputs-sha256 "$step08_inputs_sha256"
    --control-condition "$control_condition"
    --treatment-condition "$treatment_condition"
    --rna-ref "$rna_ref"
    --rna-alt "$rna_alt"
    --min-sample-dp "$min_sample_dp"
    --mean-dp-threshold "$mean_dp_threshold"
    --fdr-threshold "$fdr_threshold"
    --common-or-threshold "$common_or_threshold"
    --absolute-difference-threshold "$absolute_difference_threshold"
    --background-max-fraction "$background_max_fraction"
    --all-sites-output "$tmp_all"
    --significant-sites-output "$tmp_significant"
    --summary-output "$tmp_summary"
    --mutation-spectrum-output "$tmp_mutation"
    --mutation-spectrum-pdf-output "$tmp_mutation_pdf"
    --depth-delta-pdf-output "$tmp_depth_pdf"
)
if [[ -n "$background_condition" ]]; then
    r_command+=(--background-condition "$background_condition")
fi

printf 'Step 09 paired CMH context:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Analysis ID: %s\n' "$analysis_id"
printf '  Cohort ID: %s\n' "$cohort_id"
printf '  Samples / paired strata: %s / %s\n' "$sample_count" "$replicate_count"
printf '  Manifest-defined pairs:\n'
printf '    %s\n' "${pair_lines[@]}"
printf '  Control / treatment: %s / %s\n' "$control_condition" "$treatment_condition"
printf '  RNA change: %s>%s\n' "$rna_ref" "$rna_alt"
printf '  Step 08 sites: %s\n' "$step08_sites"
printf '  Step 08 inputs: %s\n' "$step08_inputs"
printf '  Output directory: %s\n' "$analysis_dir"
printf '  Background condition: %s\n' "${background_condition:-disabled}"
printf '  Orientation policy: legacy_provisional_v1 (provisional; not biologically validated)\n'
printf 'R command:\n'
print_command "${r_command[@]}"

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. No R process was invoked and no output path was created.\n'
    exit 0
fi

lock_owned=false
lock_owner_written=false
lock_owner_tmp="$lock_path/.owner.$run_token.tmp"
scratch_owned=false
publication_started=false
publication_committed=false
previous_set=false
pending_signal=0

trap cleanup EXIT
arm_signal_traps
mkdir -p "$analysis_dir"
# Avoid a lock-orphaning signal window between atomic acquisition and verified
# owner publication. Signals are recorded during this short critical section
# and honored immediately after ownership is fully established.
defer_signal_traps
if ! mkdir "$lock_path" 2>/dev/null; then
    arm_signal_traps
    exit_for_pending_signal
    die "Step 09 lock already exists: $lock_path"
fi
lock_owned=true
if ! printf 'run_token\t%s\npid\t%s\n' "$run_token" "$$" > "$lock_owner_tmp"; then
    arm_signal_traps
    exit_for_pending_signal
    die "Could not write Step 09 lock owner metadata: $lock_owner_tmp"
fi
if ! mv "$lock_owner_tmp" "$lock_path/owner"; then
    arm_signal_traps
    exit_for_pending_signal
    die "Could not publish Step 09 lock owner metadata: $lock_path/owner"
fi
lock_owner_written=true
arm_signal_traps
exit_for_pending_signal

for path in "${temps[@]}" "${backups[@]}"; do
    [[ ! -e "$path" ]] || die "Refusing to reuse an existing Step 09 scratch path: $path"
done
scratch_owned=true
final_count=0
for final in "${finals[@]}"; do [[ -e "$final" ]] && final_count=$((final_count + 1)); done
[[ "$final_count" -eq 0 || "$final_count" -eq 6 ]] ||
    die "Existing Step 09 outputs are incomplete; expected all six or none for analysis: $analysis_id"
[[ "$final_count" -eq 6 ]] && previous_set=true

confirm_inputs_unchanged
"${r_command[@]}" || die "Step 09 R CMH analysis failed."
confirm_inputs_unchanged
validate_outputs \
    "$tmp_all" "$tmp_significant" "$tmp_summary" "$tmp_mutation" \
    "$tmp_mutation_pdf" "$tmp_depth_pdf"
tmp_hashes=()
for temp in "${temps[@]}"; do tmp_hashes+=("$(sha256_file "$temp")"); done

publication_started=true
if [[ "$previous_set" == true ]]; then
    for index in "${!finals[@]}"; do mv "${finals[$index]}" "${backups[$index]}"; done
fi
# The summary is the commit marker and is deliberately published last.
for index in 0 1 2 3 4; do mv "${temps[$index]}" "${finals[$index]}"; done
mv "$tmp_summary" "$final_summary"
validate_outputs \
    "$final_all" "$final_significant" "$final_summary" "$final_mutation" \
    "$final_mutation_pdf" "$final_depth_pdf"
for index in "${!finals[@]}"; do
    [[ "$(sha256_file "${finals[$index]}")" == "${tmp_hashes[$index]}" ]] ||
        die "Published Step 09 output changed during publication: ${finals[$index]}"
done
publication_committed=true
for backup in "${backups[@]}"; do rm -f "$backup"; done

printf 'Step 09 execute complete. Published six-output transaction:\n'
printf '  %s\n' "${finals[@]}"
