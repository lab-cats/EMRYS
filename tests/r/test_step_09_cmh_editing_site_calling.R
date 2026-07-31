#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, scipen = 999, digits = 15)

command_values <- commandArgs(trailingOnly = FALSE)
file_value <- command_values[grepl("^--file=", command_values)]
if (length(file_value) != 1L) {
    stop("Could not resolve the Step 09 R fixture path.", call. = FALSE)
}
test_path <- normalizePath(sub("^--file=", "", file_value), mustWork = TRUE)
repo_root <- normalizePath(
    file.path(dirname(test_path), "..", ".."), mustWork = TRUE
)
engine <- file.path(repo_root, "scripts", "step_09_cmh_editing_site_calling.R")
rscript_bin <- file.path(R.home("bin"), "Rscript")

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

assert_true <- function(value, message) {
    if (length(value) != 1L || is.na(value) || !value) {
        stop(message, call. = FALSE)
    }
}

assert_identical <- function(actual, expected, message) {
    if (!identical(actual, expected)) {
        stop(
            message, "\nExpected: ", paste(expected, collapse = ", "),
            "\nObserved: ", paste(actual, collapse = ", "), call. = FALSE
        )
    }
}

assert_near <- function(actual, expected, tolerance, message) {
    if (length(actual) != 1L || is.na(actual) ||
        abs(actual - expected) > tolerance) {
        stop(
            message, "; expected ", expected, ", observed ", actual,
            call. = FALSE
        )
    }
}

assert_number_near <- function(actual, expected, tolerance, message) {
    if (is.infinite(expected)) {
        assert_true(
            length(actual) == 1L && identical(actual, expected),
            paste0(message, "; expected ", expected, ", observed ", actual)
        )
    } else {
        assert_near(actual, expected, tolerance, message)
    }
}

write_tsv <- function(table, path) {
    write.table(
        table, path, sep = "\t", quote = FALSE, row.names = FALSE,
        col.names = TRUE, na = "NA", eol = "\n"
    )
}

read_tsv <- function(path) {
    read.delim(
        path, sep = "\t", quote = "", comment.char = "",
        check.names = FALSE, stringsAsFactors = FALSE, na.strings = "NA"
    )
}

parse_count_vector <- function(value) {
    tokens <- strsplit(as.character(value), ",", fixed = TRUE)[[1L]]
    result <- suppressWarnings(as.numeric(tokens))
    result[tokens == "NA"] <- NA_real_
    assert_true(
        all(tokens == "NA" | grepl("^(0|[1-9][0-9]*)$", tokens)) &&
            all(is.na(result) | is.finite(result)),
        paste("Malformed count vector in independent CMH corpus:", value)
    )
    result
}

load_engine_run_cmh <- function() {
    expressions <- as.list(parse(engine))
    scope <- new.env(parent = baseenv())
    evaluate_assignment <- function(name) {
        matches <- vapply(expressions, function(expression) {
            is.call(expression) &&
                identical(expression[[1L]], as.name("<-")) &&
                is.symbol(expression[[2L]]) &&
                identical(as.character(expression[[2L]]), name)
        }, logical(1))
        assert_true(
            sum(matches) == 1L,
            paste("Expected one committed Step 09 assignment for", name)
        )
        eval(expressions[[which(matches)]], envir = scope)
    }
    evaluate_assignment("CMH_ALTERNATIVE")
    evaluate_assignment("run_cmh")
    assert_true(
        is.function(scope$run_cmh),
        "Committed Step 09 run_cmh assignment did not define a function."
    )
    scope$run_cmh
}

