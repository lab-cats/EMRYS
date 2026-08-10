# Owner-private Step 08 argument, path, manifest, and partition admission.
# This module defines helpers only; the public R entry point resolves and loads
# it without changing the working directory or loading packages.

ARGUMENT_NAMES <- c(
    "cohort-id", "sample-manifest", "partition-manifest", "step07-root",
    "annotation-gtf", "sample-manifest-sha256", "partition-manifest-sha256",
    "annotation-gtf-sha256", "sites-output", "inputs-output", "summary-output"
)

usage <- function() {
    cat(paste0(
        "Usage:\n",
        "  Rscript src/norad/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R \\\n",
        "    --cohort-id COHORT_ID \\\n",
        "    --sample-manifest SAMPLE_MANIFEST \\\n",
        "    --partition-manifest PARTITION_MANIFEST \\\n",
        "    --step07-root STEP07_ROOT \\\n",
        "    --annotation-gtf ANNOTATION_GTF \\\n",
        "    --sample-manifest-sha256 SHA256 \\\n",
        "    --partition-manifest-sha256 SHA256 \\\n",
        "    --annotation-gtf-sha256 SHA256 \\\n",
        "    --sites-output PATH \\\n",
        "    --inputs-output PATH \\\n",
        "    --summary-output PATH\n"
    ))
}

parse_arguments <- function(values) {
    parse_named_arguments(values, ARGUMENT_NAMES, usage_function = usage)
}

require_packages <- function() {
    required <- c(
        "VariantAnnotation", "GenomicRanges", "IRanges", "S4Vectors",
        "SummarizedExperiment", "GenomeInfoDb", "BiocGenerics", "rtracklayer"
    )
    missing <- required[
        !vapply(required, requireNamespace, logical(1), quietly = TRUE)
    ]
    if (length(missing) > 0L) {
        abort(
            "Missing required R package(s): ", paste(missing, collapse = ", "),
            ". Install them in the supported R environment before Step 08."
        )
    }
}

validate_safe_id <- function(label, value) {
    if (!grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", value)) {
        abort(
            label, " must match [A-Za-z0-9][A-Za-z0-9._-]*; got: ", value
        )
    }
}

validate_hash <- function(label, value) {
    if (!grepl("^[[:xdigit:]]{64}$", value)) {
        abort(label, " is not a 64-character SHA-256 digest: ", value)
    }
    tolower(value)
}

same_path <- function(left, right) {
    identical(normalize_existing_path(left), normalize_existing_path(right))
}

sha256_file <- function(path) {
    sha256_file_with_fallback(
        path,
        paste0(
            "No SHA-256 implementation is available. Step 08 requires ",
            "sha256sum or shasum."
        )
    )
}

read_tsv <- function(label, path, expected_columns = NULL) {
    read_contract_tsv(label, path, expected_columns)
}

parse_nonnegative_integer <- function(label, value) {
    if (length(value) != 1L || is.na(value) ||
        !grepl("^(0|[1-9][0-9]*)$", value)) {
        abort(label, " must be a non-negative integer; got: ", value)
    }
    numeric_value <- suppressWarnings(as.numeric(value))
    if (!is.finite(numeric_value) || numeric_value > .Machine$integer.max) {
        abort(label, " exceeds the supported integer range: ", value)
    }
    as.integer(numeric_value)
}

read_sample_manifest <- function(path) {
    manifest <- read_tsv("Sample manifest", path)
    if (!("sample_id" %in% names(manifest))) {
        abort("Sample manifest is missing the required sample_id column: ", path)
    }
    if (nrow(manifest) == 0L) {
        abort("Sample manifest contains no sample rows: ", path)
    }
    sample_ids <- manifest$sample_id
    if (any(is.na(sample_ids) | !nzchar(sample_ids))) {
        abort("Sample manifest contains an empty sample_id: ", path)
    }
    invisible(lapply(sample_ids, function(id) {
        validate_safe_id("sample_id", id)
    }))
    duplicate <- unique(sample_ids[duplicated(sample_ids)])
    if (length(duplicate) > 0L) {
        abort("Sample manifest contains duplicate sample_id: ", duplicate[[1L]])
    }
    sample_ids
}

