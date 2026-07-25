#!/usr/bin/env Rscript

# Step 09: validate the committed Step 08 cohort tables, build explicit
# treatment/control x edited/unedited replicate strata, run paired CMH tests,
# apply one cohort-wide BH correction, and write deterministic tables/plots.
# Publication, locking, and rollback belong to the shell wrapper; this program
# writes only the six explicitly supplied temporary output paths.

options(stringsAsFactors = FALSE, scipen = 999, digits = 15)

ORIENTATIONS <- c("FWD_like", "REV_like")
ORIENTATION_POLICY <- "legacy_provisional_v1"
CMH_ALTERNATIVE <- "two.sided"
MULTIPLE_TESTING_METHOD <- "BH"

STEP08_METADATA_COLUMNS <- c(
    "partition_id", "candidate_id", "orientation", "chromosome", "position",
    "alt_index", "genomic_ref", "genomic_alt", "rna_ref", "rna_alt",
    "annotation_strand", "gene_ids", "transcript_ids", "is_cds",
    "is_five_prime_utr", "is_three_prime_utr", "is_exon", "is_intron",
    "qual", "filter", "info_alt_depth", "orientation_policy"
)

STEP08_INPUT_COLUMNS <- c(
    "cohort_id", "partition_id", "selector_type", "selector_value",
    "orientation", "step07_receipt_path", "step07_receipt_sha256",
    "vcf_path", "vcf_sha256", "sample_manifest_sha256",
    "partition_manifest_sha256", "annotation_gtf", "annotation_gtf_sha256",
    "sample_count", "declared_vcf_record_count", "observed_vcf_record_count",
    "observed_alt_allele_count", "supported_snv_count",
    "skipped_symbolic_count", "skipped_non_snv_count",
    "published_candidate_count", "orientation_policy"
)

RESULT_COLUMNS <- c(
    "analysis_id", "partition_id", "candidate_id", "orientation",
    "chromosome", "position", "alt_index", "genomic_ref", "genomic_alt",
    "rna_ref", "rna_alt", "annotation_strand", "gene_ids",
    "transcript_ids", "is_cds", "is_five_prime_utr",
    "is_three_prime_utr", "is_exon", "is_intron", "qual", "filter",
    "info_alt_depth", "orientation_policy", "control_condition",
    "treatment_condition", "target_rna_change", "replicate_count",
    "test_status", "call_status", "background_condition",
    "background_status", "min_analysis_dp", "mean_analysis_dp",
    "mean_control_af", "mean_treatment_af",
    "treatment_control_difference", "max_background_af", "cmh_statistic",
    "cmh_degrees_freedom", "cmh_p_value", "cmh_fdr_bh",
    "common_odds_ratio"
)

SUMMARY_COLUMNS <- c(
    "analysis_id", "cohort_id", "control_condition", "treatment_condition",
    "background_condition", "target_rna_change", "replicate_count",
    "sample_count", "candidate_count", "target_candidate_count",
    "successfully_tested_count", "not_target_change_count",
    "missing_counts_count", "low_coverage_count", "degenerate_table_count",
    "below_mean_dp_count", "background_not_passed_count",
    "fdr_not_met_count", "effect_not_met_count", "significant_up_count",
    "significant_down_count", "sample_manifest_path",
    "sample_manifest_sha256", "partition_manifest_path",
    "partition_manifest_sha256", "step08_sites_path",
    "step08_sites_sha256", "step08_inputs_path", "step08_inputs_sha256",
    "min_sample_dp", "mean_dp_threshold", "fdr_threshold",
    "common_or_threshold", "absolute_difference_threshold",
    "background_max_fraction", "multiple_testing_method",
    "cmh_alternative", "continuity_correction", "orientation_policy"
)

MUTATION_COLUMNS <- c(
    "analysis_id", "rna_ref", "rna_alt", "mutation_type",
    "candidate_count", "candidate_fraction", "successfully_tested_count",
    "significant_up_count", "significant_down_count"
)

ARGUMENT_NAMES <- c(
    "analysis-id", "cohort-id", "sample-manifest", "partition-manifest",
    "sample-manifest-sha256", "partition-manifest-sha256", "step08-sites",
    "step08-inputs", "step08-sites-sha256", "step08-inputs-sha256",
    "control-condition", "treatment-condition", "rna-ref", "rna-alt",
    "min-sample-dp", "mean-dp-threshold", "fdr-threshold",
    "common-or-threshold", "absolute-difference-threshold",
    "background-condition", "background-max-fraction", "all-sites-output",
    "significant-sites-output", "summary-output",
    "mutation-spectrum-output", "mutation-spectrum-pdf-output",
    "depth-delta-pdf-output"
)

REQUIRED_ARGUMENT_NAMES <- setdiff(ARGUMENT_NAMES, "background-condition")

