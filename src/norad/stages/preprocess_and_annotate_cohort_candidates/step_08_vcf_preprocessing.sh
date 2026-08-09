#!/usr/bin/env bash
# Step 08: preprocess the complete, declared Step 07 cohort VCF set.
#
# Dry-run mode validates and enumerates the exact partition-manifest by
# orientation input set, prints the R command and publication plan, and creates
# no output directories, locks, temporary files, or final outputs. Execute mode
# asks the R implementation to write three run-token temporary TSVs, validates
# them, and publishes them as one rollback-protected cohort transaction.
set -euo pipefail
script_dir="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
helper_dir="${STEP08_HELPER_DIR:-$script_dir}"

usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh \
    --cohort-id COHORT_ID \
    --sample-manifest SAMPLE_MANIFEST \
    --partition-manifest PARTITION_MANIFEST \
    --step07-root STEP07_ROOT \
    --annotation-gtf ANNOTATION_GTF \
    --output-root OUTPUT_ROOT \
    --qc-root QC_ROOT \
    [--rscript-bin RSCRIPT_BIN] \
    [--r-script R_SCRIPT] \
    [--execute]

Preprocess the exact partition-manifest x {FWD_like, REV_like} Step 07 VCF
set. Inputs are constructed from the declared manifests; VCF globbing is not
used.

Required arguments:
  --cohort-id          Filename-safe cohort identifier.
  --sample-manifest    TSV containing a unique, non-empty sample_id column.
  --partition-manifest Step 07 TSV with partition_id, selector_type,
                       selector_value.
  --step07-root        Root containing <cohort>/<partition>/ Step 07 outputs.
  --annotation-gtf     Novogene GTF used for candidate annotation.
  --output-root        Root for the cohort sites table and input receipt.
  --qc-root            Root for the cohort preprocessing summary.

Options:
  --rscript-bin        Rscript executable/path. Resolution order: argument,
                       RSCRIPT_BIN_OVERRIDE, PATH.
  --r-script           R implementation (default:
                       src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.R; override with
                       STEP08_R_SCRIPT).
  --execute            Run R and publish validated outputs.
  -h, --help           Show this help message and exit.

Dry-run is the default and writes nothing. The orientation policy is fixed at
legacy_provisional_v1 and is not a biological validation claim.
USAGE
}

# shellcheck source=../../libraries/executable_resolution.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/orientation.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/orientation.sh"
# shellcheck source=../../libraries/argument_parsing.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/signal_traps.sh"

for step_08_helper in \
    step_08_step07_validation.sh \
    step_08_output_validation.sh
do
    # shellcheck source=/dev/null
    source "$helper_dir/$step_08_helper"
done

resolve_rscript() {
    local value="${rscript_bin_arg:-}"
    if [[ -z "$value" && -n "${RSCRIPT_BIN_OVERRIDE:-}" ]]; then
        value="$RSCRIPT_BIN_OVERRIDE"
    fi
    resolve_executable_value "Rscript" "$value" "Rscript"
}

confirm_input_hashes() {
    local current_sample_hash
    local current_partition_hash
    local current_annotation_hash

    current_sample_hash="$(sha256_file "$sample_manifest")"
    current_partition_hash="$(sha256_file "$partition_manifest")"
    current_annotation_hash="$(sha256_file "$annotation_gtf")"

    [[ "$current_sample_hash" == "$sample_manifest_sha256" ]] ||
        die "Sample manifest changed during Step 08: $sample_manifest"
    [[ "$current_partition_hash" == "$partition_manifest_sha256" ]] ||
        die "Partition manifest changed during Step 08: $partition_manifest"
    [[ "$current_annotation_hash" == "$annotation_gtf_sha256" ]] ||
        die "Annotation GTF changed during Step 08: $annotation_gtf"
}

declare_required_arguments \
    cohort_id sample_manifest partition_manifest step07_root \
    annotation_gtf output_root qc_root