read_partition_manifest <- function(path) {
    columns <- c("partition_id", "selector_type", "selector_value")
    manifest <- read_tsv("Partition manifest", path)
    if (!identical(names(manifest), columns)) {
        abort(
            "Partition manifest must have exactly these columns in order: ",
            paste(columns, collapse = "\t")
        )
    }
    if (nrow(manifest) == 0L) {
        abort("Partition manifest contains no partition rows: ", path)
    }
    manifest_values <- as.matrix(manifest)
    if (any(is.na(manifest_values) | !nzchar(manifest_values))) {
        abort("Partition manifest contains an empty required value: ", path)
    }
    invisible(lapply(manifest$partition_id, function(id) {
        validate_safe_id("partition_id", id)
    }))
    duplicate <- unique(
        manifest$partition_id[duplicated(manifest$partition_id)]
    )
    if (length(duplicate) > 0L) {
        abort("Duplicate partition_id in partition manifest: ", duplicate[[1L]])
    }
    invalid <- !(manifest$selector_type %in% c("region", "regions_file"))
    if (any(invalid)) {
        abort(
            "Invalid selector_type for partition ",
            manifest$partition_id[which(invalid)[[1L]]], ": ",
            manifest$selector_type[which(invalid)[[1L]]]
        )
    }
    manifest
}

parse_coordinate <- function(label, value, allow_zero = FALSE) {
    if (!grepl("^[0-9]+$", value)) {
        abort(label, " must be an integer; got: ", value)
    }
    result <- suppressWarnings(as.numeric(value))
    minimum <- if (allow_zero) 0 else 1
    if (!is.finite(result) || result < minimum ||
        result > (.Machine$integer.max - 1L)) {
        abort(label, " is out of range: ", value)
    }
    as.integer(result)
}

make_interval_table <- function(chromosome, start, end, partition_id) {
    data.frame(
        chromosome = as.character(chromosome),
        start = as.integer(start),
        end = as.integer(end),
        partition_id = as.character(partition_id),
        stringsAsFactors = FALSE
    )
}

parse_region_selector <- function(value, partition_id) {
    tokens <- strsplit(value, ",", fixed = TRUE)[[1L]]
    tokens <- trimws(tokens)
    if (length(tokens) == 0L || any(!nzchar(tokens))) {
        abort("Empty region token for partition ", partition_id)
    }
    result <- vector("list", length(tokens))
    maximum <- .Machine$integer.max - 1L

    for (index in seq_along(tokens)) {
        token <- tokens[[index]]
        colon_count <- lengths(regmatches(
            token, gregexpr(":", token, fixed = TRUE)
        ))
        if (colon_count > 1L) {
            abort(
                "Invalid region selector for partition ", partition_id, ": ",
                token
            )
        }
        has_coordinates <- colon_count == 1L
        chromosome <- if (has_coordinates) {
            sub(":.*$", "", token)
        } else {
            token
        }
        if (!nzchar(chromosome)) {
            abort(
                "Invalid region selector for partition ", partition_id, ": ",
                token
            )
        }
        start <- 1L
        end <- maximum
        if (has_coordinates) {
            range <- sub("^[^:]*:", "", token)
            if (!nzchar(range)) {
                abort(
                    "Invalid empty coordinate in region selector for partition ",
                    partition_id, ": ", token
                )
            }
            if (grepl("-", range, fixed = TRUE)) {
                if (!grepl("^[0-9]+-[0-9]*$", range)) {
                    abort(
                        "Invalid coordinate range for partition ", partition_id,
                        ": ", token
                    )
                }
                start_value <- sub("-.*$", "", range)
                end_value <- sub("^[^-]*-", "", range)
                start <- parse_coordinate("Region start", start_value)
                end <- if (nzchar(end_value)) {
                    parse_coordinate("Region end", end_value)
                } else {
                    maximum
                }
            } else {
                start <- parse_coordinate("Region position", range)
                end <- start
            }
        }
        if (end < start) {
            abort(
                "Region end is before start for partition ", partition_id,
                ": ", token
            )
        }
        result[[index]] <- make_interval_table(
            chromosome, start, end, partition_id
        )
    }
    do.call(rbind, result)
}

open_text_connection <- function(path) {
    if (grepl("\\.gz$", path, ignore.case = TRUE)) {
        gzfile(path, open = "rt")
    } else {
        file(path, open = "rt")
    }
}

resolve_selector_file <- function(value, manifest_path) {
    resolved <- if (startsWith(value, "/")) {
        value
    } else {
        file.path(dirname(manifest_path), value)
    }
    if (!file.exists(resolved)) {
        abort(
            "regions_file selector does not exist relative to the partition ",
            "manifest: ", resolved
        )
    }
    resolved
}

