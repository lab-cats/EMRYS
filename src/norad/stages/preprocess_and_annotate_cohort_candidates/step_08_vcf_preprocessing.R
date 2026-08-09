#!/usr/bin/env Rscript

# Step 08: validate the complete declared Step 07 VCF set, expand alternate
# alleles, apply the provisional legacy orientation policy, annotate candidates,
# and write deterministic cohort-level TSVs. Publication and locking belong to
# src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh; this program writes only its three
# explicitly supplied output paths.

options(stringsAsFactors = FALSE, scipen = 999, digits = 15)

ORIENTATIONS <- c("FWD_like", "REV_like")
ORIENTATION_POLICY <- "legacy_provisional_v1"

STEP07_RECEIPT_COLUMNS <- c(
    "cohort_id", "partition_id", "selector_type", "selector_value",
    "orientation", "vcf_path", "sample_manifest_sha256",
    "partition_manifest_sha256", "sample_count", "vcf_record_count"
)

SITE_METADATA_COLUMNS <- c(
    "partition_id", "candidate_id", "orientation", "chromosome", "position",
    "alt_index", "genomic_ref", "genomic_alt", "rna_ref", "rna_alt",
    "annotation_strand", "gene_ids", "transcript_ids", "is_cds",
    "is_five_prime_utr", "is_three_prime_utr", "is_exon", "is_intron",
    "qual", "filter", "info_alt_depth", "orientation_policy"
)

INPUT_COLUMNS <- c(
    "cohort_id", "partition_id", "selector_type", "selector_value",
    "orientation", "step07_receipt_path", "step07_receipt_sha256",
    "vcf_path", "vcf_sha256", "sample_manifest_sha256",
    "partition_manifest_sha256", "annotation_gtf", "annotation_gtf_sha256",
    "sample_count", "declared_vcf_record_count", "observed_vcf_record_count",
    "observed_alt_allele_count", "supported_snv_count",
    "skipped_symbolic_count", "skipped_non_snv_count",
    "published_candidate_count", "orientation_policy"
)

SUMMARY_COLUMNS <- c(
    "cohort_id", "partition_count", "step07_receipt_count", "input_vcf_count",
    "sample_count", "observed_vcf_record_count", "observed_alt_allele_count",
    "supported_snv_count", "skipped_symbolic_count", "skipped_non_snv_count",
    "published_candidate_count", "sample_manifest_sha256",
    "partition_manifest_sha256", "annotation_gtf", "annotation_gtf_sha256",
    "orientation_policy"
)


empty_feature_ranges <- function() {
    ranges <- GenomicRanges::GRanges()
    S4Vectors::mcols(ranges)$gene_id <- character()
    S4Vectors::mcols(ranges)$transcript_id <- character()
    ranges
}

feature_ranges <- function(table) {
    if (nrow(table) == 0L) {
        return(empty_feature_ranges())
    }
    ranges <- GenomicRanges::GRanges(
        seqnames = table$seqnames,
        ranges = IRanges::IRanges(start = table$start, end = table$end),
        strand = table$strand
    )
    S4Vectors::mcols(ranges)$gene_id <- table$gene_id
    S4Vectors::mcols(ranges)$transcript_id <- table$transcript_id
    ranges
}

normalize_feature_type <- function(value) {
    gsub(
        "_+$", "",
        gsub("[^a-z0-9]+", "_", tolower(as.character(value)))
    )
}

merge_simple_intervals <- function(start, end) {
    if (length(start) == 0L) {
        return(data.frame(start = integer(), end = integer()))
    }
    ordered <- order(start, end, method = "radix")
    start <- as.integer(start[ordered])
    end <- as.integer(end[ordered])
    output_start <- integer(length(start))
    output_end <- integer(length(start))
    count <- 1L
    output_start[[count]] <- start[[1L]]
    output_end[[count]] <- end[[1L]]
    if (length(start) > 1L) {
        for (index in 2L:length(start)) {
            adjacent <- output_end[[count]] < (.Machine$integer.max - 1L) &&
                start[[index]] == output_end[[count]] + 1L
            if (start[[index]] <= output_end[[count]] || adjacent) {
                output_end[[count]] <- max(output_end[[count]], end[[index]])
            } else {
                count <- count + 1L
                output_start[[count]] <- start[[index]]
                output_end[[count]] <- end[[index]]
            }
        }
    }
    data.frame(
        start = output_start[seq_len(count)],
        end = output_end[seq_len(count)]
    )
}

