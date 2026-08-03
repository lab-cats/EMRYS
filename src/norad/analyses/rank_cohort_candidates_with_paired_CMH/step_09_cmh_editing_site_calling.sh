#!/usr/bin/env bash
# Step 09: paired CMH editing-site calling from the committed Step 08 tables.
#
# Dry-run validates the complete declared input contract and prints the exact R
# command without creating output paths or invoking R. Execute mode writes six
# run-token outputs, validates them, and publishes the summary last as the
# transaction commit marker.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'USAGE'
Usage:
  src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.sh \
    --analysis-id ANALYSIS_ID \
    --cohort-id COHORT_ID \
    --sample-manifest SAMPLE_MANIFEST \
    --partition-manifest PARTITION_MANIFEST \
    --step08-root STEP08_ROOT \
    --output-root OUTPUT_ROOT \
    [--control-condition EV] \
    [--treatment-condition PUM1] \
    [--rna-ref A] \
    [--rna-alt G] \
    [--min-sample-dp 1] \
    [--mean-dp-threshold 50] \
    [--fdr-threshold 0.05] \
    [--common-or-threshold 1.2] \
    [--absolute-difference-threshold 0.005] \
    [--background-condition CONDITION] \
    [--background-max-fraction 0.01] \
    [--rscript-bin RSCRIPT_BIN] \
    [--r-script R_SCRIPT] \
    [--execute]

The sample manifest is the only pairing source. It must contain sample_id,
condition, and replicate. Each replicate must contain exactly one control and
one treatment sample, both conditions must have identical replicate sets, and
at least two strata are required. Pairing is never inferred from sample names.

Dry-run is the default and writes nothing.
USAGE
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

require_value() {
    local option="$1"
    local value="${2:-}"
    [[ -n "$value" && "$value" != --* ]] || die "$option requires a value."
}

validate_safe_id() {
    local label="$1"
    local value="$2"
    [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] ||
        die "$label must match [A-Za-z0-9][A-Za-z0-9._-]*; got: $value"
}

validate_condition() {
    local label="$1"
    local value="$2"
    [[ -n "$value" && "$value" != *$'\t'* && "$value" != *$'\n'* ]] ||
        die "$label must be a non-empty single TSV value."
}

validate_base() {
    local label="$1"
    local value="$2"
    [[ "$value" =~ ^[ACGT]$ ]] || die "$label must be one of A, C, G, T; got: $value"
}

validate_positive_integer() {
    local label="$1"
    local value="$2"
    [[ "$value" =~ ^[1-9][0-9]*$ ]] ||
        die "$label must be a positive integer; got: $value"
}

validate_positive_number() {
    local label="$1"
    local value="$2"
    awk -v value="$value" 'BEGIN {
        if (value !~ /^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ ||
            value + 0 <= 0) exit 1
    }' || die "$label must be a positive finite number; got: $value"
}

validate_nonnegative_number() {
    local label="$1"
    local value="$2"
    awk -v value="$value" 'BEGIN {
        if (value !~ /^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ ||
            value + 0 < 0) exit 1
    }' || die "$label must be a non-negative finite number; got: $value"
}

validate_unit_fraction() {
    local label="$1"
    local value="$2"
    awk -v value="$value" 'BEGIN {
        if (value !~ /^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ ||
            value + 0 <= 0 || value + 0 >= 1) exit 1
    }' || die "$label must be greater than 0 and less than 1; got: $value"
}

validate_probability() {
    local label="$1"
    local value="$2"
    awk -v value="$value" 'BEGIN {
        if (value !~ /^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ ||
            value + 0 <= 0 || value + 0 > 1) exit 1
    }' || die "$label must be greater than 0 and at most 1; got: $value"
}

validate_closed_unit_fraction() {
    local label="$1"
    local value="$2"
    awk -v value="$value" 'BEGIN {
        if (value !~ /^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ ||
            value + 0 < 0 || value + 0 > 1) exit 1
    }' || die "$label must be between 0 and 1 inclusive; got: $value"
}

