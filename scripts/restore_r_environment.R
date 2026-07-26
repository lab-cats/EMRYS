#!/usr/bin/env Rscript

# Restore the explicitly activated NORAD R environment from renv.lock.

arguments <- commandArgs(trailingOnly = TRUE)
if (length(arguments) != 0L) {
    stop("restore_r_environment.R does not accept positional arguments.")
}

if (!identical(Sys.getenv("NORAD_USE_RENV", unset = "0"), "1")) {
    stop("Set NORAD_USE_RENV=1 before restoring the NORAD R environment.")
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

if (!requireNamespace("renv", quietly = TRUE)) {
    stop(
        "The guarded renv activation did not load renv. ",
        "Run through `make r-restore` from the repository root."
    )
}

project_request <- Sys.getenv("RENV_PROJECT", unset = "")
if (!nzchar(project_request)) {
    stop("RENV_PROJECT must identify the NORAD repository root.")
}
project_root <- normalizePath(project_request, winslash = "/", mustWork = TRUE)
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

if (!identical(as.character(getRversion()), "4.6.1")) {
    stop("NORAD local restore requires R 4.6.1; found ", R.version.string)
}

lockfile <- file.path(project_root, "renv.lock")
if (!file.exists(lockfile)) {
    stop("Missing renv lockfile: ", lockfile)
}

message("Restoring NORAD R environment")
message("  project: ", project_root)
message("  lockfile: ", lockfile)
message("  R: ", R.version.string)
message("  Bioconductor: 3.23")

renv::restore(
    project = project_root,
    lockfile = lockfile,
    clean = FALSE,
    prompt = FALSE
)

message("NORAD R environment restore complete.")