classify_utr_rows <- function(rows, cds_min, cds_max, strand) {
    if (nrow(rows) == 0L || is.na(cds_min) || is.na(cds_max)) {
        return(list(five = rows[FALSE, , drop = FALSE],
                    three = rows[FALSE, , drop = FALSE]))
    }
    low <- rows$end < cds_min
    high <- rows$start > cds_max
    if (strand == "+") {
        list(
            five = rows[low, , drop = FALSE],
            three = rows[high, , drop = FALSE]
        )
    } else {
        list(
            five = rows[high, , drop = FALSE],
            three = rows[low, , drop = FALSE]
        )
    }
}

derive_outer_utr_rows <- function(exons, cds_min, cds_max) {
    result <- list()
    count <- 0L
    for (index in seq_len(nrow(exons))) {
        if (exons$start[[index]] < cds_min) {
            count <- count + 1L
            row <- exons[index, , drop = FALSE]
            row$end <- min(row$end, cds_min - 1L)
            if (row$start <= row$end) {
                result[[count]] <- row
            } else {
                count <- count - 1L
            }
        }
        if (exons$end[[index]] > cds_max) {
            count <- count + 1L
            row <- exons[index, , drop = FALSE]
            row$start <- max(row$start, cds_max + 1L)
            if (row$start <= row$end) {
                result[[count]] <- row
            } else {
                count <- count - 1L
            }
        }
    }
    if (count == 0L) {
        return(exons[FALSE, , drop = FALSE])
    }
    do.call(rbind, result[seq_len(count)])
}

