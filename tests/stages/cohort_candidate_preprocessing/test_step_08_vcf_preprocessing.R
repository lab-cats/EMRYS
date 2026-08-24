#!/usr/bin/env Rscript

# Real-R fixtures for the Step 08 semantic VCF/GTF implementation. The shell
# runner skips only when Rscript itself is unavailable and treats missing
# packages as a validation failure.

options(stringsAsFactors = FALSE, scipen = 999, digits = 15)

abort_test <- function(...) {
    stop(paste0(...), call. = FALSE)
}

assert_true <- function(value, message) {
    if (length(value) != 1L || is.na(value) || !isTRUE(value)) {
        abort_test("ASSERTION FAILED: ", message)
    }
}

assert_identical <- function(observed, expected, message) {
    if (!identical(observed, expected)) {
        abort_test(
            "ASSERTION FAILED: ", message, "\nObserved: ",
            paste(observed, collapse = ","), "\nExpected: ",
            paste(expected, collapse = ",")
        )
    }
}

write_lines <- function(lines, path) {
    dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
    writeLines(lines, path, useBytes = TRUE)
}

write_tsv <- function(table, path) {
    dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
    write.table(
        table,
        path,
        sep = "\t",
        quote = FALSE,
        row.names = FALSE,
        col.names = TRUE,
        na = "",
        eol = "\n"
    )
}

sha256_file <- function(path) {
    normalized <- normalizePath(path, winslash = "/", mustWork = TRUE)
    if (nzchar(Sys.which("sha256sum"))) {
        output <- system2(
            Sys.which("sha256sum"),
            args = shQuote(normalized),
            stdout = TRUE,
            stderr = TRUE
        )
    } else if (nzchar(Sys.which("shasum"))) {
        output <- system2(
            Sys.which("shasum"),
            args = c("-a", "256", shQuote(normalized)),
            stdout = TRUE,
            stderr = TRUE
        )
    } else {
        abort_test("Fixtures require sha256sum or shasum.")
    }
    match <- regexpr("[[:xdigit:]]{64}", paste(output, collapse = "\n"))
    assert_true(match[[1L]] >= 0L, "SHA-256 output must contain a digest")
    tolower(regmatches(paste(output, collapse = "\n"), match))
}

vcf_header <- function(
    samples, omit_ad_definition = FALSE, contig = "1"
) {
    header <- c(
        "##fileformat=VCFv4.2",
        "##FILTER=<ID=PASS,Description=\"All filters passed\">",
        "##FILTER=<ID=q10,Description=\"Synthetic fixture filter\">",
        "##INFO=<ID=AD,Number=R,Type=Integer,Description=\"Allelic depths\">",
        "##INFO=<ID=ADF,Number=R,Type=Integer,Description=\"Forward depths\">",
        "##INFO=<ID=ADR,Number=R,Type=Integer,Description=\"Reverse depths\">",
        "##FORMAT=<ID=DP,Number=1,Type=Integer,Description=\"Read depth\">",
        "##FORMAT=<ID=ADF,Number=R,Type=Integer,Description=\"Forward depths\">",
        "##FORMAT=<ID=ADR,Number=R,Type=Integer,Description=\"Reverse depths\">",
        "##FORMAT=<ID=SP,Number=1,Type=Integer,Description=\"Strand bias\">",
        paste0("##contig=<ID=", contig, ",length=1000>")
    )
    if (!omit_ad_definition) {
        header <- append(
            header,
            "##FORMAT=<ID=AD,Number=R,Type=Integer,Description=\"Allelic depths\">",
            after = 6L
        )
    }
    c(
        header,
        paste(
            c(
                "#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER",
                "INFO", "FORMAT", samples
            ),
            collapse = "\t"
        )
    )
}

default_fwd_rows <- function() {
    c(
        paste(
            c(
                "1", "15", ".", "A", "G", "60", "PASS", "AD=25,5",
                "DP:AD", "12:10,2", "18:15,3"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "25", ".", "C", "T,G", "50", "q10", "AD=34,5,11",
                "DP:AD", "20:13,2,5", "30:21,3,6"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "40", ".", "G", "A", "45", "PASS", "AD=20,4",
                "DP:AD", "10:8,2", "14:12,2"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "70", ".", "T", "C", "42", "PASS", "AD=21,3",
                "DP:AD", "11:9,2", "13:12,1"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "100", ".", "A", "<DEL>,AT", "30", "PASS",
                "AD=30,2,3", "DP:AD", "15:12,1,2", "20:18,1,1"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "150", ".", "A", "G", "35", "PASS", "AD=8,2",
                "DP:AD", "10:8,2", ".:.,."
            ),
            collapse = "\t"
        )
    )
}