assert_independent_cmh_corpus <- function() {
    corpus_path <- file.path(
        repo_root, "tests", "fixtures", "step_09_cmh_oracle.tsv"
    )
    corpus <- read_tsv(corpus_path)
    expected_header <- c(
        "case_id", "requirement_tags", "bh_family", "min_sample_dp",
        "control_dp", "control_ad", "treatment_dp", "treatment_ad",
        "expected_status", "expected_statistic", "expected_p_value",
        "expected_common_odds_ratio", "expected_bh"
    )
    assert_identical(
        names(corpus), expected_header,
        "Independent CMH corpus schema changed."
    )
    assert_true(
        nrow(corpus) > 0L && !anyDuplicated(corpus$case_id),
        "Independent CMH corpus must be nonempty with unique case IDs."
    )
    run_cmh <- load_engine_run_cmh()
    observed_p <- rep(NA_real_, nrow(corpus))
    for (row in seq_len(nrow(corpus))) {
        control_dp <- parse_count_vector(corpus$control_dp[[row]])
        control_ad <- parse_count_vector(corpus$control_ad[[row]])
        treatment_dp <- parse_count_vector(corpus$treatment_dp[[row]])
        treatment_ad <- parse_count_vector(corpus$treatment_ad[[row]])
        lengths <- c(
            length(control_dp), length(control_ad),
            length(treatment_dp), length(treatment_ad)
        )
        assert_true(
            length(unique(lengths)) == 1L && lengths[[1L]] >= 2L,
            paste("Corpus count-vector length mismatch:", corpus$case_id[[row]])
        )
        all_dp <- c(control_dp, treatment_dp)
        all_ad <- c(control_ad, treatment_ad)
        if (anyNA(c(all_dp, all_ad))) {
            observed_status <- "missing_counts"
            fit <- NULL
        } else if (any(all_dp < corpus$min_sample_dp[[row]])) {
            observed_status <- "low_coverage"
            fit <- NULL
        } else {
            fit <- run_cmh(
                control_dp, control_ad, treatment_dp, treatment_ad,
                paste0("r", seq_along(control_dp))
            )
            observed_status <- if (
                is.null(fit)
            ) "degenerate_table" else "tested"
        }
        assert_identical(
            observed_status, corpus$expected_status[[row]],
            paste("Committed Step 09 status differs for", corpus$case_id[[row]])
        )
        if (observed_status == "tested") {
            assert_number_near(
                fit$statistic, corpus$expected_statistic[[row]], 1e-12,
                paste("CMH statistic differs for", corpus$case_id[[row]])
            )
            assert_number_near(
                fit$p_value, corpus$expected_p_value[[row]], 1e-15,
                paste("CMH p-value differs for", corpus$case_id[[row]])
            )
            assert_number_near(
                fit$odds_ratio,
                corpus$expected_common_odds_ratio[[row]], 1e-12,
                paste("Common odds ratio differs for", corpus$case_id[[row]])
            )
            observed_p[[row]] <- fit$p_value
        } else {
            assert_true(
                all(is.na(c(
                    corpus$expected_statistic[[row]],
                    corpus$expected_p_value[[row]],
                    corpus$expected_common_odds_ratio[[row]]
                ))),
                paste(
                    "Untested corpus row contains expected CMH values:",
                    corpus$case_id[[row]]
                )
            )
        }
    }
    family <- which(!is.na(corpus$bh_family) & corpus$bh_family == "primary")
    assert_true(
        length(family) > 1L && all(is.finite(observed_p[family])),
        "Independent CMH corpus BH family is not fully tested."
    )
    adjusted <- stats::p.adjust(observed_p[family], method = "BH")
    assert_true(
        max(abs(adjusted - corpus$expected_bh[family])) <= 1e-15,
        "Committed Step 09 global BH behavior differs from the corpus."
    )
}

sha256_file <- function(path) {
    if (nzchar(Sys.which("sha256sum"))) {
        executable <- Sys.which("sha256sum")
        arguments <- shQuote(normalizePath(path, mustWork = TRUE))
    } else {
        executable <- Sys.which("shasum")
        assert_true(nzchar(executable), "Tests require sha256sum or shasum.")
        arguments <- c(
            "-a", "256", shQuote(normalizePath(path, mustWork = TRUE))
        )
    }
    output <- system2(executable, arguments, stdout = TRUE)
    match <- regexpr("[[:xdigit:]]{64}", paste(output, collapse = "\n"))
    tolower(regmatches(paste(output, collapse = "\n"), match))
}

sample_table <- function(include_background = FALSE) {
    table <- data.frame(
        sample_id = c(
            "ABE_EV_2", "ABE_EV_3", "ABE_EV4",
            "ABE_PUM1_2", "ABE_PUM1_3", "ABE_PUM1_4"
        ),
        r1_fastq = paste0("reads/r1_", seq_len(6), ".fastq.gz"),
        r2_fastq = paste0("reads/r2_", seq_len(6), ".fastq.gz"),
        strandedness = rep("reverse", 6),
        condition = c(rep("EV", 3), rep("PUM1", 3)),
        replicate = c("2", "3", "4", "2", "3", "4"),
        stringsAsFactors = FALSE
    )
    if (include_background) {
        table <- rbind(
            table,
            data.frame(
                sample_id = c("BG_1", "BG_2"),
                r1_fastq = c("reads/bg1_R1.fastq.gz",
                             "reads/bg2_R1.fastq.gz"),
                r2_fastq = c("reads/bg1_R2.fastq.gz",
                             "reads/bg2_R2.fastq.gz"),
                strandedness = c("reverse", "reverse"),
                condition = c("NODOX", "NODOX"),
                replicate = c("B1", "B2"),
                stringsAsFactors = FALSE
            )
        )
    }
    table
}

