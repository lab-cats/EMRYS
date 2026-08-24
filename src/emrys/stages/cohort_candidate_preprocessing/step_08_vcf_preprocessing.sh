#!/usr/bin/env bash
# Step 08: preprocess the complete, declared Step 07 cohort VCF set.
#
# Dry-run mode validates and enumerates the exact partition-manifest by
# orientation input set, prints the R command and publication plan, and creates
# no output directories, locks, temporary files, or final outputs. Execute mode
# asks the R implementation to write three run-token temporary TSVs, validates
# them, and publishes them as one rollback-protected cohort transaction.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.sh \
    --cohort-id COHORT_ID \
    --sample-manifest SAMPLE_MANIFEST \
    --partition-manifest PARTITION_MANIFEST \
    --step07-root STEP07_ROOT \
    --annotation-gtf ANNOTATION_GTF \
    --output-root OUTPUT_ROOT \
    --qc-root QC_ROOT \
    [--threads THREADS] \
    [--rscript-bin RSCRIPT_BIN] \
    [--r-script R_SCRIPT] \
    [--no-clobber] \
    [--execute]

Preprocess the exact partition-manifest x {FWD_like, REV_like} Step 07 VCF
set. Inputs are constructed from the declared manifests; VCF globbing is not
used.

Required arguments:
  --cohort-id          Filename-safe cohort identifier.
  --sample-manifest    Paired local-CMH TSV: sample_id, r1_fastq, r2_fastq,
                       strandedness, condition, replicate[, notes].
  --partition-manifest Step 07 TSV with partition_id, selector_type,
                       selector_value.
  --step07-root        Root containing <cohort>/<partition>/ Step 07 outputs.
  --annotation-gtf     Novogene GTF used for candidate annotation.
  --output-root        Root for the cohort sites table and input receipt.
  --qc-root            Root for the cohort preprocessing summary.

Options:
  --threads            Maximum concurrent partition/orientation workers;
                       positive integer (default: 1).
  --rscript-bin        Rscript executable/path. Resolution order: argument,
                       RSCRIPT_BIN_OVERRIDE, PATH.
  --r-script           R implementation (default:
                       src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R; override with
                       STEP08_R_SCRIPT).
  --no-clobber         Refuse to replace an existing complete output set.
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

validate_paired_sample_manifest() {
    local path="$1"
    local header
    local required_header
    local allowed_header
    local expected_fields

    required_header=$'sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate'
    allowed_header="$required_header"$'\tnotes'
    IFS= read -r header <"$path" ||
        die "Sample manifest has no readable header: $path"
    case "$header" in
        "$required_header") expected_fields=6 ;;
        "$allowed_header") expected_fields=7 ;;
        *)
            die "Sample manifest must have the exact paired local-CMH schema, with optional notes as the final column."
            ;;
    esac

    awk -F '\t' -v expected_fields="$expected_fields" '
        NR == 1 { next }
        {
            if (NF != expected_fields) {
                printf "Sample manifest row %d has %d fields; expected %d.\n",
                    NR, NF, expected_fields > "/dev/stderr"
                failed = 1
                exit
            }
            for (field = 1; field <= 6; field++) {
                if ($field == "" || $field == "NA") {
                    printf "Sample manifest row %d has an empty required value.\n",
                        NR > "/dev/stderr"
                    failed = 1
                    exit
                }
            }
            if ($1 !~ /^[A-Za-z0-9][A-Za-z0-9._-]*$/) {
                printf "sample_id must match [A-Za-z0-9][A-Za-z0-9._-]*; got: %s\n",
                    $1 > "/dev/stderr"
                failed = 1
                exit
            }
            if ($6 !~ /^[A-Za-z0-9][A-Za-z0-9._-]*$/) {
                printf "replicate must match [A-Za-z0-9][A-Za-z0-9._-]*; got: %s\n",
                    $6 > "/dev/stderr"
                failed = 1
                exit
            }
            if ($4 != "forward" && $4 != "reverse" &&
                $4 != "unstranded" && $4 != "unknown") {
                printf "Sample manifest row %d has invalid strandedness: %s\n",
                    NR, $4 > "/dev/stderr"
                failed = 1
                exit
            }
            if (seen[$1]++) {
                printf "Sample manifest contains duplicate sample_id: %s\n",
                    $1 > "/dev/stderr"
                failed = 1
                exit
            }
            rows++
        }
        END {
            if (failed) exit 1
            if (rows == 0) {
                print "Sample manifest contains no sample rows." > "/dev/stderr"
                exit 1
            }
        }
    ' "$path" ||
        die "Sample manifest validation failed: $path"
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

