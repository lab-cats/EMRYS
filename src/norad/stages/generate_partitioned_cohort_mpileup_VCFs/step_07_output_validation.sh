#!/usr/bin/env bash
# Step 07 generated VCF and receipt validation helpers.

validate_vcf() {
    local label="$1"
    local path="$2"
    local expected_samples="$3"
    local observed_samples

    [[ -s "$path" ]] || die "$label VCF does not exist or is empty: $path"
    "$bcftools_bin" view -h "$path" >/dev/null ||
        die "$label VCF header validation failed: $path"
    observed_samples="$("$bcftools_bin" query -l "$path")" ||
        die "$label VCF sample query failed: $path"
    if [[ "$observed_samples" != "$expected_samples" ]]; then
        printf 'ERROR: %s VCF sample order does not match the sample manifest: %s\n' "$label" "$path" >&2
        printf 'Expected samples:\n%s\n' "$expected_samples" >&2
        printf 'Observed samples:\n%s\n' "$observed_samples" >&2
        exit 1
    fi
}

vcf_record_count() {
    local path="$1"
    "$bcftools_bin" view -H "$path" | awk 'END { print NR + 0 }'
}

validate_receipt() {
    local path="$1"
    local expected_header
    local observed_header
    local row_count

    expected_header=$'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tvcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\tsample_count\tvcf_record_count'
    [[ -s "$path" ]] || die "Step 07 receipt does not exist or is empty: $path"
    IFS= read -r observed_header < "$path"
    [[ "$observed_header" == "$expected_header" ]] ||
        die "Step 07 receipt header is invalid: $path"
    row_count="$(awk 'END { print NR - 1 }' "$path")"
    [[ "$row_count" == "2" ]] ||
        die "Step 07 receipt must contain exactly two data rows; got $row_count: $path"
}