parse_regions_file <- function(value, partition_id, manifest_path) {
    path <- resolve_selector_file(value, manifest_path)
    validate_nonempty_file(
        paste0("regions_file for partition ", partition_id), path
    )
    connection <- open_text_connection(path)
    on.exit(close(connection), add = TRUE)
    lines <- readLines(connection, warn = FALSE)
    lines <- sub("\r$", "", lines)
    lines <- lines[
        !grepl("^[[:space:]]*$", lines) & !startsWith(lines, "#")
    ]
    if (length(lines) == 0L) {
        abort("regions_file selector contains no regions: ", path)
    }
    fields <- strsplit(lines, "\t", fixed = TRUE)
    extension <- tolower(sub("\\.gz$", "", path))
    is_bed <- grepl("\\.bed$", extension)
    is_vcf <- grepl("\\.vcf$", extension)
    result <- vector("list", length(fields))
    generic_mode <- NA_integer_

    for (index in seq_along(fields)) {
        row <- fields[[index]]
        if (is_bed) {
            if (length(row) < 3L || !nzchar(row[[1L]])) {
                abort("Malformed BED selector row ", index, ": ", path)
            }
            start_zero <- parse_coordinate(
                "BED start", row[[2L]], allow_zero = TRUE
            )
            end <- parse_coordinate("BED end", row[[3L]])
            start <- start_zero + 1L
        } else if (is_vcf) {
            if (length(row) < 2L || !nzchar(row[[1L]])) {
                abort("Malformed VCF selector row ", index, ": ", path)
            }
            start <- parse_coordinate("VCF position", row[[2L]])
            end <- start
        } else {
            if (length(row) < 2L || !nzchar(row[[1L]])) {
                abort(
                    "Generic regions_file rows must have at least two columns; ",
                    "row ", index, ": ", path
                )
            }
            row_mode <- if (length(row) == 2L) 2L else 3L
            if (!is.na(generic_mode) && row_mode != generic_mode) {
                abort(
                    "Generic regions_file mixes position and interval rows at ",
                    "row ", index, ": ", path
                )
            }
            generic_mode <- row_mode
            start <- parse_coordinate("Region start", row[[2L]])
            end <- if (row_mode == 3L) {
                parse_coordinate("Region end", row[[3L]])
            } else {
                start
            }
        }
        if (end < start) {
            abort(
                "Selector end is before start on row ", index, ": ", path
            )
        }
        result[[index]] <- make_interval_table(
            row[[1L]], start, end, partition_id
        )
    }
    do.call(rbind, result)
}

merge_intervals <- function(intervals) {
    if (nrow(intervals) == 0L) {
        return(intervals)
    }
    ordered <- intervals[order(
        intervals$chromosome, intervals$start, intervals$end,
        method = "radix"
    ), , drop = FALSE]
    output <- vector("list", nrow(ordered))
    output_count <- 0L
    for (index in seq_len(nrow(ordered))) {
        current <- ordered[index, , drop = FALSE]
        if (output_count == 0L) {
            output_count <- 1L
            output[[output_count]] <- current
            next
        }
        previous <- output[[output_count]]
        adjacent <- previous$end < (.Machine$integer.max - 1L) &&
            current$start == previous$end + 1L
        if (current$chromosome == previous$chromosome &&
            (current$start <= previous$end || adjacent)) {
            previous$end <- max(previous$end, current$end)
            output[[output_count]] <- previous
        } else {
            output_count <- output_count + 1L
            output[[output_count]] <- current
        }
    }
    do.call(rbind, output[seq_len(output_count)])
}

validate_partition_nonoverlap <- function(partitions, manifest_path) {
    interval_sets <- vector("list", nrow(partitions))
    for (index in seq_len(nrow(partitions))) {
        row <- partitions[index, , drop = FALSE]
        intervals <- if (row$selector_type == "region") {
            parse_region_selector(row$selector_value, row$partition_id)
        } else {
            parse_regions_file(
                row$selector_value, row$partition_id, manifest_path
            )
        }
        interval_sets[[index]] <- merge_intervals(intervals)
    }
    combined <- do.call(rbind, interval_sets)
    ranges <- GenomicRanges::GRanges(
        seqnames = combined$chromosome,
        ranges = IRanges::IRanges(start = combined$start, end = combined$end)
    )
    S4Vectors::mcols(ranges)$partition_id <- combined$partition_id
    hits <- GenomicRanges::findOverlaps(ranges, ranges, ignore.strand = TRUE)
    query <- S4Vectors::queryHits(hits)
    subject <- S4Vectors::subjectHits(hits)
    cross <- query < subject &
        combined$partition_id[query] != combined$partition_id[subject]
    if (any(cross)) {
        hit <- which(cross)[[1L]]
        left <- query[[hit]]
        right <- subject[[hit]]
        abort(
            "Partition selectors overlap: ", combined$partition_id[[left]],
            " (", combined$chromosome[[left]], ":", combined$start[[left]], "-",
            combined$end[[left]], ") and ",
            combined$partition_id[[right]], " (",
            combined$chromosome[[right]], ":", combined$start[[right]], "-",
            combined$end[[right]], ")."
        )
    }
    invisible(TRUE)
}
