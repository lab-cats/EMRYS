# Owner-private Step 08 raw VCF and count validation.

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
