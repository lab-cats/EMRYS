local({
    use_renv <- Sys.getenv("NORAD_USE_RENV", unset = "0")
    if (!use_renv %in% c("0", "1")) {
        stop("NORAD_USE_RENV must be exactly 0 or 1.")
    }

    if (identical(use_renv, "1")) {
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
