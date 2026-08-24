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
