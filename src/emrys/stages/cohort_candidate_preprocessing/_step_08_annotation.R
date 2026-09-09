# Owner-private Step 08 annotation model and overlap mechanics.

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

has_shared_seqlevel <- function(query, subject) {
    length(intersect(
        as.character(GenomeInfoDb::seqlevels(query)),
        as.character(GenomeInfoDb::seqlevels(subject))
    )) > 0L
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
    relevant_table <- table[relevant, , drop = FALSE]
    transcript_ids <- sort(unique(exons$transcript_id), method = "radix")
    orphan_feature_transcripts <- setdiff(
        unique(relevant_table$transcript_id),
        transcript_ids
    )
    if (length(orphan_feature_transcripts) > 0L) {
        abort(
            "Annotation feature references a transcript with no exon: ",
            sort(orphan_feature_transcripts, method = "radix")[[1L]]
        )
    }
    exon_rows_by_transcript <- split(
        seq_len(nrow(exons)), exons$transcript_id, drop = TRUE
    )
    feature_rows_by_transcript <- split(
        seq_len(nrow(relevant_table)),
        relevant_table$transcript_id,
        drop = TRUE
    )
    transcript_rows <- lapply(transcript_ids, function(transcript_id) {
        tx_exons_raw <- exons[
            exon_rows_by_transcript[[transcript_id]], , drop = FALSE
        ]
        chromosome <- unique(as.character(tx_exons_raw$seqnames))
        strand <- unique(as.character(tx_exons_raw$strand))
        gene_id <- unique(as.character(tx_exons_raw$gene_id))
        if (length(chromosome) != 1L || length(strand) != 1L ||
            length(gene_id) != 1L) {
            warning(
                "Skipping transcript ", transcript_id,
                " because it does not map to exactly one chromosome, ",
                "strand, and gene.",
                call. = FALSE
            )
            return(NULL)
        }
        tx_features <- relevant_table[
            feature_rows_by_transcript[[transcript_id]], , drop = FALSE
        ]
        if (any(as.character(tx_features$seqnames) != chromosome) ||
            any(as.character(tx_features$strand) != strand) ||
            any(as.character(tx_features$gene_id) != gene_id)) {
            warning(
                "Skipping transcript ", transcript_id,
                " because it has inconsistent chromosome, strand, or gene ",
                "annotations.",
                call. = FALSE
            )
            return(NULL)
        }
        make_rows <- function(start, end) {
            data.frame(
                seqnames = rep(chromosome, length(start)),
                start = start, end = end,
                strand = rep(strand, length(start)),
                gene_id = rep(gene_id, length(start)),
                transcript_id = rep(transcript_id, length(start)),
                stringsAsFactors = FALSE
            )
        }
        merged <- merge_simple_intervals(tx_exons_raw$start, tx_exons_raw$end)
        tx_exons <- make_rows(merged$start, merged$end)
        rows <- list(
            transcripts = make_rows(min(merged$start), max(merged$end)),
            exon = tx_exons,
            intron = make_rows(
                utils::head(tx_exons$end, -1L) + 1L,
                utils::tail(tx_exons$start, -1L) - 1L
            ),
            cds = tx_exons[FALSE, , drop = FALSE],
            five_prime_utr = tx_exons[FALSE, , drop = FALSE],
            three_prime_utr = tx_exons[FALSE, , drop = FALSE]
        )

        tx_cds_raw <- tx_features[
            tx_features$type_normalized == "cds", , drop = FALSE
        ]
        if (nrow(tx_cds_raw) > 0L) {
            merged_cds <- merge_simple_intervals(
                tx_cds_raw$start, tx_cds_raw$end
            )
            tx_cds <- make_rows(merged_cds$start, merged_cds$end)
            rows$cds <- tx_cds
            cds_min <- min(tx_cds$start)
            cds_max <- max(tx_cds$end)

            explicit_five_types <- c("five_prime_utr", "5utr", "5_utr")
            explicit_three_types <- c("three_prime_utr", "3utr", "3_utr")
            explicit_five <- tx_features[
                tx_features$type_normalized %in% explicit_five_types,
                , drop = FALSE
            ]
            explicit_three <- tx_features[
                tx_features$type_normalized %in% explicit_three_types,
                , drop = FALSE
            ]
            generic_utr <- tx_features[
                tx_features$type_normalized == "utr", , drop = FALSE
            ]
            source <- if (nrow(generic_utr) > 0L) {
                make_rows(generic_utr$start, generic_utr$end)
            } else {
                derive_outer_utr_rows(tx_exons, cds_min, cds_max)
            }
            classified <- classify_utr_rows(
                source, cds_min, cds_max, strand
            )
            if (nrow(explicit_five) > 0L) {
                rows$five_prime_utr <- make_rows(
                    explicit_five$start, explicit_five$end
                )
            } else {
                rows$five_prime_utr <- classified$five
            }
            if (nrow(explicit_three) > 0L) {
                rows$three_prime_utr <- make_rows(
                    explicit_three$start, explicit_three$end
                )
            } else {
                rows$three_prime_utr <- classified$three
            }
        }
        rows
    })
    transcript_rows <- Filter(Negate(is.null), transcript_rows)
    if (length(transcript_rows) == 0L) {
        abort(
            "Annotation GTF contains no internally consistent transcripts: ",
            path
        )
    }
    feature_names <- names(transcript_rows[[1L]])
    stats::setNames(lapply(feature_names, function(feature) {
        feature_ranges(do.call(rbind, lapply(transcript_rows, `[[`, feature)))
    }), feature_names)
}

annotation_flag <- function(query, subject) {
    result <- rep(FALSE, length(query))
    if (
        length(query) == 0L || length(subject) == 0L ||
        !has_shared_seqlevel(query, subject)
    ) {
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
    if (
        length(model$transcripts) > 0L &&
        has_shared_seqlevel(query, model$transcripts)
    ) {
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