default_rev_rows <- function() {
    c(
        paste(
            c(
                "1", "205", ".", "A", "G", "61", "PASS", "AD=27,5",
                "DP:AD", "14:12,2", "18:15,3"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "225", ".", "C", "T", "55", "PASS", "AD=30,6",
                "DP:AD", "16:13,3", "20:17,3"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "240", ".", "G", "A", "48", "PASS", "AD=22,4",
                "DP:AD", "12:10,2", "14:12,2"
            ),
            collapse = "\t"
        ),
        paste(
            c(
                "1", "270", ".", "T", "C", "44", "PASS", "AD=26,4",
                "DP:AD", "15:13,2", "15:13,2"
            ),
            collapse = "\t"
        )
    )
}

annotation_lines <- function() {
    attributes_plus <- 'gene_id "gene_plus"; transcript_id "tx_plus";'
    attributes_minus <- 'gene_id "gene_minus"; transcript_id "tx_minus";'
    attributes_conflict <-
        'gene_id "gene_conflict"; transcript_id "tx_conflict";'
    rows <- list(
        c("1", "fixture", "exon", "10", "30", ".", "+", ".", attributes_plus),
        c("1", "fixture", "exon", "50", "80", ".", "+", ".", attributes_plus),
        c("1", "fixture", "CDS", "20", "30", ".", "+", "0", attributes_plus),
        c("1", "fixture", "CDS", "50", "60", ".", "+", "0", attributes_plus),
        c(
            "1", "fixture", "five_prime_UTR", "10", "19", ".", "+", ".",
            attributes_plus
        ),
        c(
            "1", "fixture", "three_prime_UTR", "61", "80", ".", "+", ".",
            attributes_plus
        ),
        c(
            "1", "fixture", "exon", "200", "230", ".", "-", ".",
            attributes_minus
        ),
        c(
            "1", "fixture", "exon", "250", "280", ".", "-", ".",
            attributes_minus
        ),
        c(
            "1", "fixture", "CDS", "220", "230", ".", "-", "0",
            attributes_minus
        ),
        c(
            "1", "fixture", "CDS", "250", "260", ".", "-", "0",
            attributes_minus
        ),
        c(
            "1", "fixture", "five_prime_UTR", "261", "280", ".", "-", ".",
            attributes_minus
        ),
        c(
            "1", "fixture", "three_prime_UTR", "200", "219", ".", "-", ".",
            attributes_minus
        ),
        c(
            "2", "fixture", "exon", "10", "30", ".", "+", ".",
            attributes_conflict
        ),
        c(
            "2", "fixture", "exon", "50", "80", ".", "-", ".",
            attributes_conflict
        )
    )
    vapply(rows, paste, character(1), collapse = "\t")
}

count_vcf_records <- function(path) {
    lines <- readLines(path, warn = FALSE)
    sum(nzchar(lines) & !startsWith(lines, "#"))
}

