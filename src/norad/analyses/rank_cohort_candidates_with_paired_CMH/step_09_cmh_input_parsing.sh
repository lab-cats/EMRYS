# Step 09 input parsing and shared validation helpers.
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

# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"


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
