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
        "  Rscript src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.R \\\n",
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