usage <- function() {
    cat(paste0(
        "Usage:\n",
        "  Rscript scripts/step_09_cmh_editing_site_calling.R \\\n",
        "    --analysis-id ID --cohort-id ID \\\n",
        "    --sample-manifest PATH --partition-manifest PATH \\\n",
        "    --sample-manifest-sha256 SHA256 \\\n",
        "    --partition-manifest-sha256 SHA256 \\\n",
        "    --step08-sites PATH --step08-inputs PATH \\\n",
        "    --step08-sites-sha256 SHA256 --step08-inputs-sha256 SHA256 \\\n",
        "    --control-condition NAME --treatment-condition NAME \\\n",
        "    --rna-ref A --rna-alt G --min-sample-dp 1 \\\n",
        "    --mean-dp-threshold 50 --fdr-threshold 0.05 \\\n",
        "    --common-or-threshold 1.2 \\\n",
        "    --absolute-difference-threshold 0.005 \\\n",
        "    [--background-condition NAME] \\\n",
        "    --background-max-fraction 0.01 \\\n",
        "    --all-sites-output PATH --significant-sites-output PATH \\\n",
        "    --summary-output PATH --mutation-spectrum-output PATH \\\n",
        "    --mutation-spectrum-pdf-output PATH \\\n",
        "    --depth-delta-pdf-output PATH\n"
    ))
}

abort <- function(...) {
    stop(paste0(...), call. = FALSE)
}

parse_arguments <- function(values) {
    if (length(values) == 1L && values[[1L]] %in% c("-h", "--help")) {
        usage()
        quit(status = 0L)
    }
    if (length(values) %% 2L != 0L) {
        abort("Arguments must be supplied as --name value pairs.")
    }
    parsed <- setNames(vector("list", length(ARGUMENT_NAMES)), ARGUMENT_NAMES)
    parsed[["background-condition"]] <- ""
    index <- 1L
    while (index <= length(values)) {
        option <- values[[index]]
        if (!startsWith(option, "--")) {
            abort("Expected an option beginning with --; got: ", option)
        }
        name <- substring(option, 3L)
        if (!(name %in% ARGUMENT_NAMES)) {
            abort("Unknown argument: ", option)
        }
        if (!is.null(parsed[[name]]) && name != "background-condition") {
            abort("Argument supplied more than once: ", option)
        }
        if (name == "background-condition" &&
            nzchar(parsed[["background-condition"]])) {
            abort("Argument supplied more than once: ", option)
        }
        value <- values[[index + 1L]]
        if (!nzchar(value) || startsWith(value, "--")) {
            abort(option, " requires a non-empty value.")
        }
        parsed[[name]] <- value
        index <- index + 2L
    }
    missing <- REQUIRED_ARGUMENT_NAMES[
        vapply(parsed[REQUIRED_ARGUMENT_NAMES], is.null, logical(1))
    ]
    if (length(missing) > 0L) {
        abort("Missing required argument(s): --", paste(missing, collapse = ", --"))
    }
    parsed
}

validate_safe_id <- function(label, value) {
    if (length(value) != 1L ||
        !grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", value)) {
        abort(
            label, " must match [A-Za-z0-9][A-Za-z0-9._-]*; got: ", value
        )
    }
}

validate_hash <- function(label, value) {
    if (length(value) != 1L || !grepl("^[[:xdigit:]]{64}$", value)) {
        abort(label, " is not a 64-character SHA-256 digest: ", value)
    }
    tolower(value)
}

parse_number <- function(label, value, minimum = -Inf, maximum = Inf,
                         minimum_inclusive = TRUE,
                         maximum_inclusive = TRUE) {
    result <- suppressWarnings(as.numeric(value))
    if (length(result) != 1L || is.na(result) || !is.finite(result)) {
        abort(label, " must be a finite number; got: ", value)
    }
    below <- if (minimum_inclusive) result < minimum else result <= minimum
    above <- if (maximum_inclusive) result > maximum else result >= maximum
    if (below || above) {
        abort(label, " is outside its allowed range; got: ", value)
    }
    result
}

parse_positive_integer <- function(label, value) {
    if (!grepl("^[1-9][0-9]*$", value)) {
        abort(label, " must be a positive integer; got: ", value)
    }
    result <- suppressWarnings(as.numeric(value))
    if (!is.finite(result) || result > .Machine$integer.max) {
        abort(label, " exceeds the supported integer range: ", value)
    }
    as.integer(result)
}

validate_nonempty_file <- function(label, path) {
    if (!file.exists(path) || isTRUE(file.info(path)$isdir) ||
        is.na(file.info(path)$size) || file.info(path)$size <= 0L) {
        abort(label, " does not exist or is empty: ", path)
    }
}

normalize_existing_path <- function(path) {
    normalizePath(path, winslash = "/", mustWork = TRUE)
}

