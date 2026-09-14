# Application logging library

This package turns resolved logging controls and explicit event fields into
protected JSONL records and concise stderr messages using standard-library
logging and Rich for terminal presentation. It leaves machine stdout unchanged. Helpers discard secret values
before inspecting them and reject large or binary payloads; storage completes
short or interrupted writes and preserves partial logs.

The [logging contract](../../../../docs/design/LOGGING_CONTRACT.md) defines which
operations may open a log, event fields, path ownership, redaction, and failure
behavior. A log records execution; it cannot decide receipts, recovery, or exits.

`console_print` styles literal human text; `phase_progress` shows a named phase
and elapsed time. Redirected streams, `NO_COLOR`, and dumb terminals retain plain
text. Doctor keeps complete package-manager output in `package-output.log`
beside its maintenance JSONL; the progress display does not replace diagnostics.
