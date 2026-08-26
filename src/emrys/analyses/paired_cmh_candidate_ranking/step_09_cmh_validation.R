read_sample_manifest <- function(path, control, treatment, background) {
    manifest <- read_tsv("Sample manifest", path)
    allowed <- c(
        "sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition",
        "replicate", "notes"
    )
    required <- c(
        "sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition",
        "replicate"
    )
    missing <- setdiff(required, names(manifest))
    unexpected <- setdiff(names(manifest), allowed)
    if (length(missing) > 0L || length(unexpected) > 0L) {
        abort(
            "Step 09 sample manifest schema mismatch; missing: ",
            paste(missing, collapse = ","), "; unexpected: ",
            paste(unexpected, collapse = ",")
        )
    }
    if (nrow(manifest) == 0L) {
        abort("Sample manifest contains no sample rows.")
    }
    for (column in c(
        "sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition"
    )) {
        if (any(is.na(manifest[[column]]) | !nzchar(manifest[[column]]))) {
            abort("Sample manifest contains an empty ", column, ".")
        }
    }
    if (anyDuplicated(manifest$sample_id)) {
        abort("Sample manifest contains duplicate sample_id values.")
    }
    invisible(lapply(manifest$sample_id, function(value) {
        validate_safe_id("sample_id", value)
    }))
    valid_strandedness <- c("forward", "reverse", "unstranded", "unknown")
    if (any(!(manifest$strandedness %in% valid_strandedness))) {
        abort("Sample manifest contains an invalid strandedness value.")
    }
    if (identical(control, treatment)) {
        abort("Control and treatment conditions must be different.")
    }
    if (nzchar(background) && background %in% c(control, treatment)) {
        abort("Background condition must differ from control and treatment.")
    }

    analysis_rows <- manifest$condition %in% c(control, treatment)
    if (!any(manifest$condition == control) ||
        !any(manifest$condition == treatment)) {
        abort("Sample manifest must contain both requested analysis conditions.")
    }
    if (any(is.na(manifest$replicate[analysis_rows]) |
            !nzchar(manifest$replicate[analysis_rows]))) {
        abort("Every control/treatment sample must define replicate.")
    }
    replicate_order <- unique(manifest$replicate[analysis_rows])
    control_replicates <- manifest$replicate[manifest$condition == control]
    treatment_replicates <- manifest$replicate[manifest$condition == treatment]
    if (anyDuplicated(control_replicates) ||
        anyDuplicated(treatment_replicates)) {
        abort("Each condition must contain exactly one sample per replicate.")
    }
    if (!setequal(control_replicates, treatment_replicates)) {
        abort("Control and treatment replicate sets must be identical.")
    }
    if (length(control_replicates) < 2L) {
        abort("Paired CMH analysis requires at least two replicate strata.")
    }
    replicate_order <- replicate_order[replicate_order %in% control_replicates]
    if (length(replicate_order) != length(control_replicates)) {
        abort("Could not establish a deterministic paired replicate order.")
    }
    if (nzchar(background) && !any(manifest$condition == background)) {
        abort("Requested background condition is absent from sample manifest.")
    }

    control_samples <- vapply(replicate_order, function(replicate) {
        manifest$sample_id[
            manifest$condition == control & manifest$replicate == replicate
        ][[1L]]
    }, character(1))
    treatment_samples <- vapply(replicate_order, function(replicate) {
        manifest$sample_id[
            manifest$condition == treatment & manifest$replicate == replicate
        ][[1L]]
    }, character(1))
    background_samples <- if (nzchar(background)) {
        manifest$sample_id[manifest$condition == background]
    } else {
        character()
    }

    list(
        table = manifest, sample_ids = manifest$sample_id,
        replicates = replicate_order, control_samples = control_samples,
        treatment_samples = treatment_samples,
        background_samples = background_samples
    )
}

read_partition_manifest <- function(path) {
    columns <- c("partition_id", "selector_type", "selector_value")
    manifest <- read_tsv("Partition manifest", path, columns)
    if (nrow(manifest) == 0L) {
        abort("Partition manifest contains no partition rows.")
    }
    if (any(is.na(as.matrix(manifest)) | !nzchar(as.matrix(manifest)))) {
        abort("Partition manifest contains an empty required value.")
    }
    if (anyDuplicated(manifest$partition_id)) {
        abort("Partition manifest contains duplicate partition_id values.")
    }
    if (any(!(manifest$selector_type %in% c("region", "regions_file")))) {
        abort("Partition manifest contains an invalid selector_type.")
    }
    invisible(lapply(manifest$partition_id, function(value) {
        validate_safe_id("partition_id", value)
    }))
    manifest
}