sha256_file <- function(path) {
    normalized <- normalize_existing_path(path)
    if (nzchar(Sys.which("sha256sum"))) {
        executable <- Sys.which("sha256sum")
        command_args <- shQuote(normalized)
    } else if (nzchar(Sys.which("shasum"))) {
        executable <- Sys.which("shasum")
        command_args <- c("-a", "256", shQuote(normalized))
    } else {
        abort("Step 09 requires sha256sum or shasum.")
    }
    output <- suppressWarnings(system2(
        executable, args = command_args, stdout = TRUE, stderr = TRUE
    ))
    status <- attr(output, "status")
    if (!is.null(status) && status != 0L) {
        abort("SHA-256 command failed for: ", path)
    }
    joined <- paste(output, collapse = "\n")
    match <- regexpr("[[:xdigit:]]{64}", joined)
    if (match[[1L]] < 0L) {
        abort("Could not parse SHA-256 output for: ", path)
    }
    tolower(regmatches(joined, match))
}

require_matching_hash <- function(label, path, expected) {
    actual <- sha256_file(path)
    if (!identical(actual, expected)) {
        abort(
            label, " SHA-256 mismatch for ", path, "; expected ", expected,
            ", observed ", actual
        )
    }
}

read_tsv <- function(label, path, expected_columns = NULL) {
    validate_nonempty_file(label, path)
    lines <- readLines(path, warn = FALSE)
    if (length(lines) == 0L) {
        abort(label, " is empty: ", path)
    }
    header <- strsplit(sub("\r$", "", lines[[1L]]), "\t", fixed = TRUE)[[1L]]
    if (any(!nzchar(header)) || anyDuplicated(header)) {
        abort(label, " contains an empty or duplicate column name: ", path)
    }
    if (length(lines) > 1L &&
        any(!nzchar(sub("\r$", "", lines[-1L])))) {
        abort(label, " contains a blank data row: ", path)
    }
    table <- tryCatch(
        read.delim(
            path, header = TRUE, sep = "\t", quote = "", comment.char = "",
            check.names = FALSE, stringsAsFactors = FALSE,
            colClasses = "character", na.strings = "NA", fill = FALSE
        ),
        error = function(error) {
            abort(label, " could not be parsed as strict TSV: ", error$message)
        }
    )
    if (!identical(names(table), header)) {
        abort(label, " header could not be preserved exactly: ", path)
    }
    if (!is.null(expected_columns) &&
        !identical(names(table), expected_columns)) {
        abort(
            label, " header does not match the required schema. Expected: ",
            paste(expected_columns, collapse = "\t")
        )
    }
    table
}

write_tsv <- function(table, path) {
    parent <- dirname(path)
    if (!dir.exists(parent)) {
        abort("Output parent directory does not exist: ", parent)
    }
    write.table(
        table, file = path, sep = "\t", quote = FALSE, row.names = FALSE,
        col.names = TRUE, na = "NA", eol = "\n"
    )
    validate_nonempty_file("Written Step 09 output", path)
}

parse_nonnegative_integer_vector <- function(label, values) {
    result <- rep(NA_real_, length(values))
    present <- !is.na(values)
    if (any(present & !grepl("^(0|[1-9][0-9]*)$", values))) {
        bad <- which(present & !grepl("^(0|[1-9][0-9]*)$", values))[[1L]]
        abort(label, " contains a malformed non-negative integer at row ", bad)
    }
    result[present] <- suppressWarnings(as.numeric(values[present]))
    if (any(!is.finite(result[present]) |
            result[present] > .Machine$integer.max)) {
        abort(label, " contains a value outside the supported integer range.")
    }
    result
}

parse_fraction_vector <- function(label, values) {
    result <- rep(NA_real_, length(values))
    present <- !is.na(values)
    result[present] <- suppressWarnings(as.numeric(values[present]))
    if (any(!is.finite(result[present]) |
            result[present] < 0 | result[present] > 1)) {
        abort(label, " contains a malformed fraction outside [0, 1].")
    }
    result
}

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

    observed_counts <- integer(nrow(inputs))
    for (index in seq_len(nrow(inputs))) {
        observed_counts[[index]] <- sum(
            sites$partition_id == inputs$partition_id[[index]] &
            sites$orientation == inputs$orientation[[index]]
        )
    }
    if (!identical(
        as.numeric(observed_counts),
        as.numeric(input_counts$published_candidate_count)
    ) || sum(observed_counts) != nrow(sites)) {
        abort("Step 08 receipt published counts do not match sites table.")
    }
    list(dp = dp, ad = ad, af = af)
}

