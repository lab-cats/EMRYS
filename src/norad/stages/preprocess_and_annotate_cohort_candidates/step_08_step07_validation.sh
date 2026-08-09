#!/usr/bin/env bash
# Step 08 admission and stability checks for declared Step 07 inputs.

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
