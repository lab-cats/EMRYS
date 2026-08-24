local({
    use_renv <- Sys.getenv("NORAD_USE_RENV", unset = "0")
    if (!use_renv %in% c("0", "1")) {
        stop("NORAD_USE_RENV must be exactly 0 or 1.")
    }

    local_pilot <- Sys.getenv("NORAD_LOCAL_PILOT_R", unset = "0")
    if (!local_pilot %in% c("0", "1")) {
        stop("NORAD_LOCAL_PILOT_R must be exactly 0 or 1.")
    }

    if (identical(local_pilot, "1")) {
        if (!identical(use_renv, "1")) {
            stop("NORAD local-pilot R requires NORAD_USE_RENV=1.")
        }
        project_root <- Sys.getenv("RENV_PROJECT", unset = "")
        selected_library <- Sys.getenv("NORAD_RENV_LIBRARY", unset = "")
        expected_renv_version <- Sys.getenv("NORAD_RENV_VERSION", unset = "")
        if (!nzchar(project_root) || !nzchar(selected_library) ||
            !nzchar(expected_renv_version)) {
            stop("NORAD local-pilot R selectors are incomplete.")
        }
        project_root <- normalizePath(project_root, winslash = "/", mustWork = TRUE)
        selected_library <- normalizePath(
            selected_library, winslash = "/", mustWork = TRUE
        )
        profile_path <- normalizePath(
            file.path(project_root, ".Rprofile"), winslash = "/", mustWork = TRUE
        )
        if (!identical(
            normalizePath(
                Sys.getenv("R_PROFILE_USER"), winslash = "/", mustWork = TRUE
            ),
            profile_path
        )) {
            stop("NORAD local-pilot R did not select the reviewed project profile.")
        }
        renv_description <- file.path(selected_library, "renv", "DESCRIPTION")
        if (!file.exists(renv_description)) {
            stop("The selected NORAD R library has no installed renv package.")
        }
        installed_renv <- base::read.dcf(
            renv_description, fields = "Version"
        )[[1L]]
        if (!identical(installed_renv, expected_renv_version)) {
            stop(
                "The selected NORAD R library has renv ", installed_renv,
                "; expected ", expected_renv_version, "."
            )
        }
        .libPaths(selected_library)
        admitted_library <- normalizePath(.libPaths()[[1L]], winslash = "/")
        if (!identical(admitted_library, selected_library)) {
            stop("R did not admit the selected NORAD library first.")
        }
    } else if (identical(use_renv, "1")) {
        if (!nzchar(Sys.getenv("RENV_CONFIG_SANDBOX_ENABLED", unset = ""))) {
            Sys.setenv(RENV_CONFIG_SANDBOX_ENABLED = "FALSE")
        }
        if (!nzchar(Sys.getenv("RENV_CONFIG_AUTO_SNAPSHOT", unset = ""))) {
            Sys.setenv(RENV_CONFIG_AUTO_SNAPSHOT = "FALSE")
        }
        project_root <- Sys.getenv("RENV_PROJECT", unset = getwd())
        activation_script <- file.path(
            project_root,
            "renv",
            "activate.R"
        )
        if (!file.exists(activation_script)) {
            stop("Missing NORAD renv activation script: ", activation_script)
        }
        source(activation_script)
    }
})