run_cmh <- function(control_dp, control_ad, treatment_dp, treatment_ad,
                    replicate_names) {
    strata <- array(
        0, dim = c(2L, 2L, length(replicate_names)),
        dimnames = list(
            condition = c("treatment", "control"),
            outcome = c("edited", "unedited"),
            replicate = replicate_names
        )
    )
    for (index in seq_along(replicate_names)) {
        strata["treatment", "edited", index] <- treatment_ad[[index]]
        strata["treatment", "unedited", index] <-
            treatment_dp[[index]] - treatment_ad[[index]]
        strata["control", "edited", index] <- control_ad[[index]]
        strata["control", "unedited", index] <-
            control_dp[[index]] - control_ad[[index]]
    }
    fit <- tryCatch(
        suppressWarnings(stats::mantelhaen.test(
            strata, alternative = CMH_ALTERNATIVE,
            correct = TRUE, exact = FALSE
        )),
        error = function(error) NULL
    )
    if (is.null(fit)) {
        return(NULL)
    }
    statistic <- as.numeric(fit$statistic)
    degrees_freedom <- as.numeric(fit$parameter)
    p_value <- as.numeric(fit$p.value)
    odds_ratio <- as.numeric(fit$estimate)
    valid_or <- length(odds_ratio) == 1L && !is.na(odds_ratio) &&
        !is.nan(odds_ratio) && odds_ratio >= 0 &&
        (is.finite(odds_ratio) || is.infinite(odds_ratio))
    if (length(statistic) != 1L || !is.finite(statistic) || statistic < 0 ||
        length(degrees_freedom) != 1L || !is.finite(degrees_freedom) ||
        degrees_freedom != 1 ||
        length(p_value) != 1L || !is.finite(p_value) ||
        p_value < 0 || p_value > 1 || !valid_or) {
        return(NULL)
    }
    list(
        statistic = statistic, degrees_freedom = degrees_freedom,
        p_value = p_value, odds_ratio = odds_ratio
    )
}

evaluate_candidates <- function(sites, counts, manifest_contract, target_ref,
                                target_alt, min_sample_dp, mean_dp_threshold,
                                fdr_threshold, common_or_threshold,
                                difference_threshold, background_max_fraction) {
    row_count <- nrow(sites)
    test_status <- rep("not_target_change", row_count)
    call_status <- rep("not_tested", row_count)
    background_status <- if (
        length(manifest_contract$background_samples) == 0L
    ) rep("disabled", row_count) else rep("pass", row_count)
    numeric_result <- setNames(
        replicate(11L, rep(NA_real_, row_count), simplify = FALSE),
        c(
            "min_analysis_dp", "mean_analysis_dp", "mean_control_af",
            "mean_treatment_af", "treatment_control_difference",
            "max_background_af", "cmh_statistic", "cmh_degrees_freedom",
            "cmh_p_value", "cmh_fdr_bh", "common_odds_ratio"
        )
    )
    sample_ids <- manifest_contract$sample_ids
    control_index <- match(manifest_contract$control_samples, sample_ids)
    treatment_index <- match(manifest_contract$treatment_samples, sample_ids)
    background_index <- match(manifest_contract$background_samples, sample_ids)
    target <- sites$rna_ref == target_ref & sites$rna_alt == target_alt

    for (row in seq_len(row_count)) {
        control_dp <- counts$dp[row, control_index]
        control_ad <- counts$ad[row, control_index]
        treatment_dp <- counts$dp[row, treatment_index]
        treatment_ad <- counts$ad[row, treatment_index]
        analysis_dp <- c(control_dp, treatment_dp)
        analysis_ad <- c(control_ad, treatment_ad)

        if (!anyNA(analysis_dp) && !anyNA(analysis_ad)) {
            numeric_result$min_analysis_dp[[row]] <- min(analysis_dp)
            numeric_result$mean_analysis_dp[[row]] <- mean(analysis_dp)
            if (all(analysis_dp > 0)) {
                numeric_result$mean_control_af[[row]] <-
                    mean(control_ad / control_dp)
                numeric_result$mean_treatment_af[[row]] <-
                    mean(treatment_ad / treatment_dp)
                numeric_result$treatment_control_difference[[row]] <-
                    numeric_result$mean_treatment_af[[row]] -
                    numeric_result$mean_control_af[[row]]
            }
        }

        if (length(background_index) > 0L) {
            background_dp <- counts$dp[row, background_index]
            background_ad <- counts$ad[row, background_index]
            if (anyNA(background_dp) || anyNA(background_ad)) {
                background_status[[row]] <- "missing_counts"
            } else if (any(background_dp < min_sample_dp)) {
                background_status[[row]] <- "low_coverage"
                if (all(background_dp > 0)) {
                    numeric_result$max_background_af[[row]] <-
                        max(background_ad / background_dp)
                }
            } else {
                numeric_result$max_background_af[[row]] <-
                    max(background_ad / background_dp)
                background_status[[row]] <- if (
                    all(background_ad / background_dp <
                        background_max_fraction)
                ) "pass" else "fail_fraction"
            }
        }

        if (!target[[row]]) {
            next
        }
        if (anyNA(analysis_dp) || anyNA(analysis_ad)) {
            test_status[[row]] <- "missing_counts"
            next
        }
        if (any(analysis_dp < min_sample_dp)) {
            test_status[[row]] <- "low_coverage"
            next
        }
        fit <- run_cmh(
            control_dp, control_ad, treatment_dp, treatment_ad,
            manifest_contract$replicates
        )
        if (is.null(fit)) {
            test_status[[row]] <- "degenerate_table"
            next
        }
        test_status[[row]] <- "tested"
        numeric_result$cmh_statistic[[row]] <- fit$statistic
        numeric_result$cmh_degrees_freedom[[row]] <- fit$degrees_freedom
        numeric_result$cmh_p_value[[row]] <- fit$p_value
        numeric_result$common_odds_ratio[[row]] <- fit$odds_ratio
    }

    tested <- which(test_status == "tested")
    if (length(tested) > 0L) {
        numeric_result$cmh_fdr_bh[tested] <- stats::p.adjust(
            numeric_result$cmh_p_value[tested], method = MULTIPLE_TESTING_METHOD
        )
    }
    for (row in tested) {
        if (!(numeric_result$mean_analysis_dp[[row]] > mean_dp_threshold)) {
            call_status[[row]] <- "below_mean_dp"
        } else if (!(background_status[[row]] %in% c("disabled", "pass"))) {
            call_status[[row]] <- "background_not_passed"
        } else if (!(numeric_result$cmh_fdr_bh[[row]] < fdr_threshold)) {
            call_status[[row]] <- "fdr_not_met"
        } else if (
            numeric_result$common_odds_ratio[[row]] > common_or_threshold &&
            numeric_result$treatment_control_difference[[row]] >
                difference_threshold
        ) {
            call_status[[row]] <- "significant_up"
        } else if (
            numeric_result$common_odds_ratio[[row]] <
                (1 / common_or_threshold) &&
            numeric_result$treatment_control_difference[[row]] <
                -difference_threshold
        ) {
            call_status[[row]] <- "significant_down"
        } else {
            call_status[[row]] <- "effect_not_met"
        }
    }
    c(
        list(
            target = target, test_status = test_status,
            call_status = call_status,
            background_status = background_status
        ),
        numeric_result
    )
}