rscript_bin_arg=""
r_script="${STEP08_R_SCRIPT:-$script_dir/step_08_vcf_preprocessing.R}"
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cohort-id) assign_option_value "$1" "${2:-}" cohort_id; shift 2 ;;
        --sample-manifest) assign_option_value "$1" "${2:-}" sample_manifest; shift 2 ;;
        --partition-manifest) assign_option_value "$1" "${2:-}" partition_manifest; shift 2 ;;
        --step07-root) assign_option_value "$1" "${2:-}" step07_root; shift 2 ;;
        --annotation-gtf) assign_option_value "$1" "${2:-}" annotation_gtf; shift 2 ;;
        --output-root) assign_option_value "$1" "${2:-}" output_root; shift 2 ;;
        --qc-root) assign_option_value "$1" "${2:-}" qc_root; shift 2 ;;
        --rscript-bin) assign_option_value "$1" "${2:-}" rscript_bin_arg; shift 2 ;;
        --r-script) assign_option_value "$1" "${2:-}" r_script; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

validate_safe_id "--cohort-id" "$cohort_id"
validate_nonempty_file "Sample manifest" "$sample_manifest"
validate_nonempty_file "Partition manifest" "$partition_manifest"
validate_nonempty_file "Annotation GTF" "$annotation_gtf"
validate_nonempty_file "Step 08 R script" "$r_script"
rscript_bin="$(resolve_rscript)"

sample_manifest_sha256="$(sha256_file "$sample_manifest")"
partition_manifest_sha256="$(sha256_file "$partition_manifest")"
annotation_gtf_sha256="$(sha256_file "$annotation_gtf")"

append_sample_id() {
    local sample_id="$1"

    sample_ids+=("$sample_id")
    validate_safe_id "sample_id" "$sample_id"
}

sample_ids=()
if ! read_manifest_sample_ids "$sample_manifest" append_sample_id; then
    die "Sample manifest validation failed: $sample_manifest"
fi
unset -f append_sample_id

[[ "${#sample_ids[@]}" -gt 0 ]] ||
    die "Sample manifest contains no sample IDs: $sample_manifest"
sample_count="${#sample_ids[@]}"
expected_samples_csv="$(IFS=,; printf '%s' "${sample_ids[*]}")"

append_partition_record() {
    local partition_id="$1"
    local selector_type="$2"
    local selector_value="$3"

    partition_ids+=("$partition_id")
    partition_types+=("$selector_type")
    partition_values+=("$selector_value")
}

partition_ids=()
partition_types=()
partition_values=()

if ! read_manifest_partitions "$partition_manifest" append_partition_record; then
    die "Partition manifest validation failed: $partition_manifest"
fi
unset -f append_partition_record

[[ "${#partition_ids[@]}" -gt 0 ]] ||
    die "Partition manifest contains no partitions: $partition_manifest"
partition_count="${#partition_ids[@]}"
expected_input_count=$((partition_count * 2))

expected_receipts=()
expected_receipt_hashes=()
expected_vcfs=()
expected_vcf_hashes=()
expected_declared_counts=()
step07_receipt_header='cohort_id	partition_id	selector_type	selector_value	orientation	vcf_path	sample_manifest_sha256	partition_manifest_sha256	sample_count	vcf_record_count'
for index in "${!partition_ids[@]}"; do
    partition_id="${partition_ids[$index]}"
    partition_dir="$step07_root/$cohort_id/$partition_id"
    receipt="$partition_dir/$cohort_id.$partition_id.step07_outputs.tsv"
    fwd_vcf="$partition_dir/$cohort_id.$partition_id.FWD_like.mpileup.vcf"
    rev_vcf="$partition_dir/$cohort_id.$partition_id.REV_like.mpileup.vcf"

    validate_nonempty_file "Step 07 receipt for partition $partition_id" "$receipt"
    validate_nonempty_file "Step 07 FWD_like VCF for partition $partition_id" "$fwd_vcf"
    validate_nonempty_file "Step 07 REV_like VCF for partition $partition_id" "$rev_vcf"

    receipt_hash_before="$(sha256_file "$receipt")"
    fwd_hash_before="$(sha256_file "$fwd_vcf")"
    rev_hash_before="$(sha256_file "$rev_vcf")"
    validate_step07_receipt_preflight \
        "$receipt" \
        "$partition_id" \
        "${partition_types[$index]}" \
        "${partition_values[$index]}" \
        "$fwd_vcf" \
        "$rev_vcf"
    receipt_hash_after="$(sha256_file "$receipt")"
    fwd_hash_after="$(sha256_file "$fwd_vcf")"
    rev_hash_after="$(sha256_file "$rev_vcf")"
    [[ "$receipt_hash_before" == "$receipt_hash_after" &&
       "$fwd_hash_before" == "$fwd_hash_after" &&
       "$rev_hash_before" == "$rev_hash_after" ]] ||
        die "Step 07 partition inputs changed during Step 08 preflight: $partition_id"

    expected_receipts+=("$receipt")
    expected_receipt_hashes+=("$receipt_hash_after")
    expected_vcfs+=("$fwd_vcf" "$rev_vcf")
    expected_vcf_hashes+=("$fwd_hash_after" "$rev_hash_after")
    expected_declared_counts+=(
        "$preflight_fwd_record_count"
        "$preflight_rev_record_count"
    )