read_annotation_model <- function(path) {
    imported <- tryCatch(
        rtracklayer::import(path, format = "gtf"),
        error = function(error) {
            abort("Annotation GTF could not be imported: ", error$message)
        }
    )
    if (length(imported) == 0L) {
        abort("Annotation GTF contains no features: ", path)
    }
    table <- as.data.frame(imported)
    required <- c(
        "seqnames", "start", "end", "strand", "type", "gene_id",
        "transcript_id"
    )
    missing <- setdiff(required, names(table))
    if (length(missing) > 0L) {
        abort(
            "Annotation GTF is missing required field(s): ",
            paste(missing, collapse = ", ")
        )
    }
    table$type_normalized <- normalize_feature_type(table$type)
    relevant_types <- c(
        "exon", "cds", "utr", "five_prime_utr", "5utr", "5_utr",
        "three_prime_utr", "3utr", "3_utr"
    )
    relevant <- table$type_normalized %in% relevant_types
    if (any(
        relevant &
        (is.na(table$gene_id) | !nzchar(table$gene_id) |
         is.na(table$transcript_id) | !nzchar(table$transcript_id))
    )) {
        abort(
            "Every exon, CDS, and UTR annotation must have gene_id and ",
            "transcript_id."
        )
    }
    if (any(relevant & !(table$strand %in% c("+", "-")))) {
        abort("Every exon, CDS, and UTR annotation must use strand + or -.")
    }

    exons <- table[table$type_normalized == "exon", , drop = FALSE]
    if (nrow(exons) == 0L) {
        abort("Annotation GTF contains no exon features: ", path)
    }
    transcript_ids <- sort(unique(exons$transcript_id), method = "radix")
    orphan_feature_transcripts <- setdiff(
        unique(table$transcript_id[relevant]),
        transcript_ids
    )
    if (length(orphan_feature_transcripts) > 0L) {
        abort(
            "Annotation feature references a transcript with no exon: ",
            sort(orphan_feature_transcripts, method = "radix")[[1L]]
        )
    }
    transcript_rows <- vector("list", length(transcript_ids))
    exon_rows <- list()
    intron_rows <- list()
    cds_rows <- list()
    five_rows <- list()
    three_rows <- list()
    exon_count <- intron_count <- cds_count <- five_count <- three_count <- 0L

    for (index in seq_along(transcript_ids)) {
        transcript_id <- transcript_ids[[index]]
        tx_exons_raw <- exons[
            exons$transcript_id == transcript_id, , drop = FALSE
        ]
        chromosome <- unique(as.character(tx_exons_raw$seqnames))
        strand <- unique(as.character(tx_exons_raw$strand))
        gene_id <- unique(as.character(tx_exons_raw$gene_id))
        if (length(chromosome) != 1L || length(strand) != 1L ||
            length(gene_id) != 1L) {
            abort(
                "Transcript ", transcript_id,
                " does not map to exactly one chromosome, strand, and gene."
            )
        }
        tx_features <- table[
            relevant & table$transcript_id == transcript_id, , drop = FALSE
        ]
        if (any(as.character(tx_features$seqnames) != chromosome) ||
            any(as.character(tx_features$strand) != strand) ||
            any(as.character(tx_features$gene_id) != gene_id)) {
            abort(
                "Transcript ", transcript_id,
                " has inconsistent chromosome, strand, or gene annotations."
            )
        }
        merged <- merge_simple_intervals(tx_exons_raw$start, tx_exons_raw$end)
        tx_exons <- data.frame(
            seqnames = chromosome,
            start = merged$start,
            end = merged$end,
            strand = strand,
            gene_id = gene_id,
            transcript_id = transcript_id,
            stringsAsFactors = FALSE
        )
        transcript_rows[[index]] <- data.frame(
            seqnames = chromosome,
            start = min(merged$start),
            end = max(merged$end),
            strand = strand,
            gene_id = gene_id,
            transcript_id = transcript_id,
            stringsAsFactors = FALSE
        )
        for (row_index in seq_len(nrow(tx_exons))) {
            exon_count <- exon_count + 1L
            exon_rows[[exon_count]] <- tx_exons[row_index, , drop = FALSE]
        }
        if (nrow(tx_exons) > 1L) {
            for (row_index in seq_len(nrow(tx_exons) - 1L)) {
                intron_count <- intron_count + 1L
                intron_rows[[intron_count]] <- data.frame(
                    seqnames = chromosome,
                    start = tx_exons$end[[row_index]] + 1L,
                    end = tx_exons$start[[row_index + 1L]] - 1L,
                    strand = strand,
                    gene_id = gene_id,
                    transcript_id = transcript_id,
                    stringsAsFactors = FALSE
                )
            }
        }

        tx_cds_raw <- table[
            table$type_normalized == "cds" &
            table$transcript_id == transcript_id, , drop = FALSE
        ]
        if (nrow(tx_cds_raw) > 0L) {
            merged_cds <- merge_simple_intervals(
                tx_cds_raw$start, tx_cds_raw$end
            )
            tx_cds <- data.frame(
                seqnames = chromosome,
                start = merged_cds$start,
                end = merged_cds$end,
                strand = strand,
                gene_id = gene_id,
                transcript_id = transcript_id,
                stringsAsFactors = FALSE
            )
            for (row_index in seq_len(nrow(tx_cds))) {
                cds_count <- cds_count + 1L
                cds_rows[[cds_count]] <- tx_cds[row_index, , drop = FALSE]
            }
            cds_min <- min(tx_cds$start)
            cds_max <- max(tx_cds$end)

            explicit_five_types <- c("five_prime_utr", "5utr", "5_utr")
            explicit_three_types <- c("three_prime_utr", "3utr", "3_utr")
            explicit_five <- table[
                table$transcript_id == transcript_id &
                table$type_normalized %in% explicit_five_types, , drop = FALSE
            ]
            explicit_three <- table[
                table$transcript_id == transcript_id &
                table$type_normalized %in% explicit_three_types, , drop = FALSE
            ]
            generic_utr <- table[
                table$transcript_id == transcript_id &
                table$type_normalized == "utr", , drop = FALSE
            ]
            make_explicit <- function(rows) {
                data.frame(
                    seqnames = chromosome,
                    start = rows$start,
                    end = rows$end,
                    strand = strand,
                    gene_id = gene_id,
                    transcript_id = transcript_id,
                    stringsAsFactors = FALSE
                )
            }
            source <- if (nrow(generic_utr) > 0L) {
                make_explicit(generic_utr)
            } else {
                derive_outer_utr_rows(tx_exons, cds_min, cds_max)
            }
            classified <- classify_utr_rows(
                source, cds_min, cds_max, strand
            )
            if (nrow(explicit_five) > 0L) {
                tx_five <- make_explicit(explicit_five)
            } else {
                tx_five <- classified$five
            }
            if (nrow(explicit_three) > 0L) {
                tx_three <- make_explicit(explicit_three)
            } else {
                tx_three <- classified$three
            }
            if (nrow(tx_five) > 0L) {
                for (row_index in seq_len(nrow(tx_five))) {
                    five_count <- five_count + 1L
                    five_rows[[five_count]] <- tx_five[
                        row_index, , drop = FALSE
                    ]
                }
            }
            if (nrow(tx_three) > 0L) {
                for (row_index in seq_len(nrow(tx_three))) {
                    three_count <- three_count + 1L
                    three_rows[[three_count]] <- tx_three[
                        row_index, , drop = FALSE
                    ]
                }
            }
        }
    }

    bind_or_empty <- function(rows, count) {
        if (count == 0L) {
            return(data.frame(
                seqnames = character(), start = integer(), end = integer(),
                strand = character(), gene_id = character(),
                transcript_id = character(), stringsAsFactors = FALSE
            ))
        }
        do.call(rbind, rows[seq_len(count)])
    }

    list(
        transcripts = feature_ranges(do.call(rbind, transcript_rows)),
        exon = feature_ranges(bind_or_empty(exon_rows, exon_count)),
        intron = feature_ranges(bind_or_empty(intron_rows, intron_count)),
        cds = feature_ranges(bind_or_empty(cds_rows, cds_count)),
        five_prime_utr = feature_ranges(
            bind_or_empty(five_rows, five_count)
        ),
        three_prime_utr = feature_ranges(
            bind_or_empty(three_rows, three_count)
        )
    )
}

