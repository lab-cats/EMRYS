#!/usr/bin/env Rscript

# Step 08: validate the complete declared Step 07 VCF set, expand alternate
# alleles, apply the provisional legacy orientation policy, annotate candidates,
# and write deterministic cohort-level TSVs. Publication and locking belong to
# src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.sh; this program writes only its three
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


write_tsv <- function(table, path) {
    utils::write.table(
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

path_is_symlink <- function(path) {
    target <- Sys.readlink(path)
    length(target) == 1L && !is.na(target) && nzchar(target)
}

append_site_fragment <- function(output_path, fragment_path) {
    input <- file(fragment_path, open = "rb")
    on.exit(close(input), add = TRUE)
    output <- file(output_path, open = "ab")
    on.exit(close(output), add = TRUE)
    row_count <- 0
    repeat {
        bytes <- readBin(input, what = "raw", n = 1024L * 1024L)
        if (length(bytes) == 0L) {
            break
        }
        row_count <- row_count + sum(bytes == as.raw(0x0a))
        writeBin(bytes, output)
    }
    row_count
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
    threads <- parse_positive_integer("threads", arguments[["threads"]])
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
    owned_paths <- output_paths
    on.exit({
        if (!successful) {
            present <- file.exists(owned_paths) | vapply(
                owned_paths, path_is_symlink, logical(1)
            )
            unlink(owned_paths[present], force = TRUE)
        }
    }, add = TRUE)

    sample_ids <- read_sample_manifest(sample_manifest)
    partitions <- read_partition_manifest(partition_manifest)
    validate_partition_nonoverlap(partitions, partition_manifest)
    annotation_model <- read_annotation_model(annotation_gtf)

    jobs <- list()
    receipt_checks <- vector("list", nrow(partitions))
    job_count <- 0L
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
        receipt_checks[[partition_index]] <- list(
            path = receipt_path,
            sha256 = receipt_hash_before
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
            job_count <- job_count + 1L
            jobs[[job_count]] <- list(
                partition_id = partition$partition_id,
                selector_type = partition$selector_type,
                selector_value = partition$selector_value,
                orientation = orientation,
                receipt_path = receipt_path,
                receipt_sha256 = receipt_hash_before,
                vcf_path = vcf_path,
                fragment_path = sprintf(
                    "%s.fragment-%06d.tsv", output_paths[[1L]], job_count
                ),
                declared_count =
                    receipt_data$declared_counts[[orientation_index]]
            )
        }
    }

    fragment_paths <- vapply(
        jobs, function(job) job$fragment_path, character(1)
    )
    for (fragment_path in fragment_paths) {
        if (file.exists(fragment_path) || path_is_symlink(fragment_path)) {
            abort(
                "Refusing to overwrite an existing Step 08 site fragment: ",
                fragment_path
            )
        }
    }
    owned_paths <- c(output_paths, fragment_paths)

    job_results <- process_vcf_jobs(
        jobs, threads, sample_ids, annotation_model
    )
    for (receipt_check in receipt_checks) {
        receipt_hash_after <- sha256_file(receipt_check$path)
        if (!identical(receipt_check$sha256, receipt_hash_after)) {
            abort(
                "Step 07 receipt changed during semantic processing: ",
                receipt_check$path
            )
        }
    }

    candidate_ids <- unlist(
        lapply(job_results, function(job_result) job_result$candidate_ids),
        use.names = FALSE
    )
    duplicate_index <- anyDuplicated(candidate_ids)
    if (duplicate_index != 0L) {
        abort(
            "Duplicate partition-independent candidate_id across declared ",
            "inputs: ", candidate_ids[[duplicate_index]]
        )
    }
    for (job_index in seq_along(job_results)) {
        job_results[[job_index]]$candidate_ids <- NULL
    }
    rm(candidate_ids)

    input_rows <- vector("list", length(jobs))
    for (job_index in seq_along(jobs)) {
        job <- jobs[[job_index]]
        job_result <- job_results[[job_index]]
        result <- job_result$result
        input_rows[[job_index]] <- data.frame(
            cohort_id = cohort_id,
            partition_id = job$partition_id,
            selector_type = job$selector_type,
            selector_value = job$selector_value,
            orientation = job$orientation,
            step07_receipt_path = job$receipt_path,
            step07_receipt_sha256 = job$receipt_sha256,
            vcf_path = job$vcf_path,
            vcf_sha256 = job_result$vcf_sha256,
            sample_manifest_sha256 = sample_hash,
            partition_manifest_sha256 = partition_hash,
            annotation_gtf = annotation_gtf,
            annotation_gtf_sha256 = annotation_hash,
            sample_count = length(sample_ids),
            declared_vcf_record_count = job$declared_count,
            observed_vcf_record_count = result$observed_records,
            observed_alt_allele_count = result$observed_alt_alleles,
            supported_snv_count = result$supported_snvs,
            skipped_symbolic_count = result$skipped_symbolic,
            skipped_non_snv_count = result$skipped_non_snv,
            published_candidate_count = result$published_candidate_count,
            orientation_policy = ORIENTATION_POLICY,
            stringsAsFactors = FALSE,
            check.names = FALSE
        )
    }

    input_receipt <- do.call(rbind, input_rows)
    input_receipt <- input_receipt[, INPUT_COLUMNS, drop = FALSE]

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
        totals[["published_candidate_count"]]) {
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
    sites_header <- empty_sites(sample_ids)
    sites_header <- sites_header[, expected_site_columns, drop = FALSE]

    # R owns deterministic candidate construction and TSV serialization. The
    # shell owner performs post-serialization admission on these staged outputs
    # before publication; it does not reconstruct within-VCF candidate order.
    write_tsv(sites_header, output_paths[[1L]])
    appended_candidate_count <- 0
    for (job_result in job_results) {
        result <- job_result$result
        fragment_path <- job_result$fragment_path
        if (result$published_candidate_count == 0L) {
            if (file.exists(fragment_path) || path_is_symlink(fragment_path)) {
                abort(
                    "Step 08 worker wrote an unexpected empty site fragment: ",
                    fragment_path
                )
            }
            next
        }
        if (!file.exists(fragment_path) || path_is_symlink(fragment_path)) {
            abort("Step 08 site fragment is unavailable: ", fragment_path)
        }
        appended_rows <- append_site_fragment(
            output_paths[[1L]], fragment_path
        )
        if (appended_rows != result$published_candidate_count) {
            abort(
                "Step 08 site fragment row count does not reconcile: ",
                fragment_path
            )
        }
        appended_candidate_count <- appended_candidate_count + appended_rows
        if (unlink(fragment_path, force = TRUE) != 0L ||
            file.exists(fragment_path) || path_is_symlink(fragment_path)) {
            abort("Could not remove Step 08 site fragment: ", fragment_path)
        }
    }
    if (appended_candidate_count != totals[["published_candidate_count"]]) {
        abort(
            "Step 08 supported, published, and combined candidate counts do ",
            "not reconcile."
        )
    }
    write_tsv(summary, output_paths[[3L]])
    write_tsv(input_receipt, output_paths[[2L]])
    successful <- TRUE

    message(
        "Step 08 preprocessing complete: ", nrow(input_receipt),
        " VCFs, ", totals[["published_candidate_count"]],
        " supported SNV candidates."
    )
}

load_step08_owner_modules <- function() {
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
    owner_directory <- dirname(entry_path)
    shared_path <- file.path(owner_directory, "../../libraries/input_contract.R")
    owner_path <- file.path(owner_directory, "_step_08_input_contract.R")
    owner_info <- file.info(owner_path)
    if (!file.exists(owner_path) || isTRUE(owner_info$isdir) ||
        is.na(owner_info$size) || owner_info$size <= 0L) {
        stop("Step 08 input-contract owner is unavailable: ", owner_path,
             call. = FALSE)
    }
    sys.source(shared_path, envir = globalenv(), keep.source = FALSE)
    sys.source(owner_path, envir = globalenv(), keep.source = FALSE)
    module_filenames <- c(
        "_step_08_annotation.R",
        "_step_08_receipt_contract.R",
        "_step_08_vcf_counts.R",
        "_step_08_vcf_processing.R"
    )
    for (module_filename in module_filenames) {
        module_path <- file.path(owner_directory, module_filename)
        module_info <- file.info(module_path)
        if (!file.exists(module_path) || isTRUE(module_info$isdir) ||
            is.na(module_info$size) || module_info$size <= 0L) {
            stop(
                "Step 08 owner module is unavailable: ", module_path,
                call. = FALSE
            )
        }
        sys.source(module_path, envir = globalenv(), keep.source = FALSE)
    }
    invisible(owner_path)
}

tryCatch(
    {
        load_step08_owner_modules()
        main()
    },
    error = function(error) {
        message("ERROR: ", conditionMessage(error))
        quit(status = 1L)
    }
)
