# Owner-private Step 08 candidate construction.
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
            {
                scan_header <- VariantAnnotation::scanVcfHeader(vcf_path)
                required_fields_declared <-
                    all(c("AD", "ADF", "ADR") %in%
                        rownames(VariantAnnotation::info(scan_header))) &&
                    all(c("DP", "AD", "ADF", "ADR", "SP") %in%
                        rownames(VariantAnnotation::geno(scan_header)))
                scan_param <- if (required_fields_declared) {
                    VariantAnnotation::ScanVcfParam(
                        info = "AD", geno = c("DP", "AD")
                    )
                } else {
                    VariantAnnotation::ScanVcfParam()
                }
                VariantAnnotation::readVcf(
                    file = vcf_path,
                    genome = GenomeInfoDb::seqinfo(scan_header),
                    param = scan_param,
                    row.names = FALSE
                )
            },
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

process_vcf_job <- function(job, sample_ids, annotation_model) {
    vcf_hash_before <- sha256_file(job$vcf_path)
    result <- process_vcf(
        job$vcf_path,
        job$partition_id,
        job$orientation,
        job$declared_count,
        sample_ids,
        annotation_model
    )
    vcf_hash_after <- sha256_file(job$vcf_path)
    if (!identical(vcf_hash_before, vcf_hash_after)) {
        abort(
            "Step 07 VCF changed during semantic processing: ",
            job$vcf_path
        )
    }
    list(result = result, vcf_sha256 = vcf_hash_before)
}

process_vcf_jobs <- function(jobs, threads, sample_ids, annotation_model) {
    worker_count <- min(threads, length(jobs))
    if (.Platform$OS.type == "windows") {
        worker_count <- 1L
    }
    message(
        "Step 08 VCF workers: ", worker_count,
        " for ", length(jobs), " ordered input job(s)."
    )

    process_timed <- function(job) {
        started <- proc.time()[["elapsed"]]
        value <- process_vcf_job(job, sample_ids, annotation_model)
        list(
            value = value,
            worker_pid = as.integer(Sys.getpid()),
            elapsed_seconds = as.numeric(proc.time()[["elapsed"]] - started)
        )
    }
    report_worker_load <- function(outcomes) {
        worker_pid <- vapply(
            outcomes, function(outcome) outcome$worker_pid, integer(1)
        )
        for (pid in sort(unique(worker_pid), method = "radix")) {
            assigned <- which(worker_pid == pid)
            elapsed <- sum(vapply(
                outcomes[assigned],
                function(outcome) outcome$elapsed_seconds,
                numeric(1)
            ))
            message(
                "Step 08 worker load: pid=", pid,
                " jobs=", length(assigned),
                " cumulative_job_seconds=", sprintf("%.3f", elapsed)
            )
        }
    }

    if (worker_count == 1L) {
        outcomes <- lapply(jobs, process_timed)
        report_worker_load(outcomes)
        return(lapply(outcomes, function(outcome) outcome$value))
    }

    process_safely <- function(job) {
        tryCatch(
            list(
                ok = TRUE,
                value = process_timed(job)
            ),
            error = function(error) {
                list(ok = FALSE, message = conditionMessage(error))
            }
        )
    }
    results <- parallel::mclapply(
        jobs,
        process_safely,
        mc.cores = worker_count,
        mc.preschedule = TRUE,
        mc.set.seed = FALSE
    )
    valid_outcome <- vapply(
        results,
        function(outcome) {
            is.list(outcome) && length(outcome$ok) == 1L &&
                !is.na(outcome$ok) && is.logical(outcome$ok)
        },
        logical(1)
    )
    if (any(!valid_outcome)) {
        abort(
            "Step 08 parallel worker did not return a valid result for input ",
            which(!valid_outcome)[[1L]], "."
        )
    }
    failed <- which(!vapply(
        results,
        function(outcome) outcome$ok,
        logical(1)
    ))
    if (length(failed) > 0L) {
        index <- failed[[1L]]
        job <- jobs[[index]]
        abort(
            "Step 08 input processing failed for partition ",
            job$partition_id, " ", job$orientation, ": ",
            results[[index]]$message
        )
    }
    outcomes <- lapply(results, function(outcome) outcome$value)
    report_worker_load(outcomes)
    lapply(outcomes, function(outcome) outcome$value)
}