annotation_flag <- function(query, subject) {
    result <- rep(FALSE, length(query))
    if (length(query) == 0L || length(subject) == 0L) {
        return(result)
    }
    hits <- GenomicRanges::findOverlaps(
        query, subject, ignore.strand = FALSE
    )
    result[unique(S4Vectors::queryHits(hits))] <- TRUE
    result
}

annotate_candidates <- function(candidates, model) {
    count <- nrow(candidates)
    if (count == 0L) {
        candidates$gene_ids <- character()
        candidates$transcript_ids <- character()
        candidates$is_cds <- logical()
        candidates$is_five_prime_utr <- logical()
        candidates$is_three_prime_utr <- logical()
        candidates$is_exon <- logical()
        candidates$is_intron <- logical()
        return(candidates)
    }
    query <- GenomicRanges::GRanges(
        seqnames = candidates$chromosome,
        ranges = IRanges::IRanges(
            start = candidates$position, end = candidates$position
        ),
        strand = candidates$annotation_strand
    )
    gene_ids <- rep(NA_character_, count)
    transcript_ids <- rep(NA_character_, count)
    if (length(model$transcripts) > 0L) {
        hits <- GenomicRanges::findOverlaps(
            query, model$transcripts, ignore.strand = FALSE
        )
        if (length(hits) > 0L) {
            grouped <- split(
                S4Vectors::subjectHits(hits),
                S4Vectors::queryHits(hits)
            )
            model_gene <- as.character(
                S4Vectors::mcols(model$transcripts)$gene_id
            )
            model_tx <- as.character(
                S4Vectors::mcols(model$transcripts)$transcript_id
            )
            for (key in names(grouped)) {
                query_index <- as.integer(key)
                subjects <- grouped[[key]]
                gene_ids[[query_index]] <- paste(
                    sort(
                        unique(model_gene[subjects]), method = "radix"
                    ),
                    collapse = ";"
                )
                transcript_ids[[query_index]] <- paste(
                    sort(unique(model_tx[subjects]), method = "radix"),
                    collapse = ";"
                )
            }
        }
    }
    candidates$gene_ids <- gene_ids
    candidates$transcript_ids <- transcript_ids
    candidates$is_cds <- annotation_flag(query, model$cds)
    candidates$is_five_prime_utr <- annotation_flag(
        query, model$five_prime_utr
    )
    candidates$is_three_prime_utr <- annotation_flag(
        query, model$three_prime_utr
    )
    candidates$is_exon <- annotation_flag(query, model$exon)
    candidates$is_intron <- annotation_flag(query, model$intron)
    candidates
}

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