done
confirm_input_hashes

sites_header='partition_id	candidate_id	orientation	chromosome	position	alt_index	genomic_ref	genomic_alt	rna_ref	rna_alt	annotation_strand	gene_ids	transcript_ids	is_cds	is_five_prime_utr	is_three_prime_utr	is_exon	is_intron	qual	filter	info_alt_depth	orientation_policy'
for sample_id in "${sample_ids[@]}"; do
    sites_header+=$'\t'"DP__$sample_id"
done
for sample_id in "${sample_ids[@]}"; do
    sites_header+=$'\t'"AD__$sample_id"
done
for sample_id in "${sample_ids[@]}"; do
    sites_header+=$'\t'"AF__$sample_id"
done

inputs_header='cohort_id	partition_id	selector_type	selector_value	orientation	step07_receipt_path	step07_receipt_sha256	vcf_path	vcf_sha256	sample_manifest_sha256	partition_manifest_sha256	annotation_gtf	annotation_gtf_sha256	sample_count	declared_vcf_record_count	observed_vcf_record_count	observed_alt_allele_count	supported_snv_count	skipped_symbolic_count	skipped_non_snv_count	published_candidate_count	orientation_policy'
summary_header='cohort_id	partition_count	step07_receipt_count	input_vcf_count	sample_count	observed_vcf_record_count	observed_alt_allele_count	supported_snv_count	skipped_symbolic_count	skipped_non_snv_count	published_candidate_count	sample_manifest_sha256	partition_manifest_sha256	annotation_gtf	annotation_gtf_sha256	orientation_policy'

run_token="${SLURM_JOB_ID:-$$}"
validate_safe_id "run token" "$run_token"
cohort_output_dir="$output_root/$cohort_id"

final_sites="$cohort_output_dir/$cohort_id.step08_sites.tsv"
final_inputs="$cohort_output_dir/$cohort_id.step08_inputs.tsv"
final_summary="$qc_root/$cohort_id.step08_summary.tsv"

tmp_sites="$cohort_output_dir/.$cohort_id.step08.$run_token.sites.tmp.tsv"
tmp_inputs="$cohort_output_dir/.$cohort_id.step08.$run_token.inputs.tmp.tsv"
tmp_summary="$qc_root/.$cohort_id.step08.$run_token.summary.tmp.tsv"

backup_sites="$cohort_output_dir/.$cohort_id.step08.$run_token.previous.sites.tsv"
backup_inputs="$cohort_output_dir/.$cohort_id.step08.$run_token.previous.inputs.tsv"
backup_summary="$qc_root/.$cohort_id.step08.$run_token.previous.summary.tsv"

lock_path="$cohort_output_dir/.$cohort_id.step08.lock"
lock_owner_file="$lock_path/owner"

r_command=(
    "$rscript_bin"
    "$r_script"
    --cohort-id "$cohort_id"
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --step07-root "$step07_root"
    --annotation-gtf "$annotation_gtf"
    --sample-manifest-sha256 "$sample_manifest_sha256"
    --partition-manifest-sha256 "$partition_manifest_sha256"
    --annotation-gtf-sha256 "$annotation_gtf_sha256"
    --sites-output "$tmp_sites"
    --inputs-output "$tmp_inputs"
    --summary-output "$tmp_summary"
)