validate_step07_vcf_preflight() {
    local label="$1"
    local path="$2"
    local declared_count="$3"
    local observed_count

    awk -F '\t' -v expected_samples="$expected_samples_csv" '
        BEGIN {
            sample_count = split(expected_samples, samples, ",")
        }
        /^#CHROM/ {
            header_count++
            if (NF != 9 + sample_count ||
                $1 != "#CHROM" || $2 != "POS" || $3 != "ID" ||
                $4 != "REF" || $5 != "ALT" || $6 != "QUAL" ||
                $7 != "FILTER" || $8 != "INFO" || $9 != "FORMAT") {
                invalid = 1
            }
            for (sample_index = 1;
                 sample_index <= sample_count;
                 sample_index++) {
                if ($(9 + sample_index) != samples[sample_index]) invalid = 1
            }
        }
        END {
            if (header_count != 1 || invalid) exit 1
        }
    ' "$path" ||
        die "$label VCF header or sample order is invalid: $path"

    grep -q '^##INFO=<ID=AD,' "$path" ||
        die "$label VCF is missing the INFO/AD definition: $path"
    grep -q '^##FORMAT=<ID=DP,' "$path" ||
        die "$label VCF is missing the FORMAT/DP definition: $path"
    grep -q '^##FORMAT=<ID=AD,' "$path" ||
        die "$label VCF is missing the FORMAT/AD definition: $path"

    if ! observed_count="$(awk '
        /^#/ { next }
        /^[[:space:]]*$/ { invalid = 1; next }
        { count++ }
        END {
            if (invalid) exit 1
            print count + 0
        }
    ' "$path")"; then
        die "$label VCF contains a blank data row: $path"
    fi
    [[ "$observed_count" == "$declared_count" ]] ||
        die "$label VCF record count does not match its Step 07 receipt; declared $declared_count, observed $observed_count: $path"
}

