#!/usr/bin/env Rscript

# Project the validated Step 09 candidate tables into figure-ready sequence and
# known-motif records. This owner never reads alignment files, reclassifies a
# Step 09 call, discovers a motif, or renders a figure.

invocation <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(invocation) == 0L) {
    stop("Could not determine the scientific-context Rscript path.", call. = FALSE)
}
script_path <- normalizePath(
    sub("^--file=", "", invocation[[1L]]), winslash = "/", mustWork = TRUE
)
script_dir <- dirname(script_path)
source(file.path(script_dir, "../../libraries/input_contract.R"))

options(stringsAsFactors = FALSE, scipen = 999, digits = 15)

PRODUCER_VERSION <- "1.0.0"
SCHEMA_VERSION <- "1.0.0"
SEQUENCE_POLICY <- "legacy_rna_change_oriented_genomic_v1"
SCAN_POLICY <- "exact_iupac_presented_strand_v1"
MOTIF_DISTANCE_POLICY <- "nearest_midpoint_from_edit_v1"
MULTIPLE_TESTING_POLICY <- "none_single_registered_motif"
WINDOW_RADIUS <- 100L
LOGO_RADIUS <- 10L
DISTANCE_BIN_WIDTH <- 10L
MIN_SIGNIFICANT_POPULATION <- 10L
MIN_BACKGROUND_POPULATION <- 20L
DISPLAY_LIMIT <- 8L