printf 'Step 08 VCF preprocessing context:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Cohort ID: %s\n' "$cohort_id"
printf '  Sample manifest: %s\n' "$sample_manifest"
printf '  Sample manifest SHA-256: %s\n' "$sample_manifest_sha256"
printf '  Sample count: %s\n' "$sample_count"
printf '  Samples:\n'
printf '    %s\n' "${sample_ids[@]}"
printf '  Partition manifest: %s\n' "$partition_manifest"
printf '  Partition manifest SHA-256: %s\n' "$partition_manifest_sha256"
printf '  Partition count: %s\n' "$partition_count"
printf '  Expected Step 07 VCF count: %s\n' "$expected_input_count"
printf '  Step 07 root: %s\n' "$step07_root"
printf '  Annotation GTF: %s\n' "$annotation_gtf"
printf '  Annotation GTF SHA-256: %s\n' "$annotation_gtf_sha256"
printf '  Rscript: %s\n' "$rscript_bin"
printf '  R script: %s\n' "$r_script"
printf '  Sites table: %s\n' "$final_sites"
printf '  Input receipt: %s\n' "$final_inputs"
printf '  QC summary: %s\n' "$final_summary"
printf '  Orientation policy: legacy_provisional_v1 (provisional; not biologically validated)\n'

printf 'Declared Step 07 input set:\n'
for index in "${!partition_ids[@]}"; do
    printf '  Partition %s (%s %s):\n' \
        "${partition_ids[$index]}" "${partition_types[$index]}" "${partition_values[$index]}"
    printf '    Receipt: %s\n' "${expected_receipts[$index]}"
    vcf_index=$((index * 2))
    printf '    FWD_like VCF: %s\n' "${expected_vcfs[$vcf_index]}"
    printf '    REV_like VCF: %s\n' "${expected_vcfs[$((vcf_index + 1))]}"
done

printf 'R command:\n'
print_command "${r_command[@]}"
printf 'Planned validation:\n'
printf '  Recheck sample-manifest, partition-manifest, and annotation-GTF hashes\n'
printf '  Require exact sites, inputs, and summary TSV headers\n'
printf '  Require exactly %s Step 08 input-receipt rows\n' "$expected_input_count"
printf '  Accept a header-only sites table when counts reconcile\n'
printf 'Planned publication:\n'
printf '  Lock: %s\n' "$lock_path"
printf '  Temporary sites table: %s\n' "$tmp_sites"
printf '  Temporary input receipt: %s\n' "$tmp_inputs"
printf '  Temporary summary: %s\n' "$tmp_summary"
printf '  Publish sites, then summary, then the input receipt last as commit marker\n'
printf '  Restore a previous complete set on failure after backup begins\n'

if [[ "$execute" != true ]]; then
    printf 'Dry-run complete; no directories or files were created and R was not invoked.\n'
    exit 0
fi

mkdir -p "$cohort_output_dir" "$qc_root"

lock_acquired=false
lock_owner_written=false
scratch_owned=false
previous_final_set_present=false
backup_started=false
publication_committed=false
final_count=0

cleanup() {
    local status="$1"

    if [[ "$status" -ne 0 &&
          "$backup_started" == true &&
          "$publication_committed" != true ]]; then
        if [[ "$previous_final_set_present" == true ]]; then
            if [[ -e "$backup_sites" ]]; then
                rm -f "$final_sites" || true
                mv "$backup_sites" "$final_sites" || true
            fi
            if [[ -e "$backup_summary" ]]; then
                rm -f "$final_summary" || true
                mv "$backup_summary" "$final_summary" || true
            fi
            if [[ -e "$backup_inputs" ]]; then
                rm -f "$final_inputs" || true
                mv "$backup_inputs" "$final_inputs" || true
            fi
        else
            rm -f "$final_sites" "$final_summary" "$final_inputs" || true
        fi
    fi

    if [[ "$scratch_owned" == true ]]; then
        rm -f "$tmp_sites" "$tmp_inputs" "$tmp_summary" || true
        if [[ "$status" -eq 0 ||
              "$backup_started" != true ||
              "$previous_final_set_present" != true ||
              "$publication_committed" == true ]]; then
            rm -f "$backup_sites" "$backup_inputs" "$backup_summary" || true
        fi
    fi

    if [[ "$lock_acquired" == true ]]; then
        if [[ "$lock_owner_written" == true ]] &&
           [[ -f "$lock_owner_file" ]] &&
           grep -Fqx $'run_token\t'"$run_token" "$lock_owner_file"; then
            rm -f "$lock_owner_file" || true
            rmdir "$lock_path" 2>/dev/null || true
        elif [[ "$lock_owner_written" != true ]]; then
            rm -f "$lock_owner_file" || true
            rmdir "$lock_path" 2>/dev/null || true
        fi
    fi
}