build_case <- function(root, mode = "positive") {
    cohort <- "fixture_cohort"
    sample_manifest <- file.path(root, "samples.tsv")
    partition_manifest <- file.path(root, "partitions.tsv")
    annotation_gtf <- file.path(root, "annotation.gtf")
    step07_root <- file.path(root, "step07")

    samples <- data.frame(
        sample_id = c("sample_A", "sample_B"),
        r1_fastq = c("/reads/sample_A_R1.fastq.gz", "/reads/sample_B_R1.fastq.gz"),
        r2_fastq = c("/reads/sample_A_R2.fastq.gz", "/reads/sample_B_R2.fastq.gz"),
        strandedness = c("unknown", "unknown"),
        condition = c("EV", "PUM1"),
        replicate = c("1", "2"),
        stringsAsFactors = FALSE
    )
    if (mode == "missing_replicate") {
        samples$replicate <- NULL
    }
    write_tsv(samples, sample_manifest)
    selector_relative <- file.path("selectors", "p2.regions.tsv")
    selector_path <- file.path(dirname(partition_manifest), selector_relative)
    selector_chromosome <- if (mode == "disjoint_annotation") "3" else "1"
    if (mode == "mixed_regions_file") {
        write_lines(c("1\t200", "1\t250\t400"), selector_path)
    } else {
        # Generic Step 07 interval mode accepts three or more columns.
        write_lines(
            paste(
                selector_chromosome, "200", "400", "fixture_interval",
                sep = "\t"
            ),
            selector_path
        )
    }
    partitions <- data.frame(
        partition_id = c("p1", "p2"),
        selector_type = c("region", "regions_file"),
        selector_value = if (mode == "overlap") {
            c("1:1-250", selector_relative)
        } else {
            c("1:1-199", selector_relative)
        },
        stringsAsFactors = FALSE
    )
    write_tsv(partitions, partition_manifest)
    write_lines(annotation_lines(), annotation_gtf)
    sample_hash <- sha256_file(sample_manifest)
    partition_hash <- sha256_file(partition_manifest)
    annotation_hash <- sha256_file(annotation_gtf)

    p1_fwd <- default_fwd_rows()
    p2_rev <- default_rev_rows()
    if (mode == "disjoint_annotation") {
        p2_rev <- sub("^1", "3", p2_rev)
    }
    p1_samples <- c("sample_A", "sample_B")
    omit_ad_definition <- FALSE
    if (mode == "sample_order") {
        p1_samples <- rev(p1_samples)
    } else if (mode == "ad_gt_dp") {
        p1_fwd[[1L]] <- sub(
            "12:10,2", "1:0,2", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "one_sided_missing") {
        p1_fwd[[1L]] <- sub(
            "12:10,2", ".:10,2", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "partial_ad_missing") {
        p1_fwd[[1L]] <- sub(
            "12:10,2", "12:.,2", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "negative_count") {
        p1_fwd[[1L]] <- sub(
            "12:10,2", "12:10,-2", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "malformed_count") {
        p1_fwd[[1L]] <- sub(
            "12:10,2", "12:10,x", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "malformed_dp_count") {
        p1_fwd[[1L]] <- sub(
            "12:10,2", "x:10,2", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "malformed_info_count") {
        p1_fwd[[1L]] <- sub(
            "AD=25,5", "AD=25,x", p1_fwd[[1L]], fixed = TRUE
        )
    } else if (mode == "missing_format_definition") {
        omit_ad_definition <- TRUE
    } else if (mode == "duplicate_candidate") {
        p1_fwd <- c(p1_fwd, p1_fwd[[1L]])
    }

    for (partition_id in partitions$partition_id) {
        partition_dir <- file.path(step07_root, cohort, partition_id)
        dir.create(partition_dir, recursive = TRUE, showWarnings = FALSE)
        fwd_path <- file.path(
            partition_dir,
            paste0(cohort, ".", partition_id, ".FWD_like.mpileup.vcf")
        )
        rev_path <- file.path(
            partition_dir,
            paste0(cohort, ".", partition_id, ".REV_like.mpileup.vcf")
        )
        if (partition_id == "p1") {
            write_lines(
                c(
                    vcf_header(
                        p1_samples,
                        omit_ad_definition = omit_ad_definition
                    ),
                    p1_fwd
                ),
                fwd_path
            )
            write_lines(vcf_header(c("sample_A", "sample_B")), rev_path)
        } else {
            write_lines(
                vcf_header(
                    c("sample_A", "sample_B"),
                    contig = selector_chromosome
                ),
                fwd_path
            )
            write_lines(
                c(
                    vcf_header(
                        c("sample_A", "sample_B"),
                        contig = selector_chromosome
                    ),
                    p2_rev
                ),
                rev_path
            )
        }
        partition_row <- partitions[
            partitions$partition_id == partition_id, , drop = FALSE
        ]
        receipt_sample_hash <- sample_hash
        if (mode == "receipt_hash_mismatch" && partition_id == "p1") {
            receipt_sample_hash <- paste(rep("0", 64L), collapse = "")
        }
        receipt <- data.frame(
            cohort_id = rep(cohort, 2L),
            partition_id = rep(partition_id, 2L),
            selector_type = rep(partition_row$selector_type, 2L),
            selector_value = rep(partition_row$selector_value, 2L),
            orientation = c("FWD_like", "REV_like"),
            vcf_path = c(
                normalizePath(fwd_path, winslash = "/", mustWork = TRUE),
                normalizePath(rev_path, winslash = "/", mustWork = TRUE)
            ),
            sample_manifest_sha256 = rep(receipt_sample_hash, 2L),
            partition_manifest_sha256 = rep(partition_hash, 2L),
            sample_count = rep(2L, 2L),
            vcf_record_count = c(
                count_vcf_records(fwd_path),
                count_vcf_records(rev_path)
            ),
            stringsAsFactors = FALSE,
            check.names = FALSE
        )
        if (mode == "receipt_path_mismatch" && partition_id == "p1") {
            receipt$vcf_path[[1L]] <- receipt$vcf_path[[2L]]
        }
        if (mode == "declared_count_mismatch" && partition_id == "p1") {
            receipt$vcf_record_count[[1L]] <-
                receipt$vcf_record_count[[1L]] + 1L
        }
        write_tsv(
            receipt,
            file.path(
                partition_dir,
                paste0(cohort, ".", partition_id, ".step07_outputs.tsv")
            )
        )
    }
    list(
        cohort = cohort,
        sample_manifest = sample_manifest,
        partition_manifest = partition_manifest,
        annotation_gtf = annotation_gtf,
        step07_root = step07_root,
        sample_hash = sample_hash,
        partition_hash = partition_hash,
        annotation_hash = annotation_hash
    )
}

engine_arguments <- function(case, output_dir, threads = "1") {
    dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
    paths <- list(
        sites = file.path(output_dir, "sites.tsv"),
        inputs = file.path(output_dir, "inputs.tsv"),
        summary = file.path(output_dir, "summary.tsv")
    )
    list(
        args = c(
            "--cohort-id", case$cohort,
            "--sample-manifest", case$sample_manifest,
            "--partition-manifest", case$partition_manifest,
            "--step07-root", case$step07_root,
            "--annotation-gtf", case$annotation_gtf,
            "--sample-manifest-sha256", case$sample_hash,
            "--partition-manifest-sha256", case$partition_hash,
            "--annotation-gtf-sha256", case$annotation_hash,
            "--threads", threads,
            "--sites-output", paths$sites,
            "--inputs-output", paths$inputs,
            "--summary-output", paths$summary
        ),
        paths = paths
    )
}

run_engine <- function(
    engine, case, output_dir, expect_success, environment = character(),
    expected_error = NULL, threads = "1"
) {
    invocation <- engine_arguments(case, output_dir, threads)
    log <- file.path(output_dir, "engine.log")
    command <- c(
        "--no-environ", "--no-site-file", "--no-restore", "--no-save",
        shQuote(engine), shQuote(invocation$args)
    )
    status <- system2(
        test_rscript_bin,
        args = command,
        stdout = log,
        stderr = log,
        env = c(environment, "R_DEFAULT_PACKAGES=NULL")
    )
    if (is.null(status)) {
        status <- 0L
    }
    if (expect_success && status != 0L) {
        output <- paste(readLines(log, warn = FALSE), collapse = "\n")
        abort_test("Positive Step 08 fixture failed:\n", output)
    }
    if (!expect_success && status == 0L) {
        abort_test(
            "Negative Step 08 fixture unexpectedly succeeded: ",
            basename(output_dir)
        )
    }
    if (!expect_success) {
        if (!is.null(expected_error)) {
            assert_true(
                any(grepl(
                    expected_error,
                    readLines(log, warn = FALSE),
                    fixed = TRUE
                )),
                paste0(
                    basename(output_dir),
                    " did not fail for the expected reason: ",
                    expected_error
                )
            )
        }
        assert_true(
            !file.exists(invocation$paths$sites) &&
                !file.exists(invocation$paths$inputs) &&
                !file.exists(invocation$paths$summary),
            "failed engine run must remove all owned output paths"
        )
    }
    invocation$paths
}

hash_mutation_environment <- function(root, target) {
    shim_dir <- file.path(root, "hash-shim")
    dir.create(shim_dir, recursive = TRUE, showWarnings = FALSE)
    shim <- file.path(shim_dir, "sha256sum")
    counter <- file.path(root, "target-hash-count.txt")
    real_sha256sum <- Sys.which("sha256sum")
    if (nzchar(real_sha256sum)) {
        real_hash_bin <- real_sha256sum
        real_hash_mode <- "sha256sum"
    } else {
        real_hash_bin <- Sys.which("shasum")
        assert_true(
            nzchar(real_hash_bin),
            "hash mutation fixture requires sha256sum or shasum"
        )
        real_hash_mode <- "shasum"
    }
    write_lines(
        c(
            "#!/bin/sh",
            "set -eu",
            "path=\"$1\"",
            "if [ \"$path\" = \"$STEP08_HASH_TARGET\" ]; then",
            "    count=0",
            "    if [ -f \"$STEP08_HASH_COUNTER\" ]; then",
            "        count=$(sed -n '1p' \"$STEP08_HASH_COUNTER\")",
            "    fi",
            "    count=$((count + 1))",
            "    printf '%s\\n' \"$count\" > \"$STEP08_HASH_COUNTER\"",
            "    if [ \"$count\" -eq 2 ]; then",
            "        printf '\\n# synthetic hash mutation\\n' >> \"$path\"",
            "    fi",
            "fi",
            "if [ \"$STEP08_REAL_HASH_MODE\" = shasum ]; then",
            "    exec \"$STEP08_REAL_HASH_BIN\" -a 256 \"$@\"",
            "fi",
            "exec \"$STEP08_REAL_HASH_BIN\" \"$@\""
        ),
        shim
    )
    Sys.chmod(shim, mode = "0755")
    c(
        paste0("PATH=", shim_dir, ":", Sys.getenv("PATH")),
        paste0(
            "STEP08_HASH_TARGET=",
            normalizePath(target, winslash = "/", mustWork = TRUE)
        ),
        paste0("STEP08_HASH_COUNTER=", counter),
        paste0("STEP08_REAL_HASH_BIN=", real_hash_bin),
        paste0("STEP08_REAL_HASH_MODE=", real_hash_mode)
    )
}

read_result <- function(path) {
    read.delim(
        path,
        sep = "\t",
        header = TRUE,
        quote = "",
        comment.char = "",
        check.names = FALSE,
        stringsAsFactors = FALSE,
        na.strings = "NA"
    )
}

assert_positive_outputs <- function(paths) {
    sites <- read_result(paths$sites)
    inputs <- read_result(paths$inputs)
    summary <- read_result(paths$summary)
    expected_metadata <- c(
        "partition_id", "candidate_id", "orientation", "chromosome",
        "position", "alt_index", "genomic_ref", "genomic_alt", "rna_ref",
        "rna_alt", "annotation_strand", "gene_ids", "transcript_ids",
        "is_cds", "is_five_prime_utr", "is_three_prime_utr", "is_exon",
        "is_intron", "qual", "filter", "info_alt_depth",
        "orientation_policy"
    )
    expected_site_columns <- c(
        expected_metadata,
        "DP__sample_A", "DP__sample_B",
        "AD__sample_A", "AD__sample_B",
        "AF__sample_A", "AF__sample_B"
    )
    assert_identical(
        names(sites), expected_site_columns, "sites header must be exact"
    )
    assert_true(nrow(sites) == 10L, "ten supported SNV alleles are published")
    assert_identical(
        sites$candidate_id,
        c(
            "FWD_like|1|15|A>G",
            "FWD_like|1|25|C>T",
            "FWD_like|1|25|C>G",
            "FWD_like|1|40|G>A",
            "FWD_like|1|70|T>C",
            "FWD_like|1|150|A>G",
            "REV_like|1|205|A>G",
            "REV_like|1|225|C>T",
            "REV_like|1|240|G>A",
            "REV_like|1|270|T>C"
        ),
        "candidate order and partition-independent IDs must be deterministic"
    )
    fwd <- sites[sites$position == 15L, , drop = FALSE]
    assert_true(
        fwd$rna_ref == "T" && fwd$rna_alt == "C" &&
            fwd$annotation_strand == "+",
        "FWD_like must annotate plus transcripts and complement RNA alleles"
    )
    rev <- sites[sites$position == 205L, , drop = FALSE]
    assert_true(
        rev$rna_ref == "A" && rev$rna_alt == "G" &&
            rev$annotation_strand == "-",
        "REV_like must annotate minus transcripts and retain RNA alleles"
    )
    multi_one <- sites[
        sites$candidate_id == "FWD_like|1|25|C>T", , drop = FALSE
    ]
    multi_two <- sites[
        sites$candidate_id == "FWD_like|1|25|C>G", , drop = FALSE
    ]
    assert_true(
        multi_one$alt_index == 1L && multi_one$AD__sample_A == 2 &&
            multi_one$AD__sample_B == 3 &&
            multi_one$info_alt_depth == 5,
        "first multiallelic ALT must use its matching AD element"
    )
    assert_true(
        multi_two$alt_index == 2L && multi_two$AD__sample_A == 5 &&
            multi_two$AD__sample_B == 6 &&
            multi_two$info_alt_depth == 11,
        "second multiallelic ALT must use its matching AD element"
    )
    assert_true(
        isTRUE(all.equal(multi_one$AF__sample_A, 0.1)),
        "AF must be matching ALT AD divided by DP"
    )
    assert_true(
        multi_one$gene_ids == "gene_plus" &&
            multi_one$transcript_ids == "tx_plus" &&
            multi_one$is_cds && multi_one$is_exon,
        "compatible plus-strand CDS annotation must be retained"
    )
    intron <- sites[sites$position == 40L, , drop = FALSE]
    assert_true(
        intron$is_intron && !intron$is_exon && !intron$is_cds,
        "intron flag must be derived between transcript exons"
    )
    five <- sites[sites$position == 15L, , drop = FALSE]
    three <- sites[sites$position == 70L, , drop = FALSE]
    assert_true(
        five$is_five_prime_utr && three$is_three_prime_utr,
        "plus-strand UTR flags must be correct"
    )
    minus_three <- sites[sites$position == 205L, , drop = FALSE]
    minus_five <- sites[sites$position == 270L, , drop = FALSE]
    assert_true(
        minus_three$is_three_prime_utr && minus_five$is_five_prime_utr,
        "minus-strand UTR flags must be correct"
    )
    intergenic <- sites[sites$position == 150L, , drop = FALSE]
    assert_true(
        is.na(intergenic$gene_ids) &&
            is.na(intergenic$transcript_ids) &&
            !intergenic$is_cds && !intergenic$is_exon &&
            !intergenic$is_intron,
        "supported intergenic SNVs must be retained without annotation IDs"
    )
    assert_true(
        is.na(intergenic$DP__sample_B) &&
            is.na(intergenic$AD__sample_B) &&
            is.na(intergenic$AF__sample_B),
        "paired missing DP/AD must be retained as missing"
    )
    assert_true(
        all(sites$orientation_policy == "legacy_provisional_v1"),
        "every candidate must declare the provisional orientation policy"
    )

    expected_inputs <- c(
        "cohort_id", "partition_id", "selector_type", "selector_value",
        "orientation", "step07_receipt_path", "step07_receipt_sha256",
        "vcf_path", "vcf_sha256", "sample_manifest_sha256",
        "partition_manifest_sha256", "annotation_gtf",
        "annotation_gtf_sha256", "sample_count",
        "declared_vcf_record_count", "observed_vcf_record_count",
        "observed_alt_allele_count", "supported_snv_count",
        "skipped_symbolic_count", "skipped_non_snv_count",
        "published_candidate_count", "orientation_policy"
    )
    assert_identical(
        names(inputs), expected_inputs, "input receipt header must be exact"
    )
    assert_true(nrow(inputs) == 4L, "one input row is required per declared VCF")
    assert_identical(
        paste(inputs$partition_id, inputs$orientation, sep = "/"),
        c("p1/FWD_like", "p1/REV_like", "p2/FWD_like", "p2/REV_like"),
        "input receipt order must follow manifest then neutral orientation"
    )
    assert_identical(
        inputs$observed_vcf_record_count,
        c(6L, 0L, 0L, 4L),
        "header-only VCFs must be accepted and counted as zero records"
    )
    assert_identical(
        inputs$observed_alt_allele_count,
        c(8L, 0L, 0L, 4L),
        "alternate allele counts must include excluded alleles"
    )
    assert_identical(
        inputs$supported_snv_count,
        c(6L, 0L, 0L, 4L),
        "supported SNV counts must reconcile per input"
    )
    assert_identical(
        inputs$skipped_symbolic_count,
        c(1L, 0L, 0L, 0L),
        "symbolic alleles must be counted and excluded"
    )
    assert_identical(
        inputs$skipped_non_snv_count,
        c(1L, 0L, 0L, 0L),
        "non-SNV alleles must be counted and excluded"
    )
    assert_true(
        all(grepl("^[[:xdigit:]]{64}$", inputs$vcf_sha256)) &&
            all(grepl(
                "^[[:xdigit:]]{64}$", inputs$step07_receipt_sha256
            )),
        "input and receipt SHA-256 values must be recorded"
    )

    expected_summary <- c(
        "cohort_id", "partition_count", "step07_receipt_count",
        "input_vcf_count", "sample_count", "observed_vcf_record_count",
        "observed_alt_allele_count", "supported_snv_count",
        "skipped_symbolic_count", "skipped_non_snv_count",
        "published_candidate_count", "sample_manifest_sha256",
        "partition_manifest_sha256", "annotation_gtf",
        "annotation_gtf_sha256", "orientation_policy"
    )
    assert_identical(
        names(summary), expected_summary, "summary header must be exact"
    )
    assert_true(nrow(summary) == 1L, "summary must contain one row")
    assert_true(
        summary$partition_count == 2L &&
            summary$step07_receipt_count == 2L &&
            summary$input_vcf_count == 4L &&
            summary$sample_count == 2L &&
            summary$observed_vcf_record_count == 10L &&
            summary$observed_alt_allele_count == 12L &&
            summary$supported_snv_count == 10L &&
            summary$skipped_symbolic_count == 1L &&
            summary$skipped_non_snv_count == 1L &&
            summary$published_candidate_count == 10L,
        "summary counts must reconcile across every receipt"
    )
}

arguments <- commandArgs(trailingOnly = TRUE)
repo_root <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)
test_rscript_bin <- if (length(arguments) >= 1L) {
    arguments[[1L]]
} else {
    file.path(R.home("bin"), "Rscript")
}
engine <- if (length(arguments) >= 2L) {
    arguments[[2L]]
} else {
    file.path(
        repo_root,
        "src",
        "emrys",
        "stages",
        "cohort_candidate_preprocessing",
        "step_08_vcf_preprocessing.R"
    )
}
assert_true(
    file.exists(test_rscript_bin) &&
        file.access(test_rscript_bin, mode = 1L) == 0L,
    "Configured Rscript executable must exist and be executable"
)
assert_true(file.exists(engine), "Step 08 R engine must exist")

test_root <- tempfile("emrys-step08-real-r-")
dir.create(test_root, recursive = TRUE)
on.exit(unlink(test_root, recursive = TRUE, force = TRUE), add = TRUE)

positive_case <- build_case(file.path(test_root, "positive"))
first_paths <- run_engine(
    engine,
    positive_case,
    file.path(test_root, "positive-output-1"),
    expect_success = TRUE
)
assert_true(
    any(grepl(
        paste0(
            "Skipping transcript tx_conflict because it does not map to ",
            "exactly one chromosome, strand, and gene."
        ),
        readLines(
            file.path(test_root, "positive-output-1", "engine.log"),
            warn = FALSE
        ),
        fixed = TRUE
    )),
    "an internally inconsistent transcript must be warned about and skipped"
)
assert_positive_outputs(first_paths)
for (threads in c("2", "4")) {
    output_dir <- file.path(test_root, paste0("positive-output-", threads))
    compared_paths <- run_engine(
        engine,
        positive_case,
        output_dir,
        expect_success = TRUE,
        threads = threads
    )
    for (name in c("sites", "inputs", "summary")) {
        assert_true(
            identical(
                readBin(first_paths[[name]], "raw", n = file.info(
                    first_paths[[name]]
                )$size),
                readBin(compared_paths[[name]], "raw", n = file.info(
                    compared_paths[[name]]
                )$size)
            ),
            paste0(
                name, " output must be byte-deterministic at ",
                threads, " workers"
            )
        )
    }
    worker_log <- readLines(file.path(output_dir, "engine.log"), warn = FALSE)
    assert_true(
        any(grepl("Step 08 worker load:", worker_log, fixed = TRUE)),
        paste0(threads, "-worker execution must report worker load")
    )
}

disjoint_case <- build_case(
    file.path(test_root, "disjoint-annotation"),
    mode = "disjoint_annotation"
)
disjoint_output <- file.path(test_root, "disjoint-annotation-output")
disjoint_paths <- run_engine(
    engine,
    disjoint_case,
    disjoint_output,
    expect_success = TRUE
)
disjoint_log <- readLines(
    file.path(disjoint_output, "engine.log"), warn = FALSE
)
assert_true(
    !any(grepl(".merge_two_Seqinfo_objects", disjoint_log, fixed = TRUE)),
    "disjoint annotation seqlevels must be handled without a merge warning"
)
disjoint_sites <- read_result(disjoint_paths$sites)
disjoint_rows <- disjoint_sites$chromosome == "3"
assert_true(
    sum(disjoint_rows) == 4L &&
        all(is.na(disjoint_sites$gene_ids[disjoint_rows])) &&
        all(is.na(disjoint_sites$transcript_ids[disjoint_rows])) &&
        !any(disjoint_sites$is_cds[disjoint_rows]) &&
        !any(disjoint_sites$is_five_prime_utr[disjoint_rows]) &&
        !any(disjoint_sites$is_three_prime_utr[disjoint_rows]) &&
        !any(disjoint_sites$is_exon[disjoint_rows]) &&
        !any(disjoint_sites$is_intron[disjoint_rows]),
    "disjoint annotation seqlevels must retain candidates as unannotated"
)

negative_modes <- c(
    "missing_replicate",
    "overlap",
    "mixed_regions_file",
    "receipt_hash_mismatch",
    "sample_order",
    "ad_gt_dp",
    "one_sided_missing",
    "partial_ad_missing",
    "negative_count",
    "malformed_count",
    "malformed_dp_count",
    "malformed_info_count",
    "missing_format_definition",
    "duplicate_candidate",
    "receipt_path_mismatch",
    "declared_count_mismatch"
)
expected_negative_errors <- list(
    missing_replicate = paste0(
        "Sample manifest must have the exact paired local-CMH schema, ",
        "with optional notes as the final column."
    ),
    overlap = "Partition selectors overlap",
    malformed_count = "FORMAT/AD must contain",
    malformed_dp_count = "FORMAT/DP must contain",
    malformed_info_count = "INFO/AD must contain"
)
for (mode in negative_modes) {
    case <- build_case(file.path(test_root, paste0("negative-", mode)), mode)
    run_engine(
        engine,
        case,
        file.path(test_root, paste0("negative-output-", mode)),
        expect_success = FALSE,
        expected_error = expected_negative_errors[[mode]]
    )
}

vcf_mutation_case <- build_case(file.path(test_root, "negative-vcf-mutation"))
vcf_mutation_target <- file.path(
    vcf_mutation_case$step07_root,
    vcf_mutation_case$cohort,
    "p1",
    paste0(
        vcf_mutation_case$cohort, ".p1.FWD_like.mpileup.vcf"
    )
)
run_engine(
    engine,
    vcf_mutation_case,
    file.path(test_root, "negative-output-vcf-mutation"),
    expect_success = FALSE,
    environment = hash_mutation_environment(
        file.path(test_root, "vcf-mutation-shim"), vcf_mutation_target
    )
)

receipt_mutation_case <- build_case(
    file.path(test_root, "negative-receipt-mutation")
)
receipt_mutation_target <- file.path(
    receipt_mutation_case$step07_root,
    receipt_mutation_case$cohort,
    "p1",
    paste0(
        receipt_mutation_case$cohort, ".p1.step07_outputs.tsv"
    )
)
run_engine(
    engine,
    receipt_mutation_case,
    file.path(test_root, "negative-output-receipt-mutation"),
    expect_success = FALSE,
    environment = hash_mutation_environment(
        file.path(test_root, "receipt-mutation-shim"),
        receipt_mutation_target
    )
)

cat("PASS: Step 08 real-R semantic fixtures\n")