validate_step07_receipt_preflight() {
    local path="$1"
    local partition_id="$2"
    local selector_type="$3"
    local selector_value="$4"
    local fwd_vcf="$5"
    local rev_vcf="$6"
    local row_count
    local fwd_line
    local rev_line
    local fwd_cohort fwd_partition fwd_type fwd_value fwd_orientation
    local fwd_path fwd_sample_hash fwd_partition_hash fwd_samples fwd_records
    local rev_cohort rev_partition rev_type rev_value rev_orientation
    local rev_path rev_sample_hash rev_partition_hash rev_samples rev_records

    validate_exact_header \
        "Step 07 receipt for partition $partition_id" \
        "$path" \
        "$step07_receipt_header"
    awk -F '\t' 'NF != 10 { exit 1 }' "$path" ||
        die "Step 07 receipt must contain exactly 10 fields per row: $path"
    row_count="$(awk 'END { print NR - 1 }' "$path")"
    [[ "$row_count" == "2" ]] ||
        die "Step 07 receipt must contain exactly two data rows: $path"

    fwd_line="$(sed -n '2p' "$path")"
    rev_line="$(sed -n '3p' "$path")"
    IFS=$'\t' read -r \
        fwd_cohort fwd_partition fwd_type fwd_value fwd_orientation \
        fwd_path fwd_sample_hash fwd_partition_hash fwd_samples fwd_records \
        <<< "$fwd_line"
    IFS=$'\t' read -r \
        rev_cohort rev_partition rev_type rev_value rev_orientation \
        rev_path rev_sample_hash rev_partition_hash rev_samples rev_records \
        <<< "$rev_line"

    [[ "$fwd_cohort" == "$cohort_id" &&
       "$rev_cohort" == "$cohort_id" &&
       "$fwd_partition" == "$partition_id" &&
       "$rev_partition" == "$partition_id" &&
       "$fwd_type" == "$selector_type" &&
       "$rev_type" == "$selector_type" &&
       "$fwd_value" == "$selector_value" &&
       "$rev_value" == "$selector_value" ]] ||
        die "Step 07 receipt cohort, partition, or selector mismatch: $path"
    [[ "$fwd_orientation" == "${ORIENTATIONS[0]}" &&
       "$rev_orientation" == "${ORIENTATIONS[1]}" ]] ||
        die "Step 07 receipt orientations must be FWD_like then REV_like: $path"
    [[ -e "$fwd_path" && -e "$rev_path" &&
       "$fwd_path" -ef "$fwd_vcf" &&
       "$rev_path" -ef "$rev_vcf" ]] ||
        die "Step 07 receipt VCF path mismatch: $path"
    [[ "$fwd_sample_hash" == "$sample_manifest_sha256" &&
       "$rev_sample_hash" == "$sample_manifest_sha256" &&
       "$fwd_partition_hash" == "$partition_manifest_sha256" &&
       "$rev_partition_hash" == "$partition_manifest_sha256" ]] ||
        die "Step 07 receipt manifest hash mismatch: $path"
    [[ "$fwd_samples" == "$sample_count" &&
       "$rev_samples" == "$sample_count" ]] ||
        die "Step 07 receipt sample count mismatch: $path"
    validate_nonnegative_integer \
        "Step 07 FWD_like declared record count" "$fwd_records"
    validate_nonnegative_integer \
        "Step 07 REV_like declared record count" "$rev_records"

    validate_step07_vcf_preflight \
        "Step 07 FWD_like" "$fwd_vcf" "$fwd_records"
    validate_step07_vcf_preflight \
        "Step 07 REV_like" "$rev_vcf" "$rev_records"

    preflight_fwd_record_count="$fwd_records"
    preflight_rev_record_count="$rev_records"
}

confirm_step07_input_hashes() {
    local index
    local current_hash

    for index in "${!expected_receipts[@]}"; do
        current_hash="$(sha256_file "${expected_receipts[$index]}")"
        [[ "$current_hash" == "${expected_receipt_hashes[$index]}" ]] ||
            die "Step 07 receipt changed during Step 08: ${expected_receipts[$index]}"
    done
    for index in "${!expected_vcfs[@]}"; do
        current_hash="$(sha256_file "${expected_vcfs[$index]}")"
        [[ "$current_hash" == "${expected_vcf_hashes[$index]}" ]] ||
            die "Step 07 VCF changed during Step 08: ${expected_vcfs[$index]}"
    done
}