validate_nonempty_file() {
    local label="$1"
    local path="$2"
    [[ -s "$path" ]] || die "$label does not exist or is empty: $path"
}

resolve_executable() {
    local label="$1"
    local value="$2"
    local resolved
    if [[ "$value" == */* ]]; then
        [[ -e "$value" ]] || die "$label does not exist: $value"
        [[ -x "$value" ]] || die "$label exists but is not executable: $value"
        printf '%s\n' "$value"
    else
        resolved="$(command -v "$value" || true)"
        [[ -n "$resolved" ]] || die "$label executable was not found on PATH: $value"
        printf '%s\n' "$resolved"
    fi
}

sha256_file() {
    local path="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$path" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$path" | awk '{print $1}'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c '
import hashlib, sys
h = hashlib.sha256()
with open(sys.argv[1], "rb") as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
print(h.hexdigest())
' "$path"
    else
        die "No SHA-256 implementation found (sha256sum, shasum, or python3)."
    fi
}

validate_exact_header() {
    local label="$1"
    local path="$2"
    local expected="$3"
    local observed
    validate_nonempty_file "$label" "$path"
    IFS= read -r observed < "$path"
    [[ "$observed" == "$expected" ]] || die "$label header is invalid: $path"
}

read_samples_and_validate_pairs() {
    local manifest="$1"
    awk -F '\t' \
        -v control="$control_condition" \
        -v treatment="$treatment_condition" \
        -v background="$background_condition" '
        NR == 1 {
            header_fields = NF
            for (i = 1; i <= NF; i++) {
                gsub(/\r$/, "", $i)
                if (seen_header[$i]++) {
                    printf "duplicate sample manifest column: %s\n", $i > "/dev/stderr"
                    exit 2
                }
                if ($i == "sample_id") sample_col = i
                if ($i == "r1_fastq") r1_col = i
                if ($i == "r2_fastq") r2_col = i
                if ($i == "strandedness") strand_col = i
                if ($i == "condition") condition_col = i
                if ($i == "replicate") replicate_col = i
                if ($i != "sample_id" && $i != "r1_fastq" &&
                    $i != "r2_fastq" && $i != "strandedness" &&
                    $i != "condition" && $i != "replicate" && $i != "notes") {
                    printf "unexpected sample manifest column: %s\n", $i > "/dev/stderr"
                    exit 2
                }
            }
            if (!sample_col || !r1_col || !r2_col || !strand_col ||
                !condition_col || !replicate_col) {
                print "sample manifest requires sample_id, r1_fastq, r2_fastq, strandedness, condition, and replicate" > "/dev/stderr"
                exit 2
            }
            next
        }
        {
            if (NF != header_fields) {
                printf "sample manifest row %d has %d fields; expected %d\n",
                    NR, NF, header_fields > "/dev/stderr"
                exit 3
            }
            sample = $sample_col
            condition = $condition_col
            replicate = $replicate_col
            r1 = $r1_col
            r2 = $r2_col
            strandedness = $strand_col
            gsub(/\r$/, "", sample)
            gsub(/\r$/, "", condition)
            gsub(/\r$/, "", replicate)
            gsub(/\r$/, "", r1)
            gsub(/\r$/, "", r2)
            gsub(/\r$/, "", strandedness)
            if (sample == "" || r1 == "" || r2 == "" ||
                strandedness == "" || condition == "") {
                printf "sample manifest row %d has an empty required value\n", NR > "/dev/stderr"
                exit 3
            }
            if (strandedness != "forward" && strandedness != "reverse" &&
                strandedness != "unstranded" && strandedness != "unknown") {
                printf "sample %s has invalid strandedness: %s\n",
                    sample, strandedness > "/dev/stderr"
                exit 3
            }
            if (seen_sample[sample]++) {
                printf "duplicate sample_id in sample manifest: %s\n", sample > "/dev/stderr"
                exit 4
            }
            print "S\t" sample
            sample_count++
            if (condition == control || condition == treatment) {
                if (replicate == "") {
                    printf "analysis sample %s has an empty replicate\n", sample > "/dev/stderr"
                    exit 5
                }
                key = condition SUBSEP replicate
                if (seen_pair[key]++) {
                    printf "condition %s has more than one sample for replicate %s\n",
                        condition, replicate > "/dev/stderr"
                    exit 6
                }
                if (condition == control) control_rep[replicate] = sample
                else treatment_rep[replicate] = sample
                if (!(replicate in seen_replicate)) {
                    seen_replicate[replicate] = ++replicate_order_count
                    replicate_order[replicate_order_count] = replicate
                }
            } else if (background != "" && condition == background) {
                print "B\t" sample
                background_count++
            }
        }
        END {
            if (sample_count == 0) {
                print "sample manifest contains no samples" > "/dev/stderr"
                exit 7
            }
            strata = 0
            for (replicate in control_rep) {
                if (!(replicate in treatment_rep)) {
                    printf "control replicate %s has no treatment pair\n",
                        replicate > "/dev/stderr"
                    exit 8
                }
                strata++
            }
            for (replicate in treatment_rep) {
                if (!(replicate in control_rep)) {
                    printf "treatment replicate %s has no control pair\n",
                        replicate > "/dev/stderr"
                    exit 9
                }
            }
            if (strata < 2) {
                print "paired CMH analysis requires at least two replicate strata" > "/dev/stderr"
                exit 10
            }
            if (background != "" && background_count == 0) {
                printf "background condition has no samples: %s\n",
                    background > "/dev/stderr"
                exit 11
            }
            for (i = 1; i <= replicate_order_count; i++) {
                replicate = replicate_order[i]
                print "P\t" replicate "\t" control_rep[replicate] "\t" treatment_rep[replicate]
            }
            print "M\t" sample_count "\t" strata "\t" background_count
        }
    ' "$manifest"
}

read_partitions() {
    local manifest="$1"
    awk -F '\t' '
        NR == 1 {
            if (NF != 3 || $1 != "partition_id" ||
                $2 != "selector_type" || $3 != "selector_value") {
                print "partition manifest header must be exactly partition_id, selector_type, selector_value" > "/dev/stderr"
                exit 2
            }
            next
        }
        {
            if (NF != 3) {
                printf "partition manifest row %d has %d fields; expected 3\n",
                    NR, NF > "/dev/stderr"
                exit 3
            }
            id = $1; type = $2; value = $3
            gsub(/\r$/, "", value)
            if (id == "" || type == "" || value == "") {
                printf "partition manifest row %d has an empty value\n", NR > "/dev/stderr"
                exit 3
            }
            if (seen[id]++) {
                printf "duplicate partition_id: %s\n", id > "/dev/stderr"
                exit 4
            }
            if (type != "region" && type != "regions_file") {
                printf "invalid selector_type for partition %s: %s\n", id, type > "/dev/stderr"
                exit 5
            }
            print id "\t" type "\t" value
            count++
        }
        END {
            if (!count) {
                print "partition manifest contains no partitions" > "/dev/stderr"
                exit 6
            }
        }
    ' "$manifest"
}

confirm_inputs_unchanged() {
    [[ "$(sha256_file "$sample_manifest")" == "$sample_manifest_sha256" ]] ||
        die "Sample manifest changed during Step 09: $sample_manifest"
    [[ "$(sha256_file "$partition_manifest")" == "$partition_manifest_sha256" ]] ||
        die "Partition manifest changed during Step 09: $partition_manifest"
    [[ "$(sha256_file "$step08_sites")" == "$step08_sites_sha256" ]] ||
        die "Step 08 sites table changed during Step 09: $step08_sites"
    [[ "$(sha256_file "$step08_inputs")" == "$step08_inputs_sha256" ]] ||
        die "Step 08 input receipt changed during Step 09: $step08_inputs"
}

validate_step08_inputs() {
    local path="$1"
    local expected_header
    expected_header='cohort_id	partition_id	selector_type	selector_value	orientation	step07_receipt_path	step07_receipt_sha256	vcf_path	vcf_sha256	sample_manifest_sha256	partition_manifest_sha256	annotation_gtf	annotation_gtf_sha256	sample_count	declared_vcf_record_count	observed_vcf_record_count	observed_alt_allele_count	supported_snv_count	skipped_symbolic_count	skipped_non_snv_count	published_candidate_count	orientation_policy'
    validate_exact_header "Step 08 input receipt" "$path" "$expected_header"
    awk -F '\t' \
        -v cohort="$cohort_id" \
        -v sample_hash="$sample_manifest_sha256" \
        -v partition_hash="$partition_manifest_sha256" \
        -v samples="$sample_count" \
        -v partitions_csv="$partition_rows_csv" '
        BEGIN {
            partition_count = split(partitions_csv, raw, "\034")
            for (i = 1; i <= partition_count; i++) {
                split(raw[i], fields, "\035")
                ids[i] = fields[1]
                types[i] = fields[2]
                values[i] = fields[3]
            }
        }
        FNR == 1 { next }
        {
            row++
            partition_index = int((row - 1) / 2) + 1
            orientation = ((row - 1) % 2 == 0) ? "FWD_like" : "REV_like"
            if (NF != 22 || partition_index > partition_count ||
                $1 != cohort || $2 != ids[partition_index] ||
                $3 != types[partition_index] || $4 != values[partition_index] ||
                $5 != orientation || $10 != sample_hash ||
                $11 != partition_hash || $14 != samples ||
                $22 != "legacy_provisional_v1") exit 1
            if ($6 == "" || length($7) != 64 || $7 !~ /^[0-9a-f]+$/ ||
                $8 == "" || length($9) != 64 || $9 !~ /^[0-9a-f]+$/ ||
                $12 == "" || length($13) != 64 ||
                $13 !~ /^[0-9a-f]+$/) exit 1
            for (i = 15; i <= 21; i++) {
                if ($i !~ /^(0|[1-9][0-9]*)$/) exit 1
            }
            if ($16 != $15 || $18 != $21 ||
                $17 != $18 + $19 + $20) exit 1
            published += $21
        }
        END {
            if (row != partition_count * 2) exit 1
            print published + 0
        }
    ' "$path" || die "Step 08 input receipt content/order/counts are invalid: $path"
}

validate_step08_sites() {
    local path="$1"
    local inputs_path="$2"
    local row_count
    validate_exact_header "Step 08 sites table" "$path" "$step08_sites_header"
    row_count="$(awk -F '\t' \
        -v expected_fields="$step08_site_field_count" \
        -v sample_total="$sample_count" \
        -v partition_csv="$partition_ids_csv" '
        function absolute(value) { return value < 0 ? -value : value }
        BEGIN {
            count = split(partition_csv, ids, ",")
            for (i = 1; i <= count; i++) declared[ids[i]] = 1
        }
        FILENAME == ARGV[1] {
            if (FNR == 1) next
            expected[$2 SUBSEP $5] = $21 + 0
            next
        }
        FNR == 1 { next }
        {
            key = $1 SUBSEP $3
            if (NF != expected_fields || !($1 in declared) ||
                ($3 != "FWD_like" && $3 != "REV_like") ||
                !(key in expected) ||
                $22 != "legacy_provisional_v1" || $2 == "" || seen[$2]++) exit 1
            for (i = 1; i <= sample_total; i++) {
                dp = $(22 + i)
                ad = $(22 + sample_total + i)
                af = $(22 + 2 * sample_total + i)
                if (dp == "NA" || ad == "NA") {
                    if (dp != "NA" || ad != "NA" || af != "NA") exit 1
                    continue
                }
                if (dp !~ /^(0|[1-9][0-9]*)$/ ||
                    ad !~ /^(0|[1-9][0-9]*)$/ || ad + 0 > dp + 0) exit 1
                if (dp + 0 == 0) {
                    if (af != "NA") exit 1
                } else {
                    if (af !~ /^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ ||
                        absolute((af + 0) - (ad + 0) / (dp + 0)) > 0.000000000001) exit 1
                }
            }
            observed[key]++
            rows++
        }
        END {
            for (key in expected) {
                if (observed[key] + 0 != expected[key] + 0) exit 1
            }
            print rows + 0
        }
    ' "$inputs_path" "$path")" ||
        die "Step 08 sites table rows or partition/orientation counts are invalid: $path"
    [[ "$row_count" == "$step08_published_count" ]] ||
        die "Step 08 sites row count does not match the complete input receipt; sites $row_count, receipt $step08_published_count"
    step08_site_row_count="$row_count"
}

validate_pdf() {
    local label="$1"
    local path="$2"
    local signature
    validate_nonempty_file "$label" "$path"
    IFS= read -r signature < "$path"
    [[ "$signature" == %PDF-* ]] || die "$label is missing a PDF signature: $path"
    tail -c 2048 "$path" | grep -a -q '%%EOF' ||
        die "$label is missing a PDF EOF marker: $path"
}

validate_outputs() {
    local all="$1"
    local significant="$2"
    local summary="$3"
    local mutation="$4"
    local mutation_pdf="$5"
    local depth_pdf="$6"
    local all_rows significant_expected significant_rows summary_rows all_metrics
    local target_expected tested_expected not_target_expected
    local missing_expected low_coverage_expected degenerate_expected
    local below_mean_expected background_not_passed_expected
    local fdr_not_met_expected effect_not_met_expected
    local significant_up_expected significant_down_expected not_tested_expected

    confirm_inputs_unchanged
    validate_exact_header "Step 09 all-sites table" "$all" "$result_header"
    validate_exact_header "Step 09 significant-sites table" "$significant" "$result_header"
    validate_exact_header "Step 09 summary" "$summary" "$summary_header"
    validate_exact_header "Step 09 mutation spectrum" "$mutation" "$mutation_header"

    all_metrics="$(paste "$step08_sites" "$all" | awk -F '\t' \
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
        -v background_threshold="$background_max_fraction" '
        function result(field) { return $(source_fields + field) }
        function absolute(value) { return value < 0 ? -value : value }
        function is_number(value) {
            return value ~ /^-?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/
        }
        function is_nonnegative_number(value) {
            return is_number(value) && value + 0 >= 0
        }
        function is_nonnegative_integer(value) {
            return value ~ /^(0|[1-9][0-9]*)$/
        }
        function is_fraction(value) {
            return is_number(value) && value + 0 >= 0 && value + 0 <= 1
        }
        function is_odds_ratio(value) {
            return value == "Inf" || is_nonnegative_number(value)
        }
        function odds_ratio_above(value, threshold) {
            return value == "Inf" || value + 0 > threshold + 0
        }
        function odds_ratio_below(value, threshold) {
            return value != "Inf" && value + 0 < 1 / (threshold + 0)
        }
        BEGIN {
            if (background != "NA") {
                background_count = split(background_indices_csv, background_indices, ",")
                if (background_count < 1) exit 1
            }
        }
        NR == 1 { next }
        {
            rows++
            if (NF != source_fields + n || seen[result(3)]++) exit 1

            if (result(1) != analysis ||
                result(24) != control || result(25) != treatment ||
                result(26) != target_change || result(27) != replicates ||
                result(30) != background ||
                result(23) != "legacy_provisional_v1") exit 1
            for (field = 1; field <= 22; field++) {
                if (result(field + 1) != $field) exit 1
            }
            for (field = 23; field <= source_fields; field++) {
                if (result(field + 20) != $field) exit 1
            }

            test_status = result(28)
            call_status = result(29)
            background_status = result(31)
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

            is_target = (result(10) == target_ref &&
                         result(11) == target_alt)
            if ((!is_target && test_status != "not_target_change") ||
                (is_target && test_status == "not_target_change")) exit 1
            if ((test_status == "tested" && call_status == "not_tested") ||
                (test_status != "tested" && call_status != "not_tested")) {
                exit 1
            }

            if (result(32) == "NA") {
                if (result(33) != "NA" || result(34) != "NA" ||
                    result(35) != "NA" || result(36) != "NA") exit 1
            } else {
                if (!is_nonnegative_integer(result(32)) ||
                    !is_nonnegative_number(result(33)) ||
                    result(33) + 0.000000000001 < result(32) + 0) exit 1
                if (result(32) + 0 == 0) {
                    if (result(34) != "NA" || result(35) != "NA" ||
                        result(36) != "NA") exit 1
                } else {
                    if (!is_fraction(result(34)) ||
                        !is_fraction(result(35)) ||
                        !is_number(result(36)) ||
                        result(36) + 0 < -1 || result(36) + 0 > 1 ||
                        absolute((result(35) + 0) - (result(34) + 0) - (result(36) + 0)) > 0.000000000001) exit 1
                }
            }
            if (result(37) != "NA" && !is_fraction(result(37))) exit 1

            if (background == "NA") {
                if (background_status != "disabled" ||
                    result(37) != "NA") exit 1
            } else {
                background_missing = 0
                background_low = 0
                background_all_positive = 1
                background_all_below = 1
                background_max = -1
                for (background_number = 1; background_number <= background_count; background_number++) {
                    sample_index = background_indices[background_number]
                    background_dp = result(42 + sample_index)
                    background_ad = result(42 + sample_total + sample_index)
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
                    expected_background_status = background_all_below ? "pass" : "fail_fraction"
                    expected_background_is_na = 0
                }
                if (background_status != expected_background_status) exit 1
                if (expected_background_is_na) {
                    if (result(37) != "NA") exit 1
                } else if (!is_fraction(result(37)) || absolute((result(37) + 0) - background_max) > 0.000000000001) {
                    exit 1
                }
            }

            cmh_all_na = result(38) == "NA" && result(39) == "NA" &&
                result(40) == "NA" && result(41) == "NA" &&
                result(42) == "NA"
            cmh_all_present = result(38) != "NA" && result(39) != "NA" &&
                result(40) != "NA" && result(41) != "NA" &&
                result(42) != "NA"
            if (!cmh_all_na && !cmh_all_present) exit 1
            if (cmh_all_present) {
                if (!is_nonnegative_number(result(38)) ||
                    !is_number(result(39)) || result(39) + 0 != 1 ||
                    !is_fraction(result(40)) ||
                    !is_fraction(result(41)) ||
                    result(41) + 0.000000000001 < result(40) + 0 ||
                    !is_odds_ratio(result(42))) exit 1
            }

            if (test_status == "missing_counts" &&
                result(32) != "NA") exit 1
            if (test_status == "low_coverage" &&
                (result(32) == "NA" ||
                 !(result(32) + 0 < min_dp + 0))) exit 1
            if ((test_status == "tested" ||
                 test_status == "degenerate_table") &&
                (result(32) == "NA" ||
                 result(32) + 0 < min_dp + 0)) exit 1
            if (test_status != "tested" && !cmh_all_na) exit 1

            if (test_status == "tested") {
                if (!cmh_all_present || result(33) == "NA" ||
                    result(34) == "NA" || result(35) == "NA" ||
                    result(36) == "NA") exit 1
                if (!(result(33) + 0 > mean_dp_threshold + 0)) {
                    expected_call = "below_mean_dp"
                } else if (background_status != "disabled" &&
                           background_status != "pass") {
                    expected_call = "background_not_passed"
                } else if (!(result(41) + 0 < fdr_threshold + 0)) {
                    expected_call = "fdr_not_met"
                } else if (odds_ratio_above(result(42), or_threshold) &&
                           result(36) + 0 > difference_threshold + 0) {
                    expected_call = "significant_up"
                } else if (odds_ratio_below(result(42), or_threshold) &&
                           result(36) + 0 < -(difference_threshold + 0)) {
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
    ')" ||
        die "Step 09 all-sites rows do not preserve the Step 08 source/analysis contract: $all"
    read -r \
        all_rows significant_expected target_expected tested_expected \
        not_target_expected missing_expected low_coverage_expected \
        degenerate_expected below_mean_expected \
        background_not_passed_expected fdr_not_met_expected \
        effect_not_met_expected significant_up_expected \
        significant_down_expected not_tested_expected <<< "$all_metrics"
    [[ "$all_rows" == "$step08_site_row_count" ]] ||
        die "Step 09 all-sites row count must equal Step 08 sites row count."

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
    ' "$all" "$significant" ||
        die "Step 09 significant-sites rows must be the byte-identical ordered set of all significant calls."
    significant_rows="$(awk 'END { print NR - 1 }' "$significant")"
    [[ "$significant_rows" == "$significant_expected" ]] ||
        die "Step 09 significant-sites table omitted or added a called row."

    summary_rows="$(awk 'END { print NR - 1 }' "$summary")"
    [[ "$summary_rows" == "1" ]] || die "Step 09 summary must have exactly one data row."
    awk -F '\t' \
        -v fields="$summary_field_count" \
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
                $38 != "TRUE" || $39 != "legacy_provisional_v1") exit 1
        }
    ' "$summary" || die "Step 09 summary provenance/policy fields are invalid."

    awk -F '\t' \
        -v analysis="$analysis_id" \
        -v expected_total="$all_rows" \
        -v expected_tested_total="$tested_expected" \
        -v expected_up_total="$significant_up_expected" \
        -v expected_down_total="$significant_down_expected" '
        function absolute(value) { return value < 0 ? -value : value }
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
            if (FNR == 1) next
            mutation = $10 ">" $11
            candidate_count[mutation]++
            if ($28 == "tested") tested_count[mutation]++
            if ($29 == "significant_up") up_count[mutation]++
            if ($29 == "significant_down") down_count[mutation]++
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
            expected_fraction = expected_total == 0 ? 0 : (candidate_count[mutation] + 0) / expected_total
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
    ' "$all" "$mutation" ||
        die "Step 09 mutation spectrum rows/counts/fractions do not reconcile with all-sites."

    validate_pdf "Step 09 mutation-spectrum PDF" "$mutation_pdf"
    validate_pdf "Step 09 depth-delta PDF" "$depth_pdf"
    confirm_inputs_unchanged
}

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
rscript_bin="$(resolve_executable "Rscript" "$rscript_value")"
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
for sample_id in "${sample_ids[@]}"; do step08_sites_header+=$'\t'"DP__$sample_id"; done
for sample_id in "${sample_ids[@]}"; do step08_sites_header+=$'\t'"AD__$sample_id"; done
for sample_id in "${sample_ids[@]}"; do step08_sites_header+=$'\t'"AF__$sample_id"; done
step08_site_field_count=$((22 + sample_count * 3))

step08_published_count="$(validate_step08_inputs "$step08_inputs")" ||
    die "Step 08 input receipt validation failed."
validate_step08_sites "$step08_sites" "$step08_inputs"
confirm_inputs_unchanged

result_header='analysis_id	partition_id	candidate_id	orientation	chromosome	position	alt_index	genomic_ref	genomic_alt	rna_ref	rna_alt	annotation_strand	gene_ids	transcript_ids	is_cds	is_five_prime_utr	is_three_prime_utr	is_exon	is_intron	qual	filter	info_alt_depth	orientation_policy	control_condition	treatment_condition	target_rna_change	replicate_count	test_status	call_status	background_condition	background_status	min_analysis_dp	mean_analysis_dp	mean_control_af	mean_treatment_af	treatment_control_difference	max_background_af	cmh_statistic	cmh_degrees_freedom	cmh_p_value	cmh_fdr_bh	common_odds_ratio'
for sample_id in "${sample_ids[@]}"; do result_header+=$'\t'"DP__$sample_id"; done
for sample_id in "${sample_ids[@]}"; do result_header+=$'\t'"AD__$sample_id"; done
for sample_id in "${sample_ids[@]}"; do result_header+=$'\t'"AF__$sample_id"; done
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
cleanup() {
    local status=$?
    local rollback_failed=false
    trap - EXIT HUP INT TERM
    if [[ "$scratch_owned" == true ]]; then
        for temp in "${temps[@]}"; do rm -f "$temp" || true; done
    fi
    if [[ "$publication_started" == true && "$publication_committed" != true ]]; then
        for index in "${!finals[@]}"; do
            if [[ "$previous_set" != true ]]; then
                if ! rm -f "${finals[$index]}"; then
                    printf 'ERROR: Could not remove partially published Step 09 output during rollback: %s\n' \
                        "${finals[$index]}" >&2
                    rollback_failed=true
                fi
            elif [[ -e "${backups[$index]}" ]]; then
                if ! rm -f "${finals[$index]}"; then
                    printf 'ERROR: Could not clear Step 09 output before restoring its backup: %s\n' \
                        "${finals[$index]}" >&2
                    rollback_failed=true
                elif ! mv "${backups[$index]}" "${finals[$index]}"; then
                    printf 'ERROR: Could not restore Step 09 backup during rollback: %s\n' \
                        "${backups[$index]}" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "${finals[$index]}" ]]; then
                printf 'ERROR: Step 09 rollback found neither a final output nor its backup: %s\n' \
                    "${finals[$index]}" >&2
                rollback_failed=true
            fi
        done
        if [[ "$rollback_failed" == true ]]; then
            [[ "$status" -ne 0 ]] || status=1
            printf 'ERROR: Step 09 rollback was incomplete; retaining the owned lock for operator recovery: %s\n' \
                "$lock_path" >&2
        fi
    fi
    if [[ "$scratch_owned" == true && "$publication_committed" == true ]]; then
        for backup in "${backups[@]}"; do rm -f "$backup" || true; done
    fi
    if [[ "$rollback_failed" != true &&
          "${lock_owned:-false}" == true && -d "$lock_path" ]]; then
        rm -f "$lock_owner_tmp" || true
        if [[ "${lock_owner_written:-false}" == true ]]; then
            if [[ -f "$lock_path/owner" ]] &&
               grep -Fqx $'run_token\t'"$run_token" "$lock_path/owner"; then
                rm -f "$lock_path/owner" || true
            fi
        elif [[ -f "$lock_path/owner" ]] &&
             grep -Fqx $'run_token\t'"$run_token" "$lock_path/owner"; then
            # mv may have completed immediately before an interrupt, before
            # lock_owner_written could be flipped to true.
            rm -f "$lock_path/owner" || true
        fi
        rmdir "$lock_path" 2>/dev/null || true
    fi
    exit "$status"
}

arm_signal_traps() {
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

defer_signal_traps() {
    trap 'pending_signal=129' HUP
    trap 'pending_signal=130' INT
    trap 'pending_signal=143' TERM
}

exit_for_pending_signal() {
    local signal_status="$pending_signal"
    if [[ "$signal_status" -ne 0 ]]; then
        pending_signal=0
        exit "$signal_status"
    fi
}

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
