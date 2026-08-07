# Step 09 summary and mutation spectrum validation helpers.

validate_step09_summary_rows() {
    local summary="$1"
    local all_rows="$2"
    local target_expected="$3"
    local tested_expected="$4"
    local not_target_expected="$5"
    local missing_expected="$6"
    local low_coverage_expected="$7"
    local degenerate_expected="$8"
    local below_mean_expected="$9"
    local background_not_passed_expected="${10}"
    local fdr_not_met_expected="${11}"
    local effect_not_met_expected="${12}"
    local significant_up_expected="${13}"
    local significant_down_expected="${14}"
    local not_tested_expected="${15}"
    local summary_rows

    summary_rows="$(awk 'END { print NR - 1 }' "$summary")"
    [[ "$summary_rows" == "1" ]] || return 1
    awk -F '\t' \
        -v fields="$summary_field_count" \
        -v orientation_policy="$ORIENTATION_POLICY" \
        -v analysis="$analysis_id" \
        -v cohort="$cohort_id" \
        -v control="$control_condition" \
        -v treatment="$treatment_condition" \
        -v background="${background_condition:-NA}" \
        -v target_change="$rna_ref>$rna_alt" \
        -v replicates="$replicate_count" \
        -v samples="$sample_count" \
        -v candidates="$all_rows" \
        -v target_candidates="$target_expected" \
        -v tested="$tested_expected" \
        -v not_target="$not_target_expected" \
        -v missing="$missing_expected" \
        -v low_coverage="$low_coverage_expected" \
        -v degenerate="$degenerate_expected" \
        -v below_mean="$below_mean_expected" \
        -v background_not_passed="$background_not_passed_expected" \
        -v fdr_not_met="$fdr_not_met_expected" \
        -v effect_not_met="$effect_not_met_expected" \
        -v significant_up="$significant_up_expected" \
        -v significant_down="$significant_down_expected" \
        -v not_tested="$not_tested_expected" \
        -v sample_path="$sample_manifest" \
        -v sample_hash="$sample_manifest_sha256" \
        -v partition_path="$partition_manifest" \
        -v partition_hash="$partition_manifest_sha256" \
        -v sites="$step08_sites" \
        -v sites_hash="$step08_sites_sha256" \
        -v inputs="$step08_inputs" \
        -v inputs_hash="$step08_inputs_sha256" \
        -v min_dp="$min_sample_dp" \
        -v mean_dp="$mean_dp_threshold" \
        -v fdr="$fdr_threshold" \
        -v common_or="$common_or_threshold" \
        -v difference="$absolute_difference_threshold" \
        -v background_fraction="$background_max_fraction" '
        function is_nonnegative_integer(value) {
            return value ~ /^(0|[1-9][0-9]*)$/
        }
        function is_number(value) {
            return value ~ /^-?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/
        }
        NR == 2 {
            for (field = 7; field <= 21; field++) {
                if (!is_nonnegative_integer($field)) exit 1
            }
            if (NF != fields || $1 != analysis || $2 != cohort ||
                $3 != control || $4 != treatment ||
                $5 != background || $6 != target_change ||
                $7 != replicates || $8 != samples ||
                $9 != candidates || $10 != target_candidates ||
                $11 != tested || $12 != not_target ||
                $13 != missing || $14 != low_coverage ||
                $15 != degenerate || $16 != below_mean ||
                $17 != background_not_passed || $18 != fdr_not_met ||
                $19 != effect_not_met || $20 != significant_up ||
                $21 != significant_down ||
                $9 != $10 + $12 ||
                $10 != $11 + $13 + $14 + $15 ||
                $11 != $16 + $17 + $18 + $19 + $20 + $21 ||
                $9 - $11 != not_tested ||
                $22 != sample_path || $23 != sample_hash ||
                $24 != partition_path || $25 != partition_hash ||
                $26 != sites || $27 != sites_hash ||
                $28 != inputs || $29 != inputs_hash ||
                !is_nonnegative_integer($30) || $30 != min_dp ||
                !is_number($31) || $31 + 0 != mean_dp + 0 ||
                !is_number($32) || $32 + 0 != fdr + 0 ||
                !is_number($33) || $33 + 0 != common_or + 0 ||
                !is_number($34) || $34 + 0 != difference + 0 ||
                !is_number($35) ||
                $35 + 0 != background_fraction + 0 ||
                $36 != "BH" || $37 != "two.sided" ||
                $38 != "TRUE" || $39 != orientation_policy) exit 1
        }
    ' "$summary"
}

validate_step09_mutation_spectrum() {
    local all="$1"
    local mutation="$2"
    local expected_total="$3"
    local expected_tested_total="$4"
    local expected_up_total="$5"
    local expected_down_total="$6"

    awk -F '\t' \
        -v expected_total="$expected_total" \
        -v expected_tested_total="$expected_tested_total" \
        -v expected_up_total="$expected_up_total" \
        -v expected_down_total="$expected_down_total" \
        -v analysis="$analysis_id" '
        function absolute(value) { if (value < 0) return -value; return value }
        function is_number(value) {
            return value ~ /^-?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/
        }
        function is_nonnegative_integer(value) {
            return value ~ /^(0|[1-9][0-9]*)$/
        }
        BEGIN {
            split("A>C,A>G,A>T,C>A,C>G,C>T,G>A,G>C,G>T,T>A,T>C,T>G", expected, ",")
        }
        FILENAME == ARGV[1] {
            if (FNR > 1) {
                candidate_count[$10 ">" $11]++
                if ($28 == "tested") {
                    tested_count[$10 ">" $11]++
                }
                if ($29 == "significant_up") {
                    up_count[$10 ">" $11]++
                }
                if ($29 == "significant_down") {
                    down_count[$10 ">" $11]++
                }
            }
            next
        }
        FNR == 1 { next }
        {
            row++
            mutation = expected[row]
            if (NF != 9 || row > 12 || $1 != analysis ||
                $2 != substr(mutation, 1, 1) ||
                $3 != substr(mutation, 3, 1) || $4 != mutation ||
                !is_nonnegative_integer($5) ||
                !is_nonnegative_integer($7) ||
                !is_nonnegative_integer($8) ||
                !is_nonnegative_integer($9) ||
                $5 != candidate_count[mutation] + 0 ||
                $7 != tested_count[mutation] + 0 ||
                $8 != up_count[mutation] + 0 ||
                $9 != down_count[mutation] + 0 ||
                !is_number($6) || $6 + 0 < 0 || $6 + 0 > 1) exit 1
            if (expected_total == 0) {
                expected_fraction = 0
            } else {
                expected_fraction = (candidate_count[mutation] + 0) / expected_total
            }
            if (absolute(($6 + 0) - expected_fraction) > 0.000000000001) exit 1
            candidate_total += $5
            tested_total += $7
            up_total += $8
            down_total += $9
        }
        END {
            if (row != 12 || candidate_total != expected_total ||
                tested_total != expected_tested_total ||
                up_total != expected_up_total ||
                down_total != expected_down_total) exit 1
        }
    ' "$all" "$mutation"
}
