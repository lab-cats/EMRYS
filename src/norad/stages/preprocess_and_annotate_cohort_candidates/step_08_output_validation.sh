#!/usr/bin/env bash
# Step 08 reconciliation of generated sites, input-receipt, and summary tables.

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