validate_step08_inputs <- function(inputs, partitions, cohort_id,
                                   sample_count, sample_hash,
                                   partition_hash) {
    expected_partition <- rep(partitions$partition_id, each = 2L)
    expected_selector_type <- rep(partitions$selector_type, each = 2L)
    expected_selector_value <- rep(partitions$selector_value, each = 2L)
    expected_orientation <- rep(ORIENTATIONS, times = nrow(partitions))
    if (nrow(inputs) != length(expected_partition) ||
        !identical(inputs$partition_id, expected_partition) ||
        !identical(inputs$selector_type, expected_selector_type) ||
        !identical(inputs$selector_value, expected_selector_value) ||
        !identical(inputs$orientation, expected_orientation)) {
        abort(
            "Step 08 input receipt is not the complete declared ",
            "partition x orientation set in required order."
        )
    }
    identity_columns <- c(
        "cohort_id", "sample_manifest_sha256",
        "partition_manifest_sha256", "orientation_policy"
    )
    if (any(vapply(identity_columns, function(column) {
        any(is.na(inputs[[column]]) | !nzchar(inputs[[column]]))
    }, logical(1))) ||
        any(inputs$cohort_id != cohort_id) ||
        any(inputs$sample_manifest_sha256 != sample_hash) ||
        any(inputs$partition_manifest_sha256 != partition_hash) ||
        any(inputs$orientation_policy != ORIENTATION_POLICY)) {
        abort("Step 08 input receipt cohort, hashes, or orientation policy differ.")
    }
    counts <- c(
        "sample_count", "declared_vcf_record_count",
        "observed_vcf_record_count", "observed_alt_allele_count",
        "supported_snv_count", "skipped_symbolic_count",
        "skipped_non_snv_count", "published_candidate_count"
    )
    parsed <- lapply(counts, function(column) {
        values <- parse_nonnegative_integer_vector(
            paste0("Step 08 input receipt ", column), inputs[[column]]
        )
        if (any(is.na(values))) {
            abort("Step 08 input receipt contains missing ", column, ".")
        }
        values
    })
    names(parsed) <- counts
    if (any(parsed$sample_count != sample_count)) {
        abort("Step 08 input receipt sample_count differs from manifest.")
    }
    if (any(
        parsed$observed_alt_allele_count !=
        parsed$supported_snv_count + parsed$skipped_symbolic_count +
        parsed$skipped_non_snv_count
    ) ||
        any(
            parsed$declared_vcf_record_count !=
            parsed$observed_vcf_record_count
        ) ||
        any(parsed$published_candidate_count != parsed$supported_snv_count)) {
        abort("Step 08 input receipt allele/count invariants do not reconcile.")
    }
    for (column in c("step07_receipt_sha256", "vcf_sha256",
                     "annotation_gtf_sha256")) {
        invisible(vapply(inputs[[column]], function(value) {
            validate_hash(paste0("Step 08 input receipt ", column), value)
        }, character(1)))
    }
    required_text <- c(
        "step07_receipt_path", "vcf_path", "annotation_gtf"
    )
    if (any(vapply(required_text, function(column) {
        any(is.na(inputs[[column]]) | !nzchar(inputs[[column]]))
    }, logical(1)))) {
        abort("Step 08 input receipt contains an empty required path.")
    }
    parsed
}

validate_step08_sites <- function(sites, sample_ids, partitions, inputs,
                                  input_counts) {
    expected_columns <- c(
        STEP08_METADATA_COLUMNS, paste0("DP__", sample_ids),
        paste0("AD__", sample_ids), paste0("AF__", sample_ids)
    )
    if (!identical(names(sites), expected_columns)) {
        abort("Step 08 sites table does not have the exact required schema.")
    }
    if (nrow(sites) > 0L) {
        if (anyDuplicated(sites$candidate_id)) {
            abort("Step 08 sites table contains duplicate candidate_id values.")
        }
        if (any(is.na(sites$candidate_id) | !nzchar(sites$candidate_id)) ||
            any(!(sites$partition_id %in% partitions$partition_id)) ||
            any(!(sites$orientation %in% ORIENTATIONS)) ||
            any(is.na(sites$orientation_policy) |
                sites$orientation_policy != ORIENTATION_POLICY)) {
            abort("Step 08 sites table contains invalid identity metadata.")
        }
        canonical <- c("A", "C", "G", "T")
        if (any(!(sites$rna_ref %in% canonical)) ||
            any(!(sites$rna_alt %in% canonical)) ||
            any(sites$rna_ref == sites$rna_alt)) {
            abort("Step 08 sites table contains an invalid RNA substitution.")
        }
    }
    dp <- matrix(NA_real_, nrow = nrow(sites), ncol = length(sample_ids))
    ad <- dp
    af <- dp
    for (index in seq_along(sample_ids)) {
        sample_id <- sample_ids[[index]]
        dp[, index] <- parse_nonnegative_integer_vector(
            paste0("DP__", sample_id), sites[[paste0("DP__", sample_id)]]
        )
        ad[, index] <- parse_nonnegative_integer_vector(
            paste0("AD__", sample_id), sites[[paste0("AD__", sample_id)]]
        )
        af[, index] <- parse_fraction_vector(
            paste0("AF__", sample_id), sites[[paste0("AF__", sample_id)]]
        )
        partial <- xor(is.na(dp[, index]), is.na(ad[, index]))
        if (any(partial)) {
            abort("Step 08 sites table contains one-sided DP/AD missingness.")
        }
        present <- !is.na(dp[, index])
        if (any(ad[present, index] > dp[present, index])) {
            abort("Step 08 sites table contains AD greater than DP.")
        }
        zero <- present & dp[, index] == 0
        positive <- present & dp[, index] > 0
        if (any(zero & (!is.na(af[, index]) | ad[, index] != 0)) ||
            any(positive & is.na(af[, index])) ||
            any(is.na(dp[, index]) & !is.na(af[, index]))) {
            abort("Step 08 sites table contains inconsistent AF missingness.")
        }
        if (any(
            positive &
            abs(af[, index] - ad[, index] / dp[, index]) >
            sqrt(.Machine$double.eps)
        )) {
            abort("Step 08 sites table contains AF inconsistent with AD/DP.")
        }
    }

    input_keys <- paste(inputs$partition_id, inputs$orientation, sep = "\t")
    site_keys <- paste(sites$partition_id, sites$orientation, sep = "\t")
    observed_counts <- tabulate(
        match(site_keys, input_keys), nbins = nrow(inputs)
    )
    if (!identical(
        as.numeric(observed_counts),
        as.numeric(input_counts$published_candidate_count)
    ) || sum(observed_counts) != nrow(sites)) {
        abort("Step 08 receipt published counts do not match sites table.")
    }
    list(dp = dp, ad = ad, af = af)
}
