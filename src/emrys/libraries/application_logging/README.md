# Application logging library

This package turns resolved logging controls and explicit event fields into
protected JSONL records and concise stderr messages using standard-library
logging. It leaves machine stdout unchanged. Helpers discard secret values
before inspecting them and reject large or binary payloads; storage completes
short or interrupted writes and preserves partial logs.

The [logging contract](../../../../docs/design/LOGGING_CONTRACT.md) defines which
operations may open a log, event fields, path ownership, redaction, and failure
behavior. A log records execution; it cannot decide receipts, recovery, or exits.