site_row <- function(candidate_id, partition_id, orientation, rna_ref,
                     rna_alt, dp, ad, sample_ids) {
    stopifnot(length(dp) == length(sample_ids), length(ad) == length(sample_ids))
    af <- ifelse(is.na(dp) | dp == 0, NA_real_, ad / dp)
    values <- c(
        list(
            partition_id = partition_id,
            candidate_id = candidate_id,
            orientation = orientation,
            chromosome = if (partition_id == "p1") "1" else "2",
            position = as.character(100L + nchar(candidate_id)),
            alt_index = "1",
            genomic_ref = rna_ref,
            genomic_alt = rna_alt,
            rna_ref = rna_ref,
            rna_alt = rna_alt,
            annotation_strand = "+",
            gene_ids = "GENE1",
            transcript_ids = "TX1",
            is_cds = "TRUE",
            is_five_prime_utr = "FALSE",
            is_three_prime_utr = "FALSE",
            is_exon = "TRUE",
            is_intron = "FALSE",
            qual = "60",
            filter = "PASS",
            info_alt_depth = as.character(sum(ad, na.rm = TRUE)),
            orientation_policy = "legacy_provisional_v1"
        ),
        setNames(as.list(dp), paste0("DP__", sample_ids)),
        setNames(as.list(ad), paste0("AD__", sample_ids)),
        setNames(as.list(af), paste0("AF__", sample_ids))
    )
    as.data.frame(values, check.names = FALSE, stringsAsFactors = FALSE)
}

empty_sites <- function(sample_ids) {
    columns <- c(
        STEP08_METADATA_COLUMNS, paste0("DP__", sample_ids),
        paste0("AD__", sample_ids), paste0("AF__", sample_ids)
    )
    setNames(
        as.data.frame(
            replicate(length(columns), character(), simplify = FALSE),
            check.names = FALSE
        ),
        columns
    )
}

make_fixture <- function(root, rows, include_background = FALSE) {
    dir.create(root, recursive = TRUE)
    samples <- sample_table(include_background)
    sample_path <- file.path(root, "samples.tsv")
    partition_path <- file.path(root, "partitions.tsv")
    sites_path <- file.path(root, "cohort.step08_sites.tsv")
    inputs_path <- file.path(root, "cohort.step08_inputs.tsv")
    write_tsv(samples, sample_path)
    partitions <- data.frame(
        partition_id = c("p1", "p2"),
        selector_type = c("region", "region"),
        selector_value = c("1", "2"),
        stringsAsFactors = FALSE
    )
    write_tsv(partitions, partition_path)
    sites <- if (length(rows) == 0L) {
        empty_sites(samples$sample_id)
    } else {
        do.call(rbind, rows)
    }
    expected_site_columns <- c(
        STEP08_METADATA_COLUMNS, paste0("DP__", samples$sample_id),
        paste0("AD__", samples$sample_id), paste0("AF__", samples$sample_id)
    )
    sites <- sites[, expected_site_columns, drop = FALSE]
    write_tsv(sites, sites_path)
    sample_hash <- sha256_file(sample_path)
    partition_hash <- sha256_file(partition_path)
    combinations <- data.frame(
        partition_id = rep(partitions$partition_id, each = 2L),
        selector_type = rep(partitions$selector_type, each = 2L),
        selector_value = rep(partitions$selector_value, each = 2L),
        orientation = rep(c("FWD_like", "REV_like"), 2L),
        stringsAsFactors = FALSE
    )
    published <- vapply(seq_len(nrow(combinations)), function(index) {
        sum(
            sites$partition_id == combinations$partition_id[[index]] &
            sites$orientation == combinations$orientation[[index]]
        )
    }, integer(1))
    inputs <- data.frame(
        cohort_id = rep("NORAD_EV_PUM1", 4),
        partition_id = combinations$partition_id,
        selector_type = combinations$selector_type,
        selector_value = combinations$selector_value,
        orientation = combinations$orientation,
        step07_receipt_path = paste0("receipt_", seq_len(4), ".tsv"),
        step07_receipt_sha256 = rep(strrep("a", 64), 4),
        vcf_path = paste0("input_", seq_len(4), ".vcf"),
        vcf_sha256 = rep(strrep("b", 64), 4),
        sample_manifest_sha256 = rep(sample_hash, 4),
        partition_manifest_sha256 = rep(partition_hash, 4),
        annotation_gtf = rep("refs/genome.gtf", 4),
        annotation_gtf_sha256 = rep(strrep("c", 64), 4),
        sample_count = rep(nrow(samples), 4),
        declared_vcf_record_count = published,
        observed_vcf_record_count = published,
        observed_alt_allele_count = published,
        supported_snv_count = published,
        skipped_symbolic_count = rep(0, 4),
        skipped_non_snv_count = rep(0, 4),
        published_candidate_count = published,
        orientation_policy = rep("legacy_provisional_v1", 4),
        check.names = FALSE
    )
    inputs <- inputs[, STEP08_INPUT_COLUMNS, drop = FALSE]
    write_tsv(inputs, inputs_path)
    list(
        samples = samples, sample_path = sample_path,
        partition_path = partition_path, sites_path = sites_path,
        inputs_path = inputs_path, sample_hash = sample_hash,
        partition_hash = partition_hash,
        sites_hash = sha256_file(sites_path),
        inputs_hash = sha256_file(inputs_path)
    )
}