validate_output_tables() {
    local sites_path="$1"
    local inputs_path="$2"
    local summary_path="$3"
    local inputs_row_count
    local summary_row_count
    local sites_row_count
    local sites_field_count
    local partition_csv
    local partition_index
    local orientation_index
    local row_number
    local input_line
    local expected_orientation
    local vcf_index
    local current_receipt_hash
    local current_vcf_hash
    local i_cohort i_partition i_selector_type i_selector_value i_orientation
    local i_receipt_path i_receipt_hash i_vcf_path i_vcf_hash
    local i_sample_hash i_partition_hash i_annotation i_annotation_hash
    local i_sample_count i_declared i_observed i_alt i_supported
    local i_symbolic i_non_snv i_published i_policy
    local total_observed=0
    local total_alt=0
    local total_supported=0
    local total_symbolic=0
    local total_non_snv=0
    local total_published=0
    local summary_line
    local s_cohort s_partition_count s_receipt_count s_input_count
    local s_sample_count s_observed s_alt s_supported s_symbolic s_non_snv
    local s_published s_sample_hash s_partition_hash s_annotation
    local s_annotation_hash s_policy
    local summary_count

    confirm_step07_input_hashes
    validate_exact_header "Step 08 sites table" "$sites_path" "$sites_header"
    validate_exact_header "Step 08 input receipt" "$inputs_path" "$inputs_header"
    validate_exact_header "Step 08 summary" "$summary_path" "$summary_header"

    sites_field_count=$((22 + sample_count * 3))
    awk -F '\t' -v expected="$sites_field_count" '
        NF != expected { exit 1 }
    ' "$sites_path" ||
        die "Step 08 sites table contains a row with an invalid field count: $sites_path"
    awk -F '\t' 'NF != 22 { exit 1 }' "$inputs_path" ||
        die "Step 08 input receipt contains a row with an invalid field count: $inputs_path"
    awk -F '\t' 'NF != 16 { exit 1 }' "$summary_path" ||
        die "Step 08 summary contains a row with an invalid field count: $summary_path"

    inputs_row_count="$(awk 'END { print (NR > 0 ? NR - 1 : 0) }' "$inputs_path")"
    [[ "$inputs_row_count" == "$expected_input_count" ]] ||
        die "Step 08 input receipt must contain $expected_input_count data rows; got $inputs_row_count: $inputs_path"

    summary_row_count="$(awk 'END { print (NR > 0 ? NR - 1 : 0) }' "$summary_path")"
    [[ "$summary_row_count" == "1" ]] ||
        die "Step 08 summary must contain exactly one data row; got $summary_row_count: $summary_path"

    row_number=2
    for partition_index in "${!partition_ids[@]}"; do
        for orientation_index in "${!ORIENTATIONS[@]}"; do
            expected_orientation="${ORIENTATIONS[$orientation_index]}"
            vcf_index=$((partition_index * 2 + orientation_index))
            input_line="$(sed -n "${row_number}p" "$inputs_path")"
            IFS=$'\t' read -r \
                i_cohort i_partition i_selector_type i_selector_value \
                i_orientation i_receipt_path i_receipt_hash i_vcf_path \
                i_vcf_hash i_sample_hash i_partition_hash i_annotation \
                i_annotation_hash i_sample_count i_declared i_observed \
                i_alt i_supported i_symbolic i_non_snv i_published i_policy \
                <<< "$input_line"

            current_receipt_hash="$(
                sha256_file "${expected_receipts[$partition_index]}"
            )"
            current_vcf_hash="$(sha256_file "${expected_vcfs[$vcf_index]}")"
            [[ "$i_cohort" == "$cohort_id" &&
               "$i_partition" == "${partition_ids[$partition_index]}" &&
               "$i_selector_type" == "${partition_types[$partition_index]}" &&
               "$i_selector_value" == "${partition_values[$partition_index]}" &&
               "$i_orientation" == "$expected_orientation" ]] ||
                die "Step 08 input receipt row $row_number does not match manifest partition/orientation order."
            [[ "$i_receipt_path" == "${expected_receipts[$partition_index]}" &&
               "$i_vcf_path" == "${expected_vcfs[$vcf_index]}" ]] ||
                die "Step 08 input receipt row $row_number contains an unexpected Step 07 path."
            [[ "$i_receipt_hash" == "$current_receipt_hash" &&
               "$i_receipt_hash" == "${expected_receipt_hashes[$partition_index]}" &&
               "$i_vcf_hash" == "$current_vcf_hash" &&
               "$i_vcf_hash" == "${expected_vcf_hashes[$vcf_index]}" ]] ||
                die "Step 08 input receipt row $row_number contains a stale or invalid Step 07 hash."
            [[ "$i_sample_hash" == "$sample_manifest_sha256" &&
               "$i_partition_hash" == "$partition_manifest_sha256" &&
               "$i_annotation" == "$annotation_gtf" &&
               "$i_annotation_hash" == "$annotation_gtf_sha256" &&
               "$i_policy" == "$ORIENTATION_POLICY" &&
               "$i_sample_count" == "$sample_count" ]] ||
                die "Step 08 input receipt row $row_number contains invalid manifest, annotation, sample-count, or policy metadata."

            validate_nonnegative_integer \
                "Step 08 declared VCF record count" "$i_declared"
            validate_nonnegative_integer \
                "Step 08 observed VCF record count" "$i_observed"
            validate_nonnegative_integer \
                "Step 08 observed alternate-allele count" "$i_alt"
            validate_nonnegative_integer \
                "Step 08 supported SNV count" "$i_supported"
            validate_nonnegative_integer \
                "Step 08 skipped symbolic count" "$i_symbolic"
            validate_nonnegative_integer \
                "Step 08 skipped non-SNV count" "$i_non_snv"
            validate_nonnegative_integer \
                "Step 08 published candidate count" "$i_published"
            [[ "$i_declared" == "${expected_declared_counts[$vcf_index]}" &&
               "$i_declared" == "$i_observed" ]] ||
                die "Step 08 input receipt row $row_number does not reconcile declared and observed VCF records."
            [[ $((10#$i_alt)) -eq \
               $((10#$i_supported + 10#$i_symbolic + 10#$i_non_snv)) ]] ||
                die "Step 08 input receipt row $row_number does not reconcile expanded, supported, and skipped allele counts."
            [[ "$i_published" == "$i_supported" ]] ||
                die "Step 08 input receipt row $row_number does not reconcile supported and published candidate counts."

            total_observed=$((total_observed + 10#$i_observed))
            total_alt=$((total_alt + 10#$i_alt))
            total_supported=$((total_supported + 10#$i_supported))
            total_symbolic=$((total_symbolic + 10#$i_symbolic))
            total_non_snv=$((total_non_snv + 10#$i_non_snv))
            total_published=$((total_published + 10#$i_published))
            row_number=$((row_number + 1))
        done
    done

    partition_csv="$(IFS=,; printf '%s' "${partition_ids[*]}")"
    awk -F '\t' \
        -v partitions="$partition_csv" \
        -v orientation_fwd="${ORIENTATIONS[0]}" \
        -v orientation_rev="${ORIENTATIONS[1]}" \
        -v orientation_policy="$ORIENTATION_POLICY" '
        BEGIN {
            count = split(partitions, values, ",")
            for (partition_index = 1;
                 partition_index <= count;
                 partition_index++) {
                valid[values[partition_index]] = 1
            }
        }
        NR > 1 {
            if (!($1 in valid) || $2 == "" || seen[$2]++ ||
                ($3 != orientation_fwd && $3 != orientation_rev) ||
                $5 !~ /^[1-9][0-9]*$/ ||
                $6 !~ /^[1-9][0-9]*$/ ||
                $22 != orientation_policy) {
                exit 1
            }
        }
    ' "$sites_path" ||
        die "Step 08 sites table contains an invalid partition, duplicate candidate ID, orientation, coordinate, ALT index, or policy: $sites_path"
    sites_row_count="$(awk 'END { print NR - 1 }' "$sites_path")"
    [[ "$sites_row_count" == "$total_published" ]] ||
        die "Step 08 sites row count does not equal the published-candidate total."

    summary_line="$(sed -n '2p' "$summary_path")"
    IFS=$'\t' read -r \
        s_cohort s_partition_count s_receipt_count s_input_count \
        s_sample_count s_observed s_alt s_supported s_symbolic s_non_snv \
        s_published s_sample_hash s_partition_hash s_annotation \
        s_annotation_hash s_policy \
        <<< "$summary_line"
    for summary_count in \
        "$s_partition_count" "$s_receipt_count" "$s_input_count" \
        "$s_sample_count" "$s_observed" "$s_alt" "$s_supported" \
        "$s_symbolic" "$s_non_snv" "$s_published"
    do
        validate_nonnegative_integer \
            "Step 08 summary count" "$summary_count"
    done
    [[ "$s_cohort" == "$cohort_id" &&
       "$s_partition_count" == "$partition_count" &&
       "$s_receipt_count" == "$partition_count" &&
       "$s_input_count" == "$expected_input_count" &&
       "$s_sample_count" == "$sample_count" &&
       "$s_observed" == "$total_observed" &&
       "$s_alt" == "$total_alt" &&
       "$s_supported" == "$total_supported" &&
       "$s_symbolic" == "$total_symbolic" &&
       "$s_non_snv" == "$total_non_snv" &&
       "$s_published" == "$total_published" &&
       "$s_published" == "$sites_row_count" &&
       "$s_sample_hash" == "$sample_manifest_sha256" &&
       "$s_partition_hash" == "$partition_manifest_sha256" &&
       "$s_annotation" == "$annotation_gtf" &&
       "$s_annotation_hash" == "$annotation_gtf_sha256" &&
       "$s_policy" == "$ORIENTATION_POLICY"
    ]] ||
        die "Step 08 summary does not exactly reconcile its declared inputs and published sites."
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

declare_required_arguments \
    cohort_id sample_manifest partition_manifest step07_root \
    annotation_gtf output_root qc_root
requested_rscript_bin=""
r_script="${STEP08_R_SCRIPT:-$script_dir/step_08_vcf_preprocessing.R}"
threads=1
no_clobber=false
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
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --rscript-bin) assign_option_value "$1" "${2:-}" requested_rscript_bin; shift 2 ;;
        --r-script) assign_option_value "$1" "${2:-}" r_script; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

validate_safe_id "--cohort-id" "$cohort_id"
validate_nonempty_file "Sample manifest" "$sample_manifest"
validate_paired_sample_manifest "$sample_manifest"
validate_nonempty_file "Partition manifest" "$partition_manifest"
validate_nonempty_file "Annotation GTF" "$annotation_gtf"
validate_nonempty_file "Step 08 R script" "$r_script"
validate_positive_integer "--threads" "$threads"
rscript_bin="$(resolve_overridable_executable \
    "Rscript" "$requested_rscript_bin" RSCRIPT_BIN_OVERRIDE Rscript)"

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

run_token="${EMRYS_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
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
validation_report="$qc_root/$cohort_id.step08_validation.tsv"
validator_command=(
    .venv/bin/python -X pycache_prefix=/dev/null -I -m emrys
    validate cohort-candidate-preprocessing
    --cohort-id "$cohort_id"
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --annotation-gtf "$annotation_gtf"
    --sites "$final_sites"
    --inputs "$final_inputs"
    --summary "$final_summary"
    --output "$validation_report"
    --execute
)
all_pass_command=(
    .venv/bin/python -X pycache_prefix=/dev/null -I -m emrys
    validate all-pass
    --report "$validation_report"
    --step-id 08
    --scope-id "$cohort_id"
)

r_command=("$rscript_bin")
if [[ "${EMRYS_LOCAL_PILOT_R:-0}" == 1 ]]; then
    r_command+=(--no-environ --no-site-file --no-restore --no-save)
fi
r_command+=(
    "$r_script"
    --cohort-id "$cohort_id"
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --step07-root "$step07_root"
    --annotation-gtf "$annotation_gtf"
    --sample-manifest-sha256 "$sample_manifest_sha256"
    --partition-manifest-sha256 "$partition_manifest_sha256"
    --annotation-gtf-sha256 "$annotation_gtf_sha256"
    --threads "$threads"
    --sites-output "$tmp_sites"
    --inputs-output "$tmp_inputs"
    --summary-output "$tmp_summary"
)

printf 'Step 08 VCF preprocessing context:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Run token: %s\n' "$run_token"
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
printf '  Threads: %s\n' "$threads"
printf '  Rscript: %s\n' "$rscript_bin"
printf '  R script: %s\n' "$r_script"
printf '  Sites table: %s\n' "$final_sites"
printf '  Input receipt: %s\n' "$final_inputs"
printf '  QC summary: %s\n' "$final_summary"
printf '  Existing-output policy: %s\n' \
    "$([[ "$no_clobber" == true ]] && printf no-clobber || printf replace-complete-set)"
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
printf 'Post-execution validator command:\n'
print_command "${validator_command[@]}"
printf 'Semantic all-pass gate:\n'
print_command "${all_pass_command[@]}"

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Step 08" "$cohort_output_dir" ".${cohort_id}.step08.*"
    require_no_owner_residue \
        "Step 08" "$qc_root" ".${cohort_id}.step08.*"
fi

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

release_owned_lock() {
    local unexpected

    [[ "$lock_acquired" == true ]] || return 0
    if [[ "$lock_owner_written" != true || ! -f "$lock_owner_file" ]]; then
        printf 'ERROR: Step 08 cannot prove lock ownership for release: %s\n' \
            "$lock_path" >&2
        return 1
    fi
    if ! grep -Fqx $'run_token\t'"$run_token" "$lock_owner_file"; then
        printf 'ERROR: Step 08 lock owner changed; preserving lock: %s\n' \
            "$lock_path" >&2
        return 1
    fi
    unexpected="$(
        find "$lock_path" -mindepth 1 -maxdepth 1 \
            ! -path "$lock_owner_file" -print -quit
    )" || {
        printf 'ERROR: Could not inspect Step 08 lock: %s\n' "$lock_path" >&2
        return 1
    }
    if [[ -n "$unexpected" ]]; then
        printf 'ERROR: Step 08 lock contains unexpected residue; preserving it: %s\n' \
            "$unexpected" >&2
        return 1
    fi
    rm -f "$lock_owner_file"
    if ! rmdir "$lock_path" 2>/dev/null; then
        if [[ ! -e "$lock_owner_file" && -d "$lock_path" ]]; then
            (set -o noclobber; printf 'run_token\t%s\npid\t%s\n' "$run_token" "$$" > "$lock_owner_file") \
                2>/dev/null || true
        fi
        printf 'ERROR: Could not remove Step 08 lock directory; preserving residue: %s\n' \
            "$lock_path" >&2
        return 1
    fi
    lock_acquired=false
}

cleanup() {
    local status="$1"
    local rollback_failed=false

    if [[ "$status" -ne 0 &&
          "$backup_started" == true &&
          "$publication_committed" != true ]]; then
        if [[ "$no_clobber" == true ]]; then
            remove_owned_published_file \
                "Step 08 sites" "$tmp_sites" "$final_sites" || rollback_failed=true
            remove_owned_published_file \
                "Step 08 summary" "$tmp_summary" "$final_summary" || rollback_failed=true
            remove_owned_published_file \
                "Step 08 input receipt" "$tmp_inputs" "$final_inputs" || rollback_failed=true
        elif [[ "$previous_final_set_present" == true ]]; then
            if [[ -e "$backup_sites" ]]; then
                if ! rm -f "$final_sites"; then
                    printf 'ERROR: Could not clear Step 08 sites output before restore: %s\n' \
                        "$final_sites" >&2
                    rollback_failed=true
                elif ! mv "$backup_sites" "$final_sites"; then
                    printf 'ERROR: Could not restore Step 08 sites backup: %s\n' \
                        "$backup_sites" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "$final_sites" ]]; then
                printf 'ERROR: Step 08 rollback found neither sites final nor backup.\n' >&2
                rollback_failed=true
            fi
            if [[ -e "$backup_summary" ]]; then
                if ! rm -f "$final_summary"; then
                    printf 'ERROR: Could not clear Step 08 summary before restore: %s\n' \
                        "$final_summary" >&2
                    rollback_failed=true
                elif ! mv "$backup_summary" "$final_summary"; then
                    printf 'ERROR: Could not restore Step 08 summary backup: %s\n' \
                        "$backup_summary" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "$final_summary" ]]; then
                printf 'ERROR: Step 08 rollback found neither summary final nor backup.\n' >&2
                rollback_failed=true
            fi
            if [[ -e "$backup_inputs" ]]; then
                if ! rm -f "$final_inputs"; then
                    printf 'ERROR: Could not clear Step 08 input receipt before restore: %s\n' \
                        "$final_inputs" >&2
                    rollback_failed=true
                elif ! mv "$backup_inputs" "$final_inputs"; then
                    printf 'ERROR: Could not restore Step 08 input-receipt backup: %s\n' \
                        "$backup_inputs" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "$final_inputs" ]]; then
                printf 'ERROR: Step 08 rollback found neither input-receipt final nor backup.\n' >&2
                rollback_failed=true
            fi
        else
            if ! rm -f "$final_sites" "$final_summary" "$final_inputs"; then
                printf 'ERROR: Could not remove partially published Step 08 outputs.\n' >&2
                rollback_failed=true
            fi
        fi
    fi

    if [[ "$scratch_owned" == true &&
          ( "$rollback_failed" != true || "$no_clobber" != true ) ]]; then
        rm -f "$tmp_sites" "$tmp_inputs" "$tmp_summary" || true
        if [[ "$rollback_failed" != true ]] &&
           [[ "$status" -eq 0 ||
              "$backup_started" != true ||
              "$previous_final_set_present" != true ||
              "$publication_committed" == true ]]; then
            rm -f "$backup_sites" "$backup_inputs" "$backup_summary" || true
        fi
    fi

    if [[ "$rollback_failed" == true ]]; then
        printf 'ERROR: Step 08 rollback was incomplete; retaining the owned lock and backups for operator recovery: %s\n' \
            "$lock_path" >&2
    elif [[ "$lock_acquired" == true ]]; then
        if [[ "$lock_owner_written" == true ]]; then
            if ! release_owned_lock; then
                printf 'ERROR: Step 08 lock release failed; preserving lock residue: %s\n' \
                    "$lock_path" >&2
            fi
        else
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
if [[ "$final_count" -eq 3 && "$no_clobber" == true ]]; then
    die "Refusing to replace an existing complete Step 08 output set under --no-clobber for cohort: $cohort_id"
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

if [[ "$no_clobber" == true ]]; then
    publish_file_create_exclusive \
        "Step 08 sites" "$tmp_sites" "$final_sites"
    publish_file_create_exclusive \
        "Step 08 summary" "$tmp_summary" "$final_summary"
    # The input receipt is the transaction commit marker and is deliberately last.
    publish_file_create_exclusive \
        "Step 08 input receipt" "$tmp_inputs" "$final_inputs"
else
    mv "$tmp_sites" "$final_sites"
    mv "$tmp_summary" "$final_summary"
    # The input receipt is the transaction commit marker and is deliberately last.
    mv "$tmp_inputs" "$final_inputs"
fi

validate_output_tables "$final_sites" "$final_inputs" "$final_summary"
[[ "$(sha256_file "$final_sites")" == "$tmp_sites_sha256" ]] ||
    die "Published Step 08 sites table changed during publication."
[[ "$(sha256_file "$final_inputs")" == "$tmp_inputs_sha256" ]] ||
    die "Published Step 08 input receipt changed during publication."
[[ "$(sha256_file "$final_summary")" == "$tmp_summary_sha256" ]] ||
    die "Published Step 08 summary changed during publication."
confirm_input_hashes

if [[ "$no_clobber" == true ]]; then
    require_owned_published_file \
        "Step 08 sites" "$tmp_sites" "$final_sites"
    require_owned_published_file \
        "Step 08 input receipt" "$tmp_inputs" "$final_inputs"
    require_owned_published_file \
        "Step 08 summary" "$tmp_summary" "$final_summary"
    rm -f -- "$tmp_sites" "$tmp_inputs" "$tmp_summary"
    [[ ! -e "$tmp_sites" && ! -L "$tmp_sites" &&
       ! -e "$tmp_inputs" && ! -L "$tmp_inputs" &&
       ! -e "$tmp_summary" && ! -L "$tmp_summary" ]] ||
        die "Step 08 could not remove owned publication anchors."
fi

publication_committed=true
rm -f "$backup_sites" "$backup_inputs" "$backup_summary"
release_owned_lock

printf 'Step 08 execute complete.\n'
printf 'Published sites table: %s\n' "$final_sites"
printf 'Published input receipt: %s\n' "$final_inputs"
printf 'Published QC summary: %s\n' "$final_summary"