make_results <- function(arguments, sites, sample_ids, replicate_count,
                         evaluation) {
    background_value <- if (
        nzchar(arguments[["background-condition"]])
    ) arguments[["background-condition"]] else NA_character_
    result <- data.frame(
        analysis_id = rep(arguments[["analysis-id"]], nrow(sites)),
        sites[, STEP08_METADATA_COLUMNS, drop = FALSE],
        control_condition = rep(
            arguments[["control-condition"]], nrow(sites)
        ),
        treatment_condition = rep(
            arguments[["treatment-condition"]], nrow(sites)
        ),
        target_rna_change = rep(
            paste0(arguments[["rna-ref"]], ">", arguments[["rna-alt"]]),
            nrow(sites)
        ),
        replicate_count = rep(replicate_count, nrow(sites)),
        test_status = evaluation$test_status,
        call_status = evaluation$call_status,
        background_condition = rep(background_value, nrow(sites)),
        background_status = evaluation$background_status,
        min_analysis_dp = evaluation$min_analysis_dp,
        mean_analysis_dp = evaluation$mean_analysis_dp,
        mean_control_af = evaluation$mean_control_af,
        mean_treatment_af = evaluation$mean_treatment_af,
        treatment_control_difference =
            evaluation$treatment_control_difference,
        max_background_af = evaluation$max_background_af,
        cmh_statistic = evaluation$cmh_statistic,
        cmh_degrees_freedom = evaluation$cmh_degrees_freedom,
        cmh_p_value = evaluation$cmh_p_value,
        cmh_fdr_bh = evaluation$cmh_fdr_bh,
        common_odds_ratio = evaluation$common_odds_ratio,
        check.names = FALSE
    )
    result <- result[, RESULT_COLUMNS, drop = FALSE]
    sample_columns <- c(
        paste0("DP__", sample_ids), paste0("AD__", sample_ids),
        paste0("AF__", sample_ids)
    )
    result <- cbind(result, sites[, sample_columns, drop = FALSE])
    result
}