run_engine <- function(fixture, output_dir, background = NULL,
                       overrides = list(), expect_success = TRUE) {
    dir.create(output_dir, recursive = TRUE)
    outputs <- list(
        all = file.path(output_dir, "all.tsv"),
        significant = file.path(output_dir, "significant.tsv"),
        summary = file.path(output_dir, "summary.tsv"),
        mutation = file.path(output_dir, "mutation.tsv"),
        mutation_pdf = file.path(output_dir, "mutation.pdf"),
        depth_pdf = file.path(output_dir, "depth.pdf")
    )
    policy <- list(
        `min-sample-dp` = "1", `mean-dp-threshold` = "50",
        `fdr-threshold` = "0.05", `common-or-threshold` = "1.2",
        `absolute-difference-threshold` = "0.005",
        `background-max-fraction` = "0.01"
    )
    policy[names(overrides)] <- overrides
    arguments <- c(
        "--analysis-id", "cmh_fixture",
        "--cohort-id", "NORAD_EV_PUM1",
        "--sample-manifest", fixture$sample_path,
        "--partition-manifest", fixture$partition_path,
        "--sample-manifest-sha256", fixture$sample_hash,
        "--partition-manifest-sha256", fixture$partition_hash,
        "--step08-sites", fixture$sites_path,
        "--step08-inputs", fixture$inputs_path,
        "--step08-sites-sha256", fixture$sites_hash,
        "--step08-inputs-sha256", fixture$inputs_hash,
        "--control-condition", "EV",
        "--treatment-condition", "PUM1",
        "--rna-ref", "A", "--rna-alt", "G",
        "--min-sample-dp", policy[["min-sample-dp"]],
        "--mean-dp-threshold", policy[["mean-dp-threshold"]],
        "--fdr-threshold", policy[["fdr-threshold"]],
        "--common-or-threshold", policy[["common-or-threshold"]],
        "--absolute-difference-threshold",
        policy[["absolute-difference-threshold"]],
        "--background-max-fraction", policy[["background-max-fraction"]],
        "--all-sites-output", outputs$all,
        "--significant-sites-output", outputs$significant,
        "--summary-output", outputs$summary,
        "--mutation-spectrum-output", outputs$mutation,
        "--mutation-spectrum-pdf-output", outputs$mutation_pdf,
        "--depth-delta-pdf-output", outputs$depth_pdf
    )
    if (!is.null(background)) {
        insertion <- match("--background-max-fraction", arguments)
        arguments <- append(
            arguments, c("--background-condition", background),
            after = insertion - 1L
        )
    }
    log_path <- file.path(output_dir, "run.log")
    status <- system2(
        rscript_bin, args = shQuote(c(engine, arguments)),
        stdout = log_path, stderr = log_path
    )
    status <- if (is.null(status)) 0L else status
    if (expect_success && status != 0L) {
        stop(
            "Step 09 fixture failed:\n",
            paste(readLines(log_path, warn = FALSE), collapse = "\n"),
            call. = FALSE
        )
    }
    if (!expect_success && status == 0L) {
        stop("Expected Step 09 fixture failure, but it passed.", call. = FALSE)
    }
    c(outputs, list(status = status, log = log_path))
}