set_exit_trap cleanup

# Avoid a stale-lock window between the atomic mkdir and owner-file write.
trap '' HUP INT TERM
if ! mkdir "$lock_path" 2>/dev/null; then
    arm_signal_traps
    die "Step 08 lock already exists: $lock_path"
fi
lock_acquired=true
if ! printf 'run_token\t%s\npid\t%s\n' "$run_token" "$$" > "$lock_owner_file"; then
    arm_signal_traps
    die "Could not write Step 08 lock owner file: $lock_owner_file"
fi
lock_owner_written=true

for owned_path in \
    "$tmp_sites" "$tmp_inputs" "$tmp_summary" \
    "$backup_sites" "$backup_inputs" "$backup_summary"
do
    if [[ -e "$owned_path" ]]; then
        arm_signal_traps
        die "Refusing to reuse an existing Step 08 scratch path: $owned_path"
    fi
done
scratch_owned=true
arm_signal_traps

# Inspect stable state only while holding the cohort lock. The input receipt is
# the commit marker, so a stable output set must contain all three files or none.
[[ -e "$final_sites" ]] && final_count=$((final_count + 1))
[[ -e "$final_inputs" ]] && final_count=$((final_count + 1))
[[ -e "$final_summary" ]] && final_count=$((final_count + 1))
if [[ "$final_count" -ne 0 && "$final_count" -ne 3 ]]; then
    die "Existing Step 08 outputs are incomplete; expected all three or none for cohort: $cohort_id"
fi

confirm_input_hashes
if ! "${r_command[@]}"; then
    die "Step 08 R VCF preprocessing failed."
fi
confirm_input_hashes

validate_output_tables "$tmp_sites" "$tmp_inputs" "$tmp_summary"
tmp_sites_sha256="$(sha256_file "$tmp_sites")"
tmp_inputs_sha256="$(sha256_file "$tmp_inputs")"
tmp_summary_sha256="$(sha256_file "$tmp_summary")"

if [[ "$final_count" -eq 3 ]]; then
    previous_final_set_present=true
    backup_started=true
    mv "$final_sites" "$backup_sites"
    mv "$final_summary" "$backup_summary"
    mv "$final_inputs" "$backup_inputs"
else
    backup_started=true
fi

mv "$tmp_sites" "$final_sites"
mv "$tmp_summary" "$final_summary"
# The input receipt is the transaction commit marker and is deliberately last.
mv "$tmp_inputs" "$final_inputs"

validate_output_tables "$final_sites" "$final_inputs" "$final_summary"
[[ "$(sha256_file "$final_sites")" == "$tmp_sites_sha256" ]] ||
    die "Published Step 08 sites table changed during publication."
[[ "$(sha256_file "$final_inputs")" == "$tmp_inputs_sha256" ]] ||
    die "Published Step 08 input receipt changed during publication."
[[ "$(sha256_file "$final_summary")" == "$tmp_summary_sha256" ]] ||
    die "Published Step 08 summary changed during publication."
confirm_input_hashes

publication_committed=true
rm -f "$backup_sites" "$backup_inputs" "$backup_summary"

printf 'Step 08 execute complete.\n'
printf 'Published sites table: %s\n' "$final_sites"
printf 'Published input receipt: %s\n' "$final_inputs"
printf 'Published QC summary: %s\n' "$final_summary"
