# Neutral R helpers for explicit owner-defined command and file contracts.

abort <- function(...) {
    stop(paste0(...), call. = FALSE)
}

parse_named_arguments <- function(
    values,
    argument_names,
    required_names = argument_names,
    defaults = list(),
    usage_function
) {
    if (length(values) == 1L && values[[1L]] %in% c("-h", "--help")) {
        usage_function()
        quit(status = 0L)
    }
    if (length(values) %% 2L != 0L) {
        abort("Arguments must be supplied as --name value pairs.")
    }
    parsed <- stats::setNames(
        vector("list", length(argument_names)), argument_names
    )
    parsed[names(defaults)] <- defaults
    supplied <- character()
    index <- 1L
    while (index <= length(values)) {
        option <- values[[index]]
        if (!startsWith(option, "--")) {
            abort("Expected an option beginning with --; got: ", option)
        }
        name <- substring(option, 3L)
        if (!(name %in% argument_names)) {
            abort("Unknown argument: ", option)
        }
        if (name %in% supplied) {
            abort("Argument supplied more than once: ", option)
        }
        value <- values[[index + 1L]]
        if (!nzchar(value) || startsWith(value, "--")) {
            abort(option, " requires a non-empty value.")
        }
        parsed[[name]] <- value
        supplied <- c(supplied, name)
        index <- index + 2L
    }
    missing <- required_names[
        vapply(parsed[required_names], is.null, logical(1))
    ]
    if (length(missing) > 0L) {
        abort("Missing required argument(s): --", paste(missing, collapse = ", --"))
    }
    parsed
}

validate_nonempty_file <- function(label, path) {
    if (!file.exists(path) || isTRUE(file.info(path)$isdir) ||
        is.na(file.info(path)$size) || file.info(path)$size <= 0L) {
        abort(label, " does not exist or is empty: ", path)
    }
}

normalize_existing_path <- function(path) {
    normalizePath(path, winslash = "/", mustWork = TRUE)
}

sha256_file_with_fallback <- function(path, unavailable_message) {
    normalized <- normalize_existing_path(path)
    if (nzchar(Sys.which("sha256sum"))) {
        executable <- Sys.which("sha256sum")
        command_args <- shQuote(normalized)
    } else if (nzchar(Sys.which("shasum"))) {
        executable <- Sys.which("shasum")
        command_args <- c("-a", "256", shQuote(normalized))
    } else {
        abort(unavailable_message)
    }
    output <- suppressWarnings(system2(
        executable, args = command_args, stdout = TRUE, stderr = TRUE
    ))
    status <- attr(output, "status")
    if (!is.null(status) && status != 0L) {
        abort("SHA-256 command failed for: ", path)
    }
    joined <- paste(output, collapse = "\n")
    match <- regexpr("[[:xdigit:]]{64}", joined)
    if (match[[1L]] < 0L) {
        abort("Could not parse SHA-256 output for: ", path)
    }
    tolower(regmatches(joined, match))
}

read_contract_tsv <- function(
    label,
    path,
    expected_columns = NULL,
    na_strings = character(),
    preserve_header = FALSE
) {
    validate_nonempty_file(label, path)
    lines <- readLines(path, warn = FALSE)
    if (length(lines) == 0L) {
        abort(label, " is empty: ", path)
    }
    header <- strsplit(sub("\r$", "", lines[[1L]]), "\t", fixed = TRUE)[[1L]]
    if (preserve_header && (any(!nzchar(header)) || anyDuplicated(header))) {
        abort(label, " contains an empty or duplicate column name: ", path)
    }
    if (length(lines) > 1L && any(!nzchar(sub("\r$", "", lines[-1L])))) {
        abort(label, " contains a blank data row: ", path)
    }
    table <- tryCatch(
        utils::read.delim(
            path, header = TRUE, sep = "\t", quote = "", comment.char = "",
            check.names = FALSE, stringsAsFactors = FALSE,
            colClasses = "character", na.strings = na_strings, fill = FALSE
        ),
        error = function(error) {
            abort(label, " could not be parsed as strict TSV: ", error$message)
        }
    )
    if (preserve_header && !identical(names(table), header)) {
        abort(label, " header could not be preserved exactly: ", path)
    }
    if (!preserve_header && anyDuplicated(names(table))) {
        abort(label, " contains duplicate column names: ", path)
    }
    if (!is.null(expected_columns) &&
        !identical(names(table), expected_columns)) {
        abort(
            label, " header does not match the required schema. Expected: ",
            paste(expected_columns, collapse = "\t")
        )
    }
    table
}
