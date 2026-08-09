#!/usr/bin/env bash
# Step 06 generated BAM/index validation and orientation-count receipt helpers.

validate_orientation_outputs() {
    local fwd_bam="$1"
    local fwd_bai="$2"
    local rev_bam="$3"
    local rev_bai="$4"
    local counts_tsv="$5"
    local label="$6"

    # quickcheck catches corrupt BAMs before downstream mpileup consumes the
    # orientation split. BAIs and TSVs are checked for nonempty publication.
    [[ -s "$fwd_bam" ]] || die "$label FWD_like BAM is missing or empty: $fwd_bam"
    "$samtools_bin" quickcheck "$fwd_bam" || die "$label FWD_like BAM failed samtools quickcheck: $fwd_bam"
    [[ -s "$fwd_bai" ]] || die "$label FWD_like BAI is missing or empty: $fwd_bai"

    [[ -s "$rev_bam" ]] || die "$label REV_like BAM is missing or empty: $rev_bam"
    "$samtools_bin" quickcheck "$rev_bam" || die "$label REV_like BAM failed samtools quickcheck: $rev_bam"
    [[ -s "$rev_bai" ]] || die "$label REV_like BAI is missing or empty: $rev_bai"

    [[ -s "$counts_tsv" ]] || die "$label orientation counts TSV is missing or empty: $counts_tsv"
}

write_counts_tsv() {
    local input_records
    local flag_99_records
    local flag_147_records
    local flag_83_records
    local flag_163_records
    local fwd_like_records
    local rev_like_records
    local assigned_records
    local unassigned_records
    local assigned_fraction

    # Counts come from samtools view -c rather than the filter temp files alone,
    # so the QC row reflects the BAM records that downstream tools will see.
    input_records="$("${input_count_command[@]}")"
    flag_99_records="$("${flag_99_count_command[@]}")"
    flag_147_records="$("${flag_147_count_command[@]}")"
    flag_83_records="$("${flag_83_count_command[@]}")"
    flag_163_records="$("${flag_163_count_command[@]}")"
    fwd_like_records="$("${fwd_count_command[@]}")"
    rev_like_records="$("${rev_count_command[@]}")"

    validate_nonnegative_integer "input_records" "$input_records"
    validate_nonnegative_integer "flag_99_records" "$flag_99_records"
    validate_nonnegative_integer "flag_147_records" "$flag_147_records"
    validate_nonnegative_integer "flag_83_records" "$flag_83_records"
    validate_nonnegative_integer "flag_163_records" "$flag_163_records"
    validate_nonnegative_integer "fwd_like_records" "$fwd_like_records"
    validate_nonnegative_integer "rev_like_records" "$rev_like_records"

    [[ "$input_records" -gt 0 ]] || die "input_records is zero; refusing to publish empty Step 06 outputs"
    [[ "$fwd_like_records" -gt 0 ]] || die "fwd_like_records is zero; refusing to publish empty FWD_like output"
    [[ "$rev_like_records" -gt 0 ]] || die "rev_like_records is zero; refusing to publish empty REV_like output"

    assigned_records=$((fwd_like_records + rev_like_records))
    if (( assigned_records > input_records )); then
        die "assigned_records exceeds input_records: $assigned_records > $input_records"
    fi

    unassigned_records=$((input_records - assigned_records))
    # Use awk for portable floating point formatting; POSIX shell arithmetic is
    # integer-only and would silently truncate this QC fraction.
    assigned_fraction="$(awk -v assigned="$assigned_records" -v input="$input_records" 'BEGIN { printf "%.6f", assigned / input }')"

    {
        printf 'sample_id\tinput_records\tflag_99_records\tflag_147_records\tflag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\tassigned_records\tunassigned_records\tassigned_fraction\n'
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$sample_id" \
            "$input_records" \
            "$flag_99_records" \
            "$flag_147_records" \
            "$flag_83_records" \
            "$flag_163_records" \
            "$fwd_like_records" \
            "$rev_like_records" \
            "$assigned_records" \
            "$unassigned_records" \
            "$assigned_fraction"
    } > "$tmp_counts_tsv"
}
