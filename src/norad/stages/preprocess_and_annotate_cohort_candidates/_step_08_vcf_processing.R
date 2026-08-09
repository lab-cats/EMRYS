# Owner-private Step 08 VCF validation and candidate construction.

validate_header_definition <- function(header_table, field, number, type, label) {
    table <- as.data.frame(header_table, stringsAsFactors = FALSE)
    if (!(field %in% rownames(table))) {
        abort("VCF is missing required ", label, " definition: ", field)
    }
    if (!all(c("Number", "Type") %in% names(table))) {
        abort("VCF ", label, " header table lacks Number or Type columns.")
    }
    observed_number <- as.character(table[field, "Number"])
    observed_type <- as.character(table[field, "Type"])
    if (!identical(observed_number, number) ||
        !identical(observed_type, type)) {
        abort(
            "VCF ", label, "/", field, " must be Number=", number,
            " Type=", type, "; got Number=", observed_number,
            " Type=", observed_type, "."
        )
    }
}

validate_numeric_counts <- function(value, label) {
    if (!is.numeric(value) && !is.integer(value)) {
        abort(label, " is not represented as numeric counts.")
    }
    invalid <- !is.na(value) &
        (!is.finite(value) | value < 0 | value != floor(value))
    if (any(invalid)) {
        abort(label, " contains a malformed, negative, or non-integer count.")
    }
    invisible(TRUE)
}

validate_raw_count_value <- function(value, expected_width, label) {
    if (identical(value, ".")) {
        return(invisible(TRUE))
    }
    parts <- strsplit(value, ",", fixed = TRUE)[[1L]]
    if (length(parts) != expected_width ||
        any(!grepl("^([0-9]+|\\.)$", parts))) {
        abort(
            label, " must contain ", expected_width,
            " comma-separated non-negative integer count(s) or '.': ", value
        )
    }
    counts <- rep(NA_real_, length(parts))
    present <- parts != "."
    counts[present] <- suppressWarnings(as.numeric(parts[present]))
    validate_numeric_counts(counts, label)
    invisible(TRUE)
}

validate_raw_vcf_counts <- function(path, sample_ids) {
    connection <- open_text_connection(path)
    on.exit(close(connection), add = TRUE)
    record_number <- 0L

    repeat {
        lines <- readLines(connection, n = 10000L, warn = FALSE)
        if (length(lines) == 0L) {
            break
        }
        lines <- sub("\r$", "", lines)
        records <- lines[nzchar(lines) & !startsWith(lines, "#")]
        for (line in records) {
            record_number <- record_number + 1L
            fields <- strsplit(line, "\t", fixed = TRUE)[[1L]]
            expected_fields <- 9L + length(sample_ids)
            if (length(fields) != expected_fields) {
                abort(
                    "VCF record ", record_number, " must contain exactly ",
                    expected_fields, " tab-separated fields: ", path
                )
            }

            alt_count <- length(strsplit(fields[[5L]], ",", fixed = TRUE)[[1L]])
            expected_ad_width <- alt_count + 1L
            info_fields <- strsplit(fields[[8L]], ";", fixed = TRUE)[[1L]]
            info_ad <- startsWith(info_fields, "AD=") | info_fields == "AD"
            if (sum(info_ad) > 1L) {
                abort("VCF record ", record_number, " repeats INFO/AD: ", path)
            }
            if (any(info_ad)) {
                entry <- info_fields[which(info_ad)[[1L]]]
                if (!startsWith(entry, "AD=")) {
                    abort(
                        "VCF record ", record_number,
                        " has malformed INFO/AD: ", path
                    )
                }
                validate_raw_count_value(
                    substring(entry, 4L),
                    expected_ad_width,
                    paste0("VCF record ", record_number, " INFO/AD")
                )
            }

            format_keys <- strsplit(fields[[9L]], ":", fixed = TRUE)[[1L]]
            if (anyDuplicated(format_keys)) {
                abort(
                    "VCF record ", record_number,
                    " repeats a FORMAT key: ", path
                )
            }
            required <- match(c("DP", "AD"), format_keys)
            if (any(is.na(required))) {
                abort(
                    "VCF record ", record_number,
                    " must include FORMAT/DP and FORMAT/AD: ", path
                )
            }
            for (sample_index in seq_along(sample_ids)) {
                sample_value <- fields[[9L + sample_index]]
                sample_fields <- if (identical(sample_value, ".")) {
                    rep(".", length(format_keys))
                } else {
                    strsplit(sample_value, ":", fixed = TRUE)[[1L]]
                }
                if (length(sample_fields) > length(format_keys)) {
                    abort(
                        "VCF record ", record_number, ", sample ",
                        sample_ids[[sample_index]],
                        " has more values than FORMAT keys: ", path
                    )
                }
                if (length(sample_fields) < length(format_keys)) {
                    sample_fields <- c(
                        sample_fields,
                        rep(".", length(format_keys) - length(sample_fields))
                    )
                }
                validate_raw_count_value(
                    sample_fields[[required[[1L]]]],
                    1L,
                    paste0(
                        "VCF record ", record_number, ", sample ",
                        sample_ids[[sample_index]], " FORMAT/DP"
                    )
                )
                validate_raw_count_value(
                    sample_fields[[required[[2L]]]],
                    expected_ad_width,
                    paste0(
                        "VCF record ", record_number, ", sample ",
                        sample_ids[[sample_index]], " FORMAT/AD"
                    )
                )
            }
        }
    }
    invisible(TRUE)
}