make_summary <- function(arguments, manifest_contract, results,
                         sample_hash, partition_hash, sites_hash, inputs_hash,
                         min_sample_dp, mean_dp_threshold, fdr_threshold,
                         common_or_threshold, difference_threshold,
                         background_max_fraction) {
    count_status <- function(column, value) {
        sum(results[[column]] == value)
    }
    background_value <- if (
        nzchar(arguments[["background-condition"]])
    ) arguments[["background-condition"]] else NA_character_
    summary <- data.frame(
        analysis_id = arguments[["analysis-id"]],
        cohort_id = arguments[["cohort-id"]],
        control_condition = arguments[["control-condition"]],
        treatment_condition = arguments[["treatment-condition"]],
        background_condition = background_value,
        target_rna_change = paste0(
            arguments[["rna-ref"]], ">", arguments[["rna-alt"]]
        ),
        replicate_count = length(manifest_contract$replicates),
        sample_count = length(manifest_contract$sample_ids),
        candidate_count = nrow(results),
        target_candidate_count = sum(
            results$rna_ref == arguments[["rna-ref"]] &
            results$rna_alt == arguments[["rna-alt"]]
        ),
        successfully_tested_count = count_status("test_status", "tested"),
        not_target_change_count =
            count_status("test_status", "not_target_change"),
        missing_counts_count = count_status("test_status", "missing_counts"),
        low_coverage_count = count_status("test_status", "low_coverage"),
        degenerate_table_count =
            count_status("test_status", "degenerate_table"),
        below_mean_dp_count = count_status("call_status", "below_mean_dp"),
        background_not_passed_count =
            count_status("call_status", "background_not_passed"),
        fdr_not_met_count = count_status("call_status", "fdr_not_met"),
        effect_not_met_count = count_status("call_status", "effect_not_met"),
        significant_up_count =
            count_status("call_status", "significant_up"),
        significant_down_count =
            count_status("call_status", "significant_down"),
        sample_manifest_path = arguments[["sample-manifest"]],
        sample_manifest_sha256 = sample_hash,
        partition_manifest_path = arguments[["partition-manifest"]],
        partition_manifest_sha256 = partition_hash,
        step08_sites_path = arguments[["step08-sites"]],
        step08_sites_sha256 = sites_hash,
        step08_inputs_path = arguments[["step08-inputs"]],
        step08_inputs_sha256 = inputs_hash,
        min_sample_dp = min_sample_dp,
        mean_dp_threshold = mean_dp_threshold,
        fdr_threshold = fdr_threshold,
        common_or_threshold = common_or_threshold,
        absolute_difference_threshold = difference_threshold,
        background_max_fraction = background_max_fraction,
        multiple_testing_method = MULTIPLE_TESTING_METHOD,
        cmh_alternative = CMH_ALTERNATIVE,
        continuity_correction = TRUE,
        orientation_policy = ORIENTATION_POLICY,
        check.names = FALSE
    )
    summary[, SUMMARY_COLUMNS, drop = FALSE]
}

make_mutation_spectrum <- function(analysis_id, results) {
    references <- rep(c("A", "C", "G", "T"), each = 3L)
    alternates <- unlist(lapply(c("A", "C", "G", "T"), function(reference) {
        setdiff(c("A", "C", "G", "T"), reference)
    }), use.names = FALSE)
    total <- nrow(results)
    rows <- lapply(seq_along(references), function(index) {
        selected <- results$rna_ref == references[[index]] &
            results$rna_alt == alternates[[index]]
        data.frame(
            analysis_id = analysis_id,
            rna_ref = references[[index]],
            rna_alt = alternates[[index]],
            mutation_type = paste0(
                references[[index]], ">", alternates[[index]]
            ),
            candidate_count = sum(selected),
            candidate_fraction = if (total == 0L) 0 else sum(selected) / total,
            successfully_tested_count = sum(
                selected & results$test_status == "tested"
            ),
            significant_up_count = sum(
                selected & results$call_status == "significant_up"
            ),
            significant_down_count = sum(
                selected & results$call_status == "significant_down"
            ),
            stringsAsFactors = FALSE
        )
    })
    spectrum <- do.call(rbind, rows)
    spectrum[, MUTATION_COLUMNS, drop = FALSE]
}

with_pdf <- function(path, title, expression) {
    parent <- dirname(path)
    if (!dir.exists(parent)) {
        abort("PDF parent directory does not exist: ", parent)
    }
    opened <- FALSE
    tryCatch({
        grDevices::pdf(
            path, width = 7, height = 5, paper = "special",
            useDingbats = FALSE, title = title
        )
        opened <- TRUE
        force(expression)
    }, finally = {
        if (opened) {
            grDevices::dev.off()
        }
    })
}

write_mutation_pdf <- function(spectrum, path, analysis_id) {
    with_pdf(path, paste0(analysis_id, " mutation spectrum"), {
        heights <- spectrum$candidate_count
        graphics::barplot(
            heights, names.arg = spectrum$mutation_type, las = 2,
            col = "grey70", border = "grey25",
            ylim = c(0, max(1, heights) * 1.1),
            main = paste0(analysis_id, " mutation spectrum"),
            ylab = "Candidate sites", xlab = "RNA substitution"
        )
    })
}

