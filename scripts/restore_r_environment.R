#!/usr/bin/env Rscript

# Restore the explicitly activated NORAD R environment from renv.lock.

arguments <- commandArgs(trailingOnly = TRUE)
if (length(arguments) != 0L) {
    stop("restore_r_environment.R does not accept positional arguments.")
}

if (!identical(Sys.getenv("NORAD_USE_RENV", unset = "0"), "1")) {
    stop("Set NORAD_USE_RENV=1 before restoring the NORAD R environment.")
}
if (!identical(Sys.getenv("NORAD_LOCAL_PILOT_R", unset = "0"), "0")) {
    stop("R restoration must run in bootstrap-capable operator mode.")
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

restored_library <- normalizePath(
    .libPaths()[[1L]],
    winslash = "/",
    mustWork = TRUE
)
lock <- renv::lockfile_read(lockfile)
lock_recorded_packages <- names(lock$Packages)
missing_from_restored_library <- lock_recorded_packages[
    !vapply(
        file.path(restored_library, lock_recorded_packages),
        dir.exists,
        logical(1)
    )
]
if (length(missing_from_restored_library) > 0L) {
    message(
        "Hydrating lock-recorded packages found only in external R libraries: ",
        paste(missing_from_restored_library, collapse = ", ")
    )
    hydration <- renv::hydrate(
        packages = missing_from_restored_library,
        library = restored_library,
        update = FALSE,
        project = project_root,
        prompt = FALSE,
        report = TRUE
    )
    if (length(hydration$unresolved) > 0L) {
        stop(
            "Could not hydrate lock-recorded package(s) into the project library: ",
            paste(hydration$unresolved, collapse = ", ")
        )
    }
}

restore_status <- renv::status(
    project = project_root,
    library = restored_library
)
if (!isTRUE(restore_status$synchronized)) {
    stop(
        "The restored library does not match renv.lock; ",
        "r-restore will not attest an out-of-sync environment."
    )
}

message("NORAD R environment restore complete.")
message("  project library: ", restored_library)