extract_genotype_dp <- function(value, row_count, sample_count) {
    dimensions <- dim(value)
    if (is.null(dimensions) || length(dimensions) != 2L ||
        dimensions[[1L]] != row_count ||
        dimensions[[2L]] != sample_count) {
        abort("Expanded FORMAT/DP does not have record x sample dimensions.")
    }
    result <- matrix(
        as.numeric(value),
        nrow = row_count,
        ncol = sample_count,
        dimnames = dimnames(value)
    )
    validate_numeric_counts(result, "FORMAT/DP")
    result
}

extract_genotype_alt_ad <- function(
    value, row_count, sample_count, dp
) {
    dimensions <- dim(value)
    if (!is.null(dimensions) && length(dimensions) == 3L &&
        identical(as.integer(dimensions), c(row_count, sample_count, 2L))) {
        validate_numeric_counts(value, "FORMAT/AD")
        missing_count <- apply(is.na(value), c(1L, 2L), sum)
        invalid_missing <- (is.na(dp) & missing_count != 2L) |
            (!is.na(dp) & missing_count != 0L)
        if (any(invalid_missing)) {
            abort(
                "FORMAT/DP and the complete FORMAT/AD REF/ALT pair must ",
                "either both be present or both be missing."
            )
        }
        for (allele in 1:2) {
            if (any(value[, , allele] > dp, na.rm = TRUE)) {
                abort("A FORMAT/AD count exceeds FORMAT/DP.")
            }
        }
        result <- matrix(
            as.numeric(value[, , 2L, drop = FALSE]),
            nrow = row_count,
            ncol = sample_count
        )
    } else if (!is.null(dimensions) && length(dimensions) == 2L &&
               identical(as.integer(dimensions), c(row_count, sample_count)) &&
               is.list(value)) {
        result <- matrix(NA_real_, nrow = row_count, ncol = sample_count)
        for (row in seq_len(row_count)) {
            for (sample in seq_len(sample_count)) {
                pair <- value[[row, sample]]
                if (length(pair) != 2L) {
                    abort(
                        "Expanded FORMAT/AD entry is not a REF/ALT pair at ",
                        "row ", row, ", sample ", sample, "."
                    )
                }
                validate_numeric_counts(pair, "FORMAT/AD")
                if ((is.na(dp[[row, sample]]) && !all(is.na(pair))) ||
                    (!is.na(dp[[row, sample]]) && any(is.na(pair)))) {
                    abort(
                        "FORMAT/DP and the complete FORMAT/AD REF/ALT pair ",
                        "must either both be present or both be missing."
                    )
                }
                if (!is.na(dp[[row, sample]]) &&
                    any(pair > dp[[row, sample]])) {
                    abort("A FORMAT/AD count exceeds FORMAT/DP.")
                }
                alternate <- pair[[2L]]
                if (length(alternate) != 1L ||
                    (!is.na(alternate) &&
                     (!is.numeric(alternate) && !is.integer(alternate)))) {
                    abort(
                        "Expanded FORMAT/AD alternate count is malformed at ",
                        "row ", row, ", sample ", sample, "."
                    )
                }
                result[[row, sample]] <- alternate
            }
        }
    } else {
        abort(
            "Expanded FORMAT/AD does not have record x sample x REF/ALT ",
            "dimensions."
        )
    }
    validate_numeric_counts(result, "FORMAT/AD alternate depth")
    result
}

