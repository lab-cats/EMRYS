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