STEP09_RESULT_COLUMNS <- c(
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

STEP09_SUMMARY_COLUMNS <- c(
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

CANDIDATE_CONTEXT_COLUMNS <- c(
    "analysis_id", "candidate_id", "population", "display_rank",
    "chromosome", "position", "contig_length", "genomic_ref", "genomic_alt",
    "rna_ref", "rna_alt", "orientation_action", "window_start_1based",
    "window_end_1based", "edit_offset_0based", "context_status", "oriented_sequence"
)

MOTIF_HITS_COLUMNS <- c(
    "analysis_id", "candidate_id", "population", "motif_id",
    "matched_sequence", "start_offset", "end_offset", "midpoint_offset",
    "bin_start", "bin_end"
)

SEQUENCE_LOGO_COLUMNS <- c(
    "analysis_id", "population", "availability_status",
    "relative_position", "base", "candidate_count", "observed_base_count",
    "base_count", "base_fraction"
)

MOTIF_STATISTICS_COLUMNS <- c(
    "analysis_id", "motif_id", "population", "statistic_type",
    "availability_status", "bin_start", "bin_end",
    "eligible_candidate_count", "analyzable_candidate_count",
    "candidate_with_motif_count", "hit_count", "background_candidate_count",
    "background_with_motif_count", "odds_ratio",
    "odds_ratio_ci95_lower", "odds_ratio_ci95_upper",
    "fisher_p_value_two_sided", "fisher_p_value_bh"
)

POPULATIONS <- c("significant_up", "background", "significant_down")

ARGUMENT_NAMES <- c(
    "analysis-id", "step09-all-sites", "step09-significant-sites",
    "step09-summary", "step09-all-sites-sha256",
    "step09-significant-sites-sha256", "step09-summary-sha256",
    "reference-fasta", "reference-fasta-sha256", "reference-fai",
    "reference-fai-sha256", "motif-catalog", "motif-catalog-sha256",
    "candidate-context-output", "motif-hits-output",
    "sequence-logo-output", "motif-statistics-output",
    "context-receipt-output", "candidate-context-final", "motif-hits-final",
    "sequence-logo-final", "motif-statistics-final", "git-commit"
)

usage <- function() {
    cat(paste0(
        "Usage:\n",
        "  Rscript scientific_context_projection.R \\\n",
        "    --analysis-id ID \\\n",
        "    --step09-all-sites PATH --step09-significant-sites PATH \\\n",
        "    --step09-summary PATH \\\n",
        "    --step09-all-sites-sha256 SHA256 \\\n",
        "    --step09-significant-sites-sha256 SHA256 \\\n",
        "    --step09-summary-sha256 SHA256 \\\n",
        "    --reference-fasta PATH --reference-fasta-sha256 SHA256 \\\n",
        "    --reference-fai PATH --reference-fai-sha256 SHA256 \\\n",
        "    --motif-catalog PATH --motif-catalog-sha256 SHA256 \\\n",
        "    --candidate-context-output PATH --motif-hits-output PATH \\\n",
        "    --sequence-logo-output PATH --motif-statistics-output PATH \\\n",
        "    --context-receipt-output PATH \\\n",
        "    --candidate-context-final PATH --motif-hits-final PATH \\\n",
        "    --sequence-logo-final PATH --motif-statistics-final PATH \\\n",
        "    --git-commit COMMIT\n"
    ))
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

sha256_file <- function(path) {
    sha256_file_with_fallback(
        path, "Scientific-context projection requires sha256sum or shasum."
    )
}

parse_nonnegative_integer <- function(label, values) {
    if (any(is.na(values)) ||
        any(!grepl("^(0|[1-9][0-9]*)$", values))) {
        abort(label, " must contain non-negative integer text.")
    }
    parsed <- suppressWarnings(as.numeric(values))
    if (any(!is.finite(parsed)) || any(parsed > .Machine$integer.max)) {
        abort(label, " contains an integer outside the supported range.")
    }
    as.integer(parsed)
}

parse_positive_integer <- function(label, values) {
    parsed <- parse_nonnegative_integer(label, values)
    if (any(parsed < 1L)) {
        abort(label, " must contain positive integers.")
    }
    parsed
}

parse_numeric <- function(label, values, allow_na = FALSE) {
    missing <- is.na(values)
    if (!allow_na && any(missing)) {
        abort(label, " must not contain NA.")
    }
    parsed <- rep(NA_real_, length(values))
    parsed[!missing] <- suppressWarnings(as.numeric(values[!missing]))
    if (any(!is.finite(parsed[!missing]))) {
        abort(label, " must contain finite numeric values or NA.")
    }
    parsed
}

read_step09_results <- function(label, path) {
    table <- read_contract_tsv(
        label, path, na_strings = "NA", preserve_header = TRUE
    )
    fixed_count <- length(STEP09_RESULT_COLUMNS)
    if (ncol(table) <= fixed_count ||
        !identical(names(table)[seq_len(fixed_count)], STEP09_RESULT_COLUMNS)) {
        abort(label, " does not begin with the exact Step 09 result schema.")
    }
    remainder <- names(table)[-(seq_len(fixed_count))]
    if (length(remainder) %% 3L != 0L) {
        abort(label, " has an incomplete DP/AD/AF sample block.")
    }
    sample_count <- length(remainder) %/% 3L
    if (sample_count < 1L) {
        abort(label, " contains no sample columns.")
    }
    sample_ids <- sub("^DP__", "", remainder[seq_len(sample_count)])
    if (any(!nzchar(sample_ids)) || anyDuplicated(sample_ids) ||
        !identical(remainder, c(
            paste0("DP__", sample_ids), paste0("AD__", sample_ids),
            paste0("AF__", sample_ids)
        ))) {
        abort(label, " DP/AD/AF sample columns are invalid or out of order.")
    }
    attr(table, "sample_ids") <- sample_ids
    table
}

validate_step09_inputs <- function(arguments, all_sites, significant, summary) {
    analysis_id <- arguments[["analysis-id"]]
    if (!identical(names(all_sites), names(significant))) {
        abort("Step 09 all-sites and significant-sites headers differ.")
    }
    if (!identical(attr(all_sites, "sample_ids"),
                   attr(significant, "sample_ids"))) {
        abort("Step 09 all-sites and significant-sites sample orders differ.")
    }
    if (nrow(summary) != 1L) {
        abort("Step 09 summary must contain exactly one row.")
    }
    if (any(is.na(all_sites$analysis_id)) ||
        any(all_sites$analysis_id != analysis_id) ||
        any(is.na(significant$analysis_id)) ||
        any(significant$analysis_id != analysis_id) ||
        is.na(summary$analysis_id[[1L]]) ||
        summary$analysis_id[[1L]] != analysis_id) {
        abort("Step 09 inputs do not match the requested analysis_id.")
    }
    if (any(is.na(all_sites$candidate_id)) ||
        any(!nzchar(all_sites$candidate_id)) ||
        anyDuplicated(all_sites$candidate_id)) {
        abort("Step 09 all-sites candidate_id values are empty or duplicated.")
    }
    valid_calls <- c(
        "not_tested", "below_mean_dp", "background_not_passed",
        "fdr_not_met", "effect_not_met", "significant_up",
        "significant_down"
    )
    if (any(is.na(all_sites$call_status)) ||
        any(!(all_sites$call_status %in% valid_calls))) {
        abort("Step 09 all-sites contains an invalid call_status.")
    }
    significant_index <- all_sites$call_status %in%
        c("significant_up", "significant_down")
    expected_significant <- all_sites[significant_index, , drop = FALSE]
    same_significant <- nrow(expected_significant) == nrow(significant) &&
        identical(
            unname(as.matrix(expected_significant[, names(significant), drop = FALSE])),
            unname(as.matrix(significant))
        )
    if (!same_significant) {
        abort(
            "Step 09 significant-sites is not the exact ordered significant ",
            "subset of all-sites."
        )
    }
    candidate_count <- parse_nonnegative_integer(
        "Step 09 summary candidate_count", summary$candidate_count
    )
    significant_up_count <- parse_nonnegative_integer(
        "Step 09 summary significant_up_count", summary$significant_up_count
    )
    significant_down_count <- parse_nonnegative_integer(
        "Step 09 summary significant_down_count",
        summary$significant_down_count
    )
    if (candidate_count != nrow(all_sites) ||
        significant_up_count != sum(all_sites$call_status == "significant_up") ||
        significant_down_count !=
            sum(all_sites$call_status == "significant_down")) {
        abort("Step 09 summary counts do not reconcile with result tables.")
    }
    eligible <- all_sites$call_status %in% c(
        "significant_up", "significant_down", "fdr_not_met", "effect_not_met"
    )
    if (any(all_sites$test_status[eligible] != "tested")) {
        abort("A context-eligible Step 09 row was not successfully tested.")
    }
    target_change <- summary$target_rna_change[[1L]]
    if (is.na(target_change) || !grepl("^[ACGT]>[ACGT]$", target_change)) {
        abort("Step 09 summary target_rna_change is invalid.")
    }
    observed_changes <- paste0(all_sites$rna_ref[eligible], ">",
                               all_sites$rna_alt[eligible])
    if (any(is.na(observed_changes)) || any(observed_changes != target_change)) {
        abort("A context-eligible row does not match target_rna_change.")
    }
    invisible(TRUE)
}

read_motif_catalog <- function(path) {
    catalog <- read_contract_tsv(
        "PUM motif catalog", path,
        c("motif_id", "rna_consensus", "dna_consensus"),
        preserve_header = TRUE
    )
    if (nrow(catalog) != 1L ||
        !identical(catalog$motif_id[[1L]], "PUM_UGUANA") ||
        !identical(catalog$rna_consensus[[1L]], "UGUANA") ||
        !identical(catalog$dna_consensus[[1L]], "TGTANA")) {
        abort(
            "The v1 motif catalog must contain only the approved PUM ",
            "UGUANA/TGTANA model."
        )
    }
    catalog
}

read_fai <- function(path) {
    validate_nonempty_file("Reference FAI", path)
    lines <- readLines(path, warn = FALSE)
    if (length(lines) == 0L || any(!nzchar(sub("\r$", "", lines)))) {
        abort("Reference FAI is empty or contains a blank row: ", path)
    }
    fields <- strsplit(sub("\r$", "", lines), "\t", fixed = TRUE)
    if (any(lengths(fields) != 5L)) {
        abort("Reference FAI rows must contain exactly five fields: ", path)
    }
    flat_fields <- unlist(fields, use.names = FALSE)
    if (any(flat_fields != trimws(flat_fields))) {
        abort("Reference FAI fields must not have surrounding whitespace: ", path)
    }
    names <- vapply(fields, `[[`, character(1), 1L)
    if (any(!nzchar(names)) || anyDuplicated(names)) {
        abort("Reference FAI contig names are empty or duplicated: ", path)
    }
    numeric_text <- unlist(lapply(fields, `[`, 2:5), use.names = FALSE)
    if (any(!grepl("^(0|[1-9][0-9]*)$", numeric_text))) {
        abort(
            "Reference FAI numeric fields must use canonical non-negative ",
            "decimal text: ", path
        )
    }
    numeric_values <- suppressWarnings(as.numeric(numeric_text))
    if (any(!is.finite(numeric_values))) {
        abort("Reference FAI numeric fields must be finite: ", path)
    }
    dimensions <- matrix(numeric_values, ncol = 4L, byrow = TRUE)
    lengths <- dimensions[, 1L]
    line_bases <- dimensions[, 3L]
    line_widths <- dimensions[, 4L]
    if (any(lengths < 1) || any(line_bases < 1) ||
        any(line_widths < line_bases)) {
        abort("Reference FAI rows have invalid dimensions: ", path)
    }
    stats::setNames(lengths, names)
}

population_for_call <- function(call_status) {
    ifelse(
        call_status == "significant_up", "significant_up",
        ifelse(call_status == "significant_down", "significant_down", "background")
    )
}

orientation_action <- function(genomic_ref, genomic_alt, rna_ref, rna_alt) {
    complement <- function(base) chartr("ACGT", "TGCA", base)
    identity <- genomic_ref == rna_ref & genomic_alt == rna_alt
    reverse <- complement(genomic_ref) == rna_ref &
        complement(genomic_alt) == rna_alt
    if (identity && !reverse) {
        return("identity")
    }
    if (reverse && !identity) {
        return("reverse_complement")
    }
    abort(
        "Genomic and RNA alleles do not admit one mechanical orientation: ",
        genomic_ref, ">", genomic_alt, " versus ", rna_ref, ">", rna_alt
    )
}

select_display_ranks <- function(rows) {
    ranks <- rep(NA_integer_, nrow(rows))
    significant <- which(rows$population %in%
        c("significant_up", "significant_down"))
    if (length(significant) == 0L) {
        return(ranks)
    }
    fdr <- parse_numeric(
        "Step 09 significant cmh_fdr_bh", rows$cmh_fdr_bh[significant]
    )
    delta <- parse_numeric(
        "Step 09 significant treatment_control_difference",
        rows$treatment_control_difference[significant]
    )
    ranked <- significant[order(
        fdr, -abs(delta), rows$candidate_id[significant], method = "radix"
    )]
    selected <- utils::head(ranked, DISPLAY_LIMIT)
    ranks[selected] <- seq_along(selected)
    ranks
}

extract_contexts <- function(arguments, rows, fai_lengths) {
    if (nrow(rows) == 0L) {
        empty <- as.data.frame(
            stats::setNames(rep(list(character()),
                                length(CANDIDATE_CONTEXT_COLUMNS)),
                            CANDIDATE_CONTEXT_COLUMNS),
            stringsAsFactors = FALSE
        )
        return(empty)
    }
    required_packages <- c("Biostrings", "GenomicRanges", "IRanges", "Rsamtools")
    missing <- required_packages[
        !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
    ]
    if (length(missing) > 0L) {
        abort(
            "Scientific-context projection is missing required R package(s): ",
            paste(missing, collapse = ", ")
        )
    }

    positions <- parse_positive_integer("Step 09 candidate position", rows$position)
    chromosomes <- rows$chromosome
    if (any(is.na(chromosomes)) || any(!nzchar(chromosomes))) {
        abort("A context-eligible candidate has an empty chromosome.")
    }
    absent <- setdiff(unique(chromosomes), names(fai_lengths))
    if (length(absent) > 0L) {
        abort(
            "Candidate chromosome is absent from the exact reference FAI: ",
            paste(absent, collapse = ", ")
        )
    }
    contig_lengths <- unname(fai_lengths[chromosomes])
    if (any(positions > contig_lengths)) {
        index <- which(positions > contig_lengths)[[1L]]
        abort(
            "Candidate position exceeds reference contig length: ",
            rows$candidate_id[[index]]
        )
    }
    starts <- pmax.int(1L, positions - WINDOW_RADIUS)
    ends <- pmin.int(contig_lengths, positions + WINDOW_RADIUS)
    ranges <- GenomicRanges::GRanges(
        seqnames = chromosomes,
        ranges = IRanges::IRanges(start = starts, end = ends)
    )
    fasta <- Rsamtools::FaFile(
        arguments[["reference-fasta"]], index = arguments[["reference-fai"]]
    )
    Rsamtools::open.FaFile(fasta)
    on.exit(Rsamtools::close.FaFile(fasta), add = TRUE)
    extracted <- Rsamtools::scanFa(fasta, param = ranges)
    if (length(extracted) != nrow(rows)) {
        abort("Reference extraction did not return one sequence per candidate.")
    }

    sequences <- character(nrow(rows))
    actions <- character(nrow(rows))
    edit_offsets <- integer(nrow(rows))
    statuses <- ifelse(
        starts == positions - WINDOW_RADIUS &
            ends == positions + WINDOW_RADIUS,
        "available", "boundary_truncated"
    )
    for (index in seq_len(nrow(rows))) {
        genomic_ref <- toupper(rows$genomic_ref[[index]])
        genomic_alt <- toupper(rows$genomic_alt[[index]])
        rna_ref <- toupper(rows$rna_ref[[index]])
        rna_alt <- toupper(rows$rna_alt[[index]])
        bases <- c(genomic_ref, genomic_alt, rna_ref, rna_alt)
        if (any(is.na(bases)) || any(!grepl("^[ACGT]$", bases))) {
            abort("Context-eligible candidates require canonical SNV alleles.")
        }
        action <- orientation_action(genomic_ref, genomic_alt, rna_ref, rna_alt)
        sequence <- extracted[[index]]
        genomic_edit_offset <- positions[[index]] - starts[[index]]
        genomic_center <- toupper(as.character(Biostrings::subseq(
            sequence, start = genomic_edit_offset + 1L,
            end = genomic_edit_offset + 1L
        )))
        if (!identical(genomic_center, genomic_ref)) {
            abort(
                "Reference FASTA center base does not match genomic_ref for ",
                rows$candidate_id[[index]], ": expected ", genomic_ref,
                ", observed ", genomic_center
            )
        }
        if (action == "reverse_complement") {
            sequence <- Biostrings::reverseComplement(sequence)
            edit_offset <- length(sequence) - genomic_edit_offset - 1L
        } else {
            edit_offset <- genomic_edit_offset
        }
        oriented_center <- toupper(as.character(Biostrings::subseq(
            sequence, start = edit_offset + 1L, end = edit_offset + 1L
        )))
        if (!identical(oriented_center, rna_ref)) {
            abort(
                "Oriented reference center does not match rna_ref for ",
                rows$candidate_id[[index]]
            )
        }
        sequences[[index]] <- toupper(as.character(sequence))
        actions[[index]] <- action
        edit_offsets[[index]] <- edit_offset
    }

    context <- data.frame(
        analysis_id = rows$analysis_id,
        candidate_id = rows$candidate_id,
        population = rows$population,
        display_rank = ifelse(is.na(rows$display_rank), NA, rows$display_rank),
        chromosome = chromosomes,
        position = positions,
        contig_length = contig_lengths,
        genomic_ref = toupper(rows$genomic_ref),
        genomic_alt = toupper(rows$genomic_alt),
        rna_ref = toupper(rows$rna_ref),
        rna_alt = toupper(rows$rna_alt),
        orientation_action = actions,
        window_start_1based = starts,
        window_end_1based = ends,
        edit_offset_0based = edit_offsets,
        context_status = statuses,
        oriented_sequence = sequences,
        check.names = FALSE
    )
    context[, CANDIDATE_CONTEXT_COLUMNS, drop = FALSE]
}

scan_exact_motif <- function(sequence, edit_offset, pattern = "TGTA[ACGT]A") {
    motif_width <- 6L
    if (nchar(sequence, type = "bytes") < motif_width) {
        return(data.frame(
            matched_sequence = character(), start_offset = numeric(),
            end_offset = numeric(), midpoint_offset = numeric(),
            bin_start = numeric(), bin_end = numeric()
        ))
    }
    starts <- seq_len(nchar(sequence, type = "bytes") - motif_width + 1L)
    matches <- vapply(starts, function(start) {
        grepl(
            pattern, substr(sequence, start, start + motif_width - 1L),
            perl = TRUE
        )
    }, logical(1))
    starts <- starts[matches]
    if (length(starts) == 0L) {
        return(data.frame(
            matched_sequence = character(), start_offset = numeric(),
            end_offset = numeric(), midpoint_offset = numeric(),
            bin_start = numeric(), bin_end = numeric()
        ))
    }
    matched <- vapply(starts, function(start) {
        substr(sequence, start, start + motif_width - 1L)
    }, character(1))
    start_offsets <- starts - 1L - edit_offset
    end_offsets <- start_offsets + motif_width - 1L
    midpoints <- (start_offsets + end_offsets) / 2
    bin_starts <- floor((midpoints + WINDOW_RADIUS) / DISTANCE_BIN_WIDTH) *
        DISTANCE_BIN_WIDTH - WINDOW_RADIUS
    bin_starts <- pmax(-WINDOW_RADIUS,
                       pmin(WINDOW_RADIUS - DISTANCE_BIN_WIDTH, bin_starts))
    data.frame(
        matched_sequence = matched,
        start_offset = start_offsets,
        end_offset = end_offsets,
        midpoint_offset = midpoints,
        bin_start = bin_starts,
        bin_end = bin_starts + DISTANCE_BIN_WIDTH,
        stringsAsFactors = FALSE
    )
}

make_motif_hits <- function(context, motif_id) {
    rows <- list()
    output_index <- 1L
    for (index in seq_len(nrow(context))) {
        if (context$context_status[[index]] != "available") {
            next
        }
        hits <- scan_exact_motif(
            context$oriented_sequence[[index]],
            context$edit_offset_0based[[index]]
        )
        if (nrow(hits) == 0L) {
            next
        }
        rows[[output_index]] <- data.frame(
            analysis_id = context$analysis_id[[index]],
            candidate_id = context$candidate_id[[index]],
            population = context$population[[index]],
            motif_id = motif_id,
            matched_sequence = hits$matched_sequence,
            start_offset = hits$start_offset,
            end_offset = hits$end_offset,
            midpoint_offset = hits$midpoint_offset,
            bin_start = hits$bin_start,
            bin_end = hits$bin_end,
            stringsAsFactors = FALSE,
            check.names = FALSE
        )
        output_index <- output_index + 1L
    }
    if (length(rows) == 0L) {
        return(as.data.frame(
            stats::setNames(rep(list(character()), length(MOTIF_HITS_COLUMNS)),
                            MOTIF_HITS_COLUMNS),
            stringsAsFactors = FALSE
        ))
    }
    hits <- do.call(rbind, rows)
    hits[, MOTIF_HITS_COLUMNS, drop = FALSE]
}

population_minimum <- function(population) {
    if (population == "background") {
        MIN_BACKGROUND_POPULATION
    } else {
        MIN_SIGNIFICANT_POPULATION
    }
}

availability_for <- function(population, candidate_count) {
    if (candidate_count >= population_minimum(population)) {
        "available"
    } else {
        "population_below_minimum"
    }
}

make_sequence_logo <- function(analysis_id, context) {
    rows <- vector("list", length(POPULATIONS) *
        (2L * LOGO_RADIUS + 1L) * 4L)
    output_index <- 1L
    for (population in POPULATIONS) {
        population_rows <- context[context$population == population, , drop = FALSE]
        available <- population_rows[
            population_rows$context_status == "available", , drop = FALSE
        ]
        candidate_count <- nrow(available)
        status <- availability_for(population, nrow(available))
        for (relative_position in seq.int(-LOGO_RADIUS, LOGO_RADIUS)) {
            observed <- if (nrow(available) == 0L) character() else vapply(
                seq_len(nrow(available)), function(index) {
                    sequence_index <- available$edit_offset_0based[[index]] +
                        relative_position + 1L
                    substr(
                        available$oriented_sequence[[index]], sequence_index,
                        sequence_index
                    )
                }, character(1)
            )
            canonical <- observed[observed %in% c("A", "C", "G", "T")]
            observed_base_count <- length(canonical)
            for (base in c("A", "C", "G", "T")) {
                base_count <- sum(canonical == base)
                base_fraction <- if (observed_base_count == 0L) {
                    NA_real_
                } else {
                    base_count / observed_base_count
                }
                rows[[output_index]] <- data.frame(
                    analysis_id = analysis_id,
                    population = population,
                    availability_status = status,
                    relative_position = relative_position,
                    base = base,
                    candidate_count = candidate_count,
                    observed_base_count = observed_base_count,
                    base_count = base_count,
                    base_fraction = base_fraction,
                    stringsAsFactors = FALSE,
                    check.names = FALSE
                )
                output_index <- output_index + 1L
            }
        }
    }
    logo <- do.call(rbind, rows)
    logo[, SEQUENCE_LOGO_COLUMNS, drop = FALSE]
}

nearest_hits <- function(hits) {
    if (nrow(hits) == 0L) {
        return(hits)
    }
    ordered <- hits[order(
        hits$candidate_id, abs(hits$midpoint_offset), hits$start_offset,
        method = "radix"
    ), , drop = FALSE]
    ordered[!duplicated(ordered$candidate_id), , drop = FALSE]
}

fisher_values <- function(foreground_n, foreground_hit,
                          background_n, background_hit) {
    test <- stats::fisher.test(
        matrix(c(
            foreground_hit, foreground_n - foreground_hit,
            background_hit, background_n - background_hit
        ), nrow = 2L, byrow = TRUE),
        alternative = "two.sided", conf.int = TRUE
    )
    c(
        odds_ratio = unname(test$estimate),
        lower = unname(test$conf.int[[1L]]),
        upper = unname(test$conf.int[[2L]]),
        p_value = unname(test$p.value)
    )
}

make_motif_statistics <- function(analysis_id, motif_id, context, hits) {
    available_context <- context[
        context$context_status == "available", , drop = FALSE
    ]
    nearest <- nearest_hits(hits)
    rows <- list()
    output_index <- 1L

    foreground <- available_context[
        available_context$population == "significant_up", , drop = FALSE
    ]
    background <- available_context[
        available_context$population == "background", , drop = FALSE
    ]
    foreground_hits <- hits[hits$population == "significant_up", , drop = FALSE]
    background_hits <- hits[hits$population == "background", , drop = FALSE]
    foreground_with_motif <- length(unique(foreground_hits$candidate_id))
    background_with_motif <- length(unique(background_hits$candidate_id))
    enrichment_status <- if (nrow(foreground) < MIN_SIGNIFICANT_POPULATION) {
        "population_below_minimum"
    } else if (nrow(background) < MIN_BACKGROUND_POPULATION) {
        "background_below_minimum"
    } else if ((foreground_with_motif + background_with_motif) %in%
        c(0L, nrow(foreground) + nrow(background))) {
        "uninformative_table"
    } else {
        "available"
    }
    inference <- c(
        odds_ratio = NA_real_, lower = NA_real_, upper = NA_real_,
        p_value = NA_real_
    )
    if (enrichment_status == "available") {
        inference <- fisher_values(
            nrow(foreground), foreground_with_motif,
            nrow(background), background_with_motif
        )
    }
    rows[[output_index]] <- data.frame(
        analysis_id = analysis_id,
        motif_id = motif_id,
        population = "significant_up",
        statistic_type = "enrichment",
        availability_status = enrichment_status,
        bin_start = NA_real_,
        bin_end = NA_real_,
        eligible_candidate_count = sum(context$population == "significant_up"),
        analyzable_candidate_count = nrow(foreground),
        candidate_with_motif_count = foreground_with_motif,
        hit_count = nrow(foreground_hits),
        background_candidate_count = nrow(background),
        background_with_motif_count = background_with_motif,
        odds_ratio = inference[["odds_ratio"]],
        odds_ratio_ci95_lower = inference[["lower"]],
        odds_ratio_ci95_upper = inference[["upper"]],
        fisher_p_value_two_sided = inference[["p_value"]],
        fisher_p_value_bh = NA_real_,
        stringsAsFactors = FALSE,
        check.names = FALSE
    )
    output_index <- output_index + 1L

    bin_starts <- seq.int(
        -WINDOW_RADIUS, WINDOW_RADIUS - DISTANCE_BIN_WIDTH,
        by = DISTANCE_BIN_WIDTH
    )
    for (population in POPULATIONS) {
        eligible_count <- sum(context$population == population)
        analyzable <- available_context[
            available_context$population == population, , drop = FALSE
        ]
        population_hits <- hits[hits$population == population, , drop = FALSE]
        population_nearest <- nearest[
            nearest$population == population, , drop = FALSE
        ]
        status <- availability_for(population, nrow(analyzable))
        for (bin_start in bin_starts) {
            bin_end <- bin_start + DISTANCE_BIN_WIDTH
            all_in_bin <- population_hits$bin_start == bin_start
            nearest_in_bin <- population_nearest$bin_start == bin_start
            rows[[output_index]] <- data.frame(
                analysis_id = analysis_id,
                motif_id = motif_id,
                population = population,
                statistic_type = "position_bin",
                availability_status = status,
                bin_start = bin_start,
                bin_end = bin_end,
                eligible_candidate_count = eligible_count,
                analyzable_candidate_count = nrow(analyzable),
                candidate_with_motif_count = sum(nearest_in_bin),
                hit_count = sum(all_in_bin),
                background_candidate_count = NA_integer_,
                background_with_motif_count = NA_integer_,
                odds_ratio = NA_real_,
                odds_ratio_ci95_lower = NA_real_,
                odds_ratio_ci95_upper = NA_real_,
                fisher_p_value_two_sided = NA_real_,
                fisher_p_value_bh = NA_real_,
                stringsAsFactors = FALSE,
                check.names = FALSE
            )
            output_index <- output_index + 1L
        }
    }
    statistics <- do.call(rbind, rows)
    statistics[, MOTIF_STATISTICS_COLUMNS, drop = FALSE]
}

write_tsv <- function(table, path) {
    parent <- dirname(path)
    if (!dir.exists(parent)) {
        abort("Output parent directory does not exist: ", parent)
    }
    utils::write.table(
        table, file = path, sep = "\t", quote = FALSE, row.names = FALSE,
        col.names = TRUE, na = "NA", eol = "\n"
    )
    validate_nonempty_file("Written scientific-context output", path)
}

assert_output_shape <- function(table, expected_columns, label) {
    if (!identical(names(table), expected_columns)) {
        abort(label, " does not have the canonical in-memory header.")
    }
    for (column in names(table)) {
        values <- as.character(table[[column]])
        if (any(grepl("[\t\r\n]", values))) {
            abort(label, " contains a forbidden TSV control character.")
        }
    }
}

canonical_future_path <- function(path) {
    parent <- normalizePath(dirname(path), winslash = "/", mustWork = TRUE)
    file.path(parent, basename(path))
}

# The canonical contract module owns this exact one-row schema. It is kept here
# as the native R serialization boundary and is reconciled by the independent
# grouped validator.
CONTEXT_RECEIPT_COLUMNS <- c(
    "schema_name", "schema_version", "analysis_id",
    "step09_all_sites_path", "step09_all_sites_sha256",
    "step09_significant_sites_path", "step09_significant_sites_sha256",
    "step09_summary_path", "step09_summary_sha256",
    "reference_fasta_path", "reference_fasta_sha256",
    "reference_fai_path", "reference_fai_sha256", "motif_catalog_path",
    "motif_catalog_sha256", "scientific_context_schema_version",
    "context_orientation_policy", "context_radius", "logo_radius",
    "display_limit", "motif_match_policy", "motif_distance_policy",
    "motif_distance_bin_width", "foreground_population",
    "background_population", "separate_population",
    "foreground_minimum_count", "background_minimum_count",
    "separate_minimum_count", "enrichment_test",
    "enrichment_alternative", "multiple_testing_method",
    "candidate_context_path", "candidate_context_sha256",
    "candidate_context_row_count", "motif_hits_path", "motif_hits_sha256",
    "motif_hits_row_count", "sequence_logo_path", "sequence_logo_sha256",
    "sequence_logo_row_count", "motif_statistics_path",
    "motif_statistics_sha256", "motif_statistics_row_count",
    "published_output_count", "producer", "producer_version", "r_version",
    "biostrings_version", "rsamtools_version", "git_commit",
    "transaction_state"
)

make_receipt <- function(arguments, hashes, catalog, outputs) {
    data.frame(
        schema_name = "norad.scientific_context_receipt",
        schema_version = SCHEMA_VERSION,
        analysis_id = arguments[["analysis-id"]],
        step09_all_sites_path = arguments[["step09-all-sites"]],
        step09_all_sites_sha256 = hashes[["all_sites"]],
        step09_significant_sites_path = arguments[["step09-significant-sites"]],
        step09_significant_sites_sha256 = hashes[["significant"]],
        step09_summary_path = arguments[["step09-summary"]],
        step09_summary_sha256 = hashes[["summary"]],
        reference_fasta_path = arguments[["reference-fasta"]],
        reference_fasta_sha256 = hashes[["fasta"]],
        reference_fai_path = arguments[["reference-fai"]],
        reference_fai_sha256 = hashes[["fai"]],
        motif_catalog_path = arguments[["motif-catalog"]],
        motif_catalog_sha256 = hashes[["catalog"]],
        scientific_context_schema_version = SCHEMA_VERSION,
        context_orientation_policy = SEQUENCE_POLICY,
        context_radius = WINDOW_RADIUS,
        logo_radius = LOGO_RADIUS,
        display_limit = DISPLAY_LIMIT,
        motif_match_policy = SCAN_POLICY,
        motif_distance_policy = MOTIF_DISTANCE_POLICY,
        motif_distance_bin_width = DISTANCE_BIN_WIDTH,
        foreground_population = "significant_up",
        background_population = "fdr_not_met,effect_not_met",
        separate_population = "significant_down",
        foreground_minimum_count = MIN_SIGNIFICANT_POPULATION,
        background_minimum_count = MIN_BACKGROUND_POPULATION,
        separate_minimum_count = MIN_SIGNIFICANT_POPULATION,
        enrichment_test = "Fisher_exact",
        enrichment_alternative = "two.sided",
        multiple_testing_method = MULTIPLE_TESTING_POLICY,
        candidate_context_path = arguments[["candidate-context-final"]],
        candidate_context_sha256 = sha256_file(outputs[["candidate_context_path"]]),
        candidate_context_row_count = nrow(outputs[["candidate_context"]]),
        motif_hits_path = arguments[["motif-hits-final"]],
        motif_hits_sha256 = sha256_file(outputs[["motif_hits_path"]]),
        motif_hits_row_count = nrow(outputs[["motif_hits"]]),
        sequence_logo_path = arguments[["sequence-logo-final"]],
        sequence_logo_sha256 = sha256_file(outputs[["sequence_logo_path"]]),
        sequence_logo_row_count = nrow(outputs[["sequence_logo"]]),
        motif_statistics_path = arguments[["motif-statistics-final"]],
        motif_statistics_sha256 = sha256_file(outputs[["motif_statistics_path"]]),
        motif_statistics_row_count = nrow(outputs[["motif_statistics"]]),
        published_output_count = 5L,
        producer = "build_scientific_context",
        producer_version = PRODUCER_VERSION,
        r_version = as.character(getRversion()),
        biostrings_version = as.character(utils::packageVersion("Biostrings")),
        rsamtools_version = as.character(utils::packageVersion("Rsamtools")),
        git_commit = arguments[["git-commit"]],
        transaction_state = "complete",
        stringsAsFactors = FALSE,
        check.names = FALSE
    )[, CONTEXT_RECEIPT_COLUMNS, drop = FALSE]
}

main <- function() {
    arguments <- parse_named_arguments(
        commandArgs(trailingOnly = TRUE), ARGUMENT_NAMES,
        usage_function = usage
    )
    validate_safe_id("analysis_id", arguments[["analysis-id"]])
    if (!grepl("^[0-9a-f]{40}([0-9a-f]{24})?$", arguments[["git-commit"]])) {
        abort("git_commit must be one full 40- or 64-character commit ID.")
    }

    hash_arguments <- c(
        all_sites = "step09-all-sites-sha256",
        significant = "step09-significant-sites-sha256",
        summary = "step09-summary-sha256",
        fasta = "reference-fasta-sha256",
        fai = "reference-fai-sha256",
        catalog = "motif-catalog-sha256"
    )
    hashes <- vapply(names(hash_arguments), function(name) {
        validate_hash(name, arguments[[hash_arguments[[name]]]])
    }, character(1))
    input_arguments <- c(
        all_sites = "step09-all-sites", significant = "step09-significant-sites",
        summary = "step09-summary", fasta = "reference-fasta",
        fai = "reference-fai", catalog = "motif-catalog"
    )
    for (name in names(input_arguments)) {
        path <- arguments[[input_arguments[[name]]]]
        validate_nonempty_file(name, path)
        path <- normalizePath(path, winslash = "/", mustWork = TRUE)
        arguments[[input_arguments[[name]]]] <- path
    }
    output_argument_names <- c(
        "candidate-context-output", "motif-hits-output",
        "sequence-logo-output", "motif-statistics-output",
        "context-receipt-output", "candidate-context-final",
        "motif-hits-final", "sequence-logo-final", "motif-statistics-final"
    )
    for (name in output_argument_names) {
        arguments[[name]] <- canonical_future_path(arguments[[name]])
    }
    output_paths <- unname(unlist(arguments[output_argument_names]))
    input_paths <- unname(unlist(arguments[input_arguments]))
    if (anyDuplicated(output_paths) || any(output_paths %in% input_paths)) {
        abort("Scientific-context output paths must be distinct from each other and inputs.")
    }

    if (!requireNamespace("Biostrings", quietly = TRUE) ||
        !requireNamespace("Rsamtools", quietly = TRUE)) {
        abort("Biostrings and Rsamtools are required by this owner.")
    }
    all_sites <- read_step09_results(
        "Step 09 all-sites", arguments[["step09-all-sites"]]
    )
    significant <- read_step09_results(
        "Step 09 significant-sites", arguments[["step09-significant-sites"]]
    )
    summary <- read_contract_tsv(
        "Step 09 summary", arguments[["step09-summary"]],
        STEP09_SUMMARY_COLUMNS, na_strings = "NA", preserve_header = TRUE
    )
    validate_step09_inputs(arguments, all_sites, significant, summary)
    catalog <- read_motif_catalog(arguments[["motif-catalog"]])
    fai_lengths <- read_fai(arguments[["reference-fai"]])

    eligible <- all_sites$call_status %in% c(
        "significant_up", "significant_down", "fdr_not_met", "effect_not_met"
    )
    projection_rows <- all_sites[eligible, , drop = FALSE]
    projection_rows$population <- population_for_call(projection_rows$call_status)
    projection_rows$display_rank <- select_display_ranks(projection_rows)

    context <- extract_contexts(arguments, projection_rows, fai_lengths)
    hits <- make_motif_hits(context, catalog$motif_id[[1L]])
    logo <- make_sequence_logo(arguments[["analysis-id"]], context)
    statistics <- make_motif_statistics(
        arguments[["analysis-id"]], catalog$motif_id[[1L]], context, hits
    )
    assert_output_shape(context, CANDIDATE_CONTEXT_COLUMNS, "Candidate context")
    assert_output_shape(hits, MOTIF_HITS_COLUMNS, "Motif hits")
    assert_output_shape(logo, SEQUENCE_LOGO_COLUMNS, "Sequence logo")
    assert_output_shape(
        statistics, MOTIF_STATISTICS_COLUMNS, "Motif statistics"
    )

    temporary_output_paths <- c(
        arguments[["candidate-context-output"]],
        arguments[["motif-hits-output"]],
        arguments[["sequence-logo-output"]],
        arguments[["motif-statistics-output"]],
        arguments[["context-receipt-output"]]
    )
    if (anyDuplicated(temporary_output_paths)) {
        abort("Scientific-context output paths must be distinct.")
    }
    write_tsv(context, arguments[["candidate-context-output"]])
    write_tsv(hits, arguments[["motif-hits-output"]])
    write_tsv(logo, arguments[["sequence-logo-output"]])
    write_tsv(statistics, arguments[["motif-statistics-output"]])

    # The receipt is deliberately serialized after all four hashed payloads.
    receipt <- make_receipt(arguments, hashes, catalog, list(
        candidate_context = context,
        candidate_context_path = arguments[["candidate-context-output"]],
        motif_hits = hits,
        motif_hits_path = arguments[["motif-hits-output"]],
        sequence_logo = logo,
        sequence_logo_path = arguments[["sequence-logo-output"]],
        motif_statistics = statistics,
        motif_statistics_path = arguments[["motif-statistics-output"]]
    ))
    assert_output_shape(receipt, CONTEXT_RECEIPT_COLUMNS, "Context receipt")
    write_tsv(receipt, arguments[["context-receipt-output"]])

    message(
        "Scientific-context projection completed: ", nrow(context),
        " candidate contexts, ", nrow(hits), " motif hits."
    )
}

main()
