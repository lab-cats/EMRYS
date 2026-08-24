# Step 09 output validation helpers.
step_09_cmh_awk_validation_lib="${BASH_SOURCE[0]%/*}/step_09_cmh_awk_validation_functions.awk"

collect_all_sites_and_significant_counts() {
    local all="$1"
    local significant="$2"
    local all_metrics
    local all_rows significant_expected target_expected tested_expected not_target_expected
    local missing_expected low_coverage_expected degenerate_expected
    local below_mean_expected background_not_passed_expected
    local fdr_not_met_expected effect_not_met_expected
    local significant_up_expected significant_down_expected not_tested_expected
    local significant_rows

    all_metrics="$(awk -F '\t' \
        -f "$step_09_cmh_awk_validation_lib" \
        -v n="$result_field_count" \
        -v source_fields="$step08_site_field_count" \
        -v sample_total="$sample_count" \
        -v analysis="$analysis_id" \
        -v control="$control_condition" \
        -v treatment="$treatment_condition" \
        -v target_change="$rna_ref>$rna_alt" \
        -v target_ref="$rna_ref" \
        -v target_alt="$rna_alt" \
        -v replicates="$replicate_count" \
        -v background="${background_condition:-NA}" \
        -v min_dp="$min_sample_dp" \
        -v mean_dp_threshold="$mean_dp_threshold" \
        -v fdr_threshold="$fdr_threshold" \
        -v or_threshold="$common_or_threshold" \
        -v difference_threshold="$absolute_difference_threshold" \
        -v background_indices_csv="$background_indices_csv" \
        -v background_threshold="$background_max_fraction" \
        -v orientation_policy="$ORIENTATION_POLICY" \
        -f /dev/stdin \
        "$step08_sites" "$all" <<'AWK'
        BEGIN {
            if (source_fields < 1) exit 1
            if (n < 1) exit 1
            if (background != "NA") {
                background_count = split(background_indices_csv, background_indices, ",")
                if (background_count < 1) exit 1
            }
        }
        {
            if (NR == FNR) {
                if (NF != source_fields) exit 1
                if ($2 == "") exit 1
                source_by_candidate[$2] = $0
                next
            }
            if (FNR == 1) next
            rows++
            if (NF != n) exit 1

            candidate_id = $3
            split(source_by_candidate[candidate_id], source, "\t")
            if (length(source) != source_fields) exit 1
            if (seen[candidate_id]++) exit 1

            if ($1 != analysis ||
                $24 != control || $25 != treatment ||
                $26 != target_change || $27 != replicates ||
                $30 != background ||
                $23 != orientation_policy) exit 1
            for (field = 1; field <= 22; field++) {
                if ($(field + 1) != source[field]) exit 1
            }
            for (field = 23; field <= source_fields; field++) {
                if ($(field + 20) != source[field]) exit 1
            }

            test_status = $28
            call_status = $29
            background_status = $31
            if (test_status != "tested" &&
                test_status != "not_target_change" &&
                test_status != "missing_counts" &&
                test_status != "low_coverage" &&
                test_status != "degenerate_table") exit 1
            if (call_status != "significant_up" &&
                call_status != "significant_down" &&
                call_status != "not_tested" &&
                call_status != "below_mean_dp" &&
                call_status != "background_not_passed" &&
                call_status != "fdr_not_met" &&
                call_status != "effect_not_met") exit 1
            if (background_status != "disabled" &&
                background_status != "pass" &&
                background_status != "fail_fraction" &&
                background_status != "missing_counts" &&
                background_status != "low_coverage") exit 1

            is_target = ($10 == target_ref && $11 == target_alt)
            if ((!is_target && test_status != "not_target_change") ||
                (is_target && test_status == "not_target_change")) exit 1
            if ((test_status == "tested" && call_status == "not_tested") ||
                (test_status != "tested" && call_status != "not_tested")) {
                exit 1
            }

            if ($32 == "NA") {
                if ($33 != "NA" || $34 != "NA" ||
                    $35 != "NA" || $36 != "NA") exit 1
            } else {
                if (!is_nonnegative_integer($32) ||
                    !is_nonnegative_number($33) ||
                    $33 + 0.000000000001 < $32 + 0) exit 1
                if ($32 + 0 == 0) {
                    if ($34 != "NA" || $35 != "NA" || $36 != "NA") exit 1
                } else {
                    if (!is_fraction($34) ||
                        !is_fraction($35) ||
                        !is_number($36) ||
                        $36 + 0 < -1 || $36 + 0 > 1 ||
                        absolute(($35 + 0) - ($34 + 0) - ($36 + 0)) > 0.000000000001) exit 1
                }
            }
            if ($37 != "NA" && !is_fraction($37)) exit 1

            if (background == "NA") {
                if (background_status != "disabled" ||
                    $37 != "NA") exit 1
            } else {
                background_missing = 0
                background_low = 0
                background_all_positive = 1
                background_all_below = 1
                background_max = -1
                for (background_number = 1; background_number <= background_count; background_number++) {
                    sample_index = background_indices[background_number]
                    background_dp = $(42 + sample_index)
                    background_ad = $(42 + sample_total + sample_index)
                    if (background_dp == "NA" ||
                        background_ad == "NA") {
                        background_missing = 1
                        continue
                    }
                    if (background_dp + 0 < min_dp + 0) {
                        background_low = 1
                    }
                    if (background_dp + 0 <= 0) {
                        background_all_positive = 0
                        continue
                    }
                    background_af = (background_ad + 0) / (background_dp + 0)
                    if (background_af > background_max) {
                        background_max = background_af
                    }
                    if (!(background_af < background_threshold + 0)) {
                        background_all_below = 0
                    }
                }
                if (background_missing) {
                    expected_background_status = "missing_counts"
                    expected_background_is_na = 1
                } else if (background_low) {
                    expected_background_status = "low_coverage"
                    expected_background_is_na = !background_all_positive
                } else {
                if (background_all_below) {
                    expected_background_status = "pass"
                } else {
                    expected_background_status = "fail_fraction"
                }
                    expected_background_is_na = 0
                }
                if (background_status != expected_background_status) exit 1
                if (expected_background_is_na) {
                    if ($37 != "NA") exit 1
                } else if (!is_fraction($37) ||
                           absolute(($37 + 0) - background_max) > 0.000000000001) {
                    exit 1
                }
            }

            cmh_all_na = $38 == "NA" && $39 == "NA" &&
                $40 == "NA" && $41 == "NA" && $42 == "NA"
            cmh_all_present = $38 != "NA" && $39 != "NA" &&
                $40 != "NA" && $41 != "NA" && $42 != "NA"
            if (!cmh_all_na && !cmh_all_present) exit 1
            if (cmh_all_present) {
                if (!is_nonnegative_number($38) ||
                    !is_number($39) || $39 + 0 != 1 ||
                    !is_fraction($40) ||
                    !is_fraction($41) ||
                    $41 + 0.000000000001 < $40 + 0 ||
                    !is_odds_ratio($42)) exit 1
            }

            if (test_status == "missing_counts" &&
                $32 != "NA") exit 1
            if (test_status == "low_coverage" &&
                ($32 == "NA" ||
                 !($32 + 0 < min_dp + 0))) exit 1
            if ((test_status == "tested" ||
                 test_status == "degenerate_table") &&
                ($32 == "NA" ||
                 $32 + 0 < min_dp + 0)) exit 1
            if (test_status != "tested" && !cmh_all_na) exit 1

            if (test_status == "tested") {
                if (!cmh_all_present || $33 == "NA" ||
                    $34 == "NA" || $35 == "NA" ||
                    $36 == "NA") exit 1
                if (!($33 + 0 > mean_dp_threshold + 0)) {
                    expected_call = "below_mean_dp"
                } else if (background_status != "disabled" &&
                           background_status != "pass") {
                    expected_call = "background_not_passed"
                } else if (!($41 + 0 < fdr_threshold + 0)) {
                    expected_call = "fdr_not_met"
                } else if (odds_ratio_above($42, or_threshold) &&
                           $36 + 0 > difference_threshold + 0) {
                    expected_call = "significant_up"
                } else if (odds_ratio_below($42, or_threshold) &&
                           $36 + 0 < -(difference_threshold + 0)) {
                    expected_call = "significant_down"
                } else {
                    expected_call = "effect_not_met"
                }
                if (call_status != expected_call) exit 1
            }

            if (is_target) target_count++
            if (test_status == "tested") tested_count++
            else if (test_status == "not_target_change") not_target_count++
            else if (test_status == "missing_counts") missing_count++
            else if (test_status == "low_coverage") low_coverage_count++
            else if (test_status == "degenerate_table") degenerate_count++

            if (call_status == "not_tested") not_tested_count++
            else if (call_status == "below_mean_dp") below_mean_count++
            else if (call_status == "background_not_passed") {
                background_failed_count++
            } else if (call_status == "fdr_not_met") fdr_failed_count++
            else if (call_status == "effect_not_met") effect_failed_count++
            else if (call_status == "significant_up") significant_up_count++
            else if (call_status == "significant_down") significant_down_count++
        }
        END {
            print rows + 0, significant_up_count + significant_down_count,
                target_count + 0, tested_count + 0, not_target_count + 0,
                missing_count + 0, low_coverage_count + 0,
                degenerate_count + 0, below_mean_count + 0,
                background_failed_count + 0, fdr_failed_count + 0,
                effect_failed_count + 0, significant_up_count + 0,
                significant_down_count + 0, not_tested_count + 0
        }
AWK
    )" || return 1

    read -r \
        all_rows significant_expected target_expected tested_expected \
        not_target_expected missing_expected low_coverage_expected \
        degenerate_expected below_mean_expected \
        background_not_passed_expected fdr_not_met_expected \
        effect_not_met_expected significant_up_expected \
        significant_down_expected not_tested_expected <<< "$all_metrics" || return 1

    [[ "$all_rows" == "$step08_site_row_count" ]] ||
        return 1

    awk -F '\t' '
        FILENAME == ARGV[1] {
            if (FNR > 1 &&
                ($29 == "significant_up" || $29 == "significant_down")) {
                expected[++expected_count] = $0
            }
            next
        }
        FNR == 1 { next }
        {
            observed_count++
            if (observed_count > expected_count ||
                $0 != expected[observed_count]) exit 1
        }
        END {
            if (observed_count != expected_count) exit 1
        }
    ' "$all" "$significant" || return 1
    significant_rows="$(awk 'END { print NR - 1 }' "$significant")"
    [[ "$significant_rows" == "$significant_expected" ]] || return 1

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$all_rows" "$significant_expected" "$target_expected" \
        "$tested_expected" "$not_target_expected" "$missing_expected" \
        "$low_coverage_expected" "$degenerate_expected" \
        "$below_mean_expected" "$background_not_passed_expected" \
        "$fdr_not_met_expected" "$effect_not_met_expected" \
        "$significant_up_expected" "$significant_down_expected" \
        "$not_tested_expected"
}

