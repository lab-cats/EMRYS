# Owner-private Step 07 receipt reconciliation for Step 08.

resolve_receipt_vcf_path <- function(path) {
    if (!file.exists(path)) {
        abort("Step 07 receipt declares a VCF path that does not exist: ", path)
    }
    normalize_existing_path(path)
}

validate_step07_receipt <- function(
    path, cohort_id, partition, sample_ids, sample_hash, partition_hash,
    step07_root
) {
    receipt <- read_tsv(
        paste0("Step 07 receipt for partition ", partition$partition_id),
        path,
        STEP07_RECEIPT_COLUMNS
    )
    if (nrow(receipt) != 2L) {
        abort("Step 07 receipt must contain exactly two rows: ", path)
    }
    if (!identical(receipt$orientation, ORIENTATIONS)) {
        abort(
            "Step 07 receipt orientations must be exactly ",
            paste(ORIENTATIONS, collapse = " then "), ": ",
            path
        )
    }
    required_values <- as.matrix(receipt)
    if (any(is.na(required_values) | !nzchar(required_values))) {
        abort("Step 07 receipt contains an empty required value: ", path)
    }
    if (any(receipt$cohort_id != cohort_id) ||
        any(receipt$partition_id != partition$partition_id) ||
        any(receipt$selector_type != partition$selector_type) ||
        any(receipt$selector_value != partition$selector_value)) {
        abort(
            "Step 07 receipt cohort, partition, or selector does not match ",
            "the declared Step 08 inputs: ", path
        )
    }
    if (any(tolower(receipt$sample_manifest_sha256) != sample_hash) ||
        any(tolower(receipt$partition_manifest_sha256) != partition_hash)) {
        abort("Step 07 receipt manifest hash mismatch: ", path)
    }
    sample_counts <- vapply(
        seq_len(nrow(receipt)),
        function(index) parse_nonnegative_integer(
            "Step 07 receipt sample_count", receipt$sample_count[[index]]
        ),
        integer(1)
    )
    if (any(sample_counts != length(sample_ids))) {
        abort("Step 07 receipt sample_count mismatch: ", path)
    }
    declared_counts <- vapply(
        seq_len(nrow(receipt)),
        function(index) parse_nonnegative_integer(
            "Step 07 receipt vcf_record_count",
            receipt$vcf_record_count[[index]]
        ),
        integer(1)
    )

    for (index in seq_len(nrow(receipt))) {
        expected <- file.path(
            step07_root, cohort_id, partition$partition_id,
            paste0(
                cohort_id, ".", partition$partition_id, ".",
                receipt$orientation[[index]], ".mpileup.vcf"
            )
        )
        validate_nonempty_file(
            paste0("Step 07 ", receipt$orientation[[index]], " VCF"), expected
        )
        declared <- resolve_receipt_vcf_path(receipt$vcf_path[[index]])
        if (!identical(declared, normalize_existing_path(expected))) {
            abort(
                "Step 07 receipt VCF path does not match the required path for ",
                receipt$orientation[[index]], ": ", path
            )
        }
    }
    list(receipt = receipt, declared_counts = declared_counts)
}