extract_info_alt_ad <- function(
    value, row_count, alt_index, expected_allele_count
) {
    if (length(alt_index) != row_count ||
        length(expected_allele_count) != row_count) {
        abort("Internal INFO/AD alternate-index dimensions are inconsistent.")
    }
    dimensions <- dim(value)
    if (!is.null(dimensions) && length(dimensions) == 2L &&
        dimensions[[1L]] == row_count) {
        if (dimensions[[2L]] < max(expected_allele_count)) {
            abort("INFO/AD has fewer values than REF plus declared ALT alleles.")
        }
        result <- rep(NA_real_, row_count)
        for (row in seq_len(row_count)) {
            width <- expected_allele_count[[row]]
            row_values <- value[row, , drop = TRUE]
            validate_numeric_counts(
                row_values[seq_len(width)], "INFO/AD"
            )
            if (length(row_values) > width &&
                any(!is.na(row_values[(width + 1L):length(row_values)]))) {
                abort("INFO/AD has extra values at expanded row ", row, ".")
            }
            result[[row]] <- row_values[[alt_index[[row]] + 1L]]
        }
    } else {
        pairs <- tryCatch(as.list(value), error = function(error) NULL)
        if (is.null(pairs) || length(pairs) != row_count) {
            abort(
                "Expanded INFO/AD does not contain one REF/ALT pair per allele."
            )
        }
        result <- rep(NA_real_, row_count)
        for (row in seq_len(row_count)) {
            pair <- pairs[[row]]
            expected_width <- expected_allele_count[[row]]
            if (length(pair) == 1L && is.na(pair[[1L]])) {
                result[[row]] <- NA_real_
                next
            }
            if (length(pair) != expected_width) {
                abort(
                    "INFO/AD does not contain REF plus every declared ALT at ",
                    "expanded row ", row, "."
                )
            }
            validate_numeric_counts(pair, "INFO/AD")
            alternate <- pair[[alt_index[[row]] + 1L]]
            if (length(alternate) != 1L ||
                (!is.na(alternate) &&
                 (!is.numeric(alternate) && !is.integer(alternate)))) {
                abort(
                    "Expanded INFO/AD alternate count is malformed at row ",
                    row, "."
                )
            }
            result[[row]] <- alternate
        }
    }
    validate_numeric_counts(result, "INFO/AD alternate depth")
    result
}


empty_sites <- function(sample_ids) {
    result <- data.frame(
        partition_id = character(),
        candidate_id = character(),
        orientation = character(),
        chromosome = character(),
        position = integer(),
        alt_index = integer(),
        genomic_ref = character(),
        genomic_alt = character(),
        rna_ref = character(),
        rna_alt = character(),
        annotation_strand = character(),
        gene_ids = character(),
        transcript_ids = character(),
        is_cds = logical(),
        is_five_prime_utr = logical(),
        is_three_prime_utr = logical(),
        is_exon = logical(),
        is_intron = logical(),
        qual = numeric(),
        filter = character(),
        info_alt_depth = numeric(),
        orientation_policy = character(),
        stringsAsFactors = FALSE,
        check.names = FALSE
    )
    for (prefix in c("DP", "AD", "AF")) {
        for (sample_id in sample_ids) {
            result[[paste0(prefix, "__", sample_id)]] <- numeric()
        }
    }
    result
}

complement_base <- function(value) {
    map <- c(A = "T", C = "G", G = "C", T = "A")
    unname(map[value])
}

