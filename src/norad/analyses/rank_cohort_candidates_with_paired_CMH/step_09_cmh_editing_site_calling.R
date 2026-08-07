#!/usr/bin/env Rscript
invocation <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(invocation) == 0L) {
    stop("Could not determine Rscript path for sourcing Step 09 helpers.", call. = FALSE)
}
script_dir <- normalizePath(
    dirname(sub("^--file=", "", invocation[[1L]])),
    winslash = "/", mustWork = TRUE
)
for (name in c("common", "validation", "evaluation", "output")) {
    source(file.path(script_dir, paste0("step_09_cmh_", name, ".R")))
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
