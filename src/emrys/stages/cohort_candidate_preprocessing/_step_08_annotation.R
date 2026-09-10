# Owner-private Step 08 annotation model and overlap mechanics.

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
    required <- c("type", "gene_id", "transcript_id")
    missing <- setdiff(required, names(S4Vectors::mcols(imported)))
    if (length(missing) > 0L) {
        abort(
            "Annotation GTF is missing required field(s): ",
            paste(missing, collapse = ", ")
        )
    }
    S4Vectors::mcols(imported) <- S4Vectors::DataFrame(
        gene_id = as.character(imported$gene_id),
        transcript_id = as.character(imported$transcript_id),
        type_normalized = normalize_feature_type(imported$type)
    )
    relevant_types <- c(
        "exon", "cds", "utr", "five_prime_utr", "5utr", "5_utr",
        "three_prime_utr", "3utr", "3_utr"
    )
    relevant <- imported$type_normalized %in% relevant_types
    if (any(
        relevant &
        (is.na(imported$gene_id) | !nzchar(imported$gene_id) |
         is.na(imported$transcript_id) | !nzchar(imported$transcript_id))
    )) {
        abort(
            "Every exon, CDS, and UTR annotation must have gene_id and ",
            "transcript_id."
        )
    }
    if (any(relevant & !(as.character(BiocGenerics::strand(imported)) %in% c("+", "-")))) {
        abort("Every exon, CDS, and UTR annotation must use strand + or -.")
    }

    exons <- imported[imported$type_normalized == "exon"]
    if (length(exons) == 0L) {
        abort("Annotation GTF contains no exon features: ", path)
    }
    relevant_features <- imported[relevant]
    transcript_ids <- sort(unique(exons$transcript_id), method = "radix")
    orphan_feature_transcripts <- setdiff(
        unique(relevant_features$transcript_id),
        transcript_ids
    )
    if (length(orphan_feature_transcripts) > 0L) {
        abort(
            "Annotation feature references a transcript with no exon: ",
            sort(orphan_feature_transcripts, method = "radix")[[1L]]
        )
    }
    exon_rows_by_transcript <- split(
        seq_len(length(exons)), exons$transcript_id, drop = TRUE
    )
    feature_rows_by_transcript <- split(
        seq_len(length(relevant_features)),
        relevant_features$transcript_id,
        drop = TRUE
    )
    transcript_rows <- lapply(transcript_ids, function(transcript_id) {
        tx_exons_raw <- exons[exon_rows_by_transcript[[transcript_id]]]
        chromosome <- unique(as.character(GenomeInfoDb::seqnames(tx_exons_raw)))
        strand <- unique(as.character(BiocGenerics::strand(tx_exons_raw)))
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
        tx_features <- relevant_features[feature_rows_by_transcript[[transcript_id]]]
        if (any(as.character(GenomeInfoDb::seqnames(tx_features)) != chromosome) ||
            any(as.character(BiocGenerics::strand(tx_features)) != strand) ||
            any(as.character(tx_features$gene_id) != gene_id)) {
            warning(
                "Skipping transcript ", transcript_id,
                " because it has inconsistent chromosome, strand, or gene ",
                "annotations.",
                call. = FALSE
            )
            return(NULL)
        }
        make_ranges <- function(intervals) {
            GenomicRanges::GRanges(
                seqnames = rep(chromosome, length(intervals)),
                ranges = intervals,
                seqinfo = GenomeInfoDb::seqinfo(imported),
                strand = rep(strand, length(intervals)),
                gene_id = rep(gene_id, length(intervals)),
                transcript_id = rep(transcript_id, length(intervals))
            )
        }
        exonic <- IRanges::reduce(IRanges::ranges(tx_exons_raw))
        span <- IRanges::range(exonic)
        empty <- make_ranges(IRanges::IRanges())
        rows <- list(
            transcripts = make_ranges(span),
            exon = make_ranges(exonic),
            intron = make_ranges(IRanges::gaps(
                exonic, start = BiocGenerics::start(span), end = BiocGenerics::end(span)
            )),
            cds = empty,
            five_prime_utr = empty,
            three_prime_utr = empty
        )
        cds <- IRanges::reduce(IRanges::ranges(
            tx_features[tx_features$type_normalized == "cds"]
        ))
        if (length(cds) > 0L) {
            rows$cds <- make_ranges(cds)
            cds_span <- IRanges::range(cds)
            generic_utr <- IRanges::ranges(tx_features[tx_features$type_normalized == "utr"])
            source <- if (length(generic_utr) > 0L) {
                generic_utr
            } else {
                IRanges::setdiff(exonic, cds_span)
            }
            low <- BiocGenerics::end(source) < BiocGenerics::start(cds_span)
            high <- BiocGenerics::start(source) > BiocGenerics::end(cds_span)
            for (feature in c("five_prime_utr", "three_prime_utr")) {
                aliases <- if (feature == "five_prime_utr") {
                    c(feature, "5utr", "5_utr")
                } else {
                    c(feature, "3utr", "3_utr")
                }
                explicit <- IRanges::ranges(tx_features[tx_features$type_normalized %in% aliases])
                use_low <- (feature == "five_prime_utr") == (strand == "+")
                rows[[feature]] <- make_ranges(if (length(explicit) > 0L) {
                    explicit
                } else {
                    source[if (use_low) low else high]
                })
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
        ranges <- do.call(c, unname(lapply(transcript_rows, `[[`, feature)))
        GenomeInfoDb::keepSeqlevels(
            ranges, unique(as.character(GenomeInfoDb::seqnames(ranges))),
            pruning.mode = "coarse"
        )
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