resolve_receipt_vcf_path <- function(path) {
    if (!file.exists(path)) {
        abort("Step 07 receipt declares a VCF path that does not exist: ", path)
    }
    normalize_existing_path(path)
}

validate_step07_receipt <- function(
    path, cohort_id, partition, sample_ids, sample_hash, partition_hash,
    step07_root
) {
    receipt <- read_tsv(
        paste0("Step 07 receipt for partition ", partition$partition_id),
        path,
        STEP07_RECEIPT_COLUMNS
    )
    if (nrow(receipt) != 2L) {
        abort("Step 07 receipt must contain exactly two rows: ", path)
    }
    if (!identical(receipt$orientation, ORIENTATIONS)) {
        abort(
            "Step 07 receipt orientations must be exactly ",
            paste(ORIENTATIONS, collapse = " then "), ": ",
            path
        )
    }
    required_values <- as.matrix(receipt)
    if (any(is.na(required_values) | !nzchar(required_values))) {
        abort("Step 07 receipt contains an empty required value: ", path)
    }
    if (any(receipt$cohort_id != cohort_id) ||
        any(receipt$partition_id != partition$partition_id) ||
        any(receipt$selector_type != partition$selector_type) ||
        any(receipt$selector_value != partition$selector_value)) {
        abort(
            "Step 07 receipt cohort, partition, or selector does not match ",
            "the declared Step 08 inputs: ", path
        )
    }
    if (any(tolower(receipt$sample_manifest_sha256) != sample_hash) ||
        any(tolower(receipt$partition_manifest_sha256) != partition_hash)) {
        abort("Step 07 receipt manifest hash mismatch: ", path)
    }
    sample_counts <- vapply(
        seq_len(nrow(receipt)),
        function(index) parse_nonnegative_integer(
            "Step 07 receipt sample_count", receipt$sample_count[[index]]
        ),
        integer(1)
    )
    if (any(sample_counts != length(sample_ids))) {
        abort("Step 07 receipt sample_count mismatch: ", path)
    }
    declared_counts <- vapply(
        seq_len(nrow(receipt)),
        function(index) parse_nonnegative_integer(
            "Step 07 receipt vcf_record_count",
            receipt$vcf_record_count[[index]]
        ),
        integer(1)
    )

    for (index in seq_len(nrow(receipt))) {
        expected <- file.path(
            step07_root, cohort_id, partition$partition_id,
            paste0(
                cohort_id, ".", partition$partition_id, ".",
                receipt$orientation[[index]], ".mpileup.vcf"
            )
        )
        validate_nonempty_file(
            paste0("Step 07 ", receipt$orientation[[index]], " VCF"), expected
        )
        declared <- resolve_receipt_vcf_path(receipt$vcf_path[[index]])
        if (!identical(declared, normalize_existing_path(expected))) {
            abort(
                "Step 07 receipt VCF path does not match the required path for ",
                receipt$orientation[[index]], ": ", path
            )
        }
    }
    list(receipt = receipt, declared_counts = declared_counts)
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

write_tsv <- function(table, path) {
    write.table(
        table,
        file = path,
        sep = "\t",
        quote = FALSE,
        row.names = FALSE,
        col.names = TRUE,
        na = "NA",
        eol = "\n"
    )
}

main <- function() {
    arguments <- parse_arguments(commandArgs(trailingOnly = TRUE))
    require_packages()

    cohort_id <- arguments[["cohort-id"]]
    validate_safe_id("cohort_id", cohort_id)
    sample_manifest <- arguments[["sample-manifest"]]
    partition_manifest <- arguments[["partition-manifest"]]
    step07_root <- arguments[["step07-root"]]
    annotation_gtf <- arguments[["annotation-gtf"]]
    validate_nonempty_file("Sample manifest", sample_manifest)
    validate_nonempty_file("Partition manifest", partition_manifest)
    validate_nonempty_file("Annotation GTF", annotation_gtf)
    if (!dir.exists(step07_root)) {
        abort("Step 07 root does not exist or is not a directory: ", step07_root)
    }

    sample_hash <- validate_hash(
        "sample-manifest-sha256",
        arguments[["sample-manifest-sha256"]]
    )
    partition_hash <- validate_hash(
        "partition-manifest-sha256",
        arguments[["partition-manifest-sha256"]]
    )
    annotation_hash <- validate_hash(
        "annotation-gtf-sha256",
        arguments[["annotation-gtf-sha256"]]
    )
    if (sha256_file(sample_manifest) != sample_hash) {
        abort("Sample manifest SHA-256 changed before R processing.")
    }
    if (sha256_file(partition_manifest) != partition_hash) {
        abort("Partition manifest SHA-256 changed before R processing.")
    }
    if (sha256_file(annotation_gtf) != annotation_hash) {
        abort("Annotation GTF SHA-256 changed before R processing.")
    }

    output_paths <- c(
        arguments[["sites-output"]],
        arguments[["inputs-output"]],
        arguments[["summary-output"]]
    )
    if (anyDuplicated(normalizePath(
        output_paths, winslash = "/", mustWork = FALSE
    ))) {
        abort("Step 08 output paths must be distinct.")
    }
    for (path in output_paths) {
        if (!dir.exists(dirname(path))) {
            abort("Output parent directory does not exist: ", dirname(path))
        }
        if (file.exists(path)) {
            abort("Refusing to overwrite an existing temporary output: ", path)
        }
    }
    successful <- FALSE
    on.exit({
        if (!successful) {
            unlink(output_paths[file.exists(output_paths)], force = TRUE)
        }
    }, add = TRUE)

    sample_ids <- read_sample_manifest(sample_manifest)
    partitions <- read_partition_manifest(partition_manifest)
    validate_partition_nonoverlap(partitions, partition_manifest)
    annotation_model <- read_annotation_model(annotation_gtf)

    all_sites <- list()
    input_rows <- list()
    site_count <- 0L
    input_count <- 0L
    for (partition_index in seq_len(nrow(partitions))) {
        partition <- partitions[partition_index, , drop = FALSE]
        receipt_path <- file.path(
            step07_root, cohort_id, partition$partition_id,
            paste0(
                cohort_id, ".", partition$partition_id,
                ".step07_outputs.tsv"
            )
        )
        receipt_hash_before <- sha256_file(receipt_path)
        receipt_data <- validate_step07_receipt(
            receipt_path,
            cohort_id,
            partition,
            sample_ids,
            sample_hash,
            partition_hash,
            step07_root
        )

        for (orientation_index in seq_along(ORIENTATIONS)) {
            orientation <- ORIENTATIONS[[orientation_index]]
            vcf_path <- file.path(
                step07_root, cohort_id, partition$partition_id,
                paste0(
                    cohort_id, ".", partition$partition_id, ".", orientation,
                    ".mpileup.vcf"
                )
            )
            vcf_hash_before <- sha256_file(vcf_path)
            result <- process_vcf(
                vcf_path,
                partition$partition_id,
                orientation,
                receipt_data$declared_counts[[orientation_index]],
                sample_ids,
                annotation_model
            )
            vcf_hash_after <- sha256_file(vcf_path)
            if (!identical(vcf_hash_before, vcf_hash_after)) {
                abort(
                    "Step 07 VCF changed during semantic processing: ",
                    vcf_path
                )
            }
            if (nrow(result$sites) > 0L) {
                site_count <- site_count + 1L
                all_sites[[site_count]] <- result$sites
            }
            input_count <- input_count + 1L
            input_rows[[input_count]] <- data.frame(
                cohort_id = cohort_id,
                partition_id = partition$partition_id,
                selector_type = partition$selector_type,
                selector_value = partition$selector_value,
                orientation = orientation,
                step07_receipt_path = receipt_path,
                step07_receipt_sha256 = receipt_hash_before,
                vcf_path = vcf_path,
                vcf_sha256 = vcf_hash_before,
                sample_manifest_sha256 = sample_hash,
                partition_manifest_sha256 = partition_hash,
                annotation_gtf = annotation_gtf,
                annotation_gtf_sha256 = annotation_hash,
                sample_count = length(sample_ids),
                declared_vcf_record_count =
                    receipt_data$declared_counts[[orientation_index]],
                observed_vcf_record_count = result$observed_records,
                observed_alt_allele_count = result$observed_alt_alleles,
                supported_snv_count = result$supported_snvs,
                skipped_symbolic_count = result$skipped_symbolic,
                skipped_non_snv_count = result$skipped_non_snv,
                published_candidate_count = nrow(result$sites),
                orientation_policy = ORIENTATION_POLICY,
                stringsAsFactors = FALSE,
                check.names = FALSE
            )
        }
        receipt_hash_after <- sha256_file(receipt_path)
        if (!identical(receipt_hash_before, receipt_hash_after)) {
            abort(
                "Step 07 receipt changed during semantic processing: ",
                receipt_path
            )
        }
    }

    sites <- if (site_count == 0L) {
        empty_sites(sample_ids)
    } else {
        do.call(rbind, all_sites[seq_len(site_count)])
    }
    input_receipt <- do.call(rbind, input_rows)
    input_receipt <- input_receipt[, INPUT_COLUMNS, drop = FALSE]
    if (anyDuplicated(sites$candidate_id)) {
        duplicate <- unique(
            sites$candidate_id[duplicated(sites$candidate_id)]
        )[[1L]]
        abort(
            "Duplicate partition-independent candidate_id across declared ",
            "inputs: ", duplicate
        )
    }

    count_columns <- c(
        "observed_vcf_record_count", "observed_alt_allele_count",
        "supported_snv_count", "skipped_symbolic_count",
        "skipped_non_snv_count", "published_candidate_count"
    )
    totals <- vapply(
        count_columns,
        function(column) sum(as.numeric(input_receipt[[column]])),
        numeric(1)
    )
    if (totals[["supported_snv_count"]] !=
        totals[["published_candidate_count"]] ||
        totals[["published_candidate_count"]] != nrow(sites)) {
        abort(
            "Step 08 supported, published, and combined candidate counts do ",
            "not reconcile."
        )
    }
    if (totals[["observed_alt_allele_count"]] !=
        totals[["supported_snv_count"]] +
        totals[["skipped_symbolic_count"]] +
        totals[["skipped_non_snv_count"]]) {
        abort("Step 08 alternate-allele counts do not reconcile.")
    }

    summary <- data.frame(
        cohort_id = cohort_id,
        partition_count = nrow(partitions),
        step07_receipt_count = nrow(partitions),
        input_vcf_count = nrow(input_receipt),
        sample_count = length(sample_ids),
        observed_vcf_record_count =
            totals[["observed_vcf_record_count"]],
        observed_alt_allele_count =
            totals[["observed_alt_allele_count"]],
        supported_snv_count = totals[["supported_snv_count"]],
        skipped_symbolic_count = totals[["skipped_symbolic_count"]],
        skipped_non_snv_count = totals[["skipped_non_snv_count"]],
        published_candidate_count =
            totals[["published_candidate_count"]],
        sample_manifest_sha256 = sample_hash,
        partition_manifest_sha256 = partition_hash,
        annotation_gtf = annotation_gtf,
        annotation_gtf_sha256 = annotation_hash,
        orientation_policy = ORIENTATION_POLICY,
        stringsAsFactors = FALSE,
        check.names = FALSE
    )
    summary <- summary[, SUMMARY_COLUMNS, drop = FALSE]

    expected_site_columns <- c(
        SITE_METADATA_COLUMNS,
        paste0("DP__", sample_ids),
        paste0("AD__", sample_ids),
        paste0("AF__", sample_ids)
    )
    sites <- sites[, expected_site_columns, drop = FALSE]
    write_tsv(sites, output_paths[[1L]])
    write_tsv(summary, output_paths[[3L]])
    write_tsv(input_receipt, output_paths[[2L]])

    reread_sites <- read_tsv(
        "Written Step 08 sites table",
        output_paths[[1L]],
        expected_site_columns
    )
    reread_inputs <- read_tsv(
        "Written Step 08 input receipt",
        output_paths[[2L]],
        INPUT_COLUMNS
    )
    reread_summary <- read_tsv(
        "Written Step 08 summary",
        output_paths[[3L]],
        SUMMARY_COLUMNS
    )
    if (nrow(reread_sites) != nrow(sites) ||
        nrow(reread_inputs) != nrow(input_receipt) ||
        nrow(reread_summary) != 1L) {
        abort("Written Step 08 table row counts failed revalidation.")
    }
    if (nrow(reread_sites) > 0L &&
        !identical(reread_sites$candidate_id, sites$candidate_id)) {
        abort("Written Step 08 candidate order changed during serialization.")
    }
    if (!all(!is.na(reread_inputs$orientation_policy) &
            reread_inputs$orientation_policy == ORIENTATION_POLICY) ||
        !(
            !is.na(reread_summary$orientation_policy[[1L]]) &&
            reread_summary$orientation_policy[[1L]] == ORIENTATION_POLICY
        )) {
        abort("Written Step 08 orientation policy failed revalidation.")
    }
    successful <- TRUE

    message(
        "Step 08 preprocessing complete: ", nrow(input_receipt),
        " VCFs, ", nrow(sites), " supported SNV candidates."
    )
}

load_step08_input_contract <- local({
    owner_filename <- "_step_08_input_contract.R"

    function() {
        invocation <- commandArgs(trailingOnly = FALSE)
        file_options <- invocation[startsWith(invocation, "--file=")]
        if (length(file_options) != 1L) {
            stop("Could not resolve the Step 08 R entry point from --file=.",
                 call. = FALSE)
        }
        entry_value <- substring(file_options[[1L]], nchar("--file=") + 1L)
        if (!nzchar(entry_value)) {
            stop("The Step 08 --file= entry point is empty.", call. = FALSE)
        }
        entry_path <- normalizePath(
            entry_value,
            winslash = "/",
            mustWork = TRUE
        )
        shared_path <- file.path(
            dirname(entry_path), "../../libraries/input_contract.R"
        )
        owner_path <- file.path(dirname(entry_path), owner_filename)
        owner_info <- file.info(owner_path)
        if (!file.exists(owner_path) || isTRUE(owner_info$isdir) ||
            is.na(owner_info$size) || owner_info$size <= 0L) {
            stop("Step 08 input-contract owner is unavailable: ", owner_path,
                 call. = FALSE)
        }
        sys.source(shared_path, envir = globalenv(), keep.source = FALSE)
        sys.source(owner_path, envir = globalenv(), keep.source = FALSE)
        invisible(owner_path)
    }
})

tryCatch(
    {
        load_step08_input_contract()
        main()
    },
    error = function(error) {
        message("ERROR: ", conditionMessage(error))
        quit(status = 1L)
    }
)