process_vcf <- function(
    vcf_path, partition_id, orientation, declared_count, sample_ids,
    annotation_model
) {
    validate_raw_vcf_counts(vcf_path, sample_ids)
    vcf <- tryCatch(
        withCallingHandlers(
            VariantAnnotation::readVcf(file = vcf_path, row.names = FALSE),
            warning = function(warning) {
                abort("VCF parser warning: ", conditionMessage(warning))
            }
        ),
        error = function(error) {
            abort("VCF could not be parsed (", vcf_path, "): ", error$message)
        }
    )
    header <- VariantAnnotation::header(vcf)
    validate_header_definition(
        VariantAnnotation::geno(header), "DP", "1", "Integer", "FORMAT"
    )
    validate_header_definition(
        VariantAnnotation::geno(header), "AD", "R", "Integer", "FORMAT"
    )
    validate_header_definition(
        VariantAnnotation::geno(header), "ADF", "R", "Integer", "FORMAT"
    )
    validate_header_definition(
        VariantAnnotation::geno(header), "ADR", "R", "Integer", "FORMAT"
    )
    validate_header_definition(
        VariantAnnotation::geno(header), "SP", "1", "Integer", "FORMAT"
    )
    validate_header_definition(
        VariantAnnotation::info(header), "AD", "R", "Integer", "INFO"
    )
    validate_header_definition(
        VariantAnnotation::info(header), "ADF", "R", "Integer", "INFO"
    )
    validate_header_definition(
        VariantAnnotation::info(header), "ADR", "R", "Integer", "INFO"
    )
    observed_samples <- as.character(VariantAnnotation::samples(header))
    if (!identical(observed_samples, sample_ids)) {
        abort(
            "VCF sample columns do not exactly match manifest order: ", vcf_path,
            ". Expected ", paste(sample_ids, collapse = ","), "; got ",
            paste(observed_samples, collapse = ","), "."
        )
    }

    observed_records <- nrow(vcf)
    if (observed_records != declared_count) {
        abort(
            "VCF record count does not match Step 07 receipt for ", vcf_path,
            ": declared ", declared_count, ", observed ", observed_records, "."
        )
    }
    if (observed_records == 0L) {
        return(list(
            sites = empty_sites(sample_ids),
            observed_records = 0L,
            observed_alt_alleles = 0L,
            supported_snvs = 0L,
            skipped_symbolic = 0L,
            skipped_non_snv = 0L
        ))
    }

    collapsed_alt <- as.list(VariantAnnotation::alt(vcf))
    alt_counts <- lengths(collapsed_alt)
    if (any(alt_counts < 1L)) {
        abort("VCF record contains no alternate allele: ", vcf_path)
    }
    observed_alt_alleles <- sum(alt_counts)
    expanded <- tryCatch(
        withCallingHandlers(
            VariantAnnotation::expand(vcf, row.names = FALSE),
            warning = function(warning) {
                abort("VCF expansion warning: ", conditionMessage(warning))
            }
        ),
        error = function(error) {
            abort("VCF alternate alleles could not be expanded: ", error$message)
        }
    )
    if (nrow(expanded) != observed_alt_alleles) {
        abort("Expanded VCF row count does not match alternate allele count.")
    }
    alt_index <- sequence(alt_counts)
    chromosome <- as.character(GenomeInfoDb::seqnames(
        SummarizedExperiment::rowRanges(expanded)
    ))
    position <- as.integer(BiocGenerics::start(
        SummarizedExperiment::rowRanges(expanded)
    ))
    genomic_ref <- toupper(as.character(VariantAnnotation::ref(expanded)))
    genomic_alt <- toupper(as.character(VariantAnnotation::alt(expanded)))

    symbolic <- is.na(genomic_alt) | !nzchar(genomic_alt) |
        genomic_alt %in% c(".", "*") |
        grepl("^<.*>$", genomic_alt) |
        grepl("[\\[\\]]", genomic_alt)
    snv <- !symbolic &
        grepl("^[ACGT]$", genomic_ref) &
        grepl("^[ACGT]$", genomic_alt) &
        genomic_ref != genomic_alt
    skipped_symbolic <- sum(symbolic)
    skipped_non_snv <- sum(!symbolic & !snv)

    genotype <- VariantAnnotation::geno(expanded)
    if (!all(c("DP", "AD") %in% names(genotype))) {
        abort("Expanded VCF is missing parsed FORMAT/DP or FORMAT/AD.")
    }
    dp <- extract_genotype_dp(
        genotype$DP, observed_alt_alleles, length(sample_ids)
    )
    ad <- extract_genotype_alt_ad(
        genotype$AD, observed_alt_alleles, length(sample_ids), dp
    )
    af <- matrix(
        NA_real_,
        nrow = observed_alt_alleles,
        ncol = length(sample_ids)
    )
    computable <- !is.na(dp) & dp > 0
    af[computable] <- ad[computable] / dp[computable]

    info <- VariantAnnotation::info(expanded)
    if (!("AD" %in% names(info))) {
        abort("Expanded VCF is missing parsed INFO/AD.")
    }
    expanded_allele_counts <- rep.int(alt_counts + 1L, alt_counts)
    info_alt_depth <- extract_info_alt_ad(
        info$AD,
        observed_alt_alleles,
        alt_index,
        expanded_allele_counts
    )
    supported <- which(snv)
    if (length(supported) == 0L) {
        return(list(
            sites = empty_sites(sample_ids),
            observed_records = observed_records,
            observed_alt_alleles = observed_alt_alleles,
            supported_snvs = 0L,
            skipped_symbolic = skipped_symbolic,
            skipped_non_snv = skipped_non_snv
        ))
    }

    genomic_ref <- genomic_ref[supported]
    genomic_alt <- genomic_alt[supported]
    is_forward_orientation <- orientation == ORIENTATIONS[[1L]]
    annotation_strand <- if (is_forward_orientation) "+" else "-"
    rna_ref <- if (is_forward_orientation) {
        complement_base(genomic_ref)
    } else {
        genomic_ref
    }
    rna_alt <- if (is_forward_orientation) {
        complement_base(genomic_alt)
    } else {
        genomic_alt
    }
    sites <- data.frame(
        partition_id = rep(partition_id, length(supported)),
        candidate_id = paste(
            orientation,
            chromosome[supported],
            position[supported],
            paste0(genomic_ref, ">", genomic_alt),
            sep = "|"
        ),
        orientation = rep(orientation, length(supported)),
        chromosome = chromosome[supported],
        position = position[supported],
        alt_index = as.integer(alt_index[supported]),
        genomic_ref = genomic_ref,
        genomic_alt = genomic_alt,
        rna_ref = rna_ref,
        rna_alt = rna_alt,
        annotation_strand = rep(annotation_strand, length(supported)),
        stringsAsFactors = FALSE,
        check.names = FALSE
    )
    sites <- annotate_candidates(sites, annotation_model)
    sites$qual <- as.numeric(VariantAnnotation::qual(expanded))[supported]
    sites$filter <- as.character(VariantAnnotation::filt(expanded))[supported]
    sites$info_alt_depth <- info_alt_depth[supported]
    sites$orientation_policy <- rep(
        ORIENTATION_POLICY, length(supported)
    )
    for (sample_index in seq_along(sample_ids)) {
        sites[[paste0("DP__", sample_ids[[sample_index]])]] <-
            dp[supported, sample_index]
    }
    for (sample_index in seq_along(sample_ids)) {
        sites[[paste0("AD__", sample_ids[[sample_index]])]] <-
            ad[supported, sample_index]
    }
    for (sample_index in seq_along(sample_ids)) {
        sites[[paste0("AF__", sample_ids[[sample_index]])]] <-
            af[supported, sample_index]
    }
    required_order <- c(
        SITE_METADATA_COLUMNS,
        paste0("DP__", sample_ids),
        paste0("AD__", sample_ids),
        paste0("AF__", sample_ids)
    )
    sites <- sites[, required_order, drop = FALSE]
    list(
        sites = sites,
        observed_records = observed_records,
        observed_alt_alleles = observed_alt_alleles,
        supported_snvs = length(supported),
        skipped_symbolic = skipped_symbolic,
        skipped_non_snv = skipped_non_snv
    )
}