write_depth_delta_pdf <- function(results, path, analysis_id,
                                  mean_dp_threshold, difference_threshold) {
    tested <- results$test_status == "tested"
    with_pdf(path, paste0(analysis_id, " depth and editing delta"), {
        if (!any(tested)) {
            graphics::plot.new()
            graphics::title(main = paste0(analysis_id, " depth and editing delta"))
            graphics::text(
                0.5, 0.5, "No successfully tested target candidates"
            )
        } else {
            x <- results$mean_analysis_dp[tested]
            y <- results$treatment_control_difference[tested]
            status <- results$call_status[tested]
            point_color <- ifelse(
                status == "significant_up", "firebrick3",
                ifelse(status == "significant_down", "steelblue3", "grey55")
            )
            x_range <- range(c(
                x, if (mean_dp_threshold > 0) mean_dp_threshold else numeric()
            ))
            if (diff(x_range) == 0) {
                x_range <- x_range * c(0.8, 1.2)
            }
            y_range <- range(c(y, -difference_threshold,
                               difference_threshold, 0))
            if (diff(y_range) == 0) {
                y_range <- y_range + c(-0.01, 0.01)
            }
            graphics::plot(
                x, y, log = "x", xlim = x_range, ylim = y_range,
                pch = 16, cex = 0.7, col = point_color,
                main = paste0(analysis_id, " depth and editing delta"),
                xlab = "Mean analysis depth",
                ylab = "Treatment - control editing fraction"
            )
            if (mean_dp_threshold > 0) {
                graphics::abline(
                    v = mean_dp_threshold, lty = 2, col = "grey35"
                )
            }
            graphics::abline(
                h = c(-difference_threshold, difference_threshold),
                lty = 2, col = "grey35"
            )
            graphics::abline(h = 0, lty = 3, col = "grey65")
        }
    })
}

validate_pdf <- function(label, path) {
    validate_nonempty_file(label, path)
    connection <- file(path, open = "rb")
    on.exit(close(connection), add = TRUE)
    bytes <- readBin(connection, what = "raw", n = file.info(path)$size)
    if (length(bytes) < 10L ||
        !identical(bytes[seq_len(5L)], charToRaw("%PDF-"))) {
        abort(label, " is missing the PDF signature: ", path)
    }
    tail_start <- max(1L, length(bytes) - 2047L)
    tail_bytes <- bytes[tail_start:length(bytes)]
    eof_signature <- charToRaw("%%EOF")
    possible <- seq_len(length(tail_bytes) - length(eof_signature) + 1L)
    has_eof <- any(vapply(possible, function(index) {
        identical(
            tail_bytes[index:(index + length(eof_signature) - 1L)],
            eof_signature
        )
    }, logical(1)))
    if (!has_eof) {
        abort(label, " is missing the PDF EOF marker: ", path)
    }
}