validate_outputs() {
    local all="$1"
    local significant="$2"
    local summary="$3"
    local mutation="$4"
    local mutation_pdf="$5"
    local depth_pdf="$6"
    local all_rows significant_expected target_expected tested_expected
    local not_target_expected missing_expected low_coverage_expected
    local degenerate_expected below_mean_expected
    local background_not_passed_expected fdr_not_met_expected
    local effect_not_met_expected significant_up_expected
    local significant_down_expected not_tested_expected
    local summary_rows

    confirm_inputs_unchanged
    validate_exact_header "Step 09 all-sites table" "$all" "$result_header"
    validate_exact_header "Step 09 significant-sites table" "$significant" "$result_header"
    validate_exact_header "Step 09 summary" "$summary" "$summary_header"
    validate_exact_header "Step 09 mutation spectrum" "$mutation" "$mutation_header"

    local all_metrics
    all_metrics="$(collect_all_sites_and_significant_counts "$all" "$significant")" ||
        die "Step 09 all-sites rows do not preserve the Step 08 source/analysis contract: $all"
    if ! read -r \
        all_rows significant_expected target_expected tested_expected \
        not_target_expected missing_expected low_coverage_expected \
        degenerate_expected below_mean_expected \
        background_not_passed_expected fdr_not_met_expected \
        effect_not_met_expected significant_up_expected \
        significant_down_expected not_tested_expected <<< "$all_metrics"; then
        die "Step 09 all-sites rows do not preserve the Step 08 source/analysis contract: $all"
    fi
    [[ "$all_rows" == "$step08_site_row_count" ]] ||
        die "Step 09 all-sites row count must equal Step 08 sites row count."

    summary_rows="$(awk 'END { print NR - 1 }' "$summary")"
    [[ "$summary_rows" == "1" ]] || die "Step 09 summary must have exactly one data row."
    if ! validate_step09_summary_rows \
        "$summary" "$all_rows" "$target_expected" "$tested_expected" \
        "$not_target_expected" "$missing_expected" "$low_coverage_expected" \
        "$degenerate_expected" "$below_mean_expected" \
        "$background_not_passed_expected" "$fdr_not_met_expected" \
        "$effect_not_met_expected" "$significant_up_expected" \
        "$significant_down_expected" "$not_tested_expected"; then
        die "Step 09 summary provenance/policy fields are invalid."
    fi
    if ! validate_step09_mutation_spectrum \
        "$all" "$mutation" "$all_rows" "$tested_expected" \
        "$significant_up_expected" "$significant_down_expected"; then
        die "Step 09 mutation-spectrum PDF rows/counts/fractions do not reconcile with all-sites."
    fi

    validate_pdf "Step 09 mutation-spectrum PDF" "$mutation_pdf"
    validate_pdf "Step 09 depth-delta PDF" "$depth_pdf"
    confirm_inputs_unchanged
}
