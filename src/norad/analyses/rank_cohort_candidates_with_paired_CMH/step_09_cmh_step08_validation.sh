# Step 09 Step 08 input/output contract helpers.

validate_step08_inputs() {
    local path="$1"
    local expected_header
    expected_header=$'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tstep07_receipt_path\tstep07_receipt_sha256\tvcf_path\tvcf_sha256\tsample_manifest_sha256\tpartition_manifest_sha256\tannotation_gtf\tannotation_gtf_sha256\tsample_count\tdeclared_vcf_record_count\tobserved_vcf_record_count\tobserved_alt_allele_count\tsupported_snv_count\tskipped_symbolic_count\tskipped_non_snv_count\tpublished_candidate_count\torientation_policy'
    validate_exact_header "Step 08 input receipt" "$path" "$expected_header"
    awk -F '\t' \
        -v cohort="$cohort_id" \
        -v sample_hash="$sample_manifest_sha256" \
        -v partition_hash="$partition_manifest_sha256" \
        -v samples="$sample_count" \
        -v fwd_orientation="${ORIENTATIONS[0]}" \
        -v rev_orientation="${ORIENTATIONS[1]}" \
        -v orientation_policy="$ORIENTATION_POLICY" \
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
            if (((row - 1) % 2) == 0) {
                orientation = fwd_orientation
            } else {
                orientation = rev_orientation
            }
            if (NF != 22 || partition_index > partition_count ||
                $1 != cohort || $2 != ids[partition_index] ||
                $3 != types[partition_index] || $4 != values[partition_index] ||
                $5 != orientation || $10 != sample_hash ||
                $11 != partition_hash || $14 != samples ||
                $22 != orientation_policy) exit 1
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
        -v fwd_orientation="${ORIENTATIONS[0]}" \
        -v rev_orientation="${ORIENTATIONS[1]}" \
        -v orientation_policy="$ORIENTATION_POLICY" \
        -v partition_csv="$partition_ids_csv" '
        function absolute(value) { if (value < 0) return -value; return value }
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
                ($3 != fwd_orientation && $3 != rev_orientation) ||
                !(key in expected) ||
                $22 != orientation_policy || $2 == "" || seen[$2]++) exit 1
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
