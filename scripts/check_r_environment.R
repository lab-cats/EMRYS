#!/usr/bin/env Rscript

# Validate the guarded NORAD R runtime, lockfile, packages, and PDF device.

arguments <- commandArgs(trailingOnly = TRUE)
if (length(arguments) != 0L) {
    stop("check_r_environment.R does not accept positional arguments.")
}

if (!identical(Sys.getenv("NORAD_USE_RENV", unset = "0"), "1")) {
    stop("Set NORAD_USE_RENV=1 before checking the NORAD R environment.")
}
if (!identical(Sys.getenv("NORAD_LOCAL_PILOT_R", unset = "0"), "1")) {
    stop(
        "R checks require non-bootstrapping local-pilot library selection."
    )
}
selected_library_request <- Sys.getenv("NORAD_RENV_LIBRARY", unset = "")
expected_renv_version <- Sys.getenv("NORAD_RENV_VERSION", unset = "")
if (!nzchar(selected_library_request) || !nzchar(expected_renv_version)) {
    stop("NORAD_RENV_LIBRARY and NORAD_RENV_VERSION are required.")
}

bioconductor_mirror <- "https://bioconductor.posit.co"
bioconductor_binary_repository <- "https://bioc-release.r-universe.dev"
cran_repository <- "https://cloud.r-project.org"
if (!nzchar(Sys.getenv("BIOCONDUCTOR_CONFIG_FILE", unset = ""))) {
    Sys.setenv(
        BIOCONDUCTOR_CONFIG_FILE = paste0(
            bioconductor_mirror,
            "/config.yaml"
        )
    )
}
options(
    BioC_mirror = bioconductor_mirror,
    repos = c(
        BioC = bioconductor_binary_repository,
        CRAN = cran_repository
    )
)

project_request <- Sys.getenv("RENV_PROJECT", unset = "")
if (!nzchar(project_request)) {
    stop("RENV_PROJECT must identify the NORAD repository root.")
}

required_packages <- c(
    "renv",
    "BiocManager",
    "VariantAnnotation",
    "GenomicRanges",
    "IRanges",
    "S4Vectors",
    "SummarizedExperiment",
    "GenomeInfoDb",
    "BiocGenerics",
    "rtracklayer"
)

missing_packages <- required_packages[
    !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0L) {
    stop(
        "Missing required NORAD R package(s): ",
        paste(missing_packages, collapse = ", ")
    )
}

if (!identical(as.character(getRversion()), "4.6.1")) {
    stop("NORAD local R must be version 4.6.1; found ", R.version.string)
}

project_root <- normalizePath(
    project_request,
    winslash = "/",
    mustWork = TRUE
)
active_project <- normalizePath(
    renv::project(),
    winslash = "/",
    mustWork = TRUE
)
if (!identical(active_project, project_root)) {
    stop(
        "The active renv project does not match RENV_PROJECT: active=",
        active_project,
        "; requested=",
        project_root
    )
}

selected_library <- normalizePath(
    selected_library_request,
    winslash = "/",
    mustWork = TRUE
)
active_library <- normalizePath(.libPaths()[[1L]], winslash = "/", mustWork = TRUE)
if (!identical(active_library, selected_library)) {
    stop(
        "The active R library does not match NORAD_RENV_LIBRARY: active=",
        active_library,
        "; requested=",
        selected_library
    )
}
installed_renv_version <- as.character(utils::packageVersion("renv"))
if (!identical(installed_renv_version, expected_renv_version)) {
    stop(
        "The selected R library has renv ", installed_renv_version,
        "; expected ", expected_renv_version
    )
}

bioconductor_version <- as.character(BiocManager::version())
if (!identical(bioconductor_version, "3.23")) {
    stop(
        "NORAD requires Bioconductor 3.23; found ",
        bioconductor_version
    )
}

renv_status <- renv::status(project = project_root)
if (!isTRUE(renv_status$synchronized)) {
    stop("renv::status() reports that the project is not synchronized.")
}

pdf_path <- tempfile("norad-r-device-", fileext = ".pdf")
grDevices::pdf(pdf_path, width = 3, height = 3, onefile = TRUE)
graphics::plot.new()
graphics::title(main = "NORAD R runtime")
grDevices::dev.off()

pdf_size <- file.info(pdf_path)$size
if (is.na(pdf_size) || pdf_size <= 5L) {
    stop("Headless R PDF device produced an empty output.")
}

pdf_bytes <- readBin(pdf_path, what = "raw", n = pdf_size)
on.exit(unlink(pdf_path), add = TRUE)
pdf_signature <- pdf_bytes[seq_len(5L)]
if (!identical(pdf_signature, charToRaw("%PDF-"))) {
    stop("Headless R PDF device produced an invalid PDF signature.")
}
pdf_eof <- charToRaw("%%EOF")
eof_width <- length(pdf_eof)
eof_found <- any(vapply(
    seq_len(length(pdf_bytes) - eof_width + 1L),
    function(offset) {
        identical(
            pdf_bytes[offset:(offset + eof_width - 1L)],
            pdf_eof
        )
    },
    logical(1)
))
if (!eof_found) {
    stop("Headless R PDF device produced a PDF without an EOF marker.")
}

message("NORAD R environment check passed")
message("  R: ", R.version.string)
message("  Bioconductor: ", bioconductor_version)
message("  project library: ", .libPaths()[[1L]])
message("  package versions:")
for (package_name in required_packages) {
    message(
        "    ",
        package_name,
        ": ",
        as.character(utils::packageVersion(package_name))
    )
}