assert_pdf <- function(path) {
    connection <- file(path, "rb")
    on.exit(close(connection), add = TRUE)
    bytes <- readBin(connection, "raw", n = file.info(path)$size)
    assert_true(
        identical(bytes[seq_len(5L)], charToRaw("%PDF-")),
        paste("Missing PDF signature:", path)
    )
    tail_bytes <- bytes[max(1L, length(bytes) - 2047L):length(bytes)]
    eof_signature <- charToRaw("%%EOF")
    possible <- seq_len(length(tail_bytes) - length(eof_signature) + 1L)
    has_eof <- any(vapply(possible, function(index) {
        identical(
            tail_bytes[index:(index + length(eof_signature) - 1L)],
            eof_signature
        )
    }, logical(1)))
    assert_true(has_eof, "Missing PDF EOF.")
}

main <- function() {
    assert_independent_cmh_corpus()

    temporary_root <- tempfile("step09-r-tests-")
    dir.create(temporary_root)
    on.exit(unlink(temporary_root, recursive = TRUE, force = TRUE), add = TRUE)

    # Core family: four successful tests span both partitions/orientations. The
    # low-depth tested row must remain in the single BH family.
    sample_ids <- sample_table(FALSE)$sample_id
    strong_dp <- c(100, 80, 120, 100, 80, 120)
    strong_up_ad <- c(5, 4, 6, 20, 16, 24)
    low_dp <- rep(20, 6)
    low_ad <- c(1, 1, 1, 4, 4, 4)
    moderate_ad <- c(5, 4, 6, 10, 8, 12)
    null_ad <- c(10, 8, 12, 10, 8, 12)
    missing_dp <- strong_dp
    missing_ad <- strong_up_ad
    missing_dp[[1L]] <- NA
    missing_ad[[1L]] <- NA
    low_coverage_dp <- strong_dp
    low_coverage_ad <- strong_up_ad
    low_coverage_dp[[1L]] <- 0
    low_coverage_ad[[1L]] <- 0

    core_rows <- list(
        site_row("strong_up", "p1", "FWD_like", "A", "G",
                 strong_dp, strong_up_ad, sample_ids),
        site_row("low_mean", "p2", "REV_like", "A", "G",
                 low_dp, low_ad, sample_ids),
        site_row("moderate", "p2", "FWD_like", "A", "G",
                 strong_dp, moderate_ad, sample_ids),
        site_row("null", "p1", "REV_like", "A", "G",
                 strong_dp, null_ad, sample_ids),
        site_row("non_target", "p1", "FWD_like", "C", "T",
                 strong_dp, strong_up_ad, sample_ids),
        site_row("degenerate", "p2", "REV_like", "A", "G",
                 rep(100, 6), rep(0, 6), sample_ids),
        site_row("missing", "p1", "REV_like", "A", "G",
                 missing_dp, missing_ad, sample_ids),
        site_row("low_coverage", "p2", "FWD_like", "A", "G",
                 low_coverage_dp, low_coverage_ad, sample_ids)
    )
    core_fixture <- make_fixture(
        file.path(temporary_root, "core-input"), core_rows
    )
    core_output <- run_engine(
        core_fixture, file.path(temporary_root, "core-output")
    )
    core <- read_tsv(core_output$all)
    assert_identical(
        names(core),
        c(
            RESULT_COLUMNS, paste0("DP__", sample_ids),
            paste0("AD__", sample_ids), paste0("AF__", sample_ids)
        ),
        "All-sites schema or manifest-ordered sample groups changed."
    )
    assert_identical(
        core$candidate_id,
        c("strong_up", "low_mean", "moderate", "null", "non_target",
          "degenerate", "missing", "low_coverage"),
        "All-sites order must preserve Step 08 order."
    )
    assert_identical(
        core$test_status,
        c("tested", "tested", "tested", "tested", "not_target_change",
          "degenerate_table", "missing_counts", "low_coverage"),
        "Core test statuses differ."
    )
    assert_identical(
        core$call_status,
        c("significant_up", "below_mean_dp", "significant_up", "fdr_not_met",
          "not_tested", "not_tested", "not_tested", "not_tested"),
        "Core call statuses or strict threshold precedence differ."
    )
    strong <- core[core$candidate_id == "strong_up", , drop = FALSE]
    assert_near(strong$common_odds_ratio, 4.75, 1e-12, "Up OR direction changed")
    assert_near(
        strong$cmh_statistic, 29.3534270206935, 1e-11,
        "Known corrected CMH statistic changed"
    )
    assert_near(
        strong$cmh_p_value, 6.03097670340462e-08, 1e-18,
        "Known corrected CMH p-value changed"
    )
    expected_q <- c(
        2.41239068136185e-07, 0.0405655958497839,
        0.0405655958497839, 1
    )
    assert_true(
        max(abs(core$cmh_fdr_bh[seq_len(4L)] - expected_q)) < 1e-12,
        "BH was not applied once across all tested partitions/orientations."
    )
    assert_identical(
        read_tsv(core_output$significant)$candidate_id,
        c("strong_up", "moderate"),
        "Significant subset must be deterministic and retain relative order."
    )
    spectrum <- read_tsv(core_output$mutation)
    assert_identical(
        spectrum$mutation_type,
        c("A>C", "A>G", "A>T", "C>A", "C>G", "C>T",
          "G>A", "G>C", "G>T", "T>A", "T>C", "T>G"),
        "Mutation spectrum order changed."
    )
    assert_true(nrow(spectrum) == 12L, "Mutation spectrum must contain 12 rows.")
    assert_true(
        spectrum$candidate_count[spectrum$mutation_type == "A>G"] == 7L &&
        spectrum$candidate_count[spectrum$mutation_type == "C>T"] == 1L,
        "Mutation spectrum counts do not reconcile."
    )
    assert_pdf(core_output$mutation_pdf)
    assert_pdf(core_output$depth_pdf)

    # The real engine summary must preserve its exact schema, status accounting,
    # provenance, policy, and thresholds.
    core_summary <- read_tsv(core_output$summary)
    assert_true(
        length(SUMMARY_COLUMNS) == 39L && ncol(core_summary) == 39L,
        "Core summary must contain exactly 39 columns."
    )
    assert_identical(
        names(core_summary), SUMMARY_COLUMNS,
        "Core summary schema changed."
    )
    assert_true(nrow(core_summary) == 1L, "Core summary must contain one row.")
    assert_identical(
        c(
            core_summary$analysis_id, core_summary$cohort_id,
            core_summary$control_condition, core_summary$treatment_condition,
            core_summary$target_rna_change
        ),
        c("cmh_fixture", "NORAD_EV_PUM1", "EV", "PUM1", "A>G"),
        "Core summary analysis identity changed."
    )
    assert_true(
        is.na(core_summary$background_condition),
        "Disabled background must be recorded as NA in the core summary."
    )
    summary_count_columns <- c(
        "replicate_count", "sample_count", "candidate_count",
        "target_candidate_count", "successfully_tested_count",
        "not_target_change_count", "missing_counts_count",
        "low_coverage_count", "degenerate_table_count", "below_mean_dp_count",
        "background_not_passed_count", "fdr_not_met_count",
        "effect_not_met_count", "significant_up_count", "significant_down_count"
    )
    assert_identical(
        unname(as.integer(unlist(
            core_summary[1L, summary_count_columns, drop = FALSE]
        ))),
        c(3L, 6L, 8L, 7L, 4L, 1L, 1L, 1L, 1L, 1L, 0L, 1L, 0L, 2L, 0L),
        "Core summary status counts changed."
    )
    assert_identical(
        c(
            core_summary$sample_manifest_path,
            core_summary$partition_manifest_path,
            core_summary$step08_sites_path,
            core_summary$step08_inputs_path
        ),
        c(
            core_fixture$sample_path, core_fixture$partition_path,
            core_fixture$sites_path, core_fixture$inputs_path
        ),
        "Core summary input paths changed."
    )
    assert_identical(
        c(
            core_summary$sample_manifest_sha256,
            core_summary$partition_manifest_sha256,
            core_summary$step08_sites_sha256,
            core_summary$step08_inputs_sha256
        ),
        c(
            core_fixture$sample_hash, core_fixture$partition_hash,
            core_fixture$sites_hash, core_fixture$inputs_hash
        ),
        "Core summary input hashes changed."
    )
    summary_threshold_columns <- c(
        "min_sample_dp", "mean_dp_threshold", "fdr_threshold",
        "common_or_threshold", "absolute_difference_threshold",
        "background_max_fraction"
    )
    assert_true(
        max(abs(
            as.numeric(unlist(
                core_summary[1L, summary_threshold_columns, drop = FALSE]
            )) - c(1, 50, 0.05, 1.2, 0.005, 0.01)
        )) < 1e-12,
        "Core summary thresholds changed."
    )
    assert_identical(
        c(
            core_summary$multiple_testing_method,
            core_summary$cmh_alternative,
            core_summary$orientation_policy
        ),
        c("BH", "two.sided", "legacy_provisional_v1"),
        "Core summary analysis policy changed."
    )
    assert_true(
        identical(core_summary$continuity_correction, TRUE),
        "Core summary must record continuity correction as TRUE."
    )

    # Rerun to separate paths: all deterministic TSVs must be byte-identical.
    repeat_output <- run_engine(
        core_fixture, file.path(temporary_root, "core-repeat")
    )
    for (name in c("all", "significant", "summary", "mutation")) {
        assert_identical(
            readLines(core_output[[name]], warn = FALSE),
            readLines(repeat_output[[name]], warn = FALSE),
            paste("Deterministic TSV mismatch:", name)
        )
    }

    # OR direction plus explicit background statuses. Exact 0.01 must fail.
    background_samples <- sample_table(TRUE)$sample_id
    strong_down_ad <- c(20, 16, 24, 5, 4, 6, 0, 0)
    background_rows <- list(
        site_row("background_pass_down", "p1", "FWD_like", "A", "G",
                 c(strong_dp, 100, 100), strong_down_ad, background_samples),
        site_row("background_exact", "p1", "REV_like", "A", "G",
                 c(strong_dp, 100, 100), c(strong_up_ad, 1, 0),
                 background_samples),
        site_row("background_missing", "p2", "FWD_like", "A", "G",
                 c(strong_dp, NA, 100), c(strong_up_ad, NA, 0),
                 background_samples),
        site_row("background_low", "p2", "REV_like", "A", "G",
                 c(strong_dp, 0, 100), c(strong_up_ad, 0, 0),
                 background_samples)
    )
    background_fixture <- make_fixture(
        file.path(temporary_root, "background-input"),
        background_rows, include_background = TRUE
    )
    background_output <- run_engine(
        background_fixture, file.path(temporary_root, "background-output"),
        background = "NODOX"
    )
    background_result <- read_tsv(background_output$all)
    assert_identical(
        background_result$background_status,
        c("pass", "fail_fraction", "missing_counts", "low_coverage"),
        "Background statuses or strict 0.01 rule changed."
    )
    assert_identical(
        background_result$call_status,
        c("significant_down", "background_not_passed",
          "background_not_passed", "background_not_passed"),
        "Background call filtering changed."
    )
    down <- background_result[
        background_result$candidate_id == "background_pass_down", , drop = FALSE
    ]
    assert_near(
        down$common_odds_ratio, 0.210526315789474, 1e-12,
        "Treatment-relative-control down OR changed"
    )
    assert_near(
        down$treatment_control_difference, -0.15, 1e-12,
        "Treatment-control difference direction changed"
    )

    # Empty Step 08 table is a valid committed input and still publishes fixed
    # schemas, a 12-row zero spectrum, and both valid PDFs.
    empty_fixture <- make_fixture(
        file.path(temporary_root, "empty-input"), list()
    )
    empty_output <- run_engine(
        empty_fixture, file.path(temporary_root, "empty-output")
    )
    empty_all <- read_tsv(empty_output$all)
    empty_significant <- read_tsv(empty_output$significant)
    empty_summary <- read_tsv(empty_output$summary)
    empty_spectrum <- read_tsv(empty_output$mutation)
    assert_true(nrow(empty_all) == 0L, "Empty all-sites output has data rows.")
    assert_true(
        nrow(empty_significant) == 0L,
        "Empty significant output has data rows."
    )
    assert_true(
        nrow(empty_spectrum) == 12L &&
        all(empty_spectrum$candidate_count == 0L) &&
        all(empty_spectrum$candidate_fraction == 0),
        "Empty mutation spectrum is not the fixed zero spectrum."
    )
    assert_identical(
        names(empty_summary), SUMMARY_COLUMNS,
        "Empty summary schema changed."
    )
    assert_true(nrow(empty_summary) == 1L, "Empty summary must contain one row.")
    empty_summary_count_columns <- c(
        "candidate_count", "target_candidate_count", "successfully_tested_count",
        "not_target_change_count", "missing_counts_count",
        "low_coverage_count", "degenerate_table_count", "below_mean_dp_count",
        "background_not_passed_count", "fdr_not_met_count",
        "effect_not_met_count", "significant_up_count", "significant_down_count"
    )
    assert_true(
        all(as.integer(unlist(
            empty_summary[1L, empty_summary_count_columns, drop = FALSE]
        )) == 0L),
        "Empty summary candidate and status counts must all be zero."
    )
    assert_true(
        empty_summary$replicate_count == 3L &&
        empty_summary$sample_count == 6L &&
        is.na(empty_summary$background_condition),
        "Empty summary lost manifest or disabled-background context."
    )
    assert_pdf(empty_output$mutation_pdf)
    assert_pdf(empty_output$depth_pdf)

    # Equality at the mean-DP and common-OR boundaries must not pass.
    mean_boundary <- run_engine(
        core_fixture, file.path(temporary_root, "mean-boundary"),
        overrides = list(`mean-dp-threshold` = "100")
    )
    assert_true(
        read_tsv(mean_boundary$all)$call_status[[1L]] == "below_mean_dp",
        "Mean DP equality incorrectly passed the strict threshold."
    )
    or_boundary <- run_engine(
        core_fixture, file.path(temporary_root, "or-boundary"),
        overrides = list(`common-or-threshold` = "4.75")
    )
    assert_true(
        read_tsv(or_boundary$all)$call_status[[1L]] == "effect_not_met",
        "Common OR equality incorrectly passed the strict threshold."
    )
    fdr_boundary <- run_engine(
        core_fixture, file.path(temporary_root, "fdr-boundary"),
        overrides = list(`fdr-threshold` = "1")
    )
    assert_true(
        read_tsv(fdr_boundary$all)$call_status[[4L]] == "fdr_not_met",
        "FDR equality incorrectly passed the strict threshold."
    )

    # A binary-exact 0.25 delta makes the absolute-difference equality boundary
    # independent of decimal representation.
    delta_row <- site_row(
        "delta_boundary", "p1", "FWD_like", "A", "G",
        rep(100, 6), c(0, 0, 0, 25, 25, 25), sample_ids
    )
    delta_fixture <- make_fixture(
        file.path(temporary_root, "delta-input"), list(delta_row)
    )
    delta_boundary <- run_engine(
        delta_fixture, file.path(temporary_root, "delta-boundary"),
        overrides = list(`absolute-difference-threshold` = "0.25")
    )
    assert_true(
        read_tsv(delta_boundary$all)$call_status[[1L]] == "effect_not_met",
        "Absolute-difference equality incorrectly passed the strict threshold."
    )

    reciprocal_boundary <- run_engine(
        background_fixture, file.path(temporary_root, "reciprocal-boundary"),
        background = "NODOX",
        overrides = list(`common-or-threshold` = "4.75")
    )
    assert_true(
        read_tsv(reciprocal_boundary$all)$call_status[[1L]] ==
            "effect_not_met",
        "Reciprocal common-OR equality incorrectly passed the strict threshold."
    )

    # Pairing comes only from explicit replicate metadata. A duplicate control
    # replicate must fail even though sample names still look pairable.
    invalid_manifest <- read_tsv(core_fixture$sample_path)
    invalid_manifest$replicate[[2L]] <- "2"
    write_tsv(invalid_manifest, core_fixture$sample_path)
    core_fixture$sample_hash <- sha256_file(core_fixture$sample_path)
    updated_inputs <- read_tsv(core_fixture$inputs_path)
    updated_inputs$sample_manifest_sha256 <- core_fixture$sample_hash
    write_tsv(updated_inputs, core_fixture$inputs_path)
    core_fixture$inputs_hash <- sha256_file(core_fixture$inputs_path)
    failed <- run_engine(
        core_fixture, file.path(temporary_root, "invalid-pairing"),
        expect_success = FALSE
    )
    assert_true(
        any(grepl(
            "exactly one sample per replicate|replicate sets",
            readLines(failed$log, warn = FALSE)
        )),
        "Invalid pairing did not fail for the expected explicit-metadata reason."
    )

    cat("Step 09 real-R fixture tests passed.\n")
}

main()