main <- function() {
    arguments <- parse_arguments(commandArgs(trailingOnly = TRUE))
    validate_safe_id("analysis_id", arguments[["analysis-id"]])
    validate_safe_id("cohort_id", arguments[["cohort-id"]])
    validate_safe_id("control_condition", arguments[["control-condition"]])
    validate_safe_id("treatment_condition", arguments[["treatment-condition"]])
    if (nzchar(arguments[["background-condition"]])) {
        validate_safe_id(
            "background_condition", arguments[["background-condition"]]
        )
    }
    target_ref <- toupper(arguments[["rna-ref"]])
    target_alt <- toupper(arguments[["rna-alt"]])
    if (!(target_ref %in% c("A", "C", "G", "T")) ||
        !(target_alt %in% c("A", "C", "G", "T")) ||
        target_ref == target_alt) {
        abort("Target RNA change must be two different canonical DNA bases.")
    }
    arguments[["rna-ref"]] <- target_ref
    arguments[["rna-alt"]] <- target_alt

    min_sample_dp <- parse_positive_integer(
        "min_sample_dp", arguments[["min-sample-dp"]]
    )
    mean_dp_threshold <- parse_number(
        "mean_dp_threshold", arguments[["mean-dp-threshold"]], minimum = 0
    )
    fdr_threshold <- parse_number(
        "fdr_threshold", arguments[["fdr-threshold"]],
        minimum = 0, maximum = 1, minimum_inclusive = FALSE
    )
    common_or_threshold <- parse_number(
        "common_or_threshold", arguments[["common-or-threshold"]],
        minimum = 1, minimum_inclusive = FALSE
    )
    difference_threshold <- parse_number(
        "absolute_difference_threshold",
        arguments[["absolute-difference-threshold"]],
        minimum = 0, maximum = 1
    )
    background_max_fraction <- parse_number(
        "background_max_fraction",
        arguments[["background-max-fraction"]],
        minimum = 0, maximum = 1,
        minimum_inclusive = FALSE, maximum_inclusive = FALSE
    )

    sample_hash <- validate_hash(
        "sample_manifest_sha256", arguments[["sample-manifest-sha256"]]
    )
    partition_hash <- validate_hash(
        "partition_manifest_sha256",
        arguments[["partition-manifest-sha256"]]
    )
    sites_hash <- validate_hash(
        "step08_sites_sha256", arguments[["step08-sites-sha256"]]
    )
    inputs_hash <- validate_hash(
        "step08_inputs_sha256", arguments[["step08-inputs-sha256"]]
    )
    input_paths <- c(
        arguments[["sample-manifest"]], arguments[["partition-manifest"]],
        arguments[["step08-sites"]], arguments[["step08-inputs"]]
    )
    invisible(lapply(seq_along(input_paths), function(index) {
        validate_nonempty_file("Step 09 input", input_paths[[index]])
    }))
    require_matching_hash(
        "Sample manifest", arguments[["sample-manifest"]], sample_hash
    )
    require_matching_hash(
        "Partition manifest", arguments[["partition-manifest"]],
        partition_hash
    )
    require_matching_hash(
        "Step 08 sites", arguments[["step08-sites"]], sites_hash
    )
    require_matching_hash(
        "Step 08 inputs", arguments[["step08-inputs"]], inputs_hash
    )

    manifest_contract <- read_sample_manifest(
        arguments[["sample-manifest"]],
        arguments[["control-condition"]],
        arguments[["treatment-condition"]],
        arguments[["background-condition"]]
    )
    partitions <- read_partition_manifest(arguments[["partition-manifest"]])
    inputs <- read_tsv(
        "Step 08 input receipt", arguments[["step08-inputs"]],
        STEP08_INPUT_COLUMNS
    )
    input_counts <- validate_step08_inputs(
        inputs, partitions, arguments[["cohort-id"]],
        length(manifest_contract$sample_ids), sample_hash, partition_hash
    )
    sites <- read_tsv("Step 08 sites", arguments[["step08-sites"]])
    counts <- validate_step08_sites(
        sites, manifest_contract$sample_ids, partitions, inputs, input_counts
    )

    evaluation <- evaluate_candidates(
        sites, counts, manifest_contract, target_ref, target_alt,
        min_sample_dp, mean_dp_threshold, fdr_threshold,
        common_or_threshold, difference_threshold, background_max_fraction
    )
    results <- make_results(
        arguments, sites, manifest_contract$sample_ids,
        length(manifest_contract$replicates), evaluation
    )
    significant <- results[
        results$call_status %in% c("significant_up", "significant_down"),
        , drop = FALSE
    ]
    summary <- make_summary(
        arguments, manifest_contract, results, sample_hash, partition_hash,
        sites_hash, inputs_hash, min_sample_dp, mean_dp_threshold,
        fdr_threshold, common_or_threshold, difference_threshold,
        background_max_fraction
    )
    spectrum <- make_mutation_spectrum(arguments[["analysis-id"]], results)

    write_tsv(results, arguments[["all-sites-output"]])
    write_tsv(significant, arguments[["significant-sites-output"]])
    write_tsv(summary, arguments[["summary-output"]])
    write_tsv(spectrum, arguments[["mutation-spectrum-output"]])
    write_mutation_pdf(
        spectrum, arguments[["mutation-spectrum-pdf-output"]],
        arguments[["analysis-id"]]
    )
    write_depth_delta_pdf(
        results, arguments[["depth-delta-pdf-output"]],
        arguments[["analysis-id"]], mean_dp_threshold, difference_threshold
    )
    validate_pdf(
        "Step 09 mutation spectrum PDF",
        arguments[["mutation-spectrum-pdf-output"]]
    )
    validate_pdf(
        "Step 09 depth/delta PDF",
        arguments[["depth-delta-pdf-output"]]
    )

    expected_result_columns <- c(
        RESULT_COLUMNS, paste0("DP__", manifest_contract$sample_ids),
        paste0("AD__", manifest_contract$sample_ids),
        paste0("AF__", manifest_contract$sample_ids)
    )
    if (!identical(names(results), expected_result_columns) ||
        !identical(names(significant), expected_result_columns) ||
        !identical(names(summary), SUMMARY_COLUMNS) ||
        !identical(names(spectrum), MUTATION_COLUMNS) ||
        nrow(significant) !=
            sum(results$call_status %in%
                c("significant_up", "significant_down")) ||
        nrow(spectrum) != 12L) {
        abort("Internal Step 09 output reconciliation failed.")
    }
    message(
        "Step 09 completed: ", nrow(results), " candidates, ",
        sum(results$test_status == "tested"), " successfully tested, ",
        nrow(significant), " significant."
    )
}

main()
