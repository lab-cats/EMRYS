#!/usr/bin/env Rscript

abort <- function(message) stop(message, call. = FALSE)

candidate_root <- normalizePath(
    Sys.getenv("EMRYS_CANDIDATE_ROOT"), mustWork = TRUE
)
trial_root <- normalizePath(commandArgs(trailingOnly = TRUE)[[4L]], mustWork = TRUE)
arguments <- commandArgs(trailingOnly = TRUE)
mode <- arguments[[1L]]

source_owner <- function(root) {
    owner <- file.path(
        root, "src/emrys/analyses/paired_cmh_candidate_ranking"
    )
    source(file.path(root, "src/emrys/libraries/input_contract.R"))
    source(file.path(owner, "step_09_cmh_common.R"))
    source(file.path(owner, "step_09_cmh_validation.R"))
}

if (identical(mode, "setup")) {
    partition_count <- as.integer(arguments[[2L]])
    candidate_count <- as.integer(arguments[[3L]])
    source_owner(candidate_root)
    partition_ids <- sprintf("p%04d", seq_len(partition_count))
    input_partitions <- rep(partition_ids, each = 2L)
    input_orientations <- rep(ORIENTATIONS, times = partition_count)
    bucket <- rep(seq_along(input_partitions), length.out = candidate_count)
    sites <- data.frame(
        partition_id = input_partitions[bucket],
        candidate_id = paste0("candidate_", seq_len(candidate_count)),
        orientation = input_orientations[bucket],
        chromosome = "1", position = seq_len(candidate_count), alt_index = 1L,
        genomic_ref = "A", genomic_alt = "G", rna_ref = "A", rna_alt = "G",
        annotation_strand = "+", gene_ids = "gene", transcript_ids = "tx",
        is_cds = TRUE, is_five_prime_utr = FALSE,
        is_three_prime_utr = FALSE, is_exon = TRUE, is_intron = FALSE,
        qual = ".", filter = "PASS", info_alt_depth = 1L,
        orientation_policy = ORIENTATION_POLICY,
        check.names = FALSE, stringsAsFactors = FALSE
    )
    sites[["DP__sample_1"]] <- 10L
    sites[["AD__sample_1"]] <- 1L
    sites[["AF__sample_1"]] <- 0.1
    fixture <- list(
        sites = sites,
        partitions = data.frame(partition_id = partition_ids),
        inputs = data.frame(
            partition_id = input_partitions,
            orientation = input_orientations,
            stringsAsFactors = FALSE
        ),
        input_counts = list(
            published_candidate_count = tabulate(
                bucket, nbins = length(input_partitions)
            )
        )
    )
    saveRDS(fixture, file.path(trial_root, "fixture.rds"), compress = FALSE)
} else if (identical(mode, "run")) {
    variant <- as.integer(arguments[[2L]])
    source_root <- if (variant == 1L) {
        normalizePath(Sys.getenv("EMRYS_BASELINE_ROOT"), mustWork = TRUE)
    } else if (variant == 2L) {
        candidate_root
    } else {
        abort("variant must be 1 (baseline) or 2 (candidate)")
    }
    source_owner(source_root)
    fixture <- readRDS(file.path(trial_root, "fixture.rds"))
    result <- validate_step08_sites(
        fixture$sites, "sample_1", fixture$partitions,
        fixture$inputs, fixture$input_counts
    )
    if (!all(result$dp == 10) || !all(result$ad == 1) ||
        !all(abs(result$af - 0.1) <= sqrt(.Machine$double.eps))) {
        abort("validated matrices differ from the fixture")
    }
    writeLines(
        c(
            "rows\tcolumns\tdp_sum\tad_sum",
            paste(
                nrow(result$dp), ncol(result$dp),
                sum(result$dp), sum(result$ad), sep = "\t"
            )
        ),
        file.path(trial_root, "result.tsv")
    )
} else if (identical(mode, "validate")) {
    fixture <- readRDS(file.path(trial_root, "fixture.rds"))
    result <- read.delim(
        file.path(trial_root, "result.tsv"), check.names = FALSE
    )
    if (nrow(result) != 1L || result$rows[[1L]] != nrow(fixture$sites) ||
        result$columns[[1L]] != 1L ||
        result$dp_sum[[1L]] != 10 * nrow(fixture$sites) ||
        result$ad_sum[[1L]] != nrow(fixture$sites)) {
        abort("benchmark result does not reconcile with the fixture")
    }
} else {
    abort("mode must be setup, run, or validate")
}
